"""Authenticated owner-controlled DNA envelopes; no implicit key-file access."""
import base64
import json
import os
import re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .genome import canonical,validate_genome

AAD=b'NULL-GENESIS/structural-envelope/v1'
V3_AAD=b'NULL-GENESIS/web-genome/v3/'

def _key(key):
    if not isinstance(key,bytes) or len(key)!=32:raise ValueError('A caller-supplied 32-byte AES-256 key is required')
    return key

def encrypt(genome,key,message=''):
    validate_genome(genome);key=_key(key);nonce=os.urandom(12)
    if genome['genome_version']=='web-3.0.0':
        aad=V3_AAD+genome['fingerprint'].encode('ascii')
        envelope=dict(version=3,algorithm='AES-256-GCM',genome_version=genome['genome_version'],fingerprint=genome['fingerprint'])
    else:
        edition=int(genome.get('edition',0));aad=AAD+b'/'+str(edition).encode()
        envelope=dict(version=1,algorithm='AES-256-GCM',edition=edition,key_location='Owner-controlled local key; excluded from exports')
    payload=canonical(dict(genome=genome,identity=genome['fingerprint'],hidden_message=message))
    ciphertext=AESGCM(key).encrypt(nonce,payload,aad)
    return {**envelope,'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(ciphertext).decode(),'aad':base64.b64encode(aad).decode()}

def decrypt(envelope,key):
    key=_key(key)
    if not isinstance(envelope,dict) or envelope.get('algorithm')!='AES-256-GCM':raise ValueError('Unsupported DNA envelope')
    if envelope.get('version')==3:
        identity=envelope.get('fingerprint')
        if envelope.get('genome_version')!='web-3.0.0' or not isinstance(identity,str) or not re.fullmatch('[0-9a-f]{64}',identity):raise ValueError('Invalid V3 DNA identity')
        aad=V3_AAD+identity.encode('ascii')
    elif envelope.get('version')==1:
        edition=envelope.get('edition')
        if isinstance(edition,bool) or not isinstance(edition,int) or edition<0:raise ValueError('Invalid legacy DNA edition')
        aad=AAD+b'/'+str(edition).encode('ascii')
    else:raise ValueError('Unsupported DNA envelope')
    if any(not isinstance(envelope.get(k),str) for k in ('aad','nonce','ciphertext')) or len(envelope['ciphertext'])>1000000:raise ValueError('Invalid DNA encoding')
    supplied=base64.b64decode(envelope['aad'],validate=True);nonce=base64.b64decode(envelope['nonce'],validate=True);ciphertext=base64.b64decode(envelope['ciphertext'],validate=True)
    if supplied!=aad or len(nonce)!=12:raise ValueError('Invalid authenticated DNA identity')
    payload=json.loads(AESGCM(key).decrypt(nonce,ciphertext,aad));g=validate_genome(payload['genome'])
    if payload['identity']!=g['fingerprint']:raise ValueError('Decrypted identity mismatch')
    if envelope['version']==3:
        if g['genome_version']!='web-3.0.0' or g['fingerprint']!=identity:raise ValueError('Decrypted V3 identity mismatch')
    elif int(g.get('edition',0))!=edition:raise ValueError('Decrypted legacy identity mismatch')
    return payload
