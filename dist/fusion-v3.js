/* NULL GENESIS PTFE 3: deterministic structural programs, not label combinations.
 * Legacy registries and archived genomes are deliberately never mutated. */
export const CATEGORY_NAMES = Object.freeze(['Back','Body','Eyewear','Features','Form','Headwear','Mask','Method','Motion','Palette','Stage']);
export const FUSION_OPERATORS = Object.freeze(['GEOMETRIC_FUSION','MATERIAL_TRANSPLANT','ANATOMICAL_MUTATION','TOPOLOGY_REWRITE','SYMBOLIC_OVERLAY','STRUCTURAL_CORRUPTION','DIMENSIONAL_PROJECTION','CIPHER_FUSION','ORGANIC_SYNTHESIS','METAMORPHIC_FUSION']);
const NAMES = [
 ['Vertebral Halo','Fractured Wing Scaffold','Suspended Data Mantle','Recursive Spine Array','Floating Relic Ring','Skeletal Sail Structure','Orbital Bone Segments','Mechanical Tendril Fan','Asymmetric Fragment Cloak','Molecular Spine Trail'],
 ['Split Sternum Chassis','Reverse-Jointed Torso','Hollow Vertebrae Body','Interlocking Fossil Plates','Floating Organ Lattice','Synthetic Muscle Cables','Ribbed Exoshell','Segmented Predator Frame','Suspended Core Skeleton','Recursive Joint Network'],
 ['Monocular Cipher Lens','Floating Retinal Frame','Dual Aperture Visor','Broken Optical Crown','Skeletal Ocular Harness','Rotating Lens Cluster','Split-Spectrum Grayscale Optics','Hollow Prism Eyepiece','Fractal Sight Array','Asymmetric Diagnostic Lens'],
 ['Fractured Mandible Spurs','Offset Cranial Crest','Hollow Facial Channels','Asymmetric Bone Antennae','Recursive Fang Pattern','Exposed Memory Nodes','Floating Joint Relics','Bifurcated Jaw Structure','Cryptic Surface Scars','Split-Plane Facial Anatomy'],
 ['Suspended Anatomical Monolith','Recursive Hollow Titan','Inverted Skeletal Organism','Folded Dimensional Creature','Multi-Core Apparition','Segmented Floating Colossus','Paradoxical Bone Structure','Nested Living Geometry','Orbital Chimera Formation','Self-Intersecting Relic'],
 ['Floating Vertebral Diadem','Fractured Antler Crown','Geometric Bone Circlet','Suspended Thorn Halo','Mechanical Oracle Crest','Recursive Horn Assembly','Fossilized Imperial Helm','Inverted Crown Framework','Broken Cathedral Headdress','Articulated Signal Antennae'],
 ['Offset Deathplate','Recursive Cipher Mask','Floating Mandible Veil','Split Phantom Visage','Negative-Space Faceplate','Mechanical Bone Shroud','Hollow Cathedral Mask','Fragmented Identity Shell','Rotating Facial Segments','Encrypted Anatomical Cover'],
 ['Iso-Surface Carving','Recursive SDF Grafting','Depth-Guided Glyph Weaving','Cellular Bone Accretion','Constraint-Driven Fragment Assembly','Hierarchical Voxel Erosion','Topological Surface Inversion','Skeleton-Guided Implicit Growth','Multi-Field Shape Blending','Adaptive Contour Reconstruction'],
 ['Cranial Micro-Drift','Vertebral Wave Propagation','Suspended Fragment Orbit','Recursive Joint Oscillation','Glyph Cascade Recovery','Boneplate Phase Shift','Multi-Axis Anatomical Sway','Spiral Core Reorientation','Cellular Surface Migration','Breathing Topology'],
 ['Carbon Black','Moonlit Graphite','Frosted Silver','Soft Ash','Obsidian Contrast','Pale Fossil','Metallic Mist','Deep Charcoal','High-Key Monochrome','Spectral White'],
 ['Infinite Terminal Void','Fragmented Archive Chamber','Gravitational Code Field','Synthetic Fossil Vault','Collapsed Coordinate Space','Recursive Memory Chamber','Sparse Data Horizon','Broken Simulation Plane','Suspended Glyph Observatory','Null Dimension']
];
const PRIORITY = {Form:100,Body:95,Method:90,Motion:90,Palette:90,Features:80,Mask:70,Eyewear:65,Headwear:60,Back:50,Stage:40};
const GRAMMARS=['01','0123456789ABCDEF','0123456789','()[]{}<>','+-=*%&|!','/\\|_-','0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz','0123456789ABCDEF@#$%&*','0123456789+-=()[]','.,:;irsXA253hMHGS#9B&@'];
const MATERIALS={'Bone':[18,.12,.15,1],'Charcoal':[8,.02,.08,.85],'Chrome':[110,1.6,.3,1],'Polished steel':[70,.9,.24,1],'Glass-like':[100,1.2,.55,.72],'Crystalline':[85,1.3,.43,.9],'Ceramic':[42,.38,.12,1],'Organic tissue':[16,.16,.16,.92],'Synthetic armor':[60,.7,.25,.96],'Worn machinery':[28,.3,.15,.87],'Etched circuitry':[48,.6,.23,1],'Fog':[5,.02,.42,.5],'Smoke':[4,.01,.35,.42]};
const C = (x,a,b)=>Math.min(b,Math.max(a,x));
export function stableHash(value){let n=2166136261;for(const ch of String(value)){n^=ch.charCodeAt(0);n=Math.imul(n,16777619)}n^=n>>>16;n=Math.imul(n,0x7feb352d);n^=n>>>15;return n>>>0}
const random = (seed,salt)=>stableHash(seed+'|'+salt)/4294967296;
const copy = value=>JSON.parse(JSON.stringify(value));
const idFor=(category,i)=>'V3.'+category.toUpperCase()+'.'+String(i+1).padStart(2,'0');
const variant = id=>Number(String(id).split('.').at(-1))-1;
const incompatibilities={
 'V3.BODY.02':['V3.FORM.01'],
 'V3.EYEWEAR.07':['V3.MASK.06'],
 'V3.EYEWEAR.09':['V3.MASK.07'],
 'V3.HEADWEAR.02':['V3.FEATURES.04'],
 'V3.BACK.08':['V3.FORM.09']
};
const categoryBehavior={Back:'depth-occluded rear articulated structures',Body:'volumetric anatomical reconstruction',Eyewear:'front optical solids and socket carving',Features:'prioritized identity geometry and negative space',Form:'whole-scene spatial transformation',Headwear:'cranial-bounds adapted raised structures',Mask:'separate facial shells and Boolean apertures',Method:'SDF construction and glyph conversion program',Motion:'periodic geometric deformation and articulated motion',Palette:'grayscale-only lighting and material distribution',Stage:'sparse depth-aware geometry inside the ASCII grid'};

export function buildRegistry(existing){
 const original=Array.isArray(existing)?existing:existing.traits;
 if(!Array.isArray(original)||original.length!==420)throw Error('PTFE 3 requires the complete original 420-value registry.');
 const ids=new Set(original.map(t=>t.id));if(ids.size!==420)throw Error('Duplicate legacy trait identifiers.');
 const source=original.filter(t=>/^[SCA]\d{3}$/.test(t.id));
 if(source.length!==300||['S','C','A'].some(p=>source.filter(t=>t.id.startsWith(p)).length!==100))throw Error('All 300 original source concepts must be retained.');
 const traits=copy(original),categories=[];
 for(let ci=0;ci<CATEGORY_NAMES.length;ci++){
  const category=CATEGORY_NAMES[ci],items=[];
  NAMES[ci].forEach((label,i)=>{
   const id=idFor(category,i),incompatible=[...(incompatibilities[id]||[])];
   for(const [a,bs] of Object.entries(incompatibilities))if(bs.includes(id))incompatible.push(a);
   const rules={implementation:'ptfe3/'+category.toLowerCase()+'/'+String(i+1).padStart(2,'0'),variant:i,structural_effect:categoryBehavior[category],priority:PRIORITY[category],detail_cost:category==='Palette'||category==='Motion'?0:category==='Form'?12:category==='Body'?16:8,spatial_mask:category==='Back'?'rear':category==='Headwear'?'cranial':category==='Eyewear'||category==='Mask'||category==='Features'?'face':category==='Stage'?'periphery':'whole',geometry_module:category==='Motion'?'periodic-articulated-deformation':category==='Palette'?'grayscale-material-lighting':category.toLowerCase()+'-geometry',ascii_grammar:'printable-7-bit',deterministic:true};
   const trait={id,label,category,families:['SKULLS','CHARACTERS','ANIMALS'],animation_eligible:true,compatibility:{grayscale_only:true,minimum_rarity:'COMMON',exclusive_category:true,incompatible,anatomy:'adaptive',maximum_primitives:160},rules};
   traits.push(trait);items.push(id);
  });categories.push({name:category,traits:items});
 }
 return {version:'3.0.0',source_concepts:300,procedural_values:120,nft_values:110,curated_count:traits.length,categories,traits,compatibility_edges:Object.entries(incompatibilities).flatMap(([a,b])=>b.map(id=>({a,b:id,kind:'exclusive',resolution:'higher-priority-first'})))};
}

