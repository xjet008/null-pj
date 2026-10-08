"""Reproducible measured NVIDIA V3 benchmarks; synthetic and collection input supported."""
import argparse
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal
sys.path.insert(0,str(ROOT/'tests'))
from test_native import fixture

def summary(values):
    return dict(samples=len(values),mean_ms=round(statistics.mean(values),3),min_ms=round(min(values),3),max_ms=round(max(values),3))
def bench(input_path=None,output=None):
    start=time.perf_counter()
    with Renderer('cuda') as renderer:
        cold=renderer.status();genomes=json.loads(Path(input_path).read_text(encoding='utf-8')) if input_path else [fixture(renderer.coverage)]
        if isinstance(genomes,dict):genomes=genomes.get('genomes',genomes.get('items',[genomes]))
        genomes=[item.get('genome',item) for item in genomes]
        results=[]
        for grid in (30,50):
            g=seal({**genomes[0],'grid':[grid,grid]});renderer.render(g);wall=[];gpu=[]
            for _ in range(5):
                r=renderer.render(g);wall.append(r['wall_ms']);gpu.append(r['gpu_ms'])
            image_start=time.perf_counter();png=renderer.png(r);raster_png=(time.perf_counter()-image_start)*1000
            indices=list(range(min(48,g['animation']['fps']*g['animation']['seconds'])))
            before=renderer.status();t=time.perf_counter();sequence=list(renderer.render_sequence(g,indices));sequence_wall=(time.perf_counter()-t)*1000;after=renderer.status()
            t=time.perf_counter();individual=[renderer.render(g,i) for i in indices];individual_wall=(time.perf_counter()-t)*1000
            exact=all(np.array_equal(a['packet'],b['packet']) for a,b in zip(sequence,individual))
            if not exact:raise AssertionError('Batched sequence changed deterministic output')
            results.append(dict(grid=[grid,grid],scene_primitives=len(g['scene']),samples=g.get('samples',1),render_wall=summary(wall),render_gpu=summary(gpu),raster_png_ms=round(raster_png,3),png_bytes=len(png),animation_frames=len(indices),sequence_wall_ms=round(sequence_wall,3),sequence_fps=round(len(indices)*1000/sequence_wall,2),individual_wall_ms=round(individual_wall,3),sequence_speedup=round(individual_wall/sequence_wall,3),sequence_exact_match=exact,pool_bytes_before=before['pool_bytes'],pool_bytes_after=after['pool_bytes']))
        # The archived kernel is measured on the same geometry, at30x30. It has
        # simpler shading; timing is not presented as an artistic-quality match.
        legacy_spec=importlib.util.spec_from_file_location('ng_legacy_driver',ROOT/'legacy/engine/cuda_driver.py');mod=importlib.util.module_from_spec(legacy_spec);legacy_spec.loader.exec_module(mod)
        legacy=mod.Driver((ROOT/'legacy/engine/render.cu').read_text(encoding='utf-8'));g=genomes[0];scene=np.array(g['scene'],np.float32);cfg=np.array(g['config'],np.float32);grammar=np.frombuffer(g['grammar'].encode(),np.uint8);coverage=np.asarray(g['coverage'],np.float32);wall=[];gpu=[]
        for _ in range(5):
            legacy.activate();legacy.gpu_ms=0;t=time.perf_counter()
            from contextlib import ExitStack
            with ExitStack() as stack:
                sc=stack.enter_context(legacy.buffer(scene));cf=stack.enter_context(legacy.buffer(cfg));cv=stack.enter_context(legacy.buffer(coverage));gr=stack.enter_context(legacy.buffer(grammar));gg=stack.enter_context(legacy.allocate(900));cc=stack.enter_context(legacy.allocate(900*48))
                legacy.launch('render_cells',900,sc,len(scene),cf,cv,gr,len(grammar),gg,cc,g.get('samples',1));glyph=gg.download(np.uint8,(900,));cells=cc.download(np.float32,(900,12))
            wall.append((time.perf_counter()-t)*1000);gpu.append(legacy.gpu_ms)
        telemetry=None
        try:
            completed=subprocess.run([r'C:\Windows\System32\nvidia-smi.exe','--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,creationflags=0x08000000)
            if completed.returncode==0:telemetry=completed.stdout.strip()
        except (OSError,subprocess.TimeoutExpired):pass
        status=renderer.status();report=dict(version='3.0.0',device=status['device'],compute_capability=status['compute_capability'],cuda_verified=status['cuda'],cold_start_ms=cold['startup_ms'],nvrtc_compile_ms=cold['compile_ms'],input='collection experimental DNA' if input_path else 'native deterministic skull fixture',legacy_baseline=dict(grid=[30,30],simpler_lighting=True,render_wall=summary(wall),render_gpu=summary(gpu)),v3=results,telemetry=telemetry,peak_pool_bytes=status['pool_bytes'],total_vram_mb=status['total_vram_mb'],free_vram_mb=status['free_vram_mb'],wall_seconds=round(time.perf_counter()-start,3),notes=['Timing includes actual checked CUDA Driver API execution.','Animation sequence and individual rendering are byte-identical on this backend.','Legacy and V3 lighting differ intentionally; visual release requires separate inspection.','GPU utilization is a post-run point sample, not a sustained utilization benchmark.'])
        path=Path(output or ROOT/'reports/nvidia-v3-benchmark.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input');p.add_argument('--output');a=p.parse_args();bench(a.input,a.output)
