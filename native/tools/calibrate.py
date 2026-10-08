"""Write the actual local CUDA glyph calibration for deterministic preparation."""
import argparse
import json
import sys
from pathlib import Path
NATIVE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(NATIVE))
from nullgenesis.renderer import Renderer

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default=str(NATIVE/'work'/'calibration.json'))
    parser.add_argument('--device',type=int,default=0)
    args=parser.parse_args()
    with Renderer('cuda',device=args.device) as renderer:
        status=renderer.status()
        if status['backend']!='CUDA' or len(status['coverage'])!=95:
            raise RuntimeError('Verified CUDA calibration is required')
        output=Path(args.output).resolve()
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({key:status[key] for key in ('version','backend','device','font','fontName','coverage')},indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(output=str(output),device=status['device'],glyphs=95)))

if __name__=='__main__':main()