export function resolveTraits(registry,requested={},seed='NULL-GENESIS',rarity='COMMON'){
 const all=registry.traits,map=new Map(all.map(t=>[t.id,t])),selected=[];
 for(const category of CATEGORY_NAMES){
  const supplied=Object.hasOwn(requested,category),value=requested[category];
  if(supplied&&(value===null||value==='none'||value==='None'||value==='')){
   if(['Method','Motion','Palette','Form'].includes(category))throw Error(category+' is mandatory in the V3 structural timeline.');continue;
  }
  const pool=registry.categories.find(c=>c.name===category)?.traits;if(!pool?.length)throw Error('Missing category '+category);
  let t=supplied?map.get(value)||all.find(t=>t.category===category&&t.label===value):map.get(pool[Math.floor(random(seed,category)*pool.length)]);
  if(!t||t.category!==category)throw Error('Invalid '+category+' trait: '+String(value));selected.push(t);
 }
 const accepted=[],conflicts=[];
 for(const trait of selected.slice().sort((a,b)=>PRIORITY[b.category]-PRIORITY[a.category]||a.id.localeCompare(b.id))){
  const conflicting=accepted.find(t=>(trait.compatibility.incompatible||[]).includes(t.id)||(t.compatibility.incompatible||[]).includes(trait.id));
  if(conflicting){
   const pool=registry.categories.find(c=>c.name===trait.category).traits,start=Math.floor(random(seed,'replacement:'+trait.id)*pool.length);
   const replacement=Array.from({length:pool.length},(_,i)=>map.get(pool[(start+i)%pool.length])).find(candidate=>!accepted.some(t=>(candidate.compatibility.incompatible||[]).includes(t.id)||(t.compatibility.incompatible||[]).includes(candidate.id)));
   if(!replacement)throw Error('No compatible structural replacement for '+trait.category);
   conflicts.push({suppressed:trait.id,requested:trait.id,retained:conflicting.id,replacement:replacement.id,reason:'incompatible spatial/anatomical programs',resolution:'higher-priority-first; deterministic compatible replacement'});accepted.push(replacement);
  }else accepted.push(trait);
 }
 accepted.sort((a,b)=>CATEGORY_NAMES.indexOf(a.category)-CATEGORY_NAMES.indexOf(b.category));
 return {traits:accepted,conflicts};
}

export function buildRecipes(registry){
 const sources=registry.traits.filter(t=>/^[SCA]\d{3}$/.test(t.id)),recipes=[];
 if(sources.length!==300)throw Error('Source registry is incomplete.');
 for(let i=0;i<300;i++)for(let j=0;j<4;j++){
  const operator=FUSION_OPERATORS[(i+j*3)%10],indices=[i,(i+37+j*47)%300];if(j>=1)indices.push((i+109+j*29)%300);if(j===3)indices.push((i+193)%300);
  const source_concept_ids=[...new Set(indices.map(k=>sources[k].id))],seed='PTFE3:'+source_concept_ids.join(':')+':'+operator+':'+j;
  const {traits,conflicts}=resolveTraits(registry,{},seed,['COMMON','RARE','EPIC','LEGENDARY'][j]);
  const recipe={id:'PTFE3.'+String(i*4+j+1).padStart(4,'0'),name:operator.replaceAll('_',' ')+' · '+source_concept_ids.join(' + '),source_concept_ids,operator,level:j+2,trait_ids:traits.map(t=>t.id),generation_rules:{version:3,seed_salt:seed,spatial_influence:'normalized-anatomical-field',blend_strength:.22+j*.13,detail_budget:90+j*16,child_operator:j>=2?FUSION_OPERATORS[(i+j+4)%10]:null,propagation:'stable hash → spatial masks → source SDF → transformation operator'},structural_effects:OPERATOR_DESCRIPTION[operator],geometric_effects:OPERATOR_DESCRIPTION[operator],material_effects:operator==='MATERIAL_TRANSPLANT'?'blend source roughness, reflectance and rim response':'inherit weighted source materials',applicable_anatomy_rules:['adaptive bounds','preserve primary silhouette','no forced library allocation'],ascii_glyph_grammar:'printable grayscale glyph ramp with source-weighted cipher grammar',compatible_traits:traits.map(t=>t.id),incompatible_traits:traits.flatMap(t=>t.compatibility.incompatible||[]),animation_behavior:traits.find(t=>t.category==='Motion').label,rendering_requirements:{native_grid:[30,50],max_primitives:160,grayscale_only:true},quality_validation_rules:{finite_scene:true,minimum_positive_geometry:1,finite_parameters:true,maximum_primitives:160,loop_period_frames:96},resolved_conflicts:conflicts,validation:{status:'program-validated',all_source_ids_registered:true,unique_program:true}};
  recipes.push(recipe);
 }
 return {version:'3.0.0',count:recipes.length,operators:[...FUSION_OPERATORS],source_reachability:Object.fromEntries(sources.map(t=>[t.id,recipes.filter(r=>r.source_concept_ids.includes(t.id)).map(r=>r.id)])),recipes};
}
const OPERATOR_DESCRIPTION={GEOMETRIC_FUSION:'Spatially normalized source geometry smoothly unifies at shared anatomical anchors.',MATERIAL_TRANSPLANT:'Source material responses transfer through spatially weighted carved relief.',ANATOMICAL_MUTATION:'Anatomical axes, branch distribution and articulated joint positions transform coherently.',TOPOLOGY_REWRITE:'Boolean hollowing and toroidal bridges rewrite connectivity and negative space.',SYMBOLIC_OVERLAY:'Curved symbolic channels are embossed or carved into the entity surface.',STRUCTURAL_CORRUPTION:'Deterministic plane fractures offset geometry and reconnect surviving segments.',DIMENSIONAL_PROJECTION:'Folded axes and perspective-dependent strata create a dimensional sculpture.',CIPHER_FUSION:'Binary/hex grammar accompanies real carved code bars and engraved channels.',ORGANIC_SYNTHESIS:'Curved growth paths and skeletal grafts connect source anatomical fields.',METAMORPHIC_FUSION:'Spatial deformation and coherent periodic joint ownership drive living composite geometry.'};

