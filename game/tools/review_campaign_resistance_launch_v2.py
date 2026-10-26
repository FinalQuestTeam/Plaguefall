"""Whole native pattern-v2 review. No compilation, emulator or shared edits.
Composes the exported objective/actor pixels at runtime coordinates, records
16x16-foot reachability and keeps all diagnostic boxes out of the native maps.
"""
from pathlib import Path
from collections import deque
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
G=Path(__file__).resolve().parents[1]; BASE=G/'art/campaign-pattern-v2'
FONT=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12)

def read(p):return json.loads(p.read_text())
def overlay(out,name,cx,cy,frame=0,ground=True):
 p=G/f'art/objective-sprites-v1/frames/{name}-{frame}.png';im=Image.open(p).convert('RGBA');x=cx-im.width//2;y=cy-im.height+8
 if ground:x=x//8*8;y=y//8*8
 out.alpha_composite(im,(x,y));b=im.getchannel('A').getbbox()
 return {'asset':name,'frame':frame,'center':[cx,cy],'canvas':[x,y,*im.size],'ink_bbox':[x+b[0],y+b[1],x+b[2],y+b[3]],'ground_snapped_8px':ground,'source':str(p.relative_to(G))}

def reachable(bounds,solids,start):
 l,t,r,b=bounds
 def blocked(x,y):return x<l or y<t or x+15>r or y+15>b or any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h in solids)
 assert not blocked(*start),('blocked start',start)
 seen={tuple(start)};todo=deque(seen)
 while todo:
  x,y=todo.popleft()
  for p in [(x-8,y),(x+8,y),(x,y-8),(x,y+8)]:
   if p not in seen and not blocked(*p):seen.add(p);todo.append(p)
 return seen

def inspect_access(ph,bounds,solids,start,geo):
 seen=reachable(bounds,solids,start);checks=[]
 def test(name,pred):
  candidates=[p for p in seen if pred(p[0]+8,p[1]+8)];assert candidates,(ph,name,'unreachable');checks.append({'name':name,'reachable_samples':len(candidates),'example_feet':list(min(candidates))})
 if ph=='7':
  for i,(x,y) in enumerate(geo['cargo']):
   test('cargo-'+str(i+1)+'-front',lambda a,b,x=x,y=y:abs(a-x)<=24 and 8<=b-y<=32)
   test('cargo-'+str(i+1)+'-pickup',lambda a,b,x=x,y=y:abs(a-x-24)<=22 and abs(b-y-16)<=22)
  test('depot-delivery',lambda a,b:abs(a-geo['depot'][0])<=22 and abs(b-geo['depot'][1])<=22)
 elif ph=='8':
  for i,(x,y)in enumerate(geo['transmitters']):test('transmitter-'+str(i+1),lambda a,b,x=x,y=y:abs(a-x-8)<=48 and abs(b-y-8)<=48)
 elif ph=='14':
  for i,(x,y)in enumerate(geo['machines']):test('generator-'+str(i+1)+'-front',lambda a,b,x=x,y=y:abs(a-x)<=28 and 8<=b-y<=40)
 elif ph in ('15','16'):
  test('console-south-edge',lambda a,b:200<=a<=312 and 224<=b<=240)
  test('console-west-edge',lambda a,b:184<=a<=192 and 152<=b<=216)
  test('console-east-edge',lambda a,b:320<=a<=336 and 152<=b<=216)
 return {'footprint':[16,16],'step_pixels':8,'reachable_grid_positions':len(seen),'checks':checks,'method':'Axis-aligned collision at runtime bounds and whole solids; dynamic case bases included until collection. This is geometry verification, not an emulator playtest.'}

