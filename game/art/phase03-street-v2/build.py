"""Pack authored street props and exact phase1church modules; no raster synthesis."""
from pathlib import Path
from collections import deque
import json,struct,hashlib
from PIL import Image
A=Path(__file__).resolve().parent

def build(m,church,damage,cp,shelter,sp):
    sheet=Image.open(A/'source/street-kit.png').convert('RGBA');W,H=sheet.size
    specs=[('house',(64,64)),('shop',(64,64)),('car',(40,24)),('van',(48,32)),('barricade',(40,24)),('lamp',(16,48)),('road',(32,32)),('curb',(32,16))]
    colors=m.rgb(cp);assets={}
    for i,(name,size) in enumerate(specs):
        im=sheet.crop((i%4*W//4,i//4*H//2+(36 if i>=4 else 0),(i%4+1)*W//4,(i//4+1)*H//2))
        alpha=im.getchannel('A').point(lambda v:255 if v>=128 else 0);im.putalpha(alpha)
        im=im.crop(alpha.getbbox())
        if name in ('road','curb'):
            inset=max(2,min(im.width,im.height)//32)
            im=im.crop((inset,inset,im.width-inset,im.height-inset));im.putalpha(255)
        im=im.resize(size,Image.Resampling.NEAREST)
        im.save(A/f'assets/{name}.png');assets[name]=im
    # Reuse one full-size house module so street facades remain legible at native scale.
    assets['shop']=assets['house']
    # Preserve the original native church, including its roof and blue doorway.
    # All other props use the exact same16-entry RGB333 palette.
    def converted(im,material):
        out=[]
        for y in range(im.height):
            row=[]
            for x in range(im.width):
                r,g,b,a=im.getpixel((x,y));row.append(None if a<128 else min((1,2) if material=='road' else range(16),key=lambda n:sum((colors[n][j]-[r,g,b][j])**2 for j in range(3))))
            out.append(row)
        return out
    px={name:converted(im,name) for name,im in assets.items()}
    def grid(rect,source=church):
        x,y,w,h=rect
        return [row[x//8:(x+w)//8] for row in source[y//8:(y+h)//8]]
    # Start from existing material tiles, then place native modules/props.
    road=m.canvas(2560,320,church,(224,160,32,32))
    def stamp_pixels(name,x,y):
        p=px[name];height=len(p);width=len(p[0])
        for ty in range(height//8):
            for tx in range(width//8):
                old=m.unpack(road[y//8+ty][x//8+tx])
                for dy in range(8):
                    for dx in range(8):
                        c=p[ty*8+dy][tx*8+dx]
                        if c is not None:old[dy*8+dx]=c
                road[y//8+ty][x//8+tx]=m.pack(old)
    for y in range(0,320,32):
        for x in range(0,2560,32):stamp_pixels('road',x,y)
    for y in (112,128,288,304):
        for x in range(0,2560,32):stamp_pixels('curb',x,y)
    m.stamp(road,church,(24,8,192,96),(32,40))
    stamp_pixels('shop',248,48)
    for n,x in enumerate(range(336,2320,80)):
        stamp_pixels('house' if n%3 else 'shop',x,48)
        if n%3==1:stamp_pixels('lamp',x+64,96)
    industrial=m.remap(shelter,sp,cp)
    m.stamp(road,industrial,(112,32,48,48),(2448,80))
    stamp_pixels('shop',2352,48)
    stamp_pixels('lamp',224,96)
    solids=[];placements=[]
    def prop(name,x,y,box,shots=True):
        stamp_pixels(name,x,y);solids.append([*box,shots]);placements.append(dict(asset=name,x=x,y=y,collision=box,blocks_shots=shots))
    prop('car',240,208,[248,208,24,24])
    # Four staggered pileups connect to alternating sidewalks. Each leaves
    # at least48px of visible passage, forcing a north/south detour.
    for x in (400,1328):
        for y,dx in ((144,0),(176,8),(208,0)):
            prop('van',x+dx,y,[x+dx+8,y,32,32])
    for x in (848,1784):
        for y,dx in ((208,0),(232,8),(256,0),(280,8)):
            prop('car',x+dx,y,[x+dx+8,y,24,24])
    for name,x,y,box in [('barricade',640,224,[648,232,32,16]),('barricade',1096,144,[1104,152,32,16]),('barricade',1560,240,[1568,248,32,16]),('barricade',2040,144,[2048,152,32,16]),('barricade',2256,216,[2264,224,32,16])]:
        prop(name,x,y,box,False)
    assert all(all(v%8==0 for v in r[:4]) for r in solids),'collision grid alignment'
    bounds=[16,144,2543,303];start=(48,144);exit=[2472,176,48,48]
    def free(p):
        x,y=p
        return 16<=x<=2528 and 144<=y<=288 and not any(x<a+w and x+16>a and y<b+h and y+16>b for a,b,w,h,*_ in solids)
    prev={start:None};q=deque([start]);goal=None
    while q:
        p=q.popleft();x,y=p
        if 2472<=x+8<2520 and 176<=y+8<224 and goal is None:goal=p
        for p2 in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
            if p2 not in prev and free(p2):prev[p2]=p;q.append(p2)
    allfree={(x,y) for y in range(144,289,8) for x in range(16,2529,8) if free((x,y))}
    assert set(prev)==allfree and goal,('connectivity',len(prev),len(allfree))
    # Give the controller/animation a4px tolerance around solids; shortest
    # paths grazing a corner can otherwise stop2px before clearing its face.
    def routefree(p):
        x,y=p
        return free(p) and not any(x-4<a+w and x+20>a and y-4<b+h and y+20>b for a,b,w,h,*_ in solids)
    prev={start:None};q=deque([start]);goal=None
    while q:
        p=q.popleft();x,y=p
        if 2488<=x+8<2512 and 184<=y+8<216:goal=p;break
        for p2 in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
            if p2 not in prev and routefree(p2):prev[p2]=p;q.append(p2)
    assert goal,'margin-safe route unreachable'
    path=[];p=goal
    while p is not None:path.append(p);p=prev[p]
    path.reverse();corners=[path[0]]
    for i in range(1,len(path)-1):
        if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):corners.append(path[i])
    corners.append(path[-1])
    # A straight horizontal run must fail at the alternate pileups.
    assert not all(free((x,144)) for x in range(48,2481,8))
    assert any(y>=240 for x,y in path) and any(y<=192 for x,y in path if 800<=x<=896)
    ruined=[row[:] for row in road];m.stamp(ruined,damage,(24,8,192,96),(32,40))
    # Share an exact atlas for the two church outcomes.
    extra=[t for row in ruined for t in row]
    meta,indices=m.export('street',road,cp,extra)
    raw=struct.pack('>'+str(len(indices))+'H',*indices)
    (m.ART/'street/damaged.bin').write_bytes(raw)
    p=m.SRC/'campaign_early_street.inc'
    with p.open('a') as f:f.write(m.c_array('street_damaged','u16',indices))
    # Faithfulness check compares tile bytes, not a resemblance heuristic.
    exact=all(road[5+y][4+x]==church[1+y][3+x] for y in range(12) for x in range(24))
    assert exact
    meta.update(native_modules_only=False,bounds=bounds,start=list(start),solids=solids,exit=exit,objective='reach',enemy_cap=4,shot_cap=6,spawn_seconds=4,roster=[1,0],traversal_points=[list(p) for p in corners])
    layout='// Generated by art/phase03-street-v2/build.py.\nstatic const ArenaRect streetSolids[]={\n'
    layout+=''.join('    {'+','.join(map(str,r[:4]))+','+('TRUE' if r[4] else 'FALSE')+'},\n' for r in solids)+'};\n'
    layout+='const ArenaDef EARLY_ARENA03={2560,320,16,144,2543,303,48,144,streetSolids,sizeof(streetSolids)/sizeof(streetSolids[0]),&streetScene};\n'
    layout+='static const RoutePoint streetPoints[]={'+','.join('{'+str(x+8)+','+str(y+8)+',0}' for x,y in corners)+'};\n'
    layout+='const RouteDef EARLY_ROUTE03={streetPoints,sizeof(streetPoints)/sizeof(streetPoints[0]),{2472,176,48,48,FALSE}};\n'
    (m.SRC/'campaign_early_street_layout.inc').write_text(layout)
    report=dict(meta,placements=placements,church_exact_tiles=288,church_pixel_identical=exact,source_sha256=hashlib.sha256((A/'source/street-kit.png').read_bytes()).hexdigest(),path_steps=len(path),connected_positions=len(allfree),minimum_designed_passage=48,two_church_outcomes=True)
    (A/'layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return meta
