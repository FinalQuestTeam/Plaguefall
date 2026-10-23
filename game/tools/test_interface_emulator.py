"""Approved interface in the production ROM, NTSC/PAL.

Explicit RAM acceleration selects source stages and death. All subsequent UI,
help, confirmation and resume checks are controller-only under a RAM write guard.
"""
from pathlib import Path
import os,re,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

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
    out=args.output or GAME/'art/interface-ux-v2/integracao/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    cram=(C.c_uint16*64).in_dll(core,'cram')
    def vw(address):return vram[address]+(vram[address+1]<<8)
    observe_radio=False;radio_border=None;radio_bg=None;radio_frame_checks=0
    def edge():
        bpp=4 if fmt==1 else 2
        return b''.join(raw[y*pitch:y*pitch+w*bpp] if y<8 or y>=h-8 else
            raw[y*pitch:y*pitch+8*bpp]+raw[y*pitch+(w-8)*bpp:y*pitch+w*bpp] for y in range(h))
    def run(n=1):
        nonlocal radio_frame_checks
        for _ in range(n):
            core.retro_run()
            if observe_radio:
                assert read(syms['regValues'][0]+1,1)[0]&64,'mission content disabled the display'
                assert edge()==radio_border,'mission content changed the persistent border'
                assert raw_vram(0xc000,4096)==radio_bg,'mission guide rebuilt its background'
                radio_frame_checks+=1
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
    def raw_vram(start,size):return bytes(vram[(start+i)^1] for i in range(size))
    def picture():
        return (raw_vram(0,0xa800),raw_vram(1440*32,96*32),raw_vram(0xc000,4096),raw_vram(0xe000,4096))
    keys=['px','py','pfx','pfy','hp','kills','spawnTimer','phaseStats','surviveLeft','collected','npcHp','npcX','npcY','enemies','pshots','eshots','flashTimer','faceX','faceY','items','bombs','shotPower','shotMode','modeCharges','shieldTimer','invTimer','shotCooldown','speedPct','item','sel','glowClock','glowCursor','glowPhase','glowUploading','freezeTimer']
    def simulation():return {name:read(*syms[name]) for name in keys if name in syms}
    def same(expected,label):
        now=simulation();assert now==expected,(label,[n for n in expected if now[n]!=expected[n]])
    def enter_pause():
        buttons.add(3);until(lambda:state()==2,'pause');buttons.clear();run(2)
        assert 'PAUSADO' in textrow(2),textrow(2)
        # An allocation failure can leave the arena's opaque font loaded even
        # though the tilemap contains the correct text. Inspect pixels as well.
        font=raw_vram(1440*32,96*32)
        colors={pixel for byte in font for pixel in (byte>>4,byte&15)}
        assert colors=={0,15},('pause font must be transparent',u8('currentLevel'),colors)
        assert font[:32]==bytes(32),'pause space glyph must be transparent'
        assert font==(GAME/'res/text/font.bin').read_bytes(),'Portuguese pause font pixels'
    def resume(key):
        buttons.add(key);until(lambda:state()==1,'resume');buttons.clear()
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),
        'setup':'RAM accelerates phase selection and death for entry; no RAM writes during interface navigation, pause, help, cancellation or resume.',
        'phases':[],'helpPages':8,'failures':[]}
    def save(): (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    mission=json.loads((GAME/'art/interface-ux-v2/avaliacao.json').read_text())['phases']
    current_copy=json.loads((GAME/'art/interface-ux-v2/conteudo-aprovado.json').read_text())['phases']
    enemy_ids={name:int(value) for name,value in re.findall(r'^#define\s+(ENEMY_\w+)\s+(\d+)\b',
        (GAME/'src/enemies/enemies.h').read_text(),re.M)}
    portraits=(GAME/'res/mission/portraits.bin').read_bytes()
    panel_tiles=int((GAME/'src/system/video/screens/panel_data.h').read_text().split('PANEL_TILE_COUNT ')[1].split()[0])
    radio_count=int((GAME/'src/system/video/screens/radio_panel_data.h').read_text().split('RADIO_PANEL_TILE_COUNT ')[1].split()[0])
    mission_base=832
    mission_scratch=mission_base+radio_count
    radio_tiles=(GAME/'res/radio_panel/tiles.bin').read_bytes()[:radio_count*32]
    radio_map=struct.unpack('>1120H',(GAME/'res/radio_panel/map.bin').read_bytes())
    radio_palette=list(struct.unpack('>16H',(GAME/'res/radio_panel/palette.bin').read_bytes()))
    radio_palette[15]=0x4ce
    insect_palette=struct.unpack('>16H',(GAME/'res/insects/palette.bin').read_bytes())
    def packed(c):return (c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
    def radio_panel():
        assert raw_vram(mission_base*32,radio_count*32)==radio_tiles,'mission radio patterns changed'
        assert list(cram[48:64])==list(map(packed,radio_palette)),'mission radio palette'
        assert list(cram[16:32])==list(map(packed,insect_palette)),'enemy portrait palette changed'
        for y in range(28):
            for x in (0,1,38,39):
                attr=vw(0xc000+(y*64+x)*2)
                assert attr==0x6000+mission_base+radio_map[y*40+x],('radio frame',x,y,hex(attr))
        assert cram[15]==packed(0xccc) and cram[47]==packed(0x4ce),'gold titles and neutral gray descriptions'
    paper_palette=struct.unpack('>16H',(GAME/'res/interface/palette.bin').read_bytes())
    assert insect_palette[10]==paper_palette[14],'original portrait backing colour must remain exact'
    def portrait_bytes(kind):
        data=portraits[enemy_ids[kind]*512:(enemy_ids[kind]+1)*512]
        return bytes(((b>>4 or 10)<<4)|(b&15 or 10) for b in data)
    for phase,copy in zip(mission,current_copy):phase['name']=copy['name']
    import unicodedata
    def plain(text):return unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode()
    mission[4]['goal']='CHEGUE A SAIDA SINALIZADA.'
    mission[7]['goal']='LEVE DINORAH VIVA ATE A SAIDA.'
    try:
        run(120);press(3);run(fps*4);shot('menu')
        press(5);press(1);run(fps)
        for page in range(8):
            assert f'{page+1}/8' in textrow(2),('help page',page,textrow(2))
            shot('help-'+str(page+1));press(1)
        assert '1/8' in textrow(2),'A must cycle pages, not leave help'
        press(6);assert '8/8' in textrow(2),'left wrap'
        press(3);run(fps);shot('menu-after-help')
        press(4);press(1);until(lambda:state()==6,'story')
        run(2*fps);shot('dialogue-padre')
        if u16('typed')<u16('typeTotal'):press(1)
        assert state()==6 and u16('typed')==u16('typeTotal') and u8('lineIdx')==0,'radio first line incomplete'
        press(1);run(fps*2);shot('dialogue-damiao')
        if u16('typed')<u16('typeTotal'):press(1)
        assert state()==6 and u16('typed')==u16('typeTotal') and u8('lineIdx')==1,'radio last line incomplete'
        press(1);until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep1');run(2)
        assert 'PÁTIO DA IGREJA' in textrow(5),textrow(5)
        press(8);run(3);assert u8('pendingLevel')==1,'C must not skip preparation in release'
        baseline=snapshot()
        for node in range(1,21):
            ordinary=False;restore(baseline)
            # Real startPhase establishes actors/objective. Accelerated death
            # then uses the ordinary story -> briefing -> start path.
            write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'setup-play');run(fps*4)
            # Enter the actual defeat/result path, including its input delay.
            w16('hp',0);write(syms['gameOver'][0],b'\1')
            until(lambda:state()==3 and not u8('transitioning'),'setup-defeat');run(fps);press(3)
            until(lambda:state()==6 or (state()==0 and 'A: COMEÇAR' in textrow(26)),'death-entry')
            if state()==6:
                run(fps*2);shot('dialogue-'+names[node]);press(3)
            until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'briefing');run(2)
            assert mission[node-1]['name'] in textrow(5),('place',node,textrow(5))
            goal=' '.join(textrow(r).replace('.',' ').strip() for r in (9,10))
            expected=mission[node-1]['goal'].replace('.','')
            assert plain(expected) in plain(goal),('goal',node,goal,expected)
            assert 'SUA MISSÃO' in textrow(7) and 'AMEAÇA PRINCIPAL' in textrow(12)
            assert 'DICA DE COMBATE' in textrow(21) and 'B: GUIA' in textrow(26)
            tip=' '.join(' '.join(textrow(r).replace('.',' ') for r in (22,23)).split())
            expected_tip=current_copy[node-1]['route'] or current_copy[node-1]['attention']
            assert expected_tip.replace('.','') in tip,('mission tip clipped',node,tip,expected_tip)
            roster=list(dict.fromkeys(current_copy[node-1]['roster']))
            assert raw_vram(mission_scratch*32,512) in [portrait_bytes(kind) for kind in roster], 'highlighted insect absent from phase'
            radio_panel()
            shot('prep-'+names[node])
            # The guide belongs to preparation. Navigate every page under the
            # same write guard used for the pause; A must never start a level.
            ordinary=True;frozen=simulation();card=picture();card_pixels=rgb()
            observe_radio=True;radio_border=edge();radio_bg=raw_vram(0xc000,4096)
            press(0);assert state()==0 and 'GUIA DA FASE' in textrow(2)
            pages=len(roster)+2
            assert f'1/{pages}' in textrow(2)
            same(frozen,'mission guide entry')
            for page in range(pages):
                assert f'{page+1}/{pages}' in textrow(2),('mission guide page',node,page,textrow(2))
                radio_panel()
                if page==1:assert 'CONTROLES' in textrow(8) and 'ESCOLHER ITEM' in textrow(14)
                if page>=2:
                    assert 'CONHEÇA O INSETO' in textrow(8) and 'COMO RECONHECER' in textrow(19)
                    assert raw_vram(mission_scratch*32,512)==portrait_bytes(roster[page-2]), 'guide portrait does not match roster'
                if node in (1,6,8,9,20):shot('guide-'+names[node]+'-'+str(page+1))
                press(1);assert state()==0,'A in mission guide started gameplay'
                same(frozen,'mission guide browsing')
            assert f'1/{pages}' in textrow(2),'guide forward wrap'
            press(6);assert f'{pages}/{pages}' in textrow(2),'guide left wrap'
            press(7);assert f'1/{pages}' in textrow(2),'guide right wrap'
            press(0);assert 'A: COMEÇAR' in textrow(26) and picture()==card and rgb()==card_pixels,'B must restore mission card'
            press(0);press(3);assert 'A: COMEÇAR' in textrow(26) and state()==0,'START must return from guide'
            same(frozen,'mission guide return')
            observe_radio=False
            ordinary=True;press(1);until(lambda:state()==1,'play');run(fps*4)
            before=simulation();graphics=picture();enter_pause();same(before,'pause entry')
            # PANEL_begin flushes already queued actor DMA before lending VRAM.
            # Its snapshot is the stable, fully submitted gameplay picture.
            count=int((GAME/'src/system/video/screens/panel_data.h').read_text().split('PANEL_TILE_COUNT ')[1].split()[0])
            pattern_bytes=(count+112)*32
            frozen_vram=read(u32('saved'),pattern_bytes+8192+3072)
            # Arena/NPC map uploads queued on the last live frame are flushed
            # on entry too. Resume must restore this fully submitted snapshot,
            # including those map cells, rather than the pre-flush map.
            submitted_a=frozen_vram[pattern_bytes:pattern_bytes+4096]
            submitted_b=frozen_vram[pattern_bytes+4096:pattern_bytes+8192]
            assert frozen_vram[-3072:]==graphics[1], 'font snapshot'
            submitted=bytearray(raw_vram(0,0xa800));submitted[OBJECT_END*32:OBJECT_END*32+pattern_bytes]=frozen_vram[:pattern_bytes]
            assert submitted[:OBJECT_END*32]==graphics[0][:OBJECT_END*32], 'fixed object patterns'
            graphics=(bytes(submitted),graphics[1],submitted_b,submitted_a)
            assert 'ITEM SELECIONADO:' in textrow(15) or 'TIRO ATIVO:' in textrow(15)
            shot('pause-'+names[node]);run(fps);same(before,'idle pause')
            press(5);press(1);assert 'COMO JOGAR' in textrow(2),'help from pause'
            for page in range(8):
                assert f'{page+1}/8' in textrow(2)
                run(fps//5);same(before,'paused help')
                if node==6:shot('pause-help-'+str(page+1))
                press(7)
            press(0);assert state()==2 and 'PAUSADO' in textrow(2),'help must return to pause'
            # Selection remains on help. Next option requests exit, default safe.
            press(5);press(1);assert 'SAIR DA PARTIDA?' in textrow(2)
            if node==6:shot('exit-confirmation')
            same(before,'exit confirmation');press(1)
            assert state()==2 and 'PAUSADO' in textrow(2),'default confirmation must cancel'
            press(1);press(3);assert state()==2,'START cancels confirmation without leaving pause'
            resume(0);same(before,'resume exact simulation')
            after_picture=picture()
            mismatch=[(i,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:12]) for i,(a,b) in enumerate(zip(graphics,after_picture)) if a!=b]
            assert not mismatch,('graphics restoration',node,mismatch)
            run(2);shot('resumed-'+names[node])
            # Explicit START resume is also supported.
            # A host video frame can end inside the preceding world update
            # (notably scrolling escort rooms). Take the frozen baseline once
            # START has actually been consumed at the next input boundary.
            enter_pause();second=simulation();run(2);same(second,'second pause frozen')
            resume(3);same(second,'START resume')
            run(2)
            report['phases'].append({'id':names[node],'goalCorrect':True,'realProgress':True,'pauseAndHelpFreezeSimulation':True,
                'helpReturnsToPause':True,'exitDefaultsSafe':True,'BAndStartResume':True,'graphicsVRAMRestoredExactly':True,
                'missionGuidePages':pages,'missionGuideFreezesSimulation':True,'missionCardRestoredExactly':True})
            report['phases'][-1].update({'radioMonitorNativeFrameExact':True,'enemyPortraitPixelsAndPalettePreserved':True})
            print('PASS',names[node],'briefing/pause/help/restore',flush=True);save()
        # Release combo must retain the current stage. Only setup resets the foes.
        ordinary=False;restore(baseline);press(1)
        until(lambda:state()==1 and not u8('transitioning'),'release-play');run(fps*4)
        write(syms['enemies'][0],bytes(syms['enemies'][1]));w16('spawnTimer',60000)
        ordinary=True;hold({0,1,8},3);assert u8('currentLevel')==1,'release debug combo still skips stage'
        # Confirming the destructive option is the only route from pause to title.
        enter_pause();press(5);press(5);press(1);press(5);press(1);run(fps*2)
        shot('title-after-confirmed-exit');assert 'NOVO JOGO' in textrow(12),'confirmed exit did not reach title'
        report['releaseShortcutsDisabled']=True;report['confirmedExitWorks']=True
        report['persistentMissionContentFramesChecked']=radio_frame_checks
        report['passed']=True;save()
    except Exception as exc:
        report['failures'].append(repr(exc));shot('FAIL');save();raise
    finally:
        core.retro_unload_game();core.retro_deinit()
    print(json.dumps({'passed':True,'region':report['region'],'phases':len(report['phases'])}),flush=True)

if __name__=='__main__':main()
