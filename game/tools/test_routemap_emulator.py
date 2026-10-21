"""Regional atlas in the production ROM, NTSC/PAL.

RAM setup accelerates source-stage entry and completion. Once each map appears,
a write guard permits only controller input through idle, travel, dialogue and
next-stage entry. Graph conditions, art VRAM, SAT pin and restoration are checked.
Run: arch -x86_64 /usr/bin/python3 game/tools/test_routemap_emulator.py [--pal]
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
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/routemap-regional-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
    rom=GAME/'out/release/rom.bin';original=rom.read_bytes();data=bytearray(original)
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
    symbols=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(GAME/'out/release/rom.out')],text=True)
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
        if u8('arenaActive'):break
        press(3);run(fps)
        if u8('arenaActive'):break
        press(1);run(fps*4)
    if not u8('arenaActive'):shot('startup-failed');raise AssertionError(('start',u8('state'),u8('currentLevel'),u8('arenaActive')))
    assert u8('currentLevel')==1 and u16('arenaMaxX')==495
    shot('01-inicio')
    baseline=snapshot()
    original_fixed=bytes(vram[i^1] for i in range(16*32,101*32))
    tiles=(GAME/'res/routemap/tiles.bin').read_bytes()
    groups=(GAME/'res/routemap/groups.bin').read_bytes()
    font=(GAME/'res/intro/font.bin').read_bytes()
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    places=['','PATIO DA IGREJA','RUA DE SERVICO','BAIXIO DA IGREJA','ABRIGO DE MANUTENCAO',
      'TUNEIS DE MANUTENCAO','SINALIZADOR NA SANTA','PERIMETRO DO RESGATE','RETIRADA POR TERRA',
      'REDE DE ANTENAS','FORNALHA','ALFANDEGA','ACESSO DOS TECNICOS','DRENO TERMICO',
      'DEPOSITO DE DEMOLICAO','COMPORTA DE CARGA','LINHA QUENTE','DECANTACAO',
      'PATIO DOS ENXAMES','GALERIAS DOS NINHOS','CAMARA DO ESCORPIAO']
    footer_copy=json.loads((GAME/'art/routemap-footer-ux-v1/integracao/copy.json').read_text())
    copy_by_edge={(c['current'],c['next']):c for c in footer_copy['cases']}
    # Every edge of the production campaign, including all eight fork outcomes.
    edges=[(1,2),(1,3),(2,4),(3,4),(4,5),(5,6),(6,7),(6,8),(7,9),(8,9),
           (9,10),(10,11),(11,12),(11,13),(12,14),(13,14),(14,15),(15,16),
           (15,17),(16,18),(17,18),(18,19),(19,20)]
    cols=[0,0,1,1,2,3,4,5,5,6,7,8,9,9,10,11,12,12,13,14,15]
    xcoords=[32,96,160,224,56,152,248,48,120,200,280,48,104,160,216,272]
    def state():return u32('flow_state')
    def region_of(node):return 0 if cols[node]<4 else 1 if cols[node]<7 else 2 if cols[node]<11 else 3
    def point_for(node,region):
        if region_of(node)!=region:return (8,104)
        return xcoords[cols[node]],16+(32 if node in (2,7,12,16) else 136 if node in (3,8,13,17) else 88)
    def isolate():
        w16('hp',100);w16('spawnTimer',60000)
        write(syms['enemies'][0],bytes(syms['enemies'][1]))
        for n in ('pshots','eshots'):write(syms[n][0],bytes(syms[n][1]))
    def finish_to_map():
        w16('doneTimer',0);write(syms['flow_state'][0],struct.pack('>I',4));run(2)
        for _ in range(fps*8):
            if state()==5:break
            if state()==6:press(3)
            else:
                assert state()==4,('not map/story',state())
                run()
        assert state()==5,('map entry',state())
        run(3)
    def enter(node):
        restore(baseline);isolate()
        if node==1:return
        finish_to_map();write(syms['pendingLevel'][0],bytes([node]))
        for _ in range(30):
            if state()==1 and u8('currentLevel')==node:break
            if state()==6:press(3)
            else:press(1)
            run(fps//4)
        assert state()==1 and u8('currentLevel')==node,('source entry',node,state(),u8('currentLevel'))
        isolate()
    def pin():
        sat=u16('slist_addr')
        return vw(sat+6)-128,vw(sat)-128,vw(sat+4)&0x7ff,vw(sat+2)&127
    def textrow(row):
        return ''.join(chr((vw(0xe000+(row*64+x)*2)&0x7ff)-1440+32)
            if 1440<= (vw(0xe000+(row*64+x)*2)&0x7ff)<1536 else '.' for x in range(40))
    def check_line(text,row,palette,right=False):
        start=39-len(text) if right else (40-len(text))//2
        assert textrow(row)=='.'*start+text+'.'*(40-start-len(text)),('footer placement',row,textrow(row),text)
        for x in range(40):
            tile=vw(0xe000+(row*64+x)*2)
            assert tile&0x8000,('footer priority',row,x)
            assert (tile>>13)&3==(palette if start<=x<start+len(text) else 0),('footer palette',row,x)
            if not start<=x<start+len(text):assert tile&0x7ff==1,('footer solid background',row,x)
    def check_footer(a,b,traveling=False):
        copy=copy_by_edge[(names[a],names[b])]
        check_line(places[b],22,3)
        check_line(copy['cause'],23,0)
        check_line(copy['consequence'],24,0)
        action='A / START: PULAR VIAGEM' if traveling else 'A / START: SEGUIR PARA A FASE '+names[b]
        check_line(action,26,3,right=True)
        for row in (25,27):
            assert all(vw(0xe000+(row*64+x)*2)==0x8001 for x in range(40)),('footer spacing',row)
    result={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),
      'emulatedROMSHA256':hashlib.sha256(data).hexdigest(),'productionROM':str(rom),
      'setup':'Explicit RAM acceleration for source stage, stats and completion. Map idle/travel/exit run under a write guard.',
      'edges':[],'maxOverlayTiles':0,'failures':[]}
    def save(): (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        for index,(a,b) in enumerate(edges):
            ordinary=False;enter(a)
            # Use the real GRAPH_resolve: only the phase result statistics change.
            stats=bytearray(10)
            if (a,b)==(1,3):struct.pack_into('>H',stats,0,1)
            if (a,b)==(6,8):stats[8]=1
            if (a,b)==(11,13):struct.pack_into('>H',stats,2,1)
            struct.pack_into('>I',stats,4,(60 if (a,b)==(15,17) else 40)*fps)
            write(syms['phaseStats'][0],stats)
            finish_to_map()
            assert u8('pendingLevel')==b,('resolved',a,b,u8('pendingLevel'))
            assert u8('currentNode')==a and u8('nextNode')==b
            r=region_of(b);assert u8('region')==r
            count=u16('overlayCount');assert 0<count<192,('overlay',count)
            result['maxOverlayTiles']=max(result['maxOverlayTiles'],count)
            actual=bytes(vram[(101*32+i)^1] for i in range(25600))
            assert actual==tiles[r*25600:(r+1)*25600],('art patterns',a,b)
            assert bytes(vram[i^1] for i in range(1440*32,1536*32))==font,('opaque font',a,b)
            for t in range(800):
                expected=101+t | ((1+groups[r*800+t])<<13)
                assert vw(0xc000+((t//40+2)*64+t%40)*2)==expected,('art map',a,b,t)
            assert bytes(vram[i^1] for i in range(16*32,101*32))==original_fixed,'fixed tiles overwritten'
            check_footer(a,b)
            shot('map-'+names[a]+'-'+names[b])
            # No RAM writes from this point through the next playable stage.
            ordinary=True
            px0,py0=point_for(a,r);expected_pin=(px0-8,py0-17,1093,0)
            positions=set()
            for _ in range(fps+6):
                run();positions.add(pin());assert state()==5
            assert positions=={expected_pin},('idle pointer',a,b,positions,expected_pin)
            press(1);run(fps//3)
            middle=pin();assert middle[:2]!=expected_pin[:2],('pointer did not travel',a,b)
            assert state()==5,('early exit',a,b,state())
            check_footer(a,b,traveling=True)
            shot('travel-'+names[a]+'-'+names[b])
            if index%2:press(3) # second press skips the journey
            else:run(fps)
            exit_wait=0
            while state()==5 and exit_wait<fps*2:
                run();exit_wait+=1
            assert state()!=5,('map did not leave',a,b)
            for _ in range(20):
                if state()==1 and u8('currentLevel')==b:break
                if state()==6:press(3)
                elif state()==0:press(1)
                else:raise AssertionError(('unexpected exit state',a,b,state()))
                run(fps//4)
            assert state()==1 and u8('currentLevel')==b,('destination',a,b,state())
            assert bytes(vram[i^1] for i in range(16*32,101*32))==original_fixed,'fixed tiles on exit'
            run(fps//2);shot('arrival-'+names[b])
            result['edges'].append({'from':names[a],'to':names[b],'region':r+1,'overlayTiles':count,
              'idlePinPersistent':True,'travelMoved':True,'skipTested':bool(index%2),'exitWaitFrames':exit_wait,
              'artAndFontVRAMExact':True,'fixedTilesPreserved':True,'nextStageEntered':True})
            result['edges'][-1]['footer']={'copyExact':True,'bodyCentered':True,'actionsRightAligned':True,
                'goldTitleAndAction':True,'solidBackgroundAndSpacing':True,'travelActionReplaced':True}
            print('PASS',names[a],'=>',names[b],'overlay',count,flush=True);save()
        result['histories']=[]
        for path in ([1,2,4,5,6,7,9,10,11,12,14,15,16,18,19,20],
                     [1,3,4,5,6,8,9,10,11,13,14,15,17,18,19,20]):
            ordinary=False;restore(baseline);isolate()
            for a,b in zip(path,path[1:]):
                ordinary=False;isolate()
                stats=bytearray(10)
                if (a,b)==(1,3):stats[1]=1
                if (a,b)==(6,8):stats[8]=1
                if (a,b)==(11,13):stats[3]=1
                struct.pack_into('>I',stats,4,(60 if (a,b)==(15,17) else 40)*fps)
                write(syms['phaseStats'][0],stats);finish_to_map()
                assert u8('pendingLevel')==b
                assert 0<u16('overlayCount')<192
                result['maxOverlayTiles']=max(result['maxOverlayTiles'],u16('overlayCount'))
                ordinary=True;press(1);run(fps*2)
                for _ in range(20):
                    if state()==1 and u8('currentLevel')==b:break
                    if state()==6:press(3)
                    elif state()==0:press(1)
                    else:raise AssertionError(('history state',a,b,state()))
                    run(fps//4)
                assert state()==1 and u8('currentLevel')==b
                assert read(syms['departedTo'][0]+a,1)==bytes([b]),('missing edge',a,b)
                expected_visited=sum(1<<n for n in path[:path.index(b)+1])
                assert u32('visited')==expected_visited,('visited history',a,b,u32('visited'),expected_visited)
            result['histories'].append({'path':[names[n] for n in path],'passed':True})
            print('PASS full history',','.join(names[n] for n in path),flush=True);save()
        result['passed']=True;save()
    except Exception as exc:
        result['failures'].append(repr(exc));shot('FAIL');save();raise
    finally:
        core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':True,'region':result['region'],'edges':len(result['edges']),
        'maxOverlayTiles':result['maxOverlayTiles']}),flush=True)

if __name__=='__main__':main()