function bounds(scene){
 const positive=scene.filter(r=>!r[10]),lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
 for(const r of positive)for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],r[k+1]-r[k+4]);hi[k]=Math.max(hi[k],r[k+1]+r[k+4]);}
 if(!positive.length)throw Error('A fusion needs positive source geometry.');
 return {lo,hi,center:lo.map((n,k)=>(n+hi[k])/2),span:lo.map((n,k)=>hi[k]-n)};
}
function normalizeScene(scene,size=2.3){
 const b=bounds(scene),s=size/Math.max(...b.span,.1);
 return scene.map((r,i)=>{r=r.slice(0,16);while(r.length<16)r.push(0);for(let k=0;k<3;k++){r[k+1]=(r[k+1]-b.center[k])*s;r[k+4]=Math.max(.018,r[k+4]*s)}r[11]=i+1;r[13]=r[13]||1;return r;});
}
function simplifyBasis(scene,limit){
 if(scene.length<=limit)return {scene,removed:0};
 const annotated=scene.map((r,i)=>({r,i,importance:r[4]*r[5]*r[6]+(r[0]===4?.003:0)})),cutters=annotated.filter(a=>a.r[10]).sort((a,b)=>b.importance-a.importance||a.i-b.i).slice(0,Math.floor(limit*.3)),positive=annotated.filter(a=>!a.r[10]).sort((a,b)=>b.importance-a.importance||a.i-b.i).slice(0,limit-cutters.length),chosen=[...positive,...cutters].sort((a,b)=>a.i-b.i);
 return {scene:chosen.map(a=>a.r),removed:scene.length-chosen.length};
}
function createContext(scene,config,seed,grid){
 const ctx={scene,config,seed,grid,layer:0,influence:1,joint:0,grammar:GRAMMARS[9],rendering:{blend:.026,ambient:.17,fill:.22,ao:.8,rim:.22,contrast:1.08,contour:.15},repair:[],effects:[],motion:null};
 ctx.add=(k,x,y,z,sx,sy=sx,sz=sx,rx=0,ry=0,rz=0,extra=0,carve=false)=>{
  if(ctx.scene.length>=160){ctx.repair.push('geometry-budget-clipped');return null;}
  const min=grid===50?.025:.04,row=[k,x,y,z,Math.max(min,Math.abs(sx)),Math.max(min,Math.abs(sy)),Math.max(min,Math.abs(sz)),rx,ry,rz,carve?1:0,ctx.scene.length+1,extra,ctx.influence,ctx.layer,ctx.joint++%24];ctx.scene.push(row);return row;
 };
 ctx.line=(a,b,r=.045,carve=false)=>{const d=b.map((x,i)=>x-a[i]),l=Math.hypot(...d);return ctx.add(2,...a.map((x,i)=>(x+b[i])/2),r,l/2,r,Math.atan2(d[2],Math.hypot(d[0],d[1])),0,-Math.atan2(d[0],d[1]),0,carve)};
 ctx.ring=(x,y,z,rad=.35,tube=.045,rx=Math.PI/2,ry=0,rz=0)=>ctx.add(5,x,y,z,rad,tube,tube,rx,ry,rz);
 ctx.node=(x,y,z,r=.07)=>ctx.add(1,x,y,z,r,r*.85,r*.72);
 ctx.plate=(x,y,z,sx,sy,sz=.06,rz=0,carve=false)=>ctx.add(7,x,y,z,sx,sy,sz,0,0,rz,.022,carve);
 ctx.arc=(x,y,z,rx,ry,n=8,start=0,extent=Math.PI*2)=>{let prev=null;for(let i=0;i<n;i++){const a=start+extent*i/(extent>=Math.PI*2?n:n-1),p=[x+Math.cos(a)*rx,y+Math.sin(a)*ry,z];ctx.node(...p,.055);if(prev)ctx.line(prev,p,.038);prev=p;} };
 ctx.refresh=()=>{const b=bounds(ctx.scene.filter(r=>r[14]!==4));ctx.b=b;ctx.head=[b.center[0],b.hi[1]-.27,Math.min(.55,b.hi[2])];ctx.scale=C(Math.max(b.span[0],b.span[1])/2.3,.65,1.25);};ctx.refresh();return ctx;
}
function inheritSources(ctx,concepts,sourceScenes,operator){
 const primary=concepts[0],rules=concepts.map(t=>t.rules),avg=k=>rules.reduce((s,r)=>s+Number(r[k]||0),0)/rules.length;
 for(let i=0;i<ctx.scene.length;i++){
  const row=ctx.scene[i],owner=i%concepts.length,r=rules[owner],phase=random(concepts[owner].id,'anatomy')*Math.PI*2;
  for(let axis=0;axis<3;axis++){const p=C((r.proportions||[1,1,1])[axis],.65,1.4),f=.75+.25*p;row[axis+1]*=f;row[axis+4]*=f;}
  row[1]+=.035*Math.sin(row[2]*4+phase)*(1+avg('curvature'));row[9]+=.07*(1-(r.symmetry??.9))*Math.sin(phase+i*.3);row[13]=owner+1;row[15]=i%24;
 }
 const available=new Map((sourceScenes||[]).map(s=>[s.concept_id,s]));
 if(operator!=='MATERIAL_TRANSPLANT')for(let j=1;j<concepts.length;j++){
  const source=available.get(concepts[j].id);if(!source)continue;
  const normalized=normalizeScene(copy(source.scene),2.05),step=Math.max(1,Math.ceil(normalized.length/Math.max(6,Math.floor(28/concepts.length))));
  for(let k=0;k<normalized.length;k+=step){const row=normalized[k];if(row[10])continue;
   row[1]*=.72;row[2]*=.78;row[3]=row[3]*.7-.045*j;for(let axis=4;axis<7;axis++)row[axis]*=.55;row[13]=j+1;row[15]=j*5+k%5;if(ctx.scene.length<108)ctx.scene.push(row);
  }
 }
 const material=rules.map(r=>MATERIALS[r.material]||MATERIALS.Bone),mean=i=>material.reduce((s,m)=>s+m[i],0)/material.length;
 ctx.config[10]=mean(3);ctx.config[11]=mean(0);ctx.config[12]=mean(1);ctx.config[13]=mean(2);ctx.config[15]=C(avg('surface_frequency'),1,8);
 ctx.config[14]=Math.floor(avg('glyph_bias'))%10;ctx.config[7]=-.55+avg('light_yaw')*.3;
 // Each source owns a reproducible anatomical field, including legacy concepts with sparse rules.
 for(let j=0;j<concepts.length;j++){
  const t=concepts[j],r=t.rules,h=stableHash(t.id+'|'+t.label),angle=(h%6283)/1000,y=((h>>>8)%9-4)*.13,x=Math.sin(angle)*.45;
  ctx.influence=j+1;const sx=.075+((h>>>16)%7)*.006;
  ctx.add(r.feature==='armor'?7:r.feature==='beak'||r.feature==='horns'?4:r.feature==='orbital'||r.feature==='orbitals'?5:11,x,y,.25,sx,.12+((h>>>22)%5)*.03,.075,0,angle*.12,Math.sin(angle)*.32,r.feature==='armor'?.02:r.feature==='orbital'?.04:(h%17)*.03);
  if(r.feature==='wings')for(const s of [-1,1])ctx.line([s*.28,.18,-.14],[s*.85,.48,-.25],.055);
  if(r.feature==='horns'||r.feature==='crown')for(const s of [-1,1])ctx.add(4,s*.3,.9,.06,.09,.28,.09,0,0,-s*.3);
  if(r.feature==='branches'){ctx.line([0,.2,0],[x*1.8,.75,-.1],.06);ctx.node(x*1.8,.75,-.1,.09);}
 }
 ctx.influence=1;ctx.effects.push('weighted source anatomy '+concepts.map(t=>t.id).join('+'));ctx.refresh();
}
function applyOperator(ctx,name,strength=.35){
 const {scene,config:c}=ctx,b=ctx.b,h=ctx.head,s=C(strength,.1,.8);ctx.layer=0;
 switch(name){
  case 'GEOMETRIC_FUSION':ctx.rendering.blend=.035+s*.055;for(const r of scene)if(!r[10]){r[1]*=1-s*.1;r[3]*=1+s*.15;}ctx.line([-.25,-.5,0],[.25,.5,0],.1+s*.03);break;
  case 'MATERIAL_TRANSPLANT':c[11]=28+s*110;c[12]=.18+s*1.2;c[13]=.12+s*.45;c[14]=5;for(let i=0;i<5;i++)ctx.line([-.4,-.45+i*.19,.23],[.4,-.35+i*.19,.23],.042,true);break;
  case 'ANATOMICAL_MUTATION':for(const r of scene){r[1]+=s*.22*Math.sin(r[2]*3);r[9]+=s*.24*Math.sin(r[2]*4);r[15]=Math.round((r[2]+1.5)*6);}ctx.line([.15,-.3,0],[.55,-.75,.06],.08);ctx.line([.55,-.75,.06],[.33,-1,.06],.07);break;
  case 'TOPOLOGY_REWRITE':for(const r of scene)if(!r[10]&&r[4]>.18&&r[5]>.15){const q=r.slice();q[4]*=.55;q[5]*=.56;q[6]*=1.08;q[10]=1;if(scene.length<140)scene.push(q);break;}ctx.ring(0,-.3,.04,.32+s*.1,.075);ctx.rendering.blend=.015;break;
  case 'SYMBOLIC_OVERLAY':ctx.grammar='.,:;()[]{}<>/\\|_-+#@';for(let i=0;i<4;i++){const y=h[1]-.42+i*.16;ctx.line([h[0]-.26,y,h[2]+.045],[h[0]+.26,y+.065,h[2]+.045],.035,i%2===0);}break;
  case 'STRUCTURAL_CORRUPTION':for(let i=0;i<scene.length;i++){const r=scene[i];r[1]+=(r[2]>0?1:-1)*s*.16;r[3]+=(i%3-1)*s*.12;r[9]+=(i%2?1:-1)*s*.13;}ctx.plate(0,.1,.05,.8,.045,.65,0,true);c[21]=7;c[22]=Math.min(c[22],.12);break;
  case 'DIMENSIONAL_PROJECTION':for(const r of scene){const x=r[1],z=r[3];r[1]=x*.8+z*.45;r[3]=z*.7-x*.36;r[8]+=.22*Math.sin(r[2]*2);}c[1]=1;c[3]=.2;ctx.ring(0,0,-.12,.62,.055,.8,.3);break;
  case 'CIPHER_FUSION':ctx.grammar='0123456789ABCDEF+-=|/\\';c[14]=5;c[21]=5;c[22]=.045;for(let i=0;i<8;i++)ctx.plate(-.32+i*.095,h[1]-.18,h[2]+.03,.026,.10+(i%3)*.04,.05,0,i%2===0);break;
  case 'ORGANIC_SYNTHESIS':ctx.rendering.blend=.07;c[14]=2;c[11]=18;c[12]=.2;for(let i=0;i<7;i++){const a=i*.55;ctx.line([Math.sin(a)*.24,-.75+i*.22,-.06],[Math.sin(a+.55)*.24,-.53+i*.22,-.06],.065);ctx.node(Math.sin(a)*.24,-.75+i*.22,-.06,.09);}break;
  case 'METAMORPHIC_FUSION':for(const r of scene){r[9]+=.12*Math.sin(r[2]*3);r[15]=Math.floor((r[2]+1.5)*7);}ctx.rendering.blend=.045;ctx.motion={kind:9,amplitude:.36,speed:1,phase:random(ctx.seed,'metamorph-phase')*Math.PI*2};ctx.ring(0,.12,.02,.28,.065);break;
  default:throw Error('Unknown structural fusion operator: '+name);
 }ctx.effects.push(name);ctx.refresh();
}

