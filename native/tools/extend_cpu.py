"""Extend the preserved NumPy reference with the same native grid contract."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'legacy/engine/cpu.py').read_text(encoding='utf-8')
s=s.replace('def field(p,scene,top):','def field(p,scene,top,blend=0):')
s=s.replace('d=primitive(p,r);values,ids=(neg,ni) if r[10]>.5 else (pos,pi);hit=d<values;values[hit]=d[hit];ids[hit]=i+1','''d=primitive(p,r);values,ids=(neg,ni) if r[10]>.5 else (pos,pi);hit=d<values;ids[hit]=i+1
        local=min(blend,float(min(r[4:7]))*.35)
        if local>0 and r[10]<.5 and r[14]!=4:
            h=np.clip(.5+.5*(values-d)/local,0,1);values[:]=values*(1-h)+d*h-local*h*(1-h)
        else:values[hit]=d[hit]''')
s=s.replace('def normals(p,scene,top):','def normals(p,scene,top,blend=0):').replace('field(p+a,scene,top)','field(p+a,scene,top,blend)').replace('field(p-a,scene,top)','field(p-a,scene,top,blend)')
s=s.replace('def render_cpu(scene,cfg,grammar,coverage,ss):','def render_cpu(scene,cfg,grammar,coverage,ss):\n    width,height=int(cfg[24]),int(cfg[25]);count=width*height;blend=cfg[27];v3=cfg[26]>.5')
s=s.replace('900','count').replace('%30','%width').replace('//30','//width').replace('/30-.5)', '/width-.5)').replace('/30)*cfg[0]', '/height)*cfg[0]')
s=s.replace('range(108)','range(160 if v3 else 108)').replace('hit=d<.0075', 'hit=d<(.0035*30/width if v3 else .0075)').replace('d[~hit]*.72,.004', 'd[~hit]*(.68 if v3 else .72),.0015 if v3 else .004')
s=s.replace('field(origin[ix]+direction[ix]*t[ix,None],scene,top)', 'field(origin[ix]+direction[ix]*t[ix,None],scene,top,blend)').replace('normals(p,scene,top)', 'normals(p,scene,top,blend)').replace('field(p+n*.09,scene,top)', 'field(p+n*.09,scene,top,blend)').replace('field(p+light*st[:,None],scene,top)', 'field(p+light*st[:,None],scene,top,blend)')
s=s.replace('value=(.15+diff*.64*shadow+rim*cfg[13]+spec)*ao;k=int(cfg[18])','''value=(.15+diff*.64*shadow+rim*cfg[13]+spec)*ao
        if v3:
            occ=np.zeros(len(p));weight=1
            for h in [.045,.11,.23]:occ+=(h-field(p+n*h,scene,top,blend)[0])*weight;weight*=.55
            ao=np.clip(1-occ*3.5*cfg[30],.22,1);shadow=np.ones(len(p));st=np.full(len(p),.018)
            for j in range(10):
                dd,_=field(p+light*st[:,None],scene,top,blend);shadow=np.minimum(shadow,np.clip(dd*10/st,.2,1));st+=np.clip(dd,.025,.16)
            fill=norm(np.array([-.7,-.15,.6]));metal=[.04,.95,.65,.23,.8,.9,.7,.12,0,.3][max(0,min(9,int(cfg[14])))]
            spec=np.maximum((n*norm(light-direction[ix])).sum(axis=1),0)**max(2,cfg[11])*(cfg[12]+metal*.13)
            value=(cfg[28]+diff*.68*shadow+cfg[29]*np.maximum(n@fill,0)+rim*cfg[31]+spec*shadow)*ao
        k=int(cfg[18])''')
s=s.replace('lum[ix]+=np.clip(value*cfg[16],.025,1)', 'lum[ix]+=np.clip(value*cfg[16],.025,1)**(1/cfg[32] if v3 else 1)')
s=s.replace('lum[ix]>=.27','lum[ix]>=(.22 if v3 else .27)')
s=s.replace('target=np.clip(.04+lum[i]*.32,.025,.4);distances=', 'target=np.clip(.025+lum[i]*.36,.02,.42) if v3 else np.clip(.04+lum[i]*.32,.025,.4);distances=')
s=s.replace('glyph[i]=grammar[np.argmin(distances)]','''
        if v3:
            nv=normal[i]@R;edge=1-abs(nv[2]);chars=[chr(int(code)) for code in grammar]
            directional=np.array([(-.026 if char in ('_-=' if abs(nv[1])>abs(nv[0]) else '|!:') or char==('/' if nv[0]*nv[1]>0 else '\\\\') else .008)*edge*cfg[33] if edge>.45 else 0 for char in chars])
            cell_seed=int(hash32(np.uint32((math.floor(positions[i,0]*71)+512)*997+(math.floor(positions[i,1]*71)+512)*313+objects[i]*911)))
            distances=np.abs(coverage[grammar-32]-target)+directional+rnd(seed+cell_seed+grammar.astype(np.int64)*17)*.002
        glyph[i]=grammar[np.argmin(distances)]''')
s=s.replace('65+190*np.sqrt(lum[ix])','(45 if v3 else 65)+(210 if v3 else 190)*np.sqrt(lum[ix])')
s=s.replace("c=base['cells'];cfg=base['cfg'];i=np.arange(count);", "c=base['cells'];cfg=base['cfg'];width,height=int(cfg[24]),int(cfg[25]);count=width*height;i=np.arange(count);")
s=s.replace('t=frame%total/total;a=assembled(t)','t=(frame%total/total+cfg[34])%1;a=assembled(t)')
s=s.replace('if static_mode>=100:', 'if cfg[35]>=0:a=cfg[35]\n    elif static_mode>=100:')
s=s.replace('e=np.eye(3)*.003', 'e=np.eye(3)*(.0025 if blend>0 else .003)')
s=s.replace('if k==4:value=.2+rim*.8', 'if k==4:value=(.16+rim*.84) if v3 else (.2+rim*.8)')
s=s.replace('if k==7:value[p[:,0]<0]*=.28', 'if k==7:value[p[:,0]<0]*=(.32 if v3 else .28)')
s=s.replace('if k==8:value=value**1.6', 'if k==8:value=value**(1.45 if v3 else 1.6)')
s=s.replace('    x=np.asarray(x,dtype=np.uint32);x=x^(x>>16);x=x*np.uint32(0x7feb352d);x=x^(x>>15);x=x*np.uint32(0x846ca68b);return x^(x>>16)', '    with np.errstate(over=\'ignore\'):\n        x=np.asarray(x,dtype=np.uint32);x=x^(x>>16);x=x*np.uint32(0x7feb352d);x=x^(x>>15);x=x*np.uint32(0x846ca68b);return x^(x>>16)')
s=s.replace(')*30).astype(int)', ')*width).astype(int)',1).replace(')*30).astype(int)', ')*height).astype(int)',1)
s=s.replace('(x<30)', '(x<width)').replace('(y<30)', '(y<height)').replace('j=y[k]*30+x[k]', 'j=y[k]*width+x[k]')
(root/'nullgenesis/cpu.py').write_text(s,encoding='utf-8')
