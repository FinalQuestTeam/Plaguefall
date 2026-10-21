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
    rom=GAME/"out/release/rom.bin"
    data=rom.read_bytes(); buffer=C.create_string_buffer(data)
    assert core.retro_load_game(C.byref(Info(str(rom).encode(),C.cast(buffer,C.c_void_p),len(data),None)))
    out=ROOT/"validation/emulator";out.mkdir(parents=True,exist_ok=True)
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
    symbols=subprocess.check_output(["m68k-elf-nm","-Sn",str(GAME/"out/release/rom.out")],text=True)
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
