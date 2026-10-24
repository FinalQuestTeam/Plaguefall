"""Phase3 private native candidate. Source-first semantic whole-assembly composition.
No production integration: parent reviews the complete panorama before code export.
"""
from pathlib import Path
import sys,json
from PIL import Image
G=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(G/'tools'));import build_campaign_factory as b
A=Path(__file__).resolve().parent
# Decorative top band remains visible; feet never enter the HUD clipping zone.
LEVEL_BOUNDS=[16,80,2543,303]
C=Image.open(G/'art/campaign-pattern-v2/early/01-courtyard/complete-native.png');D=Image.open(G/'art/campaign-pattern-v2/early/01-courtyard/damaged-native.png')
S=b.indexed(A/'source/whole-folded-cycle3.png',(768,864),1,C)
(A/'modules').mkdir(exist_ok=True);(A/'draft').mkdir(exist_ok=True)
mods={}
def crop(n,r):
 im=S.crop(r);mods[n]={'source':list(r),'size':list(im.size)};im.save(A/f'modules/{n}.png');return im

def mat(im,w,h):
 out=Image.new('P',(w,h),11);out.putpalette(C.getpalette());b.repeat(out,im,(0,0,*im.size),(0,0,w,h));return out

def roof(w):
 middle=Image.new('P',(8,56),11);middle.putpalette(C.getpalette());middle.paste(crop('roof-plane',(392,164,400,216)),(0,4))
 out=mat(middle,w,56)
 out.paste(crop('roof-left',(342,160,366,216)),(0,0));out.paste(crop('roof-right',(500,160,524,216)),(w-24,0));return out

