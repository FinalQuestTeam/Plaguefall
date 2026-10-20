"""Technical export only: crop, register, nearest-neighbour scale, index and pack.
Creative poses come from image_gen originals. Western facings use horizontal
symmetry; never synthesize a south-facing view with a vertical flip.
"""
from pathlib import Path
import hashlib
import json
import struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
DIRS = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]
CANON = [0, 1, 2, 3, 4, 3, 2, 1]
PALETTE = [
    (0,0,0), (219,219,182), (36,182,219), (182,36,36),
    (219,182,36), (219,109,0), (73,109,109), (146,182,182),
    (109,73,146), (146,73,36), (73,36,0), (0,0,0),
    (219,109,36), (146,146,146), (73,146,36), (36,73,182),
]
LEVELS = [0,36,73,109,146,182,219,255]

def indexed(rgba):
    out = Image.new("P", rgba.size)
    out.putpalette([c for rgb in PALETTE for c in rgb] + [0]*720)
    cache = {}
    pixels = []
    for pixel in rgba.getdata():
        if pixel[3] < 128:
            pixels.append(0)
            continue
        rgb = pixel[:3]
        if rgb not in cache:
            cache[rgb] = min(range(1,16), key=lambda i: sum((rgb[c]-PALETTE[i][c])**2 for c in range(3)))
        pixels.append(cache[rgb])
    out.putdata(pixels)
    out.info["transparency"] = 0
    return out

def row_edges(image, rows):
    alpha = image.getchannel("A")
    w,h = image.size
    data = alpha.tobytes()
    counts = [sum(v>=128 for v in data[y*w:(y+1)*w]) for y in range(h)]
    edges = [0]
    for r in range(1,rows):
        target = h*r/rows
        lo,hi = round(target-h/rows*.16),round(target+h/rows*.16)
        edges.append(min(range(lo,hi),key=lambda y:(counts[y],abs(y-target))))
    return edges+[h]

def connected_components(mask):
    width,height=mask.size
    pixels=bytearray(mask.tobytes())
    components=[]
    for seed in range(len(pixels)):
        if not pixels[seed]: continue
        stack=[seed];pixels[seed]=0;component=[]
        while stack:
            pos=stack.pop();component.append(pos)
            x,y=pos%width,pos//width
            for ny in range(max(0,y-1),min(height,y+2)):
                for nx in range(max(0,x-1),min(width,x+2)):
                    neighbor=ny*width+nx
                    if pixels[neighbor]:
                        pixels[neighbor]=0;stack.append(neighbor)
        components.append(component)
    return components

