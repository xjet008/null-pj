import sys,json,unittest,copy,gzip
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal,validate_genome
from nullgenesis.codec import encrypt,decrypt
from quality_v45 import fit,quality
from release_v45 import pack_lossless,unpack
import base64
class V45(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r=Renderer('cuda')
  with gzip.open(Path(__file__).resolve().parents[2]/'dist/v45/experiments/E036.json.gz','rt',encoding='utf-8') as stream:cls.source=json.load(stream)['genome']
  cls.g,cls.result,cls.q,cls.s,cls.log=fit(cls.r,cls.source)
 @classmethod
 def tearDownClass(cls):cls.r.close()
 def test_native_grids_square_and_determinism(self):
  for grid in (30,50,64,80,96,120):
   g=copy.deepcopy(self.g);g['grid']=[grid,grid];g=seal(g);a=self.r.render(g);b=self.r.render(g);self.assertEqual(a['ascii'],b['ascii']);self.assertEqual(len(a['glyph']),grid*grid)
  for size in (300,600,1200):
   image=np.asarray(self.r.square_image(self.result,size));self.assertEqual(image.shape,(size,size,3));self.assertTrue(np.array_equal(image[:,:,0],image[:,:,2]))
 def test_batch_sequence_matches_single_frame_and_endpoint(self):
  indices=[0,3,7,11];batch=list(self.r.render_sequence(self.g,indices));single=[self.r.render(self.g,i) for i in indices]
  for a,b in zip(batch,single):self.assertEqual(a['ascii'],b['ascii']);np.testing.assert_array_equal(a['cells'],b['cells'])
  self.assertEqual(self.r.render(self.g,self.g['animation']['fps']*self.g['animation']['seconds'])['ascii'],self.result['ascii'])
 def test_framing_subject_and_versioned_encryption(self):
  self.assertTrue(self.q['accepted']);self.assertGreaterEqual(self.q['dimension_occupancy'],.7);self.assertLessEqual(self.q['dimension_occupancy'],.85)
  key=bytes(range(32));e=encrypt(self.g,key,'synthetic test');self.assertEqual(e['version'],45);self.assertEqual(decrypt(e,key)['genome'],self.g)
  with self.assertRaises(Exception):decrypt(e,bytes(reversed(range(32))))
  bad=copy.deepcopy(self.g);bad['encoder']['noise_budget']=2
  with self.assertRaises(ValueError):validate_genome(seal(bad))
  for value in (0,-.1,2,float('nan')):
   bad=copy.deepcopy(self.g);bad['density_budget']['motion']=value
   with self.assertRaises(ValueError):validate_genome(seal(bad))
  bad=copy.deepcopy(self.g);del bad['density_budget']['stage']
  with self.assertRaises(ValueError):validate_genome(seal(bad))
 def test_lossless_codec(self):
  rng=np.random.default_rng(42);raw=np.zeros((36,900,2),np.uint8);raw[:,:,0]=65;raw[:,:,1]=rng.integers(0,256,(36,900),dtype=np.uint8);raw[2:]=raw[1]
  data=dict(cells=base64.b64encode(raw.tobytes()).decode(),frame_count=36,grid=[30,30],version='4.5.0',encoding='interleaved-u8');packed,metrics=pack_lossless(data);np.testing.assert_array_equal(unpack(packed),raw);self.assertGreaterEqual(metrics['saved_bytes'],0)
if __name__=='__main__':unittest.main()
