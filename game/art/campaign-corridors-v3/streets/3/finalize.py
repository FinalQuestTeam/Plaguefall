"""Private phase3 delivery: exact native export and independently checked geometry.
Does not modify shared C, generators, tests or ROM.
"""
from pathlib import Path
from collections import deque
import json,hashlib,sys,runpy
from PIL import Image
A=Path(__file__).resolve().parent;G=A.parents[3]
sys.path.insert(0,str(G/'tools'));import build_campaign_factory as b
authored=runpy.run_path(str(A/'build.py'))
read=lambda p:json.loads(p.read_text())
placements=read(A/'draft/placements.json')
wallruns=[(0,0,320),(320,0,432),(752,0,256),(1008,32,192),(1200,0,352),(1552,0,496),(2048,32,128),(2176,0,384),(352,128,16),(608,128,64),(1648,128,16),(1952,128,48)]
parcel_boundaries=[[352,128,16,192],[656,128,16,192],[352,288,320,32],[1648,128,16,192],[1984,128,16,192],[1648,288,352,32]]
solids=parcel_boundaries+[v['building_bbox'] for v in placements]+[[1312,160,96,56],[2224,176,40,40]]+[[x,y,w,32] for x,y,w in wallruns]
bounds=authored['LEVEL_BOUNDS'];start=[32,184];exitbox=[2384,176,112,80]
# Eight pixels of free space beyond the full 16x16 actor feet, on all sides.
def free(p,margin=8):
 x,y=p
 return bounds[0]+margin<=x and x+15<=bounds[2]-margin and bounds[1]+margin<=y and y+15<=bounds[3]-margin and not any(x<sx+sw+margin and x+16>sx-margin and y<sy+sh+margin and y+16>sy-margin for sx,sy,sw,sh in solids)
def path(src,dst):
 src=tuple(src);dst=tuple(dst);assert free(src),('source',src);assert free(dst),('destination',dst)
 q=deque([src]);prev={src:None}
 while q:
  p=q.popleft()
  if p==dst:break
  for dx,dy in [(8,0),(0,-8),(0,8),(-8,0)]:
   n=(p[0]+dx,p[1]+dy)
   if n not in prev and free(n):prev[n]=p;q.append(n)
 assert dst in prev,('unreachable',src,dst)
 out=[];p=dst
 while p is not None:out.append(p);p=prev[p]
 return out[::-1]
keys=[start,[304,184],[328,96],[696,96],[696,200],[1040,200],[1160,224],[1488,224],[1600,96],[2024,96],[2072,200],[2160,232],[2280,232],[2432,200]]
walk=[]
for a,c in zip(keys,keys[1:]):walk.extend(path(a,c)[:-1])
walk.append(tuple(keys[-1]));route=[walk[0]]
for i in range(1,len(walk)-1):
 if (walk[i][0]-walk[i-1][0],walk[i][1]-walk[i-1][1])!=(walk[i+1][0]-walk[i][0],walk[i+1][1]-walk[i][1]):route.append(walk[i])
route.append(walk[-1]);assert all(free(p) for p in walk)
connectivity={}
for margin in (0,8):
 legal={(x,y) for x in range(0,2560,8) for y in range(0,320,8) if free((x,y),margin)};seen={tuple(start)};queue=deque(seen)
 while queue:
  x,y=queue.popleft()
  for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
   if p in legal and p not in seen:seen.add(p);queue.append(p)
 assert legal==seen,('orphan free areas',margin,sorted(legal-seen)[:10])
 connectivity[str(margin)]={'free_positions':len(legal),'connected_to_start':len(seen),'unreachable':0}
