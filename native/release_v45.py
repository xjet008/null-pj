"""Resumable, gated V4.5 regeneration; private keys never enter public exports."""
import base64,copy,gzip,hashlib,json,math,os,shutil,subprocess,time,zipfile
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal
from nullgenesis.codec import encrypt,decrypt
from quality_v45 import quality,repair
from experiment_v45 import candidate
from validate_v3 import Uniqueness,QUOTAS,digest,collection_analytics
from generate_v3 import frame_sequence,write_json,write_bytes,gzip_json,metadata as metadata3,animation_html

ROOT=Path(__file__).resolve().parent.parent;NATIVE=ROOT/'native';OUT=ROOT/'dist/v45'

def pack_lossless(payload):
    raw=np.frombuffer(base64.b64decode(payload['cells']),np.uint8).reshape(payload['frame_count'],-1);delta=np.empty_like(raw);delta[0]=raw[0];delta[1:]=raw[1:]^raw[:-1]
    candidate={**payload,'version':'4.5.0','encoding':'interleaved-xor-u8','presentation':[600,600],'cells':base64.b64encode(delta.tobytes()).decode()}
    old=len(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0));new=len(gzip.compress(json.dumps(candidate,separators=(',',':')).encode(),mtime=0))
    if new>=old:return {**payload,'version':'4.5.0','presentation':[600,600]},dict(encoding='interleaved-u8',raw_gzip_bytes=old,stored_gzip_bytes=old,saved_bytes=0)
    recovered=np.bitwise_xor.accumulate(delta,axis=0)
    if not np.array_equal(raw,recovered):raise ValueError('Lossless frame codec failed')
    return candidate,dict(encoding='interleaved-xor-u8',raw_gzip_bytes=old,stored_gzip_bytes=new,saved_bytes=old-new)

def unpack(data):
    raw=np.frombuffer(base64.b64decode(data['cells'],validate=True),np.uint8).reshape(data['frame_count'],-1)
    if data['encoding']=='interleaved-xor-u8':raw=np.bitwise_xor.accumulate(raw,axis=0)
    elif data['encoding']!='interleaved-u8':raise ValueError('Invalid frame encoding')
    return raw.reshape(data['frame_count'],-1,2)

def standalone(data):
    from gpu_html_v45 import document
    return document(data)

