"""Reproduce the V3 kernel extension from the preserved legacy source."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = (root / 'legacy/engine/render.cu').read_text(encoding='utf-8')
source = source.replace('int x=cell%30,y=cell/30;', 'int width=(int)cfg[24],height=(int)cfg[25];int x=cell%width,y=cell/width;')
source = source.replace('/30.f-.5f)', '/width-.5f)').replace('/30.f)*cfg[0]', '/height)*cfg[0]')
source = source.replace('int* id,int topology)', 'int* id,int topology,float blending)')
source = source.replace('else if(d<a){a=d;ai=i+1;}', '''else {
   float blend=fminf(blending,fminf(r[4],fminf(r[5],r[6]))*.35f);
   if(blend>0 && a<99 && r[14]!=4){float h=clamp(.5f+.5f*(a-d)/blend,0,1);float merged=a*(1-h)+d*h-blend*h*(1-h);if(d<a)ai=i+1;a=merged;}
   else if(d<a){a=d;ai=i+1;}
  }''')
source = source.replace('int n,int top)', 'int n,int top,float blending)')
source = source.replace(',&id,top)', ',&id,top,blending)')
source = source.replace('scene,count,&id,top,blending)', 'scene,count,&id,top,cfg[27])')
source = source.replace('n=normal(p,scene,count,top)', 'n=normal(p,scene,count,top,cfg[27])')
source = source.replace('scene,count,&dummy,top)', 'scene,count,&dummy,top,cfg[27])')
source = source.replace('float value=(.15f+diff*.64f*shadow+rim*cfg[13]+spec)*ao;', '''float value=(.15f+diff*.64f*shadow+rim*cfg[13]+spec)*ao;
  if(cfg[26]>.5f){
   float accumulated=0,weight=1;
   for(int sample=0;sample<3;sample++){float distance=sample==0?.045f:sample==1?.11f:.23f;float d=field(add(p,mul(n,distance)),scene,count,&dummy,top,cfg[27]);accumulated+=(distance-d)*weight;weight*=.55f;}
   ao=clamp(1-accumulated*3.5f*cfg[30],.22f,1);
   float st=.018f;shadow=1;for(int j=0;j<10;j++){float d=field(add(p,mul(light,st)),scene,count,&dummy,top,cfg[27]);shadow=fminf(shadow,clamp(d*10/st,.2f,1));st+=clamp(d,.025f,.16f);if(st>.85f)break;}
   V fill=norm(v(-.7f,-.15f,.6f));float fillAmount=fmaxf(dot(n,fill),0)*cfg[29];
   const float metals[10]={.04f,.95f,.65f,.23f,.8f,.9f,.7f,.12f,0,.3f};float metal=metals[max(0,min(9,(int)cfg[14]))];
   spec=powf(fmaxf(dot(n,halfway),0),fmaxf(2,cfg[11]))*(cfg[12]+metal*.13f);
   value=(cfg[28]+diff*.68f*shadow+fillAmount+rim*cfg[31]+spec*shadow)*ao;
  }''')
source=source.replace('for(int step=0;step<108;step++)','for(int step=0;step<(cfg[26]>.5f?160:108);step++)')
source=source.replace('if(d<.0075f)', 'if(d<(cfg[26]>.5f?.0035f*30/width:.0075f))')
source=source.replace('t+=fmaxf(d*.72f,.004f)', 't+=fmaxf(d*(cfg[26]>.5f?.68f:.72f),cfg[26]>.5f?.0015f:.004f)')
source=source.replace('lum+=clamp(value*cfg[16],.025f,1);','lum+=cfg[26]>.5f?powf(clamp(value*cfg[16],.025f,1),1/cfg[32]):clamp(value*cfg[16],.025f,1);')
source=source.replace('density==0&&lum<.27f','density==0&&lum<(cfg[26]>.5f?.22f:.27f)')
source=source.replace('float target=clamp(.04f+lum*.32f,.025f,.4f),best=100;', 'float target=cfg[26]>.5f?clamp(.025f+lum*.36f,.02f,.42f):clamp(.04f+lum*.32f,.025f,.4f),best=100;')
source=source.replace('unsigned seed=(unsigned)cfg[20];','''unsigned seed=(unsigned)cfg[20];V viewNormal=inverse(nr,cfg[4],cfg[3],0);float edge=1-fabsf(viewNormal.z);
 unsigned cellSeed=hash((unsigned)((floorf(pos.x*71)+512)*997+(floorf(pos.y*71)+512)*313+object*911));''')
source=source.replace('float distance=fabsf(coverage[c-32]-target)+rnd(seed+cell*131+c*17)*.006f;', '''float directional=0;if(cfg[26]>.5f && edge>.45f){bool horizontal=fabsf(viewNormal.y)>fabsf(viewNormal.x);bool tangent=horizontal?(c=='_'||c=='-'||c=='='):(c=='|'||c=='!'||c==':');bool diagonal=c==(viewNormal.x*viewNormal.y>0?'/':'\\\\');directional=(tangent||diagonal)?-.026f*edge*cfg[33]:.008f*edge*cfg[33];}
  float distance=fabsf(coverage[c-32]-target)+directional+(cfg[26]>.5f?rnd(seed+cellSeed+c*17)*.002f:rnd(seed+cell*131+c*17)*.006f);''')
source=source.replace('clamp(65+190*sqrtf(lum),0,255)', 'clamp((cfg[26]>.5f?45:65)+(cfg[26]>.5f?210:190)*sqrtf(lum),0,255)')
source=source.replace('V q=inverse(sub(p,v(r[1],r[2],r[3])),r[7],r[8],r[9]);', '''V q=sub(p,v(r[1],r[2],r[3]));float co=r[20],si=r[21];q=v(co*q.x+si*q.y,-si*q.x+co*q.y,q.z);
 co=r[18];si=r[19];q=v(co*q.x-si*q.z,q.y,si*q.x+co*q.z);
 co=r[16];si=r[17];q=v(q.x,co*q.y+si*q.z,-si*q.y+co*q.z);''')
source=source.replace('scene+i*16','scene+i*32').replace('scenes+edition*160*16','scenes+edition*160*32')
source=source.replace('const float* r=scene+i*32;float d=primitive(p,r);','''const float* r=scene+i*32;
  // Conservative lower bound of the implemented primitive field. Blending
  // influences only distances within its finite support; a positive bound
  // farther than the current minimum plus that support cannot change the result.
  float bound=(len(sub(p,v(r[1],r[2],r[3])))-r[22])*r[23];
  if(bound>0 && bound>(r[10]>.5f?b:a+blending)+.0001f)continue;
  float d=primitive(p,r);''')
source = source.replace('unsigned long long* z){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<900)', 'unsigned long long* z,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)')
source = source.replace('if(i>=900||cells[i*12+9]', 'int width=(int)cfg[24],height=(int)cfg[25];if(i>=width*height||cells[i*12+9]')
source = source.replace('+.5f)*30)', '+.5f)*width)').replace('/cfg[0])*30)', '/cfg[0])*height)')
source = source.replace('x>=30||y<0||y>=30', 'x>=width||y<0||y>=height').replace('z+y*30+x', 'z+y*width+x')
source = source.replace('unsigned char* out,float* result)', 'unsigned char* out,float* result,int n)')
source = source.replace('if(i>=900)return;', 'if(i>=n)return;')
source = source.replace('int cw,int ch)', 'int cw,int ch,int gx,int gy)')
source = source.replace('int width=30*cw,height=30*ch', 'int width=gx*cw,height=gy*ch').replace('cell=(y/ch)*30+x/cw', 'cell=(y/ch)*gx+x/cw')
source = source.replace('float t=(frame%frames)/(float)frames;float a=assembled(t);','float t=fmodf((frame%frames)/(float)frames+cfg[34],1.f);float a=assembled(t);')
source = source.replace('if(static_mode>=100)', 'if(cfg[35]>=0)a=cfg[35];else if(static_mode>=100)')
source = source.replace('float e=.003f;', 'float e=blending>0?.0025f:.003f;')
source = source.replace('if(lighting==4)value=.2f+rim*.8f;if(lighting==7&&p.x<0)value*=.28f;if(lighting==8)value=powf(value,1.6f);','if(lighting==4)value=cfg[26]>.5f?.16f+rim*.84f:.2f+rim*.8f;if(lighting==7&&p.x<0)value*=cfg[26]>.5f?.32f:.28f;if(lighting==8)value=powf(value,cfg[26]>.5f?1.45f:1.6f);')
source = source.replace('if(i<900)render_one', 'if(i<(int)(cfg[24]*cfg[25]))render_one')
source = source.replace('if(i>=batch*900)return;int edition=i/900,cell=i%900;', 'int n=(int)(configs[24]*configs[25]);if(i>=batch*n)return;int edition=i/n,cell=i%n;')
source = source.replace('configs+edition*24', 'configs+edition*40').replace('glyph+edition*900', 'glyph+edition*n').replace('cells+edition*900*12', 'cells+edition*n*12')
start=source.index('__device__ float field(');end=source.index('__device__ V normal(',start)
reference=source[start:end].replace('__device__ float field(', '__device__ float field_reference(')
reference=reference.replace('if(bound>0 && bound>(r[10]>.5f?b:a+blending)+.0001f)continue;','')
source=source[:end]+reference+source[end:]
source+='''
extern "C" __global__ void probe_field(const float* points,const float* scene,int count,const float* cfg,float* values,int samples){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=samples)return;V p=v(points[i*3],points[i*3+1],points[i*3+2]);int a,b;
 values[i*4]=field(p,scene,count,&a,(int)cfg[5],cfg[27]);values[i*4+1]=field_reference(p,scene,count,&b,(int)cfg[5],cfg[27]);values[i*4+2]=a;values[i*4+3]=b;
}
'''

(root / 'nullgenesis/render.cu').write_text(source, encoding='utf-8')
