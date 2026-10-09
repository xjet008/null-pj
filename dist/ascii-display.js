/* GPU presentation of canonical ASCII cells, using the measured native atlas. */
let fontPromise;
export class AsciiDisplay{
 static async font(){return fontPromise??=fetch('/data/glyph-atlas-v45.json').then(r=>{if(!r.ok)throw Error('Canonical glyph atlas unavailable.');return r.json();});}
 constructor(canvas,font){
  this.canvas=canvas;this.font=font;const gl=this.gl=canvas.getContext('webgl2',{alpha:false,antialias:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL2 is required for the canonical GPU presentation.');
  const vertex=`#version 300 es\nvoid main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.0-1.0,0,1);}`;
  const fragment=`#version 300 es
precision highp float;precision highp usampler2D;
uniform usampler2D cells;uniform sampler2D atlas;uniform vec2 grid;uniform vec2 glyphSize;uniform float presentation;uniform bool showGrid;
out vec4 color;
void main(){vec2 p=vec2(gl_FragCoord.x,presentation-gl_FragCoord.y);vec2 step=presentation/grid;ivec2 cell=ivec2(floor(p/step));uvec2 code=texelFetch(cells,cell,0).rg;int g=int(code.r)-32;float mask=0.0;
if(g>=0&&g<95){vec2 uv=mod(p,step)/step*glyphSize;uv=clamp(uv,vec2(.5),glyphSize-vec2(.5));vec2 base=vec2(g%10,g/10)*glyphSize;mask=texture(atlas,(base+uv)/(glyphSize*10.0)).r;}
float gray=(5.0+mask*float(code.g))/255.0;if(showGrid&&(mod(p.x,step.x)<.55||mod(p.y,step.y)<.55))gray=max(gray,.10);color=vec4(vec3(gray),1);}`;
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  const program=this.program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
  const [w,h]=font.cell,raw=Uint8Array.from(atob(font.pixels),c=>c.charCodeAt(0)),packed=new Uint8Array(w*h*100);for(let g=0;g<95;g++)for(let y=0;y<h;y++)packed.set(raw.subarray((g*h+y)*w,(g*h+y+1)*w),((Math.floor(g/10)*h+y)*w*10+g%10*w));
  this.atlas=gl.createTexture();gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,this.atlas);gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.R8,w*10,h*10,0,gl.RED,gl.UNSIGNED_BYTE,packed);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.uniform1i(gl.getUniformLocation(program,'atlas'),1);
  this.cells=gl.createTexture();gl.uniform1i(gl.getUniformLocation(program,'cells'),0);gl.uniform2f(gl.getUniformLocation(program,'glyphSize'),w,h);
 }
 draw(text,levels,grid,size=600,showGrid=false){
  if(![300,600,1200].includes(size))throw Error('Invalid square presentation size.');const gl=this.gl,[w,h]=grid,chars=text.replaceAll('\n','');if(chars.length!==w*h||levels.length!==w*h)throw Error('Invalid canonical display cells.');const raw=new Uint8Array(w*h*2);for(let i=0;i<w*h;i++){raw[i*2]=chars.charCodeAt(i);raw[i*2+1]=Math.max(0,Math.min(255,Math.round(levels[i])));}
  if(this.canvas.width!==size||this.canvas.height!==size)this.canvas.width=this.canvas.height=size;gl.useProgram(this.program);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.cells);gl.texImage2D(gl.TEXTURE_2D,0,gl.RG8UI,w,h,0,gl.RG_INTEGER,gl.UNSIGNED_BYTE,raw);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.uniform2f(gl.getUniformLocation(this.program,'grid'),w,h);gl.uniform1f(gl.getUniformLocation(this.program,'presentation'),size);gl.uniform1i(gl.getUniformLocation(this.program,'showGrid'),showGrid?1:0);gl.viewport(0,0,size,size);gl.drawArrays(gl.TRIANGLES,0,3);
 }
 dispose(){this.gl.deleteTexture(this.cells);this.gl.deleteTexture(this.atlas);this.gl.deleteProgram(this.program);}
}
export function animationDocument(animation,font){
 const data=JSON.stringify(animation).replaceAll('<','\\u003c'),calibration=JSON.stringify(font).replaceAll('<','\\u003c');
 return `<!doctype html><meta charset="utf-8"><title>NULL GENESIS V4.5</title><style>body{background:#050505;color:#ccc;text-align:center;font:14px Consolas,monospace}canvas{display:block;margin:20px auto;max-width:95vw;max-height:85vh}button,input{margin:10px;background:#111;color:#ccc;border:1px solid #555}</style><canvas id="art"></canvas><div><button id="play">Pause</button><input id="time" type="range"><span id="counter"></span></div><script>${AsciiDisplay.toString()};const d=${data},font=${calibration},canvas=document.querySelector('#art'),display=new AsciiDisplay(canvas,font),slider=document.querySelector('#time');let raw=d.cells?Uint8Array.from(atob(d.cells),c=>c.charCodeAt(0)):null;const n=d.grid[0]*d.grid[1],total=d.frame_count||d.frames.length;if(d.encoding==='interleaved-xor-u8')for(let f=1;f<total;f++)for(let i=0;i<n*2;i++)raw[f*n*2+i]^=raw[(f-1)*n*2+i];slider.min=0;slider.max=total-1;let frame=0,playing=true,last=0;function draw(){let text,gray;if(raw){text='';gray=new Uint8Array(n);for(let i=0;i<n;i++){text+=String.fromCharCode(raw[(frame*n+i)*2]);gray[i]=raw[(frame*n+i)*2+1];}}else{text=d.frames[frame];gray=d.luminance[frame];}display.draw(text,gray,d.grid,d.presentation?.[0]||600);slider.value=frame;document.querySelector('#counter').textContent=(frame+1)+' / '+total;}document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play';};slider.oninput=()=>{frame=+slider.value;playing=false;draw();};function tick(t){if(playing&&t-last>=1000/d.fps){frame=(frame+1)%total;last=t;draw();}requestAnimationFrame(tick);}draw();requestAnimationFrame(tick);<\/script>`;
}
