import sys, os, threading, time, math, hashlib
from pathlib import Path
from contextlib import ExitStack
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.genome import CONFIG,MODES,RARITIES,validate_genome
from subjects.anatomy import build_scene
ROOT=Path(__file__).resolve().parents[1]
for p in [ROOT/'.runtime/deps',ROOT.parent/'nulltype/native/.runtime/deps',ROOT.parent/'cuda-deps']:
    if p.exists():sys.path.insert(0,str(p))
from engine.cuda_driver import Driver,CUDAError
GRAMMARS=['01','0123456789ABCDEF','0123456789','()[]{}<>','+-=*%&|!','/\\|_-','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz','0123456789ABCDEF@#$%&*','0123456789+-=()[]','.,:;irsXA253hMHGS#9B&@']
MATERIALS={'Bone':(18,.12,.15,1),'Charcoal':(8,.02,.08,.85),'Dark metal':(34,.45,.12,.85),'Polished steel':(70,.9,.24,1),'Chrome':(110,1.6,.3,1),'Glass-like':(100,1.2,.55,.72),'Crystalline':(85,1.3,.43,.9),'Ceramic':(42,.38,.12,1),'Porous stone':(8,.03,.09,.9),'Fog':(5,.02,.42,.5),'Smoke':(4,.01,.35,.42),'Organic tissue':(16,.16,.16,.92),'Synthetic armor':(60,.7,.25,.96),'Worn machinery':(28,.3,.15,.87),'Etched circuitry':(48,.6,.23,1)}
def calibration():
    fp=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts/consola.ttf'
    font=ImageFont.truetype(str(fp),48);aw=round(font.getlength('M'));ah=48;atlas=np.zeros((95,ah,aw),np.uint8)
    for code in range(32,127):
        img=Image.new('L',(aw,ah));ImageDraw.Draw(img).text((0,-8),chr(code),font=font,fill=255);atlas[code-32]=np.array(img)
    coverage=atlas.mean(axis=(1,2)).astype(np.float32)/255
    return atlas,coverage,dict(font='Consolas',font_sha256=hashlib.sha256(fp.read_bytes()).hexdigest(),atlas=[aw,ah],cell_aspect=aw/ah,coverage=coverage.tolist())
def configuration(g,aspect):
    p=g['parameters'];camera=int(g['modifiers']['T01'][-2:])-1
    yaw=[0,.55,-.55,1.35,0,0,.15,.25,0,0][camera]+p['camera_yaw'];pitch=[0,0,0,0,-.35,.35,0,0,0,0][camera]+p['camera_pitch']
    wh=(5.4 if g['family']=='ANIMALS' else 4.25 if g['family']=='CHARACTERS' else 3.65)/p['zoom']
    if camera==8:wh*=.8
    if camera==9:wh=max(wh,4.6)
    light=int(g['modifiers']['T03'][-2:])-1;lx,ly,lz=[(-.25,1,.75),(-1,.35,.6),(.1,-1,.7),(1,.1,-.2),(0,.2,-1),(.8,.8,1),(-.4,.6,1),(-1,.15,.5),(-.8,.3,.4),(0,1,.3)][light]
    lx+=p['light_yaw'];power,spec,rim,opacity=MATERIALS[p['material']]
    cfg=np.array([wh,int(camera==6),aspect,yaw,pitch,int(g['modifiers']['T02'][-2:])-1,RARITIES.index(g['rarity']),lx,ly,lz,opacity,power,spec,rim,int(g['modifiers']['T04'][-2:])-1,p['surface_frequency'],p['contrast'],MODES.index(g['appearance']),light,int(g['modifiers']['T10'][-2:])-1,int(g['seed'][:6],16),int(g['modifiers']['T06'][-2:])-1,p['entropy'],int(g['modifiers']['T09'][-2:])-1],np.float32)
    grammar=GRAMMARS[int(g['modifiers']['T05'][-2:])-1]
    if g['appearance']=='ENCRYPTED':grammar=GRAMMARS[7]
    return cfg,np.frombuffer(grammar.encode('ascii'),np.uint8).copy()
def ascii_text(glyph):return '\n'.join(bytes(row).decode('ascii') for row in glyph.reshape(30,30))+'\n'
def validate_buffer(glyph,cells):
    if glyph.shape!=(900,) or cells.shape!=(900,12):raise ValueError('Expected 900 canonical cells')
    if np.any((glyph<32)|(glyph>126)) or not np.isfinite(cells).all() or np.any((cells[:,0]<0)|(cells[:,0]>255)):raise ValueError('Invalid ASCII/grayscale cells')
