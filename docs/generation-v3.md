NULL GENESIS V3 uses the installed NVIDIA GPU for procedural pose transforms,
SDF ray marching, lighting, ASCII selection, depth projection and glyph raster
generation. Video compression uses FFmpeg software codecs on the CPU. The
CUDA renderer reports actual device, kernel timing, memory and allocation data.

The original 3,333-piece collection remains an immutable archive. The new
candidate collection writes only to `dist/v3/collection`. No source-family quota
is applied; source-library usage counts overlapping genetic influences. The five
rarity supplies remain 1,900 Common, 900 Uncommon, 400 Rare, 110 Epic and 23
Legendary. Curated vocabulary and executable recipes are separate registries.

Run from the repository root with Python dependencies installed as described in
the native README. First prepare Node genomes using the real native font atlas:

```powershell
python native/tools/calibrate.py --output native/work/calibration.json
node scripts/build-v3-registry.mjs
node scripts/prepare-v3.mjs mode=experiments calibration=native/work/calibration.json
python native/generate_v3.py --mode experiments --genomes native/work/experimental-genomes.json --output dist/v3
```

Inspect all six contact sheets in `dist/v3/reports/contact-sheets`. Each tile
compares the archived PNG, native 30×30 and native 50×50. This initial run measures
three actual GPU poses per candidate and does not claim full animation validation.
The experiment report records measurable quality, depth, silhouette, native timing
and the proposed resolution. Numeric quality is a proxy; visual review is required.

After visual acceptance, produce all experiment timelines and prepare the release:

```powershell
python native/generate_v3.py --mode experiments --genomes native/work/experimental-genomes.json --output dist/v3 --animations
node scripts/prepare-v3.mjs mode=collection calibration=native/work/calibration.json
python native/generate_v3.py --mode collection --genomes native/work/collection-genomes.json --output dist/v3 --approve-experiments --canonical-grid 50
```

`--approve-experiments` records the operator's completed visual review; it must not
be used before that review. A different resolution requires fresh exports. The
renderer uses bounded reusable CUDA batches and complete ray-marched timelines.
Common, Uncommon, Rare, Epic and Legendary loops last 3, 4, 6, 8 and 12 seconds at
12 fps. All 23 existing Legendary names and reconstruction identities are retained.
Frames are losslessly packed into alternating printable-ASCII and grayscale bytes
and gzip-compressed. Frame zero must equal the accepted canonical art; an actual
repeated endpoint and preceding wrap frame are checked. Nonmoving pieces fail.

Finite deterministic quality repairs record seed, actions, prior and updated
scores and fingerprints. The duplicate index checks exact ASCII, genome, geometry,
coarse silhouette, grayscale, glyph histogram, perceptual hash and temporal pose
signatures. Exhausted repairs stop generation. Completed editions are checkpointed
only after media hashes and animation validation pass. Resume checks manifest
identity and output checksums. Partially generated editions never count as complete.

Protected release genomes use AES-256-GCM with a fresh nonce and authenticated
fingerprint context. A new release key is created only at
`native/private/v3-owner.key`. It is never included in public records, videos or
ZIPs. Original owner keys are never accessed. Protected plaintext checkpoints live
only in ignored `native/work`; public protected records contain the authenticated
envelope, public metadata, ASCII and playable animation. Experimental specimens
deliberately publish reproducible unencrypted DNA and do not claim secrecy.

Every edition has native animated HTML playback, compact frames, a PNG, metadata
and a DNA file. All 23 Legendary editions also have standard MP4 and WebM files.
Other videos can be generated on demand through `native/cli.py animate --video`.
Public ZIP parts include self-contained HTML playback and omit private keys.

After generation, independently audit and build actual 530-value usage analytics:

```powershell
python native/validate_v3.py dist/v3/collection --report dist/v3/reports/collection-audit.json --analytics dist/v3/reports/analytics.json
python native/report_v3.py dist/v3/collection --output dist/v3/reports/production-contact-sheets --count 100
```

The audit verifies exact supply, ordered eleven-category attributes, actual source
reachability, ranked editions, canonical hashes, grid dimensions, grayscale media,
envelope fields, all timeline lengths, motion/loop evidence and Legendary video
presence. Analytics count accepted public source, modifier and category IDs;
relationships are observed co-occurrences and do not invent causal connections.
The audit preserves measured timing and visual-review fields in an existing report.

The separate production report selects 100 accepted editions across all five
rarities, including every Legendary identity, and shows canonical, quarter-loop
and half-loop views from their original public GPU timelines. Selection favors
actual source, trait and motion variety. CUDA rasterizes the stored glyphs; Pillow
only composes labeled sheets. This read-only report never decrypts DNA or changes
the collection's artwork, rankings, supply or acceptance.

Publishing the studio or exporting metadata does not mint NFTs. Vercel runs the
browser WebGPU/CPU preview; Windows NVIDIA rendering requires the local CUDA bridge.

