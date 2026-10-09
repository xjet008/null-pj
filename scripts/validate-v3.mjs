import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {gunzipSync,inflateRawSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const CATEGORIES=['Back','Body','Eyewear','Features','Form','Headwear','Mask','Method','Motion','Palette','Stage'];
const QUOTAS={COMMON:1900,UNCOMMON:900,RARE:400,EPIC:110,LEGENDARY:23};
const TIER_FRAMES={COMMON:36,UNCOMMON:48,RARE:72,EPIC:96,LEGENDARY:144};
const REQUIRED_EXPORTS=['ascii.txt','preview.png','metadata.json','genome.dna.json','animation.frames.json.gz','animation.html'];
const OPTIONAL_EXPORTS=['animation.mp4','animation.webm'];
const hash=b=>createHash('sha256').update(b).digest('hex');
const crcTable=Uint32Array.from({length:256},(_,i)=>{for(let j=0;j<8;j++)i=i&1?0xedb88320^(i>>>1):i>>>1;return i>>>0;});
const crc32=b=>{let c=0xffffffff;for(const n of b)c=crcTable[(c^n)&255]^(c>>>8);return (c^0xffffffff)>>>0;};
export function checkZip(bytes,inventory,required=REQUIRED_EXPORTS,onEntry=null){
 let end=bytes.length-22;while(end>=Math.max(0,bytes.length-65557)&&bytes.readUInt32LE(end)!==0x06054b50)end--;
 assert(end>=Math.max(0,bytes.length-65557),'ZIP end record missing');let offset=bytes.readUInt32LE(end+16),count=bytes.readUInt16LE(end+10);const names=new Set();
 for(let i=0;i<count;i++){
  assert.equal(bytes.readUInt32LE(offset),0x02014b50);const method=bytes.readUInt16LE(offset+10),crc=bytes.readUInt32LE(offset+16),packed=bytes.readUInt32LE(offset+20),size=bytes.readUInt32LE(offset+24),nameLength=bytes.readUInt16LE(offset+28),extraLength=bytes.readUInt16LE(offset+30),commentLength=bytes.readUInt16LE(offset+32),local=bytes.readUInt32LE(offset+42),name=bytes.subarray(offset+46,offset+46+nameLength).toString('utf8');
  assert(!name.endsWith('.key')&&!name.split('/').includes('private')&&!name.includes('..')&&!name.includes('\\')&&!name.startsWith('/'),'Private or unsafe ZIP entry');assert(!names.has(name),'Duplicate ZIP entry: '+name);names.add(name);assert.equal(bytes.readUInt32LE(local),0x04034b50);
  const localNameLength=bytes.readUInt16LE(local+26),localName=bytes.subarray(local+30,local+30+localNameLength).toString('utf8');assert.equal(localName,name,'ZIP local/central filename mismatch');assert.equal(bytes.readUInt16LE(local+8),method,'ZIP local/central compression mismatch');
  const begin=local+30+localNameLength+bytes.readUInt16LE(local+28),data=bytes.subarray(begin,begin+packed),plain=method===0?data:method===8?inflateRawSync(data):null;assert(plain,'Unsupported ZIP compression');assert.equal(plain.length,size);assert.equal(crc32(plain),crc,'ZIP CRC mismatch: '+name);
  if(name!=='README.txt'){
   const match=/^(\d{4})\/([^/]+)$/.exec(name);assert(match,'Unexpected ZIP path: '+name);const edition=Number(match[1]),file=match[2];assert(edition>=1&&edition<=3333,'ZIP edition outside collection');assert([...required,...OPTIONAL_EXPORTS].includes(file),'Unexpected ZIP edition file: '+name);
   onEntry?.(edition,file,plain);
   if(inventory){if(!inventory.has(edition))inventory.set(edition,new Set());const files=inventory.get(edition);assert(!files.has(file),'Duplicate edition export across ZIP parts: '+name);files.add(file);}
  }
  offset+=46+nameLength+extraLength+commentLength;
 }assert(names.has('README.txt'),'ZIP public README missing');return count;
}
function validateArchiveInventory(inventory,catalog){
 assert.equal(inventory.size,catalog.length,'ZIP inventory does not cover every edition');
 for(const m of catalog){
  const files=inventory.get(m.edition);assert(files,'ZIP edition missing: '+m.edition);
  for(const file of REQUIRED_EXPORTS)assert(files.has(file),'ZIP required export missing: '+m.edition+'/'+file);
  if(m.rarity==='LEGENDARY')for(const file of OPTIONAL_EXPORTS)assert(files.has(file),'ZIP Legendary video missing: '+m.edition+'/'+file);
 }
}
export function validateV3(root){
 const json=p=>JSON.parse(readFileSync(join(root,p),'utf8')),packed=p=>JSON.parse(gunzipSync(readFileSync(join(root,p))).toString('utf8'));
 const release=json('v3/collection/release.json'),audit=json('v3/reports/collection-audit.json'),experiment=json('v3/reports/experiments.json'),registry=json('data/traits-v3.json'),recipes=json('data/recipes-v3.json'),catalog=json('v3/collection/catalog.json');
 assert.equal(release.complete,true);assert.equal(audit.passed,true);assert.equal(audit.native_backend,'CUDA');assert.equal(audit.animated,3333);assert.equal(audit.owner_keys_public,false);assert.equal(experiment.visual_review_approved,true);assert.equal(experiment.full_animation_timelines,true);assert.equal(experiment.experiment_count,120);assert.deepEqual(release.canonical_grid,[50,50]);
 assert.equal(registry.traits.length,530);assert.equal(new Set(registry.traits.map(t=>t.id)).size,530);assert.equal(recipes.recipes.length,1200);assert.equal(catalog.length,3333);
 const ids=new Set(registry.traits.map(t=>t.id)),registered=new Map(registry.traits.map(t=>[t.id,t])),rarities={},hashes=new Set(),fingerprints=new Set(),profiles=new Set(),sourceIDs=new Set(),ranks=new Set();let editions=0,frames=0,protectedDNA=0;
 for(let block=0;block<34;block++)for(const row of packed('v3/collection/block-'+String(block).padStart(2,'0')+'.json.gz')){
  editions++;const m=row.metadata,n=m.grid[0]*m.grid[1],expected=catalog[editions-1],rows=row.ascii.split('\n');assert.equal(row.edition,editions);assert.equal(expected.edition,editions);assert.equal(expected.canonical_hash,m.canonical_hash);assert.deepEqual(m.grid,release.canonical_grid);assert.equal(rows.pop(),'');assert.equal(rows.length,m.grid[1]);assert(rows.every(r=>r.length===m.grid[0]&&/^[\x20-\x7e]*$/.test(r)));assert.equal(hash(row.ascii),m.canonical_hash);assert(!hashes.has(m.canonical_hash));assert(!fingerprints.has(m.genome_fingerprint));hashes.add(m.canonical_hash);fingerprints.add(m.genome_fingerprint);
  assert.equal(row.luminance.length,n);assert(row.luminance.every(x=>Number.isFinite(x)&&x>=0&&x<=255));assert.deepEqual(m.attributes.map(t=>t.trait_type),CATEGORIES);for(const t of m.attributes){const definition=registered.get(t.id);assert(definition,'Unknown attribute: '+t.id);assert.equal(definition.category,t.trait_type,'Attribute category mismatch');assert.equal(definition.label,t.value,'Attribute label mismatch');}assert(m.quality.accepted);assert(m.loop_validation.periodic&&m.loop_validation.animated);assert(m.loop_validation.full_timeline_validated!==false);for(const id of m.base_concepts){assert(ids.has(id));sourceIDs.add(id);}rarities[m.rarity]=(rarities[m.rarity]||0)+1;
  assert(Number.isInteger(m.rank)&&m.rank>=1&&m.rank<=3333,'Invalid edition rarity rank');assert(!ranks.has(m.rank),'Duplicate rarity rank');ranks.add(m.rank);assert(Number.isFinite(m.rarity_score),'Invalid edition rarity score');assert.equal(expected.rank,m.rank,'Catalog/block rank mismatch');assert.equal(expected.rarity_score,m.rarity_score,'Catalog/block rarity score mismatch');
  const name=String(editions).padStart(4,'0'),a=packed('v3/collection/animations/'+name+'.frames.json.gz'),bytes=Buffer.from(a.cells,'base64');assert.equal(a.encoding,'interleaved-u8');assert.deepEqual(a.grid,m.grid);assert.equal(a.genome_fingerprint,m.genome_fingerprint);assert.equal(a.fps,m.animation.fps,'Timeline/metadata FPS mismatch');assert.equal(a.seconds,m.animation.seconds,'Timeline/metadata duration mismatch');assert.equal(a.profile,m.animation.name,'Timeline/metadata profile mismatch');assert.equal(a.frame_count,m.loop_validation.frame_count,'Timeline/metadata frame count mismatch');assert.equal(a.frame_count,TIER_FRAMES[m.rarity],'Timeline rarity duration mismatch');assert.equal(a.frame_count,a.fps*a.seconds);assert.equal(bytes.length,a.frame_count*n*2);let first='',moving=false;for(let i=0;i<n;i++){first+=String.fromCharCode(bytes[i*2]);if((i+1)%m.grid[0]===0)first+='\n';}assert.equal(first,row.ascii);for(let i=0;i<bytes.length;i+=2){assert(bytes[i]>=32&&bytes[i]<=126);if(i>=n*2&&(bytes[i]!==bytes[i%(n*2)]||bytes[i+1]!==bytes[(i+1)%(n*2)]))moving=true;}assert(moving,'Static release animation');frames+=a.frame_count;
  if(row.dna.algorithm){protectedDNA++;assert.equal(row.dna.version,3);assert.equal(row.dna.algorithm,'AES-256-GCM');assert.equal(row.dna.fingerprint,m.genome_fingerprint);assert.equal(Buffer.from(row.dna.nonce,'base64').length,12);assert.equal(Buffer.from(row.dna.aad,'base64').toString(),'NULL-GENESIS/web-genome/v3/'+m.genome_fingerprint);assert(!row.genome&&!row.scene&&!row.config&&!row.dna.key&&!row.dna.genome);}else{assert.equal(row.genome.fingerprint,m.genome_fingerprint);assert.equal(row.dna.fingerprint,m.genome_fingerprint);}
  assert(existsSync(join(root,'v3/collection/previews',name+'.png')));if(m.rarity==='LEGENDARY'){profiles.add(m.animation.profile);for(const ext of ['mp4','webm']){assert(existsSync(join(root,'v3/collection/animations',name+'.'+ext)));assert.equal(m.media[ext],'/v3/collection/animations/'+name+'.'+ext);}}
 }
 assert.equal(editions,3333);assert.deepEqual(rarities,QUOTAS);assert.deepEqual([...ranks].sort((a,b)=>a-b),Array.from({length:3333},(_,i)=>i+1),'Rarity ranks are not a complete permutation');assert.deepEqual([...profiles].sort((a,b)=>a-b),Array.from({length:23},(_,i)=>i),'Legendary profiles are incomplete');assert.equal(sourceIDs.size,300);assert.equal(frames,audit.frames);
 const manifest=json('v3/collection/exports/index.json'),archives=Array.isArray(manifest)?manifest:manifest.parts||manifest.archives,inventory=new Map();let entries=0;assert(archives.length);for(const part of archives){const bytes=readFileSync(join(root,part.url.slice(1)));assert.equal(bytes.length,part.bytes);assert(bytes.length<=24*1024*1024);assert.equal(hash(bytes),part.sha256);entries+=checkZip(bytes,inventory);}
 validateArchiveInventory(inventory,catalog);assert(existsSync(join(root,'v3/viewer.html')));
 return {passed:true,version:'3.0.0',editions,frames,protectedDNA,source_concepts:sourceIDs.size,curated_values:530,recipes:1200,legendary_profiles:profiles.size,archive_parts:archives.length,zip_entries_crc_verified:entries};
}
