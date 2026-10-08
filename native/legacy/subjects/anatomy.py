import math
import numpy as np
from geometry.primitives import Scene
from engine.genome import TRAITS, RARITIES, digest
def skull(s,p,subject='Human',center=(0,0,0),scale=1):
    cx,cy,cz=center;w=.68*p['width'];h=.74*p['height'];d=.46*p['depth'];head=p['head_size']
    def c(x,y,z):return (cx+x*scale,cy+y*scale,cz+z*scale)
    def ell(x,y,z,a,b,e,**kw):s.ellipsoid(c(x,y,z),(a*scale,b*scale,e*scale),**kw)
    if subject in ['Primate','Ape']:w*=1.17;d*=1.2
    if subject in ['Longjaw','Dragon','Ram']:h*=1.1;w*=.9
    if subject=='Avian':w*=.8
    ell(0,.15,0,w*head,h*head,d*head,label='cranial vault')
    socket=.22*p['socket']*head
    for side in [-1,1]:
        ell(side*w*.47,.16,d*.84,socket,socket*.83,.32*scale,cut=True,label='eye socket')
        ell(side*w*.65,-.23,.15,.2,.15,.25,label='zygomatic arch')
        s.capsule(c(side*w*.67,-.34,.04),c(side*w*.55,-.64,.16),.105*scale,'mandible')
        s.capsule(c(side*w*.27,.42,d*.62),c(side*w*.7,.34,d*.53),.09*scale,'brow ridge')
    s.cone(c(0,-.09,d*.75),.13*scale,.2*scale,cut=True,label='nasal cavity')
    ell(0,-.55,.17,w*.61,.15*p['jaw'],d*.5,label='jaw arch')
    for i in range(6):s.rounded_cube(c((i-2.5)*w*.17,-.48,d*.8),(.048*scale,.11*scale,.08*scale),.02*scale,label='tooth')
    if subject=='Broken':s.cube(c(-.35,.48,.2),(.2*scale,.27*scale,.5*scale),rotation=(0,0,.45),cut=True,label='fracture')
    if subject=='Mechanical':s.torus(c(0,0,d*.94),.43*scale,.04*scale,rotation=(math.pi/2,0,0),label='implant ring')
    if subject in ['Dragon','Ram']:p={**p,'feature':'horns'}
    accessory(s,p,c,scale)
def accessory(s,p,c=lambda x,y,z:(x,y,z),scale=1):
    feature=p['feature']
    if feature=='horns':
        for side in [-1,1]:s.bezier([c(side*.48,.55,0),c(side*.94,1.02,-.1),c(side*.72,1.22,.04)],.08*scale,4,'horn')
    elif feature in ['crown','crest','helmet']:
        s.torus(c(0,.65,0),.55*scale,.05*scale,label='headwear')
        for i in range(5):s.cone(c((i-2)*.18,.89,0),.07*scale,.18*scale,label='crest spike')
    elif feature=='wings':
        for side in [-1,1]:
            for i in range(3):s.jointed_limb([c(side*.35,.4,-.2),c(side*1.07,.52-i*.22,-.27),c(side*1.17,-.3-i*.13,-.15)],.04*scale)
    elif feature=='branches':
        for side in [-1,1]:s.fractal_branch(c(side*.35,.55,0),c(side*.68,.9,0),.035*scale,min(2,p['branch_depth']))
    elif feature in ['orbital','orbitals']:s.torus(c(0,0,-.1),1.12*scale,.025*scale,rotation=(.9,.2,.5),label='orbital ring')
    elif feature in ['mask','eye_patch']:s.rounded_cube(c(0,.1,.45),(.45*scale,.22*scale,.07*scale),.04*scale,label='mask')
    elif feature=='beak':s.cone(c(0,-.07,.58),.15*scale,.28*scale,rotation=(math.pi/2,0,0),label='beak')
