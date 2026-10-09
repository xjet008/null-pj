"""Golden CUDA comparison against the committed V3 renderer and public art."""
import gzip,json,subprocess,sys,types
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.renderer import Renderer
def committed(path):return subprocess.run(['C:/Program Files/Git/cmd/git.exe','-c','safe.directory='+ROOT.as_posix(),'show','05ce4b9b338414086198083eaf768ee5ebb69353:'+path],cwd=ROOT,capture_output=True,check=True).stdout.decode()
def main():
 source=committed('native/nullgenesis/renderer.py');source=source.replace("(ROOT/'render.cu').read_text(encoding='utf-8')+'\\n'+(ROOT/'motion.cu').read_text(encoding='utf-8')",'baseline_source')
 module=types.ModuleType('nullgenesis.compat_original');module.__file__=str(ROOT/'native/nullgenesis/renderer.py');module.__package__='nullgenesis';module.baseline_source=committed('native/nullgenesis/render.cu')+'\n'+committed('native/nullgenesis/motion.cu');exec(compile(source,module.__file__,'exec'),module.__dict__)
 selected=[]
 for p in sorted((ROOT/'dist/v3/collection').glob('block-*.json.gz')):
  with gzip.open(p,'rt',encoding='utf-8') as s:rows=json.load(s)
  plain=[r for r in rows if 'genome' in r]
  if plain:selected.append(plain[len(plain)//2])
  if len(selected)==16:break
 with Renderer('cuda') as new,module.Renderer('cuda') as old:
  for row in selected:
   g=row['genome'];a=new.render(g);b=old.render(g)
   if a['ascii']!=b['ascii'] or not np.array_equal(a['cells'],b['cells']) or a['canonical_hash']!=row['metadata']['canonical_hash']:raise ValueError('V3 golden regression '+str(row['edition']))
  examples=[]
  for id in ('E001','E032','E071','E144'):
   with gzip.open(ROOT/'dist/v45/experiments'/(id+'.json.gz'),'rt',encoding='utf-8') as s:r=json.load(s)
   a=new.render(r['genome'])
   if a['ascii']!=r['ascii'] or new.square_png(a)!=(ROOT/'dist/v45/experiments'/(id+'.png')).read_bytes():raise ValueError('V4.5 frozen render regression '+id)
   examples.append(id)
  report=dict(passed=True,v3_exact_native_cells=len(selected),v3_public_canonical_matches=len(selected),v45_exact_ascii_and_png=examples,compile_cache_hit=new.status()['compile_cache_hit'],startup_ms=new.startup_ms)
 (ROOT/'dist/v45/reports/compatibility.json').write_text(json.dumps(report));print(json.dumps(report))
if __name__=='__main__':main()
