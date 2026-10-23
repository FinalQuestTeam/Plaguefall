"""Native, palette-independent-of-scenery lava/mud tiles and portable examples.

Native reference textures, 23 connected variants/material and scene palette adaptation.
Modular geometry remains independent of the source scene.
"""
from pathlib import Path
from functools import lru_cache
import argparse
import io
import json
import struct
from PIL import Image, ImageDraw

GAME = Path(__file__).resolve().parents[1]
ART = GAME / 'art/terrain-modules-v1'
N, E, S, W = 1, 2, 4, 8
VARIANTS = 23


def read_palette(key):
    return struct.unpack('>16H',(GAME/f'res/stages/{key}/palette.bin').read_bytes())


def channels(color):
    return ((color>>1)&7,(color>>5)&7,(color>>9)&7)


def color_map(palette):
    source=read_palette('06b')
    def distance(a,b):
        ar,ag,ab=channels(a);br,bg,bb=channels(b)
        return (ar-br)**2+2*(ag-bg)**2+(ab-bb)**2
    return [0]+[min(range(1,16),key=lambda j:distance(source[i],palette[j])) for i in range(1,16)]


@lru_cache(None)
def reference(material):
    key,x,y=('06b',48,120) if material=='lava' else ('02b',32,264)
    return native_patch(key,x,y)


