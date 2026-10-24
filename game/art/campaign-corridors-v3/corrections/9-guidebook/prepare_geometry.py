"""Isolated bridge contract; reads native art and root's pure geometry library.
Never activates the proposal, edits shared generators/C, builds or runs a ROM.
"""
from pathlib import Path
from collections import deque
import json,os,sys,hashlib
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parent;G=A.parents[3];sys.path.insert(0,str(G/'tools'))
from campaign_geometry import free,route,validate
import campaign_corridors as bridge
m=json.loads((A/'manifest.json').read_text());provenance=json.loads((A/'module-trace.json').read_text());placements=json.loads((A/'placements.json').read_text())
solids=[[0,32,2560,80,True],[0,32,16,288,True],[2544,32,16,288,True],[0,304,2560,16,True]]
for x,y,w in [(352,160,480),(1088,224,512),(1712,160,416)]:solids += [[x,y,16,320-y,True],[x+w-16,y,16,320-y,True]]
for p in placements:
 if p['asset'].startswith('whole-workshop') or p['asset'].startswith('whole-rust-truck'):solids.append(p['bbox']+[True])
m.update(size=[2560,320],bounds=[16,112,2543,303],start=[48,184],solids=solids,exit=[2384,112,96,64],camera_player_y=200)
keys=[[288,184],[320,128],[848,128],[1056,184],[1152,184],[1152,248],[1344,248],[1376,184],[1664,184],[1680,128],[1744,128],[1752,184],[1960,184],[2048,128],[2160,128],[2424,136]]
assert free(m,*m['start'],8)
for p in keys:assert free(m,*p,8),('unsafe key',p)
waypoints=route(m,keys);m['player_waypoints']=waypoints;m['route_points']=[[x+8,y+8] for x,y in waypoints];m['points']=m['route_points']
# Require the entire controlled polyline to retain8px clearance, not only endpoints.
margin_samples=0
for p,q in zip(waypoints,waypoints[1:]):
 dx=q[0]-p[0];dy=q[1]-p[1];assert dx==0 or dy==0
 n=max(abs(dx),abs(dy))
 for i in range(n+1):
  x=p[0]+(dx*i//n if n else 0);y=p[1]+(dy*i//n if n else 0);assert free(m,x,y,8),('swept8margin',p,q,x,y);margin_samples+=1
m['geometry_validation']=validate(m)
# Check all legal margin positions form one component, separately from physical free cells.
l,t,r,b=m['bounds'];legal={(x,y) for x in range(l,r-14,8) for y in range(t,b-14,8) if free(m,x,y,8)};seen={tuple(m['start'])};queue=deque(seen)
while queue:
 x,y=queue.popleft()
 for p in [(x+8,y),(x-8,y),(x,y+8),(x,y-8)]:
  if p in legal and p not in seen:seen.add(p);queue.append(p)
assert legal==seen,('orphan margin positions',len(legal-seen))
m['geometry_validation'].update(margin_pixels=8,swept_margin_samples=margin_samples,margin_free_positions=len(legal),all_margin_positions_connected=True,invisible_floor_solids=0)
# Whole architectural/physical landmark bboxes. One grouped dock fits320x200 exactly.
focus=[('repair-workshop',[128,32,128,128],[184,184],[32,0]),('south-workshop',[640,160,128,128],[608,272],[456,72]),('service-dock',[1216,32,312,192],[1328,208],[1208,8]),('factory-office',[1792,32,128,128],[1840,184],[1688,0]),('factory-entry',[2392,48,80,64],[2456,184],[2240,0])]
m['camera_interest']=[]
for name,bbox,feet,camera in focus:
 assert free(m,*feet,8),(name,feet)
 x,y,w,h=bbox;cx,cy=camera
 assert w<=320 and h<=200 and cx<=x and x+w<=cx+320 and cy+24<=y and y+h<=cy+224,(name,'cropped')
 m['camera_interest'].append({'id':name,'name':name,'bbox':bbox,'player_feet':feet,'position':feet,'camera':camera,'whole_below_HUD':True})
# Each source has folder-relative path for existing bridge plus explicit game-root path.
paths=sorted({d['source'] for d in provenance.values()});m['module_provenance']=provenance;m['sources']=[{'path':os.path.relpath(G/p,A),'game_path':p,'sha256':hashlib.sha256((G/p).read_bytes()).hexdigest()} for p in paths]
assert all((A/s['path']).resolve().is_file() and (G/s['game_path']).resolve()==(A/s['path']).resolve() for s in m['sources'])
m['source_paths_game']=paths;m['complete']='complete-native.png';m['layout']='layout.png';m['native']={k:f'native/{k}.bin' for k in ['tiles','map','palette']};m['route_point_semantics']='CENTERS; player_waypoints/start are top-left16px FEET; center=feet+8';m['point_semantics']=m['route_point_semantics'];m['pauses']=[]
m['memory'].update(scene_tiles=m['memory']['tiles'],background_tiles=m['memory']['tiles'],objective_tiles=0,total_tiles=m['memory']['tiles'],limit=640,free_tiles=640-m['memory']['tiles'],graphics_bytes=m['memory']['tile_bytes'],palette_bytes=32,collision_mask_words=400)
m['status']='isolated candidate: visual family and connected entry accepted for private ROM trial by root; not published or finally approved'
m['geometry_notes']=['All solids coincide with visible native walls, complete workshop bodies or truck silhouettes. No solid rect is placed on open floor.','Full projected bboxes keep the player out of baked architecture; tall volumes and trucks block feet and shots.','Primary route has8px clearance beyond16x16feet (32px envelope); the upper lane near south workshop has48px depth.','A visible16px rear strip behind south workshop exists off the main route; it is not an8px-margin route and is not masked by an invisible floor blocker. Physical and8px-margin free regions are each globally connected.','Global lower/lateral walls and courtyard returns have native whole matching caps/corners; no orphan enclosed yard.','Exit is the front apron of the exact old80x64factory entrance; story length2560 and single continuation to10 remain unchanged.']
m['art_limitations']=['Three workshop buildings share one existing whole family, and two trucks share one existing whole family; repetition remains visible.','The candidate uses the old rusty tunnel wall as the exterior industrial boundary; no new distant factory silhouette was invented.','These five images are composed native previews, not running-ROM captures. Final visual/runtime approval remains with root/user after the isolated ROM trial.']
(A/'manifest.json').write_text(json.dumps(m,indent=2))
# Private convenience C. Root can use its existing bridge on these same binaries instead.
tiles=(A/'native/tiles.bin').read_bytes();mapping=(A/'native/map.bin').read_bytes();palette=(A/'native/palette.bin').read_bytes()
code='/* ISOLATED candidate. Do not publish without root trial/review. */\n'+bridge.array('streetTiles','u32',tiles)+bridge.array('streetPalette','u16',palette)+bridge.array('streetMap','u16',mapping)
cam,fields=bridge.camera('streetCameraFocus',m);code+=cam+f'static const ArenaScene streetScene={{.tiles=streetTiles,.map=streetMap,.palette=streetPalette,.tileCount={len(tiles)//32},.rows=40,.cols=320,.cameraPlayerY=200,{fields}}};\n'+bridge.rects('streetSolids',solids)+bridge.arena('CF_STREET','streetScene','streetSolids',m)+bridge.route('CF_ROUTE09','points09',m)
(A/'code.inc').write_text(code)
im=Image.open(A/'complete-native.png').convert('RGBA');overlay=Image.new('RGBA',im.size);draw=ImageDraw.Draw(overlay)
for x,y,w,h,*_ in solids:draw.rectangle((x,y,x+w-1,y+h-1),outline=(255,50,50,255),fill=(255,0,0,35),width=1)
draw.line([tuple(p) for p in m['route_points']],fill=(0,255,255,255),width=2)
for x,y in m['route_points']:draw.ellipse((x-3,y-3,x+3,y+3),fill=(0,255,255,255))
im.alpha_composite(overlay);im.convert('RGB').save(A/'layout.png')
print(json.dumps({'solids':len(solids),'waypoints':len(waypoints),'physical':m['geometry_validation'],'all_sources_resolve':True,'private_C_bytes':len(code)},indent=2))
