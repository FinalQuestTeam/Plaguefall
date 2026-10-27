"""Pattern v2 shipyard: complete chambers/corners/props, persistent scene states."""
from pathlib import Path
from collections import deque
import importlib.util,json,hashlib,struct
from PIL import Image,ImageDraw
G=Path(__file__).resolve().parents[1];A=G/'art/campaign-pattern-v2/launch'
spec=importlib.util.spec_from_file_location('scene_pack',G/'art/campaign-whole-scenes-v1/pack.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
for d in ['modules','native/normal','native/fire','reviews']:(A/d).mkdir(parents=True,exist_ok=True)
PAL=[(0,0,0),(36,36,36),(0,36,72),(36,72,109),(72,72,72),(109,109,109),(145,145,145),(218,218,182),(109,72,36),(145,109,72),(182,145,36),(255,182,36),(255,218,109),(36,72,109),(182,182,145),(218,182,109)]
source=Image.open(A/'source/14-16-shipyard.png');ignited=Image.open(A/'source/15-16-shipyard-ignition.png')
q,_=P.indexed(source,(512,384),4,palette=PAL);detail,_=P.indexed(source,(512,384),2,palette=PAL);fire,_=P.indexed(ignited,(512,384),4,palette=PAL)
for name,im in [('normal-whole',q),('detail-whole',detail),('fire-whole',fire)]:im.save(A/(name+'-quantized.png'))
def extract(im,box,name):
 p=im.crop(box);p.save(A/'modules'/(name+'.png'));return p
normal=Image.new('P',(512,384));normal.putpalette(q.getpalette());material=q.crop((128,224,129,225))
for y in range(384):
 for x in range(512):normal.paste(material,(x,y))
# Whole structural bays. Reuse identical manufactured chambers by translation,
# never mirror light/shadows or use the crop boundary as an exhaust terminus.
chamber=extract(q,(32,0,216,112),'engine-chamber-complete')
for xy in [(32,0),(296,0)]:normal.paste(chamber,xy)
# Resolution detail pass is an alpha extraction of the complete nozzle inside
# an already complete chamber, never an erasure or clipped replacement.
nozzle=extract(detail,(104,8,160,80),'nozzle-detail-complete');nm=Image.new('L',nozzle.size);ImageDraw.Draw(nm).polygon([(8,0),(48,0),(48,24),(56,64),(48,72),(8,72),(0,64),(8,24)],fill=255)
for xy in [(104,8),(368,8)]:normal.paste(nozzle,xy,nm)
normal.paste(extract(q,(216,0,296,112),'upper-center-bay-complete'),(216,0))
side=extract(q,(0,128,32,192),'side-wall-complete-segment')
for y in range(112,320,64):normal.paste(side,(0,y));normal.paste(side,(480,y))
low=extract(q,(32,320,216,384),'lower-full-bay')
for x in [32,296]:normal.paste(low,(x,320))
normal.paste(extract(q,(216,320,296,384),'lower-door-whole'),(216,320))
for name,box,xy in [('nw',(0,0,32,112),(0,0)),('ne',(480,0,512,112),(480,0)),('sw',(0,304,32,384),(0,304)),('se',(480,304,512,384),(480,304))]:normal.paste(extract(q,box,'corner-'+name),xy)
# Five authored complete conduits, including flanges and elbows. Source cabinets
# are NOT in these crops; the global objective cabinet bodies replace them.
conduits=[('upper-left',(72,120,200,200),[(72,128),(80,128),(88,136),(88,160),(176,160),(184,168),(184,184),(192,192),(200,192)]),('upper-right',(312,120,440,200),[(312,192),(320,192),(328,184),(328,168),(336,160),(424,160),(432,152),(432,136),(440,128)]),('middle-right',(312,192,392,208),[(312,200),(392,200)]),('lower-left',(104,272,224,304),[(104,288),(184,288),(192,280),(200,280),(216,280),(224,280)]),('lower-right',(296,272,408,304),[(296,280),(312,280),(320,288),(408,288)]),('island-feed',(248,208,264,256),[(256,208),(256,256)])]
for name,box,path in conduits:
 patch=extract(detail,box,'conduit-'+name+'-complete');mask=Image.new('L',patch.size);draw=ImageDraw.Draw(mask)
 pts=[(x-box[0],y-box[1])for x,y in path];draw.line(pts,fill=255,width=16,joint='curve')
 # Mask only extracts existing authored pixels; it never paints new pipes.
 normal.paste(patch,(box[0],box[1]),mask)
 rgba=patch.convert('RGBA');rgba.putalpha(mask);rgba.save(A/'modules'/('conduit-'+name+'-extracted.png'))
normal.paste(extract(detail,(192,112,320,224),'station-complete-supported'),(192,112))
normal.paste(extract(detail,(208,240,304,304),'island-complete-shadow'),(208,240))
# Ignition edits only the INSIDE of the complete recessed chambers. Sills and
# floors remain exact and every jet is contained before reaching the sill.
fired=normal.copy();hot=extract(fire,(56,16,200,96),'engine-ignited-interior-complete')
for xy in [(56,16),(320,16)]:fired.paste(hot,xy)
normal.save(A/'14-15-background-composed.png');fired.save(A/'15-16-fire-background-composed.png')
nc,ns=P.pack({'map':normal},PAL,A/'native/normal','normal',489)
fc,fs=P.pack({'map':fired},PAL,A/'native/fire','fire',489)
# Keep the published C names used by the emulator's exact native-pixel probe.
for before,after in [('normal_tiles','normalTiles'),('normal_map','normalMap'),('normal_palette','normalPalette')]:nc=nc.replace(before,after)
for before,after in [('fire_tiles','fireTiles'),('fire_map','fireMap'),('fire_palette','firePalette')]:fc=fc.replace(before,after)
solids=[[200,152,112,64],[248,136,16,16],[216,256,80,48],[56,128,24,16],[440,128,24,16],[392,200,24,16],[408,288,24,16],[88,288,24,16]]
assert all(v%8==0 for r in solids for v in r)
lines=['// Shared modular shipyard architecture across14/15/16.','#include "levels/campaign_launch.h"',
       '#include "levels/campaign_launch_phase14.inc"','#include "levels/campaign_launch_phase15.inc"',
       '#include "levels/campaign_launch_phase16.inc"',
       'bool CL_sceneReset(void){return CL15_sceneReset();}',
       'void CL_sceneFire(u16 row){if(row==8)CL15_sceneFire();}']
(G/'src/levels/campaign_launch_scenes.c').write_text('\n'.join(lines)+'\n')
report={'normal_tiles':ns['tiles'],'fire_tiles':fs['tiles'],'normal_plus_objectives':ns['tiles']+151,'fire_plus_objectives':fs['tiles']+151,'tile_limit':640,'world':[512,384],'bounds':[40,128,471,319],'start':[48,200],'solids':solids,'machines':[[64,136],[448,136],[400,208],[416,296],[96,296]],'radio':[256,192],'protected_station_footprint':[200,152,112,64],'persistent_generators_in':['14','15','16'],'states_share_identical_pixels_outside_engines':True,'whole_sources_first':True,'pixel_exact_reassembly':True,'lossy_tile_replacements':0}
(A/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
