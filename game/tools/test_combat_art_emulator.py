"""Native projectiles and bounded cosmetic enemy death animation.

RAM seeds controlled scenarios; physics, graphics, kill paths and controller
navigation use the normal production code in NTSC/PAL.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import decode
GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/disparos-mortes-ux-v1/integracao/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),'setup':'RAM seeds actors/projectiles and selects phase; production simulation, kill paths, controller pause and graphics run unmodified. No ROM patch.','species':[],'checks':{},'failures':[]}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    estride=syms['enemies'][1]//16;dstride=syms['combatDeaths'][1]//4
    assert estride==46 and dstride<=16,(estride,dstride)
    def zeros(name):write(syms[name][0],bytes(syms[name][1]))
    def seed(slot,kind,x,y,health=1,fire=60000):
        data=bytearray(estride);struct.pack_into('>hhii',data,0,x,y,x<<6,y<<6)
        struct.pack_into('>H',data,16,fire);data[30]=kind;data[31]=health;data[44]=1
        write(syms['enemies'][0]+slot*estride,data)
    def bullet(slot,x,y,mode=0,vx=0,vy=0):
        write(syms['pshots'][0]+slot*20,struct.pack('>iiiiBBBB',x<<6,y<<6,vx,vy,mode,0,1,0))
    def deaths():
        result=[]
        for i in range(4):
            d=read(syms['combatDeaths'][0]+i*dstride,dstride)
            if d[11]:result.append({'slot':i,'type':d[8],'age':int.from_bytes(d[4:6],'big'),'tile':int.from_bytes(d[6:8],'big'),'size':d[9],'frame':d[10],'ready':d[12]})
        return result
    def vr(addr,n):return bytes(vram[((addr+j)&65535)^1] for j in range(n))
    def shots(name):
        return [read(syms[name][0]+i*20,20) for i in range(16) if read(syms[name][0]+i*20+18,1)==b'\1']
    def sat():
        result=[];at=0
        for _ in range(80):
            off=0xf400+at*8;y=vw(off)&1023;sl=vw(off+2);attr=vw(off+4);x=vw(off+6)&1023
            result.append({'x':x-128,'y':y-128,'tile':attr&2047,'attr':attr,'size':sl>>8})
            at=sl&127
            if not at:break
        return result
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),'prep');run(2);baseline=snapshot()
        def enter(node=1):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1);until(lambda:state()==1,'play');run(fps*4)
            zeros('enemies');zeros('pshots');zeros('eshots');zeros('combatDeaths');w16('spawnTimer',60000);w16('invTimer',60000);pos(210,160)
        # One upload for all shots, outside the countdown area and unchanged scene.
        enter();run(3)
        expected=(GAME/'res/combat/shots.bin').read_bytes();assert vr(650*32,480)==expected
        report['checks']['projectileTilesExact']=True
        # Every species gets its own three streamed, PAL1-quantized death frames.
        layout=[]
        import re
        for a,b in re.findall(r'\{(\d+),(\d+)\}',(GAME/'src/system/video/combat_art_layout.h').read_text()):layout.append((int(a),int(b)))
        art=(GAME/'res/combat/deaths.bin').read_bytes()
        for kind in list(range(12))+[14]:
            enter();seed(0,kind,96,150);bullet(0,97,151);before=u16('kills');run(1)
            assert read(syms['enemies'][0]+44,1)==b'\0' and u16('kills')==before+1
            seen=set();frames=[];last_frames={};lifetime=(fps*(5 if kind==14 else 3)+9)//10
            for tick in range(lifetime+2):
                if kind in (10,14):shot('clip-%02d-%02d'%(kind,tick))
                for d in deaths():
                    if d['type']!=kind or not d['ready']:continue
                    start,tiles=layout[kind];want=art[(start+d['frame']*tiles*8)*4:(start+(d['frame']+1)*tiles*8)*4]
                    actual=vr((16+d['tile'])*32,len(want))
                    if actual!=want:
                        # ready means queued; retro_run may end before the game
                        # reaches its VBlank DMA flush. Bound that handoff,
                        # rather than treating two samples of age0 as two ticks.
                        previous=last_frames.get(d['slot'])
                        now=u32('vtimer')
                        if previous and previous[0]==d['frame']:
                            assert now-previous[1]<=3,('VRAM death upload timeout',kind,d)
                        else:last_frames[d['slot']]=(d['frame'],now)
                        continue
                    last_frames.pop(d['slot'],None)
                    seen.add(d['frame'])
                    if d['frame'] not in frames:frames.append(d['frame']);shot('death-%02d-%d'%(kind,d['frame']))
                run(1)
            assert seen=={0,1,2},(kind,seen);assert not deaths()
            assert u16('kills')==before+1,('duplicate death',kind)
            report['species'].append({'type':kind,'frames':sorted(seen),'logicalDeathImmediate':True,'countedOnce':True,'durationMs':lifetime*1000/fps});save()
        # Distinct style persists after the source enemy dies/despawns.
        for kind,style_id in [(0,1),(4,2),(8,3),(14,4)]:
            enter();seed(0,kind,80,140,10,0)
            if kind==14:write(syms['enemies'][0]+24,struct.pack('>H',4*fps))
            run(2);ss=shots('eshots');assert ss and all(s[16]==style_id for s in ss),(kind,[s[16] for s in ss])
            zeros('enemies');run(2);assert all(s[16]==style_id for s in shots('eshots'))
        report['checks']['allFourShooterStylesPersist']=True
        # Eight directional attributes, including every diagonal flip.
        dirs=[(192,0,0,0),(128,128,2,0),(0,192,1,0),(-128,128,2,0x800),(-192,0,0,0x800),(-128,-128,2,0x1800),(0,-192,1,0x1000),(128,-128,2,0x1000)]
        for style_id in range(5):
            for vx,vy,pose,flip in dirs:
                enter();name='pshots' if style_id==0 else 'eshots'
                write(syms[name][0],struct.pack('>iiiiBBBB',150<<6,140<<6,vx,vy,style_id,10,1,0));run(2)
                candidates=[s for s in sat() if 650<=s['tile']<=664]
                assert any(s['tile']==650+style_id*3+pose and s['attr']&0x1800==flip for s in candidates),(style_id,vx,vy,candidates)
        shot('projectiles-directional');report['checks']['fortyShotOrientations']=True
        # Pause/help borrows and restores combat tiles byte for byte; ages freeze.
        enter();seed(0,10,96,150);bullet(0,97,151);run(4)
        sprites=sat();corpse=next(i for i,s in enumerate(sprites) if 665<=s['tile']<=736);drops=[i for i,s in enumerate(sprites) if 21<=s['tile']<=49];assert all(corpse<i for i in drops),('drop covers death',sprites)
        before=vr(650*32,87*32);frozen=read(*syms['combatDeaths']);press(3);until(lambda:state()==2,'pause');run(fps)
        assert read(*syms['combatDeaths'])==frozen
        # Help page (down,A), back(B), resume(B). No actor reset.
        press(5);press(1);run(3);press(0);run(3);press(0);until(lambda:state()==1,'resume')
        assert vr(650*32,15*32)==before[:15*32]
        for d in deaths():
            if d['ready']:
                a,n=layout[d['type']];want=art[(a+d['frame']*n*8)*4:(a+(d['frame']+1)*n*8)*4];assert vr((16+d['tile'])*32,n*32)==want
        report['checks']['pauseHelpRestoresCombatArt']=True
        # Bomb removes all enemies with no new drop; only four visual records.
        enter();zeros('items');w16('bombs',2)
        for i in range(15):seed(i,i%9,40+(i%5)*45,80+(i//5)*40)
        press(0);assert not any(read(syms['enemies'][0]+i*estride+44,1)==b'\1' for i in range(16))
        assert u16('kills')==15 and len(deaths())<=4 and state()==1 and u8('settleKind')==1
        assert not any(read(*syms['items']))
        frozenpos=(u16('px'),u16('py'));hold({7,1},fps//10);assert (u16('px'),u16('py'))==frozenpos
        until(lambda:state()==4,'result-after-death');shot('last-death-result')
        report['checks']['bombNoDropBoundedPoolAndDelayedResult']=True
        # Burn and chain share the same death entry, including split spawn.
        enter();seed(0,0,96,150);write(syms['enemies'][0]+34,struct.pack('>HH',10,0));run(2);assert u16('kills')==1 and deaths()
        enter();seed(0,0,96,150);seed(1,0,120,150);seed(2,0,144,150);bullet(0,97,151,1);run(2);assert u16('kills')==3 and len(deaths())==3
        enter();seed(0,9,96,150);bullet(0,97,151);run(2);active=[read(syms['enemies'][0]+i*estride,estride) for i in range(16) if read(syms['enemies'][0]+i*estride+44,1)==b'\1'];assert len(active)==2 and all(e[30]==5 for e in active)
        report['checks']['burnChainAndSplitCountOnce']=True
        # Crowded scanlines: effects must not displace any previously admitted shot.
        enter()
        for i in range(10):seed(i,0,40+i*25,160,20)
        run(16)
        for name,style_id in [('pshots',0),('eshots',1)]:
            for i in range(16):write(syms[name][0]+i*20,struct.pack('>iiiiBBBB',(35+i*17)<<6,148<<6,0,0,style_id,10,1,0))
        run(3);base=snapshot()
        run(2) # Match restore()'s two post-load frames, including hero blink.
        baseline_counts=[]
        for _ in range(12):
            run();baseline_counts.append(sum(650<=s['tile']<=664 for s in sat()))
        restore(base)
        for i in range(4):write(syms['combatDeaths'][0]+i*dstride,struct.pack('>hhHHBBBBBB',40+i*60,160,0,649+i*16,10,32,255,1,0,0))
        observed=[]
        for tick in range(12):
            run();sprites=sat();observed.append(sum(650<=s['tile']<=664 for s in sprites))
            assert len(sprites)<=80
            for y in range(224):
                line=[s for s in sprites if s['y']<=y<s['y']+(((s['size']&3)+1)*8)]
                assert len(line)<=20 and sum((((s['size']>>2)&3)+1)*8 for s in line)<=320,('scanline overrun',tick,y)
        assert min(observed)>=min(baseline_counts)>0,(observed,baseline_counts)
        shot('crowded-combat');report['checks']['crowdedScanlinesKeepShotsAndHardwareLimits']=True
        # Boss uses36tiles and is presented fully before its after-dialogue.
        enter(20);zeros('enemies');seed(0,14,120,100);bullet(0,121,101);run(2)
        assert state()==1 and u8('settleKind')==2 and deaths()[0]['size']==48
        until(lambda:state()==6,'boss-death-before-dialogue');report['checks']['bossDeathBeforeFinalRadio']=True
        report['passed']=True;save();print(json.dumps(report,indent=2))
    except Exception as e:
        report['failures'].append(repr(e));shot('FAIL');save();raise
    finally:
        core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
