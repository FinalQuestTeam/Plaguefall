"""Native resistance HUD verification in the production ROM. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
"""
from pathlib import Path
import os,re,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import encode
GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--shield-tests',action='store_true');parser.add_argument('--status-tests',action='store_true');parser.add_argument('--player-shield-tests',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/hud-resistencia-v1/integracao/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    assert u8('currentLevel')==1 and u16('arenaMaxX')==495
    shot('01-inicio')
    baseline=snapshot()
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    names={2:'phase02a-service-v1',3:'phase02b-detour-v1',4:'phase03-shelter-v1',5:'phase04-tunnels-v1',6:'phase05-beacon-v1',7:'phase06a-rescue-v1',8:'phase06b-withdrawal-v1'}
    tracks={2:3,3:1,4:1,5:2,6:3,7:1,8:2}
    installation=json.loads((GAME/'art/phases02-06-v1/integration-export.json').read_text())
    installed={s['id'].upper():s for s in installation['stages']}
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),
            'emulated_rom_sha256':hashlib.sha256(data).hexdigest(),'production_rom':str(rom),'temporary_build':False,
            'region_header_override_in_memory_only':args.pal,'core_fps':av.timing.fps,'stages':[], 'failures':[],
            'method':'Controller enters phase 1. Kills and pendingLevel are accelerated only in node setup. All ordinary attempts restore a node baseline then enable an enforced RAM-write guard. Isolated probes/stress explicitly use RAM setup. FPS = region_fps * phaseStats.frames / vtimer VBlanks.'}
    def save_report():
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(label,fn,results):
        try:
            value=fn();results[label]={'passed':True,'details':value};print('PASS',label,flush=True);return value
        except Exception as exc:
            import traceback;traceback.print_exc()
            detail={'passed':False,'error':repr(exc)};results[label]=detail;report['failures'].append({'check':label,'error':repr(exc)})
            print('FAIL',label,repr(exc),flush=True);shot('FAIL-'+label.replace('/','-'));save_report();return None
    def state():return u32('flow_state')
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def clear_enemies():
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
    def isolate():
        w16('spawnTimer',60000);clear_enemies()
        for name in ('pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
    def enter(node):
        restore(baseline);isolate();w16('kills',10);run(4*fps)
        # Regional atlas preparation can span VBlanks after the completion timer.
        # Wait for the real transition instead of assuming a four-second deadline.
        for _ in range(4*fps):
            if state()!=4:break
            run()
        assert state() in (5,6),('phase1 exit',state())
        for _ in range(40):
            if state()==1 and u8('currentLevel')==node:break
            assert state()!=3,('setup died',node)
            write(syms['pendingLevel'][0],bytes([node]));press(1);run(fps//4)
            if state()==6:press(3);run(fps//4)
        else:raise AssertionError(('node entry failed',node,state(),u8('currentLevel')))
        run(3*fps+4)
        # Heavy scene/panel loads span VBlanks. Release A until the countdown
        # is over and PLAYER_update has armed autofire before saving a match.
        buttons.clear()
        for _ in range(5*fps):
            if u16('freezeTimer')==0 and frames()>=5:break
            run()
        else:raise AssertionError(('phase countdown did not finish',node))
        assert state()==1 and u8('currentLevel')==node
        return snapshot()
    def enemies():
        result=[]
        for i in range(16):
            address=enemy_addr+i*stride
            if read(address+44,1)[0]:
                x,y=struct.unpack('>hh',read(address,4));kind=read(address+30,1)[0]
                result.append((x,y,kind))
        return result
    def formation(d,count=4,shots=6,tick=0,axis='horizontal'):
        isolate();w16('hp',100);w16('kills',0);w16('freezeTimer',0)
        if 'surviveLeft' in syms:w16('surviveLeft',60*fps)
        if 'npcHp' in syms:w16('npcHp',100)
        left,top,width,height=d['walkable'];right,bottom=left+width-16,top+height-16
        def triangle(lo,hi):
            span=hi-lo;t=(tick*3)%(span*2);return lo+(t if t<=span else 2*span-t)
        pos(triangle(left,right) if axis=='horizontal' else (left+right)//2,
            triangle(top,bottom) if axis=='vertical' else (top+bottom)//2)
        for i in range(count):
            x=left+32+(i%2)*max(48,width-96);y=top+24+(i//2)*max(32,height-80)
            buf=bytearray(stride);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,32,0,600,600)
            buf[30],buf[31],buf[43],buf[44]=i%2,20,1,1;write(enemy_addr+i*stride,buf)
        for name in ('pshots','eshots'):
            address,size=syms[name];assert size==320
            for i in range(shots):
                buf=bytearray(20);struct.pack_into('>iiii',buf,0,(left+24+i%3*48)<<6,(top+24+i//3*40)<<6,32,0)
                buf[17],buf[18]=1,1;write(address+i*20,buf)
    def terrain_center(rect):
        x,y,rw,rh=rect;return x+min(16,rw//2)-8,y+min(16,rh//2)-8
    def overlapping(x,y,rect,size=16):
        a,b,c,e=rect;return x<a+c and x+size>a and y<b+e and y+size>b
    def free(d,x,y):
        a,b,c,e=d['walkable']
        if not(a<=x<=a+c-16 and b<=y<=b+e-16):return False
        return not any(overlapping(x,y,r['rect'] if isinstance(r,dict) else r) for r in d['solids']+d['hazards'])
    def dry_route(d):
        from collections import deque
        start=tuple(d['start']);goal=tuple(d['exit']);todo=deque([start]);parents={start:None}
        while todo:
            p=todo.popleft()
            if p==goal:break
            x,y=p
            for q in [(x+8,y),(x-8,y),(x,y+8),(x,y-8)]:
                if q not in parents and free(d,*q):parents[q]=p;todo.append(q)
        assert goal in parents
        route=[];p=goal
        while p is not None:route.append(p);p=parents[p]
        return list(reversed(route))
    report['checks']={}
    report['method']='Real production HUD/VDP patterns. RAM prepares phases, inventory, counters and isolated projectiles. Selection, item use, pause/resume and rendering use normal production code.'
    font_text=(GAME/'src/system/video/screens/result_font.h').read_text()
    font=list(map(int,re.findall(r'\d+',re.search(r'RESULT_FONT\[768\] = \{(.*?)\};',font_text,re.S)[1])))
    def rawv(address,count):return bytes(vram[(address+i)^1] for i in range(count))
    def hud_patterns():return rawv(425*32,120*32)
    def pixels():
        for _ in range(fps//2):
            if hud_patterns()==read(*syms['hudPixels']):break
            run()
        result=[[0]*320 for _ in range(24)]
        for row in range(3):
            for col in range(40):
                attr=vw(u16('window_addr')+(row*64+col)*2)
                assert attr&2047==425+row*40+col,('panel map',row,col,attr)
                assert attr&0x8000 and (attr>>13)&3==1,('panel priority/palette',attr)
                tile=rawv((attr&2047)*32,32)
                for y in range(8):
                    for x in range(8):result[row*8+y][col*8+x]=(tile[y*4+x//2]>>(0 if x&1 else 4))&15
        assert all(c for row in result for c in row),'transparent HUD pixels'
        assert hud_patterns()==read(*syms['hudPixels']),'pending/stale HUD patterns'
        return result
    def glyphs(p,s,x,y,color=1):
        for i,c in enumerate(s):
            for yy in range(8):
                for xx in range(8):
                    if font[(encode(c)[0]-32)*8+yy]&(128>>xx):
                        assert p[y+yy][x+i*8+xx]==color,('glyph',s,x,y,i,xx,yy,p[y+yy][x+i*8+xx],color)
    def panel():
        p=pixels();assert bytes((C.c_ubyte*32).in_dll(core,'reg'))[18]==3
        return p
    def hit(damage):
        buf=bytearray(20)
        struct.pack_into('>iiii',buf,0,(u16('px')+4)<<6,(u16('py')+4)<<6,0,0)
        buf[16:19]=bytes((1,damage,1));write(syms['eshots'][0],buf);run(12)
    def health(expected):
        p=panel();glyphs(p,f'VIDA {expected:03}',242,3)
        fill=(expected*66+50)//100
        assert p[16][243:309]==[4 if expected<=25 else 1]*fill+[11]*(66-fill),'life highlight'
        assert p[17][243:309]==[3 if expected<=25 else 14]*fill+[11]*(66-fill),'life bar'
    if args.player_shield_tests:
        def player_shield_probe():
            restore(baseline);isolate();pos(160,200);run(20)
            w16('freezeTimer',0)
            def badges():
                result=[];index=0
                for _ in range(80):
                    address=u16('slist_addr')+index*8
                    yy,ss,attr,xx=[vw(address+j) for j in (0,2,4,6)]
                    if attr&2047==16+85:
                        result.append(dict(x=(xx&511)-128,y=(yy&511)-128,
                            w=(((ss>>10)&3)+1)*8,h=(((ss>>8)&3)+1)*8,pal=(attr>>13)&3))
                    index=ss&127
                    if not index:return result
                raise AssertionError('SAT loop')
            def active(seconds,stacked=True):
                p=panel();glyphs(p,str(seconds),225,3 if stacked else 8)
                if stacked:glyphs(p,'3',225,13,2)
                mm=badges();assert len(mm)==1,mm
                b=mm[0];assert b['w']==b['h']==8 and b['pal']==1,b
                assert 0<=b['x']<=312 and 26<=b['y']<=216,b
                return b
            assert not badges()
            # Real controller activation: ice first, then shield, with a spare.
            write(syms['item'][0],bytes((6,3,4,1,4,1)))
            press(8);press(0);run(8)
            assert u8('shotMode')==2 and u8('modeCharges')==3
            press(8);press(0);run(8)
            assert 2*fps<u16('shieldTimer')<=3*fps
            active(3);shot('player-shield-3-ice')
            # The badge remains visible throughout the active effect.
            for _ in range(16):run();assert len(badges())==1
            # Pause must freeze the countdown, then restore both HUD rows.
            press(3)
            for _ in range(2*fps):
                if state()==2:break
                run()
            assert state()==2
            paused=u16('shieldTimer');run(fps);assert u16('shieldTimer')==paused
            press(3)
            for _ in range(2*fps):
                if state()==1:break
                run()
            assert state()==1
            active((u16('shieldTimer')+fps-1)//fps)
            observed=[]
            for seconds in (2,1):
                for _ in range(2*fps):
                    if u16('shieldTimer')<=seconds*fps:break
                    run()
                assert 0<u16('shieldTimer')<=seconds*fps
                active(seconds);shot('player-shield-'+str(seconds));observed.append(seconds)
            # A second shield restarts the actual gameplay timer at 3 seconds.
            press(8);press(0);run(8);assert u16('shieldTimer')>2*fps
            active(3)
            for x,y in ((0,u16('arenaMinY')),(u16('arenaMaxX')-15,u16('arenaMinY'))):
                pos(x,y);run(8);active((u16('shieldTimer')+fps-1)//fps)
            shot('player-shield-north-edge')
            pos(160,200);run(8)
            for _ in range(4*fps):
                if not u16('shieldTimer'):break
                run()
            else:raise AssertionError('player shield did not expire')
            run(12);assert not badges(),'expired player badge remained'
            p=panel();glyphs(p,'3',225,8,2)
            assert p[4][214]==6,'active weapon box was not restored'
            shot('player-shield-expired-ice')
            # Shield alone uses the full-height active-effect box.
            write(syms['item'][0],bytes((4,1,255,0,255,0)))
            write(syms['sel'][0],bytes((1,)))
            write(syms['shotMode'][0],bytes((0,)));write(syms['modeCharges'][0],bytes((0,)))
            press(0);run(8);active(3,False);shot('player-shield-alone')
            for _ in range(4*fps):
                if not u16('shieldTimer'):break
                run()
            run(12);assert not badges()
            assert panel()[4][214] not in (4,6),'expired effect box remained'
            return dict(countdown=[3,*observed],real_item_activation=True,enemy_badge_art=True,
                persistent_badge=True,pause_freezes_timer=True,reuse_restarts_timer=True,
                screen_edges=True,weapon_coexistence=True,expiry_clears_hud_and_badge=True)
        check('player-shield',player_shield_probe,report['checks'])
        report['heap_sentinel_intact']=read(u32('heapEnd')&65535,2)==bytes(2)
        assert report['heap_sentinel_intact']
        report['passed']=not report['failures'];save_report()
        core.retro_unload_game();core.retro_deinit()
        print(json.dumps(dict(passed=report['passed'],region=report['region'],failures=report['failures'])),flush=True)
        raise SystemExit(0 if report['passed'] else 1)
    if args.status_tests:
        def status_probe():
            restore(baseline);isolate();pos(96,200);run(20)
            w16('freezeTimer',0)
            # Check the actual composited inventory, including the opaque backing.
            expected=json.loads((GAME/'art/cangaco-itens-v2/source/hud-glyphs.json').read_text())['bomb']
            p=panel()
            assert all(p[8+y][111+x]==(11 if c=='.' else int(c,16))
                for y,row in enumerate(expected) for x,c in enumerate(row)), 'bomb HUD pixels'
            shot('bomb-hud')
            def sat():
                result=[];index=0
                for _ in range(80):
                    address=u16('slist_addr')+index*8
                    yy,ss,attr,xx=[vw(address+j) for j in (0,2,4,6)]
                    result.append(dict(x=(xx&511)-128,y=(yy&511)-128,
                        w=(((ss>>10)&3)+1)*8,h=(((ss>>8)&3)+1)*8,
                        tile=attr&2047,pal=(attr>>13)&3))
                    index=ss&127
                    if not index:return result
                raise AssertionError('SAT loop')
            tiles={1:16+85,2:16+87,4:16+88}
            def markers():return [s for s in sat() if s['tile'] in tiles.values()]
            def seed(kind,flags,x=224,y=200,duration=4*fps):
                clear_enemies()
                buf=bytearray(stride)
                struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6)
                struct.pack_into('>HHHHHH',buf,16,60000,60000,60000,0,60000,60000)
                buf[30],buf[31],buf[42],buf[43],buf[44]=kind,200,int(bool(flags&1)),1,1
                struct.pack_into('>HHH',buf,32,duration if flags&4 else 0,duration if flags&2 else 0,60000)
                write(enemy_addr,buf);run(12)
            cases=[]
            # Small/medium/large insects, boss and both training targets.
            for kind in (0,2,6,10,12,13,14):
                for flags in (2,4,7):
                    seed(kind,flags)
                    for _ in range(16):
                        run();mm=markers()
                        assert {s['tile'] for s in mm}=={t for f,t in tiles.items() if flags&f},(kind,flags,mm)
                        assert all(s['w']==s['h']==8 and s['pal']==1 for s in mm),mm
                        assert all(0<=s['x']<=312 and 26<=s['y']<=216 for s in mm),mm
                        assert all(abs(a['x']-b['x'])>=10 for i,a in enumerate(mm) for b in mm[i+1:]),mm
                        # A marker must coexist with its rendered body.
                        assert any(s['w']>=16 and s['pal']==1 and abs(s['x']-(224-u16('cameraX')))<=16 for s in sat()),kind
                        assert read(enemy_addr+40,2)==bytes(2),'burn probe unexpectedly flashed'
                    shot('status-%d-%d'%(kind,flags));cases.append([kind,flags])
            # Natural timer expiry: marker must clear without further RAM setup.
            for flag,offset in ((2,34),(4,32)):
                seed(0,flag,duration=40)
                assert markers()
                for _ in range(2*fps):
                    if read(enemy_addr+offset,2)==bytes(2):break
                    run()
                else:raise AssertionError('status never expired')
                run(8);assert not markers(),('expired marker remained',flag,markers())
            for x,y in ((0,40),(304,40),(304,200)):
                seed(0,7,signed('cameraX')+x,signed('cameraY')+y);mm=markers()
                assert len(mm)==3 and all(0<=s['x']<=312 and s['y']>=26 for s in mm),mm
                shot('edge-%d-%d'%(x,y))
            return dict(cases=cases,bomb_pixels=True,persistent_between_burn_ticks=True,
                timer_expiry=True,concurrent_statuses=True,screen_edges=True)
        check('enemy-status-and-bomb',status_probe,report['checks'])
        report['heap_sentinel_intact']=read(u32('heapEnd')&65535,2)==bytes(2)
        assert report['heap_sentinel_intact']
        report['passed']=not report['failures'];save_report()
        core.retro_unload_game();core.retro_deinit()
        print(json.dumps(dict(passed=report['passed'],region=report['region'],failures=report['failures'])),flush=True)
        raise SystemExit(0 if report['passed'] else 1)
    def equipment():
        enter(6);isolate();run(fps);w16('surviveLeft',30*fps)
        assert syms['item'][1]==6
        write(syms['item'][0],bytes((4,1,5,5,6,3)));run(12)
        for selected in range(4):
            p=panel()
            for i in range(4):assert p[3][108+i*26]==(4 if i==selected else 10)
            if selected<3:hold({8},4);run(4)
        hold({0},4);run(12)
        assert u8('shotMode')==2 and u8('modeCharges')==3
        p=panel();glyphs(p,'3',225,8,2);assert p[4][214]==6
        assert any(p[y][x]==2 for y in range(8,16) for x in range(216,224)),'ice mode icon'
        shot('proteger-equipamento')
        hold({1},fps*2);run(12)
        assert u8('modeCharges')==0 and u8('shotMode')==0
        assert panel()[4][214]!=6,'empty active-mode box remained visible'
        return {'four_selection_borders':True,'real_ice_activation':True,'charges':3,'native_scale':True}
    check('equipment',equipment,report['checks'])
    def protection_and_life():
        isolate();w16('surviveLeft',30*fps);run(12)
        p=panel();glyphs(p,'PROTEJA',8,3);glyphs(p,'100',20,13);health(100)
        hit(24);health(76);shot('proteger-vida-076')
        run(2*fps);hit(52);health(24);shot('proteger-vida-baixa')
        return {'opaque_320x24':True,'actual_projectile_damage':[100,76,24],'numeric_and_bar_agree':True,'low_life_red':True}
    check('protection-life',protection_and_life,report['checks'])
    def occlusion_pause_camera():
        isolate();w16('surviveLeft',30*fps);run(12);before=rgb()[:320*24*3]
        buf=bytearray(46);x,y=100,u16('cameraY')+16
        struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6)
        struct.pack_into('>HHHHHH',buf,16,60000,60000,60000,0,0,0)
        buf[30:32]=bytes((2,20));buf[44]=1;struct.pack_into('>H',buf,32,60000)
        write(enemy_addr,buf);run(8)
        assert rgb()[:320*24*3]==before,'world sprite covered the HUD'
        clear_enemies();run(12);original=hud_patterns()
        hold({3},4)
        for _ in range(3*fps):
            if state()==2:break
            run()
        assert state()==2,'pause failed'
        shot('pausa');buttons.clear();run(8);hold({3},8);run(fps);assert state()==1
        restored=hud_patterns()
        assert all(restored[(row*40+13)*32:(row*40+40)*32]==original[(row*40+13)*32:(row*40+40)*32] for row in range(3)),'pause did not restore equipment/life patterns'
        pos(64,200);run(fps);assert 120-u16('cameraY')>=24,'Santa lacks headroom nearby'
        shot('santa-folga-superior')
        pos(64,u16('arenaMaxY')-15);run(fps);assert u16('py')+17-u16('cameraY')<=224,'player left viewport at south wall'
        p=panel();glyphs(p,'PROTEJA',8,3);shot('santa-limite-sul')
        return {'sprites_cannot_cover_panel':True,'pause_exact_restore':True,'near_santa_headroom':True,'south_wall_player_visible':True}
    check('occlusion-pause-camera',occlusion_pause_camera,report['checks'])
    def other_objectives():
        enter(4);isolate();w16('kills',8);run(12);p=panel();glyphs(p,'ELIMINE',8,3);glyphs(p,'08/14',20,13,4);shot('eliminar')
        enter(5);isolate();run(12);glyphs(panel(),'SAÍDA',8,3);shot('travessia')
        enter(8);isolate();run(12);p=panel()
        label={1:'COBERTURA',2:'PASSAGEM'}.get(u8('dinorahState'),'DINORAH')
        # Read the current native companion state; no route state writes.
        candidates=['DINORAH','COBERTURA','PASSAGEM'];matched=[]
        for label in candidates:
            try:glyphs(p,label,8,3);matched.append(label)
            except AssertionError:pass
        assert len(matched)==1,matched
        shot('escolta')
        enter(20);w16('spawnTimer',60000)
        address=next(enemy_addr+i*stride for i in range(16) if read(enemy_addr+i*stride+30,1)[0]==14 and read(enemy_addr+i*stride+44,1)[0])
        write(address+32,struct.pack('>H',60000));run(12)
        maximum=read(address+31,1)[0];write(address+31,bytes((maximum-7,)));run(12)
        p=panel();glyphs(p,'ESCORPIÃO',8,3);glyphs(p,f'{maximum-7:03}/{maximum:03}',20,13,4)
        shot('escorpiao')
        pos(64,u16('arenaMinY'));run(fps)
        assert u16('py')-31-u16('cameraY')>=24,'classic arena hides player behind HUD'
        shot('arena-classica-limite-norte')
        return {'kill_counter':True,'route_exit':True,'companion_state':matched[0],'boss_live_hp':True,'classic_arena_hud':True}
    check('objectives',other_objectives,report['checks'])
    def zero_life():
        enter(6);isolate();run(fps);hit(100)
        for _ in range(5*fps):
            if state()==3:break
            run()
        assert state()==3 and u16('lastLife')==0,'lethal hit did not reach zero-life result'
        canvas=read(*syms['hudPixels'])
        for x in range(243,309):
            offset=((17//8)*40+x//8)*32+(17%8)*4+(x%8)//2
            assert (canvas[offset]>>(0 if x&1 else 4))&15==11,'zero life bar still filled'
        shot('derrota')
        return {'lethal_hit_zero_hp':True,'bar_empty':True,'result_loaded':True}
    check('zero-life',zero_life,report['checks'])
    report['heap_sentinel_intact']=read(u32('heapEnd')&65535,2)==bytes(2)
    assert report['heap_sentinel_intact'],'stack damaged heap sentinel'
    report['passed']=not report['failures'];save_report()
    core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':report['passed'],'region':report['region'],'failures':report['failures']}),flush=True)
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
