import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
import {buildRegistry,buildRecipes,compileV3,CATEGORY_NAMES,FUSION_OPERATORS} from '../dist/fusion-v3.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const original=JSON.parse(await readFile(path.join(root,'dist/data/registry.json'),'utf8'));
const registry=buildRegistry(original),recipes=buildRecipes(registry);
assert.equal(registry.traits.length,530);assert.deepEqual(registry.traits.slice(0,420),original.traits);assert.equal(recipes.count,1200);
const base={genome_version:'registry-validation-3.0.0',seed:'PROGRAM-VALIDATION',family:'SKULLS',rarity:'COMMON',scene:[[1,0,.32,0,.42,.48,.33,0,0,0,0,1,0,0,0,0],[7,0,-.4,0,.25,.35,.2,0,0,0,0,2,.025,0,0,0],[1,-.16,.36,.26,.105,.13,.13,0,0,0,1,3,0,0,0,0],[1,.16,.36,.26,.105,.13,.13,0,0,0,1,4,0,0,0,0]],config:[3.5,1,.8,.14,0,0,2,-.7,.85,.8,1,24,.15,.18,2,3,1.05,0,0,4,1,0,.04,1],parameters:{entropy:.035},animation:{profile:0,assembly_variant:0,destruction_variant:0}};
const programs=new Set(),operators=new Set();let max=0;
for(const recipe of recipes.recipes){
 const g=compileV3(base,registry,{recipe,seed:recipe.generation_rules.seed_salt,rarity:'RARE',grid:30});
 assert(g.scene.length<=160&&g.scene.length>0);assert(g.scene.every(r=>r.length===16&&r.every(Number.isFinite)));assert(g.config.every(Number.isFinite));
 assert(g.animation.enabled);assert(g.motion.amplitude>0);assert(!g.categories.some(a=>g.provenance.conflict_resolution.some(c=>c.suppressed===a.id)));
 const signature=JSON.stringify([g.scene,g.config,g.grammar,g.motion]);assert(!programs.has(signature),'Duplicate recipe program '+recipe.id);programs.add(signature);operators.add(recipe.operator);max=Math.max(max,g.scene.length);
 recipe.validation={...recipe.validation,compiled_scene_count:g.scene.length,compiled_grid:30,conflicts_resolved:g.provenance.conflict_resolution.length,finite_parameters:true,distinct_program:true};
}
assert.equal(programs.size,1200);assert.equal(operators.size,FUSION_OPERATORS.length);assert(Object.values(recipes.source_reachability).every(a=>a.length>0));
await writeFile(path.join(root,'dist/data/traits-v3.json'),JSON.stringify(registry,null,2)+'\n');
await writeFile(path.join(root,'dist/data/recipes-v3.json'),JSON.stringify(recipes,null,2)+'\n');
console.log(JSON.stringify({version:'3.0.0',curated:registry.curated_count,new_values:registry.nft_values,categories:CATEGORY_NAMES,recipes:recipes.count,unique_compiled_programs:programs.size,reachable_sources:Object.keys(recipes.source_reachability).length,max_primitives:max}));
