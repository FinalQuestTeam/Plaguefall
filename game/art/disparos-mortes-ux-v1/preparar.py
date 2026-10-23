"""Proposal exports only. Never writes src/, res/ or out/."""
from pathlib import Path
from PIL import Image
import json, shutil, math

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
OUT=ROOT/'assets'
OUT.mkdir(exist_ok=True)
PAL=json.loads((GAME/'art/cangaco-insects-sized-v3/palette.json').read_text())
MAPS={
 'player':['........','........','..BBBB..','.B9911B.','.B9911B.','..BBBB..','........','........'],
 'torreao':['........','........','.BB.....','BCBC11B.','.BCC1B..','..BB....','........','........'],
 'fuzileiro':['........','........','.B.B....','BCBC11B.','.BCC1B..','.B.B....','........','........'],
 'artilheiro':['........','........','.BBB....','BCBC11B.','BCC11B..','.BBB....','........','........'],
 'boss':['........','..BB....','.BCCB...','BCBC11B.','BCC11B..','.BCCB...','..BB....','........']
}
DIAG={
 'player':['........','........','..BB....','..B9B...','...B1B..','....BB..','........','........'],
 'spine':['........','.BB.....','.BCB....','..BCB...','...C1B..','...B11B.','.....BB.','........']
}
PROFILES=[('player','Damião',9),('torreao','Torreão',3),('fuzileiro','Fuzileiro',5),('artilheiro','Artilheiro',8),('boss','Escorpião',2)]
def tile(rows,color):
 im=Image.new('RGBA',(8,8))
 for y,row in enumerate(rows):
  assert len(row)==8
  for x,c in enumerate(row):
   if c!='.':im.putpixel((x,y),tuple(PAL[color if c=='C' else 11 if c=='B' else int(c,16)])+(255,))
 return im
def directions(h,d):
 # E,SE,S,SW,W,NW,N,NE. Three canonical tiles, hardware flips.
 v=h.transpose(Image.Transpose.TRANSPOSE)
 return [h,d,v,d.transpose(Image.Transpose.FLIP_LEFT_RIGHT),h.transpose(Image.Transpose.FLIP_LEFT_RIGHT),d.transpose(Image.Transpose.ROTATE_180),v.transpose(Image.Transpose.FLIP_TOP_BOTTOM),d.transpose(Image.Transpose.FLIP_TOP_BOTTOM)]
atlas=Image.new('RGBA',(64,40))
for r,(key,name,col) in enumerate(PROFILES):
 h=tile(MAPS[key],col);d=tile(DIAG['player' if key=='player' else 'spine'],col)
 for i,im in enumerate(directions(h,d)):atlas.paste(im,(8*i,8*r))
atlas.save(OUT/'disparos-8direcoes.png')
atlas.resize((768,480),Image.Resampling.NEAREST).save(OUT/'disparos-12x.png')
bone=Image.new('RGBA',(64,40))
for r,(key,name,col) in enumerate(PROFILES):
 h=tile(['........','........','..BBBBB.','.B99111B','..BBBBB.','........','........','........'] if key=='player' else ['........','........','.BBB....','BCC1111B','.BBB....','........','........','........'],col)
 d=tile(DIAG['player' if key=='player' else 'spine'],col)
 for i,im in enumerate(directions(h,d)):bone.paste(im,(8*i,8*r))
bone.save(OUT/'disparos-osseo.png')
for name,col in [('player',4),('enemy',5)]:
 im=Image.new('RGBA',(8,8))
 for y in range(8):
  for x in range(8):
   if (2*x-7)**2+(2*y-7)**2<=49:im.putpixel((x,y),tuple(PAL[col])+(255,))
 im.save(OUT/f'atual-{name}.png')
for key,_,_ in PROFILES[1:]:
 src='sq_red' if key=='torreao' else 'tri_red' if key=='fuzileiro' else 'pen_red' if key=='artilheiro' else 'boss'
 im=Image.open(GAME/f'art/cangaco-insects-sized-v3/enemies/{src}/{src}.png').convert('RGBA')
 size=im.width//6
 im.crop((0,4*size,size,5*size)).save(OUT/f'{key}.png')
hero=Image.open(GAME/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png').convert('RGBA')
hero.crop((0,2*96,32,2*96+48)).save(OUT/'hero.png')
capture=GAME/'art/radio-dialogos-ux-v1/integracao/validation-frozen/interface-ntsc/resumed-1.png'
shutil.copy2(capture,OUT/'cenario.png')
# Imagegen concepts: crop, remove neutral background and quantize for a size study.
# These derivatives are not approved runtime animation drawings.
src=Image.open(ROOT/'source/mortes-concept.png').convert('RGB')
for row,name,size in [(0,'leve',16),(1,'blindado',32)]:
 frames=[]
 for col in range(4):
  cell=src.crop((round(col*src.width/4),round(row*src.height/2),round((col+1)*src.width/4),round((row+1)*src.height/2)))
  rgba=cell.convert('RGBA');mask=Image.new('L',cell.size)
  mask.putdata([255 if max(p)-min(p)>22 or min(p)>90 else 0 for p in cell.getdata()])
  rgba.putalpha(mask);frames.append(rgba.crop(mask.getbbox()))
 scale=min((size-2)/max(f.width for f in frames),(size-2)/max(f.height for f in frames))
 strip=Image.new('RGBA',(size*4,size))
 for n,im in enumerate(frames):
  im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
  data=[]
  for p in im.getdata():
   if not p[3]:data.append((0,0,0,0));continue
   c=min(PAL[1:],key=lambda c:sum((p[k]-c[k])**2 for k in range(3)))
   data.append(tuple(c)+(255,))
  im.putdata(data);strip.paste(im,(n*size+(size-im.width)//2,size-im.height))
 strip.save(OUT/f'morte-{name}.png')
 strip.resize((size*4*6,size*6),Image.Resampling.NEAREST).save(OUT/f'morte-{name}-6x.png')
manifest={'status':'PROPOSTA — nenhuma alteração de runtime','palette':PAL,'profiles':[{'key':k,'name':n,'palette_index':c} for k,n,c in PROFILES],'direction_order':['L','SE','S','SO','O','NO','N','NE'],'canonical_tiles':15,'projectile_vram_bytes':480,'current_projectile_tiles':2,'native_sizes':[8,8],'death_concept_generator':'built-in image_gen','death_concept':'source/mortes-concept.png','death_runtime_art_ready':False}
(ROOT/'proposta.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Proposta exportada:',OUT)
