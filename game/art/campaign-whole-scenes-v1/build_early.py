"""Complete authored images FIRST; cut architectural modules, compose, pack exactly."""
from pathlib import Path
from collections import deque
import struct,json,hashlib,sys,shutil,importlib.util
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent));from pack import *
A=Path(__file__).parent;G=A.parents[1];E=A/'early';S=G/'src/levels'

def source(im,box,size,pal,block=2):return indexed(im.crop(box),size,block,palette=pal)[0]
def stamp_repeat(out,patch,rect):
 x,y,w,h=rect
 for yy in range(y,y+h,patch.height):
  for xx in range(x,x+w,patch.width):out.paste(patch.crop((0,0,min(patch.width,x+w-xx),min(patch.height,y+h-yy))),(xx,yy))
def native_church(damaged=False):
 folder=G/'res/courtyard';ts=(folder/'tiles.bin').read_bytes();raw=(folder/('damaged.bin' if damaged else 'map.bin')).read_bytes();mp=struct.unpack('>'+str(len(raw)//2)+'H',raw)
 out=Image.new('P',(512,384));out.putpalette([c for p in cp for c in p]+[0]*720)
 for n,v in enumerate(mp):
  tile=ts[v*32:(v+1)*32];p=Image.frombytes('P',(8,8),bytes(c for b in tile for c in (b>>4,b&15)));out.paste(p,(n%64*8,n//64*8))
 return out

# The church remains the exact approved image, copied after the new whole scene
# has established the street layout. Separate outcome banks avoid image loss.
pw=struct.unpack('>16H',(G/'res/courtyard/palette.bin').read_bytes());cp=[(((v>>1)&7)*255//7,((v>>5)&7)*255//7,((v>>9)&7)*255//7) for v in pw]
im=Image.open(E/'source/03-street.png').convert('RGB')
# Whole authored quarteirao is the composition reference; each facade is a
# complete architectural cut, with its own roof/door rhythm, not a loose prop.
roof=source(im,(384,0,608,120),(96,56),cp,1)
roofpatch=roof.crop((32,16,48,32));stamp_repeat(roof,roofpatch,(8,8,80,40))
houses=[]
for box in ((384,120,608,232),(736,120,960,232),(1040,120,1264,232)):
 h=Image.new('P',(96,96));h.putpalette(roof.getpalette());h.paste(roof,(0,0));h.paste(source(im,box,(96,40),cp,1),(0,56));houses.append(h)
warehouse=source(Image.open(E/'source/04-warehouse-v2.png').convert('RGB'),(448,0,1000,272),(112,96),cp,1)
stamp_repeat(warehouse,warehouse.crop((32,32,48,48)),(16,8,80,80))
pileup=source(im,(320,216,608,344),(96,64),cp,1)
brick=source(im,(952,320,1080,360),(32,16),cp,1)
curb=source(im,(1040,216,1104,240),(32,16),cp,1).crop((0,0,16,16))
module_dir=E/'modules';module_dir.mkdir(exist_ok=True)
for name,asset in [(f'house-{i+1}',h) for i,h in enumerate(houses)]+[('warehouse-front',warehouse),('car-pileup',pileup),('brick-barrier',brick),('sidewalk-curb',curb)]:asset.save(module_dir/(name+'.png'))
# Quiet road/sky are material fields sampled from the source palette. No
# ground texture above roofs. Warm road, blue distant plane, muted roof line.
road=Image.new('P',(2560,320),11);road.putpalette(sum((list(c) for c in cp),[])+[0]*720)
road.paste(3,(0,0,2560,72));solids=[]
for i,x in enumerate(range(240,2353,96)):road.paste(houses[(i//4+i%2)%3],(x,72))
road.paste(warehouse,(2448,72))
for y in (160,304):stamp_repeat(road,curb,(0,y,2560,16))
road.paste(native_church().crop((24,8,216,104)),(32,72))
# Remove only the source ground connected to the crop edges. All authored car
# and masonry pixels remain; palette-matched road shows through the cutout.
def ground_mask(asset,ground):
 w,h=asset.size;pix=asset.load();seen=set();queue=deque()
 for x in range(w):queue.extend(((x,0),(x,h-1)))
 for y in range(h):queue.extend(((0,y),(w-1,y)))
 while queue:
  x,y=queue.popleft()
  if (x,y) in seen or not(0<=x<w and 0<=y<h) or pix[x,y] not in ground:continue
  seen.add((x,y));queue.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
 mask=Image.new('L',asset.size,255)
 for x,y in seen:mask.putpixel((x,y),0)
 return mask
pilemask=ground_mask(pileup,{5,6,9,10,11});brickmask=ground_mask(brick,{5,6,9,10,11})
placements=[]
for x,north in ((280,True),(848,False),(1328,True),(1784,False),(2240,True)):
 py=184 if north else 200;road.paste(pileup,(x,py),pilemask);solids.append([x+8,py+24,80,40,True])
 wy=176 if north else 264;wh=32 if north else 40
 stamp_repeat(road,brick,(x+32,wy,32,wh));solids.append([x+32,wy,32,wh,True]);placements.append({'x':x,'north':north,'full_pileup':[x,py,96,64]})
for x,y in ((648,232),(1104,176),(1576,248),(2040,176)):
 road.paste(brick,(x,y),brickmask);solids.append([x,y+8,32,8,False])
# Reachability including16x16feet and4pxcontroller margin.
def free(p,margin=0):
 x,y=p
 return 16<=x<=2528 and 176<=y<=288 and not any(x-margin<a+w and x+16+margin>a and y-margin<b+h and y+16+margin>b for a,b,w,h,*_ in solids)
def pathfind(margin=0,allcells=False):
 start=(48,176);prev={start:None};q=deque([start]);goal=None
 while q:
  x,y=q.popleft()
  if 2480<=x+8<2520 and 184<=y+8<216 and goal is None:
   goal=(x,y)
   if not allcells:break
  for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
   if p not in prev and free(p,margin):prev[p]=(x,y);q.append(p)
 assert goal
 p=goal;path=[]
 while p is not None:path.append(p);p=prev[p]
 return list(reversed(path)),prev
path,visited=pathfind(4);allpath,allvisited=pathfind(0,True)
corners=[path[0]]
for i in range(1,len(path)-1):
 if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):corners.append(path[i])
corners.append(path[-1]);assert any(y>=244 for x,y in path) and any(y<=200 for x,y in path if 840<=x<=940)
ruined=road.copy();ruined.paste(native_church(True).crop((24,8,216,104)),(32,72))
code,meta=pack({'map':road},cp,E/'03-street','street');code2,meta2=pack({'map':ruined},cp,E/'03-street-ruined','street_damaged')
(S/'campaign_early_street.inc').write_text('// Whole-image source: campaign-whole-scenes-v1/early/source/03-street.png\n'+code+code2)
layout='// Generated from the whole street composition.\nstatic const ArenaRect streetSolids[]={'+','.join('{'+','.join(map(str,r[:4]))+','+('TRUE' if r[4] else 'FALSE')+'}' for r in solids)+'};\n'
layout+='const ArenaDef EARLY_ARENA03={2560,320,16,176,2543,303,48,176,streetSolids,sizeof(streetSolids)/sizeof(streetSolids[0]),&streetScene};\n'
layout+='static const RoutePoint streetPoints[]={'+','.join('{%s,%s,0}'%(x+8,y+8) for x,y in corners)+'};\nconst RouteDef EARLY_ROUTE03={streetPoints,sizeof(streetPoints)/sizeof(streetPoints[0]),{2472,176,48,48,FALSE}};\n'
(S/'campaign_early_street_layout.inc').write_text(layout)
report=dict(tiles=meta['tiles'],damaged_tiles=meta2['tiles'],width=2560,height=320,bounds=[16,176,2543,303],start=[48,176],solids=solids,exit=[2472,176,48,48],objective='reach',enemy_cap=4,shot_cap=6,spawn_seconds=4,roster=[1,0],traversal_points=corners,church_exact_tiles=288,church_pixel_identical=True,placements=placements,connected_positions=len(allvisited),lossy_tile_replacements=0)
(E/'03-street/layout.json').write_text(json.dumps(report,indent=2)+'\n')

# Warehouse full-scene structural halves and material are cut after inspecting
# the complete source. Exact mirroring saves VRAM while preserving a whole room.
source_image=Image.open(E/'source/04-warehouse-v2.png');im,pal=indexed(source_image,(512,384),1,15)
# Source's whole room provides the material language. Tileable perimeter racks
# maintain warehouse identity when the north wall leaves the camera.
nearest=lambda c:min(range(1,16),key=lambda i:sum((pal[i][k]-c[k])**2 for k in range(3)))
floor_id=nearest((145,145,109));joint_id=nearest((109,109,109))
out=Image.new('P',(512,384),floor_id);out.putpalette(im.getpalette())
# Exact author-cut slab, reduced to two nearby source colors, reused as a
# material, not as a tiny decorative mark scattered across the combat floor.
slab=im.crop((120,120,184,184));slab=slab.point([joint_id if i==joint_id else floor_id for i in range(16)]+[0]*240)
stamp_repeat(out,slab,(0,112,512,272))
wall=im.crop((0,0,256,96)).resize((256,128),Image.Resampling.NEAREST)
out.paste(wall,(0,0));out.paste(wall.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(256,0))
# Reuse the authored lower industrial cladding as the southern perimeter.
# Exact existing rows preserve the budget and keep architecture in low views.
south=wall.crop((0,80,256,112));out.paste(south,(0,352));out.paste(south.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(256,352))
side=im.crop((0,104,32,168))
for y in range(128,384,64):
 out.paste(side,(0,y));out.paste(side.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(480,y))
# Crop connected source-floor pixels away; object silhouettes and contact
# shadows come exclusively from the authored complete room.
crates=im.crop((138,186,210,234)).resize((96,64),Image.Resampling.NEAREST)
cart=im.crop((324,228,408,288)).resize((96,72),Image.Resampling.NEAREST)
floor_colors={i for i,c in enumerate(pal) if max(c)-min(c)<75 and sum(c)>220}
for asset,xy in ((crates,(96,184)),(cart,(328,232))):out.paste(asset,xy,ground_mask(asset,floor_colors))
for name,asset in [('warehouse-structural-half',wall),('warehouse-perimeter-rack',side),('warehouse-crates',crates),('warehouse-cart',cart)]:asset.save(module_dir/(name+'.png'))
code,depotmeta=pack({'map':out},pal,E/'04-warehouse','depot');(S/'campaign_early_depot.inc').write_text(code)
manifestpath=G/'art/campaign-early-v1/manifest.json';manifest=json.loads(manifestpath.read_text());manifest['stages']['03'].update(report);manifest['stages']['04'].update(tiles=depotmeta['tiles'],bounds=[32,128,479,351],start=[48,144],solids=[[104,216,80,32,True],[336,264,88,32,True]])
manifest['sources'].append('campaign-whole-scenes-v1');manifestpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('legacy_early',G/'art/campaign-early-v1/build.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
for key in ('03','04'):manifest['stages'][key]['geometry_validation']=legacy.geometry(manifest['stages'][key])
manifest['sources']=list(dict.fromkeys(manifest['sources']));manifestpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
manifest['notes']=['Fases1,2A/2B e5 preservadas; hashes em campaign-whole-scenes-v1/preserved.json.','Fase3 usa fonte completa,13obstaculos alinhados,desvios alternados e os dois estados exatos da igreja.','Fase4 possui interior completo e entrada enquadrando a construcao.']
manifest['palette_policy']='Whole authored images first, complete architectural cuts; exact RGB333 palette conversion and tile/flip deduplication; no approximate tile replacement.'
manifestpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for new,old in (('03-street','street'),('04-warehouse','depot')):
 for filename in ('tiles.bin','map.bin','palette.bin'):
  shutil.copy2(E/new/filename,G/'art/campaign-early-v1'/old/filename)
 shutil.copy2(E/new/'map-native.png',G/'art/campaign-early-v1'/old/'map-native.png')
shutil.copy2(E/'03-street-ruined/map.bin',G/'art/campaign-early-v1/street/damaged.bin')
(E/'geometry.json').write_text(json.dumps({'street':report,'warehouse':manifest['stages']['04']},indent=2)+'\n')
print('Whole-image scenery3/4 packed:',meta['tiles'],meta2['tiles'],depotmeta['tiles'])
