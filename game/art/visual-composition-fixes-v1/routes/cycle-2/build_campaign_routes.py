"""Author 3072px campaign escorts from approved native tunnel tile modules.

No raster synthesis or nearest-pattern substitutions: assembled source tiles
retain their exact 4bpp pixels. Preview PNGs decode the shipped tile maps.
"""
from pathlib import Path
import argparse, hashlib, json, math, struct
from PIL import Image
from build_route_art import compact, compose

GAME=Path(__file__).resolve().parents[1]
ART=GAME/'art/campaign-routes-v1'
WIDTH,HEIGHT=3072,320
EXIT=[2992,184,48,48]
GATES=[[1008,208,32,64],[2032,208,32,64]]
VALVES=[[968,224],[1992,224]]
DATA={
 '06a':dict(name='Pela passagem de baixo',cap=3,spawn=3,solids=[[352,96,160,64],[800,240,176,64],[1376,96,160,64],[1824,240,176,64],[2400,96,160,64]],points=[[56,216],[280,216],[568,216],[744,216],[1008,200],[1304,200],[1584,216],[1760,216],[2056,200],[2320,200],[2640,216],[3016,208]],pauses=[3,7]),
 '06b':dict(name='O peso dos que ficaram',cap=3,spawn=3,solids=[[352,96,128,64],[768,240,144,64],[1376,96,144,64],[1792,240,144,64],[2400,96,160,64]]+[[x,y,w,h] for x,_,w,_ in GATES for y,h in ((192,16),(272,32))],points=[[56,216],[280,216],[552,208],[744,208],[944,216],[960,240],[1048,240],[1080,216],[1304,216],[1584,208],[1760,208],[1968,216],[1984,240],[2072,240],[2104,216],[2320,216],[2640,216],[3016,208]],pauses=[4,11]),
 '12':dict(name='A ultima travessia',cap=3,spawn=2,solids=[[456,96,96,80],[936,240,96,64],[1400,96,96,88],[1904,224,96,80],[2416,96,96,80]],points=[[56,216],[328,216],[624,216],[848,208],[1104,200],[1304,216],[1576,216],[1808,208],[2072,208],[2304,216],[2592,216],[2824,208],[3016,208]],pauses=[3,7,10]),
}

for stage in DATA.values():stage['solids'].append([2656,240,112,64])

def overlap(a,b):
 x,y,w,h=a;rx,ry,rw,rh=b
 return x<rx+rw and x+w>rx and y<ry+rh and y+h>ry

