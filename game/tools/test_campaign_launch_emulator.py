"""Campaign stages in the FINAL production ROM. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[1]
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='2,3,4,5,6,7,8');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--shield-tests',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/campaign-whole-scenes-v1/launch/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    # Skip boot, enter NEW GAME, skip mission call, start phase 1 with A.
    run(120);press(3);run(fps*4)
    for _ in range(6):
        if u8('arenaActive') and u32('flow_state')==1:break
        press(3);run(fps)
        if u8('arenaActive') and u32('flow_state')==1:break
        press(1);run(fps*4)
    if not (u8('arenaActive') and u32('flow_state')==1):shot('startup-failed');raise AssertionError(('start',u8('state'),u8('currentLevel'),u8('arenaActive')))
    assert u8('currentLevel')==1 and u16('arenaMaxX')==487
    shot('01-inicio')
    baseline=snapshot()
    enemy_addr,enemy_bytes=syms['enemies'];stride=enemy_bytes//16;assert stride==46,stride
    # Node setup is accelerated through existing campaign progression. Tests
    # below distinguish controller-only attempts from explicit RAM probes.
    import re
    node_names=re.search(r'typedef enum\s*\{(.*?)NODE_MAX', ((build.parents[1]/'src/levels/graph.h') if (build.parents[1]/'src/levels/graph.h').exists() else GAME/'src/levels/graph.h').read_text(), re.S)[1]
    node_ids={name:i+1 for i,name in enumerate(re.findall(r'\bN_[A-Za-z0-9]+\b',node_names))}
    report={'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),'passed':False,'nodes':{},'method':'RAM seeds node entry and explicit isolated probes; objective execution uses controller input. Stress is RAM seeded, FPS measures simulation frames per VBlank.'}
    def save(): (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def state():return u32('flow_state')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def w32(name,value):write(syms[name][0],struct.pack('>I',value))
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def clear_enemies():
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
    def cr8(offset):return read(syms['campaignResistance'][0]+offset,1)[0]
    def enter(node):
        nonlocal ordinary
        ordinary=False;restore(baseline);w16('hp',100);w16('kills',999)
        if 'surviveLeft' in syms:w16('surviveLeft',1)
        # Finish the real1->2A story/map before changing pending node. Editing
        # it during ROUTEMAP preparation strands its temporary overlay buffer.
        for _ in range(60):
            if state()==0:break
            if state() in (4,6):press(3)
            elif state()==5:press(1)
            run(fps//2)
        assert state()==0,('prep entry',state())
        write(syms['pendingLevel'][0],bytes([node]));press(1)
        for _ in range(fps*12):
            if state()==1 and u8('currentLevel')==node:break
            run()
        assert state()==1 and u8('currentLevel')==node,('entry',node,state(),u8('currentLevel'))
        buttons.clear()
        for _ in range(fps*10):
            if u16('freezeTimer')==0 and frames()>5:break
            run()
        assert u16('freezeTimer')==0
        return snapshot()
    geom=json.loads((GAME/'art/campaign-pattern-v2/launch/geometry.json').read_text())
    la=syms['campaignLaunch'][0]
    def left():return int.from_bytes(read(la+10,2),'big')
    def mask():return read(la+14,1)[0]
    def free(x,y):return geom['bounds'][0]<=x<=geom['bounds'][2]-15 and geom['bounds'][1]<=y<=geom['bounds'][3]-15 and not any(x<a+w and x+16>a and y<b+h and y+16>b for a,b,w,h in geom['solids'])
    def route_to(tx,ty):
        from collections import deque
        start=(round(signed('px')/8)*8,round(signed('py')/8)*8);goal=(round(tx/8)*8,round(ty/8)*8);queue=deque([start]);prev={start:None}
        while queue:
            p=queue.popleft()
            if p==goal:break
            for q in [(p[0]+8,p[1]),(p[0]-8,p[1]),(p[0],p[1]+8),(p[0],p[1]-8)]:
                if q not in prev and free(*q):prev[q]=p;queue.append(q)
        assert goal in prev,('route',goal)
        path=[];p=goal
        while p!=start:path.append(p);p=prev[p]
        for x,y in reversed(path):
            for _ in range(30):
                dx=x-signed('px');dy=y-signed('py')
                if abs(dx)<=3 and abs(dy)<=3:break
                buttons.clear()
                if dx>3:buttons.add(7)
                elif dx< -3:buttons.add(6)
                if dy>3:buttons.add(5)
                elif dy< -3:buttons.add(4)
                run(2)
                if state()!=1:return
            else:raise AssertionError(('stuck',x,y,signed('px'),signed('py')))
        buttons.clear();run(2)
    def record_start(label):
        nonlocal record,encoder
        if not args.movie:return
        encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb565le','-s','320x224','-r',str(fps),'-i','-','-an','-vf','scale=640:448:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(label+'-playtest.mp4'))],stdin=subprocess.PIPE);record=True
    def record_stop():
        nonlocal record,encoder
        if encoder:record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
    scene_path=build/'sources/campaign_launch_scenes.c'
    if not scene_path.exists():scene_path=(build.parents[1]/'src/levels/campaign_launch_scenes.c') if (build.parents[1]/'src/levels/campaign_launch_scenes.c').exists() else GAME/'src/levels/campaign_launch_scenes.c'
    scene_source=scene_path.read_text()
    palette_samples={}
    from campaign_objective_probe import inspect_objectives
    def objective_pixels():return inspect_objectives(build.parents[1] if (build.parents[1]/'art/objective-sprites-v1/assets.json').exists() else GAME,read,vram,syms,signed('cameraX'),signed('cameraY'),u16('bga_addr'))
    def native_scene_check(kind):
        mp=[int(v,0) for v in re.findall(r'0x[0-9A-Fa-f]+|\b\d+\b',re.search(r'static const u16 '+kind+r'Map\[\]=\{(.*?)\};',scene_source,re.S)[1])]
        words=[int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)UL',re.search(r'static const u32 '+kind+r'Tiles\[\]=\{(.*?)\};',scene_source,re.S)[1])]
        expected=b''.join(struct.pack('>I',v) for v in words);base_tile=scene_base
        uploaded=bytes(vram[((base_tile*32+i)&65535)^1] for i in range(len(expected)))
        assert uploaded==expected,('native atlas mismatch',kind)
        cx,cy=signed('cameraX')//8,signed('cameraY')//8;failures=[]
        for y in range(cy,min(cy+28,48)):
            for x in range(cx,min(cx+40,64)):
                actual=vw(u16('bgb_addr')+((y&31)*64+(x&63))*2);target=0x6000|(base_tile+mp[y*64+x])
                if actual!=target:failures.append((x,y,actual,target))
        assert not failures,('native map/flip mismatch',kind,failures[:4])
        excluded=set()
        for slot in range(7):
            ox,oy,age,art,frame,mode,visible,ground,primed=struct.unpack('>hhH6B',read(syms['objectiveVisuals'][0]+slot*12,12))
            if not ground or not visible:continue
            for gy in range((oy-32+8)//8-1,(oy-32+8)//8+4):
                for gx in range((ox-16)//8,(ox-16)//8+4):excluded.add((gx,gy))
        for y in range(cy,min(cy+28,48)):
            for x in range(cx,min(cx+40,64)):
                if (x,y) in excluded:continue
                attr=vw(u16('bga_addr')+((y&31)*64+(x&63))*2);want=0x6000|(base_tile+mp[y*64+x])
                assert attr==0 or attr==want,('BG_A scroll ghost',kind,x,y,attr,want)
        cram=bytes((C.c_ubyte*128).in_dll(core,'cram'))[96:128]
        assert cram[:2]==b'\0\0','scene palette0 is not literal black'
        if kind in palette_samples:assert cram==palette_samples[kind],('palette changed after isolated movement',kind)
        else:palette_samples[kind]=cram
        return {'passed':True,'atlas_bytes':len(expected),'visible_map_cells_checked':40*min(28,48-cy),'pixel_exact':True,'hflip_vflip_supported':True,'camera':[signed('cameraX'),signed('cameraY')],'bg_a_clean':True,'palette_zero_black':True}
    for stage in ['14','15']:
        modular=out/('phase'+stage+'-modular')
        command=[__import__('sys').executable,str(GAME/('tools/test_phase'+stage+'_shipyard_emulator.py')),'--output',str(modular),'--build-dir',str(build)]
        if args.pal:command.append('--pal')
        subprocess.run(command,check=True)
        modular_report=json.loads((modular/'report.json').read_text())
        report['nodes'][stage]={'modular_native_suite':{'passed':modular_report['passed'],'report':str(modular/'report.json')}}
    for label,cap in [('16',4)]:
        node=node_ids['N_'+label];r={};report['nodes'][label]=r;base=enter(node);shot(label+'-entry')
        scene_base=int.from_bytes(read(syms['objectiveArtBases'][0]+2,2),'big')-geom['fire_tiles' if label=='16' else 'normal_tiles']
        r['entry']={'passed':True,'enemy_cap':cap,'shot_cap':4,'world':[512,384]}
        r['native_scene']=native_scene_check('fire' if label=='16' else 'normal')
        r['objective_pixels']=objective_pixels()
        if label in ('15','16'):
            persistent=[]
            for i,(gx,gy) in enumerate(geom['machines']):
                ox,oy,age,art,frame,mode,visible,ground,primed=struct.unpack('>hhH6B',read(syms['objectiveVisuals'][0]+i*12,12))
                persistent.append({'slot':i,'position':[ox,oy],'art':art,'frame':frame,'visible':visible,'passed':(ox,oy)==(gx,gy) and art==1 and bool(visible)})
            assert all(p['passed']for p in persistent),('generator continuity',persistent)
            r['persistent_generators']={'passed':True,'probes':persistent}
        if label=='14':
            ordinary=False;clear_enemies();w16('spawnTimer',60000);w16('hp',100);ordinary=True;record_start('14-generators')
            for i,(x,y) in enumerate(geom['machines']):
                route_to(x-8,min(y+24,geom['bounds'][3]-15)//8*8);run(fps)
                if state()==1:r.setdefault('native_after_movement',{'passed':True,'samples':[]})['samples'].append(native_scene_check('normal'))
                assert mask()&(1<<i),('generator',i,mask(),signed('px'),signed('py'))
                shot(label+'-generator-'+str(i+1))
            record_stop()
            r['controller_generators']={'passed':mask()==31,'mask':mask(),'setup':'RAM clears pressure and delays spawn; all5front approaches and activation with controller only'}
        elif label=='15':
            ordinary=False;clear_enemies();w16('spawnTimer',60000);start=left();ordinary=True;run(fps*3)
            r['timer_real_seconds']={'passed':abs((start-left())-fps*3)<fps//5,'initial':start,'after':left()}
            ordinary=False;restore(base);clear_enemies();w16('spawnTimer',60000)
            # Keep one live enemy and two active projectile pools in this probe.
            # A frozen empty arena would not demonstrate an AI/combat pause.
            enemy=bytearray(stride);struct.pack_into('>hhii',enemy,0,400,200,400<<6,200<<6);struct.pack_into('>hhHH',enemy,12,16,0,600,600)
            enemy[30],enemy[31],enemy[43],enemy[44]=5,250,1,1;write(enemy_addr,enemy)
            for pool in ('pshots','eshots'):
                projectile=bytearray(20);struct.pack_into('>iiii',projectile,0,(96 if pool=='pshots' else 360)<<6,224<<6,16,0);projectile[17],projectile[18]=1,1;write(syms[pool][0],projectile)
            write(la+10,struct.pack('>H',80*fps+1));ordinary=True;record_start('15-ignition')
            for _ in range(fps*4):
                run()
                if u8('launchPresentation')==1 and signed('cameraY')==24:break
            assert u8('launchPresentation')==1,'ignition presentation absent'
            run(3)
            def combat_projectiles(pool):
                data=read(*syms[pool])
                # FShot's sole visual-cache byte renderPose is lazily filled by
                # SPRITES_draw; all19physics/damage/active bytes must be frozen.
                return b''.join(data[i:i+19] for i in range(0,len(data),20))
            def presentation_state():return (left(),signed('hp'),signed('npcHp'),signed('px'),signed('py'),read(enemy_addr,enemy_bytes),combat_projectiles('pshots'),combat_projectiles('eshots'))
            frozen=presentation_state();assert read(enemy_addr+44,1)[0] and all(read(syms[p][0]+18,1)[0] for p in ('pshots','eshots')),'pause probe actors not active';run(fps//4)

            assert frozen==presentation_state(),'combat/hold advances while engine camera owns view'
            # Sample in the middle of a stable visual pose after its DMA reaches
            # VBlank; the runtime may publish the next pose before the callback.
            for _ in range(8):
                pose=read(syms['objectiveVisuals'][0]+5*12+7,1);run()
                if pose==read(syms['objectiveVisuals'][0]+5*12+7,1):break
            shot('15-ignition-focus')
            r['ignition_visual']={'passed':u8('arenaDamaged')==1,'stage':read(la+15,1)[0],'native_scene':native_scene_check('fire'),'objective_pixels':objective_pixels(),'combat_paused_during_focus':True,'pause_probe_active_enemies':1,'pause_probe_active_projectiles':2}
            for _ in range(fps*4):
                run()
                if u8('launchPresentation')==0:break
            assert u8('launchPresentation')==0,'presentation did not return control'
            run(3);shot('15-ignition-return')
            r['ignition_visual']['native_after_return']=native_scene_check('fire');record_stop()
            radio_edges=[]
            for edge,ex,ey in [('west',184,176),('east',312,176),('south',248,216),('north',208,136)]:
                ordinary=False;restore(base);clear_enemies();w16('spawnTimer',60000)
                enemy=bytearray(stride);struct.pack_into('>hhii',enemy,0,ex,ey,ex<<6,ey<<6);struct.pack_into('>hhHH',enemy,12,0,0,600,600)
                enemy[30],enemy[31],enemy[43],enemy[44]=0,20,1,1;write(enemy_addr,enemy)
                hp_before=signed('npcHp');ordinary=True;run(2)
                radio_edges.append({'edge':edge,'enemy_feet':[ex,ey],'before':hp_before,'after':signed('npcHp'),'passed':signed('npcHp')==hp_before-12})
            assert all(v['passed']for v in radio_edges),('solid console outside contact',radio_edges)
            r['radio_outer_contact']={'passed':True,'probes':radio_edges,'setup':'RAM seeds bug on legal outer edge; runtime contact and damage only'}
            ordinary=False;restore(base);w16('npcHp',0);ordinary=True;run(fps)
            r['radio_loss_retries']={'passed':state()==3,'state':state()}
            ordinary=False;restore(base);clear_enemies();write(la+10,b'\0\1');ordinary=True;run(fps)
            r['radio_timer_win']={'passed':state()!=1,'state':state()}
            ordinary=False;restore(base);clear_enemies();w16('spawnTimer',60000);ordinary=True;timer_before=left();vb=u32('vtimer')
            for _ in range(140*fps):
                run()
                if state()!=1:break
            r['full_hold_isolated']={'passed':left()==0 and state()==4,'duration_seconds':round((u32('vtimer')-vb)/fps,2),'initial_timer_frames':timer_before,'final_timer_frames':left(),'final_state':state(),'wall_clock_limit_seconds':140,'setup':'RAM clears pressure and delays reinforcements60000frames once;120active seconds plus paused ignition/loading; real result transition; no writes during hold'}
        else:
            boss=[i for i in range(16) if read(enemy_addr+i*stride+44,1)[0] and read(enemy_addr+i*stride+30,1)[0]==14]
            r['boss_spawn']={'passed':len(boss)==1,'count':len(boss),'hp':read(enemy_addr+boss[0]*stride+31,1)[0] if boss else 0}
            ordinary=False;restore(base);w16('hp',30000);ordinary=True;vb=u32('vtimer');min_life=25
            for tick in range(fps*120):
                living=[i for i in range(16) if read(enemy_addr+i*stride+44,1)[0] and read(enemy_addr+i*stride+30,1)[0]==14]
                if not living or state()!=1:break
                e=enemy_addr+living[0]*stride;bx=int.from_bytes(read(e,2),'big',signed=True)+24;by=int.from_bytes(read(e+2,2),'big',signed=True)+24
                min_life=min(min_life,read(e+31,1)[0]);dx=bx-signed('px')-8;dy=by-signed('py')-8;buttons.clear();buttons.add(1)
                if abs(dx)>20:
                    buttons.add(7 if dx>0 else 6)
                if abs(dy)>20:
                    buttons.add(5 if dy>0 else 4)
                run()
            buttons.clear();run(fps);shot('16-boss-combat-result')
            r['controller_boss_damage']={'passed':min_life<25,'minimum_boss_hp':min_life,'defeated':bool(u8('bossDefeated')),'duration_seconds':round((u32('vtimer')-vb)/fps,2),'setup':'RAM seeds heroHP30000 once to isolate combat; no bossHP mutation;120scontroller chase/fire attack'}

        ordinary=False;restore(base);clear_enemies();w16('spawnTimer',60000);coll=[]
        for rx,ry,rw,rh in geom['solids']:
            ordinary=False;pos(rx-17,ry+(rh-16)//2);ordinary=True;hold({7},fps//2)
            coll.append({'solid':[rx,ry,rw,rh],'end_x':signed('px'),'passed':signed('px')+16<=rx})
        r['controller_collision']={'passed':all(v['passed'] for v in coll),'probes':coll,'setup':'RAM seed positions; controller pushes into each obstacle'}
        bounds=geom['bounds'];limits=[]
        for edge,x,y,key in [('left',bounds[0],176,6),('right',bounds[2]-15,176,7),('top',160,bounds[1],4),('bottom',64,bounds[3]-15,5)]:
            ordinary=False;pos(x,y);ordinary=True;hold({key},fps//2)
            ok=bounds[0]<=signed('px')<=bounds[2]-15 and bounds[1]<=signed('py')<=bounds[3]-15
            limits.append({'edge':edge,'position':[signed('px'),signed('py')],'passed':ok})
        r['controller_bounds']={'passed':all(v['passed'] for v in limits),'probes':limits,'setup':'RAM seeds legal positions; controller pushes against each map boundary'}

        ordinary=False;restore(base);ordinary=True;start=frames();vb=u32('vtimer');peak=0;hpstart=u16('hp');record_start(label)
        for tick in range(fps*25):
            buttons.clear();buttons.update({1,[7,5,6,4][(tick//(fps*2))%4]});run();peak=max(peak,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
            if state()!=1 or signed('hp')<=0:break
        record_stop();buttons.clear()
        r['difficulty_sample']={'controller_only':True,'duration_seconds':round((u32('vtimer')-vb)/fps,2),'result':'defeat' if signed('hp')<=0 else {3:'defeat',4:'completed'}.get(state(),'timeout'),'initial_hp':hpstart,'remaining_hp':signed('hp'),'damage_net':hpstart-signed('hp'),'radio_hp':signed('npcHp') if label=='15' else None,'peak_enemies':peak,'simulation_fps':round(fps*(frames()-start)/max(1,u32('vtimer')-vb),2),'scope':'25s automated movement/fire; limited sample, not human difficulty rating'}
        ordinary=False;restore(base);clear_enemies();w16('hp',30000)
        def formation():
            w16('hp',30000)
            if label=='15':w16('npcHp',100)
            for i in range(cap):
                x,y=72+i*56,184;kind=14 if label=='16' and i==0 else 5
                buf=bytearray(stride);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,16,0,600,600)
                buf[30],buf[31],buf[43],buf[44]=kind,250,1,1;write(enemy_addr+i*stride,buf)
            for name in ('pshots','eshots'):
                address,size=syms[name]
                for i in range(4):
                    buf=bytearray(20);struct.pack_into('>iiii',buf,0,(32+i*56)<<6,(112+(i%2)*24)<<6,32,0);buf[17],buf[18]=1,1;write(address+i*20,buf)
        for _ in range(30):formation();run()
        start=frames();vb=u32('vtimer');loads=[]
        for _ in range(fps*5):
            formation();run()
            if 'cpuFrameLoad' in syms:loads.append(u16('cpuFrameLoad')*100/2048)
        measured=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),2)
        r['visible_maximum_stress']={'passed':measured>=fps*.95,'simulation_fps':measured,'seeded_enemies':cap,'seeded_player_shots':4,'seeded_enemy_shots':4,'cpu_mean_percent':round(statistics.mean(loads),2) if loads else None,'cpu_peak_percent':round(max(loads),2) if loads else None,'setup':'RAM re-seeds simultaneous cap and full4shot pools eachframe; artificial stress'};shot(label+'-stress');save()
    report['passed']=all(v.get('passed',True) for n in report['nodes'].values() for v in n.values());save();print(json.dumps(report,indent=2));core.retro_unload_game();core.retro_deinit()
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
