"""Technical palette/tile export of the image_gen courtyard, no scenery drawing.

Deduplicate 8x8 tiles and, when needed, select real source-tile medoids within
the fixed VRAM budget. Both church states share the same resident tiles/palette.
"""
from pathlib import Path
import argparse, hashlib, json, re, struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

GAME=Path(__file__).resolve().parents[1]
ART=GAME/'art/phase01-courtyard-v1'
OUT=GAME/'res/courtyard'
BUDGET=560

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    sources=[Image.open(ART/'source'/name).convert('RGB').resize((256,128),Image.Resampling.LANCZOS).resize((512,256),Image.Resampling.NEAREST)
             for name in ('intact.png','damaged.png')]
    # A single curated shared 16-color 3-bit palette keeps blue doors, plaster,
    # terracotta and earth distinct despite the floor's much larger area.
    colors=[(0,0,0),(36,36,36),(36,36,73),(36,73,109),(73,109,146),
            (73,109,73),(109,109,36),(109,73,36),(146,109,73),
            (182,146,73),(219,182,109),(219,146,73),(182,73,36),
            (109,36,0),(219,219,182),(255,255,219)]
    palette=np.array(colors,dtype=np.int32)
    indexes=[]
    for source in sources:
        rgb=np.asarray(source,dtype=np.int32)
        index=((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3).argmin(axis=2).astype(np.uint8)
        indexes.append(index)
    # Damage is local: other world tiles retain the exact same background.
    indexes[1][120:,:]=indexes[0][120:,:]
    indexes[1][:120,208:]=indexes[0][:120,208:]
    tiles=np.concatenate([a.reshape(32,8,64,8).transpose(0,2,1,3).reshape(-1,64) for a in indexes])
    unique,inverse,counts=np.unique(tiles,axis=0,return_inverse=True,return_counts=True)
    if len(unique)>BUDGET:
        vectors=palette[unique].reshape(len(unique),-1).astype(np.float32)/255
        distance=np.full(len(unique),np.inf);chosen=[]
        next_index=int(counts.argmax())
        weight=np.sqrt(counts)
        for _ in range(BUDGET):
            chosen.append(next_index)
            error=((vectors-vectors[next_index])**2).mean(axis=1)
            distance=np.minimum(distance,error)
            next_index=int((distance*weight).argmax())
        chosen=np.array(chosen)
        # Pick the nearest actual source tile, with deterministic tie breaking.
        best=np.full(len(unique),np.inf);mapping=np.zeros(len(unique),dtype=np.uint16)
        for slot,index in enumerate(chosen):
            error=((vectors-vectors[index])**2).mean(axis=1)
            replace=error<best;mapping[replace]=slot;best[replace]=error[replace]
        packed=unique[chosen];tilemaps=mapping[inverse].reshape(2,32,64)
    else:
        packed=unique;tilemaps=inverse.astype(np.uint16).reshape(2,32,64)
    binary=bytes((int(t[i])<<4)|int(t[i+1]) for t in packed for i in range(0,64,2))
    words=[sum(round(rgb[c]*7/255)<<(1+4*c) for c in range(3)) for rgb in colors]
    files={'tiles.bin':binary,'map.bin':tilemaps[0].astype('>u2').tobytes(),
           'damaged.bin':tilemaps[1].astype('>u2').tobytes(),'palette.bin':struct.pack('>16H',*words)}
    # Opaque text backgrounds keep the fixed WINDOW HUD readable over roofs.
    font=(GAME/'res/intro/font.bin').read_bytes()
    files['font.bin']=bytes(((b>>4 or 1)<<4)|(b&15 or 1) for b in font)
    header='#ifndef COURTYARD_DATA_H\n#define COURTYARD_DATA_H\n#define COURTYARD_TILE_COUNT %d\n#endif\n'%len(packed)
    # Editor-friendly copies preserve tile identity and both state layers.
    ts=ET.Element('tileset',version='1.10',tiledversion='1.11.2',name='Patio',tilewidth='8',tileheight='8',tilecount=str(len(packed)),columns='16')
    ET.SubElement(ts,'image',source='tileset.png',width='128',height=str(((len(packed)+15)//16)*8))
    level=ET.Element('map',version='1.10',tiledversion='1.11.2',orientation='orthogonal',renderorder='right-down',width='64',height='32',tilewidth='8',tileheight='8',infinite='0')
    ET.SubElement(level,'tileset',firstgid='1',source='courtyard.tsx')
    for ident,(name,tilemap) in enumerate(zip(('Igreja preservada','Igreja danificada'),tilemaps),1):
        layer=ET.SubElement(level,'layer',id=str(ident),name=name,width='64',height='32',visible='1' if ident==1 else '0')
        ET.SubElement(layer,'data',encoding='csv').text='\n'+',\n'.join(','.join(str(int(v)+1) for v in row) for row in tilemap)+'\n'
    arena_source=(GAME/'src/levels/arena.c').read_text()
    solids=re.search(r'static const ArenaRect solids\[\] = \{(.*?)\n\};',arena_source,re.S).group(1)
    group=ET.SubElement(level,'objectgroup',id='3',name='Colisoes',visible='0')
    for ident,rect in enumerate(re.findall(r'\{(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\}',solids),1):
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
            decoded=packed[tilemap].reshape(32,64,8,8).transpose(0,2,1,3).reshape(256,512)
            Image.fromarray(palette[decoded].astype(np.uint8),'RGB').save(ART/(state+'-native.png'))
        atlas=np.zeros((((len(packed)+15)//16)*8,16*8),dtype=np.uint8)
        for i,tile in enumerate(packed):atlas[(i//16)*8:(i//16+1)*8,(i%16)*8:(i%16+1)*8]=tile.reshape(8,8)
        Image.fromarray(palette[atlas].astype(np.uint8),'RGB').save(ART/'tileset.png')
    report={'world':[512,256],'tiles':len(packed),'tile_bytes':len(binary),'palette_colors':len(set(colors)),
            'source_unique_tiles':len(unique),'shared_states':2,'tilemap_bytes_per_state':4096,
            'source_sha256':{name:hashlib.sha256((ART/'source'/name).read_bytes()).hexdigest() for name in ('intact.png','damaged.png')},
            'export_sha256':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
    if not args.check:(ART/'export.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
