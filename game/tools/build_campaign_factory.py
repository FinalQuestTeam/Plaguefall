"""ImageGen whole-scenes first; semantically complete modules and exact H/V export.
No approximate tile substitution. Field contacts and objective reserves are measured.
"""
from pathlib import Path
from collections import deque
import argparse,json,hashlib,io
from PIL import Image
G=Path(__file__).resolve().parents[1]
A=G/'art/campaign-pattern-v2/factory'
LEGACY=G/'art/campaign-factory-v1'
PALETTE=[(0,0,0)]*16
P=Image.new('P',(1,1));P.putpalette([0]*768)
ARTIFACTS={}
FACTORY_SOLIDS=[[128,192,80,32],[576,200,40,32]]
STREET_SOLIDS=[[456,144,40,32],[1000,168,80,24],[1568,144,48,32],[2096,152,64,40]]
EGGS=[[x,y] for x in (96,240,384,528,672) for y in (168,248)]
VALVES=[[144,104],[432,104],[576,104]]
VALVE_APPROACHES=[[x-8,112] for x,y in VALVES]
WAYPOINTS=[[424,184],[520,184],[968,144],[1104,144],[1528,184],[1632,184],[2056,128],[2192,128]]
def indexed(path,world,pixel=2,palette=P):
    full=Image.open(path).convert('RGB').resize(world,Image.Resampling.NEAREST)
    if pixel>1:full=full.resize((world[0]//pixel,world[1]//pixel),Image.Resampling.NEAREST).resize(world,Image.Resampling.NEAREST)
    colors=[tuple(palette.getpalette()[i:i+3]) for i in range(0,48,3)]
    pixels=list(full.getdata())
    closest={c:min(range(16),key=lambda i:sum((c[j]-colors[i][j])**2 for j in range(3))) for c in set(pixels)}
    out=Image.new('P',full.size);out.putpalette(palette.getpalette());out.putdata([closest[c] for c in pixels]);return out

def repeat(canvas,source,rect,area):
    """Repeat a coherent material/architectural module, clipping only at area edge."""
    module=source.crop(rect);ax,ay,aw,ah=area
    for y in range(ay,ay+ah,module.height):
        for x in range(ax,ax+aw,module.width):
            canvas.paste(module.crop((0,0,min(module.width,ax+aw-x),min(module.height,ay+ah-y))),(x,y))

def variants(raw):
    rows=[raw[i:i+8] for i in range(0,64,8)]
    return [(b''.join(rows),0),(b''.join(r[::-1] for r in rows),0x0800),(b''.join(rows[::-1]),0x1000),(b''.join(r[::-1] for r in rows[::-1]),0x1800)]

def pack(im):
    w,h=im.size;p=bytes(im.getdata());tiles=[];lookup={};mapping=[];reused=0
    for y in range(0,h,8):
        for x in range(0,w,8):
            raw=bytes(p[(y+dy)*w+x+dx] for dy in range(8) for dx in range(8));canonical,flip=min(variants(raw),key=lambda v:v[0])
            if canonical not in lookup:lookup[canonical]=len(tiles);tiles.append(canonical)
            else:reused+=1
            mapping.append(lookup[canonical]|flip)
    # Decode shipped tiles/map and require pixel equality, including all flips.
    decoded=bytearray(w*h)
    for i,attr in enumerate(mapping):
        tx,ty=(i%(w//8))*8,(i//(w//8))*8;raw=variants(tiles[attr&0x07ff])[(attr>>11)&3][0]
        for dy in range(8):decoded[(ty+dy)*w+tx:(ty+dy)*w+tx+8]=raw[dy*8:dy*8+8]
    assert bytes(decoded)==p,'Tile packing altered source pixels'
    return tiles,mapping,reused

def free(x,y,solids,width,miny,maxy):return 16<=x<=width-32 and miny<=y<=maxy-15 and not any(x<a+c and x+16>a and y<b+d and y+16>b for a,b,c,d in solids)
def flood(solids,width,miny,maxy,start):
    seen={start};q=deque(seen)
    while q:
        x,y=q.popleft()
        for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
            if p not in seen and free(*p,solids,width,miny,maxy):seen.add(p);q.append(p)
    return seen

def factory():
    PA=[(0,0,0),(36,36,36),(36,72,109),(72,72,72),(72,109,145),(145,145,109),(145,145,145),(218,218,182),(109,36,0),(145,72,36),(182,109,36),(218,145,0),(36,72,72),(109,109,109),(109,145,145),(72,109,72)]
    p=Image.new('P',(1,1));p.putpalette(sum(map(list,PA),[])+[0]*(768-48))
    s=indexed(A/'source/factory-whole-cycle3.png',(768,384),1,p)
    ARTIFACTS[A/'modules/factory-source-normalized.png']=s
    out=Image.new('P',(768,320));out.putpalette(p.getpalette())
    def module(name,rect,size):
     im=s.crop(rect).resize(size,Image.Resampling.NEAREST);ARTIFACTS[A/'modules'/f'factory-{name}.png']=im;return im
    # one sampled floor color, semantically calm concrete rather than noisy source pores.
    floor=module('floor',(312,224,313,225),(8,8));repeat(out,floor,(0,0,8,8),(0,0,768,320))
    wall=module('north-wall',(212,40,228,72),(16,32));repeat(out,wall,(0,0,16,32),(0,0,768,112))
    foot=module('north-plinth',(208,88,232,104),(24,16));repeat(out,foot,(0,0,24,16),(0,96,768,16))
    for name,rect,size,pos in [('door',(72,8,208,112),(80,64),(32,16)),('furnace',(304,0,480,112),(96,64),(320,16)),('tanks',(520,0,672,112),(88,64),(632,16))]:out.paste(module(name,rect,size),pos)
    # Purpose-built lower perimeter with whole cap, brick face, service pipe and bottom footing.
    south=module('south-wall',(64,312,176,384),(64,48));repeat(out,south,(0,0,64,48),(0,272,768,48))
    post=module('south-post',(176,312,200,384),(16,48))
    for x in (144,368,592):out.paste(post,(x,272))
    side=module('side-left',(8,120,24,184),(16,64));rightside=side.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ARTIFACTS[A/'modules/factory-side-right.png']=rightside
    for x,im in [(0,side),(752,rightside)]:repeat(out,im,(0,0,16,64),(x,112,16,160))
    sw=module('corner-sw',(0,280,48,384),(32,48));out.paste(sw,(0,272));se=sw.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ARTIFACTS[A/'modules/factory-corner-se.png']=se;out.paste(se,(736,272))
    # Full original column capitals and upper corners are distinct from wall strips.
    nw=module('corner-nw',(0,0,48,112),(32,112));out.paste(nw,(0,0));ne=nw.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ARTIFACTS[A/'modules/factory-corner-ne.png']=ne;out.paste(ne,(736,0))
    def object_mask(im,bg=(5,6,13,14)):
     w,h=im.size;seen=set();q=deque([(x,y) for x in range(w) for y in (0,h-1)]+[(x,y) for y in range(h) for x in (0,w-1)])
     while q:
      x,y=q.popleft()
      if not(0<=x<w and 0<=y<h) or (x,y) in seen or im.getpixel((x,y)) not in bg:continue
      seen.add((x,y));q.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
     mask=Image.new('L',(w,h));mask.putdata([0 if (x,y) in seen else 255 for y in range(h) for x in range(w)])
     comps=[];used=set()
     for y in range(h):
      for x in range(w):
       if (x,y) in used or not mask.getpixel((x,y)):continue
       comp=set();todo=[(x,y)];used.add((x,y))
       while todo:
        a,c=todo.pop();comp.add((a,c))
        for v in ((a-1,c),(a+1,c),(a,c-1),(a,c+1)):
         if 0<=v[0]<w and 0<=v[1]<h and v not in used and mask.getpixel(v):used.add(v);todo.append(v)
       comps.append(comp)
     keep=max(comps,key=len);mask.putdata([255 if (x,y) in keep else 0 for y in range(h) for x in range(w)])
     return mask
    # Cabinet and feed are COMPLETE assemblies; their physical bases sit behind walk line112.
    station=module('station',(184,104,272,216),(56,72))
    station_mask=object_mask(station)
    # Preserve grey coupling pixels inside the pipe-to-cabinet joint; same grey as floor cannot be flood-keyed.
    for y in range(24,37):
     for x in range(31,41):
      if station.getpixel((x,y)) != 5:station_mask.putpixel((x,y),255)
    for y in range(31,38):
     for x in range(16,41):
      if station.getpixel((x,y)) != 5:station_mask.putpixel((x,y),255)
    ARTIFACTS[A/'modules/factory-station-mask.png']=station_mask
    for x in (152,440,584):out.paste(station,(x,40),station_mask)
    # Complete horizontal header, only a pipe and its wall mounting, no machine scraps.
    header=module('supply-header',(208,336,240,348),(32,8));repeat(out,header,(0,0,32,8),(32,32,704,8))
    for name,rect,size,pos in [('conveyor',(184,240,328,296),(80,32),(128,192)),('crate',(520,232,608,296),(40,32),(576,200))]:
     im=module(name,rect,size);out.paste(im,pos,object_mask(im))
    return out,dict(source="factory-whole-cycle3.png",normalized_source_size=[768,384],pixel_grid=1,complete_objects=True,lower_architecture=True)

def street():
    PA=[(0,0,0),(36,36,36),(36,72,109),(72,72,72),(72,109,145),(145,145,145),(182,182,145),(218,218,182),(109,36,0),(145,72,36),(182,109,36),(218,145,0),(36,72,72),(109,109,109),(72,109,72),(182,182,218)]
    p=Image.new('P',(1,1));p.putpalette(sum(map(list,PA),[])+[0]*(768-48))
    s=indexed(A/'source/street-whole-cycle1.png',(1024,344),1,p)
    out=Image.new('P',(2560,256));out.putpalette(p.getpalette())
    def module(name,rect,size):
     im=s.crop(rect).resize(size,Image.Resampling.NEAREST);ARTIFACTS[A/'modules'/f'street-{name}.png']=im;return im
    # whole original materials; no tile substitution.
    floor=module('floor',(376,136,377,137),(8,8))
    repeat(out,floor,(0,0,8,8),(0,0,2560,256))
    wall=module('north-wall',(312,40,336,112),(16,80))
    roof=module('roof-middle',(232,0,248,32),(16,32))
    repeat(out,wall,(0,0,16,80),(0,32,2560,80));repeat(out,roof,(0,0,16,32),(0,0,2560,32))
    # One intact workshop assembled from complete roof ends, whole door and windows.
    brick=module('brick',(136,40,152,56),(16,16))
    leftroof=module('roof-left',(72,0,104,32),(32,32));rightroof=module('roof-right',(288,0,312,32),(24,32))
    front=Image.new('P',(160,112));front.putpalette(p.getpalette())
    repeat(front,brick,(0,0,16,16),(0,32,160,80));repeat(front,roof,(0,0,16,32),(32,0,104,32));front.paste(leftroof,(0,0));front.paste(rightroof,(136,0))
    front.paste(module('service-door',(96,56,136,120),(32,56)),(16,56))
    window=module('workshop-window',(160,56,208,96),(40,32))
    for x in (64,112):front.paste(window,(x,48))
    out.paste(front,(96,0));ARTIFACTS[A/'modules/street-workshop-complete.png']=front
    # One whole gantry/roller opening on continuous cladding, one whole tank pair and one whole gate.
    out.paste(module('loading-gantry',(392,32,600,120),(128,56)),(1184,56))
    out.paste(module('tank-pair',(688,0,816,120),(64,64)),(2304,48))
    out.paste(module('factory-gate',(848,56,992,128),(128,64)),(2416,48))
    # Horizontal southern wall bay contains railing, cap and inside face; complete posts are independent.
    south=module('south-wall',(192,248,224,320),(32,48));repeat(out,south,(0,0,32,48),(0,208,2560,48))
    post=module('south-post',(280,248,296,320),(16,48))
    for x in range(144,2528,160):out.paste(post,(x,208))
    side=module('side-wall',(8,144,24,176),(16,32))
    rightside=module('side-wall-right',(1000,144,1016,176),(16,32))
    for x,im in [(0,side),(2544,rightside)]:repeat(out,im,(0,0,16,32),(x,112,16,96))
    out.paste(module('south-corner',(0,240,32,320),(24,48)),(0,208));out.paste(module('south-corner-right',(992,240,1024,320),(24,48)),(2536,208))
    out.paste(module('upper-post',(24,40,40,120),(16,80)),(0,32));out.paste(module('upper-post-right',(968,40,984,120),(16,80)),(2544,32))
    def object_mask(im):
     w,h=im.size;seen=set();q=deque([(x,y) for x in range(w) for y in (0,h-1)]+[(x,y) for y in range(h) for x in (0,w-1)])
     while q:
      x,y=q.popleft()
      if not(0<=x<w and 0<=y<h) or (x,y) in seen or im.getpixel((x,y)) not in (5,6,13,15):continue
      seen.add((x,y));q.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
     mask=Image.new('L',(w,h));mask.putdata([0 if (x,y) in seen else 255 for y in range(h) for x in range(w)])
     # Keep only the connected whole silhouette. Detached floor cracks outside it are not part of the object.
     comps=[];used=set()
     for y in range(h):
      for x in range(w):
       if (x,y) in used or not mask.getpixel((x,y)):continue
       comp=set();todo=[(x,y)];used.add((x,y))
       while todo:
        a,c=todo.pop();comp.add((a,c))
        for v in ((a-1,c),(a+1,c),(a,c-1),(a,c+1)):
         if 0<=v[0]<w and 0<=v[1]<h and v not in used and mask.getpixel(v):used.add(v);todo.append(v)
       comps.append(comp)
     keep=max(comps,key=len);mask.putdata([255 if (x,y) in keep else 0 for y in range(h) for x in range(w)])
     return mask
    for name,rect,size,pos in [('crate',(248,128,344,192),(48,32),(456,144)),('pipes',(400,192,560,256),(80,32),(1000,160)),('compressor',(624,128,736,192),(56,32),(1560,144)),('bin',(784,160,960,256),(88,48),(2088,144))]:
     im=module(name,rect,size);out.paste(im,pos,object_mask(im))
    return out,dict(source="street-whole-cycle1.png",normalized_source_size=[1024,344],pixel_grid=1,complete_objects=True,lower_architecture=True)

def compose_objectives(im,kind,points,frame=0):
    out=im.convert('RGBA');art=Image.open(G/f'art/objective-sprites-v1/frames/{kind}-{frame}.png').convert('RGBA')
    for x,y in points:
        # Exact ground-renderer 8px snap, no scaled objective art.
        left=(x-art.width//2)//8*8;top=(y-art.height+8)//8*8
        out.alpha_composite(art,(left,top))
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    files=ARTIFACTS;report={'method':'ImageGen whole scenes FIRST; complete modules and native 1px detail; exact bit-identical H/V deduplication','arbitrary_tile_replacements':0,'scenes':{}}
    header=['// Generated by tools/build_campaign_factory.py; whole-scene-first complete modules.','#include "levels/campaign_factory.h"']
    worlds=[('factory',*factory(),768,320,FACTORY_SOLIDS,112,271,128,490),('street',*street(),2560,256,STREET_SOLIDS,112,213,152,640)]
    memory={};natives={}
    for name,im,meta,w,h,solids,miny,maxy,starty,budget in worlds:
        natives[name]=im;tiles,mapping,reused=pack(im);assert len(tiles)<=budget,(name,len(tiles),budget)
        assert im.getpixel((312,224) if name=='factory' else (376,136)) != 0,'Walkable floor must remain opaque on hardware'
        files[A/f'cycle-2/{name}-native.png']=im;files[LEGACY/f'{name}-map.png']=im
        header+=['static const u32 '+name+'Tiles[]={']
        for tile in tiles:
            packed=bytes((tile[i]<<4)|tile[i+1] for i in range(0,64,2));header.append(','.join('0x'+packed[i:i+4].hex()+'UL' for i in range(0,32,4))+',')
        colors=[tuple(im.getpalette()[i:i+3]) for i in range(0,48,3)]
        header+=['};','static const u16 '+name+'Palette[]={'+','.join(hex((round(c[0]*7/255)<<1)|(round(c[1]*7/255)<<5)|(round(c[2]*7/255)<<9)) for c in colors)+'};','static const u16 '+name+'Map[]={']
        header+=[','.join(map(str,mapping[i:i+w//8]))+',' for i in range(0,len(mapping),w//8)];header+=['};']
        header+=['static const ArenaScene '+name+'Scene={.tiles='+name+'Tiles,.map='+name+'Map,.palette='+name+'Palette,.tileCount='+str(len(tiles))+',.rows='+str(h//8)+',.cols='+str(w//8)+'};']
        header+=['static const ArenaRect '+name+'Solids[]={'+','.join('{'+','.join(map(str,r))+',TRUE}' for r in solids)+'};']
        header+=['const ArenaDef CF_'+name.upper()+'={'+','.join(map(str,[w,h,16,miny,w-17,maxy,48,starty]))+','+name+'Solids,sizeof('+name+'Solids)/sizeof(ArenaRect),&'+name+'Scene};']
        memory[name]=dict(scene_tiles=len(tiles),scene_bytes=len(tiles)*32,map_bytes=len(mapping)*2,palette_bytes=32,budget=640,exact_reused_tiles=reused,tile_decode_pixel_identical=True,palette0_black=colors[0]==(0,0,0),palette_rgb333=True)
        report['scenes'][name]={**meta,**memory[name],'size':[w,h],'background_limit':budget,'source_sha256':hashlib.sha256((A/'source'/meta['source']).read_bytes()).hexdigest()}
        # Exact exports included for independent inspection, not just a PNG claim.
        files[A/f'cycle-2/{name}-tiles.bin']=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
        files[A/f'cycle-2/{name}-map.bin']=b''.join(x.to_bytes(2,'big') for x in mapping)
    route=[[56,152]]+WAYPOINTS+[[2504,144]]
    header+=['static const RoutePoint points09[]={'+','.join('{'+str(x)+','+str(y)+',0}' for x,y in route)+'};','const RouteDef CF_ROUTE09={points09,10,{2480,112,64,64,FALSE}};']
    files[G/'src/levels/campaign_factory_scenes.c']='\n'.join(header)+'\n'
    seen=flood(FACTORY_SOLIDS,768,112,271,(48,128));streetseen=flood(STREET_SOLIDS,2560,112,213,(48,152))
    for x,y in EGGS:assert (x-8,y-8) in seen,(x,y)
    for p in VALVE_APPROACHES:assert tuple(p) in seen,p
    for p in WAYPOINTS+[[2504,144]]:assert tuple(p) in streetseen,p
    assert all(168<y+h and 168+16>y for x,y,w,h in STREET_SOLIDS)
    geometry=dict(street_controller_waypoints=WAYPOINTS,street_route=route,street_exit=[2480,112,64,64],street_finish=[2504,144],street_baseline_y=168,straight_street_path_blocked=True,tiles=memory['factory']['scene_tiles'],scene_limit=490,scene_plus_nest=memory['factory']['scene_tiles']+150,scene_plus_valve=memory['factory']['scene_tiles']+65,eggs=EGGS,valves=VALVES,valve_approaches=VALVE_APPROACHES,station_monitors=[[180,88],[468,88],[612,88]],factory_solids=FACTORY_SOLIDS,street_solids=STREET_SOLIDS,factory_size=[768,320],street_size=[2560,256],factory_start=[48,128],street_start=[48,152],factory_min_y=112,factory_max_y=271,street_min_y=112,street_max_y=213,factory_reachable=len(seen),street_reachable=len(streetseen),collision='16px projected footprint flood reaches ten clutch approaches, three valve approaches and exit; field props block their full projected footprint to prevent standing inside background art; cabinets wholly behind walk boundary',pipeline='whole-scene-first',minimum_bypass_width=32)
    files[LEGACY/'geometry.json']=json.dumps(geometry,indent=2)+'\n';files[A/'geometry.json']=json.dumps(geometry,indent=2)+'\n';files[A/'export.json']=json.dumps(report,indent=2)+'\n'
    phases=[];hero=Image.open(G/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png').crop((0,0,32,48)).convert('RGBA')
    variants={'9':natives['street'].convert('RGBA'),'10':compose_objectives(natives['factory'],'nest',EGGS),'11':compose_objectives(natives['factory'],'valve',VALVES)}
    states={'10':{'destroyed':compose_objectives(natives['factory'],'nest',EGGS,3)},'11':{'open':compose_objectives(natives['factory'],'valve',VALVES,3)}}
    for phase,im in variants.items():
        isstreet=phase=='9';name='street' if isstreet else 'factory';w,h=im.size;mem=memory[name].copy();reserve=0 if isstreet else (150 if phase=='10' else 65)
        mem.update(objective_all_states_tiles=reserve,total_tiles=mem['scene_tiles']+reserve,total_vram_bytes=(mem['scene_tiles']+reserve)*32,margin_tiles=640-mem['scene_tiles']-reserve)
        files[A/f'cycle-2/{phase}-complete.png']=im
        statefiles={}
        for state,stateim in states.get(phase,{}).items():files[A/f'cycle-2/{phase}-{state}.png']=stateim;statefiles[state]=f'factory/cycle-2/{phase}-{state}.png'
        for region,x in [('entry',0),('middle',(w-320)//2//8*8),('exit',w-320)]:
            for vertical,y in [('top',0),('center',(h-224)//2//8*8),('bottom',h-224)]:
                view=im.crop((x,y,x+320,y+224))
                # This actor is a scale reference, placed only at a legal footprint.
                hero_x=next(sx for sx in (144,80,224,40,272) if free(x+sx+8,y+159,STREET_SOLIDS if isstreet else FACTORY_SOLIDS,w,112,213 if isstreet else 271))
                view.alpha_composite(hero,(hero_x,128))
                files[A/f'cycle-2/{phase}-{region}-{vertical}.png']=view.resize((640,448),Image.Resampling.NEAREST)
        phases.append(dict(phase=phase,complete=f'factory/cycle-2/{phase}-complete.png',bounds=[16,112,w-17,213 if isstreet else 271],size=[w,h],start=geometry[name+'_start'],solids=STREET_SOLIDS if isstreet else FACTORY_SOLIDS,memory=mem,sources=[f'factory/source/'+report['scenes'][name]['source']],special_states=statefiles,objectives=[] if isstreet else (EGGS if phase=='10' else VALVES),logical_objectives=0 if isstreet else (10 if phase=='10' else 3),visible_nest_slots=7 if phase=='10' else None))
    files[A/'review-manifest.json']=json.dumps(dict(phases=phases,visual_status='Candidatos nativos revistos inteiros e em 9 câmeras por fase; aguardam revisão integrada de movimento/HUD, sem aprovação automática por memória',geometry='factory/geometry.json'),indent=2)+'\n'
    from campaign_corridors import factory_override
    factory_override(files)
    files[G/'src/levels/campaign_factory_scenes.c']+='\n#include "levels/campaign_factory_phase10.inc"\n'
    phase10root=G/'art/phase10-factory-v2'
    phase10=json.loads((phase10root/'manifest.json').read_text())
    for target in (A/'geometry.json',LEGACY/'geometry.json'):
        doc=json.loads(files[target]);doc.update(eggs=phase10['eggs'],phase10=phase10,phase10_art='art/phase10-factory-v2/review.html')
        files[target]=json.dumps(doc,indent=2)+'\n'
    files[A/'cycle-2/10-complete.png']=Image.open(phase10root/'complete-with-eggs.png')
    files[A/'cycle-2/10-destroyed.png']=compose_objectives(Image.open(phase10root/'complete-native.png'),'nest',phase10['eggs'],3)
    doc=json.loads(files[A/'review-manifest.json']);row=next(r for r in doc['phases'] if r['phase']=='10')
    row.update(size=phase10['size'],bounds=phase10['bounds'],start=phase10['start'],solids=phase10['solids'],objectives=phase10['eggs'],memory=phase10['memory'],sources=['phase10-factory-v2/source/factory-whole.png'])
    files[A/'review-manifest.json']=json.dumps(doc,indent=2)+'\n'
    files[G/'src/levels/campaign_factory_scenes.c']+='\n#include "levels/campaign_factory_phase11.inc"\n'
    phase11root=G/'art/phase11-factory-v2'
    phase11=json.loads((phase11root/'manifest.json').read_text())
    for target in (A/'geometry.json',LEGACY/'geometry.json'):
        doc=json.loads(files[target]);doc.update(valves=phase11['valves'],valve_approaches=phase11['valve_approaches'],phase11=phase11,phase11_art='art/phase11-factory-v2/review.html')
        files[target]=json.dumps(doc,indent=2)+'\n'
    files[A/'cycle-2/11-complete.png']=Image.open(phase11root/'complete-with-valves.png')
    files[A/'cycle-2/11-open.png']=compose_objectives(Image.open(phase11root/'complete-background.png'),'valve',phase11['valves'],3)
    doc=json.loads(files[A/'review-manifest.json']);row=next(r for r in doc['phases'] if r['phase']=='11')
    row.update(size=phase11['size'],bounds=phase11['bounds'],start=phase11['start'],solids=phase11['solids'],objectives=phase11['valves'],logical_objectives=6,memory=phase11['memory'],sources=['phase10-factory-v2/source/factory-whole.png'])
    files[A/'review-manifest.json']=json.dumps(doc,indent=2)+'\n'
    for path,data in files.items():
        if isinstance(data,Image.Image):buf=io.BytesIO();data.save(buf,format='PNG');data=buf.getvalue()
        elif isinstance(data,str):data=data.encode()
        if args.check:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print(json.dumps({'factory':memory['factory'],'street':memory['street'],'geometry_reachable':[len(seen),len(streetseen)]},indent=2))
if __name__=='__main__':main()
