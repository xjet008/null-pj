"""Transactional, resumable V3 exports. A completion marker is written last."""
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from .codec import encrypt,decrypt
from .genome import validate_genome,CATEGORIES
from .renderer import ascii_text

def _json(path,data):
    Path(path).write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False,allow_nan=False),encoding='utf-8')
def _digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _html(data):
    encoded=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
    return '''<!doctype html><meta charset="utf-8"><title>NULL GENESIS V3</title>
<style>body{background:#050505;color:#ccc;font:14px Consolas,monospace;text-align:center}canvas{max-width:96vw;max-height:85vh;image-rendering:pixelated}button,input{background:#111;color:#ccc;border:1px solid #444;margin:12px}</style>
<canvas id="art"></canvas><div><button id="play">Pause</button><input id="time" type="range"><span id="counter"></span></div><script>
const d='''+encoded+''';const canvas=document.querySelector('#art'),ctx=canvas.getContext('2d'),slider=document.querySelector('#time');canvas.width=d.grid[0]*13;canvas.height=d.grid[1]*24;slider.min=0;slider.max=d.frames.length-1;let frame=0,playing=true,last=0;
function draw(){ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font='24px Consolas,monospace';ctx.textBaseline='top';const chars=d.frames[frame].replaceAll('\\n','');for(let i=0;i<chars.length;i++){const v=Math.round(d.luminance[frame][i]);ctx.fillStyle='rgb('+v+','+v+','+v+')';ctx.fillText(chars[i],i%d.grid[0]*13,Math.floor(i/d.grid[0])*24);}slider.value=frame;document.querySelector('#counter').textContent=frame+' / '+(d.frames.length-1);}
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play';};slider.oninput=()=>{frame=+slider.value;playing=false;draw();};function tick(t){if(playing&&t-last>=1000/d.fps){frame=(frame+1)%d.frames.length;last=t;draw();}requestAnimationFrame(tick);}draw();requestAnimationFrame(tick);</script>'''

