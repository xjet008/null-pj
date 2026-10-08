import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {webcrypto} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {Studio} from '../dist/store.js';
import {Repository,checkGenome} from '../dist/engine.js';
const root=fileURLToPath(new URL('../',import.meta.url)),dist=path.join(root,'dist');
globalThis.crypto??=webcrypto;
globalThis.location={origin:'http://127.0.0.1:4177',hostname:'127.0.0.1'};
globalThis.fetch=async input=>{const url=new URL(String(input),location.origin);try{const bytes=await fs.readFile(path.join(dist,url.pathname));return new Response(bytes,{status:200})}catch{return new Response(null,{status:404})}};
const args=Object.fromEntries(process.argv.slice(2).map(v=>v.split('=')));
const json=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const s=new Studio();s.repo=await new Repository().init();s.v3Registry=await json('dist/data/traits-v3.json');s.v3Recipes=await json('dist/data/recipes-v3.json');
const calibration=args.calibration?JSON.parse(await fs.readFile(args.calibration,'utf8')):null;
s.engine={backend:'CUDA',fontName:calibration?.font||'Consolas',coverage:calibration?.coverage||Array.from({length:95},(_,i)=>i===0?0:i/280)};
const experimental=args.mode!=='collection',count=experimental?120:3333,output=args.output||path.join(root,'native','work',experimental?'experimental-genomes.json':'collection-genomes.json');
const concepts=s.repo.registry.traits.filter(t=>t.families.length===1).map(t=>t.id),operators=['GEOMETRIC_FUSION','MATERIAL_TRANSPLANT','ANATOMICAL_MUTATION','TOPOLOGY_REWRITE','SYMBOLIC_OVERLAY','STRUCTURAL_CORRUPTION','DIMENSIONAL_PROJECTION','CIPHER_FUSION','ORGANIC_SYNTHESIS','METAMORPHIC_FUSION'];
const profiles=['SCULPTURAL','MINIMAL','ORGANIC','FRACTURED','CRYPTIC','VOID','ANATOMICAL','GEOMETRIC','CHAOTIC'],modes=['RECOGNIZABLE','FRAGMENTED','APPARENT CHAOS','ENCRYPTED','ANATOMICAL RECONSTRUCTION','WIRESPACE','DUALITY','DATA FOSSIL','VOID ENTITY','DIMENSIONAL ANOMALY'];
const categories=['Back','Body','Eyewear','Features','Form','Headwear','Mask','Method','Motion','Palette','Stage'];
const out=[];let legend=0;
for(let i=0;i<count;i++){
 const edition=i+1,legacy=s.repo.catalog[i],rarity=experimental?(i<23?'LEGENDARY':['COMMON','UNCOMMON','RARE','EPIC'][i%4]):legacy.rarity;
 const selected=experimental?[concepts[(i*17)%300],concepts[(i*47+139)%300],concepts[(i*79+227)%300]].filter((v,j,a)=>a.indexOf(v)===j):i<300?[concepts[(i*137)%300]]:[];
 const cat={};if(experimental)for(let c=0;c<11;c++){const prefix='V3.'+categories[c].toUpperCase()+'.';cat[categories[c]]=prefix+String(1+(i+c*3)%10).padStart(2,'0');}
 const appearance=i%9===0?modes[(Math.floor(i/9))%modes.length]:'RECOGNIZABLE';
 const opts={version:'3.0.0',grid:50,seed:'NULL-GENESIS-V3/'+(experimental?'experiment':'edition')+'/'+edition,rarity,profile:rarity==='LEGENDARY'?legend++%23:0,concepts:selected,categories:cat,operator:experimental?operators[i%10]:undefined,renderingProfile:profiles[experimental?i%9:Math.floor(i/15)%9],encryption:'NONE',overrides:{appearance,entropy:.045+(i%7)*.01,fragmentation:.12+(i%9)*.032,complexity:.4+(i%11)*.055,contrast:1.08,camera:experimental?'T01.02':['T01.01','T01.02','T01.03'][i%3],lighting:'T03.01'}};
 const g=await s.prepareV3(opts);await checkGenome(g);out.push({edition,id:experimental?'E'+String(edition).padStart(3,'0'):String(edition).padStart(4,'0'),genome:g,protected:rarity==='RARE'||rarity==='LEGENDARY'||appearance==='ENCRYPTED',legacy_edition:legacy.edition});
 if(edition%100===0)process.stdout.write('Prepared '+edition+' deterministic V3 genomes\n');
}
await fs.mkdir(path.dirname(output),{recursive:true});await fs.writeFile(output,JSON.stringify({version:'3.0.0',experimental,count,items:out}));console.log('Saved '+out.length+' genomes to '+output);
