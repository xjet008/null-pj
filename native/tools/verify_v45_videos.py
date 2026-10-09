"""Decode every Legendary video and verify frame counts, size, timing and still fidelity."""
import json,sys,time
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];PUBLIC=ROOT/'dist/v45/collection'

def verify_video(metadata,extension,root=PUBLIC):
    identifier=f"{metadata['edition']:04}";path=root/'animations'/(identifier+'.'+extension)
    with Image.open(root/'previews'/(identifier+'.png')) as image:canonical=np.asarray(image,dtype=np.float32)
    frames=imageio_ffmpeg.read_frames(str(path));info=next(frames);count=0;first_error=None
    assert tuple(info['size'])==(600,600) and tuple(info['source_size'])==(600,600)
    assert abs(info['fps']-metadata['animation']['fps'])<.001
    assert abs(info['duration']-metadata['animation']['seconds'])<.09
    try:
        for raw in frames:
            assert len(raw)==600*600*3
            if count==0:
                decoded=np.frombuffer(raw,np.uint8).reshape(600,600,3)
                first_error=float(np.abs(decoded.astype(np.float32)-canonical).mean())
                assert first_error<5,'Lossy first frame differs excessively from CUDA canonical'
            count+=1
    finally:frames.close()
    assert count==metadata['loop_validation']['frame_count']
    return dict(edition=metadata['edition'],format=extension,frames=count,fps=info['fps'],size=[600,600],
                duration=info['duration'],codec=info['codec'],first_frame_mean_absolute_error=round(first_error,5))

def main():
    started=time.perf_counter();release=json.loads((PUBLIC/'release.json').read_text());assert release['complete']
    catalog=json.loads((PUBLIC/'catalog.json').read_text());legends=[m for m in catalog if m['rarity']=='LEGENDARY'];assert len(legends)==23
    results=[]
    for m in legends:
        for extension in ('mp4','webm'):results.append(verify_video(m,extension))
    report=dict(passed=True,version='4.5.0',legendary_editions=23,decoded_videos=len(results),
                decoded_frames=sum(r['frames'] for r in results),presentation=[600,600],
                scope='CPU decoding of every CUDA-rendered video; complete decoded frame count and first-frame PNG comparison',
                seconds=round(time.perf_counter()-started,3),items=results)
    (ROOT/'dist/v45/reports/video-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='items'}),flush=True)

if __name__=='__main__':main()
