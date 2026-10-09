import {readdirSync,readFileSync,statSync,existsSync,writeFileSync} from 'node:fs';
import {resolve,join,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {validateV3} from './validate-v3.mjs';
import {validateV45} from './validate-v45.mjs';
const root=resolve('dist'),json=p=>JSON.parse(readFileSync(join(root,p),'utf8')),packed=p=>JSON.parse(gunzipSync(readFileSync(join(root,p))).toString('utf8')),sha=s=>createHash('sha256').update(s).digest('hex');
const grid=text=>{const rows=text.split('\n');assert.equal(rows.pop(),'');assert.equal(rows.length,30);assert(rows.every(r=>r.length===30&&/^[\x20-\x7e]*$/.test(r)));};
const catalog=json('data/catalog.json'),config=json('data/config.json');assert.equal(catalog.length,3333);
const counts={},rarities={},hashes=new Set();let records=0,protectedDNA=0,totalFrames=0;const profiles=new Set();
for(let block=0;block<34;block++){
 const rows=packed('data/block-'+String(block).padStart(2,'0')+'.json.gz');assert.equal(rows.length,Math.min(100,3333-block*100));
 for(const a of rows){records++;assert.equal(a.edition,records);assert.equal(catalog[records-1].edition,records);grid(a.ascii);assert.equal(sha(a.ascii),a.metadata.canonical_hash);hashes.add(a.metadata.canonical_hash);assert.equal(a.luminance.length,900);assert(a.luminance.every(x=>Number.isFinite(x)&&x>=0&&x<=255));assert(a.scene.length>0&&a.scene.length<=160);assert(a.scene.every(row=>row.length===16&&row.every(Number.isFinite)));assert.equal(a.cfg.length,24);assert(existsSync(join(root,'collection/previews',String(records).padStart(4,'0')+'.png')));counts[a.metadata.family]=(counts[a.metadata.family]||0)+1;rarities[a.metadata.rarity]=(rarities[a.metadata.rarity]||0)+1;if(a.dna.algorithm){protectedDNA++;assert.equal(a.dna.algorithm,'AES-256-GCM');assert.equal(Buffer.from(a.dna.nonce,'base64').length,12);assert.equal(Buffer.from(a.dna.aad,'base64').toString(),'NULL-GENESIS/structural-envelope/v1/'+a.edition);}}
}
assert.equal(records,3333);assert.equal(hashes.size,3333);assert.deepEqual(counts,config.families);assert.deepEqual(rarities,config.rarities);
for(const m of catalog.filter(m=>m.rarity==='LEGENDARY')){
 const base='collection/animations/'+String(m.edition).padStart(4,'0'),a=packed(base+'.frames.json.gz');assert.equal(a.frames.length,96);assert.equal(a.luminance.length,96);assert.equal(a.fps,12);assert.equal(a.seconds,8);profiles.add(a.profile);
 for(let f=0;f<96;f++){grid(a.frames[f]);assert.equal(a.luminance[f].length,900);assert(a.luminance[f].every(x=>Number.isFinite(x)&&x>=0&&x<=255));totalFrames++;}
 for(const ext of ['html','webm','mp4'])assert(existsSync(join(root,base+'.'+ext)));
}
assert.equal(profiles.size,23);assert.equal(totalFrames,2208);
const archives=json('exports/index.json');assert.equal(archives.length,7);for(const a of archives)assert(existsSync(join(root,a.url.slice(1))));
const walk=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(f=>f.isDirectory()?walk(join(dir,f.name)):[join(dir,f.name)]);
const files=walk(root);let bytes=0,max=0;for(const file of files){const path=relative(root,file).replaceAll('\\','/');assert(!path.endsWith('.key')&&!path.split('/').includes('private')&&!path.startsWith('.env')&&!path.startsWith('.openai/'));const size=statSync(file).size;bytes+=size;max=Math.max(max,size);}
assert(max<25*1024*1024);assert(files.length<40000);
for(const script of files.filter(f=>f.endsWith('.js'))){const result=spawnSync(process.execPath,['--check',script],{encoding:'utf8'});assert.equal(result.status,0,result.stderr);}
const report={passed:true,editions:records,native_grid:[30,30],canonical_hashes_verified:records,unique_art:hashes.size,encrypted_envelopes_preserved:protectedDNA,animation_profiles:profiles.size,animation_frames:totalFrames,zip_parts:archives.length,asset_files:files.length,expanded_assets_bytes:bytes,largest_asset_bytes:max,gzip_records:57,family_counts:counts,rarity_counts:rarities};
report.v3=validateV3(root);
report.v45=await validateV45(root);
if(process.argv.includes('--report'))writeFileSync(join(root,'reports/web-data-checks.json'),JSON.stringify(report,null,2)+'\n');
console.log('Validated original '+records+' editions, V3 '+report.v3.editions+' editions and V4.5 '+report.v45.editions+' editions / '+report.v45.frames+' new frames; '+files.length+' assets ('+(bytes/1e6).toFixed(1)+' MB).');
