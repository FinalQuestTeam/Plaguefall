"""Inspection boards: the entire map and real-camera scale, with the baseline."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
A=Path(__file__).resolve().parent
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
catalog=json.loads((A/'manifest.json').read_text())
captures=json.loads((A/'captures/ntsc/capture-report.json').read_text())
assert catalog['rom_sha256']==captures['rom_sha256']
for phase in ('3','6A','6B','9','12'):
    before=Image.open(A/'baseline'/f'{phase}-complete.png').convert('RGB')
    after=Image.open(A/'maps'/f'{phase}-complete.png').convert('RGB')
    d=next(p for p in captures['phases'] if p['phase']==phase)
    landmarks=[s for s in d['samples'] if s['row']==3]
    sweep=[s for s in d['samples'] if s['row']==1]
    selected=landmarks[:6]
    selected+= [sweep[len(sweep)//3],sweep[len(sweep)*2//3]]
    selected=selected[:8]
    h1=before.height//2;h2=after.height//2;camsY=130+h1+h2
    board=Image.new('RGB',(1600,camsY+2*254+44),'#101c22');dr=ImageDraw.Draw(board)
    dr.text((24,16),f'FASE {phase} | composição completa e câmeras reais da ROM',font=font,fill='#f0ead7')
    dr.text((24,47),'Baseline reprovado',font=small,fill='#dcaa94')
    for im,y in [(before,68),(after,104+h1)]:
        im=im.resize((im.width//2,im.height//2),Image.Resampling.NEAREST);board.paste(im,((1600-im.width)//2,y))
    dr.text((24,80+h1),'Nova composição nativa',font=small,fill='#9edbb5')
    for i,s in enumerate(selected):
        x=32+(i%4)*392;y=camsY+(i//4)*254
        board.paste(Image.open(A/'captures/ntsc'/s['path']).convert('RGB'),(x,y))
        dr.text((x,y+228),s['label']+' · '+','.join(map(str,s['camera'])),font=small,fill='#c2cecb')
    dr.text((24,board.height-25),'SHA256 '+catalog['rom_sha256'],font=small,fill='#94aaa9')
    board.save(A/'boards'/f'{phase}-review.png')
print('Prepared five whole-map / actual-camera inspection boards')