function form(ctx,v){
 const {scene,config:c}=ctx;ctx.layer=0;
 switch(v){
  case 0:for(const r of scene){r[1]*=.58;r[2]*=1.2;r[3]*=.72;}c[3]=.24;ctx.plate(0,-.78,0,.32,.18,.23);break;
  case 1:for(const r of scene){r[1]*=1.05;r[2]*=1.12;}ctx.add(1,0,0,0,.31,.74,.3,0,0,0,0,true);ctx.ring(0,0,0,.52,.065,0);break;
  case 2:for(const r of scene){r[2]=-r[2];r[7]+=Math.PI;r[1]*=.85;}c[4]=-.13;break;
  case 3:for(const r of scene){r[3]+=.4*Math.sin(r[1]*2.7);r[8]+=.45*Math.sin(r[2]*2);r[1]*=.75;}c[3]=-.3;break;
  case 4:for(const r of scene){r[1]+=(r[1]>=0?1:-1)*.14;r[2]*=.85;}for(let i=0;i<3;i++)ctx.add(11,Math.cos(i*Math.PI*2/3)*.47,Math.sin(i*Math.PI*2/3)*.47,.12,.2,.26,.21,0,i*.7,0,.05);break;
  case 5:for(const r of scene){r[2]+=Math.round(r[2]*3)*.065;r[3]+=.08*Math.sin(r[2]*4);}for(let i=0;i<5;i++)ctx.ring(0,-.68+i*.32,0,.23+.035*i,.05,0);break;
  case 6:for(const r of scene){r[1]+=.28*Math.sin(r[2]*4);r[9]+=.25*Math.cos(r[2]*3);}ctx.ring(0,0,.05,.55,.075,.3,.8);break;
  case 7:{const major=scene.find(r=>!r[10]);ctx.add(1,0,.06,0,.55,.78,.44,0,0,0,0,true);for(let i=0;i<3;i++)ctx.ring(0,0,-.1+i*.13,.38+i*.09,.035,Math.PI/2,i*.32);if(major)major[6]*=1.15;break;}
  case 8:for(const r of scene){const a=r[2]*.85,x=r[1],z=r[3];r[1]=x*Math.cos(a)-z*Math.sin(a);r[3]=x*Math.sin(a)+z*Math.cos(a);r[2]*=.82;}for(let i=0;i<5;i++){const a=i*Math.PI*2/5;ctx.node(Math.cos(a)*.75,Math.sin(a)*.75,-.12,.13);}c[1]=1;break;
  case 9:for(const r of scene){r[1]*=.8;r[2]*=.8;r[9]+=.38;}ctx.ring(0,0,0,.65,.105,Math.PI/2,.65);ctx.ring(0,0,0,.65,.09,.8,0);break;
 }ctx.refresh();
}
function body(ctx,v){
 const c=ctx,sc=ctx.scene;c.layer=0;
 switch(v){
  case 0:c.plate(-.16,-.13,.08,.11,.45,.12,-.1);c.plate(.16,-.13,.08,.11,.45,.12,.1);for(const s of [-1,1])c.line([s*.13,.2,.05],[s*.36,-.42,.03],.055);break;
  case 1:for(const r of sc)if(r[2]<0){r[1]+=.15*Math.sin(r[2]*5);r[9]-=.25*Math.sign(r[1]);}for(const s of [-1,1]){c.line([s*.18,-.15,0],[s*.4,-.58,.15],.075);c.line([s*.4,-.58,.15],[s*.22,-.88,-.06],.06);}break;
  case 2:c.add(1,0,-.1,0,.18,.57,.25,0,0,0,0,true);for(let i=0;i<6;i++)c.ring(0,-.6+i*.17,-.02,.23,.05,0);break;
  case 3:for(let i=0;i<7;i++)c.plate((i%2?1:-1)*.06,-.6+i*.16,.13,.28,.12,.07,(i%2?1:-1)*.12);break;
  case 4:for(const r of sc)if(r[2]<.2){r[1]*=1.12;r[2]-=.07;r[3]*=.7;}for(let i=0;i<6;i++){let a=i*Math.PI/3;c.node(Math.cos(a)*.37,-.15+Math.sin(a)*.45,.13,.11);c.line([0,-.15,.02],[Math.cos(a)*.37,-.15+Math.sin(a)*.45,.13],.035);}break;
  case 5:for(const s of [-1,1])for(let i=0;i<4;i++)c.line([s*(.13+i*.04),.24,0],[s*(.19+i*.045),-.65,.08],.035);break;
  case 6:for(let i=0;i<6;i++){const y=-.6+i*.17;c.ring(0,y,0,.27+.06*Math.sin(i*.5),.065,0);c.line([0,y,-.22],[0,y+.15,-.22],.075);}break;
  case 7:for(const r of sc){r[1]*=1.2;if(r[2]<0)r[2]*=.65;}for(let i=0;i<5;i++)c.add(11,-.55+i*.26,-.17,0,.18,.19,.2,0,0,0,.015);c.line([-.65,-.23,0],[-.83,.25,-.09],.065);break;
  case 8:c.add(1,0,-.2,0,.22,.47,.22,0,0,0,0,true);c.node(0,-.18,.08,.19);for(const a of [0,Math.PI*2/3,Math.PI*4/3])c.line([0,-.18,.08],[Math.cos(a)*.38,-.18+Math.sin(a)*.43,0],.045);break;
  case 9:for(let j=0;j<3;j++)for(const s of [-1,1]){const a=[s*.16,-.6+j*.3,-.02],b=[s*.37,-.42+j*.3,.07];c.node(...a,.085);c.line(a,b,.04);c.node(...b,.06);}break;
 }c.refresh();
}
function back(c,v){
 c.layer=1;const z=c.b.lo[2]-.16;
 switch(v){
  case 0:c.arc(0,.12,z,.83,.94,11);break;
  case 1:for(const s of [-1,1]){c.line([s*.18,.27,z],[s*.95,.8,z-.2],.045);c.line([s*.3,.2,z],[s*1.03,.25,z-.22],.04);c.line([s*.95,.8,z-.2],[s*.83,.1,z-.2],.04);}break;
  case 2:for(let i=0;i<7;i++){const x=(i-3)*.19;c.line([x,.6,z],[x*1.15,-.62+(i%2)*.12,z-.1],.037);c.plate(x,-.45,z,.045,.13,.05);}break;
  case 3:for(let i=0;i<7;i++){c.node(Math.sin(i*.45)*.2,-.72+i*.24,z,.075);c.line([0,-.72+i*.24,z],[.26*Math.sin(i*.45),-.6+i*.24,z-.09],.045);}break;
  case 4:c.ring(0,.13,z,.84,.075);c.plate(-.76,.13,z,.12,.09,.1,-.3);c.plate(.58,.75,z,.13,.1,.08,.7);break;
  case 5:c.line([-.2,-.64,z],[-.2,.84,z],.055);for(let i=0;i<6;i++)c.line([-.2,-.6+i*.25,z],[.64-i*.075,-.63+i*.23,z-.16],.04);c.line([.64,-.63,z-.16],[.2,.6,z-.16],.04);break;
  case 6:for(let i=0;i<7;i++){const a=i*Math.PI*2/7;c.add(2,Math.cos(a)*.83,Math.sin(a)*.83+.1,z,.065,.11,.065,0,0,a+.5);}break;
  case 7:for(let i=0;i<6;i++){const a=(i-2.5)*.28;c.line([0,.1,z],[Math.sin(a)*.83,.72*Math.cos(a),z-.15],.05);c.line([Math.sin(a)*.83,.72*Math.cos(a),z-.15],[Math.sin(a)*1.06,.87*Math.cos(a),z-.05],.04);c.node(Math.sin(a)*.83,.72*Math.cos(a),z-.15,.06);}break;
  case 8:for(let i=0;i<8;i++)c.plate(-.62+.095*Math.sin(i),-.8+i*.21,z-.1,.11,.16,.045,(i%3-1)*.3);break;
  case 9:for(let i=0;i<8;i++){const x=.28*Math.sin(i*.8),y=-.72+i*.21;c.node(x,y,z-.04*i,.08);if(i)c.line([.28*Math.sin((i-1)*.8),y-.21,z-.04*(i-1)],[x,y,z-.04*i],.033);}break;
 }
}
function eyewear(c,v){
 c.layer=2;const [x,y,z0]=c.head,z=z0+.085,w=.27;
 switch(v){
  case 0:c.ring(x-.15,y-.06,z,.15,.045);c.add(3,x-.15,y-.06,z,.11,.035,.11,Math.PI/2);c.line([x-.31,y-.04,z],[x-.4,y+.02,z-.13],.035);break;
  case 1:c.arc(x,y-.07,z+.09,.34,.17,7);c.line([x-.32,y-.07,z],[x+.32,y-.07,z],.035);break;
  case 2:c.plate(x,y-.065,z,.34,.10,.08);for(const s of [-1,1])c.add(3,x+s*.17,y-.065,z,.075,.14,.075,Math.PI/2,0,0,0,true);break;
  case 3:for(let i=0;i<4;i++)c.ring(x-.25+i*.16,y+.1,z,.1,.035,Math.PI/2,0,(i%2?1:-1)*.22);break;
  case 4:for(const s of [-1,1]){c.ring(x+s*.17,y-.09,z,.14,.04);c.line([x+s*.3,y-.03,z],[x+s*.35,y+.22,z-.03],.045);}c.line([x-.07,y-.03,z],[x+.07,y-.03,z],.04);break;
  case 5:for(let i=0;i<3;i++){const a=i*Math.PI*2/3;c.ring(x+Math.cos(a)*.19,y-.06+Math.sin(a)*.13,z+.03*Math.sin(a),.11,.033);}break;
  case 6:c.plate(x-.17,y-.07,z,.12,.1,.05,-.15);c.add(10,x+.17,y-.07,z,.13,.12,.055,0,0,0,3);c.config[12]=.95;c.config[11]=75;break;
  case 7:c.add(10,x-.08,y-.055,z,.21,.15,.05,0,0,0,3);c.add(10,x-.08,y-.055,z,.15,.09,.13,0,0,0,3,true);break;
  case 8:for(let i=0;i<5;i++){const a=(i-2)*.5;c.ring(x+Math.sin(a)*.3,y-.05+Math.cos(a)*.1,z,.07,.025);}break;
  case 9:c.ring(x+.21,y-.075,z,.165,.04);c.plate(x-.22,y-.065,z,.08,.07,.05);c.line([x+.06,y+.03,z],[x-.2,y+.02,z],.03);break;
 }
}
function features(c,v){
 c.layer=2;const [x,y,z]=c.head;
 switch(v){
  case 0:for(const s of [-1,1])c.add(4,x+s*.25,y-.36,z,.09,.21,.08,0,0,-s*.45);break;
  case 1:c.add(7,x+.14,y+.16,z-.08,.08,.23,.14,0,.15,-.25,.03);break;
  case 2:for(const s of [-1,1])c.line([x+s*.21,y+.04,z],[x+s*.14,y-.31,z+.02],.065,true);break;
  case 3:c.line([x-.23,y+.1,z-.06],[x-.39,y+.46,z-.12],.035);c.line([x+.24,y+.12,z-.05],[x+.39,y+.3,z+.04],.045);c.node(x-.39,y+.46,z-.12,.06);break;
  case 4:for(let i=0;i<6;i++)c.add(4,x-.23+i*.09,y-.36,z,.045,.075+(i%2)*.04,.045,0,0,Math.PI);break;
  case 5:for(let i=0;i<5;i++)c.add(10,x-.2+i*.1,y-.25+(i%2)*.13,z+.04,.055,.055,.07,0,0,i*.3,6);break;
  case 6:for(const s of [-1,1]){c.ring(x+s*.35,y-.3,z-.04,.08,.035);c.node(x+s*.35,y-.3,z-.04,.038);}break;
  case 7:c.line([x-.23,y-.19,z],[x-.1,y-.44,z+.02],.075);c.line([x+.23,y-.19,z],[x+.14,y-.4,z+.02],.065);c.plate(x,y-.32,z,.05,.15,.15,0,true);break;
  case 8:for(let i=0;i<3;i++)c.line([x-.25,y-.1-i*.08,z+.005],[x+.15,y+.02-i*.08,z+.005],.028,true);break;
  case 9:for(const r of c.scene)if(r[14]!==4&&r[2]>y-.48){r[1]+=(r[1]>x?.075:-.045);r[3]+=(r[1]>x?.065:-.025);}c.plate(x,y-.12,z,.04,.31,.3,0,true);break;
 }
}
function headwear(c,v){
 c.layer=3;const x=c.head[0],y=c.b.hi[1]+.07,z=c.head[2]-.2,w=C(c.b.span[0]*.25,.25,.46);
 switch(v){
  case 0:c.arc(x,y+.04,z,w,.1,7);break;
  case 1:for(const s of [-1,1]){c.line([x+s*w*.65,y-.05,z],[x+s*w*1.1,y+.3,z-.04],.045);c.line([x+s*w*1.1,y+.3,z-.04],[x+s*w*1.65,y+.44,z-.1],.037);c.line([x+s*w,y+.26,z],[x+s*w*.8,y+.4,z+.06],.034);}break;
  case 2:c.add(10,x,y,z,w,.08,.14,0,0,0,6);c.add(10,x,y,z,w*.72,.14,.18,0,0,0,6,true);break;
  case 3:c.ring(x,y+.13,z,w+.08,.035,0);for(let i=0;i<6;i++){const a=i*Math.PI/3;c.add(4,x+Math.cos(a)*w,y+.13,z+Math.sin(a)*w,.035,.13,.035);}break;
  case 4:c.plate(x,y+.15,z,.075,.25,.08);c.plate(x,y+.25,z,w*.6,.05,.06);c.node(x,y+.45,z,.07);break;
  case 5:for(const s of [-1,1])for(let i=0;i<3;i++)c.add(4,x+s*(w*.5+i*.055),y+.1+i*.09,z-i*.05,.075-i*.013,.14-i*.016,.075,0,0,-s*(.2+i*.2));break;
  case 6:c.add(1,x,y-.04,z,w*.96,.22,.23);c.add(1,x,y-.13,z+.035,w*.77,.2,.26,0,0,0,0,true);c.plate(x,y+.16,z,w*.42,.08,.1);break;
  case 7:for(const s of [-1,1])c.line([x+s*w,y+.16,z],[x+s*w*.45,y-.07,z],.045);c.line([x-w,y+.16,z],[x+w,y+.16,z],.038);break;
  case 8:for(let i=0;i<5;i++){const xx=x+(i-2)*w*.43;c.plate(xx,y+.12,z,.045,.18+(i%2)*.1,.065);c.add(4,xx,y+.32+(i%2)*.1,z,.065,.1,.07);}break;
  case 9:for(const s of [-1,1]){c.line([x+s*w*.6,y-.02,z],[x+s*w*.7,y+.24,z],.04);c.line([x+s*w*.7,y+.24,z],[x+s*w*1.2,y+.4,z+.1],.033);c.node(x+s*w*1.2,y+.4,z+.1,.065);}break;
 }
}
function mask(c,v){
 c.layer=2;const [x,y,z0]=c.head,z=z0+.045;
 switch(v){
  case 0:c.plate(x+.08,y-.15,z,.3,.28,.055,.15);c.add(3,x-.05,y-.065,z,.085,.13,.085,Math.PI/2,0,0,0,true);break;
  case 1:for(let i=0;i<3;i++)c.add(10,x,y-.16,z+i*.035,.28-i*.04,.25-i*.035,.04,0,0,i*.22,6);c.add(10,x,y-.16,z+.1,.09,.13,.22,0,0,0,4,true);break;
  case 2:c.arc(x,y-.23,z+.13,.28,.17,6,Math.PI,Math.PI);c.line([x-.27,y-.22,z],[x-.25,y+.03,z-.05],.035);break;
  case 3:for(const s of [-1,1])c.plate(x+s*.18,y-.15+s*.045,z,.135,.24,.055,-s*.15);break;
  case 4:c.plate(x,y-.14,z,.31,.3,.07);c.add(1,x,y-.1,z,.19,.21,.3,0,0,0,0,true);break;
  case 5:for(let i=0;i<4;i++)c.plate(x,y-.36+i*.13,z,.32,.06,.065);c.line([x-.3,y-.39,z],[x-.3,y+.06,z],.04);break;
  case 6:c.add(10,x,y-.12,z,.32,.36,.07,0,0,0,5);c.add(10,x,y-.14,z,.22,.25,.14,0,0,0,5,true);c.line([x,y+.12,z],[x,y-.33,z],.04);break;
  case 7:for(let i=0;i<6;i++){const a=i*Math.PI/3;c.plate(x+Math.cos(a)*.19,y-.16+Math.sin(a)*.21,z+.035*Math.cos(a),.105,.13,.045,a*.22);}break;
  case 8:for(let i=0;i<3;i++)c.plate(x+(i-1)*.17,y-.16,z+.03*(i%2),.06,.28,.065,(i-1)*.18);break;
  case 9:c.add(1,x,y-.14,z,.31,.33,.08);for(let i=0;i<5;i++)c.plate(x-.24+i*.12,y-.1,z,.03,.17,.12,0,true);c.config[21]=6;c.config[22]=.06;break;
 }
}
function method(c,v){
 c.layer=0;const positives=c.scene.filter(r=>!r[10]&&r[14]===0),selected=positives.slice(0,Math.min(10,positives.length));
 switch(v){
  case 0:for(const r of selected.slice(0,4))c.add(1,r[1],r[2],r[3]+r[6]*.8,r[4]*.4,r[5]*.43,r[6]*.65,0,0,0,0,true);c.rendering.contour=.32;break;
  case 1:for(const r of selected.slice(0,6)){const s=.5;c.add(11,r[1]+r[4]*.7,r[2]+r[5]*.18,r[3],r[4]*s,r[5]*s,r[6]*s,.1,.15,0,.025);}c.rendering.blend=.065;break;
  case 2:c.grammar='.,:;/\\|_-()[]#@';c.config[14]=0;c.config[19]=3;c.rendering.contour=.48;c.rendering.contrast=1.25;for(const r of selected.slice(0,3))c.line([r[1]-r[4],r[2],r[3]+r[6]],[r[1]+r[4],r[2],r[3]+r[6]],.032);break;
  case 3:for(const r of selected.slice(0,5))for(let j=0;j<2;j++)c.add(10,r[1]+(j?1:-1)*r[4]*.65,r[2]+r[5]*.4,r[3],.08,.10,.08,0,0,j*.5,6);c.rendering.blend=.04;break;
  case 4:for(const r of selected){r[1]=Math.round(r[1]*12)/12;r[2]=Math.round(r[2]*12)/12;r[3]=Math.round(r[3]*12)/12;}for(let i=1;i<selected.length;i++)c.line(selected[i-1].slice(1,4),selected[i].slice(1,4),.038);c.rendering.blend=.018;break;
  case 5:for(let i=0;i<selected.length;i++){const r=selected[i];c.plate(r[1]+r[4]*.5,r[2]+r[5]*.4,r[3]+r[6]*.72,.065,.08,.11,(i%3)*.1,true);}c.rendering.blend=.008;c.config[14]=7;break;
  case 6:for(const r of selected.slice(0,4)){const q=r.slice();q[4]*=.65;q[5]*=.65;q[6]*=.7;q[10]=1;c.scene.push(q);}c.ring(0,-.22,0,.33,.065,Math.PI/2);c.rendering.blend=.01;break;
  case 7:for(let i=0;i<6;i++){const x=.13*Math.sin(i*.7),y=-.7+i*.25;c.node(x,y,-.05,.075);if(i)c.line([.13*Math.sin((i-1)*.7),y-.25,-.05],[x,y,-.05],.06);}c.rendering.blend=.07;break;
  case 8:for(const r of selected.slice(0,6)){c.add(1,r[1]*.7,r[2]*.9,r[3]+.06,r[4]*.78,r[5]*.68,r[6]*.72);}c.rendering.blend=.09;c.rendering.ao=.68;break;
  case 9:for(const r of c.scene)if(!r[10]&&r[14]!==4){const minimum=c.grid===50?.03:.045;r[4]=Math.max(minimum,r[4]);r[5]=Math.max(minimum,r[5]);r[6]=Math.max(minimum,r[6]);if(r[0]===6){r[0]=7;r[12]=.02;}}c.rendering.contour=.55;c.rendering.blend=.025;c.config[16]*=1.12;c.line([-.25,-.48,.14],[.24,-.42,.14],.034);break;
 }
}
const PALETTES=[
 [.69,1.25,8,.05,.08,.12,.12],[.84,1.12,38,.25,.23,.17,.22],[1.05,1.08,65,.52,.29,.24,.28],[.94,.94,14,.09,.13,.24,.3],[.79,1.5,24,.34,.24,.09,.13],[1.12,1.04,20,.16,.16,.28,.34],[.92,1.2,92,.82,.35,.16,.25],[.73,1.14,9,.035,.12,.13,.21],[1.19,.95,32,.23,.24,.33,.39],[1.07,1.29,105,.78,.46,.24,.29]
];
function palette(c,v){const [albedo,contrast,power,spec,rim,ambient,fill]=PALETTES[v];c.config[10]=albedo;c.config[11]=power;c.config[12]=spec;c.config[13]=rim;c.config[16]=contrast;c.rendering.contrast=contrast;c.rendering.rim=rim;c.rendering.ambient=ambient;c.rendering.fill=fill;c.config[14]=v===0?9:v===3?3:v===5?7:v===6?8:c.config[14];}
function motion(c,v,rarity,intensity){
 const tier={COMMON:.18,UNCOMMON:.23,RARE:.34,EPIC:.45,LEGENDARY:.58}[rarity]??.3;
 const amplitude=C(intensity??tier,.08,.8),phase=random(c.seed,'motion-phase')*Math.PI*2,speed=1+Math.floor(random(c.seed,'motion-speed')*3);
 c.motion={version:3,kind:v,type:v,name:NAMES[8][v],amplitude,intensity:amplitude,speed,phase,frequency:1+v%3,axis:[.45+.4*random(c.seed,'mx'),.55+.35*random(c.seed,'my'),.22+.3*random(c.seed,'mz')],limbs:v===3||v===6,joints:v===1||v===3,breath:v===9,orbit:v===2||v===7,seed:stableHash(c.seed),canonical_phase:0,period_frames:96};c.config[23]=v;
}
function stage(c,v){
 c.layer=4;const z=Math.min(-.8,c.b.lo[2]-.4);
 switch(v){
  case 0:c.line([-1,-1.07,z],[-.72,-1.07,z],.026);c.line([.72,-1.07,z],[1,-1.07,z],.026);break;
  case 1:for(const s of [-1,1]){c.plate(s*1.05,-.15,z,.08,.72,.06,.1*s);c.plate(s*.9,.73,z,.23,.06,.06,-.1*s);}break;
  case 2:for(let i=0;i<6;i++){const a=i*Math.PI/3;c.line([Math.cos(a)*1.05,Math.sin(a)*1.05,z],[Math.cos(a+.1)*.93,Math.sin(a+.1)*.93,z+.08],.026);}break;
  case 3:c.line([-1,-.92,z],[1,-.92,z],.055);for(const s of [-1,1])c.add(7,s*.94,-.56,z,.065,.36,.07,0,0,0,.025);break;
  case 4:for(const s of [-1,1]){c.line([s*1.02,-.8,z],[s*.8,.82,z-.3],.03);c.line([s*.8,.82,z-.3],[0,.96,z-.6],.03);}break;
  case 5:for(let i=0;i<3;i++)c.add(7,0,0,z-i*.12,1.02-i*.12,.94-i*.10,.035,0,0,0,.03);c.add(7,0,0,z-.18,.75,.68,.65,0,0,0,.02,true);break;
  case 6:c.line([-1.14,-.85,z],[1.14,-.85,z],.027);for(let i=0;i<3;i++)c.node(-.65+i*.64,-.86,z,.035);break;
  case 7:c.plate(-.58,-.96,z,.37,.03,.22,.06);c.plate(.43,-1.02,z,.31,.04,.2,-.1);break;
  case 8:c.arc(0,.08,z,1.04,1.02,8,0,Math.PI*2);c.line([0,.92,z],[0,1.1,z],.028);break;
  case 9:c.node(.9,.85,z,.028);c.config[7]=-.72;c.config[8]=.63;c.config[9]=.8;c.rendering.ambient=Math.max(.12,c.rendering.ambient-.025);break;
 }
}

