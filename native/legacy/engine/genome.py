import hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'config/collection.json').read_text(encoding='utf-8'))
REGISTRY=json.loads((ROOT/'traits/registry.json').read_text(encoding='utf-8'))['traits']
TRAITS={t['id']:t for t in REGISTRY}
FAMILIES=list(CONFIG['families'])
RARITIES=list(CONFIG['rarities'])
MODES=['RECOGNIZABLE','FRAGMENTED','APPARENT CHAOS','ENCRYPTED','ANATOMICAL RECONSTRUCTION','WIRESPACE','DUALITY','DATA FOSSIL','VOID ENTITY','DIMENSIONAL ANOMALY']
SUBJECTS={'SKULLS':['Human','Primate','Ram','Dragon','Avian','Longjaw','Broken','Mechanical'],
 'CHARACTERS':['Punk','Android','Warrior','Skeleton','Specter','Mage','Astronaut','Ape','Plague doctor','Winged guardian'],
 'ANIMALS':['Wolf','Cat','Ape','Penguin','Stag','Serpent','Dragon','Owl','Bat','Fish','Beetle','Horse','Tiger','Fox','Tortoise','Shark']}
VERSION='1.0.0'
def normalize_numbers(obj):
    if isinstance(obj,float) and math.isfinite(obj) and obj.is_integer():return int(obj)
    if isinstance(obj,dict):return {k:normalize_numbers(v) for k,v in obj.items()}
    if isinstance(obj,list):return [normalize_numbers(v) for v in obj]
    return obj
