import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {webcrypto} from 'node:crypto';
import {Repository,seal,checkGenome,canonical,sha,readJson} from '../dist/engine.js';
import {renderCpu,frameCpu,toAscii,fromAscii,validateCells,inverse,rotate} from '../dist/math.js';
import {Studio} from '../dist/store.js';
import {zip} from '../dist/zip.js';
const root=fileURLToPath(new URL('../dist/',import.meta.url));
const cov=Array.from({length:95},(_,i)=>i/280);cov[0]=0;

// This tests the CPU core and public data. GPU/DOM integration is verified in a browser.
// Every encryption key below is newly generated test data; no owner secret is accessed.
test('NULL GENESIS browser engine and public assets',async t=>{
 const previousFetch=globalThis.fetch,previousLocation=globalThis.location,results={};
 globalThis.crypto??=webcrypto;
 globalThis.fetch=async input=>{
  const u=new URL(String(input),'https://verification.test');
  if(u.pathname==='/already-decoded.json.gz')return new Response('{"decompressedByHost":true}');
  try{const bytes=await fs.readFile(path.join(root,u.pathname));return new Response(bytes,{status:200,headers:{'Content-Type':u.pathname.endsWith('.gz')?'application/gzip':'application/json'}})}catch{return new Response(null,{status:404})}
 };
 globalThis.location={origin:'https://verification.test'};
 let genome,data,ascii,repo,studio,plain,enc;
 const run=async(name,fn)=>{results[name]=false;await t.test(name,async()=>{await fn();results[name]=true;});};
 try{
  await run('CPU render is deterministic and exactly 30 by 30',async()=>{
   genome=await seal({genome_version:'web-1.0.0',render_version:'webgpu-sdf-1.0.0',seed:'1'.repeat(64),family:'SKULLS',subject:'Human',rarity:'COMMON',style:'S031',appearance:'RECOGNIZABLE',parameters:{fragmentation:.5},config:[3.65,0,26/48,.11,.05,0,0,-.25,1,.75,1,18,.12,.15,2,8,1.05,0,0,1,1003,4,.1,0],grammar:'0123456789ABCDEF',coverage:cov,samples:1,scene:[[0,0,0,0,.65,.65,.65,0,0,0,0,1,0,0,0,0]],animation:{enabled:false,profile:4,fps:12,seconds:8,assembly_variant:2,destruction_variant:1}});
   await checkGenome(genome);data=renderCpu(genome);const again=renderCpu(genome);ascii=toAscii(data);validateCells(data);assert.deepEqual(data,again);assert.equal(data.length,10800);const rows=ascii.split('\n');assert.equal(rows.length,31);assert.ok(rows.slice(0,30).every(x=>x.length===30));assert.ok(data.some((v,i)=>i%12===9&&v===1));
   assert.equal(toAscii(fromAscii(ascii,Array.from({length:900},(_,i)=>data[i*12+1]))),ascii);
  });
  await run('96 motion frames preserve canonical holds and loop identity',async()=>{
   assert.deepEqual(frameCpu(data,genome,32),data);assert.deepEqual(frameCpu(data,genome,86),data);assert.deepEqual(frameCpu(data,genome,0),frameCpu(data,genome,96));assert.notEqual(toAscii(frameCpu(data,genome,0)),ascii);for(let i=0;i<96;i++)validateCells(frameCpu(data,genome,i));
   const point=[.2,-.3,.7],rotated=inverse(rotate(point,.4,.2,-.8),.4,.2,-.8);assert.ok(rotated.every((v,i)=>Math.abs(v-point[i])<1e-12));
  });
  await run('Web DNA rejects altered fingerprints and unsafe render parameters',async()=>{
   let bad=structuredClone(genome);bad.scene[0][4]+=.1;await assert.rejects(checkGenome(bad),/fingerprint/);
   bad=structuredClone(genome);bad.scene[0][4]=0;await seal(bad);await assert.rejects(checkGenome(bad),/primitive/);
   bad=structuredClone(genome);bad.samples=100;await seal(bad);await assert.rejects(checkGenome(bad),/grammar/);
   assert.equal(await sha(canonical({z:1,a:{b:2,a:1}})),await sha(canonical({a:{a:1,b:2},z:1})));
  });
  await run('Repository reads real gzip blocks and verifies canonical artwork',async()=>{
   repo=await new Repository().init();assert.equal(repo.catalog.length,3333);const gzip=await fs.readFile(path.join(root,'data/block-00.json.gz'));assert.equal(gzip[0],31);assert.equal(gzip[1],139);
   const independentStream=new Response(gzip).body.pipeThrough(new DecompressionStream('gzip')),block=await new Response(independentStream).json(),record=await repo.item(6);assert.deepEqual(record,block.find(x=>x.edition===6));assert.equal(await sha(record.ascii),record.metadata.canonical_hash);plain=block.find(x=>!x.dna.algorithm);enc=block.find(x=>x.dna.algorithm);assert.ok(plain&&enc);
   assert.deepEqual(await readJson('/already-decoded.json.gz'),{decompressedByHost:true});await assert.rejects(readJson('/missing.json.gz'),/404/);await assert.rejects(repo.item(0),/edition/);await assert.rejects(repo.item(3334),/edition/);
   studio=new Studio();studio.repo=repo;studio.cache=new Map();studio.engine={backend:'CPU',coverage:cov,fontName:'test-font',deviceName:'CPU test',lastMs:0,async render(g){const begin=performance.now(),result=renderCpu(g);this.lastMs=performance.now()-begin;return result},async frame(base,g,index,staticA=-1){return frameCpu(base,g,index,staticA)},async image(){return 'data:image/png;base64,'}};
  });
  await run('Compressed native legendary animation remains 96 valid frames',async()=>{
   const legend=repo.catalog.find(m=>m.rarity==='LEGENDARY'),url='/collection/animations/'+String(legend.edition).padStart(4,'0')+'.frames.json',animation=await studio.api(url);assert.equal(animation.frames.length,96);assert.equal(animation.luminance.length,96);assert.equal(animation.fps,12);assert.equal(animation.seconds,8);
   for(let i=0;i<96;i++){const rows=animation.frames[i].split('\n');assert.equal(rows.length,31);assert.ok(rows.slice(0,30).every(row=>row.length===30));assert.equal(animation.luminance[i].length,900);assert.ok(animation.luminance[i].every(v=>Number.isFinite(v)&&v>=0&&v<=255));}
  });
  for(const family of ['SKULLS','CHARACTERS','ANIMALS'])await run(family+' generation and DNA regeneration are deterministic',async()=>{
   const subject=repo.subjects[family][0],style=repo.registry.traits.find(t=>t.families.length===1&&t.families[0]===family).id,options={family,rarity:'COMMON',seed:'web-verification-'+family,profile:0,overrides:{subject,style,appearance:'RECOGNIZABLE',camera:'T01.02',lighting:'T03.01',glyph:'T05.10',entropy:.12,fragmentation:.18,complexity:.7,contrast:1.05}},a=await studio.generate(options),b=await studio.generate(options),c=await studio.regenerate(a.genome);assert.equal(a.id,b.id);assert.equal(a.ascii,b.ascii);assert.equal(a.ascii,c.ascii);assert.deepEqual(a.luminance,b.luminance);assert.equal(a.genome.scene.length,a.operators.length);validateCells(a.data);
  });
  await run('Original plain DNA rejects edits and locked DNA rejects copied identity',async()=>{
   assert.equal((await studio.regenerate(plain.dna)).ascii,plain.ascii);const altered=structuredClone(plain.dna);altered.parameters.contrast+=.1;await assert.rejects(studio.regenerate(altered),/modified|fingerprint/);const forged=structuredClone(plain.dna);forged.fingerprint=enc.metadata.genome_fingerprint;forged.seed=enc.metadata.seed;forged.parameters.contrast=.251;await assert.rejects(studio.regenerate(forged),/owner key/);
  });
  await run('Synthetic AES unlock succeeds and rejects forged envelope, bad AAD and wrong key',async()=>{
   const keyBytes=crypto.getRandomValues(new Uint8Array(32)),key=await crypto.subtle.importKey('raw',keyBytes,{name:'AES-GCM'},false,['encrypt']),nonce=crypto.getRandomValues(new Uint8Array(12)),encode=new TextEncoder(),b64=a=>Buffer.from(a).toString('base64'),aad=encode.encode('NULL-GENESIS/structural-envelope/v1/'+plain.edition),payload=encode.encode(JSON.stringify({genome:plain.dna,identity:plain.dna.fingerprint,hidden_message:'Synthetic verification message'})),ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:aad,tagLength:128},key,payload),envelope={algorithm:'AES-256-GCM',version:1,edition:plain.edition,nonce:b64(nonce),aad:b64(aad),ciphertext:b64(ciphertext)};
   await studio.loadKey(new Blob([keyBytes]));const unlocked=await studio.unlock(envelope);assert.equal(unlocked.ascii,plain.ascii);assert.equal(unlocked.genome.fingerprint,plain.dna.fingerprint);assert.equal(unlocked.hiddenMessage,'Synthetic verification message');
   const damaged=structuredClone(envelope),bytes=Buffer.from(damaged.ciphertext,'base64');bytes[4]^=1;damaged.ciphertext=bytes.toString('base64');await assert.rejects(studio.unlock(damaged));const wrongAAD=structuredClone(envelope);wrongAAD.edition+=1;await assert.rejects(studio.unlock(wrongAAD),/authentication|envelope/);await assert.rejects(studio.loadKey(new Blob([new Uint8Array(31)])),/32 bytes/);
   const fake=structuredClone(plain.dna);fake.fingerprint=enc.metadata.genome_fingerprint;fake.seed=enc.metadata.seed;const forgedAAD=encode.encode('NULL-GENESIS/structural-envelope/v1/'+enc.edition),forgedCipher=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce,additionalData:forgedAAD,tagLength:128},key,encode.encode(JSON.stringify({genome:fake,identity:fake.fingerprint,hidden_message:'Forged'}))),forged={algorithm:'AES-256-GCM',version:1,edition:enc.edition,nonce:b64(nonce),aad:b64(forgedAAD),ciphertext:b64(forgedCipher)};await assert.rejects(studio.unlock(forged),/published edition/);await assert.rejects(studio.unlock(enc.dna));studio.key=null;await assert.rejects(studio.unlock(envelope),/owner key/);
  });
  await run('ZIP export has valid offsets, Unicode names, binary bytes and known CRC values',async()=>{
   // Expected CRC values were independently computed with Python zlib.crc32.
   const fixtures=[['native/art.txt',('A'.repeat(30)+'\n').repeat(30),2357634693],['unicode/雪.txt','ASCII – café',1888807170],['bytes.bin',new Uint8Array([0,1,128,255]),906478317],['empty.txt','',0]],blob=zip(fixtures.map(([name,input])=>[name,input])),bytes=new Uint8Array(await blob.arrayBuffer()),view=new DataView(bytes.buffer),decoder=new TextDecoder(),encoder=new TextEncoder();let offset=0;const localOffsets=[];
   for(const [name,input,crc] of fixtures){localOffsets.push(offset);assert.equal(view.getUint32(offset,true),0x04034b50);assert.equal(view.getUint16(offset+6,true),0x800);assert.equal(view.getUint16(offset+8,true),0);assert.equal(view.getUint32(offset+14,true),crc);const size=view.getUint32(offset+18,true),nameLength=view.getUint16(offset+26,true),extraLength=view.getUint16(offset+28,true);assert.equal(view.getUint32(offset+22,true),size);assert.equal(decoder.decode(bytes.slice(offset+30,offset+30+nameLength)),name);const begin=offset+30+nameLength+extraLength,expected=typeof input==='string'?encoder.encode(input):input;assert.deepEqual(bytes.slice(begin,begin+size),expected);offset=begin+size;}
   const centralOffset=offset;for(let i=0;i<fixtures.length;i++){assert.equal(view.getUint32(offset,true),0x02014b50);assert.equal(view.getUint32(offset+16,true),fixtures[i][2]);assert.equal(view.getUint32(offset+42,true),localOffsets[i]);const nameLength=view.getUint16(offset+28,true);assert.equal(decoder.decode(bytes.slice(offset+46,offset+46+nameLength)),fixtures[i][0]);offset+=46+nameLength;}
   assert.equal(view.getUint32(offset,true),0x06054b50);assert.equal(view.getUint16(offset+8,true),4);assert.equal(view.getUint16(offset+10,true),4);assert.equal(view.getUint32(offset+12,true),offset-centralOffset);assert.equal(view.getUint32(offset+16,true),centralOffset);assert.equal(offset+22,bytes.length);
  });
  const report={passed:Object.values(results).every(Boolean),runtime:'Node.js with native DecompressionStream and Web Crypto',scope:'CPU native30x30 and 96 motion frames; all three family foundations; compressed public records/animation; DNA integrity; AES with newly generated synthetic key; ZIP binary, UTF-8 and independently known CRC values',owner_secret_accessed:false,checks:results};await fs.writeFile(path.join(root,'reports/web-engine-checks.json'),JSON.stringify(report,null,2)+'\n');assert.ok(report.passed,'One or more engine checks failed');
 }finally{globalThis.fetch=previousFetch;if(previousLocation===undefined)delete globalThis.location;else globalThis.location=previousLocation;}
});