"""Continuation passwords in the production ROM (NTSC/PAL).

Only changed menu rows may differ; headers, artwork and scenery must remain
identical on every intermediate frame. RAM is used only to set up defeat/final.
Run with arch -x86_64 /usr/bin/python3.
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
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);parser.add_argument('--fresh-code')
    parser.add_argument('--capture-symbols',action='store_true',help='Capture all16 symbols and three six-slot screens using controller input only')
    args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/sinal-ultimo-chao-v1/native/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    fmt=0;raw=None;w=h=pitch=0;buttons=set();watch=None
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
    def vw(address):return vram[address]+(vram[address+1]<<8)
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
    def w16(name,value):write(syms[name][0],struct.pack('>H',value&65535))
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

    def state():return u32('flow_state')
    def wait(predicate,label,limit=12*fps):
        for _ in range(limit):
            if predicate():return
            run()
        shot('FAIL-'+label)
        raise AssertionError((label,state(),u8('currentLevel'),u8('testStage')))
    def textrow(row):
        return ''.join(decode(chr((vw(0xe000+(row*64+x)*2)&0x7ff)-1440+32))
            if 1440<=(vw(0xe000+(row*64+x)*2)&0x7ff)<1536 else '.' for x in range(40))
    core.retro_serialize_size.restype=C.c_size_t
    core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_serialize.restype=C.c_bool
    core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool
    def snap():
        n=core.retro_serialize_size();buf=C.create_string_buffer(n);assert core.retro_serialize(buf,n);return buf
    def restore(buf):
        buttons.clear();assert core.retro_unserialize(buf,len(buf));run(2)
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),
            'method':'All password entry and resume navigation use controller input; RAM fixtures only accelerate victory, death and mid-attempt equipment for isolated checks.',
            'checks':[]}
    def check(name,detail=None):
        report['checks'].append({'name':name,'passed':True,'detail':detail})
        print('PASS',name,flush=True)
    def encode(node,flags,power,speed):
        payload=(1<<14)|(speed<<11)|((power-1)<<8)|(flags<<5)|node
        crc=0xa7
        for byte in payload.to_bytes(2,'big'):
            crc^=byte
            for _ in range(8):crc=((crc<<1)^7 if crc&128 else crc<<1)&255
        value=(payload<<8)|crc
        return [(value>>shift)&15 for shift in (20,16,12,8,4,0)]
    def open_input():
        press(5);press(5);press(1)
        wait(lambda:'SINTONIZAR' in textrow(2),'password-input');run(fps//2)
    def input_code(code):
        for i,target in enumerate(code):
            current=u8('selected');assert current==i,(current,i)
            value=read(syms['entered'][0]+i,1)[0]
            delta=(target-value)%16
            for _ in range(delta if delta<=8 else 16-delta):press(5 if delta<=8 else 4)
            if i<5:press(7)
        assert list(read(syms['entered'][0],6))==code
    def entry_signal(node):
        wait(lambda:state() in (6,8) and not u8('transitioning'),'entry-'+str(node),30*fps)
        if state()==6:run(fps//2);press(3)
        wait(lambda:state()==8 and 'SINAL DO ÚLTIMO CHÃO' in textrow(2) and not u8('transitioning'),'entry-code-'+str(node),30*fps)
        assert u8('pendingLevel')==node
    def play(node):
        press(1);wait(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),'mission-'+str(node))
        press(1);wait(lambda:state()==1 and not u8('transitioning'),'play-'+str(node),30*fps)
        assert u8('currentLevel')==node
    def valid_flags(node,flags):
        if node==1 and flags:return False
        if node<=6 and flags&6:return False
        if node<=14 and flags&4:return False
        if node==2 and flags&1 or node==3 and not flags&1:return False
        if node==7 and flags&2 or node==8 and not flags&2:return False
        if node==15 and flags&4 or node==16 and not flags&4:return False
        return True
    def history(node,flags):
        route=[1,3 if flags&1 else 2,4,5,6,8 if flags&2 else 7,9,10,11,12,13,14,16 if flags&4 else 15,17,18,19]
        return route[:route.index(node)]
    try:
        run(120);press(3);run(fps*4)
        assert 'SINTONIZAR' in textrow(16),textrow(16)
        if args.fresh_code:
            node,flags,power,speed=map(int,args.fresh_code.split(','))
            open_input();input_code(encode(node,flags,power,speed));press(1)
            assert u8('signalView')==2
            press(1);entry_signal(node);play(node)
            assert u8('shotPower')==power and u8('speedPct')==speed*20 and u8('campaignFlags')==flags
            assert u16('hp')==100 and u16('bombs')==2
            report['passed']=True;check('Fresh process resumes prior checkpoint using controller input only')
            return
        shot('00-menu');title=snap();open_input();shot('01-entrada')
        # Real tile bytes in VRAM, not just screenshot impressions, for all16 sprites.
        expected_icons=(GAME/'res/signal/icons.bin').read_bytes()
        for symbol in range(16):
            attr=vw(0xe000+(6*64+8)*2)
            assert (attr>>13)&3==1,'symbol palette'
            base=attr&0x7ff
            actual=bytes(vram[(base*32+i)^1] for i in range(512))
            assert actual==expected_icons[symbol*512:(symbol+1)*512],('sprite',symbol,base)
            if args.capture_symbols:shot('symbol-%02d'%symbol)
            if symbol==10:shot('01-coracao-do-logo')
            press(5)
        assert read(syms['entered'][0],1)==b'\0','symbol wrap'
        press(6);assert u8('selected')==5;press(7);assert u8('selected')==0
        check('16 native32x32 sprites: ROM bytes, VRAM pixels, palette1 and wrap')
        if args.capture_symbols:
            empty=snap()
            groups=((0,1,2,3,4,5),(6,7,8,9,10,11),(12,13,14,15,5,10))
            for index,group in enumerate(groups,1):
                restore(empty);input_code(list(group));run(fps//2)
                shot('sprites-no-jogo-%02d'%index)
            report['captures']=[{'file':'sprites-no-jogo-%02d.png'%index,'symbol_indices':group}
                                for index,group in enumerate(groups,1)]
            report['passed']=True
            check('All16 symbols captured in the actual code screen; controller input only')
            return
        press(1);assert u8('signalView')==1 and 'INVÁLIDO' in textrow(4)
        shot('02-codigo-invalido');press(0);wait(lambda:'NOVO JOGO' in textrow(12),'cancel')
        check('Invalid code rejected; B cancels to title')
        cases=[];paused_nodes=set()
        for node in range(1,20):
            for flags in range(8):
                if not valid_flags(node,flags):continue
                restore(title);open_input()
                power=1+(node+flags)%5;speed=(node+flags)%6
                code=encode(node,flags,power,speed);input_code(code)
                press(1);wait(lambda:u8('signalView')==2,'confirm')
                typed=read(syms['entered'][0],6)
                press(0);assert u8('signalView')==0 and read(syms['entered'][0],6)==typed
                press(1);assert u8('signalView')==2
                if node==19 and flags==7:shot('03-confirmacao')
                press(1);entry_signal(node)
                assert read(syms['checkpoint'][0],4)==bytes((node,flags,power,speed))
                if node==19 and flags==7:shot('04-sinal-da-fase')
                play(node)
                assert u8('campaignFlags')==flags
                assert u16('hp')==100 and u16('bombs')==2
                assert u8('shotPower')==power and u8('speedPct')==speed*20
                assert u8('shotMode')==0 and u8('modeCharges')==0
                path=history(node,flags)
                mask=sum(1<<n for n in path)
                assert u32('visited')==mask|(1<<node)
                assert int.from_bytes(read(syms['seen'][0]+4,4),'big')==mask
                departures=read(syms['departedTo'][0],20)
                for a,b in zip(path,path[1:]+[node]):assert departures[a]==b,(node,flags,a,b,departures[a])
                if node not in paused_nodes:
                    press(3);wait(lambda:state()==2,'pause-'+str(node))
                    frozen={name:read(syms[name][0],syms[name][1]) for name in ('phaseStats','hp','bombs','px','py','shotPower','speedPct')}
                    press(5);press(5);press(1)
                    assert 'SINAL DO ÚLTIMO CHÃO' in textrow(2),('missing pause code',node)
                    run(10);press(0)
                    for name,value in frozen.items():assert read(syms[name][0],syms[name][1])==value,(node,name)
                    press(0);wait(lambda:state()==1,'unpause-'+str(node))
                    paused_nodes.add(node)
                cases.append({'node':node,'flags':flags,'power':power,'speed':speed,'code':code})
        check('69 route/decision combinations restored through controller entry',cases)
        check('Pause code available in all19 campaign nodes with frozen gameplay',sorted(paused_nodes))
        # Start a fresh ordinary campaign, then mutate only a declared mid-phase fixture.
        restore(title);press(1);entry_signal(1);shot('05-novo-jogo-sinal');play(1)
        starting_checkpoint=read(syms['checkpoint'][0],4)
        allow_writes=True
        write(syms['shotPower'][0],b'\5');write(syms['speedPct'][0],bytes([80]));w16('hp',37);w16('bombs',1)
        allow_writes=False
        press(3);wait(lambda:state()==2,'pause');run(2)
        before={name:read(syms[name][0],syms[name][1]) for name in ('phaseStats','hp','bombs','px','py','shotPower','speedPct','surviveLeft')}
        press(5);press(5);press(1);run(2)
        assert 'SINAL DO ÚLTIMO CHÃO' in textrow(2);shot('06-sinal-na-pausa')
        assert read(syms['checkpoint'][0],4)==starting_checkpoint,'mid-attempt pickups changed checkpoint'
        run(fps*2);press(0);run(2)
        for name,value in before.items():assert read(syms[name][0],syms[name][1])==value,('pause changed',name)
        press(0);wait(lambda:state()==1,'resume-pause')
        check('Pause code preserves gameplay, timers and original entry equipment')
        allow_writes=True;w16('surviveLeft',1);allow_writes=False
        wait(lambda:state()==4 and u8('resultActive'),'victory');run(fps);press(1)
        wait(lambda:state() in (5,6),'after-victory')
        if state()==6:press(3);wait(lambda:state()==5,'map')
        run(fps);press(1);run(fps*2)
        if state()==5:press(1)
        entry_signal(2)
        assert read(syms['checkpoint'][0],4)==bytes((2,0,5,4)),'next phase did not capture improvements'
        shot('07-proxima-fase');play(2)
        check('Victory resolves route and generates next checkpoint with earned upgrades')
        checkpoint=read(syms['checkpoint'][0],4)
        allow_writes=True;w16('hp',0);write(syms['gameOver'][0],b'\1');allow_writes=False
        wait(lambda:state()==3 and u8('resultActive'),'defeat',20*fps);run(fps);press(3)
        wait(lambda:state()==0 and 'A: COMEÇAR' in textrow(26),'retry')
        assert read(syms['checkpoint'][0],4)==checkpoint
        check('Defeat retry retains entry code and opens mission without another code screen')
        # Reset while a mission panel owns VRAM/RAM: no stale screen pointers may survive.
        core.retro_reset();buttons.clear()
        for tick in range(20*fps):
            if 'NOVO JOGO' in textrow(12):break
            if tick%fps==fps//2:press(3)
            else:run()
        else:
            shot('FAIL-reset-boot');raise AssertionError(('reset boot',textrow(2),textrow(12)))
        run(fps)
        assert 'NOVO JOGO' in textrow(12)
        assert read(syms['checkpoint'][0],1)==b'\0','reset retained checkpoint RAM'
        open_input();input_code(encode(2,0,5,4));press(1);assert u8('signalView')==2
        press(1);entry_signal(2);play(2)
        assert u8('shotPower')==5 and u8('speedPct')==80
        check('Console reset clears borrowed screens and accepts previous continuation code')
        # A separate process starts with genuinely fresh console RAM and no save file.
        command=['/usr/bin/arch','-x86_64','/usr/bin/python3',str(Path(__file__).resolve()),
                 '--fresh-code','2,0,5,4','--output',str(out/'fresh-session')]
        if args.pal:command.append('--pal')
        subprocess.run(command,check=True)
        assert json.loads((out/'fresh-session/report.json').read_text())['passed']
        check('Fresh process then controller-only password entry restores prior session without SRAM')
        report['passed']=True
    finally:
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':report['passed'],'region':report['region'],'checks':len(report['checks'])}),flush=True)

if __name__=='__main__':main()
