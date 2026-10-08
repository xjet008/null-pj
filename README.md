# NULL GENESIS V3

A Windows NVIDIA CUDA art engine and browser ASCII studio. V3 synthesizes grayscale organisms from 300 source concepts, 120 original modifiers and 110 new values across eleven NFT categories: **530 curated values and 1,200 executable fusion recipes**. Recipes are counted separately.

The V3 release contains **3,333 animated editions**: 1,900 Common, 900 Uncommon, 400 Rare, 110 Epic and 23 Legendary. Its canonical **50 × 50** grid was selected after 120 matched 30 × 30 / 50 × 50 NVIDIA experiments. Both native grids remain in the laboratory. Concepts influence geometry without fixed output-family quotas.

The original 30 × 30 collection, its 420 definitions, DNA, 23 Legendary identities, animation and exports remain available through **Collection release**. V3 uses a separate directory and versioned DNA.

## Windows NVIDIA studio

From the repository root:

```powershell
.\native\launch.ps1 -Backend cuda
```

The launcher uses Python 3.12+ x64, installs pinned dependencies into ignored native/.runtime/deps if needed, initializes CUDA and opens **http://127.0.0.1:4177/**. An NVIDIA driver is required; NVRTC comes with the dependencies. Keep the launcher open. Options include -Python, -Dependencies, -Port and -Device. Explicit CUDA failures are reported; -Backend auto permits the measured CPU fallback.

CUDA computes SDF geometry, smooth CSG, anatomical motion, grayscale lighting, ambient occlusion, shadows, contour-aware glyphs, fragment depth resolution and glyph rasterization. CPU code handles JSON, encryption, PNG compression and video encoding. Video encoding is not presented as CUDA or NVENC.

The renderer reuses bounded buffers on a 4 GB Quadro T1000. Cached rotations and conservative SDF bounds were accepted after exact output comparisons and 491,520 CUDA field probes. Measured reports are in native/reports/. See [native instructions](native/README.md) for APIs, exports and tests.

## GitHub and Vercel preview

Import **xjet008/null-pj** into Vercel. Leave the root directory at the repository root. vercel.json selects **Other**, validates both releases with **node scripts/validate.mjs**, and serves **dist/**. No npm installation, environment variables or owner keys are required.

The hosted laboratory uses browser WebGPU compute, with a background CPU reference worker as fallback. Vercel serves the precomputed CUDA collection; Windows CUDA remains local. Browser previews can differ from canonical CUDA files because of floating-point arithmetic and font calibration. The interface reports its actual backend.

For browser development, run **npm test**, **npm run build**, then **npm run dev**. Open **http://127.0.0.1:4176/**. WebGPU and WebCrypto require HTTPS or localhost.

## Artwork and DNA

Eight views cover dashboard, laboratory, DNA inspector, animation, collection, analytics, NFT traits and experimental comparisons. Controls include both native grids, up to eight source influences, ten fusion operators, eleven categories, nine rendering profiles, ten appearance modes, motion intensity and grayscale diagnostics.

Traits execute geometry, rendering or motion. Incompatible choices receive deterministic compatible replacements; provenance records requested and executed traits. Detail budgets, finite quality repairs and visual/temporal uniqueness checks run before acceptance. Rankings use observed collection frequencies.

Every rarity has deterministic anatomical motion. The 23 Legendary identities retain named formation, destruction and reassembly sequences. Every edition includes canonical ASCII, grayscale PNG, authenticated DNA and a compressed native timeline. Legendary MP4/WebM are included. Collection ZIP parts contain self-contained animated HTML. Other videos can be generated on demand:

```text
python native/cli.py animate --input genome.dna.json --output native/generated/my-export --backend cuda --video
```

For encrypted DNA, add --key with its explicit local 32-byte key file. Keys stay local and are excluded from Git, records and archives. Browser keys remain in memory and are never uploaded. Protected V3 records omit plaintext scene and configuration. Cipher-looking art and AES-256-GCM protection are distinct.

Original DNA retains its version and fingerprint. Import or regenerate it directly. Create V3 descendants through the V3 laboratory; new fingerprints and provenance identify new artwork while the original remains accessible.

## Reproduction and validation

Keep prepared protected genomes and checkpoints in ignored native/work/. Supply the actual local font calibration rather than inventing glyph coverage. In a fresh PowerShell terminal, use the same Python executable configured in the launcher and explicitly set PYTHONPATH to native/.runtime/deps; the launcher environment does not carry into another terminal. If you passed -Python or -Dependencies, use those exact paths below. A local packaged launcher can reuse an existing neighboring runtime through -Dependencies; runtime libraries remain excluded from Git.

```powershell
$nullPython=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if(-not (Test-Path -LiteralPath $nullPython)){$nullPython=(Get-Command python).Source}
$env:PYTHONPATH=Join-Path (Get-Location) 'native\.runtime\deps'
& $nullPython native/tools/calibrate.py --output native/work/calibration.json
node scripts/prepare-v3.mjs mode=experiments calibration=native/work/calibration.json
& $nullPython native/generate_v3.py --mode experiments --genomes native/work/experimental-genomes.json --output dist/v3 --animations
node scripts/prepare-v3.mjs mode=collection calibration=native/work/calibration.json
& $nullPython native/generate_v3.py --mode collection --genomes native/work/collection-genomes.json --output dist/v3 --approve-experiments --canonical-grid 50
& $nullPython native/validate_v3.py dist/v3/collection
node scripts/validate.mjs --report
```

Inspect all paired contact sheets before approving a new release. Resume verifies candidate fingerprints and artifact hashes. The generator refuses writes into the original collection. V3 becomes selectable only after all 3,333 editions and their timelines pass the audit.

Build validation checks both releases, rarity supply, eleven ordered attributes, canonical hashes, native frame bytes, authenticated envelope structure, all 23 Legendary media sets and complete ZIP CRCs. Native tests verify CUDA/CPU fallback, all motions, synthetic-key authentication, exact GPU batch equality and buffer reuse. Contact sheets and release reports live in dist/v3/reports/.

The artwork is procedural; marketplace character images are not copied. Wallets, accounts and minting contracts are outside this engine.

