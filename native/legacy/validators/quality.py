import hashlib, math
import numpy as np
from engine.renderer import ascii_text,validate_buffer
from engine.genome import CONFIG
def features(r):
    mask=(r['glyph']!=32);bright=np.where(mask,r['cells'][:,0]/255,0).reshape(30,30)
    coarse=bright.reshape(15,2,15,2).mean(axis=(1,3)).ravel()
    hist=np.bincount(r['glyph']-32,minlength=95).astype(float);hist/=hist.sum()
    # 8x8 low-frequency DCT perceptual signature, computed without SciPy.
    n=30;k=np.arange(8)[:,None];x=np.arange(n)[None,:];basis=np.cos(np.pi*(x+.5)*k/n)
    dct=basis@bright@basis.T;phash=(dct>np.median(dct[1:])).ravel()
    return dict(mask=mask,bright=bright.ravel(),coarse=coarse,hist=hist,phash=phash)
def components(mask):
    a=mask.reshape(30,30);seen=set();sizes=[]
    for y,x in zip(*np.nonzero(a)):
        if (y,x) in seen:continue
        todo=[(y,x)];seen.add((y,x));n=0
        while todo:
            py,px=todo.pop();n+=1
            for yy,xx in [(py-1,px),(py+1,px),(py,px-1),(py,px+1)]:
                if 0<=yy<30 and 0<=xx<30 and a[yy,xx] and (yy,xx) not in seen:seen.add((yy,xx));todo.append((yy,xx))
        sizes.append(n)
    return max(sizes,default=0),len(sizes)
def quality(r,g,underlying=None):
    validate_buffer(r['glyph'],r['cells']);f=features(r);occupied=int(f['mask'].sum());biggest,clusters=components(f['mask'])
    visible=r['cells'][f['mask']];coverage=occupied/900
    source=underlying or r;sm=source['glyph']!=32;surfaces=source['cells'][sm]
    depth=float(np.std(surfaces[:,1])) if len(surfaces) else 0
    contrast=float(np.std(f['bright'][f['mask']])) if occupied else 0
    hist=f['hist'][f['hist']>0];entropy=float(-(hist*np.log2(hist)).sum())
    recognized=g['appearance'] in ['RECOGNIZABLE','ANATOMICAL RECONSTRUCTION','DUALITY','DATA FOSSIL']
    reasons=[]
    if occupied<22 or coverage>.72:reasons.append('negative-space/occupancy')
    if len(surfaces)<28 or depth<.018:reasons.append('underlying-depth')
    if contrast<.008:reasons.append('tonal-range')
    if recognized and biggest/max(occupied,1)<.4:reasons.append('anatomical-coherence')
    scores=dict(silhouette=round(biggest/max(occupied,1),3),structural_coherence=round(biggest/max(occupied,1),3),depth=round(depth,4),tonal_contrast=round(contrast,4),negative_space=round(1-coverage,4),glyph_entropy=round(entropy,4),clusters=clusters,occupied_cells=occupied,
        recognition_evaluation='silhouette/coherence proxy; human contact-sheet review required' if recognized else 'intentional abstraction: underlying surface depth and composition evaluated')
    scores['quality_score']=round(100*(.3*min(depth/.4,1)+.25*min(contrast/.15,1)+.25*biggest/max(occupied,1)+.2*min((1-coverage)/.6,1)),2)
    return not reasons,scores,reasons,f
def similarity(a,b):
    union=np.logical_or(a['mask'],b['mask']).sum();iou=np.logical_and(a['mask'],b['mask']).sum()/max(union,1)
    x,y=a['bright'],b['bright'];mx,my=x.mean(),y.mean();vx,vy=x.var(),y.var();cov=((x-mx)*(y-my)).mean()
    ssim=((2*mx*my+.0001)*(2*cov+.0009))/((mx*mx+my*my+.0001)*(vx+vy+.0009))
    return dict(silhouette_iou=float(iou),spatial_distance=float(np.mean(np.abs(a['coarse']-b['coarse']))),ssim=float(ssim),glyph_distance=float(np.abs(a['hist']-b['hist']).sum()/2),perceptual_hamming=int((a['phash']!=b['phash']).sum()))
class Uniqueness:
    def __init__(self):self.items=[];self.grids=set();self.genomes=set();self.geometry=set();self.coarse=np.empty((3333,225),np.float32)
    def check(self,r,g,f):
        grid=hashlib.sha256(ascii_text(r['glyph']).encode()).hexdigest()
        if grid in self.grids:return False,'identical ASCII grid',{}
        if g['fingerprint'] in self.genomes or r['geometry_signature'] in self.geometry:return False,'identical genome/geometry',{}
        if not self.items:return True,None,dict(nearest_edition=None)
        distances=np.mean(np.abs(self.coarse[:len(self.items)]-f['coarse']),axis=1)
        # Compare all editions coarsely; detailed 900-cell metrics on the nearest 24.
        nearest=np.argsort(distances)[:24];closest=None
        for index in nearest:
            other,oid=self.items[index];s=similarity(f,other);s['nearest_edition']=oid
            if closest is None or s['spatial_distance']<closest['spatial_distance']:closest=s
            t=CONFIG['uniqueness']
            if s['silhouette_iou']>t['silhouette_iou'] and s['spatial_distance']<t['spatial_distance'] and (s['ssim']>t['ssim'] or s['glyph_distance']<t['glyph_distance']):return False,'visually similar structure',s
        return True,None,closest
    def accept(self,r,g,f):
        n=len(self.items);self.coarse[n]=f['coarse'];self.items.append((f,g['edition']));self.grids.add(hashlib.sha256(ascii_text(r['glyph']).encode()).hexdigest());self.genomes.add(g['fingerprint']);self.geometry.add(r['geometry_signature'])