WHOLE=GAME/'art/visual-composition-fixes-v1/routes/cycle-2'
SOURCE=WHOLE/'source'
WHOLE_CFG={
 '06a':dict(base=([0,0,450,420],[112,96]),middle=([790,10,1180,400],[96,96]),arrival=([1630,0,2172,480],[128,112]),wall=([450,0,580,400],[32,96]),roof=([1000,12,1001,13],[8,8]),floor=([614,429,615,430],[8,8]),water=([200,560,280,592],[32,16]),bank=([300,490,316,498],[16,8])),
 '06b':dict(base=([0,0,450,350],[96,80]),middle=([450,0,830,370],[64,80]),arrival=([1900,0,2172,420],[96,80]),roof=([1000,12,1001,13],[8,8]),floor=([1748,382,1756,390],[8,8]),water=([600,570,616,586],[16,16]),bank=([600,650,616,658],[16,8]),pipe=([530,130,550,260],[8,48])),
 '12':dict(base=([0,70,680,460],[112,96]),middle=([750,150,1240,490],[96,96]),arrival=([1510,40,2172,590],[128,112]),wall=([370,100,650,460],[64,96]),roof=([1000,12,1001,13],[8,8]),floor=([446,530,454,538],[8,8]),water=([710,642,726,658],[16,16]),bank=([710,630,726,638],[16,8])),
}
SEWER_PALETTE=[(0,0,0),(1,1,1),(1,2,2),(2,2,2),(2,3,3),(3,3,3),(3,3,4),(4,4,3),(2,2,1),(3,2,1),(4,3,2),(5,4,2),(6,5,3),(2,3,2),(1,1,2),(5,5,4)]
PORT_PALETTE=[(0,0,0),(1,1,1),(1,1,2),(1,2,3),(2,2,2),(3,3,3),(4,4,4),(5,5,5),(6,6,5),(7,7,6),(3,2,1),(4,3,2),(5,4,2),(6,5,3),(3,1,1),(2,3,3)]
def whole_scene(key,d):
 import numpy as np
 im=Image.open(SOURCE/f'{key}-scene.png').convert('RGB')
 cfg=WHOLE_CFG[key];out=Image.new('RGB',(WIDTH,HEIGHT));modules=[]
 def module(name,spec):
  box,size=spec
  src=Image.open(SOURCE/'06a-scene.png').convert('RGB') if key=='06b' and name in ('Pavimento continuo','Cobertura e infraestrutura') else im
  if key=='06b' and name=='Pavimento continuo':box=[614,429,615,430]
  if key=='06b' and name=='Cobertura e infraestrutura':box=[1000,12,1001,13]
  p=src.crop(tuple(box)).resize(tuple(size),Image.Resampling.LANCZOS)
  modules.append({'name':name,'source':box,'sourceImage':'06a-scene.png' if key=='06b' and name in ('Pavimento continuo','Cobertura e infraestrutura') else f'{key}-scene.png','nativeSize':size})
  return p
 floor=module('Pavimento continuo',cfg['floor']);roof=module('Cobertura e infraestrutura',cfg['roof'])
 water=module('Agua ou canal tecnico',cfg['water']);bank=module('Borda construida do canal',cfg['bank'])
 facade=module('Baia arquitetonica completa',cfg['base'])
 wall=module('Intervalo arquitetonico',cfg['wall']) if 'wall' in cfg else None
 middle=module('Marco de inspecao/manutencao',cfg['middle'])
 landing=module('Construcao distinta da chegada',cfg['arrival'])
 def fill(p,x,y,w,h):
  for yy in range(y,y+h,p.height):
   for xx in range(x,x+w,p.width):out.paste(p.crop((0,0,min(p.width,x+w-xx),min(p.height,y+h-yy))),(xx,yy))
 fill(floor,0,192,WIDTH,112);fill(roof,0,0,WIDTH,192)
 # Complete connected architectural bays cover every horizontal column. No
 # decorative floating props and no per-tile substitutions are permitted.
 x=0;bay=0
 while x<WIDTH:
  out.paste(facade,(x,192-facade.height));x+=facade.width;bay+=1
  if wall:
   repeats=2 if x<1024 else (3 if x<2048 else 1)
   for _ in range(repeats):out.paste(wall,(x,192-wall.height));x+=wall.width
 # Large landmarks are authored once per sector, not stamped every bay.
 fill(roof,1408,64,middle.width,128);out.paste(middle,(1408,192-middle.height))
 fill(roof,WIDTH-landing.width,64,landing.width,128)
 out.paste(landing,(WIDTH-landing.width,192-landing.height))
 if key=='06b':
  pipe=module('Tubo fisico conectado a valvula',cfg['pipe'])
  for (gx,gy,gw,gh),(vx,vy) in zip(GATES,VALVES):
   fill(roof,gx-32,64,middle.width,128)
   out.paste(middle,(gx-32,192-middle.height))
   fill(pipe,vx-24,176,8,48)
   # The generated pipe module meets the runtime valve's left pipe mouth.
   horizontal=pipe.rotate(90,expand=True)
   fill(horizontal,vx-24,216,24,8)
 fill(water,0,304,WIDTH,16);fill(bank,0,296,WIDTH,8)
 # Collision recesses share their exact masonry/water footprint. The complete
 # image modules are repeated as material spans, never nearest tile patches.
 for rx,ry,rw,rh in d['solids']:
  if key=='06b' and rw==32:
   fill(bank,rx,ry,rw,rh);continue
  if ry<192:continue # the upper foundation is already inside the architecture
  fill(water,rx,ry,rw,rh);fill(bank,rx,ry,rw,8);fill(bank,rx,ry+rh-8,rw,8)
  side=bank.rotate(90,expand=True)
  fill(side,rx,ry,8,rh);fill(side,rx+rw-8,ry,8,rh)
 # Adaptive global palette, then Mega Drive RGB333 snapping. Quantization is
 # performed once on the complete assembled image, without dithering.
 palette=SEWER_PALETTE if key in ('06a','06b') else PORT_PALETTE
 hw=np.array([[v*255//7 for v in c] for c in palette],dtype=np.int32)
 arr=np.array(out,dtype=np.int32)
 indices=((arr[:,:,None,:]-hw[None,None,:,:])**2).sum(axis=3).argmin(axis=2).astype(np.uint8)
 cells=indices.reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64)
 unique,inverse=np.unique(cells,axis=0,return_inverse=True)
 tiles=[bytes((int(row[i])<<4)|int(row[i+1]) for i in range(0,64,2)) for row in unique]
 palette_words=[(r<<1)|(g<<5)|(b<<9) for r,g,b in palette]
 native=Image.fromarray(hw.astype(np.uint8)[indices])
 out.save(WHOLE/f'{key}-composed-complete.png');native.save(WHOLE/f'{key}-native-complete.png')
 import json
 (WHOLE/f'{key}-modules.json').write_text(json.dumps(modules,indent=2,ensure_ascii=False)+'\n')
 art={'wholeImage':str((SOURCE/f'{key}-scene.png').relative_to(GAME)),
      'wholeImageSHA256':hashlib.sha256((SOURCE/f'{key}-scene.png').read_bytes()).hexdigest(),
      'method':'Whole ImageGen scene first; complete architectural module extraction; exact 8x8 deduplication',
      'architectureBays':bay,'sourceModules':modules,'lossyTileReplacements':0,'nativeImage':str((WHOLE/f'{key}-native-complete.png').relative_to(GAME))}
 return tiles,list(map(int,inverse)),palette_words,art

def generate():
 files={};report={};source=['// Generated by tools/build_campaign_routes.py; exact approved tile modules.','#include "levels/campaign_routes.h"','#include <campaign_routes.h>'];header=['#ifndef LEVEL_CAMPAIGN_ROUTES_H','#define LEVEL_CAMPAIGN_ROUTES_H','#include "levels/levels.h"'];res=[];decl=[]
 for key,d in DATA.items():
  tiles,m,palette,art=whole_scene(key,d);cols=WIDTH//8
  rgb=[(((v>>1)&7)*255//7,((v>>5)&7)*255//7,((v>>9)&7)*255//7) for v in palette]
  from pack_campaign_ground_art import generate as packed_objectives
  _,object_counts=packed_objectives()
  budget=640-object_counts[3]-object_counts[4] if key=='06b' else 640
  assert len(tiles)<=budget,(key,len(tiles),budget)
  length=0;samples=0
  for (ax,ay),(bx,by) in zip(d['points'],d['points'][1:]):
   dist=math.hypot(bx-ax,by-ay);length+=dist
   for i in range(math.ceil(dist)+1):
    t=min(1,i/max(1,dist));x=ax+(bx-ax)*t-8;y=ay+(by-ay)*t-8
    assert 16<=x and x+16<=3056 and 192<=y and y+16<=304,(key,x,y)
    assert not any(overlap((x,y,16,16),r) for r in d['solids']),(key,'sweep',x,y)
    samples+=1
  assert not any(overlap(EXIT,r) for r in d['solids'])
  for kind,b in (('tiles',b''.join(tiles)),('map',struct.pack('>'+str(len(m))+'H',*m)),('palette',struct.pack('>16H',*palette))):
   path=f'campaign_routes/{key}/{kind}.bin';files[GAME/'res'/path]=b
   sym=f'campaign_route{key}_{kind}';res.append(f'BIN {sym} "{path}" {4 if kind=="tiles" else 2}')
   decl.append(f'extern const u8 {sym}[{len(b)}];')
  source+= [f'static const ArenaScene scene{key}={{.tiles=(const u32 *)campaign_route{key}_tiles,.map=(const u16 *)campaign_route{key}_map,.palette=(const u16 *)campaign_route{key}_palette,.tileCount={len(tiles)},.rows=40,.cols=384}};',f'static const ArenaRect solids{key}[]={{'+','.join('{%d,%d,%d,%d,TRUE}'%tuple(r) for r in d['solids'])+'};',f'const ArenaDef CAMPAIGN_ARENA{key.upper()}={{3072,320,16,192,3055,303,48,208,solids{key},{len(d["solids"])},&scene{key}}};',f'static const RoutePoint points{key}[]={{'+','.join('{%d,%d,%d}'%(x,y,1 if i in d['pauses'] else 0) for i,(x,y) in enumerate(d['points']))+'};',f'const RouteDef CAMPAIGN_ROUTE{key.upper()}={{points{key},{len(d["points"])},'+'{'+','.join(map(str,EXIT))+',FALSE}};']
  header += [f'extern const ArenaDef CAMPAIGN_ARENA{key.upper()};',f'extern const RouteDef CAMPAIGN_ROUTE{key.upper()};']
  im=Image.new('RGB',(WIDTH,HEIGHT));pixels=im.load();expanded=[[v for b in tile for v in (b>>4,b&15)] for tile in tiles]
  for y in range(HEIGHT):
   for x in range(WIDTH):pixels[x,y]=rgb[expanded[m[(y//8)*cols+x//8]][(y%8)*8+x%8]]
  import io
  b=io.BytesIO();im.save(b,format='PNG');files[ART/f'mapa-{key}.png']=b.getvalue()
  for label,x in [('entrada',0),('meio',1360),('saida',WIDTH-320)]:
   b=io.BytesIO();im.crop((x,72,x+320,296)).resize((640,448),Image.Resampling.NEAREST).save(b,format='PNG');files[ART/f'{key}-{label}.png']=b.getvalue()
  report[key]={**d,'width':WIDTH,'height':HEIGHT,'walkable':[16,192,3040,112],'gates':GATES if key=='06b' else [],'valves':VALVES if key=='06b' else [],'exit':EXIT,'tiles':len(tiles),'tileBudget':budget,'swept16pxSamples':samples,'routeLengthPx':round(length,1),'unopposedMinimumSeconds':round(length/36+len(d['pauses']),1),'art':art,'nativeTileSHA256':hashlib.sha256(b''.join(tiles)).hexdigest()}
 source+=['const ArenaRect CAMPAIGN_ROUTE06B_gates[2]={'+','.join('{%d,%d,%d,%d,TRUE}'%tuple(r) for r in GATES)+'};','const RoutePoint CAMPAIGN_ROUTE06B_valves[2]={'+','.join('{%d,%d,0}'%tuple(p) for p in VALVES)+'};']
 header+=['extern const ArenaRect CAMPAIGN_ROUTE06B_gates[2];','extern const RoutePoint CAMPAIGN_ROUTE06B_valves[2];','#endif']
 files[GAME/'src/levels/campaign_routes.c']=('\n'.join(source)+'\n').encode();files[GAME/'src/levels/campaign_routes.h']=('\n'.join(header)+'\n').encode()
 files[GAME/'res/campaign_routes.res']=('\n'.join(res)+'\n').encode();files[GAME/'res/campaign_routes.h']=('#include <genesis.h>\n\n#ifndef _RES_CAMPAIGN_ROUTES_H_\n#define _RES_CAMPAIGN_ROUTES_H_\n\n'+'\n'.join(decl)+'\n\n#endif // _RES_CAMPAIGN_ROUTES_H_\n').encode();files[ART/'export.json']=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode()
 return files,report

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
 files,report=generate()
 for p,data in files.items():
  if args.check:assert p.read_bytes()==data,p
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 print(json.dumps({k:{'tiles':d['tiles'],'length':d['routeLengthPx'],'samples':d['swept16pxSamples']} for k,d in report.items()}))
