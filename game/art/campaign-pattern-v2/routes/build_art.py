"""Image-first route backgrounds: whole architecture, axis materials, exact4bpp."""
from pathlib import Path
from collections import Counter,deque
import json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'cycle-1/source'
OUT=HERE/'cycle-2'
W,H=3072,272
YSHIFT=48
SEWER=[(0,0,0),(1,1,1),(1,2,3),(2,3,4),(2,4,4),(3,4,4),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(3,2,1),(4,3,1),(5,4,2),(7,6,3),(1,2,1),(2,2,2)]
PORT=[(0,0,0),(1,1,1),(1,2,3),(2,3,4),(3,4,5),(2,2,2),(3,3,2),(4,4,3),(5,5,4),(6,6,5),(4,2,1),(6,3,1),(7,5,2),(7,7,6),(2,3,1),(4,1,1)]
# Each range is an intact building/object or the complete transverse height of
# a material intended to repeat only on its stated axis. No8x8 substitute art.
CONFIG={
'06a':{
 'ceiling':('06a',[710,160,838,224],[32,16],'xy'),
 'wall':('06a',[690,24,864,300],[32,96],'x'),
 'entrance':('06a',[24,24,500,340],[128,88],'none'),
 'inspection':('06a',[1020,126,1240,312],[64,56],'none'),
 'arrival':('06a',[1750,24,2150,340],[112,88],'none'),
 'floor':('06a',[980,346,1114,480],[32,32],'xy'),
 'lower':('06a',[530,510,765,724],[32,32],'x'),
 'side-left':('06a',[0,330,70,430],[24,32],'y'),
 'side-right':('06a',[2102,330,2172,430],[24,32],'y'),
 'corner-upper-left':('06a',[0,24,70,320],[24,96],'none'),
 'corner-upper-right':('06a',[2102,24,2172,320],[24,96],'none'),
 'corner-lower-left':('06a',[0,480,80,724],[24,32],'none'),
 'corner-lower-right':('06a',[2092,480,2172,724],[24,32],'none'),
 'cabinet':('06a',[510,180,690,330],[40,32],'object')},
'06b':{
 'ceiling':('06a',[710,160,838,224],[32,16],'xy'),
 'wall':('06a',[690,24,864,300],[32,96],'x'),
 'pressure-house':('06b',[480,0,766,365],[64,80],'none'),
 'arrival':('06b',[1970,58,2140,290],[64,88],'none'),
 'floor':('06a',[980,346,1114,480],[32,32],'xy'),
 'lower':('06a',[530,510,648,724],[16,32],'x'),
 'side-left':('06a',[0,330,70,430],[24,32],'y'),
 'side-right':('06a',[2102,330,2172,430],[24,32],'y'),
 'corner-upper-left':('06a',[0,24,70,320],[24,64],'none'),
 'corner-upper-right':('06a',[2102,24,2172,320],[24,64],'none'),
 'corner-lower-left':('06a',[0,480,80,724],[24,32],'none'),
 'corner-lower-right':('06a',[2092,480,2172,724],[24,32],'none'),
 'partition':('06b',[20,300,64,400],[16,32],'y'),
 'partition-end':('06b',[516,480,592,650],[16,40],'object'),
 'pipe':('06a',[590,129,591,132],[1,3],'pipe'),
 'cabinet':('06a',[510,180,690,330],[32,24],'object')},
'12':{
 'ceiling':('12',[0,0,96,40],[32,16],'xy'),
 'wall':('12',[1264,105,1544,310],[72,56],'x'),
 'entrance':('12',[68,55,526,314],[128,72],'none'),
 'maintenance':('12',[978,105,1264,314],[96,72],'none'),
 'arrival':('12',[1664,34,2144,315],[128,72],'none'),
 'floor':('12',[810,330,938,546],[32,48],'xy'),
 'lower':('12',[435,575,665,710],[48,32],'x'),
 'side-left':('12',[0,342,50,510],[16,48],'y'),
 'side-right':('12',[2122,342,2172,510],[16,48],'y'),
 'corner-upper-left':('12',[0,140,90,340],[24,64],'none'),
 'corner-upper-right':('12',[2100,140,2172,340],[24,64],'none'),
 'corner-lower-left':('12',[0,568,78,724],[24,32],'none'),
 'corner-lower-right':('12',[2094,568,2172,724],[24,32],'none'),
 'cargo':('12',[1550,238,1670,314],[40,24],'object')}
}
BOUNDS=[24,192,3047,287]
GATES=[[1008,208,32,64],[2032,208,32,64]]
VALVES=[[968,224],[1992,224]]
# Complete cabinets form edge islands. The escort travels around these intact
# silhouettes, leaving at least24px to the lower wall and32px between events.
SOLIDS={
'06a':[[448,192,40,32],[1472,256,40,32],[2448,192,40,32]],
'06b':[[448,264,32,24],[1504,192,32,24],[2528,264,32,24]]+
 [[x+24,192,16,40] for x,_,_,_ in GATES]+[[x-8,264,16,24] for x,_,_,_ in GATES],
'12':[[576,192,40,24],[1568,264,40,24],[2464,192,40,24]]
}
POINTS={
'06a':[[56,216],[280,216],[416,240],[568,240],[1008,216],[1304,216],[1584,216],[1760,216],[2056,216],[2320,216],[2408,240],[2544,240],[2800,216],[3016,208]],
'06b':[[56,216],[280,216],[552,216],[744,216],[944,232],[960,248],[1048,248],[1080,232],[1304,216],[1456,240],[1584,240],[1760,216],[1968,232],[1984,248],[2072,248],[2104,232],[2320,216],[2640,216],[3016,208]],
'12':[[56,216],[328,216],[544,232],[680,232],[1104,216],[1304,216],[1576,232],[1808,216],[2072,216],[2304,216],[2424,232],[2560,232],[2824,216],[3016,208]]
}
PAUSES={'06a':[3,7],'06b':[4,12],'12':[3,7,10]}

