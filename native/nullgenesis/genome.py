"""Strict, versioned DNA validation and browser-compatible canonical hashing."""
import base64
import hashlib
import json
import math
from decimal import Decimal
import numpy as np

CATEGORIES=('Back','Body','Eyewear','Features','Form','Headwear','Mask','Method','Motion','Palette','Stage')
VERSIONS=('web-1.0.0','web-3.0.0','native-3.0.0','web-4.5.0')
DEFAULT_RENDERING=dict(blend=.026,ambient=.12,fill=.22,ao=.72,rim=.23,contrast=1.1,contour=.7)

def _number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
def _integer(value):return _number(value) and int(value)==value

def canonical(value):
    """JSON canonicalization matching the project's sorted JSON.stringify form.

    The accepted domain is JSON-safe finite values; exact IEEE-754 backend output
    is recorded independently and is never silently substituted between versions.
    """
    def encode(x):
        if x is None:return 'null'
        if x is True:return 'true'
        if x is False:return 'false'
        if isinstance(x,str):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
        if isinstance(x,(int,float)):
            if not math.isfinite(x):raise ValueError('Non-finite DNA number')
            if x==0:return '0'
            if isinstance(x,int) or float(x).is_integer():
                if abs(x)<1e21:return str(int(x))
            s=repr(float(x)).lower()
            exponent=int(s.split('e')[1]) if 'e' in s else None
            if exponent is not None and -6<=exponent<21:
                return format(Decimal(s),'f').rstrip('0').rstrip('.') if '.' in format(Decimal(s),'f') else format(Decimal(s),'f')
            if exponent is not None:
                mantissa=s.split('e')[0].rstrip('0').rstrip('.') if '.' in s.split('e')[0] else s.split('e')[0]
                return mantissa+'e'+('+' if exponent>=0 else '-')+str(abs(exponent))
            return s[:-2] if s.endswith('.0') else s
        if isinstance(x,(list,tuple)):return '['+','.join(encode(v) for v in x)+']'
        if isinstance(x,dict):return '{'+','.join(encode(k)+':'+encode(x[k]) for k in sorted(x))+'}'
        raise ValueError('DNA contains a non-JSON value')
    return encode(value).encode('utf-8')

def fingerprint(g):
    return hashlib.sha256(canonical({k:v for k,v in g.items() if k!='fingerprint'})).hexdigest()

def seal(g):
    g=dict(g);g['fingerprint']=fingerprint(g);return g