def character(s,p,subject):
    w=p['width'];h=p['height'];l=p['limb_length'];head=p['head_size']
    s.spline_skeleton([(0,-.45,0),(0,0,.02),(0,.45,0),(0,.77,0)],.045)
    if subject=='Skeleton':
        for i in range(4):s.torus((0,.05+i*.12,0),.27-i*.025,.028,rotation=(0,0,math.pi/2),label='rib')
    elif subject in ['Android','Warrior','Astronaut']:s.rounded_cube((0,.2,0),(.3*w,.38*h,.18*p['depth']),.08,label='torso armor')
    else:s.organic_blob((0,.18,0),(.3*w,.42*h,.19*p['depth']),p['primitive_phase']+p['curvature'])
    s.ellipsoid((0,-.42,0),(.25*w,.16,.18),label='pelvis')
    skull(s,{**p,'feature':'none'},'Primate' if subject=='Ape' else 'Human',(0,.99,0),.34*head)
    for side in [-1,1]:
        shoulder=(side*.35*w,.47,0);elbow=(side*(.46+.08*p['asymmetry']),-.03*l,.05);hand=(side*.42,-.4*l,.15)
        s.jointed_limb([shoulder,elbow,hand],.075 if subject!='Skeleton' else .037)
        s.ellipsoid(hand,(.085,.13,.05),label='hand')
        hip=(side*.16*w,-.43,0);knee=(side*.2,-.81*l,.02);foot=(side*.24,-1.15*l,.08)
        s.jointed_limb([hip,knee,foot],.095 if subject!='Skeleton' else .04);s.ellipsoid(foot,(.115,.065,.17),label='foot')
    if subject in ['Mage','Specter']:s.curved_ribbon((0,-.28,-.08),(.35,.64,.08),.1,label='robe')
    if subject in ['Punk','Plague doctor','Winged guardian']:p={**p,'feature':{'Punk':'crest','Plague doctor':'beak','Winged guardian':'wings'}[subject]}
    accessory(s,p,lambda x,y,z:(x,y+.62,z),.7)
def animal(s,p,species):
    w=p['width'];h=p['height'];head=p['head_size'];depth=p['depth'];tail=p['tail_length']
    if species in ['Wolf','Cat','Tiger','Fox','Horse','Stag','Dragon']:
        long=species in ['Horse','Stag'];body=.66*w;neck=.34*p['neck_length'] if long else .18
        s.ellipsoid((-.1,0,0),(body,.34*h,.29*depth),label='animal torso')
        s.jointed_limb([(.4,.1,0),(.58,.36+neck,0)],.18)
        s.ellipsoid((.66,.36+neck,.04),(.25*head,.24*head,.22*head),label='head')
        s.ellipsoid((.9,.29+neck,.03),(.22 if long else .18,.11,.13),label='muzzle')
        for z in [-.19,.19]:
            for x in [-.48,.38]:s.jointed_limb([(x,-.14,z),(x+.05,-.49*h,z),(x-.05,-.84*h,z+.04)],.063 if long else .078)
            s.cone((.61,.68+neck,z*.75),.1,.17,rotation=(0,0,-.2),label='ear')
        s.bezier([(-.65,.07,0),(-1.03,.2,0),(-1.16,.58*tail,0)],.055,5,'tail')
        if species=='Stag':
            for z in [-.17,.17]:s.fractal_branch((.62,.66+neck,z),(.74,.97+neck,z),.03,2)
        if species=='Dragon':accessory(s,{**p,'feature':'wings'},lambda x,y,z:(x-.1,y,z))
    elif species in ['Owl','Penguin','Bat']:
        s.ellipsoid((0,-.04,0),(.43*w,.67*h,.3*depth),label='avian torso');s.ellipsoid((0,.63,0),(.37*head,.32*head,.29),label='avian head')
        s.cone((0,.53,.32),.11,.2,rotation=(math.pi/2,0,0),label='beak')
        for side in [-1,1]:
            s.ellipsoid((side*.14,.7,.24),(.09,.1,.09),cut=True,label='eye')
            s.jointed_limb([(side*.36,.2,0),(side*.7,-.1,-.07),(side*.6,-.48,0)],.05 if species=='Bat' else .09)
            s.ellipsoid((side*.19,-.74,.12),(.14,.06,.15),label='claw')
        if species=='Bat':accessory(s,{**p,'feature':'wings'},scale=1.2)
    elif species=='Ape':
        s.ellipsoid((0,-.1,0),(.47*w,.58*h,.3),label='primate torso');skull(s,{**p,'feature':'none'},'Primate',(0,.6,.05),.42)
        for side in [-1,1]:
            s.jointed_limb([(side*.39,.22,0),(side*.62,-.21,0),(side*.68,-.68,.14)],.12)
            s.jointed_limb([(side*.2,-.49,0),(side*.34,-.7,.07),(side*.31,-.9,.21)],.14)
    elif species=='Serpent':
        points=[(.64*math.sin(t*math.tau*1.25),1.02-2*t,.24*math.cos(t*math.tau)) for t in np.linspace(0,1,12)]
        s.tube(points,.12*w,'serpent spine');s.ellipsoid(points[0],(.24,.17,.16),label='serpent head')
    elif species in ['Fish','Shark']:
        s.ellipsoid((0,0,0),(.8*w,.32*h,.24*depth),label='fish torso')
        s.cone((-.81,0,0),.3,.32,rotation=(0,0,math.pi/2),label='tail fin')
        s.cone((0,.42,0),.2,.25,label='dorsal fin');s.ellipsoid((.55,.1,.2),(.06,.065,.04),cut=True,label='eye')
        for side in [-1,1]:s.curved_ribbon((-.1,-.29,side*.24),(.3,.1,.08),.1,rotation=(0,side*.7,0),label='fin')
    elif species in ['Beetle','Tortoise']:
        s.ellipsoid((0,0,0),(.6*w,.32*h,.54*depth),label='shell');s.ellipsoid((.64,.03,0),(.19,.17,.16),label='head')
        for side in [-1,1]:
            for x in [-.35,0,.35]:s.jointed_limb([(x,-.1,side*.32),(x-.1,-.34,side*.61)],.037 if species=='Beetle' else .09)
    if species not in ['Dragon','Bat']:accessory(s,p,scale=.65)
