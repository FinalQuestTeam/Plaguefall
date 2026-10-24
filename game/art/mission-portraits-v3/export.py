"""Export faithful mission portraits from the same corrected sources as combat.

Reuse the existing pose extractor and palette indexing. Only select, crop,
nearest-neighbour resize and centre an authored pose; never redraw anatomy.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
KINDS = ('sq_red', 'sq_yellow', 'sq_orange',
         'tri_red', 'tri_yellow', 'tri_purple', 'tri_orange',
         'pen_red', 'pen_yellow', 'pen_orange')
DIRECTION, POSE = 3, 0  # Authored SE idle pose, also used by combat.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    layout = json.loads((GAME / 'res/actor_animation.json').read_text())
    art = GAME / layout['enemy_art_directory']
    spec = importlib.util.spec_from_file_location(
        'combat_source_pipeline', GAME / 'art/cangaco-insects-iso60-v2/export_sprites.py')
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    corrections = json.loads((art / 'direction_corrections.json').read_text())
    combat_exports = {row['id']: row for row in
                      json.loads((art / 'validation/export.json').read_text())}
    words = struct.unpack('>16H', (GAME / 'res/insects/palette.bin').read_bytes())
    palette = [((word >> shift) & 7)*255//7 for word in words for shift in (1, 5, 9)]
    frames = (GAME / 'res/insects/frames.bin').read_bytes()
    records = []
    for kind in KINDS:
        correction = corrections.get(kind, {})
        override = correction.get('source_rows', {}).get(str(DIRECTION))
        source_path = art / (override or f'originals/{kind}.png')
        source_data = source_path.read_bytes()
        source_hash = hashlib.sha256(source_data).hexdigest()
        exported = combat_exports[kind]
        expected_hash = (exported['source_row_overrides'][str(DIRECTION)]['sha256']
                         if override else exported['source_sha256'])
        assert source_hash == expected_hash, (kind, 'source differs from combat export')
        source = Image.open(source_path).convert('RGBA')
        if override:
            row_top, row_bottom = 0, source.height
        else:
            edges = pipeline.row_edges(source, 5)
            row_top, row_bottom = edges[DIRECTION:DIRECTION+2]
        row = source.crop((0, row_top, source.width, row_bottom))
        poses = pipeline.source_poses(row, expected=7 if kind == 'pen_orange' else 6,
                                      minimum=6)[:6]
        selected = poses[POSE]
        original_pose = selected['image']
        flip = POSE in correction.get('horizontal_flip_poses', {}).get(str(DIRECTION), [])
        if flip:
            original_pose = original_pose.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Confirm that the corresponding native pose is really in the combat bank.
        sheet = Image.open(art / 'enemies' / kind / f'{kind}.png')
        size = exported['size']
        combat_pose = sheet.crop((POSE*size, DIRECTION*size,
                                  (POSE+1)*size, (DIRECTION+1)*size))
        packed = pipeline.pack(combat_pose, [(0, 0, size, size)])
        offset = exported['rom_offset'] + (DIRECTION*6+POSE)*len(packed)
        assert frames[offset:offset+len(packed)] == packed, (kind, 'combat pose mismatch')

        fitted = original_pose.copy()
        fitted.thumbnail((30, 30), Image.Resampling.NEAREST)
        left, top = (32-fitted.width)//2, (32-fitted.height)//2
        canvas = Image.new('RGBA', (32, 32))
        canvas.paste(fitted, (left, top))
        portrait = pipeline.indexed(canvas)
        portrait.putpalette(palette + [0]*720)
        output = ROOT / 'portraits' / f'{kind}.png'
        if args.check:
            with Image.open(output) as saved:
                assert saved.mode == 'P' and saved.size == (32, 32), kind
                assert saved.tobytes() == portrait.tobytes(), kind
                assert saved.getpalette() == portrait.getpalette(), kind
                assert saved.info.get('transparency') == 0, kind
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            portrait.save(output, transparency=0, optimize=False)
        bounds = selected['bounds']
        records.append({
            'id': kind, 'name': exported['name'],
            'source': source_path.relative_to(GAME).as_posix(),
            'source_sha256': source_hash,
            'source_row_override': bool(override),
            'source_pose_bounds': [bounds[0], row_top+bounds[1],
                                   bounds[2], row_top+bounds[3]],
            'direction': 'SE', 'direction_index': DIRECTION, 'pose': POSE,
            'horizontal_flip': flip, 'source_pose_size': list(original_pose.size),
            'source_pose_rgba_sha256': hashlib.sha256(original_pose.tobytes()).hexdigest(),
            'fitted_size': list(fitted.size), 'canvas_position': [left, top],
            'combat_native_size': size,
            'combat_frame_sha256': hashlib.sha256(packed).hexdigest(),
            'combat_frame_matches_runtime_bank': True,
            'portrait_pixel_sha256': hashlib.sha256(portrait.tobytes()).hexdigest(),
        })
        print(f'{kind}: existing SE pose -> {fitted.width}x{fitted.height} inside 32x32')
    manifest = {
        'method': 'Existing corrected combat source pose; no new generation or redrawing',
        'enemy_art_directory': layout['enemy_art_directory'],
        'transforms': ['existing pose extraction', 'nearest-neighbour resize',
                       'centering', 'existing combat palette indexing'],
        'canvas': [32, 32], 'maximum_silhouette': [30, 30],
        'palette': 'res/insects/palette.bin', 'new_art_generated': False,
        'pixel_identical_to_smaller_combat_frame': False,
        'note': 'Same authored pose at a different resolution, not identical native pixels.',
        'assets': records,
    }
    data = (json.dumps(manifest, indent=2, ensure_ascii=False)+'\n').encode()
    manifest_path = ROOT / 'sources.json'
    if args.check:
        assert manifest_path.read_bytes() == data, manifest_path
    else:
        manifest_path.write_bytes(data)


if __name__ == '__main__':
    main()
