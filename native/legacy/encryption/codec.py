"""Authenticated structural envelopes. Owner keys never enter public metadata."""
import os,json,base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from engine.genome import canonical,validate_genome
AAD=b'NULL-GENESIS/structural-envelope/v1'
def owner_key(root,create=False):
    p=Path(root)/'private/owner.key'
    if not p.exists():
        if not create:raise ValueError('Owner key required. Import your 32-byte owner.key into private/.')
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(os.urandom(32))
    key=p.read_bytes()
    if len(key)!=32:raise ValueError('Owner key must contain exactly 32 bytes')
    return key
def encrypt(g,key,message=''):
    nonce=os.urandom(12);aad=AAD+b'/'+str(g['edition']).encode()
    payload=canonical(dict(genome=g,identity=g['fingerprint'],hidden_message=message))
    ciphertext=AESGCM(key).encrypt(nonce,payload,aad)
    return dict(version=1,algorithm='AES-256-GCM',edition=g['edition'],nonce=base64.b64encode(nonce).decode(),ciphertext=base64.b64encode(ciphertext).decode(),aad=base64.b64encode(aad).decode(),key_location='owner-controlled local key file; excluded from public exports')
def decrypt(envelope,key):
    if envelope.get('algorithm')!='AES-256-GCM' or envelope.get('version')!=1:raise ValueError('Unsupported envelope')
    aad=AAD+b'/'+str(envelope['edition']).encode()
    if base64.b64decode(envelope['aad'],validate=True)!=aad:raise ValueError('Invalid authenticated edition identity')
    data=AESGCM(key).decrypt(base64.b64decode(envelope['nonce'],validate=True),base64.b64decode(envelope['ciphertext'],validate=True),aad)
    payload=json.loads(data);validate_genome(payload['genome'])
    if payload['identity']!=payload['genome']['fingerprint']:raise ValueError('Encrypted identity mismatch')
    return payload
