/* Versioned structural extension. V1 and V3 DNA remain immutable. */
import {CATEGORY_NAMES,stableHash,FUSION_OPERATORS} from './fusion-v3.js';
export const GRIDS=[30,50,64,80,96,120];
export const FRAMINGS=['Tight Portrait','Head-and-Torso','Half-Body','Full-Body','Wide Creature','Vertical Relic','Mask/Icon','Distributed Abstract'];
const names={
 Back:['Arc Vertebrae','Braided Spines','Twin Reactor Fins','Terminal Wing','Vaulted Scapula','Interlaced Mantle','Socketed Dorsal Plates','Suspended Tail','Lateral Bone Fan','Split Orbit Harness','Rib Wing','Asymmetric Reliquary','Recessed Data Fins','Crescent Backbone','Nested Dorsal Arch'],
 Body:['Dense Sternum','Cavity Torso','Long Neck Chassis','Armored Shoulder','Rib Cage Vault','Split Pelvis','Articulated Abdomen','Hollow Chest Core','Woven Vertebrae','Wide Predator Torso','Segmented Waist','Suspended Heart','Bony Clavicle','Terminal Rib Array','Titan Breastplate','Recursive Collar','Compact Trunk','Offset Hip Frame','Deep Thoracic Socket','Layered Skeletal Armor'],
 Eyewear:['Deep Binary Sockets','Hex Retinal Cells','Slit Optics','Unilateral Lens','Cavity Goggles','Raised Diagnostic Rim','Notched Sight Plate','Suspended Iris','Nested Pupil Array','Crosshair Aperture','Triple Signal Lens','Offset Optical Shield'],
 Features:['Broken Skull Seam','Punk Jaw Crest','Ape Brow','Fang Arcade','Socket Bridge','Split Cheek','Sculpted Nose Void','Raised Canine','Temporal Horn','Cranial Scar','Double Mandible','Orbit Cheek Spurs','Occipital Shelf','Bifid Brow','Sunken Nasal Channel','Jaw Hinges','Dense Teeth','Cracked Forehead','Facial Plates','Asymmetric Brow','Bone Muzzle','Cavity Temple','Notched Chin','Crowned Jaw','Deep Zygomatic Arch'],
 Form:['Tall Relic','Wide Chimera','Compact Skull','Punk Bust','Ape Monument','Split Idol','Crescent Titan','Armored Icon','Spined Creature','Two Core Entity','Twisted Totem','Floating Mask','Recursive Vault','Bifurcated Specter','Heavy Torso','Nested Skull','Serpentine Construct','Folded Anatomy','Skeletal Sentinel','Distributed Cipher'],
 Headwear:['Binary Mohawk','Skull Crown','Broken Antler','Vaulted Helmet','Cavity Diadem','Punk Signal Crest','Spiral Horns','Terminal Headdress','Raised Oracle Plate','Three Prong Crown','Bone Tiara','Notched Halo','Offset Horn','Layered Circlet','Suspended Crest'],
 Mask:['Deep Deathplate','Socket Visage','Split Skull Mask','Punk Respirator','Ape Face Shell','Negative Nose Plate','Mandible Shield','Broken Oracle','Cipher Veil','Cavity Shroud','Double Cheek Guard','Terminal Visor','Perforated Face','Skeletal Muzzle','Bone Lattice Mask','Raised Face Rim','Notched Phantom','Cryptic Jaw Plate','Hollow Idol','Nested Identity Shell'],
 Method:['Dual-Depth SDF Sampling','Adaptive Normal Field Clustering','Anatomy-Aware Contrast Mapping','Silhouette-Preserved Glyph Quantization','Local Glyph Anisotropy Encoding','Multi-Scale Occupancy Resampling','Volumetric ASCII Error Diffusion','Edge-Preserved Density Quantization','Material-Specific Glyph Selection','Temporal Glyph Stabilization','Depth-Locked Glyph Projection','Topology-Aware Downmapping','Layered Tonal Ramp Reconstruction','Signed-Distance Contour Tracing','Thickness-Aware Skeleton Rendering','High-Frequency Detail Budgeting','Curvature-Weighted Highlight Encoding','Implicit-Field Noise Suppression','Subcell Coverage Supersampling','Perceptual ASCII Quality Scoring'],
 Motion:['Orbital Breath','Cranial Tilt','Jaw Pulse','Spinal Ripple','Retinal Scan','Mantle Drift','Thoracic Beat','Horn Sway','Pelvic Rock','Digital Unfold','Core Orbit','Cipher Flow','Signal Sweep','Shoulder Float','Vertebral Tide','Mask Phase','Tendril Roll','Bone Cascade','Relic Levitation','Terminal Blink','Socket Recovery','Facial Current','Structural Hum','Rib Oscillation','Lateral Morph','Slow Axis Turn','Quasi Static Drift','Contour Pulse','Layered Reassembly','Distributed Restoration'],
 Palette:['Cold Chalk','Silver Socket','Graphite Relief','Fog White','Deep Ink','Lunar Bone','Gray Steel','Pale Cavity','Carbon Rim','Ash Contrast','Pearl Armor','Dark Frost','Brushed White','Soft Charcoal','Terminal Gray'],
 Stage:['Quiet Archive','Low Horizon','Side Terminal','Broken Pedestal','Negative Chamber','Sparse Orbit','Code Plinth','Twin Relic Columns','Floor Grid','Deep Vault','Minimal Frame','Suspended Console','Lower Glyph Field','Split Foundation','Bone Base','Terminal Alcove','Silent Atrium','Fractured Floor','Floating Ground','Null Horizon']
};
const C=(n,a,b)=>Math.max(a,Math.min(b,n));
export function buildRegistryV45(v3){
 if(v3.curated_count!==530)throw Error('The complete frozen V3 registry is required.');
 const traits=structuredClone(v3.traits),categories=structuredClone(v3.categories);
 for(const category of CATEGORY_NAMES)names[category].forEach((label,i)=>{
  const id=`V45.${category.toUpperCase()}.${String(i+1).padStart(2,'0')}`;
  traits.push({id,label,category,families:['SKULLS','CHARACTERS','ANIMALS'],animation_eligible:true,rarity_weight:1/(1+i%5),compatibility:{grayscale_only:true,exclusive_category:true,minimum_grid:30,incompatible:[],maximum_primitives:160},rules:{implementation:`ptfe45/${category.toLowerCase()}/${i}`,variant:i,deterministic:true,priority:category==='Stage'?20:90,spatial_mask:['Features','Eyewear','Mask','Headwear'].includes(category)?'cranial':category==='Back'?'rear':category==='Stage'?'periphery':'whole',structural_effect:category==='Method'?'field / encoder configuration':category==='Motion'?'periodic geometry and shader phase':category==='Palette'?'gray lighting and roughness':'adaptive positive and negative SDF geometry',detail_cost:['Method','Motion','Palette'].includes(category)?0:4}});
  categories.find(c=>c.name===category).traits.push(id);
 });
 return {...v3,version:'4.5.0',curated_count:traits.length,v45_values:traits.length-530,categories,traits};
}
export function buildRecipesV45(registry){
 const sources=registry.traits.filter(t=>/^[SCA]\d{3}$/.test(t.id));
 return {version:'4.5.0',count:2400,operators:FUSION_OPERATORS,recipes:Array.from({length:2400},(_,i)=>({id:`PTFE45.${String(i+1).padStart(4,'0')}`,source_concept_ids:[sources[i%300].id,sources[(i*67+121)%300].id,sources[(i*137+209)%300].id].filter((x,k,a)=>a.indexOf(x)===k),operator:FUSION_OPERATORS[i%10],level:1+i%5,framing:FRAMINGS[i%8],trait_ids:CATEGORY_NAMES.map((cat,c)=>{const pool=registry.categories.find(x=>x.name===cat).traits;return pool[(i*7+c*13)%pool.length]}),generation_rules:{seed:`PTFE45/recipe/${i+1}`,geometry_strength:.16+(i%17)*.017,anatomy_band:i%19,topology:i%7,detail_budget:80+i%49}}))};
}
export function upgradeV45(base,registry,{grid=80,seed=base.seed,recipe=null,categories={},framing=null,motionIntensity=null,densityBudget={}}={}){
 if(!GRIDS.includes(grid))throw Error('Unsupported native grid.');
 const g=structuredClone(base),hash=stableHash(seed),map=new Map(registry.traits.map(t=>[t.id,t]));
 const budget={primary:.48,secondary:.16,tertiary:.045,stage:.035,ambient_code:.025,motion:.07,...densityBudget};
 if(Object.keys(budget).length!==6||Object.values(budget).some(v=>!Number.isFinite(v)||v<=0||v>1))throw Error('Invalid layer density budget.');
 g.density_budget=budget;
 const baseLimit=C(Math.round(116*(budget.primary/.48)),16,160),sceneLimit=C(baseLimit+Math.round(44*(budget.secondary/.16)),baseLimit,160);
 g.genome_version='web-4.5.0';g.render_version='cuda-sdf-4.5.0';g.seed=String(seed);g.grid=[grid,grid];g.samples=1;
 g.config[2]=1;g.config[19]=4;g.config[21]=0;g.config[22]=C(g.config[22],0,.06*(budget.ambient_code/.025));g.config[14]=2;g.config[15]=.65;g.config[3]*=.65;g.config[4]*=.6;
 g.rendering={...g.rendering,ambient:.14,fill:.22,ao:.68,rim:.19,contrast:1.13,contour:.7};g.grammar=base.modifiers?.T05!=='T05.10'?base.grammar:'.,:;-=+*/\\|()[]{}01ABCDEF#%@';
 // Silhouette-first simplification preserves subtraction fields, primary solids,
 // and large accessory structures. Tertiary geometry receives a bounded budget.
 g.scene=g.scene.filter(r=>r[14]!==4||r[4]*r[5]>.015).filter(r=>r[10]||r[14]===0||Math.max(r[4],r[5],r[6])>.045*(.045/budget.tertiary));
 g.scene=g.scene.slice(0,baseLimit);
 const stageLimit=Math.ceil((g.scene.filter(r=>r[14]===4).length+2)*(budget.stage/.035));let stages=0;
 g.scene=g.scene.filter(r=>r[14]!==4||stages++<stageLimit);
 g.encoder={version:'4.5.0',revision:'coverage-3',method_variant:0,noise_budget:C(base.parameters?.entropy??.035,0,Math.min(.12,.12*(budget.ambient_code/.025))),temporal_lock:.82,depth_weight:.32,edge_weight:.7};
 const selected=CATEGORY_NAMES.map((cat,c)=>{
  const supplied=categories[cat]||recipe?.trait_ids?.find(id=>map.get(id)?.category===cat);
  const pool=registry.categories.find(x=>x.name===cat).traits;
  const current=base.categories?.find(t=>t.trait_type===cat)?.id;
  const newPool=pool.filter(id=>id.startsWith('V45.'));
  const exponent={COMMON:1.25,UNCOMMON:1,RARE:.8,EPIC:.65,LEGENDARY:.5}[g.rarity]||1,weights=newPool.map(id=>Math.pow(map.get(id).rarity_weight,exponent));let cursor=stableHash(seed+'/'+cat)/4294967296*weights.reduce((a,b)=>a+b,0),weighted=newPool.at(-1);for(let i=0;i<newPool.length;i++){cursor-=weights[i];if(cursor<=0){weighted=newPool[i];break;}}
  const id=supplied||(hash%3===0&&current?current:weighted),t=map.get(id);if(!t||t.category!==cat)throw Error('Invalid '+cat+' trait.');
  return {trait_type:cat,value:t.label,id:t.id,implementation:t.rules.implementation};
 });
 const solid=g.scene.filter(r=>!r[10]&&r[14]!==4),top=solid.sort((a,b)=>b[2]-a[2])[0]||g.scene[0];
 const cx=0,hy=C(top[2],.3,1.1),hz=.35;
 const add=(kind,x,y,z,sx,sy,sz,subtract=0,layer=1,angle=0)=>{if(g.scene.length>=sceneLimit||layer===4&&stages>=stageLimit)return;if(layer===4)stages++;const id=g.scene.length+1;g.scene.push([kind,x,y,z,sx,sy,sz,0,0,angle,subtract,id,kind===10?5:.015,1,layer,id]);};
 for(const t of selected){
  if(!t.id.startsWith('V45.'))continue;
  const cat=t.trait_type,k=Number(t.id.split('.').at(-1))-1,u=(k%5)/4,side=k%2?1:-1;
  if(cat==='Body'){add(7,side*.045,-.15,hz,.28+u*.12,.34+(k%4)*.055,.16,0,0);if(k%3!==0)add(1,0,-.1,hz+.16,.12+u*.05,.18,.15,1,0);}
  if(cat==='Form'){const sx=.88+(k%5)*.075,sy=.9+(k%4)*.09;g.scene.forEach(r=>{if(r[14]!==4){r[1]*=sx;r[4]*=sx;r[2]*=sy;r[5]*=sy;r[9]+=(k%3-1)*.04;}});if(k%4===0)add(0,side*.32,.16,.06,.21,.31,.18,0,0);}
  if(cat==='Back')for(let j=0;j<3+k%3;j++){const a=j*.58;add(k%3===0?4:7,Math.sin(a)*(.48+u*.2),.3+Math.cos(a)*.55,-.38,.07,.18+u*.13,.055,0,2,side*a);}
  if(cat==='Features'){add(7,side*(.21+u*.04),hy-.17+(k%7)*.016,hz+.2,.12,.12+u*.075,.1+(k%3)*.015,0,1,side*.16);add(1,side*.14,hy-.08,hz+.22,.075+u*.025,.07+(k%7)*.006,.18,1,0);}
  if(cat==='Eyewear')for(const s of [-1,1]){const space=.145+k*.006;add(k%2?7:0,s*space,hy+.05,hz+.22,.12,.085+(k%3)*.009,.075,0,1);add(1,s*space,hy+.05,hz+.28,.072,.045+u*.025,.12,1,1);}
  if(cat==='Headwear')for(let j=0;j<2+k%4;j++)add(k%2?4:7,(j-(1+k%4)/2)*.115,hy+.25+(j%2)*.05,hz-.03,.045,.12+u*.16,.05,0,1,side*.12);
  if(cat==='Mask'){const space=.105+k*.0035;add(7,0,hy-.06,hz+.19,.26+u*.04,.23+(k%7)*.011,.06,0,1);for(const s of [-1,1])add(1,s*space,hy+.03,hz+.23,.077,.05+u*.02,.12,1,1);add(1,0,hy-.1,hz+.22,.043+(k%3)*.008,.09,.12,1,1);}
  if(cat==='Palette'){g.config[7]=-.6+u*.6;g.config[8]=.5+(k%3)*.18;g.config[9]=.75;g.config[11]=12+(k%5)*13;g.config[12]=.08+u*.22;g.rendering.ambient=.08+(k%4)*.035;g.rendering.contrast=.95+u*.35;}
  if(cat==='Motion'){g.motion.kind=k%10;g.motion.type=k%10;g.motion.speed=1+(k%3);g.motion.phase=(k*1.137)%6.2831853;g.motion.frequency=1+k%7;}
  if(cat==='Method'){g.encoder.method_variant=k;g.config[14]=k%3;g.config[15]=.35+u*.8;g.rendering.contour=.5+u*.45;g.rendering.ao=.45+(k%4)*.12;if(k===18)g.samples=2;}
  if(cat==='Stage')for(let j=0;j<2;j++)add(7,(j-.5)*(.9+u*.2),-1.05,-.35,.15+.02*(k%3),.035,.16,0,4,side*.05);
 }
 const chosenFraming=framing||recipe?.framing||FRAMINGS[hash%8];
 if(chosenFraming==='Distributed Abstract')g.scene.forEach(row=>{if(row[14]!==4){const group=(row[13]||1)%3;row[1]+=(group-1)*.22;row[2]*=.87;row[5]*=.87;row[9]+=(group-1)*.085;}});
 g.scene.forEach((r,i)=>{r[11]=i+1;r[15]=i+1;});
 const tierIntensity=C({COMMON:.045,UNCOMMON:.065,RARE:.095,EPIC:.13,LEGENDARY:.17}[g.rarity]*(budget.motion/.07),.015,.4),intensity=motionIntensity==null?tierIntensity:C(tierIntensity*(.4+Number(motionIntensity)/.18),.015,.4);g.motion.amplitude=intensity;g.motion.intensity=intensity;g.motion.name=selected.find(t=>t.trait_type==='Motion').value;
 g.categories=selected;g.animation={...g.animation,enabled:true,name:g.rarity==='LEGENDARY'?g.animation.name:g.motion.name,motion:g.motion,canonical_frame:0,temporal_identity:'world-anchored contour and occupancy',timing:'periodic 12 fps'};
 g.recipe=recipe?{...recipe,program:[...(g.recipe?.program||[]),...selected.map(t=>t.implementation)]}:{...g.recipe,program:[...(g.recipe?.program||[]),...selected.map(t=>t.implementation)]};
 g.composition={mode:chosenFraming,target_dimension:.8,safe_margin:.08,fit_subject_only:true,deliberate_micro_scale:false};
 g.encoder={version:'4.5.0',method_variant:0,noise_budget:.035,temporal_lock:.82,depth_weight:.32,edge_weight:.7,...g.encoder};
 g.presentation={width:600,height:600,minimum:300,optional:1200,glyph_cells:'square native cells'};
 g.provenance={...g.provenance,engine:'PTFE 4.5.0',parent_version:base.genome_version,parent_fingerprint:base.fingerprint,silhouette_first:true,canonical_grid:g.grid};
 delete g.fingerprint;return g;
}
