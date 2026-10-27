"""Phase12: three complete native blocks A+B+B+B+B+C and independent field props."""
from pathlib import Path
import argparse,io,json,math,struct,hashlib,sys,os
from PIL import Image,ImageDraw
import numpy as np
G=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;OLD=G/'art/campaign-corridors-v3/corrections/12-guidebook'
sys.path.insert(0,str(G/'tools'))
from campaign_geometry import path,free,validate
from build_campaign_factory import pack
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
def emit(p,b):
 if args.check:assert p.exists() and p.read_bytes()==b,('stale phase12 export',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
def js(p,d):emit(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
palette=Image.open(OLD/'complete-native.png').getpalette();colors=np.array(palette[:48],dtype=np.int32).reshape(16,3)
sources=[]
def asset(p):
 sources.append(dict(path=os.path.relpath(p,A),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return Image.open(p).convert('RGBA')
def indexed(im):
 rgb=np.array(im.convert('RGB'),dtype=np.int32)
 q=Image.fromarray(((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'));q.putpalette(palette);return q
# Existing native modules retain scale, closed roof edges and complete bases.
wall=asset(OLD/'modules/industrial-wall-source.png');header=asset(OLD/'modules/header-source.png');curb=asset(OLD/'modules/wall-source.png');post=asset(OLD/'modules/post-source.png')
floor=asset(G/'art/phase07-urban-v2/modules/asphalt-repeat.png');workshop=asset(OLD/'modules/workshop-assembly-rgba.png');annex=asset(OLD/'modules/annex-assembly-rgba.png');union=asset(OLD/'modules/union-assembly-rgba.png')
truck=asset(G/'art/phase09-three-segments-v1/objects/street-truck.png')
barrels=asset(G/'art/phase06-three-segments-v1/objects/barris.png');crates=asset(G/'art/phase06-three-segments-v1/objects/caixas.png')
side=asset(G/'art/phase10-factory-v2/modules/left-boundary.png')
def repeat(out,im,box):
 x,y,w,h=box
 for yy in range(y,y+h,im.height):
  for xx in range(x,x+w,im.width):out.alpha_composite(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
# New ImageGen building -> native material parts, complete facade and openings.
# Only roof/wall material runs repeat. Never rescale a complete building to fit.
newsource=asset(A/'source/service-workshop-redesign.png')
alpha=newsource.getchannel('A').point(lambda v:255 if v>=184 else 0);newsource.putalpha(alpha)
newsource=newsource.crop(alpha.getbbox());newsource=newsource.resize((160,round(newsource.height*160/newsource.width)),Image.Resampling.NEAREST)
newsource.putalpha(newsource.getchannel('A').point(lambda v:255 if v>=184 else 0))
png(A/'modules/service-workshop-native-reference.png',newsource)
faceY=newsource.height-40
roofparts={
 'sheet':newsource.crop((24,28,40,44)),
 'ridge':newsource.crop((24,0,40,8)),
 'eave':newsource.crop((24,faceY-8,40,faceY)),
 'left':newsource.crop((0,16,8,32)),
 'right':newsource.crop((152,16,160,32)),
 'brace':newsource.crop((32,20,48,28)),
}
def service_building(w,h):
 roofH=h-40;out=Image.new('RGBA',(w,h))
 repeat(out,roofparts['sheet'],(8,8,w-16,roofH-16))
 repeat(out,roofparts['ridge'],(8,0,w-16,8));repeat(out,roofparts['eave'],(8,roofH-8,w-16,8))
 repeat(out,roofparts['left'],(0,8,8,roofH-16));repeat(out,roofparts['right'],(w-8,8,8,roofH-16))
 for x,sx in [(0,0),(w-8,152)]:
  out.alpha_composite(newsource.crop((sx,0,sx+8,8)),(x,0))
  out.alpha_composite(newsource.crop((sx,faceY-8,sx+8,faceY)),(x,roofH-8))
 repeat(out,roofparts['brace'],(8,(roofH//2)//8*8,w-16,8))
 if w==160:out.alpha_composite(newsource.crop((0,faceY,160,newsource.height)),(0,roofH))
 else:
  # Complete shutter and window/conduit group remain whole, on identical rows.
  repeat(out,newsource.crop((80,faceY,96,newsource.height)),(88,roofH,w-160,40))
  out.alpha_composite(newsource.crop((0,faceY,88,newsource.height)),(0,roofH))
  out.alpha_composite(newsource.crop((88,faceY,160,newsource.height)),(w-72,roofH))
  out.alpha_composite(newsource.crop((16,faceY,80,newsource.height)),(144,roofH))
 return out
annex=service_building(160,128);workshop=service_building(304,160)
for name,im in [('service-annex-redesign',annex),('factory-workshop-redesign',workshop)]:png(A/'modules'/f'{name}.png',im)
# Approved complete STE hall, exported into reusable native architecture.
# The roof uses the same sheet/ridge/eave materials as the other buildings.
# The two complete facade bays are mirrored, preserving aligned windows,
# recessed walls and brick foundation while sharing exact H/V tile patterns.
unionSource=asset(A/'source/union-ste-building-v4.png')
alpha=unionSource.getchannel('A').point(lambda v:255 if v>=184 else 0)
unionSource.putalpha(alpha);unionSource=unionSource.crop(alpha.getbbox())
unionReference=unionSource.resize((304,round(unionSource.height*304/unionSource.width)),Image.Resampling.NEAREST)
png(A/'modules/union-ste-native-reference.png',unionReference)
facade=unionReference.crop((0,unionReference.height-48,304,unionReference.height))
union=Image.new('RGBA',(304,176))
union.alpha_composite(service_building(304,168).crop((0,0,304,128)),(0,0))
union.alpha_composite(facade.crop((0,0,120,48)),(0,128))
union.alpha_composite(facade.crop((120,0,184,48)),(120,128))
union.alpha_composite(facade.crop((0,0,120,48)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(184,128))
# Use the original approved logo, rather than a generated imitation of it.
logo=asset(G/'art/space-workers-union-logo-v1/logo-ste.png')
alpha=logo.getchannel('A').point(lambda v:255 if v>=184 else 0)
logo.putalpha(alpha);logo=logo.crop(alpha.getbbox()).resize((56,56),Image.Resampling.NEAREST)
union.alpha_composite(logo,(124,72))
png(A/'modules/union-ste-sign.png',logo)
png(A/'modules/union-ste-building.png',union)
base=Image.new('RGBA',(512,320));repeat(base,floor,(0,0,512,320));repeat(base,wall,(0,0,512,80));repeat(base,header,(0,40,512,8));repeat(base,curb,(0,80,512,32));repeat(base,curb,(0,288,512,32))
# Posts keep the same phase at each512px seam. No loose construction pieces.
for x in range(0,512,128):base.alpha_composite(post,(x,80));base.alpha_composite(post,(x,288))
first=base.copy();middle=base.copy();last=base.copy()
first.alpha_composite(workshop,(64,24));middle.alpha_composite(annex,(176,24));last.alpha_composite(union,(160,24))
repeat(first,side.crop((0,0,16,96)),(0,112,16,176));repeat(last,side.crop((0,0,16,96)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(496,112,16,176))
for name,im in [('A-factory-exit',first),('B-repeat-service',middle),('C-union-arrival',last)]:png(A/'segments'/f'{name}.png',indexed(im))
background=Image.new('RGBA',(3072,320))
for x,im in zip(range(0,3072,512),[first,middle,middle,middle,middle,last]):background.alpha_composite(im,(x,0))
png(A/'background-three-segments.png',indexed(background));scene=background.copy()
architecture=[dict(id='factory-exit',box=[64,24,304,160]),*[dict(id=f'service-bay-{i+1}',box=[512*(i+1)+176,24,160,128]) for i in range(4)],dict(id='union',box=[2720,24,304,176])]
solids=[[0,0,3072,112,True]]+[v['box']+[True] for v in architecture];placements=[]
# Only independent objects vary between instances of the exact same B image.
items=[('departure-crates',crates,400,240,[0,0,32,32],True),('departure-barrels',barrels,416,128,[0,0,40,40],True),('truck-lower-1',truck,720,208,[0,0,96,64],True),('barrels-service-1',barrels,928,224,[0,0,40,40],True),('crates-service-2',crates,1200,240,[0,0,32,32],True),('truck-upper-2',truck,1408,112,[0,0,96,64],True),('truck-lower-3',truck,1744,208,[0,0,96,64],True),('barrels-service-3',barrels,1984,224,[0,0,40,40],True),('crates-service-4',crates,2224,240,[0,0,32,32],True),('truck-upper-4',truck,2432,112,[0,0,96,64],True),('arrival-crates',crates,2608,240,[0,0,32,32],True)]
for name,im,x,y,(dx,dy,w,h),block in items:
 assert 0<=x and x+im.width<=3072 and y+im.height<=288,(name,'cut prop')
 scene.alpha_composite(im,(x,y));solids.append([x+dx,y+dy,w,h,block]);placements.append(dict(id=name,canvas=[x,y,*im.size],footprint=[x+dx,y+dy,w,h],blocks_shots=block));png(A/'objects'/f'{name}.png',im)
scene=indexed(scene);png(A/'complete-native.png',scene)
d=dict(phase='12',size=[3072,320],bounds=[16,112,3055,287],start=[48,208],solids=solids,exit=[2800,208,160,64],camera_player_y=200,camera_south_start=224,points=[],pauses=[],segments=['A','B','B','B','B','C'],segment_size=[512,320],placements=placements,architecture=architecture)
goals=[[624,208],[624,168],[880,168],[1008,168],[1008,216],[1392,216],[1600,216],[1600,168],[1904,168],[2032,168],[2032,216],[2576,216],[2848,216]]
waypoints=[d['start']]
for goal in goals:waypoints.extend(path(d,waypoints[-1],goal,8)[1:])
d.update(player_waypoints=waypoints,route_points=[[x+8,y+8] for x,y in waypoints],point_semantics='CENTERS; actor foot top-left=center-8')
d['points']=d['route_points'];d['pauses']=[i for i,p in enumerate(waypoints) if p in ([624,168],[1600,168],[2576,216])];d['geometry_validation']=validate(d)
samples=0
for a,b in zip(waypoints,waypoints[1:]):
 for i in range(int(math.dist(a,b))+1):
  ratio=i/max(1,int(math.dist(a,b)));x=round(a[0]+(b[0]-a[0])*ratio);y=round(a[1]+(b[1]-a[1])*ratio);assert free(d,x,y,8),(a,b,x,y);samples+=1
d['geometry_validation'].update(extra_margin_pixels=8,swept_margin_samples=samples)
d['camera_interest']=[dict(id=v['id'],name=v['id'],bbox=v['box'],position=[2776,216] if v['id']=='union' else [v['box'][0]+v['box'][2]//2-8,v['box'][1]+v['box'][3]+16]) for v in architecture]
# Preserve detail and use a static atlas whenever its exact deduplication fits.
tiles,mapping,reused=pack(scene);assert len(tiles)<=640,('phase12 full atlas exceeds static budget',len(tiles))
raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in colors]
emit(A/'native/tiles.bin',raw);emit(A/'native/map.bin',struct.pack('>'+str(len(mapping))+'H',*mapping));emit(A/'native/palette.bin',struct.pack('>16H',*words));png(A/'native/map-native.png',scene)
# Independently decode every VDP H/V map entry to prove exact reconstruction.
restored=Image.new('P',scene.size);restored.putpalette(palette)
for i,v in enumerate(mapping):
 patch=Image.frombytes('P',(8,8),tiles[v&2047]);patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if v&0x800 else patch;patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM) if v&0x1000 else patch;restored.paste(patch,(i%384*8,i//384*8))
assert restored.tobytes()==scene.tobytes()
seams=[]
for x in [512,1024,1536,2048,2560]:
 seam=indexed(background.crop((x-32,0,x+32,320)));png(A/'seams'/f'{x}.png',seam);seams.append(seam.tobytes())
assert len(set(seams))==1,'background seams differ'
d.update(memory=dict(scene_tiles=len(tiles),objective_tiles=0,total_tiles=len(tiles),budget=640,free_tiles=640-len(tiles),graphics_bytes=len(raw),map_bytes=len(mapping)*2,palette_bytes=32,pixel_exact_reassembly=True,lossy_pattern_replacements=0),native=dict(tiles='native/tiles.bin',map='native/map.bin',palette='native/palette.bin'),sources=sources,route_length_px=round(sum(math.dist(a,b) for a,b in zip(waypoints,waypoints[1:])),1),seams_pixel_identical=True,base_B_copies_identical=True,status='integrated-local; user visual acceptance not claimed',art_method='ImageGen service buildings and approved STE hall: repeated native roof materials, complete mirrored facade bays, central entrance and original STE logo; exact H/V deduplication',story='Escort Dinorah from factory service exit to union rest room; success13A, escort death13B. No new gates or valve objective.')
review=scene.convert('RGBA');draw=ImageDraw.Draw(review)
for x,y,w,h,*_ in solids:draw.rectangle((x,y,x+w-1,y+h-1),outline='#ff855d',width=1)
draw.line([tuple(p) for p in d['points']],fill='#50ffff',width=2)
for x in range(512,3072,512):draw.line((x,0,x,319),fill='#ede18a',width=1)
png(A/'pathing.png',review)
for i,(label,x,y) in enumerate([('departure',208,208),('service-lower',760,168),('service-upper',1456,216),('second-lower',1776,168),('union',2848,216)]):
 cx=max(0,min(2752,x-152));cy=0 if label in ('departure','union','service-lower','second-lower') else max(0,min(96,y-200));view=scene.crop((cx,cy,cx+320,cy+224)).convert('RGB');draw=ImageDraw.Draw(view);draw.rectangle((0,0,319,23),fill='#141e20');draw.text((8,6),'FASE12 / PREVIA DE COMPOSICAO',fill='#e8cf88');png(A/'cameras'/f'{i+1}-{label}.png',view)
js(A/'manifest.json',d);print(json.dumps({'memory':d['memory'],'geometry':d['geometry_validation'],'route':waypoints,'pauses':d['pauses']},indent=2))
