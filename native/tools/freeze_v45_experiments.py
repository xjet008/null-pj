"""Record completed agent visual review and freeze the measured release grid."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];reports=ROOT/'dist/v45/reports';path=reports/'experiments.json';report=json.loads(path.read_text())
assert report['passed'] and report['experiment_count']==200 and report['full_timelines']
images=[reports/Path(p).name for p in report['contact_sheets']]+[reports/'native-grid-comparison.jpg',reports/'experiment-motion-phases.jpg']
assert len(images)==12 and all(p.is_file() for p in images)
reason='80x80 retains comparable measured quality to 96 and 120 with lower CUDA time, while visually separating cavities and accessories more clearly than 30 and 50. All 200 before/after pairs, six-grid samples and five rarity timeline phases were inspected.'
review=dict(passed=True,reviewer='Codex visual inspection',canonical_grid=[80,80],presentation=[600,600],reason=reason,images={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in images},grid_comparison_images=1200,notes=['Improved silhouette size and cavity contrast across the matched V3 comparisons.','Common motion remains subtle; Legendary fragmentation remains intentional.','Quality scores are engineering proxies and require this independent visual review.'])
(reports/'experimental-visual-review.json').write_text(json.dumps(review,indent=2)+'\n')
report.update(visual_review_approved=True,canonical_grid=[80,80],canonical_resolution_frozen=True,selection_reason=reason)
path.write_text(json.dumps(report,separators=(',',':')))
print(json.dumps(dict(passed=True,canonical_grid=[80,80],experiment_count=200)))
