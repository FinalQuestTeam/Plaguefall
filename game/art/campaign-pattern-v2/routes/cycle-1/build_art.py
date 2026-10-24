"""Image-first route backgrounds: whole architecture, axis materials, exact4bpp."""
from pathlib import Path
from collections import Counter,deque
import json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'cycle-1/source'
OUT=HERE/'cycle-1'
W,H=3072,320
SEWER=[(0,0,0),(1,1,1),(1,2,3),(2,3,4),(2,4,4),(3,4,4),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(3,2,1),(4,3,1),(5,4,2),(7,6,3),(1,2,1),(2,2,2)]
PORT=[(0,0,0),(1,1,1),(1,2,3),(2,3,4),(3,4,5),(2,2,2),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(4,2,1),(6,3,1),(7,5,2),(7,7,6),(2,3,1),(4,1,1)]
# Each range is an intact building/object or the complete transverse height of
# a material intended to repeat only on its stated axis. No8x8 substitute art.
CONFIG={
'06a':{
 'ceiling':('06a',[100,0,196,24],[32,8],'xy'),
 'wall':('06a',[690,24,864,300],[32,96],'x'),
 'entrance':('06a',[24,24,500,340],[112,96],'none'),
 'inspection':('06a',[1020,126,1240,312],[72,64],'none'),
 'arrival':('06a',[1750,24,2150,340],[112,96],'none'),
 'floor':('06a',[980,346,1250,480],[64,32],'xy'),
 'lower':('06a',[530,510,765,724],[32,32],'x'),
 'side-left':('06a',[0,330,70,430],[24,32],'y'),
 'side-right':('06a',[2102,330,2172,430],[24,32],'y'),
 'corner-upper-left':('06a',[0,24,70,320],[24,96],'none'),
 'corner-upper-right':('06a',[2102,24,2172,320],[24,96],'none'),
 'corner-lower-left':('06a',[0,480,80,724],[24,32],'none'),
 'corner-lower-right':('06a',[2092,480,2172,724],[24,32],'none'),
 'cabinet':('06a',[526,194,666,323],[40,32],'object')},
'06b':{
 'ceiling':('06a',[100,0,196,24],[32,8],'xy'),
 'wall':('06b',[766,80,1030,210],[48,64],'x'),
 'pressure-house':('06b',[480,0,766,365],[64,96],'none'),
 'arrival':('06b',[1970,58,2140,290],[64,80],'none'),
 'floor':('06a',[980,346,1250,480],[64,32],'xy'),
 'lower':('06a',[530,510,765,724],[32,32],'x'),
 'side-left':('06a',[0,330,70,430],[24,32],'y'),
 'side-right':('06a',[2102,330,2172,430],[24,32],'y'),
 'corner-upper-left':('06a',[0,24,70,320],[24,64],'none'),
 'corner-upper-right':('06a',[2102,24,2172,320],[24,64],'none'),
 'corner-lower-left':('06a',[0,480,80,724],[24,32],'none'),
 'corner-lower-right':('06a',[2092,480,2172,724],[24,32],'none'),
 'partition':('06b',[20,300,64,400],[16,32],'y'),
 'partition-end':('06b',[536,480,576,642],[16,40],'none'),
 'pipe':('06a',[590,129,591,132],[1,3],'pipe'),
 'cabinet':('06a',[526,194,666,323],[32,24],'object')},
'12':{
 'ceiling':('12',[550,0,670,40],[32,16],'xy'),
 'wall':('12',[1250,105,1510,300],[64,64],'x'),
 'entrance':('12',[68,55,526,314],[112,88],'none'),
 'maintenance':('12',[970,102,1250,310],[80,64],'none'),
 'arrival':('12',[1690,40,2120,315],[112,96],'none'),
 'floor':('12',[810,350,1066,606],[64,64],'xy'),
 'lower':('12',[435,575,665,710],[48,32],'x'),
 'side-left':('12',[0,342,50,510],[16,48],'y'),
 'side-right':('12',[2122,342,2172,510],[16,48],'y'),
 'corner-upper-left':('12',[0,140,90,340],[24,64],'none'),
 'corner-upper-right':('12',[2100,140,2172,340],[24,64],'none'),
 'corner-lower-left':('12',[0,568,78,724],[24,32],'none'),
 'corner-lower-right':('12',[2094,568,2172,724],[24,32],'none'),
 'cargo':('12',[1560,250,1656,306],[40,24],'object')}
}
BOUNDS=[24,192,3047,287]
GATES=[[1008,208,32,64],[2032,208,32,64]]
VALVES=[[968,224],[1992,224]]
# Complete cabinets form edge islands. The escort travels around these intact
# silhouettes, leaving at least24px to the lower wall and32px between events.
SOLIDS={
'06a':[[448,192,40,32],[1472,256,40,32],[2448,192,40,32]],
'06b':[[448,256,32,24],[1504,192,32,24],[2528,256,32,24]]+
 [[x+24,192,16,48] for x,_,_,_ in GATES]+[[x-8,256,24,32] for x,_,_,_ in GATES],
'12':[[576,192,40,24],[1568,264,40,24],[2464,192,40,24]]
}
POINTS={
'06a':[[56,216],[280,216],[416,232],[568,232],[1008,216],[1304,216],[1584,216],[1760,216],[2056,216],[2320,216],[2408,232],[2544,232],[2800,216],[3016,208]],
'06b':[[56,216],[280,216],[552,216],[744,216],[944,232],[960,248],[1048,248],[1080,232],[1304,216],[1456,240],[1584,240],[1760,216],[1968,232],[1984,248],[2072,248],[2104,232],[2320,216],[2640,216],[3016,208]],
'12':[[56,216],[328,216],[544,232],[680,232],[1104,216],[1304,216],[1576,232],[1808,216],[2072,216],[2304,216],[2424,232],[2560,232],[2824,216],[3016,208]]
}
PAUSES={'06a':[3,7],'06b':[4,12],'12':[3,7,10]}