class Renderer:
    def __init__(self,backend='auto',device=0):
        self.lock=threading.RLock();self.atlas,self.coverage,self.font=calibration();self.driver=None;self.reason=None;self.render_count=0;self.last_ms=0;self.last_gpu_ms=0
        if backend!='cpu':
            try:self.driver=Driver((ROOT/'engine/render.cu').read_text(encoding='utf-8'),device=device)
            except Exception as e:
                if backend=='cuda':raise
                self.reason=str(e)
        self.backend='CUDA' if self.driver else 'CPU'
        if self.driver:self.d_atlas=self.driver.buffer(self.atlas);self.d_coverage=self.driver.buffer(self.coverage)
    def status(self):
        with self.lock:
            free,total=0,0
            if self.driver:self.driver.activate();free,total=self.driver.memory()
            return dict(backend=self.backend,device=self.driver.name if self.driver else 'NumPy CPU reference',cuda=bool(self.driver),device_index=self.driver.device if self.driver else None,devices=self.driver.devices if self.driver else [],compute_capability=self.driver.arch if self.driver else None,free_vram_mb=round(free/1048576,1),total_vram_mb=round(total/1048576,1),last_wall_ms=self.last_ms,last_gpu_ms=self.last_gpu_ms,render_count=self.render_count,fallback_reason=self.reason,font=self.font,grid=[30,30])
    def render(self,g,ss=None,reveal=False):
        validate_genome(g);start=time.perf_counter();scene=build_scene(g);cfg,grammar=configuration(g,self.font['cell_aspect']);ss=int(ss or CONFIG['supersampling'])
        if ss not in [1,2,4,8]:raise ValueError('Supersampling must be 1,2,4 or 8')
        with self.lock:
            if self.driver:
                d=self.driver;d.activate();d.gpu_ms=0
                with ExitStack() as st:
                    sc=st.enter_context(d.buffer(scene.array()));cf=st.enter_context(d.buffer(cfg));gr=st.enter_context(d.buffer(grammar));gb=st.enter_context(d.allocate(900));cb=st.enter_context(d.allocate(900*12*4))
                    d.launch('render_cells',900,sc,len(scene.rows),cf,self.d_coverage,gr,len(grammar),gb,cb,ss)
                    glyph=gb.download(np.uint8,(900,));cells=cb.download(np.float32,(900,12));self.last_gpu_ms=d.gpu_ms
            else:
                from engine.cpu import render_cpu
                glyph,cells=render_cpu(scene.array(),cfg,grammar,self.coverage,ss);self.last_gpu_ms=0
            validate_buffer(glyph,cells)
            result=dict(glyph=glyph,cells=cells,scene=scene.array(),cfg=cfg,geometry_signature=hashlib.sha256(scene.array().tobytes()).hexdigest(),operators=sorted(scene.operators),anatomy_labels=scene.labels,backend=self.backend)
            if not reveal and g['appearance'] in ['FRAGMENTED','APPARENT CHAOS']:result=self.frame(result,g,0,static_mode=1 if g['appearance']=='FRAGMENTED' else 2)
            self.last_ms=round((time.perf_counter()-start)*1000,3);self.render_count+=1;result['wall_ms']=self.last_ms;result['gpu_ms']=round(self.last_gpu_ms,3)
            return result
    def render_batch(self,genomes,ss=None,reveal=False):
        if not 1<=len(genomes)<=16:raise ValueError('GPU batch size must be 1–16')
        if not self.driver:return [self.render(g,ss,reveal) for g in genomes]
        start=time.perf_counter();ss=int(ss or CONFIG['supersampling']);scenes=[];config=[];grammar=[]
        if ss not in [1,2,4,8]:raise ValueError('Invalid supersampling')
        for g in genomes:
            validate_genome(g);scenes.append(build_scene(g));cf,gr=configuration(g,self.font['cell_aspect']);config.append(cf);grammar.append(gr)
        n=len(genomes);padded=np.zeros((n,160,16),np.float32);counts=np.array([len(s.rows) for s in scenes],np.int32);gram=np.zeros((n,95),np.uint8);gn=np.array([len(gr) for gr in grammar],np.int32)
        for i in range(n):padded[i,:counts[i]]=scenes[i].array();gram[i,:gn[i]]=grammar[i]
        with self.lock:
            d=self.driver;d.activate();d.gpu_ms=0
            with ExitStack() as st:
                sc=st.enter_context(d.buffer(padded));ct=st.enter_context(d.buffer(counts));cf=st.enter_context(d.buffer(np.array(config)));gr=st.enter_context(d.buffer(gram));ng=st.enter_context(d.buffer(gn));gb=st.enter_context(d.allocate(n*900));cb=st.enter_context(d.allocate(n*900*48))
                d.launch('render_batch',n*900,sc,ct,cf,self.d_coverage,gr,ng,gb,cb,ss,n)
                glyph=gb.download(np.uint8,(n,900));cells=cb.download(np.float32,(n,900,12));gpu=d.gpu_ms
            self.last_gpu_ms=gpu;self.last_ms=(time.perf_counter()-start)*1000;results=[]
            for i,g in enumerate(genomes):
                scene=scenes[i];r=dict(glyph=glyph[i].copy(),cells=cells[i].copy(),scene=scene.array(),cfg=config[i],geometry_signature=hashlib.sha256(scene.array().tobytes()).hexdigest(),operators=sorted(scene.operators),anatomy_labels=scene.labels,backend='CUDA',wall_ms=round(self.last_ms/n,3),gpu_ms=round(gpu/n,3),batch_gpu_ms=round(gpu,3),batch_size=n,timing_basis='amortized batch kernel time')
                if not reveal and g['appearance'] in ['FRAGMENTED','APPARENT CHAOS']:r=self.frame(r,g,0,static_mode=1 if g['appearance']=='FRAGMENTED' else 2)
                validate_buffer(r['glyph'],r['cells']);results.append(r)
            self.render_count+=n
            return results
    def frame(self,base,g,frame,static_mode=0):
        total=g['animation']['fps']*g['animation']['seconds'];frame=int(frame)%total
        if static_mode in [1,2]:static_mode=static_mode*100+round(g['parameters']['fragmentation']*100)
        if not static_mode and ((.32<=frame/total<.46) or (.88<=frame/total<.94)):return {**base,'frame':frame}
        with self.lock:
            if self.driver:
                d=self.driver;d.activate();before=d.gpu_ms
                with ExitStack() as st:
                    gb=st.enter_context(d.buffer(base['glyph']));cb=st.enter_context(d.buffer(base['cells']));cf=st.enter_context(d.buffer(base['cfg']));z=st.enter_context(d.allocate(900*8));motion=st.enter_context(d.allocate(900*3*4));out=st.enter_context(d.allocate(900));cells=st.enter_context(d.allocate(900*12*4))
                    d.launch('clear_depth',900,z)
                    d.launch('project_fragments',900,cb,gb,cf,z,motion,frame,total,g['animation']['profile'],g['animation']['assembly_variant'],g['animation']['destruction_variant'],static_mode)
                    d.launch('resolve_fragments',900,z,gb,cb,out,cells)
                    glyph=out.download(np.uint8,(900,));values=cells.download(np.float32,(900,12));paths=motion.download(np.float32,(900,3));self.last_gpu_ms+=d.gpu_ms-before
            else:
                from engine.cpu import frame_cpu
                glyph,values,paths=frame_cpu(base,g,frame,static_mode)
            validate_buffer(glyph,values);return {**base,'glyph':glyph,'cells':values,'motion':paths,'frame':frame}
    def image(self,result,cell_width=13,cell_height=24):
        cw,ch=int(cell_width),int(cell_height)
        if not (4<=cw<=96 and 6<=ch<=160):raise ValueError('Preview dimensions out of range')
        with self.lock:
            if self.driver:
                d=self.driver;d.activate()
                with ExitStack() as st:
                    gb=st.enter_context(d.buffer(result['glyph']));cb=st.enter_context(d.buffer(result['cells']));pixel=st.enter_context(d.allocate(30*cw*30*ch*3))
                    d.launch('raster',30*cw*30*ch,gb,cb,self.d_atlas,self.atlas.shape[2],self.atlas.shape[1],pixel,cw,ch)
                    array=pixel.download(np.uint8,(30*ch,30*cw,3))
                return Image.fromarray(array)
            output=Image.new('RGB',(30*cw,30*ch),(5,5,5))
            for i,c in enumerate(result['glyph']):
                if c==32:continue
                mask=Image.fromarray(self.atlas[c-32]).resize((cw,ch),Image.Resampling.BILINEAR);value=round(result['cells'][i,0]);output.paste((min(255,5+value),)*3,((i%30)*cw,(i//30)*ch),mask)
            return output
    def close(self):
        if self.driver:
            with self.lock:self.driver.activate();self.d_atlas.close();self.d_coverage.close()
