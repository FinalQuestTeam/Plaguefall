"""Whole-source early campaign rebuild. Exact native reuse, no fuzzy tile swaps."""
from pathlib import Path
from PIL import Image,ImageOps
from collections import deque,Counter
import sys,json,struct,re,shutil
E=Path(__file__).resolve().parent;G=E.parents[2];S=G/'src/levels'
sys.path.insert(0,str(G/'art/campaign-whole-scenes-v1'))
from pack import indexed,pack,c_array
legacy=G/'art/campaign-early-v1'
palwords=struct.unpack('>16H',(G/'res/courtyard/palette.bin').read_bytes())
cp=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in palwords]
geom={};modules={}
def new(size,pal,color):
    im=Image.new('P',size,color);im.putpalette(sum(map(list,pal),[])+[0]*720);return im
def nearest(pal,rgb):return min(range(1,16),key=lambda i:sum((pal[i][k]-rgb[k])**2 for k in range(3)))
def idx(im,pal):return indexed(im,im.size,1,palette=pal)[0]
def repeat(out,part,rect):
    x,y,w,h=rect
    for yy in range(y,y+h,part.height):
        for xx in range(x,x+w,part.width):out.paste(part.crop((0,0,min(part.width,x+w-xx),min(part.height,y+h-yy))),(xx,yy))
def cut(im,box,size=None):
    part=im.crop(box)
    return part.resize(size,Image.Resampling.NEAREST) if size else part
def mask(im,bg=None,largest=False):
    bg={Counter(im.getdata()).most_common(1)[0][0]} if bg is None else bg
    w,h=im.size;pix=im.load();todo=deque([(x,y) for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)]);outside=set()
    while todo:
        x,y=todo.popleft()
        if not(0<=x<w and 0<=y<h) or (x,y) in outside or pix[x,y] not in bg:continue
        outside.add((x,y));todo.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
    # Drop isolated floor grains after background removal; retain complete
    # connected silhouettes and their contact shadows.
    occupied={(x,y) for y in range(h) for x in range(w) if (x,y) not in outside}
    kept=set();groups=[]
    while occupied:
        first=occupied.pop();group={first};todo=deque([first])
        while todo:
            x,y=todo.popleft()
            for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if p in occupied:occupied.remove(p);group.add(p);todo.append(p)
        if len(group)>=8:kept.update(group);groups.append(group)
    if largest:kept=max(groups,key=len)
    alpha=Image.frombytes('L',im.size,bytes(255 if (x,y) in kept else 0 for y in range(h) for x in range(w)))
    return alpha
def save_module(group,name,im):
    path=E/group/'modules';path.mkdir(parents=True,exist_ok=True);im.save(path/(name+'.png'));modules.setdefault(group,[]).append(dict(name=name,size=list(im.size),path=str((path/(name+'.png')).relative_to(E))))
