"""Production result cards, controller navigation and campaign transitions.

RAM accelerates scenario setup; result rendering, navigation, retry, branch
resolution and replay use the normal production state machine in NTSC/PAL.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import encode, decode
GAME=Path(__file__).resolve().parents[1]
import re
CAMPAIGN_NODE_COUNT=len(re.findall(r'\bN_[A-Za-z0-9]+\b',re.search(r'typedef enum\s*\{(.*?)NODE_MAX',(GAME/'src/levels/graph.h').read_text(),re.S)[1]))

CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--build-dir',type=Path);parser.add_argument('--audio-only',action='store_true');args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/resultados-ux-v1/integracao/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
        shot('FAIL-'+label);raise AssertionError(('timeout',label,state(),u8('currentLevel'),u8('pendingLevel'),{'hp':u16('hp'),'freezeTimer':u16('freezeTimer'),'kills':u16('kills'),'settleKind':u8('settleKind'),'settleTimer':u16('settleTimer')}))
    def textrow(row):
        return ''.join(decode(chr((vw(0xe000+(row*64+x)*2)&0x7ff)-1440+32))
            if 1440<=(vw(0xe000+(row*64+x)*2)&0x7ff)<1536 else '.' for x in range(40))
    report={'passed':False,'romSHA256':hashlib.sha256(original).hexdigest(),'region':'PAL' if args.pal else 'NTSC','setup':'RAM selects phases, seeds resources, stabilises shimmer before capture, injects lethal projectile and accelerates counters/boss. Actual result entry, drawing, menu navigation, resets and route transitions run through production code. No ROM patch.', 'defeatPhases':[], 'failures':[]}
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    def save(): (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def start_frames():
        nonlocal trackFrames
        frameLog.clear();trackFrames=True
    def finish_frames(label,no_black=False):
        nonlocal trackFrames
        trackFrames=False
        dark_runs=sum(black and (i==0 or not frameLog[i-1]) for i,black in enumerate(frameLog))
        assert dark_runs<=(0 if no_black else 1),(label,'black flashes',dark_runs)
        report.setdefault('transitions',[]).append({'name':label,'frames':len(frameLog),
            'blackIntervals':dark_runs,'blackFrames':sum(frameLog)})
    def prep(label):
        until(lambda:state() in (0,6),label+'-entry')
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),label)
        until(lambda:not u8('transitioning'),label+'-ready');run(2)
    def ui(key):
        press(key);run(fps//3)
    def background():
        result=[]
        for i in range(2048):
            a=vw(0xc000+i*2)
            if not u8('arenaActive') and i>=64:
                decal=vw(0xe000+i*2)
                if decal&2047 in (18,19,20):a=decal
            tile=a&2047
            result.append((a&0xf800,bytes(vram[((tile*32+j)&65535)^1] for j in range(32))))
        return result
    def stable():
        return {name:read(*syms[name]) for name in ('px','py','hp','kills','phaseStats','enemies','pshots','eshots','spawnTimer','surviveLeft','npcHp','items','bombs','shotPower','speedPct')}
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3);prep('prep1')
        baseline=snapshot()
        def enter(node):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1,'play');run(fps*4)
        def lethal():
            w16('hp',1);w16('invTimer',0);w16('shieldTimer',0)
            write(syms['eshots'][0],struct.pack('>iiiiBBBB',(u16('px')+4)<<6,(u16('py')+4)<<6,0,0,0,10,1,0))
        def result_ready(expected):
            until(lambda:state()==expected and u8('resultActive')==1,'result',limit=fps*90)
            run(2)
            expected_cue=2 if expected==3 else 1 if expected==7 or (expected==4 and u8('resultKind')==1) else 0
            assert u8('resultCueKind')==expected_cue, ('wrong result cue',expected,u8('resultKind'),u8('resultCueKind'))
            assert u16('cardBase')+32*u16('cardHeight')<=1440
            report['maxBackgroundTiles']=max(report.get('maxBackgroundTiles',0),u16('cardBase')-16)
            report['lastTileObserved']=max(report.get('lastTileObserved',0),u16('cardBase')+32*u16('cardHeight')-1)
        if args.audio_only:
            report['setup']='RAM selects campaign phases and accelerates objective counters/boss. Production defeat, successful/failed objective results, final victory playback and controller dismissal are exercised. Equipment retry rules are covered by the full result suite. No ROM patch.'
            report['audioScenarios']=[]
            def cue_result(label,expected,kind):
                nonlocal audio,record
                audio=wave.open(str(out/(label+'.wav')),'wb')
                audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate));record=True
                result_ready(expected);run(5*fps)
                record=False;audio.close();audio=None
                assert u8('resultCueKind')==kind
                if kind:
                    from array import array
                    with wave.open(str(out/(label+'.wav')),'rb') as captured:
                        samples=array('h',captured.readframes(captured.getnframes()))
                    assert any(samples) and max(abs(v) for v in samples)<32767
                    assert max(abs(v) for v in samples[-round(av.timing.sample_rate)//2*2:])<10, 'background resumed after cue'
                    assert u16('resultCueElapsed')==(2400 if kind==2 else 1200)
                shot(label)
                report['audioScenarios'].append({'name':label,'cue':'game-over' if kind==2 else 'victory' if kind==1 else 'campaign','singlePlayThenSilence':bool(kind)})
            for node in (1,20):
                enter(node);lethal();cue_result('defeat-'+str(node),3,2)
                press(3);prep('defeat-retry-'+str(node))
                assert not u8('resultCueKind')
            enter(1);lethal();result_ready(3);run(fps//2);press(3)
            prep('early-defeat-retry');assert not u8('resultCueKind')
            enter(1);w16('kills',10);cue_result('stage-complete',4,1)
            press(1);until(lambda:state() in (5,6) and not u8('transitioning'),'complete-dismissed')
            assert not u8('resultCueKind')
            # A fresh confirmation may end the phrase before its natural tail.
            enter(1);w16('kills',10);result_ready(4);run(fps//2);press(1)
            until(lambda:state() in (5,6) and not u8('transitioning'),'early-dismissed')
            assert not u8('resultCueKind')
            for failed in (False,True):
                enter(6)
                if failed:w16('npcHp',0)
                else:w16('surviveLeft',1)
                cue_result('signal-lost-unchanged' if failed else 'signal-protected',4,0 if failed else 1)
            enter(20);write(syms['bossDefeated'][0],b'\1')
            until(lambda:state()==6,'final-story');run(fps);press(3)
            cue_result('campaign-victory',7,1)
            press(3);run(2*fps);assert not u8('resultCueKind')
            assert 'NOVO JOGO' in textrow(12)
            report['earlyConfirmationStopsCue']=True
            report['closingResultRestoresMusic']=True
            report['passed']=True;save()
            print(json.dumps({'passed':True,'region':report['region'],'audioScenarios':6}),flush=True)
            return
        def equipment():
            write(syms['shotPower'][0],b'\5');write(syms['speedPct'][0],b'\x64')
            write(syms['shotMode'][0],b'\2');write(syms['modeCharges'][0],b'\3');w16('bombs',2)
            write(syms['item'][0],bytes([4,1,5,5,6,3]))
        def bag_items():
            address,size=syms['items'];assert size==64
            result=[]
            for i in range(8):
                x,y,ttl,kind,active=struct.unpack('>hhHBB',read(address+i*8,8))
                if active and kind==8:result.append((x,y,ttl))
            return result
        for node in range(1,CAMPAIGN_NODE_COUNT+1):
            enter(node);equipment()
            # Ensure the lethal hit also wins over a fulfilled kill target.
            # Start between shimmer uploads so the final gameplay frame cannot
            # legitimately change the scenery being compared with the card.
            w16('glowClock',0);write(syms['glowUploading'][0],b'\0');run(2)
            if node==1:w16('kills',10)
            lethal();before=background();result_ready(3)
            after=background()
            changes=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
            assert not changes,('scenery patterns changed',node,changes[:12],[(before[i][0],after[i][0],before[i][1].hex(),after[i][1].hex()) for i in changes[:2]])
            assert u16('cardTop')==2 and u16('cardHeight')==23
            frozen=stable();run(fps);assert stable()==frozen,('result simulation advanced',node)
            shot('derrota-'+names[node])
            if node==4:
                ui(5);shot('derrota-sair');ui(1);assert u8('exitView')==1 and u8('exitChoice')==0,(state(),u8('exitView'),u8('exitChoice'),u8('choice'),u16('age'),u8('armed'))
                shot('confirmar-saida');ui(1);assert u8('exitView')==0 and state()==3
                ui(1);ui(3);assert u8('exitView')==0 and state()==3
                ui(1);ui(0);assert u8('exitView')==0 and state()==3
                ui(0);assert u8('choice')==0
            press(3);prep('retry-'+names[node]);assert u8('pendingLevel')==node
            expected=(1,0,bytes([255,0]*3),0)
            assert u16('hp')==100 and (u8('shotPower'),u8('speedPct'),read(syms['item'][0],6),u16('bombs'))==expected,(node,expected)
            assert u8('resultActive')==0
            press(1);until(lambda:state()==1,'retry-play');run(fps*4)
            # Isolate the pickup/pause probe from real combat after retry.
            # In escort arenas the old fall can be inside a new enemy wave.
            for name in ('enemies','pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
            w16('spawnTimer',60000)
            assert len(bag_items())==1,(node,bag_items())
            if bag_items():
                assert bag_items()[0][2]==65535
                shot('bolsa-fase-'+names[node])
                # The exact authored 16x16 pixels must be resident in real VRAM.
                art=json.loads((GAME/'art/bolsa-recuperacao-v1/bag-pixels.json').read_text())
                for y,row in enumerate(art['rows']):
                    for x,char in enumerate(row):
                        address=((16+89+(x//8)*2+y//8)*32)+(y%8)*4+(x%8)//2
                        value=vram[address^1]>>(0 if x&1 else 4)&15
                        assert value==art['palette_indices'].get(char,0),('bag tile',x,y,value,char)
            x,y,_=bag_items()[0];pos(x,y);run(2)
            recovered=(5,100,bytes([4,1,5,5,6,3]),2) if node<=6 else ((4,80,bytes([4,1,5,5,255,0]),2) if node<=14 else (2,20,bytes([255,0]*3),0))
            actual=(u8('shotPower'),u8('speedPct'),read(syms['item'][0],6),u16('bombs'))
            assert not bag_items() and actual==recovered,(node,actual,recovered)
            buttons.add(3);until(lambda:state()==2,'retry-pause');buttons.clear();run(2)
            assert 'PAUSADO' in textrow(2),('pause after retry',node)
            press(0);until(lambda:state()==1,'retry-resume');run(2)
            report['defeatPhases'].append({'id':names[node],'backgroundUnchanged':True,'simulationFrozen':True,'retrySamePhase':True,'deathPolicyApplied':True,'singlePersistentBag':True,'preDeathEquipmentRecovered':True,'pauseAfterRetry':True})
            print('PASS defeat/retry',names[node],flush=True);save()
        # Early retries preserve actual collected equipment, not default values.
        enter(4);write(syms['shotPower'][0],b'\5');write(syms['speedPct'][0],b'\x64')
        write(syms['shotMode'][0],b'\2');write(syms['modeCharges'][0],b'\3');w16('bombs',2)
        if syms['item'][1]==6:write(syms['item'][0],bytes([4,1,5,3,6,2]))
        lethal();result_ready(3)
        # Held A is not a confirmation and must not dismiss the new screen.
        hold({1},fps);assert state()==3
        press(1);prep('resource-retry')
        assert u8('shotPower')==1 and u8('speedPct')==0 and u16('bombs')==0
        press(1);until(lambda:state()==1,'early-bag-play');run(fps*4)
        x,y,_=bag_items()[0];pos(x,y);run(2)
        assert u8('shotPower')==5 and u8('speedPct')==100 and u8('shotMode')==2 and u8('modeCharges')==3
        assert u16('bombs')==2 and read(syms['item'][0],6)==bytes([4,1,5,3,6,2])
        report['earlyEquipmentPreserved']=True;report['heldFireDoesNotConfirm']=True
        # A late retry creates one real collectible; walking over it applies
        # its effect exactly once, and the next death replaces the old bag.
        enter(15);equipment();lethal();result_ready(3);run(fps);press(3);prep('bag-retry')
        press(1);until(lambda:state()==1,'bag-play');run(fps*4)
        assert len(bag_items())==1
        x,y,_=bag_items()[0];pos(x,y);run(2)
        assert not bag_items() and u8('shotPower')==2 and u8('speedPct')==20
        run(2);assert u8('shotPower')==2 and u8('speedPct')==20
        shot('bolsa-recolhida');report['bagPickupOnce']=True
        lethal();result_ready(3);run(fps);press(3);prep('bag-second-retry')
        press(1);until(lambda:state()==1,'bag-second-play');run(fps*4)
        assert len(bag_items())==1 and u8('shotPower')==1 and u8('speedPct')==0
        report['bagReplacedOnNextDeath']=True
        # Exit: default safe, then explicit selection is the only title exit.
        enter(4);lethal();result_ready(3);run(fps);ui(5);ui(1);ui(5);shot('confirmar-saida-escolhida');ui(1)
        run(fps*2);assert 'NOVO JOGO' in textrow(12),'result title exit'
        shot('titulo-apos-derrota');report['confirmedTitleExit']=True
        # Completion ignores a held firing button, then allows a fresh press.
        enter(1);start_frames()
        audio=wave.open(str(out/'victory-completion.wav'),'wb');audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate));record=True
        w16('kills',10);buttons.add(1);result_ready(4);run(fps//4)
        finish_frames('gameplay-to-completion',no_black=True)
        run(fps*5);assert state()==4
        record=False;audio.close();audio=None
        from array import array
        with wave.open(str(out/'victory-completion.wav'),'rb') as captured:
            captured_samples=array('h',captured.readframes(captured.getnframes()))
        assert any(captured_samples) and max(abs(v) for v in captured_samples)<32767
        assert max(abs(v) for v in captured_samples[-round(av.timing.sample_rate)*2:])<10, 'background resumed after victory cue'
        assert u16('resultCueElapsed')==1200
        report['victoryAudio']={'captured':'victory-completion.wav','singlePlayThenSilence':True,'scoreTicks':1200,'clockHz':600,'onlySuccessfulResults':True}
        buttons.clear();run(fps*5);assert state()==4,'completion must wait for a fresh confirmation'
        shot('fase-concluida');buttons.clear();run(2);start_frames();press(1)
        until(lambda:state() in (5,6) and not u8('transitioning'),'completion-next')
        assert not u8('resultCueKind'), 'victory cue survived closing result'
        run(2);finish_frames('completion-to-map-or-radio');report['completionConfirmation']=True
        if state()==6:run(fps);press(3);until(lambda:state()==5 and not u8('transitioning'),'completion-map')
        frozen=stable();run(fps*5);assert state()==5 and stable()==frozen,'map must wait for input'
        start_frames();buttons.add(1)
        until(lambda:state()!=5 and not u8('transitioning'),'map-confirmation')
        run(fps);assert state()==6,'held map confirmation must not skip the arrival dialogue'
        buttons.clear();run(2);finish_frames('map-to-arrival-radio')
        start_frames();press(3);buttons.add(1);prep('arrival-prep');finish_frames('radio-to-mission')
        run(fps);assert state()==0,'a press during transition must not start the mission'
        buttons.clear();run(2)
        report['mapWaitsForInput']=True
        # Successful and failed protection retain their original graph paths.
        for failed in (False,True):
            enter(6)
            if failed:w16('npcHp',0)
            else:w16('surviveLeft',1)
            result_ready(4);run(fps//2);shot('sinal-perdido' if failed else 'sinal-protegido')
            assert u8('resultKind')==(2 if failed else 1)
            run(fps*5);assert state()==4,'protection result must wait for confirmation'
            press(1);until(lambda:state() in (5,6),'protect-confirm')
            if state()==6:run(fps);press(3);until(lambda:state()==5,'protect-map')
            assert u8('pendingLevel')==(8 if failed else 7)
            shot('mapa-sinal-perdido' if failed else 'mapa-sinal-protegido')
        report['protectionRoutes']=['6A','6B'];report['waitsForConfirmation']=True
        # Final screen follows the final dialogue, and waits indefinitely.
        enter(20);write(syms['bossDefeated'][0],b'\1');until(lambda:state()==6,'final-story');run(fps);press(3)
        result_ready(7);run(fps);shot('vitoria-final');ending=snapshot()
        frozen=stable();run(fps*5);assert state()==7 and stable()==frozen,'final must wait without simulation'
        press(0);assert state()==7,'B must not exit the final screen'
        ui(5);shot('vitoria-rejogar');ui(1);until(lambda:state()==6,'replay-story')
        assert u8('pendingLevel')==1 and u32('visited')==0,'replay must reset the campaign'
        assert u32('seen')==2,'replay must show the first story again'
        run(fps);press(3);prep('replay-prep');press(1)
        until(lambda:state()==1 and not u8('transitioning'),'replay-play')
        # Check the reset at entry: gameplay is live immediately after 3/2/1.
        # Four idle seconds can legitimately include enemy damage now.
        assert u8('currentLevel')==1 and u16('hp')==100 and u16('freezeTimer')==0
        run(fps*4);shot('nova-campanha')
        restore(ending);press(3);run(fps*2);assert 'NOVO JOGO' in textrow(12),'START must confirm title at default focus'
        shot('titulo-apos-vitoria')
        press(4);press(1);run(fps);press(5);press(5);press(5);press(1);until(lambda:state()==1 and u8('currentLevel')==0,'sandbox');run(fps*2)
        write(syms['item'][0],bytes([4,1,5,3,6,2]));lethal();result_ready(3);run(fps);shot('derrota-treino')
        press(3);until(lambda:state()==1 and u8('resultActive')==0,'sandbox-retry');run(fps)
        assert u16('hp')==100 and read(syms['item'][0],6)==bytes([255,0]*3)
        report['sandboxRetry']=True
        report['finalWaits']=True;report['replayFullReset']=True;report['finalStartTitle']=True
        report['passed']=True;save()
    except Exception as exc:
        report['failures'].append(repr(exc));shot('FAIL');save();raise
    finally:
        core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':report['passed'],'region':report['region'],'defeatPhases':len(report['defeatPhases'])}),flush=True)

if __name__=='__main__':main()
