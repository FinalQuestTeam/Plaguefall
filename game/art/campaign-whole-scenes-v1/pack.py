"""Image-first native conversion. Crop/resample authored full scenes; exact tile reuse.
No tile similarity replacement. Map flags are native VDP H/V attributes.
"""
from pathlib import Path
import struct,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def rgb333(im):
    return im.convert('RGB').point([round(i/255*7)*255//7 for i in range(256)]*3)
def indexed(im,size,block=2,colors=15,palette=None):
    small=rgb333(im.resize((size[0]//block,size[1]//block),Image.Resampling.LANCZOS))
    if palette is None:
        q=small.quantize(colors=colors,dither=Image.Dither.NONE)
        raw=q.getpalette();palette=[(0,0,0)]+[tuple(round(v/255*7)*255//7 for v in raw[i*3:i*3+3]) for i in range(colors)]
        palette+= [(0,0,0)]*(16-len(palette))
    palim=Image.new('P',(1,1));palim.putpalette([c for p in palette for c in p]+[0]*720)
    # Pillow's palette cube can pick a different near color in neighboring
    # cells. Exact nearest RGB avoids those conversion patterns entirely.
    pixels=list(small.getdata());lookup={c:min(range(16),key=lambda i:sum((c[k]-palette[i][k])**2 for k in range(3))) for c in set(pixels)}
    q=Image.frombytes('P',small.size,bytes(lookup[c] for c in pixels)).resize(size,Image.Resampling.NEAREST)
    q.putpalette(palim.getpalette());return q,palette

def compose_floor(im,box):
    patch=im.crop(box);out=Image.new('P',im.size);out.putpalette(im.getpalette())
    for y in range(0,im.height,patch.height):
        for x in range(0,im.width,patch.width):out.paste(patch,(x,y))
    return out

def c_array(name,typ,values):
    per=8 if typ=='u32' else 16;fmt='0x%08XUL' if typ=='u32' else '0x%04X'
    return 'static const '+typ+' '+name+'[]={\n'+''.join(','.join(fmt%v for v in values[i:i+per])+',\n' for i in range(0,len(values),per))+'};\n'

def pack(images,pal,dest,prefix,limit=640):
    assert pal[0]==(0,0,0), 'Mega Drive background index0 is transparent; reserve it for black'
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    tiles=[];lookup={};maps={}
    for name,im in images.items():
        assert im.mode=='P' and im.width%8==0 and im.height%8==0
        mp=[]
        for y in range(0,im.height,8):
            for x in range(0,im.width,8):
                patch=im.crop((x,y,x+8,y+8))
                raw=patch.tobytes()
                if raw not in lookup:
                    idx=len(tiles);tiles.append(raw)
                    for trans,flag in ((None,0),(Image.Transpose.FLIP_LEFT_RIGHT,0x800),(Image.Transpose.FLIP_TOP_BOTTOM,0x1000),(Image.Transpose.ROTATE_180,0x1800)):
                        variant=raw if trans is None else patch.transpose(trans).tobytes()
                        if variant not in lookup:lookup[variant]=idx|flag
                mp.append(lookup[raw])
        maps[name]=mp
    assert len(tiles)<=limit,(prefix,len(tiles),limit)
    data=b''.join(bytes((p[i]<<4)|p[i+1] for i in range(0,64,2)) for p in tiles)
    result=c_array(prefix+'_tiles','u32',struct.unpack('>'+str(len(data)//4)+'I',data))
    palwords=[(round(r/255*7)<<1)|(round(g/255*7)<<5)|(round(b/255*7)<<9) for r,g,b in pal]
    result+=c_array(prefix+'_palette','u16',palwords)
    (dest/'palette.bin').write_bytes(struct.pack('>16H',*palwords))
    atlas=Image.new('P',(128,((len(tiles)+15)//16)*8));atlas.putpalette([v for p in pal for v in p]+[0]*720)
    for i,p in enumerate(tiles):
        patch=Image.frombytes('P',(8,8),p);atlas.paste(patch,(i%16*8,i//16*8))
    atlas.save(dest/'sprites-8x8.png');(dest/'tiles.bin').write_bytes(data)
    stats={'tiles':len(tiles),'limit':limit,'lossy_tile_replacements':0,'maps':{}}
    for name,mp in maps.items():
        im=images[name];result+=c_array(prefix+'_'+name,'u16',mp)
        restored=Image.new('P',im.size);restored.putpalette(im.getpalette())
        for n,v in enumerate(mp):
            patch=Image.frombytes('P',(8,8),tiles[v&0x7ff]);
            if v&0x800:patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if v&0x1000:patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            restored.paste(patch,(n%(im.width//8)*8,n//(im.width//8)*8))
        assert restored.tobytes()==im.tobytes(),'tile reconstruction changed image'
        restored.save(dest/(name+'-native.png'))
        (dest/(name+'.bin')).write_bytes(struct.pack('>'+str(len(mp))+'H',*mp))
        stats['maps'][name]={'size':im.size,'sha256':hashlib.sha256(im.tobytes()).hexdigest(),'pixel_exact_reassembly':True}
    (dest/'pack.json').write_text(json.dumps(stats,indent=2)+'\n')
    return result,stats