assert not all(free((x,280),0) for x in range(32,2496,8))
(A/'draft/connectivity.json').write_text(json.dumps(connectivity,indent=2))
interests=[]
for v,pose in zip(placements,[[136,176],[496,264],[872,176],[1280,160],[1824,264],[2400,176]]):
 x,y,w,h=v['building_bbox'];assert free(pose),(v,pose)
 cx=max(0,min(2240,pose[0]-152));cy=max(0,min(96,y-24))
 assert cx<=x and x+w<=cx+320 and cy+24<=y and y+h<=cy+224,(v,pose,cx,cy)
 interests.append({'id':v['kind']+'-'+str(x),'bbox':[x,y,w,h],'player_feet':pose,'camera':[cx,cy],'purpose':'Entire building silhouette, base and door visible below reserved HUD.'})
colors=[tuple(Image.open(A/'draft/candidate-complete.png').getpalette()[i:i+3]) for i in range(0,48,3)]
palbytes=b''.join(((round(c[0]*7/255)<<1)|(round(c[1]*7/255)<<5)|(round(c[2]*7/255)<<9)).to_bytes(2,'big') for c in colors)
assert colors[0]==(0,0,0)
mem={};code=['/* Private exact phase3 data. Root owns production integration. */']
for name,folder,prefix in [('candidate','native','street03'),('damaged','damaged-native','street03Damaged')]:
 im=Image.open(A/f'draft/{name}-complete.png');tiles,mapping,reused=b.pack(im);assert len(tiles)<=640
 d=A/folder;d.mkdir(exist_ok=True);im.save(d/'complete.png')
 packed=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles);mapbytes=b''.join(x.to_bytes(2,'big') for x in mapping)
 (d/'tiles.bin').write_bytes(packed);(d/'map.bin').write_bytes(mapbytes);(d/'palette.bin').write_bytes(palbytes)
 mem[folder]={'scene_tiles':len(tiles),'objective_tiles':0,'total_tiles':len(tiles),'budget':640,'tile_bytes':len(packed),'map_bytes':len(mapbytes),'palette_bytes':32,'exact_flip_reuse':reused,'pixel_identical_decode':True,'sha256':hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()}
 code+=['static const u32 '+prefix+'Tiles[]={']
 for offset in range(0,len(packed),32):code.append(','.join('0x'+packed[i:i+4].hex()+'UL' for i in range(offset,offset+32,4))+',')
 code+=['};','static const u16 '+prefix+'Palette[]={'+','.join(str(int.from_bytes(palbytes[i:i+2],'big')) for i in range(0,32,2))+'};','static const u16 '+prefix+'Map[]={']
 code+=[','.join(map(str,mapping[i:i+320]))+',' for i in range(0,len(mapping),320)];code+=['};','static const ArenaScene '+prefix+'Scene={.tiles='+prefix+'Tiles,.map='+prefix+'Map,.palette='+prefix+'Palette,.tileCount='+str(len(tiles))+',.rows=40,.cols=320};']
 hero=Image.open(G/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png').convert('RGBA').crop((0,0,32,48))
 vd=d/'views';vd.mkdir(exist_ok=True);views=[]
 for i,ci in enumerate(interests):
  cx,cy=ci['camera'];px,py=ci['player_feet'];world=im.convert('RGBA');world.alpha_composite(hero,(px-8,py-31));view=world.crop((cx,cy,cx+320,cy+224));view.save(vd/f'{i:02}-{ci["id"]}.png');views.append(view)
 sheet=Image.new('RGB',(960,448))
 for i,v in enumerate(views):sheet.paste(v,(i%3*320,i//3*224))
 sheet.save(d/'camera-sheet.png')
(A/'code.inc').write_text('\n'.join(code)+'\n')
manifest={'phase':'3','status':'candidate awaiting independent whole-map visual review','size':[2560,320],'bounds':bounds,'start':start,'solids':solids,'route_points':[[x+8,y+8] for x,y in route],'player_waypoints':[list(p) for p in route],'route_margin':8,'route_validation':{'footprint':[16,16],'grid_step':8,'walk_samples':len(walk),'all_samples_clear_with_margin':True,'movement':'axis-aligned segments; intermediate 8px samples validated'},'exit':exitbox,'camera_player_y':200,'camera_interest':interests,'church_bbox':[48,32,200,112],'church_original_bbox':[16,0,200,112],'church_identity':{'intact_source':'../../../campaign-pattern-v2/early/01-courtyard/complete-native.png','damaged_source':'../../../campaign-pattern-v2/early/01-courtyard/damaged-native.png','exact_pixels_both_states':True},'sources':['source/whole-folded-cycle2.png','source/whole-folded-cycle3.png','source/truck-extracted.png'],'complete':'native/complete.png','native':{'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin'},'damaged_native':{'complete':'damaged-native/complete.png','tiles':'damaged-native/tiles.bin','map':'damaged-native/map.bin','palette':'damaged-native/palette.bin'},'memory':mem['native'],'special_states':[{'state':'church destroyed by bomb in phase1','path':'damaged-native/complete.png','memory':mem['damaged-native']}],'palette':{'index0':'black','colors':colors,'encoding':'RGB333 16 entries, big-endian Mega Drive words'},'layout':'layout.svg','module_trace':'draft/modules.json','engineering_notes':['Curbs are low walkable pavement edges; green garden material is walkable unless bounded by listed walls/buildings.','All visible buildings, perimeter wall segments, truck and barrel pair have solid footprints. Full projected building bboxes are conservative to keep baked background architecture in front of the player.','Shared roofs/plaster/frames/slats retain their material; complete doors, canopy ends, garage jambs and church are never approximated by similar tiles.','RGBA truck/barrels composited in RGB against actual ground before nearest palette conversion, avoiding palette-index alpha interpolation.','Camera views are composed native previews with existing hero sprite, not emulator screenshots; runtime confirmation belongs to root.'],'critical_review':{'improvements':['Street bends around north/south parcels; church plaza, market block, workshop and arrival forecourt are distinct spaces.','South facades retain their full base; all six principal buildings have complete legal camera previews.','Church is pixel-identical in both conditions; no roof/bush crop replacement.'],'limitations':['Repeated roof grammar and quiet flat road are deliberate memory tradeoffs; independent visual reviewer must decide whether parcel rhythm remains too regular.','Damaged bank uses all640tiles, leaving no room for additional background art.','Whole-scene source is decomposed into shared architectural materials and complete openings; final native panorama is not a literal downscale of the source.']}}
manifest['global_connectivity']=connectivity
manifest['southern_parcels']={'closed_to_bottom':[[352,128,320,192],[1648,128,352,192]],'northwest_openings':[[368,128,48,32],[1664,128,48,32]],'walls':parcel_boundaries,'inner_yards_connected':True,'floor_y280_is_not_a_straight_bypass':True}
for folder,src in [('native','complete-native.png'),('damaged-native','damaged-native.png')]:
 actual=Image.open(A/folder/'complete.png').crop((48,32,248,144)).convert('RGB');expected=Image.open(G/'art/campaign-pattern-v2/early/01-courtyard'/src).crop((16,0,216,112)).convert('RGB');assert actual.tobytes()==expected.tobytes()
assert (A/'native/palette.bin').read_bytes()==(A/'damaged-native/palette.bin').read_bytes()
(A/'manifest.json').write_text(json.dumps(manifest,indent=2))
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="320" viewBox="0 0 2560 320">','<image href="native/complete.png" width="2560" height="320"/>']
svg.append(f'<rect x="{bounds[0]}" y="{bounds[1]}" width="{bounds[2]-bounds[0]+1}" height="{bounds[3]-bounds[1]+1}" fill="none" stroke="#00ff00" stroke-dasharray="8"/>')
for x,y,w,h in solids:svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="red" fill-opacity=".15" stroke="red"/>')
svg.append('<polyline points="'+' '.join(f'{x+8},{y+8}' for x,y in route)+'" fill="none" stroke="cyan" stroke-width="3"/>')
for ci in interests:
 x,y,w,h=ci['bbox'];svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="white" stroke-dasharray="4"/>')
svg+=['</svg>'];(A/'layout.svg').write_text('\n'.join(svg))
print(json.dumps({'memory':mem,'route_vertices':len(route),'route_samples':len(walk),'interests':len(interests)}))