def indexed(rgb,palette):
 a=np.asarray(rgb.convert('RGB'),dtype=np.int32);p=np.asarray(palette,dtype=np.int32)
 idx=((a[:,:,None]-p[None,None])**2).sum(3)[:,:,1:].argmin(2).astype(np.uint8)+1
 out=Image.fromarray(idx,'P');out.putpalette(sum(map(list,palette),[])+[0]*720);return out

def object_mask(rgb):
 # The cabinet/cargo bounds are already full silhouette rectangles. Remove
 # only the wall/floor background connected to each outside edge. Preserve
 # every enclosed grid opening and the authored dark contact shadow.
 a=np.array(rgb);h,w=a.shape;bg=Counter(a.ravel()).most_common(1)[0][0];outside=set();todo=[(x,y) for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)]
 while todo:
  x,y=todo.pop()
  if (x,y) in outside or a[y,x]!=bg:continue
  outside.add((x,y))
  todo.extend((xx,yy) for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if 0<=xx<w and 0<=yy<h)
 return Image.fromarray(np.array([[0 if (x,y) in outside else 255 for x in range(w)]for y in range(h)],dtype=np.uint8))

def render(key):
 dest=OUT/key;dest.mkdir(parents=True,exist_ok=True);(dest/'modules').mkdir(exist_ok=True)
 p333=SEWER if key!='12' else PORT;palette=[tuple(v*255//7 for v in c) for c in p333];words=[(r<<1)|(g<<5)|(b<<9) for r,g,b in p333]
 modules={};records=[];placements=[]
 for name,(src,box,size,axis) in CONFIG[key].items():
  full=Image.open(SOURCE/f'{src}-whole.png').convert('RGB');rgb=full.crop(box).resize(size,Image.Resampling.NEAREST if axis=='pipe' else Image.Resampling.LANCZOS);im=indexed(rgb,palette)
  mask=object_mask(im) if axis=='object' else None
  modules[name]=(im,mask,axis);rgba=im.convert('RGBA')
  if mask:rgba.putalpha(mask)
  rgba.save(dest/'modules'/f'{name}.png');records.append(dict(id=name,source=f'../source/{src}-whole.png',source_rect=box,native_size=size,repeat_axis=axis,extraction='complete silhouette' if axis=='object' else 'complete structure or full material cross-section'))
 out=Image.new('P',(W,H));out.putpalette(sum(map(list,palette),[])+[0]*720)
 def place(name,x,y):
  im,mask,_=modules[name];out.paste(im,(x,y),mask);placements.append(dict(module=name,position=[x,y],size=list(im.size)))
 def fill(name,x,y,w,h):
  im,mask,axis=modules[name];pw,ph=im.size
  for yy in range(y,y+h,ph):
   for xx in range(x,x+w,pw):out.paste(im.crop((0,0,min(pw,x+w-xx),min(ph,y+h-yy))),(xx,yy))
  placements.append(dict(module=name,position=[x,y],area=[w,h],repeat_axis=axis))
 fill('floor',0,0,W,H);fill('ceiling',0,0,W,128)
 wallh=modules['wall'][0].height;fill('wall',24,192-wallh,W-48,wallh)
 if key=='06a':
  place('entrance',24,96);place('inspection',1432,128);place('arrival',2936,96)
 elif key=='06b':
  for gx,_,_,_ in GATES:place('pressure-house',gx-40,96)
  place('arrival',2984,112)
 else:
  place('entrance',24,104);place('maintenance',1408,128);place('arrival',2936,96)
 # Material strips only repeat on their natural axis. Both extreme corners
 # are intact source returns, never leftover portions of the last repeat.
 fill('side-left',0,192,24,96);fill('side-right',W-24,192,24,96)
 fill('lower',24,288,W-48,32)
 for n,x in [('corner-upper-left',0),('corner-upper-right',W-24)]:place(n,x,192-modules[n][0].height)
 place('corner-lower-left',0,288);place('corner-lower-right',W-24,288)
 if key=='06b':
  for gx,gy,gw,gh in GATES:
   fill('partition',gx+24,192,16,24);place('partition-end',gx+24,200)
   fill('partition',gx-8,256,24,32)
  # This complete3px authored pipe stripe is material, not a new icon. It
  # descends from the pressure-house pipework, with an elbow into the wheel.
  pipe=modules['pipe'][0];vertical=pipe.rotate(90,expand=True)
  for vx,vy in VALVES:
   for yy in range(176,224):out.paste(vertical,(vx-24,yy))
   for xx in range(vx-24,vx-12):out.paste(pipe,(xx,221))
 for i,(x,y,w,h) in enumerate(SOLIDS[key][:3]):place('cargo' if key=='12' else 'cabinet',x,y)
 cells=np.asarray(out).reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64);unique,inverse=np.unique(cells,axis=0,return_inverse=True)
 tiles=[bytes((int(r[i])<<4)|int(r[i+1]) for i in range(0,64,2)) for r in unique];m=list(map(int,inverse));native=out.convert('RGB');native.save(dest/'complete-native.png');out.save(dest/'complete-indexed.png')
 layout=native.copy();d=ImageDraw.Draw(layout);d.rectangle((24,192,3047,287),outline='lime')
 for x,y,w,h in SOLIDS[key]:d.rectangle((x,y,x+w-1,y+h-1),outline='red',width=1)
 d.line([tuple(x)for x in POINTS[key]],fill='cyan',width=1);layout.save(dest/'layout.png')
 # Add every current hardware pose without touching the shared sprite bank.
 game=HERE.parents[2]
 for state,frame in [('closed',0),('open',5)]:
  complete=native.convert('RGBA')
  if key=='06b':
   for gx,gy,gw,gh in GATES:complete.alpha_composite(Image.open(game/f'art/objective-sprites-v1/frames/gate-{frame}.png').convert('RGBA'),(gx-16,gy))
   for vx,vy in VALVES:complete.alpha_composite(Image.open(game/f'art/objective-sprites-v1/frames/valve-{3 if frame else 0}.png').convert('RGBA'),(vx-16,vy-24))
  complete.convert('RGB').save(dest/f'complete-{state}-objectives.png')
 manifest=dict(phase=key,size=[W,H],bounds=BOUNDS,start=[48,208],exit=[2992,184,48,48],solids=SOLIDS[key],points=POINTS[key],pauses=PAUSES[key],modules=records,placements=placements,memory=dict(scene_tiles=len(tiles),objective_tiles=256 if key=='06b' else 0,total_tiles=len(tiles)+(256 if key=='06b' else 0),budget=640,lossy_pattern_replacements=0),source_stage='whole scene created and inspected before extraction',status='native_candidate_not_approved')
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 # Saved native cameras are static composition studies, not emulator proofs.
 for label,x in [('entrada',0),('meio',1360),('saida',2752)]:
  for cy in [48,72,96]:
   frame=native.crop((x,cy,x+320,cy+224));frame.resize((640,448),Image.Resampling.NEAREST).save(dest/f'camera-{label}-y{cy}.png')
 return tiles,m,words,manifest
if __name__=='__main__':
 for key in CONFIG:
  tiles,m,p,manifest=render(key);print(key,manifest['memory'])
