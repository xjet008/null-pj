"""Verify native video exports, resume and encrypted DNA using a synthetic key."""
import json
import copy
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from test_native import fixture
from nullgenesis.renderer import Renderer
from nullgenesis.genome import seal
from nullgenesis.codec import decrypt
from nullgenesis.codec import encrypt
from nullgenesis.export import export_batch
def main():
    t=time.perf_counter()
    with Renderer('cuda') as r:
        g=fixture(r.coverage,30,9,'COMMON');g['animation']['seconds']=2;g['edition']=99901;g['encryption']='AES-256-GCM';g=seal(g);key=bytes(range(32))
        with tempfile.TemporaryDirectory(prefix='native-export-check-',dir=ROOT/'work') as path:
            result=export_batch(r,[g],path,animation=True,video=True,key=key);folder=Path(path)/'99901';envelope=json.loads((folder/'genome.dna.json').read_text(encoding='utf-8'));decoded=decrypt(envelope,key)['genome']
            if not np.array_equal(r.render(g)['packet'],r.render(decoded)['packet']):raise AssertionError('Encrypted DNA reconstruction changed canonical art')
            resumed=export_batch(r,[g],path,animation=True,video=True,key=key)
            record=result['editions'][0];needed={'preview.png','ascii.txt','cells.npz','genome.dna.json','metadata.json','animation.frames.json.gz','animation.html','animation.mp4','animation.webm'}
            if not needed<=record['files'].keys() or record['frame_count']!=24 or not resumed['editions'][0]['resumed']:raise AssertionError('Missing/invalid/resume export')
            if any(p.suffix=='.key' for p in Path(path).rglob('*')):raise AssertionError('A key entered the export')
            report=dict(version='3.0.0',device=r.status()['device'],backend=r.backend,frames=24,grid=[30,30],exports=sorted(needed),resumed=True,envelope_version=envelope['version'],protected_browser_genome=True,encrypted_dna_reconstruction=True,private_key_exported=False,mp4_bytes=(folder/'animation.mp4').stat().st_size,webm_bytes=(folder/'animation.webm').stat().st_size,key_source='Synthetic test-only bytes; existing owner keys were not accessed')
        # Exercise the user's on-demand entry point, including an envelope whose
        # plaintext flag says NONE. The envelope still stays protected on export.
        with tempfile.TemporaryDirectory(prefix='native-cli-check-',dir=ROOT/'work') as path:
            test_root=Path(path);source=copy.deepcopy(g);source['edition']=99902;source['encryption']='NONE';source=seal(source)
            (test_root/'synthetic-test.key').write_bytes(key)
            (test_root/'input.dna.json').write_text(json.dumps(encrypt(source,key,'retained synthetic message')),encoding='utf-8')
            completed=subprocess.run([sys.executable,str(ROOT/'cli.py'),'animate','--backend','cuda','--input',str(test_root/'input.dna.json'),'--output',str(test_root/'export'),'--key',str(test_root/'synthetic-test.key'),'--video'],capture_output=True,text=True,check=True)
            cli_folder=test_root/'export/99902';cli_marker=json.loads((cli_folder/'complete.json').read_text(encoding='utf-8'));cli_envelope=json.loads((cli_folder/'genome.dna.json').read_text(encoding='utf-8'));payload=decrypt(cli_envelope,key)
            if not needed<=cli_marker['files'].keys() or payload['genome']!=source or payload.get('hidden_message')!='retained synthetic message' or list((test_root/'export').rglob('*.key')):raise AssertionError('Native CLI changed protected DNA/message or omitted media')
            report.update(on_demand_cli=True,encrypted_input_stays_protected=True,cli_hidden_message_preserved=True,cli_mp4_bytes=(cli_folder/'animation.mp4').stat().st_size,cli_webm_bytes=(cli_folder/'animation.webm').stat().st_size)
        report['wall_seconds']=round(time.perf_counter()-t,3)
    (ROOT/'reports/native-export-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
