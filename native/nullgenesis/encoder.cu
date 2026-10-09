// V4.5 post-field encoder: immutable input cells, row-local error diffusion,
// depth/normal contours, calibrated glyph coverage and semantic density budgets.
extern "C" __global__ void encode_rows(const unsigned char* source,const float* cells,const float* scene,const float* cfg,const float* coverage,const unsigned char* grammar,int gn,unsigned char* glyph,float* output,float temporalLock,float depthWeight,float noiseBudget,int batch){
 int row=blockIdx.x*blockDim.x+threadIdx.x,w=(int)cfg[24],h=(int)cfg[25];if(row>=h*batch)return;
 int edition=row/h,y=row%h,offset=edition*w*h;float error=0;
 int method=(int)cfg[37];float edgeWeight=cfg[39];
 for(int x=0;x<w;x++){
  int i=offset+y*w+x;const float* a=cells+i*12;float* o=output+i*12;
  for(int j=0;j<12;j++)o[j]=a[j];glyph[i]=source[i];
  if(source[i]==' '||a[9]<.5f){error=0;continue;}
  int neighbors=0,isolated=0;float depthEdge=0,normalEdge=0,gradientX=0,gradientY=0;
  for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
   if(!dx&&!dy)continue;int nx=x+dx,ny=y+dy;if(nx<0||nx>=w||ny<0||ny>=h)continue;
   const float* b=cells+(offset+ny*w+nx)*12;
   if(b[9]>.5f){neighbors++;depthEdge=fmaxf(depthEdge,fabsf(a[1]-b[1]));normalEdge=fmaxf(normalEdge,1-(a[2]*b[2]+a[3]*b[3]+a[4]*b[4]));gradientX+=dx*(a[11]-b[11]);gradientY+=dy*(a[11]-b[11]);}
   else isolated++;
  }
  int object=max(1,(int)a[8]),layer=(int)scene[(object-1)*16+14];
  // Prune unconnected peripheral micro-details; main silhouette survives.
  if(neighbors<=1&&layer>=2){glyph[i]=' ';for(int j=0;j<12;j++)o[j]=0;error=0;continue;}
  float contour=clamp(depthEdge*depthWeight*12.5f+normalEdge*.65f+isolated*.065f,0,1);
  float importance=layer==0?1:layer==1?.94f:layer==4?.45f:.78f;
  float tone=clamp(a[11]*(.94f+.06f*importance)+contour*.075f*edgeWeight, .04f,1);
  // Stable normal clusters and depth bands remove incidental flicker.
  float cluster=4+roundf(temporalLock*5);float normalX=roundf(a[2]*cluster)/cluster,normalY=roundf(a[3]*cluster)/cluster;
  unsigned anchor=hash((unsigned)((floorf(a[5]*19)+256)*977+(floorf(a[6]*19)+256)*311+object*701));
  float perturb=(rnd(anchor+method*37)-.5f)*(.006f+(method%4)*.002f+noiseBudget*.05f);
  float target=clamp(.05f+tone*(.38f+(method%5)*.006f)+error*.42f+perturb,.04f,.43f),best=100;unsigned char chosen='.';
  for(int k=0;k<gn;k++){
   unsigned char ch=grammar[k];float cost=fabsf(coverage[ch-32]-target);
   bool horizontal=fabsf(normalY)+fabsf(gradientY)>fabsf(normalX)+fabsf(gradientX);
   bool tangent=horizontal?(ch=='-'||ch=='_'||ch=='='):(ch=='|'||ch==':'||ch=='!');
   bool diagonal=ch==(normalX*normalY>0?'/':'\\');
   cost-=contour*edgeWeight*(tangent||diagonal?.022f:0);
   if(layer==4&&ch!='.'&&ch!=':'&&ch!='-')cost+=.014f;
   // Interior material ramp is deterministic in object/world coordinates.
   cost+=rnd(anchor+ch*11)*.0006f;
   if(cost<best){best=cost;chosen=ch;}
  }
  glyph[i]=chosen;error=clamp(target-coverage[chosen-32],-.04f,.04f);
  o[0]=clamp(42+205*sqrtf(tone),0,255);if(layer==4)o[0]*=.7f;o[11]=tone;
 }
}
extern "C" __global__ void raster_square(const unsigned char* glyph,const float* cells,const unsigned char* atlas,int aw,int ah,unsigned char* pixels,int size,int gx,int gy){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=size*size)return;int x=i%size,y=i/size;
 float cellW=size/(float)gx,cellH=size/(float)gy;int cx=min(gx-1,(int)(x/cellW)),cy=min(gy-1,(int)(y/cellH)),cell=cy*gx+cx,g=glyph[cell]-32;
 // Square bitmap cells preserve the logical pixel-art grid and readable glyph
 // coverage at 300 px; the measured font atlas supplies the actual ASCII shape.
 float gw=cellW,gh=cellH;
 float u=(x+.5f-cx*cellW-(cellW-gw)*.5f)*aw/gw-.5f, vv=(y+.5f-cy*cellH-(cellH-gh)*.5f)*ah/gh-.5f,mask=0;
 if(g>=0&&g<95&&u>=-.5f&&u<aw-.5f&&vv>=-.5f&&vv<ah-.5f){
  int xx=(int)floorf(u),yy=(int)floorf(vv);float fx=u-xx,fy=vv-yy;
  for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++){int ax=max(0,min(aw-1,xx+dx)),ay=max(0,min(ah-1,yy+dy));mask+=atlas[(g*ah+ay)*aw+ax]*(dx?fx:1-fx)*(dy?fy:1-fy)/255.f;}
 }
 unsigned char value=(unsigned char)clamp(5+mask*cells[cell*12],0,255);pixels[i*3]=value;pixels[i*3+1]=value;pixels[i*3+2]=value;
}
