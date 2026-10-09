import copy,gzip,json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
NATIVE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(NATIVE))
from nullgenesis.renderer import Renderer
from nullgenesis.export import export_edition
from nullgenesis.codec import decrypt
class ExportV45(unittest.TestCase):
 def test_protected_square_export_resume_and_video(self):
  with gzip.open(NATIVE.parent/'dist/v45/experiments/E025.json.gz','rt',encoding='utf-8') as s:g=json.load(s)['genome']
  key=bytes(range(32))
  with Renderer('cuda') as renderer,tempfile.TemporaryDirectory(prefix='null-v45-export-') as destination:
   report=export_edition(renderer,g,destination,video=True,key=key,force_protect=True,presentation=300);folder=Path(destination)/str(g.get('edition',0)).zfill(4)
   self.assertEqual(report['version'],'4.5.0');self.assertEqual(report['presentation_size'],[300,300]);self.assertEqual(report['frame_count'],36)
   with Image.open(folder/'preview.png') as im:self.assertEqual(im.size,(300,300))
   self.assertFalse((folder/'cells.npz').exists(),'Protected structural cells must stay sealed')
   envelope=json.loads((folder/'genome.dna.json').read_text());self.assertEqual(decrypt(envelope,key)['genome']['fingerprint'],g['fingerprint'])
   for file in ('quality.json','animation.mp4','animation.webm','animation.html'):self.assertGreater((folder/file).stat().st_size,0)
   metadata=json.loads((folder/'metadata.json').read_text());self.assertEqual(metadata['render_version'],'native-4.5.0')
   self.assertTrue(export_edition(renderer,g,destination,video=True,key=key,force_protect=True,presentation=300)['resumed'])
   with self.assertRaises(ValueError):export_edition(renderer,g,destination,key=key,force_protect=True,presentation=1200)
   with self.assertRaises(Exception):export_edition(renderer,g,destination,key=bytes(reversed(range(32))),force_protect=True,presentation=300)
if __name__=='__main__':unittest.main()
