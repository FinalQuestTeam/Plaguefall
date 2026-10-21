"""Controller-only diagonal aim regression in Genesis Plus GX.

Run with arch -x86_64 /usr/bin/python3. Scenarios restore a controller-reached
sandbox baseline using libretro save states; explicit game RAM writes are forbidden.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/player-diagonal-aim-v1'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
    rom=GAME/'out/release/rom.bin';original=rom.read_bytes();data=bytearray(original)
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
    symbols=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(GAME/'out/release/rom.out')],text=True)
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
    def write(addr,value):
        raise AssertionError('Game RAM writes forbidden in diagonal aim test')
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

    # Boot/menu/test-room entry uses only controller buttons.
    run(120);press(3);run(4*fps)
    for _ in range(3):press(5)
    press(3);run(fps)
    assert u8('currentLevel')==0 and u8('testStage')==1, ('sandbox entry failed',u8('currentLevel'),u8('testStage'))
    size=core.retro_serialize_size();baseline=C.create_string_buffer(size)
    assert core.retro_serialize(baseline,size)
    def restore():
        buttons.clear();assert core.retro_unserialize(baseline,size);run(2)

    actor_frames=(GAME/'res/heroi/frames.bin').read_bytes()
    canonical=(0,1,2,3,4,3,2,1)
    directions=[('NE',1,-1,7,4,1),('SE',1,1,7,5,3),('SO',-1,1,6,5,5),('NO',-1,-1,6,4,7)]
    cases=[]
    for label,dx,dy,horizontal,vertical,direction in directions:
        for remaining in (horizontal,vertical):
            for gap in (1,3):
                restore();setkeys({horizontal,vertical},10)
                assert facing()==(dx,dy),(label,'diagonal movement',facing())
                setkeys({remaining},gap);setkeys(set(),fps//3)
                stopped=(u16('px'),u16('py'))
                assert facing()==(dx,dy),(label,remaining,gap,'lost diagonal on release',facing())
                assert u8('loadedDir')==direction and u8('loadedPose')<2
                # Both idle poses must exist in VRAM for that diagonal, with
                # the matching hardware flip, while position remains fixed.
                poses=set()
                for _ in range(fps):
                    run();assert facing()==(dx,dy)
                    assert (u16('px'),u16('py'))==stopped
                    assert u8('loadedPose')<2
                    sat=u16('slist_addr');attr=vw(sat+4);tile=attr&2047
                    assert bool(attr&(1<<11))==(direction>4),(label,'wrong hardware mirror')
                    displayed=bytes(vram[(tile*32+i)^1] for i in range(768))
                    matches=[p for p in (0,1) if displayed==actor_frames[(canonical[direction]*6+p)*768:(canonical[direction]*6+p+1)*768]]
                    assert len(matches)==1,(label,'displayed frame is not diagonal idle')
                    poses.add(matches[0])
                assert poses=={0,1},(label,'missing idle pose',poses)
                # Real production SHOTS_firePlayer must fire in both axes.
                setkeys({1},3)
                bullets=[]
                for i in range(16):
                    base=syms['pshots'][0]+i*20
                    if read(base+18,1)[0]:bullets.append(struct.unpack('>iiii',read(base,16)))
                assert bullets,(label,'no shot while stationary')
                assert all(vx*dx>0 and vy*dy>0 for _,_,vx,vy in bullets),(label,'cardinal bullet',bullets)
                assert facing()==(dx,dy) and (u16('px'),u16('py'))==stopped
                name=f'{label.lower()}-{remaining}-{gap}'
                shot(name)
                cases.append(dict(direction=label,remaining_button=remaining,release_gap_frames=gap,
                                  stationary_position=stopped,idle_poses=sorted(poses),shot_velocities=[(x[2],x[3]) for x in bullets],capture=name+'.png'))
        # Holding the remaining axis is an intentional cardinal turn.
        restore();setkeys({horizontal,vertical},10);setkeys({horizontal},fps//5)
        assert facing()==(dx,0),(label,'held cardinal turn delayed indefinitely',facing())
        setkeys(set(),6);setkeys({vertical},3)
        assert facing()==(0,dy),(label,'fresh cardinal press after idle was delayed',facing())
        print(f'{fps}Hz: {label} diagonal idle, both release orders, both idle poses, diagonal bullets and cardinal turns OK',flush=True)

    report=dict(passed=True,region='PAL' if args.pal else 'NTSC',fps=fps,core_fps=av.timing.fps,
                rom_sha256=hashlib.sha256(original).hexdigest(),game_ram_writes=False,
                method='Controller enters sandbox; each scenario restores that libretro save-state baseline. No game RAM writes.',
                diagonal_cases=cases,checks=['four diagonal facings survive staggered release','both axis release orders','1-frame and 3-frame release gaps','position fixed during idle and fire','both diagonal idle poses match real VRAM','hardware sprite mirror matches facing','real bullets have the correct nonzero X and Y velocity','held cardinal turn works','new cardinal press after idle remains immediate'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    core.retro_unload_game();core.retro_deinit()
    print('PASS: 16 diagonal idle/shooting scenarios; no game RAM writes.')


if __name__=='__main__':main()
