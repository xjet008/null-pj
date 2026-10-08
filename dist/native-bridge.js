// Optional loopback CUDA transport. Public hosting uses the browser renderer.
export class NativeBridge {
 static async connect(){
  if(!['127.0.0.1','localhost','[::1]'].includes(location.hostname))return null;
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),1800);
  try{const response=await fetch('/api/v3/status',{signal:controller.signal,cache:'no-store'});if(!response.ok)return null;const status=await response.json();if(status.backend!=='CUDA'||!Array.isArray(status.coverage)||status.coverage.length!==95)return null;return new NativeBridge(status)}catch{return null}finally{clearTimeout(timer)}
 }
 constructor(status){this.status=status;this.lastMs=0;this.lastGpuMs=0;this.preview=null;}
 async request(path,body){const r=await fetch('/api/v3/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const p=await r.json();if(!r.ok)throw Error(p.error||'The local CUDA operation failed.');this.lastMs=Number(p.render_ms??p.wall_ms??p.ms??0);if(Number.isFinite(p.gpu_ms)){this.lastGpuMs=p.gpu_ms;this.status.last_gpu_ms=p.gpu_ms;}return p;}
 async render(genome){const p=await this.request('render',{genome});this.preview=p.preview||null;return new Float32Array(p.cells)}
 async frame(cells,genome,index,staticA=-1){const p=await this.request('frame',{genome,cells:Array.from(cells),index,staticA});return new Float32Array(p.cells)}
 async image(cells,genome,scale=1){const p=await this.request('raster',{genome,cells:Array.from(cells),scale});return p.preview;}
 dispose(){}
}
