import copy
import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report_v3 import frame_result, select_samples


def catalog_fixture():
    rows = []
    for tier in ('COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY'):
        for index in range(23 if tier == 'LEGENDARY' else 40):
            edition = len(rows) + 1
            rows.append(dict(edition=edition, rarity=tier, traits=[f'S{edition % 100 + 1:03}', f'V3.BODY.{index % 10 + 1:02}', f'V3.MOTION.{index % 10 + 1:02}'], base_concepts=[f'S{edition % 100 + 1:03}'], quality={'quality_score': 70 + index / 10}, animation=dict(profile=index if tier == 'LEGENDARY' else 0, motion=dict(kind=index % 10, speed=index % 3 + 1, amplitude=.4))))
    return rows


class ProductionReportTests(unittest.TestCase):
    def test_balanced_sampling_preserves_all_twenty_three_legendary_identities(self):
        source = catalog_fixture()
        original = copy.deepcopy(source)
        selected = select_samples(source, 100)
        self.assertEqual(len(selected), 100)
        self.assertEqual(len({m['edition'] for m in selected}), 100)
        self.assertEqual(Counter(m['rarity'] for m in selected), dict(COMMON=20, UNCOMMON=19, RARE=19, EPIC=19, LEGENDARY=23))
        self.assertEqual({m['animation']['profile'] for m in selected if m['rarity'] == 'LEGENDARY'}, set(range(23)))
        self.assertEqual(source, original)
        self.assertEqual(selected, select_samples(list(reversed(source)), 100))

    def test_sample_budget_cannot_silently_drop_legendary_identities(self):
        with self.assertRaisesRegex(ValueError, 'every Legendary'):
            select_samples(catalog_fixture(), 22)

    def test_stored_public_bytes_map_exactly_to_native_raster_contract(self):
        public_frame = np.array([[32, 0], [65, 254], [126, 31], [88, 100]], np.uint8)
        original = public_frame.copy()
        result = frame_result(public_frame, [2, 2])
        self.assertEqual(result['grid'], [2, 2])
        np.testing.assert_array_equal(result['glyph'], public_frame[:, 0])
        np.testing.assert_array_equal(result['cells'][:, 0], public_frame[:, 1])
        self.assertEqual(result['cells'].dtype, np.float32)
        self.assertEqual(result['cells'].shape, (4, 12))
        self.assertFalse(result['cells'][:, 1:].any())
        np.testing.assert_array_equal(public_frame, original)


if __name__ == '__main__':
    unittest.main()
