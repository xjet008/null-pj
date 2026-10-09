import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {webcrypto} from 'node:crypto';
import {buildRegistryV45,buildRecipesV45,upgradeV45,GRIDS,FRAMINGS} from '../dist/fusion-v45.js';
import {seal,checkGenome} from '../dist/engine.js';
import {decodeAnimation} from '../dist/store.js';
globalThis.crypto??=webcrypto;
const v3=JSON.parse(fs.readFileSync(new URL('../dist/data/traits-v3.json',import.meta.url))),r=buildRegistryV45(v3),recipes=buildRecipesV45(r);
function baseline(){return JSON.parse(gunzipSync(fs.readFileSync(new URL('../dist/v3/experiments/E001.json.gz',import.meta.url)))).genome;}
test('V4.5 retains 530 complete definitions and adds 212 operative curated values',()=>{assert.equal(r.curated_count,742);assert.deepEqual(r.traits.slice(0,530),v3.traits);assert.equal(new Set(r.traits.map(t=>t.id)).size,742);assert.equal(recipes.count,2400);assert.equal(new Set(recipes.recipes.map(x=>JSON.stringify(x.generation_rules))).size,2400);assert.equal(new Set(recipes.recipes.flatMap(x=>x.source_concept_ids)).size,300);});
test('every native resolution has separate authenticated identity and V3 grids remain frozen',async()=>{const base=baseline();let identities=[];for(const grid of GRIDS){const g=await seal(upgradeV45(base,r,{grid}));await checkGenome(g);identities.push(g.fingerprint);const bad=structuredClone(g);bad.encoder.edge_weight=2;await seal(bad);await assert.rejects(checkGenome(bad));}assert.equal(new Set(identities).size,6);const old=structuredClone(base);old.grid=[80,80];await seal(old);await assert.rejects(checkGenome(old));assert.equal(FRAMINGS.length,8);});
test('XOR frame codec exactly recovers animated glyphs and gray values',()=>{const n=30*30,total=24,stride=n*2,raw=new Uint8Array(total*stride);for(let f=0;f<total;f++)for(let i=0;i<n;i++){raw[f*stride+i*2]=i%3?65+f%6:32;raw[f*stride+i*2+1]=(f*7+i)%256;}const delta=raw.slice();for(let f=total-1;f>0;f--)for(let i=0;i<stride;i++)delta[f*stride+i]^=raw[(f-1)*stride+i];const a=decodeAnimation({encoding:'interleaved-xor-u8',grid:[30,30],fps:12,seconds:2,frame_count:total,cells:Buffer.from(delta).toString('base64')});for(let f=0;f<total;f++){assert.deepEqual(a.luminance[f],Array.from({length:n},(_,i)=>raw[f*stride+i*2+1]));assert.equal(a.frames[f].replaceAll('\n',''),Array.from({length:n},(_,i)=>String.fromCharCode(raw[f*stride+i*2])).join(''));}});
test('all 212 new values compile different operative parameters, not only names',()=>{const base=baseline(),common=Object.fromEntries(base.categories.map(t=>[t.trait_type,t.id]));for(const category of r.categories){const values=r.traits.filter(t=>t.category===category.name&&t.id.startsWith('V45.')),programs=new Set();for(const trait of values){const g=upgradeV45(base,r,{categories:{...common,[category.name]:trait.id},framing:'Full-Body'}),{name,...motion}=g.motion;programs.add(JSON.stringify({scene:g.scene,config:g.config,rendering:g.rendering,encoder:g.encoder,motion}));}assert.equal(programs.size,values.length,'Repeated operative '+category.name+' programs');}});
test('all six density budgets control geometry, noise or motion and invalid budgets fail validation',async()=>{
 const base=baseline(),categories=Object.fromEntries(r.categories.map(x=>[x.name,x.traits.find(id=>id.startsWith('V45.'))]));
 const program=g=>JSON.stringify({scene:g.scene,config:g.config,encoder:g.encoder,motion:g.motion});
 for(const [key,value] of Object.entries({primary:.06,secondary:.001,tertiary:.001,stage:.001,ambient_code:.0001,motion:.035})){
  const shared=key==='secondary'?{primary:.2}:{},options={categories,framing:'Full-Body'};
  const normal=upgradeV45(base,r,{...options,densityBudget:shared});
  const changed=await seal(upgradeV45(base,r,{...options,densityBudget:{...shared,[key]:value}}));
  await checkGenome(changed);assert.notEqual(program(changed),program(normal),'Inoperative density budget '+key);
 }
 for(const value of [0,-.1,2,NaN])assert.throws(()=>upgradeV45(base,r,{densityBudget:{primary:value}}),/density/);
 assert.throws(()=>upgradeV45(base,r,{densityBudget:{unexpected:.1}}),/density/);
 const bad=upgradeV45(base,r);bad.density_budget.motion=2;await seal(bad);await assert.rejects(checkGenome(bad));
 const invalidFraming=upgradeV45(base,r);invalidFraming.composition.mode='unsupported';await seal(invalidFraming);await assert.rejects(checkGenome(invalidFraming));
});
