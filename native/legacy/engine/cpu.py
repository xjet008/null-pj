"""Portable NumPy SDF reference. Deterministic per backend; GPU boundary rounding may differ."""
import numpy as np, math
def rotation(x,y,z):
    cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def length(v):return np.linalg.norm(v,axis=-1)
def norm(v):return v/np.maximum(length(v)[...,None],1e-8)
def box(q,s):
    a=np.abs(q)-s
    return length(np.maximum(a,0))+np.minimum(a.max(axis=-1),0)
def primitive(p,r):
    q=(p-r[1:4])@rotation(*r[7:10]);s=r[4:7];k=int(r[0])
    if k==0:return length(q)-s[0]
    if k in [1,11]:
        d=(length(q/s)-1)*s.min()
        if k==11:d+=.018*np.sin(q[:,0]*13+r[12])*np.sin(q[:,1]*11)*np.sin(q[:,2]*9)
        return d
    if k==2:return length(np.stack([q[:,0],np.maximum(np.abs(q[:,1])-s[1],0),q[:,2]],axis=-1))-s[0]
    if k==3:
        a=length(q[:,[0,2]])-s[0];b=np.abs(q[:,1])-s[1]
        return np.minimum(np.maximum(a,b),0)+np.hypot(np.maximum(a,0),np.maximum(b,0))
    if k==4:return np.maximum((length(q[:,[0,2]])-s[0]*np.clip((s[1]-q[:,1])/(2*s[1]),0,1))*.7,np.abs(q[:,1])-s[1])
    if k==5:return np.hypot(length(q[:,[0,2]])-s[0],q[:,1])-s[1]
    if k==7:return box(q,s)-r[12]
    if k==9:q[:,0]-=r[12]*np.sin(q[:,1]*4);return box(q,s)
    if k==10:
        a=np.arctan2(q[:,1]/s[1],q[:,0]/s[0]);sector=math.tau/r[12];boundary=np.cos(math.pi/r[12])/np.cos(a-sector*np.floor((a+sector*.5)/sector))
        return np.maximum((length(q[:,:2]/s[:2])-boundary)*min(s[:2]),np.abs(q[:,2])-s[2])
    return box(q,s)
def field(p,scene,top):
    pos=np.full(len(p),100.);neg=pos.copy();pi=np.zeros(len(p),int);ni=pi.copy()
    for i,r in enumerate(scene):
        d=primitive(p,r);values,ids=(neg,ni) if r[10]>.5 else (pos,pi);hit=d<values;values[hit]=d[hit];ids[hit]=i+1
    values=np.maximum(pos,-neg);ids=np.where(pos>-neg,pi,ni)
    if top==4:values=np.maximum(np.abs(values)-.018,np.abs(np.sin(p*19)).min(axis=1)*.04-.009)
    return values,ids
def normals(p,scene,top):
    e=np.eye(3)*.003;return norm(np.stack([field(p+a,scene,top)[0]-field(p-a,scene,top)[0] for a in e],axis=1))
def hash32(x):
    x=np.asarray(x,dtype=np.uint32);x=x^(x>>16);x=x*np.uint32(0x7feb352d);x=x^(x>>15);x=x*np.uint32(0x846ca68b);return x^(x>>16)
def rnd(x):return (hash32(x)&np.uint32(0xffffff)).astype(float)/16777216
def texture(p,k,f):
    x,y,z=(p*f).T
    if k==0:return .68+.32*np.abs(np.sin((x+y)*6)*np.sin((x-y)*6))
    if k==1:return .6+.4*np.abs(np.sin(x*9)*np.sin(y*9)*np.sin(z*7))**.25
    if k==2:return .72+.28*np.sin(x*6)*np.sin(y*6)
    if k==3:return .83+.17*np.sin(x*21+y*17+z*25)
    if k==4:return .72+.28*np.abs(np.sin(y*15))
    if k==5:return .62+.38*np.abs(np.sin(x*10)*np.cos(z*10))
    if k==6:return .55+.45*np.clip(np.abs(np.sin(x*5+np.sin(y*7)))*4,0,1)
    if k==7:return .63+.37*np.abs(np.sin(x*14)*np.sin(y*14))
    if k==8:return np.ones(len(p))
    return .57+.43*np.abs(np.sin(x*19+y*3)*np.sin(z*23+y*17))
