"""Isolated proposal: reuse existing native materials and complete original assets.
No changes to active art, generators, source C, or ROM. No procedural building drawing.
"""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import sys,json,hashlib
A=Path(__file__).resolve().parent;G=A.parents[3];sys.path.insert(0,str(G/'tools'));import build_campaign_factory as packer
(A/'modules').mkdir(exist_ok=True);(A/'cameras').mkdir(exist_ok=True)
C=Image.open(G/'art/campaign-pattern-v2/factory/modules/factory-door.png').copy();pal=C.getpalette();pal[8*3:8*3+3]=[218,145,72];pal[14*3:14*3+3]=[182,145,72];C.putpalette(pal);colors=[tuple(C.getpalette()[i:i+3]) for i in range(0,48,3)]
trace={}
def native(name,path,rect=None,size=None):
 im=Image.open(G/path)
 if rect:im=im.crop(rect)
 if size:im=im.resize(size,Image.Resampling.NEAREST)
 p=A/f'modules/{name}-source.png';im.save(p);result=packer.indexed(p,im.size,1,C);result.save(A/f'modules/{name}.png')
 trace[name]={'source':str(path),'crop':rect,'size':list(im.size),'grid':1,'exact_flip_unique_tiles':len(packer.pack(result)[0]) if im.width%8==im.height%8==0 else None}
 return result
floor=native('dust-floor','art/phase01-courtyard-v2/intact-native.png',(224,160,256,192))
concrete=floor
back=floor
wall=native('complete-industrial-wall','art/phase04-tunnels-v1/map-native.png',(80,0,144,80))
# Native lower/side/corner pieces retained as complete perimeter assemblies.
base=native('lower-wall','art/phase01-courtyard-v2/intact-native.png',(224,368,256,384))
left=native('left-wall','art/phase01-courtyard-v2/intact-native.png',(0,160,16,192));right=left.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
cornerl=native('lower-left-corner','art/phase01-courtyard-v2/intact-native.png',(0,352,16,384));cornerr=cornerl.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
pipebank=native('complete-valve-service-wall','art/phase04-tunnels-v1/map-native.png',(336,0,432,80))

factorydoor=native('factory-door-exact','art/campaign-pattern-v2/factory/modules/factory-door.png')


factorywall=wall

# Full pre-existing image cutouts; only alpha trim + native nearest conversion.
def cutout(name,path,rect,size):
 src=Image.open(G/path).convert('RGBA').crop(rect);mask=src.getchannel('A').point(lambda x:255 if x>=128 else 0);assert mask.getbbox();src.putalpha(mask);src=src.crop(mask.getbbox()).resize(size,Image.Resampling.NEAREST);src.save(A/f'modules/{name}-rgba.png');trace[name]={'source':path,'cell':list(rect),'size':list(size),'method':'complete alpha silhouette, nearest at1px, same16 church colors'};return src
