"""Native48px generator animation and tile-aligned, connected energy conduits."""
from collections import defaultdict, deque
import struct
import numpy as np
from PIL import Image, ImageDraw

# Routes enter the opaque bodies at both ends. Their tile centers sit four
# pixels beyond the listed coordinates, aligned with the generator sockets.
CONNECTIONS = [
    ('station-1','console',[(80,160),(136,160),(136,288),(208,288)]),
    ('station-2','console',[(432,160),(352,160),(352,272),(304,272)]),
    ('station-3','console',[(384,280),(352,280),(352,304),(304,304)]),
    ('console','battery',[(256,320),(256,432)]),
    ('station-4','battery',[(400,456),(288,456)]),
    ('station-5','battery',[(112,456),(224,456)]),
]

def conduits(size,palette,connections=CONNECTIONS):
    cells=defaultdict(set);graph=defaultdict(set)
    directions={(0,-8):'N',(8,0):'E',(0,8):'S',(-8,0):'W'}
    for a,b,points in connections:
        graph[a].add(b);graph[b].add(a)
        for start,end in zip(points,points[1:]):
            dx,dy=end[0]-start[0],end[1]-start[1]
            assert (dx==0)!=(dy==0) and dx%8==0 and dy%8==0
            step=(0 if dx==0 else 8 if dx>0 else -8,0 if dy==0 else 8 if dy>0 else -8)
            p=start
            while p!=end:
                q=(p[0]+step[0],p[1]+step[1])
                cells[p].add(directions[step]);cells[q].add(directions[(-step[0],-step[1])]);p=q
    out=Image.new('RGBA',size);parts={}
    anchors={'N':(3,0),'E':(7,3),'S':(3,7),'W':(0,3)}
    def color(i):return (*palette[i],255)
    for (x,y),exits in sorted(cells.items()):
        collar=(exits=={'E','W'} and x%32==0) or (exits=={'N','S'} and y%32==0)
        name=''.join(sorted(exits))+('-collar' if collar else '')
        if name not in parts:
            im=Image.new('RGBA',(8,8));draw=ImageDraw.Draw(im)
            # Shared endpoint profiles are identical for all orientations;
            # collars end before the tile border so no joint can protrude.
            for point in [anchors[e] for e in exits]:
                draw.line([(4,5),(point[0]+1,point[1]+2)],fill=color(1),width=5)
            for point in [anchors[e] for e in exits]:draw.line([(3,3),point],fill=color(1),width=5)
            for point in [anchors[e] for e in exits]:draw.line([(3,3),point],fill=color(3),width=3)
            for point in [anchors[e] for e in exits]:draw.line([(2,2),(point[0]-1,point[1]-1)],fill=color(6),width=1)
            if collar:
                if exits=={'E','W'}:
                    draw.rectangle((3,1,4,5),fill=color(10));draw.point((3,1),fill=color(12));draw.point((4,5),fill=color(8))
                else:
                    draw.rectangle((1,3,5,4),fill=color(10));draw.point((1,3),fill=color(12));draw.point((5,4),fill=color(8))
            parts[name]=im
        out.alpha_composite(parts[name],(x,y))
    # Every branch is a continuous physical chain of adjacent8px cells.
    for a,b,points in connections:
        for start,end in zip(points,points[1:]):
            dx=(end[0]>start[0])-(end[0]<start[0]);dy=(end[1]>start[1])-(end[1]<start[1])
            for n in range(max(abs(end[0]-start[0]),abs(end[1]-start[1]))+1):
                assert out.getpixel((start[0]+dx*n+3,start[1]+dy*n+3))[3],('gap in cable',a,b,n)
    seen={'console'};q=deque(seen)
    while q:
        for n in graph[q.popleft()]:
            if n not in seen:seen.add(n);q.append(n)
    assert seen=={'console','battery',*[f'station-{i}' for i in range(1,6)]}
    return out,parts,dict(all_seven_nodes_connected=True,tile_count=len(cells),routes=[dict(source=a,target=b,points=points) for a,b,points in connections])

def generators(source,palette):
    original=Image.open(source).convert('RGBA')
    alpha=original.getchannel('A').point(lambda v:255 if v>=160 else 0)
    original.putalpha(alpha)
    # Direct native sampling only: no smoothed image or coarse2px/4px pass.
    body=original.crop(alpha.getbbox()).resize((40,40),Image.Resampling.NEAREST)
    native=Image.new('RGBA',(48,48));native.alpha_composite(body,(4,4))
    rgba=np.array(native);colors=np.array(palette,dtype=np.int32)
    ids=((rgba[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype('uint8')+1
    ids[rgba[:,:,3]<128]=0
    base=Image.fromarray(ids);base.putpalette(sum(map(list,palette),[])+[0]*720)
    frames=[]
    for state in range(6):
        im=base.copy();draw=ImageDraw.Draw(im)
        # Native display pixels, unchanged casing/feet across all six poses.
        draw.rectangle((21,14,26,17),fill=2 if state==0 else 8 if state==1 else 13)
        if state>=2:
            for col in range(22,26):
                if (col+state)%3:draw.point((col,15),fill=7 if state%2 else 12)
        draw.rectangle((15,14,16,14),fill=5 if state==0 else 11 if state==1 else 12)
        draw.rectangle((31,14,32,14),fill=5 if state==0 else 11 if state==1 else 13)
        im.info['transparency']=0;frames.append(im)
    tiles=[];lookup={};mapping=[];visible=[]
    for im in frames:
        for x in range(0,48,8):
            for y in range(0,48,8):
                t=im.crop((x,y,x+8,y+8)).tobytes()
                if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
                mapping.append(lookup[t]);visible.append(int(any(t)))
    raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
    assert b''.join(tiles[i] for i in mapping)==b''.join(im.crop((x,y,x+8,y+8)).tobytes() for im in frames for x in range(0,48,8) for y in range(0,48,8))
    def ca(name,kind,values):
        fmt='0x%08XUL' if kind=='u32' else '%d'
        return 'static const '+kind+' '+name+'[]={\n'+''.join(','.join(fmt%v for v in values[i:i+8])+',\n' for i in range(0,len(values),8))+'};\n'
    header='// Generated phase14 generator: native48px; six exact frames; PAL3.\n'
    header+=ca('phase14GeneratorTiles','u32',struct.unpack('>'+str(len(raw)//4)+'I',raw))+ca('phase14GeneratorMap','u16',mapping)+ca('phase14GeneratorVisible','u8',visible)
    header+='static const ObjectiveArt phase14GeneratorArt={0,36,48,48};\n'
    header+='static const CampaignGroundArt phase14GeneratorGround={phase14GeneratorTiles,phase14GeneratorMap,'+str(len(tiles))+'};\n'
    return frames,raw,mapping,header,dict(size=[48,48],frames=6,tiles=len(tiles),tiles_per_frame=36,palette='PAL3',native_pixel_block=1,lossy_tile_replacements=0)
