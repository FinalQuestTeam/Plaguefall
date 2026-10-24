"""Run real-ROM volley regressions across the campaign (Genesis Plus GX).

Run with arch -x86_64 /usr/bin/python3. Fixtures select phases, equipment,
rosters and projectile occupancy through RAM, then production firing, AI,
collision and rendering execute unchanged. Inactive projectile coordinates
are marked before each measured volley so consumed bullets remain countable.
No ROM patches or production instrumentation are used.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, json, struct, subprocess, zlib
from collections import Counter, defaultdict

GAME=Path(__file__).resolve().parents[1]
import re
CAMPAIGN_NODE_COUNT=len(re.findall(r'\bN_[A-Za-z0-9]+\b',re.search(r'typedef enum\s*\{(.*?)NODE_MAX',(GAME/'src/levels/graph.h').read_text(),re.S)[1]))

CORE=Path.home()/'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'

def png(path,w,h,rgb):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--build-dir',type=Path);parser.add_argument('--nodes',type=int,nargs='+',default=list(range(1,CAMPAIGN_NODE_COUNT+1)));parser.add_argument('--quick',action='store_true');args=parser.parse_args()
    fps=50 if args.pal else 60
    out=args.output or GAME/'art/player-shots-v1/validation'/('pal' if args.pal else 'ntsc');out.mkdir(parents=True,exist_ok=True)
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
    fmt=0;raw=None;w=h=pitch=0;buttons=set()
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
    writes=0
    def write(addr,value):
        nonlocal writes
        writes+=1
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

    core.retro_serialize_size.restype=C.c_size_t
    core.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_serialize.restype=C.c_bool
    core.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];core.retro_unserialize.restype=C.c_bool

    def snapshot():
        n=core.retro_serialize_size();buf=C.create_string_buffer(n)
        assert core.retro_serialize(buf,n)
        return buf
    def restore(buf):
        buttons.clear();assert core.retro_unserialize(buf,len(buf))
    def state():return u32('flow_state')
    def textrow(row):
        return ''.join(chr((vw(0xe000+(row*64+x)*2)&2047)-1440+32)
                       if 1440<=(vw(0xe000+(row*64+x)*2)&2047)<1536 else '.' for x in range(40))
    def until(predicate,label,limit=fps*20):
        for _ in range(limit):
            if predicate():return
            run()
        shot('FAIL-'+label);raise AssertionError((label,state(),u8('currentLevel')))
    def byte(name,value):write(syms[name][0],bytes([value]))
    def records(name):
        return [struct.unpack('>iiiiBBBB',read(syms[name][0]+i*20,20)) for i in range(16)]
    def tick():return int.from_bytes(read(syms['phaseStats'][0]+4,4),'big')
    names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
    defs=['','01','02','02b','03','04','05','06','06b','07','08','09','10','10b','11','12','13','13b','14','15','16']
    type_names=['SQ_RED','SQ_YEL','SQ_PUR','SQ_ORG','TRI_RED','TRI_YEL','TRI_PUR','TRI_ORG','PEN_RED','PEN_YEL','PEN_PUR','PEN_ORG','DUMMY','TARGET','BOSS']
    import re
    report=dict(passed=False,region='PAL' if args.pal else 'NTSC',fps=fps,
                rom_sha256=hashlib.sha256(original).hexdigest(),rom_patched=False,
                method='Real production ROM. RAM fixtures select phases/equipment/rosters/pool occupancy and protect objectives. Inactive projectile coordinates are marked before firing; raw projectile records count newly created bullets even if immediately consumed by collision.',
                quick=args.quick,phases=[],training=[],failures=[],cases=0,volleys=0,projectiles=0)
    def save():
        report['ram_fixture_writes']=writes
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def phase_info(node):
        source=(GAME/'src/levels/defs'/('level'+defs[node]+'.c')).read_text()
        def cap(name,default):
            found=re.search(r'\.'+name+r'\s*=\s*(\d+)',source)
            return int(found[1]) if found and int(found[1]) else default
        roster=re.search(r'static const u8 roster\[\]\s*=\s*\{([^}]+)',source)[1]
        types=[type_names.index(t) for t in re.findall(r'ENEMY_([A-Z_]+)',roster)]
        return dict(node=node,phase=names[node],shot_cap=cap('shotCap',16),enemy_cap=cap('enemyCap',15),roster=types)
    def protect():
        w16('hp',100);w16('invTimer',60000);w16('shieldTimer',60000)
        w16('spawnTimer',60000);w16('kills',0)
        if 'surviveLeft' in syms:w16('surviveLeft',60000)
        if 'npcHp' in syms:w16('npcHp',30000)
    def seed_enemies(types,count,dense=False,status=0):
        assert syms['enemies'][1]==16*46
        write(syms['enemies'][0],bytes(16*46))
        x,y=u16('px'),u16('py')
        left,right=u16('arenaMinX'),u16('arenaMaxX')
        top,bottom=u16('arenaMinY'),u16('arenaMaxY')
        for i in range(count):
            ex=max(left,min(right-48,x+48+(i%4)*(4 if dense else 32)))
            ey=max(top,min(bottom-48,y-70+(i//4)*(4 if dense else 30)))
            e=bytearray(46)
            struct.pack_into('>hhii',e,0,ex,ey,ex*64,ey*64)
            struct.pack_into('>H',e,16,1) # live firing AI
            e[30]=types[i%len(types)];e[31]=200
            if status==1:struct.pack_into('>H',e,32,60000)
            if status==2:
                struct.pack_into('>H',e,34,60000);struct.pack_into('>H',e,36,60000)
            e[42]=int(e[30] in (2,6,10));e[44]=1
            write(syms['enemies'][0]+i*46,e)
    def seed_pool(name,cap,occupancy):
        write(syms[name][0],bytes(16*20))
        for i in range(cap):
            active=occupancy=='full' or (occupancy=='fragmented' and i%3!=1)
            write(syms[name][0]+i*20,struct.pack('>iiiiBBBB',-200*64,-200*64,0,0,0 if name=='pshots' else 1,10,int(active),0))
    def mark_inactive():
        for i,s in enumerate(records('pshots')):
            if not s[6]:write(syms['pshots'][0]+i*20,struct.pack('>ii',-4096*64,-4096*64))
    def expected_velocities(power,dx,dy,bonus):
        speed=192*(100+bonus)//100
        distance=(max(abs(dx),abs(dy))*64*246+min(abs(dx),abs(dy))*64*102)>>8
        vx,vy=int(dx*64*speed/distance),int(dy*64*speed/distance)
        return {(vx-int(vy*o/8),vy+int(vx*o/8)) for o in range(1-power,power,2)}
    def check_volley(power,dx,dy,bonus,label,mode=0):
        expected=expected_velocities(power,dx,dy,bonus)
        groups=defaultdict(list)
        px,py=u16('px'),u16('py')
        steps=max(1,fps*8//10-u16('shotCooldown')+1)
        for i,s in enumerate(records('pshots')):
            x,y,vx,vy,mode,dmg,active,pose=s
            if (vx,vy) not in expected or s[4]!=mode:continue
            moved=steps if active else 1
            origin=(x-moved*vx,y-moved*vy)
            if abs(origin[0]-px*64)<=48*64 and abs(origin[1]-py*64)<=48*64:
                groups[origin].append((i,vx,vy,active))
        matches=[v for v in groups.values() if len(v)==power and {(s[1],s[2]) for s in v}==expected]
        report['volleys']+=1
        if len(matches)!=1:
            failure=dict(case=label,expected=power,velocities=sorted(expected),groups={str(k):v for k,v in groups.items()},cooldown=u16('shotCooldown'))
            report['failures'].append(failure);save();shot('FAIL-volley-'+str(len(report['failures'])))
            raise AssertionError(failure)
        report['projectiles']+=power
        return matches[0]
    # Reach campaign preparation through real menus, then select each node.
    try:
        run(120);press(3);run(fps*4);title=snapshot();press(1)
        until(lambda:state()==6,'opening-story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COME' in textrow(26),'preparation')
        until(lambda:not u8('transitioning'),'ready');run(2)
        baseline=snapshot()
        dirs=[('E',1,0),('SE',1,1),('S',0,1),('SW',-1,1),('W',-1,0),('NW',-1,-1),('N',0,-1),('NE',1,-1)]
        for node in args.nodes:
            info=phase_info(node);restore(baseline);byte('pendingLevel',node);press(1)
            until(lambda:state()==1 and u8('currentLevel')==node,'phase-'+str(node));run(2)
            protect();stage=snapshot();begin_cases=report['cases'];begin_shots=report['projectiles']
            powers=[5] if args.quick else range(1,6)
            directions=dirs[:2] if args.quick else dirs
            for power in powers:
                for name,dx,dy in directions:
                    for occupancy in ('empty','fragmented','full'):
                        for count in (0,info['enemy_cap']):
                            for bonus in (0,100):
                                restore(stage);protect();seed_enemies(info['roster'],count)
                                seed_pool('pshots',info['shot_cap'],occupancy)
                                seed_pool('eshots',info['shot_cap'],'full' if count else 'empty')
                                byte('shotPower',power);byte('speedPct',bonus)
                                byte('shotMode',0);byte('modeCharges',0)
                                w16('faceX',dx);w16('faceY',dy);w16('shotCooldown',0);byte('fireArmed',1)
                                label=f"{info['phase']}/p{power}/{name}/{occupancy}/e{count}/speed{bonus}"
                                before=tick();buttons.add(1)
                                until(lambda:u16('shotCooldown')>0,label,6)
                                assert state()==1 and not u8('gameOver'),label
                                assert tick()-before<=2,(label,'ambiguous sampling')
                                check_volley(power,dx,dy,bonus,label)
                                assert sum(s[6]!=0 for s in records('pshots'))<=info['shot_cap'],label
                                report['cases']+=1
            # Sustained combat: six volleys with real cadence and moving/firing AI.
            for count in (1,min(4,info['enemy_cap']),info['enemy_cap']):
                restore(stage);protect();seed_enemies(info['roster'],count,dense=True)
                seed_pool('pshots',info['shot_cap'],'full');seed_pool('eshots',info['shot_cap'],'full')
                byte('shotPower',5);byte('speedPct',0);byte('modeCharges',0)
                w16('faceX',1);w16('faceY',0);w16('shotCooldown',0);byte('fireArmed',1)
                buttons.add(1);observed=0;start_ticks=tick();start_vblank=u32('vtimer')
                for _ in range(fps*30):
                    if u16('shotCooldown')<=1:mark_inactive()
                    old=u16('shotCooldown');run()
                    if u16('shotCooldown')>old:
                        check_volley(5,1,0,0,f"{info['phase']}/autofire/e{count}/{observed}")
                        observed+=1
                    assert state()==1 and not u8('gameOver'),('combat stopped',info['phase'])
                    if observed>=6:break
                assert observed>=6,(info['phase'],'autofire missed',observed)
                report['cases']+=1
                info.setdefault('sustained',[]).append(dict(enemies=count,volleys=observed,
                    updates=tick()-start_ticks,vblanks=u32('vtimer')-start_vblank))
            info['cases']=report['cases']-begin_cases;info['projectiles']=report['projectiles']-begin_shots
            report['phases'].append(info);save()
            print(json.dumps(dict(region=report['region'],phase=info['phase'],cases=info['cases'],projectiles=info['projectiles'],failures=len(report['failures']))),flush=True)
            shot('phase-'+info['phase'])
        # Combat lab loads every real enemy species; cover homogeneous groups
        # up to its legal 16-actor limit and all four player ammunition modes.
        restore(title)
        for _ in range(3):press(5)
        press(1);run(fps)
        for _ in range(4):hold({5},6);run(8)
        hold({1},6)
        until(lambda:state()==1 and u8('currentLevel')==0 and u8('testStage')==5,'combat-lab')
        run(3);protect();lab=snapshot()
        for kind in list(range(12))+[14]:
            begin_cases=report['cases'];begin_shots=report['projectiles']
            for count in (1,4,8,16):
                for mode in range(4):
                    for name,dx,dy in dirs:
                        for occupancy in ('empty','fragmented','full'):
                            restore(lab);protect();seed_enemies([kind],count,dense=True,status=mode%3)
                            seed_pool('pshots',16,occupancy);seed_pool('eshots',16,'full')
                            bonus=100 if mode&1 else 0
                            byte('shotPower',5);byte('speedPct',bonus)
                            byte('shotMode',mode);byte('modeCharges',2 if mode else 0)
                            w16('faceX',dx);w16('faceY',dy);w16('shotCooldown',0);byte('fireArmed',1)
                            label=f"lab/{kind}/e{count}/mode{mode}/{name}/{occupancy}"
                            buttons.add(1);until(lambda:u16('shotCooldown')>0,label,6)
                            check_volley(5,dx,dy,bonus,label,mode)
                            assert u8('modeCharges')==(1 if mode else 0),label
                            assert state()==1 and not u8('gameOver'),label
                            report['cases']+=1
            value=dict(enemy_type=kind,enemy_name=type_names[kind],counts=[1,4,8,16],
                       modes=[0,1,2,3],statuses=['normal','frozen','burning'],
                       cases=report['cases']-begin_cases,projectiles=report['projectiles']-begin_shots)
            report['training'].append(value);save()
            print(json.dumps(dict(region=report['region'],training=value)),flush=True)
        shot('combat-lab-final')
        report['passed']=not report['failures'];save()
        print(json.dumps({k:report[k] for k in ('passed','region','cases','volleys','projectiles')}),flush=True)
    finally:
        save();core.retro_unload_game();core.retro_deinit()


if __name__=='__main__':main()
