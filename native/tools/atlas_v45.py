import sys,base64,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nullgenesis.renderer import calibration
atlas,coverage,font=calibration();out=Path(__file__).resolve().parents[2]/'dist/data/glyph-atlas-v45.json';out.write_text(json.dumps(dict(version='4.5.0',cell=[atlas.shape[2],atlas.shape[1]],font=font,pixels=base64.b64encode(atlas.tobytes()).decode(),coverage=coverage.tolist()),separators=(',',':')),encoding='utf-8');print('Saved measured 95-glyph atlas')
