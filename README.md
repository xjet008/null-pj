# NULL GENESIS

A grayscale ASCII art studio with a complete 3,333-edition collection, browser GPU generation, trait rankings, DNA inspection and 23 animated editions.

Every artwork has exactly **30 × 30 ASCII cells**. The collection contains 1,111 SKULLS, 1,111 CHARACTERS and 1,111 ANIMALS, with 420 curated style and modifier values.

## Deploy on Vercel

1. Import **xjet008/null-pj** from GitHub into Vercel.
2. Keep the root directory at the repository root.
3. Deploy. The included vercel.json selects **Other**, runs **node scripts/validate.mjs**, and serves **dist/**. No package installation or environment variables are required.

The build checks all 3,333 canonical hashes, native grid dimensions, family and rarity quotas, encrypted envelopes, and all 2,208 animation frames before deployment. Collection data and native animation frames use lossless gzip JSON; the browser decodes these files locally.

Use Vercel's **GitHub import** for this complete asset collection. The checked-in static assets occupy approximately 240 MB. Vercel documents a 100 MB Hobby source-upload limit specifically for CLI deployments, so uploading this repository with `vercel` CLI is not the recommended route. See [Vercel deployment limits](https://vercel.com/docs/limits#static-file-uploads).

Vercel's website access settings control who can visit the deployed studio. The repository itself does not implement account login, wallets or minting contracts.

## Local development

Requires Node.js 22 or newer. There are no npm dependencies.

    npm run build
    npm test
    npm run dev

Open http://127.0.0.1:4176/. WebGPU and WebCrypto require HTTPS or localhost.

## Rendering

New laboratory artwork runs in the visitor's browser. WebGPU compute performs 3D SDF ray marching, lighting, ASCII glyph selection, surface-fragment projection, depth resolution and preview rasterization. A background CPU worker is the fallback.

The archived collection preserves the original **NVIDIA CUDA** artwork. Vercel does not run the Windows CUDA engine. Original editions keep their canonical ASCII records; browser previews can differ across devices because of floating-point arithmetic and installed fonts.

Browser DNA uses web-1.0.0, a SHA-256 fingerprint and explicit scene, render configuration, glyph grammar, coverage and motion parameters. Generating laboratory artwork does not consume collection supply.

## DNA and exports

Original AES-256-GCM envelopes remain encrypted. The owner key is excluded from this repository and every export. Loading a key in DNA Inspector uses browser WebCrypto; it stays in browser memory and is never uploaded. Decoding protected original DNA requires its matching published envelope and owner key.

Collection Explorer exports single or selected editions and provides seven complete collection ZIP parts. Each part contains canonical ASCII, PNG, metadata, mathematical geometry and DNA. Animation Studio exports interactive HTML, native frames, WebM and MP4 for archived animated editions. For new browser artwork, video formats depend on the browser's MediaRecorder support.

## Layout

- dist/index.html, style.css, app.js: responsive six-section studio.
- dist/engine.js, renderer.wgsl: browser GPU compute and rasterization.
- dist/math.js, cpu-worker.js: deterministic CPU renderer and motion reference.
- dist/store.js: collection loading, procedural variation, DNA integrity and local decryption.
- dist/zip.js: selected-edition ZIP exports.
- dist/data: catalog, registry, config and 34 compressed canonical record blocks.
- dist/collection: 3,333 PNGs and 23 animation sets.
- dist/exports: seven complete downloadable collection parts.
- dist/reports: collection audit and validation results.
- scripts/validate.mjs: deployment validation.
- tests: renderer, DNA, encryption and archive checks.

The included assets are original procedural artwork. No marketplace character images are copied into the collection.
