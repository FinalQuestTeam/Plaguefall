"""Read-only exact proof of horizontal early rejection in camera focus.

Exercises every integer actor foot coordinate inside each authored world,
including coordinates inside solids. Production selection remains unchanged.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    snapshot = HERE / 'expected-ce8b35'
    maps = json.loads((snapshot / 'maps.json').read_text())
    report = {'passed': False, 'source': str(snapshot / 'maps.json'),
              'proof': 'dx,dy are nonnegative distances to an AABB. With strict dx+dy<nearest, dx>=nearest cannot select the rectangle, including ties. Current world ranges cannot overflow signed16.',
              'productionModified': False, 'phases': {}}
    for key, data in maps.items():
        rects = [tuple(v['bbox']) for v in data['camera_interest']]
        width, height = data['size']
        total = skipped = poses = 0
        for py in range(height):
            cy = py + 8
            for px in range(width):
                cx = px + 8
                original = optimized = -1
                old_nearest = new_nearest = 65
                for index, (x, y, w, h) in enumerate(rects):
                    dx = x-cx if cx<x else cx-x-w if cx>x+w else 0
                    dy = y-cy if cy<y else cy-y-h if cy>y+h else 0
                    if dx+dy < old_nearest:
                        original = index
                        old_nearest = dx+dy
                    total += 1
                    if dx >= new_nearest:
                        skipped += 1
                        continue
                    if dx+dy < new_nearest:
                        optimized = index
                        new_nearest = dx+dy
                assert (original, old_nearest) == (optimized, new_nearest), (key, px, py)
                poses += 1
        report['phases'][key] = {'integerFootCoordinates': poses,
                                 'focusRectEvaluations': total,
                                 'dyCalculationsAvoided': skipped,
                                 'avoidedPercent': round(100*skipped/total, 4),
                                 'focusAndTieSelectionExact': True}
    report['passed'] = True
    (HERE / 'camera-focus-equivalence.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