def geometry(name,size,bounds,start,solids,exit=None):
    l,t,r,b=bounds
    def free(p):
        x,y=p;return l<=x<=r-15 and t<=y<=b-15 and not any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,*_ in solids)
    prev={tuple(start):None};todo=deque(prev);goal=None
    while todo:
        x,y=todo.popleft()
        if exit and exit[0]<=x+8<exit[0]+exit[2] and exit[1]<=y+8<exit[1]+exit[3] and goal is None:goal=(x,y)
        for p in ((x-8,y),(x+8,y),(x,y-8),(x,y+8)):
            if p not in prev and free(p):prev[p]=(x,y);todo.append(p)
    allfree={(x,y) for y in range(t,b-14,8) for x in range(l,r-14,8) if free((x,y))}
    assert free(tuple(start)) and set(prev)==allfree,(name,'disconnected',len(prev),len(allfree))
    path=[]
    if name=='03' and exit:
        # Route guidance uses a full8px clearance around projected vehicle
        # bodies, and aims inside the exit instead of its activation edge.
        target=(exit[0]+exit[2]//2-8,exit[1]+exit[3]//2-8)
        def navfree(p):
            x,y=p
            return free(p) and not any(x<a+w+8 and x+16>a-8 and y<c+h+8 and y+16>c-8 for a,c,w,h,*_ in solids)
        navprev={tuple(start):None};navq=deque(navprev)
        while navq:
            x,y=navq.popleft()
            if (x,y)==target:break
            for p in ((x-8,y),(x+8,y),(x,y-8),(x,y+8)):
                if p not in navprev and navfree(p):navprev[p]=(x,y);navq.append(p)
        assert target in navprev,'Safe route cannot reach exit center'
        prev=navprev;goal=target
    if exit:
        assert goal,(name,'unreachable exit')
        while goal is not None:path.append(goal);goal=prev[goal]
        path.reverse()
    corners=[]
    for i,p in enumerate(path):
        if i in (0,len(path)-1) or (p[0]-path[i-1][0],p[1]-path[i-1][1])!=(path[i+1][0]-p[0],path[i+1][1]-p[1]):corners.append(p)
    geom[name]=dict(size=size,width=size[0],height=size[1],bounds=bounds,start=start,solids=solids,exit=exit,traversal_points=corners,geometry_validation=dict(footprint=16,free_positions=len(allfree),reachable_positions=len(allfree),all_free_positions_connected=True))
    return corners
def rects_c(name,solids):return 'static const ArenaRect '+name+'[]={'+','.join('{'+','.join(map(str,v[:4]))+','+('TRUE' if v[4] else 'FALSE')+'}' for v in solids)+'};\n'
def finish(group,images,pal,prefix,filename=None,limit=640):
    folder=E/group;folder.mkdir(exist_ok=True)
    for name,im in images.items():im.save(folder/(name+'-whole-before-pack.png'))
    code,stats=pack(images,pal,folder,prefix,limit)
    if filename:(S/filename).write_text('// Whole scenes and complete modules:art/campaign-pattern-v2/early\n'+code)
    return code,stats

#1/2A preserve the same physical courtyard;2B adds actual bomb rubble.
church=Image.open(E/'01-courtyard/complete-native.png');damage=Image.open(E/'01-courtyard/damaged-native.png')
cmeta=json.loads((E/'01-courtyard/manifest.json').read_text());cs=cmeta['solids'];cb=cmeta['bounds'];cstart=cmeta['start']
for ph in ('01','02A'):geometry(ph,[512,384],cb,cstart,cs)
ruins=damage.copy();rubble=Image.open(legacy/'source/rubble.png').convert('RGBA');rubble=rubble.crop(rubble.getchannel('A').getbbox());rubble=ImageOps.contain(rubble,(56,32),Image.Resampling.LANCZOS)
ri=idx(rubble.convert('RGB'),cp);ra=rubble.getchannel('A').point(lambda v:255 if v>=128 else 0)
ruin_solids=cs.copy()
for x,y in ((168,152),(280,216),(72,248)):
    ruins.paste(ri,(x,y+32-ri.height),ra);ruin_solids.append([x,y,56,32,False])
geometry('02B',[512,384],cb,cstart,ruin_solids)
_,rs=finish('02B-ruins',{'map':ruins},cp,'church_ruins','campaign_early_church_ruins.inc');geom['02B']['tiles']=rs['tiles']

#3: whole church + one whole economical house type, courtyard intervals and a
# whole warehouse entrance. Repetition uses architecture, never roof fragments.
src=Image.open(E/'source/03-street-whole.png').convert('RGB').resize((960,320),Image.Resampling.LANCZOS)
si=idx(src,cp)
house=idx(src.crop((24,8,248,136)).resize((96,64),Image.Resampling.LANCZOS),cp)
entrance=idx(src.crop((784,0,952,136)).resize((72,80),Image.Resampling.LANCZOS),cp)
van=idx(src.crop((168,160,328,248)).resize((72,40),Image.Resampling.LANCZOS),cp)
crates=idx(src.crop((688,176,784,248)).resize((32,24),Image.Resampling.LANCZOS),cp)
parts={n:Image.open(E/'01-courtyard/modules'/f'{n}.png').convert('RGB') for n in ('floor','upper-vegetation','upper-wall','side-left','side-right','lower-wall','lower-post','corner-left','corner-right')}
parts={k:idx(v,cp) for k,v in parts.items()}
road=new((2560,256),cp,11);repeat(road,parts['floor'].crop((0,0,16,16)),(0,0,2560,256));repeat(road,parts['upper-vegetation'],(0,0,2560,112));repeat(road,parts['upper-wall'],(16,56,2528,56))
for x in (288,576,912,1248,1584,1920,2256):road.paste(house,(x,48))
road.paste(church.crop((16,0,216,112)),(24,0));road.paste(entrance,(2472,32))
sidewalk=si.crop((272,128,288,152));repeat(road,sidewalk,(0,112,2560,24))
repeat(road,parts['lower-wall'],(24,224,2512,32))
for x in (480,1008,1520,2032):road.paste(parts['lower-post'],(x,224))
repeat(road,parts['side-left'],(0,0,16,224));repeat(road,parts['side-right'],(2544,0,16,224));road.paste(parts['corner-left'],(0,224));road.paste(parts['corner-right'],(2536,224))
street_solids=[]
for x,y in ((328,136),(800,184),(1288,136),(1760,184),(2200,136)):
    road.paste(van,(x,y),mask(van,{9,10,11},largest=True));street_solids.append([x,y,72,40,True])
# Keep the five full vehicles as the traversal obstacles. Tiny crate silhouettes
# competed with the floor at native scale and are intentionally not scattered.
corners=geometry('03',[2560,256],[16,136,2543,223],[48,144],street_solids,[2472,176,48,48])
road_ruins=road.copy();road_ruins.paste(damage.crop((16,0,216,112)),(24,0))
_,st=finish('03-street',{'map':road},cp,'street');_,sd=finish('03-street-ruined',{'map':road_ruins},cp,'street_damaged')
(S/'campaign_early_street.inc').write_text((E/'03-street/candidate.inc').read_text() if (E/'03-street/candidate.inc').exists() else '')
code1,_=pack({'map':road},cp,E/'03-street','street');code2,_=pack({'map':road_ruins},cp,E/'03-street-ruined','street_damaged');(S/'campaign_early_street.inc').write_text(code1+code2)
layout=rects_c('streetSolids',street_solids)+'const ArenaDef EARLY_ARENA03={2560,256,16,136,2543,223,48,144,streetSolids,sizeof(streetSolids)/sizeof(streetSolids[0]),&streetScene};\n'
layout+='static const RoutePoint streetPoints[]={'+','.join('{%s,%s,0}'%(x+8,y+8) for x,y in corners)+'};\nconst RouteDef EARLY_ROUTE03={streetPoints,sizeof(streetPoints)/sizeof(streetPoints[0]),{2472,176,48,48,FALSE}};\n'
(S/'campaign_early_street_layout.inc').write_text(layout);geom['03'].update(tiles=st['tiles'],damaged_tiles=sd['tiles'],objective='reach',enemy_cap=4,shot_cap=6,spawn_seconds=4,roster=[1,0],source='campaign-pattern-v2')
for n,v in [('house-whole',house),('warehouse-entrance-whole',entrance),('van-whole',van),('crate-pallet-whole',crates),('sidewalk',sidewalk)]:save_module('03-street',n,v)

#4: window bays, one entire gate and dedicated south storage wall.
master=Image.open(E/'source/04-warehouse-whole.png').convert('RGB');wi,wp=indexed(master,(512,384),1,15)
floorid=nearest(wp,(145,145,109));warehouse=new((512,320),wp,floorid)
floor=wi.crop((240,128,248,136));floor=Image.new('P',(8,8),Counter(floor.getdata()).most_common(1)[0][0]);floor.putpalette(wi.getpalette());repeat(warehouse,floor,(0,0,512,320))
wall=wi.crop((48,0,56,88));repeat(warehouse,wall,(0,0,512,88))
bay=wi.crop((64,0,184,88));gate=wi.crop((184,0,328,88))
warehouse.paste(bay,(40,0));warehouse.paste(bay,(352,0));warehouse.paste(gate,(184,0))
side_l=wi.crop((0,160,32,192));side_r=wi.crop((480,160,512,192));repeat(warehouse,side_l,(0,88,32,176));repeat(warehouse,side_r,(480,88,32,176))
south=wi.crop((64,328,96,384));repeat(warehouse,south,(0,264,512,56))
warehouse.paste(wi.crop((0,328,32,384)),(0,264));warehouse.paste(wi.crop((480,328,512,384)),(480,264))
bench=idx(master.resize((512,384),Image.Resampling.LANCZOS).crop((80,112,208,176)).resize((96,48),Image.Resampling.LANCZOS),wp)
crate=idx(master.resize((512,384),Image.Resampling.LANCZOS).crop((208,216,296,280)).resize((64,48),Image.Resampling.LANCZOS),wp)
depot_solids=[]
for asset,x,y in ((bench,64,120),(bench,336,168),(crate,208,208)):
    warehouse.paste(asset,(x,y),mask(asset));depot_solids.append([x,y,asset.width,asset.height,True])
geometry('04',[512,320],[32,104,479,263],[48,112],depot_solids)
_,depot=finish('04-warehouse',{'map':warehouse},wp,'depot','campaign_early_depot.inc');geom['04'].update(tiles=depot['tiles'],objective='kill',target=20)
for n,v in [('north-bay-whole',bay),('north-gate-whole',gate),('south-storage-wall',south),('workbench-whole',bench),('supply-pallet-whole',crate)]:save_module('04-warehouse',n,v)

#5 is built once its entire outdoor master is ready.
if (E/'source/05-signal-whole.png').exists():
    spw=struct.unpack('>16H',(G/'res/stages/05/palette.bin').read_bytes());sp=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in spw]
    sm=Image.open(E/'source/05-signal-whole.png').convert('RGB').resize((384,320),Image.Resampling.LANCZOS);qi=idx(sm,sp)
    floor=new((384,320),sp,nearest(sp,(145,145,145)));repeat(floor,qi.crop((176,128,192,144)),(0,0,384,320))
    # Whole facade and dedicated complete perimeter heights are preserved.
    repeat(floor,qi.crop((0,0,16,112)),(0,0,384,112))
    facade=qi.crop((0,0,384,112)).resize((272,112),Image.Resampling.NEAREST);floor.paste(facade,(56,0))
    repeat(floor,qi.crop((0,144,16,176)),(0,112,16,160));repeat(floor,qi.crop((368,144,384,176)),(368,112,16,160))
    repeat(floor,qi.crop((64,272,80,320)),(16,272,352,48));floor.paste(qi.crop((0,272,24,320)),(0,272));floor.paste(qi.crop((360,272,384,320)),(360,272))
    # Concepts can move flanking objects. Whole extraction is verified manually.
    sidecrate=qi.crop((24,128,112,208));barrel=qi.crop((280,200,352,272))
    # Use the complete known supply/blue-barrel silhouettes from the warehouse
    # master rather than any fragment left by a shifted source illustration.
    supply=idx(Image.open(E/'04-warehouse/modules/supply-pallet-whole.png').convert('RGB').resize((56,40),Image.Resampling.NEAREST),sp)
    blue=idx(Image.open(G/'art/phase01-pattern-v1/modules/barrels.png').convert('RGBA').convert('RGB'),sp)
    floor.paste(supply,(40,144),mask(supply));floor.paste(blue,(304,224),Image.open(G/'art/phase01-pattern-v1/modules/barrels.png').getchannel('A'))
    signal=floor.copy();santa=Image.open(G/'art/santa-iso60-v2/santa.png');signal.paste(santa,(176,176),santa.convert('RGBA').getchannel('A'))
    code,stats=pack({'map':signal,'floor':floor},sp,E/'05-signal','signal',638)
    tiledata=(E/'05-signal/tiles.bin').read_bytes();native_old=(G/'res/stages/05/tiles.bin').read_bytes();crowns=native_old[634*32:636*32];assert len(crowns)==64
    full=tiledata+crowns;(E/'05-signal/tiles.bin').write_bytes(full)
    atlas=Image.open(E/'05-signal/sprites-8x8.png')
    for i in range(len(full)//32-2,len(full)//32):
        b=full[i*32:(i+1)*32];patch=Image.frombytes('P',(8,8),bytes(v for c in b for v in (c>>4,c&15)));atlas.paste(patch,(i%16*8,i//16*8))
    atlas.save(E/'05-signal/sprites-8x8.png')
    stats.update(tiles=len(full)//32,crown_extra_tiles=2,limit=640);(E/'05-signal/pack.json').write_text(json.dumps(stats,indent=2)+'\n')
    pwords=[(round(r/255*7)<<1)|(round(g/255*7)<<5)|(round(b/255*7)<<9) for r,g,b in sp]
    mp=struct.unpack('>1920H',(E/'05-signal/map.bin').read_bytes());fp=struct.unpack('>1920H',(E/'05-signal/floor.bin').read_bytes())
    code=c_array('signal_tiles','u32',struct.unpack('>'+str(len(full)//4)+'I',full))+c_array('signal_palette','u16',pwords)+c_array('signal_map','u16',mp)
    (S/'campaign_early_signal.inc').write_text(code)
    restore=[fp[(20+y)*48+22+x] for y in range(8) for x in range(5)]
    (S/'campaign_early_signal_npc.inc').write_text(c_array('earlyNpcFloor','u16',restore)+f'#define EARLY_NPC_CROWN {stats["tiles"]-2}\n')
    sigsolids=[[176,176,40,48,False],[40,144,56,40,True],[304,224,40,40,False]]
    geometry('05',[384,320],[16,112,367,271],[64,232],sigsolids);geom['05'].update(tiles=stats['tiles'],objective='protect',target=120,npc_hp=180,npc_position=[176,200])

(E/'geometry.json').write_text(json.dumps(geom,ensure_ascii=False,indent=2)+'\n')
(E/'modules.json').write_text(json.dumps(modules,ensure_ascii=False,indent=2)+'\n')
import sys
sys.path.insert(0,str(G/'tools'))
from campaign_corridors import active,early_files
if active('3'):
 for path,data in early_files().items():path.write_bytes(data)
print(json.dumps({p:dict(tiles=d.get('tiles'),size=d['size'],solids=len(d['solids'])) for p,d in geom.items()},indent=2))