@lru_cache(None)
def native_patch(key,x,y):
    base=GAME/f'res/stages/{key}'
    raw=(base/'tiles.bin').read_bytes();m=struct.unpack('>3072H',(base/'map.bin').read_bytes())
    return tuple((raw[m[yy//8*64+xx//8]*32+yy%8*4+xx%8//2]>>(0 if xx%2 else 4))&15
                 for yy in range(y,y+16) for xx in range(x,x+32))


def lava_border(x,y,mask,grain,color):
    """Recessed pool: far cut face, narrow near lip, upper-left light.

    A six-pixel far face reads as a 12px cut viewed at 60 degrees.
    Everything stays inside the existing hazard footprint. One-tile channels
    compress that face to retain a visible strip of molten material.
    """
    north=not mask&N;east=not mask&E;south=not mask&S;west=not mask&W
    if ((north and west and x+y<2) or (north and east and 7-x+y<2) or
        (south and west and x+7-y<2) or (south and east and 14-x-y<2)):
        return 0
    # Upper ground bevel: lit rock, not an emissive lava-colored outline.
    if north and y==0:return 9 if grain<4 else 8 if grain<17 else 7
    if south and y==7:return 8 if grain<12 else 7
    if west and x==0:return 8 if grain<13 else 7
    if east and x==7:return 7 if grain<17 else 1
    depth=3 if south else 6
    if north and y<depth:
        if y==1:return 7 if grain<7 else 1
        if y==depth-1:return 13 if grain<17 else 12
        if y==2:return 7 if grain>6 else 13
        if y==3:return 13 if grain>7 else 1
        return 1 if grain<15 else 13
    # The near wall faces away from the camera: only its thin lip is visible.
    if south and y==6:return 1 if grain<16 else 7
    if west and x==1:return 7 if grain<10 else 13
    if east and x==6:return 1 if grain<16 else 13
    if west and x==2:return 13 if grain<13 else color
    if east and x==5:return 13 if grain<17 else color
    return color


def tile(material, mask, phase=0, interior=0):
    # Keep the clustered, irregular pixel work of the approved map artwork.
    # No Voronoi plates, repeating geometric cracks or bright icon outlines.
    source=reference(material);pixels=[]
    mud_shades={0:1,1:1,6:13,7:7,8:7,9:8,11:9,12:1,13:1}
    for y in range(8):
        for x in range(8):
            distances=([y] if not mask&N else [])+([7-x] if not mask&E else [])
            distances+=([7-y] if not mask&S else [])+([x] if not mask&W else [])
            edge=min(distances,default=8)
            px=x+8*(interior&3);py=y+8*(interior>>2)
            color=source[py*32+px]
            grain=(px*11+py*7+px*py*3)%23
            if material=='mud':color=mud_shades.get(color,7)
            elif phase and color==11 and grain<3:color=10
            elif phase and color==12 and grain==0:color=11
            if material=='lava':
                color=lava_border(x,y,mask,grain,color)
            else:
                # Mud stains the ground plane; never give it a raised rim,
                # vertical cut face or directional cast shadow.
                if edge==0:color=0 if grain<15 else 7
                elif edge==1:
                    if grain<5:color=0
                    elif grain<16:color=1
                elif edge==2 and grain<7:color=7
            pixels.append(color)
    return pixels


def stamp(image, rects, material, palette=None):
    """Render the same portable layer over a scene preview; rects are pixels."""
    occupied = {(x, y) for rx,ry,w,h in rects
                for y in range(ry//8,(ry+h)//8) for x in range(rx//8,(rx+w)//8)}
    palette=palette or read_palette('06b');mapping=color_map(palette)
    rgb = [(((c>>1)&7)*255//7,((c>>5)&7)*255//7,((c>>9)&7)*255//7) for c in palette]
    for x,y in occupied:
        mask=sum(bit for dx,dy,bit in [(0,-1,N),(1,0,E),(0,1,S),(-1,0,W)] if (x+dx,y+dy) in occupied)
        pixels=tile(material,mask,interior=(x&3)+((y&1)<<2) if mask==15 else 0)
        for yy in range(8):
            for xx in range(8):
                c=pixels[yy*8+xx]
                if c:image.putpixel((x*8+xx,y*8+yy),rgb[mapping[c]])


def generate():
    palette=read_palette('06b')
    rgb = [(((c>>1)&7)*255//7, ((c>>5)&7)*255//7, ((c>>9)&7)*255//7) for c in palette]
    sets = [[tile(kind, min(mask, 15), phase, max(0,mask-15)) for mask in range(VARIANTS)]
            for kind, phase in [('lava', 0), ('lava', 1), ('mud', 0)]]
    def array(name, tiles):
        words = [sum(row[x] << ((7-x)*4) for x in range(8))
                 for pixels in tiles for row in [pixels[y:y+8] for y in range(0, 64, 8)]]
        return 'static const u32 '+name+'['+str(len(words))+']={\n'+''.join(
            '    '+','.join(f'0x{v:08x}UL' for v in words[i:i+8])+',\n' for i in range(0, len(words), 8))+'};\n'
    header = '// Generated from native stage textures by tools/build_terrain_modules.py; transparent index 0.\n'
    header += '#ifndef TERRAIN_ART_H\n#define TERRAIN_ART_H\n#include <genesis.h>\n#define TERRAIN_VARIANTS 23\n'
    header += 'static const u16 TERRAIN_SOURCE_PALETTE[16]={'+','.join(hex(v) for v in palette)+'};\n'
    default=struct.unpack('>16H',(GAME/'res/insects/palette.bin').read_bytes())
    header += 'static const u8 TERRAIN_DEFAULT_MAP[16]={'+','.join(map(str,color_map(default)))+'};\n'
    header += array('TERRAIN_LAVA_ART', sets[0]+sets[1])+array('TERRAIN_MUD_ART', sets[2])+'#endif\n'
    files = {GAME/'src/elements/terrain_art.h': header.encode()}
    for name, groups in [('lava-frames',sets[:2]),('mud',sets[2:])]:
        packed=bytes((pixels[i]<<4)|pixels[i+1] for tiles in groups for pixels in tiles for i in range(0,64,2))
        files[ART/(name+'.bin')]=packed
    def png(path, im):
        buf = io.BytesIO(); im.save(buf, format='PNG'); files[path] = buf.getvalue()
    def rgba(pixels, palette=palette):
        mapping=color_map(palette)
        rgb=[tuple(v*255//7 for v in channels(c)) for c in palette]
        im = Image.new('RGBA', (8, 8)); im.putdata([(*rgb[mapping[c]], 255 if c else 0) for c in pixels]); return im
    atlas = Image.new('RGBA', (VARIANTS*8, 24))
    for row, tiles in enumerate(sets):
        for col, pixels in enumerate(tiles):
            atlas.paste(rgba(pixels), (col*8, row*8))
    png(ART/'atlas.png', atlas)
    png(ART/'atlas-nearest.png', atlas.resize((VARIANTS*8*5, 24*5), Image.Resampling.NEAREST))
    preview = Image.new('RGB', (432, 262), '#141919'); draw = ImageDraw.Draw(preview)
    draw.text((12, 8), 'TERRENOS MODULARES / PLAGUEFALL', fill='#e3d8b9')
    draw.text((12, 23), 'LAVA: PROFUNDIDADE 60G / LAMA: RENTE AO SOLO', fill='#b4a789')
    shapes = [(0, 0, 8, 4), (10, 0, 3, 5), (13, 3, 7, 2), (16, 0, 4, 1)]
    occupied = {(x, y) for rx, ry, w, h in shapes for y in range(ry, ry+h) for x in range(rx, rx+w)}
    for theme,(key,fx,fy) in enumerate([('04',224,160),('06b',208,96),('02b',224,176)]):
        top=48+theme*65;theme_palette=read_palette(key)
        theme_rgb=[tuple(v*255//7 for v in channels(c)) for c in theme_palette]
        floor=native_patch(key,fx,fy)
        draw.text((12,top),['TUNEIS','RETIRADA','DESVIO'][theme],fill='#e3d8b9')
        for y in range(top+13,top+61):
            for x in range(12,420):
                preview.putpixel((x,y),theme_rgb[floor[((y-top-13)%16)*32+(x-12)%32]])
        for kind, left in [('lava', 20), ('mud', 228)]:
            for x, y in occupied:
                mask = sum(bit for dx, dy, bit in [(0,-1,N),(1,0,E),(0,1,S),(-1,0,W)] if (x+dx,y+dy) in occupied)
                pixels = tile(kind, mask, interior=((x&3)+((y&1)<<2)) if mask==15 else 0)
                im = rgba(pixels,theme_palette); preview.paste(im, (left+x*8, top+17+y*8), im)
    draw.text((12, 248), '8x8 / PECAS CONECTAVEIS / PALETA DO CENARIO', fill='#b4a789')
    png(ART/'preview-nearest.png', preview.resize((1296, 786), Image.Resampling.NEAREST))
    files[ART/'layout.json'] = (json.dumps({'tile_size':8, 'variants_per_material':23,
        'resident_tiles':46, 'resident_bytes':1472, 'rom_art_bytes':2208,
        'source_palette':'native 06b; adapted to active scene PAL3, PAL1 fallback', 'source_palette_words':list(palette), 'style_references':{'lava':{'stage':'06b','rect':[48,120,32,16]},'mud':{'stage':'02b','rect':[32,264,32,16]}}, 'depth':{'view_degrees':60,'lava_far_wall_pixels':6,'lava_near_lip_pixels':2,'narrow_channel_wall_pixels':3,'mud_ground_level':True}, 'transparent_index':0,
        'neighbours':{'north':N,'east':E,'south':S,'west':W},
        'examples':[{'x':x,'y':y,'w':w,'h':h} for x,y,w,h in shapes]}, indent=2)+'\n').encode()
    return files


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    for path, data in generate().items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    print('Terrain: 23 connected variants/material, native map textures, scene palette adaptation verified.' if args.check else 'Terrain modules exported.')


if __name__ == '__main__':
    main()
