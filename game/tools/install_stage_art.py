"""Install approved stage exports as deterministic runtime resources.

Scenery outside the beacon area is unchanged pixel for pixel. Lava tiles are partitioned
into a private contiguous block, with two subtle indexed highlight variants.
The phase05 statue is replaced by the generated iso60 asset requested by the
user; its old rectangle is cleared to the existing repeating floor first.
No palette entry changes or raster resampling occur in this installer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from io import BytesIO
from PIL import Image, ImageDraw

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


def replace_santa(tiles, tilemap):
    asset = ART / 'santa-iso60-v2'
    meta = json.loads((asset / 'export.json').read_text())
    image = Image.open(asset / 'santa.png')
    assert image.mode == 'P' and image.size == tuple(meta['native_size'])
    atlas = [tiles[i:i+32] for i in range(0, len(tiles), 32)]
    native_map = list(struct.unpack('>3072H', tilemap))
    canvas = Image.frombytes('P',(384,384),decoded(atlas,native_map,384,384))
    expanded = [unpack_tile(t) for t in atlas]
    def clear_floor(rect):
        rx,ry,rw,rh=rect
        for yy in range(ry,ry+rh):
            for xx in range(rx,rx+rw):
                tile=native_map[(40+(yy//8)%4)*64+12+(xx//8)%4]
                canvas.putpixel((xx,yy),expanded[tile][(yy%8)*8+xx%8])
    # Remove the disconnected old arrow fragments and the old statue/cable
    # bend. Keep the surrounding architecture and repeating floor intact.
    design=json.loads((ART/'phase05-beacon-v1/design.json').read_text())
    for module in design['modules']:
        if module['name'].startswith('Marca de pouso'):
            clear_floor(module['dest'])
    clear_floor(meta['erase_rect'])
    clear_floor((200,160,32,40))
    draw=ImageDraw.Draw(canvas)
    # Complete projected circles and four inward arrows: native floor paint,
    # not actor artwork. Existing ochre/gold palette slots keep it readable.
    draw.ellipse((132,152,260,264),outline=11,width=2)
    draw.ellipse((156,176,236,240),outline=10,width=1)
    arrows=[[(196,140),(188,130),(193,130),(193,120),(199,120),(199,130),(204,130)],
            [(196,276),(188,286),(193,286),(193,296),(199,296),(199,286),(204,286)],
            [(116,208),(106,200),(106,205),(96,205),(96,211),(106,211),(106,216)],
            [(276,208),(286,200),(286,205),(296,205),(296,211),(286,211),(286,216)]]
    for arrow in arrows:
        draw.polygon(arrow,fill=10,outline=7)
    # Continue the existing upper cable around the statue to its east base.
    cable=[(224,152),(228,166),(228,210),(208,218)]
    draw.line(cable,fill=1,width=3)
    draw.line(cable,fill=7,width=1)
    draw.rectangle((206,215,211,220),fill=6,outline=1)
    x,y,w,h = meta['erase_rect']
    col,row,cols,rows = x//8,y//8,w//8,h//8
    lookup = {tile:i for i,tile in enumerate(atlas)}
    def register(pixels):
        tile=pack_tile(pixels)
        if tile not in lookup:
            lookup[tile]=len(atlas);atlas.append(tile)
        return lookup[tile]
    # Preserve the connected cable beneath the statue during hit/death.
    floor=[register(canvas.crop((x+xx*8,y+yy*8,x+xx*8+8,y+yy*8+8)).tobytes())
           for yy in range(rows) for xx in range(cols)]
    ox,oy = meta['world_origin']
    assert image.getpixel((cable[-1][0]-ox,cable[-1][1]-oy)), 'cable must meet the opaque pedestal'
    # Only palette registration and transparent compositing. No generated
    # pose, silhouette or detail is drawn by this deterministic exporter.
    mask=Image.frombytes('L',image.size,bytes(255 if p else 0 for p in image.tobytes()))
    canvas.paste(image,(ox,oy),mask)
    for yy in range(48):
        for xx in range(48):
            native_map[yy*64+xx]=register(canvas.crop((xx*8,yy*8,xx*8+8,yy*8+8)).tobytes())
    # Reclaim the old statue/fragments' now-unused patterns before adding the
    # complete rings. There is no approximate tile replacement or resampling.
    used=sorted(set(native_map)|set(floor))
    remap={old:new for new,old in enumerate(used)}
    atlas=[atlas[i] for i in used]
    native_map=[remap[i] for i in native_map];floor=[remap[i] for i in floor]
    meta={**meta,'ground_rect':[96,112,208,192],'ring_center':[196,208],
          'ring_bounds':[[132,152,260,264],[156,176,236,240]],
          'inward_arrows':4,'cable_path':[list(p) for p in cable],
          'cable_endpoint':list(cable[-1]),'crown_tile':len(atlas),'crown_colors':[3,4]}
    # PAL1 slots3/4 are red/yellow. Zero is transparent; no white/black ink.
    sparkle=('...c....','...c..c.','..ccc...','ccccccc.','..ccc...','...c..c.','...c....','........')
    for color,core in ((3,4),(4,3)):
        pixels=[color if sparkle[yy][xx]=='c' else 0 for yy in range(8) for xx in range(8)]
        pixels[3*8+3]=core
        atlas.append(pack_tile(pixels))
    return b''.join(atlas),struct.pack('>3072H',*native_map),floor,meta


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
        santa = None
        if stage_id == '05':
            tiles,tilemap,santa_floor,santa = replace_santa(tiles,tilemap)
        tile_count = len(tiles) // 32
        assert tile_count <= 640 and 785 + tile_count + 11 <= 1440, (stage_id, tile_count)
        base_decoded = decoded([original['tiles.bin'][i:i + 32] for i in range(0, len(original['tiles.bin']), 32)], struct.unpack('>3072H', original['map-vdp.bin']), design['width'], design['height'])
        installed_decoded = decoded([tiles[i:i + 32] for i in range(0, len(tiles), 32)], struct.unpack('>3072H', tilemap), design['width'], design['height'])
        if not santa:
            assert installed_decoded == base_decoded, ('approved base pixels changed', stage_id)
        else:
            # All scenery outside the explicitly revised beacon area is identical.
            x,y,w,h = santa['ground_rect']
            for yy in range(design['height']):
                for xx in range(design['width']):
                    if not (x<=xx<x+w and y<=yy<y+h):
                        assert installed_decoded[yy*design['width']+xx] == base_decoded[yy*design['width']+xx]
            preview=Image.frombytes('P',(design['width'],design['height']),installed_decoded)
            palette=struct.unpack('>16H',original['palette.bin'])
            preview.putpalette([v for c in palette for v in (((c>>1)&7)*255//7,((c>>5)&7)*255//7,((c>>9)&7)*255//7)]+[0]*720)
            buffer=BytesIO();preview.convert('RGB').save(buffer,format='PNG')
            files[ART/'santa-iso60-v2/ground-layout.png']=buffer.getvalue()
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
        npc_visual = None
        if stage_id == '05':
            x,y,w,h = santa['erase_rect']
            col,row,cols,rows = x//8,y//8,w//8,h//8
            solid = ','.join(map(str,santa['solid_rect']))
            crown = ','.join(map(str,santa['crown']))
            source.extend(['static const u16 npc05Floor[%d] = {'%len(santa_floor)+', '.join(map(str,santa_floor))+'};',
                           'static const ArenaNpcVisual npc05Visual = {%d,%d,%d,%d,npc05Floor,{%s,FALSE},%s,%d,%d};'%(col,row,cols,rows,solid,crown,santa['crown_tile'],santa['ground_rect'][1])])
            npc_visual = {'rect':santa['erase_rect'],'floor_tiles':santa_floor,'bar_rect':[180,152,32,8],
                          'solid_rect':santa['solid_rect'],'crown':santa['crown'],'asset':'santa-iso60-v2',
                          'crown_tile':santa['crown_tile'],'crown_colors':santa['crown_colors'],
                          'focus_top':santa['ground_rect'][1],
                          'ground_rect':santa['ground_rect'],'ring_center':santa['ring_center'],
                          'ring_bounds':santa['ring_bounds'],'inward_arrows':santa['inward_arrows'],
                          'cable_path':santa['cable_path'],'cable_endpoint':santa['cable_endpoint'],
                          'source_sha256':santa['source_sha256']}
        scene = 'scene' + stage_id
        source.extend(['static const ArenaScene %s = {' % scene,
                       '    .tiles = (const u32 *)%s_tiles,' % stem,
                       '    .map = (const u16 *)%s_map,' % stem,
                       '    .damaged = (const u16 *)%s_map,' % stem,
                       '    .palette = (const u16 *)%s,' % runtime_symbols['palette'],
                       '    .tileCount = %d, .rows = %d,' % (tile_count, design['height'] // 8),
                       '    .glow = %s, .glowStart = %d, .glowCount = %d,' % ('(const u32 *)' + runtime_symbols['glow'] if glow else 'NULL', glow_start, glow_count),
                       '    .npcInMap = %s,' % ('TRUE' if stage_id == '05' else 'FALSE'),
                       '    .npcVisual = %s' % ('&npc05Visual' if npc_visual else 'NULL'), '};'])
        solids = design.get('solids', [])
        if santa:
            solids = [{'name':'Santa iso60, corpo e base','rect':santa['solid_rect'],'blocks_shots':False}]
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
                        'installed_decoded_pixel_sha256': digest(installed_decoded), 'approved_base_pixel_identical': not bool(santa),
                        'unchanged_outside_beacon_area': True,
                        'base_tile_count': len(original['tiles.bin']) // 32, 'tile_count': tile_count, 'tile_bytes': len(tiles),
                        'tile_budget': 640, 'vram_end_with_hud': 785 + tile_count + 11,
                        'glow_start': glow_start, 'glow_count': glow_count, 'glow': glow_meta,
                        'scene_rows': design['height'] // 8, 'map_stride': 64, 'npc_in_map': stage_id == '05',
                        'npc_visual': npc_visual,
                        'solids': solids, 'hazards': design.get('hazards', [])})
    header.extend(['', '#endif', ''])
    files[GAME / 'src/levels/stage_scenes.h'] = '\n'.join(header).encode()
    files[GAME / 'src/levels/stage_scenes.c'] = ('\n'.join(source).rstrip() + '\n').encode()
    files[GAME / 'res/stages.res'] = ('\n'.join(resources) + '\n').encode()
    files[GAME / 'res/stages.h'] = ('#include <genesis.h>\n\n#ifndef _RES_STAGES_H_\n#define _RES_STAGES_H_\n\n' + '\n'.join(declarations) + '\n\n#endif // _RES_STAGES_H_\n').encode()
    report = {'generated_by': 'game/tools/install_stage_art.py', 'generator_sha256': digest(Path(__file__).read_bytes()),
              'approved_base_pixel_identical': False, 'unchanged_outside_beacon_area': True, 'global_palettes_changed': False,
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
    print(json.dumps({'checked': args.check, 'unchanged_outside_beacon_area': report['unchanged_outside_beacon_area'],
                      'stages': [{key: stage[key] for key in ('id', 'base_tile_count', 'tile_count', 'glow_start', 'glow_count')} for stage in report['stages']]}))


if __name__ == '__main__':
    main()
