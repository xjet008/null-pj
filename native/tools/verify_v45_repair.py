"""Regression: near-duplicate 615 must be repaired without weakening thresholds."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.renderer import Renderer
from quality_v45 import quality,repair
from experiment_v45 import candidate
from validate_v3 import Uniqueness
def main():
 old=json.loads((ROOT/'native/work/collection-v45-state/0015.json').read_text());item=json.loads((ROOT/'native/work/collection-v45.json').read_text())['items'][614];records=[]
 with Renderer('cuda') as renderer:
  r=renderer.render(old['genome']);q,s=quality(r,old['genome']);u=Uniqueness(2);u.accept(r,old['genome'],s,15,old['trajectory']);g,result,q,s,logs=candidate(renderer,item);before=u.inspect(result,g,s);(ROOT/'dist/v45/reports/repair-before.png').write_bytes(renderer.square_png(result));attempts=0
  for attempt in range(6):
   if u.inspect(result,g,s)['unique'] and q['accepted']:break
   g,result,q,s,extra,actions=repair(renderer,g,q,attempt,True);records.extend(extra);attempts+=1
  after=u.inspect(result,g,s);assert after['unique'] and q['accepted'];(ROOT/'dist/v45/reports/repair-after.png').write_bytes(renderer.square_png(result))
 report=dict(passed=True,edition=615,nearest_edition=15,initial=before,final=after,attempts=attempts,quality_score=q['quality_score'],occupancy=q['dimension_occupancy'],deterministic_repair_log=records,thresholds_unchanged=True);(ROOT/'dist/v45/reports/repair-regression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='deterministic_repair_log'}))
if __name__=='__main__':main()