def validate_genome(g,verify=True):
    if not isinstance(g,dict) or g.get('genome_version') not in VERSIONS:raise ValueError('Unsupported native/browser genome version')
    v3=g['genome_version']!='web-1.0.0'
    grid=g.get('grid',[30,30])
    allowed=([30,30],[50,50],[64,64],[80,80],[96,96],[120,120]) if g['genome_version']=='web-4.5.0' else ([30,30],[50,50])
    if grid not in allowed:raise ValueError('Unsupported versioned native grid')
    if g['genome_version']=='web-1.0.0' and grid!=[30,30]:raise ValueError('Legacy DNA cannot be silently resized')
    rows=g.get('scene')
    if not isinstance(rows,list) or not 1<=len(rows)<=160 or any(not isinstance(r,list) or len(r)!=16 or any(not _number(x) or abs(x)>(160 if v3 and i in (11,13,15) else 100) for i,x in enumerate(r)) for r in rows):raise ValueError('Invalid scene rows')
    scene=np.asarray(rows,dtype=np.float64)
    if any(r[0]!=int(r[0]) or not 0<=r[0]<=11 or min(r[4:7])<.001 or r[0]==10 and r[12]<3 for r in scene):raise ValueError('Invalid primitive or dimensions')
    config=g.get('config')
    if not isinstance(config,list) or len(config)!=24 or any(not _number(x) for x in config):raise ValueError('Invalid camera/lighting parameters')
    cfg=np.asarray(config,dtype=np.float64)
    if cfg.shape!=(24,) or not np.isfinite(cfg).all() or max(abs(cfg))>16777216 or cfg[0]<.1 or cfg[2]<.1 or cfg[11]<1:raise ValueError('Invalid camera/lighting parameters')
    grammar=g.get('grammar')
    if not isinstance(grammar,str) or not 1<=len(grammar)<=95 or any(not 32<=ord(c)<=126 for c in grammar):raise ValueError('Invalid ASCII grammar')
    values=g.get('coverage')
    if not isinstance(values,list) or len(values)!=95 or any(not _number(x) for x in values):raise ValueError('Invalid glyph calibration')
    coverage=np.asarray(values,dtype=np.float64)
    if coverage.shape!=(95,) or not np.isfinite(coverage).all() or min(coverage)<0 or max(coverage)>1:raise ValueError('Invalid glyph calibration')
    if not _integer(g.get('samples')) or g['samples'] not in (1,2,4):raise ValueError('Invalid supersampling')
    a=g.get('animation',{})
    if not isinstance(a,dict) or a.get('fps')!=12 or not _integer(a.get('seconds')) or (not 2<=a['seconds']<=15 if v3 else a['seconds']!=8) or not _integer(a.get('profile')) or not 0<=a['profile']<23:raise ValueError('Invalid animation timeline')
    if any(not _integer(a.get(k)) or not 0<=a[k]<10 for k in ('assembly_variant','destruction_variant')):raise ValueError('Invalid reconstruction variants')
    if v3:
        m=g.get('motion')
        if not isinstance(m,dict):raise ValueError('Invalid V3 motion definition')
        kind=m.get('kind',m.get('type'));amp=m.get('amplitude',m.get('intensity'))
        if not _integer(kind) or not 0<=kind<=9 or not _number(amp) or not 0<=amp<=1 or a.get('enabled') is not True:raise ValueError('Invalid V3 motion definition')
        if not _integer(m.get('speed')) or not 1<=m['speed']<=4 or not _number(m.get('phase')) or abs(m['phase'])>math.tau:raise ValueError('Invalid periodic motion parameters')
        if 'kind' in m and 'type' in m and m['kind']!=m['type'] or 'amplitude' in m and 'intensity' in m and m['amplitude']!=m['intensity']:raise ValueError('Conflicting motion aliases')
        if 'frequency' in m and (not _number(m['frequency']) or abs(m['frequency'])>32):raise ValueError('Invalid motion frequency')
        for k in ('limbs','joints','breath','orbit'):
            if k in m and not isinstance(m[k],bool) and (not _number(m[k]) or abs(m[k])>32):raise ValueError('Invalid motion parameter')
        if 'axis' in m and (not isinstance(m['axis'],list) or len(m['axis'])!=3 or any(not _number(x) or abs(x)>1 for x in m['axis'])):raise ValueError('Invalid motion axis')
        if 'seed' in m and (not _integer(m['seed']) or not 0<=m['seed']<=4294967295):raise ValueError('Invalid motion seed')
        bounds=dict(blend=(0,.12),ambient=(0,1),fill=(0,1),ao=(0,1),rim=(0,1),contrast=(.5,2),contour=(0,1))
        rendering=g.get('rendering',{})
        if not isinstance(rendering,dict) or any(k not in bounds for k in rendering):raise ValueError('Invalid rendering profile')
        if any(not _number(v) or not bounds[k][0]<=v<=bounds[k][1] for k,v in rendering.items()):raise ValueError('Invalid rendering profile')
        for r in rows:
            if not _integer(r[13]) or r[13]<0 or not _integer(r[14]) or not 0<=r[14]<=4 or not _integer(r[15]) or r[15]<0:raise ValueError('Invalid geometry ownership')
        if np.all(cfg[7:10]==0) or cfg[0]>8 or cfg[2]>3 or not 0<=cfg[22]<=1:raise ValueError('Invalid V3 render bounds')
    if g['genome_version']=='web-4.5.0':
        e=g.get('encoder',{});c=g.get('composition',{});p=g.get('presentation',{})
        budget=g.get('density_budget',{})
        if not isinstance(budget,dict) or set(budget)!=set(('primary','secondary','tertiary','stage','ambient_code','motion')) or any(not _number(v) or not 0<v<=1 for v in budget.values()):raise ValueError('Invalid V4.5 layer density budget')
        if e.get('version')!='4.5.0' or not _integer(e.get('method_variant')) or not 0<=e['method_variant']<20:raise ValueError('Invalid V4.5 encoder method')
        for key in ('noise_budget','temporal_lock','depth_weight','edge_weight'):
            if not _number(e.get(key)) or not 0<=e[key]<=1:raise ValueError('Invalid encoder parameter')
        if not .65<=c.get('target_dimension',0)<=.88 or not 0<=c.get('safe_margin',-1)<=.15:raise ValueError('Invalid composition target')
        if c.get('mode') not in ('Tight Portrait','Head-and-Torso','Half-Body','Full-Body','Wide Creature','Vertical Relic','Mask/Icon','Distributed Abstract'):raise ValueError('Invalid framing mode')
        if p.get('width')!=p.get('height') or p.get('width') not in (300,600,1200):raise ValueError('Invalid square presentation')
    if verify:
        if not isinstance(g.get('fingerprint'),str) or g['fingerprint']!=fingerprint(g):raise ValueError('DNA fingerprint mismatch')
    return g

def configuration(g):
    cfg=np.zeros(40,np.float32);cfg[:24]=g['config'];cfg[24:26]=g.get('grid',[30,30])
    v3=g['genome_version']!='web-1.0.0';cfg[26]=int(v3)
    r={**DEFAULT_RENDERING,**g.get('rendering',{})}
    if v3:cfg[27:34]=[r[k] for k in ('blend','ambient','fill','ao','rim','contrast','contour')]
    else:cfg[27:34]=[0,.15,0,1,g['config'][13],1,0]
    cfg[34]=.32 if v3 else 0
    cfg[35]=-1
    if g['genome_version']=='web-4.5.0':
        cfg[36]=4.5;cfg[37]=g['encoder']['method_variant'];cfg[38]=g['encoder']['noise_budget'];cfg[39]=g['encoder']['edge_weight']
    return cfg

def motion_parameters(g):
    m=g.get('motion',{})
    return np.array([m.get('kind',m.get('type',0)),m.get('amplitude',m.get('intensity',.15)),m.get('speed',1),m.get('phase',0),m.get('frequency',2)],np.float32)
