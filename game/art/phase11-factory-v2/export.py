"""Phase11 reuses phase10's exact scenery and six complete industrial props."""
from pathlib import Path
import argparse,json,io,math,struct
from PIL import Image,ImageDraw
import sys
G=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;S=G/'art/phase10-factory-v2'
sys.path.insert(0,str(G/'tools'));from campaign_geometry import validate,free,path
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
def emit(p,b):
 if args.check:assert p.exists() and p.read_bytes()==b,('stale phase11 export',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
m=json.loads((S/'manifest.json').read_text());valves=[[112,192],[456,176],[648,288],[248,320],[88,400],[560,456]]
d={k:m[k] for k in ['size','width','height','bounds','start','solids']};d.update(valves=valves,valve_count=6,enemy_cap=5,shot_cap=6,spawn_seconds=2,work_seconds=2.5,points=[])
approaches=[[x-8,min(y+8,(d['bounds'][3]-19)//8*8)] for x,y in valves];route=[d['start']]
for goal in approaches:
 assert free(d,*goal,4),('blocked interaction face',goal)
 route.extend(path(d,route[-1],goal,4)[1:])
d['valve_approaches']=approaches;d['player_route']=route;d['points']=[[x+8,y+8] for x,y in route];d['geometry']=validate(d)
d['memory']={**m['memory'],'nest_all_six_pose_tiles':0,'valve_all_six_pose_tiles':65,'work_bar_tiles':4,'total_resident_tiles':m['memory']['cache_tiles']+65+4,'resident_bytes':(m['memory']['cache_tiles']+65+4)*32}
d.update(background_pixel_identical_to_phase10=False,background_indices_identical_to_phase10=True,shared_ROM_patterns='phase10Tiles',shared_ROM_map='phase10Map',palette_only_variant=True,art_newly_generated=False,props_count=6,eggs_return=False,route_length_px=round(sum(math.dist(a,b) for a,b in zip(route,route[1:])),1))
# Reuse every tile and map index; only the four warm palette slots change.
background=Image.open(S/'complete-native.png');palette=background.getpalette()
for index in (8,9,10,11):
 r,g,b=palette[index*3:index*3+3];palette[index*3:index*3+3]=[b,g,r]
background.putpalette(palette)
words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in zip(palette[0:48:3],palette[1:48:3],palette[2:48:3])]
emit(A/'native/palette.bin',struct.pack('>16H',*words))
d['palette_changed_slots']=[8,9,10,11];d['palette_words']=words
code='// Generated phase11: shared phase10 tiles/map with blue brick palette.\n'
code+='static const u16 phase11Palette[16]={'+','.join(str(v) for v in words)+'};\n'
code+='static const ArenaScene phase11Scene={.tiles=phase10Tiles,.map=phase10Map,.palette=phase11Palette,.tileCount=320,.rows=68,.cols=96,.cameraPlayerY=184,.stream=&phase10Stream,.streamOverlay=TRUE,.cameraSouthStart=352};\n'
code+='const ArenaDef CF_FACTORY_REHEAT={768,544,24,128,743,479,56,160,phase10Solids,6,&phase11Scene};\n'
emit(G/'src/levels/campaign_factory_phase11.inc',code.encode())
header='// Generated phase11 valve positions and interaction timing.\n#ifndef PHASE11_LAYOUT_H\n#define PHASE11_LAYOUT_H\n#define PHASE11_VALVE_COUNT 6\n#define PHASE11_WORK_FRAMES ((fps*5+1)/2)\nstatic const s16 PHASE11_VALVES[6][2]={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in valves)+'};\n#endif\n'
emit(G/'src/levels/phase11_layout.h',header.encode())
png(A/'complete-background.png',background)
scene=background.convert('RGBA');icon=Image.open(G/'art/objective-sprites-v1/frames/valve-0.png').convert('RGBA')
for x,y in valves:scene.alpha_composite(icon,((x-16)//8*8,(y-24)//8*8))
png(A/'complete-with-valves.png',scene)
routeimage=scene.copy();draw=ImageDraw.Draw(routeimage)
for x,y,w,h,*_ in d['solids']:draw.rectangle((x,y,x+w-1,y+h-1),outline='#ff7755',width=1)
draw.line([tuple(p) for p in d['points']],fill='#50ffff',width=2)
for i,(x,y) in enumerate(valves):draw.text((x+20,y-8),str(i+1),fill='#ffffff')
png(A/'layout.png',routeimage)
emit(A/'manifest.json',(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps({'memory':d['memory'],'geometry':d['geometry'],'route_length_px':d['route_length_px']},indent=2))
