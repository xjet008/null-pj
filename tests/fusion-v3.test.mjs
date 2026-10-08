import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {buildRegistry,buildRecipes,compileV3,resolveTraits,CATEGORY_NAMES,FUSION_OPERATORS} from '../dist/fusion-v3.js';
import {renderCpu,animateScene,validateCells,toAscii,rotate} from '../dist/math.js';
const old=JSON.parse(await readFile(new URL('../dist/data/registry.json',import.meta.url),'utf8'));
const registry=buildRegistry(old),recipes=buildRecipes(registry),digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const base={genome_version:'web-1.0.0',seed:'FUSION-VISUAL-VALIDATION',family:'SKULLS',rarity:'COMMON',appearance:'RECOGNIZABLE',scene:[[1,0,.3,0,.44,.48,.34,0,0,0,0,1,0,1,0,0],[7,0,-.42,0,.26,.35,.2,0,0,0,0,2,.025,1,0,1],[1,-.16,.36,.26,.11,.14,.15,0,0,0,1,3,0,1,0,0],[1,.16,.36,.26,.11,.14,.15,0,0,0,1,4,0,1,0,0]],config:[3.5,1,.8,.12,0,0,0,-.7,.85,.8,1,24,.15,.18,2,3,1.05,0,0,4,1,0,.035,1],parameters:{entropy:.035},animation:{profile:3,assembly_variant:0,destruction_variant:0}};
const minimal={Back:null,Body:null,Eyewear:null,Features:null,Form:'V3.FORM.01',Headwear:null,Mask:null,Method:'V3.METHOD.01',Motion:'V3.MOTION.07',Palette:'V3.PALETTE.03',Stage:null};
const prepare=o=>({...base,...compileV3(base,registry,{concepts:['S001'],operator:'GEOMETRIC_FUSION',categories:minimal,grid:30,...o}),genome_version:'web-3.0.0',samples:1,coverage:Array.from({length:95},(_,i)=>i===0?0:i/280)});
const program=g=>({scene:g.scene,config:g.config,grammar:g.grammar,rendering:g.rendering,motion:g.motion,animation:g.animation});

