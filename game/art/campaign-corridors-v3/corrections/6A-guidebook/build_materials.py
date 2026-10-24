"""Isolated6A/6B material trial. Reuses current native geometry/modules and R04
native surface samples. No new bitmap, noise synthesis, scene activation or C edit.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,sys,hashlib,io
CHECK="--check" in sys.argv
CHECKED=[]
def emit(path,data):
 if CHECK:
  assert path.read_bytes()==data,("builder byte mismatch",str(path))
  CHECKED.append(str(path))
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
def image_emit(path,im):
 buf=io.BytesIO();im.save(buf,format="PNG");emit(path,buf.getvalue())
A=Path(__file__).resolve().parent;V=A.parents[1];G=V.parents[1];sys.path.insert(0,str(G/'tools'));import build_campaign_factory as pack
old=Image.open(V/'sewers/6A/complete-indexed.png');OLD=[tuple(old.getpalette()[i:i+3]) for i in range(0,48,3)];PAL=OLD.copy();PAL[7]=(109,109,109);PAL[8]=(145,145,145);PAL[6]=(145,109,72);PAL[14]=(36,36,72)
# Retain deep blues of existing pumps, warm rust/iron pigments, and all16entries.
assert PAL[0]==(0,0,0) and len(set(PAL))==16
r04=Image.open(G/'art/phase04-tunnels-v1/map-native.png').convert('RGB');floor_source=r04.crop((360,208,376,224))
def nearest_material(im,colors):
 rgb=np.array(im.convert('RGB'));p=np.array([PAL[i] for i in colors]);ix=((rgb[:,:,None].astype(int)-p[None,None])**2).sum(3).argmin(2);return np.array(colors,dtype=np.uint8)[ix]
# Existing concrete3shade pattern stays1px; charcoal channel reuses its sparse grain.
F=nearest_material(floor_source,[7,8,15]);W=np.where(F==7,1,np.where(F==8,14,0)).astype(np.uint8);B=np.choose(np.argmin(((np.array(floor_source)[:,:,None].astype(int)-np.array([(109,109,109),(145,145,145),(72,72,72)])[None,None])**2).sum(3),axis=2),[15,6,1]).astype(np.uint8)
def rgba_from_idx(a,alpha=None,palette=PAL):
 rgb=np.array(palette,dtype=np.uint8)[a];alpha=np.full(a.shape,255,dtype=np.uint8) if alpha is None else alpha;return Image.fromarray(np.concatenate([rgb,alpha[:,:,None]],2),'RGBA')
def indices(im):
 raw=np.array(im.convert('RGBA'));rgb=raw[:,:,:3];p=np.array(OLD);ix=((rgb[:,:,None].astype(int)-p[None,None])**2).sum(3).argmin(2).astype(np.uint8);return ix,raw[:,:,3]
def texture_fill(a,shape):return np.tile(a,((shape[0]+a.shape[0]-1)//a.shape[0],(shape[1]+a.shape[1]-1)//a.shape[1]))[:shape[0],:shape[1]]
def mods_for(key,edited):
 src=V/'sewers'/key/('cycle3-candidate' if key=='6A' else 'candidate');mods={}
 names=['inlet-detail','stairs-detail','tank-detail','bridge-detail','canopy','curve','floor','water','bank','side','corner']+(['feed-pipe','brick','edge','pillar-face'] if key=='6B' else [])
 for name in names:
  im=Image.open(src/(name+'.png')).convert('RGBA');ix,alpha=indices(im)
  if edited:
   if name=='floor':ix=texture_fill(F,ix.shape)
   elif name=='water':ix=texture_fill(W,ix.shape)
   elif name in ['curve','inlet-detail']:
    # Water pigment only; exact mouth/cascade/curve silhouette remains intact.
    watermap={2:1,3:14,4:15,5:15}
    orig=ix.copy()
    for pigment,target in watermap.items():ix[orig==pigment]=target
   elif name in ['bank','side','pillar-face']:
    tx=texture_fill(B,ix.shape);ix=np.where(ix==15,tx,ix).astype(np.uint8)
   mods[name]=rgba_from_idx(ix,alpha)
  else:mods[name]=im
 return mods

def compose(key,mods,palette):
 out=Image.new('RGBA',(3072,320),(*palette[2],255))
 def fill(name,rect):
  x,y,w,h=rect;m=mods[name]
  for yy in range(y,y+h,m.height):
   for xx in range(x,x+w,m.width):out.alpha_composite(m.crop((0,0,min(m.width,x+w-xx),min(m.height,y+h-yy))),(xx,yy))
 def put(name,x,y):out.alpha_composite(mods[name],(x,y))
 fill('water',(0,0,3072,320))
 platforms=([[24,96,640,176],[664,208,160,64],[824,80,448,192],[1272,96,184,80],[1456,80,672,192],[2128,184,416,80],[2160,112,192,152],[2544,88,504,184]] if key=='6A' else [[24,96,640,176],[664,208,168,64],[832,80,400,192],[1232,96,208,80],[1440,80,624,192],[2064,184,160,80],[2224,88,824,184]])
 mask=np.zeros((40,384),dtype=bool)
 for x,y,w,h in platforms:fill('floor',(x,y,w,h));mask[y//8:(y+h)//8,x//8:(x+w)//8]=True
 for ty in range(40):
  for tx in range(384):
   if not mask[ty,tx]:continue
   if ty==0 or not mask[ty-1,tx]:fill('bank',(tx*8,ty*8-32,8,32))
   if ty==39 or not mask[ty+1,tx]:fill('bank',(tx*8,ty*8+8,8,min(32,320-ty*8-8)))
   if tx==0 or not mask[ty,tx-1]:fill('side',(max(0,tx*8-8),ty*8,8,8))
   if tx==383 or not mask[ty,tx+1]:fill('side',(tx*8+8,ty*8,8,8))
 def basin(x,y,w,h):
  fill('water',(x,y,w,h));fill('bank',(x,y-32,w,32));fill('bank',(x,y+h,w,min(32,320-y-h)));fill('side',(x-8,y,8,h));fill('side',(x+w,y,8,h))
 if key=='6A':
  basin(80,104,144,80);basin(224,144,176,40);put('curve',384,128);put('inlet-detail',112,32)
  basin(912,80,48,64);basin(912,192,48,80);put('bridge-detail',896,152)
  basin(1656,144,160,96);put('tank-detail',1672,128)
 else:
  basin(80,104,144,80);put('inlet-detail',112,32)
  basin(1480,144,128,96);put('tank-detail',1496,136)
 fill('bank',(2848,112,160,32));fill('bank',(2896,80,32,32));put('canopy',2848,72);put('stairs-detail',2928,48)
 if key=='6A':
  put('tank-detail',2192,120);put('inlet-detail',2480,104);basin(2496,184,24,16)
 else:
  def col(x,y,w,h):fill('pillar-face',(x,y,w,h));fill('edge',(x,y,w,8));fill('bank',(x,y+h-32,w,32))
  for gx,gy in [(960,112),(2080,192)]:
   col(gx+24,24,32,gy);col(gx-8,gy+56,32,320-gy-56);put('tank-detail',gx-152,gy-48);fill('feed-pipe',(gx-72,gy+12,16,8))
  put('inlet-detail',2480,104);basin(2496,184,24,16)
 return out
for key in ['6A','6B']:
 dest=V/'corrections'/(key+'-guidebook')
 baseline=compose(key,mods_for(key,False),OLD).convert('RGB');canonical=Image.open(V/'sewers'/key/'complete-native.png').convert('RGB');assert baseline.tobytes()==canonical.tobytes(),('baseline mismatch',key)
 mods=mods_for(key,True)
 for n,im in mods.items():image_emit(dest/'modules'/(n+'.png'),im)
 out=compose(key,mods,PAL);rgb=np.array(out.convert('RGB'));lookup={c:i for i,c in enumerate(PAL)};ix=np.array([lookup[tuple(c)] for c in rgb.reshape(-1,3)],dtype=np.uint8).reshape(320,3072);im=Image.fromarray(ix,'P');im.putpalette(sum(map(list,PAL),[])+[0]*720);image_emit(dest/'complete-indexed.png',im);image_emit(dest/'complete-native.png',im.convert('RGB'))
 tiles,mapping,reused=pack.pack(im);reserve=256 if key=='6B' else 0
 report={'phase':key,'status':'isolated material checkpoint pending visual and budget review','scene_tiles':len(tiles),'objective_tiles':reserve,'total_tiles':len(tiles)+reserve,'scene_limit':640-reserve,'fits':len(tiles)+reserve<=640,'baseline_reproduces_active_pixels':True,'geometry_unchanged':True,'new_bitmap_art':False,'procedural_noise':False,'arbitrary_tile_substitutions':0,'material_sources':{'floor':['art/phase04-tunnels-v1/map-native.png',[360,208,16,16]],'dark_channel':['art/phase04-tunnels-v1/map-native.png',[360,208,16,16],'same quiet concrete grain mapped to dark charcoal; existing blue mouths pigment-normalized only'],'bank_grit':'same R04concrete1px grain, palette-normalized only within existing wall-face pigment'},'palette':PAL}
 emit(dest/'material-checkpoint.json',json.dumps(report,indent=2).encode());print(json.dumps(report)[:350])
 if report['fits']:
  emit(dest/'native/tiles.bin',b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles));emit(dest/'native/map.bin',b''.join(v.to_bytes(2,'big') for v in mapping));emit(dest/'native/palette.bin',b''.join(((round(c[0]*7/255)<<1)|(round(c[1]*7/255)<<5)|(round(c[2]*7/255)<<9)).to_bytes(2,'big') for c in PAL))

if CHECK:print("CHECK PASS:",len(CHECKED),"isolated outputs reproduce byte-for-byte; no writes")
