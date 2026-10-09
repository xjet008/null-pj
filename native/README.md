# NULL GENESIS NVIDIA engine V4.5

V4.5 adds calibrated multi-factor CUDA encoding, subject-only automatic framing,
six native resolutions and square 300/600/1200 presentation. The accepted release
uses 80×80 cells and 600×600 previews. The preserved V3 instructions below remain
available for older DNA. See [V4.5 architecture](../docs/V45.md) for new release tools.
Use `--presentation 300`, `600` or `1200` with `native/cli.py` for V4.5 PNG, HTML
and video exports. Protected exports omit plaintext structural cell archives.

The main Windows studio uses NVIDIA CUDA for SDF surfaces, grayscale lighting, glyph selection, primitive motion, depth-aware Legendary fragments and glyph rasterization. The browser receives native ASCII cell packets and PNG previews. Vercel serves the separate WebGPU/CPU edition; it does not run CUDA.

## Run the local studio

From the repository root:

~~~powershell
.\native\launch.ps1 -Backend cuda
~~~

The launcher installs pinned dependencies into ignored native/.runtime/deps if necessary, initializes the NVIDIA GPU, and serves http://127.0.0.1:4177. Keep it open. Options: -Python, -Dependencies, -Device, -Port, -NoBrowser. CUDA failures are explicit with -Backend cuda; -Backend auto reports the actual CPU fallback.

Python 3.12+ x64, an NVIDIA Windows driver and NVRTC are required. NVRTC comes from requirements.txt or an official CUDA Toolkit exposed through CUDA_PATH. No GPU libraries or keys are committed.

A local packaged copy can reuse an existing neighboring installation with -Dependencies, for example .\native\launch.ps1 -Backend cuda -Dependencies ..\null-genesis\.runtime\deps when that directory exists. The runtime stays in place; it is not copied into Git. New installations use native/.runtime/deps.

Before running exports, preparation tools or tests in a fresh PowerShell terminal, select the same Python interpreter used by the launcher and expose its dependency directory:

~~~powershell
$nullPython=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if(-not (Test-Path -LiteralPath $nullPython)){$nullPython=(Get-Command python).Source}
$env:PYTHONPATH=Join-Path (Get-Location) 'native\.runtime\deps'
~~~

If you supplied -Python, set $nullPython to that exact executable instead. If you supplied -Dependencies, set PYTHONPATH to that directory instead. A fresh terminal does not inherit the launcher's process environment. Run the launcher once to install the pinned dependencies, or install requirements.txt into the selected dependency directory with that same interpreter.

## Native API

nullgenesis.renderer.Renderer('cuda') consumes fingerprint-verified browser V3 DNA: scene rows of 16 floats, 24 configuration values, printable ASCII grammar, 95 glyph coverage values, native grid [30,30] or [50,50], and deterministic motion/animation parameters.

V4.5 DNA additionally requires its encoder, composition, six layer budgets and
square presentation record. Its native grids are 30, 50, 64, 80, 96 and 120.
V4.5 canonical rendering explicitly requires CUDA.

- render(genome,index=0,staticA=-1): actual posed geometry.
- render_batch(genomes): bounded canonical frames.
- render_sequence(genome,indices=None,chunk_size=16): bounded GPU animation batches; DNA is authenticated once and base geometry stays on CUDA.
- frame(base,genome,index,staticA=-1): posed geometry and reconstruction.
- image(result), png(result,scale=1): CUDA glyph rasterization.
- square_image(result,size=600), square_png(result,size=600): V4.5 CUDA square presentation at 300, 600 or 1200 pixels.
- status(): actual device, timings, VRAM, buffer pool, allocations and font calibration.

The result includes native ASCII, grid, glyph and native cells arrays, and a browser packet in this exact order:

~~~text
glyph, gray, normalX, normalY, normalZ, pointX, pointY, pointZ, depth, foreground, objectID, linearLuminance
~~~

