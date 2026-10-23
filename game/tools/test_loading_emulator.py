"""Campaign loading regression, NTSC/PAL, all A or B branches.

Run with arch -x86_64 /usr/bin/python3. RAM accelerates objectives and selects
branch statistics; production code owns loading, audio, input and transitions.
Checks the minimum visible time, frozen simulation, held START, audio service
intervals, black-frame bounds and balanced loading ownership.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import encode, decode
GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--branch-b',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/phase-countdown-v1/validation'/(('pal' if args.pal else 'ntsc')+('-b' if args.branch_b else ''));out.mkdir(parents=True,exist_ok=True);(out/'report.json').unlink(missing_ok=True)
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
    frameLog=[];trackFrames=False
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
        if trackFrames:frameLog.append(raw.count(0)>len(raw)*0.995)
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
    cram=(C.c_uint16*64).in_dll(core,'cram')
    overlay=(GAME/'res/radio_panel/tiles.bin').read_bytes()
    # Genesis Plus GX keeps each native VRAM word byte-swapped on this host.
    overlay_raw=bytes(value for pair in zip(overlay[1::2],overlay[::2]) for value in pair)
    overlay_colors=list(struct.unpack('>16H',(GAME/'res/radio_panel/palette.bin').read_bytes()))
    overlay_colors[15]=0x4ce
    overlay_colors=[(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6) for c in overlay_colors]
    overlay_checked=0
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
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    def prep(label):
        until(lambda:state() in (0,6),label+'-entry')
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),label)
        until(lambda:not u8('transitioning'),label+'-ready');run(2)
    # Observe the final ROM without patching instructions or bypassing loads.
    from collections import Counter
    import bisect
    fullsyms=[]
    for ln in symbols.splitlines():
        ps=ln.split()
        if len(ps)==4 and ps[2].lower()=='t':fullsyms.append((int(ps[0],16),int(ps[1],16),ps[3]))
    fullsyms.sort();starts=[s[0] for s in fullsyms]
    def location(pc):
        i=bisect.bisect_right(starts,pc)-1
        if i>=0 and pc<fullsyms[i][0]+fullsyms[i][1]:return fullsyms[i][2]
        return hex(pc)
    core.m68k_get_reg.argtypes=[C.c_int];core.m68k_get_reg.restype=C.c_uint
    framesLog=[];segment='boot';capture=False
    baseRun=run
    def run(n=1):
        nonlocal overlay_checked
        for _ in range(n):
            baseRun()
            if capture:
                if u8('loadingActive'):
                    assert bytes(vram[64:64+len(overlay_raw)])==overlay_raw,'destination overwrote visible radio tiles'
                    assert list(cram[:16])==overlay_colors,'destination overwrote visible radio palette'
                    overlay_checked+=1
                pc=core.m68k_get_reg(16)
                framesLog.append({'segment':segment,'state':state(),'node':u8('currentLevel'),
                    'black':bool(raw and raw.count(0)>len(raw)*0.995),
                    'display':bool(read(syms['regValues'][0]+1,1)[0]&64),
                    'transition':u8('transitioning'),'vtimer':u32('vtimer'),
                    'musicClock':u32('resultCueLastVBlank') if u8('resultCueKind') else u32('lastVBlank'),'loading':u8('loadingActive'),'loadingStart':u32('loadingStart'),'digit':u8('loadingDigit'),'resultActive':u8('resultActive'),'freeze':u16('freezeTimer'),'phaseFrames':int.from_bytes(read(syms['phaseStats'][0]+4,4),'big'),
                    'psgCache':(read(*syms['lastFreq'])+read(*syms['lastVol'])).hex(),
                    'pc':hex(pc),'function':location(pc),
                    'rowTop':u16('rowTop'),'overlayCount':u16('overlayCount')})
    def longest(values):
        best=cur=0
        for value in values:
            cur=cur+1 if value else 0;best=max(best,cur)
        return best
    measurements=[]
    def border():
        # Eight native pixels around the shared radio artwork never change.
        bpp=4 if fmt==1 else 2
        return b''.join(raw[y*pitch:y*pitch+w*bpp] if y<8 or y>=h-8 else
            raw[y*pitch:y*pitch+8*bpp]+raw[y*pitch+(w-8)*bpp:y*pitch+w*bpp] for y in range(h))
    def measure(label,action,predicate,limit=1800):
        nonlocal segment,capture,record,audio
        segment=label;capture=True;start=len(framesLog)
        recordClip=False
        if recordClip:
            audio=wave.open(str(out/'result-to-map-4.wav'),'wb');audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate));record=True
        continuous=label.startswith(('prep-to-play-','arrival-radio-to-prep-'))
        old_border=border() if continuous else None
        border_checks=0
        action()
        for _ in range(limit):
            if continuous and (state()==0 or u8('loadingActive') or state()==6):
                assert border()==old_border,(label,'persistent radio border changed')
                border_checks+=1
            if label.startswith('prep-to-play-') and u8('loadingActive') and u8('loadingDigit') in (1,2,3) and (u32('vtimer')-u32('loadingStart'))%fps>=fps//3:
                name='countdown-'+str(u8('loadingDigit'))
                if not (out/(name+'.png')).exists():shot(name)
            if predicate() and not u8('transitioning'):break
            run()
        else:raise AssertionError(('timeout',label,state(),u8('currentLevel'),u8('transitioning')))
        run(3)
        if recordClip:record=False;audio.close();audio=None
        trace=framesLog[start:]
        unchanged=[i>0 and f['musicClock']==trace[i-1]['musicClock'] for i,f in enumerate(trace)]
        frozen=[unchanged[i] and f['psgCache']==trace[i-1]['psgCache'] for i,f in enumerate(trace)]
        x={'name':label,'frames':len(trace),'blackFrames':sum(f['black'] for f in trace),
            'longestBlack':longest(f['black'] for f in trace),
            'longestMusicStall':longest(unchanged),'longestFrozenPSGCache':longest(frozen),
            'displayOffFrames':sum(not f['display'] for f in trace),'loadingFrames':sum(bool(f['loading']) for f in trace),'visibleLoadingFrames':sum(bool(f['loading']) and not f['black'] for f in trace),'digits':{str(n):sum(f['loading'] and f['digit']==n for f in trace) for n in (3,2,1)},
            'persistentBorderFramesChecked':border_checks,
            'functionsWhileAudioStalled':Counter(f['function'] for i,f in enumerate(trace) if unchanged[i]).most_common(8)}
        measurements.append(x);print(json.dumps(x),flush=True)
        (out/'measurements.json').write_text(json.dumps({'romSHA256':hashlib.sha256(original).hexdigest(),'region':'PAL' if args.pal else 'NTSC','measurements':measurements},indent=2))
        if label.startswith('prep-to-play-'):
            assert x['visibleLoadingFrames']>=fps*3,(label,'loading too short',x)
            assert u16('freezeTimer')==0,(label,'second countdown inside gameplay')
            assert x['frames']<fps*4,(label,'double wait before gameplay')
            assert all(x['digits'][str(n)]>=fps-3 for n in (3,2,1)),(label,'missing countdown digit')
            assert int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')>0,(label,'gameplay did not begin immediately')
            tail=[f for f in trace if f['loading']][-fps:]
            assert all(f['phaseFrames']==0 and f['freeze']==0 for f in tail),(label,'simulation advanced during loading')
            assert state()==1,(label,'held START leaked into pause')
        if continuous:
            assert x['blackFrames']==0 and x['displayOffFrames']==0,(label,'radio transition blanked the display',x)
        assert x['longestMusicStall']<=3,(label,'audio starved',x)
        assert x['longestBlack']<=(8 if label.startswith('prep-to-play-') else fps//2),(label,'long black gap',x)
    def fresh(key):
        buttons.clear();run(3);press(key)
    def start_stage():
        buttons.clear();run(3);buttons.update({1,3});run(2)
    def ready():return not u8('transitioning')
    def at(st):return lambda:state()==st
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story',fps*20);run(fps)
        measure('arrival-radio-to-prep-1',lambda:fresh(3),at(0));prep('prep1')
        capture=True
        route=[]
        for step in range(1,17):
            buttons.clear();run(fps)
            node=u8('pendingLevel');route.append(node)
            systemTiles=bytes(vram[2*32:16*32])
            measure('prep-to-play-'+names[node],start_stage,at(1))
            assert bytes(vram[2*32:16*32])==systemTiles,'loading changed resident system tiles'
            # Isolate transition coverage now that gameplay starts immediately.
            # Shield also blocks terrain damage, unlike the enemy-hit timer.
            w16('hp',100);w16('shieldTimer',60000);w16('invTimer',60000);w16('spawnTimer',60000)
            write(syms['phaseStats'][0]+2,struct.pack('>H',0))
            buttons.clear();run(fps*4)
            assert state()==1,('not playing',node,state())
            w16('invTimer',60000);w16('spawnTimer',60000)
            if node==20:
                write(syms['bossDefeated'][0],b'\1')
                measure('boss-to-radio',lambda:None,at(6))
                run(fps)
                measure('final-radio-to-victory',lambda:fresh(3),lambda:state()==7 and u8('resultActive'))
                break
            if args.branch_b:
                if node==1:write(syms['phaseStats'][0],struct.pack('>H',1))
                if node==6:w16('npcHp',0)
                if node==11:write(syms['phaseStats'][0]+2,struct.pack('>H',1))
                if node==15:write(syms['phaseStats'][0]+4,struct.pack('>I',fps*61))
            if node==8:
                w16('dinorahInvTimer',60000);write(syms['dinorahNode'][0],bytes([39]));w16('dinorahFireTimer',60000);run(fps)
                pos(1992,168);w16('dinorahX',1992);w16('dinorahY',168)
                write(syms['dinorahFx'][0],struct.pack('>i',1992*64));write(syms['dinorahFy'][0],struct.pack('>i',168*64))
                w16('dinorahAimTimer',0);w16('dinorahPauseTimer',0);w16('dinorahFireTimer',60000);w16('dinorahInvTimer',60000)
                write(syms['dinorahState'][0],bytes([4]));write(syms['dinorahNode'][0],bytes([39]))
                w16('arrivalTimer',fps)
            elif node==5:
                pos(1992,168);w16('arrivalTimer',fps)
            else:
                w16('kills',100);w16('surviveLeft',1);w16('collected',100)
            measure('play-to-result-'+names[node],lambda:None,lambda:(state()==4 and u8('resultActive')) or state()==6)
            if state()==4:
                run(fps)
                measure('result-to-next-'+names[node],lambda:fresh(1),lambda:state() in (5,6))
            if state()==6:
                run(fps)
                measure('after-radio-to-map-'+names[node],lambda:fresh(3),at(5))
            run(fps)
            measure('map-to-arrival-'+names[node],lambda:fresh(1),lambda:state() in (0,6))
            if state()==6:
                run(fps)
                measure('arrival-radio-to-prep-'+names[node],lambda:fresh(3),at(0))
        print('ROUTE',route,flush=True)
        assert u8('workDepth')==0,'unbalanced loading owner'
        assert not u8('loadingActive')
        (out/'failure-trace.json').unlink(missing_ok=True)
        (out/'report.json').write_text(json.dumps({'passed':True,'romSHA256':hashlib.sha256(original).hexdigest(),'region':'PAL' if args.pal else 'NTSC','route':route,'transitions':measurements,'radioOverlayFramesPixelDataChecked':overlay_checked,'objectiveSetup':'RAM accelerates objectives/positions and branch statistics; loading, audio, routing and countdown use production code.'},indent=2)+'\n')
    finally:
        if not (out/'report.json').exists():(out/'failure-trace.json').write_text(json.dumps(framesLog))
        core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
