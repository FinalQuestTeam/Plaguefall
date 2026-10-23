"""Traversal, escort entry, complete walk cycles and objective combat regressions.

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
    out=args.output or GAME/'art/objetivos-travessia-escolta-v1/integracao-2048/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    def zeros(name):write(syms[name][0],bytes(syms[name][1]))
    def vr(addr,n):return bytes(vram[((addr+j)&65535)^1] for j in range(n))
    def seed(slot,kind,x,y,health=10,fire=60000):
        d=bytearray(46);struct.pack_into('>hhii',d,0,x,y,x<<6,y<<6);struct.pack_into('>H',d,16,fire);d[30]=kind;d[31]=health;d[44]=1
        write(syms['enemies'][0]+slot*46,d)
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),'checks':{}}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(name,value=True):report['checks'][name]=value;save();print('PASS',name,value,flush=True)
    maps=json.loads((GAME/'art/objetivos-travessia-escolta-v1/integracao-2048/mapas.json').read_text())
    width=maps['04']['width'];cols=width//8;goalX=maps['04']['exit'][0]+8;goalY=168
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2);baseline=snapshot()
        def enter(node):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1);until(lambda:state()==1 and not u8('transitioning'),'play')
            zeros('enemies');zeros('pshots');zeros('eshots');zeros('combatDeaths');w16('spawnTimer',60000);run(fps*4)
        # Inspect the displayed scroll, not the next camera position in RAM.
        # Left/up movement used to expose old ring cells before queued DMA.
        vsram=(C.c_uint16*64).in_dll(core,'vsram')
        for node,key,rows in ((5,'04',36),(8,'06b',40)):
            enter(node);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
            rawmap=struct.unpack('>'+str(cols*rows)+'H',(GAME/f'res/routes/{key}/map.bin').read_bytes())
            terrain={(rx//8+dx,ry//8+dy) for rx,ry,rw,rh in maps[key]['hazards'] for dx in range(rw//8) for dy in range(rh//8)}
            terrainBase=545+(23 if key=='04' else 0)
            pos(1900,270);run(fps*10);samples=0;planeA=u16('bga_addr')
            for targetX,targetY in ((48,96),(1900,270),(48,96)):
                pos(targetX,targetY)
                for _ in range(500):
                    run();samples+=1
                    cx=(-vw(u16('hscrl_addr')+2))&65535;cy=vsram[1]&1023
                    for ty in range((cy+24)//8,min((cy+223)//8+1,rows)):
                        for tx in range(cx//8,min((cx+319)//8+1,cols)):
                            address=((ty&31)*64+(tx&63))*2
                            got=vw(0xc000+address)&2047;want=785+rawmap[ty*cols+tx]
                            assert got==want,('visible streaming cell',key,samples,tx,ty,got,want,cx,cy)
                            if (tx,ty) in terrain:
                                mask=int((tx,ty-1) in terrain)|(int((tx+1,ty) in terrain)<<1)|(int((tx,ty+1) in terrain)<<2)|(int((tx-1,ty) in terrain)<<3)
                                variant=15+(tx&3)+((ty&1)<<2) if mask==15 else mask
                                assert (vw(planeA+address)&2047)==terrainBase+variant,('visible terrain cell',key,samples,tx,ty)
            check('streamingEveryDisplayedFrame-'+key,{'frames':samples,'staleSceneryCells':0,'missingTerrainCells':0,'bothAxesAndDirections':True})
        # Inspect each unique landmark through the production camera/VDP ring,
        # with both actors and the normal HUD present. RAM only sets viewpoints.
        for key,node in [('04',5),('06b',8)]:
            enter(node)
            scene=maps[key];art=scene['art'];rows=scene['height']//8
            patterns=(GAME/f'res/routes/{key}/tiles.bin').read_bytes()
            rawmap=struct.unpack('>'+str(cols*rows)+'H',(GAME/f'res/routes/{key}/map.bin').read_bytes())
            assert scene['tiles']<=640 and len(patterns)==scene['tiles']*32
            assert max(art['blockSimilarityToFirst'])<0.8
            for index,landmark in enumerate(art['landmarks']+art['ground_details']):
                x,y,w,h=landmark['rect']
                if index<4:assert y+h<=scene['bounds'][1]
                # Returning from the last landmark to the first floor detail
                # needs up to 432 frames at the camera's 4px/frame slew limit.
                pos(x+w//2,112 if key=='04' else 192);run(fps*10)
                assert vr(785*32,len(patterns))==patterns,('scenery atlas',key,index)
                cx=u16('cameraX')//8;cy=u16('cameraY')//8
                for ty in range(cy,min(cy+28,rows)):
                    for tx in range(cx,min(cx+40,cols)):
                        got=vw(0xc000+((ty&31)*64+(tx&63))*2)&2047
                        assert got==785+rawmap[ty*cols+tx],('landmark ring',key,index,tx,ty)
                shot(f'{key}-marco-{index+1}' if index<4 else f'{key}-piso-{index-3}')
            check('continuousScenery-'+key,{'landmarks':len(art['landmarks']),'tiles':scene['tiles'],
                  'groundDetails':len(art['ground_details']),'sceneryVRAMMatchesExport':True,'blockSimilarityToFirst':art['blockSimilarityToFirst']})
        mud_centers=set()
        def move_to(x,y,limit=2000):
            for i in range(limit):
                if u8('playerSlowPct'):mud_centers.add(u16('px')+8)
                dx=x-u16('px');dy=y-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:buttons.clear();run();return
                buttons.clear()
                if abs(dx)>2:buttons.add(7 if dx>0 else 6)
                if abs(dy)>2:buttons.add(5 if dy>0 else 4)
                run()
                assert state()==1,('move ended',x,y,state())
            raise AssertionError(('stuck',x,y,u16('px'),u16('py')))
        # A stale position from a previous stage must never seed the entry camera.
        restore(baseline);pos(1990,264);write(syms['pendingLevel'][0],bytes([8]));press(1)
        until(lambda:state()==1,'escort-entry')
        expectedY=max(0,208+8-16-(224+24)//2)
        assert u16('cameraX')==0 and u16('cameraY')==expectedY,('entry camera',u16('cameraX'),u16('cameraY'))
        start=(u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))
        remaining=u16('freezeTimer');assert remaining>fps*2
        while u16('freezeTimer'):
            assert u16('dinorahHp')==100 and (u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))==start
            assert u16('cameraX')==0 and u16('cameraY')==expectedY
            run()
        assert u16('dinorahHp')==100
        shot('06b-inicio-camera');check('escortEntryStartsAtSpawnAndFreezesUntilGo',{'countdownFrames':remaining,'cameraY':expectedY})
        # Request a stop just after the first footfall. Every remaining pose
        # must still advance in world coordinates, before settling into idle.
        frames=(GAME/'res/dinorah/frames.bin').read_bytes()
        def pose():
            pixels=vr(761*32,768)
            matches=[i%6 for i in range(30) if pixels==frames[i*768:(i+1)*768]]
            assert matches, 'unknown Dinorah frame in VRAM'
            return matches[0]
        until(lambda:pose()==2,'escort-first-footfall',fps)
        zeros('enemies');zeros('eshots');w16('spawnTimer',60000);pos(600,208)
        sequence=[];holdFrames={};posePositions={};firstStep=(u16('dinorahX'),u16('dinorahY'))
        for _ in range(fps*2):
            current=pose();holdFrames[current]=holdFrames.get(current,0)+1
            posePositions.setdefault(current,[]).append((u16('dinorahX'),u16('dinorahY')))
            if not sequence or sequence[-1]!=current:sequence.append(current)
            if current<2:break
            run()
        assert sequence==[2,3,4,5,0],sequence
        assert all(holdFrames.get(p,0)>=fps*3//20 for p in (3,4,5)),holdFrames
        assert all(posePositions[p][0]!=posePositions[p][-1] for p in (3,4,5)),posePositions
        assert u16('dinorahX')>firstStep[0]+8 and u16('dinorahY')>firstStep[1]+8
        stopped=(u16('dinorahX'),u16('dinorahY'));run(fps)
        assert stopped==(u16('dinorahX'),u16('dinorahY')) and u8('dinorahState')==1
        check('escortStepKeepsMovingThroughAllFourPoses',{'poses':sequence,'framesPerPose':holdFrames,'posePositions':posePositions})
        # A short approach to an authored pause must use the whole cycle for
        # its remaining distance, without arriving early and walking in place.
        stoppedBase=snapshot()
        def escort_position(x,y,node):
            w16('dinorahX',x);w16('dinorahY',y)
            write(syms['dinorahFx'][0],struct.pack('>i',x<<6));write(syms['dinorahFy'][0],struct.pack('>i',y<<6))
            write(syms['dinorahNode'][0],bytes([node]));w16('dinorahPauseTimer',0);w16('dinorahFireTimer',60000)
            pos(x,y)
        escort_position(848,156,15)
        until(lambda:pose()==2,'escort-short-waypoint-step',fps)
        sequence=[];positions={}
        for _ in range(fps*2):
            current=pose()
            if not sequence or sequence[-1]!=current:sequence.append(current)
            positions.setdefault(current,[]).append((u32('dinorahFx'),u32('dinorahFy')))
            if current<2:break
            if u8('dinorahState')==2:assert current==5  # RAM can precede the queued VBlank
            else:assert u8('dinorahState')==0 and u8('dinorahNode')==15
            run()
        assert sequence==[2,3,4,5,0],sequence
        assert all(positions[p][0]!=positions[p][-1] for p in (2,3,4,5)),positions
        assert (u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'),u8('dinorahState'))==(856,152,16,2)
        stopped=(u16('dinorahX'),u16('dinorahY'));run(fps)
        assert stopped==(u16('dinorahX'),u16('dinorahY'))
        check('escortShortWaypointMovesUntilFinalPoseThenPauses',{'poses':sequence,'arrival':stopped})
        # A ready shot must wait for the moving step to end before aiming.
        restore(stoppedBase);escort_position(48,220,1)
        until(lambda:pose()==2,'escort-step-before-aim',fps)
        w16('dinorahFireTimer',0);seed(0,0,112,220,30,60000)
        sequence=[];positions={}
        for _ in range(fps*2):
            current=pose()
            if not sequence or sequence[-1]!=current:sequence.append(current)
            positions.setdefault(current,[]).append((u16('dinorahX'),u16('dinorahY')))
            if u8('dinorahState')==3 and current<2:break
            if u8('dinorahState')==3:assert current==5
            else:assert u8('dinorahState')==0
            run()
        assert sequence==[2,3,4,5,0],sequence
        assert all(positions[p][0]!=positions[p][-1] for p in (3,4,5)),positions
        aimPosition=(u16('dinorahX'),u16('dinorahY'));run(2)
        assert aimPosition==(u16('dinorahX'),u16('dinorahY')) and u8('dinorahState')==3
        check('escortFinishesMovingStepBeforeAiming',{'poses':sequence,'aimPosition':aimPosition})
        if args.only_entry:
            report['passed']=True;save();print('ALL ENTRY CHECKS PASSED',flush=True);return
        # Full-height terrain must slow feet at the north, middle and south,
        # including late rectangles beyond the old hard-coded mudCount of 8.
        enter(5)
        reach=maps['04'];crossings=[r for r in reach['hazards'] if r[1]==80 and r[3]==192]
        assert len(crossings)==3,crossings
        import re
        mud_header=(GAME/'src/elements/mud.h').read_text()
        mud_base=int(re.search(r'#define MUD_PLAYER_BASE\s+(\d+)',mud_header).group(1))
        mud_max=int(re.search(r'#define MUD_PLAYER_MAX\s+(\d+)',mud_header).group(1))
        for rx,ry,rw,rh in crossings:
            for py_probe in (80,160,256):
                pos(rx+rw//2-8,py_probe);run(4)
                assert u8('playerSlowPct')>=mud_base,('full-height mud',rx,py_probe,u8('playerSlowPct'))
        pos(264,144);run(4);assert u8('playerSlowPct')==0
        before=u32('pfx');hold({7},fps//3);dry_distance=u32('pfx')-before
        pos(464,160);run(fps*5);assert u8('playerSlowPct')==mud_max
        before=u32('pfx');hold({7},fps//3);mud_distance=u32('pfx')-before
        assert 0<mud_distance<dry_distance*.6,(dry_distance,mud_distance)
        run(fps*4);shot('04-lama-altura-inteira')
        pos(264,144);run(4);assert u8('playerSlowPct')==0
        assert u16('hp')==100,'mud should slow rather than damage'
        check('reachMudFullHeightAndProgressiveSlow',{'crossings':crossings,'coverage':reach['terrainCoverage']['walkableFraction'],
              'maximumSlowPercent':mud_max,'dryDistanceFixed':dry_distance,'mudDistanceFixed':mud_distance,'resetsOnDryGround':True})
        # Controller-only traversal after scenario setup; no quota and both ring axes.
        enter(5);assert u16('arenaMaxX')==width-16
        mud_centers.clear()
        ordinary=True
        for i,(x,y) in enumerate(maps['04']['points'][1:]):
            if i==len(maps['04']['points'])-2:break
            move_to(x-8,y-8)
            if x>1536 and x<1900:shot('04-caminho-longo')
        ordinary=False
        assert all(any(x<=cx<x+w for cx in mud_centers) for x,y,w,h in crossings),'route skipped an unavoidable muddy crossing'
        check('reachFullRouteControllerOnly')
        assert u16('kills')==0 and state()==1
        # Full visible tile window always matches the 256-column ROM map.
        rawmap=struct.unpack('>'+str(cols*36)+'H',(GAME/'res/routes/04/map.bin').read_bytes())
        def verify_map(rawmap,rows):
            cx=u16('cameraX')//8;cy=u16('cameraY')//8
            for ty in range(cy,min(cy+28,rows)):
                for tx in range(cx,min(cx+40,cols)):
                    got=vw(0xc000+((ty&31)*64+(tx&63))*2)&2047
                    want=785+rawmap[ty*cols+tx]
                    assert got==want,('ring',tx,ty,got,want,cx,cy)
        run(3);verify_map(rawmap,36);assert u16('cameraX')>1536;check('horizontalAndVerticalRingPast1536')
        # Pause truly freezes escort/objective; scrolling map is restored.
        before=vr(0xc000,4096);press(3);until(lambda:state()==2,'pause');run(4);shot('04-pausa');run(fps)
        press(0);until(lambda:state()==1,'resume');run(2);assert vr(0xc000,4096)==before;check('pauseRestoresExtendedMap')
        ordinary=True;move_to(goalX,goalY);buttons.clear();run(fps//2);ordinary=False
        assert state()==4 and u16('kills')==0;shot('04-sucesso');check('reachWinsWithoutKills')
        # No hidden early kill quota. Holding on the start cannot complete it.
        enter(5);w16('kills',999);run(fps);assert state()==1;check('reachIgnoresKillQuota')
        pos(960,168);run(fps);assert state()==1;check('former1024ExitNoLongerCompletes')
        # Hole blocks feet; player bullets cross it.
        pos(152,144);hold({7},30);assert u16('px')<=160
        zeros('pshots');write(syms['pshots'][0],struct.pack('>iiiiBBBB',164<<6,160<<6,192,0,0,0,1,0));run(15)
        assert read(syms['pshots'][0]+18,1)==b'\1';check('holesBlockFeetButNotBullets')
        pos(1176,144);hold({7},30);assert 1176<=u16('px')<=1184;shot('04-buraco-apos-1024');check('collisionMaskBeyond1024')
        # Normal controller follows the authored escort route. No RAM writes.
        enter(8);escortBase=snapshot();initial=(u16('dinorahX'),u16('dinorahY'));ordinary=True
        run(fps*5);assert u8('dinorahState')==1;assert u16('dinorahX')>initial[0]
        far=(u16('dinorahX'),u16('dinorahY'));run(fps*2);assert far==(u16('dinorahX'),u16('dinorahY'));ordinary=False
        shot('06b-aguardando');check('escortWaitsForCover')
        markerArt=(GAME/'res/routes/markers.bin').read_bytes();assert vr(605*32,len(markerArt))==markerArt
        def sat():
            result=[];at=0
            for _ in range(80):
                off=0xf400+at*8;sl=vw(off+2);attr=vw(off+4);result.append((attr&2047,sl>>8,attr));at=sl&127
                if not at:break
            return result
        sprites=sat();assert any(605<=t<613 and size==5 for t,size,a in sprites),sprites
        assert any(621<=t<629 and size==5 for t,size,a in sprites),sprites
        assert not any(1440<=t<1536 for t,size,a in sprites);check('nativeArrowAndAlertUseInterfacePalette')
        restore(escortBase);ordinary=True;seen=set();ticks=0;shotsTaken=set();playerNode=1
        while state()==1 and ticks<fps*100:
            node=u8('dinorahNode');seen.add(u8('dinorahState'))
            target=maps['06b']['points'][min(playerNode,len(maps['06b']['points'])-1)]
            dx=target[0]-8-u16('px');dy=target[1]-8-u16('py')
            ax=target[0]-8-u16('dinorahX');ay=target[1]-8-u16('dinorahY')
            buttons.clear()
            if abs(dx)<=3 and abs(dy)<=3 and node>playerNode:playerNode+=1
            if abs(dx)+abs(dy)>=abs(ax)+abs(ay)-32 or node>=len(maps['06b']['points']):
                if abs(dx)>3:buttons.add(7 if dx>0 else 6)
                if abs(dy)>3:buttons.add(5 if dy>0 else 4)
            run();ticks+=1
            if ticks%(fps*8)==0:shot('06b-percurso-'+str(ticks//fps))
        ordinary=False;buttons.clear()
        assert state()==4,('escort route',state(),ticks,u16('dinorahX'),u16('dinorahY'),u16('px'),u16('py'),u8('dinorahNode'),seen)
        assert u16('dinorahHp')==100 and 2 in seen and u16('kills')==0
        shot('06b-chegada');until(lambda:u8('resultActive')==1,'escort-result-render');run(2);shot('06b-sucesso');check('escortFullRouteControllerOnly',{'seconds':round(ticks/fps,1),'hp':u16('dinorahHp'),'states':sorted(seen)})
        enter(8);w16('dinorahPauseTimer',60000);run(fps)  # finish the last footfall before testing idle restoration
        w16('dinorahAnimTick',0);run(6)
        frozen=(u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'),u16('dinorahPauseTimer'));pixels=vr(761*32,24*32)
        press(3);until(lambda:state()==2,'escort-pause');run(fps);assert (u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'),u16('dinorahPauseTimer'))==frozen
        press(0);until(lambda:state()==1,'escort-resume');run(2);assert vr(761*32,24*32)==pixels;check('escortPauseFreezesAndRestoresSprite')
        # Local invulnerability and normal attack paths, in isolated scenarios.
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',0)
        x=u16('dinorahX');y=u16('dinorahY')
        def enemy_bullet():
            write(syms['eshots'][0],struct.pack('>iiiiBBBB',(u16('dinorahX')+4)<<6,(u16('dinorahY')+4)<<6,0,0,1,10,1,0));run()
        enemy_bullet();assert u16('dinorahHp')==90
        enemy_bullet();assert u16('dinorahHp')==90
        run(fps);enemy_bullet();assert u16('dinorahHp')==80;check('escortBulletDamageAndLocalInvulnerability')
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahFireTimer',1);w16('dinorahInvTimer',0)
        x=u16('dinorahX');y=u16('dinorahY');seed(0,0,x+64,y,1,60000)
        allyPeak=0
        for _ in range(fps*4):
            run();allyPeak=max(allyPeak,sum(read(syms['allyShots'][0]+i*20+18,1)==b'\1' for i in range(2)))
        assert u16('kills')==1 and allyPeak>0 and u16('dinorahHp')==100
        shot('06b-disparo');check('allyShotKillsWithoutInventoryOrFriendlyFire',{'peakBullets':allyPeak,'kills':u16('kills')})
        enter(8);w16('dinorahPauseTimer',60000);pos(320,192);run(12);seed(0,0,200,248,10,0);run(8)
        shotdata=read(syms['eshots'][0],20);assert shotdata[18] and int.from_bytes(shotdata[8:12],'big',signed=True)<0,(state(),u16('dinorahHp'),read(syms['enemies'][0],46).hex(),read(syms['eshots'][0],120).hex())
        zeros('eshots');seed(0,0,200,248,10,0);write(syms['enemies'][0]+43,b'\1');run(8)
        shotdata=read(syms['eshots'][0],20);assert shotdata[18] and int.from_bytes(shotdata[8:12],'big',signed=True)>0
        check('enemyShooterAimsAssignedActor')
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',0)
        seed(0,4,u16('dinorahX'),u16('dinorahY'));run(2);assert u16('dinorahHp')==88 and u16('flashTimer')==0;check('escortContactDamage')
        # The destination requires both living actors, with 400ms confirmation.
        enter(8);pos(600,208);run(fps)  # finish the committed step before seeding an arrival
        w16('dinorahX',goalX);w16('dinorahY',goalY);write(syms['dinorahFx'][0],struct.pack('>i',goalX<<6));write(syms['dinorahFy'][0],struct.pack('>i',goalY<<6));write(syms['dinorahNode'][0],bytes([len(maps['06b']['points'])]));pos(goalX-200,goalY);run(fps)
        assert state()==1;pos(goalX-40,goalY);run(fps//5);assert state()==1
        # Confirmation advances on game updates; a fixed VBlank count can
        # expire early under load or while the final effects settle.
        until(lambda:state()==4,'escort-arrival-confirmation',fps*2)
        check('escortNeedsBothActorsAndConfirmation')
        # Enemy bullets hit Dinorah, fail/retry reset.
        enter(8);zeros('enemies');w16('dinorahInvTimer',0);w16('dinorahHp',10)
        enemy_bullet();until(lambda:state()==3,'escort-defeat')
        assert state()==3 and u16('dinorahHp')==0,(state(),u16('dinorahHp'));run(5);shot('06b-derrota');check('escortFailureOnEnemyBullet')
        run(fps);press(3);until(lambda:state() in (0,1,6),'retry-request')
        if state()==6:run(fps);press(3);until(lambda:state()==0,'retry-prep')
        if state()==0:
            until(lambda:'A: COMEÇAR' in textrow(26),'retry-prep-ready');run(3);press(1);until(lambda:state()==1,'retry')
        run(fps*4)
        assert u8('currentLevel')==8 and u16('dinorahHp')==100 and u8('dinorahNode')<=2;check('escortRetryResetsSameStage')
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
        spawned=0
        for trial in range(80):
            zeros('enemies');w16('spawnTimer',0);run(2)
            for i in range(16):
                e=read(syms['enemies'][0]+i*46,46)
                if not e[44]:continue
                x,y=struct.unpack_from('>hh',e);size=16;spawned+=1
                assert abs(x-u16('dinorahX'))+abs(y-u16('dinorahY'))>=56
                assert all(not(x<rx+rw and x+size>rx and y<ry+rh and y+size>ry) for rx,ry,rw,rh in maps['06b']['pits'])
                ex,ey,ew,eh=maps['06b']['exit'];assert not(x<ex+ew and x+size>ex and y<ey+eh and y+size>ey)
        assert spawned>=20,spawned;check('sectorSpawnsAvoidActorsHolesAndExit',{'samples':spawned})
        # Peak pilot load: four enemies, Dinorah, Damião, all shot pools.
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000);pos(224,192)
        for i,kind in enumerate([4,5,7,4]):seed(i,kind,224+i*40,112,30,0)
        vb=u32('vtimer');frames0=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big');buttons.add(1);run(fps*6);buttons.clear()
        speed=fps*(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-frames0)/(u32('vtimer')-vb)
        assert speed>=fps*.80,(speed,fps);shot('06b-carga');check('pilotLoadPerformance',{'gameFPS':round(speed,2),'regionFPS':fps})
        # Isolate tempo from the enemy ramp while keeping the real combat load.
        # 8 NTSC-equivalent frames/step -> 90 steps in 12 seconds in both regions.
        enter(8);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
        for i,kind in enumerate([4,5,7,4]):seed(i,kind,224+i*40,112,255,0)
        music=syms['music'][0];assert syms['music'][1]==46
        write(music+36,struct.pack('>HH',8,8));write(music+44,bytes([8,8]));run(fps*8)
        def music_step():return int.from_bytes(read(music+34,2),'big')
        previous=music_step();steps=0;vb=u32('vtimer')
        initial=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
        for _ in range(fps*12):
            run();current=music_step();steps+=(current-previous)%128;previous=current
        elapsed=u32('vtimer')-vb;expected=elapsed*(6 if args.pal else 5)/40
        assert abs(steps-expected)<=1,('music clock stretched under load',steps,expected)
        check('musicTempoFollowsVideoClockUnderCombatLoad',{'steps':steps,'expectedSteps':expected,'videoFrames':elapsed,
              'gameFPS':round(fps*(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-initial)/elapsed,2)})
        report['heap_sentinel_intact']=read(u32('heapEnd')&65535,2)==bytes(2);assert report['heap_sentinel_intact']
        report['passed']=True;save();print('ALL PASSED',flush=True)
    except Exception as exc:
        report['error']=str(exc);shot('FAIL');save();raise
    finally:core.retro_unload_game();core.retro_deinit()
if __name__=='__main__':main()
