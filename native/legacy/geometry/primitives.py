"""Twenty reusable 3D operators compose a compact SDF scene. Units are world units."""
import math
import numpy as np
PRIMITIVES=['sphere','ellipsoid','capsule','cylinder','cone','torus','cube','rounded_cube','plane','curved_ribbon','tube','bezier','spline_skeleton','helix','fractal_branch','extruded_contour','organic_blob','cellular','jointed_limb','fragmented_shell']
class Scene:
    def __init__(self):self.rows=[];self.operators=set();self.labels=[]
    def add(self,kind,center,size,rotation=(0,0,0),cut=False,label='surface',extra=0):
        self.operators.add(PRIMITIVES[kind]);i=len(self.rows)
        # kind, center[3], size[3], rotation[3], subtract, ID, extra, reserved[3]
        self.rows.append([kind,*center,*size,*rotation,int(cut),i+1,extra,0,0,0]);self.labels.append(label)
        return i
    def sphere(self,c,r,**kw):return self.add(0,c,(r,r,r),**kw)
    def ellipsoid(self,c,s,**kw):return self.add(1,c,s,**kw)
    def capsule(self,a,b,r,label='bone'):
        a,b=np.array(a),np.array(b);v=b-a;length=float(np.linalg.norm(v));center=(a+b)/2
        # Rotation maps local Y onto the segment direction.
        z=-math.atan2(v[0],v[1]);x=math.atan2(v[2],math.hypot(v[0],v[1]))
        return self.add(2,center,(r,length/2,r),rotation=(x,0,z),label=label)
    def cylinder(self,c,r,h,**kw):return self.add(3,c,(r,h,r),**kw)
    def cone(self,c,r,h,**kw):return self.add(4,c,(r,h,r),**kw)
    def torus(self,c,r,t,**kw):return self.add(5,c,(r,t,r),**kw)
    def cube(self,c,s,**kw):return self.add(6,c,s,**kw)
    def rounded_cube(self,c,s,r=.08,**kw):return self.add(7,c,s,extra=r,**kw)
    def plane(self,c,s,**kw):return self.add(8,c,s,**kw)
    def curved_ribbon(self,c,s,curve=.3,**kw):return self.add(9,c,s,extra=curve,**kw)
    def tube(self,points,r,label='tube'):
        self.operators.add('tube')
        for a,b in zip(points,points[1:]):self.capsule(a,b,r,label)
    def bezier(self,points,r,steps=5,label='bezier'):
        self.operators.add('bezier');p=np.array(points,float);curve=[]
        for t in np.linspace(0,1,steps+1):
            q=p.copy()
            for n in range(len(p)-1,0,-1):q=(1-t)*q[:n]+t*q[1:n+1]
            curve.append(q[0])
        self.tube(curve,r,label)
    def spline_skeleton(self,points,r):
        self.operators.add('spline_skeleton');p=np.array(points,float)
        for i in range(len(p)-1):
            a=p[max(0,i-1)];b=p[i];c=p[i+1];d=p[min(len(p)-1,i+2)]
            curve=[.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3) for t in np.linspace(0,1,4)]
            self.tube(curve,r,'spine')
    def helix(self,c,radius,height,turns,tube=.025,steps=14,phase=0):
        self.operators.add('helix');points=[(c[0]+radius*math.cos(t*turns*math.tau+phase),c[1]+height*(t-.5),c[2]+radius*math.sin(t*turns*math.tau+phase)) for t in np.linspace(0,1,steps+1)]
        self.tube(points,tube,'helix')
    def fractal_branch(self,a,b,r,depth=2):
        self.operators.add('fractal_branch');self.capsule(a,b,r,'branch')
        if depth:
            a,b=np.array(a),np.array(b);v=b-a
            for sign in [-1,1]:self.fractal_branch(b,b+v*.55+np.array([sign*.2,.08,0]),r*.7,depth-1)
    def extruded_contour(self,c,s,sides=6):
        self.operators.add('extruded_contour');return self.add(10,c,s,extra=sides,label='polygon extrusion')
    def organic_blob(self,c,s,phase):
        self.operators.add('organic_blob');return self.add(11,c,s,extra=phase,label='organic tissue')
    def cellular(self,c,r,count=5):
        self.operators.add('cellular')
        for i in range(count):
            a=i*2.39996;self.sphere((c[0]+r*.6*math.cos(a),c[1]+r*.6*math.sin(a),c[2]+r*.25*math.cos(i*1.3)),r*.45,label='cell')
    def jointed_limb(self,points,r):
        self.operators.add('jointed_limb');self.tube(points,r,'limb')
        for p in points[1:-1]:self.sphere(p,r*1.18,label='joint')
    def fragmented_shell(self,c,r,t=.07):
        self.operators.add('fragmented_shell');self.sphere(c,r,label='shell');self.sphere(c,r-t,cut=True,label='shell cavity')
    def array(self):return np.ascontiguousarray(self.rows,np.float32)