def canonical(obj): return json.dumps(normalize_numbers(obj),sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def digest(obj): return hashlib.sha256(canonical(obj)).hexdigest()
class Stream:
    def __init__(self,seed): self.key=bytes.fromhex(seed);self.counter=0
    def unit(self):
        b=hashlib.sha256(self.key+self.counter.to_bytes(8,'little')).digest();self.counter+=1
        return int.from_bytes(b[:8],'little')/2**64
    def choice(self,n): return min(n-1,int(self.unit()*n))
    def between(self,a,b): return a+(b-a)*self.unit()
    def weighted(self,weights):
        target=self.unit()*sum(weights)
        for i,w in enumerate(weights):
            target-=w
            if target<0:return i
        return len(weights)-1
def selection_weights(group,key,size,fallback):
    table=CONFIG.get('probabilities',{}).get(group,{})
    values=table.get(key,fallback)
    if len(values)!=size or any(not isinstance(w,(int,float)) or not math.isfinite(w) or w<0 for w in values) or sum(values)<=0:
        raise ValueError('Invalid probability weights: '+group+'/'+key)
    return values

def modifier_weights(rarity,category,tier):
    defaults=[5 if i<3 and tier<2 else 2 if i<7 else 1 for i in range(10)]
    table=CONFIG.get('probabilities',{}).get('modifiers',{}).get(rarity,{})
    values=table.get(category,table.get('default',defaults))
    if len(values)!=10 or any(not isinstance(w,(int,float)) or not math.isfinite(w) or w<0 for w in values) or sum(values)<=0:
        raise ValueError('Invalid modifier weights: '+rarity+'/'+category)
    return values

def allocation():
    families=[f for f,count in CONFIG['families'].items() for _ in range(count)]
    rarities=[r for r,count in CONFIG['rarities'].items() for _ in range(count)]
    for values,key in [(families,'family'),(rarities,'rarity')]:
        rng=Stream(hashlib.sha256((CONFIG['master_seed']+key).encode()).hexdigest())
        for i in range(len(values)-1,0,-1):
            j=rng.choice(i+1);values[i],values[j]=values[j],values[i]
    counters={f:0 for f in FAMILIES};legend=0;result=[]
    for e,(f,r) in enumerate(zip(families,rarities),1):
        result.append(dict(edition=e,family=f,rarity=r,style_index=counters[f]%100,legend_index=legend if r=='LEGENDARY' else -1))
        counters[f]+=1
        if r=='LEGENDARY':legend+=1
    return result
def make_genome(edition=0,family='SKULLS',rarity='EPIC',seed=None,mutation=0,style_index=None,legend_index=0,overrides=None):
    if family not in FAMILIES or rarity not in RARITIES:raise ValueError('Unknown family or rarity')
    overrides=overrides or {}
    if seed is None: seed=f'{CONFIG["master_seed"]}/{edition}/{family}/{mutation}'
    if not isinstance(seed,str) or len(seed)>256:raise ValueError('Seed must be text, at most 256 characters')
    seed256=hashlib.sha256(seed.encode()).hexdigest() if len(seed)!=64 or any(c not in '0123456789abcdef' for c in seed) else seed
    rng=Stream(seed256);tier=RARITIES.index(rarity)
    prefix=['S','C','A'][FAMILIES.index(family)]
    style=overrides.get('style') or f'{prefix}{(rng.weighted(selection_weights("styles",family,100,[1]*100)) if style_index is None else style_index)+1:03}'
    if style not in TRAITS or family not in TRAITS[style]['families']:raise ValueError('Style is incompatible with family')
    rule=TRAITS[style]['rules'];repairs=[]
    modifiers={}
    for category in range(1,13):
        # Rarity biases simpler topology/camera/entropy without eliminating vocabulary.
        weights=modifier_weights(rarity,f'T{category:02}',tier)
        modifiers[f'T{category:02}']=f'T{category:02}.{rng.weighted(weights)+1:02}'
    for key,name in [('T02','topology'),('T04','texture')]:
        if rule[name] != ('Solid Core' if key=='T02' else 'Halftone'):
            modifiers[key]=next(t['id'] for t in REGISTRY if t['label']==rule[name])
    modifiers['T05']=f'T05.{rule["glyph_bias"]+1:02}'
    if rarity!='LEGENDARY':
        modifiers['T09']='T09.01';repairs.append('Static rarity: motion set to Static State; assembly/destruction are reveal controls only.')
    appearance=overrides.get('appearance') or rule['appearance']
    if appearance not in MODES:raise ValueError('Unknown appearance')
    if rarity=='COMMON' and appearance=='DIMENSIONAL ANOMALY':appearance='RECOGNIZABLE';repairs.append('Common excludes dimensional hybrid topology.')
    if appearance=='WIRESPACE':modifiers['T02']='T02.05'
    if appearance=='VOID ENTITY':modifiers['T10']='T10.01'
    if modifiers['T10'] in ['T10.01','T10.02'] and modifiers['T04'] in ['T04.03','T04.06']:
        modifiers['T04']='T04.02';repairs.append('Sparse density replaced dense texture with stippling.')
    for cat,override in [('T01','camera'),('T03','lighting'),('T05','glyph')]:
        if overrides.get(override):
            value=overrides[override]
            if value not in TRAITS or not value.startswith(cat+'.'):raise ValueError('Invalid '+override)
            modifiers[cat]=value
    subject=overrides.get('subject') or SUBJECTS[family][rng.weighted(selection_weights('subjects',family,len(SUBJECTS[family]),[1]*len(SUBJECTS[family])))]
    if subject not in SUBJECTS[family]:raise ValueError('Subject incompatible with family')
    if family=='ANIMALS':
        for word,spec in [('Dragon','Dragon'),('Phoenix','Owl'),('Unicorn','Horse'),('Pegasus','Horse'),('Fenrir','Wolf'),('Kitsune','Fox'),('Thunderbird','Owl')]:
            if word==TRAITS[style]['label'] and 'subject' not in overrides:subject=spec
    p=dict(width=rng.between(.72,1.18)*rule['proportions'][0],height=rng.between(.82,1.12)*rule['proportions'][1],
        depth=rng.between(.7,1.3)*rule['proportions'][2],limb_length=rng.between(.75,1.2),head_size=rng.between(.72,1.24),
        jaw=rng.between(.55,1.25),socket=rng.between(.75,1.3),asymmetry=rng.between(0,.13)*(2-rule['symmetry']),
        curvature=rule['curvature'],segment_count=rule['segmentation']+tier,branch_depth=rule['branch_depth'],
        entropy=rng.between(.01,.05+tier*.035)+rule['entropy'],fragmentation=rng.between(.02,.08+tier*.035),
        complexity=.18+tier*.17,contrast=rng.between(.85,1.2),surface_frequency=rule['surface_frequency'],
        camera_yaw=rng.between(-.15,.15),camera_pitch=rng.between(-.12,.12),zoom=rng.between(.9,1.1),
        light_yaw=rule['light_yaw']+rng.between(-.3,.3),material=rule['material'],feature=rule['feature'],
        primitive_phase=rng.between(0,math.tau),background_density=0 if tier<2 else rng.between(0,.015),
        twist=rng.between(-.2,.2),neck_length=rng.between(.7,1.3),tail_length=rng.between(.7,1.3))
    for name in ['entropy','fragmentation','complexity','contrast']:
        if name in overrides:
            value=float(overrides[name])
            if not math.isfinite(value) or not 0<=value<=(2 if name=='contrast' else 1):raise ValueError('Invalid '+name)
            p[name]=value
    if 'camera_yaw' in overrides:
        yaw=float(overrides['camera_yaw'])
        if not math.isfinite(yaw) or abs(yaw)>math.pi:raise ValueError('Camera yaw must be finite and within -pi to pi')
        p['camera_yaw']=yaw
    if appearance=='FRAGMENTED':p['fragmentation']=max(.22,p['fragmentation'])
    if appearance=='APPARENT CHAOS':p['fragmentation']=max(.42,p['fragmentation'])
    if appearance=='DATA FOSSIL':p['material']='Porous stone';modifiers['T04']='T04.05'
    if appearance=='DUALITY':p['feature']='duality'
    state=int(modifiers['T12'][-2:])-1
    p['entity_state']=state
    p['head_size']*=1+(state-4.5)*.015
    p['curvature']*=.7+state*.065
    if state==4:p['asymmetry']+=.06
    if state==5:modifiers['T05']='T05.08'
    if state==6:p['entropy']=min(.4,p['entropy']+.09)
    if state==7:p['entropy']*=.4
    if state==8:p['contrast']*=1.08
    if state==9:p['fragmentation']=max(.2,p['fragmentation'])
    secondary=f'{prefix}{rng.weighted(selection_weights('secondary_styles',family,100,[1]*100))+1:03}' if tier>=3 else None
    g=dict(edition=edition,genome_version=VERSION,render_version='sdf-ascii-1.0.0',seed=seed256,mutation=mutation,
        family=family,subject=subject,rarity=rarity,style=style,secondary_style=secondary,appearance=appearance,
        modifiers=modifiers,parameters=p,repairs=repairs,
        animation=dict(enabled=rarity=='LEGENDARY',profile=int(legend_index)%23,name=CONFIG['legends'][int(legend_index)%23] if rarity=='LEGENDARY' else 'STATIC',
            fps=CONFIG['frames_per_second'],seconds=CONFIG['loop_seconds'],fragment_identity='canonical-surface-cell',assembly_variant=int(modifiers['T07'][-2:])-1,destruction_variant=int(modifiers['T08'][-2:])-1),
        encryption='AES-256-GCM' if appearance=='ENCRYPTED' or rarity in ['RARE','LEGENDARY'] else 'VISUAL-CIPHER' if modifiers['T05'] in ['T05.01','T05.02','T05.08'] else 'NONE')
    g['fingerprint']=digest(g)
    return g
def validate_genome(g):
    if g.get('genome_version')!=VERSION or g.get('render_version')!='sdf-ascii-1.0.0':raise ValueError('Unsupported genome/render version')
    if g.get('fingerprint')!=digest({k:v for k,v in g.items() if k!='fingerprint'}):raise ValueError('Genome fingerprint mismatch')
    if g['family'] not in FAMILIES or g['rarity'] not in RARITIES:raise ValueError('Invalid allocation')
    for id in [g['style'],g['secondary_style'],*g['modifiers'].values()]:
        if id is not None and id not in TRAITS:raise ValueError('Unsupported trait '+id)
    if len(g['seed'])!=64 or any(c not in '0123456789abcdef' for c in g['seed']):raise ValueError('Invalid seed')
    if g['appearance'] not in MODES or g['subject'] not in SUBJECTS[g['family']]:raise ValueError('Invalid subject or appearance')
    if g['family'] not in TRAITS[g['style']]['families']:raise ValueError('Style family mismatch')
    if set(g['modifiers'])!={f'T{i:02}' for i in range(1,13)}:raise ValueError('Expected 12 engineering categories')
    if any(not value.startswith(cat+'.') for cat,value in g['modifiers'].items()):raise ValueError('Modifier category mismatch')
    p=g['parameters']
    if p['material'] not in CONFIG['materials']:raise ValueError('Unknown material')
    for name,value in p.items():
        if isinstance(value,(int,float)):
            if not math.isfinite(value) or abs(value)>32:raise ValueError('Invalid numerical parameter '+name)
    for name in ['width','height','depth','limb_length','head_size','jaw','socket','zoom','neck_length','tail_length']:
        if not .15<=p[name]<=3:raise ValueError('Anatomical proportion out of bounds: '+name)
    for name in ['entropy','fragmentation','complexity']:
        if not 0<=p[name]<=1:raise ValueError('Effect out of bounds: '+name)
    if not 0<=p['contrast']<=2:raise ValueError('Contrast out of bounds')
    a=g['animation']
    if a['fps'] not in [12,15,20,24] or not 6<=a['seconds']<=12 or not 0<=a['profile']<23:raise ValueError('Invalid animation configuration')
    if a['enabled']!=(g['rarity']=='LEGENDARY'):raise ValueError('Animation must match rarity')
    return g
