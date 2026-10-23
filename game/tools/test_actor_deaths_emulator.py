"""Damião and Dinorah collapse through real fatal damage, in NTSC/PAL.

RAM seeds controlled scenarios; physics, graphics, kill paths and controller
navigation use the normal production code in NTSC/PAL.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, struct, subprocess, zlib

from text_codec import decode
GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/actor-deaths-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    def state():return u32('flow_state')
    def until(predicate,label,limit=fps*12):
        for _ in range(limit):
            if predicate():return
            run()
        shot('FAIL-'+label);raise AssertionError(('timeout',label,state(),u8('currentLevel'),u8('pendingLevel')))
    def textrow(row):
        return ''.join(decode(chr((vw(0xe000+(row*64+x)*2)&0x7ff)-1440+32))
            if 1440<=(vw(0xe000+(row*64+x)*2)&0x7ff)<1536 else '.' for x in range(40))
    def zeros(name):write(syms[name][0],bytes(syms[name][1]))
    def vr(addr,n):return bytes(vram[((addr+j)&65535)^1] for j in range(n))
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),'checks':{}}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(name,value=True):report['checks'][name]=value;save();print('PASS',name,value,flush=True)
    art=(GAME/'res/actors/deaths.bin').read_bytes()
    stride=syms['actorDeaths'][1]//2
    assert stride==6,('ActorDeath layout',stride)
    def death(actor):return read(syms['actorDeaths'][0]+actor*stride,stride)
    def sat():
        sprites=[];at=0
        for _ in range(80):
            off=0xf400+at*8;link=vw(off+2);attr=vw(off+4)
            sprites.append((attr&2047,link>>8,attr));at=link&127
            if not at:break
        return sprites
    def fatal(actor):
        if actor:
            w16('dinorahHp',10);w16('dinorahInvTimer',0)
            x,y=u16('dinorahX'),u16('dinorahY')
        else:
            w16('hp',10);w16('invTimer',0);w16('shieldTimer',0)
            x,y=u16('px'),u16('py')
        write(syms['eshots'][0]+actor*20,struct.pack('>iiiiBBBB',(x+4)<<6,(y+4)<<6,0,0,1,10,1,0))
    def verify(actors,label,end=3,pause=False):
        positions=(u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'))
        previous=[-1,-1];seen=[[],[]];holds=[{},{}];steps=0;paused=False;lag=[0,0]
        buttons.update({1,7,8,0}) # held movement, fire and inventory cannot interrupt collapse
        while state()==1 and (end!=1 or not u8('testResult')) and steps<fps*4:
            for actor in actors:
                d=death(actor);pose=d[2];loaded=d[3]
                assert d[4],('not active',label,actor,d)
                if loaded!=pose:continue
                if pose==3 and int.from_bytes(d[:2],'big')>=fps//2:continue
                assert pose>=previous[actor],('looped',label,actor,d)
                tile=761 if actor else 737
                if vr(tile*32,768)!=art[(actor*4+pose)*768:(actor*4+pose+1)*768]:
                    lag[actor]+=1;assert lag[actor]<=3,('VRAM upload stalled',label,actor,d)
                    continue
                lag[actor]=0
                pieces=sat()
                assert any(t==tile and size==15 for t,size,a in pieces),('missing torso',label,actor,pieces)
                assert any(t==tile+16 and size==13 for t,size,a in pieces),('missing legs',label,actor,pieces)
                assert all(bool(a&2048)==bool(d[5]) for t,size,a in pieces if t in (tile,tile+16)),('wrong flip',label)
                if previous[actor]!=pose:
                    seen[actor].append(pose);previous[actor]=pose;shot(label+'-'+str(actor)+'-pose-'+str(pose))
                holds[actor][pose]=holds[actor].get(pose,0)+1
            assert positions==(u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY')),('moved after death',label)
            if pause and not paused and previous[actors[0]]==1:
                buttons.clear();press(3);until(lambda:state()==2,'death-pause')
                frozen=read(syms['actorDeaths'][0],syms['actorDeaths'][1]);run(fps)
                assert read(syms['actorDeaths'][0],len(frozen))==frozen,'pause advances death'
                press(0);until(lambda:state()==1,'death-resume');paused=True
            run();steps+=1
        buttons.clear()
        assert state()==end,(label,state(),steps)
        for actor in actors:
            assert seen[actor]==[0,1,2,3],(label,seen)
            # press() advances two uncounted gameplay frames on pause/resume.
            assert all(holds[actor].get(p,0)>=fps*.13-(2 if pause and p==1 else 0) for p in range(3)),(label,holds)
            assert holds[actor].get(3,0)>=fps*.45,(label,holds)
        if pause:assert paused
        run(5);shot(label+'-result');check(label,{'poses':seen,'holdFrames':holds,'elapsedFrames':steps,'pause':paused})
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),'prep');run(2);baseline=snapshot()
        def enter(node=1):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1);until(lambda:state()==1,'play');run(fps*4)
            zeros('enemies');zeros('pshots');zeros('eshots');zeros('combatDeaths');w16('spawnTimer',60000)
            pos(200,160);w16('dinorahPauseTimer',60000);run(fps)
        for western in (False,True):
            enter();w16('faceX',-1 if western else 1);w16('faceY',0);run(2)
            fatal(0);until(lambda:bool(death(0)[4]),'hero-fatal')
            verify([0],'damiao-'+('west' if western else 'east'),pause=western)
            assert u16('hp')==0
        enter(8);fatal(1);until(lambda:bool(death(1)[4]),'dinorah-fatal')
        assert u8('dinorahState')==5 and u16('dinorahHp')==0
        verify([1],'dinorah',pause=True)
        # Retry through ordinary controller navigation and phase loading.
        run(fps);press(3);until(lambda:state() in (0,6),'retry')
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),'retry-prep')
        press(1);until(lambda:state()==1,'retry-play');run(fps*4)
        assert u16('hp')==100 and u16('dinorahHp')==100
        assert not death(0)[4] and not death(1)[4]
        check('retryClearsBothDeaths')
        # Two distinct fatal bullets in one normal update must preserve both animations.
        enter(8);fatal(0);fatal(1);until(lambda:bool(death(0)[4]) and bool(death(1)[4]),'simultaneous')
        verify([0,1],'simultaneous')
        # Environmental fatal damage uses the same player collapse path.
        enter(4);pos(132,108);w16('hp',1);w16('shieldTimer',0)
        # Authored phase 3 lava rectangles are read from production level definitions.
        level_source=(GAME/'src/levels/stage_scenes.c').read_text()
        import re
        lava=re.search(r'const TileRect STAGE03_lava[^=]*=\s*\{\s*\{\s*(\d+),\s*(\d+)',level_source)
        if lava:
            pos(int(lava[1])*8+16,int(lava[2])*8+16)
            until(lambda:bool(death(0)[4]),'lava-fatal',fps*4);verify([0],'lava')
        else:raise AssertionError('lava definition not found')
        report['passed']=True;save();print('ALL ACTOR DEATH CHECKS PASSED',flush=True)
    except Exception as exc:
        report['error']=str(exc);shot('FAIL');save();raise
    finally:core.retro_unload_game();core.retro_deinit()
if __name__=='__main__':main()
