"""Convert the ImageGen master into sixteen native32x32 PAL1 sprites."""
from pathlib import Path
import argparse, hashlib, json, struct
from PIL import Image

GAME=Path(__file__).resolve().parents[1]
ART=GAME/'art/sinal-ultimo-chao-v1/native'
NAMES=('mandacaru','engrenagem','santa','sauva','chapeu','radio','capela','mutuca',
       'barro','foguete','ex-voto','escorpiao','cordel','alicate','sino','sindicato')

def build(check=False):
    source=ART/'source/symbols-master.png'
    master=Image.open(source).convert('RGBA')
    # Keep alphabet index10 compatible with existing passwords; replace its art only.
    heart_source=ART/'source/heart-logo-master.png'
    radio_source=ART/'source/radio-master-v2.png'
    raw_palette=(GAME/'res/insects/palette.bin').read_bytes()
    colors=[tuple(round(((word>>shift)&7)*255/7) for shift in (1,5,9))
            for word in struct.unpack('>16H',raw_palette)]
    # Index0 is transparent. Index11 is a duplicate black, also unused.
    usable=[i for i in range(1,16) if any(colors[i])]
    palette=[value for color in colors for value in color]+[0]*(768-48)
    tiles=bytearray();atlas=Image.new('P',(128,128));atlas.putpalette(palette)
    for index,name in enumerate(NAMES):
        col,row=index%4,index//4
        # The generated master uses uneven row gutters; keep adjacent art out.
        rows=(0,315,568,835,master.height)
        cell=master.crop((round(col*master.width/4),rows[row],
                          round((col+1)*master.width/4),rows[row+1]))
        if name=='ex-voto':cell=Image.open(heart_source).convert('RGBA')
        if name=='radio':cell=Image.open(radio_source).convert('RGBA')
        bbox=cell.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        assert bbox,(name,'empty source')
        icon=cell.crop(bbox);ratio=min(28/icon.width,28/icon.height)
        # Preserve the radio's deliberately separated hard pixel clusters.
        sampling=Image.Resampling.NEAREST if name=='radio' else Image.Resampling.LANCZOS
        icon=icon.resize((max(1,round(icon.width*ratio)),max(1,round(icon.height*ratio))),sampling)
        pixels=[0]*1024;ox=(32-icon.width)//2;oy=(32-icon.height)//2
        for y in range(icon.height):
            for x in range(icon.width):
                r,g,b,a=icon.getpixel((x,y))
                if a>=128:
                    pixels[(oy+y)*32+ox+x]=min(usable,key=lambda i:sum((v-c)**2 for v,c in zip((r,g,b),colors[i])))
        # Match the pale silhouette of the game's existing item sprites.
        outlined=pixels.copy()
        for y in range(1,31):
            for x in range(1,31):
                at=y*32+x
                if not pixels[at] and any(pixels[at+d] for d in (-32,32,-1,1)):outlined[at]=1
        image=Image.new('P',(32,32));image.putpalette(palette);image.putdata(outlined)
        assert 20<sum(bool(p) for p in outlined)<1000
        assert not any(outlined[:32]+outlined[-32:]+outlined[::32]+outlined[31::32])
        path=ART/(name+'-32.png')
        if check:
            existing=Image.open(path)
            assert existing.size==(32,32) and existing.mode=='P' and existing.info.get('transparency')==0,path
            assert existing.tobytes()==bytes(outlined),path
            assert existing.getpalette()[:48]==palette[:48],path
        else:
            image.save(path,bits=4,transparency=0)
            if name=='radio':
                image.convert('RGBA').resize((256,256),Image.Resampling.NEAREST).save(ART/'radio-preview.png')
        atlas.paste(image,(col*32,row*32))
        # SGDK sprite order: tile columns first, then tile rows.
        for tx in range(4):
            for ty in range(4):
                for py in range(8):
                    for px in range(0,8,2):
                        at=(ty*8+py)*32+tx*8+px
                        tiles.append((outlined[at]<<4)|outlined[at+1])
    assert len(tiles)==8192
    target=GAME/'res/signal/icons.bin'
    if check:assert target.read_bytes()==tiles,target
    else:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tiles)
        atlas.save(ART/'atlas-128.png',bits=4,transparency=0)
        atlas.convert('RGBA').resize((1024,1024),Image.Resampling.NEAREST).save(ART/'atlas-preview.png')
        (ART/'manifest.json').write_text(json.dumps({'size':[32,32],'count':16,'tiles':256,
            'rom_bytes':8192,'vram_visible_tiles':96,'palette':'res/insects/palette.bin',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_overrides':{'ex-voto':{'source':'source/heart-logo-master.png',
                'sha256':hashlib.sha256(heart_source.read_bytes()).hexdigest(),
                'reference':'../../menu-logo-v1/originals/plaguefall-menu-native-v2.png'},
                'radio':{'source':'source/radio-master-v2.png',
                    'sha256':hashlib.sha256(radio_source.read_bytes()).hexdigest(),
                    'sampling':'nearest','prompts':'../prompts-radio-v2.json'}},
            'symbols':NAMES},ensure_ascii=False,indent=2)+'\n')
    print('Signal icons:16 x32x32, PAL1,256 ROM tiles/8192 bytes,96 visible VRAM tiles; verified.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    build(parser.parse_args().check)
