"""Campaign factory phases in the supplied build. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
"""
from pathlib import Path
from campaign_geometry import faces,edges
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--shield-tests',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/campaign-factory-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
    build=args.build_dir or GAME/'out/release';rom=build/'rom.bin';original=rom.read_bytes();data=bytearray(original)
    if args.pal:data[0x1f0:0x200]=b'E               '
    core=C.CDLL(str(CORE))
    class Info(C.Structure):_fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
    class Geometry(C.Structure):_fields_=[('base_width',C.c_uint),('base_height',C.c_uint),('max_width',C.c_uint),('max_height',C.c_uint),('aspect_ratio',C.c_float)]
    class Timing(C.Structure):_fields_=[('fps',C.c_double),('sample_rate',C.c_double)]
    class AVInfo(C.Structure):_fields_=[('geometry',Geometry),('timing',Timing)]
    class Variable(C.Structure):_fields_=[('key',C.c_char_p),('value',C.c_char_p)]
    ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p);VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
    SAMPLE=C.CFUNCTYPE(None,C.c_int16,C.c_int16);BATCH=C.CFUNCTYPE(C.c_size_t,C.POINTER(C.c_int16),C.c_size_t)
    POLL=C.CFUNCTYPE(None);INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
    fmt=0;raw=None;w=h=pitch=0;buttons=set();record=False;encoder=None;audio=None
    @ENV
    def env(command,ptr):
        nonlocal fmt
        command&=65535
        if command==10:fmt=C.cast(ptr,C.POINTER(C.c_int))[0];return fmt in (0,1,2)
        if command==15:
            v=C.cast(ptr,C.POINTER(Variable));key=v[0].key;v[0].value=None
            if key==b'genesis_plus_gx_region_detect':v[0].value=b'pal' if args.pal else b'ntsc-u';return True
            return False
        if command in (9,31):C.cast(ptr,C.POINTER(C.c_char_p))[0]=b'/private/tmp';return True
        if command==3:C.cast(ptr,C.POINTER(C.c_bool))[0]=True;return True
        if command==39:C.cast(ptr,C.POINTER(C.c_uint))[0]=0;return True
        if command==47:C.cast(ptr,C.POINTER(C.c_int))[0]=3;return True
        return command in (8,11,16,18,35,37)
    @VIDEO
    def video(ptr,width,height,stride):
        nonlocal raw,w,h,pitch
        if not ptr or ptr==C.c_void_p(-1).value:return
        w,h,pitch=width,height,stride;raw=C.string_at(ptr,stride*height)
        if record and encoder:
            assert fmt==2 and (w,h)==(320,224)
            encoder.stdin.write(b''.join(raw[y*stride:y*stride+w*2] for y in range(h)))
    @SAMPLE
    def sample(l,r):
        if record and audio:audio.writeframesraw(struct.pack('<hh',l,r))
    @BATCH
    def batch(ptr,n):
        if record and audio:audio.writeframesraw(C.string_at(ptr,n*4))
        return n
    @POLL
    def poll():pass
    @INPUT
    def input_state(port,device,index,button):return int(port==0 and button in buttons)
    for name,cb in [('environment',env),('video_refresh',video),('audio_sample',sample),('audio_sample_batch',batch),('input_poll',poll),('input_state',input_state)]:getattr(core,'retro_set_'+name)(cb)
    core.retro_load_game.argtypes=[C.POINTER(Info)];core.retro_load_game.restype=C.c_bool
    core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p
    core.retro_get_memory_size.argtypes=[C.c_uint];core.retro_get_memory_size.restype=C.c_size_t
    core.retro_init();buffer=C.create_string_buffer(bytes(data));assert core.retro_load_game(C.byref(Info(str(rom).encode(),C.cast(buffer,C.c_void_p),len(data),None)))
    core.retro_get_system_av_info.argtypes=[C.POINTER(AVInfo)];av=AVInfo();core.retro_get_system_av_info(C.byref(av))
    symbols=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(build/'rom.out')],text=True)
    syms={};rom_syms={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:
            addr,size,kind,name=parts
            rom_syms[name]=(int(addr,16),int(size,16));rom_syms[name.split('.lto_priv.')[0]]=rom_syms[name]
            syms[name]=(int(addr,16)&65535,int(size,16))
            syms[name.split('.lto_priv.')[0]]=syms[name]
            if name.split('.lto_priv.')[0]=='state' and int(size,16)==4:syms['flow_state']=syms[name]
    ram=(C.c_ubyte*core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    vram=(C.c_ubyte*65536).in_dll(core,'vram')
    def vw(address):return vram[address]+(vram[address+1]<<8)
    def run(n=1):
        for _ in range(n):core.retro_run()
    for _ in range(8*fps):
        if bytes(ram[syms['fps'][0]:syms['fps'][0]+2]) in (struct.pack('<H',fps),struct.pack('>H',fps)):break
        run()
    swapped=bytes(ram[syms['fps'][0]:syms['fps'][0]+2])==struct.pack('<H',fps)
    def read(addr,n):return bytes(ram[((addr+i)&65535)^int(swapped)] for i in range(n))
    ordinary=False
    writes=0
    def write(addr,value):
        nonlocal writes
        assert not ordinary,'RAM write attempted during ordinary match'
        writes+=1
        for i,v in enumerate(value):ram[((addr+i)&65535)^int(swapped)]=v
    def u8(name):return read(syms[name][0],1)[0]
    def u16(name):return int.from_bytes(read(syms[name][0],2),'big')
    def u32(name):return int.from_bytes(read(syms[name][0],4),'big')
    def w16(name,value):write(syms[name][0],struct.pack('>H',value&65535))
    def settle():
        initial=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
        for _ in range(120):
            run()
            if int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-initial>=4:return
        raise AssertionError('game update stalled')
    def pos(x,y):
        w16('px',x);w16('py',y);write(syms['pfx'][0],struct.pack('>i',x<<6));write(syms['pfy'][0],struct.pack('>i',y<<6))
    def hold(keys,n):buttons.update(keys);run(n);buttons.clear();run(2)
    def press(key):hold({key},2)
    def rgb():
        result=bytearray(w*h*3)
        for y in range(h):
            for x in range(w):
                if fmt==1:b,g,r,_=raw[y*pitch+x*4:y*pitch+x*4+4]
                else:
                    value=struct.unpack_from('<H',raw,y*pitch+x*2)[0]
                    if fmt==2:r,g,b=(value>>11&31)*255//31,(value>>5&63)*255//63,(value&31)*255//31
                    else:r,g,b=(value>>10&31)*255//31,(value>>5&31)*255//31,(value&31)*255//31
                result[(y*w+x)*3:(y*w+x+1)*3]=bytes((r,g,b))
        return bytes(result)
    def shot(name):png(out/(name+'.png'),w,h,rgb())
    core.retro_serialize_size.restype=C.c_size_t
    core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_serialize.restype=C.c_bool
    core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool
    def snapshot():
        size=core.retro_serialize_size();statebuf=C.create_string_buffer(size)
        assert core.retro_serialize(statebuf,size)
        return statebuf
    def restore(statebuf):
        buttons.clear();assert core.retro_unserialize(statebuf,len(statebuf))
        run(2)
    # Skip boot, enter NEW GAME, skip mission call, start phase 1 with A.
    run(120);press(3);run(fps*4)
    for _ in range(6):
        if u8('arenaActive') and u32('flow_state')==1:break
        press(3);run(fps)
        if u8('arenaActive') and u32('flow_state')==1:break
        press(1);run(fps*4)
    if not (u8('arenaActive') and u32('flow_state')==1):shot('startup-failed');raise AssertionError(('start',u8('state'),u8('currentLevel'),u8('arenaActive')))
    assert u8('currentLevel')==1 and u16('arenaMaxX')==487
    shot('01-inicio')
    baseline=snapshot()
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    # Node setup is accelerated through existing campaign progression. Tests
    # below distinguish controller-only attempts from explicit RAM probes.
    import re
    node_names=re.search(r'typedef enum\s*\{(.*?)NODE_MAX', ((build.parents[1]/'src/levels/graph.h') if (build.parents[1]/'src/levels/graph.h').exists() else GAME/'src/levels/graph.h').read_text(), re.S)[1]
    node_ids={name:i+1 for i,name in enumerate(re.findall(r'\bN_[A-Za-z0-9]+\b',node_names))}
    report={'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),'passed':False,'nodes':{},'method':'RAM seeds node entry and explicit isolated probes; objective execution uses controller input. Stress is RAM seeded, FPS measures simulation frames per VBlank.'}
    def save(): (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def state():return u32('flow_state')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def w32(name,value):write(syms[name][0],struct.pack('>I',value))
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def clear_enemies():
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
    def cr8(offset):return read(syms['campaignResistance'][0]+offset,1)[0]
    def enter(node):
        nonlocal ordinary
        ordinary=False;restore(baseline);w16('hp',100);w16('kills',999)
        if 'surviveLeft' in syms:w16('surviveLeft',1)
        # Finish the real1->2A story/map before changing pending node. Editing
        # it during ROUTEMAP preparation strands its temporary overlay buffer.
        for _ in range(60):
            if state()==0:break
            if state() in (4,6):press(3)
            elif state()==5:press(1)
            run(fps//2)
        assert state()==0,('prep entry',state())
        write(syms['pendingLevel'][0],bytes([node]));press(1);run(fps*4)
        assert state()==1 and u8('currentLevel')==node,('entry',node,state(),u8('currentLevel'))
        buttons.clear()
        for _ in range(fps*10):
            if u16('freezeTimer')==0 and frames()>5:break
            run()
        assert u16('freezeTimer')==0
        return snapshot()
    geom=json.loads((GAME/'art/campaign-factory-v1/geometry.json').read_text())
    street_geometry={'bounds':[16,geom['street_min_y'],geom['street_size'][0]-17,geom['street_max_y']],'solids':geom['street_solids']}
    report['scene_export_sha256']=hashlib.sha256((GAME/'art/campaign-pattern-v2/factory/export.json').read_bytes()).hexdigest()
    report['geometry_sha256']=hashlib.sha256((GAME/'art/campaign-factory-v1/geometry.json').read_bytes()).hexdigest()
    def cf8(offset):return read(syms['campaignFactory'][0]+offset,1)[0]
    def cf16(offset):return int.from_bytes(read(syms['campaignFactory'][0]+offset,2),'big')
    def isolate():
        nonlocal ordinary
        ordinary=False;clear_enemies();w16('hp',100);w16('spawnTimer',60000)
    def move_to(tx,ty):
        for _ in range(fps*30):
            dx=tx-signed('px');dy=ty-signed('py');keys=set()
            if abs(dx)<=3 and abs(dy)<=3:break
            if dx>3:keys.add(7)
            elif dx< -3:keys.add(6)
            if dy>3:keys.add(5)
            elif dy< -3:keys.add(4)
            buttons.clear();buttons.update(keys);run()
            if state()!=1:break
        buttons.clear();run(2)
    def native_graphics(label):
        # Production atlas bytes and every visible BG_B cell, including H/V
        # attributes, must agree with the ROM data. Objectives occupy BG_A.
        scene='street' if label=='9' else 'factory';base_tile=785
        paletteaddr,_=rom_syms[scene+'Palette'];palette_zero=int.from_bytes(original[paletteaddr:paletteaddr+2],'big')
        tileaddr,tilesize=rom_syms[scene+'Tiles'];expected=original[tileaddr:tileaddr+tilesize]
        got=bytes(vram[(base_tile*32+i)^1] for i in range(tilesize))
        differing=[i for i in range(tilesize//32) if got[i*32:(i+1)*32]!=expected[i*32:(i+1)*32]]
        mapaddr,mapsize=rom_syms[scene+'Map'];mp=struct.unpack('>'+str(mapsize//2)+'H',original[mapaddr:mapaddr+mapsize]);cols=320 if label=='9' else 96;rows=geom['street_size'][1]//8 if label=='9' else geom['factory_size'][1]//8
        left,top=signed('cameraX')//8,signed('cameraY')//8;plane=u16('bgb_addr');errors=[];flipped=0;checked=0
        for row in range(top,min(rows,top+28)):
            for col in range(left,min(cols,left+40)):
                attr=mp[row*cols+col];wanted=(base_tile+attr)|0x6000;actual=vw(plane+((row&31)*64+(col&63))*2)
                checked+=1;flipped+=bool(attr&0x1800)
                if actual!=wanted:errors.append([col,row,actual,wanted])
        return {'passed':not differing and not errors and palette_zero==0,'palette_index_zero_black':palette_zero==0,'scene_tiles':tilesize//32,'atlas_bytes_compared':tilesize,'atlas_differing_tiles':differing[:16],'visible_cells_checked':checked,'visible_flipped_cells':flipped,'tilemap_errors':errors[:16],'camera':[signed('cameraX'),signed('cameraY')],'method':'exact ROM-to-VRAM comparison of scene atlas and BG_B H/V attributes; palette index0 must be black because it is transparent on hardware'}
    for label,cap,shotcap in [('9',3,4),('10',4,6),('11',3,6)]:
        if label=='9':continue  # Current streamed street has its dedicated suite below.
        node=node_ids['N_'+label];r={};report['nodes'][label]=r
        base=enter(node);shot(label+'-entry')
        r['entry']={'passed':True,'enemy_cap':cap,'shot_cap':shotcap,'width':2560 if label=='9' else 768}
        r['native_graphics_entry']=native_graphics(label)
        isolate()
        if label=='9':
            ordinary=True
            for i,(x,y) in enumerate(geom['street_controller_waypoints']):
                move_to(x,y)
                if i==0:shot('9-obstacle-detour');r['native_graphics_obstacle']=native_graphics(label)
                if i==len(geom['street_controller_waypoints'])//2:shot('9-camera-middle');r['native_graphics_middle']=native_graphics(label)
            shot('9-camera-exit');r['native_graphics_exit']=native_graphics(label)
            move_to(*geom['street_finish']);run(fps)
            r['controller_corridor']={'passed':state()!=1,'ending_x':signed('px'),'detour_waypoints':geom['street_controller_waypoints'],'method':'controller only after isolated spawn-delay setup; authored sectors require detours around architecture'}
        elif label=='10':
            ordinary=False;w16('kills',999);run(2)
            r['kills_do_not_count']={'passed':cf8(29)==0 and state()==1}
            hits=[]
            for i,(x,y) in enumerate(geom['eggs']):
                ordinary=False;pos(x-72,y-8);w16('faceX',1);w16('faceY',0);run(3)
                ordinary=True;hold({1},fps*3);hits.append(cf8(12+i)==0)
                shot('10-eggs-'+str(i+1))
                if i==1:r['native_graphics_south']=native_graphics(label)
            r['controller_egg_hits']={'passed':all(hits) and cf16(0)==1023,'destroyed_mask':cf16(0),'hits':hits,'method':'RAM position setup per clutch; controller firing with ordinary write guard; no objective-state seeds'}
            ordinary=False;restore(base);isolate();w16('bombs',1);cx=signed('cameraX');cy=signed('cameraY')
            expected=sum(1<<i for i,(x,y) in enumerate(geom['eggs']) if cx<=x<cx+320 and cy+24<=y<cy+224)
            ordinary=True;press(0);run(fps)
            r['controller_bomb']={'passed':cf16(0)==expected,'destroyed_mask':cf16(0),'expected_visible_mask':expected,'setup':'one bomb seeded, controller B activates; only viewport eggs may die'}
            beforemask=cf16(0);press(3);run(fps*2);pause_state=state();paused=state()==2;shot('10-paused');press(3);run(fps*2)
            heap_blocks=[];heap_address=u32('heap')&65535
            for _ in range(80):
                bsize=int.from_bytes(read(heap_address,2),'big')
                if not bsize:break
                heap_blocks.append([heap_address,bsize]);heap_address=(heap_address+(bsize&65534))&65535
            r['pause_persistence']={'heap_blocks':heap_blocks,'passed':paused and state()==1 and cf16(0)==beforemask,'destroyed_mask':cf16(0),'paused_state':pause_state,'resumed_state':state(),'heap_pointer':u32('heap'),'saved_pointer':u32('saved'),'mission_map_pointer':u32('missionMap'),'loading_saved_pointer':u32('savedTiles'),'loading_active':u8('loadingActive'),'result_active':u8('resultActive'),'card_pointer':u32('card')};shot('10-resumed')
        else:
            results=[]
            for i,(x,y) in enumerate(geom['valves']):
                ordinary=False;pos(*geom['valve_approaches'][i]);run(2);before=cf16(4+i*2)
                ordinary=True;buttons.update({1});run(fps);after=cf16(4+i*2)
                buttons.clear();run(fps*2);results.append({'valve':i,'fire_blocks_work':after==before,'opened':bool(cf16(2)&(1<<i))})
                if i<2:move_to(x+48,geom['valve_approaches'][i][1])
                shot('11-valve-'+str(i+1))
            r['controller_valves']={'passed':all(v['opened'] and v['fire_blocks_work'] for v in results),'probes':results,'opened_mask':cf16(2),'method':'RAM position per valve; runtime interaction and A rejection controller only'}
        ordinary=False;restore(base);isolate();solids=geom['street_solids'] if label=='9' else geom['factory_solids'];collisions=[]
        collision_geometry=street_geometry if label=='9' else {'bounds':[16,geom['factory_min_y'],767-16,geom['factory_max_y']],'solids':solids}
        for x,y,button,axis,limit,sign in faces(collision_geometry):
            ordinary=False;pos(x,y);ordinary=True;hold({button},fps//2)
            value=signed(axis);passed=value<=limit if sign==1 else value>=limit
            collisions.append({'approach':[x,y],'direction':button,'passed':passed,'end':[signed('px'),signed('py')]})
        r['controller_collision']={'passed':all(p['passed'] for p in collisions),'probes':collisions}
        if label=='9':
            baseline_probes=[]
            y=geom['street_baseline_y']
            for x,sy,w0,h0 in solids:
                if not(sy<y+16 and sy+h0>y):continue
                from campaign_geometry import free
                if not free(street_geometry,x-24,y):continue
                ordinary=False;pos(x-24,y);ordinary=True;hold({7},fps//2)
                baseline_probes.append({'obstacle_x':x,'passed':signed('px')+16<=x,'position':[signed('px'),signed('py')]})
            r['straight_route_blocked']={'passed':bool(baseline_probes) and all(p['passed'] for p in baseline_probes),'probes':baseline_probes,'method':'RIGHT at entry walking height must meet visible architecture along the route'}
        # Real architecture occupies the north frontage / southern retaining
        # wall. Their walk boundaries need controller probes as well as benches.
        minimum=geom.get('street_min_y',96) if label=='9' else geom.get('factory_min_y',80)
        maximum=geom.get('street_max_y',303) if label=='9' else geom.get('factory_max_y',367)
        width=2560 if label=='9' else 768
        bounds=[]
        for x,y,button,axis,limit in edges(collision_geometry):
            ordinary=False;restore(base);isolate();pos(x,y);ordinary=True;hold({button},fps//2)
            bounds.append({'edge':button,'passed':signed(axis)==limit,'position':[signed('px'),signed('py')]})
        r['controller_world_bounds']={'passed':all(p['passed'] for p in bounds),'probes':bounds}
        ordinary=False;restore(base);ordinary=True
        initial=frames();vb=u32('vtimer');active_end_frames=initial;active_end_vb=vb;peak=0;hpstart=signed('hp')
        if args.movie:
            encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb565le','-s','320x224','-r',str(fps),'-i','-','-an','-vf','scale=640:448:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(label+'-playtest.mp4'))],stdin=subprocess.PIPE);record=True
        for tick in range(fps*20):
            buttons.clear();buttons.update({1,[7,5,6,4][(tick//(fps*2))%4]});run()
            peak=max(peak,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
            if signed('hp')>0:active_end_frames=frames();active_end_vb=u32('vtimer')
            if state()!=1:break
        if args.movie:record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
        r['difficulty_sample']={'controller_only':True,'duration_seconds':round((active_end_vb-vb)/fps,2),'video_duration_seconds':round((u32('vtimer')-vb)/fps,2),'result':'defeat' if signed('hp')<=0 else 'timeout','remaining_hp':signed('hp'),'damage_net':hpstart-signed('hp'),'peak_enemies':peak,'simulation_fps':round(fps*(active_end_frames-initial)/max(1,active_end_vb-vb),2),'fps_measurement':'Active gameplay only; death settling freezes phaseStats and is excluded','scope':'Up to20s movement/fire patrol bot pressure sample; does not attempt the route or provide a human difficulty rating'}
        ordinary=False;restore(base);clear_enemies();w16('hp',30000);initial=frames();vb=u32('vtimer');peak=0
        for tick in range(fps*20):
            if tick%fps==0:w16('hp',30000)
            run();peak=max(peak,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
        r['saturation']={'passed':peak<=cap,'peak_enemies':peak,'cap':cap,'simulation_fps':round(fps*(frames()-initial)/max(1,u32('vtimer')-vb),2),'setup':'health reseed only; normal production spawning, no shooting'};shot(label+'-saturation')
        restore(base);clear_enemies()
        def formation():
            w16('hp',30000)
            for i in range(cap):
                x,y=24+i*56,184;buf=bytearray(stride);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,16,0,600,600)
                buf[30],buf[31],buf[43],buf[44]=[4,5,2][i%3],250,1,1;write(enemy_addr+i*stride,buf)
            for name in ('pshots','eshots'):
                address,size=syms[name]
                for i in range(shotcap):
                    buf=bytearray(20);struct.pack_into('>iiii',buf,0,(32+i*40)<<6,(160+(i%2)*24)<<6,32,0);buf[17],buf[18]=1,1;write(address+i*20,buf)
        for _ in range(30):formation();run()
        initial=frames();vb=u32('vtimer');loads=[]
        for _ in range(fps*5):
            formation();run()
            if 'cpuFrameLoad' in syms:loads.append(u16('cpuFrameLoad')*100/2048)
        measured=round(fps*(frames()-initial)/max(1,u32('vtimer')-vb),2)
        r['visible_maximum_stress']={'passed':measured>=fps*.95,'simulation_fps':measured,'seeded_visible_enemies':cap,'seeded_player_shots':shotcap,'seeded_enemy_shots':shotcap,'cpu_mean_percent':round(statistics.mean(loads),2) if loads else None,'cpu_peak_percent':round(max(loads),2) if loads else None,'setup':'RAM seeded full formations and pools each frame; stress only'}
        save()
    report['passed']=all(v.get('passed',True) for node in report['nodes'].values() for v in node.values());save();print(json.dumps(report,indent=2))
    core.retro_unload_game();core.retro_deinit()
    import sys
    target=out/'phase09-current'
    command=[sys.executable,str(GAME/'tools/test_phase09_stream_emulator.py'),'--output',str(target),'--build-dir',str(build)]
    if args.pal:command.append('--pal')
    result=subprocess.run(command,check=False)
    native=json.loads((target/'report.json').read_text()) if (target/'report.json').exists() else {}
    report['nodes']['9']={'dedicated_native_suite':{'passed':result.returncode==0 and native.get('passed') is True,'report':'phase09-current/report.json'}}
    report['passed']=report['passed'] and report['nodes']['9']['dedicated_native_suite']['passed'];save()
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