def indexed(rgb,palette):
 a=np.asarray(rgb.convert('RGB'),dtype=np.int32);p=np.asarray(palette,dtype=np.int32)
 idx=((a[:,:,None]-p[None,None])**2).sum(3)[:,:,1:].argmin(2).astype(np.uint8)+1
 out=Image.fromarray(idx,'P');out.putpalette(sum(map(list,palette),[])+[0]*720);return out

def object_mask(rgb,name):
 # The cabinet/cargo bounds are already full silhouette rectangles. Remove
 # only the wall/floor background connected to each outside edge. Preserve
 # every enclosed grid opening and the authored dark contact shadow.
 # Matte follows the complete authored silhouette and its contact shadow;
 # it never draws replacement object pixels or deletes internal dark grilles.
 polygons={'cabinet':([(22,13),(146,13),(155,31),(153,118),(165,131),(164,143),(10,143),(7,130),(19,119),(19,45),(17,44)],(180,150)),
 'cargo':([(7,13),(107,13),(116,21),(116,61),(109,67),(6,67),(3,60),(3,26)],(120,76)),
 'partition-end':([(17,3),(57,3),(60,36),(57,154),(64,164),(7,164),(14,151),(14,35)],(76,170))}
 points,size=polygons[name];m=Image.new('L',size);ImageDraw.Draw(m).polygon(points,fill=255)
 return m.resize(rgb.size,Image.Resampling.NEAREST)

