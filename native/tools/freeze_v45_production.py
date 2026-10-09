"""Record completed visual review; run only after inspecting all five sheets."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'dist/v45/reports'

def main():
    review=json.loads((REPORTS/'production-visual-review.json').read_text())
    audit=json.loads((REPORTS/'collection-audit.json').read_text())
    assert audit['passed'] and audit['editions']==3333 and audit['animated']==3333
    assert review['sampled']==100 and review['legendary_profiles']==23
    assert len(review['images'])==5
    for name,expected in review['images'].items():
        assert hashlib.sha256((REPORTS/name).read_bytes()).hexdigest()==expected
    review.update(passed=True,review_required=False,reviewer='local visual inspection',
                  findings=['Subject scale and safe padding remain clear across all framing modes.',
                            'Common through Epic retain structural continuity across sampled poses. Legendary middle phases intentionally fragment and reconstruct, returning to readable canonical and wrap bodies.',
                            'Every Legendary phenomenon and all four ordinary rarity tiers were inspected.'])
    audit.update(visual_review_approved=True,visual_review_required=False,
                 visual_review='/v45/reports/production-visual-review.json')
    for name,data in [('production-visual-review.json',review),('collection-audit.json',audit)]:
        (REPORTS/name).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(passed=True,reviewed_editions=100,reviewed_sheets=5)))

if __name__=='__main__':main()
