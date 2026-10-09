import {fromAscii,toAscii,validateCells,dimensions,isV3,animateScene,V3_RENDER_DEFAULTS} from './math.js';
export const canonical=o=>JSON.stringify(sort(o));
function sort(o){if(Array.isArray(o))return o.map(sort);if(o&&typeof o==='object')return Object.fromEntries(Object.keys(o).sort().map(k=>[k,sort(o[k])]));return o}
export async function sha(text){const bytes=typeof text==='string'?new TextEncoder().encode(text):text;return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('')}
export async function seal(g){delete g.fingerprint;g.fingerprint=await sha(canonical(g));return g}
export async function checkGenome(g){
 if(!g||!['web-1.0.0','web-3.0.0','web-4.5.0'].includes(g.genome_version))throw Error('This laboratory genome version is not supported.');
 const copy=structuredClone(g);delete copy.fingerprint;if(await sha(canonical(copy))!==g.fingerprint)throw Error('DNA fingerprint mismatch.');
 if(!Array.isArray(g.scene)||!g.scene.length||g.scene.length>160||g.scene.some(r=>r.length!==16||r.some((x,i)=>!Number.isFinite(x)||Math.abs(x)>(isV3(g)&&[11,13,15].includes(i)?160:100))))throw Error('Invalid geometry.');
 for(const r of g.scene){if(!Number.isInteger(r[0])||r[0]<0||r[0]>11||r.slice(4,7).some(x=>x<.001)||r[0]===10&&r[12]<3)throw Error('Invalid primitive.');}
 if(!Array.isArray(g.config)||g.config.length!==24||g.config.some(x=>!Number.isFinite(x)||Math.abs(x)>16777216)||g.config[0]<.1||g.config[2]<.1||g.config[11]<1)throw Error('Invalid render parameters.');
 if(!Array.isArray(g.coverage)||g.coverage.length!==95||g.coverage.some(x=>!Number.isFinite(x)||x<0||x>1)||typeof g.grammar!=='string'||g.grammar.length<1||g.grammar.length>95||!/^[\x20-\x7e]+$/.test(g.grammar)||![1,2,4].includes(g.samples))throw Error('Invalid glyph grammar.');
 const a=g.animation;if(!a||a.fps!==12||(!isV3(g)?a.seconds!==8:!Number.isInteger(a.seconds)||a.seconds<2||a.seconds>15)||!Number.isInteger(a.profile)||a.profile<0||a.profile>22||![a.assembly_variant,a.destruction_variant].every(x=>Number.isInteger(x)&&x>=0&&x<10))throw Error('Invalid motion definition.');
 if(!isV3(g)&&g.grid!==undefined&&dimensions(g).width!==30)throw Error('Legacy DNA requires its original 30 by 30 grid.');
 if(g.genome_version==='web-3.0.0'&&!['30,30','50,50'].includes(String(g.grid)))throw Error('V3 DNA requires its frozen native grid.');
 if(g.genome_version==='web-4.5.0'){
  const budget=g.density_budget;if(!budget||Object.keys(budget).length!==6||['primary','secondary','tertiary','stage','ambient_code','motion'].some(k=>!Number.isFinite(budget[k])||budget[k]<=0||budget[k]>1))throw Error('Invalid V4.5 layer density budget.');
  if(!g.encoder||g.encoder.version!=='4.5.0'||!Number.isInteger(g.encoder.method_variant)||g.encoder.method_variant<0||g.encoder.method_variant>=20)throw Error('Invalid V4.5 encoder.');
  for(const key of ['noise_budget','temporal_lock','depth_weight','edge_weight'])if(!Number.isFinite(g.encoder[key])||g.encoder[key]<0||g.encoder[key]>1)throw Error('Invalid encoder parameter.');
  const c=g.composition;if(!c||!['Tight Portrait','Head-and-Torso','Half-Body','Full-Body','Wide Creature','Vertical Relic','Mask/Icon','Distributed Abstract'].includes(c.mode)||!Number.isFinite(c.target_dimension)||c.target_dimension<.65||c.target_dimension>.88||!Number.isFinite(c.safe_margin)||c.safe_margin<0||c.safe_margin>.15)throw Error('Invalid V4.5 composition.');
  if(!g.presentation||g.presentation.width!==g.presentation.height||![300,600,1200].includes(g.presentation.width))throw Error('Invalid presentation.');
 }
 if(isV3(g)){
  dimensions(g);if(!Array.isArray(g.grid))throw Error('V3 DNA requires a native ASCII grid.');
  const m=g.motion;if(!m||typeof m!=='object'||!Number.isInteger(m.kind??m.type)||(m.kind??m.type)<0||(m.kind??m.type)>9||!Number.isFinite(m.amplitude??m.intensity)||(m.amplitude??m.intensity)<0||(m.amplitude??m.intensity)>1||!Number.isInteger(m.speed)||m.speed<1||m.speed>4||!Number.isFinite(m.phase)||Math.abs(m.phase)>Math.PI*2||a.enabled!==true)throw Error('Invalid V3 motion definition.');
  if(m.kind!==undefined&&m.type!==undefined&&m.kind!==m.type||m.amplitude!==undefined&&m.intensity!==undefined&&m.amplitude!==m.intensity)throw Error('Conflicting motion aliases.');
  if(m.frequency!==undefined&&(!Number.isFinite(m.frequency)||Math.abs(m.frequency)>32))throw Error('Invalid motion parameter.');
  for(const key of ['limbs','joints','breath','orbit'])if(m[key]!==undefined&&typeof m[key]!=='boolean'&&(!Number.isFinite(m[key])||Math.abs(m[key])>32))throw Error('Invalid motion parameter.');
  if(m.axis!==undefined&&(!Array.isArray(m.axis)||m.axis.length!==3||m.axis.some(x=>!Number.isFinite(x)||Math.abs(x)>1)))throw Error('Invalid motion axis.');
  if(m.seed!==undefined&&(!Number.isInteger(m.seed)||m.seed<0||m.seed>4294967295))throw Error('Invalid motion seed.');
  const ranges={blend:[0,.12],ambient:[0,1],fill:[0,1],ao:[0,1],rim:[0,1],contrast:[.5,2],contour:[0,1]};
  if(g.rendering!==undefined){if(!g.rendering||typeof g.rendering!=='object'||Array.isArray(g.rendering)||Object.keys(g.rendering).some(k=>!ranges[k]))throw Error('Invalid V3 lighting profile.');for(const [key,value] of Object.entries(g.rendering)){const [lo,hi]=ranges[key];if(!Number.isFinite(value)||value<lo||value>hi)throw Error('Invalid V3 lighting parameter.');}}
  for(const row of g.scene)if(!Number.isInteger(row[13])||row[13]<0||!Number.isInteger(row[14])||row[14]<0||row[14]>4||!Number.isInteger(row[15])||row[15]<0)throw Error('Invalid procedural geometry ownership.');
  if(g.config.slice(7,10).every(x=>x===0)||g.config[0]>8||g.config[2]>3||g.config[22]<0||g.config[22]>1)throw Error('Invalid V3 render bounds.');
 }
 return g;
}
export async function readJson(path){const r=await fetch(path);if(!r.ok)throw Error('Could not load '+path+' ('+r.status+').');if(!path.endsWith('.gz'))return r.json();let bytes=new Uint8Array(await r.arrayBuffer());if(bytes[0]===31&&bytes[1]===139){if(!globalThis.DecompressionStream)throw Error('This browser does not support compressed collection records. Use a current Chrome, Edge, Firefox or Safari.');const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));return JSON.parse(await new Response(stream).text());}return JSON.parse(new TextDecoder().decode(bytes));}
export class Repository {
 async init(){[this.config,this.registry,this.catalog]=await Promise.all([readJson('/data/config.json'),readJson('/data/registry.json'),readJson('/data/catalog.json')]);this.blocks=new Map();this.subjects=Object.fromEntries(Object.keys(this.config.families).map(f=>[f,[...new Set(this.catalog.filter(m=>m.family===f).map(m=>m.subject))]]));return this}
 async item(edition){if(!Number.isInteger(edition)||edition<1||edition>3333)throw Error('Invalid edition.');const block=Math.floor((edition-1)/100);if(!this.blocks.has(block))this.blocks.set(block,readJson('/data/block-'+String(block).padStart(2,'0')+'.json.gz'));const a=(await this.blocks.get(block)).find(x=>x.edition===edition);if(!a||await sha(a.ascii)!==a.metadata.canonical_hash)throw Error('Canonical artwork verification failed.');return a}
 async foundation(family,subject,style,seed){let rows=this.catalog.filter(m=>m.family===family&&m.subject===subject);rows.sort((a,b)=>(b.style_id===style)-(a.style_id===style)||a.edition-b.edition);return this.item(rows[parseInt(seed.slice(6,10),16)%Math.min(4,rows.length)].edition)}
}
export class Engine {
 constructor(){this.backend='CPU';this.deviceName='CPU reference · browser worker';this.lastMs=null;this.jobs=new Map();this.serial=Promise.resolve();this.counter=0;this.pools=new Map();this.metrics={renders:0,frames:0,allocations:0,gpuBytes:0};}
 async init(){
  this.font();this.worker=new Worker(new URL('./cpu-worker.js',import.meta.url),{type:'module'});this.worker.onmessage=e=>{const j=this.jobs.get(e.data.id);if(j){this.jobs.delete(e.data.id);e.data.error?j.reject(Error(e.data.error)):j.resolve(e.data.result);}};
  this.worker.onerror=()=>{for(const j of this.jobs.values())j.reject(Error('The browser worker failed. Reload to restart the renderer.'));this.jobs.clear();};
  try{
   if(!navigator.gpu)throw Error('WebGPU is unavailable in this browser.');this.adapter=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});if(!this.adapter)throw Error('No WebGPU adapter.');this.device=await this.adapter.requestDevice();
   if(this.device.limits.maxStorageBuffersPerShaderStage<8||this.device.limits.maxStorageBufferBindingSize<3000000)throw Error('The GPU cannot allocate the required native renderer buffers.');
   this.device.lost.then(info=>{if(!this.native){this.backend='CPU';this.deviceName='CPU reference · GPU device lost';this.fallbackReason=info.message;}this.clearPools();});
   const response=await fetch('/renderer.wgsl?v=3',{cache:'no-store'});if(!response.ok)throw Error('The renderer shader could not be loaded.');const module=this.device.createShaderModule({code:await response.text()}),info=await module.getCompilationInfo(),errors=info.messages.filter(m=>m.type==='error');if(errors.length)throw Error(errors.map(e=>e.message).join(' '));
   this.layout=this.device.createBindGroupLayout({entries:Array.from({length:8},(_,binding)=>({binding,visibility:GPUShaderStage.COMPUTE,buffer:{type:binding===4||binding===6||binding===7?'storage':'read-only-storage'}}))});
   const layout=this.device.createPipelineLayout({bindGroupLayouts:[this.layout]});this.pipelines={};for(const entryPoint of ['render_cells','clear_depth','project_fragments','resolve_fragments','raster_pixels'])this.pipelines[entryPoint]=await this.device.createComputePipelineAsync({layout,compute:{module,entryPoint}});
   this.backend='WebGPU';this.deviceName=this.adapter.info?.description||[this.adapter.info?.vendor,this.adapter.info?.architecture].filter(Boolean).join(' ')||'WebGPU high-performance adapter';
  }catch(e){this.fallbackReason=e.message;this.backend='CPU';this.clearPools();}
  return this;
 }
 font(){
  const canvas=document.createElement('canvas');canvas.width=40;canvas.height=48;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.font='48px Consolas,monospace';const width=Math.ceil(ctx.measureText('M').width);canvas.width=width;ctx.font='48px Consolas,monospace';ctx.textBaseline='top';this.aw=width;this.ah=48;this.fontName='48px Consolas,monospace';this.atlas=new Uint32Array(width*48*95);this.coverage=[];
  for(let i=0;i<95;i++){ctx.clearRect(0,0,width,48);ctx.fillStyle='white';ctx.fillText(String.fromCharCode(i+32),0,0);const data=ctx.getImageData(0,0,width,48).data;let sum=0;for(let p=0;p<width*48;p++){const v=data[p*4+3];this.atlas[i*width*48+p]=v;sum+=v;}this.coverage.push(sum/(255*width*48));}
 }
 cpu(op,g,base,index,staticA){return new Promise((resolve,reject)=>{const id=++this.counter;this.jobs.set(id,{resolve,reject});this.worker.postMessage({id,op,g,base,index,staticA});});}
 queue(fn){const p=this.serial.then(fn);this.serial=p.catch(()=>{});return p;}
 attachNative(adapter){if(!adapter||adapter.status?.backend!=='CUDA'||!['render','frame','image'].every(k=>typeof adapter[k]==='function'))throw Error('A verified CUDA renderer adapter is required.');this.native=adapter;this.backend='CUDA';this.deviceName=adapter.status.device||adapter.status.gpu||'NVIDIA CUDA';this.fallbackReason=null;if(Array.isArray(adapter.status.coverage)&&adapter.status.coverage.length===95&&adapter.status.coverage.every(x=>Number.isFinite(x)&&x>=0&&x<=1)){this.coverage=[...adapter.status.coverage];this.fontName=adapter.status.fontName||(typeof adapter.status.font==='string'?adapter.status.font:adapter.status.font?.font)||this.fontName;}return this;}
 clearPools(){for(const pool of this.pools.values()){pool.buffers.forEach(b=>b.destroy());pool.back.destroy();}this.pools.clear();this.metrics.gpuBytes=0;}
 dispose(){this.clearPools();this.worker?.terminate();for(const j of this.jobs.values())j.reject(Error('Renderer closed.'));this.jobs.clear();this.device?.destroy();}
 pool(key,size){
  const existing=this.pools.get(key);if(existing&&existing.size>=size)return existing;
  if(existing){existing.buffers.forEach(b=>b.destroy());existing.back.destroy();this.metrics.gpuBytes-=existing.bytes;}
  const limits=this.device.limits;if(size>limits.maxStorageBufferBindingSize||size>limits.maxBufferSize)throw Error('This raster size exceeds the GPU allocation limit.');
  const capacity=14400,sizes=[160*16*4,64*4,key==='pixels'?this.atlas.byteLength:95*4,95*4,size,capacity*12*4,capacity*4,capacity*3*4],buffers=sizes.map((bytes,i)=>this.device.createBuffer({size:Math.max(32,bytes),usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|(i===4?GPUBufferUsage.COPY_SRC:0)})),back=this.device.createBuffer({size,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ}),bytes=sizes.reduce((a,b)=>a+b,0)+size;
  const pool={buffers,back,size,bytes,group:this.device.createBindGroup({layout:this.layout,entries:buffers.map((buffer,binding)=>({binding,resource:{buffer}}))})};this.pools.set(key,pool);this.metrics.allocations+=9;this.metrics.gpuBytes+=bytes;if(key==='pixels')this.device.queue.writeBuffer(buffers[2],0,this.atlas);return pool;
 }
 async compute(g,base,entries,pixels=false,index=0,staticA=-1,scale=1){
  const d=this.device,{width,height,count}=dimensions(g),c=new Float32Array(64),v3=isV3(g),settings={...V3_RENDER_DEFAULTS,...g.rendering};c.set(g.config);c[24]=g.scene.length;c[25]=g.grammar.length;c[26]=g.samples;c[27]=((index%(g.animation.fps*g.animation.seconds))+g.animation.fps*g.animation.seconds)%(g.animation.fps*g.animation.seconds)/(g.animation.fps*g.animation.seconds);if(v3)c[27]=(c[27]+.32)%1;c[28]=g.animation.profile;c[29]=g.animation.assembly_variant;c[30]=g.animation.destruction_variant;c[31]=staticA;c[32]=13*scale;c[33]=24*scale;c[34]=this.aw;c[35]=this.ah;c[36]=width;c[37]=height;c[38]=v3?3:1;c[39]=settings.blend;c[40]=settings.ambient;c[41]=settings.fill;c[42]=settings.ao;c[43]=settings.rim;c[44]=settings.contrast;c[45]=settings.contour;c[46]=width===50?12:10;
  const size=pixels?width*height*13*24*scale*scale*4:count*12*4,pool=this.pool(pixels?'pixels':'cells',size),arrays=[new Float32Array(g.scene.flat()),c,pixels?null:new Uint32Array([...g.grammar].map(x=>x.charCodeAt(0))),new Float32Array(g.coverage),null,base,null,null];
  for(let i=0;i<8;i++)if(arrays[i])d.queue.writeBuffer(pool.buffers[i],0,arrays[i]);
  d.pushErrorScope('validation');const encoder=d.createCommandEncoder();for(const entry of entries){const pass=encoder.beginComputePass();pass.setPipeline(this.pipelines[entry]);pass.setBindGroup(0,pool.group);pass.dispatchWorkgroups(Math.ceil((entry==='raster_pixels'?size/4:count)/64));pass.end();}encoder.copyBufferToBuffer(pool.buffers[4],0,pool.back,0,size);d.queue.submit([encoder.finish()]);const error=await d.popErrorScope();if(error)throw Error(error.message);await pool.back.mapAsync(GPUMapMode.READ,0,size);const bytes=pool.back.getMappedRange(0,size).slice(0);pool.back.unmap();return pixels?new Uint8ClampedArray(bytes):new Float32Array(bytes);
 }
 async render(g){
  const start=performance.now(),data=await this.queue(()=>this.backend==='CUDA'?this.native.render(g):this.backend==='WebGPU'?this.compute(g,null,['render_cells']):this.cpu('render',g));validateCells(data,g.grid);this.lastMs=performance.now()-start;this.metrics.renders++;return data;
 }
 async frame(base,g,index,staticA=-1){
  validateCells(base,g.grid);if(!Number.isInteger(index)||Math.abs(index)>10000000||!Number.isFinite(staticA)||staticA< -1||staticA>1)throw Error('Invalid frame parameters.');const total=g.animation.fps*g.animation.seconds,t=((index%total)+total)%total/total;
  if(isV3(g)&&t===0&&staticA<0)return base.slice();if(!isV3(g)&&staticA<0&&(t>=.32&&t<.46||t>=.88&&t<.94))return base.slice();
  const start=performance.now(),data=await this.queue(async()=>{
   if(this.backend==='CUDA')return this.native.frame(base,g,index,staticA);
   if(this.backend!=='WebGPU'&&!(this.backend==='CUDA'&&this.device))return this.cpu('frame',g,base,index,staticA);
   if(!isV3(g))return this.compute(g,base,['clear_depth','project_fragments','resolve_fragments'],false,index,staticA);
   const pose=await this.compute(animateScene(g,index),null,['render_cells']);if(staticA<0&&!g.animation.legendary&&g.rarity!=='LEGENDARY')return pose;const ft=(t+.32)%1;if(staticA<0&&(ft>=.32&&ft<.46||ft>=.88&&ft<.94))return pose;return this.compute(g,pose,['clear_depth','project_fragments','resolve_fragments'],false,index,staticA);
  });validateCells(data,g.grid);this.lastFrameMs=performance.now()-start;this.metrics.frames++;return data;
 }
 async image(data,g,scale=1){
  if(!Number.isInteger(scale)||scale<1||scale>4)throw Error('Raster scale must be an integer from one to four.');const {width,height,count}=dimensions(g);validateCells(data,g.grid);const canvas=document.createElement('canvas');canvas.width=width*13*scale;canvas.height=height*24*scale;const ctx=canvas.getContext('2d');
  if(this.backend==='CUDA')return this.queue(()=>this.native.image(data,g,scale));
  if(this.backend==='WebGPU'||this.backend==='CUDA'&&this.device){const pixels=await this.queue(()=>this.compute(g,data,['raster_pixels'],true,0,-1,scale));ctx.putImageData(new ImageData(pixels,canvas.width,canvas.height),0,0);}
  else{ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font=24*scale+'px Consolas,monospace';ctx.textBaseline='top';for(let i=0;i<count;i++){const v=Math.round(data[i*12+1]);ctx.fillStyle='rgb('+v+','+v+','+v+')';ctx.fillText(String.fromCharCode(data[i*12]),i%width*13*scale,Math.floor(i/width)*24*scale);}}
  return canvas.toDataURL('image/png');
 }
}
export {fromAscii,toAscii,dimensions,V3_RENDER_DEFAULTS};
