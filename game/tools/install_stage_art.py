"""Install approved stage exports as deterministic runtime resources.

The base artwork is unchanged pixel for pixel. Lava tiles are partitioned
into a private contiguous block, with two subtle indexed highlight variants.
No palette entry changes and no image drawing or raster resampling occur.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

GAME = Path(__file__).resolve().parents[1]
ART = GAME / 'art'
STAGES = (
    ('02A', 'phase02a-service-v1'), ('02B', 'phase02b-detour-v1'),
    ('03', 'phase03-shelter-v1'), ('04', 'phase04-tunnels-v1'),
    ('05', 'phase05-beacon-v1'), ('06A', 'phase06a-rescue-v1'),
    ('06B', 'phase06b-withdrawal-v1'),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unpack_tile(data):
    return [v for byte in data for v in (byte >> 4, byte & 15)]


def pack_tile(pixels):
    return bytes((pixels[i] << 4) | pixels[i + 1] for i in range(0, 64, 2))


def decoded(tiles, tilemap, width, height):
    result = bytearray(width * height)
    expanded = [unpack_tile(tile) for tile in tiles]
    for ty in range(height // 8):
        for tx in range(width // 8):
            pix = expanded[tilemap[ty * 64 + tx]]
            for row in range(8):
                start = (ty * 8 + row) * width + tx * 8
                result[start:start + 8] = bytes(pix[row * 8:row * 8 + 8])
    return bytes(result)


def lava_cells(design):
    result = set()
    for hazard in design.get('hazards', []):
        if hazard['kind'] not in ('thermal', 'lava'):
            continue
        x, y, w, h = hazard['rect']
        assert not any(v % 8 for v in (x, y, w, h))
        result.update(ty * 64 + tx for ty in range(y // 8, (y + h) // 8) for tx in range(x // 8, (x + w) // 8))
    return result


def warm_highlight(palette):
    colors = [((v >> 1) & 7, (v >> 5) & 7, (v >> 9) & 7) for v in struct.unpack('>16H', palette)]
    # The approved molten material's orange highlight is shared by all three
    # palettes. Choose a slightly brighter existing warm color, never white.
    origin = colors.index((7, 4, 1))
    luma = lambda rgb: rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114
    base_luma = luma(colors[origin])
    brighter = [(sum((a - b) ** 2 for a, b in zip(rgb, colors[origin])), i)
                for i, rgb in enumerate(colors)
                if rgb[0] >= rgb[1] > rgb[2] and rgb[0] - rgb[2] >= 2
                and 0 < luma(rgb) - base_luma <= 1000]
    assert brighter, 'No subtle existing warm highlight in approved palette'
    return origin, min(brighter)[1], colors


def partition(design, source_tiles, source_map, palette):
    tiles = [source_tiles[i:i + 32] for i in range(0, len(source_tiles), 32)]
    tilemap = list(struct.unpack('>' + str(len(source_map) // 2) + 'H', source_map))
    assert len(tilemap) == 64 * 48 and all(t < len(tiles) for t in tilemap)
    lava = lava_cells(design)
    if not lava:
        return source_tiles, source_map, b'', 0, 0, {'variants': 0, 'shared_tiles_duplicated': 0, 'changed_pixels_per_variant': []}
    origin, target, colors = warm_highlight(palette)
    # Only tiles containing the liquid highlight need an animated allocation.
    hot = {tilemap[cell] for cell in lava if origin in unpack_tile(tiles[tilemap[cell]])}
    outside = {tile for cell, tile in enumerate(tilemap) if cell not in lava}
    shared = hot & outside
    normal = [tile for tile in range(len(tiles)) if tile not in hot or tile in shared]
    hot = sorted(hot)
    start = len(normal)
    base = [tiles[tile] for tile in normal + hot]
    normal_id = {tile: i for i, tile in enumerate(normal)}
    hot_id = {tile: start + i for i, tile in enumerate(hot)}
    installed_map = [hot_id[tile] if cell in lava and tile in hot_id else normal_id[tile] for cell, tile in enumerate(tilemap)]
    assert all(not (start <= tile < start + len(hot)) for cell, tile in enumerate(installed_map) if cell not in lava)
    glow_base = [unpack_tile(tile) for tile in base[start:]]
    candidates = [(tile, pixel) for tile, pixels in enumerate(glow_base) for pixel, color in enumerate(pixels) if color == origin]
    number = len(candidates) // 8
    variants = []
    counts = []
    for phase in (0, 4):
        pixels = [p[:] for p in glow_base]
        for i in range(number):
            tile, pixel = candidates[i * 8 + phase]
            pixels[tile][pixel] = target
        counts.append(sum(a != b for aa, bb in zip(glow_base, pixels) for a, b in zip(aa, bb)))
        assert counts[-1] == number
        variants.append(b''.join(pack_tile(tile) for tile in pixels))
    installed_tiles = b''.join(base)
    installed_map = struct.pack('>' + str(len(installed_map)) + 'H', *installed_map)
    meta = {'variants': 2, 'variant_order': ['A', 'B'], 'runtime_sequence': ['base', 'A', 'B', 'A'],
            'shared_tiles_duplicated': len(shared), 'highlight_index': origin, 'brighter_index': target,
            'highlight_rgb3': list(colors[origin]), 'brighter_rgb3': list(colors[target]),
            'eligible_highlight_pixels': len(candidates), 'changed_pixels_per_variant': counts,
            'maximum_highlight_fraction': '1/8', 'variant_bytes': len(hot) * 32,
            'private_lava_tiles_only': True, 'global_palette_changed': False}
    return installed_tiles, installed_map, b''.join(variants), start, len(hot), meta


def generate():
    files = {}
    resources = []
    declarations = []
    header = ['// Generated by tools/install_stage_art.py. Do not edit.', '#ifndef STAGE_SCENES_H', '#define STAGE_SCENES_H', '#include "levels/arena.h"', '#include "elements/elements.h"', '']
    source = ['// Generated by tools/install_stage_art.py. Do not edit.', '#include "levels/stage_scenes.h"', '#include "stages.h"', '#include "courtyard.h"', '']
    # Identical immutable palettes/glow frames share a single ROM resource.
    shared = {('palette', digest((GAME / 'res/courtyard/palette.bin').read_bytes())): 'courtyard_palette'}
    shared_bytes_saved = 0
    reports = []
    for stage_id, folder in STAGES:
        stage = ART / folder
        design_path, export_path = stage / 'design.json', stage / 'export.json'
        design = json.loads(design_path.read_text())
        export = json.loads(export_path.read_text())
        hardware = stage / 'hardware'
        original = {name: (hardware / name).read_bytes() for name in ('tiles.bin', 'map-vdp.bin', 'palette.bin')}
        for name, data in original.items():
            assert digest(data) == export['export_sha256'][name], ('stale approved export', stage_id, name)
        tiles, tilemap, glow, glow_start, glow_count, glow_meta = partition(design, original['tiles.bin'], original['map-vdp.bin'], original['palette.bin'])
        tile_count = len(tiles) // 32
        assert tile_count <= 640 and 781 + tile_count + 11 <= 1440, (stage_id, tile_count)
        base_decoded = decoded([original['tiles.bin'][i:i + 32] for i in range(0, len(original['tiles.bin']), 32)], struct.unpack('>3072H', original['map-vdp.bin']), design['width'], design['height'])
        installed_decoded = decoded([tiles[i:i + 32] for i in range(0, len(tiles), 32)], struct.unpack('>3072H', tilemap), design['width'], design['height'])
        assert installed_decoded == base_decoded, ('approved base pixels changed', stage_id)
        stem = 'stage' + stage_id.lower()
        data_files = {'tiles': tiles, 'map': tilemap, 'palette': original['palette.bin']}
        if glow:
            data_files['glow'] = glow
        runtime_symbols = {}
        for kind, data in data_files.items():
            name = stem + '_' + kind
            path = GAME / 'res/stages' / stage_id.lower() / (kind + '.bin')
            files[path] = data
            key = (kind, digest(data))
            if kind in ('palette', 'glow') and key in shared:
                runtime_symbols[kind] = shared[key]
                shared_bytes_saved += len(data)
                continue
            runtime_symbols[kind] = name
            shared[key] = name
            resources.append('BIN %s "stages/%s/%s.bin" %d' % (name, stage_id.lower(), kind, 4 if kind in ('tiles', 'glow') else 2))
            declarations.append('extern const u8 %s[%d];' % (name, len(data)))
        scene = 'scene' + stage_id
        source.extend(['static const ArenaScene %s = {' % scene,
                       '    .tiles = (const u32 *)%s_tiles,' % stem,
                       '    .map = (const u16 *)%s_map,' % stem,
                       '    .damaged = (const u16 *)%s_map,' % stem,
                       '    .palette = (const u16 *)%s,' % runtime_symbols['palette'],
                       '    .tileCount = %d, .rows = %d,' % (tile_count, design['height'] // 8),
                       '    .glow = %s, .glowStart = %d, .glowCount = %d,' % ('(const u32 *)' + runtime_symbols['glow'] if glow else 'NULL', glow_start, glow_count),
                       '    .npcInMap = %s' % ('TRUE' if stage_id == '05' else 'FALSE'), '};'])
        solids = design.get('solids', [])
        if solids:
            source.append('static const ArenaRect solids%s[] = {' % stage_id)
            for solid in solids:
                source.append('    {%s, %s},' % (', '.join(str(v) for v in solid['rect']), 'TRUE' if solid.get('blocks_shots', False) else 'FALSE'))
            source.append('};')
        x, y, w, h = design['walkable']
        sx, sy = design['start']
        source.extend(['const ArenaDef ARENA%s = {' % stage_id,
                       '    %d, %d, %d, %d, %d, %d, %d, %d, %s, %d, &%s' % (design['width'], design['height'], x, y, x + w - 1, y + h - 1, sx, sy, 'solids' + stage_id if solids else 'NULL', len(solids), scene), '};', ''])
        header.append('extern const ArenaDef ARENA%s;' % stage_id)
        for kind, label in (('mud', 'mud'), ('thermal', 'lava')):
            hazards = [h for h in design.get('hazards', []) if h['kind'] == kind]
            if not hazards:
                continue
            assert len(hazards) == 2
            symbol = 'STAGE%s_%s' % (stage_id, label)
            header.extend(['#define STAGE%s_%s_COUNT %d' % (stage_id, label.upper(), len(hazards)), 'extern const TileRect %s[%d];' % (symbol, len(hazards))])
            source.append('const TileRect %s[%d] = {' % (symbol, len(hazards)))
            for hazard in hazards:
                assert all(v % 8 == 0 for v in hazard['rect'])
                source.append('    {%s},' % ', '.join(str(v // 8) for v in hazard['rect']))
            source.extend(['};', ''])
        module_sources = {name: digest((stage / name).read_bytes()) for name in export.get('module_source_sha256', {})}
        reports.append({'id': stage_id, 'folder': folder, 'world': [design['width'], design['height']],
                        'approved_source_sha256': digest((stage / design['source']).read_bytes()),
                        'module_source_sha256': module_sources, 'design_sha256': digest(design_path.read_bytes()),
                        'art_export_sha256': digest(export_path.read_bytes()),
                        'approved_base_sha256': {name: digest(data) for name, data in original.items()},
                        'installed_sha256': {kind + '.bin': digest(data) for kind, data in data_files.items()},
                        'runtime_symbols': runtime_symbols,
                        'base_decoded_pixel_sha256': digest(base_decoded),
                        'installed_decoded_pixel_sha256': digest(installed_decoded), 'approved_base_pixel_identical': True,
                        'base_tile_count': len(original['tiles.bin']) // 32, 'tile_count': tile_count, 'tile_bytes': len(tiles),
                        'tile_budget': 640, 'vram_end_with_hud': 781 + tile_count + 11,
                        'glow_start': glow_start, 'glow_count': glow_count, 'glow': glow_meta,
                        'scene_rows': design['height'] // 8, 'map_stride': 64, 'npc_in_map': stage_id == '05',
                        'solids': solids, 'hazards': design.get('hazards', [])})
    header.extend(['', '#endif', ''])
    files[GAME / 'src/levels/stage_scenes.h'] = '\n'.join(header).encode()
    files[GAME / 'src/levels/stage_scenes.c'] = ('\n'.join(source).rstrip() + '\n').encode()
    files[GAME / 'res/stages.res'] = ('\n'.join(resources) + '\n').encode()
    files[GAME / 'res/stages.h'] = ('#include <genesis.h>\n\n#ifndef _RES_STAGES_H_\n#define _RES_STAGES_H_\n\n' + '\n'.join(declarations) + '\n\n#endif // _RES_STAGES_H_\n').encode()
    report = {'generated_by': 'game/tools/install_stage_art.py', 'generator_sha256': digest(Path(__file__).read_bytes()),
              'approved_base_pixel_identical': True, 'global_palettes_changed': False,
              'glow_variant_order': ['A', 'B'], 'runtime_glow_sequence': ['base', 'A', 'B', 'A'],
              'runtime_upload_limit_bytes_per_frame': 128, 'runtime_upload_limit_tiles_per_frame': 4,
              'shared_resource_bytes_saved': shared_bytes_saved,
              'stages': reports,
              'generated_file_sha256': {str(path.relative_to(GAME.parent)): digest(data) for path, data in files.items()}}
    files[ART / 'phases02-06-v1/integration-export.json'] = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode()
    return files, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files, report = generate()
    for path, data in files.items():
        if args.check:
            assert path.exists() and path.read_bytes() == data, ('stale integration resource', path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps({'checked': args.check, 'approved_base_pixel_identical': True,
                      'stages': [{key: stage[key] for key in ('id', 'base_tile_count', 'tile_count', 'glow_start', 'glow_count')} for stage in report['stages']]}))


if __name__ == '__main__':
    main()
