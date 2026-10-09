"""Native AES and actual Studio WebCrypto interoperability; synthetic key only."""
import base64,gzip,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'native'))
from nullgenesis.codec import encrypt,decrypt
from nullgenesis.genome import seal

def main():
    with gzip.open(ROOT/'dist/v45/experiments/E036.json.gz','rt',encoding='utf-8') as stream:g=json.load(stream)['genome']
    g['encryption']='AES-256-GCM';g=seal(g);key=bytes(range(32));envelope=encrypt(g,key,'native synthetic message')
    node=shutil.which('node') or 'C:/Program Files/nodejs/node.exe'
    result=subprocess.run([node,str(ROOT/'native/tools/crypto_bridge_v45.mjs')],input=json.dumps(dict(genome=g,key=list(key),envelope=envelope)),text=True,capture_output=True,check=True)
    browser=json.loads(result.stdout);payload=decrypt(browser['browserEnvelope'],key)
    assert payload['genome']==g and payload['hidden_message']=='browser synthetic message' and browser['fingerprint']==g['fingerprint']
    rejected=0
    for forged in [{**envelope,'fingerprint':'f'*64},{**envelope,'version':3},
                   {**envelope,'nonce':base64.b64encode(bytes(11)).decode()},
                   {**envelope,'aad':base64.b64encode(b'bad').decode()},
                   {**envelope,'ciphertext':envelope['ciphertext'][:-4]+'AAAA'}]:
        try:decrypt(forged,key)
        except Exception:rejected+=1
    assert rejected==5 and browser['rejected']==5 and browser['wrongKeyRejected']
    report=dict(passed=True,version='4.5.0',native_to_studio=True,studio_to_native=True,
                fingerprint_preserved=True,hidden_message_preserved=True,native_tamper_cases_rejected=5,
                studio_tamper_cases_rejected=5,studio_wrong_key_rejected=True,
                key_source='Known synthetic test bytes; actual owner keys were not read')
    (ROOT/'dist/v45/reports/crypto-interop.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
