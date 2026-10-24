"""Integrated3072px escort scenes: exact VRAM pixels, gates, routes and load.

RAM seeds controlled scenarios; physics, graphics, kill paths and controller
navigation use the normal production code in NTSC/PAL.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

from text_codec import decode
from campaign_geometry import closest,faces
GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--mechanism-pixels-only',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    wanted_phases=os.environ.get('CAMPAIGN_TEST_ESCORT_KEYS','06a,06b,12').split(',')
    out=args.output or GAME/'art/campaign-whole-scenes-v1/routes/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','romSHA256':hashlib.sha256(original).hexdigest(),'buildDirectory':str(build),'emulatedRomSHA256':hashlib.sha256(data).hexdigest(),'movieEnabled':args.movie,'checks':{}}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(name,value=True):report['checks'][name]=value;save();print('PASS',name,value,flush=True)

    maps=json.loads((GAME/'art/campaign-routes-v1/export.json').read_text())
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def living():return sum(read(syms['enemies'][0]+i*46+44,1)[0]!=0 for i in range(16))
    def isolate():
        zeros('enemies');zeros('pshots');zeros('eshots');w16('spawnTimer',60000)
    def sprite_limits():
        rectangles=[];index=0;base=u16('slist_addr')
        for _ in range(80):
            at=base+index*8;sl=vw(at+2)
            x=(vw(at+6)&511)-128;y=(vw(at)&1023)-128
            ww=(((sl>>10)&3)+1)*8;hh=(((sl>>8)&3)+1)*8
            if x<320 and x+ww>0 and y<224 and y+hh>0:rectangles.append((x,y,ww,hh))
            index=sl&127
            if not index:break
        else:raise AssertionError('SAT link loop or more than80 sprites')
        mostSprites=mostPixels=0
        for row in range(24,224):
            cells=[r for r in rectangles if r[1]<=row<r[1]+r[3]]
            mostSprites=max(mostSprites,len(cells));mostPixels=max(mostPixels,sum(r[2] for r in cells))
        assert mostSprites<=20 and mostPixels<=320,('scanline overflow',mostSprites,mostPixels)
        return len(rectangles),mostSprites,mostPixels
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2);baseline=snapshot()
        def enter(node):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1);until(lambda:state()==1 and not u8('transitioning'),'play');
            isolate();run(fps*4);assert u16('freezeTimer')==0
        import re
        graph=(GAME/'src/levels/graph.h').read_text().split('N_1 = 1,',1)[1].split('NODE_MAX',1)[0]
        node12=(['N_1']+re.findall(r'N_\d+[AB]?',graph)).index('N_12')+1
        for node,key in ((7,'06a'),(8,'06b'),(node12,'12')):
            if key not in wanted_phases:continue
            if args.mechanism_pixels_only and key!='06b':continue
            enter(node);initial=snapshot();d=maps[key];shot(key+'-entrada')
            assert u16('arenaMaxX')==d['bounds'][2] and u16('arenaMaxY')==d['bounds'][3] and u16('arenaMinY')==d['bounds'][1]
            patterns=(GAME/f'res/campaign_routes/{key}/tiles.bin').read_bytes()
            assert struct.unpack('>16H',(GAME/f'res/campaign_routes/{key}/palette.bin').read_bytes())[0]==0,('Genesis transparent palette slot must be black',key)
            assert vr(785*32,len(patterns))==patterns,(key,'scenery atlas')
            if key=='06b':
                bases=read(syms['objectiveArtBases'][0],20)
                assert int.from_bytes(bases[8:10],'big')>=785+len(patterns)//32
                assert int.from_bytes(bases[10:12],'big')>=785+len(patterns)//32
            # Test far-camera ring and static solid mask beyond2048px.
            w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
            cols,rows=d['width']//8,d['height']//8
            rawmap=struct.unpack('>'+str(cols*rows)+'H',(GAME/f'res/campaign_routes/{key}/map.bin').read_bytes())
            for x in (48,2720,1360,48):
                xx,yy=closest(d,x,208,extra=d.get('gates',[]));pos(xx,yy);run(fps*14)
                cx=u16('cameraX')//8;cy=u16('cameraY')//8
                for ty in range(cy,min(cy+28,rows)):
                    for tx in range(cx,min(cx+40,cols)):
                        attr=rawmap[ty*cols+tx];expected=(785+(attr&2047))|(attr&0x1800)
                        assert (vw(0xc000+((ty&31)*64+(tx&63))*2)&0x1fff)==expected,(key,'streaming',tx,ty)
            late=faces(d,[r for r in d['solids'] if r[0]>2048 and r[1]+r[3]>d['bounds'][1]])
            assert late,(key,'no legal late collision face')
            for xx,yy,button,axis,limit,sign in late:
                pos(xx,yy);hold({button},fps//2);value=u16(axis)
                assert value<=limit if sign==1 else value>=limit,(key,'late solid',xx,yy,value,limit)
            check(key+'-bounds-atlas-ring-and-late-collision')
            restore(initial)
            if key=='06b':
                # Probe both compounds with genuine work ticks and player A
                # projectiles; RAM sets only the isolated approach positions.
                isolate();w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
                op=syms['campaignRouteOps'][0]
                objectiveSource=(GAME/'res/objectives/animations.bin').read_bytes()
                def verify_object_pixels(slot):
                    # Compare the displayed complete frame with original art,
                    # independently of deduplicated tile IDs and packing.
                    address=syms['objectiveVisuals'][0]+slot*12
                    anchorX,anchorY=struct.unpack('>hh',read(address,4))
                    art=read(address+6,1)[0];frame=read(address+7,1)[0]
                    assert art in (4,5)
                    width,height,sourceOffset=(4,4,4032*4) if art==4 else (8,8,4800*4)
                    col=(anchorX-width*4)//8;row=(anchorY-height*8+8)//8;checked=0
                    for tx in range(width):
                        for ty in range(height):
                            local=tx*height+ty
                            offset=sourceOffset+(frame*width*height+local)*32
                            expected=objectiveSource[offset:offset+32]
                            if not any(expected):continue
                            attr=vw(u16('bga_addr')+(((row+ty)&31)*64+((col+tx)&63))*2)
                            assert vr((attr&2047)*32,32)==expected,('mechanism pixel mismatch',slot,art,frame,tx,ty,attr&2047)
                            checked+=1
                    assert checked>0
                    return checked
                def verify_gate_pixels(slot,gx,gy):return verify_object_pixels(slot)
                for i,(gate,valve) in enumerate(zip(d['gates'],d['valves'])):
                    gx,gy,_,_=gate;vx,vy=valve
                    pos(*d.get('valve_approaches',[[x-8,y+16] for x,y in d['valves']])[i])
                    run(fps*6)
                    shot(key+'-portao-'+str(i+1)+'-fechado')
                    verify_gate_pixels(i,gx,gy)
                    for workTick in range(fps*5):
                        run()
                        if read(op+10,1)[0]&(1<<i):break
                    assert int.from_bytes(read(op+i*2,2),'big')==(fps*3+1)//2
                    assert read(op+10,1)[0]&(1<<i),(key,'pressure',i,read(op,12).hex())
                    pos(*d.get('gate_shot_approaches',[[x-64,y+16] for x,y,_,_ in d['gates']])[i]);hold({7},2)
                    buttons.clear();buttons.add(1)
                    for shotTick in range(fps*4):
                        run()
                        if read(op+8+i,1)[0]==0:break
                    buttons.clear()
                    assert read(op+8+i,1)[0]==0,(key,'gate',i,read(op,16).hex())
                    address=syms['objectiveVisuals'][0]+i*12
                    clearTicks=int.from_bytes(read(op+12+i*2,2),'big')
                    assert 0<clearTicks<=fps*4//5,('collapse timing not armed',i,clearTicks)
                    sawFinal=False
                    for collapseTick in range(fps):
                        run()
                        visible=bool(read(address+9,1)[0]);frame=read(address+7,1)[0]
                        if visible and frame==5 and not sawFinal:
                            # RAM animation state precedes queued BG_A DMA.
                            # Commit two real VBlanks, then compare every
                            # opaque tile exactly while final pose is visible.
                            run(2)
                            assert read(address+9,1)[0] and read(address+7,1)[0]==5,('final pose lost before DMA commit',i)
                            verify_gate_pixels(i,gx,gy);shot(key+'-portao-'+str(i+1)+'-colapso');sawFinal=True
                        if not visible:break
                    assert sawFinal,('final gate pose never shown before clear',i)
                    assert not read(address+9,1)[0] and int.from_bytes(read(op+12+i*2,2),'big')==0
                    run(2) # The hide background restoration is queued DMA too.
                    anchorX,anchorY=struct.unpack('>hh',read(address,4));col=(anchorX-32)//8;row=(anchorY-56)//8
                    for tx in range(8):
                        for ty in range(8):
                            attr=vw(u16('bga_addr')+(((row+ty)&31)*64+((col+tx)&63))*2)
                            nativeAttr=rawmap[(row+ty)*cols+col+tx]
                            assert (attr&0x1fff)==((785+(nativeAttr&2047))|(nativeAttr&0x1800)),('gate did not restore native support/background',i,tx,ty)
                    check(key+'-gate-'+str(i+1)+'-collapse-then-native-opening',{'finalPoseObserved':True,'delaySeconds':.8,'permanentSpriteVisible':False,'openingPixels':32})
                    assert vr(785*32,len(patterns))==patterns
                    shot(key+'-portao-'+str(i+1)+'-aberto')
                check(key+'-two-valves-and-four-shot-gates')
                before=read(op,12)
                for attempt in range(4):
                    hold({3},8)
                    if state()==2:break
                    run(fps//4)
                if state()==2:
                    run(fps)
                    assert read(op,4)==before[:4] and read(op+8,3)==before[8:11]
                    press(0);until(lambda:state()==1,'gate-resume');run(2)
                    assert read(op,4)==before[:4] and read(op+8,3)==before[8:11]
                    check(key+'-pause-preserves-compound-state')
                else:
                    check(key+'-pause-preserves-compound-state',{'passed':False,'error':'pause does not open after four Start presses; likely PANEL_begin snapshot allocation failure'})
                    report.setdefault('limitations',[]).append('6B pause did not open')

                # Isolated presentation scenario: seed each of the six art
                # poses after the genuine interactions above. A small camera
                # move requests a normal full visual redraw; the real renderer
                # and VDP still perform all tile lookup and DMA operations.
                mechanismY=d['valves'][0][1];poseX,poseY=d.get('gate_shot_approaches',[[944,mechanismY]])[0];pos(poseX,poseY);run(fps*6);poseChecks=[]
                for poseIndex in range(6):
                    for slot in (0,2):
                        address=syms['objectiveVisuals'][0]+slot*12
                        write(address+7,bytes([poseIndex,2,1]))
                    # Alternate two legal positions instead of walking into
                    # the landmark camera clamp. Every raw frame selection
                    # needs a genuine tile-window move to request repaint.
                    xx,yy=closest(d,poseX+(16 if poseIndex%2==0 else 0),poseY);pos(xx,yy);run(16)
                    poseChecks.append({'frame':poseIndex,'gateOpaqueCells':verify_object_pixels(0),'valveOpaqueCells':verify_object_pixels(2)})
                    assert vr(785*32,len(patterns))==patterns
                    shot('06b-mecanismos-pose-'+str(poseIndex))
                check('06b-all-six-mechanism-frames-exact',{'poses':poseChecks,'isolatedRamFrameSelection':True,'renderingAndDma':'production','sceneryAtlasPreserved':True})
                if args.mechanism_pixels_only:
                    report['passed']=not report.get('limitations');save();return

            # Real insect contact triggers Dinorah's death and its route.
            # It works beside projected walls too: a bullet seeded at the
            # same foot may correctly hit the wall16px above it first.
            restore(initial);isolate();w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',0);w16('dinorahHp',1);pos(*closest(d,320,208))
            seed(0,4,u16('dinorahX'),u16('dinorahY'),health=200,fire=60000)
            run(fps*3)
            assert state()==(4 if key=='12' else 3),(key,'death outcome',state())
            if key=='12':assert read(syms['phaseStats'][0]+8,1)[0] and u16('hp')>0
            check(key+'-escort-death-outcome',{'state':state(),'objectiveFailed':bool(read(syms['phaseStats'][0]+8,1)[0]),'expected':'continue13B' if key=='12' else 'restart','trigger':'real insect contact'})
            restore(initial);isolate();w16('hp',0);w16('dinorahHp',0);run(fps*4)
            assert state()==3,(key,'simultaneous defeat priority',state())
            check(key+'-player-death-priority')
            # A full traversal isolates combat and gate opening, then enforces
            # controller-only movement until both actors reach the destination.
            restore(initial);isolate();w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
            if key=='06b':
                write(syms['campaignRouteOps'][0]+8,bytes([0,0,3]))
                for slot in (0,1):write(syms['objectiveVisuals'][0]+slot*12+9,b'\0')
            if args.movie:
                encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb565le','-s','320x224','-r',str(fps),'-i','-','-an','-vf','scale=640:448:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(key+'-traversal.mp4'))],stdin=subprocess.PIPE);record=True
            ordinary=True;playerNode=1;ticks=0;seen=set();writesBefore=writes;middleCaptured=False;exitCaptured=False
            while state()==1 and ticks<fps*180:
                nodeIndex=u8('dinorahNode');seen.add(u8('dinorahState'))
                target=d['points'][min(playerNode,len(d['points'])-1)]
                dx=target[0]-8-u16('px');dy=target[1]-8-u16('py')
                ax=target[0]-8-u16('dinorahX');ay=target[1]-8-u16('dinorahY')
                buttons.clear()
                if abs(dx)<=3 and abs(dy)<=3 and nodeIndex>playerNode:playerNode+=1
                if abs(dx)+abs(dy)>=abs(ax)+abs(ay)-32 or nodeIndex>=len(d['points']):
                    if abs(dx)>3:buttons.add(7 if dx>0 else 6)
                    if abs(dy)>3:buttons.add(5 if dy>0 else 4)
                run();ticks+=1
                if not middleCaptured and u16('px')>=1400:
                    shot(key+'-meio');middleCaptured=True
                    # Native palette index0 can be valid black in an atlas
                    # while rendering transparent on BG_B. Probe the actual
                    # displayed dry floor below both actors, not only VRAM.
                    displayed=rgb();cy=u16('cameraY');cx=u16('cameraX');tested=black=0
                    palette=struct.unpack('>16H',(GAME/f'res/campaign_routes/{key}/palette.bin').read_bytes())
                    for worldY in range(cy+176,cy+184):
                        screenY=worldY-cy
                        for screenX in range(8,312):
                            worldX=cx+screenX
                            if any(abs(worldX-u16(actor))<32 for actor in ('px','dinorahX')):continue
                            tile=rawmap[(worldY//8)*cols+worldX//8]
                            localX=worldX%8;localY=worldY%8
                            if tile&0x800:localX=7-localX
                            if tile&0x1000:localY=7-localY
                            byte=patterns[(tile&2047)*32+localY*4+localX//2]
                            color=(byte&15) if localX&1 else byte>>4
                            if palette[color]==0:continue
                            value=displayed[(screenY*w+screenX)*3:(screenY*w+screenX+1)*3]
                            tested+=1;black+=max(value)<=4
                    assert tested>1600 and black/tested<.01,(key,'transparent floor pixels',black,tested)
                    report['checks'][key+'-displayed-floor-transparency']={'testedPixels':tested,'unexpectedBlackPixels':black,'fraction':round(black/tested,6)}
                    save()
                if not exitCaptured and u16('px')>=d['points'][-1][0]-72:
                    shot(key+'-saida');exitCaptured=True
            ordinary=False;buttons.clear()
            if args.movie:
                record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
            assert middleCaptured and exitCaptured,(key,'missing middle/exit captures',state(),u16('px'),u16('py'),u8('dinorahNode'))
            assert writes==writesBefore
            assert state()==4,(key,'route stuck',ticks,u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))
            assert u16('dinorahHp')==100 and not read(syms['phaseStats'][0]+8,1)[0]
            shot(key+'-chegada');check(key+'-full-controller-traversal',{'seconds':round(ticks/fps,2),'hp':u16('dinorahHp'),'states':sorted(seen),'combatDisabled':True,'gateOpenScenario':key=='06b','ramWritesDuringTraversal':False})
            # Stress uses explicit RAM setup to hold3/4/8/16 active insects
            # and6 projectiles in each group; it is not an ordinary match.
            metrics=[]
            stageRoster={'06a':[4,5],'06b':[4,5,7],'12':[4,5,2]}[key]
            for count,shotCount in ((3,4),(3,6),(4,6),(8,6),(16,6)):
                restore(initial);isolate();w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
                def arrange():
                    w16('hp',100);w16('spawnTimer',60000)
                    for i in range(count):seed(i,stageRoster[i%len(stageRoster)],80+i%4*48,200+i//4*24,200,60000)
                    for name in ('pshots','eshots'):
                        for i in range(shotCount):
                            buf=bytearray(20);struct.pack_into('>iiii',buf,0,(80+i%3*64)<<6,(216+i//3*32)<<6,24,0);buf[17]=1;buf[18]=1
                            write(syms[name][0]+i*20,buf)
                for _ in range(30):arrange();run()
                begin=frames();vb=u32('vtimer');loads=[];peaks=[];spritePeaks=[0,0,0]
                for _ in range(fps*3):
                    arrange();run();loads.append(u16('cpuFrameLoad')*100/2048);peaks.append(living())
                    spritePeaks=[max(a,b) for a,b in zip(spritePeaks,sprite_limits())]
                game=frames()-begin;physical=u32('vtimer')-vb
                metrics.append({'forcedEnemies':count,'enemyRoster':stageRoster,'peakActive':max(peaks),'gameFPS':round(fps*game/max(1,physical),2),'meanCPULoadPct':round(statistics.mean(loads),2),'p95CPULoadPct':round(sorted(loads)[int(len(loads)*.95)],2),'playerShots':shotCount,'enemyShots':shotCount,'ramSetupEveryFrame':True,'peakVisibleSprites':spritePeaks[0],'busiestScanlineSprites':spritePeaks[1],'busiestScanlinePixels':spritePeaks[2]})
            check(key+'-stress',metrics)
            # Ordinary stationary defense reveals actual production cap and
            # exposes difficulty; no health, enemy or projectile RAM updates.
            restore(initial);w16('spawnTimer',fps*d['spawn']);ordinary=True;begin=frames();vb=u32('vtimer');peak=0;ticks=0
            if args.movie:
                encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb565le','-s','320x224','-r',str(fps),'-i','-','-an','-vf','scale=640:448:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(key+'-combat.mp4'))],stdin=subprocess.PIPE);record=True
            buttons.add(1)
            while state()==1 and ticks<fps*45:
                run();ticks+=1;peak=max(peak,living())
            ordinary=False;buttons.clear()
            if args.movie:
                record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
            shot(key+'-defesa-sem-movimento')
            check(key+'-ordinary-stationary-defense',{'seconds':round(ticks/fps,2),'state':state(),'playerHP':u16('hp'),'dinorahHP':u16('dinorahHp'),'peakEnemies':peak,'gameFPS':round(fps*(frames()-begin)/max(1,u32('vtimer')-vb),2),'ramWrites':False,'limitation':'stationary shooting probe, not a completed combat escort'})
        report['passed']=not report.get('limitations');save()
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:
        if encoder is not None:
            record=False;encoder.stdin.close();encoder.wait()
        core.retro_unload_game();core.retro_deinit()
if __name__=='__main__':main()
