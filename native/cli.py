"""Render versioned V3 DNA through the local NVIDIA engine."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if (ROOT/'.runtime/deps').is_dir():sys.path.insert(0,str(ROOT/'.runtime/deps'))
from nullgenesis.renderer import Renderer
from nullgenesis.export import export_batch
from nullgenesis.codec import decrypt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['status','generate','animate']);p.add_argument('--backend',choices=['auto','cuda','cpu'],default='cuda');p.add_argument('--device',type=int,default=0);p.add_argument('--input');p.add_argument('--output');p.add_argument('--no-animation',action='store_true');p.add_argument('--video',action='store_true');p.add_argument('--key',help='Explicit local AES-256 key file; never exported');p.add_argument('--no-resume',action='store_true')
    p.add_argument('--presentation',type=int,choices=[300,600,1200],default=600,help='V4.5 square PNG, HTML and video size')
    args=p.parse_args()
    if args.command!='status' and (not args.input or not args.output):p.error('generate/animate requires --input and --output')
    with Renderer(args.backend,args.device) as r:
        if args.command=='status':print(json.dumps(r.status(),indent=2));return
        key=Path(args.key).read_bytes() if args.key else None
        if key is not None and len(key)!=32:raise ValueError('The supplied AES key must be exactly 32 bytes')
        data=json.loads(Path(args.input).read_text(encoding='utf-8'))
        messages={};protected=set()
        if isinstance(data,dict) and data.get('algorithm')=='AES-256-GCM':
            payload=decrypt(data,key);data={'genome':payload['genome']};messages[payload['genome']['fingerprint']]=payload.get('hidden_message','');protected.add(payload['genome']['fingerprint'])
        genomes=data if isinstance(data,list) else data.get('genomes',data.get('items',[data]));genomes=[item.get('genome',item) for item in genomes]
        if args.command=='animate' and args.no_animation:p.error('animate requires deterministic frame output')
        result=export_batch(r,genomes,args.output,not args.no_animation,args.video,key,not args.no_resume,messages,protected,args.presentation)
        print(json.dumps(dict(count=result['count'],backend=result['backend'],output=str(Path(args.output).resolve()),requires_visual_review=True)))
if __name__=='__main__':main()
