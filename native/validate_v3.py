"""Measured V3 quality, visual/temporal duplicate detection and release auditing.

Scores are repeatable engineering proxies. Contact-sheet inspection is a separate,
explicit release gate; this module never claims that a numeric score proves art.
"""
from __future__ import annotations
import argparse
import base64
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

CATEGORIES=('Back','Body','Eyewear','Features','Form','Headwear','Mask','Method','Motion','Palette','Stage')
QUOTAS={'COMMON':1900,'UNCOMMON':900,'RARE':400,'EPIC':110,'LEGENDARY':23}

def digest(data):
    if isinstance(data,str):data=data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def json_digest(value):
    return digest(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False))

def _components(mask):
    h,w=mask.shape;seen=np.zeros_like(mask,bool);largest=0;components=0
    for yy,xx in np.argwhere(mask):
        yy=int(yy);xx=int(xx)
        if seen[yy,xx]:continue
        components+=1;queue=[(yy,xx)];seen[yy,xx]=True;n=0
        while n<len(queue):
            y,x=queue[n];n+=1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    ny,nx=y+dy,x+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;queue.append((ny,nx))
        largest=max(largest,n)
    return largest,components

def quality(result,genome):
    values=np.asarray(result['packet'],np.float32);w,h=result['grid'];n=w*h
    if values.shape!=(n,12) or not np.isfinite(values).all():raise ValueError('Malformed or non-finite native cell packet')
    glyph=values[:,0].astype(np.uint8)
    if np.any(values[:,0]!=glyph) or np.any((glyph<32)|(glyph>126)) or np.any((values[:,1]<0)|(values[:,1]>255)):raise ValueError('Invalid ASCII glyph or non-grayscale luminance')
    mask=(glyph!=32)&(values[:,9]>.5);shape=mask.reshape(h,w);occupied=int(mask.sum());density=occupied/n
    tone=np.where(mask,values[:,1]/255,0).reshape(h,w);ys,xs=np.nonzero(shape)
    center=[float(xs.mean()/(w-1)),float(ys.mean()/(h-1))] if occupied else [.5,.5]
    balance=max(0,1-math.hypot(center[0]-.5,center[1]-.5)*2)
    border=int(shape[0].sum()+shape[-1].sum()+shape[1:-1,0].sum()+shape[1:-1,-1].sum());clipping=border/max(1,occupied)
    largest,components=_components(shape);coherence=largest/max(1,occupied)
    contrast=float(values[mask,1].std()/255) if occupied else 0
    depth=float(np.ptp(values[mask,8])) if occupied else 0
    normals=values[mask,2:5].mean(axis=0) if occupied else np.zeros(3);normal_spread=float(np.clip(1-np.linalg.norm(normals),0,1))
    abstract=any(k in genome.get('appearance','') for k in ('CHAOS','VOID','ANOMALY','FRAGMENT','DUALITY','ABSTRACT','SCATTERED'))
    target=.20 if abstract else .36;density_fit=max(0,1-abs(density-target)/.48)
    score=100*(.23*density_fit+.20*balance+.18*(1-min(1,clipping*12))+.14*(max(.35,coherence) if abstract else coherence)+.13*min(1,contrast*5)+.07*min(1,depth/.9)+.05*min(1,normal_spread*3)) if occupied else 0
    edges=np.concatenate(((shape[:,1:]!=shape[:,:-1]).ravel(),(shape[1:]!=shape[:-1]).ravel()))
    edge_tone=np.concatenate((np.abs(tone[:,1:]-tone[:,:-1]).ravel(),np.abs(tone[1:]-tone[:-1]).ravel()))
    reasons=[]
    if occupied<=n*.05:reasons.append('insufficient focal geometry')
    if density>=.82:reasons.append('insufficient negative space')
    if clipping>=.12:reasons.append('clipped primary silhouette')
    if score<48:reasons.append('composition score below 48')
    if depth<.015:reasons.append('insufficient geometric depth')
    metrics=dict(quality_score=round(score,2),density=round(density,4),occupied_cells=occupied,components=components,coherence=round(coherence,4),center=[round(x,4) for x in center],balance=round(balance,4),clipping=round(clipping,4),tonal_contrast=round(contrast,4),depth_span=round(depth,4),normal_spread=round(normal_spread,4),edge_separation=round(float(edge_tone[edges].mean()) if edges.any() else 0,4),distinct_glyphs=int(len(np.unique(glyph[mask]))),visible_objects=int(len(np.unique(values[mask,10]))),grid=[w,h],accepted=not reasons,reasons=reasons,visual_review_required=True)
    blocks=[];silhouette=[]
    for by in range(8):
        for bx in range(8):
            ys=slice(by*h//8,(by+1)*h//8);xs=slice(bx*w//8,(bx+1)*w//8);blocks.append(float(tone[ys,xs].mean()));silhouette.append(float(shape[ys,xs].mean()))
    k=np.arange(8)[:,None];x=np.arange(w)[None,:];basis=np.cos(np.pi*(x+.5)*k/w);dct=basis@tone@basis.T;phash=(dct>np.median(dct.ravel()[1:])).ravel()
    hist=np.bincount(glyph-32,minlength=95).astype(np.float32)/n
    geometry=[[r[0],*[round(v*20) for v in r[1:10]],r[10]] for r in genome['scene']]
    signature=dict(tone=np.array(blocks,np.float32),silhouette=np.array(silhouette,np.float32),mask=mask,brightness=tone.ravel().astype(np.float32),hist=hist,phash=phash,geometry=json_digest(geometry),motion=json_digest(genome.get('motion',{})))
    return metrics,signature

def repair(genome,metrics,attempt,duplicate=False):
    from nullgenesis.genome import seal
    if not 0<=attempt<6:raise ValueError('Finite repair budget exceeded')
    g=json.loads(json.dumps(genome));actions=[]
    if metrics['clipping']>.025 or metrics['density']>.65:g['config'][0]=min(8,g['config'][0]*1.16);actions.append('expand_camera_to_recover_silhouette')
    elif metrics['density']<.14:g['config'][0]=max(1.6,g['config'][0]*.84);actions.append('enlarge_focal_structure')
    if metrics['balance']<.75:
        solids=[r for r in g['scene'] if not r[10] and r[14]!=4]
        if solids:
            cx=sum(r[1] for r in solids)/len(solids);cy=sum(r[2] for r in solids)/len(solids)
            for row in g['scene']:row[1]-=cx*.65;row[2]-=cy*.65
            actions.append('recenter_primary_geometry')
    if metrics['tonal_contrast']<.10:g['config'][16]=min(1.8,g['config'][16]+.12);g['rendering']['fill']=max(.12,g['rendering'].get('fill',.22)-.03);actions.append('separate_surface_tones')
    if duplicate:
        # Geometry/camera change rather than different random glyphs. The exact
        # candidate sequence is recorded and repeated identically on resume.
        direction=1 if attempt%2==0 else -1;g['config'][3]+=direction*(.12+.03*attempt)
        for row in g['scene']:
            if row[14]!=4:row[1]*=1+.025*(attempt+1);row[3]*=1-.018*(attempt+1)
        actions.append('separate_duplicate_structure_and_pose')
    if not actions:g['config'][3]+=(1 if attempt%2==0 else -1)*.12;actions.append('adjust_view_for_depth_separation')
    g.setdefault('provenance',{}).setdefault('native_repairs',[]).append(dict(attempt=attempt+1,actions=actions))
    return seal(g),actions

def frame_distance(a,b):
    x=np.asarray(a['packet']);y=np.asarray(b['packet']);changed=(x[:,0]!=y[:,0])|(np.abs(x[:,1]-y[:,1])>1)
    return dict(changed=int(changed.sum()),fraction=float(changed.mean()),tone=float(np.abs(x[:,1]-y[:,1]).mean()/255),geometry=float(np.linalg.norm(x[:,5:8]-y[:,5:8],axis=1).mean()))

def loop_samples(canonical,quarter,end,previous=None):
    seam=frame_distance(canonical,end);moving=frame_distance(canonical,quarter)
    wrap=frame_distance(previous,canonical) if previous is not None else None
    return dict(periodic=seam['changed']==0 and seam['geometry']<1e-6,animated=moving['changed']>0 and moving['geometry']>1e-7,seam_cells=seam['changed'],moving_cells=moving['changed'],pose_difference=round(moving['fraction'],5),pose_geometry=round(moving['geometry'],6),wrap_transition_fraction=round(wrap['fraction'],5) if wrap else None,wrap_geometry_step=round(wrap['geometry'],6) if wrap else None,sampling='canonical, quarter, repeated end'+(', previous boundary' if wrap else ''))

class Uniqueness:
    def __init__(self,capacity=3333):
        self.exact=set();self.genomes=set();self.geometry=set();self.items=[];self.tone=np.empty((capacity,64),np.float32);self.shape=np.empty_like(self.tone);self.motion_templates=Counter()
    def inspect(self,result,g,signature,temporal=None):
        if result['canonical_hash'] in self.exact:return dict(unique=False,reason='identical ASCII grid')
        if g['fingerprint'] in self.genomes:return dict(unique=False,reason='identical genome')
        if signature['geometry'] in self.geometry:return dict(unique=False,reason='identical structural geometry')
        n=len(self.items)
        if not n:return dict(unique=True,nearest_edition=None)
        shape=np.abs(self.shape[:n]-signature['silhouette']).mean(axis=1);tone=((self.tone[:n]-signature['tone'])**2).mean(axis=1);nearest=np.argsort(shape+np.sqrt(tone))[:24];closest=None
        for i in nearest:
            old,edition,old_temporal=self.items[int(i)];hamming=int(np.count_nonzero(old['phash']!=signature['phash']));union=np.logical_or(old['mask'],signature['mask']).sum();iou=float(np.logical_and(old['mask'],signature['mask']).sum()/max(1,union));x,y=old['brightness'],signature['brightness'];mx,my=float(x.mean()),float(y.mean());vx,vy=float(x.var()),float(y.var());cov=float(((x-mx)*(y-my)).mean());ssim=((2*mx*my+.0001)*(2*cov+.0009))/((mx*mx+my*my+.0001)*(vx+vy+.0009));glyph=float(np.abs(old['hist']-signature['hist']).sum()/2)
            comparison=dict(nearest_edition=edition,silhouette_distance=round(float(shape[i]),6),tonal_mse=round(float(tone[i]),6),silhouette_iou=round(iou,6),ssim=round(ssim,6),perceptual_hamming=hamming,glyph_histogram_distance=round(glyph,6))
            if closest is None or shape[i]<closest['silhouette_distance']:closest=comparison
            if shape[i]<.008 and tone[i]<.00035 and hamming<=2:return dict(unique=False,reason='perceptual silhouette/tone duplicate',**comparison)
            if iou>.985 and ssim>.99 and glyph<.015:return dict(unique=False,reason='grayscale spatial duplicate',**comparison)
            if temporal is not None and old_temporal is not None and shape[i]<.04 and tone[i]<.004 and np.abs(np.asarray(temporal)-old_temporal).mean()<.004:return dict(unique=False,reason='animated visual duplicate',**comparison)
        return dict(unique=True,**(closest or {}))
    def accept(self,result,g,signature,edition,temporal=None):
        verdict=self.inspect(result,g,signature,temporal)
        if not verdict['unique']:raise ValueError('Cannot accept duplicate: '+str(verdict))
        n=len(self.items);self.tone[n]=signature['tone'];self.shape[n]=signature['silhouette'];self.items.append((signature,edition,np.asarray(temporal) if temporal is not None else None));self.exact.add(result['canonical_hash']);self.genomes.add(g['fingerprint']);self.geometry.add(signature['geometry']);m=g['motion'];self.motion_templates[(m.get('kind',m.get('type')),m['speed'],round(m.get('amplitude',m.get('intensity')),1))]+=1;return verdict

def unpack_animation(path):
    with gzip.open(path,'rt',encoding='utf-8') as stream:data=json.load(stream)
    if data.get('encoding')!='interleaved-u8':raise ValueError('Unsupported compact animation encoding')
    w,h=data['grid'];n=w*h;total=data['fps']*data['seconds'];raw=base64.b64decode(data['cells'],validate=True)
    if data['frame_count']!=total or len(raw)!=total*n*2:raise ValueError('Animation frame count/byte length mismatch')
    cells=np.frombuffer(raw,np.uint8).reshape(total,n,2)
    if np.any((cells[:,:,0]<32)|(cells[:,:,0]>126)):raise ValueError('Invalid animation glyphs')
    return data,cells

def audit_collection(root,expected=3333):
    root=Path(root);catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'));records=[]
    for path in sorted(root.glob('block-*.json.gz')):
        with gzip.open(path,'rt',encoding='utf-8') as stream:records.extend(json.load(stream))
    if len(catalog)!=expected or len(records)!=expected:raise ValueError('Collection is incomplete')
    if sorted(r['edition'] for r in records)!=list(range(1,expected+1)):raise ValueError('Duplicate or missing editions')
    rarities=Counter(m['rarity'] for m in catalog)
    if expected==3333 and dict(rarities)!=QUOTAS:raise ValueError('Rarity supply quota mismatch')
    exact=set();genomes=set();animations=0;protected=0;legend_profiles=set();grids=Counter();counts=Counter();category_counts=Counter();source_counts=Counter();timeline_frames=0
    for row in records:
        e=row['edition'];m=row['metadata'];w,h=m['render_resolution'];lines=row['ascii'].splitlines()
        if len(lines)!=h or any(len(x)!=w or any(not 32<=ord(c)<=126 for c in x) for x in lines):raise ValueError('Malformed native ASCII edition '+str(e))
        if digest(row['ascii'])!=m['canonical_hash'] or m['canonical_hash'] in exact:raise ValueError('Identical or corrupted ASCII edition '+str(e))
        if m['genome_fingerprint'] in genomes:raise ValueError('Duplicate genome edition '+str(e))
        levels=np.asarray(row['luminance']);
        if levels.shape!=(w*h,) or not np.isfinite(levels).all() or levels.min()<0 or levels.max()>255:raise ValueError('Invalid grayscale data')
        attrs=m['attributes'];order=[a['trait_type'] for a in attrs]
        if order!=list(CATEGORIES) or any(not a.get('id') or a['value'] in ('None','none','') for a in attrs):raise ValueError('Exactly eleven operative ordered NFT categories are required')
        counts.update(m['traits']);category_counts.update(a['id'] for a in attrs);source_counts.update(m['base_concepts'])
        if not set(m['base_concepts'])<=set(m['traits']) or not set(m['modifiers'].values())<=set(m['traits']) or not {a['id'] for a in attrs}<=set(m['traits']):raise ValueError('Missing operative source/modifier/category IDs in public trait index')
        data,frames=unpack_animation(root/'animations'/f'{e:04}.frames.json.gz');first='\n'.join(bytes(a).decode('ascii') for a in frames[0,:,0].reshape(h,w))+'\n'
        if first!=row['ascii'] or data['genome_fingerprint']!=m['genome_fingerprint'] or data['grid']!=[w,h]:raise ValueError('Canonical animation/DNA identity mismatch')
        if not np.any(frames[1:]!=frames[0]):raise ValueError('Static artwork marked animated')
        if not m.get('loop_validation',{}).get('periodic') or not m['loop_validation'].get('animated'):raise ValueError('Animation loop validation missing')
        preview=root/'previews'/f'{e:04}.png'
        with Image.open(preview) as im:
            pixels=np.asarray(im.convert('RGB'))
            if not np.array_equal(pixels[:,:,0],pixels[:,:,1]) or not np.array_equal(pixels[:,:,1],pixels[:,:,2]):raise ValueError('Chromatic preview detected')
        encrypted=row['dna'].get('algorithm')=='AES-256-GCM'
        if encrypted:
            protected+=1
            if 'genome' in row or 'scene' in row or 'config' in row or any(k in row['dna'] for k in ('key','owner_key','genome')):raise ValueError('Protected plaintext leaked into public collection')
            if row['dna']['version']!=3 or row['dna']['fingerprint']!=m['genome_fingerprint'] or base64.b64decode(row['dna']['aad'])!=('NULL-GENESIS/web-genome/v3/'+m['genome_fingerprint']).encode():raise ValueError('Invalid V3 authenticated envelope')
        else:
            from nullgenesis.genome import validate_genome
            validate_genome(row['genome']);validate_genome(row['dna'])
        if not m['quality']['accepted']:raise ValueError('Unaccepted candidate marked released')
        if m['rarity']=='LEGENDARY':
            legend_profiles.add(m['animation']['profile'])
            for ext in ('mp4','webm'):
                if not (root/'animations'/f'{e:04}.{ext}').is_file():raise ValueError('Legendary '+ext+' export missing')
        exact.add(m['canonical_hash']);genomes.add(m['genome_fingerprint']);animations+=1;timeline_frames+=len(frames);grids.update([w])
    if expected==3333 and legend_profiles!=set(range(23)):raise ValueError('Legendary identity profiles incomplete')
    if expected==3333 and len(grids)!=1:raise ValueError('Release resolution has not been frozen to a single native grid')
    if expected==3333 and len(source_counts)!=300:raise ValueError('One or more original source concepts are absent from the accepted collection')
    if expected==3333 and sorted(m['rank'] for m in catalog)!=list(range(1,3334)):raise ValueError('Rarity rankings are incomplete or duplicate')
    if list(root.rglob('*.key')):raise ValueError('Private encryption key found in release directory')
    return dict(version='3.0.0',passed=True,editions=expected,rarity=dict(rarities),unique_ascii=len(exact),unique_genomes=len(genomes),animated=animations,frames=timeline_frames,protected=protected,legendary_profiles=len(legend_profiles),resolution=dict(grids),trait_usage=dict(counts),category_usage=dict(category_counts),source_usage=dict(source_counts),owner_keys_public=False,validation_scope='native dimensions/grayscale/DNA/envelope/frame counts/canonical frame/loop evidence/quality/quota/media/eleven ordered attributes/source reachability/ranking; visual approval recorded separately')

def collection_analytics(root,registry_path=None):
    root=Path(root);catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'));registry_path=Path(registry_path) if registry_path else root.parents[1]/'data'/'traits-v3.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));supply=len(catalog);registered={t['id']:t for t in registry['traits']};counts=Counter(t for m in catalog for t in set(m['traits']));unknown=set(counts)-set(registered)
    if unknown:raise ValueError('Unregistered public trait identifiers: '+str(sorted(unknown)))
    traits=[]
    for t in registry['traits']:
        matching=[m for m in catalog if t['id'] in m['traits']];sources=Counter(c for m in matching for c in m['base_concepts']);operators=Counter(c for m in matching for c in m['composite_traits']);rarity=Counter(m['rarity'] for m in matching)
        traits.append(dict(id=t['id'],label=t['label'],category=t['category'],count=counts[t['id']],percentage=round(counts[t['id']]/max(1,supply)*100,2),rarity=dict(rarity),applicable_rarities=['COMMON','UNCOMMON','RARE','EPIC','LEGENDARY'],source_relationships=[dict(id=k,count=n) for k,n in sources.most_common(8)],composite_relationships=dict(operators),examples=[dict(edition=m['edition'],image=m['image']) for m in matching[:3]],relationship_scope='observed accepted-edition co-occurrence'))
    categories=[dict(name=name,traits=[t for t in traits if t['category']==name]) for name in CATEGORIES]
    return dict(version='3.0.0',accepted=supply,rarity=dict(Counter(m['rarity'] for m in catalog)),family={'SYNTHESIS':supply},source_library_usage=dict(Counter(library for m in catalog for library in set(m['source_libraries']))),source_concept_usage=dict(Counter(c for m in catalog for c in m['base_concepts'])),traits=traits,categories=categories,curated_traits=registry['curated_count'],original_values_retained=420,new_values=110,unique_combinations=len({tuple(sorted(m['traits'])) for m in catalog}),unused_traits=[t['id'] for t in traits if not t['count']],quality_mean=round(float(np.mean([m['quality']['quality_score'] for m in catalog])),4),quality_minimum=min(m['quality']['quality_score'] for m in catalog),animated=sum(bool(m['animated']) for m in catalog),native_grids=dict(Counter(str(m['render_resolution']) for m in catalog)),appearance=dict(Counter(m['appearance'] for m in catalog)),rendering_profiles=dict(Counter(m['rendering_profile'] for m in catalog)),source_family_quotas=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--expected',type=int,default=3333);parser.add_argument('--report');parser.add_argument('--analytics');parser.add_argument('--registry');args=parser.parse_args();report=audit_collection(args.directory,args.expected)
    if args.report:
        target=Path(args.report);previous=json.loads(target.read_text(encoding='utf-8')) if target.is_file() else {};target.write_text(json.dumps({**previous,**report},indent=2)+'\n',encoding='utf-8')
    if args.analytics:Path(args.analytics).write_text(json.dumps(collection_analytics(args.directory,args.registry),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
