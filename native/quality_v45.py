"""Repeatable composition proxies; semantic recognition still needs visual review."""
import copy,math
import numpy as np
from nullgenesis.genome import seal
from validate_v3 import quality as old_quality

def subject_mask(result,g):
    ids=result['cells'][:,8].astype(int)-1;layers=np.array([r[14] for r in g['scene']]);valid=(ids>=0)&(ids<len(layers));mask=(result['glyph']!=32)&valid
    mask[valid]&=layers[ids[valid]]!=4
    return mask.reshape(*reversed(result['grid']))

def quality(result,g):
    metrics,signature=old_quality(result,g);mask=subject_mask(result,g);ys,xs=np.nonzero(mask);w,h=g['grid'];n=max(1,len(xs));span=[(int(xs.max()-xs.min())+1)/w,(int(ys.max()-ys.min())+1)/h] if len(xs) else [0,0];extent=max(span)
    bbox=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1] if len(xs) else [0,0,0,0]
    neighbors=np.zeros_like(mask,int)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not dx and not dy:continue
            shifted=np.zeros_like(mask);sy=slice(max(0,-dy),min(h,h-dy));sx=slice(max(0,-dx),min(w,w-dx));shifted[slice(max(0,dy),min(h,h+dy)),slice(max(0,dx),min(w,w+dx))]=mask[sy,sx];neighbors+=shifted
    noise=float(((neighbors<=1)&mask).sum()/n);frame_fit=max(0,1-abs(extent-.8)/.3);clarity=max(0,metrics['coherence']-noise)
    score=100*(.25*frame_fit+.18*clarity+.15*metrics['balance']+.13*min(1,metrics['tonal_contrast']*6)+.12*(1-min(1,noise*8))+.1*(1-min(1,metrics['clipping']*18))+.07*min(1,metrics['depth_span']))
    reasons=[]
    if not .69<=extent<=.87:reasons.append('subject dimension outside 69–87% finite-grid allowance')
    if metrics['clipping']>.055:reasons.append('clipped silhouette')
    if noise>.08:reasons.append('excess isolated details')
    if metrics['density']<.065 or metrics['density']>.75:reasons.append('unbalanced density')
    if score<55:reasons.append('quality proxy below 55')
    checks=dict(frame_occupancy=round(frame_fit,4),shape_clarity=round(clarity,4),noise_control=round(1-noise,4),subject_confidence=round(clarity*metrics['balance'],4),composition_balance=metrics['balance'],presentation_readability=round(min(1,w/80)*min(1,metrics['tonal_contrast']*7),4),motion_readability=None,trait_expression={'registered':len(g['categories'])==11,'geometry_coverage':metrics['visible_objects']},fusion_coherence=metrics['coherence'],nft_appeal=round(score/100,4))
    metrics.update(version='4.5.0',quality_score=round(score,2),subject_bbox=bbox,subject_span=[round(x,4) for x in span],dimension_occupancy=round(extent,4),isolated_detail_fraction=round(noise,5),checks=checks,accepted=not reasons,reasons=reasons,interpretation='engineering proxies, not trained semantic recognition or market valuation')
    return metrics,signature

def fit(renderer,genome,max_passes=5):
    g=copy.deepcopy(genome);log=[];mode=g['composition']['mode']
    if not g.get('provenance',{}).get('framing_prepared'):
        # Framing changes topology and proportions before the camera is solved.
        cutoff={'Tight Portrait':.05,'Head-and-Torso':-.48,'Half-Body':-.75,'Mask/Icon':.16}.get(mode)
        if cutoff is not None and len(g['scene'])<160:
            i=len(g['scene'])+1;g['scene'].append([7,0,cutoff-2,0,5,2,5,0,0,0,1,i,.01,1,0,i])
        if mode in ('Wide Creature','Vertical Relic'):
            axis=1 if mode=='Wide Creature' else 2
            for row in g['scene']:
                if row[14]!=4:row[axis]*=1.12;row[axis+3]*=1.12
        g['provenance']['framing_prepared']=True
    g=seal(g)
    for attempt in range(max_passes):
        result=renderer.render(g);before,_=quality(result,g);bbox=before['subject_bbox'];w,h=g['grid'];extent=before['dimension_occupancy'];dx=((bbox[0]+bbox[2])/2/w-.5)*g['config'][0];dy=(.5-(bbox[1]+bbox[3])/2/h)*g['config'][0]
        if .75<=extent<=.84 and abs(dx)<g['config'][0]*.025 and abs(dy)<g['config'][0]*.025 and before['clipping']<.03:break
        if not extent:raise ValueError('No visible subject to frame')
        old=g['fingerprint'];yaw,pitch=g['config'][3:5];factor=.88 if g['config'][1]<.5 else 1
        # Translate in the camera plane. Subtraction fields follow their solids.
        move=np.array([dx,dy*math.cos(pitch),dy*math.sin(pitch)]);move=np.array([math.cos(yaw)*move[0]+math.sin(yaw)*move[2],move[1],-math.sin(yaw)*move[0]+math.cos(yaw)*move[2]])*factor
        for row in g['scene']:
            for j in range(3):row[j+1]-=float(move[j])
        scale=max(.7,min(1.25,extent/g['composition']['target_dimension']));g['config'][0]=max(1.2,min(8,g['config'][0]*scale));g=seal(g)
        after,_=quality(renderer.render(g),g);log.append(dict(attempt=attempt+1,reason=before['reasons'] or ['safe-margin subject centering'],path=['subject-only effective bounds','camera-plane recenter','camera refit'],previous_fingerprint=old,updated_fingerprint=g['fingerprint'],pre=before,post=after,outcome='accepted' if after['accepted'] else 'revalidation required'))
    result=renderer.render(g);metrics,signature=quality(result,g)
    return g,result,metrics,signature,log

