"""Complete phase7 image -> coherent material modules -> exact native map.

Other favela/union stages retain their existing banks and geometry. No nearest
pattern replacements: large source banks use the existing visible tile cache.
"""
from pathlib import Path
from collections import Counter,deque
import argparse,hashlib,io,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;GAME=HERE.parents[1]
sys.path.insert(0,str(GAME/'tools'))
from campaign_geometry import free,path,validate
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
def emit(p,data):
 if args.check:assert p.exists() and p.read_bytes()==data,('stale phase7 export',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
def js(p,v):emit(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
def ca(name,typ,values):
 return 'static const '+typ+' '+name+'[]={\n'+''.join(','.join(('0x%08XUL'%v if typ=='u32' else str(v)) for v in values[i:i+12])+',\n' for i in range(0,len(values),12))+'};\n'
# Keep the established warm brick/blue shop/cream canvas style, adding true
# gray asphalt ramps within a single16-color RGB333 scenery palette.
pal=[(0,0,0),(36,36,36),(72,72,72),(109,109,109),(145,145,145),(218,218,182),(255,255,255),(109,72,36),(145,109,72),(182,72,36),(109,36,0),(36,72,109),(72,109,145),(182,145,72),(72,109,72),(182,182,182)]
words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in pal]
paldata=struct.pack('>16H',*words);palflat=[v for c in pal for v in c]+[0]*720
master=Image.open(HERE/'source/07-urban-whole.png').convert('RGB')
rgb=master.resize((768,544),Image.Resampling.NEAREST);a=np.array(rgb,dtype=np.int32)
colors=np.array(pal,dtype=np.int32);dist=((a[:,:,None,:]-colors[None,None,:,:])**2).sum(3)
q=Image.fromarray(dist.argmin(2).astype('uint8'));q.putpalette(palflat)
png(HERE/'source/07-urban-native-reference.png',q)
def canvas(size):
 out=Image.new('P',size);out.putpalette(palflat);return out
def repeat(out,im,box):
 x,y,w,h=box
 for yy in range(y,y+h,im.height):
  for xx in range(x,x+w,im.width):out.paste(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
def module(name,box,size=None):
 im=q.crop(box)
 if size:im=im.resize(size,Image.Resampling.NEAREST)
 png(HERE/'modules'/f'{name}.png',im);return im
floor=module('asphalt-repeat',(392,192,408,208));scene=canvas((768,544));repeat(scene,floor,(0,0,768,544))
# Whole two-storey frontages have a complete parapet. Reuse exact aligned
# modules linked by concrete party walls instead of a forest backdrop.
brick=module('brick-city-front-whole',(24,8,152,168),(96,136))
refuge=module('refuge-city-front-whole',(312,16,464,168),(112,144))
backwall=module('city-brick-material',(32,32,48,48));backwall=backwall.point([0,1,2,3,4,15,6,2,3,3,1,2,3,4,2,15]+[0]*240);backwall.putpalette(palflat);png(HERE/'modules/city-concrete-material.png',backwall);repeat(scene,backwall,(0,24,768,152))
# Preserve a quiet skyline cap and complete front parapets; avoid a strip of
# miniature identical houses floating behind the street frontage.
cap=module('city-parapet-material',(40,8,56,16));repeat(scene,cap,(0,16,768,8))
for im,xy in [(brick,(32,40)),(brick,(144,40)),(refuge,(272,32)),(brick,(400,40)),(brick,(512,40)),(brick,(640,40))]:scene.paste(im,xy)
pavement=module('upper-pavement-repeat',(208,144,224,168));repeat(scene,pavement,(0,152,768,24))
# Restore building footings in front of the continuous pavement/backing.
for im,xy in [(brick,(32,40)),(brick,(144,40)),(refuge,(272,32)),(brick,(400,40)),(brick,(512,40)),(brick,(640,40))]:scene.paste(im,xy)
left=module('left-urban-boundary',(0,192,32,224));right=module('right-urban-boundary',(736,192,768,224))
repeat(scene,left,(0,176,32,304));repeat(scene,right,(736,176,32,304))
south=module('lower-urban-boundary',(80,480,112,544));repeat(scene,south,(0,480,768,64))
scene.paste(module('southwest-whole-corner',(0,480,32,544)),(0,480));scene.paste(module('southeast-whole-corner',(736,480,768,544)),(736,480))
# Edge-connected dirt becomes transparent. Preserve the complete object ink,
# posts, supports and contact shadows, without retaining rectangles of dirt.
floor_ids={1,2,3,4,15}
def prop(name,box,size,xy,protected):
 im=module(name,box,size);raw=im.tobytes();w,h=im.size;seen=set();stack=[(x,y) for x in range(w) for y in (0,h-1)]+[(x,y) for y in range(h) for x in (0,w-1)]
 while stack:
  x,y=stack.pop()
  if not(0<=x<w and 0<=y<h) or (x,y) in seen or raw[y*w+x] not in floor_ids:continue
  if any(l<=x<r and t<=y<b for l,t,r,b in protected):continue
  seen.add((x,y));stack.extend(((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
 mask=Image.frombytes('L',im.size,bytes(0 if (x,y) in seen else 255 for y in range(h) for x in range(w)))
 rgba=im.convert('RGBA');rgba.putalpha(mask);png(HERE/'modules'/f'{name}-cutout.png',rgba);scene.paste(im,xy,mask)
 return [*xy,w,h]
prop('white-canvas-stall-whole',(60,224,204,336),(128,104),(48,256),[(8,4,116,96)])
stall=Image.open(HERE/'modules/white-canvas-stall-whole-cutout.png')
for xy in [(464,248),(248,344),(600,80)]:scene.paste(stall.convert('RGB').quantize(palette=scene,dither=Image.Dither.NONE),xy,stall.getchannel('A'))
prop('open-manhole-whole',(104,180,192,224),(80,40),(24,184),[(4,6,74,32)])
png(HERE/'complete-background.png',scene)
# Plain source IDs (no flip flags) are consumed by the exact scene cache.
lookup={};tiles=[];mp=[]
for y in range(0,544,8):
 for x in range(0,768,8):
  raw=scene.crop((x,y,x+8,y+8)).tobytes()
  if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
  mp.append(lookup[raw])
data=b''.join(bytes((p[i]<<4)|p[i+1] for i in range(0,64,2)) for p in tiles)
# Conservative window covers all sub-tile camera offsets below the24px HUD.
mpa=np.array(mp).reshape((68,96));maximum=0;pose=None
for y in range(3,43+1):
 for x in range(0,57):
  count=len(np.unique(mpa[y:y+26,x:x+41]))
  if count>maximum:maximum=count;pose=[x*8,y*8-24]
cache=560;assert maximum<=cache,('visible working set exceeds cache',maximum,pose,len(tiles))
assert cache+74<=640
layout=json.loads((HERE/'layout.json').read_text())
layout['geometry']=validate(layout)
# Validate opening south and pickup east, with generous lanes and initial cases.
layout['cargo_solids']=[[x-16,y,32,8] for x,y in layout['cargo']]
route_layout={**layout,'solids':layout['solids']+layout['cargo_solids']}
legs=[]
for i,(x,y) in enumerate(layout['cargo']):
 opening=[x-8,y+16];pickup=[x+24,y+16];drop=[96,384]
 legs.append(dict(source=i,opening=opening,pickup=pickup,to_open=path(route_layout,layout['start'],opening,4),to_pickup=path(route_layout,opening,pickup,4),to_depot=path(route_layout,pickup,drop,4)))
layout['routes']=legs
png(HERE/'native/map-native.png',scene);emit(HERE/'native/tiles.bin',data);emit(HERE/'native/map.bin',struct.pack('>'+str(len(mp))+'H',*mp));emit(HERE/'native/palette.bin',paldata)
code='// Generated by art/phase07-urban-v2/export.py. Exact visible pixel cache.\n'+ca('phase07_tiles','u32',struct.unpack('>'+str(len(data)//4)+'I',data))+ca('phase07_palette','u16',words)+ca('phase07_map','u16',mp)
code+=f'static const ArenaStream phase07Stream={{{len(tiles)}}};\nstatic const ArenaScene phase07Scene={{.tiles=phase07_tiles,.map=phase07_map,.palette=phase07_palette,.tileCount={cache},.rows=68,.cols=96,.cameraPlayerY=184,.stream=&phase07Stream,.streamOverlay=TRUE,.cameraSouthStart=352}};\n'
code+='static const ArenaRect phase07Solids[]={'+','.join('{'+','.join(str(int(v)) for v in r)+'}' for r in layout['solids'])+'};\nconst ArenaDef CAMPAIGN_RESISTANCE_FAVELA={768,544,32,176,735,479,64,192,phase07Solids,4,&phase07Scene};\n'
emit(GAME/'src/levels/campaign_resistance_phase07.inc',code.encode())
header='// Generated phase7 mission anchors; same source as collision and image.\n#ifndef PHASE07_LAYOUT_H\n#define PHASE07_LAYOUT_H\n'+'static const s16 PHASE07_SOURCES[5][2]={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in layout['cargo'])+'};\n'+'#define PHASE07_DEPOT_X 104\n#define PHASE07_DEPOT_Y 392\n#endif\n'
emit(GAME/'src/levels/phase07_layout.h',header.encode())
# Complete composition before reviewing individual camera crops.
complete=scene.convert('RGBA');cargo=Image.open(GAME/'art/objective-sprites-v1/frames/cargo-0.png').convert('RGBA');opened=Image.open(GAME/'art/objective-sprites-v1/frames/cargo-5.png').convert('RGBA')
for x,y in layout['cargo']:complete.alpha_composite(cargo,(x-16,y-24))
complete.alpha_composite(opened,(layout['depot'][0]-16,layout['depot'][1]-24));png(HERE/'complete-with-objectives.png',complete)
for name,x,y in [('entrada',0,0),('casas',224,0),('deposito',0,192),('centro',224,192),('inferior',224,320),('direita',448,208)]:
 view=complete.crop((x,y,x+320,y+224));dr=ImageDraw.Draw(view);dr.rectangle((0,0,319,23),fill='#111713');dr.text((8,6),'ENQUADRAMENTO / FASE 7',fill='#e8c674');png(HERE/'cameras'/f'{name}.png',view)
# Quiet floor reuse and whole silhouettes keep ROM size independent of arena area.
layout['memory']=dict(source_patterns=len(tiles),source_graphics_bytes=len(data),map_bytes=len(mp)*2,scene_cache_slots=cache,cargo_tiles=74,total_reserved_tiles=cache+74,resident_bytes=(cache+74)*32,spare_tiles=640-cache-74,maximum_visible_patterns=maximum,maximum_window_camera=pose,cache_heap_bytes=(len(tiles)+cache*4)*2,lossy_tile_replacements=0)
layout['source']=dict(path='source/07-urban-whole.png',sha256=hashlib.sha256((HERE/'source/07-urban-whole.png').read_bytes()).hexdigest(),tool='built-in image_gen',prompt='prompts/whole-scene.txt',palette='urban RGB33316 colors: gray asphalt, white canvas, brick and blue storefronts',whole_image_first=True)
layout['before']=dict(artifact='../phase07-spacious-v1/review.html',size=[768,544],bounds=[32,176,735,479],walkable_height=304,theme='rural courtyard with dirt and foliage',source_patterns=1048)
js(HERE/'manifest.json',layout)
print(json.dumps(dict(memory=layout['memory'],geometry=layout['geometry']),indent=2))
