"""CUDA V3 SDF rendering, universal primitive motion and native glyph rasterization."""
import hashlib
import io
import os
import threading
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .cuda_driver import Driver
from .genome import validate_genome, configuration, motion_parameters

ROOT=Path(__file__).resolve().parent

def calibration():
    candidates=[Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts/consola.ttf',Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]
    path=next((p for p in candidates if p.exists()),None)
    if path is None:raise RuntimeError('A monospace TrueType font is required. Install Consolas or DejaVu Sans Mono.')
    font=ImageFont.truetype(str(path),48);aw=round(font.getlength('M'));ah=48;atlas=np.zeros((95,ah,aw),np.uint8)
    for code in range(32,127):
        image=Image.new('L',(aw,ah));ImageDraw.Draw(image).text((0,-8),chr(code),font=font,fill=255);atlas[code-32]=np.array(image)
    coverage=atlas.mean(axis=(1,2)).astype(np.float32)/255
    return atlas,coverage,dict(font=path.stem,font_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),atlas=[aw,ah],cell_aspect=aw/ah)

def ascii_text(glyph,grid):
    width,height=map(int,grid);return '\n'.join(bytes(row).decode('ascii') for row in glyph.reshape(height,width))+'\n'

def packet(glyph,cells):
    result=np.empty_like(cells);result[:,0]=glyph;result[:,1]=cells[:,0];result[:,2:8]=cells[:,2:8];result[:,8]=cells[:,1];result[:,9]=cells[:,9];result[:,10]=cells[:,8];result[:,11]=cells[:,11]
    return result

def from_packet(values,grid):
    values=np.asarray(values,np.float32).reshape(-1,12)
    if values.shape!=(grid[0]*grid[1],12) or not np.isfinite(values).all() or np.any(values[:,0]!=np.floor(values[:,0])) or np.any((values[:,0]<32)|(values[:,0]>126)) or np.any((values[:,1]<0)|(values[:,1]>255)):raise ValueError('Invalid ASCII cell packet')
    cells=np.zeros_like(values);cells[:,0]=values[:,1];cells[:,1]=values[:,8];cells[:,2:8]=values[:,2:8];cells[:,8]=values[:,10];cells[:,9]=values[:,9];cells[:,11]=values[:,11]
    return values[:,0].astype(np.uint8),cells

