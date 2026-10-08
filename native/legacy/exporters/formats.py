import json, io, hashlib, time, shutil, subprocess, zipfile
from pathlib import Path
import numpy as np
from engine.renderer import ascii_text
def atomic_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(path)
def png_bytes(renderer,result,cw=13,ch=24):
    b=io.BytesIO();renderer.image(result,cw,ch).save(b,format='PNG');return b.getvalue()
def ffmpeg_path():
    if shutil.which('ffmpeg'):return shutil.which('ffmpeg')
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:return None
def animation(renderer,base,g,dest,video=True):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);edition=f'{g["edition"]:04}';frames=[];luminance=[];images=[];fps=g['animation']['fps'];total=fps*g['animation']['seconds'];start=time.perf_counter()
    for index in range(total):
        r=renderer.frame(base,g,index);frames.append(ascii_text(r['glyph']));luminance.append(np.round(r['cells'][:,0],3).tolist());images.append(np.array(renderer.image(r,13,24)))
    data=dict(version='1.0.0',edition=g['edition'],grid=[30,30],fps=fps,seconds=g['animation']['seconds'],profile=g['animation']['name'],fragment_identity='canonical-surface-cell',frames=frames,luminance=luminance,genome_fingerprint=g['fingerprint'])
    atomic_json(dest/(edition+'.frames.json'),data)
    js=json.dumps(data,separators=(',',':')).replace('</','<\\/')
    html='''<!doctype html><meta charset="utf-8"><title>NULL GENESIS</title><style>body{background:#080808;color:#bbb;font:14px Consolas,monospace;display:grid;place-items:center}canvas{max-height:85vh;border:1px solid #333}button,input{margin:8px;background:#222;color:#ddd;border:1px solid #444}</style><h1>NULL GENESIS · EDITION '''+edition+'''</h1><canvas width="390" height="720"></canvas><div><button id="play">Pause</button><input id="time" type="range" min="0"><button id="step">Step</button><span id="counter"></span></div><script>const data='''+js+''';const canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');let index=0,playing=true,last=0;const slider=document.querySelector('#time');slider.max=data.frames.length-1;function draw(){ctx.fillStyle='#050505';ctx.fillRect(0,0,390,720);ctx.font='24px Consolas,monospace';ctx.textBaseline='top';let chars=data.frames[index].split('\\n').slice(0,30).join('');for(let i=0;i<900;i++){let v=Math.round(data.luminance[index][i]);ctx.fillStyle='rgb('+v+','+v+','+v+')';ctx.fillText(chars[i],(i%30)*13,Math.floor(i/30)*24)}slider.value=index;document.querySelector('#counter').textContent=index+' / '+(data.frames.length-1)}document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play'};slider.oninput=()=>{index=+slider.value;playing=false;draw()};document.querySelector('#step').onclick=()=>{index=(index+1)%data.frames.length;playing=false;draw()};function tick(t){if(playing&&t-last>1000/data.fps){index=(index+1)%data.frames.length;last=t;draw()}requestAnimationFrame(tick)}draw();requestAnimationFrame(tick)</script>'''
    (dest/(edition+'.html')).write_text(html,encoding='utf-8')
    exports=['frames.json','html'];ff=ffmpeg_path();errors=[]
    if video and ff:
        for ext,codec,extra in [('webm','libvpx-vp9',['-b:v','0','-crf','28','-deadline','realtime','-cpu-used','5','-row-mt','1','-threads','4']),('mp4','libx264',['-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-threads','4'])]:
            args=[ff,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','390x720','-r',str(fps),'-i','-','-an','-c:v',codec,*extra,str(dest/(edition+'.'+ext))]
            p=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000 if __import__('os').name=='nt' else 0)
            _,err=p.communicate(b''.join(i.tobytes() for i in images))
            if p.returncode:errors.append(ext+': '+err.decode(errors='replace')[-500:])
            else:exports.append(ext)
    elif video:errors.append('FFmpeg unavailable; canonical frames and HTML remain available.')
    return dict(frames=total,fps=fps,seconds=g['animation']['seconds'],exports=exports,errors=errors,wall_seconds=round(time.perf_counter()-start,3),frame_hashes=[hashlib.sha256(f.encode()).hexdigest() for f in frames])
def public_zip(root,editions=None):
    root=Path(root);output=io.BytesIO();ids=set(editions) if editions else None
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in ['ascii','metadata','previews','animations','genomes','cells']:
            for p in (root/'collection'/folder).glob('*'):
                if p.is_file() and (ids is None or int(p.name.split('.')[0]) in ids):z.write(p,'collection/'+folder+'/'+p.name)
        for p in (root/'reports').glob('*.json'):z.write(p,'reports/'+p.name)
    return output.getvalue()
