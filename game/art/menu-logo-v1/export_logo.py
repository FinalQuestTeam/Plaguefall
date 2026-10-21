"""Reduce the approved option B to a transparent, single-palette menu logo."""
from pathlib import Path
import argparse, hashlib, importlib.util, json
import numpy as np
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
SOURCE=ROOT/'originals/plaguefall-menu-native-v2.png'
TARGET=GAME/'src/system/video/sprites/menulogo_data.h'
spec=importlib.util.spec_from_file_location('title_palette',ROOT.parent/'title-caatinga-v1/export_title.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def export():
    source=Image.open(SOURCE).convert('RGBA')
    source=source.crop(source.getchannel('A').point(lambda a: 255 if a>=128 else 0).getbbox())
    fitted=ImageOps.contain(source,(128,88),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(128,88))
    canvas.paste(fitted,((128-fitted.width)//2,(88-fitted.height)//2))
    rgba=np.asarray(canvas).astype(np.int32)
    visible=rgba[:,:,3]>=96
    pixels=rgba[:,:,:3]*rgba[:,:,3,None]//255
    # Keep real black outlines opaque; only alpha-zero backdrop is transparent.
    candidates=[tuple(map(int,c)) for c in helper.palette(pixels[visible]) if np.any(c)]
    # The small molten fissure must not lose its red/orange inks to the much
    # larger ivory wordmark when the palette is quantized by frequency.
    core_colors=[(255,36,0),(255,109,0)]
    opaque=list(candidates)
    opaque.extend(c for c in core_colors if c not in opaque)
    while len(opaque)>14:
        colors=np.array([(0,0,0)]+opaque,dtype=np.int32)
        distances=((pixels[visible][:,None,:]-colors[None,:,:])**2).sum(axis=2)
        nearest=distances.argmin(axis=1)
        ordered=np.sort(distances,axis=1)
        cost=[(int((ordered[nearest==i+1,1]-ordered[nearest==i+1,0]).sum()),i)
              for i,c in enumerate(opaque) if c not in core_colors]
        opaque.pop(min(cost)[1])
    pal=np.array([(0,0,0),(0,0,0)]+opaque+[(0,0,0)]*(14-len(opaque)),dtype=np.int32)
    indices=((pixels[:,:,None]-pal[None,None,1:])**2).sum(axis=3).argmin(axis=2).astype('uint8')+1
    indices[~visible]=0
    tiles=indices.reshape(11,8,16,8).transpose(0,2,1,3).reshape(176,8,8)
    unique,lookup,tilemap=[],{},[]
    for tile in tiles:
        key=tile.tobytes()
        if key not in lookup:
            lookup[key]=len(unique)
            unique.append(tile)
        tilemap.append(lookup[key])
    words=[]
    for tile in unique:
        for row in tile:
            word=0
            for index in row: word=(word<<4)|int(index)
            words.append(word)
    header='''// Generated from the menu-size reconstruction of approved option B by art/menu-logo-v1/export_logo.py.
#ifndef MENULOGO_DATA_H
#define MENULOGO_DATA_H
#include <genesis.h>
#define MENULOGO_TILES_W 16
#define MENULOGO_TILES_H 11
#define MENULOGO_TILES '''+str(len(unique))+'''
#define MENULOGO_X 1
#define MENULOGO_Y 0
static const u16 MENULOGO_PAL[16] = { '''+', '.join(f'0x{v:03X}' for v in helper.words(pal))+''' };
static const u8 MENULOGO_MAP[MENULOGO_TILES_W * MENULOGO_TILES_H] = { '''+', '.join(map(str,tilemap))+''' };
static const u32 MENULOGO_PIXELS[MENULOGO_TILES * 8] = {
'''
    for offset in range(0,len(words),8):
        header+='    '+', '.join(f'0x{word:08X}' for word in words[offset:offset+8])+',\n'
    header+='};\n#endif\n'
    image=Image.fromarray(indices,mode='P');image.putpalette(pal.astype('uint8').flatten().tolist()+[0]*(768-48));image.info['transparency']=0
    return header,image,dict(source=str(SOURCE.relative_to(GAME)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),canvas=[128,88],position=[8,0],tiles=len(unique),tile_bytes=len(unique)*32,palette='PAL3, index 0 transparent',approved_art='B — Ex-voto de metal, reconstructed for 128x88 menu display',header_sha256=hashlib.sha256(header.encode()).hexdigest())
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    header,image,report=export()
    if args.check:
        assert TARGET.read_text()==header
        saved=Image.open(ROOT/'logo-native.png');assert saved.tobytes()==image.tobytes() and saved.info['transparency']==0
    else:
        TARGET.write_text(header);image.save(ROOT/'logo-native.png',bits=4,transparency=0)
        image.convert('RGBA').resize((512,352),Image.Resampling.NEAREST).save(ROOT/'logo-4x.png')
        (ROOT/'export.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False))
