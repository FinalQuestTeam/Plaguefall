"""Restore the authored vertical gate in the isolated phase6 proposal.

Technical extraction uses the original exporter and original per-pose south
jamb registration. No image generation, rotation or production writes.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
ORIGINAL = GAME / 'art/visual-composition-fixes-v1/objectives/cycle-0'
EXPORTER = GAME / 'art/objective-sprites-v1/export.py'
spec = importlib.util.spec_from_file_location('existing_objective_export', EXPORTER)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
# extract() reads the matching original source_mount_center_x values here.
exporter.HERE = ORIGINAL
frames, boxes = exporter.extract(ORIGINAL / 'gate.png', 64, 64)
out = HERE / 'references'
out.mkdir(exist_ok=True)
strip = Image.new('RGBA', (384, 64))
measured = []
for i, frame in enumerate(frames):
    frame.save(out / f'gate-vertical-{i}.png')
    rgba = frame.convert('RGBA')
    strip.alpha_composite(rgba, (i * 64, 0))
    alpha = rgba.getchannel('A')
    top = alpha.crop((0, 0, 64, 9)).getbbox()
    bottom = alpha.crop((0, 55, 64, 64)).getbbox()
    assert top and bottom, ('missing post', i)
    top_x = (top[0] + top[2] - 1) / 2
    bottom_x = (bottom[0] + bottom[2] - 1) / 2
    # Folded leaf may join the southern post; closure frames are the reliable
    # orientation measurement, with no debris included in either end region.
    if i < 2:
        assert abs(top_x - bottom_x) <= 1, (i, top_x, bottom_x)
    measured.append(dict(frame=i, bbox=alpha.getbbox(),
                         top_support_center_x=top_x,
                         bottom_region_center_x=bottom_x))
strip.save(out / 'gate-vertical-strip.png')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
current = GAME / 'art/objective-sprites-v1/source/gate.png'
diagonal = GAME / 'art/visual-composition-fixes-v1/routes/cycle-2/source/gate-clean.png'
assert sha(current) == sha(diagonal), 'Investigate changed production source'
report = dict(
    issue='Preview imported current shared gate frames; current source is the diagonal cycle2 revision.',
    restored_source=str((ORIGINAL / 'gate.png').relative_to(GAME)),
    restored_source_sha256=sha(ORIGINAL / 'gate.png'),
    registration=str((ORIGINAL / 'gate-mount.json').relative_to(GAME)),
    original_exporter=str(EXPORTER.relative_to(GAME)),
    current_source=str(current.relative_to(GAME)),
    current_source_sha256=sha(current),
    current_source_matches_cycle2=True,
    cycle2_prompt='art/visual-composition-fixes-v1/routes/cycle-2/prompts/gate-orientation.txt',
    preview_closed='references/gate-vertical-0.png',
    preview_folded='references/gate-vertical-5.png',
    frames=measured,
    generated_new_art=False,
    rotated_or_sheared=False,
    production_resources_changed=False,
    production_rom_sha256=sha(GAME / 'out/release/Plaguefall.bin'),
)
(HERE / 'gate-investigation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
