from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import importlib.util,numpy as np,json,struct
P=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('asm',P/'build_assemblies.py');asm=importlib.util.module_from_spec(spec);spec.loader.exec_module(asm);asm.USE=[1,2,6,8];O=P/'cycle2-candidate';S=Image.open(P/'source/whole-v2-clean.png').convert('RGB');W,H=3072,320
palette=asm.RGB

def indexed(rgb,indices=range(1,16)):
 a=np.asarray(rgb.convert('RGB'),dtype=np.int32);p=np.array([palette[i]for i in indices],dtype=np.int32);ix=((a[:,:,None]-p[None,None])**2).sum(3).argmin(2);o=Image.fromarray(np.array(list(indices),dtype=np.uint8)[ix],'P');o.putpalette(sum(map(list,palette),[])+[0]*720);return o
mods={}
for name,(box,size)in asm.BOXES.items():mods[name],_=asm.convert(S,box,size)
def detail(name,box,size):
 c=S.crop(box);r=min(size[0]/c.width,size[1]/c.height);nw,nh=round(c.width*r),round(c.height*r);z=indexed(c.resize((nw,nh),Image.Resampling.NEAREST)).convert('RGBA');o=Image.new('RGBA',size);o.alpha_composite(z,((size[0]-nw)//2,(size[1]-nh)//2));mods[name]=o
for args in [('inlet-detail',[120,64,292,310],[56,80]),('stairs-detail',[1920,28,2136,296],[64,80]),('tank-detail',[1320,306,1428,480],[40,64]),('bridge-detail',[718,420,878,564],[48,48])]:detail(*args)
# Pixel-sharp complete cross-sections, only their natural material axis repeats.
for name,box,size in [('floor',[284,372,412,436],[64,32]),('water',[800,536,864,600],[16,16]),('bank',[208,520,240,648],[8,32]),('side',[22,324,54,388],[8,16]),('corner',[16,488,96,656],[16,32])]:detail(name,box,size)
out=Image.new('RGBA',(W,H),(*palette[2],255))
def fill(name,rect):
 x,y,w,h=rect;m=mods[name]
 for yy in range(y,y+h,m.height):
  for xx in range(x,x+w,m.width):out.alpha_composite(m.crop((0,0,min(m.width,x+w-xx),min(m.height,y+h-yy))),(xx,yy))
def put(name,x,y):out.alpha_composite(mods[name],(x,y))
# Four real platform rooms and alternating north/south connecting galleries.
platforms=[[24,96,640,176],[664,208,160,64],[824,80,448,192],[1272,96,184,80],[1456,80,672,192],[2128,184,416,80],[2544,88,504,184]]
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
placements=[('cistern',40,32),('bridge',864,80),('maintenance',1536,48),('refuge',2848,48)]
for name,x,y in placements:put(name,x,y)
# Exact detail overlays preserve recognizable holes/stairs/machinery over broad mass sampling.
put('inlet-detail',72,48);put('bridge-detail',928,152);put('tank-detail',1664,136);put('stairs-detail',2928,48)
native=indexed(out.convert('RGB'));native.convert('RGB').save(O/'complete-native.png');native.save(O/'complete-indexed.png')
raw=np.array(native);cells=raw.reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64);u,m=np.unique(cells,axis=0,return_inverse=True);print('native scene tiles',len(u))
for name,im in mods.items():im.save(O/f'{name}.png')
for i,x in enumerate([0,400,800,1200,1600,2000,2400,2752]):
 for cy in [0,48,96]:native.crop((x,cy,x+320,cy+224)).convert('RGB').save(O/f'camera-x{i}-y{cy}.png')
(O/'candidate.json').write_text(json.dumps({'tiles':len(u),'platforms':platforms,'assemblies':placements,'status':'composition_checkpoint_not_integrated','source':'source/whole-v2-clean.png','details':'Exact full cropped1px inlet/bridge arch/tank/stair overlays; broad complete room masses4px prequantized to4colors; no tile substitution.'},indent=2)+'\n')
