"""Eight mission prototypes: real ROM, controller navigation, logic and FPS.

Run using arch -x86_64 /usr/bin/python3. Navigation and mission solutions use
controller input. Stress/failure probes explicitly seed RAM and are reported
separately; they never substitute for controller completion checks.
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
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--seconds',type=int,default=30);parser.add_argument('--rooms',default='11,12,13,14,15,16,17,18');parser.add_argument('--quick',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/objective-sprites-v1/validation/mission-polish'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    observer=None
    def run(n=1):
        for _ in range(n):
            core.retro_run()
            if observer:observer()
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
        ui(1);run(4 if action is not None else fps)
        wait(lambda:state()==1,'configuration')

    report={'passed':False,'region':'PAL' if args.pal else 'NTSC',
            'rom_sha256':hashlib.sha256(original).hexdigest(),'checks':{},'failures':[],
            'method':'Controller-only entry, configuration and solutions. RAM seeds only explicitly labelled boundary and worst-case stress probes.'}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(name,fn):
        try:
            value=fn();report['checks'][name]={'passed':True,'details':value};print('PASS',name,value,flush=True)
        except Exception as error:
            report['checks'][name]={'passed':False,'error':repr(error)};report['failures'].append(name);shot('FAIL-'+name);print('FAIL',name,repr(error),flush=True)
        save()
    def op():
        b=read(syms['operations'][0],34)
        return dict(work=struct.unpack('>3H',b[:6]),clock=int.from_bytes(b[6:8],'big'),
                    captured=int.from_bytes(b[12:14],'big'),done=b[20],delivered=b[21],
                    cargo=b[22],phase=b[23],gates=list(b[24:27]),outcome=b[27],bonus=b[28],post=b[29],trapped=int.from_bytes(b[30:32],'big'),opened=b[32],held=b[33])
    def enemy(i):
        b=read(syms['enemies'][0]+i*46,46)
        return {'x':int.from_bytes(b[:2],'big',signed=True),'y':int.from_bytes(b[2:4],'big',signed=True),
                'type':b[30],'hp':b[31],'active':bool(b[44])}
    def shots(name):return sum(bool(read(syms[name][0]+i*20+18,1)[0]) for i in range(16))
    def restart():
        pause();ui(5,2);ui(1);wait(lambda:state()==1 and not u8('testResult'),'restart',fps*20);run(fps//3)
    # Eight source layouts, also used to plan controller movement around walls.
    from build_operations import SOLIDS, EVAC_GATES, EVAC_ROUTE, CONTAINMENT
    def walls():
        room=u8('testStage');result=list(SOLIDS[room-11]);current=op()
        if room==11 and not current['done']&1:result.append((224,208,16,64))
        if room==16:
            result += [gate for i,gate in enumerate(EVAC_GATES) if current['gates'][i]]
        return result
    def clear(x,y):
        return 40<=x<=456 and 104<=y<=328 and all(not(x<rx+rw and x+16>rx and y<ry+rh and y+16>ry) for rx,ry,rw,rh in walls())
    def walk(tx,ty,fire=False,limit=1800):
        from collections import deque
        # Targets are player ground centers; the actual 16px body must fit.
        for _ in range(limit):
            if u8('testResult') or state()!=1:buttons.clear();return
            x,y=signed('px'),signed('py')
            if abs(x+8-tx)<=7 and abs(y+8-ty)<=7:buttons.clear();run(2);return
            start=(round(x/8)*8,round(y/8)*8);goal=(round((tx-8)/8)*8,round((ty-8)/8)*8)
            queue=deque([start]);previous={start:None};found=None
            while queue:
                q=queue.popleft()
                if abs(q[0]-goal[0])<=8 and abs(q[1]-goal[1])<=8:found=q;break
                for dx,dy in ((8,0),(-8,0),(0,8),(0,-8)):
                    nxt=(q[0]+dx,q[1]+dy)
                    if nxt not in previous and clear(*nxt):previous[nxt]=q;queue.append(nxt)
            assert found is not None,('no controller path',x,y,tx,ty,walls())
            if found==start:
                nx,ny=tx-8,ty-8
            else:
                while previous[found]!=start:found=previous[found]
                nx,ny=found
            keys={1} if fire else set()
            if x<nx-1:keys.add(7)
            elif x>nx+1:keys.add(6)
            if y<ny-1:keys.add(5)
            elif y>ny+1:keys.add(4)
            setkeys(keys,2)
        buttons.clear();raise AssertionError(('walk timeout',signed('px'),signed('py'),tx,ty))
    def work_at(x,y,n=2):walk(x,y+32);buttons.clear();run(int(fps*n)+8)
    points=((96,144),(400,144),(256,304))
    art_metadata=json.loads((GAME/'art/objective-sprites-v1/assets.json').read_text())['assets']
    art_binary=(GAME/'res/objectives/animations.bin').read_bytes()
    def visuals():
        address,size=syms['objectiveVisuals'];assert size==84
        result=[]
        for i in range(7):
            b=read(address+i*12,12)
            result.append(dict(x=int.from_bytes(b[:2],'big',signed=True),y=int.from_bytes(b[2:4],'big',signed=True),
                age=int.from_bytes(b[4:6],'big'),art=b[6],frame=b[7],mode=b[8],visible=b[9],ground=b[10]))
        return result
    def art_residency():
        bases=struct.unpack('>10H',read(syms['objectiveArtBases'][0],20));ranges=[]
        for art,base in enumerate(bases):
            if not base:continue
            meta=art_metadata[art];n=meta['bytes'];start=meta['offset_words']*4
            actual=bytes(vram[((base*32+j)&65535)^1] for j in range(n))
            assert actual==art_binary[start:start+n],('objective VRAM art differs',art,base)
            ranges.append((base,base+n//32,meta['name']))
        for a,b in zip(sorted(ranges),sorted(ranges)[1:]):assert a[1]<=b[0],('objective VRAM overlap',a,b)
        return {'palette':'production PAL1','resident_assets':ranges,'all_frames_match_rom':True}
    def gate_mount():
        meta=art_metadata[5];rows=meta['height']//8;start=meta['offset_words']*4
        def ink(x,y):
            tile=(x//8)*rows+y//8
            value=art_binary[start+tile*32+(y%8)*4+(x%8)//2]
            return bool(value&15 if x&1 else value>>4)
        center=meta['width']//2
        # The middle of the closed leaf follows the wall's north-south axis.
        # A frontal door can be correctly positioned but still fail this fit.
        for y in range(8,56):
            assert any(ink(x,y) for x in range(center-8,center+8)),('gate has a visible seam inside the opening',y)
        middle=[x for y in range(8,56) for x in range(meta['width']) if ink(x,y)]
        assert min(middle)>=center-12 and max(middle)<center+12,('gate body faces across wall instead of along it',min(middle),max(middle))
        assert any(ink(x,y) for y in range(8) for x in range(center-8,center+8)),'north jamb is detached'
        assert any(ink(x,y) for y in range(56,64) for x in range(center-8,center+8)),'south jamb is detached'
        mounted=[]
        for v,(x,y,w,h) in zip(visuals(),EVAC_GATES):
            assert (v['x'],v['y'])==(x+w//2,y+h),('gate art/collision anchor mismatch',v)
            assert any(rx==x and ry+rh==y for rx,ry,rw,rh in SOLIDS[5]),'north wall does not meet leaf'
            assert any(rx==x and ry==y+h for rx,ry,rw,rh in SOLIDS[5]),'south wall does not meet leaf'
            mounted.append({'leaf':[x,y,w,h],'north_jamb':[x,y-8,w,8],'south_jamb':[x,y+h,w,8]})
        return {'north_south_orientation':True,'closed_leaf_width_pixels':max(middle)-min(middle)+1,'mounts':mounted}
    def solution_with_animation(room):
        nonlocal observer
        masks={};captured=set();seen_modes={};pending_at_result=False;active_samples=[]
        stable_frames={};ground_samples=0
        def observe():
            nonlocal pending_at_result,ground_samples
            if state()!=1:return
            if not u8('testResult'):active_samples.append((u32('testTicks'),u32('vtimer')))
            if u8('testResult') and any(v['mode']==1 for v in visuals()):pending_at_result=True
            for slot,v in enumerate(visuals()):
                if not v['visible']:continue
                art=v['art'];frame=v['frame'];masks[art]=masks.get(art,0)|(1<<frame)
                seen_modes.setdefault(art,set()).add(v['mode'])
                meta=art_metadata[art];cx,cy=signed('cameraX'),signed('cameraY')
                on_screen=cx+meta['width']//2<=v['x']<=cx+320-meta['width']//2 and cy+56+meta['height']<=v['y']+8<=cy+224
                previous,count=stable_frames.get(slot,(-1,0));count=count+1 if previous==frame else 1
                stable_frames[slot]=(frame,count)
                if v['ground'] and on_screen and count>=3 and u32('vtimer')%13==0 and (art!=6 or v['mode']==0):
                    bases=struct.unpack('>10H',read(syms['objectiveArtBases'][0],20));base=bases[art]+frame*meta['tiles_per_frame']
                    col=(v['x']-meta['width']//2)//8;row=(v['y']-meta['height']+8)//8
                    rows,cols=meta['height']//8,meta['width']//8
                    for yy in range(rows):
                        for xx in range(cols):
                            source_tile=(meta['offset_words']*4)+(frame*meta['tiles_per_frame']+xx*rows+yy)*32
                            if not any(art_binary[source_tile:source_tile+32]):continue
                            actual=vw(0xe000+(((row+yy)&31)*64+((col+xx)&63))*2)&2047
                            expected=base+xx*rows+yy
                            assert actual==expected,('objective ground scroll/animation mismatch',art,slot,frame,col+xx,row+yy,actual,expected)
                    ground_samples+=1
                key=(art,frame)
                if frame>=2 and count>=3 and on_screen and key not in captured:
                    captured.add(key);shot('animation-%02d-%s-frame-%d'%(room,meta['name'],frame))
        observer=observe
        try:detail=solve(room)
        finally:observer=None
        primary=room-11
        expected=0x1c if room==18 else 0x3c
        assert masks.get(primary,0)&expected==expected,('missing action or resolved frame',room,masks)
        events=struct.unpack('>10H',read(syms['objectiveAnimationEvents'][0],20))
        assert events[primary]>=1,('action animation never triggered',room,events)
        if room==16:assert u8('dinorahState')==4 and signed('dinorahHp')>0,('Dinorah did not arrive alive',op())
        if room==12:
            assert pending_at_result,'final activation was not observed continuing after mission completion'
            pulse=set();steady=0;previous=-1;shots_taken=set()
            frozen=op()
            for _ in range(fps*2):
                run();frame=visuals()[2]['frame'];pulse.add(frame)
                steady=steady+1 if previous==frame else 1;previous=frame
                if steady>=3 and frame not in shots_taken:
                    shot('generator-powered-pulse-%d'%frame);shots_taken.add(frame)
            assert pulse=={3,4,5} and op()==frozen,('powered generator stopped pulsing after completion',pulse)
            detail['powered_pulse_after_result']=sorted(pulse)
        detail['animations']={'frame_masks':{art_metadata[k]['name']:hex(v) for k,v in masks.items()},
            'events':{art_metadata[k]['name']:v for k,v in enumerate(events) if v},
            'continues_after_result':pending_at_result,'native_captures':len(captured),'ground_map_samples':ground_samples}
        ticks=active_samples[-1][0]-active_samples[0][0];vblanks=active_samples[-1][1]-active_samples[0][1]
        detail['animations']['active_game_fps']=round(fps*ticks/vblanks,4)
        detail['animations']['missed_vblanks_during_actions']=vblanks-ticks
        return detail
    def paused_clock():
        pause();before=(op(),u32('testTicks'),visuals(),signed('dinorahX'),signed('dinorahY'));run(fps*2)
        assert before==(op(),u32('testTicks'),visuals(),signed('dinorahX'),signed('dinorahY')),'pause advanced mission/animation clock'
        ui(3);wait(lambda:state()==1,'resume');return {'pause_seconds':2,'frozen':True}
    def escort_node(target):
        for _ in range(fps*30):
            if u8('testResult') or u8('dinorahNode')>target:return
            node=u8('dinorahNode');tx,ty=EVAC_ROUTE[min(node,len(EVAC_ROUTE)-1)]
            x,y=signed('dinorahX')+8,signed('dinorahY')+8
            walk(x+max(-24,min(24,tx-x)),y+max(-24,min(24,ty-y)))
            run(fps//5)
        raise AssertionError(('escort stalled',target,u8('dinorahNode'),signed('dinorahX'),signed('dinorahY')))
    def solve(room):
        if room in (11,12,15):
            for x,y in points:work_at(x,y,2.2)
            if room!=12:walk(448,304)
        elif room==13:
            for _ in range(5):
                if op()['delivered']==3:break
                if op()['cargo']==255:
                    i=next(i for i in range(3) if not op()['done']&(1<<i))
                    walk(points[i][0]-8,points[i][1]+8);run(2)
                    assert op()['cargo']==255,'touching a closed chest skipped the bag'
                    run(fps);walk(points[i][0]-32,points[i][1]+32);shot('cargo-open-bag-%d'%i)
                    walk(points[i][0]+32,points[i][1]+16);run(3)
                    assert op()['cargo']==i,('bag was not picked up',i,op())
                    shot('cargo-bag-carried-%d'%i)
                walk(64,304);run(3)
            assert op()['delivered']==3 and op()['bonus']==1,op()
            walk(448,304)
        elif room==14:
            for i in range(3):
                started=u32('testTicks')
                while u32('testTicks')-started<fps*60:
                    if state()!=1:break
                    if op()['done']&(1<<i):break
                    target=enemy(i)
                    candidates=[(target['x']+dx,target['y']) for dx in (-64,64)]
                    candidates=[p for p in candidates if clear(*p)]
                    assert candidates,('no firing position',target)
                    tx,ty=min(candidates,key=lambda p:abs(p[0]-signed('px'))+abs(p[1]-signed('py')))
                    walk(tx+8,ty+8)
                    target=enemy(i)
                    if abs(target['y']-signed('py'))>10:continue
                    setkeys({7 if target['x']>signed('px') else 6},1)
                    setkeys({1},fps);buttons.clear();run(2)
                else:raise AssertionError(('transmitter survived',i,enemy(i),op()))
            buttons.clear()
        elif room==16:
            for i,(x,y,w,h) in enumerate(EVAC_GATES):
                escort_node((2,5,8)[i])
                if not i:run(4);shot('gate-mount-closed')
                walk(x-32,y+h//2+16);hold({7},2)
                for _ in range(fps*8):
                    if not op()['gates'][i]:break
                    setkeys({1})
                buttons.clear();assert op()['gates'][i]==0,op()
                escort_node((3,6,9)[i])
                if not i:shot('gate-mount-open')
            escort_node(len(EVAC_ROUTE)-1);run(fps)
            assert signed('dinorahHp')>0 and u8('dinorahState')==4,'Dinorah did not finish the corridor'
        elif room==17:
            for cycle in range(12):
                if u8('testResult'):break
                walk(224,192);walk(296,192)
                for _ in range(16):
                    if op()['held']>=2:break
                    run(fps//2);walk(296,192)
                assert op()['held']>=2,('lure did not fill cage before leaving',op())
                retained=op()['trapped']
                shot('containment-held-%d'%cycle)
                walk(224,192)
                for _ in range(fps):
                    run()
                    if cycle==0 and u32('vtimer')%6==0:shot('containment-occupied-frame-%d'%visuals()[1]['frame'])
                for i in range(16):
                    if op()['trapped']&(1<<i):
                        e=enemy(i);assert 248<=e['x']<=288 and 168<=e['y']<=200,('held insect is outside cage',e)
                walk(216,240)
                assert op()['trapped']&retained==retained,('captured insects escaped while walking to panel',op())
                shot('containment-locked-%d'%cycle)
                buttons.clear();run(fps*6//5);walk(192,304);run(fps*2)
            assert op()['captured']>=6,op()
        else:
            # Paused reinforcements let us validate the entire hold->retreat rule.
            run(fps*26);assert op()['phase']==1,op();walk(64,304)
        buttons.clear();run(5);assert u8('testResult')==1 and op()['outcome']==1,op()
        shot('room-%02d-success'%room)
        before=op();run(fps);assert op()==before,'completed objective must freeze'
        return {'controller_only':True,'state':op(),'hp':u16('hp'),'game_frames':u32('testTicks')}

    def seed_load(room):
        # Deliberate, documented RAM setup, not a claim about natural spawns.
        nonlocal allow_writes
        allow_writes=True
        try:
            pos(256,288)
            candidates=[(x,y) for y in (128,160,200,240,288,320) for x in (64,112,208,256,304,384,440)
                        if clear(x,y) and abs(x-256)+abs(y-288)>64]
            assert len(candidates)>=4
            cap=3 if room==16 else 4
            for i,(x,y) in enumerate(candidates[:cap]):
                kind=(0,4,7)[i] if room==16 else (0,4,5,7,2)[i%5]
                b=bytearray(46);struct.pack_into('>hhii',b,0,x,y,x<<6,y<<6)
                struct.pack_into('>H',b,16,fps);b[30]=kind;b[31]=200;b[43]=1;b[44]=1
                write(syms['enemies'][0]+46*i,b)
            for i in range(cap,16):write(syms['enemies'][0]+46*i+44,b'\0')
        finally:allow_writes=False
    def seed_projectiles():
        nonlocal allow_writes
        allow_writes=True
        try:
            for name,velocity,style in (('pshots',-128,0),('eshots',128,1)):
                for i in range(6):
                    # In the active viewport, separated over several scanlines.
                    x=128+(i%8)*32;y=168+(i//8)*64+(i%3)*8
                    write(syms[name][0]+20*i,struct.pack('>iiiiBBBB',x<<6,y<<6,0,velocity,style,10,1,0))
        finally:allow_writes=False
    def profile(room,stress):
        nonlocal allow_writes
        # Previous solution uses paused reinforcements. Baseline -> continuous.
        configure([(0,1)])
        if stress:
            configure([(1,4),(2,5)]) # all five projectiles and +100% movement
            seed_load(room)
        else:walk(96 if room==16 else 256,288)
        setkeys({1},fps*2);buttons.clear()
        if stress:seed_load(room)
        begin,vb=u32('testTicks'),u32('vtimer');counts=[];pools=[[],[]];cpu=[];health=[];prof={name:[] for name in ('operationsProfile','renderProfileTicks','playProfileTicks') if name in syms}
        for frame in range(fps*args.seconds):
            if room==16:
                # Sustain the load profile; the separate boundary test checks
                # that losing Dinorah really fails the playable mission.
                allow_writes=True
                try:w16('dinorahHp',100)
                finally:allow_writes=False
            if room==18:
                allow_writes=True
                try:
                    write(syms['operations'][0]+6,struct.pack('>H',fps*25))
                    write(syms['operations'][0]+29,bytes((60,)))
                finally:allow_writes=False
            if stress:
                seed_projectiles()
                allow_writes=True
                try:
                    for i in range(3 if room==16 else 4):write(syms['enemies'][0]+46*i+31,bytes((200,)))
                    # Keep the defense in its most expensive hold stage.
                    if room==18:write(syms['operations'][0]+6,struct.pack('>H',fps*25))
                finally:allow_writes=False
            # Fire and turn in place. No installation work can auto-complete.
            keys={1}
            if frame%(fps*2)==0:keys.add((7,5,6,4)[frame//(fps*2)%4])
            setkeys(keys)
            assert state()==1 and not u8('testResult'),('profile ended',room,op(),state())
            counts.append(active());pools[0].append(shots('pshots'));pools[1].append(shots('eshots'))
            cpu.append(u16('cpuFrameLoad')*100/2048);health.append(u16('hp'))
            for name in prof:prof[name].append(struct.unpack('>4H',read(syms[name][0],8)))
        buttons.clear();ticks=u32('testTicks')-begin;elapsed=u32('vtimer')-vb
        detail={'profile':('seeded %d enemies, 6+6 projectiles, max equipment'%(3 if room==16 else 4)) if stress else 'normal reinforcement cadence, controller fire, no-defeat enabled',
                'game_ram_setup':stress or room in (16,18),'radio_held_alive_for_measurement':room==18,
                'dinorah_held_alive_for_measurement':room==16,
                'game_frames':ticks,'physical_frames':elapsed,'fps':round(fps*ticks/elapsed,4),
                'missed_vblanks':elapsed-ticks,'target_met':ticks==elapsed,
                'enemies_min':min(counts),'enemies_max':max(counts),
                'player_shots_max':max(pools[0]),'enemy_shots_max':max(pools[1]),
                'cpu_max_pct':round(max(cpu),2),'cpu_p95_pct':round(sorted(cpu)[int(len(cpu)*.95)],2),
                'minimum_hp':min(health),'damage_taken':int.from_bytes(read(syms['phaseStats'][0]+2,2),'big')}
        detail['profiling']={name:[[round(statistics.mean(x[i] for x in values),2),max(x[i] for x in values)] for i in range(4)] for name,values in prof.items()}
        shot('room-%02d-%s'%(room,'stress' if stress else 'normal'))
        # Preserve exact misses and FPS in the report. Prototypes must retain
        # >=98% cadence normally and >=95% under a permanently full stress load.
        # target_met remains strict: a single dropped VBlank makes it false.
        detail['acceptance_minimum_fps']=fps*(.95 if stress else .98)
        assert detail['fps']>=detail['acceptance_minimum_fps'],detail
        if stress:assert max(counts)==(3 if room==16 else 4) and max(pools[0])==6 and max(pools[1])==6,detail
        return detail

    def boundaries(room):
        nonlocal allow_writes
        restart();saved=snap();allow_writes=True
        address=syms['operations'][0]
        try:
            # A visible exit never bypasses incomplete work/delivery/evacuation.
            pos(448-8,304-8);run(4)
            assert u8('testResult')==0,'premature completion at exit'
            if room==11:
                pos(56,304);write(address+20,b'\7');write(address+23,b'\1');write(address+6,b'\0\1');run(2)
                assert u8('testResult')==2,'demolition timeout did not fail'
            elif room==12:
                pos(248,328);run(fps*3);assert not op()['done']&4,'central panel enabled before generators'
            elif room==13:
                assert op()['delivered']==0 and op()['cargo']==255
            elif room==14:
                # All three reserved slots dying to a bomb still count exactly once.
                buttons.clear();hold({0},2);run(4) # B = the production bomb inventory
                assert u8('testResult')==1 and op()['done']==7,op()
            elif room==15:
                write(address+6,struct.pack('>H',fps*2));pos(184,144)
                before=u16('hp');run(fps//2);assert u16('hp')<before,'active thermal lane caused no damage'
            elif room==16:
                pos(136,184);hold({7},12);assert signed('px')<=144,'closed gate failed to block movement'
                assert op()['done']==0,'crossing gate awarded evacuation without breaking it'
                # Remove only the leaves. Both wall ends must remain solid,
                # while the middle must let a full-size body pass eastward.
                write(address+24,b'\0\0\0')
                for x,y,w,h in EVAC_GATES:
                    for yy in (y-8,y+h-8):
                        pos(x-24,yy);hold({7},12)
                        assert signed('px')<=x-16,('open gate lost a permanent jamb',x,yy,signed('px'))
                    pos(x-24,y+16);hold({7},30)
                    assert signed('px')>=x+w,('open passage still blocked',x,signed('px'))
                shot('gate-jamb-collision-check')
                w16('dinorahHp',0);run(2)
                assert u8('testResult')==2,'losing Dinorah did not fail the escort'
            elif room==17:
                write(address+23,b'\1');write(address+6,b'\0\1');pos(272,200)
                before=u16('hp');run(3);assert u16('hp')<before,'armed trap did not harm player inside'
            elif room==18:
                write(address+29,b'\0');run(2);assert u8('testResult')==2,'radio destruction did not fail'
                run(fps);assert visuals()[0]['frame']==5 and visuals()[0]['mode']==4,'radio wreck animation did not finish after failure'
                shot('radio-destroyed-after-result')
        finally:allow_writes=False;restore(saved)
        return {'isolated_ram_setup':True,'exit_guard':True,'rule_boundary':True}

    def difficulty(room):
        # A repeatable route bot, without invincibility or RAM preparation.
        # It aims/shoots for the hunt and gates, but does not use bombs or
        # dodge intelligently. These numbers are a pressure probe, not a
        # substitute for human playtesting.
        saved=snap()
        try:
            configure([(0,1),(3,-1)])
            error=None
            try:solve(room)
            except AssertionError as e:error=repr(e)
            return {'controller_only':True,'no_defeat':False,'bot_won':u8('testResult')==1,
                    'hp_remaining':u16('hp'),'active_seconds':round(u32('testTicks')/fps,2),
                    'damage_taken':int.from_bytes(read(syms['phaseStats'][0]+2,2),'big'),
                    'outcome':op(),'bot_limit':error}
        finally:restore(saved)

    run(120);ui(3);run(4*fps);ui(5,3);ui(1);run(fps);shot('room-selector')
    ui(5,10);shot('room-selector-missions');ui(1)
    wait(lambda:state()==1 and u8('testStage')==11,'first-mission',fps*20)
    run(fps);shot('room-11-entry')
    rooms=[int(x) for x in args.rooms.split(',')]
    for room in rooms:
        if u8('testStage')!=room:switch(room)
        check('room-%d-entry'%room,lambda:{'controller_only':True,'room':u8('testStage'),'state':op(),'enemies':active()})
        shot('room-%02d-entry'%room)
        check('room-%d-pause'%room,paused_clock)
        configure([(0,-1),(3,1)]) # paused reinforcements, no defeat; normal rules
        if room==16:check('room-16-gate-mount',gate_mount)
        check('room-%d-art-residency'%room,art_residency)
        check('room-%d-solution'%room,lambda room=room:solution_with_animation(room))
        check('room-%d-boundaries'%room,lambda room=room:boundaries(room))
        if not args.quick:
            check('room-%d-difficulty-probe'%room,lambda room=room:difficulty(room))
            check('room-%d-normal-performance'%room,lambda room=room:profile(room,False))
            check('room-%d-stress-performance'%room,lambda room=room:profile(room,True))
    report['passed']=not report['failures'];save();core.retro_unload_game();core.retro_deinit()
    assert report['passed'],report['failures']


if __name__=='__main__':main()
