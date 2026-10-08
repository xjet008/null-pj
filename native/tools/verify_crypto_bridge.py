"""Synthetic Python AES ↔ actual Studio WebCrypto interoperability checks."""
import base64
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from test_native import fixture
from nullgenesis.genome import seal,validate_genome
from nullgenesis.codec import encrypt,decrypt

def main():
    node=shutil.which('node')
    if not node:raise RuntimeError('Node.js is required for the actual Studio WebCrypto check')
    g=fixture([.1]*95);g['encryption']='AES-256-GCM';g=seal(g);key=bytes(range(32));envelope=encrypt(g,key,'synthetic hidden message')
    result=subprocess.run([node,str(ROOT/'tools/crypto_bridge.mjs')],input=json.dumps(dict(genome=g,key=list(key),envelope=envelope)),text=True,capture_output=True,check=True)
    browser=json.loads(result.stdout);decoded=decrypt(browser['browserEnvelope'],key)
    if decoded['genome']!=g or browser['unlockedFingerprint']!=g['fingerprint']:raise AssertionError('Cross-language DNA identity mismatch')
    if decoded.get('hidden_message')!='browser synthetic message':raise AssertionError('Studio hidden message changed after native decryption')
    if decrypt(envelope,key)['hidden_message']!='synthetic hidden message':raise AssertionError('Native hidden message changed')
    legacy=copy.deepcopy(g);legacy['genome_version']='web-1.0.0';legacy['animation']['seconds']=8;legacy=seal(legacy);old=encrypt(legacy,key)
    if old['version']!=1 or base64.b64decode(old['aad'])!=b'NULL-GENESIS/structural-envelope/v1/10001' or decrypt(old,key)['genome']!=legacy:raise AssertionError('Legacy V1 DNA/AAD changed')
    rejected=0
    for field,value in [('fingerprint','f'*64),('nonce',base64.b64encode(bytes(11)).decode()),('aad',base64.b64encode(b'bad').decode()),('ciphertext',envelope['ciphertext'][:-4]+'AAAA')]:
        forged={**envelope,field:value}
        try:decrypt(forged,key)
        except Exception:rejected+=1
    if rejected!=4:raise AssertionError('Forged native V3 envelope accepted')
    report=dict(version='3.0.0',python_to_studio=True,studio_to_python=True,fingerprint_preserved=True,legacy_version_1_preserved=True,legacy_aad_preserved=True,synthetic_hidden_message_preserved=True,studio_hidden_message_preserved=True,tamper_cases_rejected=rejected,studio_forged_identity_rejected=browser['forgedRejected'],key_source='Synthetic test-only bytes; existing owner keys were not accessed')
    (ROOT/'reports/dna-webcrypto-interop.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
