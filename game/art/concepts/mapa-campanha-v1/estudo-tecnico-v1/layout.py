"""Croqui de interface com os glifos existentes; não cria arte de cenário."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[3]
FONT=Image.open(GAME.parent/'SGDK/res/image/font_default.png')
im=Image.new('RGB',(320,224),(0,0,0));d=ImageDraw.Draw(im)
ivory=(255,219,182);gold=(255,182,73);blue=(109,146,146)

def label(x,y,s,color=ivory):
 assert 0<=x and x+len(s)*8<=320 and 0<=y<=216
 for i,c in enumerate(s):
  g=ord(c)-32
  assert 0<=g<96
  a=FONT.crop(((g%16)*8,(g//16)*8,(g%16)*8+8,(g//16)*8+8))
  mask=a.convert('L').point(lambda v:255 if v else 0)
  im.paste(color,(x+i*8,y),mask)

d.rectangle((0,16,319,175),fill=(36,36,36))
label(8,4,'BASE INDUSTRIAL')
for i in range(4):d.rectangle((192+i*28,5,212+i*28,10),fill=gold if i==2 else blue)
pts={'8':(40,90),'9':(112,90),'10A':(192,42),'10B':(192,138),'11':(280,90)}
edges=[('8','9'),('9','10A'),('9','10B'),('10A','11'),('10B','11')]
for a,b in edges:
 color=ivory if (a,b)==('8','9') else gold if (a,b)==('9','10A') else blue
 d.line([pts[a],pts[b]],fill=(0,0,0),width=5)
 d.line([pts[a],pts[b]],fill=color,width=2)
for n,(x,y) in pts.items():
 w=8*len(n)+4
 d.rectangle((x-w//2,y-7,x+w//2,y+6),fill=(0,0,0),outline=gold if n in ('9','10A') else blue)
 label(x-len(n)*4,y-4,n,gold if n in ('9','10A') else ivory)
x,y=pts['9'];d.polygon([(x,y-10),(x-6,y-19),(x+6,y-19)],fill=gold)
x,y=pts['10A'];d.rectangle((x-17,y-10,x+17,y+9),outline=gold)
label(8,164,'ARTE REGIONAL: 320 X 160',blue)
d.line((0,176,319,176),fill=gold)
for y,s,c in [(180,'AGORA 9: ALFANDEGA',gold),(190,'PROXIMA 10A: ACESSO DOS TECNICOS',ivory),
              (200,'ROTA: VOCE SAIU SEM DANO',ivory),(212,'A SEGUIR',gold)]:
 assert 8+len(s)*8<=312
 label(8,y,s,c)
im.save(ROOT/'layout-320x224.png')
im.resize((960,672),Image.Resampling.NEAREST).save(ROOT/'layout-ampliado.png')
