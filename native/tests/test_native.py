import copy
import json
import os
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nullgenesis.genome import seal,validate_genome,canonical,configuration
from nullgenesis.renderer import Renderer,from_packet
from nullgenesis.motion import animate_scene
from nullgenesis.codec import encrypt,decrypt

def fixture(coverage,grid=30,kind=9,rarity='COMMON',profile=0):
    def row(k,c,s,cut=0,layer=0,joint=0,extra=0):
        return [k,*c,*s,0,0,0,cut,1,extra,0,layer,joint]
    scene=[
        row(1,(0,.2,0),(.67,.8,.48)),
        row(1,(-.24,.37,.4),(.2,.22,.22),1,2),
        row(1,(.24,.37,.4),(.2,.22,.22),1,2),
        row(4,(0,.02,.46),(.11,.15,.12),1,2),
        row(7,(0,-.55,.02),(.4,.12,.25),extra=.04),
        row(2,(-.48,-.34,0),(.07,.26,.07),joint=1),
        row(2,(.48,-.34,0),(.07,.26,.07),joint=2),
        row(5,(0,.26,-.3),(.82,.035,.82),layer=1),
        row(4,(-.46,.96,0),(.11,.32,.11),layer=3,joint=3),
        row(4,(.46,.96,0),(.11,.32,.11),layer=3,joint=4)
    ]
    for i,r in enumerate(scene):r[11]=i+1
    cfg=[3.8,0,26/48,.25,.07,0,2,-.25,1,.75,1,34,.4,.2,1,1,1,0,0,1,77823,0,.03,1]
    return seal(dict(genome_version='web-3.0.0',edition=10001,seed='native-fixture',scene=scene,config=cfg,grammar='.,:;irsXA253hMHGS#9B&@/\\|_-',coverage=list(map(float,coverage)),samples=1,grid=[grid,grid],rarity=rarity,motion=dict(kind=kind,amplitude=.4,speed=1,phase=.2,frequency=2),animation=dict(enabled=True,fps=12,seconds=3 if rarity=='COMMON' else 8,profile=profile,assembly_variant=profile%10,destruction_variant=(profile+3)%10,legendary=rarity=='LEGENDARY')))

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.renderer=Renderer(os.environ.get('NULL_GENESIS_TEST_BACKEND','cpu'))
    @classmethod
    def tearDownClass(cls):cls.renderer.close()
    def test_native_resolution_and_determinism(self):
        for grid in (30,50):
            g=fixture(self.renderer.coverage,grid);a=self.renderer.render(g);b=self.renderer.render(g)
            self.assertEqual(a['ascii'],b['ascii']);self.assertEqual(a['packet'].shape,(grid*grid,12));self.assertTrue(np.array_equal(a['packet'],b['packet']))
            self.assertEqual(len(a['ascii'].splitlines()),grid);self.assertTrue(all(len(r)==grid for r in a['ascii'].splitlines()))
            image=np.asarray(self.renderer.image(a,6,12));self.assertEqual(image.shape,(grid*12,grid*6,3));self.assertTrue(np.array_equal(image[:,:,0],image[:,:,1]));self.assertTrue(np.array_equal(image[:,:,1],image[:,:,2]))
    def test_universal_motion_loop_and_geometry(self):
        for kind in range(10):
            g=fixture(self.renderer.coverage,30,kind);scene=np.asarray(g['scene'],np.float32);total=g['animation']['fps']*g['animation']['seconds']
            self.assertTrue(np.array_equal(animate_scene(scene,g['motion'],0,total),scene));self.assertTrue(np.array_equal(animate_scene(scene,g['motion'],total,total),scene))
            self.assertGreater(np.max(abs(animate_scene(scene,g['motion'],total//4,total)-scene)),.001)
            # Adjacent boundary poses must be comparably close to regular frames.
            loop=np.linalg.norm(animate_scene(scene,g['motion'],total-1,total)-scene);regular=np.linalg.norm(animate_scene(scene,g['motion'],1,total)-scene)
            self.assertLess(loop,max(regular*2,.15))
        for rarity in ('COMMON','UNCOMMON','RARE','EPIC','LEGENDARY'):
            g=fixture(self.renderer.coverage,30,9,rarity);a=self.renderer.render(g);b=self.renderer.frame(a,g,9);c=self.renderer.frame(a,g,g['animation']['fps']*g['animation']['seconds'])
            self.assertEqual(a['ascii'],c['ascii']);self.assertFalse(np.array_equal(a['packet'],b['packet']))
    def test_batch_and_memory_pool(self):
        batch=[fixture(self.renderer.coverage,30,kind) for kind in (0,1,2)]
        result=self.renderer.render_batch(batch)
        self.assertEqual(len(result),3)
        for g,r in zip(batch,result):self.assertEqual(r['ascii'],self.renderer.render(g)['ascii'])
        if self.renderer.driver:
            g=batch[0];self.renderer.render(g);self.renderer.image(self.renderer.render(g));before=self.renderer.status()
            for _ in range(5):self.renderer.image(self.renderer.render(g))
            after=self.renderer.status();self.assertEqual(before['allocations'],after['allocations']);self.assertEqual(before['pool_bytes'],after['pool_bytes'])
    def test_authenticated_encryption_and_reject_tampering(self):
        g=fixture(self.renderer.coverage);key=bytes(range(32));envelope=encrypt(g,key)
        self.assertEqual(decrypt(envelope,key)['genome'],g)
        regenerated=self.renderer.render(decrypt(envelope,key)['genome']);canonical=self.renderer.render(g)
        self.assertTrue(np.array_equal(regenerated['packet'],canonical['packet']))
        self.assertEqual(envelope['version'],3)
        forged=copy.deepcopy(envelope);forged['fingerprint']='f'*64
        with self.assertRaises(Exception):decrypt(forged,key)
        with self.assertRaises(Exception):decrypt(envelope,bytes(reversed(range(32))))
        forged=copy.deepcopy(g);forged['scene'][0][4]+=.1
        with self.assertRaises(ValueError):validate_genome(forged)
        with self.assertRaises(ValueError):validate_genome(seal({**g,'grid':[40,40]}))
        glyph,cells=from_packet(self.renderer.render(g)['packet'],[30,30]);self.assertEqual(glyph.shape,(900,))
        legacy=copy.deepcopy(g);legacy['genome_version']='web-1.0.0';legacy['animation']['seconds']=8;legacy=seal(legacy)
        old_envelope=encrypt(legacy,key,'legacy message');self.assertEqual(old_envelope['version'],1)
        self.assertEqual(decrypt(old_envelope,key)['genome'],legacy)
        self.assertEqual(decrypt(old_envelope,key)['hidden_message'],'legacy message')
        forged=copy.deepcopy(old_envelope);forged['edition']+=1
        with self.assertRaises(Exception):decrypt(forged,key)
    def test_browser_validation_domain(self):
        g=fixture(self.renderer.coverage);g['motion'].update(speed=4,frequency=-32,phase=-6.28,axis=[1,0,-1],limbs=True,seed=4294967295);g['rendering']=dict(blend=.12,ambient=1,fill=1,ao=1,rim=1,contrast=2,contour=1);validate_genome(seal(g))
        for change in ({'speed':5},{'frequency':33},{'phase':7},{'kind':True},{'type':3},{'amplitude':True},{'axis':[2,0,0]},{'seed':-1}):
            candidate=copy.deepcopy(g);candidate['motion'].update(change)
            with self.assertRaises(ValueError):validate_genome(seal(candidate))
        candidate=copy.deepcopy(g);candidate['rendering']['unknown']=.2
        with self.assertRaises(ValueError):validate_genome(seal(candidate))
        candidate=copy.deepcopy(g);candidate['scene'][0][14]=5
        with self.assertRaises(ValueError):validate_genome(seal(candidate))
    def test_integer_valued_json_numbers(self):
        original=fixture(self.renderer.coverage,30,2,'LEGENDARY',7);g=copy.deepcopy(original)
        g['grid']=[30.0,30.0];g['samples']=1.0
        for k in ('fps','seconds','profile','assembly_variant','destruction_variant'):g['animation'][k]=float(g['animation'][k])
        for k in ('kind','speed'):g['motion'][k]=float(g['motion'][k])
        g=seal(g);self.assertEqual(g['fingerprint'],original['fingerprint'])
        reference=self.renderer.render(original,28);actual=self.renderer.render(g,28)
        self.assertTrue(np.array_equal(reference['packet'],actual['packet']))
        frames=list(self.renderer.render_sequence(g,[0,28],chunk_size=2));self.assertTrue(np.array_equal(frames[1]['packet'],reference['packet']))
    def test_sequence_matches_individual_frames(self):
        for rarity in ('COMMON','LEGENDARY'):
            for grid in (30,50):
                g=fixture(self.renderer.coverage,grid,2,rarity,7);indices=[0,5,17,29,41]
                sequence=list(self.renderer.render_sequence(g,indices,chunk_size=3))
                for index,result in zip(indices,sequence):
                    individual=self.renderer.render(g,index)
                    self.assertEqual(result['ascii'],individual['ascii'])
                    self.assertTrue(np.array_equal(result['packet'],individual['packet']))
    def test_all_legendary_profiles_are_reachable(self):
        sequences=set()
        for profile in range(23):
            g=fixture(self.renderer.coverage,30,9,'LEGENDARY',profile);base=self.renderer.render(g);r=self.renderer.frame(base,g,28);self.assertEqual(len(r['ascii'].splitlines()),30)
            sequences.add(r['packet'].tobytes())
        self.assertEqual(len(sequences),23)

if __name__=='__main__':unittest.main()