def clean_source_mask(mask):
    """Discard disconnected fragments from neighboring generated atlas rows."""
    width,height=mask.size
    components=connected_components(mask)
    if not components:return mask
    main=max(components,key=len)
    main_box=(min(p%width for p in main),min(p//width for p in main),
              max(p%width for p in main),max(p//width for p in main))
    tolerance=max(3,round(width*.04))
    minimum=max(16,round(max(map(len,components))*.03))
    cleaned=bytearray(width*height)
    for component in components:
        box=(min(p%width for p in component),min(p//width for p in component),
             max(p%width for p in component),max(p//width for p in component))
        gap=max(main_box[0]-box[2],box[0]-main_box[2],main_box[1]-box[3],box[1]-main_box[3],0)
        if len(component)>=minimum and gap<=tolerance:
            for pos in component:cleaned[pos]=255
    return Image.frombytes("L",mask.size,bytes(cleaned))

def source_poses(row,expected=10,minimum=8):
    """Isolate bodies by alpha connectivity, including interleaved appendages."""
    mask=row.getchannel("A").point(lambda a:255 if a>=128 else 0)
    groups=connected_components(mask)
    # Some generated legs bridge neighboring poses by a few pixels. Split only
    # components wider than a full pose at their low-density alpha separator.
    split=[]
    nominal=row.width/expected
    for group in groups:
        left=min(p%row.width for p in group);right=max(p%row.width for p in group)+1
        if right-left>nominal*1.35:
            counts=[0]*(right-left)
            for p in group:counts[p%row.width-left]+=1
            center=(left+right)/2
            lo=max(left+1,round(center-nominal*.22));hi=min(right-1,round(center+nominal*.22))
            cut=min(range(lo,hi),key=lambda x:(counts[x-left],abs(x-center)))
            split.extend([[p for p in group if p%row.width<cut],[p for p in group if p%row.width>=cut]])
        else:split.append(group)
    groups=sorted((g for g in split if g),key=len,reverse=True)
    count=min(expected,sum(len(g)>=len(groups[0])*.30 for g in groups))
    if count<minimum:
        raise ValueError(("Insufficient separate pose bodies",count,minimum))
    def bbox(g):
        return (min(p%row.width for p in g),min(p//row.width for p in g),
                max(p%row.width for p in g)+1,max(p//row.width for p in g)+1)
    primary=sorted(groups[:count],key=lambda g:(bbox(g)[0]+bbox(g)[2])/2)
    boxes=[bbox(g) for g in primary]
    assigned=[list(g) for g in primary]
    tolerance=max(3,round(row.width/10*.04))
    for g in groups[count:]:
        # Extra complete poses must not be reattached as appendage fragments.
        if len(g)>=len(groups[0])*.30:continue
        if len(g)<max(16,round(len(groups[0])*.03)):continue
        b=bbox(g)
        gaps=[max(bb[0]-b[2],b[0]-bb[2],bb[1]-b[3],b[1]-bb[3],0) for bb in boxes]
        index=min(range(count),key=lambda j:(gaps[j],abs((boxes[j][0]+boxes[j][2])-(b[0]+b[2]))))
        if gaps[index]<=tolerance:assigned[index].extend(g)
    result=[]
    for g in assigned:
        b=bbox(g);pixels=bytearray(row.width*row.height)
        for pos in g:pixels[pos]=255
        isolated=row.copy();isolated.putalpha(Image.frombytes("L",row.size,bytes(pixels)))
        result.append({"image":isolated.crop(b),"bounds":b,"clipped_right":b[2]==row.width})
    return result

def pack(image, pieces):
    data = bytearray()
    for x0,y0,w,h in pieces:
        for tx in range(x0,x0+w,8):
            for ty in range(y0,y0+h,8):
                for y in range(ty,ty+8):
                    for x in range(tx,tx+8,2):
                        data.append((image.getpixel((x,y))<<4)|image.getpixel((x+1,y)))
    return data

def frame_bytes(frame):
    return pack(frame,[(0,0,32,32),(0,32,32,16)])

def export(e):
    source = ROOT/"originals"/(e["id"]+".png")
    image = Image.open(source).convert("RGBA")
    rows = 5
    edges = row_edges(image,rows)
    poses, bounds = [], []
    repair_path = ROOT/"originals"/(e["id"]+"-camera.png")
    repair = Image.open(repair_path).convert("RGBA") if e["id"].startswith("pen_") and repair_path.exists() else None
    repair_edges = row_edges(repair,5) if repair else None
    run_path=ROOT/"originals"/(e["id"]+"-east-run.png")
    run_poses=[]
    if run_path.exists():
        run_image=Image.open(run_path).convert("RGBA")
        run_edges=row_edges(run_image,2)
        for rr in range(2):
            for pose in source_poses(run_image.crop((0,run_edges[rr],run_image.width,run_edges[rr+1])),3,3):
                pose["row_origin"]=run_edges[rr]
                run_poses.append(pose)
    for r in range(5):
        active_image=repair if repair and r==2 else image
        active_edges=repair_edges if repair and r==2 else edges
        active_source=repair_path if repair and r==2 else source
        source_row=active_image.crop((0,active_edges[r],active_image.width,active_edges[r+1]))
        extracted=source_poses(source_row)
        good=[i for i,pose in enumerate(extracted) if not pose["clipped_right"]]
        if len(good)<6:raise ValueError((e["id"],r,"Too few intact source poses"))
        pose_map=good[:4]+good[-6:]
        run_scale=(sum(extracted[i]["image"].width for i in good[:4])/4)/(sum(p["image"].width for p in run_poses)/6) if r==2 and run_poses else None
        row = []
        for c in range(10):
            source_col = pose_map[c]
            source_layout_adjusted=len(good)!=10
            b=extracted[source_col]["bounds"]
            box=(b[0],active_edges[r]+b[1],b[2],active_edges[r]+b[3])
            crop=extracted[source_col]["image"].copy()
            pose_source=active_source
            ratio=image.width/active_image.width
            if r==2 and c>=4 and run_poses:
                source_col=c-4
                selected=run_poses[source_col]
                b=selected["bounds"];origin=selected["row_origin"]
                box=(b[0],origin+b[1],b[2],origin+b[3])
                crop=selected["image"].copy()
                pose_source=run_path
                ratio=run_scale
                source_layout_adjusted=False
            mask = crop.getchannel("A").point(lambda a:255 if a>=128 else 0)
            original_count=sum(a!=0 for a in mask.tobytes())
            mask = clean_source_mask(mask)
            removed=original_count-sum(a!=0 for a in mask.tobytes())
            crop.putalpha(mask)
            bbox = mask.getbbox()
            if not bbox:
                raise ValueError((e["id"],r,c,"empty source cell"))
            trimmed = crop.crop(bbox)
            if ratio!=1:
                trimmed = trimmed.resize((max(1,round(trimmed.width*ratio)),max(1,round(trimmed.height*ratio))),Image.Resampling.NEAREST)
            row.append(trimmed)
            bounds.append({"dir":r,"pose":c,"source_cell":list(box),"trim":list(bbox),"source_pose":source_col,
                "source_file":str(pose_source.relative_to(ROOT)),"detached_source_pixels_removed":removed,
                "source_layout_adjusted":source_layout_adjusted,
                "reused_idle_pose_for_movement":c>=4 and source_col in pose_map[:4] and pose_source==active_source})
        poses.append(row)
    scale = min(30/max(f.width for row in poses for f in row),
                44/max(f.height for row in poses for f in row))
    canonical = []
    for row in poses:
        frames = []
        for f in row:
            f = f.resize((max(1,round(f.width*scale)),max(1,round(f.height*scale))),Image.Resampling.NEAREST)
            f = f.crop(f.getchannel("A").getbbox())
            cell = Image.new("RGBA",(32,48))
            # Stable ground line and horizontal registration. No artificial bounce.
            cell.paste(f,((32-f.width)//2,47-f.height))
            frames.append(indexed(cell))
        canonical.append(frames)
    folder = ROOT/"enemies"/e["id"]
    (folder/"directions").mkdir(parents=True,exist_ok=True)
    (folder/"previews").mkdir(exist_ok=True)
    master = Image.new("P",(192,768))
    master.putpalette(canonical[0][0].getpalette())
    turn = Image.new("P",(256,48)); turn.putpalette(master.getpalette())
    for d in range(8):
        frames = canonical[CANON[d]]
        if d>=5:
            frames = [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in frames]
        sheet = Image.new("P",(192,96)); sheet.putpalette(master.getpalette())
        for p,f in enumerate(frames):
            row,col = (0,p) if p<4 else (1,p-4)
            sheet.paste(f,(col*32,row*48))
        name = e["id"]+"_"+DIRS[d]+".png"
        sheet.save(folder/"directions"/name,bits=4,transparency=0)
        master.paste(sheet,(0,d*96)); turn.paste(frames[0],(d*32,0))
    master.save(folder/(e["id"]+".png"),bits=4,transparency=0)
    turn.save(folder/(e["id"]+"_turntable.png"),bits=4,transparency=0)
    turn.convert("RGBA").resize((1024,192),Image.Resampling.NEAREST).save(folder/"previews"/"turntable-4x.png")
    gif = []
    for p in range(6):
        canvas = Image.new("RGB",(1024,192),(24,24,36))
        for d in range(8):
            f = master.crop((p*32,d*96+48,p*32+32,d*96+96)).convert("RGBA")
            f = f.resize((128,192),Image.Resampling.NEAREST)
            canvas.paste(f,(d*128,0),f)
        gif.append(canvas)
    gif[0].save(folder/"previews"/"movement-4x.gif",save_all=True,append_images=gif[1:],duration=100,loop=0,disposal=2)
    raw = bytearray()
    for d in range(5):
        for frame in canonical[d]:
            raw.extend(frame_bytes(frame))
    icon_size = 32 if e["id"] in ("sq_purple","pen_purple","boss") else 24 if e["family"]=="pen" else 16
    icon = canonical[4][0].convert("RGBA")
    icon = icon.crop(icon.getchannel("A").getbbox())
    ratio = min(icon_size/icon.width,icon_size/icon.height)
    icon = icon.resize((max(1,round(icon.width*ratio)),max(1,round(icon.height*ratio))),Image.Resampling.NEAREST)
    canvas = Image.new("RGBA",(icon_size,icon_size))
    canvas.paste(icon,((icon_size-icon.width)//2,icon_size-icon.height))
    icon_raw = pack(indexed(canvas),[(0,0,icon_size,icon_size)])
    icon_raw.extend(bytes(512-len(icon_raw)))
    return raw,icon_raw,{"id":e["id"],"original":str(source.relative_to(ROOT)),
        "source_size":list(image.size),"source_row_bounds":edges,"scale":scale,
        "cells":bounds,"canonical_directions":["N","NE","L","SE","S"],
        "horizontal_mirrors":{"SO":"SE","O":"L","NO":"NE"},
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest()}

def main():
    catalog = json.loads((ROOT/"catalog.json").read_text())
    available = [e for e in catalog if (ROOT/"originals"/(e["id"]+".png")).exists()]
    raw,icons,reports = bytearray(),bytearray(15*512),[]
    for e in available:
        frames,icon,report = export(e)
        # Fixed 13 resource slots; boss data index12, project enemy index14.
        index = catalog.index(e)
        report["runtime_data_index"] = index
        report["runtime_offset"] = index*50*768
        while len(raw)<index*50*768:
            raw.extend(bytes(50*768))
        raw.extend(frames)
        enemy_index = 14 if e["id"]=="boss" else index
        icons[enemy_index*512:(enemy_index+1)*512] = icon
        reports.append(report)
        print("Exported",e["id"],flush=True)
    (ROOT/"validation"/"export.json").write_text(json.dumps(reports,indent=2)+"\n")
    (ROOT/"palette.json").write_text(json.dumps(PALETTE,indent=2)+"\n")
    (ROOT/"palette.gpl").write_text("GIMP Palette\nName: RedRex Cangaco shared PAL1\nColumns: 4\n#\n"+
        "\n".join(f"{r:3d} {g:3d} {b:3d} index{i}" for i,(r,g,b) in enumerate(PALETTE))+"\n")
    res = "// Optional SGDK Sprite Engine resources, not linked into the manual streaming renderer.\n"
    for e in available:
        res += f'SPRITE insect_{e["id"]} "enemies/{e["id"]}/{e["id"]}.png" 4 6 FAST 6 NONE BALANCED FAST\n'
    (ROOT/"enemies.res").write_text(res)
    if len(available)==13:
        output = ROOT/"runtime"
        output.mkdir(exist_ok=True)
        (output/"frames.bin").write_bytes(raw)
        (output/"icons.bin").write_bytes(icons)
        palette = b"".join(struct.pack(">H", (round(r/255*7)<<1)|(round(g/255*7)<<5)|(round(b/255*7)<<9)) for r,g,b in PALETTE)
        (output/"palette.bin").write_bytes(palette)
        (GAME/"res"/"insects.res").write_text('BIN insect_frames "insects/frames.bin" 4\nBIN insect_icons "insects/icons.bin" 4\nBIN insect_palette "insects/palette.bin" 2\n')
        print("Runtime ROM data:",len(raw)+len(icons)+len(palette),"bytes")

if __name__=="__main__":
    main()
