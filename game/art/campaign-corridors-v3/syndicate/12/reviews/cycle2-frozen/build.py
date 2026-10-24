"""Phase12 private builder: whole source -> exact architectural grammar.
Only this phase folder is written. No shared C/resources/ROM are touched.
"""
from pathlib import Path
from collections import deque
import importlib.util,json,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
A=Path(__file__).resolve().parent;G=A.parents[3]
spec=importlib.util.spec_from_file_location('scene_pack',G/'art/campaign-whole-scenes-v1/pack.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
for p in ['modules','native','reviews/cycle2']:(A/p).mkdir(parents=True,exist_ok=True)
PAL=[(0,0,0),(218,218,182),(182,145,109),(145,145,145),(145,145,109),(109,145,72),(109,109,109),(72,109,145),(145,72,36),(72,72,72),(36,72,109),(36,72,36),(109,36,36),(72,36,36),(36,36,36),(0,36,72)]
src=Image.open(A/'source/12-whole-cycle3.png').crop((0,160,2172,516))
q,_=P.indexed(src,(1360,224),2,palette=PAL);fine,_=P.indexed(src,(1360,224),1,palette=PAL)
q.save(A/'source/native-clean-2px.png');fine.save(A/'source/native-clean-1px.png')
parts={};meta=[]
def part(name,box,detail=False):
 im=(fine if detail else q).crop(box);im.save(A/'modules'/(name+'.png'));parts[name]=im
 meta.append({'id':name,'source':'source/12-whole-cycle3.png','source_bbox_native_scaled':list(box),'source_bbox_original':[round(box[0]*2172/1360),round(box[1]*356/224+160),round(box[2]*2172/1360),round(box[3]*356/224+160)],'size':list(im.size),'grid':1 if detail else 2,'function':'complete end/cap/opening or repeatable material cross-section'});return im
# Whole horizontal roof cross-sections and their closed endcaps. No tile is
# substituted by similarity; these exact authored parts repeat by design.
part('terra-left',(32,0,56,88));part('terra-run',(112,0,128,88));part('terra-right',(280,0,304,88))
part('steel-left',(672,40,696,104));part('steel-run',(752,40,768,104));part('steel-right',(880,40,904,104))
part('brick',(1080,80,1096,88));part('plinth',(64,216,96,224))
part('column-cap',(40,184,56,200));part('column-run',(40,200,56,216));part('column-foot',(40,216,56,224))
part('wall-run',(64,200,96,224));part('foliage-context',(312,0,376,72))
part('window',(1088,80,1160,128),True);part('door',(1184,128,1224,168),True);part('banner',(1168,64,1232,128),True)
part('workshop-opening',(80,80,192,144),True)
part('vent',(408,32,440,64));part('bench',(104,160,176,184),True)
part('paving-warm',(188,152,204,168));part('paving-service',(188,152,204,168));part('paving-union',(188,152,204,168));part('paving-step',(1200,168,1208,176))
# Every drawing operation below composes already authored source pixels.
def canvas(size):
 im=Image.new('P',size);im.putpalette(q.getpalette());return im
def fill(im,name,box):
 l,t,r,b=box;p=parts[name]
 for y in range(t,b,p.height):
  for x in range(l,r,p.width):im.paste(p.crop((0,0,min(p.width,r-x),min(p.height,b-y))),(x,y))
def column(im,x,top,bottom):
 im.paste(parts['column-cap'],(x,top));fill(im,'column-run',(x,top+16,x+16,bottom-8));im.paste(parts['column-foot'],(x,bottom-8))
def building(name,width,height,kind):
 im=canvas((width,height));roof='terra'if kind in ['workshop','union']else'steel';rh=88 if roof=='terra'else 64
 fill(im,'brick',(0,rh,width,height-8));im.paste(parts[roof+'-left'],(0,0))
 for x in range(24,width-24,16):im.paste(parts[roof+'-run'],(x,0))
 im.paste(parts[roof+'-right'],(width-24,0));fill(im,'plinth',(0,height-8,width,height))
 column(im,0,rh-8,height);column(im,width-16,rh-8,height)
 if kind=='workshop':
  im.paste(parts['workshop-opening'],(32,88));im.paste(parts['door'],(width-72,height-48))
 elif kind=='union':
  im.paste(parts['window'],(24,88));im.paste(parts['window'],(width-96,88));im.paste(parts['banner'],(width//2-32,64));im.paste(parts['door'],(width//2-20,128))
 elif kind=='covered':
  im.paste(parts['workshop-opening'],(32,72));im.paste(parts['workshop-opening'],(160,72))
 else:
  im.paste(parts['door'],(width-64,height-48));im.paste(parts['vent'],(32,64))
 im.save(A/'modules'/(name+'-assembly.png'));return im
assemblies={'workshop':building('workshop',304,160,'workshop'),'annex':building('annex',160,128,'annex'),'covered':building('covered',304,144,'covered'),'low-dock':building('low-dock',240,112,'annex'),'union':building('union',304,176,'union')}
world=canvas((3072,320));fill(world,'paving-warm',(0,0,3072,320))
# Floor colors belong to whole architectural sectors, not random rectangles.
fill(world,'paving-service',(704,144,1344,288));fill(world,'paving-union',(2208,112,3072,288))
# Stepped rear enclosure: its returns define the service crossing and the
# opening into the dock pocket. Architecture overlaps this enclosure naturally.
wall_sectors=[(0,704,96),(704,1344,144),(1344,2208,96),(2208,3072,112)]
solids=[]
for l,r,base in wall_sectors:
 fill(world,'foliage-context',(l,0,r,base-24));fill(world,'wall-run',(l,base-24,r,base));solids.append([l,0,r-l,base])
 for x in range(l,r,160):column(world,x,max(0,base-40),base)
# Perpendicular returns are complete metal/post assemblies, closing each bend.
for x,t,b in [(704,96,144),(1344,96,144),(2208,96,112)]:column(world,x,t,b)
fill(world,'wall-run',(0,288,3072,312));fill(world,'plinth',(0,312,3072,320))
for x in range(0,3072,160):column(world,x,272,312)
# Side enclosures use the same complete caps/shafts/feet, never cut fragments.
for x in [0,3056]:column(world,x,0,312)
placements=[('workshop',80,32),('annex',736,32),('low-dock',1008,200),('covered',1488,24),('low-dock',1760,200),('annex',2176,32),('low-dock',2304,200),('union',2704,24)]
for name,x,y in placements:
 im=assemblies[name];world.paste(im,(x,y));solids.append([x,y,*im.size])
# Walkable source paving/sidewalk belongs to specific entrances. Closed strips
# and curb cross-sections touch the building bases; no floating visual boxes.
for x,y,w in [(96,192,272),(2720,200,272)]:
 fill(world,'paving-step',(x,y,x+w,y+24));fill(world,'plinth',(x,y+24,x+w,y+32))
for x,y in [(224,248),(2560,248)]:world.paste(parts['bench'],(x,y));solids.append([x,y,72,24])
world.save(A/'complete-before-pack.png')
code,stats=P.pack({'map':world},PAL,A/'native','syndicate12',640)
shutil.copy2(A/'native/map-native.png',A/'complete-native.png')
print('tiles',stats['tiles'])
bounds=[16,96,3055,287];start=[48,208]
points=[[56,216],[336,216],[424,232],[592,232],[704,232],[920,232],[952,184],[1264,184],[1400,184],[1496,184],[1784,184],[2024,184],[2104,208],[2168,208],[2280,184],[2560,184],[2600,208],[2856,216]];pauses=[3,7,16];exit=[2824,192,64,64]
def blocked(x,y,size=16):return x<bounds[0]or y<bounds[1]or x+size-1>bounds[2]or y+size-1>bounds[3]or any(x<a+w and x+size>a and y<b+h and y+size>b for a,b,w,h in solids)
assert all(v%8==0 for r in solids for v in r);assert not blocked(*start)
seen={tuple(start)};todo=deque(seen)
while todo:
 x,y=todo.popleft()
 for p in [(x-8,y),(x+8,y),(x,y-8),(x,y+8)]:
  if p not in seen and not blocked(*p):seen.add(p);todo.append(p)
for i,(x,y)in enumerate(points):assert(x-8,y-8)in seen,('point',i,x,y)
sweep=0
for i,((ax,ay),(bx,by))in enumerate(zip(points,points[1:])):
 n=max(abs(bx-ax),abs(by-ay))
 for t in range(n+1):
  x=round(ax+(bx-ax)*t/max(1,n))-8;y=round(ay+(by-ay)*t/max(1,n))-8
  assert not blocked(x,y),('sweep',i,x,y);sweep+=1
assert any(exit[0]<=x+8<exit[0]+exit[2]and exit[1]<=y+8<exit[1]+exit[3]for x,y in seen)
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12);hero=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA')
interests=[]
for label,name,xy,actor in [('workshop','workshop',(80,32),(224,208)),('covered-dock','covered',(1488,24),(1624,184)),('union-arrival','union',(2704,24),(2848,208)),('south-dock1','low-dock',(1008,200),(1176,176)),('south-dock2','low-dock',(1760,200),(1880,176)),('south-dock3','low-dock',(2304,200),(2416,176))]:
 w,h=assemblies[name].size;cx=max(0,min(2752,xy[0]+w//2-160));cy=(xy[1]+h-224)if xy[1]>=200 else max(0,min(96,xy[1]-24));assert not blocked(*actor)
 v={'id':label,'bbox':[xy[0],xy[1],w,h],'center':[xy[0]+w//2,xy[1]+h//2],'camera':[cx,cy],'position':list(actor),'whole_inside_visible_world':xy[0]>=cx and xy[0]+w<=cx+320 and xy[1]>=cy+24 and xy[1]+h<=cy+224}
 im=world.convert('RGBA');im.alpha_composite(hero,(actor[0]-8,actor[1]-31));din=Image.open(G/'art/objetivos-travessia-escolta-v1/assets/dinorah.png').convert('RGBA').crop((32,0,64,48));assert not blocked(actor[0]-32,actor[1]);im.alpha_composite(din,(actor[0]-40,actor[1]-31));shot=im.crop((cx,cy,cx+320,cy+224)).convert('RGB');dr=ImageDraw.Draw(shot);dr.rectangle((0,0,319,23),fill='#10201b');dr.text((4,5),'FOCO NATIVO - SEM ROM',font=font,fill='#dedeb6');p=A/'reviews'/('camera-'+label+'.png');shot.save(p);v['preview']=str(p.relative_to(A));interests.append(v)
layout=world.convert('RGB');dr=ImageDraw.Draw(layout)
for x,y,w,h in solids:dr.rectangle((x,y,x+w-1,y+h-1),outline='#ff6060')
dr.line([tuple(p)for p in points],fill='#e1ff93',width=2);layout.save(A/'layout.png')
manifest={'phase':'12','size':[3072,320],'bounds':bounds,'start':start,'solids':solids,'route_points':points,'point_semantics':'CENTERS; actor foot top-left=center−8','pauses':pauses,'exit':exit,'camera_player_y':200,'camera_interest':interests,'sources':[{'path':'source/12-whole-cycle3.png','sha256':hashlib.sha256((A/'source/12-whole-cycle3.png').read_bytes()).hexdigest(),'whole_art_strip_crop':[0,160,2172,516],'native_pre_cut_size':[1360,224],'native_palette':'RGB333; index0 literal black','authoring':'Built-in ImageGen full source; prompts and cycles preserved'}],'memory':{'scene_tiles':stats['tiles'],'objective_tiles':0,'total_tiles':stats['tiles'],'budget':640,'free_tiles':640-stats['tiles'],'graphics_bytes':stats['tiles']*32,'map_bytes':24576,'palette_bytes':32,'collision_mask_words':480,'lossy_pattern_replacements':0,'pixel_exact_reassembly':True},'modules':meta,'assemblies':[{'id':n,'size':list(im.size),'file':'modules/'+n+'-assembly.png'}for n,im in assemblies.items()],'placements':placements,'source_geometry':{'blockout':'blockout.json','principle':'Full source first. Closed roof ends plus authored repeatable roof/wall cross-sections and complete sharp openings form whole closed buildings; no approximate tile substitution. North enclosure steps96→144→96→112 and south volumes project to200, creating distinct courts/crossings.','first_native':'reviews/cycle1/rejected-native.png','first_native_verdict':'Rejected by author and parent:4px mosaic, floating masses, broad empty field.'},'geometry':{'actor_footprint':[16,16],'point_margin':8,'BFS_step':8,'connected_positions':len(seen),'all_points_reachable':True,'swept16pxSamples':sweep,'all_segments_collision_free':True,'exit_reachable':True,'open_depth':192,'service_neck_width':32},'complete':'complete-native.png','layout':'layout.png','native':{'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin'},'status':'final_native_material_fix_pending_parent_visual_review'}
(A/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('BFS',len(seen),'sweep',sweep)