function legacyModifiers(ctx,mods={}){
 for(const [id,value] of Object.entries(mods)){
  const group=Number(String(id).slice(1)),v=variant(value);if(!/^T\d{2}$/.test(id)||!Number.isInteger(v)||v<0||v>9)continue;
  const c=ctx.config;ctx.layer=0;
  if(group===1){c[1]=v===6?1:0;c[3]=[0,.55,-.55,1.1,0,0,.18,.3,.06,-.08][v];c[4]=v===4?-.3:v===5?.3:0;ctx.cameraScale=v===8?.86:v===9?1.15:1;}
  if(group===2){c[5]=v===4?4:0;if(v===1||v===2){const r=ctx.scene.find(r=>!r[10]&&r[4]>.17);if(r)ctx.add(1,r[1],r[2],r[3],r[4]*.6,r[5]*.65,r[6]*1.1,0,0,0,0,true);if(v===2){for(const r of ctx.scene)if(!r[10])r[4]*=.72;ctx.line([0,-.8,0],[0,.7,0],.065);}}else if(v===3||v===7)for(let i=0;i<4;i++)ctx.ring(0,-.5+i*.3,0,.32,.04,v===7?Math.PI/2:0,v===7?i*.35:0);else if(v===5||v===8)for(const r of ctx.scene){if(v===5)r[2]+=(r[2]>0?1:-1)*.06;else{r[1]+=(r[1]>0?1:-1)*.075;r[9]+=.08*Math.sin(r[2]*7);}}else if(v===6)ctx.ring(0,0,.03,.38,.055);else if(v===9)for(let i=0;i<3;i++)ctx.plate(0,-.3+i*.3,-.03,.35,.03,.12);}
  if(group===3){const lights=[[-.25,1,.75],[-1,.35,.6],[.1,-1,.7],[1,.1,-.2],[0,.2,-1],[.8,.8,1],[-.4,.6,1],[-1,.15,.5],[-.8,.3,.4],[0,1,.3]];c.splice(7,3,...lights[v]);c[18]=v;}
  if(group===4)c[14]=v;
  if(group===5)ctx.grammar=GRAMMARS[v];
  if(group===6){c[21]=v;if(v===2||v===3)for(const r of ctx.scene)r[v===2?1:2]+=.04*Math.sin(r[2]*7);}
  if(group===7)ctx.assembly=v;
  if(group===8)ctx.destruction=v;
  if(group===9){ctx.legacyMotion=v;ctx.config[23]=v;}
  if(group===10)c[19]=v;
  if(group===11){ctx.layer=1;const z=ctx.b.lo[2]-.14;for(let i=0;i<6;i++){const a=i*Math.PI/3;if(v===0||v===1){ctx.node(.26*Math.sin(i*.8),-.7+i*.27,z,.055);if(v===1){ctx.node(-.26*Math.sin(i*.8),-.7+i*.27,z+.16,.055);ctx.line([.26*Math.sin(i*.8),-.7+i*.27,z],[-.26*Math.sin(i*.8),-.7+i*.27,z+.16],.026);}}else if(v===2||v===4)ctx.ring(0,0,z,.35+i*.04,.03,Math.PI/2,v===4?i*.2:0);else if(v===3||v===5){const x=(i%3-1)*.33,y=(Math.floor(i/3)-.5)*.55;ctx.plate(x,y,z,.11,.11,.06,v===3?Math.PI/4:0);}else if(v===6)ctx.node(Math.cos(a)*(i+1)*.1,Math.sin(a)*(i+1)*.1,z,.045);else if(v===7)ctx.line([Math.cos(a)*.55,Math.sin(a)*.55,z],[Math.cos(a+Math.PI*2/3)*.55,Math.sin(a+Math.PI*2/3)*.55,z],.03);else if(v===8)ctx.line([0,-.6+i*.15,z],[Math.sin(a)*.6,-.42+i*.15,z],.035);else ctx.plate(0,-.6+i*.23,z,.3,.025,.14);}}
  if(group===12){for(const r of ctx.scene)if(r[14]===0){if(v===0)r[2]*=.97;if(v===1){r[5]*=1.09;r[2]*=1.04;}if(v===2)r[7]+=.055*Math.sin(r[2]*3);if(v===4)r[9]+=.1*Math.sin(r[2]*4);if(v===8){r[1]*=.94;r[3]*=1.08;}if(v===9){r[2]*=.86;r[9]+=.06*Math.sign(r[1]);}}if(v===3){ctx.layer=1;ctx.ring(0,0,ctx.b.lo[2]-.1,.75,.04);}if(v===5){ctx.grammar=GRAMMARS[7];c[21]=6;}if(v===6){c[21]=7;c[22]=.1;}if(v===7){c[14]=8;c[16]*=1.08;}ctx.state=v;}
 }
}

