"""Detailed union interior: native1px art, shared STE wall sign and two outcomes."""
from pathlib import Path
import argparse, hashlib, importlib.util, io, json, struct
import numpy as np
from PIL import Image, ImageDraw

G=Path(__file__).resolve().parents[1]
A=G/'art/phase13-union-v2'
O=G/'art/campaign-pattern-v2/resistance'
PALETTE=[(0,0,0),(36,36,36),(72,72,72),(109,109,109),(145,145,145),(182,182,145),(218,218,182),(109,72,36),(145,109,72),(182,145,109),(109,36,36),(145,72,36),(0,36,72),(36,72,109),(72,109,145),(218,182,109)]
WIDTH,HEIGHT=512,576
BOUNDS=[24,160,487,487]
START=[280,168]
SOLIDS=[[80,328,104,16,True],[216,272,104,16,True],[352,392,104,16,True]]
# Native coordinates within the complete 128x48 bench crop. Only the furniture
# silhouette comes from the source; its textured floor must not enter the room.
BENCH_OUTLINE=[(11,10),(15,10),(15,11),(109,11),(109,39),(102,39),(102,30),(17,30),(17,39),(10,39),(10,11),(11,11)]
BENCH_SHADOW=[(14,30),(108,30),(116,35),(116,41),(18,41)]
FLOOR_CELL=32
FLOOR_ORIGIN=(16,128)
# Lower silhouettes of the north fixtures, in room coordinates. Source crops
# include a strip of their old floor, which must not be kept as furniture.
NORTH_FIXTURE_RECTS=[(16,112,22,115),(23,112,26,113),(45,112,46,116),
    (47,112,155,118),(156,112,158,115),(176,112,189,113),
    (190,112,247,112),(248,112,257,114),(365,112,366,116),
    (367,112,475,118),(476,112,478,115)]
NORTH_COUNTER_OUTLINE=[(258,112),(372,112),(372,136),(369,140),
    (265,140),(259,137),(259,133),(258,132)]
