"""Headless libretro smoke test using an already installed Genesis Plus GX core.
Only the emulator's volatile game RAM is modified for the all-enemy stress view.
"""
from pathlib import Path
import ctypes as C
import json, subprocess, struct, argparse, hashlib
class Frame:
    def __init__(self,size,rgb): self.size,self.rgb=size,rgb
    def save(self,path):
        # PPM keeps the Intel emulator runner free of native Python dependencies.
        path=path.with_suffix(".ppm")
        path.write_bytes(("P6\n%d %d\n255\n"%self.size).encode()+self.rgb)

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT.parents[1]
CORE=Path.home()/"Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--core",type=Path,default=CORE)
    parser.add_argument("--rom",type=Path,default=GAME/"out/release/rom.bin")
    parser.add_argument("--symbols",type=Path,default=GAME/"out/release/rom.out")
    parser.add_argument("--benchmark",action="store_true")
    parser.add_argument("--combat",action="store_true")
    parser.add_argument("--saint",action="store_true")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--counts",default="0,1,3,8,15,16")
    parser.add_argument("--gameplay",action="store_true")
    parser.add_argument("--enemy-type",type=int,default=1)
    args=parser.parse_args()
    core=C.CDLL(str(args.core))
    class Info(C.Structure):
        _fields_=[("path",C.c_char_p),("data",C.c_void_p),("size",C.c_size_t),("meta",C.c_char_p)]
    fmt=0
    buttons=set()
    frame_count=0
    capture=False
    last=None
    directory=b"/private/tmp"
    ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
    VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
    SAMPLE=C.CFUNCTYPE(None,C.c_int16,C.c_int16)
    BATCH=C.CFUNCTYPE(C.c_size_t,C.POINTER(C.c_int16),C.c_size_t)
    POLL=C.CFUNCTYPE(None)
    INPUT=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
    @ENV
    def env(cmd,data):
        nonlocal fmt
        cmd=cmd&0xffff
        if cmd==10:
            fmt=C.cast(data,C.POINTER(C.c_int))[0]
            return fmt in (0,1,2)
        if cmd in (9,31):
            C.cast(data,C.POINTER(C.c_char_p))[0]=directory
            return True
        if cmd==3:
            C.cast(data,C.POINTER(C.c_bool))[0]=True
            return True
        if cmd==39:
            C.cast(data,C.POINTER(C.c_uint))[0]=0
            return True
        if cmd==47:
            C.cast(data,C.POINTER(C.c_int))[0]=3
            return True
        return cmd in (8,11,16,18,35,37)
    @VIDEO
    def video(data,w,h,pitch):
        nonlocal last
        if not capture or not data or data==C.c_void_p(-1).value:return
        raw=C.string_at(data,pitch*h)
        if fmt==1:
            rgb=bytearray(w*h*3)
            for y in range(h):
                for x in range(w):
                    o=(y*w+x)*3; offset=y*pitch+x*4
                    rgb[o:o+3]=bytes((raw[offset+2],raw[offset+1],raw[offset]))
            last=Frame((w,h),bytes(rgb))
        else:
            rgb=bytearray(w*h*3)
            for y in range(h):
                for x in range(w):
                    n=struct.unpack_from("<H",raw,y*pitch+x*2)[0]
                    if fmt==2:r,g,b=(n>>11)&31,(n>>5)&63,n&31; green=63
                    else:r,g,b=(n>>10)&31,(n>>5)&31,n&31; green=31
                    o=(y*w+x)*3;rgb[o:o+3]=bytes((r*255//31,g*255//green,b*255//31))
            last=Frame((w,h),bytes(rgb))
    @SAMPLE
    def sample(l,r):pass
    @BATCH
    def batch(data,n):return n
    @POLL
    def poll():pass
    @INPUT
    def input_state(port,device,index,id):
        return int(port==0 and id in buttons)
    for name,callback in [("environment",env),("video_refresh",video),("audio_sample",sample),
        ("audio_sample_batch",batch),("input_poll",poll),("input_state",input_state)]:
        getattr(core,"retro_set_"+name)(callback)
    core.retro_load_game.argtypes=[C.POINTER(Info)]
    core.retro_load_game.restype=C.c_bool
    core.retro_get_memory_data.argtypes=[C.c_uint];core.retro_get_memory_data.restype=C.c_void_p
    core.retro_get_memory_size.argtypes=[C.c_uint];core.retro_get_memory_size.restype=C.c_size_t
    core.retro_init()
    rom=args.rom
    data=rom.read_bytes(); buffer=C.create_string_buffer(data)
    assert core.retro_load_game(C.byref(Info(str(rom).encode(),C.cast(buffer,C.c_void_p),len(data),None)))
    out=(args.output.parent/(args.output.stem+"-screens") if (args.benchmark or args.combat or args.saint) and args.output else (args.output or ROOT/"validation/emulator"));out.mkdir(parents=True,exist_ok=True)
    def run(n=1):
        nonlocal frame_count
        for _ in range(n):core.retro_run();frame_count+=1
    def shot(name):
        nonlocal capture
        capture=True;run();capture=False
        assert last is not None
        last.save(out/(name+".png"))
    def press(id):
        buttons.add(id);run(2);buttons.clear();run(2)
    run(480);shot("title")
    # Open the character gallery first: Damião is the default, with eight views.
    for _ in range(2):press(5)
    press(3);run(40);shot("hero-gallery")
    press(3);run(120) # title bitmap generation precedes the half-second input lock
    # Select sandbox (next title entry after the character gallery).
    press(5)
    press(3);run(100);shot("sandbox")
    symbols=subprocess.check_output(["m68k-elf-nm","-Sn",str(args.symbols)],text=True)
    sym={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:
            addr,size,kind,name=parts
            if name not in sym or int(size,16)>sym[name][1]:sym[name]=(int(addr,16)&65535,int(size,16))
    ramPtr=core.retro_get_memory_data(2);assert ramPtr
    ram=(C.c_ubyte*core.retro_get_memory_size(2)).from_address(ramPtr)
    hpAddr=sym["hp"][0]
    swap=bytes(ram[hpAddr:hpAddr+2])==b"\x64\x00"
    def read(addr,n):
        return bytes(ram[(addr+i)^int(swap)] for i in range(n))
    def write(addr,data):
        for i,v in enumerate(data):ram[(addr+i)^int(swap)]=v
    def w16(name,value):write(sym[name][0],struct.pack(">H",value&65535))
    assert int.from_bytes(read(hpAddr,2),"big")==100,("did not enter sandbox",swap,read(hpAddr,2))
    enemyAddr,enemyBytes=sym["enemies"];stride=enemyBytes//16
    assert stride==46,stride
    if args.saint:
        # Enter the actual protect sandbox through its normal door transitions.
        for stage in range(2,7):
            w16("freezeTimer",0);w16("px",282);w16("py",88)
            write(sym["pfx"][0],struct.pack(">i",282<<6));write(sym["pfy"][0],struct.pack(">i",88<<6))
            for _ in range(120):
                run()
                if read(sym["testStage"][0],1)[0]==stage:break
            else:raise AssertionError(("door transition",stage))
            run(30)
        def clear_enemies():
            for i in range(16):write(enemyAddr+i*stride+44,b"\0")
        def u16(name):return int.from_bytes(read(sym[name][0],2),"big")
        clear_enemies();run(5)
        assert u16("npcHp")==60
        x,y=u16("npcX"),u16("npcY")
        w16("px",80);w16("py",160)
        write(sym["pfx"][0],struct.pack(">i",80<<6));write(sym["pfy"][0],struct.pack(">i",160<<6))
        seen_glow=set();body_checks=0
        for _ in range(70):
            clear_enemies();w16("freezeTimer",2);run()
            index=0;body=[];glow=[]
            for _ in range(80):
                yy,packed,attr,xx=struct.unpack(">4H",read(sym["vdpSpriteCache"][0]+index*8,8))
                tile=attr&2047;sz=packed>>8;link=packed&127
                rect=((xx&511)-128,(yy&511)-128,(((sz>>2)&3)+1)*8,((sz&3)+1)*8)
                if tile==16+72:body.append(rect)
                if tile==16+82:glow.append(rect)
                if not link:break
                index=link
            assert body==[(x,y,24,24)],body
            assert glow in ([],[(x+8,y,8,8)]),glow
            seen_glow.add(bool(glow));body_checks+=1
        assert seen_glow=={False,True}
        shot("santa-proteger")
        def contact():
            clear_enemies();w16("freezeTimer",0)
            buf=bytearray(46);struct.pack_into(">hhii",buf,0,x,y,x<<6,y<<6)
            buf[30]=0;buf[31]=20;buf[43]=1;buf[44]=1
            write(enemyAddr,buf);run(4)
        contact();assert u16("npcHp")==48,u16("npcHp")
        contact();assert u16("npcHp")==48,"invulnerability changed"
        for _ in range(360):clear_enemies();run()
        contact();assert u16("npcHp")==36,u16("npcHp")
        clear_enemies();run(25)
        report={"passed":True,"rom_sha256":hashlib.sha256(data).hexdigest(),"protect_stage":6,"native_size":[24,24],"body_sat_checks":body_checks,"glow_both_phases_verified":True,"hp_initial":60,"contact_damage":12,"invulnerability_preserved":True,"damage_after_invulnerability":True,"npc_position":[x,y],"method":"Normal door transitions into actual protect level; real SAT rectangles and HP observed, controlled enemy placement in volatile emulator RAM."}
        target=args.output or ROOT/"validation/saint.json"
        target.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
        core.retro_unload_game();core.retro_deinit();return
    if args.combat:
        # Validate the optimized info overlay against actual video pixels:
        # a changed stat must appear before the periodic6-frame refresh.
        w16("freezeTimer",0);write(sym["shotPower"][0],b"\1");write(sym["speedPct"][0],b"\0");run(8)
        capture=True;run(2);capture=False
        def info_pixels(frame):
            w,h=frame.size
            return b"".join(frame.rgb[(y*w+16)*3:(y*w+148)*3] for y in range(32,40))
        beforeInfo=info_pixels(last)
        write(sym["infoTicks"][0],b"\5");write(sym["shotPower"][0],b"\2")
        capture=True;run(2);capture=False
        assert info_pixels(last)!=beforeInfo,"HUD value change was deferred"
        write(sym["shotPower"][0],b"\1");run(2)
        sizes=[16,16,32,16,16,16,16,16,24,24,32,24,24,24,48]
        vectors=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
        slotAddr,slotBytes=sym["slots"];assert slotBytes//16==16
        shotAddr,shotBytes=sym["pshots"];assert shotBytes//16==20
        cases=0;geometry=0
        for kind,size in enumerate(sizes):
            for direction,(dx,dy) in enumerate(vectors):
                for scenario in ["hit","miss","shield","ice","fire"]:
                    w16("freezeTimer",0);w16("hp",100)
                    w16("px",120+size//2+dx*60-8);w16("py",100+size//2+dy*60-8)
                    w16("faceX",1);w16("faceY",0)
                    for i in range(16):
                        write(enemyAddr+i*46+44,b"\0")
                        write(shotAddr+i*20+18,b"\0")
                    buf=bytearray(46);struct.pack_into(">hhii",buf,0,120,100,120<<6,100<<6)
                    struct.pack_into(">HH",buf,16,600,600);buf[30]=kind;buf[31]=9
                    struct.pack_into(">H",buf,32,600);buf[42]=int(scenario=="shield");buf[43]=1;buf[44]=1
                    write(enemyAddr,buf);write(slotAddr+10,b"\0")
                    # Cold legacy icon generation can span physical VBlanks.
                    # Let3 complete draw starts settle the target before firing;
                    # otherwise RAM injection can race a cached C type register.
                    begin=int.from_bytes(read(sym["frame.0"][0],2),"big")
                    for warm in range(60):
                        run()
                        if (int.from_bytes(read(sym["frame.0"][0],2),"big")-begin)&65535>=3:break
                    else:raise AssertionError("target draw did not settle")
                    bullet=bytearray(20);x=112 if scenario=="miss" else 120+size//2-4;y=100+size//2-4
                    struct.pack_into(">4i",bullet,0,x<<6,y<<6,0,0);bullet[16]=2 if scenario=="ice" else 3 if scenario=="fire" else 0;bullet[18]=1
                    write(shotAddr,bullet);run(3)
                    expected=9 if scenario in ("miss","shield") else 8
                    assert read(enemyAddr+31,1)[0]==expected,(kind,direction,scenario,"HP",read(enemyAddr+31,1))
                    assert bool(read(shotAddr+18,1)[0])==(scenario=="miss"),(kind,direction,scenario,"shot consumed")
                    if scenario=="ice":assert 290<=int.from_bytes(read(enemyAddr+32,2),"big")<=300
                    if scenario=="fire":assert 350<=int.from_bytes(read(enemyAddr+34,2),"big")<=360
                    cases+=1
                    if scenario!="hit":continue
                    tile=419+kind*16 if kind in (12,13) else int.from_bytes(read(slotAddr+12,2),"big")+16
                    index=0;rects=[];satDebug=[]
                    for _ in range(80):
                        y,packed,attr,x=struct.unpack(">4H",read(sym["vdpSpriteCache"][0]+index*8,8))
                        artTile=attr&2047;sz=packed>>8;link=packed&127
                        satDebug.append((index,artTile,(x&511)-128,(y&511)-128,sz))
                        if tile<=artTile<tile+size*size//64:
                            x=(x&511)-128;y=(y&511)-128;w=(((sz>>2)&3)+1)*8;h=((sz&3)+1)*8
                            rects.append((x,y,x+w,y+h))
                        if not link:break
                        index=link
                    assert len(rects)==(4 if size==48 else 1),(kind,direction,tile,rects,satDebug,read(enemyAddr+30,16).hex())
                    assert (min(r[0] for r in rects),min(r[1] for r in rects),max(r[2] for r in rects),max(r[3] for r in rects))==(120,84,120+size,84+size),(kind,direction,rects)
                    geometry+=1
        report={"passed":True,"rom_sha256":hashlib.sha256(data).hexdigest(),"collision_cases":cases,"types":15,"directions":8,"scenarios":["hit","miss","shield","ice","fire"],"sat_geometry_checks":geometry,"hud_changes_immediate":True,"method":"Actual 68000 ROM: injected stationary targets/projectiles in volatile emulator RAM; checked HP, projectile consumption, status and actual SAT rectangles."}
        target=args.output or ROOT/"validation/emulator-combat.json";target.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
        core.retro_unload_game();core.retro_deinit();return
    if args.benchmark:
        # Count game draws against physical VBlanks; wall-clock/core FPS alone
        # cannot reveal a 68000 loop missing frames inside a 60Hz emulator.
        import statistics
        def u16(name):return int.from_bytes(read(sym[name][0],2),"big")
        def u32(name):return int.from_bytes(read(sym[name][0],4),"big")
        def stage(count,tick):
            w16("hp",100);w16("freezeTimer",0 if args.gameplay else 2)
            w16("px",148+tick%6);w16("py",192 if args.gameplay else 100)
            w16("faceX",1);w16("faceY",0)
            for i in range(16):
                address=enemyAddr+i*stride
                if i>=count:write(address+44,b"\0");continue
                x=20+(i%5)*58+tick%6;y=64+(i//5)*48
                buf=bytearray(46)
                struct.pack_into(">hhii",buf,0,x,y,x<<6,y<<6)
                struct.pack_into(">hh",buf,12,32,0)
                struct.pack_into(">HH",buf,16,600,(tick+i)%16)
                buf[30]=args.enemy_type;buf[31]=20;buf[43]=1;buf[44]=1
                write(address,buf)
        cases=[]
        for count in map(int,args.counts.split(",")):
            assert 0<=count<=16
            for tick in range(120):stage(count,tick);run()
            start=u16("frame.0");vstart=u32("vtimer");loads=[];profiles=[]
            for tick in range(240):
                stage(count,tick+120);run()
                loads.append(u16("cpuFrameLoad")*100/(8*256))
                if "renderProfileTicks" in sym:profiles.append(struct.unpack(">"+str(sym["renderProfileTicks"][1]//2)+"H",read(*sym["renderProfileTicks"])))
            drawn=(u16("frame.0")-start)&65535
            elapsed=u32("vtimer")-vstart
            cases.append({"enemies":count,"physical_frames":elapsed,
                "game_frames":drawn,"game_fps_at_60hz":round(60*drawn/elapsed,2),
                "cpu_load_mean_pct":round(statistics.mean(loads),2),
                "cpu_load_p95_pct":round(sorted(loads)[int(len(loads)*.95)],2)})
            if profiles:cases[-1]["render_stage_subticks"]=[round(statistics.mean(p[i] for p in profiles),2) for i in range(len(profiles[0]))]
        report={"rom":str(rom),"rom_sha256":hashlib.sha256(data).hexdigest(),
            "enemy_type":args.enemy_type,"method":"Count SPRITES_draw frame counter vs VBlank; SGDK 8-frame CPU load; moving sprites in controlled sandbox, same type, no scanline congestion. Gameplay logic active: "+str(args.gameplay)+".","cases":cases}
        target=args.output or ROOT/"validation/performance/render.json"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))
        core.retro_unload_game();core.retro_deinit();return
    # Populate one of every new enemy in a controlled arena without editing ROM.
    types=list(range(12))+[14]
    vectors=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
    peak_sat=peak_line=peak_pixels=0
    def inspect_sat():
        nonlocal peak_sat,peak_line,peak_pixels
        counts=[0]*224;pixels=[0]*224;seen=set();index=0
        while True:
            assert index<80 and index not in seen
            seen.add(index)
            entry=read(sym["vdpSpriteCache"][0]+index*8,8)
            y,packed,attr,x=struct.unpack(">HHHH",entry)
            size=packed>>8;link=packed&127;x=(x&511)-128;y=(y&511)-128
            w=(((size>>2)&3)+1)*8;h=((size&3)+1)*8
            if x<320 and x+w>0:
                for row in range(max(0,y),min(224,y+h)):
                    counts[row]+=1;pixels[row]+=w
            if link==0:break
            index=link
        assert max(counts)<=20 and max(pixels)<=320
        peak_sat=max(peak_sat,len(seen));peak_line=max(peak_line,max(counts));peak_pixels=max(peak_pixels,max(pixels))
    for phase in range(8):
        dx,dy=vectors[phase]
        for tick in range(48):
            w16("hp",100)
            w16("freezeTimer",2) # exercise drawing without combat changing the controlled poses
            for i in range(16):
                address=enemyAddr+i*stride
                if i>=len(types):write(address+44,b"\0");continue
                x=24+(i%5)*58+dx*(tick%6)
                y=60+(i//5)*56+dy*(tick%6)
                if types[i]==14:x,y=132,80
                buf=bytearray(46)
                struct.pack_into(">hhii",buf,0,x,y,x<<6,y<<6)
                struct.pack_into(">hh",buf,12,dx*32,dy*32)
                buf[30]=types[i];buf[31]=20
                buf[42]=0;buf[43]=1;buf[44]=1
                write(address,buf)
            w16("px",148+dx*64+dx*(tick%6));w16("py",96+dy*64+dy*(tick%6))
            w16("faceX",dx);w16("faceY",dy)
            run()
            inspect_sat()
        shot("all-enemies-direction-"+str(phase))
    # Observe actual RAM/VDP addresses after the run.
    heap=int.from_bytes(read(sym["heap"][0],4),"big")&65535
    heap_end=int.from_bytes(read(sym["heapEnd"][0],4),"big")&65535
    cursor=heap;free_total=largest=0;blocks=0
    while cursor<heap_end:
        size=int.from_bytes(read(cursor,2),"big");block_size=size&65534
        assert block_size>=2 and cursor+block_size<=heap_end
        if not size&1:free_total+=block_size;largest=max(largest,block_size)
        cursor+=block_size;blocks+=1
        assert blocks<1000
    assert cursor==heap_end and largest>=2656 # largest existing procedural tile buffer
    mem={"core":str(args.core),"frames":frame_count,
        "rom_sha256":hashlib.sha256(data).hexdigest(),
        "actual_sat_peak":peak_sat,"actual_scanline_sprite_peak":peak_line,"actual_scanline_pixel_peak":peak_pixels,
        "heap_free_bytes":free_total,"heap_largest_free_bytes":largest,"heap_blocks":blocks,
        "hero_directions_tested":["N","NE","L","SE","S","SO","O","NO"],
        "all_new_types":types,"enemy_struct_bytes":stride,"ram_word_swapped":swap,
        "screenshots":len(list(out.glob("*.ppm")))}
    for name in ["bga_addr","bgb_addr","window_addr","hscrl_addr","slist_addr"]:
        if name in sym:mem[name]=int.from_bytes(read(sym[name][0],2),"big")
    (out/"report.json").write_text(json.dumps(mem,indent=2)+"\n")
    print(json.dumps(mem,indent=2))
    core.retro_unload_game();core.retro_deinit()

if __name__=="__main__":main()
