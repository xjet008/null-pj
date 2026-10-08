import {Engine,Repository,seal,checkGenome,sha,canonical,toAscii,fromAscii,readJson} from './engine.js';
import {rnd} from './math.js';
const grammars=['01','0123456789ABCDEF','0123456789','()[]{}<>','+-=*%&|!','/\\|_-','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz','0123456789ABCDEF@#$%&*','0123456789+-=()[]','.,:;irsXA253hMHGS#9B&@'];
const modes=['RECOGNIZABLE','FRAGMENTED','APPARENT CHAOS','ENCRYPTED','ANATOMICAL RECONSTRUCTION','WIRESPACE','DUALITY','DATA FOSSIL','VOID ENTITY','DIMENSIONAL ANOMALY'];
const modIndex=id=>Math.max(0,Number(String(id).split('.')[1])-1);
const materials={'Bone':[18,.12,.15,1],'Charcoal':[8,.02,.08,.85],'Dark metal':[34,.45,.12,.85],'Polished steel':[70,.9,.24,1],'Chrome':[110,1.6,.3,1],'Glass-like':[100,1.2,.55,.72],'Crystalline':[85,1.3,.43,.9],'Ceramic':[42,.38,.12,1],'Porous stone':[8,.03,.09,.9],'Fog':[5,.02,.42,.5],'Smoke':[4,.01,.35,.42],'Organic tissue':[16,.16,.16,.92],'Synthetic armor':[60,.7,.25,.96],'Worn machinery':[28,.3,.15,.87],'Etched circuitry':[48,.6,.23,1]};
const lights=[[-.25,1,.75],[-1,.35,.6],[.1,-1,.7],[1,.1,-.2],[0,.2,-1],[.8,.8,1],[-.4,.6,1],[-1,.15,.5],[-.8,.3,.4],[0,1,.3]];
export class Studio {
 async init(){this.repo=await new Repository().init();this.engine=await new Engine().init();this.cache=new Map();return this}
 async render(g,reveal=false){await checkGenome(g);const base=await this.engine.render(g);let data=base;if(!reveal&&!g.animation.enabled&&['FRAGMENTED','APPARENT CHAOS'].includes(g.appearance))data=await this.engine.frame(base,g,0,1-g.parameters.fragmentation);const packet={id:g.fingerprint,genome:g,ascii:toAscii(data),luminance:Array.from({length:900},(_,i)=>data[i*12+1]),preview:await this.engine.image(data,g),operators:g.scene,base,data,performance:{backend:this.engine.backend,gpu_ms:this.engine.backend==='WebGPU'?this.engine.lastMs:null,render_ms:this.engine.lastMs}};this.cache.set(packet.id,packet);return packet}
 async generate(o){
  const r=this.repo,seed=await sha(o.seed||crypto.randomUUID()),v=o.overrides||{},rule=r.registry.traits.find(t=>t.id===v.style&&t.families.includes(o.family)&&t.families.length===1);if(!rule)throw Error('Choose a foundation style.');const record=await r.foundation(o.family,v.subject,v.style,seed),spec=rule.rules,scene=structuredClone(record.scene),c=record.cfg.slice(),n=parseInt(seed.slice(0,6),16),params={entropy:v.entropy??.12,fragmentation:v.fragmentation??.18,complexity:v.complexity??.7,contrast:v.contrast??1.05};
  for(let i=0;i<scene.length;i++){const row=scene[i];for(let axis=0;axis<3;axis++){const factor=.84+.2*spec.proportions[axis]+(rnd(n+i*37+axis*911)-.5)*.06;row[axis+1]*=factor;row[axis+4]*=factor;}if(!row[10]){row[7]+=(rnd(n+i*149)-.5)*spec.curvature*.12;row[8]+=(rnd(n+i*997)-.5)*(1-spec.symmetry)*.3;}}
  const add=(k,x,y,z,sx,sy,sz,rx=0,ry=0,rz=0,extra=0)=>scene.push([k,x,y,z,sx,sy,sz,rx,ry,rz,0,scene.length+1,extra,0,0,0]);
  const top=record.scene.reduce((m,row)=>row[10]?m:Math.max(m,row[2]+row[5]),0);
  if(spec.feature==='horns')for(const s of [-1,1])add(4,s*.35,top-.03,0,.10,.24,.1,0,0,-s*.4);
  if(spec.feature==='wings')for(const s of [-1,1])add(7,s*.54,.1,-.1,.32,.46,.04,0,0,s*.55,.025);
  if(spec.feature==='armor')for(const s of [-1,1])add(7,s*.35,.1,.12,.12,.2,.10,0,0,s*.2,.025);
  const count=Math.floor(params.complexity*(o.rarity==='LEGENDARY'?12:7));for(let i=0;i<count;i++){const row=scene.find((x,j)=>!x[10]&&j>i&&x[4]>.05)||scene[0],angle=rnd(n+i*863)*Math.PI*2;add(0,row[1]+Math.cos(angle)*row[4]*.82,row[2]+(rnd(n+i*197)-.5)*row[5]*1.5,row[3]+row[6]*.7,.018+.015*rnd(n+i*887),.025,.025);}
  const modifiers={...record.metadata.modifiers,T01:v.camera,T03:v.lighting,T05:v.glyph};for(let i=2;i<=12;i++){const prefix='T'+String(i).padStart(2,'0');if([4,6,7,8,9,10].includes(i))modifiers[prefix]=prefix+'.'+String(1+Math.floor(rnd(n+i*7919)*10)).padStart(2,'0');}
  const camera=modIndex(v.camera),lighting=modIndex(v.lighting),mat=materials[spec.material]||materials.Bone;
  c[0]=o.family==='ANIMALS'?5.4:o.family==='CHARACTERS'?4.25:3.65;c[1]=camera===6?1:0;c[3]=[0,.55,-.55,1.35,0,0,.15,.25,0,0][camera]+(rnd(n+177)-.5)*.12;c[4]=(camera===4?-.35:camera===5?.35:0)+(rnd(n+399)-.5)*.06;c[5]=record.cfg[5];c[6]=Object.keys(r.config.rarities).indexOf(o.rarity);c.splice(7,3,...lights[lighting]);c[10]=mat[3];c[11]=mat[0];c[12]=mat[1];c[13]=mat[2];c[14]=modIndex(modifiers.T04);c[15]=spec.surface_frequency;c[16]=params.contrast;c[17]=Math.max(0,modes.indexOf(v.appearance));c[18]=lighting;c[19]=modIndex(modifiers.T10);c[20]=n;c[21]=modIndex(modifiers.T06);c[22]=params.entropy;c[23]=modIndex(modifiers.T09);
  if(v.appearance==='WIRESPACE'){c[5]=4;modifiers.T02='T02.05';}if(v.appearance==='VOID ENTITY'){c[19]=0;modifiers.T10='T10.01';}if(v.appearance==='DATA FOSSIL'){c[14]=4;modifiers.T04='T04.05';}const enabled=o.rarity==='LEGENDARY';if(!enabled){c[23]=0;modifiers.T09='T09.01';}
  const g={genome_version:'web-1.0.0',render_version:'webgpu-sdf-1.0.0',seed,family:o.family,subject:v.subject,rarity:o.rarity,style:rule.id,appearance:v.appearance,modifiers,parameters:params,encryption:'NONE',scene,config:c,grammar:grammars[modIndex(v.glyph)],coverage:this.engine.coverage.slice(),samples:this.engine.backend==='WebGPU'?2:1,font:this.engine.fontName,anatomical_basis:{edition:record.edition,fingerprint:record.metadata.genome_fingerprint},animation:{enabled,profile:Math.max(0,Math.min(22,o.profile||0)),name:enabled?r.config.legends[o.profile||0]:'STATIC',fps:12,seconds:8,fragment_identity:'canonical-surface-cell',assembly_variant:modIndex(modifiers.T07),destruction_variant:modIndex(modifiers.T08)}};
  return this.render(await seal(g));
 }
 async item(e){const record=await this.repo.item(e),m=record.metadata,g=record.dna.algorithm?{edition:e,genome_version:m.genome_version,seed:m.seed,family:m.family,subject:m.subject,rarity:m.rarity,style:m.style_id,appearance:m.appearance,modifiers:m.modifiers,parameters:{entropy:record.cfg[22],fragmentation:.18,complexity:.7,contrast:record.cfg[16]},encryption:'AES-256-GCM · locked',fingerprint:m.genome_fingerprint,animation:{enabled:m.rarity==='LEGENDARY',profile:this.repo.config.legends.indexOf(m.animation_profile)}}:record.dna;
  const p={id:'E'+e,record,genome:g,dna:record.dna,ascii:record.ascii,luminance:record.luminance,operators:record.scene,preview:'/collection/previews/'+String(e).padStart(4,'0')+'.png',performance:{backend:'CUDA · archived canonical',gpu_ms:null}};this.cache.set(p.id,p);return p;
 }
 async regenerate(g,authenticated=false){
  if(g.genome_version==='web-1.0.0')return this.render(g);
  const m=this.repo.catalog.find(x=>x.genome_fingerprint===g.fingerprint&&x.seed===g.seed);if(!m)throw Error('Original DNA does not match a published edition.');const p=await this.item(m.edition);
  if(p.record.dna.algorithm){this.authenticatedDNA ||= new Map();if(authenticated)this.authenticatedDNA.set(g.fingerprint,structuredClone(g));else if(!this.authenticatedDNA.has(g.fingerprint)||canonical(this.authenticatedDNA.get(g.fingerprint))!==canonical(g))throw Error('Unlock the original encrypted envelope with your owner key before regenerating this edition.');}else if(canonical(p.record.dna)!==canonical(g))throw Error('Original DNA has been modified.');return p;
 }
 async unlock(envelope){
  if(!this.key)throw Error('Load your 32-byte owner key in DNA Inspector. It stays in this browser.');
  if(envelope.algorithm!=='AES-256-GCM'||envelope.version!==1||!Number.isInteger(envelope.edition)||typeof envelope.ciphertext!=='string'||envelope.ciphertext.length>100000)throw Error('Unsupported encrypted envelope.');
  const published=await this.repo.item(envelope.edition);if(published.dna.algorithm&&['version','algorithm','edition','nonce','ciphertext','aad'].some(k=>published.dna[k]!==envelope[k]))throw Error('Encrypted envelope does not match this published edition.');const decode=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0)),aad=decode(envelope.aad),expected='NULL-GENESIS/structural-envelope/v1/'+envelope.edition;
  if(new TextDecoder().decode(aad)!==expected)throw Error('Invalid envelope authentication context.');
  const data=await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(envelope.nonce),additionalData:aad,tagLength:128},this.key,decode(envelope.ciphertext)),payload=JSON.parse(new TextDecoder().decode(data));
  if(payload.identity!==payload.genome.fingerprint)throw Error('Decrypted DNA identity mismatch.');const p=await this.regenerate(payload.genome,true);p.genome=payload.genome;p.dna=payload.genome;p.hiddenMessage=payload.hidden_message;return p;
 }
 async loadKey(file){if(file.size!==32)throw Error('The owner key must contain exactly 32 bytes.');this.key=await crypto.subtle.importKey('raw',await file.arrayBuffer(),{name:'AES-GCM'},false,['decrypt']);}
 async reveal(p){
  if(p.record){let g=await this.browserBasis(p);const data=await this.engine.render(g);return {...p,preview:await this.engine.image(data,g),ascii:toAscii(data),luminance:Array.from({length:900},(_,i)=>data[i*12+1]),base:data};}
  return this.render(p.genome,true);
 }
 async browserBasis(p){const m=p.record.metadata;return seal({genome_version:'web-1.0.0',render_version:'webgpu-sdf-1.0.0',seed:m.seed,family:m.family,subject:m.subject,rarity:m.rarity,style:m.style_id,appearance:'RECOGNIZABLE',parameters:{fragmentation:0},encryption:'NONE',scene:p.record.scene,config:p.record.cfg,grammar:grammars[modIndex(m.modifiers.T05)],coverage:this.engine.coverage.slice(),samples:this.engine.backend==='WebGPU'?2:1,animation:{enabled:false,profile:22,name:'STATIC',fps:12,seconds:8,assembly_variant:modIndex(m.modifiers.T07),destruction_variant:modIndex(m.modifiers.T08)}});}
 async sequence(p,progress){
  let g=p.genome,base=p.base;if(p.record){g=await this.browserBasis(p);base=await this.engine.render(g);}if(!base)base=await this.engine.render(g);
  const out={version:'web-1.0.0',grid:[30,30],fps:12,seconds:8,profile:g.animation.enabled?g.animation.name:'Interactive reconstruction',fragment_identity:'canonical-surface-cell',frames:[],luminance:[]};
  for(let i=0;i<96;i++){const data=await this.engine.frame(base,g,i);out.frames.push(toAscii(data));out.luminance.push(Array.from({length:900},(_,j)=>data[j*12+1]));progress?.(i+1);if(i%8===0)await new Promise(r=>setTimeout(r,0));}return out;
 }
 async api(path,body){
  const u=new URL(path,location.origin),q=u.searchParams,r=this.repo;
  if(u.pathname==='/api/config')return {families:Object.keys(r.config.families),rarities:Object.keys(r.config.rarities),subjects:r.subjects,traits:r.registry.traits,config:r.config,modes};
  if(u.pathname==='/api/generate')return this.generate(body);
  if(u.pathname==='/api/item')return this.item(Number(q.get('edition')));
  if(u.pathname==='/api/regenerate')return this.regenerate(body.genome);
  if(u.pathname==='/api/decode')return this.unlock(body.envelope);
  if(u.pathname==='/api/reveal'){const p=body.edition?await this.item(body.edition):this.cache.get(body.id);if(!p)throw Error('Construct an entity first.');return this.reveal(p)}
  if(u.pathname==='/api/animation'){const p=this.cache.get(body.id);if(!p)throw Error('Construct an entity first.');return this.sequence(p,n=>{document.querySelector('#busy b').textContent='Computing frame '+n+' / 96…';});}
  if(u.pathname==='/api/collection'){
   let rows=r.catalog.filter(m=>(!q.get('family')||m.family===q.get('family'))&&(!q.get('rarity')||m.rarity===q.get('rarity'))&&(!q.get('trait')||m.traits.includes(q.get('trait')))&&(!q.get('search')||[m.edition,m.subject,m.primary_style,m.name].join(' ').toLowerCase().includes(q.get('search').toLowerCase())));
   rows.sort(q.get('sort')==='rank'?(a,b)=>a.rank-b.rank:q.get('sort')==='quality'?(a,b)=>b.quality.quality_score-a.quality.quality_score:(a,b)=>a.edition-b.edition);let page=Number(q.get('page')||0),limit=Math.min(100,Number(q.get('limit')||24));return {total:rows.length,items:rows.slice(page*limit,page*limit+limit).map(m=>({...m,animation:m.rarity==='LEGENDARY'}))};
  }
  if(u.pathname==='/api/status')return {hardware:{device:this.engine.deviceName,backend:this.engine.backend,cuda:false,last_gpu_ms:this.engine.lastMs,reason:this.engine.fallbackReason},collection:{accepted:3333,remaining:0,rejected:0,running:false,errors:[],rarity:Object.fromEntries(Object.entries(r.config.rarities).map(([k,v])=>[k,{count:v,quota:v}]))}};
  if(u.pathname==='/api/analytics')return fetch('/reports/analytics.json').then(x=>x.json());
  if(u.pathname==='/api/audit')return fetch('/reports/collection-audit.json').then(x=>x.json());
  if(u.pathname.startsWith('/collection/animations/'))return readJson(path+'.gz');
  throw Error('This operation is not available in the web edition.');
 }
}