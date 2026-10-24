"""Private reproducible sewer v3 exporter. Exact palette, exact8x8 patterns."""
from pathlib import Path
from collections import deque
import argparse,json,hashlib,math,struct
import numpy as np
from PIL import Image,ImageDraw,ImageOps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;W,H=3072,320
COLORS=[(0,0,0),(1,1,1),(1,2,3),(1,3,4),(2,4,5),(3,4,4),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(3,2,1),(4,3,1),(5,4,2),(7,6,3),(1,2,1),(2,2,2)]
RGB=[tuple(v*255//7 for v in c)for c in COLORS]
def quantize(im):
 a=np.asarray(im.convert('RGB'),dtype=np.int32);p=np.array(RGB,dtype=np.int32);idx=((a[:,:,None]-p[None,None])**2).sum(3)[:,:,1:].argmin(2).astype(np.uint8)+1;o=Image.fromarray(idx,'P');o.putpalette(sum(map(list,RGB),[])+[0]*720);return o

def render(key='6A',write=True):
 P=ROOT/key;d=json.loads((P/'blockout.json').read_text());S=Image.open(P/'source'/('whole-v1.png'if key=='6A'else'whole-v3-open-hardware.png')).convert('RGB');A=Image.open(ROOT/'6A/source/whole-v1.png').convert('RGB');mods={};records=[]
 def module(name,box,size,axis='none',source='6A',matte=False):
  src=A if source=='6A'else S;crop=src.crop(box);scale=min(size[0]/crop.width,size[1]/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);im=crop.resize((nw,nh),Image.Resampling.LANCZOS)
  # Uniform scale preserves complete volumes. Dark exterior is technicalalpha.
  rgba=quantize(im).convert('RGBA');arr=np.asarray(im);mask=np.full((nh,nw),255,dtype=np.uint8)
  if matte:
   dark=arr.max(2)<28;seen=set();todo=deque([(x,y)for x in range(nw)for y in [0,nh-1]]+[(x,y)for y in range(nh)for x in [0,nw-1]])
   while todo:
    x,y=todo.popleft()
    if(x,y)in seen or not(0<=x<nw and 0<=y<nh)or not dark[y,x]:continue
    seen.add((x,y));mask[y,x]=0;todo.extend([(x+1,y),(x-1,y),(x,y+1),(x,y-1)])
  rgba.putalpha(Image.fromarray(mask));canvas=Image.new('RGBA',tuple(size));canvas.alpha_composite(rgba,((size[0]-nw)//2,(size[1]-nh)//2));mods[name]=canvas;records.append({'id':name,'source':str((ROOT/source/'source'/('whole-v1.png'if source=='6A'else'whole-v3-open-hardware.png')).relative_to(P.parent)),'crop':box,'size':size,'uniformScale':scale,'repeat_axis':axis,'alpha':'dark exterior connected to boundary only'if matte else'none'})
 module('floor',[160,385,288,449],[32,16],'xy')
 module('water',[208,644,272,668],[16,8],'xy')
 module('bank-front',[208,520,240,648],[8,32],'x')
 module('bank-side',[20,324,84,388],[16,16],'y')
 module('wall-cap',[1284,76,1412,108],[32,8],'x')
 module('brick',[208,552,240,584],[8,8],'xy')
 module('corner',[16,488,96,656],[16,32],'none',matte=True)
 if key=='6A':
  module('entrance',[48,12,400,336],[96,88],matte=True)
  module('pump',[1112,204,1580,584],[112,96],matte=False)
  module('arrival',[1812,18,2154,450],[96,120],matte=True)
 else:
  module('pump',[1000,240,1300,480],[80,64],source='6B',matte=False)
  module('arrival',[1872,100,2160,390],[80,80],source='6B',matte=True)
  module('pressure',[550,184,804,416],[64,64],source='6B',matte=False)
 out=Image.new('RGBA',(W,H),(*RGB[2],255));placements=[]
 def fill(name,rect):
  x,y,w,h=rect;im=mods[name];pw,ph=im.size
  for yy in range(y,y+h,ph):
   for xx in range(x,x+w,pw):out.alpha_composite(im.crop((0,0,min(pw,x+w-xx),min(ph,y+h-yy))),(xx,yy))
  placements.append({'module':name,'rect':list(rect)})
 def place(name,x,y,mirror=False):
  im=ImageOps.mirror(mods[name])if mirror else mods[name];out.alpha_composite(im,(x,y));placements.append({'module':name,'position':[x,y],'mirror':mirror})
 def volume(rect,water=False):
  x,y,w,h=rect;fill('water'if water else'brick',rect)
  fill('wall-cap',(x,y,w,8));fill('bank-front',(x,y+h-32,w,32));fill('bank-side',(x,y+8,16,max(0,h-40)));fill('bank-side',(x+w-16,y+8,16,max(0,h-40)))
  place('corner',x,y+h-32);place('corner',x+w-16,y+h-32,True)
 fill('water',(0,0,W,H));fill('floor',(24,80,W-48,216))
 # Continuous outer architecture, then contiguous intrusions deform the floor.
 volume((0,24,W,56));volume((0,296,W,24));fill('bank-side',(0,80,24,216));fill('bank-side',(W-24,80,24,216))
 for x,y,w,h,vertical in d['solids']:
  if w<=32 and key=='6B':continue
  volume((x,y,w,h),not vertical)
 if key=='6A':
  place('entrance',40,24);place('pump',1344,176);place('arrival',2936,24)
  added=[[40,24,96,88,True],[2936,24,96,120,True]]
 else:
  place('pump',1416,208);place('arrival',2960,24);added=[[2960,24,80,80,True]]
  for gx,gy,gw,gh in d['gates']:
   volume((gx+24,24,32,gy),False);volume((gx-8,gy+56,32,H-gy-56),False)
   place('pressure',gx-96,max(24,gy-88))
 d['solids']+=added
 native=quantize(out.convert('RGB'));a=np.array(native);cells=a.reshape(H//8,8,W//8,8).transpose(0,2,1,3).reshape(-1,64);unique,inverse=np.unique(cells,axis=0,return_inverse=True)
 tiles=b''.join(bytes((int(r[i])<<4)|int(r[i+1])for i in range(0,64,2))for r in unique);maps=struct.pack('>'+str(len(inverse))+'H',*map(int,inverse));pal=struct.pack('>16H',*[(r<<1)|(g<<5)|(b<<9)for r,g,b in COLORS])
 d.update(phase=key,sourcePaths=[str(P/'source'/('whole-v1.png'if key=='6A'else'whole-v3-open-hardware.png'))],modules=records,placements=placements,memory={'scene_tiles':len(unique),'objective_tiles':256 if key=='6B'else 0,'total_tiles':len(unique)+(256 if key=='6B'else 0),'budget':640,'exact_pattern_replacements':0},native={'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin','image':'complete-native.png'},start=[40,192],status='native_candidate_pending_visual_review')
 files={'native/tiles.bin':tiles,'native/map.bin':maps,'native/palette.bin':pal,'manifest.json':(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()}
 if write:
  for f,data in files.items():(P/f).parent.mkdir(parents=True,exist_ok=True);(P/f).write_bytes(data)
  native.convert('RGB').save(P/'complete-native.png');native.save(P/'complete-indexed.png');(P/'modules').mkdir(exist_ok=True)
  for name,im in mods.items():im.save(P/'modules'/f'{name}.png')
  closed=native.convert('RGBA');game=ROOT.parents[3]
  if key=='6B':
   for gx,gy,gw,gh in d['gates']:closed.alpha_composite(Image.open(game/'art/objective-sprites-v1/frames/gate-0.png').convert('RGBA'),(gx-16,gy))
   for vx,vy in d['valves']:closed.alpha_composite(Image.open(game/'art/objective-sprites-v1/frames/valve-0.png').convert('RGBA'),(vx-16,vy-24))
  closed.convert('RGB').save(P/'complete-objectives.png')
 return files,d
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',default='6A',choices=['6A','6B']);args=p.parse_args();files,d=render(args.phase);print(json.dumps(d['memory']))