GPU and CPU floating-point boundaries can differ. Reconstruction is deterministic for the same engine version, DNA, calibration and backend. The V3 renderer also accepts web-1.0.0 scene genomes. Original native 1.0.0 structural DNA uses the preserved native legacy/ sources or the Studio's archived DNA import/regenerate path. V3 never calls the archived renderer's historical fixed family allocation.

The engine caches sin/cos values for every posed primitive in an internal CUDA row. Public DNA stays unchanged. GPU pipeline timing synchronizes once per chunk, buffers are reused, and the grayscale glyph atlas stays resident.

## Local transport

The server binds to 127.0.0.1. It checks local Host, browser Origin and Fetch-Site, requires JSON, limits requests to 4 MB, verifies DNA, and serializes the CUDA context.

~~~text
GET  /api/v3/status
POST /api/v3/render  {genome}
POST /api/v3/frame   {genome,index,staticA?,preview?}
POST /api/v3/raster  {genome,cells,scale}
POST /api/v3/fit     {genome}                     # V4.5 composition and finite quality repairs
~~~

Render/frame return flat browser cells, actual backend, gpu_ms, render_ms, grid, frame and ASCII hash. Render also returns a PNG preview data URL. Raster returns PNG and wall time. No HTTP key or decryption endpoints exist.

V4.5 render returns a 600-square PNG and measured quality. V4.5 raster accepts
`size` (300, 600 or 1200). Fit returns the accepted fitted genome, its cells,
quality, repair history and square preview; its fingerprint identifies that
final composition.

## Transactional exports

~~~powershell
& $nullPython native/cli.py generate --input genomes.json --output native/generated/experiment --backend cuda
& $nullPython native/cli.py generate --input genomes.json --output native/generated/video --backend cuda --video
& $nullPython native/cli.py animate --input genome.dna.json --output native/generated/on-demand --backend cuda --video
~~~

Input accepts a genome list, {genomes:[...]}, or {items:[{genome:...}]}. Edition IDs must be in the sealed genome. Each edition is staged and atomically renamed only after every requested export succeeds. complete.json records artifact hashes. Resume verifies DNA and every artifact; partial or incompatible editions fail.

Exports include canonical PNG, ASCII, compressed cells, DNA, metadata, compressed animation frames and playable HTML. --video also requires successful MP4 and WebM encoding. Missing media is an error. Bounded GPU batches avoid retaining an entire collection in memory.

Real encryption is independent of cipher-looking artwork. Mark a genome encryption:"AES-256-GCM", protected:true or encryption_mode:"AES-256-GCM" before sealing, then pass an explicit local --key file. The key must be 32 bytes and is never exported. No existing owner key is accessed. Browser V3 DNA uses the same version 3 envelope and fingerprint-bound authentication in the native tool; legacy version 1 edition-bound envelopes remain supported.

The animate command accepts a plain browser genome.dna.json or an AES envelope with an explicit --key path, decrypts locally, checks its identity and fingerprint, then regenerates canonical art and all requested motion media. An encrypted input stays encrypted on export, including its hidden message, without rewriting the genome. Use a new output directory when adding videos or changing protection to a previous export; completed editions are never silently overwritten. A single laboratory DNA without an edition field exports under 0000 and retains its original fingerprint.

The exporter refuses an existing collection directory without its V3 marker. It does not replace the archived 3,333 editions. Experimental output is marked as requiring visual review.

## Verification

~~~powershell
$env:NULL_GENESIS_TEST_BACKEND='cuda'
& $nullPython -m unittest discover -s native/tests -v
& $nullPython native/tools/benchmark.py --input native/work/experimental-genomes.json
& $nullPython native/tools/verify_crypto_bridge.py
~~~

Use NULL_GENESIS_TEST_BACKEND=cpu for the NumPy reference. Tests cover both grids, grayscale rasterization, DNA and authenticated-encryption tampering with a dummy key, all ten motions, five rarities, 23 Legendary identities, deterministic loops, exact batched-versus-individual equality, and stable buffer allocations.

reports/nvidia-v3-benchmark.json contains measured GPU timings. Legacy lighting is simpler, so its timing is not an assertion of equivalent artistic quality. Production resolution and complete regeneration require matched contact-sheet review and a collection audit.