def videos(renderer,g,data,directory,identifier):
    import imageio_ffmpeg
    ffmpeg=shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe();frames=unpack(data);processes=[]
    try:
        for ext,args in [('mp4',['-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart']),('webm',['-c:v','libvpx-vp9','-crf','25','-b:v','0','-deadline','realtime','-cpu-used','5'])]:
            p=subprocess.Popen([ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','600x600','-r',str(g['animation']['fps']),'-i','pipe:0','-an',*args,str(directory/(identifier+'.'+ext))],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);processes.append(p)
        for values in frames:
            cells=np.zeros((len(values),12),np.float32);cells[:,0]=values[:,1];r=dict(glyph=values[:,0],cells=cells,grid=g['grid']);raw=np.asarray(renderer.square_image(r)).tobytes()
            for p in processes:p.stdin.write(raw)
        for p in processes:
            p.stdin.close();error=p.stderr.read().decode();code=p.wait()
            if code:raise RuntimeError('Video encoding failed: '+error)
    finally:
        for p in processes:
            if p.poll() is None:p.kill();p.wait()

def archives(root,records):
    directory=root/'exports';directory.mkdir(exist_ok=True);parts=[];entries=[];size=0;split=[];reused=0
    limit=23*1048576
    readme='NULL GENESIS V4.5 — native ASCII, square CUDA stills, animated HTML, lossless frames, metadata, quality record and owner-protected DNA. Private keys excluded. MP4/WebM encoding uses FFmpeg software.\n'
    def finish():
        nonlocal entries,size,reused
        if not entries:return
        p=directory/f'null-genesis-v45-part-{len(parts)+1:03}.zip'
        valid=False
        if p.exists() and p.stat().st_size<25*1048576:
            try:
                with zipfile.ZipFile(p) as existing:
                    expected=['README.txt']+[name for _,name,_ in entries]
                    valid=existing.namelist()==expected and existing.read('README.txt')==readme.encode() and all(existing.read(name)==data for _,name,data in entries)
            except (OSError,zipfile.BadZipFile,RuntimeError,KeyError):valid=False
        if valid:reused+=1
        else:
            temporary=p.with_suffix('.zip.tmp')
            with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
                archive.writestr('README.txt',readme)
                for _,name,data in entries:archive.writestr(name,data)
            if temporary.stat().st_size>=25*1048576:raise ValueError('Export archive exceeds public asset budget')
            os.replace(temporary,p)
        parts.append(dict(file=p.name,url='/v45/collection/exports/'+p.name,bytes=p.stat().st_size,sha256=digest(p.read_bytes()),first_edition=entries[0][0],last_edition=entries[-1][0]))
        if len(parts)%20==0:print(json.dumps(dict(archive_parts=len(parts),packaged_through=entries[-1][0],reused_parts=reused)),flush=True)
        entries=[];size=0
    for row in records:
        e=row['edition'];id=f'{e:04}';fp=root/'animations'/(id+'.frames.json.gz')
        with gzip.open(fp,'rt',encoding='utf-8') as stream:data=json.load(stream)
        files=[('ascii.txt',row['ascii'].encode('ascii')),('preview.png',(root/'previews'/(id+'.png')).read_bytes()),('metadata.json',json.dumps(row['metadata'],separators=(',',':')).encode()),('genome.dna.json',json.dumps(row['dna'],separators=(',',':')).encode()),('quality.json',(root/'quality'/(id+'.json')).read_bytes()),('animation.frames.json.gz',fp.read_bytes()),('animation.html',standalone(data).encode())]
        for ext in ('mp4','webm'):
            p=root/'animations'/(id+'.'+ext)
            if p.exists():files.append(('animation.'+ext,p.read_bytes()))
        estimate=sum(len(v) for _,v in files)
        if entries and size+estimate>limit:finish()
        if estimate>limit:split.append(e)
        for name,data in files:
            if len(data)>limit:raise ValueError('Individual export exceeds conservative part budget: '+id+'/'+name)
            if entries and size+len(data)>limit:finish()
            entries.append((e,id+'/'+name,data));size+=len(data)
    finish()
    expected={part['file'] for part in parts}
    for stale in directory.glob('null-genesis-v45-part-*.zip'):
        if stale.name not in expected:
            if stale.resolve().parent!=directory.resolve() or ROOT.resolve() not in stale.resolve().parents:raise ValueError('Unsafe stale archive path')
            stale.unlink()
    write_json(directory/'index.json',dict(version='4.5.0',count=len(records),owner_keys_included=False,parts=parts,split_editions=split,extraction='Extract all parts into the same folder; large video editions can span parts.'))
    return parts

def audit(root):
    records=[]
    for p in sorted(root.glob('block-*.json.gz')):
        with gzip.open(p,'rt',encoding='utf-8') as stream:records.extend(json.load(stream))
    if len(records)!=3333 or sorted(r['edition'] for r in records)!=list(range(1,3334)):raise ValueError('Incomplete release')
    rarities=Counter(r['metadata']['rarity'] for r in records)
    if dict(rarities)!=QUOTAS:raise ValueError('Rarity supply changed')
    exact=set();genomes=set();total=0;protected=0;profiles=set();occupancies=[];sources=set();categories=set();recipes=set()
    for row in records:
        m=row['metadata'];e=row['edition'];grid=m['native_grid'];lines=row['ascii'].splitlines();w=grid[0]
        if len(lines)!=w or any(len(x)!=w or any(not 32<=ord(c)<=126 for c in x) for x in lines):raise ValueError('Invalid native ASCII')
        if digest(row['ascii'])!=m['canonical_hash'] or m['canonical_hash'] in exact or m['genome_fingerprint'] in genomes:raise ValueError('Duplicate or corrupted canonical')
        if len(m['attributes'])!=11 or not m['quality']['accepted']:raise ValueError('Invalid traits/quality')
        with Image.open(root/'previews'/f'{e:04}.png') as im:
            if im.size!=(600,600):raise ValueError('Non-square presentation')
            pixels=np.asarray(im)
            if not np.array_equal(pixels[:,:,0],pixels[:,:,1]) or not np.array_equal(pixels[:,:,1],pixels[:,:,2]):raise ValueError('Chromatic art')
        with gzip.open(root/'animations'/f'{e:04}.frames.json.gz','rt',encoding='utf-8') as s:data=json.load(s)
        cells=unpack(data)
        if cells.shape!=(m['animation']['fps']*m['animation']['seconds'],w*w,2) or np.any((cells[:,:,0]<32)|(cells[:,:,0]>126)):raise ValueError('Invalid timeline')
        first='\n'.join(bytes(v).decode('ascii') for v in cells[0,:,0].reshape(w,w))+'\n'
        if first!=row['ascii'] or data['genome_fingerprint']!=m['genome_fingerprint'] or not np.any(cells[1:]!=cells[0]):raise ValueError('Static or mismatched animation')
        if not m['loop_validation']['periodic'] or not m['loop_validation']['animated']:raise ValueError('Loop proof missing')
        q=json.loads((root/'quality'/f'{e:04}.json').read_text())
        if q['genome_fingerprint']!=m['genome_fingerprint'] or q['metrics']!=m['quality']:raise ValueError('Quality identity mismatch')
        if row['dna'].get('algorithm'):
            protected+=1
            if row['dna']['version']!=45 or row['dna']['fingerprint']!=m['genome_fingerprint'] or 'genome' in row:raise ValueError('Protected DNA leakage or identity mismatch')
            if base64.b64decode(row['dna']['aad'])!=('NULL-GENESIS/web-genome/v45/'+m['genome_fingerprint']).encode():raise ValueError('Invalid authentication context')
        else:
            from nullgenesis.genome import validate_genome
            validate_genome(row['genome']);validate_genome(row['dna'])
        if m['rarity']=='LEGENDARY':
            profiles.add(m['animation']['profile'])
            for ext in ('mp4','webm'):
                if not (root/'animations'/f'{e:04}.{ext}').exists():raise ValueError('Missing Legend video')
        total+=len(cells);exact.add(m['canonical_hash']);genomes.add(m['genome_fingerprint']);occupancies.append(m['quality']['dimension_occupancy']);sources.update(m['source_concepts']);categories.update(a['id'] for a in m['attributes']);recipes.update(m['composite_traits'])
    if profiles!=set(range(23)) or len(sources)!=300 or len(recipes)<2000:raise ValueError('Legend, source or recipe coverage incomplete')
    if list(root.rglob('*.key')):raise ValueError('Private key in public release')
    return dict(version='4.5.0',passed=True,editions=3333,animated=3333,frames=total,rarity=dict(rarities),unique_ascii=len(exact),unique_genomes=len(genomes),protected=protected,legendary_profiles=23,native_grid=grid,presentation=[600,600],curated_values=742,operative_new_values=212,recipe_coverage=len(recipes),source_coverage=len(sources),category_values_used=len(categories),occupancy_mean=float(np.mean(occupancies)),occupancy_70_85=sum(.7<=v<=.85 for v in occupancies),owner_keys_public=False,visual_review_required=True)

def finish_release(root,records,renderer,timings,codecs,started):
    parts=archives(root,records);verification=audit(root)
    verification.update(hardware=renderer.status(),visual_review_approved=False,archive_parts=len(parts),elapsed_seconds=time.perf_counter()-started,gpu_per_frame_ms={'median':float(np.median(timings)),'p95':float(np.percentile(timings,95))},lossless_saved_bytes=sum(c['saved_bytes'] for c in codecs),legacy_preserved=True,v3_preserved=True)
    write_json(OUT/'reports/collection-audit.json',verification);analytics=collection_analytics(root,ROOT/'dist/data/traits-v45.json');write_json(OUT/'reports/analytics.json',analytics)
    write_json(root/'release.json',dict(version='4.5.0',complete=True,accepted=3333,canonical_grid=records[0]['metadata']['native_grid'],presentation=[600,600],audit='/v45/reports/collection-audit.json'))
    write_json(NATIVE/'work/collection-v45-state/progress.json',dict(completed=3333,total=3333,running=False,passed=True));print(json.dumps({k:v for k,v in verification.items() if k!='hardware'}),flush=True)


def finalize_existing(document):
    root=OUT/'collection';records=[];timings=[];codecs=[];started=time.perf_counter();first=None
    for p in sorted(root.glob('block-*.json.gz')):
        with gzip.open(p,'rt',encoding='utf-8') as stream:records.extend(json.load(stream))
    if len(records)!=3333:raise ValueError('Finalization requires all 3333 generated records')
    for item,row in zip(document['items'],records):
        state=json.loads((NATIVE/'work/collection-v45-state'/(item['id']+'.json')).read_text())
        if state['candidate']!=item['genome']['fingerprint'] or state['grid']!=80 or state['genome']['fingerprint']!=row['metadata']['genome_fingerprint']:raise ValueError('Finalization candidate mismatch')
        actual=copy.deepcopy(row);expected=copy.deepcopy(state['record'])
        for record in (actual,expected):
            for key in ('rank','rarity_score'):record['metadata'].pop(key,None)
        if actual!=expected:raise ValueError('Finalization public/checkpoint mismatch')
        for path,expected_hash in state['files'].items():
            if digest((root/path).read_bytes())!=expected_hash:raise ValueError('Finalization export integrity failure')
        if not row['metadata']['quality']['accepted'] or not row['metadata']['uniqueness']['unique']:raise ValueError('Unaccepted checkpoint')
        timings.extend(state['timings']);codecs.append(state['codec'])
        if first is None:first=state['genome']
    with Renderer('cuda') as renderer:
        result=renderer.render(first)
        if result['ascii']!=records[0]['ascii'] or renderer.square_png(result)!=(root/'previews/0001.png').read_bytes():raise ValueError('Finalization CUDA golden mismatch')
        finish_release(root,records,renderer,timings,codecs,started)


def main():
    report=json.loads((OUT/'reports/experiments.json').read_text());
    if not report.get('passed') or not report.get('visual_review_approved') or not report.get('canonical_grid'):raise ValueError('Complete and visually review the 200 experimental timelines before regeneration')
    document=json.loads((NATIVE/'work/collection-v45.json').read_text());grid=report['canonical_grid'][0]
    if len(document['items'])!=3333 or Counter(x['genome']['rarity'] for x in document['items'])!=QUOTAS:raise ValueError('Incorrect prepared supply')
    import sys
    if '--finalize-only' in sys.argv:
        finalize_existing(document);return
    root=OUT/'collection';root.mkdir(parents=True,exist_ok=True)
    for p in ('previews','animations','quality'):(root/p).mkdir(exist_ok=True)
    key_path=NATIVE/'private/v45-owner.key';key_path.parent.mkdir(exist_ok=True)
    if not key_path.exists():
        with key_path.open('xb') as s:s.write(os.urandom(32))
    key=key_path.read_bytes()
    if len(key)!=32:raise ValueError('Invalid V4.5 key length')
    states=NATIVE/'work/collection-v45-state';states.mkdir(exist_ok=True);records=[];uniqueness=Uniqueness(3333);started=time.perf_counter();timings=[];codecs=[]
    with Renderer('cuda') as renderer:
        for ordinal,item in enumerate(document['items']):
            id=item['id'];checkpoint=states/(id+'.json');cached=json.loads(checkpoint.read_text()) if checkpoint.exists() else None
            if cached:
                if cached['candidate']!=item['genome']['fingerprint'] or cached['grid']!=grid:raise ValueError('Resume candidate mismatch')
                if any(not (root/p).exists() or digest((root/p).read_bytes())!=h for p,h in cached['files'].items()):raise ValueError('Resume export integrity failure')
                g=cached['genome'];record=cached['record'];result=renderer.render(g);q,signature=quality(result,g);trajectory=cached['trajectory'];verdict=uniqueness.inspect(result,g,signature,trajectory);uniqueness.accept(result,g,signature,item['edition'],trajectory);frame_times=cached['timings'];codec=cached['codec']
            else:
                item=copy.deepcopy(item);item['genome']['grid']=[grid,grid];item['genome']['encryption']='AES-256-GCM' if item['protected'] else 'NONE';item['genome']=seal(item['genome']);g,result,q,signature,repairs=candidate(renderer,item)
                for attempt in range(7):
                    verdict=uniqueness.inspect(result,g,signature)
                    temporal=False
                    if verdict['unique'] and q['accepted']:
                        payload,loop,trajectory,frame_times=frame_sequence(renderer,g,result);verdict=uniqueness.inspect(result,g,signature,trajectory)
                        if verdict['unique']:break
                        temporal=True
                    if attempt==6:raise ValueError('Candidate '+id+' exhausted repair budget: '+json.dumps(dict(quality=q['reasons'],uniqueness=verdict)))
                    g,result,q,signature,logs,actions=repair(renderer,g,q,attempt,duplicate=not verdict['unique'],temporal=temporal);repairs.extend(logs)
                uniqueness.accept(result,g,signature,item['edition'],trajectory);payload,codec=pack_lossless(payload);q['checks']['motion_readability']={'periodic':loop['periodic'],'animated':loop['animated'],'wrap_fraction':loop['wrap_transition_fraction'],'maximum_transition':loop['max_transition_fraction']}
                m=metadata3(item,g,result,q,repairs,loop);m.update(release='v45',canonical_renderer='cuda-sdf-4.5.0',native_grid=g['grid'],presentation_size=[600,600],encoder_version='4.5.0',framing_mode=g['composition']['mode'],frame_occupancy=q['dimension_occupancy'],silhouette_clarity=q['checks']['shape_clarity'],derived_composite_identity=g['recipe']['id'],generation_method=next(t['value'] for t in g['categories'] if t['trait_type']=='Method'),motion_type=g['motion']['name'],palette=next(t['value'] for t in g['categories'] if t['trait_type']=='Palette'),stage=next(t['value'] for t in g['categories'] if t['trait_type']=='Stage'),composition=g['composition'],density_budget=g['density_budget'],uniqueness=verdict,frame_codec=codec,export_formats=['ASCII','PNG','HTML','MP4','WebM','ZIP','DNA','quality JSON']);
                m['repair_log']=[dict(attempt=x.get('attempt'),reason=x.get('reason'),path=x.get('path'),outcome=x.get('outcome'),previous_score=x.get('pre',{}).get('quality_score'),updated_score=x.get('post',{}).get('quality_score')) for x in repairs]
                m['quality_record']='/v45/collection/quality/'+id+'.json'
                for k in ('image','animation_url'):m[k]=m[k].replace('/v3/','/v45/')
                m['media']={k:v.replace('/v3/','/v45/') if isinstance(v,str) else v for k,v in m['media'].items()};dna=encrypt(g,key) if item['protected'] else g
                if item['protected'] and decrypt(dna,key)['genome']['fingerprint']!=g['fingerprint']:raise ValueError('Encrypted round-trip failed')
                record=dict(edition=item['edition'],ascii=result['ascii'],luminance=np.round(result['cells'][:,0],4).tolist(),metadata=m,dna=dna)
                if not item['protected']:record['genome']=g
                write_bytes(root/'previews'/(id+'.png'),renderer.square_png(result));gzip_json(root/'animations'/(id+'.frames.json.gz'),payload);write_json(root/'quality'/(id+'.json'),dict(version='4.5.0',genome_fingerprint=g['fingerprint'],metrics=q,repair_log=repairs,loop=loop))
                if g['rarity']=='LEGENDARY':videos(renderer,g,payload,root/'animations',id)
                paths=[root/'previews'/(id+'.png'),root/'animations'/(id+'.frames.json.gz'),root/'quality'/(id+'.json')]
                if g['rarity']=='LEGENDARY':paths.extend(root/'animations'/(id+'.'+ext) for ext in ('mp4','webm'))
                write_json(checkpoint,dict(candidate=document['items'][ordinal]['genome']['fingerprint'],grid=grid,genome=g,record=record,trajectory=trajectory,timings=frame_times,codec=codec,files={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in paths}))
            records.append(record);timings.extend(frame_times);codecs.append(codec)
            if (ordinal+1)%100==0 or ordinal+1==3333:
                status=dict(version='4.5.0',completed=ordinal+1,total=3333,frames=len(timings),elapsed_seconds=round(time.perf_counter()-started,2),running=True);write_json(states/'progress.json',status);print(json.dumps(status),flush=True)
        usage=Counter(a['id'] for r in records for a in r['metadata']['attributes'])
        for r in records:r['metadata']['rarity_score']=round(sum(-math.log2(usage[a['id']]/3333) for a in r['metadata']['attributes'])-math.log2(QUOTAS[r['metadata']['rarity']]/3333),5)
        for rank,r in enumerate(sorted(records,key=lambda x:(-x['metadata']['rarity_score'],x['edition'])),1):r['metadata']['rank']=rank
        for offset in range(0,3333,100):gzip_json(root/f'block-{offset//100:02}.json.gz',records[offset:offset+100])
        write_json(root/'catalog.json',[r['metadata'] for r in records]);finish_release(root,records,renderer,timings,codecs,started)
if __name__=='__main__':main()
