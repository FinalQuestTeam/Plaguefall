"""Campaign stages in the FINAL production ROM. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
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
    out=args.output or GAME/'art/phases02-06-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    names={2:'phase02a-service-v1',3:'phase02b-detour-v1',4:'phase03-shelter-v1',5:'phase04-tunnels-v1',6:'phase05-beacon-v1',7:'phase06a-rescue-v1',8:'phase06b-withdrawal-v1'}
    tracks={2:3,3:1,4:1,5:2,6:3,7:1,8:2}
    installation=json.loads((GAME/'art/phases02-06-v1/integration-export.json').read_text())
    installed={s['id'].upper():s for s in installation['stages']}
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),
            'emulated_rom_sha256':hashlib.sha256(data).hexdigest(),'production_rom':str(rom),'temporary_build':False,
            'region_header_override_in_memory_only':args.pal,'core_fps':av.timing.fps,'stages':[], 'failures':[],
            'method':'Controller enters phase 1. Kills and pendingLevel are accelerated only in node setup. All ordinary attempts restore a node baseline then enable an enforced RAM-write guard. Isolated probes/stress explicitly use RAM setup. FPS = region_fps * phaseStats.frames / vtimer VBlanks.'}
    def save_report():
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(label,fn,results):
        try:
            value=fn();results[label]={'passed':True,'details':value};print('PASS',label,flush=True);return value
        except Exception as exc:
            detail={'passed':False,'error':repr(exc)};results[label]=detail;report['failures'].append({'check':label,'error':repr(exc)})
            print('FAIL',label,repr(exc),flush=True);shot('FAIL-'+label.replace('/','-'));save_report();return None
    def state():return u32('flow_state')
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def clear_enemies():
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
    def isolate():
        w16('spawnTimer',60000);clear_enemies()
        for name in ('pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
    def enter(node):
        restore(baseline);isolate();w16('kills',10);run(4*fps)
        assert state() in (5,6),('phase1 exit',state())
        for _ in range(40):
            if state()==1 and u8('currentLevel')==node:break
            assert state()!=3,('setup died',node)
            write(syms['pendingLevel'][0],bytes([node]));press(1);run(fps//4)
            if state()==6:press(3);run(fps//4)
        else:raise AssertionError(('node entry failed',node,state(),u8('currentLevel')))
        run(3*fps+4)
        assert state()==1 and u8('currentLevel')==node
        return snapshot()
    def enemies():
        result=[]
        for i in range(16):
            address=enemy_addr+i*stride
            if read(address+44,1)[0]:
                x,y=struct.unpack('>hh',read(address,4));kind=read(address+30,1)[0]
                result.append((x,y,kind))
        return result
    def formation(d,count=4,shots=6,tick=0,axis='horizontal'):
        isolate();w16('hp',100);w16('kills',0);w16('freezeTimer',0)
        if 'surviveLeft' in syms:w16('surviveLeft',60*fps)
        if 'npcHp' in syms:w16('npcHp',100)
        left,top,width,height=d['walkable'];right,bottom=left+width-16,top+height-16
        def triangle(lo,hi):
            span=hi-lo;t=(tick*3)%(span*2);return lo+(t if t<=span else 2*span-t)
        pos(triangle(left,right) if axis=='horizontal' else (left+right)//2,
            triangle(top,bottom) if axis=='vertical' else (top+bottom)//2)
        for i in range(count):
            x=left+32+(i%2)*max(48,width-96);y=top+24+(i//2)*max(32,height-80)
            buf=bytearray(stride);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,32,0,600,600)
            buf[30],buf[31],buf[43],buf[44]=i%2,20,1,1;write(enemy_addr+i*stride,buf)
        for name in ('pshots','eshots'):
            address,size=syms[name];assert size==320
            for i in range(shots):
                buf=bytearray(20);struct.pack_into('>iiii',buf,0,(left+24+i%3*48)<<6,(top+24+i//3*40)<<6,32,0)
                buf[17],buf[18]=1,1;write(address+i*20,buf)
    def terrain_center(rect):
        x,y,rw,rh=rect;return x+min(16,rw//2)-8,y+min(16,rh//2)-8
    def overlapping(x,y,rect,size=16):
        a,b,c,e=rect;return x<a+c and x+size>a and y<b+e and y+size>b
    def free(d,x,y):
        a,b,c,e=d['walkable']
        if not(a<=x<=a+c-16 and b<=y<=b+e-16):return False
        return not any(overlapping(x,y,r['rect'] if isinstance(r,dict) else r) for r in d['solids']+d['hazards'])
    def dry_route(d):
        from collections import deque
        start=tuple(d['start']);goal=tuple(d['exit']);todo=deque([start]);parents={start:None}
        while todo:
            p=todo.popleft()
            if p==goal:break
            x,y=p
            for q in [(x+8,y),(x-8,y),(x,y+8),(x,y-8)]:
                if q not in parents and free(d,*q):parents[q]=p;todo.append(q)
        assert goal in parents
        route=[];p=goal
        while p is not None:route.append(p);p=parents[p]
        return list(reversed(route))
    stage_baselines={}
    for node in [int(n) for n in args.nodes.split(',')]:
        stage=GAME/'art'/names[node];d=json.loads((stage/'design.json').read_text());ex=json.loads((stage/'export.json').read_text())
        runtime=installed[d['id'].upper()];resource=GAME/'res/stages'/d['id'].lower()
        d['solids']=runtime['solids'];ex.update(glow_start=runtime['glow_start'],glow_count=runtime['glow_count'],tiles=runtime['tile_count'])
        result={'node':node,'id':d['id'],'world':[d['width'],d['height']],'isolated_probes':{},'ordinary_matches':[]};report['stages'].append(result)
        initial=enter(node);stage_baselines[node]=initial;shot(d['id']+'-entry')
        left,top,width,height=d['walkable'];right,bottom=left+width-16,top+height-16
        def entry_probe():
            assert u8('arenaActive') and u16('arenaMinX')==left and u16('arenaMinY')==top and u16('arenaMaxX')==right+15 and u16('arenaMaxY')==bottom+15
            assert read(syms['music'][0]+33,1)[0]==tracks[node],('music',read(syms['music'][0]+33,1)[0],tracks[node])
            return {'music_track':tracks[node],'bounds':[left,top,right,bottom],'setup':'phase1 kill counter + pendingLevel override; normal startPhase and countdown'}
        check(d['id']+'/entry',entry_probe,result['isolated_probes'])
        if args.only_entry:save_report();continue
        def hardware_probe():
            nonlocal record,encoder
            restore(initial);isolate();pos(*d['start']);settle()
            atlas=(resource/'tiles.bin').read_bytes();uploaded=bytes(vram[(781*32+i)^1] for i in range(len(atlas)))
            glow_start=ex.get('glow_start',ex.get('glowStart'));glow_count=ex.get('glow_count',ex.get('glowCount',0))
            # Base data may currently be a glow animation frame. Every byte
            # outside the declared range must still match its exact atlas.
            if glow_start is not None and glow_count:
                lo,hi=int(glow_start)*32,(int(glow_start)+int(glow_count))*32
                assert uploaded[:lo]==atlas[:lo] and uploaded[hi:]==atlas[hi:]
            else:assert uploaded==atlas,'VRAM atlas differs from final level export'
            # HUD clones use a fixed 640-tile scene reservation, independent
            # of the current scene's shorter atlas. Read the actual skull or
            # clock WINDOW attribute instead of guessing from tileCount.
            icon_attr=vw(u16('window_addr')+(7 if node==6 else 1)*2)
            icon_tile=icon_attr&2047
            icon_base=icon_tile-(7 if node==6 else 0)
            assert icon_base==781+640,('HUD clone base',icon_base,icon_attr)
            icons=bytes(vram[(icon_base*32+i)^1] for i in range(11*32))
            assert all(v>>4 and v&15 for v in icons),'HUD icons contain transparent pixels'
            font=(GAME/'res/intro/font.bin').read_bytes()
            actual_font=bytes(vram[(1440*32+i)^1] for i in range(len(font)))
            assert actual_font==font,'opaque font differs in VRAM'
            before_atlas=uploaded;before_pal=bytes((C.c_ubyte*128).in_dll(core,'cram'));variants=set()
            if args.movie and glow_count:
                encoder=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(av.timing.fps),'-i','pipe:0','-vf','scale=960:672:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(d['id']+'-glow.mp4'))],stdin=subprocess.PIPE)
                record=True
            for _ in range(fps*4):
                run();variants.add(bytes(vram[(781*32+i)^1] for i in range(len(atlas))))
            if record:
                record=False;encoder.stdin.close();encoder.wait();assert encoder.returncode==0;encoder=None
            if glow_start is not None and glow_count:
                for variant in variants:assert variant[:lo]==atlas[:lo] and variant[hi:]==atlas[hi:]
                assert len(variants)>1,'lava glow did not animate'
                highlight=runtime['glow']['highlight_index'];brighter=runtime['glow']['brighter_index']
                base_nibbles=[n for b in atlas[lo:hi] for n in (b>>4,b&15)]
                changed_pixels=0
                for variant in variants:
                    nibbles=[n for b in variant[lo:hi] for n in (b>>4,b&15)]
                    for original_pixel,current_pixel in zip(base_nibbles,nibbles):
                        if original_pixel!=current_pixel:
                            assert (original_pixel,current_pixel)==(highlight,brighter),'glow altered a non-highlight pixel'
                            changed_pixels+=1
            after_pal=bytes((C.c_ubyte*128).in_dll(core,'cram'));assert before_pal==after_pal,'palette changed during isolated glow'
            return {'exact_atlas_except_glow':True,'opaque_hud_tiles':11,'hud_vram_base':icon_base,'font_bytes':len(font),'glow_variants':len(variants),'glow_start':glow_start,'glow_count':glow_count,'only_lava_highlight_pixels_changed':bool(glow_count),'palette_stable':True,'scene_atlas_end':781+ex['tiles'],'reserved_scene_end_with_hud':781+640+11}
        check(d['id']+'/hardware',hardware_probe,result['isolated_probes'])
        def bounds_probe():
            restore(initial);isolate();w16('hp',100);checks=0
            midx=(left+right)//2;midy=(top+bottom)//2
            for key,x,y,expected in [(6,left+16,midy,(left,midy)),(7,right-16,midy,(right,midy)),(4,midx,top+16,(midx,top)),(5,midx,bottom-16,(midx,bottom))]:
                pos(x,y);hold({key},fps);assert (u16('px'),u16('py'))==expected,('wall',key,u16('px'),u16('py'),expected);checks+=1
            for side,x in [('left',left),('right',right)]:
                for direction,key in [(0,4),(4,5)]:
                    pos(x,midy);hold({key},1);settle();write(syms['pshots'][0],bytes(syms['pshots'][1]));w16('shotCooldown',0)
                    hold({1},2)
                    assert any(read(syms['pshots'][0]+i*20+18,1)[0] for i in range(6)),('vertical shot blocked',side,direction)
                    checks+=1
            pos(right,bottom);settle();shot(d['id']+'-lower-right');pos(left,bottom);settle();shot(d['id']+'-lower-left')
            return {'wall_and_vertical_shot_cases':checks}
        check(d['id']+'/bounds',bounds_probe,result['isolated_probes'])
        def terrain_probe():
            restore(initial);isolate();pos(*d['start']);run(4);hp0=u16('hp');run(fps);assert u16('hp')==hp0
            values=[]
            for hazard in d['hazards']:
                restore(initial);isolate();pos(*terrain_center(hazard['rect']));run(4)
                if hazard['kind']=='thermal':
                    hp1=u16('hp');run(fps);hp2=u16('hp');run(fps);hp3=u16('hp');assert hp3<hp2<hp1,('lava damage samples',hazard,hp1,hp2,hp3)
                    pos(*d['start']);settle();dryhp=u16('hp');run(fps);assert u16('hp')==dryhp,('lava continued on dry floor',dryhp,u16('hp'))
                    if 'lavaTime' in syms:assert u16('lavaTime')==0,('lava counter did not reset',u16('lavaTime'))
                    pos(*terrain_center(hazard['rect']));settle()
                    if 'lavaTime' in syms:assert 0<u16('lavaTime')<=5,('lava counter not restarted',u16('lavaTime'))
                    values.append({'kind':'thermal','hp_samples':[hp1,hp2,hp3],'damage_stops_on_exit':True,'progress_resets':True,'hp_held_during_probe':False})
                else:
                    slow1=u8('playerSlowPct');run(fps);slow2=u8('playerSlowPct');assert slow2>=slow1>=50
                    pos(*d['start']);run(3);assert u8('playerSlowPct')==0
                    values.append({'kind':'mud','slow_pct':[slow1,slow2],'reset_on_dry':True})
            restore(initial);isolate();pos(*d['start']);run(3);start_hp=u16('hp');route=dry_route(d);route_frames=0
            for gx,gy in route[1:]:
                for _ in range(15):
                    x,y=u16('px'),u16('py')
                    if abs(x-gx)<=1 and abs(y-gy)<=1:break
                    buttons.clear();buttons.add((7 if x<gx else 6) if x!=gx else (5 if y<gy else 4));run();route_frames+=1
                    assert u16('hp')==start_hp and u8('playerSlowPct')==0,('dry route terrain',x,y)
                else:raise AssertionError(('dry route stalled',gx,gy,u16('px'),u16('py')))
            buttons.clear();return {'hazards':values,'controller_dry_route':True,'controller_route_frames':route_frames,'ram_writes_during_route':False}
        check(d['id']+'/terrain',terrain_probe,result['isolated_probes'])
        def pause_probe():
            restore(initial);isolate();pos(*d['start']);settle();before=(u16('cameraX'),u16('cameraY'))
            press(3);assert state()==2;shot(d['id']+'-pause');press(3);settle();assert state()==1 and u8('arenaActive')
            assert (u16('cameraX'),u16('cameraY'))==before;assert read(syms['music'][0]+33,1)[0]==tracks[node]
            return {'scene_restored':True,'camera_restored':True,'music_track':tracks[node]}
        check(d['id']+'/pause',pause_probe,result['isolated_probes'])
        if node==8:
            def spawn_probe():
                restore(initial);clear_enemies();pos(*d['start']);w16('spawnTimer',0)
                run();first=len(enemies());timer=u16('spawnTimer')
                assert first==1 and timer==2*fps,('6B first spawn/reload',first,timer)
                run(2*fps+2)
                assert len(enemies())>=2,('6B second spawn',len(enemies()))
                return {'spawn_reload_frames':timer,'spawn_seconds':2,'second_enemy_spawned':True,'hp_not_held':True,'setup':'initial enemy pool cleared and first cooldown zeroed only'}
            check(d['id']+'/spawn-interval',spawn_probe,result['isolated_probes'])
        if not args.no_stress:
            def stress_probe():
                tests=[]
                for axis in ['horizontal','vertical']:
                    restore(initial);buttons.add(1)
                    for t in range(90):formation(d,tick=t,axis=axis);run()
                    begin=frames();vb=u32('vtimer');loads=[];cx=[];cy=[]
                    for t in range(90,390):
                        formation(d,tick=t,axis=axis);run();loads.append(u16('cpuFrameLoad')*100/2048);cx.append(u16('cameraX'));cy.append(u16('cameraY'))
                    game=frames()-begin;physical=u32('vtimer')-vb;rate=fps*game/physical
                    item={'axis':axis,'enemies':4,'shots_per_pool':6,'game_frames':game,'physical_frames':physical,'fps':round(rate,2),'cpu_mean_pct':round(statistics.mean(loads),2),'cpu_p95_pct':round(sorted(loads)[285],2),'camera_x_range':[min(cx),max(cx)],'camera_y_range':[min(cy),max(cy)]}
                    assert rate>=fps*.99,item
                    actual_range=item['camera_x_range'] if axis=='horizontal' else item['camera_y_range']
                    assert actual_range==[0,max(0,d['width']-320 if axis=='horizontal' else d['height']-224)],item
                    tests.append(item)
                buttons.clear();return tests
            check(d['id']+'/stress',stress_probe,result['isolated_probes'])
        for trial in range(args.matches):
            restore(initial);ordinary=True;writes_before=writes;begin=frames();vb=u32('vtimer');walk=0;damage_samples=[];heals=[];peak_enemies=peak_player=peak_enemy=0;lastpos=(u16('px'),u16('py'));previous_hp=u16('hp');enemy_bound_checks=0;min_npc_hp=u16('npcHp') if node==6 else None
            for tick in range(args.seconds*fps):
                if state() in (3,4):break
                assert state()==1,('ordinary match unexpected state',node,trial,state())
                ax,ay=u16('px'),u16('py');assert left<=ax<=right and top<=ay<=bottom
                current=enemies();peak_enemies=max(peak_enemies,len(current));keys={1}
                for enemy_x,enemy_y,kind in current:
                    assert left<=enemy_x<=right and top<=enemy_y<=bottom,('enemy outside',node,kind,enemy_x,enemy_y);enemy_bound_checks+=1
                if current:
                    enemy_x,enemy_y,_=min(current,key=lambda e:abs(e[0]-ax)+abs(e[1]-ay));dx,dy=enemy_x-ax,enemy_y-ay
                    if abs(dx)+abs(dy)<40:key=(6 if dx>0 else 7) if abs(dx)>abs(dy) else(4 if dy>0 else 5);keys.add(key)
                    elif abs(dx)>6 and abs(dy)>6:keys.add((5 if dy>0 else 4) if abs(dx)>abs(dy) else(7 if dx>0 else 6))
                    else:
                        desired=(1 if dx>0 else -1,0) if abs(dx)>abs(dy) else(0,1 if dy>0 else -1)
                        if (signed('faceX'),signed('faceY'))!=desired:keys.add(7 if desired[0]>0 else 6 if desired[0]<0 else 5 if desired[1]>0 else 4)
                else:keys.add((7,5,6,4)[(tick//fps+trial)%4])
                # Reject a movement step into any declared pool. Try another
                # dry cardinal direction when the aiming route reaches a pool.
                step={4:(0,-2),5:(0,2),6:(-2,0),7:(2,0)}
                moving=next((k for k in keys if k in step),None)
                if moving is not None:
                    dx,dy=step[moving]
                    if not free(d,ax+dx,ay+dy):
                        keys.discard(moving)
                        for alternative in [7,5,6,4]:
                            dx,dy=step[alternative]
                            if free(d,ax+dx,ay+dy):keys.add(alternative);break
                if trial%2 and tick>15*fps and current and u16('bombs') and tick%(20*fps)<2:keys.add(0)
                buttons.clear();buttons.update(keys);run()
                hp_now=signed('hp')
                if hp_now<previous_hp:damage_samples.append({'at_frame':tick,'hp':hp_now})
                if hp_now>previous_hp:heals.append({'at_frame':tick,'hp':hp_now})
                previous_hp=hp_now
                if node==6 and state()==1:min_npc_hp=min(min_npc_hp,u16('npcHp'))
                now=(u16('px'),u16('py'));walk+=now!=lastpos;lastpos=now
                peak_player=max(peak_player,sum(read(syms['pshots'][0]+i*20+18,1)[0]!=0 for i in range(16)))
                peak_enemy=max(peak_enemy,sum(read(syms['eshots'][0]+i*20+18,1)[0]!=0 for i in range(16)))
            ordinary=False;buttons.clear();assert writes==writes_before
            assert peak_enemies<=4 and peak_player<=6 and peak_enemy<=6,('production caps',node,peak_enemies,peak_player,peak_enemy)
            end_state=state();match={'attempt':trial+1,'result':{3:'defeat',4:'completed'}.get(end_state,'timeout'),'objective_failed':bool(read(syms['phaseStats'][0]+8,1)[0]),'physical_seconds':round((u32('vtimer')-vb)/fps,2),'active_seconds':round((frames()-begin)/fps,2),'game_fps':round(fps*(frames()-begin)/max(1,u32('vtimer')-vb),2),'kills':u16('kills'),'remaining_hp':signed('hp'),'minimum_npc_hp':min_npc_hp,'moving_frames':walk,'enemy_bound_checks':enemy_bound_checks,'damage_events':damage_samples,'healing_events':heals,'peak_enemies':peak_enemies,'peak_player_shots':peak_player,'peak_enemy_shots':peak_enemy,'game_ram_writes':False}
            result['ordinary_matches'].append(match);shot(d['id']+'-attempt-'+str(trial+1));print('MATCH',d['id'],json.dumps(match),flush=True)
            if end_state not in (3,4):report['failures'].append({'check':d['id']+'/attempt-'+str(trial+1),'error':'ordinary attempt timed out'})
        save_report()
    # Branch probes isolate only their initial state. Real objective logic,
    # contact damage, timers and graph resolution determine the outgoing edge.
    branches={};report['objective_branch_probes']=branches
    if 6 in stage_baselines and not args.only_entry:
        initial=stage_baselines[6]
        def objective_success():
            restore(initial);isolate();pos(64,288)
            assert (signed('npcX'),signed('npcY'))==(176,200)
            pos(176,232);hold({4},30);assert u16('py')>=224,'player walked through Santa pedestal'
            pos(64,288);run(31*fps);assert state()==4 and not read(syms['phaseStats'][0]+8,1)[0]
            run(4*fps);assert u8('pendingLevel')==7
            return {'target_seconds':30,'next_node':7,'npc_spawn':[176,200],'pedestal_collision':True,'setup':'spawn cooldown suppressed; timer and objective not patched'}
        check('05/protect-success',objective_success,branches)
        def objective_failure():
            restore(initial);isolate();pos(64,288);assert u16('npcHp')==100
            buf=bytearray(stride);x,y=176,200;struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,32,0,600,600);buf[30]=0;buf[31]=20;buf[43]=1;buf[44]=1;write(enemy_addr,buf)
            losses=[];prior=100;start=frames()
            for tick in range(30*fps):
                if state()!=1:break
                # Controlled continuous enemy contact. HP, invulnerability,
                # objective timer and graph flags are never written.
                write(enemy_addr,struct.pack('>hhii',x,y,x<<6,y<<6));run()
                now=u16('npcHp')
                if now<prior:losses.append({'frame':frames()-start,'hp':now})
                prior=now
            assert state()==4 and read(syms['phaseStats'][0]+8,1)[0],'NPC contact did not fail objective'
            assert len(losses)==9 and losses[-1]['frame']<30*fps,losses
            intervals=[b['frame']-a['frame'] for a,b in zip(losses,losses[1:])]
            assert all(2.4*fps<=v<=2.6*fps for v in intervals),intervals
            run(4*fps);assert u8('pendingLevel')==8
            return {'next_node':8,'real_npc_contact_damage':True,'initial_npc_hp':100,'hp_never_written':True,'contact_damage_events':losses,'interval_frames':intervals,'setup':'One enemy initial contact, then enemy position pinned each frame; real NPC contact/knockback/invulnerability/timer/graph logic'}
        check('05/protect-failure',objective_failure,branches)
    if 8 in stage_baselines and not args.only_entry:
        def classic_transition():
            restore(stage_baselines[8]);isolate();w16('kills',20);run(4*fps)
            assert u8('pendingLevel')==9
            for _ in range(40):
                if state()==1 and u8('currentLevel')==9:break
                press(1);run(fps//4)
                if state()==6:press(3);run(fps//4)
            assert u8('currentLevel')==9 and not u8('arenaActive')
            assert (u16('arenaMinX'),u16('arenaMaxX'),u16('cameraX'),u16('cameraY'))==(8,311,0,0)
            shot('09-classic-restored');return {'next_node':9,'classic_bounds':[8,311],'camera':[0,0],'scene_left_safely':True}
        check('06B/classic-transition',classic_transition,branches)
    report['passed']=not report['failures'];save_report();print(json.dumps({'passed':report['passed'],'region':report['region'],'failures':report['failures'],'output':str(out/'report.json')}),flush=True)
    core.retro_unload_game();core.retro_deinit()
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
