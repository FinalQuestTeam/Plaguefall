"""Actual Genesis Plus GX ROM checks; run with arch -x86_64 /usr/bin/python3.

Controller entry/movement/pause/bomb/transition are real. Stress formations,
HP and counters are held in volatile emulator RAM, not patched into the ROM.
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
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=6);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/phase01-courtyard-v2/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    def write(addr,value):
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
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    def safe():
        w16('hp',100);w16('spawnTimer',60000);w16('kills',0)
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
    layout=json.loads((GAME/'res/actor_animation.json').read_text())
    muzzle=json.loads((GAME/'res/heroi/muzzle.json').read_text())
    source_poses=layout['idle_source_poses']+layout['run_source_poses']
    canonical=(0,1,2,3,4,3,2,1)
    def barrel():
        direction=u8('loadedDir');pose=u8('loadedPose')
        x,y=muzzle[layout['canonical_directions'][canonical[direction]]][str(source_poses[pose])]
        if direction>4:x=32-x
        return u16('px')-8+x,u16('py')-31+y
    # Exercise the reported wall case with every idle/run frame. Compare the
    # simulated origin with the barrel AND verify the displayed VRAM frame/SAT.
    actor_frames=(GAME/'res/heroi/frames.bin').read_bytes()
    muzzle_cases=0;hardware_muzzle_cases=0;coverage={};wall_shots=[];barrel_wall_hits=0
    for side,x in (('left',16),('right',480)):
        for direction,key in ((0,4),(4,5)):
            for moving in (False,True):
                restore(baseline);safe();pos(x,240);settle()
                hold({key},1);run(5)
                seen=set()
                for tick in range(fps*3//4 if moving else fps):
                    write(syms['pshots'][0],bytes(syms['pshots'][1]));w16('shotCooldown',0)
                    buttons.clear();buttons.add(1)
                    if moving:buttons.add(key)
                    run()
                    assert u8('loadedDir')==direction
                    pose=u8('loadedPose');seen.add(pose)
                    bx,by,vx,vy=struct.unpack('>iiii',read(syms['pshots'][0],16))
                    visible=(bx//64+1,by//64-16+1)
                    blocked=not (16<=visible[0]<=490 and 96<=visible[1]<=362)
                    active=bool(read(syms['pshots'][0]+18,1)[0])
                    assert active!=blocked,('vertical shot incorrectly blocked at wall',side,direction,moving,pose,u16('px'),u16('py'),visible)
                    barrel_wall_hits+=int(blocked)
                    origin=((bx-vx)//64+4,(by-vy)//64-16+4)
                    assert origin==barrel(),('barrel origin mismatch',side,direction,moving,pose,origin,barrel())
                    sat=u16('slist_addr');attr=vw(sat+4);tile=attr&2047
                    assert (attr>>13)&3==2 and not attr&0x1800
                    actual=bytes(vram[(tile*32+i)^1] for i in range(768))
                    displayed=[p for p in range(6) if actual==actor_frames[(canonical[direction]*6+p)*768:(canonical[direction]*6+p+1)*768]]
                    assert len(displayed)==1,('invalid displayed hero frame',side,direction,pose)
                    # The core may stop before the next queued VBlank DMA.
                    # Compare hardware bullet + hardware hero from that same
                    # displayed frame, independently of the newer RAM state.
                    if tick and (vw(sat+18)>>8)&15==0:
                        hx,hy=(vw(sat+6)&511)-128,(vw(sat)&511)-128
                        bx,by=(vw(sat+22)&511)-128,(vw(sat+16)&511)-128
                        displayed_origin=(bx+4-(vx//64)-hx,by+4-(vy//64)-hy)
                        anchor=tuple(muzzle[layout['canonical_directions'][canonical[direction]]][str(source_poses[displayed[0]])])
                        assert displayed_origin==anchor,('displayed barrel mismatch',side,direction,moving,displayed[0],displayed_origin,anchor)
                        hardware_muzzle_cases+=1
                    muzzle_cases+=1
                    if not moving and pose==0 and tick==1:
                        name='13-muzzle-'+side+('-up' if direction==0 else '-down');shot(name)
                        wall_shots.append({'side':side,'direction':direction,'origin':origin,'screenshot':name+'.png'})
                buttons.clear()
                required=set(range(2,6)) if moving else {0,1}
                assert required<=seen,(side,direction,moving,seen)
                coverage[side+('-up' if direction==0 else '-down')+('-run' if moving else '-idle')]=sorted(seen)
    restore(baseline);safe()
    safe()
    # Projectiles share the same solid footprints; distant shots cannot
    # overflow the 68000's 16-bit circle test and damage across the map.
    pos(40,160)
    bullet=bytearray(20);struct.pack_into('>iiii',bullet,0,450<<6,240<<6,0,0);bullet[17]=10;bullet[18]=1
    write(syms['eshots'][0],bullet);run(2);assert u16('hp')==100
    struct.pack_into('>iiii',bullet,0,488<<6,180<<6,128,0)
    write(syms['pshots'][0],bullet);run(3);assert read(syms['pshots'][0]+18,1)==b'\0'
    write(syms['eshots'][0],bytes(20));pos(256,160);run(2)
    if args.movie:
        encoder=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(av.timing.fps),'-i','pipe:0','-vf','scale=960:672:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/'video.mp4')],stdin=subprocess.PIPE)
        audio=wave.open(str(out/'audio.wav'),'wb');audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate));record=True
    # Walk the real boundaries and foreground objects with controller input.
    hold({6},140);left=u16('cameraX');shot('02-esquerda')
    hold({7},210);right=u16('cameraX');shot('03-direita')
    hold({5},140);shot('04-muro-inferior')
    assert u16('py')==352 and u16('cameraY')==160
    hold({6},232);hold({4},180);top=u16('cameraY');shot('05-igreja')
    assert left==0 and right==192,(left,right)
    assert top==0
    # HUD row remains pixel-identical when just the world camera moves.
    def hud_pixels():return b''.join(raw[y*pitch:y*pitch+640] for y in range(8))
    safe();pos(224,160);settle();hud=hud_pixels();assert any(hud)
    pos(352,320);settle();assert hud_pixels()==hud,'HUD background/icons are transparent or scrolling'
    safe();pos(240,160);hold({4},100);assert u16('py')==112,('upper wall',u16('py'))
    safe();pos(400,160);hold({7},70);assert u16('px')==480,('right wall',u16('px'))
    safe();pos(240,264);press(3);shot('06-pausa');press(3);run(5)
    assert u16('cameraX')==88 and u8('arenaActive')==1
    # A real firing sequence with the normal AI/spawn logic; only HP is held.
    safe();w16('spawnTimer',1);combat_begin=u32('vtimer');game_begin=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    max_enemies=max_player=max_enemy=0
    buttons.add(1)
    for tick in range(24*fps):
        w16('hp',100);w16('kills',0)
        for key in (4,5,6,7):buttons.discard(key)
        buttons.add((7,5,6,4)[tick//(3*fps)%4]);run()
        max_enemies=max(max_enemies,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
        for name in ('pshots','eshots'):
            count=sum(read(syms[name][0]+i*20+18,1)[0]!=0 for i in range(16))
            if name=='pshots':max_player=max(max_player,count)
            else:max_enemy=max(max_enemy,count)
    buttons.clear();run(2);shot('06b-combate')
    normal_fps=fps*(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-game_begin)/(u32('vtimer')-combat_begin)
    assert max_enemies<=4 and max_player<=6 and max_enemy<=6
    assert normal_fps>=fps*.99,normal_fps
    safe();pos(128,144);run(3)
    safe();press(0);run(20);assert u8('arenaDamaged')==1;shot('07-igreja-danificada')
    press(3);press(3);run(3);assert u8('arenaDamaged')==1
    if args.movie:
        record=False;encoder.stdin.close();encoder.wait();audio.close()
        assert encoder.returncode==0
        subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-i',str(out/'video.mp4'),'-i',str(out/'audio.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(out/'fase01.mp4')],check=True)
    # Sweep the whole new floor, including the old invisible lower obstacles.
    # RAM positioning isolates a location; movement/fire still use the pad.
    restore(baseline);safe();grid_moves=grid_shots=0
    for y in range(128,353,32):
        for x in range(32,465,32):
            for key,dx,dy in ((6,-1,0),(7,1,0),(4,0,-1),(5,0,1)):
                pos(x,y);hold({key},2)
                assert (u16('px'),u16('py'))==(max(16,min(480,x+4*dx)),max(112,min(352,y+4*dy))),('invisible movement solid',x,y,key,u16('px'),u16('py'))
                grid_moves+=1
                write(syms['pshots'][0],bytes(syms['pshots'][1]));w16('shotCooldown',0)
                buttons.add(1);run()
                mx,my=barrel();sx,sy=mx-4,my-4
                clear=all(16<=sx+dx*3*n<=488 and 96<=sy+dy*3*n<=360 for n in (1,2,3,4))
                buttons.clear();run(3)
                if clear:
                    assert any(read(syms['pshots'][0]+i*20+18,1)[0] for i in range(6)),('shot vanished on clear floor',x,y,key)
                    grid_shots+=1
    # The VDP ring must match the exported map after crossing and revisiting
    # y=256. Sample background pixels outside the actor/HUD, not a mock render.
    tiles=(GAME/'res/courtyard/tiles.bin').read_bytes();tilemap=(GAME/'res/courtyard/map.bin').read_bytes();palette=struct.unpack('>16H',(GAME/'res/courtyard/palette.bin').read_bytes())
    sampled=0
    for y in (112,160,224,288,352,224,112,352):
        safe();write(syms['pshots'][0],bytes(syms['pshots'][1]));pos(256,y);settle()
        for sy in (40,72,160,208):
            wy=sy+u16('cameraY')
            if not 128<=wy<368:continue
            for sx in (24,56,264,296):
                wx=sx+u16('cameraX');tile=struct.unpack_from('>H',tilemap,((wy//8)*64+wx//8)*2)[0]
                packed=tiles[tile*32+(wy%8)*4+(wx%8)//2];index=packed>>4 if wx%2==0 else packed&15
                color=palette[index];r,g,b=[((color>>shift)&7)*34 for shift in (1,5,9)]
                expected=struct.pack('<H',((r>>3)<<11)|((g>>2)<<5)|(b>>3))
                actual=raw[sy*pitch+sx*2:sy*pitch+sx*2+2]
                if actual!=expected:
                    shot('ring-mismatch')
                    offset=(((wy//8)&31)*64+wx//8)*2
                    bga=vw(u16('bga_addr')+offset);bgb=vw(u16('bgb_addr')+offset)
                    raise AssertionError(('ring tile mismatch',wx,wy,'camera',u16('cameraX'),u16('cameraY'),'tile',tile,'index',index,'palette',hex(color),'actual',actual.hex(),'expected',expected.hex(),'planes',hex(bga),hex(bgb),'tiledata',bytes(vram[((785+tile)*32+i)^1] for i in range(32)).hex(),tiles[tile*32:tile*32+32].hex()))
                sampled+=1
    shot('11-patio-amplo')
    # Both actual lower corners and the central gate must match the exported
    # map, including the last visible scanline after the VDP ring wraps.
    corner_checks=0
    for damaged in (False,True):
        restore(baseline);safe()
        if damaged:press(0);run(20)
        for x in (16,480):
            pos(x,352);settle()
            shot('14-bottom-'+('left' if x==16 else 'right')+('-damaged' if damaged else ''))
            # Exclude Damião's last body row and the foot shadow at y368..371.
            points={(wx,wy) for wx in (range(24) if x==16 else range(488,512)) for wy in range(372,384)}
            points|={(wx,wy) for wx in (range(8) if x==16 else range(504,512)) for wy in range(344,372)}
            for wx,wy in sorted(points):
                sx,sy=wx-u16('cameraX'),wy-u16('cameraY')
                tile=struct.unpack_from('>H',tilemap,((wy//8)*64+wx//8)*2)[0]
                packed=tiles[tile*32+(wy%8)*4+(wx%8)//2];index=packed>>4 if wx%2==0 else packed&15
                color=palette[index];r,g,b=[((color>>shift)&7)*34 for shift in (1,5,9)]
                expected=struct.pack('<H',((r>>3)<<11)|((g>>2)<<5)|(b>>3))
                assert raw[sy*pitch+sx*2:sy*pitch+sx*2+2]==expected,('bottom corner mismatch',damaged,wx,wy)
                corner_checks+=1
    # Multiple complete attempts with ordinary spawn/AI/HP/drops. No game RAM
    # is written during these matches; only joypad input and initial savestate.
    matches=[];bullet_checks=0
    def active_enemies():
        return [struct.unpack('>hh',read(enemy_addr+i*stride,4)) for i in range(16) if read(enemy_addr+i*stride+44,1)[0]]
    def player_bullets():
        return [struct.unpack('>iiii',read(syms['pshots'][0]+i*20,16)) if read(syms['pshots'][0]+i*20+18,1)[0] else None for i in range(16)]
    for trial in range(args.matches):
        restore(baseline);last_bomb=-100*fps;pauses=0;paused_frames=0;lastpos=None;walk=0;start_v=u32('vtimer');start_frames=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
        if args.movie and trial==1:
            encoder=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(av.timing.fps),'-i','pipe:0','-vf','scale=960:672:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/'partida-video.mp4')],stdin=subprocess.PIPE)
            audio=wave.open(str(out/'partida-audio.wav'),'wb');audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate));record=True
        prior_enemies=active_enemies();prior_bullets=player_bullets()
        for tick in range(120*fps):
            state=u32('flow_state')
            if state in (3,4):break
            assert state==1,('unexpected match state',trial,state)
            ax,ay=u16('px'),u16('py');assert 16<=ax<=480 and 112<=ay<=352,(trial,'player outside',ax,ay)
            current=active_enemies()
            for ex,ey in current:assert 16<=ex<=480 and 112<=ey<=352,(trial,'enemy outside',ex,ey)
            keys={1}
            if current:
                ex,ey=min(current,key=lambda p:abs(p[0]-ax)+abs(p[1]-ay));dx,dy=ex-ax,ey-ay
                if abs(dx)+abs(dy)<40:
                    # Retreat before the muzzle would overlap the enemy.
                    if abs(dx)>abs(dy):keys.add(6 if dx>0 else 7)
                    else:keys.add(4 if dy>0 else 5)
                elif abs(dx)>6 and abs(dy)>6:
                    # Align a cardinal lane instead of charging into contact.
                    if abs(dx)>abs(dy):keys.add(5 if dy>0 else 4)
                    else:keys.add(7 if dx>0 else 6)
                else:
                    desired=(1 if dx>0 else -1,0) if abs(dx)>abs(dy) else (0,1 if dy>0 else -1)
                    facing=tuple(int.from_bytes(read(syms[n][0],2),'big',signed=True) for n in ('faceX','faceY'))
                    if facing!=desired:keys.add(7 if desired[0]>0 else 6 if desired[0]<0 else 5 if desired[1]>0 else 4)
            else:keys.add((7,5,6,4)[(tick//fps+trial)%4])
            if trial%2 and current and tick>15*fps and tick-last_bomb>20*fps and u16('bombs'):
                keys.add(0);last_bomb=tick
            buttons.clear();buttons.update(keys);run()
            now_enemies=active_enemies();now_bullets=player_bullets()
            if u32('flow_state')==1:
                for before,after in zip(prior_bullets,now_bullets):
                    if before is None or after is not None:continue
                    bx,by,vx,vy=before;bx=(bx+vx)>>6;by=(by+vy)>>6
                    wall=not (15<=bx<=489 and 95<=by-16<=361)
                    hit=any(bx<ex+20 and bx+12>ex and by<ey+20 and by+12>ey for ex,ey in prior_enemies+now_enemies)
                    assert wall or hit,('unexplained shot disappearance',trial,tick,bx,by,current)
                    bullet_checks+=1
            prior_enemies,prior_bullets=now_enemies,now_bullets
            newpos=(u16('px'),u16('py'))
            if lastpos and newpos!=lastpos:walk+=1
            lastpos=newpos
            if tick==18*fps:
                pause_v=u32('vtimer');pause_f=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
                buttons.clear();press(3);assert u32('flow_state')==2;press(3);assert u32('flow_state')==1;pauses+=1
                paused_frames+=u32('vtimer')-pause_v-(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-pause_f)
                prior_enemies,prior_bullets=active_enemies(),player_bullets()
        buttons.clear();state=u32('flow_state');elapsed=u32('vtimer')-start_v
        frames=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-start_frames
        result={'attempt':trial+1,'result':{3:'defeat',4:'victory'}.get(state,'timeout'),'physical_seconds':round(elapsed/fps,2),'game_fps':round(fps*frames/(elapsed-paused_frames),2),'kills':u16('kills'),'remaining_hp':int.from_bytes(read(syms['hp'][0],2),'big',signed=True),'bombs_used':int.from_bytes(read(syms['phaseStats'][0],2),'big'),'moving_frames':walk,'pause_resume_cycles':pauses,'game_ram_writes':False}
        matches.append(result);print('match:',json.dumps(result),flush=True)
        if args.movie and trial==1:
            run(2*fps) # keep the actual victory/defeat message readable
            record=False;encoder.stdin.close();encoder.wait();audio.close();assert encoder.returncode==0
            subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-i',str(out/'partida-video.mp4'),'-i',str(out/'partida-audio.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(out/'partida-completa.mp4')],check=True)
        assert state in (3,4),('match did not conclude',result)
        shot('12-partida-'+str(trial+1))
    if matches:assert any(m['result']=='victory' for m in matches),matches
    restore(baseline);safe()
    # Benchmark real game ticks vs physical VBlanks, including camera movement.
    def stage(count,tick,projectiles):
        phase=tick%224
        safe();w16('freezeTimer',0);pos(224+tick%80,128+2*(phase if phase<112 else 224-phase))
        for i in range(count):
            x=56+(i%6)*60;y=112+(i//6)*40
            buf=bytearray(46);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,32,0,600,600)
            buf[30]=i%2;buf[31]=20;buf[43]=1;buf[44]=1;write(enemy_addr+i*stride,buf)
        for name in ('pshots','eshots'):
            addr,size=syms[name];assert size//16==20
            for i in range(16):
                buf=bytearray(20)
                if i<projectiles:struct.pack_into('>iiii',buf,0,(64+i%8*44)<<6,(128+i//8*48)<<6,32,0);buf[17]=1;buf[18]=1
                write(addr+i*20,buf)
    cases=[]
    for count,projectiles in [(0,0),(3,0),(4,6),(6,4),(6,6),(8,0),(8,16),(15,16)]:
        for tick in range(90):stage(count,tick,projectiles);run()
        begin=int.from_bytes(read(syms['phaseStats'][0]+4,4),'big');vbegin=u32('vtimer');loads=[]
        for tick in range(90,390):stage(count,tick,projectiles);run();loads.append(u16('cpuFrameLoad')*100/2048)
        drawn=(int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')-begin)&0xffffffff;elapsed=u32('vtimer')-vbegin
        cases.append({'enemies':count,'shots_per_pool':projectiles,'physical_frames':elapsed,'game_frames':drawn,'fps':round(fps*drawn/elapsed,2),'cpu_mean_pct':round(statistics.mean(loads),2),'cpu_p95_pct':round(sorted(loads)[int(len(loads)*.95)],2)})
    configured=next(c for c in cases if c['enemies']==4 and c['shots_per_pool']==6)
    assert configured['fps']>=fps*.99,configured
    # Exercise both real graph exits; only the kill counter is accelerated.
    routes=[]
    for bomb,target,track in ((False,2,3),(True,3,1)):
        restore(baseline);safe()
        if bomb:press(0);run(20)
        assert u8('arenaDamaged')==int(bomb)
        w16('kills',10);run(4*fps)
        assert u8('pendingLevel')==target,(bomb,u8('pendingLevel'))
        assert not u8('arenaActive') and u16('cameraX')==0
        shot('08-rota-'+('2B' if bomb else '2A'))
        press(1);run(fps);shot('09-dialogo-'+('2B' if bomb else '2A'))
        assert read(syms['music'][0]+33,1)[0]==track
        press(3);run(fps);press(1);run(4*fps)
        assert u8('currentLevel')==target and u8('arenaActive')
        assert u16('arenaMinX')==16 and u16('arenaMaxX')==495 and u16('cameraX')==0
        shot('10-fase-'+('2B' if bomb else '2A'))
        routes.append({'bomb_used':bomb,'next_node':target,'music_track':track})
    export=json.loads((GAME/'art/phase01-courtyard-v2/export.json').read_text())
    report={'passed':True,'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),'world':[512,384],
            'camera_limits':[left,right],'hud_fixed':True,'player_solid_collisions':True,'projectile_solid_collisions':True,'distant_shots_do_not_hit':True,'pause_restores_scene':True,'bomb_damages_church':True,'damaged_state_survives_pause':True,'next_custom_stage_loaded':True,
            'scene_tiles':export['tiles'],'scene_tile_bytes':export['tile_bytes'],'level_enemy_cap':4,'shots_per_pool_cap':6,'benchmark':cases,'routes':routes,'hud_icons_opaque':True,'floor_move_cases':grid_moves,'clear_floor_shot_cases':grid_shots,'ring_pixel_checks':sampled,'natural_matches':matches,'explained_shot_disappearances':bullet_checks,'unexplained_shot_disappearances':0,'walkable_bounds':[16,112,495,367],'camera_y_limits':[0,160],
            'natural_combat':{'seconds':24,'fps':round(normal_fps,2),'max_enemies':max_enemies,'max_player_shots':max_player,'max_enemy_shots':max_enemy},
            'barrel_origin_cases':muzzle_cases,'hardware_barrel_cases':hardware_muzzle_cases,'barrel_frame_coverage':coverage,'wall_barrel_screenshots':wall_shots,'barrel_inside_wall_hits':barrel_wall_hits,'bottom_corner_pixel_checks':corner_checks,
            'method':'Real ROM in Genesis Plus GX. Controller-driven entry/movement/pause/bomb; stress formations and HP held in volatile RAM; game-active frame counter compared with vtimer, not host emulation speed.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
