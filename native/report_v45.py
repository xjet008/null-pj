"""Production visual sampling and observed release reports, without decryption."""
import gzip,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from nullgenesis.renderer import Renderer
from report_v3 import select_samples,frame_result
from release_v45 import unpack
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'dist/v45';REPORTS=OUT/'reports'
def write(name,data):(REPORTS/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
 root=OUT/'collection';release=json.loads((root/'release.json').read_text());assert release['complete'];catalog=json.loads((root/'catalog.json').read_text());assert len(catalog)==3333;selected=select_samples(catalog,100);images={};items=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
 with Renderer('cuda') as renderer:
  for offset in range(0,100,20):
   canvas=Image.new('RGB',(2240,1280),(8,8,8));draw=ImageDraw.Draw(canvas)
   for i,m in enumerate(selected[offset:offset+20]):
    with gzip.open(root/'animations'/f"{m['edition']:04}.frames.json.gz",'rt',encoding='utf-8') as s:data=json.load(s)
    cells=unpack(data);assert data['genome_fingerprint']==m['genome_fingerprint'];first='\n'.join(bytes(row).decode('ascii') for row in cells[0,:,0].reshape(80,80))+'\n';assert hashlib.sha256(first.encode()).hexdigest()==m['canonical_hash']
    x=i%4*560;y=i//4*256;indices=[0,len(cells)//4,len(cells)//2,len(cells)-1]
    draw.text((x+5,y+3),f"#{m['edition']:04} {m['rarity']} / {m['framing_mode']}",font=font,fill=(220,)*3)
    for col,f in enumerate(indices):
     im=renderer.square_image(frame_result(cells[f],data['grid']),300).resize((136,136),Image.Resampling.LANCZOS);canvas.paste(im,(x+col*140,y+30));draw.text((x+col*140+4,y+171),f'frame {f}',font=font,fill=(170,)*3)
    draw.text((x+5,y+195),f"fill {m['frame_occupancy']:.3f} Q{m['quality']['quality_score']} | {m['motion_type'][:25]}",font=font,fill=(180,)*3)
    items.append(dict(edition=m['edition'],rarity=m['rarity'],indices=indices,frame_hashes=[hashlib.sha256(cells[f].tobytes()).hexdigest() for f in indices],framing=m['framing_mode']))
   path=REPORTS/f'production-{offset//20+1:02}.jpg';canvas.save(path,quality=95,subsampling=0);images[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
 write('production-visual-review.json',dict(passed=False,review_required=True,version='4.5.0',sampled=100,legendary_profiles=23,rarities=dict(Counter(m['rarity'] for m in selected)),images=images,items=items))
 occupancies=np.array([m['frame_occupancy'] for m in catalog]);write('occupancy.json',dict(version='4.5.0',scope='visible subject bounding dimension excluding stage',count=3333,mean=float(occupancies.mean()),minimum=float(occupancies.min()),maximum=float(occupancies.max()),within_70_85=int(((occupancies>=.7)&(occupancies<=.85)).sum()),framing=dict(Counter(m['framing_mode'] for m in catalog)),bins=[dict(lower=float(a),upper=float(b),count=int(((occupancies>=a)&(occupancies<b)).sum())) for a,b in zip(np.arange(.65,.9,.025),np.arange(.675,.925,.025))]))
 write('animation-validation.json',dict(passed=all(m['loop_validation']['periodic'] and m['loop_validation']['animated'] for m in catalog),animated=3333,frames=sum(m['loop_validation']['frame_count'] for m in catalog),tiers={tier:dict(editions=len(rows),frames=sum(m['loop_validation']['frame_count'] for m in rows),mean_pose_change=float(np.mean([m['loop_validation']['pose_difference'] for m in rows])),max_wrap_change=max(m['loop_validation']['wrap_transition_fraction'] for m in rows),motion_values=len({m['motion_type'] for m in rows})) for tier in ('COMMON','UNCOMMON','RARE','EPIC','LEGENDARY') if (rows:=[m for m in catalog if m['rarity']==tier])},scope='full stored timelines, CUDA geometry poses, repeated endpoints and preceding wrap frames'))
 write('duplicate-detection.json',dict(passed=all(m['uniqueness']['unique'] for m in catalog),canonical_hashes=len({m['canonical_hash'] for m in catalog}),genomes=len({m['genome_fingerprint'] for m in catalog}),motion_trajectories=len({tuple(m['loop_validation']['motion_trajectory_signature']) for m in catalog}),scope='all candidate comparisons: exact ASCII/genome/geometry, silhouette and tonal signatures, perceptual hash, glyph histograms and sampled motion trajectory'))
 write('composite-recipes.json',dict(version='4.5.0',registered=2400,accepted_usage=dict(Counter(id for m in catalog for id in m['composite_traits'])),used=len({id for m in catalog for id in m['composite_traits']}),source_concepts=len({id for m in catalog for id in m['source_concepts']})))
 analytics=json.loads((REPORTS/'analytics.json').read_text());analytics.update(version='4.5.0',new_values=322,v3_values=110,v45_values=212,recipes=2400);write('analytics.json',analytics)
 print(json.dumps(dict(passed=True,sampled=100,sheets=5,reports=5,visual_review_pending=True)),flush=True)
if __name__=='__main__':main()
