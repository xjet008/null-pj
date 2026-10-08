import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {seal,checkGenome,Engine} from '../dist/engine.js';
import {renderCpu,frameCpu,animateScene,dimensions,toAscii,fromAscii,validateCells,fieldV3,V3_RENDER_DEFAULTS} from '../dist/math.js';
import {evaluateArt,evaluateLoop,diagnosticCells,repairGenome,UniquenessIndex} from '../dist/quality-v3.js';
globalThis.crypto??=webcrypto;
const coverage=Array.from({length:95},(_,i)=>i/280);coverage[0]=0;
const row=(kind,x,y,z,sx,sy,sz,carve=0,layer=0,joint=0)=>[kind,x,y,z,sx,sy,sz,0,0,0,carve,1,kind===10?5:0,1,layer,joint];
const fixture=()=>({genome_version:'web-3.0.0',render_version:'webgpu-sdf-3.0.0',grid:[30,30],seed:'a'.repeat(64),rarity:'COMMON',appearance:'RECOGNIZABLE',scene:[row(1,0,.12,0,.5,.65,.38),row(7,0,-.55,.1,.36,.08,.28),row(0,-.19,.25,.31,.11,.11,.11,1,2),row(0,.19,.25,.31,.11,.11,.11,1,2),row(2,.48,-.35,0,.055,.24,.055,0,1,1)],config:[3.65,0,26/48,.11,.05,0,0,-.25,1,.75,1,18,.12,.15,2,3,1.05,0,0,1,1003,4,.03,0],grammar:' .:-=+*#%@/\\|_!',coverage:[...coverage],samples:1,rendering:{...V3_RENDER_DEFAULTS},motion:{kind:9,type:9,amplitude:.45,intensity:.45,speed:1,phase:.3,frequency:2,axis:[1,0,0],seed:1003},animation:{enabled:true,legendary:false,profile:4,fps:12,seconds:3,assembly_variant:2,destruction_variant:1}});

