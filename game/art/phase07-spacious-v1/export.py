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
# Same physical RGB333 palette as phase1; retain its ochre, terracotta, foliage
# and blue doors instead of the old ten-color olive reduction.
paldata=(GAME/'res/courtyard/palette.bin').read_bytes();words=struct.unpack('>16H',paldata)
pal=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in words]
palflat=[v for c in pal for v in c]+[0]*720
master=Image.open(HERE/'source/07-favela-whole.png').convert('RGB')
# Fine native pixels: never reduce the whole scene to4x4 blocks.
rgb=master.resize((768,512),Image.Resampling.NEAREST);a=np.array(rgb,dtype=np.int32)
colors=np.array(pal,dtype=np.int32);dist=((a[:,:,None,:]-colors[None,None,:,:])**2).sum(3)
q=Image.fromarray(dist.argmin(2).astype('uint8'));q.putpalette(palflat)
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
floor=module('dirt-repeat',(320,168,336,184));scene=canvas((768,544));repeat(scene,floor,(0,0,768,544))
trees=[module('foliage-repeat-'+str(i),box) for i,box in enumerate([(0,0,32,24),(160,0,192,24),(224,0,256,24)])]
# A staggered material sequence breaks the conspicuous32x24 checkerboard.
# These crops contain foliage only, with no architectural silhouettes.
for yy in range(0,168,24):
 for xx in range(-16 if (yy//24)%2 else 0,768,32):
  scene.paste(trees[((xx//32)*7+(yy//24)*5+(xx//96))%3],(xx,yy))
# Complete houses at a common footing, reusing exact module pixels. No
# fragment of a neighboring roof is allowed in a repeatable facade.

wall=Image.open(GAME/'art/phase01-pattern-v1/modules/upper-wall.png').convert('RGB').quantize(palette=q,dither=Image.Dither.NONE)
repeat(scene,wall,(0,144,768,32))
green=module('green-house-complete',(32,24,160,152),(96,112))
blue=module('blue-house-complete',(520,24,616,152),(96,112))
refuge=module('refuge-complete',(320,0,448,152),(112,136))
for im,xy in [(green,(48,64)),(green,(192,64)),(refuge,(328,40)),(blue,(480,64)),(blue,(624,64))]:scene.paste(im,xy)
# Original full-height pillars connect the top wall to the side limits.
scene.paste(q.crop((0,72,16,152)),(0,96));scene.paste(q.crop((752,72,768,152)),(752,96))
left=module('left-wall-repeat',(0,160,16,192));right=module('right-wall-repeat',(752,160,768,192))
repeat(scene,left,(0,176,16,304));repeat(scene,right,(752,176,16,304))
south=module('lower-wall-repeat',(80,448,112,512));repeat(scene,south,(0,480,768,64))
scene.paste(module('southwest-whole-corner',(0,448,32,512)),(0,480));scene.paste(module('southeast-whole-corner',(736,448,768,512)),(736,480))
# Edge-connected dirt becomes transparent. Preserve the complete object ink,
# posts, supports and contact shadows, without retaining rectangles of dirt.
floor_ids={i for i,n in Counter(floor.tobytes()).most_common(2)}
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
depot_box=prop('depot-whole',(40,200,192,320),(128,104),(48,256),[(8,4,102,90)])
barrier1=prop('barricade-whole',(432,216,576,264),(128,40),(432,280),[(8,4,120,32)])
# Reuse the same physical silhouette, preserving its light direction.
bar=Image.open(HERE/'modules/barricade-whole-cutout.png');scene.paste(bar.convert('RGB').quantize(palette=scene,dither=Image.Dither.NONE),(248,344),bar.getchannel('A'))
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
layout=dict(width=768,height=544,size=[768,544],bounds=[32,176,735,479],start=[64,192],solids=[[48,256,112,104,True],[440,288,112,24,True],[256,352,112,24,True]],points=[],cargo=[[232,216],[440,208],[664,280],[280,408],[608,416]],depot=[104,392],camera_player_y=184,camera_south_start=352)
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
code='// Generated by art/phase07-spacious-v1/export.py. Exact visible pixel cache.\n'+ca('phase07_tiles','u32',struct.unpack('>'+str(len(data)//4)+'I',data))+ca('phase07_palette','u16',words)+ca('phase07_map','u16',mp)
code+=f'static const ArenaStream phase07Stream={{{len(tiles)}}};\nstatic const ArenaScene phase07Scene={{.tiles=phase07_tiles,.map=phase07_map,.palette=phase07_palette,.tileCount={cache},.rows=68,.cols=96,.cameraPlayerY=184,.stream=&phase07Stream,.streamOverlay=TRUE,.cameraSouthStart=352}};\n'
code+='static const ArenaRect phase07Solids[]={'+','.join('{'+','.join(str(int(v)) for v in r)+'}' for r in layout['solids'])+'};\nconst ArenaDef CAMPAIGN_RESISTANCE_FAVELA={768,544,32,176,735,479,64,192,phase07Solids,3,&phase07Scene};\n'
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
layout['source']=dict(path='source/07-favela-whole.png',sha256=hashlib.sha256((HERE/'source/07-favela-whole.png').read_bytes()).hexdigest(),tool='built-in image_gen',prompt='prompts/whole-scene.txt',palette='exact phase1 courtyard RGB333',whole_image_first=True)
layout['before']=dict(size=[768,384],bounds=[40,160,727,335],walkable_height=176,whole_image_pixel_block=4,scene_tiles=492,cargo_tiles=74)
js(HERE/'manifest.json',layout)
print(json.dumps(dict(memory=layout['memory'],geometry=layout['geometry']),indent=2))
