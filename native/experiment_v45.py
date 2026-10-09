"""Two hundred CUDA timelines plus six-grid comparisons; no production writes."""
import copy,json,time,gzip
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal
from quality_v45 import fit,quality,repair
from generate_v3 import frame_sequence,write_json,write_bytes,gzip_json
ROOT=Path(__file__).resolve().parent.parent

def candidate(renderer,item):
    g,result,metrics,signature,repairs=fit(renderer,item['genome'])
    for attempt in range(6):
        if metrics['accepted']:return g,result,metrics,signature,repairs
        previous=metrics;g,result,metrics,signature,logs,actions=repair(renderer,g,metrics,attempt);repairs.extend(logs);repairs.append(dict(reason=previous['reasons'],pre=previous,post=metrics,path=actions,outcome='accepted' if metrics['accepted'] else 'retry'))
    raise ValueError('Candidate failed '+item['id']+': '+json.dumps(metrics))

def contacts(items,out):
    paths=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
    for start in range(0,len(items),20):
        group=items[start:start+20];canvas=Image.new('RGB',(1600,1400),(10,10,10));draw=ImageDraw.Draw(canvas)
        for i,item in enumerate(group):
            x=i%4*400;y=i//4*280
            for j,name in enumerate((item['id']+'-old.png',item['id']+'.png')):
                with Image.open(out/name) as im:im.thumbnail((190,244));canvas.paste(im,(x+j*200+(190-im.width)//2,y+22))
            draw.text((x+5,y+3),f"{item['id']} {item['rarity']} / V3 -> V4.5",font=font,fill=(210,)*3)
            draw.text((x+5,y+259),f"{item['framing']} | fill {item['quality']['dimension_occupancy']:.2f}",font=font,fill=(155,)*3)
        path=out.parent/'reports'/f'comparison-{start//20+1:02}.jpg';canvas.save(path,quality=94);paths.append('/v45/reports/'+path.name)
    return paths

def main():
    document=json.loads((ROOT/'native/work/experiments-v45.json').read_text());out=ROOT/'dist/v45/experiments';out.mkdir(parents=True,exist_ok=True);reports=out.parent/'reports';reports.mkdir(exist_ok=True);started=time.perf_counter();rows=[];bench=[]
    with Renderer('cuda') as renderer:
        for i,item in enumerate(document['items']):
            checkpoint=ROOT/'native/work/experiment-v45-state'/(item['id']+'.json');checkpoint.parent.mkdir(exist_ok=True)
            if checkpoint.exists():
                saved=json.loads(checkpoint.read_text());
                if saved['candidate']==item['genome']['fingerprint']:
                    rows.append(saved['row']);bench.extend(saved['bench']);continue
            g,result,q,signature,repairs=candidate(renderer,item);native=[]
            old=renderer.render(item['baseline']);write_bytes(out/(item['id']+'-old.png'),renderer.png(old));write_bytes(out/(item['id']+'.png'),renderer.square_png(result))
            for grid in (30,50,64,80,96,120):
                v=copy.deepcopy(g);v['grid']=[grid,grid];v=seal(v);r=renderer.render(v);m,_=quality(r,v)
                if i<32:write_bytes(out/(item['id']+f'-{grid}.png'),renderer.square_png(r,300))
                native.append(dict(id=item['id'],grid=grid,gpu_ms=r['gpu_ms'],wall_ms=r['wall_ms'],quality=m,canonical_hash=r['canonical_hash']))
            payload,loop,trajectory,timings=frame_sequence(renderer,g,result);payload.update(version='4.5.0',presentation=[600,600]);q['checks']['motion_readability']={'periodic':loop['periodic'],'animated':loop['animated'],'max_transition_fraction':loop['max_transition_fraction']}
            record=dict(genome=g,dna=g,ascii=result['ascii'],luminance=np.round(result['cells'][:,0],4).tolist(),metadata=dict(id=item['id'],rarity=g['rarity'],grid=g['grid'],render_resolution=g['grid'],canonical_hash=result['canonical_hash'],attributes=g['categories'],quality=q,repair_log=repairs,loop_validation=loop,presentation_size=[600,600],animation_url='/v45/viewer.html?experiment='+item['id']))
            gzip_json(out/(item['id']+'.json.gz'),record);gzip_json(out/(item['id']+'.frames.json.gz'),payload)
            row=dict(id=item['id'],rarity=g['rarity'],framing=g['composition']['mode'],quality=q,repairs=len(repairs),loop=loop,frame_gpu_ms=timings,old_gpu_ms=old['gpu_ms'],genome_fingerprint=g['fingerprint'],preview='/v45/experiments/'+item['id']+'.png',animation_url=record['metadata']['animation_url'],attributes=g['categories'])
            write_json(checkpoint,dict(candidate=item['genome']['fingerprint'],row=row,bench=native));rows.append(row);bench.extend(native)
            if (i+1)%10==0:print(json.dumps(dict(completed=i+1,total=200,elapsed=round(time.perf_counter()-started,1))),flush=True)
        sheets=contacts(rows,out);summary=[]
        for grid in (30,50,64,80,96,120):
            values=[r for r in bench if r['grid']==grid];summary.append(dict(grid=grid,median_gpu_ms=float(np.median([r['gpu_ms'] for r in values])),mean_quality=float(np.mean([r['quality']['quality_score'] for r in values])),mean_visible_objects=float(np.mean([r['quality']['visible_objects'] for r in values])),mean_glyphs=float(np.mean([r['quality']['distinct_glyphs'] for r in values])),mean_occupancy=float(np.mean([r['quality']['dimension_occupancy'] for r in values]))))
        report=dict(version='4.5.0',passed=len(rows)==200 and all(r['quality']['accepted'] and r['loop']['animated'] and r['loop']['periodic'] for r in rows),experiment_count=200,full_timelines=True,visual_review_approved=False,hardware=renderer.status(),elapsed_seconds=time.perf_counter()-started,grids=summary,contact_sheets=sheets,items=rows,comparisons=bench,rarities=dict(Counter(r['rarity'] for r in rows)),canonical_grid=None)
        write_json(reports/'experiments.json',report);write_json(out/'index.json',dict(version='4.5.0',items=rows,contact_sheets=sheets));print(json.dumps({k:v for k,v in report.items() if k not in ('items','comparisons','hardware')}),flush=True)
if __name__=='__main__':main()