def render_cpu(scene,cfg,grammar,coverage,ss):
    lum=np.zeros(900);depth=np.zeros(900);positions=np.zeros((900,3));normal=np.zeros((900,3));hits=np.zeros(900);objects=np.zeros(900)
    x=np.arange(900)%30;y=np.arange(900)//30;top=int(cfg[5]);R=rotation(cfg[4],cfg[3],0)
    for sy in range(ss):
      for sx in range(ss):
        px=((x+(sx+.5)/ss)/30-.5)*cfg[0]*cfg[2];py=(.5-(y+(sy+.5)/ss)/30)*cfg[0]
        origin=np.tile([0.,0.,4.],(900,1));direction=norm(np.stack([px,py,np.full(900,-4)],axis=1))
        if cfg[1]>.5:origin=np.stack([px,py,np.full(900,4)],axis=1);direction=np.tile([0.,0.,-1.],(900,1))
        origin=origin@R.T;direction=direction@R.T;t=np.zeros(900);active=np.ones(900,bool);done=np.zeros(900,bool);ids=np.zeros(900,int)
        for step in range(108):
            ix=np.flatnonzero(active)
            if not len(ix):break
            d,oid=field(origin[ix]+direction[ix]*t[ix,None],scene,top);hit=d<.0075;done[ix[hit]]=True;ids[ix[hit]]=oid[hit];active[ix[hit]]=False
            move=ix[~hit];t[move]+=np.maximum(d[~hit]*.72,.004);active[t>8]=False
        ix=np.flatnonzero(done)
        if not len(ix):continue
        p=origin[ix]+direction[ix]*t[ix,None];n=normals(p,scene,top);light=norm(cfg[7:10]);diff=np.maximum(n@light,0);rim=(1-np.maximum(-(n*direction[ix]).sum(axis=1),0))**2.7
        spec=np.maximum((n*norm(light-direction[ix])).sum(axis=1),0)**cfg[11]*cfg[12];ao=np.clip(field(p+n*.09,scene,top)[0]/.09,.18,1);shadow=np.ones(len(p))
        if cfg[6]>=2:
            st=np.full(len(p),.035)
            for j in range(8):
                d,_=field(p+light*st[:,None],scene,top);shadow=np.minimum(shadow,np.clip(d*12/st,.15,1));st+=np.clip(d,.04,.2)
        value=(.15+diff*.64*shadow+rim*cfg[13]+spec)*ao;k=int(cfg[18])
        if k==4:value=.2+rim*.8
        if k==7:value[p[:,0]<0]*=.28
        if k==8:value=value**1.6
        value*=texture(p,int(cfg[14]),cfg[15])*cfg[10];lum[ix]+=np.clip(value*cfg[16],.025,1);depth[ix]+=t[ix];positions[ix]+=p;normal[ix]+=n;hits[ix]+=1;objects[ix]=ids[ix]
    ix=np.flatnonzero(hits);lum/=ss*ss;positions[ix]/=hits[ix,None];depth[ix]/=hits[ix];normal[ix]=norm(normal[ix])
    density=int(cfg[19])
    if density==0:ix=ix[lum[ix]>=.27]
    if density==5:ix=ix[~((np.abs(positions[ix,0])<.15)&(np.abs(positions[ix,1])<.25))]
    if density in [6,7]:lum*=np.clip(.7+positions[:,0]*(.25 if density==7 else -.25),.3,1)
    if density==8:lum*=.65+.35*np.abs(np.sin(length(positions)*12))
    if density==9:lum*=.65+.35*np.abs(np.sin(positions[:,0]*9)*np.sin(positions[:,1]*7))
    if int(cfg[17])==8:lum*=.42
    if int(cfg[17])==7:lum*=.75
    glyph=np.full(900,32,np.uint8);cells=np.zeros((900,12),np.float32);seed=int(cfg[20])
    for i in ix:
        target=np.clip(.04+lum[i]*.32,.025,.4);distances=np.abs(coverage[grammar-32]-target)+rnd(seed+i*131+grammar.astype(np.int64)*17)*.006;glyph[i]=grammar[np.argmin(distances)]
    rv=rnd(seed+np.arange(900)*983);corrupt=int(cfg[21]);entropy=cfg[22];on=np.zeros(900,bool);on[ix]=True
    if corrupt in [1,9]:glyph[on&(rv<entropy*(.45 if corrupt==1 else .25))]=32
    if corrupt==4:
        j=np.flatnonzero(on&(rv<entropy));glyph[j]=grammar[hash32(seed+j)%len(grammar)]
    if corrupt==5:
        j=np.flatnonzero(on&(rv<entropy*.5));glyph[j]=np.where(j%2,48,49)
    if corrupt==7:lum[on&(positions[:,0]<0)&(rv<entropy)]*=.35
    if corrupt==0:glyph[on&(rv<entropy*.2)]=46
    if corrupt==6:
        j=np.flatnonzero(on&(rv<entropy*.35));glyph[j]=np.frombuffer(b'0123456789ABCDEF',np.uint8)[hash32(j+seed)%16]
    if corrupt==8:glyph[on&(rv<entropy*.3)]=35
    if corrupt==2:positions[:,0]+=np.sin(positions[:,1]*13)*entropy*.06
    if corrupt==3:positions[:,1]+=np.sin(positions[:,0]*17)*entropy*.06
    cells[ix,0]=np.clip(65+190*np.sqrt(lum[ix]),0,255);cells[ix,1]=depth[ix];cells[ix,2:5]=normal[ix];cells[ix,5:8]=positions[ix];cells[ix,8]=objects[ix];cells[ix,9]=1;cells[ix,10]=entropy;cells[ix,11]=lum[ix]
    return glyph,cells
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def assembled(t):
    if t<.15:return 0
    if t<.32:return smooth((t-.15)/.17)
    if t<.46:return 1
    if t<.65:return 1-smooth((t-.46)/.19)
    if t<.72:return 0
    if t<.88:return smooth((t-.72)/.16)
    if t<.94:return 1
    return 1-smooth((t-.94)/.06)