def repair(renderer,g,metrics,attempt,duplicate=False,temporal=False):
    previous=g['fingerprint'];g=copy.deepcopy(g);actions=[]
    if metrics['isolated_detail_fraction']>.025:
        g['scene']=[r for r in g['scene'] if r[10] or r[14]<=1 or max(r[4:7])>.085];actions.append('prune peripheral microgeometry')
    if metrics['tonal_contrast']<.13:
        g['rendering']['contrast']=min(1.6,g['rendering']['contrast']+.09);g['rendering']['fill']=max(.1,g['rendering']['fill']-.03);actions.append('reinforce cavity and material contrast')
    if metrics['clipping']>.03:
        for row in g['scene']:
            if row[14]==4:row[4]*=.88;row[5]*=.9
        actions.append('simplify stage silhouette while retaining its structures')
    if duplicate or not actions:
        # Cumulative projection changes cannot undo the preceding repair.
        g['config'][3]=max(-1.1,min(1.1,g['config'][3]+.14+.025*attempt));g['config'][4]=max(-.35,min(.35,g['config'][4]+.018))
        actions.append('separate overlapping anatomy by cumulative projection')
        if attempt>=1:
            for row in g['scene']:
                if row[14]!=4 and not (row[10] and max(row[4:7])>3):row[1]*=1.035;row[4]*=1.035
            actions.append('correct lateral body proportions and accessory separation')
        if attempt>=2:
            primary=[row for row in g['scene'] if not row[10] and row[14]==0]
            if primary:
                head=max(primary,key=lambda row:row[2]);head[4]*=1.055;head[5]*=1.04;head[6]*=1.035
                actions.append('reinforce focal head mass')
        if attempt>=3:
            for row in g['scene']:
                if row[10] and row[0]==1 and max(row[4:7])<.5:row[4]*=1.065;row[5]*=1.045;row[6]*=1.08
            actions.append('deepen and separate cranial cavities')
        if attempt>=4:
            g['rendering']['contrast']=min(1.6,g['rendering']['contrast']+.05);g['rendering']['rim']=min(.5,g['rendering']['rim']+.035)
            actions.append('recover contour and depth contrast')
        if temporal:
            maximum={'COMMON':.085,'UNCOMMON':.12,'RARE':.18,'EPIC':.24,'LEGENDARY':.3}[g['rarity']]
            g['motion']['phase']=(g['motion']['phase']+.47+.17*attempt)%(2*math.pi);g['motion']['amplitude']=min(maximum,g['motion']['amplitude']*(1.16+.04*attempt));g['motion']['intensity']=g['motion']['amplitude'];g['animation']['motion']=g['motion']
            actions.append('separate periodic motion phase with bounded tier amplitude')
    g['scene']=[[*r[:11],i+1,*r[12:15],i+1] for i,r in enumerate(g['scene'])];g=seal(g)
    fitted,result,post,signature,logs=fit(renderer,g)
    logs.insert(0,dict(attempt=attempt+1,reason=['perceptual duplicate'] if duplicate else metrics['reasons'] or ['overlapping focal structures'],path=actions,previous_fingerprint=previous,updated_fingerprint=fitted['fingerprint'],pre=metrics,post=post,outcome='requires uniqueness revalidation' if duplicate else 'accepted' if post['accepted'] else 'retry'))
    return fitted,result,post,signature,logs,actions
