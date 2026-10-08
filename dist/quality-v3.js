// Measured composition diagnostics. Scores are engineering aids; visual review remains required.
import {dimensions,toAscii,validateCells} from './math.js';
const clamp=x=>Math.max(0,Math.min(1,x));
export function evaluateArt(data,g={}){
 validateCells(data);const {width:w,height:h,count:n}=dimensions(data),mask=new Uint8Array(n),tone=new Float64Array(n);let occupied=0,border=0,sx=0,sy=0,sum=0,sq=0,minD=Infinity,maxD=-Infinity,normals=[0,0,0],edges=0,edgeTone=0,glyphs=new Set(),objects=new Map();
 for(let i=0;i<n;i++){
  mask[i]=data[i*12+9]>.5&&data[i*12]!==32?1:0;tone[i]=mask[i]?data[i*12+1]/255:0;if(!mask[i])continue;const x=i%w,y=Math.floor(i/w);occupied++;sx+=x;sy+=y;sum+=tone[i];sq+=tone[i]**2;glyphs.add(data[i*12]);border+=x===0||y===0||x===w-1||y===h-1;minD=Math.min(minD,data[i*12+8]);maxD=Math.max(maxD,data[i*12+8]);for(let a=0;a<3;a++)normals[a]+=data[i*12+2+a];const id=data[i*12+10];objects.set(id,(objects.get(id)||0)+1);
 }
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;for(const j of [x+1<w?i+1:-1,y+1<h?i+w:-1])if(j>=0&&mask[i]!==mask[j]){edges++;edgeTone+=Math.abs(tone[i]-tone[j]);}}
 const seen=new Uint8Array(n);let largest=0,components=0;for(let i=0;i<n;i++){if(!mask[i]||seen[i])continue;components++;let size=0,queue=[i];seen[i]=1;for(let p=0;p<queue.length;p++){const c=queue[p],x=c%w,y=Math.floor(c/w);size++;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const xx=x+dx,yy=y+dy,j=yy*w+xx;if(xx>=0&&xx<w&&yy>=0&&yy<h&&mask[j]&&!seen[j]){seen[j]=1;queue.push(j);}}}largest=Math.max(largest,size);}
 const density=occupied/n,mean=sum/Math.max(1,occupied),contrast=Math.sqrt(Math.max(0,sq/Math.max(1,occupied)-mean*mean)),center=[occupied?sx/occupied/(w-1):.5,occupied?sy/occupied/(h-1):.5],balance=clamp(1-Math.hypot(center[0]-.5,center[1]-.5)*2),clipping=border/Math.max(1,occupied),coherence=largest/Math.max(1,occupied),normalSpread=occupied?clamp(1-Math.hypot(...normals.map(x=>x/occupied))):0;
 const abstract=/CHAOS|VOID|ANOMALY|FRAGMENT|DUALITY|ABSTRACT|SCATTERED/.test(g.appearance||''),target=abstract?.2:.36,densityFit=clamp(1-Math.abs(density-target)/.48),depth=Number.isFinite(minD)?maxD-minD:0,depthScore=clamp(depth/.9),edgeSeparation=edges?edgeTone/edges:0;
 const score=occupied?100*(.23*densityFit+.20*balance+.18*(1-clamp(clipping*12))+.14*(abstract?Math.max(.35,coherence):coherence)+.13*clamp(contrast*5)+.07*depthScore+.05*clamp(normalSpread*3)):0;
 const metrics={quality_score:+score.toFixed(2),density:+density.toFixed(4),occupied_cells:occupied,components,coherence:+coherence.toFixed(4),center:center.map(x=>+x.toFixed(4)),balance:+balance.toFixed(4),clipping:+clipping.toFixed(4),tonal_contrast:+contrast.toFixed(4),edge_separation:+edgeSeparation.toFixed(4),depth_span:+depth.toFixed(4),normal_spread:+normalSpread.toFixed(4),distinct_glyphs:glyphs.size,visible_objects:objects.size,grid:[w,h],accepted:occupied>n*.05&&density<.82&&clipping<.12&&score>=48};
 const blocks=[],silhouette=[];for(let by=0;by<8;by++)for(let bx=0;bx<8;bx++){let s=0,k=0,c=0;for(let y=Math.floor(by*h/8);y<Math.floor((by+1)*h/8);y++)for(let x=Math.floor(bx*w/8);x<Math.floor((bx+1)*w/8);x++){s+=tone[y*w+x];c+=mask[y*w+x];k++;}blocks.push(s/Math.max(1,k));silhouette.push(c/Math.max(1,k));}
 const average=blocks.reduce((a,b)=>a+b,0)/64;
 return {...metrics,signature:{tone:blocks,silhouette,perceptual:blocks.map(x=>x>=average?'1':'0').join(''),geometry:JSON.stringify((g.scene||[]).map(r=>[r[0],...r.slice(1,10).map(v=>Math.round(v*20)),r[10]])),motion:JSON.stringify(g.motion||g.animation||{})},ascii:toAscii(data)};
}
export function repairGenome(genome,metrics,attempt){
 if(!Number.isInteger(attempt)||attempt<0||attempt>5)throw Error('The deterministic repair budget is limited to six attempts.');const g=structuredClone(genome),actions=[];
 if(metrics.clipping>.025||metrics.density>.65){g.config[0]=Math.min(8,g.config[0]*1.16);actions.push('expand_camera_to_recover_silhouette');}
 else if(metrics.density<.14){g.config[0]=Math.max(.3,g.config[0]*.84);actions.push('enlarge_focal_structure');}
 if(metrics.balance<.75){const solid=g.scene.filter(r=>!r[10]&&r[14]!==4);if(solid.length){const cx=solid.reduce((a,r)=>a+r[1],0)/solid.length,cy=solid.reduce((a,r)=>a+r[2],0)/solid.length;for(const r of g.scene){r[1]-=cx*.65;r[2]-=cy*.65;}actions.push('recenter_primary_geometry');}}
 if(metrics.tonal_contrast<.10){g.config[16]=Math.min(1.8,g.config[16]+.12);g.rendering={...g.rendering,fill:Math.max(.12,(g.rendering?.fill??.22)-.03)};actions.push('separate_surface_tones');}
 if(!actions.length){g.config[3]+=(attempt%2===0?1:-1)*.12;actions.push('adjust_view_for_depth_separation');}
 delete g.fingerprint;return {genome:g,actions};
}
const distance=(a,b)=>a.reduce((sum,x,i)=>sum+Math.abs(x-b[i]),0)/a.length;
export class UniquenessIndex{
 constructor(){this.exact=new Set();this.fingerprints=new Set();this.signatures=[];this.motionTemplates=new Map();}
 inspect(hash,fingerprint,signature){
  if(this.exact.has(hash)||this.fingerprints.has(fingerprint))return {unique:false,reason:'exact_duplicate'};
  for(let i=0;i<this.signatures.length;i++){
   const old=this.signatures[i],shape=distance(old.silhouette,signature.silhouette),tone=old.tone.reduce((a,x,j)=>a+(x-signature.tone[j])**2,0)/64,hamming=[...old.perceptual].filter((x,j)=>x!==signature.perceptual[j]).length;
   if(shape<.008&&tone<.00035&&hamming<=2||shape<.018&&tone<.0015&&old.geometry===signature.geometry)return {unique:false,reason:'perceptual_and_structural_duplicate',match:i,shape_distance:shape,tonal_distance:tone};
   if(old.temporal&&signature.temporal&&shape<.04&&tone<.004&&distance(old.temporal,signature.temporal)<.004)return {unique:false,reason:'animated_visual_duplicate',match:i};
  }
  return {unique:true,motion_template_uses:this.motionTemplates.get(signature.motion)||0};
 }
 add(hash,fingerprint,signature){const verdict=this.inspect(hash,fingerprint,signature);if(verdict.unique){this.exact.add(hash);this.fingerprints.add(fingerprint);this.signatures.push(signature);this.motionTemplates.set(signature.motion,(this.motionTemplates.get(signature.motion)||0)+1);}return verdict;}
}
function frameDistance(a,b){let changes=0,geometry=0,tone=0;for(let i=0;i<a.length;i+=12){changes+=a[i]!==b[i]||Math.abs(a[i+1]-b[i+1])>1;tone+=Math.abs(a[i+1]-b[i+1])/255;geometry+=Math.hypot(a[i+5]-b[i+5],a[i+6]-b[i+6],a[i+7]-b[i+7]);}const n=a.length/12;return {changed:changes,fraction:changes/n,tone:tone/n,geometry:geometry/n};}
export function evaluateLoop(frames){
 if(!Array.isArray(frames)||frames.length<3)throw Error('Loop diagnostics need at least three frames including the repeated boundary.');const first=frames[0],last=frames.at(-1);for(const f of frames){validateCells(f);if(f.length!==first.length)throw Error('Loop frame dimensions differ.');}
 const seam=frameDistance(first,last);let change=0,maxTransition=0,maxGeometryStep=0;const temporal=[];
 for(let i=0;i<frames.length-1;i++){const relative=frameDistance(first,frames[i]),step=frameDistance(frames[i],frames[i+1]),art=evaluateArt(frames[i]);change+=relative.changed;maxTransition=Math.max(maxTransition,step.fraction);maxGeometryStep=Math.max(maxGeometryStep,step.geometry);temporal.push(relative.fraction,relative.tone,relative.geometry,...art.center,art.density);}
 // The wrap step preceding the repeated canonical frame is checked separately.
 // Exact periodicity alone does not prove a smooth loop or genuine motion.
 const wrap=frameDistance(frames.at(-2),first),averageStep=temporal.length?temporal.filter((_,i)=>i%6===0).reduce((a,b)=>a+b,0)/(temporal.length/6):0;
 return {seam_cells:seam.changed,periodic:seam.changed===0&&seam.geometry<1e-6,moving_cells:change,animated:change>0,max_transition_fraction:+maxTransition.toFixed(4),max_geometry_step:+maxGeometryStep.toFixed(5),wrap_transition_fraction:+wrap.fraction.toFixed(4),wrap_geometry_step:+wrap.geometry.toFixed(5),temporal_signature:temporal.map(x=>+x.toFixed(5)),average_pose_difference:+averageStep.toFixed(4)};
}
// Diagnostic modes preserve the cell grid and produce grayscale output. Affected
// channels retain geometry so the original canonical buffer is never modified.
export function diagnosticCells(data,mode='canonical',g={}){
 validateCells(data);const out=data.slice(),{count}=dimensions(data),depths=[];for(let i=0;i<count;i++)if(data[i*12+9]>.5)depths.push(data[i*12+8]);const lo=Math.min(...depths),span=Math.max(.0001,Math.max(...depths)-lo),influences=Math.max(1,...(g.scene||[]).map(r=>r[13]||0));
 if(!['canonical','silhouette','depth','normals','wireframe','fragments','influence'].includes(mode))throw Error('Unsupported diagnostic preview.');if(mode==='canonical')return out;
 for(let i=0;i<count;i++){
  const off=i*12;if(data[off+9]<.5||data[off]===32){out[off]=32;out[off+1]=0;continue;}let v=1,char=data[off];
  if(mode==='silhouette'){char=35;v=.95;}
  if(mode==='depth')v=1-(data[off+8]-lo)/span*.8;
  if(mode==='normals')v=.12+.88*(data[off+2]*.3+data[off+3]*.45+data[off+4]*.25+1)/2;
  if(mode==='wireframe'){const p=data.slice(off+5,off+8),line=p.some(x=>Math.abs(Math.sin(x*18))<.16);v=line?1:.1;char=line?43:46;}
  if(mode==='fragments'){char='0123456789ABCDEF'.charCodeAt(i%16);v=.22+.78*(i%37)/36;}
  if(mode==='influence'){const row=g.scene[Math.round(data[off+10])-1],owner=row?.[13]||0;char='0123456789ABCDEF'.charCodeAt(owner%16);v=.2+.8*owner/influences;}
  out[off]=char;out[off+1]=255*clamp(v);
 }
 return out;
}
