"""Public V3 production visual report, generated after the frozen release.

This reads accepted public metadata and the original complete CUDA-generated
animation bytes. It never decrypts DNA or alters genomes, artwork, or rankings.
CUDA rerasterizes the stored glyphs for consistent quarter/half-loop views;
Pillow only resizes and composes the labeled report sheets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from validate_v3 import CATEGORIES, QUOTAS, unpack_animation


def select_samples(catalog, count=100):
    """Choose deterministic cross-tier coverage, retaining every Legendary.

    Selection prioritizes unseen real source/category IDs and motion programs;
    quality resolves close choices, then edition resolves exact ties. This is
    only report sampling and cannot affect supply, trait choices, or rarity.
    """
    count = min(int(count), len(catalog))
    if count <= 0:
        raise ValueError('Sample count must be positive')
    by_tier = {tier: sorted((m for m in catalog if m['rarity'] == tier), key=lambda m: m['edition']) for tier in QUOTAS}
    legends = by_tier['LEGENDARY']
    if count < len(legends):
        raise ValueError('Report sample count must include every Legendary edition')
    chosen = list(legends)
    quotas = Counter({'LEGENDARY': len(legends)})
    ordinary = [tier for tier in QUOTAS if tier != 'LEGENDARY' and by_tier[tier]]
    remaining = count - len(chosen)
    # Balanced report exposure intentionally differs from collection supply.
    while remaining:
        eligible = [tier for tier in ordinary if quotas[tier] < len(by_tier[tier])]
        if not eligible:
            raise ValueError('Insufficient samples across the registered rarity tiers')
        tier = min(eligible, key=lambda t: (quotas[t], ordinary.index(t)))
        quotas[tier] += 1
        remaining -= 1
    usage = Counter(t for m in chosen for t in m['traits'])
    motion_usage = Counter(_motion_key(m) for m in chosen)
    for tier in ordinary:
        candidates = list(by_tier[tier])
        for _ in range(quotas[tier]):
            def key(m):
                ids = set(m['traits'])
                sources = set(m['base_concepts'])
                novelty = sum(1 / (1 + usage[t]) for t in ids) / max(1, len(ids))
                source_novelty = sum(1 / (1 + usage[t]) for t in sources) / max(1, len(sources))
                return (novelty + source_novelty * .6 + .25 / (1 + motion_usage[_motion_key(m)]), m['quality']['quality_score'], -m['edition'])
            picked = max(candidates, key=key)
            candidates.remove(picked)
            chosen.append(picked)
            usage.update(set(picked['traits']))
            motion_usage.update([_motion_key(picked)])
    return sorted(chosen, key=lambda m: (list(QUOTAS).index(m['rarity']), m['edition']))


def _motion_key(metadata):
    motion = metadata['animation'].get('motion', {})
    return (motion.get('kind', motion.get('type')), motion.get('speed'), round(motion.get('amplitude', motion.get('intensity', 0)), 1))


def frame_result(values, grid):
    """Adapt the lossless public glyph/gray frame to the native raster API."""
    glyph = np.ascontiguousarray(values[:, 0], dtype=np.uint8)
    cells = np.zeros((len(glyph), 12), dtype=np.float32)
    cells[:, 0] = values[:, 1]
    return dict(glyph=glyph, cells=cells, grid=list(grid))


def _font(size):
    for path in ('C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/arial.ttf'):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _short(value, length=50):
    text = str(value)
    return text if len(text) <= length else text[:length - 1] + '…'


def production_contact_sheets(root, destination, count=100, renderer=None):
    root, destination = Path(root), Path(destination)
    release_file = root / 'release.json'
    if not release_file.is_file() or not json.loads(release_file.read_text(encoding='utf-8')).get('complete'):
        raise ValueError('Visual report requires a completed production release')
    release = json.loads(release_file.read_text(encoding='utf-8'))
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
    if len(catalog) != 3333 or release.get('canonical_grid') != [50, 50]:
        raise ValueError('Production report requires the complete accepted native 50×50 release')
    selected = select_samples(catalog, count)
    if any([a['trait_type'] for a in m['attributes']] != list(CATEGORIES) for m in selected):
        raise ValueError('Selected metadata lacks the eleven actual ordered categories')
    owned_renderer = renderer is None
    if owned_renderer:
        from nullgenesis.renderer import Renderer
        renderer = Renderer('cuda')
    if str(renderer.backend).upper() != 'CUDA':
        raise ValueError('Production report frame rasterization requires the NVIDIA CUDA renderer')
    destination.mkdir(parents=True, exist_ok=True)
    title_font, label_font, tiny_font = _font(21), _font(16), _font(13)
    columns, per_sheet = 4, 20
    view_w, view_h = 130, 240
    tile_w, tile_h = view_w * 3 + 30, view_h + 120
    sheet_w, sheet_h = tile_w * columns + 36, tile_h * 5 + 92
    report_items, sheets = [], []
    try:
        for offset in range(0, len(selected), per_sheet):
            sheet = Image.new('RGB', (sheet_w, sheet_h), (9, 9, 9))
            draw = ImageDraw.Draw(sheet)
            page = offset // per_sheet + 1
            draw.text((18, 16), f'NULL GENESIS V3 | CUDA production | samples {offset + 1}–{min(offset + per_sheet, len(selected))}', fill=(230, 230, 230), font=title_font)
            draw.text((18, 47), 'Accepted native 50×50 art • canonical / quarter loop / half loop • real public timeline bytes', fill=(157, 157, 157), font=label_font)
            for index, m in enumerate(selected[offset:offset + per_sheet]):
                edition = int(m['edition'])
                data, frames = unpack_animation(root / 'animations' / f'{edition:04}.frames.json.gz')
                if data['genome_fingerprint'] != m['genome_fingerprint'] or data['grid'] != m['render_resolution']:
                    raise ValueError('Report timeline identity mismatch for edition ' + str(edition))
                first = '\n'.join(bytes(row).decode('ascii') for row in frames[0, :, 0].reshape(data['grid'][1], data['grid'][0])) + '\n'
                if hashlib.sha256(first.encode('ascii')).hexdigest() != m['canonical_hash']:
                    raise ValueError('Report canonical ASCII hash mismatch for edition ' + str(edition))
                total = len(frames)
                indices = [0, total // 4, total // 2]
                x = 18 + (index % columns) * tile_w
                y = 83 + (index // columns) * tile_h
                draw.text((x, y), f'#{edition:04}  {m["rarity"]}  rank {m["rank"]}', fill=(238, 238, 238), font=label_font)
                draw.text((x, y + 22), _short(m['primary_style'], 43), fill=(158, 158, 158), font=tiny_font)
                hashes = []
                changes = []
                for column, frame_index in enumerate(indices):
                    frame = frames[frame_index]
                    hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
                    changes.append(int(np.any(frame != frames[0], axis=1).sum()))
                    image = renderer.image(frame_result(frame, data['grid']))
                    image = image.resize((view_w, view_h), Image.Resampling.LANCZOS)
                    view_x = x + column * (view_w + 4)
                    sheet.paste(image, (view_x, y + 43))
                    draw.text((view_x + 4, y + 43 + view_h + 4), ['0%', '25%', '50%'][column], fill=(165, 165, 165), font=tiny_font)
                motion = next(a['value'] for a in m['attributes'] if a['trait_type'] == 'Motion')
                draw.text((x, y + tile_h - 49), _short(motion, 47), fill=(211, 211, 211), font=tiny_font)
                draw.text((x, y + tile_h - 29), f'{total} frames / {data["seconds"]}s • changed cells {changes[1]}/{changes[2]}', fill=(145, 145, 145), font=tiny_font)
                report_items.append(dict(edition=edition, rarity=m['rarity'], rank=m['rank'], canonical_hash=m['canonical_hash'], genome_fingerprint=m['genome_fingerprint'], quality_score=m['quality']['quality_score'], attributes=m['attributes'], base_concepts=m['base_concepts'], motion=motion, frame_count=total, sampled_indices=indices, sampled_frame_sha256=hashes, sampled_changed_cells=changes, sheet=f'production-{page:02}.jpg'))
            path = destination / f'production-{page:02}.jpg'
            sheet.save(path, quality=94, subsampling=0)
            sheets.append(dict(file=path.name, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), samples=min(per_sheet, len(selected) - offset)))
        status = renderer.status()
        report = dict(version='3.0.0', production=True, sampled=len(selected), collection_supply=len(catalog), rarity=dict(Counter(m['rarity'] for m in selected)), source_concepts=len({c for m in selected for c in m['base_concepts']}), category_values=len({a['id'] for m in selected for a in m['attributes']}), legendary_profiles=sorted(m['animation']['profile'] for m in selected if m['rarity'] == 'LEGENDARY'), backend='CUDA', device=status['device'], sampling='balanced report tiers; every Legendary; deterministic observed trait/source/motion diversity', scope='Postrun visual review only. Original public GPU timeline bytes are rerasterized by CUDA; labels and resizing use Pillow. This does not change collection artwork, ranking, or acceptance.', sheets=sheets, items=report_items)
        (destination / 'index.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return report
    finally:
        if owned_renderer:
            renderer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Completed public V3 collection directory')
    parser.add_argument('--output', default='dist/v3/reports/production-contact-sheets')
    parser.add_argument('--count', type=int, default=100)
    args = parser.parse_args()
    report = production_contact_sheets(args.directory, args.output, args.count)
    print(json.dumps({k: v for k, v in report.items() if k != 'items'}))


if __name__ == '__main__':
    main()
