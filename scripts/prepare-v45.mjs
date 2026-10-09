import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {webcrypto} from 'node:crypto';
import {Studio} from '../dist/store.js';
import {Repository,seal} from '../dist/engine.js';
import {buildRegistryV45,buildRecipesV45,upgradeV45,FRAMINGS} from '../dist/fusion-v45.js';
import {CATEGORY_NAMES} from '../dist/fusion-v3.js';
const root=fileURLToPath(new URL('../',import.meta.url)),dist=path.join(root,'dist');
globalThis.crypto??=webcrypto;globalThis.location={origin:'http://127.0.0.1:4178',hostname:'127.0.0.1'};
globalThis.fetch=async input=>{try{return new Response(await fs.readFile(path.join(dist,new URL(String(input),location.origin).pathname)))}catch{return new Response(null,{status:404})}};
const args=Object.fromEntries(process.argv.slice(2).map(v=>v.split('='))),read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const v3=await read('dist/data/traits-v3.json'),registry=buildRegistryV45(v3),recipes=buildRecipesV45(registry);
await fs.writeFile(path.join(dist,'data/traits-v45.json'),JSON.stringify(registry));await fs.writeFile(path.join(dist,'data/recipes-v45.json'),JSON.stringify(recipes));
const calibration=await read('native/work/calibration.json'),studio=new Studio();studio.repo=await new Repository().init();studio.v3Registry=v3;studio.engine={backend:'CUDA',fontName:calibration.font,coverage:calibration.coverage};
const experimental=args.mode!=='collection',count=experimental?200:3333,items=[];let legend=0;
const original=studio.repo.catalog;
for(let i=0;i<count;i++){
 const recipe=recipes.recipes[(i*17)%2400],rarity=experimental?(i<23?'LEGENDARY':['COMMON','UNCOMMON','RARE','EPIC'][i%4]):original[i].rarity;
 const cats=Object.fromEntries(recipe.trait_ids.map(id=>[registry.traits.find(t=>t.id===id).category,id]));
 // Each retained V3 value is executed by its original structural compiler.
 // New values add their own geometry/field programs after that compiler.
 const oldCats=Object.fromEntries(CATEGORY_NAMES.map((cat,c)=>[cat,cats[cat].startsWith('V3.')?cats[cat]:`V3.${cat.toUpperCase()}.${String(1+(i+c)%10).padStart(2,'0')}`]));
 const base=await studio.prepareV3({seed:`NULL-GENESIS-V45/${experimental?'experiment':'edition'}/${i+1}`,rarity,grid:50,profile:rarity==='LEGENDARY'?legend++%23:0,concepts:recipe.source_concept_ids,categories:oldCats,operator:recipe.operator,level:recipe.level,renderingProfile:'SCULPTURAL',overrides:{entropy:.035,fragmentation:.08,complexity:.55,contrast:1.08,camera:'T01.01',lighting:'T03.01',appearance:i%13===0?'ENCRYPTED':i%19===0?'DIMENSIONAL ANOMALY':'RECOGNIZABLE'}});
 for(const t of base.categories)if(cats[t.trait_type].startsWith('V3.'))cats[t.trait_type]=t.id;
 const g=await seal(upgradeV45(base,registry,{grid:Number(args.grid||80),recipe,categories:cats,framing:FRAMINGS[i%8]}));
 items.push({edition:i+1,id:experimental?'E'+String(i+1).padStart(3,'0'):String(i+1).padStart(4,'0'),genome:g,...(experimental?{baseline:base}:{}),protected:rarity==='RARE'||rarity==='LEGENDARY'||g.appearance==='ENCRYPTED',legacy_edition:i+1});
 if((i+1)%100===0)console.log('Prepared '+(i+1)+' / '+count);
}
const programs=recipes.recipes.map(r=>JSON.stringify([r.source_concept_ids,r.operator,r.generation_rules,r.trait_ids]));if(new Set(programs).size!==2400)throw Error('Duplicate recipe programs');
const filename=args.manifest||(experimental?'experiments-v45.json':'collection-v45.json');if(path.basename(filename)!==filename||!filename.endsWith('.json'))throw Error('Manifest must be a JSON filename inside native/work.');
const file=path.join(root,'native/work',filename);await fs.writeFile(file,JSON.stringify({version:'4.5.0',count,items}));console.log(JSON.stringify({curated:registry.curated_count,operative_additions:registry.v45_values,recipes:recipes.count,count,file}));