def render(key):
 dest=OUT/key;dest.mkdir(parents=True,exist_ok=True);(dest/'modules').mkdir(exist_ok=True)
 p333=SEWER if key!='12' else PORT;palette=[tuple(v*255//7 for v in c) for c in p333];words=[(r<<1)|(g<<5)|(b<<9) for r,g,b in p333]
 modules={};records=[];placements=[]
 for name,(src,box,size,axis) in CONFIG[key].items():
  full=Image.open(SOURCE/f'{src}-whole.png').convert('RGB');rgb=full.crop(box).resize(size,Image.Resampling.NEAREST if axis=='pipe' else Image.Resampling.LANCZOS);im=indexed(rgb,palette)
  mask=object_mask(im,name) if axis=='object' else None
  if name=='partition-end':
   bbox=mask.getbbox();rgba=im.convert('RGBA');rgba.putalpha(mask);cut=rgba.crop(bbox);ratio=min(size[0]/cut.width,size[1]/cut.height);cut=cut.resize((round(cut.width*ratio),round(cut.height*ratio)),Image.Resampling.NEAREST);pad=Image.new('RGBA',tuple(size));pad.alpha_composite(cut,((size[0]-cut.width)//2,size[1]-cut.height));im=indexed(pad.convert('RGB'),palette);mask=pad.getchannel('A')
  modules[name]=(im,mask,axis);rgba=im.convert('RGBA')
  if mask:rgba.putalpha(mask)
  rgba.save(dest/'modules'/f'{name}.png');records.append(dict(id=name,source=f'../source/{src}-whole.png',source_rect=box,native_size=size,repeat_axis=axis,extraction='complete silhouette' if axis=='object' else 'complete structure or full material cross-section'))
 out=Image.new('P',(W,H+YSHIFT));out.putpalette(sum(map(list,palette),[])+[0]*720)
 def place(name,x,y):
  im,mask,_=modules[name];out.paste(im,(x,y),mask);placements.append(dict(module=name,position=[x,y],size=list(im.size)))
 def fill(name,x,y,w,h):
  im,mask,axis=modules[name];pw,ph=im.size
  for yy in range(y,y+h,ph):
   for xx in range(x,x+w,pw):out.paste(im.crop((0,0,min(pw,x+w-xx),min(ph,y+h-yy))),(xx,yy))
  placements.append(dict(module=name,position=[x,y],area=[w,h],repeat_axis=axis))
 fill('floor',0,0,W,H+YSHIFT);fill('ceiling',0,0,W,192)
 wallh=modules['wall'][0].height;fill('wall',24,192-wallh,W-48,wallh)
 if key=='06a':
  place('entrance',24,192-modules['entrance'][0].height);place('inspection',1432,192-modules['inspection'][0].height);place('arrival',W-24-modules['arrival'][0].width,192-modules['arrival'][0].height)
 elif key=='06b':
  for gx,_,_,_ in GATES:place('pressure-house',gx-64,192-modules['pressure-house'][0].height)
  place('arrival',2984,192-modules['arrival'][0].height)
 else:
  place('entrance',24,192-modules['entrance'][0].height);place('maintenance',1408,192-modules['maintenance'][0].height);place('arrival',W-24-modules['arrival'][0].width,192-modules['arrival'][0].height)
 # Material strips only repeat on their natural axis. Both extreme corners
 # are intact source returns, never leftover portions of the last repeat.
 fill('side-left',0,192,24,96);fill('side-right',W-24,192,24,96)
 fill('lower',24,288,W-48,32)
 for n,x in [('corner-upper-left',0),('corner-upper-right',W-24)]:place(n,x,192-modules[n][0].height)
 place('corner-lower-left',0,288);place('corner-lower-right',W-24,288)
 if key=='06b':
  for gx,gy,gw,gh in GATES:
   place('partition-end',gx+24,192)
   place('partition-end',gx-8,248)
  # This complete3px authored pipe stripe is material, not a new icon. It
  # descends from the pressure-house pipework, with an elbow into the wheel.
  pipe=modules['pipe'][0];vertical=pipe.rotate(90,expand=True)
  for vx,vy in VALVES:
   for yy in range(160,224):out.paste(vertical,(vx-20,yy))
   for xx in range(vx-20,vx-12):out.paste(pipe,(xx,221))
 for i,(x,y,w,h) in enumerate(SOLIDS[key][:3]):place('cargo' if key=='12' else 'cabinet',x,y)
 out=out.crop((0,YSHIFT,W,H+YSHIFT))
 cells=np.asarray(out).reshape(H//8,8,384,8).transpose(0,2,1,3).reshape(-1,64);unique,inverse=np.unique(cells,axis=0,return_inverse=True)
 tiles=[bytes((int(r[i])<<4)|int(r[i+1]) for i in range(0,64,2)) for r in unique];m=list(map(int,inverse));native=out.convert('RGB');native.save(dest/'complete-native.png');out.save(dest/'complete-indexed.png')
 layout=native.copy();d=ImageDraw.Draw(layout);d.rectangle((24,144,3047,239),outline='lime')
 for x,y,w,h in SOLIDS[key]:d.rectangle((x,y-YSHIFT,x+w-1,y+h-YSHIFT-1),outline='red',width=1)
 d.line([(x,y-YSHIFT)for x,y in POINTS[key]],fill='cyan',width=1);layout.save(dest/'layout.png')
 # Add every current hardware pose without touching the shared sprite bank.
 game=HERE.parents[2]
 for state,frame in [('closed',0),('collapse',5),('open',None)]:
  complete=native.convert('RGBA')
  if key=='06b':
   for gx,gy,gw,gh in GATES:
    if frame is None:continue
    complete.alpha_composite(Image.open(game/f'art/objective-sprites-v1/frames/gate-{frame}.png').convert('RGBA'),(gx-16,gy-YSHIFT))
   for vx,vy in VALVES:complete.alpha_composite(Image.open(game/f'art/objective-sprites-v1/frames/valve-{3 if frame else 0}.png').convert('RGBA'),(vx-16,vy-24-YSHIFT))
  complete.convert('RGB').save(dest/f'complete-{state}-objectives.png')
 manifest=dict(phase=key,size=[W,H],bounds=[24,144,3047,239],start=[48,160],exit=[2992,136,48,48],gates=[[x,y-YSHIFT,w,h]for x,y,w,h in GATES] if key=='06b' else [],valves=[[x,y-YSHIFT]for x,y in VALVES] if key=='06b' else [],solids=[[x,y-YSHIFT,w,h]for x,y,w,h in SOLIDS[key]],points=[[x,y-YSHIFT]for x,y in POINTS[key]],pauses=PAUSES[key],modules=records,placements=placements,memory=dict(scene_tiles=len(tiles),objective_tiles=256 if key=='06b' else 0,total_tiles=len(tiles)+(256 if key=='06b' else 0),budget=640,lossy_pattern_replacements=0),source_stage='whole scene created and inspected before extraction',status='native_candidate_not_approved')
 # Verify production actor footprint, every authored route segment and the
 # disconnected/connected states of both pressure doors before integration.
 bounds=manifest['bounds'];solids=manifest['solids'];points=manifest['points']
 def free(x,y,extra=()):
  return bounds[0]<=x and x+15<=bounds[2] and bounds[1]<=y and y+15<=bounds[3] and not any(x<rx+rw and x+16>rx and y<ry+rh and y+16>ry for rx,ry,rw,rh in list(solids)+list(extra))
 import math
 swept=0
 for (ax,ay),(bx,by) in zip(points,points[1:]):
  distance=math.hypot(bx-ax,by-ay)
  for tick in range(math.ceil(distance)+1):
   t=min(1,tick/max(1,distance));x=ax+(bx-ax)*t-8;y=ay+(by-ay)*t-8;assert free(x,y),(key,'route hits solid',x,y);swept+=1
 def connected(extra=()):
  todo=[tuple(manifest['start'])];seen=set()
  while todo:
   xy=todo.pop()
   if xy in seen or not free(*xy,extra):continue
   seen.add(xy);x,y=xy;todo.extend(((x-8,y),(x+8,y),(x,y-8),(x,y+8)))
  return seen
 visited=connected();goal=(points[-1][0]-8,points[-1][1]-8);assert goal in visited
 manifest['geometry']=dict(footprint=[16,16],swept16pxSamples=swept,connectedPositions=len(visited),arrivalConnected=True,physicalGateOpeningPx=32 if key=='06b' else None)
 if key=='06b':
  assert goal not in connected(manifest['gates']);assert goal not in connected(manifest['gates'][1:]);manifest['geometry'].update(closedGatesDisconnect=True,firstGateOnlyDoesNotAllowCompletion=True)
 manifest['states']=[dict(name='closed',file='complete-closed-objectives.png'),dict(name='collapse',file='complete-collapse-objectives.png',gateFrame=5,collision='closed until0.8s'),dict(name='open',file='complete-open-objectives.png',gateSpriteVisible=False,clearAfterSeconds=.8)] if key=='06b' else [dict(name='default',file='complete-native.png')]
 manifest['placements']=[{**v,'position':[v['position'][0],v['position'][1]-YSHIFT]} for v in placements]
 manifest['sourceInputs']={k:hashlib.sha256((SOURCE/f'{k}-whole.png').read_bytes()).hexdigest()for k in sorted(set(v[0]for v in CONFIG[key].values()))}
 manifest['memory'].update(graphics_bytes=manifest['memory']['total_tiles']*32,map_bytes=len(m)*2,palette_bytes=32,free_tiles=640-manifest['memory']['total_tiles'],all_objective_frames_included=True)
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 # Saved native cameras are static composition studies, not emulator proofs.
 for label,x in [('entrada',0),('meio',1360),('saida',2752)]:
  for cy in [0,24,48]:
   frame=native.crop((x,cy,x+320,cy+224));frame.resize((640,448),Image.Resampling.NEAREST).save(dest/f'camera-{label}-y{cy}.png')
 return tiles,m,words,manifest
if __name__=='__main__':
 for key in CONFIG:
  tiles,m,p,manifest=render(key);print(key,manifest['memory'])