# Unadorned plaster: the sampled material is a flat source wall pixel, not a lantern/plant slice.
wall=crop('plaster-material',(355,216,356,217))
print('plaster',wall.getpixel((0,0)))
door=crop('human-door',(360,216,392,264))
bay=crop('retail-complete-bay',(440,212,472,272));retail=mat(bay,96,60)
retail.paste(crop('canopy-start',(400,212,408,244)),(0,0));retail.paste(crop('canopy-end',(488,212,496,244)),(88,0))
window=crop('residential-window',(92,432,128,468))
roller=Image.new('P',(144,64),15);roller.putpalette(C.getpalette())
roller.paste(mat(crop('roller-slat',(520,672,536,680)),128,48),(8,8))
roller.paste(mat(crop('roller-head',(507,652,523,660)),128,8),(8,0));roller.paste(mat(crop('roller-foot',(520,706,536,714)),128,8),(8,56))
roller.paste(crop('roller-left-frame',(499,652,507,716)),(0,0));roller.paste(crop('roller-right-frame',(632,652,640,716)),(136,0))
roller.save(A/'modules/roller-whole-assembled.png')
garage=crop('garage-door-whole',(167,736,240,781))
def building(w,kind):
 h=128 if kind=='warehouse' else 112
 out=Image.new('P',(w,h),11);out.putpalette(C.getpalette());out.paste(mat(wall,w,h-56),(0,56));out.paste(roof(w),(0,0))
 out.paste(mat(curb,w,16),(0,h-16))
 out.paste(mat(crop('facade-left-edge',(345,220,349,228)),4,h-56),(0,56))
 out.paste(mat(crop('facade-right-edge',(514,220,518,228)),4,h-56),(w-4,56))
 if kind=='market':out.paste(door,(16,56));out.paste(retail,(56,52))
 elif kind=='house':out.paste(door,(w//2-16,56));out.paste(window,(12,56))
 elif kind=='garage':out.paste(garage,(w//2-garage.width//2,60))
 else:out.paste(roller,(w//2-roller.width//2,56))
 return out

out=Image.new('P',(2560,320),11);out.putpalette(C.getpalette())
# Continuous land-use blocks shape the road, with corners/junctions and frontage courts.
curb=crop('curb-straight',(400,272,416,288));corner=crop('curb-corner',(536,264,576,288))
wallparcel=Image.open(G/'art/campaign-pattern-v2/early/01-courtyard/modules/lower-wall.png')
# Use a genuine flat green material sampled from the whole source; no tiled leaf fragments.
xy=next((x,y) for y in range(0,48) for x in range(0,112) if S.getpixel((x,y))==5)
green=crop('garden-ground',(xy[0],xy[1],xy[0]+1,xy[1]+1));road=crop('road-ground',(584,280,585,281))
print('road',road.getpixel((0,0)))
out.paste(mat(green,2560,320),(0,0))
segments=[(0,96,352,208),(352,24,352,152),(704,112,448,192),(1152,96,416,208),(1568,24,480,184),(2048,96,512,208)]
for x,y,w,h in segments:out.paste(mat(road,w,h),(x,y))
# Connected frontages/forecourts, not isolated background rectangles.
for x,y,w,h in [(0,24,320,152),(352,128,320,176),(752,24,256,152),(1200,24,352,216),(1648,128,352,176),(2176,24,384,264)]:out.paste(mat(road,w,h),(x,y))
# Road limits change depth. Complete curve modules are placed at each returning corner.
for x,y,w,h in segments:
 b.repeat(out,curb,(0,0,16,16),(x,y,w,16));b.repeat(out,curb,(0,0,16,16),(x,y+h-16,w,16))
 out.paste(corner,(x+w-40,y+h-24))
# Low plot walls physically connect buildings into blocks; openings face forecourts.
def wallrun(x,y,w):b.repeat(out,wallparcel,(0,0,*wallparcel.size),(x,y,w,32))
for x,y,w in [(0,0,320),(320,0,432),(752,0,256),(1008,32,192),(1200,0,352),(1552,0,496),(2048,32,128),(2176,0,384),(352,128,16),(608,128,64),(1648,128,16),(1952,128,48)]:wallrun(x,y,w)
# Garden strips hug the back/side of whole structures. Church's source vegetation belongs inside a bounded plot.
for x,y,w,h in [(0,32,48,112),(248,32,72,112),(752,32,48,112),(960,32,48,112),(352,160,48,128),(624,160,48,128),(1648,160,64,128),(1952,160,48,128)]:out.paste(mat(green,w,h),(x,y))
# Parcel pavements connect to the road and continue around foreground buildings.
for x,y,w in [(0,160,320),(352,288,320),(752,160,256),(1200,224,352),(1648,288,352),(2176,272,384)]:b.repeat(out,curb,(0,0,16,16),(x,y,w,16));out.paste(corner,(x+w-40,y-8))
vcurb=crop('curb-vertical',(256,208,264,224))
for x,y1,y2 in [(352,24,96),(704,24,112),(1152,96,112),(1568,24,96),(2048,24,96)]:b.repeat(out,vcurb,(0,0,8,16),(x-8,y1,8,y2-y1))
for x,y1,y2 in [(352,176,304),(704,176,304),(1568,208,304),(2048,208,304)]:b.repeat(out,vcurb,(0,0,8,16),(x-8,y1,8,y2-y1))
# Closed southern parcel boundaries: exact source stone face mirrored into 16px wall.
# 48px north-west openings keep both inner yards connected to the street.
sidewall=Image.new('P',(16,16));sidewall.putpalette(C.getpalette());sidewall.paste(vcurb,(0,0));sidewall.paste(vcurb.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(8,0));sidewall.save(A/'modules/parcel-sidewall.png')
for left,right in [(352,672),(1648,2000)]:
 b.repeat(out,sidewall,(0,0,16,16),(left,128,16,192));b.repeat(out,sidewall,(0,0,16,16),(right-16,128,16,192))
 wallrun(left,288,right-left)
placements=[]
def assembly(x,y,w,kind):
 im=building(w,kind);out.paste(im,(x,y));placements.append({'kind':kind,'building_bbox':[x,y,w,im.height]})
church=C.crop((16,0,216,112));out.paste(church,(48,32));placements.append({'kind':'church','building_bbox':[48,32,200,112]})
assembly(416,144,192,'market')
assembly(800,32,160,'house')
assembly(1248,32,192,'garage')
assembly(1712,144,240,'garage')
assembly(2288,32,240,'warehouse')
raw=Image.open(A/'source/truck-extracted.png').convert('RGBA');raw=raw.crop(raw.getchannel('A').getbbox());raw=raw.resize((96,56),Image.Resampling.NEAREST)
raw.save(A/'modules/truck-alpha.png')
truckground=out.crop((1312,160,1408,216)).convert('RGBA');truckground.alpha_composite(raw);truckground.save(A/'modules/truck-on-road.png')
out.paste(b.indexed(A/'modules/truck-on-road.png',(96,56),1,C),(1312,160))
bp=G/'art/campaign-pattern-v2/early/01-courtyard/modules/barrels.png';rawbarrels=Image.open(bp).convert('RGBA');barrels=b.indexed(bp,rawbarrels.size,1,C)
barrelground=out.crop((2224,176,2264,216)).convert('RGBA');barrelground.alpha_composite(rawbarrels);barrelground.save(A/'modules/barrels-on-road.png')
out.paste(b.indexed(A/'modules/barrels-on-road.png',(40,40),1,C),(2224,176))
for n,im in [('candidate',out),('damaged',out.copy())]:
 if n=='damaged':im.paste(D.crop((16,0,216,112)),(48,32))
 im.save(A/f'draft/{n}-complete.png');print(n,len(b.pack(im)[0]))
 for i,x in enumerate((0,288,672,1120,1600,2016,2240)):
  im.crop((x,0,x+320,224)).resize((640,448),Image.Resampling.NEAREST).save(A/f'draft/{n}-view-{i}.png')
(A/'draft/modules.json').write_text(json.dumps(mods,indent=2));(A/'draft/placements.json').write_text(json.dumps(placements,indent=2))