test('Legacy CPU render retains its exact pre-upgrade bytes',()=>{
 const g=fixture();g.genome_version='web-1.0.0';delete g.grid;g.scene=[[0,0,0,0,.65,.65,.65,0,0,0,0,1,0,0,0,0]];g.config=[3.65,0,26/48,.11,.05,0,0,-.25,1,.75,1,18,.12,.15,2,8,1.05,0,0,1,1003,4,.1,0];g.grammar='0123456789ABCDEF';g.animation.seconds=8;const data=renderCpu(g),hash=createHash('sha256').update(new Uint8Array(data.buffer)).digest('hex');assert.equal(hash,'6242ea2881f8a6e5dd16135638d7ae732ded01ca2aebc48ed9ca464242afe7e9');assert.deepEqual(frameCpu(data,g,32),data);assert.deepEqual(frameCpu(data,g,86),data);assert.deepEqual(frameCpu(data,g,0),frameCpu(data,g,96));
});
test('V3 renders native 900 and 2500 cells with real geometry and grayscale',()=>{
 const g=fixture(),small=renderCpu(g),large=renderCpu({...g,grid:[50,50]});validateCells(small);validateCells(large);assert.equal(small.length,10800);assert.equal(large.length,30000);assert.deepEqual([...dimensions(large)],[50,50]);const lines=toAscii(large).slice(0,-1).split('\n');assert.equal(lines.length,50);assert.equal(toAscii(large).split('\n')[0].length,50);assert.ok(large.some((v,i)=>i%12===9&&v===1));assert.ok(large.some((v,i)=>i%12===2&&Math.abs(v)>.2));assert.deepEqual(renderCpu(g),small);assert.notEqual(toAscii(large),toAscii(small));assert.equal(toAscii(fromAscii(toAscii(large),Array.from({length:2500},(_,i)=>large[i*12+1]))),toAscii(large));
});
test('All twelve primitives and smooth CSG have finite, meaningful signed fields',()=>{
 const g=fixture();for(let k=0;k<12;k++){g.scene=[row(k,0,0,0,.4,.25,.3)];assert.ok(fieldV3([0,.03,.01],g).every(Number.isFinite));assert.ok(fieldV3([3,3,3],g)[0]>0);}
 g.scene=[row(0,0,0,0,.5,.5,.5),row(0,0,0,.4,.2,.2,.2,1)];assert.ok(fieldV3([0,0,.4],g)[0]>0,'carved cavity is empty');assert.ok(fieldV3([0,0,-.2],g)[0]<0,'solid body remains');g.scene=[row(0,-.2,0,0,.3,.3,.3),row(0,.2,0,0,.3,.3,.3)];const hard=fieldV3([0,0,0],{...g,rendering:{blend:0}})[0],soft=fieldV3([0,0,0],{...g,rendering:{blend:.09}})[0];assert.ok(soft<hard,'smooth union changes the geometric field');
});
test('V3 lighting follows physical key direction and occlusion, not random glyphs',()=>{
 const g=fixture(),a=renderCpu(g),b=renderCpu({...g,config:g.config.map((v,i)=>i===7?-v:v)});let changed=0;for(let i=0;i<a.length;i+=12)if(a[i+9]&&Math.abs(a[i+1]-b[i+1])>2)changed++;assert.ok(changed>20);const dark=renderCpu({...g,rendering:{...g.rendering,fill:0,ambient:0,rim:0}});assert.notDeepEqual(a,dark);assert.deepEqual(a,renderCpu(g),'temporal canonical glyph selection is stable');
});
test('Ten motion programs alter primitive poses, close loops and preserve canonical zero',()=>{
 for(let kind=0;kind<10;kind++){const g=fixture();g.motion.kind=g.motion.type=kind;const a=animateScene(g,0),b=animateScene(g,7),total=g.animation.fps*g.animation.seconds;assert.deepEqual(a.scene,g.scene);assert.deepEqual(animateScene(g,total).scene,g.scene);assert.notDeepEqual(b.scene,g.scene,'kind '+kind+' changes geometry');const near=animateScene(g,total-1).scene;let seam=0;for(let i=0;i<near.length;i++)for(let j=1;j<10;j++)seam=Math.max(seam,Math.abs(near[i][j]-g.scene[i][j]));assert.ok(seam<.15,'kind '+kind+' has a bounded wrap pose step');const canonical=renderCpu(g),moved=frameCpu(canonical,g,7);validateCells(moved);assert.notDeepEqual(moved,canonical,'kind '+kind+' changes actual native ASCII cells');}
 const g=fixture(),base=renderCpu(g),frames=[base,frameCpu(base,g,7),frameCpu(base,g,14),frameCpu(base,g,35),frameCpu(base,g,36)],loop=evaluateLoop(frames);assert.equal(loop.periodic,true);assert.equal(loop.animated,true);assert.ok(loop.moving_cells>0);assert.deepEqual(frames.at(-1),base);
});
test('V3 Legendary profiles keep distinct depth-aware reconstruction paths at 50 by 50',()=>{
 const g=fixture();g.grid=[50,50];g.rarity='LEGENDARY';g.animation.legendary=true;g.animation.seconds=8;const base=renderCpu(g),signatures=new Set();for(let profile=0;profile<23;profile++){g.animation.profile=profile;const frame=frameCpu(base,g,25,0);validateCells(frame);signatures.add(createHash('sha256').update(new Uint8Array(frame.buffer)).digest('hex'));assert.deepEqual(frameCpu(base,g,0),base);assert.deepEqual(frameCpu(base,g,96),base);}assert.equal(signatures.size,23);
});
test('V3 DNA validates exact hash, bounded native grids, geometry ownership, lighting and periodic motion',async()=>{
 const g=await seal(fixture());await checkGenome(g);for(const [key,value,expected] of [['grid',[31,31],/grid/],['samples',8,/grammar/],['motion',{...g.motion,speed:1.5},/motion/],['rendering',{...g.rendering,blend:2},/lighting/]]){const bad=structuredClone(g);bad[key]=value;await seal(bad);await assert.rejects(checkGenome(bad),expected);}let bad=structuredClone(g);bad.scene[0][14]=5;await seal(bad);await assert.rejects(checkGenome(bad),/ownership/);bad=structuredClone(g);bad.motion.type=4;await seal(bad);await assert.rejects(checkGenome(bad),/aliases/);bad=structuredClone(g);bad.motion.phase=Infinity;await seal(bad);await assert.rejects(checkGenome(bad),/motion/);bad=structuredClone(g);bad.scene[0][1]+=.001;await assert.rejects(checkGenome(bad),/fingerprint/);
});
test('Cell and ASCII imports reject malformed grids, Unicode and nongray levels',()=>{
 assert.throws(()=>dimensions(new Float32Array(120)),/grid/);assert.throws(()=>fromAscii(('A'.repeat(30)+'\n').repeat(30),Array(900).fill(256)),/grayscale/);assert.throws(()=>fromAscii(('雪'.repeat(30)+'\n').repeat(30),Array(900).fill(100)),/ASCII/);const data=renderCpu(fixture());data[0]=32.2;assert.throws(()=>validateCells(data),/ASCII/);assert.throws(()=>toAscii(new Float32Array(100)),/grid/);
});
test('Measured quality, diagnostics, finite repairs and visual duplicate rejection',()=>{
 const g=fixture(),data=renderCpu(g),quality=evaluateArt(data,g);assert.ok(quality.quality_score>0);assert.ok(quality.depth_span>0);assert.ok(quality.normal_spread>0);assert.equal(quality.grid[0],30);const blank=new Float32Array(10800);for(let i=0;i<900;i++)blank[i*12]=32;assert.equal(evaluateArt(blank).accepted,false);assert.equal(evaluateArt(blank).quality_score,0);for(const mode of ['canonical','silhouette','depth','normals','wireframe','fragments','influence']){const d=diagnosticCells(data,mode,g);validateCells(d);assert.equal(d.length,data.length);}assert.deepEqual(data,renderCpu(g),'diagnostics preserve the canonical buffer');const metrics={...quality,density:.01},repair=repairGenome(g,metrics,0);assert.ok(repair.genome.config[0]<g.config[0]);assert.deepEqual(repairGenome(g,metrics,0),repair);assert.throws(()=>repairGenome(g,metrics,6),/budget/);const index=new UniquenessIndex();assert.equal(index.add('hash-a','fp-a',quality.signature).unique,true);assert.equal(index.add('hash-a','fp-b',quality.signature).reason,'exact_duplicate');const signature={...quality.signature,geometry:'different internal scene'};assert.equal(index.inspect('hash-b','fp-b',signature).unique,false,'identical visible art cannot pass with a renamed genome');
});
test('CUDA adapter routing requires measured CUDA status and preserves grayscale validation',async()=>{
 const engine=new Engine(),g=fixture(),data=renderCpu(g),calls=[];assert.throws(()=>engine.attachNative({status:{backend:'CPU'}}),/verified CUDA/);engine.attachNative({status:{backend:'CUDA',device:'Synthetic NVIDIA adapter for dispatch test'},async render(genome){calls.push(['render',genome]);return data},async frame(base,genome,index,staticA){calls.push(['frame',index,staticA]);return frameCpu(base,genome,index,staticA)},async image(){return 'data:image/png;base64,test'}});assert.deepEqual(await engine.render(g),data);await engine.frame(data,g,7);assert.equal(engine.backend,'CUDA');assert.equal(calls[0][0],'render');assert.equal(calls[1][0],'frame');assert.equal(engine.metrics.renders,1);assert.equal(engine.metrics.frames,1);
});
test('Legacy laboratory genomes use CUDA when the active backend reports CUDA',async()=>{
 const engine=new Engine(),g={...fixture(),genome_version:'web-1.0.0'},data=renderCpu(g),calls=[];
 engine.attachNative({status:{backend:'CUDA'},async render(){calls.push('render');return data},async frame(){calls.push('frame');return data},async image(){return ''}});
 assert.deepEqual(await engine.render(g),data);await engine.frame(data,g,7);
 assert.deepEqual(calls,['render','frame']);assert.equal(engine.backend,'CUDA');
});
