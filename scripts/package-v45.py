"""Copy audited source/public assets into a clean local distribution, without keys."""
import argparse,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','.runtime','private','work','generated','__pycache__','node_modules','.openai','.vercel'}

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
    return digest.hexdigest()

def public_files():
    for name in ('.gitattributes','.gitignore','package.json','README.md','vercel.json'):
        yield ROOT/name
    for folder in ('dist','docs','native','scripts','tests'):
        for path in sorted((ROOT/folder).rglob('*')):
            rel=path.relative_to(ROOT)
            if set(rel.parts)&EXCLUDED or path.suffix in ('.key','.pyc','.pyo','.log','.tmp') or path.name.startswith('.env'):continue
            if path.is_symlink():raise ValueError('Distribution cannot contain a symlink: '+str(rel))
            if path.is_file():yield path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();destination=args.output.resolve()
    if destination==ROOT or ROOT in destination.parents or destination in ROOT.parents:
        raise ValueError('Choose a separate distribution directory')
    audit=json.loads((ROOT/'dist/v45/reports/collection-audit.json').read_text())
    build=json.loads((ROOT/'dist/reports/web-data-checks.json').read_text())
    assert audit['passed'] and audit['visual_review_approved'] and audit['editions']==3333
    assert build['passed'] and build['v45']['passed'] and build['v45']['editions']==3333
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Choose an empty output directory; existing files will not be overwritten')
    destination.mkdir(parents=True,exist_ok=True)
    entries=[]
    for source in public_files():
        rel=source.relative_to(ROOT);target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        digest=sha(source)
        if sha(target)!=digest:raise ValueError('Copy integrity failure: '+str(rel))
        entries.append(dict(path=rel.as_posix(),bytes=target.stat().st_size,sha256=digest))
    launcher=destination/'Launch-V4.5.ps1'
    launcher.write_text('''param([int]$Port=4181,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
$nullDependencies=Join-Path $PSScriptRoot '..\\null-genesis\\.runtime\\deps'
$nullOptions=@{Port=$Port;Backend='cuda'}
if(Test-Path -LiteralPath $nullDependencies){$nullOptions.Dependencies=(Resolve-Path -LiteralPath $nullDependencies).Path}
if($NoBrowser){$nullOptions.NoBrowser=$true}
& (Join-Path $PSScriptRoot 'native\\launch.ps1') @nullOptions
''',encoding='utf-8')
    start=destination/'START-HERE.md'
    start.write_text('''# NULL GENESIS V4.5

Run `Launch-V4.5.ps1` in PowerShell, then open **http://127.0.0.1:4181/**. Keep
the launcher running. It reuses the neighboring original package's Python
dependencies when available; otherwise the native launcher installs its pinned
dependencies into this package's isolated runtime. An NVIDIA driver is required.

The accepted release contains 3,333 animated grayscale ASCII editions, 742
curated values and 2,400 executable recipes. All release editions use 80×80
native cells with 600×600 CUDA presentations. The laboratory also supports
30, 50, 64, 96 and 120 cell grids and 300/600/1200 square exports.

Choose Original, V3 or V4.5 through **Collection release**. Collection ZIP parts
include ASCII, PNG, portable animation HTML, lossless frames, metadata, quality
records and DNA. All 23 Legendary editions additionally include MP4 and WebM.
Other videos are available through the studio or native CLI.
Extract all ZIP parts into the same folder; large Legendary video bundles can
span parts, as listed in the archive index.

The separate `null-genesis-v45-owner.key` beside this package unlocks protected
V4.5 DNA. Load it in **DNA Inspector → Load owner key**. Keep a private backup.
Original and V3 DNA still require their separate earlier keys. Keys are excluded
from this package, GitHub, hosted assets and NFT archives.

The local studio uses CUDA for geometry, shading, ASCII encoding, animation
frames and presentation. CPU code compresses files and videos. Public web
hosting plays the saved CUDA collection and uses browser WebGPU/CPU for live
previews. See `docs/V45.md` for measured benchmarks and implementation details.

Local audits: `dist/v45/reports/collection-audit.json`,
`dist/v45/reports/production-visual-review.json`, and
`dist/reports/web-data-checks.json`. `PACKAGE-MANIFEST.json` records hashes of
every copied file. Private checkpoints, keys and runtime dependencies are omitted.

For GitHub/Vercel, import xjet008/null-pj with the repository root selected.
The existing vercel.json validates all three releases and serves dist/.
''',encoding='utf-8')
    for path in (launcher,start):entries.append(dict(path=path.name,bytes=path.stat().st_size,sha256=sha(path)))
    manifest=dict(version='4.5.0',passed=True,source_files=len(entries),bytes=sum(e['bytes'] for e in entries),
                  owner_keys_included=False,private_checkpoints_included=False,files=entries)
    (destination/'PACKAGE-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'}),flush=True)

if __name__=='__main__':main()