class Renderer:
    def __init__(self,backend='auto',device=0):
        if backend not in ('auto','cuda','cpu'):raise ValueError('Backend must be auto, cuda or cpu')
        started=time.perf_counter();self.lock=threading.RLock();self.atlas,self.coverage,self.font=calibration();self.driver=None;self.fallback_reason=None;self.pool={};self.allocations=0;self.render_count=0;self.last_ms=0;self.last_gpu_ms=0;self.prepared=None
        if backend!='cpu':
            try:self.driver=Driver((ROOT/'render.cu').read_text(encoding='utf-8')+'\n'+(ROOT/'motion.cu').read_text(encoding='utf-8')+'\n'+(ROOT/'encoder.cu').read_text(encoding='utf-8'),device=device)
            except Exception as error:
                if backend=='cuda':raise
                self.fallback_reason=str(error)
        self.backend='CUDA' if self.driver else 'CPU'
        if self.driver:
            self._buffer('atlas',self.atlas.nbytes).upload(self.atlas);self._buffer('coverage',self.coverage.nbytes).upload(self.coverage)
        self.startup_ms=(time.perf_counter()-started)*1000
    def _buffer(self,name,size):
        previous=self.pool.get(name)
        if previous is None or previous.size<size:
            if previous is not None:previous.close()
            self.pool[name]=self.driver.allocate(size);self.allocations+=1
        return self.pool[name]
    def status(self):
        with self.lock:
            free,total=0,0
            if self.driver:self.driver.activate();free,total=self.driver.memory()
            return dict(version='4.5.0',backend=self.backend,cuda=bool(self.driver),device=self.driver.name if self.driver else 'NumPy CPU reference',device_index=self.driver.device if self.driver else None,compute_capability=self.driver.arch if self.driver else None,devices=self.driver.devices if self.driver else [],fontName=self.font['font'],font=self.font,coverage=self.coverage.tolist(),last_gpu_ms=self.last_gpu_ms,last_wall_ms=self.last_ms,startup_ms=round(self.startup_ms,3),compile_ms=round(self.driver.compile_ms,3) if self.driver else 0,compile_cache_hit=bool(self.driver and self.driver.cache_hit),free_vram_mb=round(free/1048576,1),total_vram_mb=round(total/1048576,1),pool_bytes=sum(b.size for b in self.pool.values()),allocations=self.allocations,render_count=self.render_count,supported_grids=[[n,n] for n in (30,50,64,80,96,120)],presentation_sizes=[300,600,1200],encoder='CUDA depth/normal/coverage contour with row error diffusion',fallback_reason=self.fallback_reason)
    def _prepare(self,g):
        scene=np.ascontiguousarray(g['scene'],np.float32);cfg=configuration(g);grammar=np.frombuffer(g['grammar'].encode('ascii'),np.uint8).copy();coverage=np.array(g['coverage'],np.float32)
        self.grammar_bytes=grammar
        self.encoder_parameters=g.get('encoder',dict(temporal_lock=.82,depth_weight=.32,noise_budget=.035))
        if self.driver:
            self.driver.activate()
            signature=g['fingerprint']
            if self.prepared!=signature:
                self._buffer('scene',160*16*4).upload(scene);self._buffer('config',40*4).upload(cfg);self._buffer('grammar',95).upload(grammar);self._buffer('coverage',95*4).upload(coverage);self._buffer('motion_params',5*4).upload(motion_parameters(g));self.prepared=signature
        return scene,cfg,grammar,coverage
    def render(self,g,index=0,staticA=-1,legacy_reconstruction=False):
        if g.get('genome_version')=='web-4.5.0' and not self.driver:raise RuntimeError('V4.5 canonical generation requires NVIDIA CUDA; browser and V3 CPU rendering remain separate preview/reference backends')
        validate_genome(g);started=time.perf_counter();grid=list(map(int,g.get('grid',[30,30])));count=grid[0]*grid[1];total=int(g['animation']['fps']*g['animation']['seconds']);index=int(index)%total;v3=g['genome_version']!='web-1.0.0';legendary=g.get('rarity')=='LEGENDARY' or g['animation'].get('legendary',False)
        with self.lock:
            scene,cfg,grammar,coverage=self._prepare(g)
            cfg[35]=staticA
            if self.driver:self.pool['config'].upload(cfg)
            fragments=staticA>=0 or ((legendary or legacy_reconstruction) and index!=0)
            t=(index/total+(.32 if v3 else 0))%1
            if staticA<0 and (.32<=t<.46 or .88<=t<.94):fragments=False
            if self.driver:
                d=self.driver;d.activate();d.gpu_ms=0
                glyph=self._buffer('glyph',count);cells=self._buffer('cells',count*48);posed=self._buffer('posed_scene',160*32*4)
                if v3:
                    with d.measure():
                        d.enqueue('animate_scene',len(scene),self.pool['scene'],posed,len(scene),self.pool['motion_params'],index,total)
                        d.enqueue('render_cells',count,posed,len(scene),self.pool['config'],self.pool['coverage'],self.pool['grammar'],len(grammar),glyph,cells,int(g.get('samples',1)))
                else:
                    with d.measure():
                        d.enqueue('animate_scene',len(scene),self.pool['scene'],posed,len(scene),self.pool['motion_params'],0,total)
                        d.enqueue('render_cells',count,posed,len(scene),self.pool['config'],self.pool['coverage'],self.pool['grammar'],len(grammar),glyph,cells,int(g.get('samples',1)))
                if g['genome_version']=='web-4.5.0':
                    with d.measure():glyph,cells=self._encode(glyph,cells,grid,1,'encoded')
                if fragments:
                    depth=self._buffer('depth',count*8);paths=self._buffer('paths',count*12);out=self._buffer('frame_glyph',count);values=self._buffer('frame_cells',count*48)
                    # Existing fragment modes are retained. Explicit staticA is an
                    # assembly fraction, converted to the native legacy quantity.
                    static_mode=0
                    paths.upload(np.zeros((count,3),np.float32))
                    with d.measure():
                        d.enqueue('clear_depth',count,depth,count)
                        d.enqueue('project_fragments',count,cells,glyph,self.pool['config'],depth,paths,index,total,int(g['animation']['profile']),int(g['animation']['assembly_variant']),int(g['animation']['destruction_variant']),static_mode)
                        d.enqueue('resolve_fragments',count,depth,glyph,cells,out,values,count)
                    glyph,cells=out,values
                out_glyph=glyph.download(np.uint8,(count,));out_cells=cells.download(np.float32,(count,12));gpu_ms=d.gpu_ms
            else:
                from .cpu import render_cpu,frame_cpu
                from .motion import animate_scene
                posed=animate_scene(scene,g.get('motion',{}),index,total) if v3 else scene
                out_glyph,out_cells=render_cpu(posed,cfg,grammar,coverage,int(g.get('samples',1)));gpu_ms=0
                if fragments:
                    base=dict(glyph=out_glyph,cells=out_cells,cfg=cfg)
                    static_mode=0
                    out_glyph,out_cells,_=frame_cpu(base,g,index,static_mode)
            if not np.isfinite(out_cells).all() or np.any((out_glyph<32)|(out_glyph>126)) or np.any((out_cells[:,0]<0)|(out_cells[:,0]>255)):raise RuntimeError('Renderer produced invalid canonical cells')
            self.last_ms=(time.perf_counter()-started)*1000;self.last_gpu_ms=gpu_ms;self.render_count+=1
            return self._result(g,out_glyph,out_cells,cfg,index,self.last_ms,gpu_ms)
    def _result(self,g,glyph,cells,cfg,index,wall,gpu):
        grid=list(map(int,g.get('grid',[30,30])));text=ascii_text(glyph,grid)
        return dict(glyph=glyph,cells=cells,packet=packet(glyph,cells),ascii=text,grid=list(grid),frame=index,backend=self.backend,wall_ms=round(wall,3),gpu_ms=round(gpu,3),canonical_hash=hashlib.sha256(text.encode('ascii')).hexdigest(),cfg=cfg,genome_fingerprint=g['fingerprint'])
    def _encode(self,glyph,cells,grid,batch,prefix):
        count=grid[0]*grid[1]*batch;out=self._buffer(prefix+'_glyph',count);values=self._buffer(prefix+'_cells',count*48)
        e=self.encoder_parameters;self.driver.enqueue('encode_rows',grid[1]*batch,glyph,cells,self.pool['scene'],self.pool['config'],self.pool['coverage'],self.pool['grammar'],len(self.grammar_bytes),out,values,float(e['temporal_lock']),float(e['depth_weight']),float(e['noise_budget']),batch)
        return out,values
    def frame(self,base,g,index,staticA=-1):
        # V3 rerenders the posed geometry; it never projects a stale silhouette.
        return self.render(g,index,staticA,legacy_reconstruction=g['genome_version']=='web-1.0.0')
    def render_sequence(self,g,indices=None,chunk_size=16):
        """Yield bounded animation batches with one GPU barrier per chunk.

        DNA is authenticated once and base geometry remains on CUDA. Poses,
        ray marching and Legendary depth projection run on the GPU.
        """
        validate_genome(g);total=int(g['animation']['fps']*g['animation']['seconds']);indices=list(range(total)) if indices is None else [int(i)%total for i in indices]
        if not self.driver or g['genome_version']=='web-1.0.0':
            for index in indices:yield self.render(g,index)
            return
        grid=list(map(int,g.get('grid',[30,30])));count=grid[0]*grid[1];complexity=len(g['scene']);cap=16 if complexity<60 else 8 if complexity<100 else 4
        if g.get('samples',1)>1:cap=min(cap,4)
        chunk_size=max(1,min(int(chunk_size),cap));legendary=g.get('rarity')=='LEGENDARY' or g['animation'].get('legendary',False)
        with self.lock:
            scene,cfg,grammar,coverage=self._prepare(g);d=self.driver;d.activate()
            for start in range(0,len(indices),chunk_size):
                begun=time.perf_counter();frames=indices[start:start+chunk_size];n=len(frames);d.gpu_ms=0
                arrays=dict(seq_count=np.full(n,len(scene),np.int32),seq_config=np.repeat(cfg[None,:],n,axis=0),seq_grammar=np.zeros((n,95),np.uint8),seq_lengths=np.full(n,len(grammar),np.int32),seq_indices=np.asarray(frames,np.int32))
                arrays['seq_grammar'][:,:len(grammar)]=grammar
                for name,a in arrays.items():self._buffer(name,a.nbytes).upload(a)
                posed=self._buffer('seq_scene',n*160*32*4);glyph=self._buffer('seq_glyph',n*count);cells=self._buffer('seq_cells',n*count*48)
                final_glyph=glyph;final_cells=cells
                with d.measure():
                    d.enqueue('animate_scene_batch',n*len(scene),self.pool['scene'],posed,len(scene),self.pool['motion_params'],self.pool['seq_indices'],total,n)
                    d.enqueue('render_batch',n*count,posed,self.pool['seq_count'],self.pool['seq_config'],self.pool['coverage'],self.pool['seq_grammar'],self.pool['seq_lengths'],glyph,cells,int(g.get('samples',1)),n)
                    if g['genome_version']=='web-4.5.0':
                        glyph,cells=self._encode(glyph,cells,grid,n,'seq_encoded');final_glyph=glyph;final_cells=cells
                    if legendary:
                        final_glyph=self._buffer('seq_out_glyph',n*count);final_cells=self._buffer('seq_out_cells',n*count*48);depth=self._buffer('seq_depth',n*count*8);paths=self._buffer('seq_paths',n*count*12)
                        d.enqueue('copy_render',n*count,glyph,cells,final_glyph,final_cells,n*count)
                        for i,index in enumerate(frames):
                            t=(index/total+.32)%1
                            if index==0 or .32<=t<.46 or .88<=t<.94:continue
                            z=depth.view(i*count*8,count*8);p=paths.view(i*count*12,count*12);gb=glyph.view(i*count,count);cb=cells.view(i*count*48,count*48);out=final_glyph.view(i*count,count);result=final_cells.view(i*count*48,count*48)
                            d.enqueue('clear_depth',count,z,count)
                            d.enqueue('project_fragments',count,cb,gb,self.pool['config'],z,p,index,total,int(g['animation']['profile']),int(g['animation']['assembly_variant']),int(g['animation']['destruction_variant']),0)
                            d.enqueue('resolve_fragments',count,z,gb,cb,out,result,count)
                gg=final_glyph.download(np.uint8,(n,count));cc=final_cells.download(np.float32,(n,count,12));wall=(time.perf_counter()-begun)*1000;gpu=d.gpu_ms;self.last_gpu_ms=gpu;self.last_ms=wall;self.render_count+=n
                results=[self._result(g,gg[i],cc[i],cfg,index,wall/n,gpu/n) for i,index in enumerate(frames)]
                for result in results:yield result

    def adaptive_batch_size(self,genomes):
        """Select a bounded batch from actual scene complexity and free VRAM."""
        if not genomes:return 0
        complexity=max(len(g['scene']) for g in genomes);size=16 if complexity<48 else 8 if complexity<100 else 4
        if self.driver:
            self.driver.activate();free,_=self.driver.memory();per=max(g.get('grid',[30,30])[0]**2*49+160*16*4+40*4+95 for g in genomes)
            size=min(size,max(1,int(free*.05//max(per,1))))
        return min(size,len(genomes))
    def render_batch(self,genomes,index=0):
        if not genomes:return []
        for g in genomes:validate_genome(g)
        if not self.driver or index or len(genomes)==1 or any(g['genome_version']=='web-4.5.0' for g in genomes):return [self.render(g,index) for g in genomes]
        if len({tuple(g.get('grid',[30,30])) for g in genomes})!=1:return [self.render(g,index) for g in genomes]
        if len(genomes)>self.adaptive_batch_size(genomes):
            size=self.adaptive_batch_size(genomes);return [r for offset in range(0,len(genomes),size) for r in self.render_batch(genomes[offset:offset+size],index)]
        started=time.perf_counter();n=len(genomes);grid=list(map(int,genomes[0].get('grid',[30,30])));count=grid[0]*grid[1];scenes=np.zeros((n,160,16),np.float32);counts=np.empty(n,np.int32);gram=np.zeros((n,95),np.uint8);lengths=np.empty(n,np.int32);cfg=np.array([configuration(g) for g in genomes])
        # Coverage is part of DNA; different calibrations are rendered separately.
        if any(g['coverage']!=genomes[0]['coverage'] for g in genomes):return [self.render(g) for g in genomes]
        for i,g in enumerate(genomes):
            counts[i]=len(g['scene']);scenes[i,:counts[i]]=g['scene'];raw=g['grammar'].encode('ascii');lengths[i]=len(raw);gram[i,:len(raw)]=np.frombuffer(raw,np.uint8)
        with self.lock:
            d=self.driver;d.activate();d.gpu_ms=0
            values={'batch_scene':scenes,'batch_count':counts,'batch_config':cfg,'batch_grammar':gram,'batch_lengths':lengths,'batch_coverage':np.asarray(genomes[0]['coverage'],np.float32)}
            for name,a in values.items():self._buffer(name,a.nbytes).upload(a)
            glyph=self._buffer('batch_glyph',n*count);cells=self._buffer('batch_cells',n*count*48)
            cached=self._buffer('batch_cached_scene',n*160*32*4)
            with d.measure():
                d.enqueue('prepare_scene_batch',n*160,self.pool['batch_scene'],cached,self.pool['batch_count'],n)
                d.enqueue('render_batch',n*count,cached,self.pool['batch_count'],self.pool['batch_config'],self.pool['batch_coverage'],self.pool['batch_grammar'],self.pool['batch_lengths'],glyph,cells,int(genomes[0].get('samples',1)),n)
            if any(g.get('samples',1)!=genomes[0].get('samples',1) for g in genomes):raise ValueError('Batch supersampling must be identical')
            gg=glyph.download(np.uint8,(n,count));cc=cells.download(np.float32,(n,count,12));wall=(time.perf_counter()-started)*1000;gpu=d.gpu_ms;self.render_count+=n;self.last_ms=wall;self.last_gpu_ms=gpu
            return [self._result(g,gg[i],cc[i],cfg[i],0,wall/n,gpu/n) for i,g in enumerate(genomes)]
    def image(self,result,cell_width=13,cell_height=24):
        cw,ch=int(cell_width),int(cell_height);gx,gy=map(int,result['grid']);count=gx*gy
        if not (4<=cw<=96 and 6<=ch<=160):raise ValueError('Raster cell dimensions out of range')
        with self.lock:
            if self.driver:
                d=self.driver;d.activate();gb=self._buffer('raster_glyph',count).upload(result['glyph']);cb=self._buffer('raster_cells',count*48).upload(result['cells']);pixel=self._buffer('raster_pixels',gx*cw*gy*ch*3)
                with d.measure():d.enqueue('raster',gx*cw*gy*ch,gb,cb,self.pool['atlas'],self.atlas.shape[2],self.atlas.shape[1],pixel,cw,ch,gx,gy)
                return Image.fromarray(pixel.download(np.uint8,(gy*ch,gx*cw,3)))
            output=Image.new('RGB',(gx*cw,gy*ch),(5,5,5))
            for i,c in enumerate(result['glyph']):
                if c==32:continue
                mask=Image.fromarray(self.atlas[c-32]).resize((cw,ch),Image.Resampling.BILINEAR);value=round(result['cells'][i,0]);output.paste((min(255,5+value),)*3,((i%gx)*cw,(i//gx)*ch),mask)
            return output
    def png(self,result,scale=1):
        stream=io.BytesIO();self.image(result,13*scale,24*scale).save(stream,format='PNG');return stream.getvalue()
    def square_image(self,result,size=600):
        if size not in (300,600,1200):raise ValueError('Square presentation must be 300, 600 or 1200 pixels')
        if not self.driver:raise RuntimeError('V4.5 square canonical raster requires NVIDIA CUDA')
        with self.lock:
            d=self.driver;d.activate();gx,gy=result['grid'];count=gx*gy
            gb=self._buffer('square_glyph',count).upload(result['glyph']);cb=self._buffer('square_cells',count*48).upload(result['cells']);pixels=self._buffer('square_pixels',size*size*3)
            with d.measure():d.enqueue('raster_square',size*size,gb,cb,self.pool['atlas'],self.atlas.shape[2],self.atlas.shape[1],pixels,size,gx,gy)
            return Image.fromarray(pixels.download(np.uint8,(size,size,3)))
    def square_png(self,result,size=600):
        stream=io.BytesIO();self.square_image(result,size).save(stream,format='PNG');return stream.getvalue()
    def close(self):
        with self.lock:
            if self.driver:
                self.driver.activate()
                for buffer in self.pool.values():buffer.close()
                self.pool.clear();self.driver.close();self.driver=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
