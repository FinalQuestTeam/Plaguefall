"""Phase9: A+B+B+B+C, original whole props, exact native material reuse."""
from pathlib import Path
import argparse,json,sys,io,struct,hashlib,math,os
from PIL import Image,ImageDraw
import numpy as np
G=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;OLD=G/'art/campaign-corridors-v3/corrections/9-guidebook'
sys.path.insert(0,str(G/'tools'));from campaign_geometry import validate,path,free
import build_campaign_factory as packer
args=argparse.ArgumentParser();args.add_argument('--check',action='store_true');args=args.parse_args()
def emit(p,b):
 if args.check:assert p.exists() and p.read_bytes()==b,('stale phase9 export',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
def js(p,v):emit(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
palette=Image.open(OLD/'complete-native.png').getpalette();colors=np.array(palette[:48]).reshape(16,3).astype(np.int32)
def indexed(im):
 a=np.array(im.convert('RGB'),dtype=np.int32);q=Image.fromarray(((a[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'));q.putpalette(palette);return q
def canvas(size):
 im=Image.new('P',size);im.putpalette(palette);return im
def repeat(out,im,box):
 x,y,w,h=box
 for yy in range(y,y+h,im.height):
  for xx in range(x,x+w,im.width):out.paste(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
source=Image.open(A/'source/industrial-street-base.png').convert('RGB').resize((768,256),Image.Resampling.NEAREST)
# Quiet shared materials rather than storing thousands of unique floor speckles.
wall=indexed(source.crop((144,0,272,88)).resize((128,96),Image.Resampling.NEAREST))
floor=indexed(Image.open(G/'art/phase07-urban-v2/modules/asphalt-repeat.png'))
lower=indexed(source.crop((144,200,272,256)).resize((128,32),Image.Resampling.NEAREST))
for name,im in [('upper-industrial-perimeter',wall),('asphalt-repeat',floor),('lower-sidewalk-perimeter',lower)]:png(A/'modules'/f'{name}.png',im)
B=canvas((512,320));repeat(B,wall,(0,0,512,96));repeat(B,floor,(0,96,512,192));repeat(B,lower,(0,288,512,32))
# Every512px boundary shares the exact same16px material collar. Columns
# inside the road stay empty; only the absolute world ends close laterally.
B.paste(B.crop((0,0,16,320)),(496,0));C=B.copy();first=B.copy()
door=Image.open(OLD/'modules/factory-door-exact.png');C.paste(door,(368,32))
left=indexed(Image.open(OLD/'modules/left-wall.png'));repeat(first,left,(0,96,16,192));repeat(C,left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(496,96,16,192))
for name,im in [('A-arrival',first),('B-repeat',B),('C-factory',C)]:png(A/'segments'/f'{name}.png',im)
background=canvas((2560,320))
for x,im in zip([0,512,1024,1536,2048],[first,B,B,B,C]):background.paste(im,(x,0))
png(A/'background-three-segments.png',background)
shop=Image.open(OLD/'modules/whole-workshop-rgba.png').convert('RGBA');truck=Image.open(OLD/'modules/whole-rust-truck-rgba.png').convert('RGBA')
def extended(im):
 out=Image.new('RGBA',(288,128));out.paste(im.crop((0,0,48,128)),(0,0))
 for x in range(48,240,16):out.paste(im.crop((48,0,64,128)),(x,0))
 out.paste(im.crop((80,0,128,128)),(240,0));return out
wide=extended(shop)
props=[('arrival-workshop',shop,128,32),('south-workshop',shop,672,160),('loading-shed',wide,1120,32),('south-warehouse',wide,1760,160),('street-truck',truck,400,208),('loading-truck',truck.transpose(Image.Transpose.FLIP_LEFT_RIGHT),1248,224),('final-truck',truck,2256,176)]
scene=background.copy();solids=[];placements=[]
for name,im,x,y in props:
 png(A/'objects'/f'{name}.png',im);scene.paste(indexed(im),(x,y),im.getchannel('A'));solids.append([x,y,im.width,im.height,True]);placements.append(dict(name=name,canvas=[x,y,*im.size]))
png(A/'complete-native.png',scene)
assert scene.crop((2416,32,2496,96)).convert('RGB').tobytes()==door.convert('RGB').tobytes(),'factory entry RGB must remain exact'
d=dict(phase='9',size=[2560,320],bounds=[16,96,2543,287],start=[48,184],solids=solids,exit=[2400,96,112,80],camera_player_y=184,camera_south_start=216,points=[])
# Route forces readable bottom -> top -> bottom -> top detours, with64px
# minimum passage at southern roofs and loading dock. No full-height dividers.
goals=[[288,184],[584,184],[584,120],[848,120],[1032,120],[1032,176],[1456,176],[1640,176],[1640,120],[2112,120],[2448,120]]
waypoints=[d['start']]
for goal in goals:
 if goal!=waypoints[-1]:waypoints.extend(path(d,waypoints[-1],goal,8)[1:])
d['player_waypoints']=waypoints;d['route_points']=[[x+8,y+8] for x,y in waypoints];d['points']=d['route_points'];d['geometry_validation']=validate(d)
# Every pixel of the path retains an additional8px margin around16px feet.
margin_samples=0
for a,b in zip(waypoints,waypoints[1:]):
 steps=int(math.dist(a,b))
 for i in range(steps+1):
  x=round(a[0]+(b[0]-a[0])*i/max(1,steps));y=round(a[1]+(b[1]-a[1])*i/max(1,steps));assert free(d,x,y,8),(a,b,x,y);margin_samples+=1
d['geometry_validation'].update(margin_pixels=8,swept_margin_samples=margin_samples,minimum_authored_passage_width=64)
focus=[]
for name,im,x,y in props[:4]:focus.append(dict(id=name,name=name,bbox=[x,y,*im.size],position=[x-40,y+136] if y==32 else [x-40,120]))
focus.append(dict(id='factory-entry',name='factory-entry',bbox=[2416,32,80,64],position=[2448,120]));d['camera_interest']=focus
# Preserve all detail; prefer a static bank when the exact material reuse fits.
tiles,mapping,reused=packer.pack(scene)
if len(tiles)<=640:
 raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles);resident=len(tiles)
else:
 # Exact visible cache uses source IDs (no H/V flags).
 rawtiles=[];lookup={};mapping=[]
 for y in range(0,320,8):
  for x in range(0,2560,8):
   t=scene.crop((x,y,x+8,y+8)).tobytes()
   if t not in lookup:lookup[t]=len(rawtiles);rawtiles.append(t)
   mapping.append(lookup[t])
 raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in rawtiles);resident=640
 mp=np.array(mapping).reshape(40,320);peak=0
 for y in range(3,15+1):
  for x in range(0,279+1):peak=max(peak,len(np.unique(mp[y:y+26,x:x+41])))
 assert peak+16<=640,('visible cache does not fit',peak)
 resident=math.ceil((peak+16)/32)*32
 d['streamed_tiles']=dict(resident_budget=resident,maximum_visible_tiles=peak,source_tiles=len(rawtiles))
palwords=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in colors]
emit(A/'native/tiles.bin',raw);emit(A/'native/map.bin',struct.pack('>'+str(len(mapping))+'H',*mapping));emit(A/'native/palette.bin',struct.pack('>16H',*palwords));png(A/'native/map-native.png',scene)
d.update(memory=dict(source_tiles=len(raw)//32,resident_tiles=resident,resident_bytes=resident*32,map_bytes=len(mapping)*2,rom_graphics_bytes=len(raw),limit=640,lossy_tile_substitutions=0),segments=['A','B','B','B','C'],segment_size=[512,320],placements=placements,sources=[dict(path=os.path.relpath(p,A),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [A/'source/industrial-street-base.png',G/'art/phase07-urban-v2/modules/asphalt-repeat.png',OLD/'modules/whole-workshop-rgba.png',OLD/'modules/whole-rust-truck-rgba.png',OLD/'modules/factory-door-exact.png',OLD/'modules/left-wall.png']],native=dict(tiles='native/tiles.bin',map='native/map.bin',palette='native/palette.bin'),status='integrated; native tests passed; user visual acceptance not claimed',background_tool='built-in image_gen',props_reused_from=str(OLD.relative_to(G)),path_length_px=round(sum(math.dist(a,b) for a,b in zip(waypoints,waypoints[1:])),1))
# Review overlay only: it is never part of the native map.
review=scene.convert('RGBA');overlay=Image.new('RGBA',scene.size);dr=ImageDraw.Draw(overlay)
for x,y,w,h,*_ in solids:dr.rectangle((x,y,x+w-1,y+h-1),fill=(240,60,45,34),outline=(255,92,64,230),width=1)
dr.line([tuple(p) for p in d['points']],fill=(45,235,235,255),width=3)
for i,(x,y) in enumerate(d['points']):dr.ellipse((x-3,y-3,x+3,y+3),fill='#d7ffff')
review.alpha_composite(overlay);png(A/'pathing.png',review)
for i,(name,px,py) in enumerate([('arrival',184,184),('south-workshop',624,120),('loading',1280,176),('warehouse',1704,120),('factory',2448,120)]):
 cx=max(0,min(2240,px+8-160));cy=0 if name in ('arrival','loading','factory') else 64
 view=scene.crop((cx,cy,cx+320,cy+224)).convert('RGB');dr=ImageDraw.Draw(view);dr.rectangle((0,0,319,23),fill='#111713');dr.text((8,6),'COMPOSICAO / FASE9',fill='#e8c674');png(A/'cameras'/f'{i+1}-{name}.png',view)
js(A/'manifest.json',d);print(json.dumps({'memory':d['memory'],'geometry':d['geometry_validation'],'streamed':d.get('streamed_tiles'),'path':waypoints},indent=2))
