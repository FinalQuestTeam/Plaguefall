"""Private phase9: full approved folded source -> whole modular architecture."""
from pathlib import Path
from collections import deque
import importlib.util,json,shutil,hashlib
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parent;G=A.parents[3]
s=importlib.util.spec_from_file_location('pack',G/'art/campaign-whole-scenes-v1/pack.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
for d in ['modules','native','reviews']:(A/d).mkdir(exist_ok=True)
PAL=[(0,0,0),(218,218,182),(182,182,145),(145,145,145),(109,109,109),(72,72,72),(36,36,36),(36,72,109),(72,109,145),(36,109,145),(36,72,36),(72,109,36),(145,72,36),(109,36,36),(182,145,36),(36,72,72)]
src=Image.open(A/'source/whole-folded-cycle3.png').convert('RGB');parts={};meta=[]
def part(n,box,size,grid=2):
 im,_=P.indexed(src.crop(box),size,grid,palette=PAL);parts[n]=im;im.save(A/'modules'/(n+'.png'));meta.append({'id':n,'source_bbox':list(box),'size':list(size),'grid':grid,'source':'source/whole-folded-cycle3.png'});return im
part('blue-left',(526,6,590,142),(32,64));part('blue-run',(730,8,762,142),(16,64));part('blue-right',(1070,8,1136,142),(32,64))
part('flat-left',(64,40,104,120),(24,56));part('flat-run',(180,40,212,120),(16,56));part('flat-right',(284,40,324,120),(24,56))
part('wall',(112,170,128,186),(16,16));part('cream',(180,304,196,320),(16,16));part('plinth',(100,206,132,218),(16,8))
part('office-window',(110,130,145,158),(32,24),1);part('office-door',(150,156,198,214),(32,40),1)
part('blue-window',(752,1078,804,1102),(40,24),1);part('dock-door',(606,134,688,196),(64,48),1);part('roll-door',(130,1084,224,1138),(64,48),1)
part('truck',(924,154,1040,336),(72,120),2)
part('engine-body',(680,580,922,672),(112,40),2)
part('pipe-arch',(716,520,808,614),(40,48),2)
part('pipe-elbow',(908,592,990,708),(32,48),2)
part('pipe-stack',(1032,584,1118,710),(32,48),2)
part('tank-top',(550,974,630,1014),(48,24),2)
part('tank-body',(554,1022,630,1046),(48,16),2)
part('tank-foot',(550,1096,630,1128),(48,16),2)
part('gate-post',(864,1004,900,1156),(24,144),2)
part('gate-run',(948,1040,980,1148),(16,72),2)
part('gate-header',(932,1028,964,1052),(16,16),2)
part('fence',(232,366,264,438),(16,40));part('foliage',(332,12,396,76),(32,32));part('post',(220,358,240,442),(16,48))
part('road',(704,1240,720,1256),(16,16));parts['road'].paste(5,(0,0,16,16));parts['road'].save(A/'modules/road.png');part('pad',(760,280,776,296),(16,16));part('curb',(200,430,232,438),(16,8));part('dash',(500,430,540,438),(24,4),1)
# Retain the source dash silhouette on neutral asphalt; the requested yellow
# marking uses an existing RGB333 palette entry, preserving all steel blues.
parts['dash'].putdata([14 if v in (2,3,4) else 5 for v in parts['dash'].getdata()]);parts['dash'].save(A/'modules/dash.png')
def canvas(size):
 im=Image.new('P',size);im.putpalette(parts['road'].getpalette());return im
def fill(im,n,box):
 p=parts[n];l,t,r,b=box
 for y in range(t,b,p.height):
  for x in range(l,r,p.width):im.paste(p.crop((0,0,min(p.width,r-x),min(p.height,b-y))),(x,y))
def building(n,w,h,roof='flat',kind='office'):
 im=canvas((w,h));rh=64 if roof=='blue'else 56;cap=32 if roof=='blue'else 24
 fill(im,'cream'if kind=='utility'else'wall',(0,rh,w,h-8));im.paste(parts[roof+'-left'],(0,0));fill(im,roof+'-run',(cap,0,w-cap,rh));im.paste(parts[roof+'-right'],(w-cap,0));fill(im,'plinth',(0,h-8,w,h))
 if kind=='dock':
  for x in [40,136,232]:im.paste(parts['dock-door'],(x,h-56))
 elif kind=='warehouse':
  im.paste(parts['roll-door'],(w-88,h-56));im.paste(parts['office-window'],(32,h-48));im.paste(parts['office-window'],(96,h-48))
 elif kind=='utility':im.paste(parts['office-door'],(w-48,h-48));im.paste(parts['office-window'],(24,h-48))
 else:
  for x in [32,88,184,240]:im.paste(parts['office-window'],(x,h-64))
  im.paste(parts['office-door'],(w//2-16,h-48))
 im.save(A/'modules'/(n+'-assembly.png'));return im
assemblies={'office':building('office',304,160),'dock':building('dock',304,160,'blue','dock'),'warehouse':building('warehouse',304,112,'flat','warehouse'),'utility':building('utility',160,104,'flat','utility'),'utility-low':building('utility-low',160,88,'flat','utility'),'truck':parts['truck']}
# Complete equipment assemblies reuse real authored mechanical cross-sections.
# Quiet physical slabs replace the irrelevant surrounding source-yard pixels.
engine=canvas((256,120));fill(engine,'pad',(0,0,256,120));engine.paste(parts['engine-body'],(48,48));engine.paste(parts['pipe-arch'],(64,4));engine.paste(parts['pipe-elbow'],(152,48));engine.paste(parts['pipe-stack'],(208,40));fill(engine,'fence',(0,80,256,120));engine.paste(parts['post'],(0,72));engine.paste(parts['post'],(240,72));fill(engine,'fence',(0,0,256,16));fill(engine,'post',(0,16,16,80));fill(engine,'post',(240,16,256,80));assemblies['machine-yard']=engine
tanks=canvas((160,160));fill(tanks,'pad',(0,0,160,160))
for tx in [16,88]:
 tanks.paste(parts['tank-top'],(tx,16));fill(tanks,'tank-body',(tx,40,tx+48,120));tanks.paste(parts['tank-foot'],(tx,120))
fill(tanks,'fence',(0,120,160,160));tanks.paste(parts['post'],(0,112));tanks.paste(parts['post'],(144,112));fill(tanks,'fence',(0,0,160,16));fill(tanks,'post',(0,16,16,112));fill(tanks,'post',(144,16,160,112));assemblies['tank-yard']=tanks
gate=canvas((224,144));fill(gate,'road',(0,0,224,144));gate.paste(parts['gate-post'],(0,0));gate.paste(parts['gate-post'].transpose(Image.Transpose.FLIP_LEFT_RIGHT),(200,0));fill(gate,'gate-run',(24,56,200,128));fill(gate,'gate-header',(24,40,200,56));assemblies['gate']=gate
for n in ['machine-yard','tank-yard','gate']:assemblies[n].save(A/'modules'/(n+'-assembly.png'))
# Shared roof grammar remains human-scale; none of the full source buildings
# is squashed to make it fit the corridor length.
placements=[('office',64,32),('utility',416,208),('dock',672,24),('truck',1048,192),('machine-yard',1216,32),('warehouse',1424,200),('utility-low',1808,224),('tank-yard',1840,24),('utility-low',2080,224),('gate',2288,40)]
world=canvas((2560,320));fill(world,'road',(0,0,2560,320));solids=[]
sectors=[(0,608,96),(608,1152,104),(1152,1808,96),(1808,2560,104)]
for l,r,b in sectors:
 fill(world,'foliage',(l,0,r,b-40));fill(world,'fence',(l,b-40,r,b));solids.append([l,0,r-l,b])
 for x in range(l,r,160):world.paste(parts['post'],(x,b-48))
fill(world,'fence',(0,280,2560,320))
for x in range(0,2560,160):world.paste(parts['post'],(x,272))
for n,x,y in placements:
 im=assemblies[n]
 # Complete physical pad is tied to each assembly, never a spare rectangle.
 if n not in ['truck','machine-yard','tank-yard','gate']:fill(world,'pad',(x+8,y+im.height,x+im.width-8,min(320,y+im.height+8)));fill(world,'curb',(x+8,y+im.height+8,x+im.width-8,min(320,y+im.height+16)))
 world.paste(im,(x,y))
 if n=='gate':
  # Posts and closed leaves are solid. The air below the leaf stays free.
  solids.extend([[x,y,24,144],[x+200,y,24,144],[x+24,y+56,176,72]])
 else:solids.append([x,y,*im.size])
# Source road dashes form one intentional travel lane through open courts.
for x,y in [(160,240),(320,240),(608,240),(768,240),(1280,184),(1888,208),(2416,216)]:world.paste(parts['dash'],(x,y))
world.save(A/'complete-before-pack.png');_,stats=P.pack({'map':world},PAL,A/'native','street09',640);shutil.copy2(A/'native/map-native.png',A/'complete-native.png')
bounds=[16,96,2543,279];start=[24,216]
points=[[32,224],[392,224],[392,184],[616,184],[640,224],[1000,224],[1000,168],[1144,168],[1184,184],[1400,184],[1752,184],[1808,208],[2032,208],[2264,208],[2512,216]]
# Points use centers, additional player controller waypoints use feet origins.
def blocked(x,y,size=16):return x<bounds[0]or y<bounds[1]or x+size-1>bounds[2]or y+size-1>bounds[3]or any(x<a+w and x+size>a and y<b+h and y+size>b for a,b,w,h in solids)
assert all(v%8==0 for r in solids for v in r);assert not blocked(*start)
seen={tuple(start)};q=deque(seen)
while q:
 x,y=q.popleft()
 for p in [(x-8,y),(x+8,y),(x,y-8),(x,y+8)]:
  if p not in seen and not blocked(*p):seen.add(p);q.append(p)
for i,(x,y)in enumerate(points):assert(x-8,y-8)in seen,('point',i,x,y)
sweep=0
for i,(a,b)in enumerate(zip(points,points[1:])):
 n=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
 for t in range(n+1):
  x=round(a[0]+(b[0]-a[0])*t/max(1,n))-8;y=round(a[1]+(b[1]-a[1])*t/max(1,n))-8
  assert not blocked(x,y),('sweep',i,x,y)
  assert not blocked(x-8,y-8,32),('eight-pixel-clearance',i,x,y)
  sweep+=1
interests=[]
for n,x,y in placements:
 w,h=assemblies[n].size
 # Landmark poses are in front of northern architecture, above southern.
 py=y+h+(8 if n=='tank-yard' else 16) if y<100 else y-24;px=x+w//2-8
 if blocked(px,py):continue
 cx=max(0,min(2240,x+w//2-160));cy=max(0,min(96,y+h-224 if y>=192 else y-24));im=world.convert('RGBA');hero=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA');im.alpha_composite(hero,(px-8,py-31));im=im.crop((cx,cy,cx+320,cy+224)).convert('RGB');dr=ImageDraw.Draw(im);dr.rectangle((0,0,319,23),fill='#18202a');dr.text((5,6),'NATIVE - NO ROM',fill='white');file=f'reviews/camera-{n}-{x}.png';im.save(A/file)
 interests.append({'id':f'{n}-{x}','bbox':[x,y,w,h],'center':[x+w//2,y+h//2],'position':[px,py],'preview':file})
exit=[2480,192,64,64];layout=world.convert('RGB');d=ImageDraw.Draw(layout)
for x,y,w,h in solids:d.rectangle((x,y,x+w-1,y+h-1),outline='red')
d.line([tuple(v)for v in points],fill='yellow',width=2);layout.save(A/'layout.png')
m={'phase':'9','size':[2560,320],'bounds':bounds,'start':start,'solids':solids,'route_points':points,'point_semantics':'CENTERS; actor feet top-left=center−8','player_waypoints':[[x-8,y-8]for x,y in points],'pauses':[],'exit':exit,'camera_player_y':200,'camera_interest':interests,'sources':[{'path':'source/whole-folded-cycle3.png','sha256':hashlib.sha256((A/'source/whole-folded-cycle3.png').read_bytes()).hexdigest(),'authoring':'Whole folded scene built with native ImageGen by factory agent; source approved before modular extraction.'}],'memory':{'scene_tiles':stats['tiles'],'objective_tiles':0,'total_tiles':stats['tiles'],'budget':640,'free_tiles':640-stats['tiles'],'graphics_bytes':stats['tiles']*32,'map_bytes':20480,'palette_bytes':32,'collision_mask_words':400,'lossy_pattern_replacements':0,'pixel_exact_reassembly':True},'modules':meta,'assemblies':[{'id':n,'size':list(i.size)}for n,i in assemblies.items()],'placements':placements,'geometry':{'actor_footprint':[16,16],'BFS_step':8,'connected_positions':len(seen),'all_points_reachable':True,'swept16pxSamples':sweep,'all_segments_collision_free':True},'complete':'complete-native.png','layout':'layout.png','native':{'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin'},'status':'candidate_requires_visual_review'}
(A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('tiles',stats['tiles'],'BFS',len(seen),'sweep',sweep)
