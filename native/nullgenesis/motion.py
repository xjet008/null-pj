"""The browser V3 primitive-motion contract, without frame-random noise."""
import math
import numpy as np
from .cpu import rotation

def animate_scene(scene,motion,index,total):
    result=scene.copy();index=int(index)%int(total)
    if index==0:return result
    kind=int(motion.get('kind',motion.get('type',0)));amp=float(motion.get('amplitude',motion.get('intensity',.15)))
    q=math.tau*int(motion.get('speed',1))*index/total;phase=float(motion.get('phase',0));freq=float(motion.get('frequency',2))
    s=math.sin(q+phase)-math.sin(phase);co=math.cos(q+phase)-math.cos(phase)
    for i,r in enumerate(scene):
        o=result[i];layer=r[14];joint=r[15]
        if layer==4:continue
        x,y,z=r[1:4];a=amp*(1.25 if layer==1 else .75 if layer in (2,3) else 1);j=joint*.71
        local=math.sin(q+phase+y*freq+j)-math.sin(phase+y*freq+j)
        if kind==0:
            w=1 if layer>=2 else np.clip((y+.7)/1.6,0,1);o[1]+=s*a*.065*w;o[2]+=co*a*.06*w;o[8]+=s*a*.12*w
        if kind==1:o[1]+=local*a*.14;o[3]+=co*a*.07*math.sin(y*freq);o[9]+=local*a*.08
        if kind==2:
            w=1 if layer==1 or joint>0 else .18;p=rotation(0,q,0)@np.array([x,y,z]);o[1]=x+a*w*(p[0]-x);o[3]=z+a*w*(p[2]-z);o[2]+=s*a*.1*w;o[8]+=s*a*.22*w
        if kind==3:
            angle=local*a*.22;pivot=np.clip(y,-.25,.25);p=rotation(0,0,angle)@np.array([x,y-pivot,z]);o[1]=p[0];o[2]=p[1]+pivot;o[9]+=angle
        if kind==4:o[1]+=local*a*.08;o[2]+=s*a*.06*np.clip(abs(x),.2,1);o[7]+=local*a*.09
        if kind==5:
            w=1 if layer in (2,3) else .35;o[3]+=local*a*.1*w;o[8]+=s*a*.13*w;o[9]+=co*a*.09*w
        if kind==6:
            p=rotation(s*a*.13,co*a*.14,s*a*.05)@np.array([x,y,z]);o[1]=p[0];o[2]=p[1]+co*a*.045;o[3]=p[2];o[7]+=s*a*.13;o[8]+=co*a*.14;o[9]+=s*a*.05
        if kind==7:
            angle=s*a*.24*(.8+y*.3);p=rotation(0,angle,0)@np.array([x,y,z]);o[1]=p[0];o[3]=p[2];o[8]+=angle
        if kind==8:
            o[1]+=local*a*.065;o[3]+=co*a*.075;o[12]+=s*a*.015
            if r[0]==11:o[12]=r[12]+s*a*.8
        if kind==9:
            o[4:7]*=1+s*a*.05;o[1]*=1+s*a*.025;o[2]+=co*a*.03;o[3]*=1+s*a*.04
    return result
