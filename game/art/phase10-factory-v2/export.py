"""Whole factory image -> complete native modules, scattered nests and exact cache."""
from pathlib import Path
import argparse,json,io,sys,struct,math,hashlib
from PIL import Image,ImageDraw
import numpy as np
G=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent
sys.path.insert(0,str(G/'tools'));from campaign_geometry import validate,free,path,route
args=argparse.ArgumentParser();args.add_argument('--check',action='store_true');args=args.parse_args()
def emit(p,b):
 if args.check:assert p.exists() and p.read_bytes()==b,('stale phase10 export',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
def js(p,v):emit(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
def ca(name,typ,vals):
 return 'static const '+typ+' '+name+'[] __attribute__((aligned(32)))={\n'+''.join(','.join('0x%08XUL'%v if typ=='u32' else str(v) for v in vals[i:i+12])+',\n' for i in range(0,len(vals),12))+'};\n'
# Retain industrial hues and literal black index0; no extra palette bank.
pal=[(0,0,0),(36,36,36),(36,72,109),(72,72,72),(72,109,145),(145,145,109),(145,145,145),(218,218,182),(109,36,0),(145,72,36),(182,109,36),(218,145,0),(36,72,72),(109,109,109),(109,145,145),(72,109,72)]
colors=np.array(pal,dtype=np.int32);palette=sum(map(list,pal),[])+[0]*720
source=Image.open(A/'source/factory-whole.png').convert('RGB').resize((768,544),Image.Resampling.NEAREST)
def indexed(im):
 a=np.array(im.convert('RGB'),dtype=np.int32);out=Image.fromarray(((a[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'));out.putpalette(palette);return out
def canvas(size):
 out=Image.new('P',size);out.putpalette(palette);return out
def module(name,box,size):
 im=indexed(source.crop(box).resize(size,Image.Resampling.NEAREST));png(A/'modules'/f'{name}.png',im);return im
def repeat(out,im,box):
 x,y,w,h=box
 for yy in range(y,y+h,im.height):
  for xx in range(x,x+w,im.width):out.paste(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
scene=canvas((768,544))
floor=module('quiet-concrete',(64,304,96,336),(32,32));repeat(scene,floor,(0,0,768,544))
# Coherent repeated128px service bays, material texture at native1px density.
wall=module('service-wall',(488,8,504,124),(16,128));repeat(scene,wall,(0,0,768,128))
for name,box,size,xy in [('door',(40,12,206,124),(96,96),(32,24)),('furnace',(300,0,488,128),(112,112),(320,16)),('tanks',(528,12,688,128),(96,96),(632,24))]:scene.paste(module(name,box,size),xy)
left=module('left-boundary',(0,136,32,232),(24,96));right=module('right-boundary',(736,136,768,232),(24,96));repeat(scene,left,(0,128,24,352));repeat(scene,right,(744,128,24,352))
lower=module('lower-boundary',(168,456,296,544),(128,64));repeat(scene,lower,(0,480,768,64))
scene.paste(module('corner-left',(0,416,48,544),(24,64)),(0,480));scene.paste(module('corner-right',(720,416,768,544),(24,64)),(744,480))
# Native props are whole assemblies. Edge flood-fill removes ONLY connected
# concrete around them, then retains the dominant complete assembly.
def prop(name,box,size,xy):
 rgb=source.crop(box).resize(size,Image.Resampling.NEAREST);a=np.array(rgb);q=indexed(rgb);w,h=size
 # Low-saturation warm concrete is exterior background. Blue steel, rust,
 # brick and near-black shadows remain attached to the object.
 seen=set();stack=[(x,y) for x in range(w) for y in (0,h-1)]+[(x,y) for y in range(h) for x in (0,w-1)]
 while stack:
  x,y=stack.pop()
  if not(0<=x<w and 0<=y<h) or (x,y) in seen:continue
  r,g,b=map(int,a[y,x]);floor=(max(r,g,b)-min(r,g,b)<43 and 67<r<200 and r>=b and g>=b-4)
  if not floor:continue
  seen.add((x,y));stack.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
 mask=Image.frombytes('L',size,bytes(0 if (x,y) in seen else 255 for y in range(h) for x in range(w)))
 rgba=q.convert('RGBA');rgba.putalpha(mask);png(A/'objects'/f'{name}.png',rgba);scene.paste(q,xy,mask)
 return [*xy,*size,True]
props=[('conveyor',(160,184,308,248),(112,48),(128,224)),('pump',(456,160,576,264),(80,80),(496,192)),('compressor',(292,292,408,376),(80,64),(304,320)),('crates',(584,292,672,384),(64,64),(600,352)),('barrels',(136,372,200,440),(64,56),(120,408)),('supplies',(464,384,544,448),(64,56),(456,416))]
solids=[prop(*p) for p in props]
eggs=[[96,192],[272,280],[440,168],[680,208],[368,304],[680,336],[200,352],[80,448],[416,424],[624,464]]
d=dict(size=[768,544],width=768,height=544,bounds=[24,128,743,479],start=[56,160],solids=solids,points=[],eggs=eggs)
d['geometry']=validate(d)
# Unobstructed shooting approaches per target; lines never cross a prop.
approaches=[]
for i,(x,y) in enumerate(eggs):
 assert free(d,x-8,y-8),('egg on solid',i,x,y)
 good=[]
 for ax in [x-72,x+56,x-48,x+40]:
  ay=y-8
  if not free(d,ax,ay,4):continue
  line=range(min(ax+8,x),max(ax+8,x)+1)
  if any(any(rx<=sx<rx+rw and ry<=y-16<ry+rh for rx,ry,rw,rh,*_ in solids) for sx in line):continue
  good.append([ax,ay]);path(d,d['start'],[ax,ay],4)
 assert good,('unshootable nest',i)
 approaches.append(good)
d['egg_approaches']=approaches
maxslots=0
for cy in range(321):
 for cx in range(0,449,8):maxslots=max(maxslots,sum(cx-24<=x<cx+344 and cy+8<=y<cy+272 for x,y in eggs))
assert maxslots<=7;d['maximum_requested_nest_slots']=maxslots
# Plain source IDs for the exact visible cache; all frames of nests stay resident.
lookup={};tiles=[];mp=[]
for y in range(0,544,8):
 for x in range(0,768,8):
  t=scene.crop((x,y,x+8,y+8)).tobytes()
  if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
  mp.append(lookup[t])
a=np.array(mp).reshape(68,96);maximum=0
for y in range(3,44):
 for x in range(57):maximum=max(maximum,len(np.unique(a[y:y+26,x:x+41])))
assert maximum<=490,('cache does not fit with nests',maximum)
cache=min(490,math.ceil((maximum+8)/16)*16);assert cache>=maximum and cache+150<=640
raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles);words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in pal]
for name,data in [('tiles',raw),('map',struct.pack('>'+str(len(mp))+'H',*mp)),('palette',struct.pack('>16H',*words))]:emit(A/'native'/f'{name}.bin',data)
png(A/'complete-native.png',scene)
code='// Generated phase10: whole factory modules and scattered persistent nests.\n'+ca('phase10Tiles','u32',struct.unpack('>'+str(len(raw)//4)+'I',raw))+ca('phase10Palette','u16',words)+ca('phase10Map','u16',mp)
code+=f'static const ArenaStream phase10Stream={{{len(tiles)}}};\nstatic const ArenaScene phase10Scene={{.tiles=phase10Tiles,.map=phase10Map,.palette=phase10Palette,.tileCount={cache},.rows=68,.cols=96,.cameraPlayerY=184,.stream=&phase10Stream,.streamOverlay=TRUE,.cameraSouthStart=352}};\n'
code+='static const ArenaRect phase10Solids[]={'+','.join('{'+','.join(str(int(v)) for v in r)+'}' for r in solids)+'};\nconst ArenaDef CF_FACTORY_NEST={768,544,24,128,743,479,56,160,phase10Solids,6,&phase10Scene};\n';emit(G/'src/levels/campaign_factory_phase10.inc',code.encode())
header='// Generated phase10 anchors.\n#ifndef PHASE10_LAYOUT_H\n#define PHASE10_LAYOUT_H\nstatic const s16 PHASE10_EGGS[10][2]={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in eggs)+'};\n#endif\n';emit(G/'src/levels/phase10_layout.h',header.encode())
complete=scene.convert('RGBA');art=Image.open(G/'art/objective-sprites-v1/frames/nest-0.png').convert('RGBA')
for x,y in eggs:complete.alpha_composite(art,((x-24)//8*8,(y-40)//8*8))
png(A/'complete-with-eggs.png',complete)
layout=complete.copy();dr=ImageDraw.Draw(layout)
for x,y,w,h,*_ in solids:dr.rectangle((x,y,x+w-1,y+h-1),outline='#ff735d',width=1)
for i,(x,y) in enumerate(eggs):dr.text((x-8,y+12),str(i+1),fill='#ffffff')
png(A/'layout.png',layout)
d['memory']=dict(source_tiles=len(tiles),rom_graphics_bytes=len(raw),map_bytes=len(mp)*2,cache_tiles=cache,maximum_visible_patterns=maximum,nest_all_six_pose_tiles=150,total_resident_tiles=cache+150,resident_bytes=(cache+150)*32,heap_bytes=(len(tiles)+cache*4)*2,lossy_tile_replacements=0)
js(A/'manifest.json',d);print(json.dumps({'memory':d['memory'],'geometry':d['geometry'],'maximum_nest_slots':maxslots},indent=2))
