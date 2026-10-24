"""Production-ROM verification of the ten-room training suite.

Run with arch -x86_64 /usr/bin/python3. Room/settings menus and the gallery use
only controls. Isolated contact, pickup and terrain probes declare RAM setup.
"""
from pathlib import Path
import re, argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);parser.add_argument('--only-deaths',action='store_true');parser.add_argument('--only-death-rules',action='store_true');parser.add_argument('--only-santa',action='store_true');parser.add_argument('--only-routes',action='store_true');parser.add_argument('--only-terrain',action='store_true');args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/training-v2/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    syms={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:
            addr,size,kind,name=parts
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
    allow_writes=False
    def write(addr,value):
        assert allow_writes,'RAM writes forbidden outside isolated probes'
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

    def setkeys(keys,n=1):
        buttons.clear();buttons.update(keys);run(n)
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def facing():return signed('faceX'),signed('faceY')
    def wait_for(predicate,limit):
        for _ in range(limit):
            if predicate():return
            run()
        shot('timeout');raise AssertionError(('timeout',u8('currentLevel'),facing()))
    core.retro_serialize_size.restype=C.c_size_t
    core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_serialize.restype=C.c_bool
    core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool

    def state():return u32('flow_state')
    def snap():
        n=core.retro_serialize_size();buf=C.create_string_buffer(n);assert core.retro_serialize(buf,n);return buf
    def restore(buf):
        buttons.clear();assert core.retro_unserialize(buf,len(buf));run(2)
    def active():return sum(read(syms['enemies'][0]+i*46+44,1)[0]!=0 for i in range(16))
    def wait(predicate,label,limit=240):
        for _ in range(limit):
            if predicate():return
            run()
        shot('FAIL-'+label);raise AssertionError((label,state(),u8('testStage'),u8('currentLevel')))
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def pause():
        ui(3);wait(lambda:state()==2,'pause');run(10)
    def switch(room):
        current=u8('testStage');pause();ui(5,3);ui(1);run(15)
        ui(5,(room-current)%18);ui(1);run(fps)
        wait(lambda:state()==1 and u8('testStage')==room,'switch-room')
        assert u8('currentLevel')==0
    def configure(changes,action=None):
        pause();ui(5);ui(1);run(10);row=0
        for target,delta in changes:
            ui(5,target-row);row=target
            ui(7 if delta>0 else 6,abs(delta))
        if action is not None:ui(5,action-row)
        if args.only_deaths:shot('death-configuration')
        if args.only_deaths and action is not None:press(1);run(1)
        else:ui(1);run(4 if action is not None else fps)
        wait(lambda:state()==1,'configuration')
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),
            'method':'Menu entry, room switching, settings and gallery previews use controller input only. Isolated contact/terrain probes explicitly use RAM setup.', 'checks':{},'failures':[]}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(label,fn):
        if args.only_terrain and label not in ('room-4-entry','room-7-entry','room-8-entry','route-graphics','traversal','escort','escort-failure','collision-terrain','portable-terrain'):return
        if args.only_routes and label not in ('room-7-entry','room-8-entry','route-graphics','traversal','escort','escort-failure'):return
        if args.only_santa and label not in ('room-3-entry','santa-success','santa-failure','santa-geometry-and-effects'):return
        try:
            value=fn();report['checks'][label]={'passed':True,'details':value};print('PASS',label,value,flush=True)
        except Exception as e:
            report['checks'][label]={'passed':False,'error':repr(e)};report['failures'].append(label);shot('FAIL-'+label);print('FAIL',label,repr(e),flush=True)
        save()
    run(120);ui(3);run(4*fps);ui(5,3);ui(1);run(fps);shot('room-selector')
    if args.only_death_rules:
        # Scroll to room 10; the suite now also contains eight mission prototypes.
        ui(5,9);shot('room-selector-10');ui(1)
        wait(lambda:state()==1 and u8('testStage')==10,'rules-room',fps*20)
        run(fps//3);shot('rules-initial')
        def stock():
            slots=read(syms['item'][0],6)
            return (u8('shotPower'),u8('speedPct'),sum(slots[i]!=255 for i in (0,2,4)),u16('bombs'))
        def bags():
            address,size=syms['items'];assert size==64
            result=[]
            for i in range(8):
                x,y,ttl,kind,live=struct.unpack('>hhHBB',read(address+i*8,8))
                if live and kind==8:result.append((x,y,ttl))
            return result
        def die(label):
            press(1)
            wait(lambda:state()==3 and u8('resultActive')==1,label+'-defeat',fps*90)
            run(fps);shot(label+'-defeat');press(3)
            wait(lambda:state()==1 and u8('testStage')==10 and not u8('transitioning'),label+'-retry',fps*90)
            run(fps//3);assert u16('hp')==100
            assert u8('currentLevel')==0 and active()==0
            shot(label+'-retry')
        def collect_bag(label):
            assert len(bags())==1
            for _ in range(fps*2):
                if not bags():break
                x,y,_=bags()[0];keys=set()
                if signed('px')>x:keys.add(6)
                elif signed('px')<x:keys.add(7)
                if signed('py')>y:keys.add(4)
                elif signed('py')<y:keys.add(5)
                setkeys(keys)
            buttons.clear();run(fps//3)
            assert not bags(),(label,bags())
            before=stock();run(fps//3);assert stock()==before,'recovery applied twice'
            shot(label+'-collected')
        def rules_lab():
            assert stock()==(5,100,3,2) and not bags(),stock()
            for i in range(2):
                die('early-'+str(i+1));assert stock()==(1,0,0,0) and len(bags())==1
                collect_bag('early-'+str(i+1));assert stock()==(5,100,3,2),stock()
            assert u16('ruleDeaths')==2
            ui(8);run(fps//3);assert stock()==(5,100,3,2) and u16('ruleDeaths')==0
            expected=[(4,80,2,2),(3,60,1,2),(2,40,0,2),(1,20,0,1),(1,0,0,0),(1,0,0,0)]
            for i,value in enumerate(expected):
                die('middle-'+str(i+1));assert stock()==(1,0,0,0) and len(bags())==1
                collect_bag('middle-'+str(i+1));assert stock()==value,(i,stock(),value)
            ui(0);run(fps//3);assert stock()==(5,100,3,2) and u16('ruleDeaths')==0
            ui(8);run(fps//3)
            die('late-1');assert stock()==(1,0,0,0) and len(bags())==1 and bags()[0][2]==65535
            pause();ui(5,4);ui(1);run(fps);shot('help-from-rules')
            ui(0);ui(3);run(fps//3);assert len(bags())==1 and stock()==(1,0,0,0)
            collect_bag('late-1');assert stock()==(2,20,0,0)
            die('late-after-pickup');collect_bag('late-after-pickup');assert stock()==(2,20,0,0)
            die('late-uncollected');die('late-replaces-uncollected')
            collect_bag('late-replaces-uncollected');assert stock()==(1,0,0,0)
            configure([(0,-1),(1,-3),(2,-4),(3,-3),(4,-2)])
            assert stock()==(2,20,0,0) and not bags(),stock()
            die('middle-last-improvement');collect_bag('middle-last-improvement')
            assert stock()==(1,0,0,0),stock()
            pause();ui(5);ui(1);run(fps//3);shot('rules-configuration')
            ui(7);ui(0);run(fps//3)
            assert stock()==(1,0,0,0) and u16('ruleDeaths')==1
            pause();ui(5,2);ui(1);run(fps)
            assert stock()==(2,20,0,0) and u16('ruleDeaths')==0
            switch(1);assert active()==13 and not bags()
            switch(10);assert stock()==(2,20,0,0) and not bags()
            ui(8);run(fps//3);die('late-one-of-each');collect_bag('late-one-of-each')
            assert stock()==(2,20,0,0)
            configure([(1,-1),(2,-1)])
            assert stock()==(1,0,0,0)
            die('late-empty-stock');collect_bag('late-empty-stock');assert stock()==(1,0,0,0)
            configure([(1,1)])
            die('late-shots-only');collect_bag('late-shots-only');assert stock()==(2,0,0,0)
            configure([(1,-1),(2,1)])
            die('late-speed-only');collect_bag('late-speed-only');assert stock()==(1,20,0,0)
            die('bag-before-room-switch');assert len(bags())==1
            switch(2);assert not bags()
            pause();ui(5,2);ui(1);run(fps)
            assert stock()==(1,0,0,2),stock()
            return {'controller_only':True,'bag_after_every_death':True,'baseline_before_recovery':True,
                    'early_full_recovery_twice':True,'middle_deaths':expected,'middle_has_no_floor':True,
                    'late_only_predeath_improvements':True,'late_empty_shots_only_speed_only':True,
                    'uncollected_bag_replaced_from_latest_death':True,'bag_pickup_once':True,
                    'refill_shortcut':True,'configuration_apply_cancel_restart':True,
                    'pause_help_preserves_experiment':True,'room_switch_clears_bag':True,
                    'ordinary_training_reset_unchanged':True}
        check('campaign-death-rules-room',rules_lab)
        report['passed']=not report['failures'];save();core.retro_unload_game();core.retro_deinit()
        raise SystemExit(0 if report['passed'] else 1)
    if args.only_deaths:
        ui(5,8);press(1);run(1)
        wait(lambda:state()==1 and u8('testStage')==9,'death-room')
        shot('death-room')
        def death_gallery():
            art=(GAME/'res/actors/deaths.bin').read_bytes()
            addr,size=syms['actorDeaths'];assert size==12
            def actor_data(actor):return read(addr+actor*6,6)
            def vr(address,n):return bytes(vram[(address+j)^1] for j in range(n))
            default_seen=[[],[]]
            for _ in range(fps*2):
                for actor in range(2):
                    d=actor_data(actor)
                    assert d[4],('default actor not collapsing',actor,d)
                    tile=761 if actor else 737
                    if d[3]==d[2] and vr(tile*32,768)==art[(actor*4+d[2])*768:(actor*4+d[2]+1)*768]:
                        if d[2] not in default_seen[actor]:default_seen[actor].append(d[2])
                if default_seen==[[0,1,2,3],[0,1,2,3]]:break
                run()
            assert default_seen==[[0,1,2,3],[0,1,2,3]],('default preview',default_seen)
            run(2);shot('both-default-death')
            pieces=set();index=0
            for _ in range(80):
                entry=u16('slist_addr')+index*8;pieces.add(vw(entry+4)&2047)
                index=vw(entry+2)&127
                if not index:break
            assert {737,753,761,777}<=pieces,('both death sprites missing',pieces)
            # C switches immediately, including while a collapse is running.
            for target in (0,1,2):
                press(8)
                cfg=read(syms['testSettings'][0]+8*16,16)
                assert cfg[3]==target,('C target',target,cfg)
                assert [bool(actor_data(a)[4]) for a in range(2)]==[target in (0,2),target in (1,2)]
                assert all(actor_data(a)[2]<2 for a in range(2) if actor_data(a)[4]),'C waited for previous collapse'
            selected=2;slow=0;side=0;results=[]
            for actor,tempo,flip in ((0,0,0),(1,0,1),(0,2,1),(1,2,0)):
                changes=[(0,actor-selected),(1,flip-side),(2,tempo-slow)]
                if not results:changes.append((3,-1)) # disable default loop
                configure(changes,4);selected,slow,side=actor,tempo,flip
                wait(lambda:actor_data(actor)[4] and actor_data(actor)[2]==0,'preview-start',fps*6)
                seen=[];ticks={};paused=False;lag=0
                positions=tuple(u16(n) for n in ('px','py','dinorahX','dinorahY'))
                buttons.update({7,0})
                for frame in range(fps*7):
                    d=actor_data(actor);pose=d[2]
                    assert state()==1 and not u8('testResult') and not u8('gameOver')
                    assert d[4] and d[5]==flip,(actor,d)
                    assert positions==tuple(u16(n) for n in ('px','py','dinorahX','dinorahY'))
                    if d[3]==pose:
                        tile=761 if actor else 737
                        if vr(tile*32,768)!=art[(actor*4+pose)*768:(actor*4+pose+1)*768]:
                            lag+=1;assert lag<=3,('VRAM',actor,pose)
                            run();continue
                        lag=0
                        if pose not in seen:
                            seen.append(pose);shot(f'death-{actor}-speed-{tempo}-pose-{pose}')
                        ticks[pose]=ticks.get(pose,0)+1
                    if pose==1 and not paused:
                        buttons.clear();pause();frozen=read(addr,size);run(fps)
                        assert read(addr,size)==frozen,'pause advanced collapse'
                        press(0);wait(lambda:state()==1,'death-resume');paused=True
                        buttons.update({7,0})
                    if pose==3 and int.from_bytes(d[:2],'big')>=fps//2:break
                    run()
                buttons.clear()
                assert seen==[0,1,2,3],(actor,tempo,seen)
                assert paused
                frozen=actor_data(actor);run(fps);assert actor_data(actor)==frozen,'one-shot looped'
                assert u16('hp')==100 and u16('dinorahHp')==100
                assert not any(read(syms['pshots'][0]+i*20+18,1)[0] for i in range(16))
                results.append({'actor':actor,'slow':tempo,'flip':flip,'poses':seen,'observed_frames':ticks})
            # A replays a finished sequence without menus.
            ui(1);assert actor_data(1)[2]<3,'A did not replay'
            run(fps*5)
            configure([(2,-2),(3,1)])
            starts=0;previous=255
            for _ in range(fps*5):
                pose=actor_data(1)[2]
                if pose==0 and previous==3:starts+=1
                previous=pose;run()
            assert starts>=2,('repeat',starts)
            # Restart and leave through real pause/menu navigation.
            pause();ui(5,2);ui(1);run(fps)
            assert u16('hp')==100 and u16('dinorahHp')==100
            switch(1);assert active()==13 and not any(read(addr+i*6+4,1)[0] for i in range(2))
            return {'controller_only':True,'default_both_poses':default_seen,'direct_C_selection':[0,1,2],'sequences':results,'loop_restarts':starts,'exit_clears_deaths':True}
        check('actor-death-gallery',death_gallery)
        report['passed']=not report['failures'];save();core.retro_unload_game();core.retro_deinit()
        raise SystemExit(0 if report['passed'] else 1)
    ui(5,7);ui(1);run(2*fps)
    assert state()==1 and u8('testStage')==8 and u8('currentLevel')==0
    shot('direct-room-8');switch(7);shot('direct-room-7');switch(1)
    assert state()==1 and u8('currentLevel')==0 and u8('testStage')==1,('entry',state(),u8('currentLevel'),u8('testStage'))
    baselines={1:snap()};shot('room-1-gallery')
    def gallery():
        assert active()==13,active()
        addr,size=syms['enemies'];before=read(addr,size)
        kinds=[read(addr+i*46+30,1)[0] for i in range(13)];assert kinds==list(range(12))+[14],kinds
        seen=[set() for _ in range(13)];slots,slot_size=syms['slots'];assert slot_size==256
        for _ in range(2*fps):
            run()
            for i in range(13):
                assert read(addr+i*46,12)==before[i*46:i*46+12],('actor moved',i)
                assert read(slots+i*16+10,1)[0],('missing cached actor',i)
                seen[i].add(read(slots+i*16+6,1)[0])
        assert all(s=={0,1} for s in seen),seen
        configure([(0,1)])
        seen=[set() for _ in range(13)]
        for _ in range(2*fps):
            run()
            for i in range(13):seen[i].add(read(slots+i*16+6,1)[0])
        assert all(s=={2,3,4,5} for s in seen),seen
        directions=set()
        for _ in range(10*fps):run();directions.add(read(slots+5,1)[0])
        assert directions==set(range(8)),directions
        shot('gallery-walking')
        # Preview a small insect, a 32px insect and the boss using only menu.
        previews=[];selected=0
        for index in (0,2,12):
            changes=([(2,2)] if not previews else []) + ([] if selected==index else [(3,index-selected)])
            configure(changes,5);selected=index
            assert not read(addr+index*46+44,1)[0],('preview did not kill selected',index)
            death_addr,death_size=syms['combatDeaths'];assert death_size==4*14,(death_size,syms['combatDeaths'])
            assert any(read(death_addr+i*14+11,1)[0] for i in range(4)),('death animation missing',index)
            shot('gallery-death-'+str(index));run(fps*3);assert active()==13,('missing respawn',active())
            previews.append(index)
        return {'types':kinds,'fixed_positions':True,'idle_and_walk_all_13':True,'eight_directions':sorted(directions),'death_previews':previews,'controller_only':True}
    check('gallery',gallery)
    for room in range(2,9):
        switch(room);run(fps//2);shot('room-'+str(room));baselines[room]=snap()
        check('room-'+str(room)+'-entry',lambda room=room:{'stage':u8('testStage'),'arena_active':bool(u8('arenaActive')),'enemies':active(),'controller_only':True})
    def load():
        # Default 4 -> 16; mixed -> large purple; 6 ->16 shots; forced shield.
        configure([(0,2),(1,3),(2,1),(3,1)])
        observed=[]
        for _ in range(3*fps):run();observed.append(active())
        assert max(observed)==16 and max(observed)<=16,observed
        shot('load-16-shields')
        result={'max_enemies':max(observed),'hud_fps':u16('measuredFps'),'peak_cpu_pct':u16('peakCpu'),'controller_only':True}
        configure([(4,1)])
        run(3*fps);shot('load-deaths');return result
    restore(baselines[6])
    check('load-controls',load)
    restore(baselines[3])
    def santa_success():
        configure([(0,-1)]) # stop attacks, real 30-second objective
        for _ in range(40*fps):
            if u8('testResult'):break
            run()
        assert u8('testResult')==1 and u16('npcHp')==100,('success',u8('testResult'),u16('npcHp'))
        frozen=u32('testTicks');run(fps*2);assert u32('testTicks')==frozen
        shot('santa-success');return {'real_30_second_timer':True,'result_frozen':True,'controller_only':True}
    check('santa-success',santa_success)
    def menu_controls():
        restore(baselines[2]);addr=syms['testSettings'][0]+16;before=read(addr,16)
        pause();ui(5);ui(1);run(10);ui(7);ui(0);run(10)
        assert state()==1 and read(addr,16)==before, 'cancel changed settings'
        pause();ui(5,2);ui(1);wait(lambda:state()==1,'restart-ready');run(4)
        assert state()==1 and u8('testStage')==2 and u16('hp')==100
        assert 0<u32('testTicks')<fps, 'restart did not reset simulation'
        pause();ui(5,3);ui(1);run(10);ui(0);run(10)
        assert state()==1 and u8('testStage')==2, 'cancel room selector changed room'
        return {'configuration_cancel_rolls_back':True,'restart_resets_room':True,'room_selector_cancel_resumes':True,'controller_only':True}
    check('menu-controls',menu_controls)
    # A preserved build may carry its exported maps, so concurrent source
    # edits cannot change the expected tile IDs halfway through validation.
    fixtures=build/'route-fixtures'
    maps_path=fixtures/'mapas.json' if (fixtures/'mapas.json').exists() else GAME/'art/objetivos-travessia-escolta-v1/integracao-2048/mapas.json'
    maps=json.loads(maps_path.read_text())
    def route_map(key):
        path=fixtures/key/'map.bin'
        return path if path.exists() else GAME/f'res/routes/{key}/map.bin'
    def terrain_window(key):
        tiles=(GAME/'src/system/video/sprites/tiles.h').read_text()
        number=lambda name:int(re.search(r'^#define\s+'+name+r'\s+(\d+)',tiles,re.M)[1])
        terrain_base=16+number('NUM_TILES')+number('ENEMY_CACHE_TILES')+120
        if key=='test':
            lava=[(36,32,14,8)];mud=[(42,10,14,6)];height=384
        else:
            rectangles=[tuple(v//8 for v in r) for r in maps[key]['hazards']]
            lava=rectangles if key=='06b' else []
            mud=rectangles if key=='04' else [];height=maps[key]['height']
        def contains(rects,x,y):return any(rx<=x<rx+w and ry<=y<ry+h for rx,ry,w,h in rects)
        cx,cy=u16('cameraX')//8,u16('cameraY')//8;count=0
        for y in range(cy,min(cy+29,height//8)):
            for x in range(cx,cx+40):
                rects=lava if contains(lava,x,y) else mud if contains(mud,x,y) else []
                want=0
                if rects:
                    mask=sum(bit for dx,dy,bit in [(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)] if contains(rects,x+dx,y+dy))
                    variant=15+(x&3)+((y&1)<<2) if mask==15 else mask
                    want=0x6000+terrain_base+(0 if rects is lava else 23)+variant;count+=1
                got=vw(0xe000+((y&31)*64+(x&63))*2)
                assert got==want,('portable terrain map',key,x,y,hex(got),hex(want))
        return count
    def route_graphics():
        samples={
            '04':[(488,152),(520,208),(1000,152),(1032,208),(1512,152),(1544,208)],
            '06b':[(440,160),(488,152),(520,208),(952,160),(1000,152),(1032,208)],
        }
        for key,points in samples.items():
            source=struct.unpack('>3072H',(GAME/f'res/stages/{key}/map.bin').read_bytes())
            col,row=(24,20) if key=='04' else (28,16)
            floor={source[y*64+x] for y in range(row,row+4) for x in range(col,col+4)}
            data=route_map(key).read_bytes();route=struct.unpack('>'+str(len(data)//2)+'H',data)
            if maps[key].get('art',{}).get('whole_room_repeats') is False:
                # The newer continuous maps deliberately place safety bands
                # and authored fixtures at some of the old floor samples.
                assert len(maps[key]['art']['landmarks'])==4
                assert maps[key]['art']['lossyTileReplacements']==0
            else:
                for x,y in points:
                    assert route[(y//8)*256+x//8] in floor,('orphaned scenery',key,x,y)
                if key=='04':
                    for x in (528,1040,1552):
                        assert route[31*256+x//8]!=source[31*64+2],('pillar copied into mud',x)
            restore(baselines[7 if key=='04' else 8])
            cx,cy=u16('cameraX')//8,u16('cameraY')//8
            for y in range(cy,min(cy+29,maps[key]['height']//8)):
                for x in range(cx,cx+40):
                    assert vw(0xc000+((y&31)*64+(x&63))*2)==0x6000+785+route[y*256+x],('entry map corruption',key,x,y)
        return {'authored_route_art_checked':True,'native_floor_and_map_intact':True,'both_room_entries':True}
    check('route-graphics',route_graphics)

    def restart_room():
        pause();ui(5,2);ui(1);run(fps)
        assert state()==1 and u8('testResult')==0 and u8('currentLevel')==0
    def frozen_result():
        ticks=u32('testTicks');position=(u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'))
        hold({7,1},fps)
        assert u32('testTicks')==ticks
        assert position==(u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'))
        assert state()==1 and u8('currentLevel')==0
    def traversal():
        restore(baselines[7]);configure([(0,-1)])
        for x,y,*_ in maps['04']['points'][1:]:
            x-=8;y-=8
            for _ in range(fps*10):
                if u8('testResult') or (abs(x-u16('px'))<=2 and abs(y-u16('py'))<=2):break
                keys=set()
                if abs(x-u16('px'))>2:keys.add(7 if x>u16('px') else 6)
                if abs(y-u16('py'))>2:keys.add(5 if y>u16('py') else 4)
                setkeys(keys)
            else:raise AssertionError(('traversal stuck',x,y,u16('px'),u16('py')))
        buttons.clear();run(fps)
        assert u8('testResult')==1 and u16('kills')==0
        assert u16('cameraX')>1536
        terrain_window('04')
        frozen_result();shot('traversal-success');restart_room()
        assert u8('testStage')==7 and u16('px')==48
        return {'controller_only':True,'route_width':2048,'wins_without_kills':True,'frozen_result':True,'restart':True}
    check('traversal',traversal)
    def escort():
        restore(baselines[8]);configure([(0,-1)])
        run(fps*7);assert u8('dinorahState')==1
        before=(u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))
        pause();run(fps)
        assert before==(u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))
        ui(0);run(4);assert state()==1
        player_node=1;seen=set()
        for _ in range(fps*110):
            if u8('testResult'):break
            node=u8('dinorahNode');seen.add(u8('dinorahState'))
            target=maps['06b']['points'][min(player_node,len(maps['06b']['points'])-1)]
            dx=target[0]-8-u16('px');dy=target[1]-8-u16('py')
            ax=target[0]-8-u16('dinorahX');ay=target[1]-8-u16('dinorahY')
            if abs(dx)<=3 and abs(dy)<=3 and node>player_node:player_node+=1
            keys=set()
            if node>player_node or abs(dx)+abs(dy)>=abs(ax)+abs(ay)-32 or node>=len(maps['06b']['points']):
                if abs(dx)>3:keys.add(7 if dx>0 else 6)
                if abs(dy)>3:keys.add(5 if dy>0 else 4)
            setkeys(keys)
        buttons.clear()
        assert u8('testResult')==1 and u16('dinorahHp')==100,(u8('testResult'),u16('dinorahHp'),u8('dinorahNode'),u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'),player_node,target)
        assert 2 in seen
        terrain_window('06b')
        frozen_result();shot('escort-success');restart_room()
        assert u8('testStage')==8 and u16('dinorahHp')==100 and u8('dinorahNode')<=2
        return {'controller_only':True,'waits_for_cover':True,'pause_freezes':True,'wins_with_both_actors':True,'hp':100,'frozen_result':True,'restart':True}
    check('escort',escort)
    allow_writes=True
    def portable_terrain():
        restore(baselines[4]);terrain_window('test')
        def vr(address,n):return bytes(vram[(address+i)^1] for i in range(n))
        lava=(GAME/'art/terrain-modules-v1/lava-frames.bin').read_bytes()
        mud=(GAME/'art/terrain-modules-v1/mud.bin').read_bytes()
        import re
        palette_text=re.search(r'testPalette\[16\]=\{([^}]+)',(GAME/'src/levels/test_scene.c').read_text()).group(1)
        palette=[int(v,0) for v in palette_text.split(',')]
        source_palette=json.loads((GAME/'art/terrain-modules-v1/layout.json').read_text())['source_palette_words']
        def channels(c):return (c>>1)&7,(c>>5)&7,(c>>9)&7
        def distance(a,b):
            ar,ag,ab=channels(a);br,bg,bb=channels(b)
            return (ar-br)**2+2*(ag-bg)**2+(ab-bb)**2
        mapping=[0]+[min(range(1,16),key=lambda j:distance(source_palette[i],palette[j])) for i in range(1,16)]
        def mapped(data):return bytes((mapping[v>>4]<<4)|mapping[v&15] for v in data)
        expected={mapped(lava[:736]),mapped(lava[736:])};frames=set()
        for _ in range(fps*2):
            run();frame=vr(545*32,736);assert frame in expected,'lava atlas overwritten'
            frames.add(frame);assert vr(568*32,736)==mapped(mud),'mud atlas overwritten'
        assert len(frames)==2,'lava does not animate'
        before=vr(0xe000,4096);pause();run(fps);ui(0);run(4)
        assert vr(0xe000,4096)==before,'pause damaged terrain layer'
        terrain_window('test')
        pos(304,272);settle();shot('lava-on-stone')
        restore(baselines[4]);pos(352,96);settle();shot('mud-on-stone')
        restore(baselines[7]);terrain_window('04');shot('mud-in-tunnels')
        restore(baselines[8]);terrain_window('06b');shot('lava-on-retreat')
        return {'scene_palette_preserved':True,'lava_frames':2,'mud_atlas_exact':True,'pause_restores_layer':True,
                'independent_scenery_and_overlay':True,'scrolling_2048px_checked_by_route_tests':True,
                'resident_tiles':46,'setup':'Positioning only for screenshots; entry, animation, pause and routes use production rendering.'}
    check('portable-terrain',portable_terrain)
    def santa_geometry_and_effects():
        restore(baselines[3])
        write(syms['testSettings'][0]+2*16+9,b'\0') # isolated, attacks off
        write(syms['enemies'][0],bytes(syms['enemies'][1]))
        write(syms['eshots'][0],bytes(syms['eshots'][1]))
        pos(64,288);settle();baseline=snap()
        assert u16('cameraY')+24<=120 and 296-u16('cameraY')<224,'beacon arrows clipped at entry'
        visual=next(s for s in json.loads((GAME/'art/phases02-06-v1/integration-export.json').read_text())['stages'] if s['id']=='05')['npc_visual']
        x,y,ww,hh=visual['rect'];cells=[(xx,yy) for yy in range(y//8,(y+hh)//8) for xx in range(x//8,(x+ww)//8)]
        tilemap=struct.unpack('>3072H',(GAME/'res/stages/05/map.bin').read_bytes())
        original=tuple(785+tilemap[yy*64+xx] for xx,yy in cells)
        hidden=tuple(785+t for t in visual['floor_tiles'])
        def patch():return tuple(vw(u16('bgb_addr')+((yy&31)*64+xx)*2)&2047 for xx,yy in cells)
        def glow():
            index=0
            for _ in range(80):
                addr=u16('slist_addr')+index*8
                tile=vw(addr+4)&2047
                if tile in (785+visual['crown_tile'],786+visual['crown_tile']):
                    assert (vw(addr+4)>>13)&3==1,'crown must use red/yellow PAL1'
                    assert [(vw(addr+6)&511)-128+u16('cameraX'),(vw(addr)&511)-128+u16('cameraY')]==visual['crown'],'glow is not on crown'
                    return tile-(785+visual['crown_tile'])+1
                index=vw(addr+2)&127
                if not index:return 0
            raise AssertionError('SAT loop')
        phases=set()
        for phase in range(2):
            start=(785+visual['crown_tile']+phase)*32
            ink=bytes(vram[(start+j)^1] for j in range(32))
            assert {n for b in ink for n in (b>>4,b&15)}=={0,3,4},'crown contains white/black ink'
        for _ in range(fps+4):
            run();phase=glow()
            if phase and phase not in phases:
                shot('santa-crown-'+('red' if phase==1 else 'yellow'))
                shot('santa-crown-glow')
            phases.add(phase)
        assert phases=={1,2},('red/yellow glow phases',phases)
        stops=[]
        for start,key,expected in [((144,184),7,(160,184)),((232,184),6,(216,184)),((184,144),5,(184,160)),((184,240),4,(184,224))]:
            restore(baseline);pos(*start);settle();hold({key},24)
            actual=(u16('px'),u16('py'));assert actual==expected,('statue crossed',start,key,actual,expected)
            stops.append(actual);shot('santa-solid-'+str(key))
        for ex,ey in ((160,184),(216,184),(184,160),(184,224)):
            restore(baseline);pos(64,288);settle()
            addr=syms['enemies'][0];buf=bytearray(46)
            struct.pack_into('>hhii',buf,0,ex,ey,ex<<6,ey<<6)
            struct.pack_into('>HHH',buf,16,60000,60000,60000)
            buf[30],buf[31],buf[44]=0,200,1;write(addr,buf)
            for _ in range(fps):
                run()
                if u16('npcHp')==88:break
            assert u16('npcHp')==88,('enemy cannot touch solid edge',ex,ey,u16('npcHp'))
        write(syms['enemies'][0],bytes(syms['enemies'][1]))
        seen=set()
        for tick in range(60):
            run();p=patch();assert p in (original,hidden),'partially updated statue'
            seen.add(p)
            if p==hidden:
                assert not glow(),'glow survives hidden statue'
                if tick>24:shot('santa-whole-statue-hidden')
        assert seen=={original,hidden},'whole statue must blink'
        # The pedestal rows must change too; the old test only covered the top.
        assert any(original[i]!=hidden[i] for i,(_,yy) in enumerate(cells) if yy>=26),'pedestal not included in blink'
        return {'solid_stops_four_sides':stops,'real_contact_four_sides':True,'full_blink_cells':len(cells),
                'body_and_pedestal_blink':True,'glow_on_crown_both_phases':True,'glow_red_yellow_only':True,'glow_hidden_with_statue':True,
                'setup':'Controller movement after isolated player/enemy positioning; real contact damage, no NPC HP writes.'}
    check('santa-geometry-and-effects',santa_geometry_and_effects)
    def escort_failure():
        restore(baselines[8]);configure([(0,-1),(1,1)])
        w16('dinorahHp',10);w16('dinorahInvTimer',0)
        write(syms['eshots'][0],struct.pack('>iiiiBBBB',(u16('dinorahX')+4)<<6,(u16('dinorahY')+4)<<6,0,0,1,10,1,0))
        run(4)
        assert u8('testResult')==0 and u16('dinorahHp')==0 and state()==1
        # Failure freezes the room only after Dinorah's visible collapse.
        death_addr=syms['actorDeaths'][0]+syms['actorDeaths'][1]//2
        poses=set()
        for _ in range(fps*3):
            d=read(death_addr,6)
            if d[4] and d[2]==d[3]:poses.add(d[2])
            if u8('testResult'):break
            run()
        assert poses=={0,1,2,3},('missing escort death poses',poses)
        assert u8('testResult')==2 and u16('dinorahHp')==0 and state()==1
        frozen_result();shot('escort-failure');restart_room()
        assert u16('dinorahHp')==100
        return {'real_projectile_damage':True,'damiao_no_defeat_does_not_protect_dinorah':True,'death_poses':sorted(poses),'frozen_failure':True,'restart_hp':100,'setup':'isolated lethal projectile and 10 HP'}
    check('escort-failure',escort_failure)
    def no_defeat():
        restore(baselines[6]);configure([(0,-1),(1,1)])
        def hit():
            w16('hp',1)
            x,y=u16('px'),u16('py')
            shot_data=bytearray(20);struct.pack_into('>iiii',shot_data,0,(x+4)<<6,(y+4)<<6,0,0)
            shot_data[16:19]=bytes((1,10,1));write(syms['eshots'][0],shot_data);run(4)
        hit();assert state()==1 and u16('hp')==1 and not u8('gameOver'), 'no-defeat clamp failed'
        configure([(5,-1)]);hit();wait(lambda:state()==3,'normal-life-result',5*fps)
        assert state()==3 and u8('gameOver'), ('normal-life mode did not defeat',state(),u16('hp'),read(syms['testSettings'][0]+5*16,16).hex())
        return {'lethal_projectile_no_defeat_hp':1,'normal_life_defeats':True,'setup':'controller settings, isolated 1 HP and stationary lethal projectile'}
    check('no-defeat',no_defeat)
    def items():
        restore(baselines[2]);configure([(0,1),(1,1),(3,-2)])
        addr,size=syms['items'];assert size==64,size
        types={read(addr+i*8+6,1)[0] for i in range(8) if read(addr+i*8+7,1)[0]}
        assert types==set(range(8)),types
        assert active()==3 and u16('hp')==25
        eaddr=syms['enemies'][0];assert read(eaddr+31,1)[0]==100
        pos(40,176);run(4);assert u16('hp')==40
        pos(72,176);run(4)
        pos(104,176);run(4);assert u8('shotPower')==2
        pos(136,176);run(4);assert u8('speedPct')==20
        pos(168,176);run(4);ui(8);ui(0) # use shield, freeing an inventory slot
        for x in (200,232,264):pos(x,176);run(4)
        ui(0);assert u8('shotMode')==1 and u8('modeCharges')==5
        pos(148,168);hold({4},4);run(10);hold({1},2);run(20)
        assert not read(eaddr+46+44,1)[0] and not read(eaddr+92+44,1)[0],'chain targets survived'
        ui(8);ui(0);assert u8('shotMode')==2
        pos(148,168);hold({4},4);run(10);hold({1},2);run(20)
        frozen=int.from_bytes(read(eaddr+32,2),'big');assert frozen>0,'dummy did not freeze'
        shot('items-ice')
        ui(8);ui(0);assert u8('shotMode')==3
        pos(148,168);hold({4},4);run(10);hold({1},2);run(20)
        burn=int.from_bytes(read(eaddr+34,2),'big');assert burn>0,'dummy did not burn'
        pos(72,144);run(3*fps)
        types_after={read(addr+i*8+6,1)[0] for i in range(8) if read(addr+i*8+7,1)[0]}
        assert types_after==set(range(8)),types_after
        shot('items-all-replenished')
        return {'eight_types':sorted(types),'healing':40,'power':2,'speed_bonus':20,'chain_targets_killed':2,'dummy_ice_frames':frozen,'dummy_burn_frames':burn,'replenishment':True,'setup':'real pickups/activation/shots; player repositioning only'}
    check('item-bench',items)
    def behavior():
        restore(baselines[5]);configure([(0,12)]) # first common enemy -> boss
        addr=syms['enemies'][0]
        assert read(addr+30,1)[0]==14 and read(addr+44,1)[0]
        pos(48,184)
        start=read(addr,4);run(fps);assert read(addr,4)!=start,'boss does not move'
        # Accelerate the summon cycle without changing behaviour or minions.
        write(addr+24,struct.pack('>H',10*fps-1));run(5)
        assert active()>=3,active();shot('behavior-boss-minions')
        return {'boss_moves':True,'real_minion_summon':True,'setup':'controller selects boss, cycle accelerated for summon'}
    check('behavior-boss',behavior)
    def santa_failure():
        restore(baselines[3]);addr=syms['enemies'][0];write(addr,bytes(syms['enemies'][1]));pos(64,288)
        cfg=syms['testSettings'][0];write(cfg+2*16+9,b'\0') # attacks paused, isolated contacts
        buf=bytearray(46);struct.pack_into('>hhii',buf,0,160,208,160<<6,208<<6)
        struct.pack_into('>HHH',buf,16,60000,60000,60000);buf[30],buf[31],buf[44]=0,200,1;write(addr,buf)
        hp_seen=[]
        for _ in range(70*fps):
            if u8('testResult'):break
            write(addr,struct.pack('>hhii',160,208,160<<6,208<<6));write(addr+12,bytes(4));write(addr+20,struct.pack('>H',6000));run()
            hp=u16('npcHp')
            if not hp_seen or hp!=hp_seen[-1]:hp_seen.append(hp)
        assert u8('testResult')==2 and u16('npcHp')==0,('failure',u8('testResult'),hp_seen)
        frozen=u32('testTicks');run(fps);assert u32('testTicks')==frozen
        shot('santa-failure');return {'real_contact_damage':hp_seen,'no_npc_hp_writes':True,'result_frozen':True}
    check('santa-failure',santa_failure)
    def terrain():
        restore(baselines[4]);pos(304,272);settle();h1=u16('hp');run(fps);h2=u16('hp');assert h2<h1,(h1,h2)
        pos(352,96);settle();slow=u8('playerSlowPct');assert slow>0,slow
        pos(48,112);settle();assert u8('playerSlowPct')==0,('mud exit',u8('playerSlowPct'))
        # Tall wall blocks feet. Blue low obstacle blocks feet but not shots.
        pos(72,128);settle();hold({7},15);assert u16('px')==80,('wall feet',u16('px'))
        pos(296,184);settle();hold({4},8);assert u16('py')==176,('low obstacle feet',u16('py'))
        write(syms['pshots'][0],bytes(syms['pshots'][1]));w16('shotCooldown',0)
        hold({1},2);run(12)
        assert any(read(syms['pshots'][0]+i*20+18,1)[0] and int.from_bytes(read(syms['pshots'][0]+i*20+4,4),'big',signed=True)<160<<6 for i in range(16)),'low obstacle blocked bullets'
        shot('collision-lava-mud');return {'lava_hp':[h1,h2],'mud_slow':slow,'mud_exit_reset':True}
    check('collision-terrain',terrain)
    report['passed']=not report['failures'];save();core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':report['passed'],'failures':report['failures']}),flush=True)
    raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