def build_scene(g):
    s=Scene();p=g['parameters'];family=g['family'];subject=g['subject'];tier=RARITIES.index(g['rarity'])
    if family=='SKULLS':skull(s,p,subject)
    elif family=='CHARACTERS':character(s,p,subject)
    else:animal(s,p,subject)
    # A secondary style changes geometry rather than just metadata.
    if g['secondary_style']:
        secondary=TRAITS[g['secondary_style']]['rules'];p2={**p,'feature':secondary['feature']}
        if p2['feature']!=p['feature']:accessory(s,p2,scale=.65)
        for row in s.rows:
            if not row[10]:row[4]*=secondary['proportions'][0]**.25;row[5]*=secondary['proportions'][1]**.25
    topology=int(g['modifiers']['T02'][-2:])-1
    if topology==1:s.ellipsoid((0,.05,0),(.28,.38,.22),cut=True,label='hollow core')
    elif topology==2 and family!='SKULLS':
        for row in s.rows:
            if row[0] in [1,11]:row[4]*=.67;row[6]*=.55
    elif topology==3:
        for y in [-.32,-.16,0,.16,.32]:s.torus((0,y,-.05),.48,.02,label='ribbed contour')
    elif topology==5:
        for i,row in enumerate(s.rows):
            if not row[10]:row[1]+=.025*math.sin(i*1.7);row[2]+=.02*math.cos(i*2.1)
    elif topology==6:s.sphere((0,0,-.14),.18,label='nested core')
    elif topology==7:
        for angle in [0,.8,1.6]:s.torus((0,0,-.18),.72,.026,rotation=(angle,.7,angle/2),label='interlocked ring')
    elif topology==8:
        for i,row in enumerate(s.rows):
            if not row[10]:row[1]+=.06*math.sin(i*2.4);row[2]+=.06*math.cos(i*1.9)
    elif topology==9:
        for i in range(3):s.extruded_contour((0,0,-.3-i*.09),(.6+i*.07,.7+i*.05,.018),5+i)
    if tier>=0:
        mathmode=int(g['modifiers']['T11'][-2:])-1
        if mathmode in [0,1]:
            s.helix((-.95,0,-.15),.12,1.8,1.5,.025,10,p['primitive_phase']+p['curvature'])
            if mathmode==1:s.helix((-.95,0,-.15),.12,1.8,1.5,.025,10,p['primitive_phase']+math.pi)
        elif mathmode==2:s.torus((0,0,-.3),1,.02,rotation=(.8,.4,0),label='torus field')
        elif mathmode in [3,5]:
            for x in [-.7,.7]:
                for y in [-.8,.8]:s.capsule((x,y,-.4),(x,y,.4),.015,'lattice')
        elif mathmode==4:
            for r in [.17,.25,.34]:s.torus((-.8,.62,0),r,.02,label='nested sphere contour')
        elif mathmode==6:s.bezier([(-.8,-.8,0),(-1.3,.8,0),(.9,1.3,0),(.5,.7,.4)],.018,8,'fibonacci arc')
        elif mathmode==7:s.extruded_contour((0,0,-.45),(.95,1.1,.02),3)
        elif mathmode==8:s.fractal_branch((-.7,-.7,0),(-.9,0,0),.022,2)
        elif mathmode==9:
            for i in range(3):s.plane((0,-.8+i*.7,-.4),(.9,.015,.15),label='floating stratum')
    if g['appearance']=='DIMENSIONAL ANOMALY':s.torus((0,0,0),.95,.05,rotation=(.8,.4,.6),label='impossible intersection')
    if p['feature']=='duality':
        for row in s.rows:
            if row[1]>0 and not row[10]:row[0]=6 if row[0] in [0,1,11] else row[0];row[6]*=.7
    # Geometry controls scale, curvature and asymmetry across all anatomical builders.
    for i,row in enumerate(s.rows):
        row[1]+=p['asymmetry']*math.sin(row[2]*3+i*.17)
        row[3]+=p['twist']*row[1]*row[2]+p['curvature']*.04*math.sin(row[2]*p['segment_count'])
        if row[0] in [1,11]:row[6]*=.85+.3*p['complexity']
    if len(s.rows)>160:raise ValueError('Scene exceeds bounded primitive budget')
    return s
