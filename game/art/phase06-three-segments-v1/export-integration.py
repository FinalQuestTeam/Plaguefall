"""Exact native phase6 banks, aligned geometry and a local vertical gate bank."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,math,struct,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;GAME=HERE.parents[1];OUT=HERE/'integration-v1'
sys.path.insert(0,str(GAME/'tools'))
from campaign_geometry import free,path,validate
parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
def emit(p,data):
 if args.check:assert p.read_bytes()==data,('stale integration',p)
 else:
  p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
def js(p,d):emit(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def c_array(name,kind,values):
 return 'static const '+kind+' '+name+'[]={\n'+''.join(','.join(('0x%08XUL'%v if kind=='u32' else str(v)) for v in values[i:i+12])+',\n' for i in range(0,len(values),12))+'};\n'
meta=json.loads((HERE/'manifest.json').read_text());palette=meta['palette'];palwords=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in palette]
# Reuse all six original vertical poses, isolated from other mission gates.
spec=importlib.util.spec_from_file_location('objective_export',GAME/'art/objective-sprites-v1/export.py');obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
gate_data=b''.join(obj.pack(Image.open(HERE/f'references/gate-vertical-{i}.png')) for i in range(6));lookup={};gate_tiles=[];gate_map=[]
for i in range(0,len(gate_data),32):
 tile=gate_data[i:i+32]
 if tile not in lookup:lookup[tile]=len(gate_tiles);gate_tiles.append(tile)
 gate_map.append(lookup[tile])
visibility=[int(any(gate_data[i:i+32])) for i in range(0,len(gate_data),32)]
assert gate_tiles[0]==bytes(32) and len(gate_tiles)==112
header='// Original vertical gate; exact six-pose packing, shared by phases6A/6B.\n'+c_array('sewerGateTiles','u32',struct.unpack('>'+str(len(gate_tiles)*8)+'I',b''.join(gate_tiles)))+c_array('sewerGateMap','u16',gate_map)+c_array('sewerGateVisible','u8',visibility)+'static const CampaignGroundArt sewerGateGround={sewerGateTiles,sewerGateMap,sizeof(sewerGateTiles)/32};\n'
emit(GAME/'src/system/video/sewer_gate_art.h',header.encode());emit(OUT/'mechanisms/gate-frames.bin',gate_data)
js(OUT/'mechanisms/memory.json',dict(gate_tiles=112,valve_tiles=65,mechanism_tiles_6A=112,mechanism_tiles_6B=177,progress_bar_tiles_6B=4,scene_slots=456,total_resident_tiles_6A=568,total_resident_tiles_6B=637,resident_bytes_6B=637*32,source='art/visual-composition-fixes-v1/objectives/cycle-0/gate.png'))
def aligned(r):
 x,y,w,h,shots=r;l=x//8*8;t=y//8*8;rr=math.ceil((x+w)/8)*8;b=math.ceil((y+h)/8)*8
 return [l,t,rr-l,b-t,shots]
for key,source in [('6A','6B-estatico'),('6B','6B-estatico')]:
 dest=OUT/key;image_path=HERE/f'palette-preview/panorama-{source}.png';im=Image.open(image_path).convert('RGB');a=np.array(im);colors={tuple(rgb):i for i,rgb in enumerate(palette)}
 ix=np.array([colors[tuple(rgb)] for rgb in a.reshape(-1,3)],dtype=np.uint8).reshape(320,3072)
 cells=ix.reshape(40,8,384,8).transpose(0,2,1,3).reshape(-1,64);unique={};tiles=[];mapping=[]
 for cell in cells:
  tile=bytes(int(cell[i])*16+int(cell[i+1]) for i in range(0,64,2))
  if tile not in unique:unique[tile]=len(tiles);tiles.append(tile)
  mapping.append(unique[tile])
 grid=np.array(mapping).reshape(40,384);peak=0;at=[]
 for y in range(3,15):
  for x in range(344):
   n=len(np.unique(grid[y:y+26,x:x+41]))
   if n>peak:peak=n;at=[x,y]
 assert peak<=456,(key,'visible cache overflow',peak)
 emit(dest/'native/tiles.bin',b''.join(tiles));emit(dest/'native/map.bin',struct.pack('>15360H',*mapping));emit(dest/'native/palette.bin',struct.pack('>16H',*palwords))
 emit(dest/'complete-native.png',image_path.read_bytes())
 # Game masks use whole8px cells. Round outwards, then regenerate the NPC path.
 solids=[aligned(r) for r in meta['base_solids']+meta['prop_solids']]
 solids+=[aligned(r) for r in meta['pressure']['barriers']]
 gates=[[840,112,16,64],[1864,192,16,64]]
 valves=meta['pressure']['valves'] if key=='6B' else []
 d=dict(phase=key,size=[3072,320],bounds=meta['bounds'],start=meta['start'],solids=solids,exit=meta['exit'],gates=gates,valves=valves,valve_approaches=[[784,152],[1808,232]] if key=='6B' else [],gate_shot_approaches=[[760,152],[1784,232]],camera_player_y=200,camera_south_start=192,camera_interest=[dict(name='Entrada dos esgotos',bbox=[56,24,102,144],preferred_feet=[104,192]),dict(name='Acesso ao abrigo',bbox=[2880,24,128,115],preferred_feet=[2936,176])],sources=['../../palette-preview/panorama-'+source+'.png'],native=dict(tiles='native/tiles.bin',map='native/map.bin',palette='native/palette.bin'),status='native_export_for_active_phase06',streamed_tiles=dict(source_count=len(tiles),resident_budget=456,maximum_visible_tiles=peak,peak_cell=at,window=[41,26]),memory=dict(source_tiles=len(tiles),resident_budget=456,maximum_visible_tiles=peak,source_graphics_rom_bytes=len(tiles)*32,cache_heap_bytes=(len(tiles)+456*4)*2,map_bytes=30720,objective_tiles=181 if key=='6B' else 112),objective_tiles=181 if key=='6B' else 112,sequence=meta['sequence'])
 waypoints=[[104,192],[560,216],[808,136],[896,136],[1120,176],[1328,176],[1584,216],[1832,216],[1912,216],[2080,176],[2528,176],[2936,176]] if key=='6A' else [[104,192],[560,216],[784,152],[808,136],[896,136],[1120,176],[1584,216],[1808,232],[1832,216],[1912,216],[2080,176],[2528,176],[2936,176]]
 route=[d['start']]
 for goal in waypoints[1:]:route+=path(d,route[-1],goal,margin=8)[1:]
 d['route_points']=[[x+8,y+8] for x,y in route];d['points']=d['route_points'];d['pauses']=sorted(set(min(range(1,len(route)-1),key=lambda i:abs(route[i][0]-x)+abs(route[i][1]-y)) for x,y in [[560,216],[1328,176],[2080,176],[2528,176]]))
 d['geometry_validation']=validate(d)
 if gates:
  # Closed gates divide the dry corridor; each valve remains reachable before its gate.
  from collections import deque
  def reaches(extra):
   seen={tuple(d['start'])};q=deque(seen)
   while q:
    x,y=q.popleft()
    for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
     if p not in seen and free(d,*p,extra=extra):seen.add(p);q.append(p)
   return seen
  assert tuple(route[-1]) not in reaches(gates)
  assert tuple(route[-1]) not in reaches(gates[1:])
  for i,p in enumerate(d['valve_approaches']):assert tuple(p) in reaches(gates[i:])
  d['gate_geometry_validation']=dict(closed_gates_disconnect=True,first_open_second_still_blocks=True,both_open_connect=True,opening_height=64)
 js(dest/'manifest.json',d);js(dest/'native/memory.json',d['streamed_tiles'])
 for state in ('closed','collapse','open'):
  # Reconstruct both real VDP palettes: scenery PAL3 and transparent objectives PAL1.
  composed=im.convert('RGBA')
  if gates:
   pal1=[tuple(round(v*7/255)*255//7 for v in rgb) for rgb in obj.PALETTE]
   def frame(raw,width,height,index):
    rgba=Image.new('RGBA',(width,height));pixels=rgba.load();at=index*width*height//2
    for tx in range(width//8):
     for ty in range(height//8):
      for yy in range(8):
       for xx in range(0,8,2):
        byte=raw[at];at+=1
        for dx,n in [(0,byte>>4),(1,byte&15)]:
         if n:pixels[tx*8+xx+dx,ty*8+yy]=(*pal1[n],255)
    return rgba
   vr=(GAME/'res/objectives/animations.bin').read_bytes()[4032*4:4800*4]
   for gx,gy,gw,gh in gates:
    if state!='open':composed.alpha_composite(frame(gate_data,64,64,0 if state=='closed' else 5),(gx+gw//2-32,gy+gh-64))
   for vx,vy in valves:composed.alpha_composite(frame(vr,32,32,0 if state=='closed' else 5),(vx-16,vy-16))
  buffer=io.BytesIO();composed.convert('RGB').save(buffer,format='PNG')
  emit(dest/f'complete-{state}-objectives.png',buffer.getvalue())
 print(key,len(tiles),'source tiles;',peak,'visible /456;',len(route),'NPC nodes;',d['geometry_validation']['free_positions'],'connected feet positions')
