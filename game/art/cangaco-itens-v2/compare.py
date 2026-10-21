"""Preview the existing native grids over a real unoccupied floor sample."""
from pathlib import Path
import json,re
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
PALETTE=json.loads((ROOT/'palette.json').read_text())
IDS=['heart','bomb','shots','speed','shield','chain','ice','fire']
LABELS=['Marmita','Carga','Divisor','Servo','Capacitor','Bobina','Refil frio','Refil quente']

def legacy(item):
    data=(ROOT/'source/legacy-items_data.h').read_text()
    rows=re.findall(r'"([^"]+)"',re.search('ITEM_'+item.upper()+r'_ART\[16\].*?\{(.*?)\};',data,re.S)[1])
    legend=dict((char,int(color)) for char,color in re.findall(r"\{\s*'(.)'\s*,\s*(\d+)",re.search('ITEM_'+item.upper()+r'_LEG\[\].*?\{(.*?)\};',data,re.S)[1]))
    assert len(rows)==16 and all(len(row)==16 for row in rows)
    im=Image.new('P',(16,16));im.putpalette(sum(PALETTE,[])+[0]*720)
    im.putdata([legend.get(c,0) for row in rows for c in row]);im.info['transparency']=0
    return im

def main():
    out=Image.new('RGB',(680,40+8*76),(24,28,30));draw=ImageDraw.Draw(out)
    draw.text((12,10),'ITEM',fill='white')
    for text,x in [('ANTIGO',160),('V1',280),('V2 (NOVO)',420),('HUD 8x8',560)]:draw.text((x,10),text,fill='white')
    floor=Image.open(ROOT.parent/'cangaco-itens-v1/validation/emulator/arena-items.png').convert('RGBA').crop((40,160,56,176))
    for i,item in enumerate(IDS):
        y=40+i*76
        draw.text((12,y+24),LABELS[i],fill='white')
        variants=[legacy(item),Image.open(ROOT.parent/'cangaco-itens-v1/native'/f'{item}-world.png'),Image.open(ROOT/'native'/f'{item}-world.png')]
        for x,im in zip([160,280,420],variants):
            bg=floor.copy();bg.alpha_composite(im.convert('RGBA'))
            out.paste(bg.convert('RGB').resize((64,64),Image.Resampling.NEAREST),(x,y))
        hud=Image.open(ROOT/'native'/f'{item}-hud.png').convert('RGBA')
        block=Image.new('RGBA',(8,8),(0,0,0,255));block.alpha_composite(hud)
        out.paste(block.convert('RGB').resize((32,32),Image.Resampling.NEAREST),(568,y+16))
    out.save(ROOT/'comparison-nearest.png')
    for kind in ['world','hud']:
        im=Image.open(ROOT/'native'/f'items-{kind}.png').convert('RGBA')
        bg=Image.new('RGBA',im.size,(45,51,54,255));bg.alpha_composite(im)
        bg.resize((im.width*10,im.height*10),Image.Resampling.NEAREST).save(ROOT/f'atlas-{kind}-nearest.png')

if __name__=='__main__':main()
