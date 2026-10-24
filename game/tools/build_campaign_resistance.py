"""Pattern v2: complete ImageGen sources -> whole modules -> scene -> exact SGDK tiles."""
from pathlib import Path
from collections import deque,Counter
import importlib.util,json,hashlib
from PIL import Image
G=Path(__file__).resolve().parents[1];A=G/'art/campaign-pattern-v2/resistance'
spec=importlib.util.spec_from_file_location('scene_pack',G/'art/campaign-whole-scenes-v1/pack.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
for d in ['modules/favela','modules/union','native','reviews']: (A/d).mkdir(parents=True,exist_ok=True)
FC=[(0,0,0),(36,36,36),(72,72,36),(109,109,72),(145,145,109),(218,218,182),(109,36,36),(182,109,72),(0,36,72),(72,109,36)]+[(0,0,0)]*6
UC=[(0,0,0),(36,36,36),(72,72,72),(109,109,109),(145,145,145),(182,182,145),(218,218,182),(109,72,36),(145,109,72),(182,145,109),(109,36,36),(145,72,36),(0,36,72),(36,72,109),(72,109,145),(218,182,109)]
def quant(src,size,pal,block=4):return P.indexed(src,size,block,palette=pal)[0]
def blank(size,pal):
 im=Image.new('P',size);im.putpalette([v for p in pal for v in p]+[0]*720);return im
def tilefloor(q,box,size,pal):
 # One complete quiet material sample, no fragments of furniture/props.
 patch=q.crop(box);out=blank(size,pal)
 for y in range(0,size[1],patch.height):
  for x in range(0,size[0],patch.width):out.paste(patch,(x,y))
 return out
def module(q,box,name,group,size=None):
 p=q.crop(box)
 if size:p=p.resize(size,Image.Resampling.NEAREST)
 p.save(A/f'modules/{group}/{name}.png');return p
def paste_prop(canvas,im,xy,floor_colors,protected):
 # Remove ONLY source floor connected to the crop edge. The closed silhouettes,
 # end caps, legs and contact shadows are kept; never trim by an inner rectangle.
 w,h=im.size;data=im.tobytes();seen=set();stack=[]
 for x in range(w):stack.extend([(x,0),(x,h-1)])
 for y in range(h):stack.extend([(0,y),(w-1,y)])
 while stack:
  x,y=stack.pop()
  if (x,y)in seen or not(0<=x<w and 0<=y<h)or data[y*w+x]not in floor_colors or any(a<=x<b and c<=y<d for a,c,b,d in protected):continue
  seen.add((x,y));stack.extend([(x+1,y),(x-1,y),(x,y+1),(x,y-1)])
 mask=Image.frombytes('L',im.size,bytes(0 if(x,y)in seen else 255 for y in range(h)for x in range(w)))
 canvas.paste(im,xy,mask)
src=Image.open(A/'source/07-08-favela-cycle3.png');fq=quant(src.crop((0,128,src.width,src.height)),(768,384),FC)
fq.save(A/'favela-whole-quantized.png');fd=quant(src.crop((0,128,src.width,src.height)),(768,384),FC,2);fd.save(A/'favela-detail-whole-quantized.png')
# All roof silhouettes fit inside the source. Scaling applies to complete houses.
fav=tilefloor(fq,(192,184,193,185),(768,384),FC)
forest=module(fq,(16,8,17,9),'tree-material','favela',(8,8))
for y in range(0,160,8):
 for x in range(768//8):fav.paste(forest,(x*8,y))
front=module(fq,(80,24,192,160),'house-complete','favela',None)
refuge=module(fd,(328,8,432,160),'refuge-complete','favela',None)
wall=module(fq,(160,320,288,368),'front-wall-bay','favela')
for x in range(0,768,128):fav.paste(wall,(x,112));fav.paste(wall,(x,336))
for i,x in enumerate([64,192,320,448,576]):fav.paste(refuge if i==2 else front,(x+8,0 if i==2 else 8))
# Continuous side walls with complete end/corner source sectors.
side=module(fq,(16,240,48,304),'side-middle','favela')
for y in range(144,336,64):fav.paste(side,(0,y));fav.paste(side,(736,y))
for name,box,xy in [('nw',(0,64,64,160),(0,64)),('ne',(704,64,768,160),(704,64)),('sw',(0,304,64,384),(0,304)),('se',(704,304,768,384),(704,304))]:fav.paste(module(fq,box,'corner-'+name,'favela'),xy)
depot=module(fd,(40,192,176,312),'depot-complete','favela');paste_prop(fav,depot,(40,208),{4,5},[(8,8,104,104)])
barrier=module(fd,(240,208,400,256),'barricade-complete-with-shadow','favela')
for xy in [(240,208),(440,256)]:paste_prop(fav,barrier,xy,{4,5},[(8,8,136,40)])
fav.save(A/'07-08-background-composed.png')
# New union room with complete exterior quadrants and an intact booth bevel.
uq=quant(Image.open(A/'source/13A-union.png'),(512,384),UC,4);ud=quant(Image.open(A/'source/13A-union.png'),(512,384),UC,2);ud.save(A/'union-detail-whole-quantized.png');mq=quant(Image.open(A/'source/13B-union-memorial.png'),(512,384),UC,1)
uq.save(A/'union-whole-quantized.png');mq.save(A/'memorial-whole-quantized.png')
room=tilefloor(uq,(192,144,193,145),(512,384),UC)
# Whole rear bays and independent singular booth/banner.
bay=module(ud,(16,0,176,128),'locker-window-bay','union')
room.paste(bay,(16,0));room.paste(bay,(336,0))
room.paste(module(uq,(176,0,264,128),'union-banner-bay','union'),(176,0))
room.paste(module(uq,(256,0,384,24),'upper-beam-complete','union'),(256,0))
room.paste(module(ud,(256,24,384,152),'booth-complete','union'),(256,24))
side=module(uq,(0,128,16,192),'side-middle','union')
for y in range(128,320,64):room.paste(side,(0,y));room.paste(side,(496,y))
for name,box,xy in [('nw',(0,0,16,128),(0,0)),('ne',(496,0,512,128),(496,0)),('sw',(0,296,32,384),(0,296)),('se',(480,296,512,384),(480,296))]:room.paste(module(uq,box,'corner-'+name,'union'),xy)
lower=module(uq,(32,304,208,384),'lower-bay-complete','union')
room.paste(lower,(32,304));room.paste(lower,(304,304));room.paste(module(uq,(208,296,304,384),'lower-door-complete','union'),(208,296))
bench=module(ud,(72,240,200,288),'bench-complete-shadow','union')
for xy in [(72,240),(208,184),(344,240)]:room.paste(bench,xy)
# Canonical Dinorah is behind the wooden counter: entire figure composited,
# then original foreground ledge/front restored to occlude waist/legs.
din=Image.open(G/'art/objetivos-travessia-escolta-v1/assets/dinorah.png').convert('RGBA').crop((32,0,64,48))
alive=room.convert('RGBA');alive.alpha_composite(din,(300,72));alive=quant(alive,(512,384),UC,1)
alive.paste(room.crop((256,108,384,152)),(256,108))
dead=room.copy();dead.paste(mq.crop((272,72,368,112)),(272,72));dead.paste(room.crop((256,112,384,152)),(256,112))
alive.save(A/'13A-background-composed.png');dead.save(A/'13B-background-composed.png')
fc,fs=P.pack({'map':fav},FC,A/'native/favela','favela',544)
uc,us=P.pack({'alive':alive,'dead':dead},UC,A/'native/union','union',640)
fsol=[[40,208,112,104],[248,224,136,24],[448,272,136,24]];cargoSol=[[216,184,32,8],[376,184,32,8],[536,184,32,8],[200,304,32,8],[608,312,32,8]];usol=[[80,264,104,16],[216,208,104,16],[352,264,104,16]]
assert all(v%8==0 for r in fsol+usol for v in r)
lines=['// Pattern v2, complete authored modules and exact tile reconstruction.','#include "levels/campaign_resistance.h"',fc,uc]
lines+=['static const ArenaScene favScene={.tiles=favela_tiles,.map=favela_map,.palette=favela_palette,.tileCount='+str(fs['tiles'])+',.rows=48,.cols=96};']
for name,mp in [('alive','union_alive'),('dead','union_dead')]:lines+=['static const ArenaScene '+name+'Scene={.tiles=union_tiles,.map='+mp+',.palette=union_palette,.tileCount='+str(us['tiles'])+',.rows=48,.cols=64};']
for name,sol in [('favela',fsol),('union',usol)]:lines+=['static const ArenaRect '+name+'Solids[]={'+','.join('{'+','.join(map(str,r))+',TRUE}'for r in sol)+'};']
lines+=['const ArenaDef CAMPAIGN_RESISTANCE_FAVELA={768,384,40,160,727,335,80,176,favelaSolids,3,&favScene};','const ArenaDef CAMPAIGN_RESISTANCE_FAVELA_TARGETS={768,384,40,160,727,335,80,176,favelaSolids,3,&favScene};','const ArenaDef CAMPAIGN_RESISTANCE_UNION_ALIVE={512,384,24,160,487,295,280,168,unionSolids,3,&aliveScene};','const ArenaDef CAMPAIGN_RESISTANCE_UNION_DEAD={512,384,24,160,487,295,280,168,unionSolids,3,&deadScene};']
(G/'src/levels/campaign_resistance_scenes.c').write_text('\n'.join(lines)+'\n')
report={'favela_tiles':fs['tiles'],'union_tiles':us['tiles'],'favela_bounds':[40,160,727,335],'union_bounds':[24,160,487,295],'favela_solids':fsol,'cargo_solids':cargoSol,'cargo_solids_dynamic_until_collected':True,'union_solids':usol,'cargo':[[232,184],[392,184],[552,184],[216,304],[624,312]],'depot':[104,328],'transmitters':[[200,176],[416,304],[664,232]],'worlds':{'7/8':[768,384],'13A/13B':[512,384]},'whole_source_first':True,'pixel_exact_reassembly':True,'lossy_tile_replacements':0,'dinorah_occluded_below_y':108,'source_favela_crop':[0,128,src.width,src.height],'roof_and_prop_extents_review_required':True}
(A/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
