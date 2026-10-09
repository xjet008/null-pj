// NULL GENESIS: all surface evaluation, lighting, cells, fragments and raster run on CUDA.
struct V{float x,y,z;};
__device__ V v(float x,float y,float z){return {x,y,z};}
__device__ V add(V a,V b){return v(a.x+b.x,a.y+b.y,a.z+b.z);}
__device__ V sub(V a,V b){return v(a.x-b.x,a.y-b.y,a.z-b.z);}
__device__ V mul(V a,float b){return v(a.x*b,a.y*b,a.z*b);}
__device__ float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
__device__ V cross(V a,V b){return v(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
__device__ float len(V a){return sqrtf(dot(a,a));}
__device__ V norm(V a){return mul(a,1.f/fmaxf(len(a),.00001f));}
__device__ float clamp(float a,float b,float c){return fminf(c,fmaxf(b,a));}
__device__ V rotate(V a,float x,float y,float z){
 float co=cosf(x),si=sinf(x);a=v(a.x,co*a.y-si*a.z,si*a.y+co*a.z);
 co=cosf(y);si=sinf(y);a=v(co*a.x+si*a.z,a.y,-si*a.x+co*a.z);
 co=cosf(z);si=sinf(z);return v(co*a.x-si*a.y,si*a.x+co*a.y,a.z);
}
__device__ V inverse(V a,float x,float y,float z){
 float co=cosf(z),si=sinf(z);a=v(co*a.x+si*a.y,-si*a.x+co*a.y,a.z);
 co=cosf(y);si=sinf(y);a=v(co*a.x-si*a.z,a.y,si*a.x+co*a.z);
 co=cosf(x);si=sinf(x);return v(a.x,co*a.y+si*a.z,-si*a.y+co*a.z);
}
__device__ float box(V q,V s){
 V a=v(fabsf(q.x)-s.x,fabsf(q.y)-s.y,fabsf(q.z)-s.z);
 return len(v(fmaxf(a.x,0),fmaxf(a.y,0),fmaxf(a.z,0)))+fminf(fmaxf(a.x,fmaxf(a.y,a.z)),0);
}
__device__ float primitive(V p,const float* r){
 V q=sub(p,v(r[1],r[2],r[3]));float co=r[20],si=r[21];q=v(co*q.x+si*q.y,-si*q.x+co*q.y,q.z);
 co=r[18];si=r[19];q=v(co*q.x-si*q.z,q.y,si*q.x+co*q.z);
 co=r[16];si=r[17];q=v(q.x,co*q.y+si*q.z,-si*q.y+co*q.z);V s=v(r[4],r[5],r[6]);int k=(int)r[0];
 if(k==0)return len(q)-s.x;
 if(k==1||k==11){
  float d=(len(v(q.x/s.x,q.y/s.y,q.z/s.z))-1)*fminf(s.x,fminf(s.y,s.z));
  if(k==11)d+=.018f*sinf(q.x*13+r[12])*sinf(q.y*11)*sinf(q.z*9);
  return d;
 }
 if(k==2)return len(v(q.x,fmaxf(fabsf(q.y)-s.y,0),q.z))-s.x;
 if(k==3){float a=sqrtf(q.x*q.x+q.z*q.z)-s.x,b=fabsf(q.y)-s.y;return fminf(fmaxf(a,b),0)+sqrtf(fmaxf(a,0)*fmaxf(a,0)+fmaxf(b,0)*fmaxf(b,0));}
 if(k==4){float radius=s.x*clamp((s.y-q.y)/(2*s.y),0,1);return fmaxf((sqrtf(q.x*q.x+q.z*q.z)-radius)*.7f,fabsf(q.y)-s.y);}
 if(k==5){float a=sqrtf(q.x*q.x+q.z*q.z)-s.x;return sqrtf(a*a+q.y*q.y)-s.y;}
 if(k==7)return box(q,s)-r[12];
 if(k==9){q.x-=r[12]*sinf(q.y*4);return box(q,s);}
 if(k==10){
  int sides=(int)r[12];float a=atan2f(q.y/s.y,q.x/s.x),sector=6.2831853f/sides;
  float radial=sqrtf(q.x*q.x/(s.x*s.x)+q.y*q.y/(s.y*s.y));
  float boundary=cosf(3.14159265f/sides)/cosf(a-sector*floorf((a+sector*.5f)/sector));
  return fmaxf((radial-boundary)*fminf(s.x,s.y),fabsf(q.z)-s.z);
 }
 return box(q,s);
}
__device__ float field(V p,const float* scene,int count,int* id,int topology,float blending){
 float a=100,b=100;int ai=0,bi=0;
 for(int i=0;i<count;i++){
  const float* r=scene+i*32;
  // Conservative lower bound of the implemented primitive field. Blending
  // influences only distances within its finite support; a positive bound
  // farther than the current minimum plus that support cannot change the result.
  float bound=(len(sub(p,v(r[1],r[2],r[3])))-r[22])*r[23];
  if(bound>0 && bound>(r[10]>.5f?b:a+blending)+.0001f)continue;
  float d=primitive(p,r);
  if(r[10]>.5f){if(d<b){b=d;bi=i+1;}}else {
   float blend=fminf(blending,fminf(r[4],fminf(r[5],r[6]))*.35f);
   if(blend>0 && a<99 && r[14]!=4){float h=clamp(.5f+.5f*(a-d)/blend,0,1);float merged=a*(1-h)+d*h-blend*h*(1-h);if(d<a)ai=i+1;a=merged;}
   else if(d<a){a=d;ai=i+1;}
  }
 }
 float result=fmaxf(a,-b);*id=a>-b?ai:bi;
 if(topology==4){ // volumetric wire cage: shell intersected with world-space lattice
  float lattice=fminf(fabsf(sinf(p.x*19)),fminf(fabsf(sinf(p.y*19)),fabsf(sinf(p.z*19))))*.04f-.009f;
  result=fmaxf(fabsf(result)-.018f,lattice);
 }
 return result;
}
__device__ float field_reference(V p,const float* scene,int count,int* id,int topology,float blending){
 float a=100,b=100;int ai=0,bi=0;
 for(int i=0;i<count;i++){
  const float* r=scene+i*32;
  // Conservative lower bound of the implemented primitive field. Blending
  // influences only distances within its finite support; a positive bound
  // farther than the current minimum plus that support cannot change the result.
  float bound=(len(sub(p,v(r[1],r[2],r[3])))-r[22])*r[23];
  
  float d=primitive(p,r);
  if(r[10]>.5f){if(d<b){b=d;bi=i+1;}}else {
   float blend=fminf(blending,fminf(r[4],fminf(r[5],r[6]))*.35f);
   if(blend>0 && a<99 && r[14]!=4){float h=clamp(.5f+.5f*(a-d)/blend,0,1);float merged=a*(1-h)+d*h-blend*h*(1-h);if(d<a)ai=i+1;a=merged;}
   else if(d<a){a=d;ai=i+1;}
  }
 }
 float result=fmaxf(a,-b);*id=a>-b?ai:bi;
 if(topology==4){ // volumetric wire cage: shell intersected with world-space lattice
  float lattice=fminf(fabsf(sinf(p.x*19)),fminf(fabsf(sinf(p.y*19)),fabsf(sinf(p.z*19))))*.04f-.009f;
  result=fmaxf(fabsf(result)-.018f,lattice);
 }
 return result;
}
__device__ V normal(V p,const float* sc,int n,int top,float blending){
 int id;float e=blending>0?.0025f:.003f;
 return norm(v(field(add(p,v(e,0,0)),sc,n,&id,top,blending)-field(sub(p,v(e,0,0)),sc,n,&id,top,blending),
 field(add(p,v(0,e,0)),sc,n,&id,top,blending)-field(sub(p,v(0,e,0)),sc,n,&id,top,blending),
 field(add(p,v(0,0,e)),sc,n,&id,top,blending)-field(sub(p,v(0,0,e)),sc,n,&id,top,blending)));
}
__device__ unsigned hash(unsigned x){x^=x>>16;x*=0x7feb352dU;x^=x>>15;x*=0x846ca68bU;return x^(x>>16);}
__device__ float rnd(unsigned x){return (hash(x)&0xFFFFFF)/16777216.f;}
__device__ float texture(V p,int kind,float f){
 float x=p.x*f,y=p.y*f,z=p.z*f;
 if(kind==0)return .68f+.32f*fabsf(sinf((x+y)*6)*sinf((x-y)*6));
 if(kind==1)return .6f+.4f*powf(fabsf(sinf(x*9)*sinf(y*9)*sinf(z*7)),.25f);
 if(kind==2)return .72f+.28f*sinf(x*6)*sinf(y*6);
 if(kind==3)return .83f+.17f*sinf(x*21+y*17+z*25);
 if(kind==4)return .72f+.28f*fabsf(sinf(y*15));
 if(kind==5)return .62f+.38f*fabsf(sinf(x*10)*cosf(z*10));
 if(kind==6)return .55f+.45f*clamp(fabsf(sinf(x*5+sin(y*7)))*4,0,1);
 if(kind==7)return .63f+.37f*fabsf(sinf(x*14)*sinf(y*14));
 if(kind==8)return 1;
 return .57f+.43f*fabsf(sinf(x*19+y*3)*sinf(z*23+y*17));
}
__device__ __noinline__ void render_one(const float* scene,int count,const float* cfg,const float* coverage,const unsigned char* grammar,int gn,unsigned char* glyph,float* cells,int ss,int cell){
 int width=(int)cfg[24],height=(int)cfg[25];int x=cell%width,y=cell/width;
 float lum=0,depth=0;V pos=v(0,0,0),nr=v(0,0,0);int hits=0,object=0,top=(int)cfg[5];
 for(int sy=0;sy<ss;sy++)for(int sx=0;sx<ss;sx++){
  float px=((x+(sx+.5f)/ss)/width-.5f)*cfg[0]*cfg[2],py=(.5f-(y+(sy+.5f)/ss)/height)*cfg[0];
  V origin=v(0,0,4),dir=norm(v(px,py,-4));
  if(cfg[1]>.5f){origin=v(px,py,4);dir=v(0,0,-1);}
  origin=rotate(origin,cfg[4],cfg[3],0);dir=rotate(dir,cfg[4],cfg[3],0);
  float t=0;int id=0;bool hit=false;
  for(int step=0;step<(cfg[26]>.5f?160:108);step++){V q=add(origin,mul(dir,t));float d=field(q,scene,count,&id,top,cfg[27]);if(d<(cfg[26]>.5f?.0035f*30/width:.0075f)){hit=true;break;}t+=fmaxf(d*(cfg[26]>.5f?.68f:.72f),cfg[26]>.5f?.0015f:.004f);if(t>8)break;}
  if(!hit)continue;
  V p=add(origin,mul(dir,t)),n=normal(p,scene,count,top,cfg[27]),light=norm(v(cfg[7],cfg[8],cfg[9]));
  float diff=fmaxf(dot(n,light),0),rim=powf(1-fmaxf(-dot(n,dir),0),2.7f);
  V halfway=norm(sub(light,dir));float spec=powf(fmaxf(dot(n,halfway),0),cfg[11])*cfg[12];
  int dummy;float ao=clamp(field(add(p,mul(n,.09f)),scene,count,&dummy,top,cfg[27])/.09f,.18f,1);
  float shadow=1;
  if(cfg[6]>=2){float st=.035f;for(int j=0;j<8;j++){float d=field(add(p,mul(light,st)),scene,count,&dummy,top,cfg[27]);shadow=fminf(shadow,clamp(d*12/st,.15f,1));st+=clamp(d,.04f,.2f);}}
  float value=(.15f+diff*.64f*shadow+rim*cfg[13]+spec)*ao;
  if(cfg[26]>.5f){
   float accumulated=0,weight=1;
   for(int sample=0;sample<3;sample++){float distance=sample==0?.045f:sample==1?.11f:.23f;float d=field(add(p,mul(n,distance)),scene,count,&dummy,top,cfg[27]);accumulated+=(distance-d)*weight;weight*=.55f;}
   ao=clamp(1-accumulated*3.5f*cfg[30],.22f,1);
   float st=.018f;shadow=1;for(int j=0;j<10;j++){float d=field(add(p,mul(light,st)),scene,count,&dummy,top,cfg[27]);shadow=fminf(shadow,clamp(d*10/st,.2f,1));st+=clamp(d,.025f,.16f);if(st>.85f)break;}
   V fill=norm(v(-.7f,-.15f,.6f));float fillAmount=fmaxf(dot(n,fill),0)*cfg[29];
   const float metals[10]={.04f,.95f,.65f,.23f,.8f,.9f,.7f,.12f,0,.3f};float metal=metals[max(0,min(9,(int)cfg[14]))];
   spec=powf(fmaxf(dot(n,halfway),0),fmaxf(2,cfg[11]))*(cfg[12]+metal*.13f);
   value=(cfg[28]+diff*.68f*shadow+fillAmount+rim*cfg[31]+spec*shadow)*ao;
  }
  int lighting=(int)cfg[18];if(lighting==4)value=cfg[26]>.5f?.16f+rim*.84f:.2f+rim*.8f;if(lighting==7&&p.x<0)value*=cfg[26]>.5f?.32f:.28f;if(lighting==8)value=powf(value,cfg[26]>.5f?1.45f:1.6f);
  if(cfg[36]>4){
   // Dual depth and curvature probes separate cavities and thin surfaces before
   // glyph quantization. Small probes follow the actual implicit surface.
   float d1=field(add(p,mul(dir,.025f)),scene,count,&dummy,top,cfg[27]);
   float d2=field(add(p,mul(dir,.09f)),scene,count,&dummy,top,cfg[27]);
   float thickness=clamp(-d2/.09f,0,1);
   V tangent=norm(cross(n,v(.3f,.8f,.4f)));
   float curvature=fabsf(field(add(p,mul(tangent,.045f)),scene,count,&dummy,top,cfg[27]))/.045f;
   float cavity=clamp(1+fminf(d1,0)*2.3f,.72f,1);
   value=value*cavity*(.9f+.1f*thickness)+clamp(curvature,0,1)*rim*.11f;
   value*=.86f+.14f*texture(p,(int)cfg[14],cfg[15]);value*=cfg[10];
  }else value*=texture(p,(int)cfg[14],cfg[15])*cfg[10];
  lum+=cfg[26]>.5f?powf(clamp(value*cfg[16],.025f,1),1/cfg[32]):clamp(value*cfg[16],.025f,1);depth+=t;pos=add(pos,p);nr=add(nr,n);hits++;object=id;
 }
 float* o=cells+cell*12;
 for(int j=0;j<12;j++)o[j]=0;
 if(!hits){glyph[cell]=' ';return;}
 lum/=ss*ss;depth/=hits;pos=mul(pos,1.f/hits);nr=norm(nr);
 int density=(int)cfg[19];if(density==0&&lum<(cfg[26]>.5f?.22f:.27f)){glyph[cell]=' ';return;}
 if(density==5&&fabsf(pos.x)<.15f&&fabsf(pos.y)<.25f){glyph[cell]=' ';return;}
 if(density==6)lum*=clamp(.7f-pos.x*.25f,.3f,1);
 if(density==7)lum*=clamp(.7f+pos.x*.25f,.3f,1);
 if(density==8)lum*=.65f+.35f*fabsf(sinf(len(pos)*12));
 if(density==9)lum*=.65f+.35f*fabsf(sinf(pos.x*9)*sinf(pos.y*7));
 int mode=(int)cfg[17];if(mode==8)lum*=.42f;if(mode==7)lum*=.75f;
 float target=cfg[26]>.5f?clamp(.025f+lum*.36f,.02f,.42f):clamp(.04f+lum*.32f,.025f,.4f),best=100;unsigned char g='.';
 unsigned seed=(unsigned)cfg[20];V viewNormal=inverse(nr,cfg[4],cfg[3],0);float edge=1-fabsf(viewNormal.z);
 unsigned cellSeed=hash((unsigned)((floorf(pos.x*71)+512)*997+(floorf(pos.y*71)+512)*313+object*911));
 for(int i=0;i<gn;i++){
  unsigned char c=grammar[i];float directional=0;if(cfg[26]>.5f && edge>.45f){bool horizontal=fabsf(viewNormal.y)>fabsf(viewNormal.x);bool tangent=horizontal?(c=='_'||c=='-'||c=='='):(c=='|'||c=='!'||c==':');bool diagonal=c==(viewNormal.x*viewNormal.y>0?'/':'\\');directional=(tangent||diagonal)?-.026f*edge*cfg[33]:.008f*edge*cfg[33];}
  float distance=fabsf(coverage[c-32]-target)+directional+(cfg[26]>.5f?rnd(seed+cellSeed+c*17)*.002f:rnd(seed+cell*131+c*17)*.006f);
  if(distance<best){best=distance;g=c;}
 }
 int corrupt=(int)cfg[21];float entropy=cfg[22];
 float rv=rnd(seed+cell*983);
 if(corrupt==1&&rv<entropy*.45f)g=' ';
 else if(corrupt==4&&rv<entropy)g=grammar[hash(seed+cell)%gn];
 else if(corrupt==5&&rv<entropy*.5f)g=(cell%2)?'0':'1';
 else if(corrupt==7&&pos.x<0&&rv<entropy)lum*=.35f;
 else if(corrupt==9&&rv<entropy*.25f)g=' ';
 else if(corrupt==0&&rv<entropy*.2f)g='.';
 else if(corrupt==6&&rv<entropy*.35f)g="0123456789ABCDEF"[hash(cell+seed)%16];
 else if(corrupt==8&&rv<entropy*.3f)g='#';
 if(corrupt==2)pos.x+=sinf(pos.y*13)*entropy*.06f;
 if(corrupt==3)pos.y+=sinf(pos.x*17)*entropy*.06f;
 glyph[cell]=g;o[0]=clamp((cfg[26]>.5f?45:65)+(cfg[26]>.5f?210:190)*sqrtf(lum),0,255);o[1]=depth;o[2]=nr.x;o[3]=nr.y;o[4]=nr.z;
 o[5]=pos.x;o[6]=pos.y;o[7]=pos.z;o[8]=object;o[9]=1;o[10]=cfg[36]>4?hits/(float)(ss*ss):entropy;o[11]=lum;
}
__device__ float smooth(float a){a=clamp(a,0,1);return a*a*(3-2*a);}
__device__ float assembled(float t){
 // Distributed origin -> helix -> body -> disintegration -> identity restoration.
 if(t<.15f)return 0;
 if(t<.32f)return smooth((t-.15f)/.17f);
 if(t<.46f)return 1;
 if(t<.65f)return 1-smooth((t-.46f)/.19f);
 if(t<.72f)return 0;
 if(t<.88f)return smooth((t-.72f)/.16f);
 if(t<.94f)return 1;
 return 1-smooth((t-.94f)/.06f);
}
extern "C" __global__ void clear_depth(unsigned long long* z,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)z[i]=~0ULL;}
extern "C" __global__ void project_fragments(const float* cells,const unsigned char* glyph,const float* cfg,unsigned long long* z,float* motion,int frame,int frames,int profile,int assembly,int destruction,int static_mode){
 int i=blockIdx.x*blockDim.x+threadIdx.x;int width=(int)cfg[24],height=(int)cfg[25];if(i>=width*height||cells[i*12+9]<.5f||glyph[i]==' ')return;
 const float* c=cells+i*12;float t=fmodf((frame%frames)/(float)frames+cfg[34],1.f);float a=assembled(t);
 if(cfg[35]>=0)a=cfg[35];else if(static_mode>=100){float amount=(static_mode%100)/100.f;a=static_mode<200?1-clamp(amount,.22f,.8f):1-clamp(.5f+amount*.7f,.5f,.95f);}else if(static_mode)a=static_mode==1?.58f:.16f;
 V target=v(c[5],c[6],c[7]);float r=rnd(i*191+profile*7919),b=rnd(i*73+profile*1709),angle=6.2831853f*r;
 // Stable ID-derived 3D anchors, not frame-random noise.
 V dispersed=v(cosf(angle)*(1.1f+.6f*b),sinf(angle)*(1.5f+.7f*r),(.5f-b)*1.8f);
 float turns=2+(profile%5)*.4f,spin=6.2831853f*t*(1+profile%3),yy=(r-.5f)*2.6f;
 V helix=v(.5f*cosf(yy*turns+spin+(i%2)*3.14159f),yy,.5f*sinf(yy*turns+spin+(i%2)*3.14159f));
 V anchor=dispersed;
 int type=profile%8;
 if(type==0)anchor=rotate(dispersed,0,spin,.2f*sinf(spin));
 if(type==1)anchor=add(helix,mul(dispersed,.22f));
 if(type==2)anchor=v(dispersed.x,sinf(r*20+t*6.2831853f)*.8f,dispersed.z);
 if(type==3)anchor=v(dispersed.x,dispersed.y,dispersed.z+sin(t*6.283f)*.7f);
 if(type==4)anchor=v(cosf(angle+spin)*(1+r),yy,sinf(angle+spin)*(1+r));
 if(type==5)anchor=mul(dispersed,.6f+.5f*cosf(t*6.2831853f));
 if(type==6)anchor=v((i%7-3)*.42f,(i/7%9-4)*.37f,(b-.5f)*1.3f);
 if(type==7)anchor=rotate(dispersed,sinf(t*6.2831853f)*3.14159f,spin,0);
 // All assembly/destruction operators have distinct spatial fields.
 float loose=1-a;int motiontype=(int)cfg[23];
 if(motiontype==1)anchor=mul(anchor,1+.06f*sinf(t*6.2831853f));
 else if(motiontype==2)anchor=rotate(anchor,0,.25f*sinf(t*6.2831853f),0);
 else if(motiontype==3)anchor.x+=.14f*sinf(t*6.2831853f);
 else if(motiontype==4)anchor=rotate(anchor,.18f*sinf(spin),.18f*cosf(spin),0);
 else if(motiontype==5)anchor=mul(anchor,1+.12f*cosf(spin));
 else if(motiontype==6)anchor.z+=.04f*sin(spin*7);
 else if(motiontype==7)anchor=rotate(anchor,0,spin,0);
 else if(motiontype==8)anchor.x+=.05f*sinf(spin*13);
 else if(motiontype==9)anchor=rotate(anchor,0,.4f*sinf(spin),0);

 if(assembly==0)anchor=rotate(anchor,0,spin,0);
 else if(assembly==1)anchor=helix;
 else if(assembly==2)anchor=add(anchor,v(sinf(i*.21+spin)*.28f,cosf(i*.19+spin)*.28f,0));
 else if(assembly==3)anchor.z+=1.5f*loose*(r-.5f);
 else if(assembly==4)anchor=rotate(anchor,(i%5-2)*loose,.2f,0);
 else if(assembly==5)anchor=rotate(anchor,0,spin*2,spin);
 else if(assembly==6)anchor=mul(anchor,1.25f-powf(a,3)*.25f);
 else if(assembly==7)anchor=mul(dispersed,1.3f);
 else if(assembly==8)anchor=v(dispersed.x,yy,sinf(spin+yy)*.3f);
 else if(assembly==9)anchor=mul(helix,.65f+r*.5f);
 if(t>.46f&&t<.72f){
  if(destruction==1)anchor.y-=b*.65f;
  else if(destruction==2)anchor.x+=yy*.7f;
  else if(destruction==3)anchor.y-=r*.8f;
  else if(destruction==4)anchor=v(roundf(anchor.x*3)/3,roundf(anchor.y*3)/3,roundf(anchor.z*3)/3);
  else if(destruction==5)anchor=mul(anchor,.7f+r*.6f);
  else if(destruction==6)anchor.x+=sinf(target.y*5+spin)*.5f;
  else if(destruction==7)anchor=dispersed;
  else if(destruction==8)anchor=rotate(anchor,0,0,spin);
  else if(destruction==9)anchor=mul(anchor,.35f);
 }
 float helicity=smooth(clamp((t-.06f)/.09f,0,1))*(1-smooth(clamp((t-.2f)/.12f,0,1)));
 anchor=add(mul(anchor,1-helicity),mul(helix,helicity));
 V p=add(mul(anchor,loose),mul(target,a));
 V view=inverse(p,cfg[4],cfg[3],0);float dep=4-view.z;
 float scale=cfg[1]>.5f?1:4/fmaxf(dep,.25f);
 int x=(int)floorf((view.x*scale/(cfg[0]*cfg[2])+.5f)*width),y=(int)floorf((.5f-view.y*scale/cfg[0])*height);
 motion[i*3]=p.x;motion[i*3+1]=p.y;motion[i*3+2]=p.z;
 if(x<0||x>=width||y<0||y>=height)return;
 unsigned d=(unsigned)clamp(dep*100000,1,4000000);
 unsigned long long packed=((unsigned long long)d<<32)|(unsigned)i;
 atomicMin(z+y*width+x,packed);
}
extern "C" __global__ void resolve_fragments(const unsigned long long* z,const unsigned char* base,const float* cells,unsigned char* out,float* result,int n){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
 unsigned long long packed=z[i];int id=packed==~0ULL?-1:(int)(packed&0xffffffff);
 out[i]=id<0?' ':base[id];
 for(int j=0;j<12;j++)result[i*12+j]=id<0?0:cells[id*12+j];
 if(id>=0){result[i*12+1]=(packed>>32)/100000.f;result[i*12+8]=id+1;}
}
extern "C" __global__ void raster(const unsigned char* glyph,const float* cells,const unsigned char* atlas,int aw,int ah,unsigned char* pixels,int cw,int ch,int gx,int gy){
 int i=blockIdx.x*blockDim.x+threadIdx.x;int width=gx*cw,height=gy*ch;if(i>=width*height)return;
 int x=i%width,y=i/width,cell=(y/ch)*gx+x/cw,g=(int)glyph[cell]-32;
 float u=(x%cw+.5f)*aw/cw-.5f,vv=(y%ch+.5f)*ah/ch-.5f;int xx=(int)floorf(u),yy=(int)floorf(vv);float fx=u-xx,fy=vv-yy;
 float mask=0;
 if(g>=0&&g<95)for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++){
  int ax=max(0,min(aw-1,xx+dx)),ay=max(0,min(ah-1,yy+dy));
  mask+=atlas[(g*ah+ay)*aw+ax]*(dx?fx:1-fx)*(dy?fy:1-fy)/255.f;
 }
 unsigned char value=(unsigned char)clamp(5+mask*cells[cell*12],0,255);
 pixels[i*3]=value;pixels[i*3+1]=value;pixels[i*3+2]=value;
}
extern "C" __global__ void render_cells(const float* scene,int count,const float* cfg,const float* coverage,const unsigned char* grammar,int gn,unsigned char* glyph,float* cells,int ss){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<(int)(cfg[24]*cfg[25]))render_one(scene,count,cfg,coverage,grammar,gn,glyph,cells,ss,i);
}
extern "C" __global__ void render_batch(const float* scenes,const int* counts,const float* configs,const float* coverage,const unsigned char* grammars,const int* gn,unsigned char* glyph,float* cells,int ss,int batch){
 int i=blockIdx.x*blockDim.x+threadIdx.x;int n=(int)(configs[24]*configs[25]);if(i>=batch*n)return;int edition=i/n,cell=i%n;
 render_one(scenes+edition*160*32,counts[edition],configs+edition*40,coverage,grammars+edition*95,gn[edition],glyph+edition*n,cells+edition*n*12,ss,cell);
}

extern "C" __global__ void probe_field(const float* points,const float* scene,int count,const float* cfg,float* values,int samples){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=samples)return;V p=v(points[i*3],points[i*3+1],points[i*3+2]);int a,b;
 values[i*4]=field(p,scene,count,&a,(int)cfg[5],cfg[27]);values[i*4+1]=field_reference(p,scene,count,&b,(int)cfg[5],cfg[27]);values[i*4+2]=a;values[i*4+3]=b;
}
