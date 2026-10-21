"""Technical export of image_gen item designs; no procedural sprite drawing."""
from pathlib import Path
import hashlib, json, struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
PALETTE = json.loads((GAME / 'art/cangaco-insects-sized-v3/palette.json').read_text())
IDS = ['heart', 'bomb', 'shots', 'speed', 'shield', 'chain', 'ice', 'fire']
NAMES = ['Marmita do abrigo', 'Carga de desmonte', 'Divisor de disparo',
         'Servo de passada', 'Capacitor de protecao', 'Bobina de subestacao',
         'Refil de arrefecimento', 'Refil de macarico']

def index_image(rgba):
    out = Image.new('P', rgba.size)
    out.putpalette(sum(PALETTE, []) + [0] * (768 - 48))
    out.info['transparency'] = 0
    indices = []
    for r,g,b,a in rgba.get_flattened_data():
        if a < 128:
            indices.append(0)
        else:
            indices.append(min(range(1,16), key=lambda i:
                sum((p-q)**2 for p,q in zip((r,g,b), PALETTE[i]))))
    out.putdata(indices)
    return out

def extract(source, size, right=False):
    w,h = source.size
    cut = round(w * .66)
    area = source.crop((cut,0,w,h) if right else (0,0,cut,h))
    mask = area.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    box = mask.getbbox()
    assert box, 'missing transparent isolated object'
    area = area.crop(box)
    # Register each static pickup centrally with bottom at row 15; HUD at row 7.
    factor = min(size/area.width, size/area.height)
    fitted = area.resize((max(1,round(area.width*factor)), max(1,round(area.height*factor))), Image.Resampling.NEAREST)
    frame = Image.new('RGBA', (size,size))
    frame.paste(fitted, ((size-fitted.width)//2, size-fitted.height))
    return index_image(frame), list(box)

def pack(image):
    pixels = image.load()
    words=[]
    for tx in range(image.width//8):
        for ty in range(image.height//8):
            for y in range(8):
                value=0
                for x in range(8): value=(value<<4)|pixels[tx*8+x,ty*8+y]
                words.append(value)
    return words

def export():
    world_atlas = Image.new('P',(64,32)); world_atlas.putpalette(sum(PALETTE,[])+[0]*720)
    hud_atlas = Image.new('P',(32,16)); hud_atlas.putpalette(world_atlas.getpalette())
    preview = Image.new('RGB',(624,8*64+40),(22,26,29))
    draw=ImageDraw.Draw(preview)
    draw.text((12,8),'ITEM / ARENA 16x16 (3x e 1x) / HUD 8x8 (3x e 1x)',fill=(219,219,182))
    chars=['#ifndef ITEMS_DATA_H','#define ITEMS_DATA_H',
           '// Generated from indexed PNGs by art/cangaco-itens-v1/export.py.',
           '// PAL1 unchanged; index 0 transparent. Include after items/items.h.']
    icons=['#ifndef ITEM_ICONS_DATA_H','#define ITEM_ICONS_DATA_H',
           '// Generated native 8x8 HUD counterparts; 32 bytes per icon.']
    report=[]
    expectations={}
    for i,item in enumerate(IDS):
        src=Image.open(ROOT/'source'/f'{item}.png').convert('RGBA')
        assert src.getchannel('A').getextrema()[0]==0, (item,'not transparent')
        world,wb=extract(src,16)
        hud,hb=extract(src,8,True)
        for kind,img in [('world',world),('hud',hud)]:
            path=ROOT/'native'/f'{item}-{kind}.png'
            img.save(path,transparency=0,optimize=False,bits=4)
            check=Image.open(path)
            assert check.mode=='P' and check.info['transparency']==0
            assert set(check.get_flattened_data()) <= set(range(16))
            assert check.getpalette()[:48]==sum(PALETTE,[])
            assert len(pack(check))==check.width*check.height//8
        expectations[item]={'world':list(world.get_flattened_data()),'hud':list(hud.get_flattened_data())}
        world_atlas.paste(world,((i%4)*16,(i//4)*16))
        hud_atlas.paste(hud,((i%4)*8,(i//4)*8))
        yy=40+i*64
        draw.text((12,yy+20),NAMES[i],fill=(219,219,182))
        preview.paste(world.convert('RGBA').resize((48,48),Image.Resampling.NEAREST),(240,yy),world.convert('RGBA').resize((48,48),Image.Resampling.NEAREST))
        preview.paste(world.convert('RGBA'),(312,yy+16),world.convert('RGBA'))
        preview.paste(hud.convert('RGBA').resize((24,24),Image.Resampling.NEAREST),(384,yy+12),hud.convert('RGBA').resize((24,24),Image.Resampling.NEAREST))
        preview.paste(hud.convert('RGBA'),(432,yy+20),hud.convert('RGBA'))
        upper=item.upper()
        chars += [f'\n// {NAMES[i]}',f'static const char *const ITEM_{upper}_ART[16] =', '{']
        pix=list(world.get_flattened_data())
        chars += ['    "'+''.join('.' if p==0 else format(p,'x') for p in pix[y*16:y*16+16])+'",' for y in range(16)]
        chars += ['};', f'static const TilePixel ITEM_{upper}_LEG[] = {{ '+', '.join("{ '%x', %d }"%(p,p) for p in sorted(set(pix)-{0}))+' };']
        icons += [f'\nstatic const u32 ITEM_{upper}_ICON_DATA[8] = {{',
                  '    '+', '.join(f'0x{v:08X}' for v in pack(hud)), '};']
        report.append(dict(id=i,key=item,name=NAMES[i],world_size=list(world.size),hud_size=list(hud.size),
            world_visible_colors=sorted(set(world.get_flattened_data())-{0}),hud_visible_colors=sorted(set(hud.get_flattened_data())-{0}),
            source_sha256=hashlib.sha256((ROOT/'source'/f'{item}.png').read_bytes()).hexdigest(),
            source_crop_world=wb,source_crop_hud=hb))
    for name,img in [('items-world.png',world_atlas),('items-hud.png',hud_atlas)]:img.save(ROOT/'native'/name,transparency=0,bits=4)
    preview.save(ROOT/'preview-nearest.png')
    (GAME/'src/system/video/sprites/items_data.h').write_text('\n'.join(chars+['\n#endif','']))
    (GAME/'src/system/video/sprites/item_icons_data.h').write_text('\n'.join(icons+['\n#endif','']))
    (ROOT/'validation/render-expectations.json').write_text(json.dumps(expectations)+'\n')
    (ROOT/'palette.json').write_text(json.dumps(PALETTE,indent=2)+'\n')
    (ROOT/'palette-md.bin').write_bytes((GAME/'res/insects/palette.bin').read_bytes())
    (ROOT/'validation/assets.json').write_text(json.dumps(dict(passed=True,tool='built-in image_gen',
        processing='Alpha crop, nearest-neighbor registration, shared PAL1 indexing; independent generated HUD drawings.',
        palette_shared=True,transparent_index=0,items=report),indent=2)+'\n')
    print(json.dumps(dict(passed=True,items=8,native_pngs=18,world_bytes=8*128,hud_bytes=8*32)))

if __name__=='__main__':export()