rg=read(BASE/'resistance/geometry.json');lg=read(BASE/'launch/geometry.json')
hero=Image.open(BASE/'routes/review-evidence/damiao-production-frame.png').convert('RGBA')
boss=Image.open(G/'art/cangaco-insects-sized-v3/enemies/boss/boss.png').convert('RGBA').crop((0,0,48,48))
rows={'resistance':[],'launch':[]}
for ph in ['7','8','13A','13B','14','15','16']:
 group='resistance' if ph in ['7','8','13A','13B']else'launch';A=BASE/group
 for folder in ['complete','layouts','camera-previews','reviews']:(A/folder).mkdir(exist_ok=True)
 if ph=='8':
  urban=read(G/'art/phase08-urban-v1/manifest.json');bg=G/'art/phase08-urban-v1/complete-background.png';bounds=urban['bounds'];solids=[r[:4] for r in urban['solids']];start=urban['start'];source=G/'art/phase07-urban-v2/source/07-urban-whole.png';tiles=560;reserve=76
 elif ph=='7':
  bg=A/'native/favela/map-native.png';bounds=rg['favela_bounds'];solids=rg['favela_solids']+(rg['cargo_solids']if ph=='7'else[]);start=[80,176];source=A/'source/07-08-favela-cycle3.png';tiles=rg['favela_tiles'];reserve=74 if ph=='7'else 96
 elif ph in ['13A','13B']:
  bg=A/f'native/union/{"alive"if ph=="13A"else"dead"}-native.png';bounds=rg['union_bounds'];solids=rg['union_solids'];start=[280,168];source=A/('source/13A-union.png'if ph=='13A'else'source/13B-union-memorial.png');tiles=rg['union_tiles'];reserve=0
 else:
  bg=A/f'native/{"fire"if ph=="16"else"normal"}/map-native.png';bounds=lg['bounds'];solids=lg['solids'];start=lg['start'];source=A/('source/15-16-shipyard-ignition.png'if ph=='16'else'source/14-16-shipyard.png');tiles=lg['normal_tiles'];reserve=151
 out=Image.open(bg).convert('RGBA');objs=[]
 def add(name,x,y,frame=0,ground=True):objs.append(overlay(out,name,x,y,frame,ground))
 if ph=='7':
  for x,y in rg['cargo']:add('cargo',x,y)
  add('cargo',*rg['depot'],5)
 if ph=='8':
  for x,y in urban['targets']:add('transmitter',x+8,y-8,2,False)
 if ph in ['14','15','16']:
  for x,y in lg['machines']:add('generator',x,y,0 if ph=='14'else 3)
  if ph in ['15','16']:add('radio',*lg['radio'],2 if ph=='15'else 4)
 if ph=='16':out.alpha_composite(boss,(140,112));objs.append({'asset':'boss','canvas':[140,112,48,48],'representative_spawn_pose':True})
 dest=A/f'complete/{ph}-complete.png';out.convert('RGB').save(dest)
 layout=out.convert('RGB');draw=ImageDraw.Draw(layout);draw.rectangle(bounds,outline='#33ee88',width=2)
 for x,y,w,h in solids:draw.rectangle((x,y,x+w-1,y+h-1),outline='#ff5555')
 draw.rectangle((start[0],start[1],start[0]+15,start[1]+15),outline='#00ddff',width=2);layout.save(A/f'layouts/{ph}.png')
 specials=[]
 if ph=='14':
  im=Image.open(bg).convert('RGBA')
  for x,y in lg['machines']:overlay(im,'generator',x,y,3)
  p=A/'complete/14-on-complete.png';im.convert('RGB').save(p);specials.append({'label':'Cinco máquinas ligadas','complete':str(p.relative_to(G))})
 if ph=='15':
  im=Image.open(A/'native/fire/map-native.png').convert('RGBA')
  for x,y in lg['machines']:overlay(im,'generator',x,y,3)
  overlay(im,'radio',*lg['radio'],3);p=A/'complete/15-fire-complete.png';im.convert('RGB').save(p);specials.append({'label':'Ignição, cinco geradores preservados','complete':str(p.relative_to(G))})
 # These are honest native composition previews. They do NOT claim to be
 # emulator captures: HUD is a neutral band, actor pixels are production art.
 walkable=reachable(bounds,solids,start)
 w,h=out.size;camera_positions=[(max(0,min(w-320,start[0]+8-160)),max(0,min(h-224,start[1]+8-112))), (max(0,(w-320)//2),0),(max(0,(w-320)//2),h-224)]
 cameras=[]
 for i,(cx,cy)in enumerate(camera_positions):
  im=out.copy();pos=start if i==0 else ((w//2-8,160)if i==1 else(w//2-8,bounds[3]-23));pos=min(walkable,key=lambda p:abs(p[0]-pos[0])+abs(p[1]-pos[1]));im.alpha_composite(hero,(pos[0]-8,pos[1]-31))
  shot=im.crop((cx,cy,cx+320,cy+224)).convert('RGB');dr=ImageDraw.Draw(shot);dr.rectangle((0,0,319,23),fill='#152623');dr.text((5,5),'PREVIEW NATIVO - HUD RESERVADO',font=FONT,fill='#dedeb6');p=A/f'camera-previews/{ph}-{i}.png';shot.save(p);cameras.append({'path':str(p.relative_to(G)),'camera':[cx,cy],'actor_ground_top_left':list(pos),'emulator_capture':False})
 access=inspect_access(ph,bounds,solids,start,{'transmitters':urban['targets']} if ph=='8' else rg if group=='resistance'else lg)
 row={'phase':ph,'size':list(out.size),'bounds':bounds,'solids':solids,'start':start,'complete':str(dest.relative_to(G)),'background':str(bg.relative_to(G)),'special_states':specials,'memory':{'scene_tiles':tiles,'reserved_objective_tiles':reserve,'total_reserved_tiles':tiles+reserve,'limit':640,'margin_tiles':640-tiles-reserve,'tile_bytes':tiles*32,'map_bytes':out.width*out.height//32,'palette_bytes':32,'exact_reconstruction':True,'lossy_tile_replacements':0},'source':str(source.relative_to(G)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'palette':{'index0':[0,0,0],'format':'RGB333','palette_file':str(bg.with_name('palette.bin').relative_to(G))},'objects':objs,'layout':str((A/f'layouts/{ph}.png').relative_to(G)),'camera_previews':cameras,'access':access,'runtime_verification':'Pending parent integrated build; no new ROM compiled in this subtask.'}
 rows[group].append(row)
for group,phases in rows.items():
 (BASE/group/'manifest.json').write_text(json.dumps({'pattern':'phase01-pattern-v1/workflow.json','whole_image_first':True,'composition_previews_are_not_emulator_captures':True,'phases':phases},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({group:{r['phase']:{'tiles':r['memory']['total_reserved_tiles'],'reachable':r['access']['reachable_grid_positions']}for r in v}for group,v in rows.items()}))
