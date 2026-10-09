# NULL GENESIS V4.5

A Windows NVIDIA CUDA art engine and browser ASCII studio. V4.5 synthesizes grayscale organisms from 300 source concepts, 120 original modifiers and 322 NFT values across eleven categories: **742 curated values and 2,400 executable fusion recipes**. Recipes are counted separately. The complete original and V3 vocabularies remain intact.

The V4.5 release contains **3,333 animated editions**: 1,900 Common, 900 Uncommon, 400 Rare, 110 Epic and 23 Legendary. Its canonical **80 × 80** grid was selected after 200 NVIDIA experiments across six native resolutions. Standard previews are **600 × 600** pixels; exports support 300, 600 and 1200 square pixels. Concepts influence geometry without fixed output-family quotas.

The original 30 × 30 and V3 50 × 50 releases, their DNA, Legendary identities, animations and exports remain available through **Collection release**. V4.5 writes to a separate directory and uses versioned DNA. See [V4.5 architecture and regeneration](docs/V45.md) for the composition, encoder, quality and validation pipeline.

## Windows NVIDIA studio

From the repository root:

```powershell
.\native\launch.ps1 -Backend cuda -Port 4178
```

The launcher uses Python 3.12+ x64, installs pinned dependencies into ignored native/.runtime/deps if needed, initializes CUDA and opens **http://127.0.0.1:4178/** with this command. An NVIDIA driver is required; NVRTC comes with the dependencies. Keep the launcher open. Options include -Python, -Dependencies, -Port and -Device. V4.5 canonical generation requires CUDA; the preserved reference backend supports older DNA.

CUDA computes SDF geometry, smooth CSG, anatomical motion, grayscale lighting, ambient occlusion, shadows, depth and curvature probes, calibrated multi-factor glyph encoding, fragment depth resolution and square glyph rasterization. CPU code handles JSON, encryption, PNG compression and video encoding. MP4/WebM use FFmpeg software codecs.

The renderer reuses bounded buffers on a 4 GB Quadro T1000. Cached rotations and conservative SDF bounds were accepted after exact output comparisons and 491,520 CUDA field probes. Measured reports are in native/reports/. See [native instructions](native/README.md) for APIs, exports and tests.

## GitHub and Vercel preview

Import **xjet008/null-pj** into Vercel. Leave the root directory at the repository root. vercel.json selects **Other**, validates all three releases with **node scripts/validate.mjs**, and serves **dist/**. No npm installation, environment variables or owner keys are required. The repository includes extensive animation and export assets; hosting acceptance depends on the selected plan's current limits.

The hosted laboratory uses browser WebGPU compute, with a background CPU reference worker as fallback. Vercel serves the precomputed CUDA collection; Windows CUDA remains local. Browser previews can differ from canonical CUDA files because of floating-point arithmetic and font calibration. The interface reports its actual backend.

For browser development, run **npm test**, **npm run build**, then **npm run dev**. Open **http://127.0.0.1:4176/**. WebGPU and WebCrypto require HTTPS or localhost.

## Artwork and DNA

Eight views cover dashboard, laboratory, DNA inspector, animation, collection, analytics, NFT traits and experimental comparisons. V4.5 controls include six native grids, eight framing modes, three square presentation sizes, up to eight source influences, ten fusion operators, eleven categories, nine rendering profiles, ten appearance modes, motion intensity and grayscale diagnostics.

Traits execute geometry, rendering or motion. Incompatible choices receive deterministic compatible replacements; provenance records requested and executed traits. Detail budgets, finite quality repairs and visual/temporal uniqueness checks run before acceptance. Rankings use observed collection frequencies.

Every rarity has deterministic anatomical motion. The 23 Legendary identities retain named formation, destruction and reassembly sequences. Every edition includes canonical ASCII, grayscale PNG, authenticated DNA and a compressed native timeline. Legendary MP4/WebM are included. Collection ZIP parts contain self-contained animated HTML. Other videos can be generated on demand:

```text
python native/cli.py animate --input genome.dna.json --output native/generated/my-export --backend cuda --video
```

For encrypted DNA, add --key with its explicit local 32-byte key file. Keys stay local and are excluded from Git, records and archives. Browser keys remain in memory and are never uploaded. Protected V3 records omit plaintext scene and configuration. Cipher-looking art and AES-256-GCM protection are distinct.

Original DNA retains its version and fingerprint. Import or regenerate it directly, or create V4.5 descendants with recorded parent provenance. A new V4.5 owner key protects the new release; original and V3 keys remain separate. Keys are excluded from Git and public archives.

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

Build validation checks all three releases, rarity supply, eleven ordered attributes, canonical hashes, native frame bytes, authenticated envelope structure, all 23 Legendary media sets and complete ZIP CRCs. V4.5 additionally verifies square dimensions, detailed quality identities, lossless XOR decoding, recipe coverage, review gates and archive/source hashes. Native tests verify CUDA/CPU fallback, all motions, synthetic-key authentication, exact GPU batch equality and buffer reuse. New contact sheets and release reports live in dist/v45/reports/.

The artwork is procedural; marketplace character images are not copied. Wallets, accounts and minting contracts are outside this engine.

