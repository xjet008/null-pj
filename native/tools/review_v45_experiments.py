"""Complete grid images and expose cached timeline phases for visual review."""
import base64,copy,gzip,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal

def main():
 out=ROOT/'dist/v45/experiments';reports=ROOT/'dist/v45/reports';report=json.loads((reports/'experiments.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
 benchmarks={(r['id'],r['grid']):r for r in report['comparisons']}
 with Renderer('cuda') as renderer:
  for ordinal,item in enumerate(report['items']):
   with gzip.open(out/(item['id']+'.json.gz'),'rt',encoding='utf-8') as s:record=json.load(s)
   for grid in (30,50,64,80,96,120):
    path=out/(item['id']+f'-{grid}.png')
    if path.exists():continue
    g=copy.deepcopy(record['genome']);g['grid']=[grid,grid];g=seal(g);result=renderer.render(g)
    if result['canonical_hash']!=benchmarks[(item['id'],grid)]['canonical_hash']:raise ValueError('Frozen grid identity changed')
    path.write_bytes(renderer.square_png(result,300))
   if (ordinal+1)%50==0:print(json.dumps(dict(grid_visuals_completed=ordinal+1,total=200)),flush=True)
  ids=['E001','E024','E025','E026','E027'];canvas=Image.new('RGB',(1800,1600),(8,8,8));draw=ImageDraw.Draw(canvas)
  for row,id in enumerate(ids):
   with gzip.open(out/(id+'.frames.json.gz'),'rt',encoding='utf-8') as s:data=json.load(s)
   cells=np.frombuffer(base64.b64decode(data['cells']),np.uint8).reshape(data['frame_count'],-1,2)
   for col,f in enumerate([0,len(cells)//4,len(cells)//2,3*len(cells)//4,len(cells)-2,len(cells)-1]):
    values=cells[f];packed=np.zeros((len(values),12),np.float32);packed[:,0]=values[:,1];im=renderer.square_image(dict(glyph=values[:,0],cells=packed,grid=data['grid']),300);canvas.paste(im,(col*300,row*320+20));draw.text((col*300+5,row*320),f'{id} frame {f}',font=font,fill=(210,)*3)
  canvas.save(reports/'experiment-motion-phases.jpg',quality=95)
 canvas=Image.new('RGB',(1800,1280),(8,8,8));draw=ImageDraw.Draw(canvas)
 for row,id in enumerate(['E001','E007','E024','E026']):
  for col,grid in enumerate((30,50,64,80,96,120)):
   with Image.open(out/(id+f'-{grid}.png')) as im:canvas.paste(im,(col*300,row*320+20))
   draw.text((col*300+5,row*320),f'{id} {grid}x{grid}',font=font,fill=(210,)*3)
 canvas.save(reports/'native-grid-comparison.jpg',quality=95)
 print(json.dumps(dict(passed=True,grid_images=1200,motion_tiers=5)),flush=True)
if __name__=='__main__':main()
