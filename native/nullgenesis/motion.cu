// Primitive transforms are performed on CUDA before SDF ray marching. Every
// profile is deterministic and returns exactly to the original scene at frame 0.
__device__ void pose_one(const float* r,float* o,const float* motion,int frame,int total){
 for(int k=0;k<16;k++)o[k]=r[k];
 int index=((frame%total)+total)%total;if(index==0)return;
 float layer=r[14],joint=r[15];if(layer==4)return;
 float t=index/(float)total,q=6.283185307f*motion[2]*t,phase=motion[3];
 float s=sinf(q+phase)-sinf(phase),co=cosf(q+phase)-cosf(phase),freq=motion[4];
 float x=r[1],y=r[2],z=r[3],a=motion[1]*(layer==1?1.25f:layer==2||layer==3?.75f:1),j=joint*.71f;
 float local=sinf(q+phase+y*freq+j)-sinf(phase+y*freq+j);int kind=(int)motion[0];
 if(kind==0){float w=layer>=2?1:clamp((y+.7f)/1.6f,0,1);o[1]+=s*a*.065f*w;o[2]+=co*a*.06f*w;o[8]+=s*a*.12f*w;}
 if(kind==1){o[1]+=local*a*.14f;o[3]+=co*a*.07f*sinf(y*freq);o[9]+=local*a*.08f;}
 if(kind==2){float w=layer==1||joint>0?1:.18f;V p=rotate(v(x,y,z),0,q,0);o[1]=x+a*w*(p.x-x);o[3]=z+a*w*(p.z-z);o[2]+=s*a*.1f*w;o[8]+=s*a*.22f*w;}
 if(kind==3){float angle=local*a*.22f,pivot=clamp(y,-.25f,.25f);V p=rotate(v(x,y-pivot,z),0,0,angle);o[1]=p.x;o[2]=p.y+pivot;o[9]+=angle;}
 if(kind==4){o[1]+=local*a*.08f;o[2]+=s*a*.06f*clamp(fabsf(x),.2f,1);o[7]+=local*a*.09f;}
 if(kind==5){float w=layer==2||layer==3?1:.35f;o[3]+=local*a*.1f*w;o[8]+=s*a*.13f*w;o[9]+=co*a*.09f*w;}
 if(kind==6){V p=rotate(v(x,y,z),s*a*.13f,co*a*.14f,s*a*.05f);o[1]=p.x;o[2]=p.y+co*a*.045f;o[3]=p.z;o[7]+=s*a*.13f;o[8]+=co*a*.14f;o[9]+=s*a*.05f;}
 if(kind==7){float angle=s*a*.24f*(.8f+y*.3f);V p=rotate(v(x,y,z),0,angle,0);o[1]=p.x;o[3]=p.z;o[8]+=angle;}
 if(kind==8){o[1]+=local*a*.065f;o[3]+=co*a*.075f;o[12]+=s*a*.015f;if(r[0]==11)o[12]=r[12]+s*a*.8f;}
 if(kind==9){float breath=1+s*a*.05f;for(int k=4;k<7;k++)o[k]*=breath;o[1]*=1+s*a*.025f;o[2]+=co*a*.03f;o[3]*=1+s*a*.04f;}
}
__device__ void prepare_cache(float* out){
 out[16]=cosf(out[7]);out[17]=sinf(out[7]);out[18]=cosf(out[8]);out[19]=sinf(out[8]);out[20]=cosf(out[9]);out[21]=sinf(out[9]);
 float sx=out[4],sy=out[5],sz=out[6],maximum=fmaxf(sx,fmaxf(sy,sz)),minimum=fminf(sx,fminf(sy,sz));int kind=(int)out[0];
 float radius=sqrtf(sx*sx+sy*sy+sz*sz),factor=1;
 if(kind==0)radius=sx;
 if(kind==1||kind==11){radius=maximum;factor=minimum/maximum;if(kind==11)radius+=.018f/factor;}
 if(kind==2)radius=sx+sy;
 if(kind==3)radius=sqrtf(sx*sx+sy*sy);
 if(kind==4){radius=sqrtf(sx*sx+sy*sy);factor=.49f;}
 if(kind==5)radius=sx+sy;
 if(kind==7)radius+=fmaxf(out[12],0);
 if(kind==9){radius+=fabsf(out[12]);factor=1/(1+4*fabsf(out[12]));}
 if(kind==10){radius=fmaxf(sx,sy)+sz;factor=.5f*fminf(sx,sy)/fmaxf(sx,sy);}
 out[22]=radius;out[23]=factor;
}
extern "C" __global__ void animate_scene(const float* base,float* scene,int count,const float* motion,int frame,int total){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<count){float* out=scene+i*32;pose_one(base+i*16,out,motion,frame,total);prepare_cache(out);}
}
extern "C" __global__ void animate_scene_batch(const float* base,float* scenes,int count,const float* motion,const int* indices,int total,int batch){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count*batch)return;
 int item=i/count,primitive=i%count;float* out=scenes+(item*160+primitive)*32;pose_one(base+primitive*16,out,motion,indices[item],total);prepare_cache(out);
}
extern "C" __global__ void prepare_scene_batch(const float* base,float* scenes,const int* counts,int batch){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=batch*160)return;int item=i/160,primitive=i%160;if(primitive>=counts[item])return;
 const float* r=base+i*16;float* out=scenes+i*32;for(int k=0;k<16;k++)out[k]=r[k];prepare_cache(out);
}
extern "C" __global__ void copy_render(const unsigned char* glyph,const float* cells,unsigned char* out,float* result,int count){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count)return;out[i]=glyph[i];for(int j=0;j<12;j++)result[i*12+j]=cells[i*12+j];
}