def _ffmpeg():
    path=shutil.which('ffmpeg')
    if path:return path
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def export_edition(renderer,g,destination,animation=True,video=False,key=None,resume=True,hidden_message='',force_protect=False,presentation=600):
    if presentation not in (300,600,1200):raise ValueError('Presentation must be 300, 600 or 1200 square pixels')
    validate_genome(g);protect=force_protect or g.get('encryption')=='AES-256-GCM' or g.get('encryption_mode')=='AES-256-GCM' or g.get('protected',False)
    if protect and key is None:raise ValueError('Protected DNA export requires an explicitly supplied local AES key')
    dest=Path(destination).resolve();dest.mkdir(parents=True,exist_ok=True);identifier=str(g.get('edition',0)).zfill(4);final=dest/identifier
    if final.exists():
        if not resume:raise FileExistsError('Refusing to overwrite existing edition '+identifier)
        marker=final/'complete.json'
        if not marker.is_file():raise ValueError('Edition exists without a transactional completion marker')
        record=json.loads(marker.read_text(encoding='utf-8'))
        if record['genome_fingerprint']!=g['fingerprint']:raise ValueError('Resume DNA mismatch for '+identifier)
        if g['genome_version']=='web-4.5.0' and record.get('presentation_size')!=[presentation,presentation]:raise ValueError('Resume presentation changed; use a new output directory')
        if any(not (final/p).is_file() or _digest(final/p)!=digest for p,digest in record['files'].items()):raise ValueError('Completed export integrity mismatch for '+identifier)
        existing_dna=json.loads((final/'genome.dna.json').read_text(encoding='utf-8'))
        if bool(existing_dna.get('algorithm')=='AES-256-GCM')!=bool(protect):raise ValueError('Resume DNA protection changed; use a new output directory')
        if protect:
            payload=decrypt(existing_dna,key)
            if payload['genome']['fingerprint']!=g['fingerprint'] or hidden_message and payload.get('hidden_message','')!=hidden_message:raise ValueError('Resume encrypted DNA identity/message mismatch')
        if video and not {'animation.mp4','animation.webm'}<=record['files'].keys():raise ValueError('Resume requires missing video media; use a new output directory')
        return {**record,'resumed':True}
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='.'+identifier+'-',dir=dest) as temporary:
        staging=Path(temporary);canonical=renderer.render(g);v45=g['genome_version']=='web-4.5.0';image=renderer.square_image(canonical,presentation) if v45 else renderer.image(canonical);image.save(staging/'preview.png')
        (staging/'ascii.txt').write_text(canonical['ascii'],encoding='ascii',newline='\n')
        if not protect:np.savez_compressed(staging/'cells.npz',glyph=canonical['glyph'],cells=canonical['cells'],packet=canonical['packet'],config=canonical['cfg'],grid=np.array(canonical['grid']))
        dna=encrypt(g,key,hidden_message) if protect else dict(genome=g)
        _json(staging/'genome.dna.json',dna)
        frames=[];luminance=[];timings=[];processes=[];error_files=[]
        total=g['animation']['fps']*g['animation']['seconds'];grid=g.get('grid',[30,30]);fps=g['animation']['fps']
        try:
            if video:
                ffmpeg=_ffmpeg();width,height=(presentation,presentation) if v45 else (grid[0]*13,grid[1]*24)
                for ext,codec,extra in [('mp4','libx264',['-crf','18','-preset','veryfast','-pix_fmt','yuv420p']),('webm','libvpx-vp9',['-b:v','0','-crf','28','-deadline','realtime','-cpu-used','5','-row-mt','1'])]:
                    err=(staging/(ext+'.stderr')).open('wb');error_files.append(err)
                    args=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','-','-an','-c:v',codec,*extra,'-threads','4',str(staging/('animation.'+ext))]
                    processes.append((ext,subprocess.Popen(args,stdin=subprocess.PIPE,stderr=err,creationflags=0x08000000 if os.name=='nt' else 0)))
            if animation or video:
                for result in renderer.render_sequence(g):
                    frames.append(result['ascii']);luminance.append(np.round(result['cells'][:,0],3).tolist());timings.append(result['gpu_ms'])
                    if video:
                        pixels=np.asarray(renderer.square_image(result,presentation) if v45 else renderer.image(result)).tobytes()
                        for ext,process in processes:process.stdin.write(pixels)
                for ext,process in processes:
                    process.stdin.close()
                    if process.wait(timeout=120):raise RuntimeError('FFmpeg '+ext+' encoding failed')
                for stream in error_files:stream.close()
                for ext,_ in processes:(staging/(ext+'.stderr')).unlink(missing_ok=True)
                data=dict(version='3.0.0',edition=g.get('edition',0),grid=grid,fps=fps,seconds=g['animation']['seconds'],profile=g['animation'].get('name',str(g['animation']['profile'])),motion=g.get('motion'),canonical_frame=0,genome_fingerprint=g['fingerprint'],frames=frames,luminance=luminance)
                if v45:data.update(version='4.5.0',presentation=[presentation,presentation])
                with gzip.open(staging/'animation.frames.json.gz','wt',encoding='utf-8',compresslevel=9) as stream:json.dump(data,stream,separators=(',',':'),allow_nan=False)
                if v45:
                    from gpu_html_v45 import document
                    html=document(data)
                else:html=_html(data)
                (staging/'animation.html').write_text(html,encoding='utf-8')
        finally:
            for ext,process in processes:
                if process.poll() is None:process.kill();process.wait()
            for stream in error_files:
                if not stream.closed:stream.close()
        attributes=g.get('categories',[])
        if isinstance(attributes,dict):attributes=[dict(trait_type=k,value=v.get('name',v.get('value',v)) if isinstance(v,dict) else v) for k,v in attributes.items()]
        attrs=[dict(trait_type=a['trait_type'],value=a.get('value',a.get('name',a.get('id')))) for a in attributes if isinstance(a,dict)]
        sources=g.get('base_concepts',g.get('source_concepts',g.get('concepts',[])))
        composites=g.get('composite_traits',g.get('recipes',[g['recipe'].get('id')] if isinstance(g.get('recipe'),dict) else []))
        metadata=dict(name='NULL GENESIS #'+identifier,edition=g.get('edition',0),rarity=g.get('rarity'),genome_version=g['genome_version'],render_version='native-3.0.0',render_resolution=grid,animated=bool(animation or video),image='preview.png',animation_url='animation.html' if animation or video else None,attributes=attrs,base_concepts=sources,composite_traits=composites,animation=g['animation'],genome_fingerprint=g['fingerprint'],canonical_hash=canonical['canonical_hash'],encryption_mode='AES-256-GCM' if protect else 'Encoded genome',backend=renderer.backend)
        if v45:
            from quality_v45 import quality
            metrics,_=quality(canonical,g)
            _json(staging/'quality.json',dict(version='4.5.0',genome_fingerprint=g['fingerprint'],metrics=metrics,repair_log=[],exported_without_repairs=True))
            metadata.update(render_version='native-4.5.0',native_grid=grid,presentation_size=[presentation,presentation],framing_mode=g['composition']['mode'],encoder_version=g['encoder']['version'],frame_occupancy=metrics['dimension_occupancy'],quality=metrics,quality_record='quality.json',density_budget=g['density_budget'])
        _json(staging/'metadata.json',metadata)
        files={p.name:_digest(p) for p in staging.iterdir() if p.is_file()}
        record=dict(version='3.0.0',edition=g.get('edition',0),genome_fingerprint=g['fingerprint'],canonical_hash=canonical['canonical_hash'],grid=grid,backend=renderer.backend,frame_count=len(frames),gpu_frame_ms=timings,files=files,wall_seconds=round(time.perf_counter()-start,3),completed=True,visual_release_approved=False)
        if v45:record.update(version='4.5.0',presentation_size=[presentation,presentation])
        _json(staging/'complete.json',record)
        # Rename only a directory created by this transaction; the archived
        # collection is never touched and failure leaves no completed edition.
        staging.rename(final)
    return record

def export_batch(renderer,genomes,destination,animation=True,video=False,key=None,resume=True,hidden_messages=None,protected_fingerprints=None,presentation=600):
    root=Path(destination).resolve();marker=root/'.nullgenesis-v3-output'
    if root.exists() and any(root.iterdir()) and not marker.is_file():raise ValueError('Refusing to write into an existing unmarked collection directory')
    root.mkdir(parents=True,exist_ok=True);marker.write_text('NULL GENESIS V3 experimental exports\n',encoding='ascii')
    editions=[int(g.get('edition',0)) for g in genomes]
    if len(set(editions))!=len(editions):raise ValueError('Duplicate edition IDs')
    results=[]
    for i,g in enumerate(genomes):
        record=export_edition(renderer,g,root,animation,video,key,resume,(hidden_messages or {}).get(g['fingerprint'],''),g['fingerprint'] in (protected_fingerprints or set()),presentation);results.append(record)
        print(json.dumps(dict(edition=g.get('edition',0),completed=i+1,total=len(genomes),resumed=record.get('resumed',False))),flush=True)
    report=dict(version='3.0.0',count=len(results),backend=renderer.backend,editions=results,requires_visual_review=True,approved_for_collection_replacement=False)
    _json(root/'batch-report.json',report);return report