NORTH_MODULES=['locker-window-left','locker-window-right','banner','pulpit']
spec=importlib.util.spec_from_file_location('scene_pack',G/'art/campaign-whole-scenes-v1/pack.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def export(check=False):
    def emit(path,data):
        if check:assert path.exists() and path.read_bytes()==data,('stale phase13 export',path)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists() or path.read_bytes()!=data:path.write_bytes(data)
    def png(path,im):
        b=io.BytesIO();im.save(b,format='PNG');emit(path,b.getvalue())
    def js(path,data):emit(path,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
    sources=[]
    def asset(path):
        sources.append(dict(path=str(path.relative_to(G)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        return Image.open(path).convert('RGBA')
    colors=np.array(PALETTE,dtype=np.int32)
    def quant(im):
        rgb=np.array(im.convert('RGB'),dtype=np.int32)
        out=Image.fromarray(((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(3).argmin(2).astype('uint8'))
        out.putpalette(sum(map(list,PALETTE),[])+[0]*720);return out
    def cut(path,w,h):
        im=asset(path);alpha=im.getchannel('A').point(lambda v:255 if v>=184 else 0)
        im.putalpha(alpha);im=im.crop(alpha.getbbox());im.thumbnail((w,h),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(w,h));out.alpha_composite(im,((w-im.width)//2,h-im.height));return out
    source=asset(O/'source/13A-union.png')
    # Original approved room, sampled at native resolution, no2px/4px blocks.
    q=P.indexed(source,(512,384),1,palette=PALETTE)[0]
    floor=q.getpixel((192,144))
    room=Image.new('P',(WIDTH,HEIGHT),floor);room.putpalette(q.getpalette())
    placements=[('locker-window-left',(16,0,176,128),(16,0)),('locker-window-right',(16,0,176,128),(336,0)),('banner',(176,0,264,128),(176,0)),('booth-beam',(256,0,384,24),(256,0)),('pulpit',(256,24,384,152),(256,24)),('corner-nw',(0,0,16,128),(0,0)),('corner-ne',(496,0,512,128),(496,0)),('corner-sw',(0,296,32,384),(0,488)),('corner-se',(480,296,512,384),(480,488)),('south-left',(32,304,208,384),(32,496)),('south-right',(32,304,208,384),(304,496)),('door',(208,296,304,384),(208,488)),('bench-left',(72,240,200,288),(72,304)),('bench-center',(72,240,200,288),(208,248)),('bench-right',(72,240,200,288),(344,368))]
    for name,rect,xy in placements:
        part=q.crop(rect)
        if name.startswith('bench-'):
            # Compose furniture only after the continuous floor is in place.
            continue
        if name not in NORTH_MODULES:png(A/'modules'/f'{name}.png',part)
        room.paste(part,xy)
    for y in range(128,512,64):
        for x in [0,496]:room.paste(q.crop((0,128,16,192)),(x,y))
    # Repeat a native 64px module, using only the room's existing gray palette.
    # The connected flat-floor mask keeps the source architecture and wear.
    floor_tile=Image.new('P',(FLOOR_CELL*2,FLOOR_CELL*2));floor_tile.putpalette(q.getpalette())
    fd=ImageDraw.Draw(floor_tile)
    for row in range(2):
        for col in range(2):
            x,y=col*FLOOR_CELL,row*FLOOR_CELL
            shade=4 if (row+col)%2==0 else 3
            fd.rectangle((x,y,x+31,y+31),fill=shade)
            fd.line((x,y,x+31,y),fill=2)
            fd.line((x,y,x,y+31),fill=2)
            # Sparse one-pixel scuffs; no random noise or new colors.
            for dx,dy in [(7,9),(23,25),(15,20)]:
                fd.point((x+dx,y+dy),fill=shade-1)
    floor_pattern=Image.new('P',room.size);floor_pattern.putpalette(q.getpalette())
    for y in range(FLOOR_ORIGIN[1]%64-64,HEIGHT,64):
        for x in range(FLOOR_ORIGIN[0]%64-64,WIDTH,64):floor_pattern.paste(floor_tile,(x,y))
    connected=room.copy();ImageDraw.floodfill(connected,(192,144),255)
    floor_mask=Image.fromarray(np.where(np.array(connected)==255,255,0).astype('uint8'))
    md=ImageDraw.Draw(floor_mask)
    md.rectangle((0,0,WIDTH-1,111),fill=0)
    md.rectangle((0,496,WIDTH-1,HEIGHT-1),fill=0)
    md.rectangle((0,0,15,HEIGHT-1),fill=0)
    md.rectangle((496,0,WIDTH-1,HEIGHT-1),fill=0)
    north_floor_mask=Image.new('L',room.size);nf=ImageDraw.Draw(north_floor_mask)
    nf.rectangle((16,112,495,155),fill=255)
    for rect in NORTH_FIXTURE_RECTS:nf.rectangle(rect,fill=0)
    nf.polygon(NORTH_COUNTER_OUTLINE,fill=0)
    # Override the entire old material, including non-gray wear and baked shade.
    floor_mask.paste(north_floor_mask.crop((16,112,496,156)),(16,112))
    room.paste(floor_pattern,(0,0),floor_mask)
    png(A/'modules/floor-checker-64x64.png',floor_tile)
    png(A/'modules/floor-checker-mask.png',floor_mask)
    shade_lut=[max(0,i-1) if i<=4 else i for i in range(256)]
    north_structure=Image.new('L',room.size);ns=ImageDraw.Draw(north_structure)
    ns.rectangle((16,108,495,111),fill=255)
    for rect in NORTH_FIXTURE_RECTS:ns.rectangle(rect,fill=255)
    ns.polygon(NORTH_COUNTER_OUTLINE,fill=255)
    def north_shade(offset):
        shifted=Image.new('L',room.size);shifted.paste(north_structure,offset)
        return Image.fromarray(np.minimum(np.array(shifted),np.array(north_floor_mask)))
    north_cast=north_shade((3,4));north_contact=north_shade((0,1))
    for mask in [north_cast,north_contact]:room.paste(room.point(shade_lut),(0,0),mask)
    for name,mask in [('floor',north_floor_mask),('fixture-silhouette',north_structure),
                      ('cast-shadow',north_cast),('contact-shadow',north_contact)]:
        png(A/f'modules/north-{name}-mask.png',mask)
    for name,rect,(x,y) in placements:
        if name in NORTH_MODULES:
            png(A/'modules'/f'{name}.png',room.crop((x,y,x+rect[2]-rect[0],y+rect[3]-rect[1])))
    # Clean source matte and baked shadows before adding new floor-aware shade.
    # Both supports use the intact left metal foot; the former right crop also
    # contained source-floor fragments that cannot be part of its silhouette.
    bench=q.crop((72,240,200,288))
    bench.paste(bench.crop((10,31,18,40)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(102,31))
    bench_mask=Image.new('L',bench.size);bm=ImageDraw.Draw(bench_mask)
    bm.rectangle((11,10,15,10),fill=255)
    bm.rectangle((10,11,109,30),fill=255)
    for x in [10,102]:bm.rectangle((x,31,x+7,39),fill=255)
    shadow_mask=Image.new('L',bench.size);ImageDraw.Draw(shadow_mask).polygon(BENCH_SHADOW,fill=255)
    contact_mask=Image.new('L',bench.size);cm=ImageDraw.Draw(contact_mask)
    for x in [10,102]:cm.rectangle((x,38,x+9,40),fill=255)
    # Darken each existing gray by one step, preserving tile seams and scuffs.
    for name,rect,(x,y) in placements:
        if not name.startswith('bench-'):continue
        clean=room.crop((x,y,x+128,y+48))
        clean.paste(clean.point(shade_lut),(0,0),shadow_mask)
        clean.paste(clean.point(shade_lut),(0,0),contact_mask)
        clean.paste(bench,(0,0),bench_mask)
        png(A/'modules'/f'{name}.png',clean);room.paste(clean,(x,y))
    png(A/'modules/bench-silhouette-mask.png',bench_mask)
    png(A/'modules/bench-cast-shadow-mask.png',shadow_mask)
    png(A/'modules/bench-contact-shadow-mask.png',contact_mask)
    # Keep the complete cloth and its frame; clear only the former insignia.
    room.paste(10,(196,20,244,84))
    logo=cut(G/'art/space-workers-union-logo-v1/logo-ste.png',48,56)
    rgba=room.convert('RGBA');rgba.alpha_composite(logo,(196,24));room=quant(rgba)
    # Exact approved character pixels, never recolored to the room palette.
    master=G/'art/cangaco-parceira-iso60-v1'
    din=asset(master/'parceira/directions/parceira_S.png').crop((0,0,32,48))
    north=Image.open(master/'parceira/directions/parceira_N.png')
    asset(master/'parceira/directions/parceira_N.png')
    helmet=Image.new('P',(24,16),0);helmet.putpalette(north.getpalette());helmet.info['transparency']=0
    # Complete hat from the approved north pose; no face, weapon or new colors.
    helmet.paste(north.crop((5,12,21,24)),(4,2))
    png(A/'sprites/dinorah-room-32x48.png',din);png(A/'sprites/dinorah-helmet-24x16.png',helmet);png(A/'sprites/STE-wall-sign.png',logo)
    alive=room.convert('RGBA');alive.alpha_composite(din,(300,76))
    # The counter's complete ledge/front is foreground, occluding her waist.
    alive.paste(room.crop((256,108,384,152)),(256,108))
    dead=room.convert('RGBA');dead.alpha_composite(helmet.convert('RGBA'),(304,92))
    previews={'alive':alive,'dead':dead}
    for name,im in previews.items():png(A/f'13{"A" if name=="alive" else "B"}-complete-native.png',im)
    png(A/'north-floor-fit-preview.png',alive.crop((0,0,WIDTH,176)))
    # PAL2 props are hardware sprites. Both PAL3 backgrounds stay identical.
    hat=np.array(helmet);hatraw=b''
    for x in range(0,24,8):
        for y in range(0,16,8):
            t=hat[y:y+8,x:x+8].flatten()
            hatraw+=bytes((int(t[i])<<4)|int(t[i+1]) for i in range(0,64,2))
    emit(A/'native/headgear.bin',hatraw)
    emit(G/'src/levels/union_headgear.inc',P.c_array('union_headgear','u32',struct.unpack('>48I',hatraw)).encode())
    png(A/'common-room.png',room)
    images={'alive':room,'dead':room};tiles=[];lookup={};maps={}
    for name,im in images.items():
        pixels=np.array(im);mapping=[]
        for y in range(0,HEIGHT,8):
            for x in range(0,WIDTH,8):
                raw=pixels[y:y+8,x:x+8].tobytes()
                if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
                mapping.append(lookup[raw])
        maps[name]=mapping
        png(A/f'native/{name}-native.png',im)
        emit(A/f'native/{name}.bin',struct.pack('>'+str(len(mapping))+'H',*mapping))
        restored=Image.new('P',(WIDTH,HEIGHT));restored.putpalette(im.getpalette())
        for i,t in enumerate(mapping):restored.paste(Image.frombytes('P',(8,8),tiles[t]),(i%64*8,i//64*8))
        assert restored.tobytes()==im.tobytes(),'native reconstruction changed pixels'
    # Source IDs have no H/V flags: production cache copies exact ROM tiles.
    raw=b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles)
    emit(A/'native/tiles.bin',raw)
    words=[(round(r*7/255)<<1)|(round(g*7/255)<<5)|(round(b*7/255)<<9) for r,g,b in PALETTE]
    emit(A/'native/palette.bin',struct.pack('>16H',*words))
    peaks=[]
    for name,mapping in maps.items():
        m=np.array(mapping).reshape(HEIGHT//8,WIDTH//8);maximum=0;pose=None
        for row in range(3,(HEIGHT-224)//8+4):
            for col in range((WIDTH-320)//8+1):
                count=len(np.unique(m[row:min(row+26,HEIGHT//8),col:min(col+41,WIDTH//8)]))
                if count>maximum:maximum=count;pose=[col*8,(row-3)*8]
        peaks.append(dict(phase='13A' if name=='alive' else '13B',patterns=maximum,conservative_camera=pose))
    assert max(v['patterns'] for v in peaks)<=640,('union cache exceeds640',peaks)
    arrays=P.c_array('union_tiles','u32',struct.unpack('>'+str(len(raw)//4)+'I',raw)).replace('union_tiles[]={','union_tiles[] __attribute__((aligned(32)))={')
    arrays+=P.c_array('union_palette','u16',words)
    for name,mapping in maps.items():arrays+=P.c_array('union_'+name,'u16',mapping)
    arrays+='static const ArenaStream unionStream={'+str(len(tiles))+'};\n'
    for name in maps:
        arrays+='static const ArenaScene '+name+'Scene={.tiles=union_tiles,.map=union_'+name+',.palette=union_palette,.tileCount=640,.rows='+str(HEIGHT//8)+',.cols='+str(WIDTH//8)+',.stream=&unionStream,.streamOverlay=TRUE};\n'
    # Collision, artwork and both variants share the generated room geometry.
    arrays+='static const ArenaRect unionSolids[]={'+','.join('{'+','.join(map(str,r[:4]))+',TRUE}' for r in SOLIDS)+'};\n'
    for name,variant in [('alive','ALIVE'),('dead','DEAD')]:
        arrays+='const ArenaDef CAMPAIGN_RESISTANCE_UNION_'+variant+'={'+','.join(map(str,[WIDTH,HEIGHT,*BOUNDS,*START]))+',unionSolids,3,&'+name+'Scene};\n'
    emit(G/'src/levels/campaign_resistance_phase13.inc',('// Detailed union interior; generated by tools/build_phase13_union.py.\n'+arrays).encode())
    manifest=dict(phases=['13A','13B'],size=[WIDTH,HEIGHT],bounds=BOUNDS,start=START,solids=SOLIDS,targets={'13A':30,'13B':45},native_pixel_block=1,camera_policy='player-only body center; same stable follow as stages 1–12',camera_player_y=0,camera_south_start=0,palette=PALETTE,complete_source_preserved=True,modules=placements,logo={'box':[196,24,48,56],'source':'../space-workers-union-logo-v1/logo-ste.png'},dinorah={'sprite':'sprites/dinorah-room-32x48.png','box':[300,80,32,48],'occluded_below_y':108,'protected_behind_counter':True,'static_scene_character':True},memorial={'sprite':'sprites/dinorah-helmet-24x16.png','box':[304,92,24,16],'portrait':False,'candles':False},memory=dict(source_tiles=len(tiles),cache_tiles=640,cache_vram_bytes=640*32,maximum_visible_patterns=max(v['patterns'] for v in peaks),minimum_cache_spare=640-max(v['patterns'] for v in peaks),viewport_peaks=peaks,cache_heap_bytes=(len(tiles)+640*4)*2,graphics_rom_bytes=len(raw),maps_rom_bytes=sum(len(m)*2 for m in maps.values()),palette_bytes=32,pixel_exact_reassembly=True,lossy_pattern_replacements=0),sources=sources,status='integrated-local; awaiting visual review')
    manifest['dinorah'].update(box=[300,76,32,48],static_scene_character=False,hardware_sprite=True,palette='PAL2; original actor palette',source='cangaco-parceira-iso60-v1/parceira/directions/parceira_S.png',source_pose=0,pixel_changes=0)
    manifest['memorial'].update(hardware_sprite=True,palette='PAL2; original actor palette',source='cangaco-parceira-iso60-v1/parceira/directions/parceira_N.png',crop=[5,12,21,24],pixel_changes=0,description='Original Dinorah headgear; not a newly invented hard hat')
    manifest['memory'].update(additional_vram_bytes=0,headgear_rom_bytes=len(hatraw),actor_frame_rom_bytes_added=0,prop_uses_existing_dinorah_reservation=True)
    manifest['bench_composition']={'source_floor_removed':True,'source_shadows_removed':True,'outline':BENCH_OUTLINE,'cast_shadow':BENCH_SHADOW,'silhouette_mask':'modules/bench-silhouette-mask.png','cast_shadow_mask':'modules/bench-cast-shadow-mask.png','contact_shadow_mask':'modules/bench-contact-shadow-mask.png','shadow_method':'darken underlying floor gray by one palette step; additional contact shade at feet','checker_seams_preserved_under_shadow':True,'seat_and_frame_pixels_preserved':True,'right_foot':'mirrored clean left support','collision_changes':False}
    manifest['floor']={'style':'worn gray checkerboard','cell_size':[FLOOR_CELL,FLOOR_CELL],'repeat_size':[64,64],'origin':FLOOR_ORIGIN,'palette_indices':{'light':4,'dark':3,'grout':2},'module':'modules/floor-checker-64x64.png','mask':'modules/floor-checker-mask.png','native_pixel_block':1,'shared_between_variants':True,'continuous_under_benches':True,'collision_changes':False}
    manifest['north_composition']={'old_floor_and_baked_shadows_removed':True,'cleanup_box':[16,112,496,156],'fixture_rectangles':NORTH_FIXTURE_RECTS,'counter_outline':NORTH_COUNTER_OUTLINE,'floor_mask':'modules/north-floor-mask.png','cast_shadow_mask':'modules/north-cast-shadow-mask.png','contact_shadow_mask':'modules/north-contact-shadow-mask.png','shadow_offset':[3,4],'checker_origin_unchanged':True,'fixture_pixels_preserved':True,'collision_changes':False}
    js(A/'manifest.json',manifest)
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    print(json.dumps(export(args.check)['memory'],indent=2))
