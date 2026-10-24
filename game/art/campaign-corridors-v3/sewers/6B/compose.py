from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import importlib.util,numpy as np,json,struct
P=Path(__file__).resolve().parent;ASRC=P.parent/'6A';spec=importlib.util.spec_from_file_location('asm',ASRC/'build_assemblies.py');asm=importlib.util.module_from_spec(spec);spec.loader.exec_module(asm);asm.USE=[1,2,6,8];O=P/'candidate';O.mkdir(exist_ok=True);S=Image.open(ASRC/'source/whole-v2-clean.png').convert('RGB');W,H=3072,320
palette=asm.RGB.copy();palette[2]=(0,36,72);palette[3]=(0,72,109);palette[4]=(36,109,145)

def indexed(rgb,indices=range(1,16)):
 a=np.asarray(rgb.convert('RGB'),dtype=np.int32);p=np.array([palette[i]for i in indices],dtype=np.int32);ix=((a[:,:,None]-p[None,None])**2).sum(3).argmin(2);o=Image.fromarray(np.array(list(indices),dtype=np.uint8)[ix],'P');o.putpalette(sum(map(list,palette),[])+[0]*720);return o
mods={}
# Full structural details and axis materials replace coarse room masses.
def detail(name,box,size):
 c=S.crop(box);r=min(size[0]/c.width,size[1]/c.height);nw,nh=round(c.width*r),round(c.height*r);z=indexed(c.resize((nw,nh),Image.Resampling.NEAREST)).convert('RGBA');o=Image.new('RGBA',size);o.alpha_composite(z,((size[0]-nw)//2,(size[1]-nh)//2));mods[name]=o
for args in [('inlet-detail',[120,64,292,310],[56,80]),('stairs-detail',[1920,28,2136,296],[64,80]),('tank-detail',[1112,204,1580,584],[96,80]),('bridge-detail',[688,352,888,528],[80,72]),('canopy',[1790,156,1950,300],[48,48]),('curve',[500,220,800,480],[96,88])]:detail(*args)
detail('feed-pipe',[1280,284,1312,300],[16,8]);detail('brick',[208,552,240,584],[8,8]);detail('edge',[208,528,240,560],[8,8]);detail('pillar-face',[48,96,80,224],[32,128])
# Pixel-sharp complete cross-sections, only their natural material axis repeats.
for name,box,size in [('floor',[284,372,412,436],[64,32]),('water',[800,576,864,640],[32,32]),('bank',[208,520,240,648],[8,32]),('side',[22,324,54,388],[8,16]),('corner',[16,488,96,656],[16,32])]:detail(name,box,size)
out=Image.new('RGBA',(W,H),(*palette[2],255))
def fill(name,rect):
 x,y,w,h=rect;m=mods[name]
 for yy in range(y,y+h,m.height):
  for xx in range(x,x+w,m.width):out.alpha_composite(m.crop((0,0,min(m.width,x+w-xx),min(m.height,y+h-yy))),(xx,yy))
def put(name,x,y):out.alpha_composite(mods[name],(x,y))
fill('water',(0,0,W,H))
platforms=[[24,96,640,176],[664,208,168,64],[832,80,400,192],[1232,96,208,80],[1440,80,624,192],[2064,184,160,80],[2224,88,824,184]]
mask=np.zeros((40,384),dtype=bool)
for x,y,w,h in platforms:
 fill('floor',(x,y,w,h));mask[y//8:(y+h)//8,x//8:(x+w)//8]=True
for ty in range(40):
 for tx in range(384):
  if not mask[ty,tx]:continue
  if ty==0 or not mask[ty-1,tx]:fill('bank',(tx*8,ty*8-32,8,32))
  if ty==39 or not mask[ty+1,tx]:fill('bank',(tx*8,ty*8+8,8,min(32,H-ty*8-8)))
  if tx==0 or not mask[ty,tx-1]:fill('side',(max(0,tx*8-8),ty*8,8,8))
  if tx==383 or not mask[ty,tx+1]:fill('side',(tx*8+8,ty*8,8,8))
def basin(x,y,w,h):
 fill('water',(x,y,w,h));fill('bank',(x,y-32,w,32));fill('bank',(x,y+h,w,min(32,H-y-h)));fill('side',(x-8,y,8,h));fill('side',(x+w,y,8,h))
def bank_column(x,y,w,h):
 fill('pillar-face',(x,y,w,h));fill('edge',(x,y,w,8));fill('bank',(x,y+h-32,w,32))
# Real entry cistern, pump island and dry refuge with connected perimeter.
basin(80,104,144,80);put('inlet-detail',112,32)
basin(1480,144,128,96);put('tank-detail',1496,136)
fill('bank',(2848,112,160,32));fill('bank',(2896,80,32,32));put('canopy',2848,72);put('stairs-detail',2928,48)
# The same intact pressure mechanism is deployed high, then low. The native
# diagonal bank ends survive; all temporary bronze gate pixels disappear.
gates=[[960,112,32,64],[2080,192,32,64]];valves=[[920,128],[2040,208]]
for gx,gy,gw,gh in gates:
 bank_column(gx+24,24,32,gy)
 bank_column(gx-8,gy+56,32,H-gy-56)
 put('tank-detail',gx-152,gy-48);fill('feed-pipe',(gx-72,gy+12,16,8))
# Reused whole maintenance inlet distinguishes the approach to the refuge.
put('inlet-detail',2480,104);basin(2496,184,24,16)
native=indexed(out.convert('RGB'));raw=np.array(native);cells=raw.reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64);u,m=np.unique(cells,axis=0,return_inverse=True)
print('6B scene',len(u),'total',len(u)+256)
# Real shared global art is only overlaid in complete-state review images.
game=P.parents[3]
for state,frame in [('closed',0),('collapse',5),('open',None)]:
 image=native.convert('RGBA')
 for gx,gy,gw,gh in gates:
  if frame is not None:image.alpha_composite(Image.open(game/'art/objective-sprites-v1/frames'/f'gate-{frame}.png').convert('RGBA'),(gx-16,gy))
 for vx,vy in valves:image.alpha_composite(Image.open(game/'art/objective-sprites-v1/frames'/f'valve-{0 if state=="closed"else 3}.png').convert('RGBA'),(vx-16,vy-24))
 image.convert('RGB').save(O/f'complete-{state}-objectives.png')
native.convert('RGB').save(O/'complete-native.png');native.save(O/'complete-indexed.png')
for name,im in mods.items():im.save(O/f'{name}.png')
for i,x in enumerate([0,400,800,1200,1600,1920,2400,2752]):
 for cy in [0,48,96]:Image.open(O/'complete-closed-objectives.png').crop((x,cy,x+320,cy+224)).save(O/f'camera-x{i}-y{cy}.png')

def rectangles(grid):
 active={};done=[]
 for y,row in enumerate(grid):
  runs=[];x=0
  while x<grid.shape[1]:
   if not row[x]:x+=1;continue
   left=x
   while x<grid.shape[1]and row[x]:x+=1
   runs.append((left,x-left))
  nxt={}
  for r in runs:
   if r in active:rx,ry,rw,rh=active.pop(r);nxt[r]=[rx,ry,rw,rh+8]
   else:nxt[r]=[r[0]*8,y*8,r[1]*8,8]
  done.extend(active.values());active=nxt
 done.extend(active.values());return done
solids=[r+[False]for r in rectangles(~mask)]
vertical=[[112,32,56,80],[80,72,144,32],[72,104,8,80],[224,104,8,80],[80,184,144,32],[1472,144,8,96],[1608,144,8,96],[1480,112,128,32],[1480,240,128,32],[1496,136,96,80],[2480,104,56,80],[2496,200,24,32],[2848,112,160,32],[2896,80,32,32],[2848,72,48,48],[2928,48,64,80]]
for (gx,gy,gw,gh),(vx,vy) in zip(gates,valves):vertical += [[gx+24,24,32,gy],[gx-8,gy+56,32,H-gy-56],[gx-152,gy-48,96,80],[vx-16,vy-24,32,32]]
solids += [r+[True]for r in vertical]
solids += [[80,104,144,80,False],[1480,144,128,96,False],[2496,184,24,16,False]]
points=[[48,232],[280,232],[544,232],[648,240],[784,240],[848,240],[848,192],[920,160],[936,152],[976,152],[1032,152],[1168,136],[1360,136],[1456,136],[1456,96],[1640,96],[1840,144],[1896,248],[2040,240],[2056,232],[2096,232],[2160,232],[2240,232],[2432,248],[2544,248],[2768,200],[3016,176]]
manifest={'phase':'6B','size':[W,H],'bounds':[24,80,3047,271],'start':[40,224],'route_points':points,'route_points_are':'centers','pauses':[2,7,15,18,24],'exit':[2976,152,64,64],'solids':solids,'gates':gates,'valves':valves,'valve_approaches':[[912,152],[2032,232]],'gate_shot_approaches':[[888,152],[2008,232]],'approach_coordinates':'feet top-left, not centers','camera_interest':[{'name':'Cisterna de entrada','bbox':[72,32,168,184],'preferred_feet':[40,200]},{'name':'Câmara de pressão alta','bbox':[800,64,240,184],'preferred_feet':[912,152]},{'name':'Bacia de bombas','bbox':[1472,112,144,160],'preferred_feet':[1632,192]},{'name':'Câmara de pressão baixa','bbox':[1920,136,224,168],'preferred_feet':[2032,232]},{'name':'Abrigo','bbox':[2848,48,160,96],'preferred_feet':[3008,168]}],'camera_player_y':200,'camera_player_y_samples':[184,200,248],'sourcePaths':['source/whole-v1.png','source/whole-v2.png','source/whole-v3-open-hardware.png','../6A/source/whole-v2-clean.png'],'hardware':'Existing shared global gate191+valve65; no baked gate leaf; native diagonal bank ends persist after0.8s collapse+hide.','states':[{'name':'closed','file':'complete-closed-objectives.png','gate_frame':0},{'name':'collapse','file':'complete-collapse-objectives.png','gate_frame':5,'temporary':True,'solid_until_seconds':0.8},{'name':'open','file':'complete-open-objectives.png','gate_visible':False,'physical_opening':32}],'native':{'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin','image':'complete-native.png','objectives':'complete-closed-objectives.png'},'memory':{'scene_tiles':len(u),'objective_tiles':256,'total_tiles':len(u)+256,'budget':640,'approximate_tile_replacements':0},'status':'private_candidate_pending_geometry_and_visual_review'}
from collections import deque
import math
def free(x,y,margin=8,extra=()):
 r=8+margin;l,t,right,bottom=manifest['bounds'];return l<=x-r and x+r<=right+1 and t<=y-r and y+r<=bottom+1 and not any(x-r<rx+rw and x+r>rx and y-r<ry+rh and y+r>ry for rx,ry,rw,rh,*_ in solids+list(extra))
sweep=0
for a,b in zip(points,points[1:]):
 n=math.ceil(math.dist(a,b))
 for i in range(n+1):
  x,y=[a[k]+(b[k]-a[k])*i/n for k in [0,1]];assert free(x,y),('route clearance',a,b,x,y);sweep+=1
def reachable(extra=(),margin=8):
 seen=set();todo=deque([tuple(points[0])])
 while todo:
  x,y=todo.popleft()
  if(x,y)in seen or not free(x,y,margin,extra):continue
  seen.add((x,y));todo.extend([(x-8,y),(x+8,y),(x,y-8),(x,y+8)])
 return seen
seen=reachable();assert tuple(points[-1])in seen
assert tuple(points[-1])not in reachable(gates);assert tuple(points[-1])not in reachable(gates[1:])
for feet in manifest['valve_approaches']+manifest['gate_shot_approaches']+[x['preferred_feet']for x in manifest['camera_interest']]:assert free(feet[0]+8,feet[1]+8)
for i in range(2):
 access=reachable(gates[i:])
 for feet in [manifest['valve_approaches'][i],manifest['gate_shot_approaches'][i]]:assert(feet[0]+8,feet[1]+8)in access
manifest['geometry_checks']={'actor_feet':[16,16],'margin':8,'swept_samples':sweep,'reachable_centers':len(seen),'arrival_connected':True,'closed_gates_disconnect':True,'first_gate_only_open_still_blocks_exit':True,'open_gap':32}
(O/'native').mkdir(exist_ok=True)
(O/'native/tiles.bin').write_bytes(b''.join(bytes((int(r[i])<<4)|int(r[i+1])for i in range(0,64,2))for r in u))
(O/'native/map.bin').write_bytes(struct.pack('>'+str(len(m))+'H',*map(int,m)))
colors=[tuple(round(v*7/255)for v in c)for c in palette];(O/'native/palette.bin').write_bytes(struct.pack('>16H',*[(r<<1)|(g<<5)|(b<<9)for r,g,b in colors]))
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def render(key='6B'):
 assert key=='6B';return {str(f.relative_to(O)):f.read_bytes()for f in O.glob('native/*.bin')},manifest
if __name__=='__main__':
 import sys,shutil
 if '--publish'in sys.argv:
  for name in ['complete-native.png','complete-indexed.png','complete-closed-objectives.png','complete-collapse-objectives.png','complete-open-objectives.png','manifest.json']:shutil.copyfile(O/name,P/name)
  shutil.copyfile(O/'complete-closed-objectives.png',P/'complete-objectives.png');(P/'native').mkdir(exist_ok=True)
  for f in (O/'native').glob('*.bin'):shutil.copyfile(f,P/'native'/f.name)
  print('Published private6B handoff, no active ROM/resources changed.')
print(manifest['geometry_checks'])
