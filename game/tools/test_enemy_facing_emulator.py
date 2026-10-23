"""Check all 13 native enemy assets in ROM VRAM and SAT at 50/60Hz.

Controller enters the gallery; RAM fixes its direction and animation clock.
No ROM patch. Every cached upload is compared byte-for-byte to packed art.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, re, struct, subprocess, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/cangaco-insects-sized-v3/validation/directions'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    def batch(ptr,n):
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
    def hold(keys,n):buttons.update(keys);run(n);buttons.clear();run(2)
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

    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)

    def state():return u32('flow_state')
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
        ui(5,(room-current)%6);ui(1);run(fps)
        wait(lambda:state()==1 and u8('testStage')==room,'switch-room')
        assert u8('currentLevel')==0
    def configure(changes,action=None):
        pause();ui(5);ui(1);run(10);row=0
        for target,delta in changes:
            ui(5,target-row);row=target
            ui(7 if delta>0 else 6,abs(delta))
        if action is not None:ui(5,action-row)
        ui(1);run(4 if action is not None else fps)
        wait(lambda:state()==1,'configuration')
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC',
            'rom_sha256':hashlib.sha256(original).hexdigest(),
            'setup':'Controller gallery entry; RAM fixes gallery settings and clock, production loader and renderer run unchanged.',
            'frames_checked':0,'directions':8,'types':13,'failures':[]}
    def vr(addr,n):return bytes(vram[((addr+j)&65535)^1] for j in range(n))
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        run(120);ui(3);run(4*fps);ui(5,3);ui(1);run(fps);ui(1);run(2*fps)
        assert state()==1 and u8('currentLevel')==0 and u8('testStage')==1
        allow_writes=True
        slots,slot_size=syms['slots'];assert slot_size==16*16
        cfg=syms['testSettings'][0];write(cfg+2,b'\x03')
        art=json.loads((GAME/'art/cangaco-insects-sized-v3/validation/export.json').read_text())
        packed=(GAME/'res/insects/frames.bin').read_bytes()
        canonical=[0,1,2,3,4,3,2,1]
        for direction in range(8):
            write(cfg+1,bytes([direction]))
            for pose in range(6):
                write(cfg,bytes([int(pose>=2)]))
                clock=pose*(fps*2//5) if pose<2 else (pose-2)*(fps*3//20)
                write(syms['testTicks'][0],struct.pack('>I',clock*8))
                run(12)
                for index,entry in enumerate(art):
                    slot=read(slots+index*16,16)
                    assert slot[5]==direction and slot[6]==pose and slot[10],(entry['id'],direction,pose,slot.hex())
                    tile=int.from_bytes(slot[12:14],'big')+16
                    start=entry['rom_offset']+(canonical[direction]*6+pose)*entry['bytes_per_frame']
                    expected=packed[start:start+entry['bytes_per_frame']]
                    assert vr(tile*32,len(expected))==expected,('VRAM',entry['id'],direction,pose)
                    # Follow the active SGDK SAT chain; unused entries are stale.
                    matches=[];j=0
                    for _ in range(80):
                        sat=vr(0xf400+j*8,8);attr=int.from_bytes(sat[4:6],'big')
                        if attr&2047==tile:matches.append((sat,attr))
                        j=sat[3]&127
                        if not j:break
                    assert len(matches)==1,('SAT',entry['id'],direction,pose,len(matches))
                    sat,attr=matches[0];assert bool(attr&0x800)==(direction>=5)
                    assert not attr&0x1000,('unexpected VFLIP',entry['id'])
                    entity=read(syms['enemies'][0]+index*46,4)
                    x,y=struct.unpack('>hh',entity)
                    actual_x=(int.from_bytes(sat[6:8],'big')&511)-128
                    actual_y=(int.from_bytes(sat[:2],'big')&511)-128
                    assert actual_x==x+(16 if entry['size']==48 and direction>=5 else 0)-signed('cameraX')
                    assert actual_y==y-16-signed('cameraY')
                    report['frames_checked']+=1
                if pose==0:shot('all-enemies-direction-'+str(direction))
        assert report['frames_checked']==624
        switch(2);write(syms['testSettings'][0]+16+6,b'\x01');run(12)
        # Read the tested build's layout: adding fixed items can move the icon
        # reservation without changing the enemy animation/cache contract.
        layout=(build.parents[1]/'src/system/video/sprites/tiles.h').read_text()
        def tile_count(name):return int(re.search(r'^#define\s+'+name+r'\s+(\d+)',layout,re.M).group(1))
        icon_base=tile_count('NUM_TILES')+tile_count('ENEMY_CACHE_TILES')
        legacy=[]
        for index,kind in enumerate((12,13,13)):
            entity=read(syms['enemies'][0]+index*46,46)
            assert entity[30]==kind and entity[44]
            x,y=struct.unpack('>hh',entity[:4]);tile=16+icon_base+kind*tile_count('ENEMY_ICON_TILES')
            j=0;found=False
            for _ in range(80):
                sat=vr(0xf400+j*8,8);attr=int.from_bytes(sat[4:6],'big')
                if attr&2047==tile and (int.from_bytes(sat[6:8],'big')&511)-128==x-signed('cameraX'):
                    assert sat[2]==10 and not attr&0x1800
                    assert (int.from_bytes(sat[:2],'big')&511)-128==y-16-signed('cameraY')
                    found=True
                j=sat[3]&127
                if not j:break
            assert found,('legacy static target',kind,index)
            legacy.append(kind)
        report['legacy_static_targets']=legacy;shot('legacy-static-targets')
        report['passed']=True;save();print(json.dumps(report,indent=2))
    except Exception as error:
        report['failures'].append(repr(error));shot('FAIL');save();raise
    finally:
        core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
