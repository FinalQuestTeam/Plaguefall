"""Native radio portraits/text, frame-by-frame line changes and combat entry.

RAM accelerates scenario setup; dialogue navigation, rendering and countdowns
use the normal production state machine in NTSC/PAL.
"""
from pathlib import Path
import os,re,textwrap,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import encode, decode
GAME=Path(__file__).resolve().parents[1]
TILE_DEFS=Path(os.environ.get('PLAGUEFALL_TILE_DEFS',str(GAME/'src/system/video/sprites/tiles.h'))).read_text()
def tile_constant(name):return int(re.search(r'^#define\s+'+name+r'\s+(\d+)',TILE_DEFS,re.M).group(1))
OBJECT_END=16+tile_constant('NUM_TILES')
ICON_BASE=OBJECT_END+tile_constant('ENEMY_CACHE_TILES')
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/radio-dialogos-ux-v1/integracao/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    fmt=0;raw=None;w=h=pitch=0;buttons=set();record=False;encoder=None;audio=None;watch=None
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
        if watch:watch()
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
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),'setup':'RAM selects source phases, accelerates death/completion/boss only for scene entry. Radio navigation and every countdown run with normal production code/controller input, without RAM writes.','dialogues':[],'countdowns':[],'failures':[]}
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    source=re.sub(r'//[^\n]*','',(GAME/'src/levels/story.c').read_text())
    scenes={name:re.findall(r'(ESQUERDA|DIREITA)\((P_\w+),\s*"([^"]*)"',body) for name,body in re.findall(r'^CENA\((\w+)\)(.*?)^FIM',source,re.M|re.S)}
    registry={(names.index(node),when):scenes[name] for node,when,name in re.findall(r'QUANDO\(N_(\w+),\s*(ANTES|DEPOIS),\s*(\w+)\)',source) if node in names}
    art=re.findall(r'"([0-9a-f]{48})"',(GAME/'src/system/video/sprites/portraits_data.h').read_text());assert len(art)==4*48
    palette_source=(GAME/'src/system/video/sprites/portraits_data.h').read_text().split('PORTRAIT_PAL')[1].split('};')[0]
    portrait_colors=[int(c,16) for c in re.findall(r'0x[0-9a-fA-F]+',palette_source)]
    console_colors=list(struct.unpack('>16H',(GAME/'res/radio/palette.bin').read_bytes()))
    console_colors[13]=0xccc;console_colors[15]=0x4ce
    ids={'P_DAMIAO':0,'P_COMANDO':1,'P_ESCORPIAO':2,'P_DINORAH':3}
    font=bytes(int(x) for x in re.findall(r'\d+',(GAME/'src/system/video/screens/result_font.h').read_text().split('= {')[1]))
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def rawv(address,size):return bytes(vram[(address+i)^1] for i in range(size))
    def pixel(x,y):
        attr=vw(0xe000+((y//8)*64+x//8)*2);tile=attr&2047
        value=vram[(tile*32+(y%8)*4+(x%8)//2)^1]
        return (value>>4) if x%2==0 else value&15
    def glyphs(words,x,y):
        for i,ch in enumerate(words):
            for gy in range(8):
                mask=font[(encode(ch)[0]-32)*8+gy]
                for gx in range(8):
                    if mask&(128>>gx):assert pixel(x+i*8+gx,y+gy)==13,('glyph pixel',words,i,gx,gy)
    def portraits(remote,left):
        for who,x,y,pal,speaking in [(0,2,18,1,left),(remote,22,18,2,not left)]:
            for i,c in enumerate(portrait_colors[who*16:who*16+16]):
                expected=c if speaking else sum(((((c>>shift)&7)+1)//3)<<shift for shift in (1,5,9))
                # Genesis Plus GX stores CRAM as packed 9-bit RGB internally.
                packed=(expected>>1&7)|((expected>>5&7)<<3)|((expected>>9&7)<<6)
                assert cram[pal*16+i]==packed,('speaker palette',who,speaking,i,hex(cram[pal*16+i]),hex(packed))
            for tr in range(6):
                for tc in range(6):
                    attr=vw(0xe000+((y+tr)*64+x+tc)*2)
                    assert ((attr>>13)&3)==pal and not attr&0x1800,('portrait anchor/flip',who,tc,tr,hex(attr))
                    expect=bytes(int(art[who*48+tr*8+py][tc*8+px:tc*8+px+2],16) for py in range(8) for px in range(0,8,2))
                    assert rawv((attr&2047)*32,32)==expect,('portrait source pixels',who,tr,tc)
    def frozen():
        return {n:read(*syms[n]) for n in ('currentLevel','px','py','phaseStats','hp','bombs','shotPower','speedPct','enemies','pshots','eshots','items','npcHp','surviveLeft','visited')}
    def radio_scene(node,when):
        nonlocal watch
        until(lambda:state()==6 and u8('radioActive')==1 and not u8('transitioning'),'radio-ready');run(2)
        before=frozen();expected=registry[(node,when)];remote=next((ids[p] for side,p,t in expected if side=='DIREITA'),1)
        for i,(side,who,words) in enumerate(expected):
            lines=textwrap.wrap(words,width=26,break_long_words=False,break_on_hyphens=False)
            until(lambda:u8('lineIdx')==i and u16('typeTotal')==sum(map(len,lines)) and decode(read(syms['wrapBuf'][0],27).split(b'\0')[0])==lines[0],'line-ready');run(2)
            if side=='DIREITA':remote=ids[who]
            if node==1 and i==0:shot('radio-digitando')
            # Complete via A, then inspect every native glyph and portrait tile.
            if u16('typed')<u16('typeTotal'):press(1)
            until(lambda:u16('typed')==u16('typeTotal'),'complete-text');run(fps//3)
            lines=textwrap.wrap(words,width=26,break_long_words=False,break_on_hyphens=False)
            assert u8('wrapLines')==len(lines)<=4,(node,when,i,u8('lineIdx'),u8('wrapLines'),u16('typed'),u16('typeTotal'),lines)
            got=[decode(read(syms['wrapBuf'][0]+r*27,27).split(b'\0')[0]) for r in range(len(lines))]
            assert got==lines,(node,when,got,lines)
            for r,line in enumerate(lines):glyphs(line,24,56+r*16)
            portraits(remote,side=='ESQUERDA');assert u16('used')<=400
            assert list(cram[:16])==[(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6) for c in console_colors],'console palette changed'
            assert not any(rawv(0xc000,4096)),'stage remains behind console'
            for y in range(56,120):
                for x in range(24,232):
                    assert pixel(x,y) in (1,13),('non-black dialogue background',x,y,pixel(x,y))
            report['maxDynamicTiles']=max(report.get('maxDynamicTiles',0),u16('used'))
            if node==1:shot('radio-padre' if i==0 else 'radio-damiao')
            if node==8:shot('radio-6B-'+str(i+1))
            if node==20:shot(('radio-final-' if when=='DEPOIS' else 'radio-chefe-')+str(i+1))
            assert frozen()==before,('radio simulation changed',node,when,i)
            report['dialogues'].append({'phase':names[node],'when':when,'line':i+1,'portrait':who,'side':side,'wrapAndGlyphsExact':True,'portraitPixelsAndAnchorsExact':True,'listenerDimmedSpeakerOriginal':True,'blackMonitorGoldTitlesGrayBody':True,'noStageBackdrop':True,'simulationFrozen':True})
            if i+1<len(expected):
                # Inspect every rendered frame, including frames spent inside
                # RADIO_line, rather than only its completed screenshot.
                baseline=raw;frames=0;bad=[]
                mutable=[(24,40,272,8),(24,56,208,64),(16,144,48,48),(176,144,48,48),
                         (72,144,72,8),(72,160,72,8),(72,184,24,8),
                         (232,144,72,8),(232,160,72,8),(232,184,24,8),(16,208,176,8)]
                bpp=4 if fmt==1 else 2;spans=[]
                for y in range(h):
                    start=None
                    for x in range(w+1):
                        stable=x<w and not any(rx<=x<rx+rw and ry<=y<ry+rh for rx,ry,rw,rh in mutable)
                        if stable and start is None:start=x
                        if not stable and start is not None:
                            spans.append((y*pitch+start*bpp,y*pitch+x*bpp));start=None
                chrome=rawv((OBJECT_END)*32,int(re.search(r'RADIO_TILE_COUNT (\d+)',(GAME/'src/system/video/screens/radio_layout.h').read_text()).group(1))*32)
                def inspect():
                    nonlocal frames
                    frames+=1
                    if any(raw[a:b]!=baseline[a:b] for a,b in spans):
                        if not bad:shot('FAIL-line-background')
                        bad.append(frames)
                watch=inspect
                press(1);run(fps//3)
                watch=None
                assert rawv(OBJECT_END*32,len(chrome))==chrome,'console tiles were reloaded or corrupted'
                check={'phase':names[node],'when':when,'fromLine':i+1,'frames':frames,'unexpectedBackgroundFrames':bad,'passed':not bad}
                report.setdefault('lineTransitions',[]).append(check);save()
                assert not bad,('line transition changed static background',node,when,i+1,bad)
            else:
                press(1);run(fps//3)
        until(lambda:state()!=6,'scene-end');assert u8('radioActive')==0
    def prep():
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2)
    try:
        run(120);press(3);run(fps*4);press(1);radio_scene(1,'ANTES');prep();baseline=snapshot()
        def enter(node):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1);until(lambda:state()==1,'play');run(fps*4)
        for node in range(2,21):
            enter(node);write(syms['flow_state'][0],struct.pack('>I',3));press(3)
            radio_scene(node,'ANTES');prep();save();print('PASS radio',names[node],flush=True)
        for node in (19,20):
            enter(node)
            if node==20:write(syms['bossDefeated'][0],b'\1')
            else:
                w16('kills',65535)
                until(lambda:state()==4 and u8('resultActive')==1,'completion')
                run(fps);press(1)
            radio_scene(node,'DEPOIS');save()
        assert len(report['dialogues'])==51
        # Test START without completing a partial line; the new UI must release
        # its heap/VRAM loan and return to the ordinary mission screen.
        enter(4);write(syms['flow_state'][0],struct.pack('>I',3));press(3)
        until(lambda:state()==6 and u8('radioActive')==1 and not u8('transitioning'),'skip-entry');run(3);press(3);prep()
        report['startSkipsPartialScene']=True
        for node in range(1,21):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            native_hud='countdownActive' in syms
            def countdown_active():return u8('countdownActive') if native_hud else u32('savedCountdown')!=0
            until(lambda:state()==1 and countdown_active() and not u8('transitioning'),'count-ready')
            original_icons=rawv(ICON_BASE*32,120*32) if native_hud else read(u32('savedCountdown'),180*32)
            initial=(u16('px'),u16('py'));initial_stats=read(*syms['phaseStats'])
            transitions=[];last=4;frames=0
            while u16('freezeTimer')>0:
                digit=u8('countdownDigit')
                if digit!=last:transitions.append((digit,frames));last=digit
                if node in (1,4,20) and digit and frames==transitions[-1][1]+3:shot('contagem-'+names[node]+'-'+str(digit))
                assert (u16('px'),u16('py'))==initial and read(*syms['phaseStats'])==initial_stats,'countdown advanced simulation'
                if u16('freezeTimer')<=5:buttons.update({7,1})
                run();frames+=1
                assert frames<=fps*3+3
            transitions.append((0,frames));buttons.clear();run(2)
            assert [d for d,t in transitions]==[3,2,1,0],transitions
            gaps=[transitions[i+1][1]-transitions[i][1] for i in range(3)]
            assert all(abs(g-fps)<=2 for g in gaps),(node,transitions,gaps)
            assert u16('px')>initial[0] and int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')>=1,'zero did not release control'
            assert u16('goTimer')>0 and u8('countdownDigit')==0
            assert u16('shotCooldown')>0,'fire was not released at zero'
            if node in (1,4,20):shot('contagem-vai-'+names[node])
            until(lambda:not countdown_active(),'go-remove',fps)
            if native_hud:
                for _ in range(fps//2):
                    if rawv(ICON_BASE*32,120*32)==read(*syms['hudPixels']):break
                    run()
                assert rawv(ICON_BASE*32,120*32)==read(*syms['hudPixels']),('countdown changed HUD',node)
            else:assert rawv(ICON_BASE*32,180*32)==original_icons,('countdown icon restoration',node)
            # Pause/help depends on the borrowed icon art and palettes being back.
            press(3);until(lambda:state()==2,'pause-after-go');run(2);assert 'PAUSADO' in textrow(2)
            press(0);until(lambda:state()==1,'resume-after-go')
            report['countdowns'].append({'phase':names[node],'transitions':transitions,'gapsFrames':gaps,'freezeSeconds':3,'movesAtZero':True,'firesAtZero':True,'goTagThenRestore':True,'pauseAfterGo':True})
            print('PASS countdown',names[node],flush=True);save()
        # A held continuously from the mission confirmation stays disarmed;
        # a release during/after the countdown permits the next fire press.
        restore(baseline);buttons.add(1)
        until(lambda:state()==1 and countdown_active(),'held-menu-fire')
        until(lambda:u16('freezeTimer')==0,'held-menu-zero',fps*4);run(2)
        assert u16('shotCooldown')==0,'menu A leaked into combat'
        buttons.clear();run(2);press(1);run(2)
        assert u16('shotCooldown')>0,'released A did not rearm'
        report['heldMenuFireDoesNotLeak']=True
        report['passed']=True;save()
    except Exception as exc:
        report['failures'].append(repr(exc));shot('FAIL');save();raise
    finally:core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':True,'region':report['region'],'dialogues':len(report['dialogues']),'countdowns':len(report['countdowns'])}),flush=True)
if __name__=='__main__':main()
