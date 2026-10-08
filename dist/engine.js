import {fromAscii,toAscii,validateCells} from './math.js';
export const canonical=o=>JSON.stringify(sort(o));
function sort(o){if(Array.isArray(o))return o.map(sort);if(o&&typeof o==='object')return Object.fromEntries(Object.keys(o).sort().map(k=>[k,sort(o[k])]));return o}
export async function sha(text){const bytes=typeof text==='string'?new TextEncoder().encode(text):text;return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('')}
export async function seal(g){delete g.fingerprint;g.fingerprint=await sha(canonical(g));return g}
export async function checkGenome(g){
 if(g.genome_version!=='web-1.0.0')throw Error('This laboratory genome version is not supported.');
 const copy=structuredClone(g);delete copy.fingerprint;if(await sha(canonical(copy))!==g.fingerprint)throw Error('DNA fingerprint mismatch.');
 if(!Array.isArray(g.scene)||!g.scene.length||g.scene.length>160||g.scene.some(r=>r.length!==16||r.some(x=>!Number.isFinite(x)||Math.abs(x)>100)))throw Error('Invalid geometry.');
 for(const r of g.scene){if(!Number.isInteger(r[0])||r[0]<0||r[0]>11||r.slice(4,7).some(x=>x<.001)||r[0]===10&&r[12]<3)throw Error('Invalid primitive.');}
 if(!Array.isArray(g.config)||g.config.length!==24||g.config.some(x=>!Number.isFinite(x)||Math.abs(x)>16777216)||g.config[0]<.1||g.config[2]<.1||g.config[11]<1)throw Error('Invalid render parameters.');
 if(!Array.isArray(g.coverage)||g.coverage.length!==95||g.coverage.some(x=>!Number.isFinite(x)||x<0||x>1)||typeof g.grammar!=='string'||g.grammar.length<1||g.grammar.length>95||!/^[\x20-\x7e]+$/.test(g.grammar)||![1,2,4].includes(g.samples))throw Error('Invalid glyph grammar.');
 const a=g.animation;if(!a||a.fps!==12||a.seconds!==8||!Number.isInteger(a.profile)||a.profile<0||a.profile>22||![a.assembly_variant,a.destruction_variant].every(x=>Number.isInteger(x)&&x>=0&&x<10))throw Error('Invalid motion definition.');
 return g;
}
export async function readJson(path){const r=await fetch(path);if(!r.ok)throw Error('Could not load '+path+' ('+r.status+').');if(!path.endsWith('.gz'))return r.json();let bytes=new Uint8Array(await r.arrayBuffer());if(bytes[0]===31&&bytes[1]===139){if(!globalThis.DecompressionStream)throw Error('This browser does not support compressed collection records. Use a current Chrome, Edge, Firefox or Safari.');const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));return JSON.parse(await new Response(stream).text());}return JSON.parse(new TextDecoder().decode(bytes));}
export class Repository {
 async init(){[this.config,this.registry,this.catalog]=await Promise.all([readJson('/data/config.json'),readJson('/data/registry.json'),readJson('/data/catalog.json')]);this.blocks=new Map();this.subjects=Object.fromEntries(Object.keys(this.config.families).map(f=>[f,[...new Set(this.catalog.filter(m=>m.family===f).map(m=>m.subject))]]));return this}
 async item(edition){if(!Number.isInteger(edition)||edition<1||edition>3333)throw Error('Invalid edition.');const block=Math.floor((edition-1)/100);if(!this.blocks.has(block))this.blocks.set(block,readJson('/data/block-'+String(block).padStart(2,'0')+'.json.gz'));const a=(await this.blocks.get(block)).find(x=>x.edition===edition);if(!a||await sha(a.ascii)!==a.metadata.canonical_hash)throw Error('Canonical artwork verification failed.');return a}
 async foundation(family,subject,style,seed){let rows=this.catalog.filter(m=>m.family===family&&m.subject===subject);rows.sort((a,b)=>(b.style_id===style)-(a.style_id===style)||a.edition-b.edition);return this.item(rows[parseInt(seed.slice(6,10),16)%Math.min(4,rows.length)].edition)}
}
export class Engine {
 constructor(){this.backend='CPU';this.deviceName='CPU reference · browser worker';this.lastMs=null;this.jobs=new Map();this.serial=Promise.resolve();this.counter=0;}
 async init(){
  this.font();this.worker=new Worker(new URL('./cpu-worker.js',import.meta.url),{type:'module'});this.worker.onmessage=e=>{let j=this.jobs.get(e.data.id);if(j){this.jobs.delete(e.data.id);e.data.error?j.reject(Error(e.data.error)):j.resolve(e.data.result)}};
  this.worker.onerror=()=>{for(const j of this.jobs.values())j.reject(Error('The browser worker failed. Reload to restart the renderer.'));this.jobs.clear()};
  try{if(!navigator.gpu)throw Error('WebGPU is unavailable in this browser.');this.adapter=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});if(!this.adapter)throw Error('No WebGPU adapter.');this.device=await this.adapter.requestDevice();this.device.lost.then(info=>{this.backend='CPU';this.deviceName='CPU reference · GPU device lost';this.fallbackReason=info.message});
   const source=await fetch('/renderer.wgsl?v=1',{cache:'no-store'}).then(r=>r.text()),module=this.device.createShaderModule({code:source}),info=await module.getCompilationInfo();const errors=info.messages.filter(m=>m.type==='error');if(errors.length)throw Error(errors.map(e=>e.message).join(' '));
   this.layout=this.device.createBindGroupLayout({entries:Array.from({length:8},(_,binding)=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:binding===4||binding===6||binding===7?'storage':'read-only-storage'}}))});
   const layout=this.device.createPipelineLayout({bindGroupLayouts:[this.layout]});this.pipelines={};for(const entryPoint of ['render_cells','clear_depth','project_fragments','resolve_fragments','raster_pixels'])this.pipelines[entryPoint]=await this.device.createComputePipelineAsync({layout,compute:{module,entryPoint}});
   this.backend='WebGPU';this.deviceName=this.adapter.info?.description||[this.adapter.info?.vendor,this.adapter.info?.architecture].filter(Boolean).join(' ')||'WebGPU high-performance adapter';
  }catch(e){this.fallbackReason=e.message;this.backend='CPU';}
  return this;
 }
 font(){
  const canvas=document.createElement('canvas');canvas.width=40;canvas.height=48;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.font='48px Consolas,monospace';const width=Math.ceil(ctx.measureText('M').width);canvas.width=width;ctx.font='48px Consolas,monospace';ctx.textBaseline='top';this.aw=width;this.ah=48;this.fontName='48px Consolas,monospace';this.atlas=new Uint32Array(width*48*95);this.coverage=[];
  for(let i=0;i<95;i++){ctx.clearRect(0,0,width,48);ctx.fillStyle='white';ctx.fillText(String.fromCharCode(i+32),0,0);const data=ctx.getImageData(0,0,width,48).data;let sum=0;for(let p=0;p<width*48;p++){const v=data[p*4+3];this.atlas[i*width*48+p]=v;sum+=v}this.coverage.push(sum/(255*width*48));}
 }
 cpu(op,g,base,index,staticA){return new Promise((resolve,reject)=>{const id=++this.counter;this.jobs.set(id,{resolve,reject});this.worker.postMessage({id,op,g,base,index,staticA})})}
 queue(fn){const p=this.serial.then(fn);this.serial=p.catch(()=>{});return p}
 async compute(g,base,entries,pixels=false,index=0,staticA=-1,scale=1){
  const d=this.device,c=new Float32Array(36);c.set(g.config);c[24]=g.scene.length;c[25]=g.grammar.length;c[26]=g.samples;c[27]=(index%96)/96;c[28]=g.animation.profile;c[29]=g.animation.assembly_variant;c[30]=g.animation.destruction_variant;c[31]=staticA;c[32]=13*scale;c[33]=24*scale;c[34]=this.aw;c[35]=this.ah;
  const size=pixels?390*720*scale*scale*4:10800*4,arrays=[new Float32Array(g.scene.flat()),c,pixels?this.atlas:new Uint32Array([...g.grammar].map(x=>x.charCodeAt(0))),new Float32Array(g.coverage),null,base||new Float32Array(10800),new Uint32Array(900),new Float32Array(2700)],buffers=[];
  let back;try{
   for(let i=0;i<8;i++){const data=arrays[i],b=d.createBuffer({size:Math.max(32,data?.byteLength||size),usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|(i===4?GPUBufferUsage.COPY_SRC:0)});buffers.push(b);if(data)d.queue.writeBuffer(b,0,data);}
   const group=d.createBindGroup({layout:this.layout,entries:buffers.map((buffer,binding)=>({binding,resource:{buffer}}))}),encoder=d.createCommandEncoder();
   for(const entry of entries){const pass=encoder.beginComputePass();pass.setPipeline(this.pipelines[entry]);pass.setBindGroup(0,group);pass.dispatchWorkgroups(Math.ceil((entry==='raster_pixels'?size/4:900)/64));pass.end();}
   back=d.createBuffer({size,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ});encoder.copyBufferToBuffer(buffers[4],0,back,0,size);d.queue.submit([encoder.finish()]);await back.mapAsync(GPUMapMode.READ);const bytes=back.getMappedRange().slice(0);back.unmap();return pixels?new Uint8ClampedArray(bytes):new Float32Array(bytes);
  }finally{buffers.forEach(b=>b.destroy());back?.destroy();}
 }
 async render(g){const start=performance.now();const data=await this.queue(()=>this.backend==='WebGPU'?this.compute(g,null,['render_cells']):this.cpu('render',g));validateCells(data);this.lastMs=performance.now()-start;return data;}
 async frame(base,g,index,staticA=-1){const t=(index%96)/96;if(staticA<0&&(t>=.32&&t<.46||t>=.88&&t<.94))return base.slice();const data=await this.queue(()=>this.backend==='WebGPU'?this.compute(g,base,['clear_depth','project_fragments','resolve_fragments'],false,index,staticA):this.cpu('frame',g,base,index,staticA));validateCells(data);return data}
 async image(data,g,scale=1){
  const canvas=document.createElement('canvas');canvas.width=390*scale;canvas.height=720*scale;const ctx=canvas.getContext('2d');
  if(this.backend==='WebGPU'){const pixels=await this.queue(()=>this.compute(g,data,['raster_pixels'],true,0,-1,scale));ctx.putImageData(new ImageData(pixels,canvas.width,canvas.height),0,0);}
  else{ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font=24*scale+'px Consolas,monospace';ctx.textBaseline='top';for(let i=0;i<900;i++){const v=Math.round(data[i*12+1]);ctx.fillStyle='rgb('+v+','+v+','+v+')';ctx.fillText(String.fromCharCode(data[i*12]),i%30*13*scale,Math.floor(i/30)*24*scale);}}
  return canvas.toDataURL('image/png');
 }
}
export {fromAscii,toAscii};