import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {webcrypto} from 'node:crypto';
import {Studio,decodeAnimation} from '../dist/store.js';
import {Repository,readJson,canonical,sha,checkGenome} from '../dist/engine.js';
import {fromAscii} from '../dist/math.js';
import {NativeBridge} from '../dist/native-bridge.js';
globalThis.crypto??=webcrypto;
const root=new URL('../dist/',import.meta.url);
test('V3 DNA and cached timelines preserve identity and reject tampering with a synthetic key',async()=>{
 const originalFetch=globalThis.fetch,originalLocation=globalThis.location;
 globalThis.location={origin:'https://test.example',hostname:'test.example'};
 globalThis.fetch=async input=>{try{return new Response(await readFile(new URL(new URL(String(input),location.origin).pathname.slice(1),root)))}catch{return new Response(null,{status:404})}};
 try{
  const record=await readJson('/v3/experiments/E025.json.gz'),g=record.genome;await checkGenome(g);
  const s=new Studio();s.cache=new Map();s.v3Catalog=[];s.engine={backend:'CPU',async render(){return fromAscii(record.ascii,record.luminance,g.grid)},async image(){return 'data:image/png;base64,'}};
  const keyBytes=crypto.getRandomValues(new Uint8Array(32));await s.loadKey(new Blob([keyBytes]));const e=await s.encryptV3(g),p=await s.unlockV3(e);
  assert.equal(p.genome.fingerprint,g.fingerprint);assert.equal(p.ascii,record.ascii);assert.equal(e.version,3);assert.equal(e.genome_version,'web-3.0.0');assert.equal(Buffer.from(e.aad,'base64').toString(),'NULL-GENESIS/web-genome/v3/'+g.fingerprint);assert.equal(e.genome,undefined);
  const bad=structuredClone(e),cipher=Buffer.from(bad.ciphertext,'base64');cipher[7]^=1;bad.ciphertext=cipher.toString('base64');await assert.rejects(s.unlockV3(bad));
  await assert.rejects(s.unlockV3({...e,fingerprint:'f'.repeat(64)}),/context/);
  s.key=null;await assert.rejects(s.unlockV3(e),/owner key/);await s.loadKey(new Blob([crypto.getRandomValues(new Uint8Array(32))]));await assert.rejects(s.unlockV3(e));
  const packed=await readJson('/v3/experiments/E025.frames.json.gz'),a=decodeAnimation(packed);assert.equal(a.frames.length,g.animation.fps*g.animation.seconds);assert.equal(a.frames[0],record.ascii);assert.deepEqual(a.grid,g.grid);assert(a.frames.some(f=>f!==a.frames[0]));await assert.rejects(async()=>decodeAnimation({...packed,cells:packed.cells.slice(0,-8)}),/truncated/);
  const bytes=Buffer.from(packed.cells,'base64');bytes[0]=0;assert.throws(()=>decodeAnimation({...packed,cells:bytes.toString('base64')}),/ASCII/);
  const repo=await new Repository().init();s.repo=repo;s.v3Registry=await readJson('/data/traits-v3.json');s.v3Recipes=await readJson('/data/recipes-v3.json');s.engine.coverage=g.coverage;s.engine.fontName=g.font;
  const block=JSON.parse(gunzipSync(await readFile(new URL('data/block-00.json.gz',root)))),plain=block.find(r=>!r.dna.algorithm),before=canonical(plain.dna);s.authenticatedDNA=new Map();
  const descendant=await s.migrate(plain.dna,{grid:50,seed:'Synthetic migration test'});assert.equal(descendant.genome.genome_version,'web-3.0.0');assert.equal(descendant.genome.provenance.migrated_from.fingerprint,plain.dna.fingerprint);assert.notEqual(descendant.id,plain.dna.fingerprint);assert.equal(canonical(plain.dna),before);assert.equal((await s.regenerate(plain.dna)).ascii,plain.ascii);
 }finally{globalThis.fetch=originalFetch;if(originalLocation===undefined)delete globalThis.location;else globalThis.location=originalLocation;}
});
test('Native transport keeps measured GPU timing after raster responses and stays on loopback',async()=>{
 const oldFetch=globalThis.fetch,oldLocation=globalThis.location;let calls=0;
 try{globalThis.location={hostname:'example.com'};globalThis.fetch=async()=>{calls++;return new Response(JSON.stringify({ms:2.5}))};assert.equal(await NativeBridge.connect(),null);assert.equal(calls,0);const bridge=new NativeBridge({backend:'CUDA'});bridge.lastGpuMs=31.25;await bridge.request('raster',{cells:[]});assert.equal(bridge.lastGpuMs,31.25);assert.equal(bridge.lastMs,2.5);}finally{globalThis.fetch=oldFetch;if(oldLocation===undefined)delete globalThis.location;else globalThis.location=oldLocation;}
});
