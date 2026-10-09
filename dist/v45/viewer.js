import {AsciiDisplay} from '../ascii-display.js';
let display;
import {readJson} from '../engine.js';
import {decodeAnimation} from '../store.js';
const $=id=>document.getElementById(id);
let a,frame=0,playing=true,last=0;
function draw(){display.draw(a.frames[frame],a.luminance[frame],a.grid,600);$('timeline').value=frame;$('counter').textContent=`${frame+1} / ${a.frames.length}`;}
function tick(t){if(a&&playing&&t-last>=1000/a.fps){frame=(frame+1)%a.frames.length;last=t;draw();}requestAnimationFrame(tick);}
async function init(){
 const q=new URLSearchParams(location.search),e=q.get('edition'),experiment=q.get('experiment');
 let path,name;
 if(e&&/^\d{1,4}$/.test(e)&&Number(e)>=1&&Number(e)<=3333){path='/v45/collection/animations/'+e.padStart(4,'0')+'.frames.json.gz';name='EDITION / '+e.padStart(4,'0');}
 else if(experiment&&/^E\d{3}$/.test(experiment)){path='/v45/experiments/'+experiment+'.frames.json.gz';name='EXPERIMENT / '+experiment;}
 else throw Error('Choose a valid edition or experiment.');
 a=decodeAnimation(await readJson(path));display=new AsciiDisplay($('art'),await AsciiDisplay.font());$('art').width=600;$('art').height=600;$('timeline').max=a.frames.length-1;$('play').disabled=$('timeline').disabled=false;
 $('name').textContent=name+' · '+a.profile;$('facts').textContent=a.grid.join(' × ')+' ASCII · '+a.fps+' FPS · '+a.seconds+' second loop';
 $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
 $('timeline').oninput=()=>{playing=false;$('play').textContent='Play';frame=Number($('timeline').value);draw();};draw();requestAnimationFrame(tick);
}
init().catch(e=>{$('name').textContent='Artwork unavailable';$('error').textContent=e.message;});
