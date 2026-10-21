"""Technical export of image_gen item designs; no procedural sprite drawing."""
from pathlib import Path
import hashlib, json, struct, re
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
PALETTE = json.loads((GAME / 'art/cangaco-insects-sized-v3/palette.json').read_text())
IDS = ['heart', 'bomb', 'shots', 'speed', 'shield', 'chain', 'ice', 'fire']
NAMES = ['Marmita do abrigo', 'Carga de desmonte', 'Divisor de disparo',
         'Servo de passada', 'Capacitor de protecao', 'Bobina de subestacao',
         'Refil de arrefecimento', 'Refil de macarico']

def index_image(rgba, allowed):
    out = Image.new('P', rgba.size)
    out.putpalette(sum(PALETTE, []) + [0] * (768 - 48))
    out.info['transparency'] = 0
    indices = []
    for r,g,b,a in rgba.get_flattened_data():
        if a < 128:
            indices.append(0)
        else:
            indices.append(min(allowed, key=lambda i:
                sum((p-q)**2 for p,q in zip((r,g,b), PALETTE[i]))))
    out.putdata(indices)
    return out

def source_boxes(source):
    # Alpha connectivity selects the two designed objects and rejects output specks.
    mask=source.getchannel('A').point(lambda a:255 if a>=192 else 0)
    step=4
    small=mask.resize((source.width//step,source.height//step),Image.Resampling.NEAREST)
    w,h=small.size;bits=bytearray(small.tobytes());components=[]
    for seed in range(len(bits)):
        if not bits[seed]:continue
        todo=[seed];bits[seed]=0;count=0;l=r=seed%w;t=b=seed//w
        while todo:
            pos=todo.pop();x=pos%w;y=pos//w;count+=1
            l=min(l,x);r=max(r,x);t=min(t,y);b=max(b,y)
            for yy in range(max(0,y-1),min(h,y+2)):
                for xx in range(max(0,x-1),min(w,x+2)):
                    nxt=yy*w+xx
                    if bits[nxt]:bits[nxt]=0;todo.append(nxt)
        components.append((count,(max(0,(l-1)*step),max(0,(t-1)*step),min(source.width,(r+2)*step),min(source.height,(b+2)*step))))
    selected=sorted(sorted(components,reverse=True)[:2],key=lambda c:c[1][0])
    assert len(selected)==2 and selected[1][0]>=selected[0][0]*.03,selected
    boxes=[]
    for count,box in selected:
        sub=mask.crop(box).getbbox()
        boxes.append((box[0]+sub[0],box[1]+sub[1],box[0]+sub[2],box[1]+sub[3]))
    assert boxes[0][2]<boxes[1][0],boxes
    return boxes

def extract(source, size, box, allowed):
    area=source.crop(box)
    factor=min(size/area.width,size/area.height)
    fitted=area.resize((max(1,round(area.width*factor)),max(1,round(area.height*factor))),Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(size,size))
    frame.paste(fitted,((size-fitted.width)//2,size-fitted.height))
    return index_image(frame,allowed),list(box)

def boundary_stats(image):
    pixels=image.load();edges=[]
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x,y] and any(xx<0 or yy<0 or xx>=image.width or yy>=image.height or pixels[xx,yy]==0
                for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]):
                edges.append(pixels[x,y])
    return dict(boundary_pixels=len(edges),white_boundary_pixels=edges.count(1),
                white_boundary_fraction=round(edges.count(1)/len(edges),4))

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
           '// Generated from indexed PNGs by art/cangaco-itens-v2/export.py.',
           '// PAL1 unchanged; index 0 transparent. Include after items/items.h.']
    icons=['#ifndef ITEM_ICONS_DATA_H','#define ITEM_ICONS_DATA_H',
           '// Generated native 8x8 HUD counterparts; 32 bytes per icon.']
    specs={v['id']:v for v in json.loads((ROOT/'generation.json').read_text())}
    world_glyphs=json.loads((ROOT/'source/world-glyphs.json').read_text())
    hud_glyphs=json.loads((ROOT/'source/hud-glyphs.json').read_text())
    report=[]
    expectations={}
    for i,item in enumerate(IDS):
        src=Image.open(ROOT/'source'/f'{item}.png').convert('RGBA')
        assert src.getchannel('A').getextrema()[0]==0, (item,'not transparent')
        boxes=source_boxes(src)
        allowed=specs[item]['indices']
        world_draft,wb=extract(src,16,boxes[0],allowed)
        # Final editable native grid: hand-reviewed perimeter, like the legacy art.
        rows=world_glyphs[item]
        assert len(rows)==16 and all(len(row)==16 for row in rows)
        world=Image.new('P',(16,16));world.putpalette(world_draft.getpalette());world.info['transparency']=0
        world.putdata([0 if c=='.' else int(c,16) for row in rows for c in row])
        assert boundary_stats(world)['white_boundary_fraction']==1
        hud_draft,hb=extract(src,8,boxes[1],allowed)
        # Native char-maps extend the game's original editable 8x8 icon system.
        rows=hud_glyphs[item]
        assert len(rows)==8 and all(len(row)==8 for row in rows)
        hud=Image.new('P',(8,8));hud.putpalette(world.getpalette());hud.info['transparency']=0
        hud.putdata([0 if c=='.' else int(c,16) for row in rows for c in row])
        assert boundary_stats(hud)['white_boundary_fraction']==1
        for kind,img in [('world',world),('hud',hud)]:
            path=ROOT/'native'/f'{item}-{kind}.png'
            img.save(path,transparency=0,optimize=False,bits=4)
            check=Image.open(path)
            assert check.mode=='P' and check.info['transparency']==0
            assert set(check.get_flattened_data()) <= set(range(16))
            assert check.getpalette()[:48]==sum(PALETTE,[])
            assert len(pack(check))==check.width*check.height//8
        expectations[item]={'world':list(world.get_flattened_data()),'hud':list(hud.get_flattened_data())}
        assert len(set(world.get_flattened_data())-{0})<=3
        assert len(set(hud.get_flattened_data())-{0})<=3
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
            source_crop_world=wb,source_crop_hud=hb,world_contour=boundary_stats(world),hud_contour=boundary_stats(hud)))
    for name,img in [('items-world.png',world_atlas),('items-hud.png',hud_atlas)]:img.save(ROOT/'native'/name,transparency=0,bits=4)
    preview.save(ROOT/'preview-nearest.png')
    (GAME/'src/system/video/sprites/items_data.h').write_text('\n'.join(chars+['\n#endif','']))
    (GAME/'src/system/video/sprites/item_icons_data.h').write_text('\n'.join(icons+['\n#endif','']))
    (ROOT/'validation/render-expectations.json').write_text(json.dumps(expectations)+'\n')
    (ROOT/'palette.json').write_text(json.dumps(PALETTE,indent=2)+'\n')
    (ROOT/'palette-md.bin').write_bytes((GAME/'res/insects/palette.bin').read_bytes())
    (ROOT/'validation/assets.json').write_text(json.dumps(dict(passed=True,tool='built-in image_gen',
        processing='Alpha component isolation; nearest-neighbor registration; three visible colors per item from unchanged PAL1; image_gen designs refined in editable native char-maps (16x16 and 8x8), like the original icons; complete white perimeter verified on final grids.',
        palette_shared=True,transparent_index=0,items=report),indent=2)+'\n')
    print(json.dumps(dict(passed=True,items=8,native_pngs=18,world_bytes=8*128,hud_bytes=8*32)))

if __name__=='__main__':export()
