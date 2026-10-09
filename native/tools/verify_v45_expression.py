"""Compare actual CUDA glyph/gray poses for all new curated values."""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.renderer import Renderer
from quality_v45 import fit
def main():
 items=json.loads((ROOT/'native/work/expression-v45.json').read_text())['items'];groups=defaultdict(list)
 with Renderer('cuda') as renderer:
  for item in items:
   g,result,q,signature,repairs=fit(renderer,item['genome']);posed=renderer.render(g,g['animation']['fps']*g['animation']['seconds']//4);h=hashlib.sha256(result['packet'][:,:2].tobytes()+posed['packet'][:,:2].tobytes()).hexdigest();groups[item['category']].append(dict(id=item['id'],actual_pose_signature=h,visible_objects=q['visible_objects']))
 summary={category:dict(values=len(rows),distinct_rendered_pose_signatures=len({r['actual_pose_signature'] for r in rows})) for category,rows in groups.items()};passed=all(row['values']==row['distinct_rendered_pose_signatures'] for row in summary.values());report=dict(passed=passed,operative_new_values=212,backend='CUDA',comparison='actual canonical and quarter-loop glyph/gray packets; names and metadata excluded',categories=summary,items=[r for rows in groups.values() for r in rows]);(ROOT/'dist/v45/reports/trait-expression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='items'}),flush=True)
 if not passed:raise ValueError('Indistinguishable CUDA trait fixture outputs')
if __name__=='__main__':main()
