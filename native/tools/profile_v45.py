"""Measure warm startup and resident-buffer reuse without speed assumptions."""
import gzip,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.renderer import Renderer
def main():
 with gzip.open(ROOT/'dist/v45/experiments/E025.json.gz','rt',encoding='utf-8') as s:g=json.load(s)['genome']
 with Renderer('cuda') as renderer:
  first=renderer.render(g);renderer.square_image(first);before=renderer.allocations;times=[]
  for i in range(12):
   r=renderer.render(g);assert r['ascii']==first['ascii'];renderer.square_image(r);times.append(r['gpu_ms'])
  status=renderer.status();assert renderer.allocations==before
  report=dict(passed=True,device=status['device'],warm_compile_cache_hit=status['compile_cache_hit'],startup_ms=status['startup_ms'],compile_ms=status['compile_ms'],resident_pool_bytes=status['pool_bytes'],allocations=before,repeated_stills=12,additional_allocations=renderer.allocations-before,median_gpu_ms=float(np.median(times)),scope='Measured while production and local studio share this GPU; no universal speedup claim')
 (ROOT/'dist/v45/reports/performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
