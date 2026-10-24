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
    out=args.output or GAME/'art/campaign-whole-scenes-v1/resistance/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    geom=json.loads((GAME/'art/campaign-pattern-v2/resistance/geometry.json').read_text())
    def free(x,y,solids,width):
        bounds=geom['favela_bounds'] if width==768 else geom['union_bounds']
        dynamic=([r for i,r in enumerate(geom['cargo_solids'])if not(cr8(17)&(1<<i))] if u8('currentLevel')==node_ids['N_7']else[])
        return bounds[0]<=x<=bounds[2]-15 and bounds[1]<=y<=bounds[3]-15 and not any(x<a+c+4 and x+16>a-4 and y<b+d+4 and y+16>b-4 for a,b,c,d in solids) and not any(x<a+c+4 and x+16>a-4 and y<b+d+4 and y+16>b-4 for a,b,c,d in dynamic)
    def route_to(tx,ty,solids,width):
        from collections import deque
        sx,sy=signed('px'),signed('py');start=(round(sx/8)*8,round(sy/8)*8);goal=(round(tx/8)*8,round(ty/8)*8)
        queue=deque([start]);prev={start:None}
        while queue:
            p=queue.popleft()
            if p==goal:break
            for q in [(p[0]+8,p[1]),(p[0]-8,p[1]),(p[0],p[1]+8),(p[0],p[1]-8)]:
                if q not in prev and free(*q,solids,width):prev[q]=p;queue.append(q)
        assert goal in prev,('unreachable',goal)
        path=[];p=goal
        while p!=start:path.append(p);p=prev[p]
        for x,y in reversed(path):
            for _ in range(24):
                dx=x-signed('px');dy=y-signed('py')
                if abs(dx)<=3 and abs(dy)<=3:break
                keys={1}
                if dx>3:keys.add(7)
                elif dx< -3:keys.add(6)
                if dy>3:keys.add(5)
                elif dy< -3:keys.add(4)
                buttons.clear();buttons.update(keys);run(2)
                if state()!=1:
                    if cr8(18)==5:return
                    raise AssertionError(('leftplay',state(),u16('hp')))
            else:raise AssertionError(('stuck',x,y,signed('px'),signed('py')))
        buttons.clear();run(2)
    scene_path=build/'sources/campaign_resistance_scenes.c'
    if not scene_path.exists():scene_path=(build.parents[1]/'src/levels/campaign_resistance_scenes.c') if (build.parents[1]/'src/levels/campaign_resistance_scenes.c').exists() else GAME/'src/levels/campaign_resistance_scenes.c'
    scene_source=scene_path.read_text()
    palette_samples={}
    from campaign_objective_probe import inspect_objectives
    def objective_pixels():return inspect_objectives(build.parents[1] if (build.parents[1]/'art/objective-sprites-v1/assets.json').exists() else GAME,read,vram,syms,signed('cameraX'),signed('cameraY'),u16('bga_addr'))
    def native_scene_check(prefix,mapname):
        body=re.search(r'static const u16 '+prefix+'_'+mapname+r'\[\]=\{(.*?)\};',scene_source,re.S)[1]
        mp=[int(v,0) for v in re.findall(r'0x[0-9A-Fa-f]+|\b\d+\b',body)]
        body=re.search(r'static const u32 '+prefix+r'_tiles\[\]=\{(.*?)\};',scene_source,re.S)[1]
        expected=b''.join(struct.pack('>I',int(v,16)) for v in re.findall(r'0x([0-9A-Fa-f]+)UL',body))
        actual=bytes(vram[((scene_base*32+i)&65535)^1] for i in range(len(expected)))
        assert actual==expected,('atlas mismatch',prefix)
        cols=96 if prefix=='favela' else 64;cx=signed('cameraX')//8;cy=signed('cameraY')//8;errors=[]
        for y in range(cy,min(cy+28,48)):
            for x in range(cx,min(cx+40,cols)):
                attr=vw(u16('bgb_addr')+((y&31)*64+(x&63))*2);want=0x6000|(scene_base+mp[y*cols+x])
                if attr!=want:errors.append((x,y,attr,want))
        assert not errors,('native map/flip mismatch',prefix,errors[:4])
        # Outside current ground objects/labels, BG_A must be transparent or an
        # exact scenery restoration; a foreign tile indicates a scroll ghost.
        excluded=set()
        for slot in range(7):
            ox,oy,age,art,frame,mode,visible,ground,primed=struct.unpack('>hhH6B',read(syms['objectiveVisuals'][0]+slot*12,12))
            if not ground or not visible:continue
            for gy in range((oy-32+8)//8-1,(oy-32+8)//8+4):
                for gx in range((ox-16)//8,(ox-16)//8+4):excluded.add((gx,gy))
        for y in range(cy,min(cy+28,48)):
            for x in range(cx,min(cx+40,cols)):
                if (x,y) in excluded:continue
                attr=vw(u16('bga_addr')+((y&31)*64+(x&63))*2)
                want=0x6000|(scene_base+mp[y*cols+x])
                assert attr==0 or attr==want,('BG_A scroll ghost',prefix,x,y,attr,want)
        cram=bytes((C.c_ubyte*128).in_dll(core,'cram'))[96:128]
        assert cram[:2]==b'\0\0','scene palette0 is not literal black'
        if prefix in palette_samples:assert cram==palette_samples[prefix],('palette changed after isolated movement',prefix)
        else:palette_samples[prefix]=cram
        return {'passed':True,'atlas_bytes':len(expected),'pixel_exact':True,'hflip_vflip_supported':True,'camera':[signed('cameraX'),signed('cameraY')],'bg_a_clean':True,'palette_zero_black':True}
    for label in ('7','8','13A','13B'):
        node=node_ids['N_'+label];r={};report['nodes'][label]=r
        base=enter(node);shot(label+'-entry')
        if label=='7':scene_base=int.from_bytes(read(syms['objectiveArtBases'][0]+4,2),'big')-geom['favela_tiles']
        r['native_scene']=native_scene_check('favela' if label in ('7','8') else 'union','map' if label in ('7','8') else 'alive' if label=='13A' else 'dead')
        r['entry']={'passed':True,'enemy_cap':4 if label=='7' else 6 if label=='8' else 5,'shot_cap':6,'width':768 if label in ('7','8') else 512}
        if label in ('7','8'):r['objective_pixels']=objective_pixels()
        if label=='7':
            # Control-only interactions in an explicitly isolated zero-pressure
            # baseline. No mutation of mission state and no collection shortcuts.
            ordinary=False;clear_enemies();write(syms['campaignResistance'][0]+2,struct.pack('>H',60000));w16('hp',100);ordinary=True
            try:
                for i,(x,y) in enumerate(geom['cargo']):
                    rx,ry,rw,rh=geom['cargo_solids'][i]
                    route_to(rx-24,ry,geom['favela_solids'],768)
                    hold({1,7},fps//3)
                    before_pickup={'source':i,'taken_before':cr8(17),'blocked_x':signed('px'),'blocked':signed('px')+16<=rx}
                    assert before_pickup['blocked'],('case did not block before pickup',i,signed('px'))
                    front_y=min(y+16,geom['favela_bounds'][3]-15)//8*8
                    if free(x-8,front_y,geom['favela_solids'],768):
                        route_to(x-8,front_y,geom['favela_solids'],768)
                    else:
                        # The bottom case has a legal16px front lane, narrower
                        # than the navigation padding. Reach its clear right
                        # flank, then use actual collision to touch its side.
                        route_to(x+24,front_y,geom['favela_solids'],768)
                        for _ in range(fps):
                            if signed('px')<=x+16:break
                            buttons.clear();buttons.update({1,6});run()
                        assert signed('px')<=x+16,('front side approach',i,signed('px'))
                        buttons.clear()
                    run(fps)
                    r.setdefault('native_after_movement',{'passed':True,'samples':[]})['samples'].append(native_scene_check('favela','map'))
                    assert cr8(16)&(1<<i),('chest not opened',i,read(syms['campaignResistance'][0],30).hex())
                    route_to(x+24,min(y+16,geom['favela_bounds'][3]-15)//8*8,geom['favela_solids'],768);run(8)
                    assert cr8(19)==i,('no cargo',i,read(syms['campaignResistance'][0],30).hex())
                    assert cr8(17)&(1<<i),('taken did not change through controller',i)
                    route_to(rx-24,ry,geom['favela_solids'],768);hold({1,7},fps)
                    before_pickup.update({'taken_after':cr8(17),'released_x':signed('px'),'released':signed('px')>=rx+rw})
                    assert before_pickup['released'],('case remained blocking after pickup',i,signed('px'))
                    r.setdefault('dynamic_case_collision',{'passed':True,'probes':[]})['probes'].append(before_pickup)
                    # Passing another source while loaded may never add a load.
                    route_to(geom['depot'][0]-8,geom['depot'][1]-8,geom['favela_solids'],768);run(8)
                    assert cr8(18)==i+1,('delivery',i,cr8(18))
                    shot('7-delivery-'+str(i+1))
                r['controller_transport']={'passed':True,'delivered':cr8(18),'setup':'isolated enemy pressure; all5loops use controller only; fire held in transit to avoid opening a different chest en route','state':state()}
            except Exception as e:r['controller_transport']={'passed':False,'error':repr(e)};shot('7-failure')
        elif label=='8':
            ordinary=False
            # A separate restore proves normal kill count is ignored while all
            # targets remain alive; their3HP records stay intact.
            restore(base);w16('kills',999);run(2);r['kill_counter_ignored']={'passed':state()==1 and cr8(20)==0}
            for i in range(3):
                before=cr8(20);write(enemy_addr+i*stride+44,b'\0');run(2)
                assert cr8(20)&(1<<i),('priority death missing',i,before,cr8(20))
            r['priority_progress']={'passed':cr8(20)==7,'mask':cr8(20),'setup':'RAM seeded inactive flags; runtime observed priority progress'};shot('8-priorities-destroyed')
        else:
            ordinary=False;restore(base);w16('kills',29 if label=='13A' else 44);run(2);before=state();w16('kills',30 if label=='13A' else 45);run(fps)
            r['kill_target']={'passed':before==1 and state()!=1,'target':30 if label=='13A' else 45,'setup':'RAM seeded kill counter boundary'}
        # Every authored wall is probed with actual controller movement after
        # isolated position setup. No position writes while pressing into it.
        ordinary=False;restore(base);clear_enemies();w16('hp',100);w16('spawnTimer',60000)
        if label in ('7','8'):write(syms['campaignResistance'][0]+2,struct.pack('>H',60000))
        solids=geom['favela_solids'] if label in ('7','8') else geom['union_solids'];collision=[]
        for rx,ry,rw,rh in solids:
            ordinary=False
            bounds=geom['favela_bounds'] if label in ('7','8') else geom['union_bounds']
            if rx-17>=bounds[0]:
                pos(rx-17,ry+max(0,(rh-16)//2));ordinary=True;hold({7},fps//2)
                collision.append({'solid':[rx,ry,rw,rh],'face':'west','end_x':signed('px'),'passed':signed('px')+16<=rx})
            else:
                # Attached depot has no legal western approach. Push its front
                # from the courtyard instead; keep the same real footprint test.
                pos(rx+(rw-16)//2,ry+rh+1);ordinary=True;hold({4},fps//2)
                collision.append({'solid':[rx,ry,rw,rh],'face':'south','end_y':signed('py'),'passed':signed('py')>=ry+rh})
        r['controller_collision']={'passed':all(c['passed'] for c in collision),'probes':collision,'setup':'RAM positions at each wall; collision attempts use controller only'}
        bounds=geom['favela_bounds'] if label in ('7','8') else geom['union_bounds'];limits=[]
        for edge,x,y,key in [('left',bounds[0],176,6),('right',bounds[2]-15,176,7),('top',80,bounds[1],4),('bottom',80,bounds[3]-15,5)]:
            ordinary=False;pos(x,y);ordinary=True;hold({key},fps//2)
            ok=bounds[0]<=signed('px')<=bounds[2]-15 and bounds[1]<=signed('py')<=bounds[3]-15
            limits.append({'edge':edge,'position':[signed('px'),signed('py')],'passed':ok})
        r['controller_bounds']={'passed':all(v['passed'] for v in limits),'probes':limits,'setup':'RAM seeds legal positions; controller pushes against each map boundary'}

        ordinary=False;restore(base);ordinary=True
        before=frames();vb=u32('vtimer');peak=0;hpstart=u16('hp')
        if args.movie:
            encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb565le','-s','320x224','-r',str(fps),'-i','-','-an','-vf','scale=640:448:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(label+'-playtest.mp4'))],stdin=subprocess.PIPE);record=True
        for tick in range(fps*20):
            buttons.clear();buttons.update({1,[7,5,6,4][(tick//(fps*2))%4]});run()
            peak=max(peak,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
            if state()!=1 or signed('hp')<=0:break
        if args.movie:
            record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
        buttons.clear();r['difficulty_sample']={'controller_only':True,'duration_seconds':round((u32('vtimer')-vb)/fps,2),'result':'defeat' if signed('hp')<=0 else {3:'defeat',4:'completed'}.get(state(),'timeout'),'initial_hp':hpstart,'remaining_hp':signed('hp'),'damage_net':hpstart-signed('hp'),'peak_enemies':peak,'simulation_fps':round(fps*(frames()-before)/max(1,u32('vtimer')-vb),2),'scope':'20s automated movement/fire pressure sample; not a human difficulty rating'}
        # Isolated enemy saturation: real spawn loop and occupied production
        # pools; immortality is reseeded and reported as a stress-only probe.
        ordinary=False;restore(base);w16('hp',30000)
        if label=='7':write(syms['campaignResistance'][0]+2,b'\0\0')
        if label=='8':write(syms['campaignResistance'][0]+2,b'\0\0')
        initial=frames();vb=u32('vtimer');peak=0
        for tick in range(fps*20):
            if tick%fps==0:w16('hp',30000)
            run();peak=max(peak,sum(read(enemy_addr+i*stride+44,1)[0]!=0 for i in range(16)))
            if state()!=1:break
        elapsed=u32('vtimer')-vb;sim=frames()-initial
        cap=r['entry']['enemy_cap'];r['saturation']={'passed':peak<=cap,'peak_enemies':peak,'cap':cap,'simulation_fps':round(fps*sim/max(1,elapsed),2),'setup':'RAM seeded health; no shots fired; production reinforcements fill pool'};shot(label+'-saturation')
        # Worst visible formation at the configured cap, with both6-shot
        # pools occupied. Re-seeding is intentionally RAM-only stress setup.
        ordinary=False;restore(base);clear_enemies();w16('hp',30000);cap=r['entry']['enemy_cap']
        def formation():
            w16('hp',30000)
            for i in range(cap):
                x,y=64+i*40,184;kind=0 if label=='8' and i<3 else [4,5,2][i%3]
                if label=='8' and i>=3:kind=5
                buf=bytearray(stride);struct.pack_into('>hhii',buf,0,x,y,x<<6,y<<6);struct.pack_into('>hhHH',buf,12,16,0,600,600)
                buf[30],buf[31],buf[43],buf[44]=kind,250,1,1;write(enemy_addr+i*stride,buf)
            for name in ('pshots','eshots'):
                address,size=syms[name]
                for i in range(6):
                    buf=bytearray(20);struct.pack_into('>iiii',buf,0,(32+i*40)<<6,(112+(i%2)*24)<<6,32,0);buf[17],buf[18]=1,1;write(address+i*20,buf)
        for _ in range(30):formation();run()
        start=frames();vb=u32('vtimer');loads=[]
        for _ in range(fps*5):
            formation();run()
            if 'cpuFrameLoad' in syms:loads.append(u16('cpuFrameLoad')*100/2048)
        measured=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),2)
        r['visible_maximum_stress']={'passed':measured>=fps*.95,'simulation_fps':measured,'seeded_visible_enemies':cap,'seeded_player_shots':6,'seeded_enemy_shots':6,'cpu_mean_percent':round(statistics.mean(loads),2) if loads else None,'cpu_peak_percent':round(max(loads),2) if loads else None,'setup':'RAM seeds simultaneous horizontal formation and full configured shot pools eachframe; not ordinary gameplay'}
        save()
    report['passed']=all(v.get('passed',True) for node in report['nodes'].values() for v in node.values());save();print(json.dumps(report,indent=2))
    core.retro_unload_game();core.retro_deinit()
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
