"""Campaign stages in the FINAL production ROM. Run with arch -x86_64 /usr/bin/python3.

Explicit RAM setup isolates nodes and probes. Ordinary match loops enable a
write guard: after each baseline restore, ONLY controller input is permitted.
FPS uses phaseStats.frames / vtimer, never host execution speed.
"""
from pathlib import Path
import os,argparse, ctypes as C, hashlib, json, statistics, struct, subprocess, wave, zlib

GAME=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(GAME/'tools'))
from campaign_geometry import closest,faces,edges
CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--movie',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--matches',type=int,default=2);parser.add_argument('--nodes',default='1,2,3,4,5,6');parser.add_argument('--seconds',type=int,default=150);parser.add_argument('--only-entry',action='store_true');parser.add_argument('--no-stress',action='store_true');parser.add_argument('--shield-tests',action='store_true');parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/campaign-early-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
    build=args.build_dir or Path('/tmp/plaguefall-early-build/game/out/release');rom=build/'rom.bin';original=rom.read_bytes();data=bytearray(original)
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
    def state():return u32('flow_state')
    def frames():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def zeros(name):write(syms[name][0],bytes(syms[name][1]))
    def isolate():
        w16('spawnTimer',60000);zeros('enemies');zeros('pshots');zeros('eshots')
    def enter(node,ruined=False):
        restore(baseline)
        if node!=1:
            isolate();w16('freezeTimer',0);w16('surviveLeft',1);run(4*fps)
            # Complete the real map/story transition before choosing a node;
            # changing pendingLevel earlier can strand the map's heap buffer.
            for _ in range(60):
                if state()==0:break
                if state() in (4,6):press(3)
                elif state()==5:press(1)
                run(fps//2)
            assert state()==0,('prep entry',state())
            write(syms['pendingLevel'][0],bytes([node]));
            if node==4:write(syms['campaignFlags'][0],bytes([1 if ruined else 0]))
            press(1);run(fps*4)
            assert state()==1 and u8('currentLevel')==node
        for _ in range(8*fps):
            if u16('freezeTimer')==0 and frames()>=5:break
            run()
        assert state()==1 and u8('currentLevel')==node
        return snapshot()
    def enemy_list():
        result=[]
        for i in range(16):
            address=enemy_addr+i*stride
            if read(address+44,1)[0]:
                x,y=struct.unpack('>hh',read(address,4));kind=read(address+30,1)[0]
                result.append((x,y,kind))
        return result
    def seed(i,kind,x,y,hp=20):
        b=bytearray(stride);struct.pack_into('>hhii',b,0,x,y,x<<6,y<<6)
        struct.pack_into('>HH',b,16,600,600);b[30]=kind;b[31]=hp;b[43]=1;b[44]=1
        write(enemy_addr+i*stride,b)
    def free(d,x,y):
        l,t,r,b=d['bounds']
        return l<=x<=r-15 and t<=y<=b-15 and not any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,*_ in d['solids'])
    manifest=json.loads((GAME/'art/campaign-early-v1/manifest.json').read_text())['stages']
    ids={1:'01',2:'02A',3:'02B',4:'03',5:'04',6:'05'}
    report={'passed':False,'region':'PAL' if args.pal else 'NTSC','rom_sha256':hashlib.sha256(original).hexdigest(),'rom':str(rom),'isolated_build':build.resolve()!=(GAME/'out/release').resolve(),'method':'RAM only prepares isolated nodes/collision/load probes; ordinary matches enable a write guard and use controller only. FPS derived from logical phase frames / VBlanks, not host time.','stages':[],'failures':[]}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def check(name,fn,result):
        try:result[name]={'passed':True,'details':fn()};print('PASS',name,flush=True)
        except Exception as exc:result[name]={'passed':False,'error':repr(exc)};report['failures'].append({'check':name,'error':repr(exc)});print('FAIL',name,repr(exc),flush=True)
        save()
    for node in [int(n) for n in args.nodes.split(',')]:
        key=ids[node];d=manifest[key];initial=enter(node);entry=out/(key+'-entry.png');shot(key+'-entry')
        result={'phase':key,'node':node,'checks':{},'ordinary_matches':[]};report['stages'].append(result)
        def entry_probe():
            assert [signed(n) for n in ['arenaMinX','arenaMinY','arenaMaxX','arenaMaxY']]==d['bounds']
            if d['objective'] in ['survive','protect']:assert 0<u16('surviveLeft')<=d['target']*fps
            if node==6:assert u16('npcHp')==180
            return {'bounds':d['bounds'],'target':d.get('target'),'atlas_tiles':d['tiles'],'enemy_cap':d['enemy_cap'],'shots_each_pool':d['shot_cap']}
        check(key+'/entry',entry_probe,result['checks'])
        if args.only_entry:continue
        def atlas_probe():
            restore(initial);isolate();run(4)
            source=GAME/'res/courtyard' if node in (1,2) else GAME/'art/campaign-pattern-v2/early'/({3:'02B-ruins',4:'03-street',5:'04-warehouse',6:'05-signal'}[node])
            if node==4 and d.get('native_bank'):source=GAME/d['native_bank']
            rawtiles=(source/'tiles.bin').read_bytes();actual=bytes(vram[(785*32+i)^1] for i in range(len(rawtiles)))
            assert actual==rawtiles,'VRAM atlas differs from export'
            rawmap=struct.unpack('>'+str(d['width']//8*d['height']//8)+'H',(source/'map.bin').read_bytes())
            samples=0
            for sample_index,(x,y) in enumerate([(d['start'][0],d['start'][1]),(d['width']//2,d['bounds'][1]+16),(d['width']-128,d['bounds'][3]-40),(48,d['bounds'][1]+16),(d['width']//2,d['bounds'][3]-16)]):
                x,y=closest(d,x,y);pos(x,y);run(fps*12);cx=u16('cameraX')//8;cy=u16('cameraY')//8;cols=d['width']//8
                for ty in range(cy,min(cy+28,d['height']//8)):
                    for tx in range(cx,min(cx+40,cols)):
                        got=vw(0xc000+((ty&31)*64+(tx&63))*2)&0x1fff
                        expected=(785+(rawmap[ty*cols+tx]&2047))|(rawmap[ty*cols+tx]&0x1800)
                        assert got==expected,('ring',tx,ty,got,rawmap[ty*cols+tx]);samples+=1
                shot(key+'-camera-sample-'+str(sample_index))
            shot(key+'-camera-return');return {'atlas_matches':True,'ring_cells_compared':samples,'camera_return_checked':True}
        check(key+'/atlas-camera',atlas_probe,result['checks'])
        def collisions():
            restore(initial);isolate();w16('shieldTimer',60000)
            probes=0;l,t,r,b=d['bounds']
            for x,y,k,axis,limit in edges(d):
                pos(x,y);hold({k},40);assert signed(axis)==limit,(axis,signed(axis),limit);probes+=1
            for rx,ry,rw,rh,*_ in d['solids']:
                for x,y,k,axis,limit,sign in [(rx-24,ry,7,'px',rx-16,1),(rx+rw+8,ry,6,'px',rx+rw,-1),(rx,ry-24,5,'py',ry-16,1),(rx,ry+rh+8,4,'py',ry+rh,-1)]:
                    if not free(d,x,y):continue
                    pos(x,y);hold({k},36);value=signed(axis)
                    assert value<=limit if sign==1 else value>=limit,(rx,ry,k,value,limit)
                    probes+=1
            return {'movement_face_probes':probes,'player_footprint':16,'static_reachability':d['geometry_validation']}
        check(key+'/collision',collisions,result['checks'])
        def cap_and_load():
            restore(initial);isolate();w16('shieldTimer',60000);w16('freezeTimer',0)
            l,t,r,b=d['bounds'];samples=[];peaks=[0,0,0];begin=frames();vb=u32('vtimer')
            for tick in range(600):
                x=l+32+(tick*4)%max(1,r-l-80);y=t+64
                if not free(d,x,y):x,y=d['start']
                pos(x,y);w16('hp',100);w16('spawnTimer',60000)
                if node in (1,6):w16('surviveLeft',60*fps)
                if node==6:w16('npcHp',180)
                for i in range(d['enemy_cap']):seed(i,d['roster'][i%len(d['roster'])],max(l,min(r-31,x+32+(i%2)*64)),t+24+(i//2)*64)
                for name in ('pshots','eshots'):
                    address,size=syms[name]
                    for i in range(6):
                        buf=bytearray(20);struct.pack_into('>iiii',buf,0,(x+16+i%3*16)<<6,(t+80+i//3*24)<<6,32,0);buf[17]=buf[18]=1;write(address+i*20,buf)
                run();samples.append(u16('cpuFrameLoad')*100/2048)
                peaks[0]=max(peaks[0],len(enemy_list()))
                for j,name in enumerate(('pshots','eshots'),1):peaks[j]=max(peaks[j],sum(read(syms[name][0]+i*20+18,1)[0]!=0 for i in range(16)))
                assert state()==1
            rate=fps*(frames()-begin)/max(1,u32('vtimer')-vb)
            assert peaks[0]<=d['enemy_cap'] and peaks[1]<=6 and peaks[2]<=6,peaks
            return {'frames':frames()-begin,'vblanks':u32('vtimer')-vb,'fps':round(rate,2),'nominal_region_fps':fps,'cpu_mean_pct':round(statistics.mean(samples),2),'cpu_p95_pct':round(sorted(samples)[int(len(samples)*.95)],2),'peak_enemies':peaks[0],'peak_player_shots':peaks[1],'peak_enemy_shots':peaks[2],'setup':str(d['enemy_cap'])+' enemies and six shots per pool refreshed each VBlank; RAM controlled load, full production update/render'}
        if not args.no_stress:check(key+'/load',cap_and_load,result['checks'])
        if node==4:
            def traversal():
                nonlocal ordinary
                restore(initial);isolate();w16('shieldTimer',60000)
                before=writes;begin=frames();vb=u32('vtimer');ordinary=True;index=1
                points=d['traversal_points'];samples=[]
                for tick in range(fps*90):
                    if state()!=1:break
                    x,y=signed('px'),signed('py');tx,ty=points[min(index,len(points)-1)]
                    if abs(tx-x)<=3 and abs(ty-y)<=3 and index<len(points)-1:index+=1;tx,ty=points[index]
                    keys=set()
                    if abs(tx-x)>3:keys.add(7 if tx>x else 6)
                    elif abs(ty-y)>3:keys.add(5 if ty>y else 4)
                    buttons.clear();buttons.update(keys);run()
                    if tick%(fps*2)==0:samples.append([signed('px'),signed('py')])
                ordinary=False;buttons.clear();assert writes==before
                assert state()==4,('blocked street route',signed('px'),signed('py'),index)
                shot(key+'-traversal-complete')
                return dict(controller_only=True,combat_isolated=True,passed=True,waypoints=len(points),samples=samples,seconds=round((frames()-begin)/fps,2),physical_seconds=round((u32('vtimer')-vb)/fps,2))
            check(key+'/full-controller-traversal',traversal,result['checks'])

            def church_continuity():
                checks=[]
                for ruined,filename in [(False,'map.bin'),(True,'damaged.bin')]:
                    enter(node,ruined);isolate();pos(*d['start']);run(fps)
                    source=GAME/'art/campaign-pattern-v2/early'/('03-street-ruined' if ruined else '03-street')
                    if d.get('native_bank'):source=(GAME/d['native_bank']).parent/('damaged-native' if ruined else 'native')
                    raw=(source/'map.bin').read_bytes();tilemap=struct.unpack('>'+str(len(raw)//2)+'H',raw);cy=u16('cameraY')//8;cx=u16('cameraX')//8
                    compared=0
                    for ty in range(cy+3,min(cy+28,d['height']//8)):
                        for tx in range(cx,min(cx+40,d['width']//8)):
                            attr=vw(0xc000+((ty&31)*64+(tx&63))*2)&0x1fff
                            expected=(785+(tilemap[ty*320+tx]&2047))|(tilemap[ty*320+tx]&0x1800)
                            assert attr==expected,('church variant',ruined,tx,ty,attr)
                            compared+=1
                    shot(key+('-church-ruined' if ruined else '-church-preserved'));checks.append(dict(ruined=ruined,tiles_compared=compared))
                return dict(passed=True,variants=checks,original_native_church=True)
            check(key+'/church-continuity',church_continuity,result['checks'])


        for trial in range(args.matches):
            if args.movie:
                encoder=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(av.timing.fps),'-i','pipe:0','-vf','scale=960:672:flags=neighbor','-c:v','libx264','-pix_fmt','yuv420p',str(out/(key+'-playtest-'+str(trial+1)+'.mp4'))],stdin=subprocess.PIPE)
                record=True
            restore(initial);waypoint=1;ordinary=True;before=writes;begin=frames();vb=u32('vtimer');peak=0;damage=0;last=signed('hp');minimum_npc=180 if node==6 else None
            for tick in range(args.seconds*fps):
                if state()!=1:break
                x,y=signed('px'),signed('py');current=enemy_list();peak=max(peak,len(current));keys={1}
                if node==4:
                    points=d['traversal_points'];tx,ty=points[min(waypoint,len(points)-1)]
                    if abs(tx-x)<=3 and abs(ty-y)<=3 and waypoint<len(points)-1:waypoint+=1;tx,ty=points[waypoint]
                    dx,dy=tx-x,ty-y
                    if abs(dx)>2:keys.add(7 if dx>0 else 6)
                    elif abs(dy)>2:keys.add(5 if dy>0 else 4)
                elif current:
                    ex,ey,kind=min(current,key=lambda e:abs(e[0]-x)+abs(e[1]-y));dx,dy=ex-x,ey-y
                    if abs(dx)+abs(dy)<48:keys.add((6 if dx>0 else 7) if abs(dx)>abs(dy) else (4 if dy>0 else 5))
                    elif abs(dx)>6 and abs(dy)>6:keys.add((5 if dy>0 else 4) if abs(dx)>abs(dy) else (7 if dx>0 else 6))
                    else:
                        desired=(1 if dx>0 else -1,0) if abs(dx)>abs(dy) else (0,1 if dy>0 else -1)
                        if (signed('faceX'),signed('faceY'))!=desired:keys.add(7 if desired[0]>0 else 6 if desired[0]<0 else 5 if desired[1]>0 else 4)
                else:keys.add((7,5,6,4)[(tick//fps+trial)%4])
                steps={4:(0,-2),5:(0,2),6:(-2,0),7:(2,0)}
                for k in list(keys):
                    if k in steps and not free(d,x+steps[k][0],y+steps[k][1]):
                        keys.remove(k)
                        candidates=[a for a,(vx,vy) in steps.items() if free(d,x+vx*8,y+vy*8)]
                        if candidates:
                            def score(a):
                                vx,vy=steps[a];xx,yy=x+vx*8,y+vy*8
                                nearest=min((abs(xx-ex)+abs(yy-ey) for ex,ey,_ in current),default=100)
                                l,t,r,b=d['bounds'];wall=min(xx-l,r-15-xx,yy-t,b-15-yy)
                                return min(nearest,96)+min(wall,32)*2
                            keys.add(max(candidates,key=score))
                if trial and current and tick>15*fps and u16('bombs') and tick%(20*fps)<2:keys.add(0)
                buttons.clear();buttons.update(keys);run()
                now=signed('hp');damage+=now<last;last=now
                if node==6 and state()==1:minimum_npc=min(minimum_npc,u16('npcHp'))
            ordinary=False;buttons.clear();assert before==writes,'ordinary playtest modified RAM'
            if args.movie:
                record=False;encoder.stdin.close();encoder.wait();assert encoder.returncode==0;encoder=None
            detail={'attempt':trial+1,'result':{3:'defeat',4:'completed'}.get(state(),'timeout'),'objective_failed':bool(read(syms['phaseStats'][0]+8,1)[0]),'game_seconds':round((frames()-begin)/fps,2),'physical_seconds':round((u32('vtimer')-vb)/fps,2),'fps':round(fps*(frames()-begin)/max(1,u32('vtimer')-vb),2),'kills':u16('kills'),'hp':signed('hp'),'minimum_npc_hp':minimum_npc,'peak_enemies':peak,'damage_events':damage,'ram_writes_during_attempt':False}
            result['ordinary_matches'].append(detail);shot(key+'-playtest-'+str(trial+1));print('MATCH',key,detail,flush=True);save()
        if node in (1,6):
            def timer_win():
                restore(initial);isolate();w16('shieldTimer',60000);begin=frames();vb=u32('vtimer');remaining=u16('surviveLeft')
                for _ in range(remaining*2+fps):
                    if state()!=1:break
                    run()
                assert state()==4 and not read(syms['phaseStats'][0]+8,1)[0]
                return {'seconds':d['target'],'remaining_timer_at_start':remaining,'logical_frames_until_completion':frames()-begin,'physical_seconds':round((u32('vtimer')-vb)/fps,2),'timer_never_patched':True}
            check(key+'/timer-victory',timer_win,result['checks'])
        if node==6:
            def abandonment_loss():
                restore(initial);isolate();pos(64,232);seed(0,5,160,184);begin=frames();history=[];prior=u16('npcHp')
                for _ in range(60*fps):
                    if state()!=1:break
                    write(enemy_addr,struct.pack('>hhii',160,184,160<<6,184<<6));run();now=u16('npcHp')
                    if now<prior:history.append({'frame':frames()-begin,'hp':now})
                    prior=now
                assert state()==4 and read(syms['phaseStats'][0]+8,1)[0]
                return {'loss_after_seconds':round((frames()-begin)/fps,2),'initial_hp':180,'contact_damage_events':history,'npc_hp_never_written':True}
            check(key+'/abandonment-failure',abandonment_loss,result['checks'])
        save()
    report['passed']=not report['failures'];save();print(json.dumps({'passed':report['passed'],'failures':report['failures'],'output':str(out/'report.json')}),flush=True)
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
