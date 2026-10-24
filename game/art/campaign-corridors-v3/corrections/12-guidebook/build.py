"""Isolated style proposal12. Writes ONLY this directory; active scene untouched."""
from pathlib import Path
import json,hashlib,importlib.util,shutil,os
from PIL import Image,ImageDraw,ImageFont
A=Path(__file__).resolve().parent;G=A.parents[3];BASE=G/'art/campaign-corridors-v3/syndicate/12';OLD=G/'art/campaign-pattern-v2/early/01-courtyard/modules';KIT=G/'art/campaign-corridors-v3/corrections/9-guidebook/modules'
s=importlib.util.spec_from_file_location('pack',G/'art/campaign-whole-scenes-v1/pack.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
for n in ['modules','native','reviews']:(A/n).mkdir(exist_ok=True)
PAL=[(0,0,0),(218,218,182),(218,182,109),(182,145,72),(145,109,72),(109,72,36),(182,72,36),(109,36,36),(36,36,36),(72,72,72),(109,109,109),(145,145,145),(36,36,72),(36,72,109),(72,109,145),(72,109,72)]
active=json.loads((BASE/'manifest.json').read_text());trace=[]
def source(name,path,box=None):
 im=Image.open(path).convert('RGBA');im=im.crop(box)if box else im
 im.save(A/'modules'/(name+'-source.png'));trace.append({'id':name,'path':os.path.relpath(path,A),'game_path':str(path.relative_to(G)),'bbox_xyxy':list(box)if box else None,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()});return im
work=source('legacy-workshop',A/'source/existing-workshop-rgba.png')
trace[-1]['legacy_parent']='art/phase03-street-v2/source/street-kit.png; cell443,0,887,443; normalized whole128x128'
parts={}
for n,file in [('wall','lower-wall.png'),('post','lower-post.png'),('vegetation','upper-vegetation.png'),('bench','bench.png')]:parts[n]=source(n,OLD/file)
parts['floor']=source('floor',G/'art/phase04-tunnels-v1/map-native.png',(64,112,96,144))
parts['rear-earth']=source('rear-earth',OLD/'floor.png')
# Sample only unobstructed pale plaster; no curb/brick diagonal is tiled.
parts['plaster']=Image.new('RGBA',(16,16))
for box,xy in [((64,80,72,88),(0,0)),((88,80,96,88),(8,0)),((116,76,124,84),(0,8)),((184,72,192,80),(8,8))]:
 patch=source('plaster-'+str(xy[0])+'-'+str(xy[1]),G/'art/phase01-courtyard-v2/intact-native.png',box);parts['plaster'].alpha_composite(patch,xy)
parts['plaster'].save(A/'modules/plaster-material.png')
# Existing1px projected openings remain whole. Only small doors/bays are
# normalized as separate complete pieces; no complete building is reshaped.
for n in ['window','door','banner','vent']:
 parts[n]=source(n,BASE/'modules'/(n+'.png'))
parts['small-door']=parts['door'].resize((32,32),Image.Resampling.NEAREST)
parts['whole-bay']=source('whole-bay',A/'source/existing-workshop-rgba.png',(8,64,120,128)).resize((70,40),Image.Resampling.NEAREST)
parts['industrial-wall']=source('industrial-wall',G/'art/phase04-tunnels-v1/map-native.png',(80,0,144,80))
parts['header']=source('header',G/'art/campaign-pattern-v2/factory/modules/factory-supply-header.png')
for n,box in [('steel-left',(672,56,696,104)),('steel-run',(752,56,768,104)),('steel-right',(880,56,904,104))]:
 parts[n]=source(n,BASE/'source/native-clean-1px.png',box)
parts['roof-left']=work.crop((0,0,24,64));parts['roof-run']=work.crop((40,0,56,64));parts['roof-right']=work.crop((104,0,128,64))
# Preserve ridge/eave/endcaps. Extend the plane from an authored8px band,
# as a roof canvas; this never rescales the building or its closed footings.
def extend_roof(im,h,steel=False):
 cap=8 if steel else 16;bottom=40 if steel else 48
 out=Image.new('RGBA',(im.width,h));out.alpha_composite(im.crop((0,0,im.width,cap)),(0,0))
 band=im.crop((0,cap,im.width,bottom))
 for y in range(cap,h-cap,band.height):out.alpha_composite(band.crop((0,0,im.width,min(band.height,h-cap-y))),(0,y))
 out.alpha_composite(im.crop((0,bottom,im.width,bottom+cap)),(0,h-cap));return out
floor=parts['floor'].convert('RGB');road_base=Image.new('RGBA',(3072,320),(109,109,109,255))
def repeat(im,p,box):
 l,t,r,b=box
 for y in range(t,b,p.height):
  for x in range(l,r,p.width):im.alpha_composite(p.crop((0,0,min(p.width,r-x),min(p.height,b-y))),(x,y))
repeat(road_base,parts['floor'],(0,0,3072,320))
world=road_base.copy()
sectors=[(0,704,96),(704,1344,144),(1344,2208,96),(2208,3072,112)]
for l,r,b in sectors:repeat(world,parts['rear-earth'],(l,0,r,b-32))
# Shared industrial wall64x80is complete; the32x8header runs on its wall
# mount at one constant height. Both remain wholly within old blocked ground.
repeat(world,parts['industrial-wall'],(0,0,3072,80));repeat(world,parts['header'],(0,40,3072,48))
for l,r,b in sectors:
 repeat(world,parts['wall'],(l,b-32,r,b))
 for x in range(l,r,160):world.alpha_composite(parts['post'],(x,b-32))
repeat(world,parts['wall'],(0,288,3072,320))
for x in range(0,3072,160):world.alpha_composite(parts['post'],(x,288))
# Complete wall returns stay inside the already blocked northern sectors.
for x,t,b in[(704,96,144),(1344,96,144),(2208,96,112)]:repeat(world,parts['wall'],(x,t,x+16,b))
roof_heights={'workshop':104,'annex':88,'covered':96,'low-dock':72,'union':120}
sizes={a['id']:a['size']for a in active['assemblies']};assemblies={}
for name,(w,h)in sizes.items():
 rh=roof_heights[name];im=Image.new('RGBA',(w,h))
 repeat(im,parts['plaster'],(0,rh,w,h-8));repeat(im,parts['wall'].crop((0,24,16,32)),(0,h-8,w,h))
 steel=name!='union';prefix='steel' if steel else 'roof'
 im.alpha_composite(extend_roof(parts[prefix+'-left'],rh,steel),(0,0));repeat(im,extend_roof(parts[prefix+'-run'],rh,steel),(24,0,w-24,rh));im.alpha_composite(extend_roof(parts[prefix+'-right'],rh,steel),(w-24,0))
 if name=='union':
  im.alpha_composite(parts['window'],(24,h-56));im.alpha_composite(parts['window'],(w-96,h-56));im.alpha_composite(parts['door'],(w//2-20,h-48));im.alpha_composite(parts['banner'],(w//2-32,64))
 elif name=='workshop':
  im.alpha_composite(parts['whole-bay'],(32,h-48));im.alpha_composite(parts['door'],(w-72,h-48))
 elif name=='covered':
  im.alpha_composite(parts['whole-bay'],(40,h-48));im.alpha_composite(parts['whole-bay'],(176,h-48))
 else:
  im.alpha_composite(parts['small-door'],(w-56,h-40));im.alpha_composite(parts['vent'].resize((24,24),Image.Resampling.NEAREST),(32,h-32))
 im.save(A/'modules'/(name+'-assembly-rgba.png'));assemblies[name]=im
for n,x,y in active['placements']:world.alpha_composite(assemblies[n],(x,y))
# Benches are the whole approved native72x40piece with the same248..272foot.
for x,y in[(224,232),(2560,232)]:world.alpha_composite(parts['bench'],(x,y))
# Source-ground support strips have sparse1px grain, no long flat rectangle.
world=world.convert('RGB');world.save(A/'complete-before-pack.png');q,_=P.indexed(world,world.size,1,palette=PAL);q.save(A/'complete-indexed.png');_,stats=P.pack({'map':q},PAL,A/'native','guidebook12',640);shutil.copy2(A/'native/map-native.png',A/'complete-native.png')
# Exactly the active geometry/route/roster/story; isolated palette/art proposal.
m=json.loads(json.dumps(active));m['memory']={'scene_tiles':stats['tiles'],'objective_tiles':0,'total_tiles':stats['tiles'],'budget':640,'free_tiles':640-stats['tiles'],'graphics_bytes':(A/'native/tiles.bin').stat().st_size,'map_bytes':(A/'native/map.bin').stat().st_size,'palette_bytes':(A/'native/palette.bin').stat().st_size,'pixel_exact_reassembly':True,'lossy_pattern_replacements':0};m['native']={'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin'};m['complete']='complete-native.png';m['sources']=trace;m['modules']=trace;m['assemblies']=[{'id':n,'size':list(im.size),'file':'modules/'+n+'-assembly-rgba.png','roof_height':roof_heights[n]}for n,im in assemblies.items()];m['source_geometry']={'principle':'Existing approved kit parts; whole roof canvases with native material runs, whole openings, original footings. No whole-building reshape.','active_geometry_origin':str(BASE.relative_to(G))};[it.pop('preview',None)for it in m['camera_interest']];m['status']='isolated_candidate_requires_parent_and_user_review';m['style_changes']={'roof_heights':roof_heights,'method':'Whole roof canvases: original ridge/eave/caps plus repeated native material band; separate whole openings preserved. No whole-building reshape.','floor':'Existing phase04 tunnel32x32patch,1px grid, palette normalization only.','roof_materials':'Unionhall terracotta; all other families steel fine1px crops at y56..104 (back wall y40..56 excluded).','perimeter':'Existing R04 complete64x80industrial wall with shared factory10header at constant y40; wholly inside existing blocked perimeter.','geometry':'Bounds,solids,start,route,exit,pauses and camera metadata retained byte-for-byte as values.'};(A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
hero=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA');din=Image.open(G/'art/objetivos-travessia-escolta-v1/assets/dinorah.png').convert('RGBA').crop((32,0,64,48));font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
# Normal active camera target with close escort and the existing focus rules.
# These are native simulations, not emulator screenshots or new engine logic.
poses=[('entry',[224,208]),('service-bend',[1112,176]),('covered',[1624,184]),('dock-and-annex',[2048,176]),('union',[2848,200])];cams=[]
for n,(px,py)in poses:
 cx=px-168;cy=py-200;focus=None;nearest=65
 for it in active['camera_interest']:
  ax,ay,aw,ah=it['bbox'];dx=max(ax-px-8,px+8-ax-aw,0);dy=max(ay-py-8,py+8-ay-ah,0)
  if dx+dy<nearest:nearest=dx+dy;focus=(ax,ay,aw,ah)
 if focus:
  ax,ay,aw,ah=focus;cx=max(ax+aw-320,min(cx,ax));cy=max(ay+ah-224,min(cy,ay-24))
 cx=max(px+24-320,px-32+24-320,min(cx,px-8,px-40));cx=max(0,min(2752,cx));cy=max(py+8-224,min(cy,py-55));cy=max(0,min(96,cy));im=q.convert('RGBA');im.alpha_composite(hero,(px-8,py-31));im.alpha_composite(din,(px-40,py-31));im=im.crop((cx,cy,cx+320,cy+224)).convert('RGB');dr=ImageDraw.Draw(im);dr.rectangle((0,0,319,23),fill='#151e20');dr.text((4,5),'PROPOSTA NATIVA12 - SEM ROM',font=font,fill='#dedeb6');im.save(A/'reviews'/('camera-'+n+'.png'));cams.append({'id':n,'feet':[px,py],'camera':[cx,cy],'preview':'reviews/camera-'+n+'.png','camera_model':'current normal ARENA rules with close escort; offline target simulation only'})
(A/'reviews/cameras.json').write_text(json.dumps(cams,indent=2)+'\n');m['proposal_previews']=cams;(A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('tiles',stats['tiles'])
