"""Audit the immutable V3 release without accessing private genomes or keys."""
import gzip,json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
def audit():
    rows=[]
    for path in sorted((ROOT/'dist/v3/collection').glob('block-*.json.gz')):
        with gzip.open(path,'rt',encoding='utf-8') as stream:records=json.load(stream)
        for record in records:
            mask=np.array([[c!=' ' for c in line] for line in record['ascii'].splitlines()]);ys,xs=np.nonzero(mask);h,w=mask.shape
            span=max((xs.max()-xs.min()+1)/w,(ys.max()-ys.min()+1)/h) if len(xs) else 0
            with Image.open(ROOT/'dist/v3/collection/previews'/f"{record['edition']:04}.png") as im:size=list(im.size)
            rows.append(dict(edition=record['edition'],rarity=record['metadata']['rarity'],dimension_occupancy=round(float(span),4),cell_density=round(float(mask.mean()),4),center=[round(float(xs.mean()/w),4),round(float(ys.mean()/h),4)],presentation=size))
    values=np.array([r['dimension_occupancy'] for r in rows]);summary=dict(version='4.5.0-baseline',release='V3',count=len(rows),native_grid=[50,50],dimension_occupancy_mean=float(values.mean()),dimension_occupancy_median=float(np.median(values)),below_70_percent=int((values<.7).sum()),in_70_to_85_percent=int(((values>=.7)&(values<=.85)).sum()),above_85_percent=int((values>.85).sum()),square_presentations=sum(r['presentation'][0]==r['presentation'][1] for r in rows),scope='visible glyph bounding box including stage; conservative baseline, no semantic recognition',items=rows)
    out=ROOT/'dist/v45/reports/baseline.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(summary,separators=(',',':')),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k!='items'}))
if __name__=='__main__':audit()
