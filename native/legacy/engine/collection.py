import json,time,hashlib,threading,collections
from pathlib import Path
import numpy as np
from engine.genome import CONFIG,REGISTRY,TRAITS,FAMILIES,RARITIES,allocation,make_genome,validate_genome,canonical,digest
from engine.renderer import ascii_text,validate_buffer
from validators.quality import quality,features,Uniqueness
from exporters.formats import atomic_json,png_bytes,animation
from encryption.codec import owner_key,encrypt,decrypt
class Collection:
    def __init__(self,root,renderer):
        self.root=Path(root);self.renderer=renderer;self.lock=threading.RLock();self.job_lock=threading.Lock();self.stop=threading.Event();self.thread=None
        self.index={};self.unique=Uniqueness();self.rejected=0;self.started=None;self.errors=[];self.current=None
        for folder in ['ascii','metadata','previews','animations','genomes','cells']:(self.root/'collection'/folder).mkdir(parents=True,exist_ok=True)
        self._load()
    def path(self,folder,e,ext):return self.root/'collection'/folder/f'{e:04}.{ext}'
    def load_genome(self,e):
        data=json.loads(self.path('genomes',e,'dna.json').read_text(encoding='utf-8'))
        if data.get('algorithm')=='AES-256-GCM':return decrypt(data,owner_key(self.root))['genome']
        return validate_genome(data)
    def result(self,e):
        data=np.load(self.path('cells',e,'npz'));return {k:data[k] for k in ['glyph','cells','cfg','scene']}|dict(geometry_signature=self.index[e]['geometry_signature'],backend=self.index[e]['backend'])
    def _load(self):
        cache=self.root/'reports/collection-index.json';feature_cache=self.root/'reports/collection-features.npz'
        files=list((self.root/'collection/metadata').glob('*.json'))
        if cache.exists() and feature_cache.exists():
            records=json.loads(cache.read_text(encoding='utf-8'))
            if len(records)==len(files) and all(p.stat().st_mtime<=cache.stat().st_mtime for p in files):
                with np.load(feature_cache) as archive:data={key:archive[key] for key in ['mask','bright','coarse','hist','phash']}
                for n,m in enumerate(records):
                    e=m['edition'];self.index[e]=m
                    f={key:data[key][n] for key in ['mask','bright','coarse','hist','phash']}
                    self.unique.items.append((f,e));self.unique.coarse[n]=f['coarse'];self.unique.grids.add(m['canonical_hash']);self.unique.genomes.add(m['genome_fingerprint']);self.unique.geometry.add(m['geometry_signature']);self.rejected+=m['mutation']
                return
        for p in sorted((self.root/'collection/metadata').glob('*.json')):
            m=json.loads(p.read_text(encoding='utf-8'));e=m['edition'];r=self.result_from_metadata(m)
            text=self.path('ascii',e,'txt').read_bytes()
            if hashlib.sha256(text).hexdigest()!=m['canonical_hash']:raise ValueError(f'Corrupt edition {e}: canonical hash')
            if ascii_text(r['glyph']).encode()!=text:raise ValueError(f'Corrupt edition {e}: ASCII/cell mismatch')
            self.index[e]=m;self.unique.items.append((features(r),e));n=len(self.unique.items)-1;self.unique.coarse[n]=self.unique.items[n][0]['coarse'];self.unique.grids.add(m['canonical_hash']);self.unique.genomes.add(m['genome_fingerprint']);self.unique.geometry.add(m['geometry_signature']);self.rejected+=m['mutation']
    def result_from_metadata(self,m):
        e=m['edition'];data=np.load(self.path('cells',e,'npz'));r={k:data[k] for k in ['glyph','cells','cfg','scene']};r['geometry_signature']=m['geometry_signature'];r['backend']=m['backend'];validate_buffer(r['glyph'],r['cells']);return r
    def save_cache(self):
        if not self.index:return
        features_list=[f for f,e in self.unique.items]
        target=self.root/'reports/collection-features.npz';temporary=target.with_suffix('.tmp.npz')
        np.savez_compressed(temporary,**{key:np.array([f[key] for f in features_list]) for key in ['mask','bright','coarse','hist','phash']})
        temporary.replace(target)
        atomic_json(self.root/'reports/collection-index.json',[self.index[e] for f,e in self.unique.items])
    def status(self):
        with self.lock:
            rar=collections.Counter(m['rarity'] for m in self.index.values());fam=collections.Counter(m['family'] for m in self.index.values())
            return dict(accepted=len(self.index),remaining=3333-len(self.index),rejected=self.rejected,running=bool(self.thread and self.thread.is_alive()),current=self.current,
                rarity={k:dict(count=rar[k],quota=v) for k,v in CONFIG['rarities'].items()},family={k:dict(count=fam[k],quota=v) for k,v in CONFIG['families'].items()},
                errors=self.errors[-5:],elapsed_seconds=round(time.perf_counter()-self.started,2) if self.started else None)
    def start(self,limit=3333,video=True):
        with self.job_lock:
            if self.thread and self.thread.is_alive():return self.status()
            self.stop.clear();self.errors=[];self.thread=threading.Thread(target=self.run,args=(int(limit),video),daemon=True);self.thread.start()
        return self.status()
    def run(self,limit=3333,video=True):
        self.started=time.perf_counter();render_ms=[];gpu_ms=[];export_ms=[];start_count=len(self.index)
        try:
            key=owner_key(self.root,create=True)
            pending=[p for p in allocation() if p['edition'] not in self.index];batch_cache={}
            for plan in pending:
                e=plan['edition']
                if e in self.index:continue
                if self.stop.is_set() or len(self.index)>=limit:break
                self.current=e
                if e not in batch_cache:
                    position=next(i for i,p in enumerate(pending) if p['edition']==e);plans=pending[position:position+CONFIG['batch_size']]
                    candidates=[make_genome(**p,mutation=0) for p in plans]
                    batch_cache={p['edition']:(g,r) for p,g,r in zip(plans,candidates,self.renderer.render_batch(candidates,reveal=True))}
                for mutation in range(120):
                    if mutation==0:g,base=batch_cache.pop(e)
                    else:g=make_genome(**plan,mutation=mutation);base=self.renderer.render(g,reveal=True)
                    r=base if g['animation']['enabled'] or g['appearance'] not in ['FRAGMENTED','APPARENT CHAOS'] else self.renderer.frame(base,g,0,static_mode=1 if g['appearance']=='FRAGMENTED' else 2)
                    ok,scores,reasons,f=quality(r,g,base)
                    if ok:ok,reason,nearest=self.unique.check(r,g,f)
                    else:reason=', '.join(reasons);nearest={}
                    if ok:break
                    self.rejected+=1
                    with (self.root/'reports/rejections.jsonl').open('a',encoding='utf-8') as log:log.write(json.dumps(dict(edition=e,mutation=mutation,reason=reason,metrics=nearest))+'\n')
                else:raise RuntimeError(f'Edition {e}: exhausted deterministic mutations')
                text=ascii_text(r['glyph']).encode();self.path('ascii',e,'txt').write_bytes(text)
                np.savez_compressed(self.path('cells',e,'npz'),glyph=r['glyph'],cells=r['cells'],cfg=r['cfg'],scene=r['scene'])
                data=encrypt(g,key,f'Entity {e}: {g["fingerprint"]}') if g['encryption']=='AES-256-GCM' else g
                atomic_json(self.path('genomes',e,'dna.json'),data)
                t=time.perf_counter();self.path('previews',e,'png').write_bytes(png_bytes(self.renderer,r))
                anim=animation(self.renderer,base,g,self.root/'collection/animations',video) if g['animation']['enabled'] else None
                export_ms.append((time.perf_counter()-t)*1000)
                ids=[g['style'],g['secondary_style'],*g['modifiers'].values()];ids=[id for id in ids if id]
                m=dict(edition=e,name=f'NULL GENESIS #{e:04}',family=g['family'],subject=g['subject'],rarity=g['rarity'],primary_style=TRAITS[g['style']]['label'],style_id=g['style'],secondary_style=TRAITS[g['secondary_style']]['label'] if g['secondary_style'] else None,secondary_style_id=g['secondary_style'],traits=ids,modifiers=g['modifiers'],appearance=g['appearance'],seed=g['seed'],genome_version=g['genome_version'],render_version=g['render_version'],geometry_signature=r['geometry_signature'],genome_fingerprint=g['fingerprint'],canonical_hash=hashlib.sha256(text).hexdigest(),animation=anim,animation_profile=g['animation']['name'],encryption_mode=g['encryption'],grid=[30,30],backend=r['backend'],quality=scores,uniqueness=nearest,mutation=mutation,repairs=g['repairs'],operators=base['operators'],anatomy_components=base['anatomy_labels'],performance=dict(wall_ms=base['wall_ms'],gpu_ms=base['gpu_ms'],batch_size=base.get('batch_size',1),timing_basis=base.get('timing_basis','single-artwork kernel time')),font=self.renderer.font['font'],font_sha256=self.renderer.font['font_sha256'],output_files=dict(ascii=f'ascii/{e:04}.txt',genome=f'genomes/{e:04}.dna.json',preview=f'previews/{e:04}.png',cells=f'cells/{e:04}.npz'),provenance='Local procedural ASCII; hashes assert integrity, not blockchain ownership.')
                # Metadata is the final commit marker. Partial output is overwritten on resume.
                atomic_json(self.path('metadata',e,'json'),m)
                with self.lock:self.index[e]=m;self.unique.accept(r,g,f)
                render_ms.append(base['wall_ms']);gpu_ms.append(base['gpu_ms'])
                if e%16==0:atomic_json(self.root/'reports/progress.json',self.status())
                print(f'Accepted {len(self.index)}/3333 · edition {e} · {g["family"]} · {g["rarity"]} · GPU {base["gpu_ms"]:.1f} ms',flush=True)
            self.current=None
            self.analytics()
            report=dict(backend=self.renderer.status(),new_editions=len(self.index)-start_count,accepted=len(self.index),rejected=self.rejected,wall_seconds=round(time.perf_counter()-self.started,3),mean_render_ms=float(np.mean(render_ms)) if render_ms else None,mean_gpu_ms=float(np.mean(gpu_ms)) if gpu_ms else None,mean_export_ms=float(np.mean(export_ms)) if export_ms else None,resumable=True)
            atomic_json(self.root/'reports/generation-benchmark.json',report)
            if len(self.index)==3333:self.audit()
        except Exception as e:self.errors.append(str(e));print('Generation failed:',e,flush=True);atomic_json(self.root/'reports/generation-error.json',dict(error=str(e),progress=self.status()))
    def analytics(self):
        with self.lock:items=list(self.index.values())
        counts=collections.Counter(t for m in items for t in m['traits']);co=collections.Counter()
        for m in items:
            for a in m['traits']:
                for b in m['traits']:
                    if a<b:co[(a,b)]+=1
        scores={m['edition']:sum(len(items)/counts[t] for t in m['traits']) for m in items}
        rank={e:i+1 for i,(e,_) in enumerate(sorted(scores.items(),key=lambda x:(-x[1],x[0])))}
        for m in items:m['rank']=rank[m['edition']];m['trait_frequency_score']=round(scores[m['edition']],3);atomic_json(self.path('metadata',m['edition'],'json'),m)
        data=dict(accepted=len(items),rarity=dict(collections.Counter(m['rarity'] for m in items)),family=dict(collections.Counter(m['family'] for m in items)),traits=[dict(id=t['id'],label=t['label'],category=t['category'],count=counts[t['id']],percentage=round(100*counts[t['id']]/max(len(items),1),4)) for t in REGISTRY],unused_traits=[t['id'] for t in REGISTRY if not counts[t['id']]],cooccurrence=[dict(a=a,b=b,count=n) for (a,b),n in co.most_common(120)],unique_combinations=len({tuple(m['traits']) for m in items}),exclusions=['one camera, topology, lighting and glyph grammar per genome','static Common/Uncommon/Rare/Epic motion','sparse texture compatibility repairs'],quality_mean=float(np.mean([m['quality']['quality_score'] for m in items])) if items else None,ranking_method='sum of inverse observed trait frequencies; ranks are separate from fixed rarity tiers')
        atomic_json(self.root/'reports/analytics.json',data)
        self.save_cache()
        return data
    def audit(self):
        errors=[];hashes=set();genomes=set();geometry=set();rar=collections.Counter();fam=collections.Counter();legend_profiles=set();frames_checked=0
        for e,m in sorted(self.index.items()):
            r=self.result(e);text=self.path('ascii',e,'txt').read_bytes();rows=text.decode('ascii').splitlines()
            if len(rows)!=30 or any(len(row)!=30 for row in rows):errors.append(f'{e}: dimensions')
            if hashlib.sha256(text).hexdigest()!=m['canonical_hash']:errors.append(f'{e}: hash')
            for value,seen,label in [(m['canonical_hash'],hashes,'grid'),(m['genome_fingerprint'],genomes,'DNA'),(m['geometry_signature'],geometry,'geometry')]:
                if value in seen:errors.append(f'{e}: duplicate {label}')
                seen.add(value)
            g=self.load_genome(e);validate_genome(g);validate_buffer(r['glyph'],r['cells']);rar[m['rarity']]+=1;fam[m['family']]+=1
            if any(t not in TRAITS for t in m['traits']):errors.append(f'{e}: unsupported trait')
            if m['rarity']=='LEGENDARY':
                legend_profiles.add(m['animation_profile']);d=json.loads(self.path('animations',e,'frames.json').read_text())
                if len(d['frames'])!=d['fps']*d['seconds']:errors.append(f'{e}: frame count')
                for frame,levels in zip(d['frames'],d['luminance']):
                    rows=frame.splitlines();frames_checked+=1
                    if len(rows)!=30 or any(len(row)!=30 for row in rows) or any(ord(c)<32 or ord(c)>126 for row in rows for c in row) or len(levels)!=900 or any(v<0 or v>255 for v in levels):errors.append(f'{e}: animation cell integrity')
                if len(set(d['frames']))<15:errors.append(f'{e}: missing structural motion')
        if len(self.index)!=3333:errors.append('Supply must be 3333')
        if dict(rar)!=CONFIG['rarities']:errors.append('Rarity quotas')
        if dict(fam)!=CONFIG['families']:errors.append('Family quotas')
        if len(legend_profiles)!=23:errors.append('23 unique Legendary profiles')
        report=dict(passed=not errors,errors=errors,supply=len(self.index),families=dict(fam),rarities=dict(rar),unique_ascii=len(hashes),unique_genomes=len(genomes),unique_geometry=len(geometry),legendary_profiles=len(legend_profiles),animation_frames_checked=frames_checked,registry_values=len(REGISTRY),ascii_grid=[30,30],color_space='strict grayscale')
        atomic_json(self.root/'reports/collection-audit.json',report);return report
