from pathlib import Path
from PIL import Image,ImageDraw
import json,math,collections
ROOT=Path('/Users/fabiocantarimmelo/Workspace/RedRex/MegaDrive/game/art/campaign-corridors-v3/sewers')
S={
'6A':{'solids':[[320,80,240,64,True],[576,80,224,128,False],[384,248,192,72,False],[864,192,224,128,False],[1328,168,144,112,True],[1744,80,304,120,True],[2144,216,320,104,False]],'route_points':[[48,200],[264,200],[352,200],[520,200],[560,232],[744,232],[832,232],[832,152],[1120,152],[1288,128],[1504,128],[1664,168],[1712,232],[2080,232],[2112,176],[2400,176],[2520,200],[2784,200],[3016,176]],'pauses':[4,9,15],'sectors':[{'name':'Cisterna de entrada','rect':[24,80,552,216]},{'name':'Canal em curva e ponte','rect':[576,80,512,216]},{'name':'Câmara de manutenção','rect':[1088,80,1056,216]},{'name':'Abrigo e escada','rect':[2144,80,904,216]}],'camera_interest':[{'name':'Arco e cisterna','bbox':[32,24,176,144]},{'name':'Curva e ponte','bbox':[560,144,288,144]},{'name':'Bomba completa','bbox':[1312,144,176,144]},{'name':'Escada de chegada','bbox':[2896,24,152,160]}]},
'6B':{'solids':[[320,80,320,64,True],[128,256,320,64,False],[640,224,224,96,False],[984,24,32,112,True],[952,168,32,152,True],[1376,184,160,112,True],[1568,80,224,64,True],[1792,264,192,56,False],[2104,24,32,192,True],[2072,248,32,72,True],[2304,216,320,104,False],[2528,80,224,48,True]],'route_points':[[48,200],[264,200],[352,200],[600,184],[784,184],[920,160],[936,152],[976,152],[1032,152],[1192,152],[1328,152],[1512,152],[1552,152],[1552,200],[1624,200],[1896,216],[2040,240],[2056,232],[2096,232],[2152,232],[2240,176],[2448,176],[2696,176],[2864,200],[3016,176]],'pauses':[5,10,16,22],'gates':[[960,112,32,64],[2080,192,32,64]],'valves':[[920,128],[2040,208]],'valve_approaches':[[920,160],[2040,240]],'gate_shot_approaches':[[904,144],[2024,224]],'sectors':[{'name':'Cisterna danificada','rect':[24,80,808,216]},{'name':'Câmara de pressão alta','rect':[832,80,384,216]},{'name':'Bacia de bombas e desvio','rect':[1216,80,736,216]},{'name':'Câmara de pressão baixa e abrigo','rect':[1952,80,1096,216]}],'camera_interest':[{'name':'Câmara de pressão1 inteira','bbox':[848,48,224,224]},{'name':'Ilha de bombas','bbox':[1360,136,192,176]},{'name':'Câmara de pressão2 inteira','bbox':[1968,96,224,200]},{'name':'Escada abrigo','bbox':[2896,24,152,160]}]}}
for phase,d in S.items():
 d.update(size=[3072,320],bounds=[24,80,3047,295],start=[48,200],exit=[2976,152,64,64],route_points_are='centers',footprint=[16,16],route_clearance=8,gates=d.get('gates',[]),valves=d.get('valves',[]))
 def free(x,y,extra=(),margin=8):
  r=8+margin;return 24<=x-r and x+r<=3048 and 80<=y-r and y+r<=296 and not any(x-r<rx+rw and x+r>rx and y-r<ry+rh and y+r>ry for rx,ry,rw,rh,*_ in d['solids']+list(extra))
 count=0
 for a,b in zip(d['route_points'],d['route_points'][1:]):
  n=math.ceil(math.dist(a,b))
  for i in range(n+1):
   x,y=[a[k]+(b[k]-a[k])*i/n for k in [0,1]];assert free(x,y),(phase,'route',a,b,x,y);count+=1
 def bfs(extra=()):
  q=collections.deque([tuple(d['start'])]);seen=set()
  while q:
   x,y=q.popleft()
   if (x,y)in seen or not free(x,y,extra):continue
   seen.add((x,y));q.extend([(x+8,y),(x-8,y),(x,y+8),(x,y-8)])
  return seen
 seen=bfs();goal=tuple(d['route_points'][-1]);assert goal in seen,(phase,'goal')
 if phase=='6B':
  assert goal not in bfs(d['gates']);assert goal not in bfs(d['gates'][1:]);assert all(free(*v)for v in d['valve_approaches']+d['gate_shot_approaches'])
 d['geometry_checks']={'swept_16px_footprint_with_8px_margin':count,'bfs_reachable_centers':len(seen),'arrival_connected':True,'closed_gates_disconnect':phase=='6B'}
 p=ROOT/phase;p.mkdir(exist_ok=True);(p/'blockout.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 im=Image.new('RGB',(3072,368),'#091927');r=ImageDraw.Draw(im);r.rectangle((24,80,3047,295),fill='#b2ac83')
 for x,y,w,h,vertical in d['solids']:r.rectangle((x,y,x+w-1,y+h-1),fill='#59644f'if vertical else'#1b5062',outline='#d8d1a4')
 for x,y,w,h in d['gates']:r.rectangle((x,y,x+w-1,y+h-1),fill='#b96836',outline='#ffffbb')
 for x,y in d['valves']:r.ellipse((x-6,y-6,x+6,y+6),fill='#c32727')
 r.line([tuple(v)for v in d['route_points']],fill='#f6e8b6',width=2)
 for i,(x,y)in enumerate(d['route_points']):r.ellipse((x-3,y-3,x+3,y+3),fill='#7cffc4');r.text((x+4,y+4),str(i),fill='white')
 for region in d['sectors']:
  x,y,w,h=region['rect'];r.text((x+8,332),region['name'],fill='white');r.line((x,324,x,364),fill='#d8d1a4')
 r.text((8,8),phase+' LOGICAL BLOCKOUT | floor / visible vertical stone masses / contained water | route centers+8pxmargin',fill='white');im.save(p/'blockout.png');print(phase,d['geometry_checks'])
