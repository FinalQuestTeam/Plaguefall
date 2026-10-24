"""Static composition evidence only; does not emulate or modify production."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,struct
A=Path(__file__).resolve().parent;G=A.parents[2];O=A/'cycle-2';E=A/'review-evidence';E.mkdir(exist_ok=True)
palette=struct.unpack('>16H',(G/'res/heroi/palette.bin').read_bytes());rgb=[tuple(((v>>s)&7)*255//7 for s in (1,5,9))for v in palette]
def actor(name):
 data=(G/f'res/{name}/frames.bin').read_bytes()[2*6*768:2*6*768+768];out=Image.new('RGBA',(32,48));p=out.load()
 for base,height,yy in [(0,4,0),(16,2,32)]:
  for x in range(4):
   for y in range(height):
    tile=data[(base+x*height+y)*32:(base+x*height+y+1)*32]
    for ry in range(8):
     for rx in range(8):
      v=tile[ry*4+rx//2];v=v&15 if rx&1 else v>>4;p[x*8+rx,yy+y*8+ry]=(*rgb[v],255 if v else 0)
 return out
hero=actor('heroi');dino=actor('dinorah');hero.save(E/'damiao-production-frame.png');dino.save(E/'dinorah-production-frame.png')
for key in ['06a','06b','12']:
 d=json.loads((O/key/'manifest.json').read_text());native=Image.open(O/key/'complete-native.png').convert('RGB');closed=Image.open(O/key/'complete-closed-objectives.png').convert('RGB');opened=Image.open(O/key/'complete-open-objectives.png').convert('RGB');layout=Image.open(O/key/'layout.png').convert('RGB')
 # Full-world board preserves every native pixel and includes geometry second.
 board=Image.new('RGB',(3072,2*272+96),(17,24,27));draw=ImageDraw.Draw(board);draw.text((12,12),f'FASE {key} |3072x272 | panorama integral + objetivos + geometria',fill='white');board.paste(closed,(0,40));board.paste(layout,(0,272+72));board.save(E/f'{key}-whole-board.png')
 hud=Image.open(G/f'art/campaign-integrated-v1/escorts/ntsc/{key}-entrada.png').convert('RGB').crop((0,0,320,24))
 contact=Image.new('RGB',(3*640,3*480),(17,24,27));draw=ImageDraw.Draw(contact)
 for row,cy in enumerate([0,24,48]):
  for col,(label,cx) in enumerate([('entrada',0),('meio',1360),('saida',2752)]):
   frame=closed.convert('RGBA');py=168+row*24
   frame.alpha_composite(dino,(cx+112-8,py-8-31));frame.alpha_composite(hero,(cx+184-8,py-31));view=frame.crop((cx,cy,cx+320,cy+224)).convert('RGB');view.paste(hud,(0,0));x=col*640;y=row*480;draw.text((x+10,y+8),f'{key} {label} y{cy} | estudo estatico, sprites reais',fill='white');contact.paste(view.resize((640,448),Image.Resampling.NEAREST),(x,y+26))
 contact.save(E/f'{key}-camera-actor-board.png')
 # Every intact module is shown separately with its provenance and axis.
 modules=d['modules'];atlas=Image.new('RGB',(4*320,((len(modules)+3)//4)*220),(17,24,27));draw=ImageDraw.Draw(atlas)
 for i,m in enumerate(modules):
  x=i%4*320;y=i//4*220;im=Image.open(O/key/'modules'/f'{m["id"]}.png').convert('RGBA');im.thumbnail((300,160),Image.Resampling.NEAREST);draw.text((x+8,y+6),f'{m["id"]} {m["native_size"]} eixo:{m["repeat_axis"]}',fill='white');atlas.paste(im,(x+8,y+38),im);draw.text((x+8,y+192),str(m['source_rect']),fill='#bbd9e5')
 atlas.save(E/f'{key}-module-atlas.png')
 if key=='06b':
  for state in ['closed','collapse','open']:
   image=Image.open(O/key/f'complete-{state}-objectives.png');image.crop((896,80,1120,256)).resize((896,704),Image.Resampling.NEAREST).save(E/f'06b-station-{state}-4x.png')
manifest={'kind':'static composition studies, not emulator captures','spriteSource':'production frames.bin, east idle, PAL2; exact32x48 decode','hudSource':'existing integrated NTSC capture, top24px only','worldCameraSamples':{'x':[0,1360,2752],'y':[0,24,48]},'world':[3072,272],'footprint':[16,16],'runtimeEmulatorReviewPending':True}
(E/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