test('V3 preserves all 420 exact legacy definitions and adds exact ordered 110 values',()=>{
 assert.deepEqual(registry.traits.slice(0,420),old.traits);assert.equal(registry.traits.length,530);assert.equal(new Set(registry.traits.map(t=>t.id)).size,530);assert.equal(registry.nft_values,110);
 assert.deepEqual(registry.categories.map(c=>c.name),CATEGORY_NAMES);for(const c of registry.categories){assert.equal(c.traits.length,10);for(const id of c.traits){const t=registry.traits.find(t=>t.id===id);assert.equal(t.category,c.name);assert(t.rules.implementation.startsWith('ptfe3/'));}}
 assert.deepEqual(buildRegistry(old),registry);assert.throws(()=>buildRegistry({traits:old.traits.slice(1)}),/420/);
});
test('1,200 distinct executable structural recipes reach every source without allocation quotas',()=>{
 assert.equal(recipes.count,1200);assert.deepEqual(new Set(recipes.recipes.map(r=>r.operator)),new Set(FUSION_OPERATORS));assert.equal(Object.keys(recipes.source_reachability).length,300);assert(Object.values(recipes.source_reachability).every(a=>a.length>0));
 const signatures=new Set();for(const recipe of recipes.recipes){const g=compileV3(base,registry,{recipe,seed:recipe.generation_rules.seed_salt,rarity:'RARE',grid:30});assert(g.scene.length<=160);assert(g.scene.every(r=>r.length===16&&r.every(Number.isFinite)));assert(g.animation.enabled);assert(g.motion.amplitude>0);assert.deepEqual(g.categories.map(t=>t.trait_type),CATEGORY_NAMES);const s=digest(program(g));assert(!signatures.has(s),recipe.id);signatures.add(s);assert(!g.categories.some(t=>g.provenance.conflict_resolution.some(c=>c.suppressed===t.id)));}assert.equal(signatures.size,1200);
 const sameLibrary=prepare({concepts:['S001','S017','S078']}),crossLibrary=prepare({concepts:['S001','C099','A069']});assert.deepEqual(sameLibrary.influences.map(t=>t.library),['SKULLS','SKULLS','SKULLS']);assert.equal(new Set(crossLibrary.influences.map(t=>t.library)).size,3);assert.notDeepEqual(sameLibrary.scene,crossLibrary.scene);
});
test('all 300 concepts control distinct structural programs and inputs remain immutable',()=>{
 const before=digest(base),original=digest(old),signatures=new Set();for(const t of registry.traits.slice(0,300)){const g=prepare({concepts:[t.id]});const sig=digest([g.scene,g.config]);assert(!signatures.has(sig),'Visually inert source '+t.id);signatures.add(sig);}assert.equal(signatures.size,300);assert.equal(digest(base),before);assert.equal(digest(old),original);
});
test('ten fusion operators change actual geometry and rendering deterministically',()=>{
 const programs=new Set();for(const operator of FUSION_OPERATORS){const a=prepare({operator,concepts:['S017','C099','A069']}),b=prepare({operator,concepts:['S017','C099','A069']});assert.deepEqual(program(a),program(b));programs.add(digest([a.scene,a.config,a.grammar,a.motion]));}assert.equal(programs.size,10);
 const second={concept_id:'A069',scene:[[4,.8,.4,0,.2,.5,.2,0,0,.6,0,1,0,2,0,0]],cfg:base.config};const fused=compileV3({...base,source_scenes:[second]},registry,{concepts:['S017','A069'],operator:'GEOMETRIC_FUSION',traits:minimal});const noSource=compileV3(base,registry,{concepts:['S017','A069'],operator:'GEOMETRIC_FUSION',traits:minimal});assert.notDeepEqual(fused.scene,noSource.scene);assert(fused.scene.some(r=>r[13]===2));
});
test('compatibility conflicts resolve by priority and invalid controls cannot become fake traits',()=>{
 const a=resolveTraits(registry,{...minimal,Form:'V3.FORM.01',Body:'V3.BODY.02',Mask:'V3.MASK.06',Eyewear:'V3.EYEWEAR.07'},'SAME','RARE');assert(a.conflicts.some(c=>c.suppressed==='V3.BODY.02'));assert(a.conflicts.some(c=>c.suppressed==='V3.EYEWEAR.07'));assert(!a.traits.some(t=>t.id==='V3.BODY.02'||t.id==='V3.EYEWEAR.07'));
 assert.deepEqual(a,resolveTraits(registry,{...minimal,Form:'V3.FORM.01',Body:'V3.BODY.02',Mask:'V3.MASK.06',Eyewear:'V3.EYEWEAR.07'},'SAME','RARE'));
 const defaults=resolveTraits(registry,{Body:'V3.BODY.02',Form:'V3.FORM.01',Eyewear:'V3.EYEWEAR.07',Mask:'V3.MASK.06'},'SAME','COMMON');assert.deepEqual(defaults.traits.map(t=>t.category),CATEGORY_NAMES);assert(defaults.conflicts.every(c=>defaults.traits.some(t=>t.id===c.replacement)));assert(defaults.traits.every(t=>!defaults.traits.some(a=>(t.compatibility.incompatible||[]).includes(a.id))));
 assert.throws(()=>prepare({concepts:['MISSING']}),/source/);assert.throws(()=>prepare({grid:40}),/30 or 50/);assert.throws(()=>prepare({categories:{...minimal,Body:'label-only fake'}}),/Invalid Body/);assert.throws(()=>prepare({categories:{...minimal,Motion:null}}),/mandatory/);assert.throws(()=>prepare({concepts:['S001','S001']}),/distinct/);
});
test('all 120 original modifiers retain operative geometry, rendering or choreography',()=>{
 for(let group=1;group<=12;group++){const id='T'+String(group).padStart(2,'0'),signatures=new Set();for(let v=1;v<=10;v++){const value=id+'.'+String(v).padStart(2,'0'),g=prepare({modifiers:{[id]:value},rarity:'LEGENDARY'});signatures.add(digest(program(g)));}assert.equal(signatures.size,10,'Inert or duplicate '+id+' modifier programs');}
});
test('all 110 new values make distinct rendered grayscale art or geometric poses',()=>{
 // Identical seed, source and all other choices isolate the selected trait's real effect.
 // Native CPU ray marching uses the same SDF semantics as the NVIDIA compute path.
 for(const category of CATEGORY_NAMES){const signatures=new Set();for(const id of registry.categories.find(c=>c.name===category).traits){const categories={...minimal,[category]:id};if(category==='Body'&&id==='V3.BODY.02')categories.Form='V3.FORM.03';const g=prepare({categories}),pose=category==='Motion'?animateScene(g,19):g,data=renderCpu(pose);validateCells(data,g.grid);assert(data.some((v,i)=>i%12===9&&v===1),'Empty '+id);const signature=digest(Array.from(data,(v,i)=>i%12===0||i%12===1||i%12===8||i%12===9?Math.round(v*1000)/1000:0));assert(!signatures.has(signature),'No rendered distinction for '+id);signatures.add(signature);assert.equal(toAscii(data).split('\n').length,31);}assert.equal(signatures.size,10,category);}
});
test('native 50 grid, every rarity motion, loops and bounded detail budgets remain reproducible',()=>{
 for(const rarity of ['COMMON','UNCOMMON','RARE','EPIC','LEGENDARY']){const g=prepare({rarity,grid:50}),zero=animateScene(g,0),end=animateScene(g,96),moving=animateScene(g,19);assert.deepEqual(zero.scene,end.scene);assert.notDeepEqual(zero.scene,moving.scene);assert(g.animation.enabled);assert.deepEqual(g.grid,[50,50]);assert.equal(g.animation.legendary,rarity==='LEGENDARY');}
 const g=prepare({grid:50}),data=renderCpu(g);validateCells(data,[50,50]);assert.equal(data.length,30000);assert.equal(toAscii(data).split('\n').length,51);
 const large={...base,scene:Array.from({length:120},(_,i)=>[1,Math.sin(i)*.5,Math.cos(i)*.6,Math.sin(i*.3)*.3,.1,.12,.1,0,0,0,0,i+1,0,1,0,i%24])};const capped=compileV3(large,registry,{concepts:['S001','C050','A070'],rarity:'LEGENDARY',detailBudget:96});assert(capped.scene.length<=96);assert(capped.scene.every(r=>r.every(Number.isFinite)));assert(capped.provenance.deterministic_repairs.length>0);
});
test('complexity and fragmentation controls change rendered geometry and the finite detail budget',()=>{
 const simple=prepare({parameters:{complexity:.05,fragmentation:0}}),detailed=prepare({parameters:{complexity:.95,fragmentation:0}}),fragmented=prepare({parameters:{complexity:.95,fragmentation:.9}});
 assert(detailed.parameters.detail_budget>simple.parameters.detail_budget);assert(detailed.scene.length>simple.scene.length);assert.notDeepEqual(simple.scene,detailed.scene);assert.notDeepEqual(detailed.scene,fragmented.scene);
 const a=renderCpu(simple),b=renderCpu(detailed),c=renderCpu(fragmented);assert.notDeepEqual(a,b);assert.notDeepEqual(b,c);assert.equal(fragmented.parameters.fragmentation,.9);assert(detailed.scene.length<=160);
});
test('articulated cables follow their actual 3D endpoints rather than skewing off joints',()=>{
 const g=prepare({categories:{...minimal,Body:'V3.BODY.02',Form:'V3.FORM.03'},parameters:{complexity:0,fragmentation:0}});
 const expected=[[-.18,-.15,0],[-.4,-.58,.15]],center=expected[0].map((a,i)=>(a+expected[1][i])/2),row=g.scene.find(r=>r[0]===2&&r.slice(1,4).every((x,i)=>Math.abs(x-center[i])<1e-9));assert(row);
 const actual=rotate([0,row[5],0],row[7],row[8],row[9]).map((x,i)=>x+center[i]);assert(actual.every((x,i)=>Math.abs(x-expected[1][i])<1e-9));
});