def frame_cpu(base,g,frame,static_mode):
    c=base['cells'];cfg=base['cfg'];i=np.arange(900);profile=g['animation']['profile'];total=g['animation']['fps']*g['animation']['seconds'];t=frame%total/total;a=assembled(t)
    if static_mode>=100:a=1-(np.clip(static_mode%100/100,.22,.8) if static_mode<200 else np.clip(.5+static_mode%100/100*.7,.5,.95))
    elif static_mode:a=.58 if static_mode==1 else .16
    r=rnd(i*191+profile*7919);b=rnd(i*73+profile*1709);angle=math.tau*r;spin=math.tau*t*(1+profile%3);yy=(r-.5)*2.6
    disp=np.stack([np.cos(angle)*(1.1+.6*b),np.sin(angle)*(1.5+.7*r),(.5-b)*1.8],axis=1);helix=np.stack([.5*np.cos(yy*(2+profile%5*.4)+spin+i%2*math.pi),yy,.5*np.sin(yy*(2+profile%5*.4)+spin+i%2*math.pi)],axis=1)
    anchor=disp.copy();k=profile%8
    if k==0:anchor=anchor@rotation(0,spin,.2*math.sin(spin)).T
    if k==1:anchor=helix+disp*.22
    if k==2:anchor[:,1]=np.sin(r*20+t*math.tau)*.8
    if k==3:anchor[:,2]+=math.sin(t*math.tau)*.7
    if k==4:anchor=np.stack([np.cos(angle+spin)*(1+r),yy,np.sin(angle+spin)*(1+r)],axis=1)
    if k==5:anchor*=.6+.5*math.cos(t*math.tau)
    if k==6:anchor=np.stack([(i%7-3)*.42,(i//7%9-4)*.37,(b-.5)*1.3],axis=1)
    if k==7:anchor=anchor@rotation(math.sin(t*math.tau)*math.pi,spin,0).T
    asm=g['animation']['assembly_variant'];des=g['animation']['destruction_variant'];loose=1-a
    motion=int(cfg[23])
    if motion==1:anchor*=1+.06*math.sin(t*math.tau)
    if motion==2:anchor=anchor@rotation(0,.25*math.sin(t*math.tau),0).T
    if motion==3:anchor[:,0]+=.14*math.sin(t*math.tau)
    if motion==4:anchor=anchor@rotation(.18*math.sin(spin),.18*math.cos(spin),0).T
    if motion==5:anchor*=1+.12*math.cos(spin)
    if motion==6:anchor[:,2]+=.04*math.sin(spin*7)
    if motion==7:anchor=anchor@rotation(0,spin,0).T
    if motion==8:anchor[:,0]+=.05*math.sin(spin*13)
    if motion==9:anchor=anchor@rotation(0,.4*math.sin(spin),0).T
    if asm==0:anchor=anchor@rotation(0,spin,0).T
    if asm==1:anchor=helix.copy()
    if asm==2:anchor+=np.stack([np.sin(i*.21+spin)*.28,np.cos(i*.19+spin)*.28,np.zeros(900)],axis=1)
    if asm==3:anchor[:,2]+=1.5*loose*(r-.5)
    if asm==4:
        for j in range(5):anchor[i%5==j]=anchor[i%5==j]@rotation((j-2)*loose,.2,0).T
    if asm==5:anchor=anchor@rotation(0,spin*2,spin).T
    if asm==6:anchor*=1.25-a**3*.25
    if asm==7:anchor=disp*1.3
    if asm==8:anchor=np.stack([disp[:,0],yy,np.sin(spin+yy)*.3],axis=1)
    if asm==9:anchor=helix*(.65+r*.5)[:,None]
    if .46<t<.72:
        if des==1:anchor[:,1]-=b*.65
        if des==2:anchor[:,0]+=yy*.7
        if des==3:anchor[:,1]-=r*.8
        if des==4:anchor=np.round(anchor*3)/3
        if des==5:anchor*=(.7+r*.6)[:,None]
        if des==6:anchor[:,0]+=np.sin(c[:,6]*5+spin)*.5
        if des==7:anchor=disp.copy()
        if des==8:anchor=anchor@rotation(0,0,spin).T
        if des==9:anchor*=.35
    h=smooth((t-.06)/.09)*(1-smooth((t-.2)/.12));anchor=anchor*(1-h)+helix*h
    p=anchor*loose+c[:,5:8]*a;view=p@rotation(cfg[4],cfg[3],0);dep=4-view[:,2];scale=np.ones(900) if cfg[1]>.5 else 4/np.maximum(dep,.25)
    x=np.floor((view[:,0]*scale/(cfg[0]*cfg[2])+.5)*30).astype(int);y=np.floor((.5-view[:,1]*scale/cfg[0])*30).astype(int)
    valid=np.flatnonzero((c[:,9]>.5)&(base['glyph']!=32)&(x>=0)&(x<30)&(y>=0)&(y<30));winner=np.full(900,np.uint64(2**64-1));out=np.full(900,32,np.uint8);values=np.zeros((900,12),np.float32)
    depths=np.clip(dep*100000,1,4000000).astype(np.uint64);packed=(depths<<np.uint64(32))|i.astype(np.uint64)
    for k in valid:
        j=y[k]*30+x[k]
        if packed[k]<winner[j]:winner[j]=packed[k];out[j]=base['glyph'][k];values[j]=c[k];values[j,1]=depths[k]/100000;values[j,8]=k+1
    return out,values,p.astype(np.float32)
