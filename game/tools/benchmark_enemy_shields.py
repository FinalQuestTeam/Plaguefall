"""Controlled 4/8-enemy shield benchmark in the production campaign loop.

Run with arch -x86_64 /usr/bin/python3. Entry uses controls; RAM setup
keeps targets alive, disables spawning/summoning and pins shield state.
FPS counts game updates against physical VBlanks, never host speed.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, re, statistics, struct, subprocess, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--build-dir',type=Path)
    parser.add_argument('--combat',action='store_true',help='Eight grouped shielded enemies with sustained projectile loads')
    parser.add_argument('--frames',type=int,default=1800)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--formations',default='all',help='Combat subset: Baluarte,Fortaleza,Escudeiro,mixed')
    parser.add_argument('--loads',default='0,6,16')
    parser.add_argument('--allow-profile',action='store_true',help='Diagnostic timings only; exclude from final FPS evidence')
    parser.add_argument('--audit-sprites',action='store_true',help='Read the live hardware sprite chain and verify bodies, bullets and scanline limits')
    args=parser.parse_args()
    assert args.frames>=120 and args.repeats>=1
    fps=50 if args.pal else 60
    out=args.output;out.mkdir(parents=True,exist_ok=True)
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
    fmt=0;raw=None;w=h=pitch=0;buttons=set()
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
    @SAMPLE
    def sample(l,r):pass
    @BATCH
    def batch(ptr,n):return n
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
    syms={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:
            addr,size,kind,name=parts
            syms[name]=(int(addr,16)&65535,int(size,16))
            syms[name.split('.lto_priv.')[0]]=syms[name]
            if name.split('.lto_priv.')[0]=='state' and int(size,16)==4:syms['flow_state']=syms[name]
    ram=(C.c_ubyte*core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    def run(n=1):
        for _ in range(n):core.retro_run()
    for _ in range(8*fps):
        if bytes(ram[syms['fps'][0]:syms['fps'][0]+2]) in (struct.pack('<H',fps),struct.pack('>H',fps)):break
        run()
    swapped=bytes(ram[syms['fps'][0]:syms['fps'][0]+2])==struct.pack('<H',fps)
    def read(addr,n):return bytes(ram[((addr+i)&65535)^int(swapped)] for i in range(n))
    def write(addr,value):
        for i,v in enumerate(value):ram[((addr+i)&65535)^int(swapped)]=v
    def u8(name):return read(syms[name][0],1)[0]
    def u16(name):return int.from_bytes(read(syms[name][0],2),'big')
    def u32(name):return int.from_bytes(read(syms[name][0],4),'big')
    def w16(name,value):write(syms[name][0],struct.pack('>H',value&65535))
    def grant_hit_immunity():
        # LTO may swap the private suffixes of player/NPC invTimer variables.
        # Phase 1 has no NPC: initialize every matching timer instead of
        # accidentally granting only the inactive NPC invulnerability.
        addresses={addr for name,(addr,size) in syms.items()
                   if name.split('.lto_priv.')[0]=='invTimer' and size==2}
        assert addresses,'no invulnerability timer found'
        for addr in addresses:write(addr,struct.pack('>H',60000))
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
    assert u8('currentLevel')==1 and u16('arenaMaxX')==495
    baseline=snapshot()
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    if args.combat:
        assert u16('fps')==fps and abs(av.timing.fps-fps)<1,'wrong emulator region'
        assert args.allow_profile or not any(name in syms for name in ('renderProfileTicks','logicProfileTicks')),'use an uninstrumented build'
        report={'region_fps':fps,'rom_sha256':hashlib.sha256(original).hexdigest(),
                'emulated_rom_sha256':hashlib.sha256(data).hexdigest(),'core':str(CORE),
                'benchmark_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'frames_per_case':args.frames,'repeats':args.repeats,'cases':[],
                'method':'Production phase-1 loop, 8 initially overlapping shielded enemies; normal movement, separation, collision, rendering, audio and HUD. RAM setup disables new spawns and summons, pins enemy shields and grants player hit immunity. A is held in projectile cases. Moving player/enemy projectiles replenish inactive slots up to 6 or 16 per pool before each physical frame. Purple enemies do not gain a shooting behaviour: enemy bullets are an injected load. Zero-projectile controls do not hold A. 180 physical warmup frames; FPS counts phaseStats updates / vtimer VBlanks. This is controlled stress, not a normal campaign attempt.'}
        def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
        slot_addr,slot_bytes=syms['slots'];assert slot_bytes==16*16
        def graphics():
            records=read(slot_addr,8*16)
            tiles=[int.from_bytes(records[i*16+12:i*16+14],'big') for i in range(8) if records[i*16+10]]
            return len(tiles),len(set(tiles))
        if args.audit_sprites:
            vram=(C.c_ubyte*65536).in_dll(core,'vram')
            layout=(build.parents[1]/'src/system/video/sprites/tiles.h').read_text()
            def tile_constant(name):return int(re.search(r'^#define\s+'+name+r'\s+(\d+)',layout,re.M).group(1))
            shot_base=16+tile_constant('NUM_TILES')+tile_constant('ENEMY_CACHE_TILES')+15*tile_constant('ENEMY_ICON_TILES')-15
            def audit_sprites():
                records=read(slot_addr,8*16)
                body_tiles={16+int.from_bytes(records[i*16+12:i*16+14],'big') for i in range(8) if records[i*16+10]}
                index=0;visited=set();bodies=set();bullets=[0,0];counts=[0]*224;widths=[0]*224
                while True:
                    assert index<80 and index not in visited,('invalid SAT link',index)
                    visited.add(index)
                    base=u16('slist_addr')+index*8
                    entry=bytes(vram[((base+j)&65535)^1] for j in range(8))
                    tile=int.from_bytes(entry[4:6],'big')&2047
                    if tile in body_tiles:bodies.add(tile)
                    if shot_base<=tile<shot_base+15:bullets[int(tile>=shot_base+3)]+=1
                    x=(int.from_bytes(entry[6:8],'big')&511)-128
                    y=(int.from_bytes(entry[:2],'big')&511)-128
                    width=(((entry[2]>>2)&3)+1)*8;height=((entry[2]&3)+1)*8
                    if x<320 and x+width>0:
                        for line in range(max(0,y),min(224,y+height)):
                            counts[line]+=1;widths[line]+=width
                    index=entry[3]&127
                    if not index:break
                assert max(counts)<=20 and max(widths)<=320,('SAT scanline overflow',max(counts),max(widths))
                return len(bodies),*bullets,len(visited)
        def active_shots(name):
            address,size=syms[name];assert size==320
            return sum(read(address+i*20+18,1)[0]!=0 for i in range(16))
        def geometry():
            records=[read(enemy_addr+i*stride,stride) for i in range(8)]
            assert all(r[44] and r[42] and r[30] in (2,6,10) for r in records),'enemy/shield state changed'
            boxes=[(*struct.unpack_from('>hh',r),16 if r[30]==6 else 32) for r in records]
            span=(max(x+s for x,y,s in boxes)-min(x for x,y,s in boxes),
                  max(y+s for x,y,s in boxes)-min(y for x,y,s in boxes))
            visible=sum(x+s>u16('cameraX') and x<u16('cameraX')+320 and
                        y-16+s>u16('cameraY')+24 and y-16<u16('cameraY')+224 for x,y,s in boxes)
            return span,visible
        def seed_shots(load):
            for pool,name in enumerate(('pshots','eshots')):
                address=syms[name][0]
                for i in range(load):
                    if read(address+i*20+18,1)[0]:continue
                    # Stagger lifetimes so every pool stays busy as old bullets
                    # hit shields, the player or the arena boundary.
                    x=136+(i%8)*34;y=(136+(i*11)%40) if pool else (200+(i*7)%24)
                    buf=bytearray(20)
                    struct.pack_into('>iiii',buf,0,x*64,y*64,0,128 if pool else -192)
                    buf[16],buf[17],buf[18]=(1+i%3 if pool else 0),10,1
                    write(address+i*20,buf)
        formations=[('Baluarte',[2]*8),('Fortaleza',[10]*8),('Escudeiro',[6]*8),('Baluarte + Fortaleza',[2,10]*4)]
        if args.formations!='all':
            wanted=args.formations.split(',')
            formations=[(label,kinds) for label,kinds in formations if label in wanted or (label=='Baluarte + Fortaleza' and 'mixed' in wanted)]
            assert formations,'no matching formations'
        shot_loads=[int(v) for v in args.loads.split(',')];assert shot_loads and all(v in (0,6,16) for v in shot_loads)
        try:
            for label,kinds in formations:
              for load in shot_loads:
               for repeat in range(args.repeats):
                restore(baseline);w16('spawnTimer',60000);w16('kills',0)
                for name in ('enemies','pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
                pos(256,160);w16('freezeTimer',0);grant_hit_immunity()
                w16('faceX',0);w16('faceY',1)
                for i,kind in enumerate(kinds):
                    buf=bytearray(stride);x,y=240+(i%4)*12,184+(i//4)*12
                    struct.pack_into('>hhii',buf,0,x,y,x*64,y*64)
                    struct.pack_into('>HH',buf,16,60000,i)
                    struct.pack_into('>HH',buf,24,60000,60000)
                    buf[30],buf[31],buf[42],buf[43],buf[44]=kind,200,1,1,1
                    write(enemy_addr+i*stride,buf)
                initial_span,_=geometry()
                if load:buttons.add(1) # libretro A -> the normal autofire path
                for _ in range(180):seed_shots(load);run()
                begin,vb=frames(),u32('vtimer');loads=[];occupancy=[[],[]];spans=[];visibility=[];firing=set();gfx_samples=[];timings={};sat_samples=[]
                for _ in range(args.frames):
                    seed_shots(load);run()
                    loads.append(u16('cpuFrameLoad')*100/2048)
                    for pool,name in enumerate(('pshots','eshots')):occupancy[pool].append(active_shots(name))
                    span,visible=geometry();spans.append(span);visibility.append(visible)
                    gfx_samples.append(graphics())
                    if args.audit_sprites:sat_samples.append(audit_sprites())
                    firing.add(u16('shotCooldown'))
                    for name in ('renderProfileTicks','logicProfileTicks'):
                        if name in syms:
                            addr,size=syms[name];timings.setdefault(name,[]).append(struct.unpack('>'+str(size//2)+'H',read(addr,size)))
                    assert u32('flow_state')==1 and u8('currentLevel')==1,'benchmark left campaign'
                    assert u16('hp')==100,'player hit immunity was not maintained'
                elapsed=u32('vtimer')-vb;drawn=frames()-begin
                both=sum(a>0 and b>0 for a,b in zip(*occupancy))
                assert sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16))==8,'population changed'
                assert min(visibility)==8,'enemies left viewport'
                assert all(x<=128 and y<=128 for x,y in spans),'group dispersed'
                if load:
                    assert both==args.frames,('projectile load was not sustained',both,args.frames,
                                             [(min(v),round(statistics.mean(v),2),max(v)) for v in occupancy])
                    assert len(firing)>1,'normal autofire did not run'
                else:assert not any(occupancy[0]+occupancy[1]),'control has projectiles'
                item={'formation':label,'repeat':repeat+1,'enemies':8,'shields':8,'shot_target_per_pool':load,
                      'physical_frames':elapsed,'game_frames':drawn,'fps':round(fps*drawn/elapsed,2),
                      'target_fps':fps,'target_met':drawn==elapsed,
                      'cpu_mean':round(statistics.mean(loads),2),'cpu_p95':round(sorted(loads)[int(len(loads)*.95)],2),
                      'shots_after_step':[{'min':min(v),'mean':round(statistics.mean(v),2),'max':max(v)} for v in occupancy],
                      'both_projectile_pools_nonempty_frames':both,'all_enemies_visible_frames':sum(v==8 for v in visibility),
                      'initial_group_span':initial_span,'max_group_span':[max(v[i] for v in spans) for i in range(2)],
                      'ready_enemy_frames_min':min(v[0] for v in gfx_samples),
                      'distinct_graphics_mean':round(statistics.mean(v[1] for v in gfx_samples),2),
                      'distinct_graphics_min':min(v[1] for v in gfx_samples),
                      'distinct_graphics_max':max(v[1] for v in gfx_samples),
                      'autofire_observed':len(firing)>1 if load else False}
                for name,samples in timings.items():item[name]=[round(statistics.mean(v[i] for v in samples),2) for i in range(len(samples[0]))]
                if sat_samples:
                    assert min(v[0] for v in sat_samples)==8,'a live enemy body was missing from the SAT'
                    if load:assert all(statistics.mean(v[i] for v in sat_samples)>0 for i in (1,2)),'a projectile pool was never rendered'
                    item['hardware_sprites']={'enemy_bodies_min':min(v[0] for v in sat_samples),
                        'player_bullets_mean':round(statistics.mean(v[1] for v in sat_samples),2),
                        'enemy_bullets_mean':round(statistics.mean(v[2] for v in sat_samples),2),
                        'sat_count_max':max(v[3] for v in sat_samples),'scanline_limits_checked':True}
                report['cases'].append(item)
                print(json.dumps(item),flush=True)
                if repeat==0:shot('combat-type-'+str(kinds[0])+'-load-'+str(load)+('-mixed' if len(set(kinds))>1 else ''))
                (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            report['test_completed']=True
            report['performance_target_met']=all(c['target_met'] for c in report['cases'] if c['shot_target_per_pool'])
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        finally:
            core.retro_unload_game();core.retro_deinit()
        return
    results=[]
    for kind in (1,2,6,10):
      for count in (4,8):
       for shield in (0,1):
        restore(baseline)
        w16('spawnTimer',60000);w16('kills',0)
        for name in ('enemies','pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
        pos(256,160);w16('freezeTimer',0);grant_hit_immunity()
        for i in range(count):
            addr=syms['enemies'][0]+i*46;buf=bytearray(46)
            x,y=160+(i%4)*60,192+(i//4)*40
            struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6)
            struct.pack_into('>HH',buf,16,60000,i)
            struct.pack_into('>HH',buf,24,60000,60000)
            buf[30],buf[31],buf[43],buf[44]=kind,200,1,1
            write(addr,buf)
        def step():
            w16('hp',100)
            for i in range(count):write(syms['enemies'][0]+i*46+42,bytes([shield]))
            run()
        for _ in range(120):step()
        start=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big');vb=u32('vtimer');loads=[];profiles=[];logic_profiles=[]
        for _ in range(600):
            step();loads.append(u16('cpuFrameLoad')*100/2048)
            if 'renderProfileTicks' in syms:
                addr,size=syms['renderProfileTicks'];profiles.append(struct.unpack('>'+str(size//2)+'H',read(addr,size)))
            if 'logicProfileTicks' in syms:logic_profiles.append(struct.unpack('>4H',read(syms['logicProfileTicks'][0],8)))
        assert u32('flow_state')==1 and u8('currentLevel')==1,'benchmark left active campaign'
        assert sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16))==count,'enemy count changed'
        item={'type':kind,'count':count,'shield':shield,'fps':round(fps*(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-start)/(u32('vtimer')-vb),2),'physical_frames':u32('vtimer')-vb,'game_frames':int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-start,'cpu_mean':round(statistics.mean(loads),2),'cpu_p95':round(sorted(loads)[570],2)}
        if profiles:item['render_subticks']=[round(statistics.mean(p[i] for p in profiles),2) for i in range(len(profiles[0]))]
        if logic_profiles:item['logic_subticks']=[round(statistics.mean(p[i] for p in logic_profiles),2) for i in range(4)]
        results.append(item);print(item,flush=True)
        if count==8:shot('type-'+str(kind)+'-shield-'+str(shield))
        (out/'report.json').write_text(json.dumps({'region_fps':fps,'rom_sha256':hashlib.sha256(original).hexdigest(),'core':str(CORE),'instrumented':'renderProfileTicks' in syms,'method':'Production phase 1, no shooting or new spawns; 120 physical warmup frames and 600 measured frames. RAM injects 4/8 live enemies (HP 200), disables summon/shield timers, grants player hit immunity and forces enemy shield state. Movement, separation, animation, sprite admission, audio and HUD run normally. Game updates / physical VBlanks measure FPS. This is a controlled stress test, not a normal campaign attempt.','cases':results},indent=2)+'\n')
    (out/'report.json').write_text(json.dumps({'region_fps':fps,'rom_sha256':hashlib.sha256(original).hexdigest(),'core':str(CORE),'instrumented':'renderProfileTicks' in syms,'method':'Production phase 1, no shooting or new spawns; 120 physical warmup frames and 600 measured frames. RAM injects 4/8 live enemies (HP 200), disables summon/shield timers, grants player hit immunity and forces enemy shield state. Movement, separation, animation, sprite admission, audio and HUD run normally. Game updates / physical VBlanks measure FPS. This is a controlled stress test, not a normal campaign attempt.','cases':results},indent=2)+'\n')
    core.retro_unload_game();core.retro_deinit()


if __name__=="__main__":main()
