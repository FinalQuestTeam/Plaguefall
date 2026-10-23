"""Compose continuous 2048px routes from native modules and generated landmarks.

Only palette quantization/downsampling of the generated atlas is lossy. Every
8x8 production tile is then preserved exactly; no nearest-tile replacement.
The final atlas is compacted so unused source-arena tiles consume no VRAM.
"""
from pathlib import Path
import hashlib
import numpy as np
from PIL import Image

ART = Path(__file__).resolve().parents[1] / 'art/routes-2048-v2'
SECTIONS = {
    '04': ['Entrada de manutencao', 'Casa de bombas', 'Tubulacao avariada', 'Portao de servico'],
    '06b': ['Posto de evacuacao', 'Bagagem e transporte', 'Acampamento abandonado', 'Saida terrestre'],
}


def packed(pixels):
    return bytes((int(pixels[i]) << 4) | int(pixels[i+1]) for i in range(0, 64, 2))


def compose(key, tiles, source, height, width=2048):
    """Return tile indices and the auditable list of environmental landmarks."""
    cols = width // 8
    tile_index = {tile: i for i, tile in enumerate(tiles)}

    def intern(tile):
        if tile not in tile_index:
            tile_index[tile] = len(tiles)
            tiles.append(tile)
        return tile_index[tile]

    def source_tile(x, y):
        return source[(y // 8) * 64 + x // 8]

    # Four small floor modules, arranged in irregular broad slabs rather than
    # repeating an entire closed room. Subtle material variants share PAL3.
    fx, fy = (192, 160) if key == '04' else (224, 128)
    ground = [source_tile(fx+x*8, fy+y*8) for y in range(2) for x in range(2)]
    variants = [ground]
    for variant, remap in enumerate(({7: 6, 8: 7}, {7: 6, 8: 6}) if key == '04' else ({9: 8}, {9: 8})):
        # Sparse wear in the material, not solid differently coloured slabs.
        patches = []
        for t in ground:
            pixels = [v for b in tiles[t] for v in (b >> 4, b & 15)]
            patches.append(intern(packed([remap.get(v, v) if ((i*13+i//8*7) % 47 < (2 if variant else 3)) else v
                                          for i, v in enumerate(pixels)])))
        variants.append(patches)
    band = 80 if key == '04' else 96
    canvas = []
    # A quiet continuous wall supports individually placed equipment. Do not
    # repeat the original arena's pillars, hatch, shelters or room ends.
    wall_x = 144 if key == '04' else 160
    for y in range(height // 8):
        for x in range(cols):
            px, py = x*8, y*8
            if px < 16:
                tile = source_tile(px, py)
            elif px >= width-16:
                tile = source_tile(512-(width-px), py)
            elif py < band:
                tile = source_tile(wall_x + (x % 2)*8, py)
            elif py >= height-16:
                tile = source_tile(128 + (x % 8)*8, py)
            else:
                # Scatter compatible native texture cells without moving their
                # pixels. Preserve the base floor colour: large tint blocks or
                # busy stripes make enemy bullets and hole edges harder to read.
                seed = (x*73856093) ^ (y*19349663) ^ ((x//13)*83492791)
                tile = variants[(seed>>9) % 3][seed % len(ground)]
            canvas.append(tile)

    # The old arena is a flattened painting: arbitrary rectangular crops cut
    # through pipes, pillars and shelters. Keep only complete alpha silhouettes
    # below; the quiet wall/floor strips above contain no isolated equipment.
    fixtures = []

    # Generated source is a 2x2 transparent sheet. Crop each complete silhouette
    # before its single native downsample, avoiding clipped lamps or luggage.
    name = 'tunnel' if key == '04' else 'evacuation'
    path = ART / f'source/{name}-cutouts.png'
    image = Image.open(path).convert('RGBA')
    assert image.getchannel('A').getextrema() == (0, 255), 'landmarks require a transparent source'
    palette_path = ART.parents[1] / f'res/stages/{key}/palette.bin'
    import struct
    words = struct.unpack('>16H', palette_path.read_bytes())
    palette = np.array([(((c >> 1) & 7)*255//7, ((c >> 5) & 7)*255//7, ((c >> 9) & 7)*255//7) for c in words], dtype=np.int32)
    from PIL import ImageOps

    def stamp(rgba_image, x, top):
        rgba = np.asarray(rgba_image, dtype=np.int32)
        indexed = ((rgba[:, :, None, :3] - palette[None, None, :, :]) ** 2).sum(axis=3).argmin(axis=2)
        for ty in range(rgba_image.height//8):
            for tx in range(rgba_image.width//8):
                address = (top//8+ty)*cols+x//8+tx
                base = [v for b in tiles[canvas[address]] for v in (b >> 4, b & 15)]
                pixels = indexed[ty*8:(ty+1)*8, tx*8:(tx+1)*8].flatten()
                alpha = rgba[ty*8:(ty+1)*8, tx*8:(tx+1)*8, 3].flatten()
                canvas[address] = intern(packed([pixels[j] if alpha[j]>=128 else base[j] for j in range(64)]))

    landmarks = []
    for i, x in enumerate((56, 680, 1264, 1904)):
        half_x, half_y = image.width//2, image.height//2
        quadrant = image.crop(((i%2)*half_x, (i//2)*half_y, (i%2+1)*half_x, (i//2+1)*half_y))
        bounds = quadrant.getchannel('A').getbbox()
        assert bounds, (key, i, 'empty generated landmark')
        module = Image.new('RGBA', (80, 64))
        patch = ImageOps.contain(quadrant.crop(bounds), (80, 64), Image.Resampling.LANCZOS)
        module.paste(patch, ((80-patch.width)//2, 64-patch.height))
        top = 16 if key == '04' else 24
        stamp(module, x, top)
        landmarks.append({'name': SECTIONS[key][i], 'rect': [x, top, 80, 64],
                          'source_quadrant': i, 'source_bounds': list(bounds)})

    # The escort camera often excludes the upper architecture. Flat, walkable
    # details therefore carry the environmental story through the actual lane.
    ground_path = ART / 'source/ground-details.png'
    ground_image = Image.open(ground_path).convert('RGBA')
    assert ground_image.getchannel('A').getextrema() == (0, 255)
    details = []
    positions = [(88, 160), (520, 144), (1040, 144), (1632, 160)] if key == '04' else [(200, 240), (744, 184), (1224, 232), (1768, 184)]
    names = ['Grelha nivelada', 'Inspecao de conduites', 'Concreto desgastado', 'Rastro de manutencao'] if key == '04' else ['Marcas de carrinho', 'Faixa de evacuacao', 'Vestigios da retirada', 'Pavimento da saida']
    for i, ((x, top), label) in enumerate(zip(positions, names)):
        col, row = i % 2, i//2+(0 if key == '04' else 2)
        cw, ch = ground_image.width//2, ground_image.height//4
        cell = ground_image.crop((col*cw, row*ch, (col+1)*cw, (row+1)*ch))
        bounds = cell.getchannel('A').getbbox()
        assert bounds, (key, i, 'empty floor detail')
        patch = ImageOps.contain(cell.crop(bounds), (64, 32), Image.Resampling.LANCZOS)
        module = Image.new('RGBA', (64, 32));module.paste(patch, ((64-patch.width)//2, (32-patch.height)//2))
        stamp(module, x, top)
        details.append({'name': label, 'rect': [x, top, 64, 32], 'walkable': True, 'source_cell': [col, row]})
    return canvas, {'source': str(path.relative_to(ART)),
                    'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'landmarks': landmarks, 'inherited_fixtures': [list(r) for r in fixtures],
                    'ground_source': str(ground_path.relative_to(ART)),
                    'ground_source_sha256': hashlib.sha256(ground_path.read_bytes()).hexdigest(),
                    'ground_details': details,
                    'whole_room_repeats': False}


def compact(tiles, tilemap):
    """Retain exact patterns referenced by this route, in deterministic order."""
    used = sorted(set(tilemap))
    remap = {old: new for new, old in enumerate(used)}
    return [tiles[i] for i in used], [remap[i] for i in tilemap]
