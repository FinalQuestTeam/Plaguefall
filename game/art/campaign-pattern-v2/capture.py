"""Campaign stages in the FINAL production ROM. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[2]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--shield-tests',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or Path(__file__).resolve().parent/'captures'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
        write(syms['pendingLevel'][0],bytes([node]));press(1)
        for _ in range(fps*12):
            if state()==1 and u8('currentLevel')==node:break
            run()
        assert state()==1 and u8('currentLevel')==node,('entry',node,state(),u8('currentLevel'))
        buttons.clear()
        for _ in range(fps*10):
            if u16('freezeTimer')==0 and frames()>5:break
            run()
        assert u16('freezeTimer')==0
        return snapshot()

    catalog=json.loads((Path(__file__).resolve().parent/'manifest.json').read_text())
    capture_report={'rom_sha256':hashlib.sha256(original).hexdigest(),'region':'PAL' if args.pal else 'NTSC','purpose':'visual camera inspection, not a gameplay completion test','setup':'Snapshots seed each real phase; RAM suppresses combat, progress and auto-interactions while player feet are moved to free positions. Native camera/streaming/rendering remain active.','phases':[]}
    wanted=None if args.nodes=='2,3,4,5,6,7,8' else set(map(int,args.nodes.split(',')))
    def suppress(ph):
        w16('hp',100)
        if 'surviveLeft' in syms:w16('surviveLeft',(120 if ph in ('5','15') else 90)*fps)
        if 'spawnTimer' in syms:w16('spawnTimer',60000)
        if ph in ('5','15'):w16('npcHp',180 if ph=='5' else 100)
        for name in ('pshots','eshots'):
            if name in syms:write(syms[name][0],bytes(syms[name][1]))
        keep=3 if ph=='8' else 1 if ph=='16' else 0
        for i in range(keep,16):write(enemy_addr+i*stride+44,bytes([0]))
        for name,off,count in [('campaignResistance',4,10),('campaignFactory',4,6),('campaignLaunch',0,10),('campaignRouteOps',0,4)]:
            if name in syms:write(syms[name][0]+off,bytes(count))
    def free(d,x,y):
        l,t,r,b=d['bounds'];solids=d['solids'][:]
        if d['phase']=='6B':solids+= d.get('gates',[])
        return l<=x<=r-15 and t<=y<=b-15 and not any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,*rest in solids)
    def closest(d,x,y):
        pts=[(abs(a-x)+abs(b-y),a,b) for a in range(d['bounds'][0],d['bounds'][2]-14,8) for b in range(d['bounds'][1],d['bounds'][3]-14,8) if free(d,a,b)]
        _,a,b=min(pts);return a,b
    for d in catalog['phases']:
        if wanted is not None and d['node'] not in wanted:continue
        ph=d['phase'];initial=enter(d['node']);folder=out/ph;folder.mkdir(exist_ok=True);worldW,worldH=d['size'];l,t,r,b=d['bounds']
        xs=[l+8,(l+r-15)//2,min(r-15,worldW-128)] if worldW<=768 else list(range(l+8,worldW-128,160))+[worldW-128]
        ys=[t+8,(t+b-15)//2,b-16];samples=[]
        shot('entry-'+ph)
        for yi,y in enumerate(ys):
            for xi,x in enumerate(xs):
                restore(initial);x,y2=closest(d,x,y);pos(x,y2)
                targetX=max(0,min(worldW-320,x+8-160));targetY=max(0,min(worldH-224,y2+8-16-124))
                ticks=int((abs(targetX-signed('cameraX'))+abs(targetY-signed('cameraY')))/3)+48
                for _ in range(ticks):
                    suppress(ph);run()
                    if state()!=1:break
                assert state()==1 and u8('currentLevel')==d['node'],('phase left during visual sweep',ph,xi,yi,state(),u8('currentLevel'))
                filename=f'{ph}/x{xi}-y{yi}.png';png(out/filename,w0:=320,h0:=224,rgb())
                visual=[]
                if 'objectiveVisuals' in syms:
                    rawobj=read(syms['objectiveVisuals'][0],84)
                    for i in range(7):
                        xx,yy,age,art,frame,mode,visible,ground,primed=struct.unpack_from('>hhH6B',rawobj,i*12)
                        if visible:visual.append(dict(slot=i,x=xx,y=yy,art=art,frame=frame,mode=mode,ground=ground))
                samples.append({'path':filename,'position':[signed('px'),signed('py')],'camera':[signed('cameraX'),signed('cameraY')],'row':yi,'col':xi,'visible_world':[signed('cameraX'),signed('cameraY')+24,signed('cameraX')+320,signed('cameraY')+224],'objectives':visual,'label':['Faixa superior','Campo central','Faixa inferior'][yi]})
        capture_report['phases'].append({'phase':ph,'node':d['node'],'samples':samples})
        (out/'capture-report.json').write_text(json.dumps(capture_report,ensure_ascii=False,indent=2)+'\n')
        print('CAPTURED',ph,len(samples),flush=True)
    core.retro_unload_game();core.retro_deinit()
    print('DONE',len(capture_report['phases']),'phases',flush=True)

if __name__=='__main__':main()
