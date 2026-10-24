"""Image-first church rebuild. Extract complete modules and measure exact reuse.
The resource exporter retains the shared640tile allocation for every stage.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import deque,Counter
import json,struct,sys,hashlib,subprocess,shutil
A=Path(__file__).resolve().parent/'01-courtyard';G=Path(__file__).resolve().parents[3]
A.mkdir(exist_ok=True)
for sub in ('source','modules','native'):(A/sub).mkdir(exist_ok=True)
shutil.copy2(G/'art/phase01-pattern-v1/source/whole-scene.png',A/'source/whole-scene.png')
sys.path.insert(0,str(G/'art/campaign-whole-scenes-v1'))
from pack import pack
palette_words=struct.unpack('>16H',(G/'res/courtyard/palette.bin').read_bytes())
palette=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in palette_words]
flat=sum(map(list,palette),[])+[0]*720

def index(im):
    im=im.convert('RGB');lookup={c:min(range(1,16),key=lambda i:sum((c[k]-palette[i][k])**2 for k in range(3))) for c in set(im.getdata())}
    out=Image.frombytes('P',im.size,bytes(lookup[c] for c in im.getdata()));out.putpalette(flat);return out

source=index(Image.open(A/'source/whole-scene.png').resize((512,384),Image.Resampling.LANCZOS))
old=index(Image.open(G/'art/campaign-composition-forensic-v1/maps/1-complete.png'))
old_damage=index(Image.open(G/'art/phase01-courtyard-v2/damaged-native.png'))
modules={};placements=[]
def module(name,im,region,origin,repeat='none',mask=None):
    modules[name]=dict(image=im,region=region,origin=origin,repeat=repeat,mask=mask)
    if mask:
        rgba=im.convert('RGBA');rgba.putalpha(mask);rgba.save(A/'modules'/f'{name}.png')
    else:im.save(A/'modules'/f'{name}.png')
    return im

def object_mask(im,components=1):
    # Extract authored silhouettes, retaining enclosed same-colored pixels.
    # This is sprite preparation, not repainting or shape invention.
    bg=Counter(im.getdata()).most_common(1)[0][0];w,h=im.size;pix=im.load();seen=set();groups=[]
    for y in range(h):
        for x in range(w):
            if (x,y) in seen or pix[x,y]==bg:continue
            todo=[(x,y)];seen.add((x,y));group=[]
            while todo:
                xx,yy=todo.pop();group.append((xx,yy))
                for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and pix[nx,ny]!=bg:seen.add((nx,ny));todo.append((nx,ny))
            groups.append(group)
    occupied=set(p for group in sorted(groups,key=len,reverse=True)[:components] for p in group)
    outside=set();todo=[(x,y) for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)]
    while todo:
        xy=todo.pop();x,y=xy
        if xy in outside or xy in occupied:continue
        outside.add(xy)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in outside:todo.append((nx,ny))
    return Image.frombytes('L',(w,h),bytes(0 if (x,y) in outside else 255 for y in range(h) for x in range(w)))

# The approved identity survives as one WHOLE church, not roof/façade slices.
module('church',old.crop((16,0,216,112)),'upper','existing phase1, complete church x16..215')
module('upper-vegetation',old.crop((256,0,272,48)),'upper','existing phase1, repeatable background material','x')
module('upper-wall',old.crop((240,48,256,104)),'upper','existing phase1, full height of the repeatable wall material','x')
module('evacuation-gate',old.crop((368,48,488,104)),'upper','existing phase1, whole gate and posts')
module('side-left',source.crop((0,160,16,192)),'sides','whole generated scene, straight left wall','y')
module('side-right',source.crop((496,160,512,192)),'sides','whole generated scene, straight right wall','y')
module('lower-wall',source.crop((64,352,80,384)),'lower','whole generated scene, complete wall height','x')
module('lower-post',source.crop((208,352,232,384)),'lower','whole generated scene, whole post')
module('corner-left',source.crop((0,352,24,384)),'lower','whole generated scene, complete bottom-left junction')
module('corner-right',source.crop((488,352,512,384)),'lower','whole generated scene, complete bottom-right junction')
module('floor',source.crop((248,272,280,304)),'field','whole generated scene, quiet earth material','xy')
bench=source.crop((152,144,224,184));barrels=source.crop((328,168,368,208))
module('bench',bench,'field','whole generated scene, complete first bench including contact shadow',mask=object_mask(bench))
module('barrels',barrels,'field','whole generated scene, complete pair of barrels and contact shadow',mask=object_mask(barrels,2))

def canvas():
    im=Image.new('P',(512,384));im.putpalette(flat);return im
out=canvas()
def place(name,x,y):
    m=modules[name];out.paste(m['image'],(x,y),m['mask']);placements.append(dict(module=name,position=[x,y],size=list(m['image'].size)))
def repeat(name,x,y,w,h):
    m=modules[name];pw,ph=m['image'].size
    for yy in range(y,y+h,ph):
        for xx in range(x,x+w,pw):
            out.paste(m['image'].crop((0,0,min(pw,x+w-xx),min(ph,y+h-yy))),(xx,yy))
    placements.append(dict(module=name,position=[x,y],area=[w,h],repeat=m['repeat']))
repeat('floor',0,0,512,384)
repeat('upper-vegetation',0,0,512,48)
repeat('upper-wall',16,48,480,56)
place('church',16,0);place('evacuation-gate',368,48)
repeat('side-left',0,112,16,240);repeat('side-right',496,112,16,240)
# Upper corner material is retained in the same authored projection.
out.paste(old.crop((0,48,16,112)),(0,48));out.paste(old.crop((496,48,512,112)),(496,48))
repeat('lower-wall',24,352,464,32)
place('lower-post',208,352);place('lower-post',280,352)
place('corner-left',0,352);place('corner-right',488,352)
for name,x,y in [('bench',88,184),('bench',136,288),('barrels',392,264)]:place(name,x,y)
damaged=out.copy();damaged.paste(old_damage.crop((16,0,216,112)),(16,0))
out.save(A/'complete-native.png');damaged.save(A/'damaged-native.png')
code,stats=pack({'map':out,'damaged':damaged},palette,A/'native','pattern',limit=640)
(A/'native/candidate.inc').write_text(code)
out.save(A/'complete-native.png');damaged.save(A/'damaged-native.png')

# Conservative full visual rectangles for this first low-obstacle prototype:
# avoids actors standing inside benches/barrels with a background-only renderer.
solids=[[88,184,72,40,False],[136,288,72,40,False],[392,264,40,40,False]]
bounds=[24,128,487,351];start=[256,160]
def blocked(x,y):
    l,t,r,b=bounds
    return not(l<=x<=r-15 and t<=y<=b-15) or any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,_ in solids)
free={(x,y) for y in range(128,337,8) for x in range(24,473,8) if not blocked(x,y)}
todo=[(256,160)];seen=set()
while todo:
    v=todo.pop()
    if v in seen or v not in free:continue
    seen.add(v);x,y=v;todo.extend(((x-8,y),(x+8,y),(x,y-8),(x,y+8)))
assert free==seen,'Disconnected walking area'
assert not blocked(*start)
layout=out.convert('RGB');d=ImageDraw.Draw(layout)
for rect,color in [((0,0,511,111),'#62b9dc'),((0,352,511,383),'#efbb64'),((0,112,15,351),'#b8b3e9'),((496,112,511,351),'#b8b3e9')]:d.rectangle(rect,outline=color,width=2)
for x,y,w,h,_ in solids:d.rectangle((x,y,x+w-1,y+h-1),outline='#f07f81',width=2)
d.rectangle((*start,start[0]+15,start[1]+15),outline='#eaffd7',width=2)
layout.save(A/'layout.png')
counts=Counter()
for m in modules.values():
    counts[m['region']]+=m['image'].width*m['image'].height//64
manifest=dict(phase='1',node=1,name='Pátio da igreja · padrão por faixas',goal='Sobreviver90s; um tipo de inimigo; evacuação pelo portão superior',size=[512,384],bounds=bounds,solids=solids,start=start,complete='complete-native.png',background='complete-native.png',objects=[],special_states=[dict(label='Igreja danificada',path='damaged-native.png')],placements=placements,modules=[dict(id=n,region=m['region'],size=list(m['image'].size),path=f'modules/{n}.png',origin=m['origin'],repeat=m['repeat']) for n,m in modules.items()],memory=dict(unique_tiles=stats['tiles'],budget=640,graphic_bytes=len((A/'native/tiles.bin').read_bytes()),budget_bytes=640*32,free_tiles=640-stats['tiles'],tilemap_bytes_per_state=6144,palette_bytes=32,states=2,exact_tile_reassembly=True,lossy_tile_replacements=0),geometry=dict(footprint=[16,16],free_sampled_positions=len(free),connected_positions=len(seen),connected=True),production_rom_sha256=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest(),status='candidate_for_user_review',scope='Production integration of church phases;3field objects preserve an open evacuation lane')
(A/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(tiles=stats['tiles'],free_tiles=640-stats['tiles'],connected_positions=len(seen)),indent=2))
