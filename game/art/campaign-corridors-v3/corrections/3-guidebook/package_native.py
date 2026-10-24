"""Package the parent's existing draft; never executes or edits build.py.

Private proposal only. Active geometry is copied without changing values.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import sys
from PIL import Image, ImageDraw, ImageFont

A = Path(__file__).resolve().parent
G = A.parents[3]
BASE = G / 'art/campaign-corridors-v3/streets/3'
sys.path.insert(0, str(G / 'tools'))
import campaign_geometry as geometry
import campaign_corridors as bridge

spec = importlib.util.spec_from_file_location('exact_pack', G / 'art/campaign-whole-scenes-v1/pack.py')
packer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packer)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(name, path, purpose):
    assert path.exists(), path
    return dict(id=name, path=os.path.relpath(path, A), game_path=str(path.relative_to(G)),
                sha256=digest(path), purpose=purpose)


active = json.loads((BASE / 'manifest.json').read_text())
protected = [BASE / 'manifest.json', *(BASE / 'native').glob('*.bin'),
             *(BASE / 'damaged-native').glob('*.bin'), A / 'build.py']
before = {str(p): digest(p) for p in protected}
images = {name: Image.open(A / f'draft/{file}-complete.png')
          for name, file in [('intact', 'candidate'), ('damaged', 'damaged')]}
palette = [tuple(images['intact'].getpalette()[i:i+3]) for i in range(0, 48, 3)]
assert palette[0] == (0, 0, 0)
assert all(c in [i * 255 // 7 for i in range(8)] for color in palette for c in color)
assert images['damaged'].getpalette()[:48] == images['intact'].getpalette()[:48]
ref = Image.open(G / 'art/campaign-pattern-v2/early/01-courtyard/complete-native.png')
assert ref.getpalette()[:48] == images['intact'].getpalette()[:48]
stats = {}
for name, bank, complete, expected in [
    ('intact', 'native', 'complete-native.png', 554),
    ('damaged', 'damaged-native', 'complete-damaged-native.png', 570),
]:
    im = images[name]
    assert im.mode == 'P' and list(im.size) == active['size'] and max(im.getdata()) < 16
    _, packed = packer.pack({'map': im}, palette, A / bank, f'private_street3_{name}', 640)
    assert packed['tiles'] == expected, (name, packed['tiles'], expected)
    shutil.copy2(A / bank / 'map-native.png', A / complete)
    shutil.copy2(A / bank / 'map-native.png', A / bank / 'complete.png')
    restored = Image.open(A / complete)
    assert restored.tobytes() == im.tobytes()
    stats[name] = dict(scene_tiles=packed['tiles'], objective_tiles=0, total_tiles=packed['tiles'],
                       budget=640, free_tiles=640-packed['tiles'],
                       graphics_bytes=(A/bank/'tiles.bin').stat().st_size,
                       map_bytes=(A/bank/'map.bin').stat().st_size, palette_bytes=32,
                       exact_hv_deduplication=True, pixel_exact_reassembly=True,
                       lossy_pattern_replacements=0, tile_sha256=digest(A/bank/'tiles.bin'))
assert (A/'native/palette.bin').read_bytes() == (A/'damaged-native/palette.bin').read_bytes()

m = copy.deepcopy(active)
m.update(status='private_trial_only_requires_visual_review_and_real_ROM_tests',
         complete='complete-native.png',
         native=dict(tiles='native/tiles.bin', map='native/map.bin', palette='native/palette.bin'),
         damaged_native=dict(complete='complete-damaged-native.png', tiles='damaged-native/tiles.bin',
                             map='damaged-native/map.bin', palette='damaged-native/palette.bin'))
m['memory'] = dict(stats['intact'], damaged_scene_tiles=stats['damaged']['scene_tiles'],
                   max_state_tiles=570, states_resident_simultaneously=False)
m['special_states'] = [dict(state='church destroyed by bomb in phase1',
                            path='complete-damaged-native.png', memory=stats['damaged'])]
m['sources'] = [
    source('whole-scene', A/'source/whole-folded-cycle3.png', 'Existing whole source; complete openings, curbs and frames.'),
    source('truck-cutout', A/'source/truck-extracted.png', 'Existing whole truck; composed against street before palette indexing.'),
    source('church-intact-and-palette', G/'art/campaign-pattern-v2/early/01-courtyard/complete-native.png', 'Exact church crop [16,0,216,112]; shared16color palette and32x32ground [224,192,256,224].'),
    source('church-damaged', G/'art/campaign-pattern-v2/early/01-courtyard/damaged-native.png', 'Exact damaged church crop [16,0,216,112].'),
    source('roof-whole-kit', G/'art/campaign-corridors-v3/corrections/9-guidebook/modules/whole-workshop-rgba.png', 'Existing complete128x128workshop; native roof cap/plane/eave canvases.'),
    source('native-plaster', G/'art/phase01-courtyard-v2/intact-native.png', 'Four unobstructed8x8light plaster crops at [64,80],[88,80],[116,76],[184,72].'),
    source('parcel-wall', G/'art/campaign-pattern-v2/early/01-courtyard/modules/lower-wall.png', 'Existing complete perimeter wall strip.'),
    source('whole-barrels', G/'art/campaign-pattern-v2/early/01-courtyard/modules/barrels.png', 'Whole approved barrels; ground composed before palette indexing.'),
    source('parent-composer', A/'build.py', 'Parent-owned exact composition; packager never edits or executes this file.'),
]
m['module_trace'] = 'draft/modules.json'
m['layout'] = 'draft/placements.json'
m['palette'] = dict(index0='black', colors=palette, encoding='RGB33316entries, big-endian Mega Drive words',
                    exact_reference='../../../campaign-pattern-v2/early/01-courtyard/complete-native.png')
m['critical_review'] = dict(
    improvements=[
        'Church is preserved pixel-for-pixel in both states, including its worn material and roof silhouette.',
        'Roof area72/112 and88/128 now dominates ordinary buildings; separate short fronts retain complete doors/windows.',
        'Existing1px roof/plaster/floor kit removes the previous large one-color street and flat building planes.',
        'Existing north/south parcels, openings and paths are retained; no silhouette was shrunk to fit a tile count.',
    ],
    reservations=[
        'The pale wall16x16patch repeats visibly, and orange terracotta roofs are very regular across different building families.',
        'The shared ochre ground is recognizably the church material but reads as dry earth; asphalt distinction remains limited.',
        'Warehouse roller and shortened garage openings are cleaner than the worn church; this is still an isolated style candidate.',
        'Offline previews do not prove camera interpolation, collisions, FPS, combat readability or ROM palette upload.',
    ],
    decision='Suitable for private comparative trial; no publication or final style approval.')
for k in ['size','bounds','start','solids','route_points','player_waypoints','route_margin',
          'route_validation','exit','camera_player_y','camera_interest','southern_parcels']:
    assert m[k] == active[k], k
validation = geometry.validate(dict(m, points=m['route_points']))
m['packaging_validation'] = dict(active_geometry_unchanged=True, source_paths_resolve=True,
                                 palette_same_as_reference=True, decoded_pixels_unchanged=True,
                                 geometry=validation)
assert all((A/s['path']).exists() for s in m['sources'])
(A/'manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n')

# Normal camera target from ARENA_camera, actor alone. No smoothing/ROM is claimed.
def camera(px, py):
    x, y = px-152, py-active['camera_player_y']
    focus = None
    nearest = 65
    for item in active['camera_interest']:
        ax, ay, aw, ah = item['bbox']
        dx = max(ax-px-8, px+8-ax-aw, 0)
        dy = max(ay-py-8, py+8-ay-ah, 0)
        if dx+dy < nearest:
            nearest, focus = dx+dy, item
    if focus:
        ax, ay, aw, ah = focus['bbox']
        y = min(ay-24, max(ay+ah-224, y))
        x = min(ax, max(ax+aw-320, x))
    y = min(py-24-16-31, max(py+8-224, y))
    x = min(px-8, max(px+24-320, x))
    return max(0, min(2240, x)), max(0, min(96, y))

reviews = A/'reviews'
reviews.mkdir(exist_ok=True)
hero = Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA')
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
poses = [('church',[136,176]),('market',[496,264]),('garage-north',[1280,160]),
         ('garage-south',[1824,264]),('warehouse',[2400,176])]
rows = []
sheet = Image.new('RGB',(640,5*248),(25,25,25))
for i,(name,(px,py)) in enumerate(poses):
    assert geometry.free(active,px,py), (name,'preview actor collides')
    cx,cy = camera(px,py)
    for col,state in enumerate(['intact','damaged']):
        im = images[state].convert('RGBA')
        im.alpha_composite(hero,(px-8,py-31))
        im = im.crop((cx,cy,cx+320,cy+224)).convert('RGB')
        draw=ImageDraw.Draw(im)
        draw.rectangle((0,0,319,23),fill='#181818')
        draw.text((5,5),'PRÉVIA, NÃO ROM - FASE3',font=font,fill='#dadaaf')
        file=f'camera-{name}-{state}.png'
        im.save(reviews/file)
        sheet.paste(im,(col*320,i*248+24))
        ImageDraw.Draw(sheet).text((col*320+4,i*248+5),f'{name} / {state} / x{cx} y{cy}',font=font,fill='#dedeb6')
    rows.append(dict(id=name,feet=[px,py],camera=[cx,cy],size=[320,224],scale=1,
                     preview=f'reviews/camera-{name}-intact.png',
                     damaged_preview=f'reviews/camera-{name}-damaged.png',
                     camera_model='Normal ARENA settled target; no interpolation, no ROM rendering.'))
sheet.save(reviews/'five-cameras-1x.png')
(reviews/'cameras.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
report=dict(status='private_trial_only',phase='3',source='Existing parent draft; no new raster art',
            memory=stats,geometry=validation,previews=rows,opinion=m['critical_review'],
            protected_hashes=before)
(reviews/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
m['proposal_previews']=rows
(A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
for path,sha in before.items():
    assert digest(Path(path))==sha, ('Protected input changed during packaging',path)
bridge.FOLDERS['3']='corrections/3-guidebook'
bridge.read('3')
print(json.dumps(dict(tiles={k:v['scene_tiles'] for k,v in stats.items()},
                     geometry=validation,all_sources_resolve=True,
                     protected_inputs_unchanged=True,bridge_read_passed=True),indent=2))
