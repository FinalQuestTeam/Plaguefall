"""Verify room 6 on the current ROM using only controller input.

Run with arch -x86_64 /usr/bin/python3. Measure updates against VBlanks,
verify eight shielded bodies in the SAT, and exercise room configuration.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=next(p for p in Path(__file__).resolve().parents if p.name=='game')
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
    report={'passed':False,'rom_sha256':hashlib.sha256(original).hexdigest(),'region_fps':fps,
            'controller_only':True,'ram_writes':0,'cases':[]}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def shot_count(name):return sum(read(syms[name][0]+i*20+18,1)[0]!=0 for i in range(16))
    def hardware_bodies():
        addr=syms['slots'][0]
        body_tiles={16+int.from_bytes(read(addr+i*16+12,2),'big') for i in range(8)}
        found=set();index=0
        for _ in range(80):
            base=u16('slist_addr')+index*8
            entry=bytes(vram[((base+j)&65535)^1] for j in range(8))
            tile=int.from_bytes(entry[4:6],'big')&2047
            if tile in body_tiles:found.add(tile)
            index=entry[3]&127
            if not index:break
        return len(found)
    def check_case(label,frames=1800):
        run(180);begin,vb=u32('testTicks'),u32('vtimer');counts=[];shields=[];pools=[[],[]];health=[];cpu=[];bodies=[]
        for _ in range(frames):
            run();counts.append(active());health.append(u16('hp'));cpu.append(u16('cpuFrameLoad')*100/2048)
            shields.append(sum(read(syms['enemies'][0]+i*46+42,1)[0]!=0 for i in range(8)));bodies.append(hardware_bodies())
            for i,name in enumerate(('pshots','eshots')):pools[i].append(shot_count(name))
            assert state()==1 and u8('currentLevel')==0 and u8('testStage')==6
        ticks,elapsed=u32('testTicks')-begin,u32('vtimer')-vb
        cfg=read(syms['testSettings'][0]+5*16,16)
        value={'label':label,'game_frames':ticks,'physical_frames':elapsed,'fps':round(fps*ticks/elapsed,4),
               'target_met':ticks==elapsed,'enemy_count_min':min(counts),'enemy_count_max':max(counts),
               'shields_min':min(shields),'player_hp_min':min(health),'hud_fps':u16('measuredFps'),
               'cpu_mean':round(statistics.mean(cpu),2),'cpu_p95':round(sorted(cpu)[int(len(cpu)*.95)],2),
               'projectiles':[{'min':min(v),'mean':round(statistics.mean(v),2),'max':max(v)} for v in pools],
               'kind':cfg[10],'shot_setting':cfg[13],'hardware_bodies_min':min(bodies)}
        assert min(counts)==max(counts)==8 and min(shields)==8 and min(health)==100 and min(bodies)==8,value
        types=[read(syms['enemies'][0]+i*46+30,1)[0] for i in range(8)]
        assert types==([2,10]*4 if cfg[10]==0 else [[2]*8,[10]*8,[6]*8][cfg[10]-1]),types
        value['enemy_types']=types
        if cfg[13]:assert all(min(v)>0 for v in pools),value
        else:assert not any(pools[0]+pools[1]),value
        report['cases'].append(value);print(json.dumps(value),flush=True);shot(label);save()
    try:
        run(120);ui(3);run(4*fps);ui(5,3);ui(1);run(fps);shot('room-selector')
        ui(5,5);ui(1);wait(lambda:state()==1 and u8('testStage')==6,'load-room',fps*20)
        run(fps*2)
        cfg=read(syms['testSettings'][0]+5*16,16)
        assert (cfg[10],cfg[11],cfg[12],cfg[13],cfg[14],cfg[15])==(1,1,2,2,1,0),cfg.hex()
        check_case('baluarte-16')
        configure([(1,-1)]);check_case('mixed-16')
        configure([(1,2)]);check_case('fortaleza-16')
        configure([(1,1)]);check_case('escudeiro-16')
        configure([(2,-1)]);check_case('escudeiro-6')
        configure([(2,-1)]);check_case('escudeiro-0')
        configure([(4,1)])
        death_peak=0
        for _ in range(fps*4):
            run();death_peak=max(death_peak,sum(read(syms['combatDeaths'][0]+i*(syms['combatDeaths'][1]//4)+11,1)[0]!=0 for i in range(4)))
        assert death_peak>0,'death loop never generated an effect'
        report['death_loop_works']=True
        configure([(4,-1)])
        for delta,wanted in [(-2,1),(1,4),(2,16),(-1,8)]:
            configure([(0,delta)]);assert active()==wanted,(delta,active())
        report['quantity_options_work']=[1,4,8,16]
        # Menu cancellation preserves the selected configuration and resumes.
        pause();ui(5);ui(1);run(10);ui(7);ui(0);run(fps)
        wait(lambda:state()==1,'cancel-config');assert read(syms['testSettings'][0]+5*16,16)[12]==2
        pause();ui(5);ui(1);run(10);shot('configuration');ui(0);run(fps)
        report['configuration_cancel_preserves_settings']=True
        report['performance_target_met']=all(v['target_met'] for v in report['cases']);report['passed']=True;save()
    finally:core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
