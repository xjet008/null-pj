"""Loopback-only local studio: SDF lighting, animation and glyph raster use CUDA."""
import argparse
import base64
import json
import mimetypes
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

NATIVE=Path(__file__).resolve().parent
for path in [NATIVE/'.runtime/deps']:
    if path.is_dir():sys.path.insert(0,str(path))
from nullgenesis.renderer import Renderer,from_packet
from nullgenesis.genome import validate_genome,configuration

def run(port=4177,backend='cuda',device=0,web_root=None):
    root=Path(web_root or NATIVE.parent/'dist').resolve()
    if not (root/'index.html').is_file():raise ValueError('The studio dist/index.html was not found')
    renderer=Renderer(backend,device)
    hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
    origins={f'http://{h}' for h in hosts}
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(root),**kwargs)
        def _json(self,status,data):
            raw=json.dumps(data,separators=(',',':'),allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
        def _host(self):
            if self.headers.get('Host') not in hosts:raise ValueError('Only the local studio host is accepted')
        def do_GET(self):
            try:
                self._host()
                if self.path.split('?')[0]=='/api/v3/status':return self._json(200,renderer.status())
                if self.path.startswith('/api/'):return self._json(404,dict(error='Unknown local API'))
                self.extensions_map.update({'.gz':'application/gzip','.wgsl':'text/plain; charset=utf-8'})
                return super().do_GET()
            except ValueError as error:return self._json(403,dict(error=str(error)))
        def do_POST(self):
            try:
                self._host();origin=self.headers.get('Origin')
                if origin is not None and origin not in origins:raise PermissionError('A same-origin local request is required')
                if self.headers.get('Sec-Fetch-Site') not in (None,'same-origin','none'):raise PermissionError('Cross-site API requests are rejected')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Use application/json')
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4000000:raise ValueError('JSON request size must be 1 byte to 4 MB')
                payload=json.loads(self.rfile.read(size));route=self.path.split('?')[0]
                if route not in ('/api/v3/render','/api/v3/frame','/api/v3/raster','/api/v3/fit'):return self._json(404,dict(error='Unknown local API'))
                g=validate_genome(payload.get('genome',payload.get('g',{})))
                with renderer.lock:
                    started=time.perf_counter()
                    if route=='/api/v3/raster':
                        scale=int(payload.get('scale',1))
                        if not 1<=scale<=4:raise ValueError('Raster scale must be 1 to 4')
                        glyph,cells=from_packet(payload['cells'],g.get('grid',[30,30]))
                        result=dict(glyph=glyph,cells=cells,grid=g.get('grid',[30,30]));png=renderer.square_png(result,int(payload.get('size',600))) if g['genome_version']=='web-4.5.0' else renderer.png(result,scale)
                        return self._json(200,dict(preview='data:image/png;base64,'+base64.b64encode(png).decode(),backend=renderer.backend,ms=round((time.perf_counter()-started)*1000,3)))
                    if route.endswith('/fit'):
                        if g['genome_version']!='web-4.5.0':raise ValueError('Versioned fitting requires V4.5 DNA')
                        from experiment_v45 import candidate
                        g,result,metrics,signature,repairs=candidate(renderer,dict(genome=g,id='local-laboratory'))
                        return self._json(200,dict(genome=g,cells=result['packet'].reshape(-1).tolist(),quality=metrics,repairs=repairs,backend=renderer.backend,gpu_ms=result['gpu_ms'],render_ms=result['wall_ms'],preview='data:image/png;base64,'+base64.b64encode(renderer.square_png(result)).decode()))
                    index=int(payload.get('index',0)) if route.endswith('/frame') else 0
                    staticA=float(payload.get('staticA',-1))
                    if not -1<=staticA<=1:raise ValueError('Invalid assembly fraction')
                    result=renderer.frame(None,g,index,staticA) if route.endswith('/frame') else renderer.render(g,index,staticA)
                    response=dict(cells=result['packet'].reshape(-1).tolist(),grid=result['grid'],frame=result['frame'],backend=result['backend'],gpu_ms=result['gpu_ms'],render_ms=result['wall_ms'],canonical_hash=result['canonical_hash'])
                    if g['genome_version']=='web-4.5.0' and route.endswith('/render'):
                        from quality_v45 import quality
                        response['quality']=quality(result,g)[0]
                    if route.endswith('/render') or payload.get('preview',False):
                        png=renderer.square_png(result) if g['genome_version']=='web-4.5.0' else renderer.png(result)
                        response['preview']='data:image/png;base64,'+base64.b64encode(png).decode()
                    return self._json(200,response)
            except PermissionError as error:return self._json(403,dict(error=str(error)))
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:return self._json(400,dict(error=str(error)))
            except Exception as error:return self._json(500,dict(error=type(error).__name__+': '+str(error)))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(json.dumps(dict(url=f'http://127.0.0.1:{port}',backend=renderer.backend,device=renderer.status()['device'])),flush=True)
    try:server.serve_forever()
    finally:server.server_close();renderer.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=4177);parser.add_argument('--backend',choices=['auto','cuda','cpu'],default='cuda');parser.add_argument('--device',type=int,default=0);parser.add_argument('--web-root')
    args=parser.parse_args();run(args.port,args.backend,args.device,args.web_root)