s=Image.open(G/'art/phase03-street-v2/source/street-kit.png');w,h=s.size
shop=cutout('whole-workshop','art/phase03-street-v2/source/street-kit.png',(w//4,0,w//2,h//2),(128,128))
e=Image.open(G/'art/routes-2048-v2/source/evacuation-cutouts.png');w,h=e.size
truck=cutout('whole-rust-truck','art/routes-2048-v2/source/evacuation-cutouts.png',(w//2,0,w,h//2),(96,64))



out=Image.new('P',(2560,320));out.putpalette(C.getpalette())
def repeat(im,rect):packer.repeat(out,im,(0,0,*im.size),rect)
repeat(floor,(0,0,2560,320))
# Land-use boundaries move in and out with complete native ends; not new filled architecture.
# Continuous complete original tunnel wall: no detached machine rectangles or grey fills.
repeat(wall,(0,32,2560,80))
repeat(base,(0,304,2560,16));repeat(left,(0,32,16,288));repeat(right,(2544,32,16,288))
out.paste(cornerl,(0,288));out.paste(cornerr,(2544,288))
out.paste(cornerl.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(0,32));out.paste(cornerr.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(2544,32))
# Three connected outdoor court shapes, using complete native side/footing/corner pieces.
# The lower repair court projects into the street; the loading court steps back.
for x,y,w in [(352,160,480),(1088,224,512),(1712,160,416)]:
 repeat(left,(x,y,16,320-y));repeat(right,(x+w-16,y,16,320-y));repeat(base,(x,304,w,16));out.paste(cornerl,(x,288));out.paste(cornerr,(x+w-16,288));out.paste(cornerl.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(x,y));out.paste(cornerr.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(x+w-16,y))
# Exact old factory entry is embedded in its full-height rusty host wall.
out.paste(factorydoor,(2392,48))
placements=[]
def prop(name,src,x,y):
 if src.mode=='RGBA':
  ground=out.crop((x,y,x+src.width,y+src.height)).convert('RGBA');ground.alpha_composite(src);p=A/f'modules/{name}-on-ground.png';ground.save(p);im=packer.indexed(p,src.size,1,C)
 else:im=src
 out.paste(im,(x,y));placements.append({'asset':name,'bbox':[x,y,*src.size]})
prop('whole-workshop',shop,128,32)
prop('whole-workshop-south',shop,640,160)
prop('whole-workshop-arrival',shop,1792,32)
prop('complete-valve-service-wall',pipebank,920,32)
prop('complete-valve-service-wall-dock',pipebank,1432,32)
prop('complete-valve-service-wall-arrival',pipebank,2104,32)
prop('whole-rust-truck',truck,448,176)
prop('whole-rust-truck-dock',truck.transpose(Image.Transpose.FLIP_LEFT_RIGHT),1216,160)
assert out.crop((2392,48,2472,112)).convert('RGB').tobytes()==Image.open(G/'art/campaign-pattern-v2/factory/modules/factory-door.png').convert('RGB').tobytes(),'Factory door must retain exact RGB pixels'
out.save(A/'complete-native.png')
tiles,mapping,reused=packer.pack(out)
# Full source/style checkpoint. Export exact data only if it fits, never discard detail to fit.
mem={'tiles':len(tiles),'budget':640,'tile_bytes':len(tiles)*32,'map_bytes':len(mapping)*2,'exact_flip_reused':reused,'lossy_tile_substitutions':0,'native_grid':1,'fits':len(tiles)<=640}
(A/'memory.json').write_text(json.dumps(mem,indent=2));(A/'module-trace.json').write_text(json.dumps(trace,indent=2));(A/'placements.json').write_text(json.dumps(placements,indent=2))
# Five composed normal320x224 viewports with the existing actor and real HUD art.
hero=Image.open(G/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png').crop((0,0,32,48)).convert('RGBA');hud=Image.open(G/'art/campaign-corridors-v3/captures/ntsc/9/landmark-0.png').crop((0,0,320,24)).convert('RGBA')
views=[]
for i,(px,py,cx,cy) in enumerate([(184,184,32,0),(608,272,456,72),(1328,208,1208,8),(1840,184,1688,0),(2456,184,2240,0)]):
 world=out.convert('RGBA');world.alpha_composite(hero,(px-8,py-47));view=world.crop((cx,cy,cx+320,cy+224));view.alpha_composite(hud,(0,0));view.save(A/f'cameras/{i+1:02}.png');views.append({'file':f'cameras/{i+1:02}.png','feet':[px,py],'camera':[cx,cy]})
sheet=Image.new('RGB',(960,488),(20,24,28));d=ImageDraw.Draw(sheet)
for i,v in enumerate(views):
 x=i%3*320;y=i//3*244;sheet.paste(Image.open(A/v['file']),(x,y+20));d.text((x+2,y+3),f'Native proposal{i+1} feet{v["feet"]}',fill='white')
sheet.save(A/'camera-sheet.png')
(A/'manifest.json').write_text(json.dumps({'phase':'9','status':'isolated unapproved style/layout proposal; active phase9 unchanged','size':[2560,320],'whole':'complete-native.png','views':views,'memory':mem,'sources':trace,'landmarks':['roofed service block with loading truck and lower workshop court','rusty service dock with complete valve-wall bays and loaded truck','stepped factory forecourt with lower workshop and exact10/11door embedded in original rusty tunnel wall'],'limits':['Composed native preview, not emulator frames.','Geometry/collision not integrated or tested; review composition before any integration.','Palette keeps all13colors of existing factory door exactly, adding the original church ochre floor colors in the two unused factory slots. No door pixel is recolored.','No new bitmap artwork, no generated buildings, no2pxgrid or approximate tile substitutions.']},indent=2))
print(json.dumps(mem));print('complete panorama and five views ready; not approved or integrated')
