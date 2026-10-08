"""Compare CUDA conservative-field acceleration against its uncullled reference."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal
def verify(input_path,output=None):
    data=json.loads(Path(input_path).read_text(encoding='utf-8'));items=data if isinstance(data,list) else data.get('items',data.get('genomes',[data]));genomes=[item.get('genome',item) for item in items]
    rng=np.random.default_rng(813733);points=rng.uniform([-2.7,-2.7,-1.8],[2.7,2.7,1.8],(2048,3)).astype(np.float32);results=[]
    with Renderer('cuda') as r:
        for ordinal,g in enumerate(genomes):
            for index in [0,(g['animation']['fps']*g['animation']['seconds'])//3]:
                r.render(g,index);d=r.driver;d.activate();p=r._buffer('probe_points',points.nbytes).upload(points);values=r._buffer('probe_values',len(points)*16)
                with d.measure():d.enqueue('probe_field',len(points),p,r.pool['posed_scene'],len(g['scene']),r.pool['config'],values,len(points))
                out=values.download(np.float32,(len(points),4));exact=np.array_equal(out[:,0],out[:,1]) and np.array_equal(out[:,2],out[:,3]);maximum=float(abs(out[:,0]-out[:,1]).max())
                if not exact:raise AssertionError(f'Primitive lower bound changed field for item{ordinal} frame{index}: delta{maximum}')
                results.append(dict(item=ordinal,frame=index,samples=len(points),exact=exact,maximum_field_error=maximum))
        report=dict(version='3.0.0',device=r.status()['device'],input_sha256=hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),scenes=len(genomes),probes=sum(v['samples'] for v in results),field_and_owner_identical=True,pose_indices=['canonical','one-third loop'],results=results)
    path=Path(output or ROOT/'reports/cuda-field-regression.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output');a=p.parse_args();verify(a.input,a.output)