export function compileV3(base,registry,options={}){
 if(!base||!Array.isArray(base.scene)||!Array.isArray(base.config)||base.config.length!==24)throw Error('A valid scene and 24-value renderer configuration are required.');
 if(registry.curated_count!==530||registry.traits?.length!==530)throw Error('Use the frozen PTFE 3 530-value registry.');
 const seed=String(options.seed??base.seed??'NULL-GENESIS-V3'),gridValue=Array.isArray(options.grid)?options.grid[0]:options.grid??30;if(![30,50].includes(gridValue))throw Error('V3 native grid must be 30 or 50.');
 const rarity=String(options.rarity??base.rarity??'COMMON').toUpperCase();if(!['COMMON','UNCOMMON','RARE','EPIC','LEGENDARY'].includes(rarity))throw Error('Unknown V3 rarity.');
 const map=new Map(registry.traits.map(t=>[t.id,t])),sources=registry.traits.filter(t=>/^[SCA]\d{3}$/.test(t.id));
 let recipe=options.recipe??null;if(!recipe&&options.recipeId){const numeric=Number(String(options.recipeId).split('.').at(-1));if(!Number.isInteger(numeric)||numeric<1||numeric>1200)throw Error('Unknown V3 recipe.');recipe=(options.recipes?.recipes??buildRecipes(registry).recipes)[numeric-1];if(!recipe||recipe.id!==options.recipeId)throw Error('V3 recipe identity mismatch.');}
 let conceptIds=options.concepts?.length?[...options.concepts]:recipe?.source_concept_ids;
 if(!conceptIds){const count=1+Math.floor(random(seed,'concept-count')*5),start=Math.floor(random(seed,'concept-start')*300);conceptIds=Array.from({length:count},(_,i)=>sources[(start+i*67)%300].id);}
 if(conceptIds.length>8||new Set(conceptIds).size!==conceptIds.length)throw Error('Select 1–8 distinct source concepts.');
 const concepts=conceptIds.map(id=>{const t=map.get(id);if(!t||!sources.includes(t))throw Error('Unknown source concept: '+id);return t;});
 const requested=Object.fromEntries((recipe?.trait_ids||[]).map(id=>{const t=map.get(id);if(!t)throw Error('Unregistered composite trait.');return [t.category,id]}));Object.assign(requested,options.categories||{},options.traits||{});
 const resolution=resolveTraits(registry,requested,seed,rarity),basisLimit=C(112-resolution.traits.reduce((n,t)=>n+Math.min(8,t.rules.detail_cost),0),42,76),simplified=simplifyBasis(copy(base.scene),basisLimit),scene=normalizeScene(simplified.scene,2.25),config=base.config.slice();
 const ctx=createContext(scene,config,seed,gridValue);if(simplified.removed)ctx.repair.push('basis detail simplification: '+simplified.removed+' small primitives');ctx.config[2]=base.config[2]||.78;ctx.config[6]=['COMMON','UNCOMMON','RARE','EPIC','LEGENDARY'].indexOf(rarity);ctx.config[20]=stableHash(seed)&0xffffff;ctx.config[22]=C(options.parameters?.entropy??base.parameters?.entropy??.045,0,.45);ctx.config[21]=0;ctx.config[19]=4;ctx.config[5]=0;
 const operator=options.operator??recipe?.operator??FUSION_OPERATORS[Math.floor(random(seed,'operator')*10)];if(!FUSION_OPERATORS.includes(operator))throw Error('Unknown fusion operator.');
 const level=C(Number(options.level??recipe?.level??Math.min(5,concepts.length+1)),1,5);
 inheritSources(ctx,concepts,base.source_scenes,operator);if(level>1)applyOperator(ctx,operator,recipe?.generation_rules?.blend_strength??options.strength??.36);else ctx.effects.push('DIRECT_CONCEPT_EXPRESSION');
 if(level>=4)applyOperator(ctx,recipe?.generation_rules?.child_operator??FUSION_OPERATORS[(FUSION_OPERATORS.indexOf(operator)+4)%10],.22);
 const modifiers={...(base.modifiers||{}),...(options.modifiers||{})};legacyModifiers(ctx,Object.fromEntries(Object.entries(modifiers).filter(([id])=>id!=='T01'&&id!=='T03')));
 const handlers={Form:form,Body:body,Back:back,Eyewear:eyewear,Features:features,Headwear:headwear,Mask:mask,Method:method,Palette:palette,Stage:stage};
 const executionOrder=['Form','Body','Back','Features','Headwear','Mask','Eyewear','Method','Palette','Stage'];
 for(const category of executionOrder){const t=resolution.traits.find(t=>t.category===category);if(t){handlers[category](ctx,variant(t.id));ctx.effects.push(t.rules.implementation);ctx.refresh();}}
 const complexity=C(Number(options.parameters?.complexity??base.parameters?.complexity??.7),0,1),fragmentation=C(Number(options.parameters?.fragmentation??base.parameters?.fragmentation??.18),0,1);
 // Complexity adds bounded anatomical relief; it also sets the primitive budget.
 // Fragmentation offsets complete anatomical bands, including their subtraction
 // fields, so it changes actual three-dimensional topology rather than glyph noise.
 ctx.layer=0;const core=ctx.scene.filter(r=>!r[10]&&r[14]===0).sort((a,b)=>b[4]*b[5]*b[6]-a[4]*a[5]*a[6])[0];
 if(core)for(let i=0;i<Math.floor(complexity*6);i++){const a=(i+1)*2.399963229728653;ctx.add(7,core[1]+Math.sin(a)*core[4]*.55,core[2]+Math.cos(a)*core[5]*.6,core[3]+core[6]*.84,.038+complexity*.016,.05+complexity*.021,.035,0,0,a*.08,.018);}
 for(const row of ctx.scene)if(row[14]===0){const band=Math.floor((row[2]+1.8)*3),sign=band%2?1:-1;row[1]+=sign*fragmentation*.075;row[3]+=Math.sin(band*1.4)*fragmentation*.035;if(row[0]===11)row[12]+=complexity*.035;}
 ctx.effects.push('anatomical-relief complexity='+complexity,'segmented-spatial fragmentation='+fragmentation);
 const motionTrait=resolution.traits.find(t=>t.category==='Motion');motion(ctx,variant(motionTrait.id),rarity,options.motionIntensity??options.parameters?.motion_intensity);
 if(ctx.legacyMotion!==undefined){ctx.motion.amplitude=C(ctx.motion.amplitude*(.85+ctx.legacyMotion*.035),.08,.8);ctx.motion.intensity=ctx.motion.amplitude;ctx.motion.phase=(ctx.motion.phase+ctx.legacyMotion*.21)%(Math.PI*2);ctx.motion.legacy_profile=ctx.legacyMotion;}
 if(level>=5){ctx.motion.amplitude=C(ctx.motion.amplitude*1.12,.08,.8);ctx.motion.intensity=ctx.motion.amplitude;}
 const appearance=options.appearance??base.appearance??'RECOGNIZABLE';if(appearance==='WIRESPACE'){ctx.config[5]=4;ctx.rendering.contour=.6;}if(appearance==='VOID ENTITY'){ctx.config[19]=0;ctx.config[16]*=1.14;}if(appearance==='DATA FOSSIL')ctx.config[14]=4;if(appearance==='ENCRYPTED')ctx.grammar=GRAMMARS[7];
 const budget=C(Math.floor(options.detailBudget??recipe?.generation_rules?.detail_budget??(gridValue===50?72+complexity*80:48+complexity*80)),32,160);
 if(ctx.scene.length>budget){const primary=ctx.scene.filter(r=>r[14]===0),others=ctx.scene.filter(r=>r[14]!==0).sort((a,b)=>a[14]===4?1:b[14]===4?-1:b[4]*b[5]-a[4]*a[5]);ctx.scene=primary.slice(0,budget).concat(others.slice(0,Math.max(0,budget-primary.length)));ctx.repair.push('detail-budget '+budget);}
 legacyModifiers(ctx,Object.fromEntries(Object.entries(modifiers).filter(([id])=>id==='T01'||id==='T03')));
 const allBounds=bounds(ctx.scene),span=Math.max(allBounds.span[1]/.76,allBounds.span[0]/(ctx.config[2]*.76));ctx.config[0]=C(Math.max(3.45,span)*(ctx.cameraScale||1),2.8,6.8);if(options.cameraYaw!==undefined)ctx.config[3]=C(options.cameraYaw,-1.5,1.5);if(options.cameraPitch!==undefined)ctx.config[4]=C(options.cameraPitch,-.8,.8);
 if(options.contrast!==undefined)ctx.config[16]=C(options.contrast,.55,1.8);if(options.light){if(!Array.isArray(options.light)||options.light.length!==3||!options.light.every(Number.isFinite))throw Error('Invalid key light.');ctx.config.splice(7,3,...options.light.map(x=>C(x,-2,2)));}
 ctx.config[16]=C(ctx.config[16],.55,1.8);ctx.rendering.contrast=ctx.config[16];ctx.scene.forEach((r,i)=>{r[11]=i+1;for(let k=0;k<16;k++)if(!Number.isFinite(r[k]))throw Error('Fusion emitted non-finite geometry.');});if(!ctx.config.every(Number.isFinite))throw Error('Fusion emitted non-finite parameters.');
 const categories=resolution.traits.map(t=>({trait_type:t.category,value:t.label,id:t.id,implementation:t.rules.implementation}));
 const result={scene:ctx.scene,config:ctx.config,grid:[gridValue,gridValue],grammar:ctx.grammar,rendering:ctx.rendering,motion:ctx.motion,animation:{enabled:true,legendary:rarity==='LEGENDARY',profile:C(base.animation?.profile??options.profile??0,0,22),name:rarity==='LEGENDARY'?(base.animation?.name??'Legendary reconstruction'):ctx.motion.name,fps:12,seconds:8,loop:true,fragment_identity:'canonical-surface-cell',assembly_variant:ctx.assembly??base.animation?.assembly_variant??0,destruction_variant:ctx.destruction??base.animation?.destruction_variant??0,motion:ctx.motion},categories,influences:concepts.map((t,i)=>({id:t.id,name:t.label,library:t.families[0],weight:1/concepts.length,spatial_field:'anatomical ownership '+(i+1),geometry_primitives:ctx.scene.filter(r=>r[13]===i+1).length})),recipe:{id:recipe?.id??'DYNAMIC.'+stableHash(seed+'|'+conceptIds.join('|')+'|'+operator).toString(16).padStart(8,'0'),operator,level,source_concept_ids:conceptIds,program:ctx.effects},parameters:{...(base.parameters||{}),...(options.parameters||{}),complexity,fragmentation,entropy:ctx.config[22],contrast:ctx.config[16],motion_intensity:ctx.motion.amplitude,detail_budget:budget},provenance:{engine:'PTFE 3.0.0',source_genome_version:base.genome_version??'legacy',legacy_basis_fingerprint:base.fingerprint??null,source_ids:conceptIds,conflict_resolution:resolution.conflicts,deterministic_repairs:[...new Set(ctx.repair)],geometry_count:ctx.scene.length,canonical_grid:[gridValue,gridValue],no_fixed_family_allocation:true,release_status:'experimental'},bounds:allBounds};
 return result;
}
