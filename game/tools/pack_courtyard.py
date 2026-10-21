"""Native 8x8 module export from image_gen source art.

Assemble generated modules at 512x384, quantize once to hardware colors and
deduplicate exactly. Never halve native detail or replace a tile by a medoid.
"""
from pathlib import Path
import argparse, hashlib, json, re, struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

GAME=Path(__file__).resolve().parents[1]
ART=GAME/'art/phase01-courtyard-v2'
OUT=GAME/'res/courtyard'
BUDGET=640
WIDTH,HEIGHT=512,384
ROWS,COLS=HEIGHT//8,WIDTH//8

def assemble(source):
    """Place generated 8px modules into the game map; no fuzzy tile swaps."""
    canvas=np.empty((HEIGHT,WIDTH),dtype=np.uint8)
    def repeat(rect,dest):
        sx,sy,w,h=rect;x,y,dw,dh=dest
        patch=source[sy:sy+h,sx:sx+w]
        canvas[y:y+dh,x:x+dw]=np.tile(patch,((dh+h-1)//h,(dw+w-1)//w))[:dh,:dw]
    def copy(rect):
        x,y,w,h=rect;canvas[y:y+h,x:x+w]=source[y:y+h,x:x+w]
    repeat((224,224,32,32),(0,0,512,384))
    for y in range(0,384,32):
        for x in range(0,512,32):
            if ((x//32)*7+(y//32)*3)%5<2:
                canvas[y:y+32,x:x+32]=source[192:224,320:352]
    repeat((240,8,64,32),(0,0,512,48))
    repeat((240,48,32,56),(216,48,280,56))
    copy((16,0,200,112))
    # Repeat the roof's generated tile motifs while preserving its outer
    # silhouette, ridge, windows, doors and bell gable pixel-for-pixel.
    repeat((80,16,16,16),(48,16,128,16))
    repeat((80,48,16,16),(48,48,128,16))
    copy((272,72,56,40));copy((368,48,120,56))
    repeat((0,160,16,32),(0,48,16,320))
    repeat((496,160,16,32),(496,48,16,320))
    # Move the generated bottom wall out of the combat floor. The former
    # bottom props/vegetation are not invisible solid boxes in the new map.
    repeat((144,336,32,16),(0,368,512,16))
    # The corners and gate must share the wall's exact +32px translation.
    # A straight strip at the corners and a gate offset by +24px broke the cap.
    canvas[360:384,:16]=source[328:352,:16]
    canvas[360:384,496:512]=source[328:352,496:512]
    canvas[368:384,208:304]=source[336:352,208:304]
    return canvas

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    sources=[Image.open(ART/'source'/name).convert('RGB').resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)
             for name in ('intact.png','damaged.png')]
    # A single curated shared 16-color 3-bit palette keeps blue doors, plaster,
    # terracotta and earth distinct despite the floor's much larger area.
    colors=[(0,0,0),(36,36,36),(36,36,73),(36,73,109),(73,109,146),
            (73,109,73),(109,109,36),(109,73,36),(146,109,73),
            (182,146,73),(219,182,109),(219,146,73),(182,73,36),
            (109,36,0),(219,219,182),(255,255,219)]
    palette=np.array(colors,dtype=np.int32)
    indexes=[];quantized=[]
    for source in sources:
        rgb=np.asarray(source,dtype=np.int32)
        index=((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3).argmin(axis=2).astype(np.uint8)
        quantized.append(index);indexes.append(assemble(index))
    # Damage is local: other world tiles retain the exact same background.
    indexes[1]=indexes[0].copy()
    indexes[1][8:72,144:216]=quantized[1][8:72,144:216]
    tiles=np.concatenate([a.reshape(ROWS,8,COLS,8).transpose(0,2,1,3).reshape(-1,64) for a in indexes])
    unique,inverse,counts=np.unique(tiles,axis=0,return_inverse=True,return_counts=True)
    assert len(unique)<=BUDGET, f'{len(unique)} tiles exceed the lossless budget {BUDGET}; simplify modules, never substitute fuzzy tiles'
    packed=unique;tilemaps=inverse.astype(np.uint16).reshape(2,ROWS,COLS)
    binary=bytes((int(t[i])<<4)|int(t[i+1]) for t in packed for i in range(0,64,2))
    words=[sum(round(rgb[c]*7/255)<<(1+4*c) for c in range(3)) for rgb in colors]
    files={'tiles.bin':binary,'map.bin':tilemaps[0].astype('>u2').tobytes(),
           'damaged.bin':tilemaps[1].astype('>u2').tobytes(),'palette.bin':struct.pack('>16H',*words)}
    # The opening and arena now share the same opaque font in ROM.
    font=(GAME/'res/intro/font.bin').read_bytes()
    assert all((b>>4) and (b&15) for b in font), 'Shared HUD font must stay opaque'
    header='#ifndef COURTYARD_DATA_H\n#define COURTYARD_DATA_H\n#define COURTYARD_TILE_COUNT %d\n#define COURTYARD_MAP_ROWS 48\n#define COURTYARD_DAMAGE_COLS 27\n#define COURTYARD_DAMAGE_ROWS 14\n#endif\n'%len(packed)
    # Editor-friendly copies preserve tile identity and both state layers.
    ts=ET.Element('tileset',version='1.10',tiledversion='1.11.2',name='Patio',tilewidth='8',tileheight='8',tilecount=str(len(packed)),columns='16')
    ET.SubElement(ts,'image',source='tileset.png',width='128',height=str(((len(packed)+15)//16)*8))
    level=ET.Element('map',version='1.10',tiledversion='1.11.2',orientation='orthogonal',renderorder='right-down',width='64',height='48',tilewidth='8',tileheight='8',infinite='0')
    ET.SubElement(level,'tileset',firstgid='1',source='courtyard.tsx')
    for ident,(name,tilemap) in enumerate(zip(('Igreja preservada','Igreja danificada'),tilemaps),1):
        layer=ET.SubElement(level,'layer',id=str(ident),name=name,width='64',height='48',visible='1' if ident==1 else '0')
        ET.SubElement(layer,'data',encoding='csv').text='\n'+',\n'.join(','.join(str(int(v)+1) for v in row) for row in tilemap)+'\n'
    arena_source=(GAME/'src/levels/arena.c').read_text()
    solids=re.search(r'static const ArenaRect solids\[\] = \{(.*?)\n\};',arena_source,re.S).group(1)
    group=ET.SubElement(level,'objectgroup',id='3',name='Colisoes',visible='0')
    for ident,rect in enumerate(re.findall(r'\{(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(FALSE|TRUE)\}',solids),1):
        ET.SubElement(group,'object',id=str(ident),name='Obstaculo '+str(ident),x=rect[0],y=rect[1],width=rect[2],height=rect[3])
    editor={'courtyard.tsx':ET.tostring(ts,encoding='utf-8',xml_declaration=True),'phase01.tmx':ET.tostring(level,encoding='utf-8',xml_declaration=True)}
    target=GAME/'src/levels/courtyard_data.h'
    if args.check:
        assert target.read_text()==header
        for name,content in files.items():assert (OUT/name).read_bytes()==content,name
        for name,content in editor.items():assert (ART/name).read_bytes()==content,name
    else:
        OUT.mkdir(exist_ok=True);target.write_text(header)
        for name,content in files.items():(OUT/name).write_bytes(content)
        for name,content in editor.items():(ART/name).write_bytes(content)
        for state,tilemap in zip(('intact','damaged'),tilemaps):
            decoded=packed[tilemap].reshape(ROWS,COLS,8,8).transpose(0,2,1,3).reshape(HEIGHT,WIDTH)
            Image.fromarray(palette[decoded].astype(np.uint8),'RGB').save(ART/(state+'-native.png'))
        atlas=np.zeros((((len(packed)+15)//16)*8,16*8),dtype=np.uint8)
        for i,tile in enumerate(packed):atlas[(i//16)*8:(i//16+1)*8,(i%16)*8:(i%16+1)*8]=tile.reshape(8,8)
        Image.fromarray(palette[atlas].astype(np.uint8),'RGB').save(ART/'tileset.png')
    report={'world':[WIDTH,HEIGHT],'tiles':len(packed),'tile_bytes':len(binary),'palette_colors':len(set(colors)),
            'source_unique_tiles':len(unique),'shared_states':2,'tilemap_bytes_per_state':ROWS*COLS*2,'native_pixel_scale':1,'lossy_tile_replacements':0,
            'source_sha256':{name:hashlib.sha256((ART/'source'/name).read_bytes()).hexdigest() for name in ('intact.png','damaged.png')},
            'export_sha256':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
    if not args.check:(ART/'export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
