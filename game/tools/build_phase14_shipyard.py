"""Phase14: native-detail architecture, an isolated console and seamless perimeter."""
from pathlib import Path
import argparse, hashlib, io, json, math, struct
import numpy as np
from PIL import Image, ImageDraw
from campaign_geometry import validate, free, path
from phase14_energy import conduits, generators

G = Path(__file__).resolve().parents[1]
A = G / 'art/phase14-shipyard-v2'
SOURCE = G / 'art/campaign-pattern-v2/launch/source/14-16-shipyard.png'
PALETTE = [(0,0,0),(36,36,36),(0,36,72),(36,72,109),(72,72,72),
           (109,109,109),(145,145,145),(218,218,182),(109,72,36),
           (145,109,72),(182,145,36),(255,182,36),(255,218,109),
           (72,109,145),(182,182,145),(218,182,109)]
SIZE = (512,576)
BOUNDS = [40,128,471,511]
START = [48,232]
MACHINES = [[64,168],[448,168],[400,288],[416,464],[96,464]]
SOLIDS = [[200,264,112,64],[248,232,16,32],[216,432,80,48]] + [[x-16,y-8,32,16] for x,y in MACHINES]

def export(check=False):
    def emit(p,b):
        if check: assert p.exists() and p.read_bytes()==b, ('stale phase14 export',p)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            if not p.exists() or p.read_bytes()!=b:p.write_bytes(b)
    def png(p,im):
        b=io.BytesIO();im.save(b,format='PNG');emit(p,b.getvalue())
    def js(p,d):emit(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    palette=sum(map(list,PALETTE),[])+[0]*720
    colors=np.array(PALETTE,dtype=np.int32)
    def quant(im):
        rgb=np.array(im.convert('RGB'),dtype=np.int32)
        out=Image.fromarray(((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'))
        out.putpalette(palette);return out
    source=quant(Image.open(SOURCE).convert('RGB').resize((512,384),Image.Resampling.LANCZOS))
    room=Image.new('P',SIZE,4);room.putpalette(palette)
    modules={}
    def module(name,box):
        im=source.crop(box);modules[name]=im;return im
    def repeat(im,box):
        x,y,w,h=box
        for yy in range(y,y+h,im.height):
            for xx in range(x,x+w,im.width):room.paste(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
    floor_source=A/'source/iron-floor-plate.png'
    floor=quant(Image.open(floor_source).convert('RGB').resize((64,64),Image.Resampling.NEAREST))
    # Share the literal seam pixels at all four edges of the repeated plate.
    floor.paste(floor.crop((0,0,64,1)),(0,63))
    floor.paste(floor.crop((0,0,1,64)),(63,0))
    png(A/'modules/iron-floor-plate.png',floor)
    repeat(floor,(0,0,*SIZE))
    # Upper and lower architecture are independent complete bands; no4px pass.
    bay=module('upper-engine-bay',(32,0,216,112))
    # The source cabinet starts below the bay; its cropped head is floor here.
    bay.paste(4,(8,104,40,112))
    bay_mask=Image.new('L',bay.size,255);bay_mask.paste(0,(8,104,40,112))
    room.paste(bay,(32,0),bay_mask);room.paste(bay,(296,0),bay_mask)
    room.paste(module('upper-center',(216,0,296,112)),(216,0))
    room.paste(module('upper-left-corner',(0,0,32,112)),(0,0))
    room.paste(module('upper-right-corner',(480,0,512,112)),(480,0))
    # The shared connector is literal source steel. Identical edge pixels make
    # consecutive wall modules meet without a gap, offset or flipped lighting.
    seam_checks=[]
    for side,x,box in [('left',0,(0,128,32,192)),('right',480,(480,128,512,192))]:
        im=module(side+'-boundary',box)
        im.paste(im.crop((0,0,32,1)),(0,63))
        repeat(im,(x,112,32,400))
        seam_checks.append(dict(module=side+'-boundary',axis='vertical',matching_edge_pixels=im.crop((0,0,32,1)).tobytes()==im.crop((0,63,32,64)).tobytes()))
    lower=module('lower-boundary',(32,320,144,384))
    lower.paste(lower.crop((0,0,1,64)),(111,0))
    repeat(lower,(32,512,176,64));repeat(lower,(304,512,176,64))
    seam_checks.append(dict(module='lower-boundary',axis='horizontal',matching_edge_pixels=lower.crop((0,0,1,64)).tobytes()==lower.crop((111,0,112,64)).tobytes()))
    room.paste(module('lower-door',(208,320,304,384)),(208,512))
    for name,box,xy in [('lower-left-corner',(0,304,32,384),(0,496)),('lower-right-corner',(480,304,512,384),(480,496))]:room.paste(module(name,box),xy)
    png(A/'upper.png',room.crop((0,0,512,112)))
    png(A/'lower.png',room.crop((0,496,512,576)))
    cables,cable_parts,energy=conduits(SIZE,PALETTE)
    png(A/'connections.png',cables)
    for name,im in cable_parts.items():png(A/'modules/conduits'/f'{name}.png',im)
    room.paste(quant(cables),(0,0),cables.getchannel('A'))
    # ImageGen cutout retains real alpha. Threshold only removes the soft outer
    # shadow for the indexed runtime; the original RGBA stays untouched.
    prop=Image.open(A/'source/control-station.png').convert('RGBA')
    alpha=prop.getchannel('A').point(lambda v:255 if v>=184 else 0)
    prop.putalpha(alpha);prop=prop.crop(alpha.getbbox()).resize((128,112),Image.Resampling.LANCZOS)
    mask=prop.getchannel('A').point(lambda v:255 if v>=128 else 0)
    station=quant(prop);native=station.convert('RGBA');native.putalpha(mask)
    png(A/'objects/control-station.png',native);room.paste(station,(192,224),mask)
    # Original lower tank assembly, whole and supported, with exterior concrete
    # flood-keyed exactly like the factory props.
    island=module('tank-island',(208,240,304,304))
    rgb=np.array(Image.open(SOURCE).convert('RGB').resize((512,384),Image.Resampling.LANCZOS).crop((208,240,304,304)))
    seen=set();todo=[(x,y) for x in range(96) for y in (0,63)]+[(x,y) for y in range(64) for x in (0,95)]
    while todo:
        x,y=todo.pop()
        if not(0<=x<96 and 0<=y<64) or (x,y) in seen:continue
        r,g,b=map(int,rgb[y,x])
        if max(r,g,b)-min(r,g,b)>16 or not 45<r<170:continue
        seen.add((x,y));todo.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
    mask=Image.frombytes('L',(96,64),bytes(0 if (x,y) in seen else 255 for y in range(64) for x in range(96)))
    native=island.convert('RGBA');native.putalpha(mask);png(A/'objects/tank-island.png',native);room.paste(island,(208,416),mask)
    for name,im in modules.items():png(A/'modules'/f'{name}.png',im)
    seam_checks.append(dict(module='iron-floor-plate',axis='both',matching_edge_pixels=
        floor.crop((0,0,64,1)).tobytes()==floor.crop((0,63,64,64)).tobytes() and
        floor.crop((0,0,1,64)).tobytes()==floor.crop((63,0,64,64)).tobytes()))
    assert all(c['matching_edge_pixels'] for c in seam_checks)
    png(A/'complete-native.png',room)
    frames,generator_tiles,generator_map,generator_header,generator_info=generators(A/'source/generator-native-grid.png',PALETTE)
    emit(G/'src/system/video/phase14_generator.h',generator_header.encode())
    emit(A/'native/generator-tiles.bin',generator_tiles)
    emit(A/'native/generator-map.bin',struct.pack('>'+str(len(generator_map))+'H',*generator_map))
    for i,im in enumerate(frames):png(A/'objects'/f'generator-{i}.png',im)
    sheet=Image.new('RGBA',(48*6,48))
    for i,im in enumerate(frames):sheet.alpha_composite(im.convert('RGBA'),(i*48,0))
    png(A/'generator-states.png',sheet)
    complete=room.convert('RGBA');generator=frames[0].convert('RGBA')
    for x,y in MACHINES:complete.alpha_composite(generator,((x-24)//8*8,(y-40)//8*8))
    endpoints={'console':(Image.open(A/'objects/control-station.png').convert('RGBA'),(192,224)),
               'battery':(native,(208,416))}
    endpoints.update({'station-'+str(i+1):(generator,(x-24,y-40)) for i,(x,y) in enumerate(MACHINES)})
    for connection in energy['routes']:
        for node,point in [(connection['source'],connection['points'][0]),(connection['target'],connection['points'][-1])]:
            art,(x,y)=endpoints[node];u,v=point[0]+3-x,point[1]+3-y
            assert 0<=u<art.width and 0<=v<art.height and art.getpixel((u,v))[3],('cable does not enter equipment',node,point)
    energy['all_twelve_terminals_enter_opaque_equipment']=True
    png(A/'complete-with-generators.png',complete)
    powered=room.convert('RGBA')
    for x,y in MACHINES:powered.alpha_composite(frames[3].convert('RGBA'),((x-24)//8*8,(y-40)//8*8))
    png(A/'complete-powered.png',powered)
    d=dict(size=list(SIZE),bounds=BOUNDS,start=START,solids=SOLIDS,points=[],machines=MACHINES,native_pixel_block=1,station_position=[192,224],seams=seam_checks,energy=energy,generator=generator_info)
    d['geometry']=validate(d)
    approaches=[]
    for x,y in MACHINES:
        goal=[x-8,y+24];assert free(d,*goal);approaches.append(path(d,START,goal,4))
    d['generator_routes']=approaches
    tiles=[];lookup={};mapping=[]
    for y in range(0,SIZE[1],8):
        for x in range(0,SIZE[0],8):
            raw=room.crop((x,y,x+8,y+8)).tobytes()
            if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
            mapping.append(lookup[raw])
    # Cache includes the complete conservative41x26 sub-tile viewport.
    grid=np.array(mapping).reshape(SIZE[1]//8,SIZE[0]//8);maximum=0;pose=None
    for y in range(3,(SIZE[1]-224)//8+4):
        for x in range((SIZE[0]-320)//8+1):
            count=len(np.unique(grid[y:y+26,x:x+41]))
            if count>maximum:maximum=count;pose=[x*8,(y-3)*8]
    bar_tiles=5*4
    reserved=generator_info['tiles']+bar_tiles
    cache=min(640-reserved,math.ceil((maximum+8)/16)*16)
    assert maximum<=cache and cache+reserved<=640,('phase14 visible cache overflow',maximum,cache,pose)
    raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
    words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in PALETTE]
    for name,data in [('tiles',raw),('map',struct.pack('>'+str(len(mapping))+'H',*mapping)),('palette',struct.pack('>16H',*words))]:emit(A/'native'/f'{name}.bin',data)
    restored=b''.join(b''.join(tiles[mapping[(y//8)*64+x//8]][(y%8)*8:(y%8+1)*8] for x in range(0,512,8)) for y in range(576))
    assert restored==room.tobytes(),'tile reconstruction changed pixels'
    def ca(name,kind,values):
        fmt='0x%08XUL' if kind=='u32' else '0x%04X'
        return 'static const '+kind+' '+name+'[] __attribute__((aligned(32)))={\n'+''.join(','.join(fmt%v for v in values[i:i+8])+',\n' for i in range(0,len(values),8))+'};\n'
    code='// Generated by tools/build_phase14_shipyard.py; exact native detail.\n'
    code+=ca('phase14Tiles','u32',struct.unpack('>'+str(len(raw)//4)+'I',raw))+ca('phase14Palette','u16',words)+ca('phase14Map','u16',mapping)
    code+=f'static const ArenaStream phase14Stream={{{len(tiles)}}};\nstatic const ArenaScene phase14Scene={{.tiles=phase14Tiles,.map=phase14Map,.palette=phase14Palette,.tileCount={cache},.rows=72,.cols=64,.stream=&phase14Stream,.streamOverlay=TRUE}};\n'
    code+='static const ArenaRect phase14Solids[]={'+','.join('{'+','.join(map(str,r))+',TRUE}' for r in SOLIDS)+'};\n'
    code+='const ArenaDef CAMPAIGN_LAUNCH_POWER={'+','.join(map(str,[*SIZE,*BOUNDS,*START]))+',phase14Solids,'+str(len(SOLIDS))+',&phase14Scene};\n'
    emit(G/'src/levels/campaign_launch_phase14.inc',code.encode())
    header='// Generated phase14 anchors.\n#ifndef PHASE14_LAYOUT_H\n#define PHASE14_LAYOUT_H\nstatic const s16 PHASE14_MACHINES[5][2]={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in MACHINES)+'};\n#endif\n'
    emit(G/'src/levels/phase14_layout.h',header.encode())
    d['activation']=dict(seconds=10,decay_interval_seconds=1,decay_work_seconds=1,independent_bars=5,completed_stations_do_not_decay=True)
    d['floor']=dict(module='modules/iron-floor-plate.png',size=[64,64],material='riveted iron',native_pixel_block=1,seam_edges_identical=True)
    d['memory']=dict(source_tiles=len(tiles),cache_tiles=cache,maximum_visible_patterns=maximum,maximum_camera=pose,objective_reserved_tiles=reserved,progress_bar_tiles=bar_tiles,total_resident_tiles=cache+reserved,rom_graphics_bytes=len(raw),generator_rom_bytes=len(generator_tiles),map_bytes=len(mapping)*2,heap_bytes=(len(tiles)+cache*4)*2,lossy_tile_replacements=0,pixel_exact_reconstruction=True)
    d['sources']=[dict(path=str(p.relative_to(G)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [SOURCE,A/'source/control-station.png',A/'source/generator-native-grid.png',floor_source]]
    js(A/'manifest.json',d)
    return d

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    print(json.dumps(export(args.check)['memory'],indent=2))
