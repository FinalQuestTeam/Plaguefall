from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import importlib.util,numpy as np,json,struct
P=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('asm',P/'build_assemblies.py');asm=importlib.util.module_from_spec(spec);spec.loader.exec_module(asm);asm.USE=[1,2,6,8];O=P/'cycle3-candidate';O.mkdir(exist_ok=True);S=Image.open(P/'source/whole-v2-clean.png').convert('RGB');W,H=3072,320
palette=asm.RGB.copy();palette[2]=(0,36,72);palette[3]=(0,72,109);palette[4]=(36,109,145)

def indexed(rgb,indices=range(1,16)):
 a=np.asarray(rgb.convert('RGB'),dtype=np.int32);p=np.array([palette[i]for i in indices],dtype=np.int32);ix=((a[:,:,None]-p[None,None])**2).sum(3).argmin(2);o=Image.fromarray(np.array(list(indices),dtype=np.uint8)[ix],'P');o.putpalette(sum(map(list,palette),[])+[0]*720);return o
mods={}
# Full structural details and axis materials replace coarse room masses.
def detail(name,box,size):
 c=S.crop(box);r=min(size[0]/c.width,size[1]/c.height);nw,nh=round(c.width*r),round(c.height*r);z=indexed(c.resize((nw,nh),Image.Resampling.NEAREST)).convert('RGBA');o=Image.new('RGBA',size);o.alpha_composite(z,((size[0]-nw)//2,(size[1]-nh)//2));mods[name]=o
for args in [('inlet-detail',[120,64,292,310],[56,80]),('stairs-detail',[1920,28,2136,296],[64,80]),('tank-detail',[1112,204,1580,584],[128,104]),('bridge-detail',[688,352,888,528],[80,72]),('canopy',[1790,156,1950,300],[48,48]),('curve',[500,220,800,480],[96,88])]:detail(*args)
# Pixel-sharp complete cross-sections, only their natural material axis repeats.
for name,box,size in [('floor',[284,372,412,436],[64,32]),('water',[800,576,864,640],[32,32]),('bank',[208,520,240,648],[8,32]),('side',[22,324,54,388],[8,16]),('corner',[16,488,96,656],[16,32])]:detail(name,box,size)
out=Image.new('RGBA',(W,H),(*palette[2],255))
def fill(name,rect):
 x,y,w,h=rect;m=mods[name]
 for yy in range(y,y+h,m.height):
  for xx in range(x,x+w,m.width):out.alpha_composite(m.crop((0,0,min(m.width,x+w-xx),min(m.height,y+h-yy))),(xx,yy))
def put(name,x,y):out.alpha_composite(mods[name],(x,y))
fill('water',(0,0,W,H))
# Four real platform rooms and alternating north/south connecting galleries.
platforms=[[24,96,640,176],[664,208,160,64],[824,80,448,192],[1272,96,184,80],[1456,80,672,192],[2128,184,416,80],[2160,112,192,152],[2544,88,504,184]]
mask=np.zeros((40,384),dtype=bool)
for x,y,w,h in platforms:
 fill('floor',(x,y,w,h));mask[y//8:(y+h)//8,x//8:(x+w)//8]=True
# Wall faces on every exposed horizontal run, side returns on exposed verticals.
for ty in range(40):
 for tx in range(384):
  if not mask[ty,tx]:continue
  if ty==0 or not mask[ty-1,tx]:fill('bank',(tx*8,ty*8-32,8,32))
  if ty==39 or not mask[ty+1,tx]:fill('bank',(tx*8,ty*8+8,8,min(32,H-ty*8-8)))
  if tx==0 or not mask[ty,tx-1]:fill('side',(max(0,tx*8-8),ty*8,8,8))
  if tx==383 or not mask[ty,tx+1]:fill('side',(tx*8+8,ty*8,8,8))
# Four source-derived assemblies, each a coherent complete construction:
# inlet/cistern with curved outlet; whole arched bridge; pump basin; refuge.
def basin(x,y,w,h):
 fill('water',(x,y,w,h));fill('bank',(x,y-32,w,32));fill('bank',(x,y+h,w,min(32,H-y-h)));fill('side',(x-8,y,8,h));fill('side',(x+w,y,8,h))
# The cistern contains the inlet and a connected canal that turns into the bank.
basin(80,104,144,80);basin(224,144,176,40);put('curve',384,128);put('inlet-detail',112,32)
# Cross-water room: deep banks leave one wide, legible bridge deck.
basin(912,80,48,64);basin(912,192,48,80);put('bridge-detail',896,152)
# Maintenance island: full water containment, connected pipework and tank body.
basin(1656,144,160,96);put('tank-detail',1672,128)
# Refuge: entire stair opening and canopy share a complete masonry plinth.
fill('bank',(2848,112,160,32));fill('bank',(2896,80,32,32));put('canopy',2848,72);put('stairs-detail',2928,48)
# Reused maintenance ensembles make the long approach a service alcove.
put('tank-detail',2192,120);put('inlet-detail',2480,104);basin(2496,184,24,16)
placements=[('cistern',[72,32,408,184]),('bridge',[896,48,80,256]),('pump-island',[1648,112,176,160]),('refuge',[2848,48,160,96])]
native=indexed(out.convert('RGB'));native.convert('RGB').save(O/'complete-native.png');native.save(O/'complete-indexed.png')
raw=np.array(native);cells=raw.reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64);u,m=np.unique(cells,axis=0,return_inverse=True);print('native scene tiles',len(u))
for name,im in mods.items():im.save(O/f'{name}.png')
for i,x in enumerate([0,400,800,1200,1600,2000,2400,2752]):
 for cy in [0,48,96]:native.crop((x,cy,x+320,cy+224)).convert('RGB').save(O/f'camera-x{i}-y{cy}.png')
(O/'candidate.json').write_text(json.dumps({'tiles':len(u),'platforms':platforms,'assemblies':placements,'status':'composition_checkpoint_not_integrated','source':'source/whole-v2-clean.png','details':'Full1px source structures and complete material cross-sections; no coarse room masses and no tile substitution.'},indent=2)+'\n')
# Export authored collision and center routes; art and geometry remain private.
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
# Foot obstacles include the complete authored bank faces and body silhouettes.
vertical=[[112,32,56,80],[80,72,144,32],[80,184,320,32],[224,112,176,32],[384,128,96,88],[1656,112,160,32],[1648,144,8,96],[1816,144,8,96],[1656,240,160,32],[1672,128,128,104],[2192,120,128,104],[2480,104,56,80],[2496,200,24,32],[2848,112,160,32],[2896,80,32,32],[2848,72,48,48],[2928,48,64,80]]
solids += [r+[True]for r in vertical]
solids += [[80,104,144,80,False],[224,144,176,40,False],[912,80,48,64,False],[912,192,48,80,False],[1656,144,160,96,False],[2496,184,24,16,False]]
points=[[48,232],[280,232],[544,232],[648,240],[776,240],[848,240],[880,216],[880,168],[1000,168],[1168,144],[1248,136],[1360,136],[1480,136],[1552,96],[1840,96],[1840,216],[2096,216],[2160,248],[2344,248],[2432,248],[2544,248],[2688,200],[2824,200],[3016,176]]
manifest={'phase':'6A','size':[W,H],'bounds':[24,80,3047,271],'start':[40,224],'route_points':points,'route_points_are':'centers','pauses':[2,10,15,19],'exit':[2976,152,64,64],'solids':solids,'gates':[],'valves':[],'valve_approaches':[],'gate_shot_approaches':[],'camera_interest':[{'name':'Cisterna e arco','bbox':[72,32,168,184]},{'name':'Ponte inteira','bbox':[880,136,112,96]},{'name':'Ilha de bombas','bbox':[1648,112,176,160]},{'name':'Recuo de manutenção','bbox':[2160,112,192,152]},{'name':'Abrigo','bbox':[2848,48,160,96]}],'camera_player_y':200,'camera_player_y_samples':[184,200,248],'sourcePaths':['source/whole-v1.png','source/whole-v2-clean.png'],'assembly_notes':placements,'native':{'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin','image':'complete-native.png','objectives':'complete-objectives.png'},'memory':{'scene_tiles':len(u),'objective_tiles':0,'total_tiles':len(u),'budget':640,'approximate_tile_replacements':0},'status':'private_candidate_pending_final_geometry_and_visual_review'}
from collections import deque
import math
def free(x,y,margin=8,extra=()):
 r=8+margin;l,t,right,bottom=manifest['bounds'];return l<=x-r and x+r<=right+1 and t<=y-r and y+r<=bottom+1 and not any(x-r<rx+rw and x+r>rx and y-r<ry+rh and y+r>ry for rx,ry,rw,rh,*_ in solids+list(extra))
sweep=0
for a,b in zip(points,points[1:]):
 n=math.ceil(math.dist(a,b))
 for i in range(n+1):
  x,y=[a[k]+(b[k]-a[k])*i/n for k in [0,1]];assert free(x,y),('route clearance',a,b,x,y);sweep+=1
seen=set();todo=deque([tuple(points[0])])
while todo:
 x,y=todo.popleft()
 if(x,y)in seen or not free(x,y):continue
 seen.add((x,y));todo.extend([(x-8,y),(x+8,y),(x,y-8),(x,y+8)])
assert tuple(points[-1])in seen
for interest,feet in zip(manifest['camera_interest'],[[40,200],[872,160],[1832,192],[2336,240],[3008,168]]):
 assert free(feet[0]+8,feet[1]+8)
 interest['preferred_feet']=feet
manifest['geometry_checks']={'actor_feet':[16,16],'margin':8,'swept_samples':sweep,'reachable_centers':len(seen),'arrival_connected':True}
# All output bytes correspond exactly to displayed native image.
(O/'native').mkdir(exist_ok=True)
(O/'native/tiles.bin').write_bytes(b''.join(bytes((int(r[i])<<4)|int(r[i+1])for i in range(0,64,2))for r in u))
(O/'native/map.bin').write_bytes(struct.pack('>'+str(len(m))+'H',*map(int,m)))
colors=[tuple(round(v*7/255)for v in c)for c in palette]
(O/'native/palette.bin').write_bytes(struct.pack('>16H',*[(r<<1)|(g<<5)|(b<<9)for r,g,b in colors]))
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');native.convert('RGB').save(O/'complete-objectives.png')
for alias in ['closed','collapse','open']:native.convert('RGB').save(O/f'complete-{alias}-objectives.png')
print(manifest['geometry_checks'])

# Stable root handoff: render() exposes exact binary file paths and metadata.
def render(key='6A'):
 assert key=='6A'
 return {str(f.relative_to(O)):f.read_bytes()for f in O.glob('native/*.bin')},manifest
if __name__=='__main__':
 import sys,shutil
 if '--publish'in sys.argv:
  for name in ['complete-native.png','complete-indexed.png','complete-objectives.png','complete-closed-objectives.png','complete-collapse-objectives.png','complete-open-objectives.png','manifest.json']:
   shutil.copyfile(O/name,P/name)
  (P/'native').mkdir(exist_ok=True)
  for f in (O/'native').glob('*.bin'):shutil.copyfile(f,P/'native'/f.name)
  print('Published private6A handoff, no active ROM/resources changed.')
