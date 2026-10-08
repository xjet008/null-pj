import {readJson} from '../engine.js';
import {decodeAnimation} from '../store.js';
const $=id=>document.getElementById(id);
let a,frame=0,playing=true,last=0;
function draw(){
 const [w,h]=a.grid,canvas=$('art'),ctx=canvas.getContext('2d'),chars=a.frames[frame].replaceAll('\n','');
 ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font='24px Consolas,monospace';ctx.textBaseline='top';
 for(let i=0;i<w*h;i++){const gray=Math.round(a.luminance[frame][i]);ctx.fillStyle=`rgb(${gray},${gray},${gray})`;ctx.fillText(chars[i],i%w*13,Math.floor(i/w)*24);}
 $('timeline').value=frame;$('counter').textContent=`${frame+1} / ${a.frames.length}`;
}
function tick(t){if(a&&playing&&t-last>=1000/a.fps){frame=(frame+1)%a.frames.length;last=t;draw();}requestAnimationFrame(tick);}
async function init(){
 const q=new URLSearchParams(location.search),e=q.get('edition'),experiment=q.get('experiment');
 let path,name;
 if(e&&/^\d{1,4}$/.test(e)&&Number(e)>=1&&Number(e)<=3333){path='/v3/collection/animations/'+e.padStart(4,'0')+'.frames.json.gz';name='EDITION / '+e.padStart(4,'0');}
 else if(experiment&&/^E\d{3}$/.test(experiment)){path='/v3/experiments/'+experiment+'.frames.json.gz';name='EXPERIMENT / '+experiment;}
 else throw Error('Choose a valid edition or experiment.');
 a=decodeAnimation(await readJson(path));$('art').width=a.grid[0]*13;$('art').height=a.grid[1]*24;$('timeline').max=a.frames.length-1;$('play').disabled=$('timeline').disabled=false;
 $('name').textContent=name+' · '+a.profile;$('facts').textContent=a.grid.join(' × ')+' ASCII · '+a.fps+' FPS · '+a.seconds+' second loop';
 $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
 $('timeline').oninput=()=>{playing=false;$('play').textContent='Play';frame=Number($('timeline').value);draw();};draw();requestAnimationFrame(tick);
}
init().catch(e=>{$('name').textContent='Artwork unavailable';$('error').textContent=e.message;});
