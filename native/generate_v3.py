"""Resumable NVIDIA V3 experimental validation and separate collection exports.

The immutable legacy collection is never opened for writing. Production generation
requires both a passed experiment report and an explicit visual-approval argument.
Every completion marker is written after the edition's media and identity checks.
"""
from __future__ import annotations
import argparse
import base64
import copy
import gzip
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import time
import zipfile
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal,validate_genome,canonical
from validate_v3 import quality,repair,Uniqueness,loop_samples,frame_distance,audit_collection,digest,QUOTAS,CATEGORIES

NATIVE=Path(__file__).resolve().parent
REPO=NATIVE.parent

def write_json(path,value,pretty=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2 if pretty else None,separators=None if pretty else (',',':'),ensure_ascii=False,allow_nan=False),encoding='utf-8');os.replace(temporary,path)

def write_bytes(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_name(path.name+'.tmp');temporary.write_bytes(data);os.replace(temporary,path)

def gzip_json(path,value):
    raw=json.dumps(value,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8');write_bytes(path,gzip.compress(raw,compresslevel=9,mtime=0))

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def new_owner_key(path):
    """Only this release's named key is read; legacy keys are never accessed."""
    path=Path(path).resolve();expected=(NATIVE/'private'/'v3-owner.key').resolve()
    if path!=expected:raise ValueError('The V3 release key must use native/private/v3-owner.key')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        key=path.read_bytes()
        if len(key)!=32:raise ValueError('Existing V3 release key has an invalid length')
        return key
    key=os.urandom(32)
    with path.open('xb') as stream:stream.write(key)
    return key

def protect_genome(g,key):
    nonce=os.urandom(12);aad=('NULL-GENESIS/web-genome/v3/'+g['fingerprint']).encode('ascii');payload=canonical(dict(identity=g['fingerprint'],genome=g));cipher=AESGCM(key).encrypt(nonce,payload,aad)
    envelope=dict(version=3,algorithm='AES-256-GCM',genome_version=g['genome_version'],fingerprint=g['fingerprint'],nonce=base64.b64encode(nonce).decode(),aad=base64.b64encode(aad).decode(),ciphertext=base64.b64encode(cipher).decode())
    recovered=json.loads(AESGCM(key).decrypt(nonce,cipher,aad));validate_genome(recovered['genome'])
    if recovered['identity']!=g['fingerprint']:raise ValueError('Authenticated V3 export round-trip failed')
    return envelope

def metadata(item,g,result,metrics,repairs,loop,experimental=False):
    edition=item['edition'];identifier=item['id'];rarity=g['rarity'];attributes=[dict(trait_type=t['trait_type'],value=t['value'],id=t['id']) for t in g['categories']]
    root='/v3/experiments/' if experimental else '/v3/collection/previews/'
    media_root='/v3/experiments/'+identifier if experimental else '/v3/collection/animations/'+identifier
    viewer='/v3/viewer.html?'+('experiment='+identifier if experimental else 'edition='+str(edition));all_traits=list(dict.fromkeys([*g['source_concepts'],*g['modifiers'].values(),*[t['id'] for t in attributes]]))
    return dict(name='NULL GENESIS '+('EXPERIMENT '+identifier if experimental else '#'+str(edition)),edition=edition,id=identifier,release='v3-experimental' if experimental else 'v3-candidate',genome_version=g['genome_version'],render_version=g['render_version'],canonical_renderer='cuda-sdf-3.0.0',render_resolution=g['grid'],grid=g['grid'],rarity=rarity,animated=True,base_concepts=g['source_concepts'],source_concepts=g['source_concepts'],source_libraries=list(dict.fromkeys(t['library'] for t in g['influences'])),composite_traits=[g['recipe']['id']],attributes=attributes,traits=all_traits,family='SYNTHESIS',subject=g['subject'],style_id=g['style'],primary_style=g['subject'],appearance=g['appearance'],rendering_profile=g['rendering_profile'],modifiers=g['modifiers'],parameters=g['parameters'],genome_fingerprint=g['fingerprint'],seed=g['seed'],encryption_mode='AES-256-GCM' if item.get('protected') and not experimental else 'Encoded genome',encryption='AES-256-GCM' if item.get('protected') and not experimental else 'NONE',animation_profile=g['animation']['name'],animation={**g['animation'],'motion':g['motion']},loop_validation=loop,quality=metrics,repair_log=repairs,uniqueness=None,backend=result['backend'],gpu_ms=result['gpu_ms'],render_ms=result['wall_ms'],canonical_hash=result['canonical_hash'],image=root+identifier+'.png',animation_url=viewer,media=dict(html=viewer,frames=media_root+'.frames.json.gz',mp4=media_root+'.mp4' if rarity=='LEGENDARY' and not experimental else None,webm=media_root+'.webm' if rarity=='LEGENDARY' and not experimental else None),legacy_edition=item['legacy_edition'],provenance={k:v for k,v in g['provenance'].items() if k not in ('hidden_message',)})

def frame_sequence(renderer,g,canonical_result=None):
    total=g['animation']['fps']*g['animation']['seconds'];n=g['grid'][0]*g['grid'][1];packed=np.empty((total,n,2),np.uint8);timings=[];temporal=[];first=None;quarter=None;previous=None;transition=0;prior=None
    iterator=renderer.render_sequence(g) if hasattr(renderer,'render_sequence') else (renderer.render(g,i) for i in range(total))
    for index,result in enumerate(iterator):
        if index>=total:raise RuntimeError('Renderer produced too many animation frames')
        if index==0:
            first=result
            if canonical_result is not None and result['ascii']!=canonical_result['ascii']:raise RuntimeError('Animation canonical frame differs from accepted art')
        if index==total//4:quarter=result
        if index==total-1:previous=result
        packed[index,:,0]=result['glyph'];packed[index,:,1]=np.rint(result['cells'][:,0]).clip(0,255).astype(np.uint8);timings.append(result['gpu_ms'])
        if prior is not None:transition=max(transition,frame_distance(prior,result)['fraction'])
        prior=result
        if index in (0,total//4,total//2,3*total//4,total-1):
            mask=result['glyph']!=32;positions=result['packet'][mask,5:8];levels=result['cells'][mask,0];temporal.extend([float(mask.mean()),float(levels.mean()/255) if len(levels) else 0,*([float(x) for x in positions.mean(axis=0)] if len(positions) else [0,0,0])])
    if first is None or quarter is None or previous is None or index!=total-1:raise RuntimeError('Renderer produced an incomplete animation timeline')
    end=renderer.render(g,total);loop=loop_samples(first,quarter,end,previous)
    if not loop['periodic'] or not loop['animated']:raise RuntimeError('Procedural animation failed periodicity or geometric motion validation')
    loop['max_transition_fraction']=round(transition,5);loop['frame_count']=total;loop['motion_trajectory_signature']=[round(x,6) for x in temporal]
    # Exact canonical endpoint is measured, not merely implied by a modulo time.
    payload=dict(version='3.0.0',encoding='interleaved-u8',grid=g['grid'],fps=g['animation']['fps'],seconds=g['animation']['seconds'],profile=g['animation']['name'],frame_count=total,canonical_frame=0,genome_fingerprint=g['fingerprint'],loop=True,cells=base64.b64encode(packed.tobytes()).decode('ascii'))
    return payload,loop,temporal,timings

def preview_samples(renderer,g,canonical_result):
    total=g['animation']['fps']*g['animation']['seconds'];results=list(renderer.render_sequence(g,[total//4,total])) if hasattr(renderer,'render_sequence') else [renderer.render(g,total//4),renderer.render(g,total)];loop=loop_samples(canonical_result,results[0],results[1])
    if not loop['periodic'] or not loop['animated']:raise RuntimeError('Experimental pose validation failed')
    loop['full_timeline_validated']=False
    return loop

def accepted_candidate(renderer,item,uniqueness=None,full_animation=False,max_repairs=6):
    original=item['genome'];g=copy.deepcopy(original);repairs=[];best=None
    for attempt in range(max_repairs+1):
        result=renderer.render(g);metrics,signature=quality(result,g);verdict=uniqueness.inspect(result,g,signature) if uniqueness else dict(unique=True)
        if best is None or metrics['quality_score']>best[2]['quality_score']:best=(g,result,metrics,signature)
        if metrics['accepted'] and verdict['unique']:
            if full_animation:
                payload,loop,temporal,timings=frame_sequence(renderer,g,result);temporal_verdict=uniqueness.inspect(result,g,signature,temporal) if uniqueness else verdict
                if temporal_verdict['unique']:return g,result,metrics,signature,repairs,payload,loop,temporal,timings,temporal_verdict
                verdict=temporal_verdict
            else:return g,result,metrics,signature,repairs,None,preview_samples(renderer,g,result),None,[],verdict
        if attempt==max_repairs:break
        updated,actions=repair(g,metrics,attempt,duplicate=not verdict['unique']);next_result=renderer.render(updated);next_metrics,_=quality(next_result,updated)
        repairs.append(dict(attempt=attempt+1,candidate_seed=g['seed'],previous_fingerprint=g['fingerprint'],updated_fingerprint=updated['fingerprint'],actions=actions,previous_score=metrics['quality_score'],updated_score=next_metrics['quality_score'],duplicate_reason=verdict.get('reason'),acceptance_status='candidate repaired; revalidation required'));g=updated
    error=dict(edition=item['edition'],candidate_seed=original['seed'],best_score=best[2]['quality_score'],quality_reasons=best[2]['reasons'],repairs=repairs,final_acceptance_status='rejected')
    raise RuntimeError('Finite candidate budget exhausted: '+json.dumps(error))

def contact_sheets(root,items,legacy_root,destination,per_sheet=20):
    destination.mkdir(parents=True,exist_ok=True);paths=[];font=ImageFont.truetype(str(Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts/consola.ttf'),13)
    tile_w=440;tile_h=272;columns=4
    for offset in range(0,len(items),per_sheet):
        group=items[offset:offset+per_sheet];rows=math.ceil(len(group)/columns);canvas=Image.new('RGB',(tile_w*columns,tile_h*rows),(10,10,10));draw=ImageDraw.Draw(canvas)
        for index,item in enumerate(group):
            ox=(index%columns)*tile_w;oy=(index//columns)*tile_h;m=item['metadata'];paths2=[legacy_root/'collection'/'previews'/f"{item['legacy_edition']:04}.png",root/(item['id']+'-30.png'),root/(item['id']+'.png')]
            for j,path in enumerate(paths2):
                if path.is_file():
                    with Image.open(path) as image:image.thumbnail((132,226),Image.Resampling.LANCZOS);canvas.paste(image,(ox+7+j*143+(132-image.width)//2,oy+22))
                draw.text((ox+7+j*143,oy+3),['ARCHIVED','NATIVE 30','NATIVE 50'][j],font=font,fill=(145,)*3)
            draw.text((ox+7,oy+249),f"{item['id']} {m['rarity']} Q{m['quality']['quality_score']:.0f} / {m['subject'][:22]}",font=font,fill=(215,)*3)
        path=destination/f'comparisons-{offset//per_sheet+1:02}.jpg';canvas.save(path,quality=92,subsampling=0);paths.append(str(path))
    return paths

def run_experiments(renderer,document,output,animations=False,resume=True):
    root=output/'experiments';reports=output/'reports';root.mkdir(parents=True,exist_ok=True);reports.mkdir(parents=True,exist_ok=True);items=[];comparisons=[];started=time.perf_counter();uniqueness=Uniqueness(len(document['items']));states=NATIVE/'work'/'experiment-state';states.mkdir(parents=True,exist_ok=True)
    for ordinal,item in enumerate(document['items']):
        identifier=item['id'];checkpoint=states/(identifier+'.json');cached=read_json(checkpoint) if resume and checkpoint.is_file() else None
        if cached and cached['candidate_fingerprint']!=item['genome']['fingerprint']:raise ValueError('Experimental resume manifest mismatch '+identifier)
        if cached and (root/(identifier+'.json.gz')).is_file() and (root/(identifier+'.png')).is_file() and (root/(identifier+'-30.png')).is_file() and (not animations or (root/(identifier+'.frames.json.gz')).is_file()):
            g=cached['genome'];result=renderer.render(g);metrics,signature=quality(result,g);loop=cached['metadata']['loop_validation'];repairs=cached['metadata']['repair_log'];m=cached['metadata'];comparison=cached['comparison'];temporal=cached.get('temporal')
        else:
            g,result,metrics,signature,repairs,payload,loop,temporal,timings,verdict=accepted_candidate(renderer,item,uniqueness,animations)
            thirty=copy.deepcopy(g);thirty['grid']=[30,30];thirty=seal(thirty);r30=renderer.render(thirty);q30,_=quality(r30,thirty);m=metadata(item,g,result,metrics,repairs,loop,True);m['uniqueness']=verdict;m['full_animation_available']=bool(payload)
            write_bytes(root/(identifier+'.png'),renderer.png(result));write_bytes(root/(identifier+'-30.png'),renderer.png(r30));record=dict(genome=g,dna=g,metadata=m,ascii=result['ascii'],luminance=np.round(result['cells'][:,0],4).tolist());gzip_json(root/(identifier+'.json.gz'),record)
            if payload:gzip_json(root/(identifier+'.frames.json.gz'),payload)
            comparison=dict(id=identifier,canonical_hash_50=result['canonical_hash'],canonical_hash_30=r30['canonical_hash'],quality_50=metrics,quality_30=q30,gpu_ms_50=result['gpu_ms'],gpu_ms_30=r30['gpu_ms'],wall_ms_50=result['wall_ms'],wall_ms_30=r30['wall_ms'],frame_gpu_ms=timings,loop=loop,legacy_edition=item['legacy_edition'],source_editions=g['provenance'].get('source_editions'),operator=g['recipe']['operator'],source_concepts=g['source_concepts'])
            files={p.name:digest(p.read_bytes()) for p in [root/(identifier+'.png'),root/(identifier+'-30.png'),root/(identifier+'.json.gz')]}
            if payload:files[identifier+'.frames.json.gz']=digest((root/(identifier+'.frames.json.gz')).read_bytes())
            write_json(checkpoint,dict(candidate_fingerprint=item['genome']['fingerprint'],genome=g,metadata=m,comparison=comparison,temporal=temporal,files=files,completed=True))
        uniqueness.accept(result,g,signature,item['edition'],temporal);items.append({**item,'genome':None,'metadata':m});comparisons.append(comparison)
        if (ordinal+1)%10==0:print(json.dumps(dict(mode='experiments',completed=ordinal+1,total=len(document['items']),elapsed_seconds=round(time.perf_counter()-started,2))),flush=True)
    contacts=contact_sheets(root,items,REPO/'dist',reports/'contact-sheets');q50=np.array([r['quality_50']['quality_score'] for r in comparisons]);q30=np.array([r['quality_30']['quality_score'] for r in comparisons]);t50=np.array([r['gpu_ms_50'] for r in comparisons]);t30=np.array([r['gpu_ms_30'] for r in comparisons]);objects50=np.array([r['quality_50']['visible_objects'] for r in comparisons]);objects30=np.array([r['quality_30']['visible_objects'] for r in comparisons])
    passed=all(r['quality_50']['accepted'] and r['loop']['periodic'] and r['loop']['animated'] for r in comparisons)
    report=dict(version='3.0.0',passed=passed,experiment_count=len(items),native_backend=renderer.backend,hardware=renderer.status(),elapsed_seconds=round(time.perf_counter()-started,3),native_grids=[[30,30],[50,50]],native_50=dict(median_quality=float(np.median(q50)),mean_quality=float(q50.mean()),median_visible_objects=float(np.median(objects50)),median_gpu_ms=float(np.median(t50)),p95_gpu_ms=float(np.percentile(t50,95))),native_30=dict(median_quality=float(np.median(q30)),mean_quality=float(q30.mean()),median_visible_objects=float(np.median(objects30)),median_gpu_ms=float(np.median(t30)),p95_gpu_ms=float(np.percentile(t30,95))),resolution_recommendation=50 if objects50.mean()>objects30.mean() else 30,canonical_resolution_frozen=False,visual_review_required=True,visual_review_approved=False,full_animation_timelines=animations,loop_validation_scope='all full timelines and preceding boundary' if animations else 'three actual CUDA poses: canonical, quarter and repeated endpoint; full timelines await visual gate',contact_sheets=contacts,comparisons=comparisons,legacy_collection_preserved=True)
    write_json(reports/'experiments.json',report,True);public_items=[{**item['metadata'],'id':item['id'],'full_animation_available':item['metadata'].get('full_animation_available',False)} for item in items];write_json(root/'index.json',dict(version='3.0.0',items=public_items,report='/v3/reports/experiments.json',contact_sheets=['/v3/reports/contact-sheets/'+Path(p).name for p in contacts],full_animation_timelines=animations));print(json.dumps(dict(mode='experiments',passed=passed,report=str(reports/'experiments.json'),contact_sheets=len(contacts),elapsed_seconds=report['elapsed_seconds'])),flush=True);return report

def animation_html(data):
    # A self-contained player embeds gzip JSON. This remains playable after the
    # archive is extracted, without network access or a private key.
    encoded=base64.b64encode(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)).decode()
    return '''<!doctype html><meta charset="utf-8"><title>NULL GENESIS V3</title><style>body{background:#050505;color:#ddd;text-align:center;font:14px Consolas,monospace}canvas{image-rendering:pixelated;max-width:95vw;max-height:85vh}button,input{margin:12px;background:#111;color:#ddd;border:1px solid #555}</style><canvas id="art"></canvas><div><button id="play">Pause</button><input id="time" type="range"><span id="counter"></span></div><script type="module">
const encoded="'''+encoded+'''",gzip=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)),d=await new Response(new Blob([gzip]).stream().pipeThrough(new DecompressionStream('gzip'))).json(),raw=Uint8Array.from(atob(d.cells),c=>c.charCodeAt(0)),canvas=document.querySelector('#art'),ctx=canvas.getContext('2d'),slider=document.querySelector('#time'),n=d.grid[0]*d.grid[1];canvas.width=d.grid[0]*13;canvas.height=d.grid[1]*24;slider.min=0;slider.max=d.frame_count-1;let frame=0,playing=true,last=0;function draw(){ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font='24px Consolas,monospace';ctx.textBaseline='top';for(let i=0;i<n;i++){let o=(frame*n+i)*2,c=raw[o],v=raw[o+1];if(c===32)continue;ctx.fillStyle='rgb('+v+','+v+','+v+')';ctx.fillText(String.fromCharCode(c),i%d.grid[0]*13,Math.floor(i/d.grid[0])*24);}slider.value=frame;document.querySelector('#counter').textContent=frame+' / '+(d.frame_count-1);}document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play'};slider.oninput=()=>{frame=+slider.value;playing=false;draw()};function tick(t){if(playing&&t-last>=1000/d.fps){frame=(frame+1)%d.frame_count;last=t;draw()}requestAnimationFrame(tick)}draw();requestAnimationFrame(tick);</script>'''

def encode_video(renderer,g,data,directory,identifier):
    try:import imageio_ffmpeg;ffmpeg=shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as error:raise RuntimeError('imageio-ffmpeg is required for NFT video exports') from error
    raw=np.frombuffer(base64.b64decode(data['cells']),np.uint8).reshape(data['frame_count'],-1,2);w,h=data['grid'];processes=[];errors=[];started=time.perf_counter()
    try:
        for ext,codec,extra in [('mp4','libx264',['-crf','18','-preset','veryfast','-pix_fmt','yuv420p']),('webm','libvpx-vp9',['-b:v','0','-crf','28','-deadline','realtime','-cpu-used','5','-row-mt','1'])]:
            output=directory/(identifier+'.'+ext);error_path=directory/(identifier+'.'+ext+'.stderr');stream=error_path.open('wb');errors.append((stream,error_path));command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w*13}x{h*24}','-r',str(data['fps']),'-i','-','-an','-c:v',codec,*extra,'-threads','4',str(output)];processes.append((ext,subprocess.Popen(command,stdin=subprocess.PIPE,stderr=stream,creationflags=0x08000000 if os.name=='nt' else 0)))
        for frame in raw:
            cells=np.zeros((w*h,12),np.float32);cells[:,0]=frame[:,1];image=renderer.image(dict(grid=[w,h],glyph=frame[:,0],cells=cells));pixels=np.asarray(image).tobytes()
            for ext,process in processes:process.stdin.write(pixels)
        for ext,process in processes:
            process.stdin.close()
            if process.wait(timeout=180)!=0:raise RuntimeError('FFmpeg '+ext+' failed; encoding log retained')
    finally:
        for ext,process in processes:
            if process.poll() is None:process.kill();process.wait()
        for stream,path in errors:stream.close()
    for stream,path in errors:path.unlink(missing_ok=True)
    return round(time.perf_counter()-started,3)

def export_archives(collection,records,maximum=24*1024*1024):
    directory=collection/'exports';directory.mkdir(parents=True,exist_ok=True);parts=[];archive=None;size=0;first=None;last=None;part=0
    def start():
        nonlocal part,archive,size,first,last
        part+=1;archive=zipfile.ZipFile(directory/f'null-genesis-v3-part-{part:02}.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9);archive.writestr('README.txt','NULL GENESIS V3: deterministic native grayscale ASCII and local encrypted DNA. Open animation.html in a current browser. Private owner keys are excluded. GPU generation is NVIDIA CUDA; FFmpeg MP4/WebM encoding is CPU software. No NFT minting or ownership is implied.\n');size=0;first=None;last=None
    def finish():
        nonlocal archive
        archive.close();path=Path(archive.filename)
        if path.stat().st_size>=25*1024*1024:raise RuntimeError('Archive exceeds GitHub web asset size budget')
        parts.append(dict(part=part,url='/v3/collection/exports/'+path.name,file=path.name,first_edition=first,last_edition=last,bytes=path.stat().st_size,sha256=digest(path.read_bytes())));archive=None
    for row in records:
        edition=row['edition'];identifier=f'{edition:04}';frames_path=collection/'animations'/(identifier+'.frames.json.gz')
        with gzip.open(frames_path,'rt',encoding='utf-8') as stream:animation=json.load(stream)
        files=[('ascii.txt',row['ascii'].encode('ascii')),('preview.png',(collection/'previews'/(identifier+'.png')).read_bytes()),('metadata.json',json.dumps(row['metadata'],separators=(',',':')).encode()),('genome.dna.json',json.dumps(row['dna'],separators=(',',':')).encode()),('animation.frames.json.gz',frames_path.read_bytes()),('animation.html',animation_html(animation).encode())]
        for ext in ('mp4','webm'):
            path=collection/'animations'/(identifier+'.'+ext)
            if path.is_file():files.append(('animation.'+ext,path.read_bytes()))
        estimate=sum(len(data) for _,data in files)
        if archive is not None and size+estimate>maximum:finish()
        if archive is None:start()
        if first is None:first=edition
        last=edition
        for name,data in files:archive.writestr(identifier+'/'+name,data)
        size+=estimate
    if archive is not None:finish()
    write_json(directory/'index.json',dict(version='3.0.0',count=len(records),parts=parts,owner_keys_included=False));return parts

def run_collection(renderer,document,output,visual_approval=False,canonical_grid=50,resume=True,max_repairs=6,videos=True):
    report_path=output/'reports'/'experiments.json';experiment=read_json(report_path)
    if not experiment.get('passed') or not experiment.get('full_animation_timelines') or not visual_approval:raise ValueError('Validate full experimental timelines, inspect all contact sheets, then explicitly pass --approve-experiments')
    if len(document['items'])!=3333 or Counter(item['genome']['rarity'] for item in document['items'])!=QUOTAS:raise ValueError('Exactly 3,333 candidates with preserved five rarity quotas are required')
    if canonical_grid not in (30,50):raise ValueError('Choose a measured native 30 or 50 release grid')
    experiment.update(visual_review_approved=True,canonical_resolution_frozen=True,canonical_grid=[canonical_grid,canonical_grid]);write_json(report_path,experiment,True)
    root=output/'collection';previews=root/'previews';animations=root/'animations';reports=output/'reports';root.mkdir(parents=True,exist_ok=True);previews.mkdir(exist_ok=True);animations.mkdir(exist_ok=True);reports.mkdir(parents=True,exist_ok=True);states=NATIVE/'work'/'collection-state';states.mkdir(parents=True,exist_ok=True);key=new_owner_key(NATIVE/'private'/'v3-owner.key');uniqueness=Uniqueness(3333);records=[];completed=[];started=time.perf_counter();frame_count=0;gpu_timings=[];encoding_seconds=0
    marker=root/'.nullgenesis-v3-output';marker.write_text('V3 separate candidate output; immutable archived collection preserved\n',encoding='ascii')
    for ordinal,item in enumerate(document['items']):
        identifier=f"{item['edition']:04}";checkpoint=states/(identifier+'.json');state=read_json(checkpoint) if resume and checkpoint.is_file() else None
        if state and state['candidate_fingerprint']!=item['genome']['fingerprint']:raise ValueError('Collection resume manifest mismatch '+identifier)
        if state:
            if state['canonical_grid']!=canonical_grid:raise ValueError('Cannot reinterpret a completed edition at a new grid')
            if any(not (root/name).is_file() or digest((root/name).read_bytes())!=sha for name,sha in state['files'].items()):raise ValueError('Completed edition export integrity mismatch '+identifier)
            g=state['genome'];record=state['record'];result=renderer.render(g);metrics,signature=quality(result,g);temporal=state['temporal'];uniqueness.accept(result,g,signature,item['edition'],temporal);loop=record['metadata']['loop_validation'];timings=state['timings'];encoding_seconds+=state.get('encoding_seconds',0)
        else:
            g=copy.deepcopy(item['genome']);g['grid']=[canonical_grid,canonical_grid];g['encryption']='AES-256-GCM' if item['protected'] else 'NONE';g=seal(g);candidate={**item,'genome':g};g,result,metrics,signature,repairs,payload,loop,temporal,timings,verdict=accepted_candidate(renderer,candidate,uniqueness,True,max_repairs);uniqueness.accept(result,g,signature,item['edition'],temporal)
            m=metadata(item,g,result,metrics,repairs,loop);m['uniqueness']=verdict;dna=protect_genome(g,key) if item['protected'] else g;record=dict(edition=item['edition'],ascii=result['ascii'],luminance=np.round(result['cells'][:,0],4).tolist(),metadata=m,dna=dna)
            if not item['protected']:record['genome']=g
            write_bytes(previews/(identifier+'.png'),renderer.png(result));gzip_json(animations/(identifier+'.frames.json.gz'),payload);video_time=0
            if videos and g['rarity']=='LEGENDARY':video_time=encode_video(renderer,g,payload,animations,identifier);encoding_seconds+=video_time
            files={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in [previews/(identifier+'.png'),animations/(identifier+'.frames.json.gz')]}
            if videos and g['rarity']=='LEGENDARY':
                for ext in ('mp4','webm'):p=animations/(identifier+'.'+ext);files[p.relative_to(root).as_posix()]=digest(p.read_bytes())
            # Protected plaintext genomes live only in ignored native/work.
            write_json(checkpoint,dict(version='3.0.0',candidate_fingerprint=item['genome']['fingerprint'],canonical_grid=canonical_grid,genome=g,record=record,temporal=temporal,timings=timings,encoding_seconds=video_time,files=files,completed=True,accepted=True))
        records.append(record);completed.append(item['edition']);frame_count+=loop['frame_count'];gpu_timings.extend(timings)
        if (ordinal+1)%100==0 or ordinal+1==3333:
            write_json(states/'progress.json',dict(version='3.0.0',completed=len(records),total=3333,frames=frame_count,elapsed_seconds=round(time.perf_counter()-started,2),last_edition=item['edition'],running=True))
            print(json.dumps(dict(mode='collection',completed=len(records),total=3333,frames=frame_count,elapsed_seconds=round(time.perf_counter()-started,2),device=renderer.status()['device'],pool_mb=round(renderer.status()['pool_bytes']/1048576,2))),flush=True)
    usage=Counter(a['id'] for row in records for a in row['metadata']['attributes']);supply=len(records)
    for row in records:
        m=row['metadata'];m['rarity_score']=round(sum(-math.log2(usage[a['id']]/supply) for a in m['attributes'])-math.log2(QUOTAS[m['rarity']]/supply),5)
    for rank,row in enumerate(sorted(records,key=lambda r:(-r['metadata']['rarity_score'],r['edition'])),1):row['metadata']['rank']=rank
    for offset in range(0,len(records),100):gzip_json(root/f'block-{offset//100:02}.json.gz',records[offset:offset+100])
    catalog=[row['metadata'] for row in records];write_json(root/'catalog.json',catalog);parts=export_archives(root,records)
    audit=audit_collection(root);audit.update(native_backend=renderer.backend,hardware=renderer.status(),visual_review_approved=True,canonical_resolution_frozen=True,canonical_grid=[canonical_grid,canonical_grid],legacy_collection_preserved=True,source_concepts_reachable=300,curated_traits=530,composite_recipes=1200,archive_parts=len(parts),export_video_policy='All 23 Legendary MP4/WebM standard; remaining editions native animated HTML and on-demand MP4/WebM via native CLI',gpu_per_frame_ms=dict(mean=float(np.mean(gpu_timings)),median=float(np.median(gpu_timings)),p95=float(np.percentile(gpu_timings,95))),elapsed_seconds=round(time.perf_counter()-started,3),software_video_encoding_seconds=round(encoding_seconds,3),motion_template_usage=[dict(kind=k[0],speed=k[1],amplitude_bin=k[2],count=n) for k,n in uniqueness.motion_templates.most_common()])
    write_json(reports/'collection-audit.json',audit,True);write_json(root/'release.json',dict(version='3.0.0',complete=True,accepted=3333,canonical_grid=[canonical_grid,canonical_grid],audit='/v3/reports/collection-audit.json',legacy_collection_preserved=True));write_json(states/'progress.json',dict(completed=3333,total=3333,running=False,passed=True));print(json.dumps(dict(mode='collection',passed=True,editions=3333,frames=frame_count,archive_parts=len(parts),elapsed_seconds=audit['elapsed_seconds'])),flush=True);return audit

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['experiments','collection'],required=True);parser.add_argument('--genomes',required=True);parser.add_argument('--output',default=str(REPO/'dist'/'v3'));parser.add_argument('--device',type=int,default=0);parser.add_argument('--animations',action='store_true');parser.add_argument('--approve-experiments',action='store_true');parser.add_argument('--canonical-grid',type=int,choices=[30,50],default=50);parser.add_argument('--no-resume',action='store_true');parser.add_argument('--max-repairs',type=int,default=6);args=parser.parse_args()
    if not 0<=args.max_repairs<=6:raise ValueError('Repair budget must be zero through six')
    document=read_json(args.genomes)
    if document.get('version')!='3.0.0' or len(document.get('items',[]))!=document.get('count'):raise ValueError('Invalid prepared genome manifest')
    if args.mode=='experiments' and not document.get('experimental') or args.mode=='collection' and document.get('experimental'):raise ValueError('Manifest kind does not match generation mode')
    output=Path(args.output).resolve()
    if output==(REPO/'dist').resolve() or output==(REPO/'dist'/'collection').resolve() or output==(NATIVE/'legacy').resolve():raise ValueError('Refusing to write into preserved legacy output')
    with Renderer('cuda',device=args.device) as renderer:
        if args.mode=='experiments':run_experiments(renderer,document,output,args.animations,not args.no_resume)
        else:run_collection(renderer,document,output,args.approve_experiments,args.canonical_grid,not args.no_resume,args.max_repairs)

if __name__=='__main__':main()
