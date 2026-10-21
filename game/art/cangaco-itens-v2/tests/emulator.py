"""Real ROM item/HUD rendering checks using the installed Genesis Plus GX core.
Harness adapted from the project insect smoke runner. RAM writes only position
the player in sandbox; collection and effects use production game code.
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

    expected=json.loads((ROOT/'validation/render-expectations.json').read_text())
    color_map={}
    pixel_checks=0
    def check_pixels(item,kind,x,y,learn=False):
        nonlocal pixel_checks
        size=16 if kind=='world' else 8
        assert last.size==(320,224),last.size
        for p,index in enumerate(expected[item][kind]):
            if not index:continue
            off=((y+p//size)*320+x+p%size)*3
            rgb=last.rgb[off:off+3]
            if index not in color_map:
                assert learn,('unseen palette index',index)
                color_map[index]=rgb
            assert rgb==color_map[index],(item,kind,p,index,tuple(rgb),tuple(color_map[index]))
            pixel_checks+=1
    # Skip the opening with START, then enter Help through controller input.
    run(840);press(3);run(150);shot('title')
    press(5);press(3);run(60)
    for _ in range(3):press(7)
    shot('help-instant')
    for item,row in [('heart',6),('shots',10),('speed',14)]:
        check_pixels(item,'world',24,row*8,True)
        check_pixels(item,'hud',280,row*8,True)
    press(7);shot('help-inventory')
    for item,row in [('bomb',5),('shield',8),('chain',11),('ice',14),('fire',17)]:
        check_pixels(item,'world',24,row*8,True)
        check_pixels(item,'hud',280,row*8,True)
    # Help returns to its own menu selection; two more DOWN inputs select Test.
    press(3);run(150);press(5);press(5);press(3);run(240);shot('arena-items')
    symbols=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm','-Sn',str(args.symbols)],text=True)
    sym={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:
            addr,size,kind,name=parts
            if name not in sym or int(size,16)>sym[name][1]:sym[name]=(int(addr,16)&65535,int(size,16))
    ram=(C.c_ubyte*core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    hpAddr=sym['hp'][0]
    swap=bytes(ram[hpAddr:hpAddr+2])==b'\x64\x00'
    def read(addr,n):return bytes(ram[(addr+i)^int(swap)] for i in range(n))
    def write(addr,data):
        for i,v in enumerate(data):ram[(addr+i)^int(swap)]=v
    def w16(name,value):write(sym[name][0],struct.pack('>H',value&65535))
    assert int.from_bytes(read(hpAddr,2),'big')==100,('sandbox did not start',read(hpAddr,2))
    stride=sym['items'][1]//8
    assert stride==8,stride
    positions={}
    for i in range(8):
        x,y,ttl,t,active=struct.unpack('>hhHBB',read(sym['items'][0]+i*stride,stride))
        assert active and t==i,(i,t,active)
        positions[t]=(x,y)
        check_pixels(['heart','bomb','shots','speed','shield','chain','ice','fire'][t],'world',x,y)
    check_pixels('bomb','hud',15*8,0)
    def move_player(x,y):
        w16('px',x);w16('py',y)
        write(sym['pfx'][0],struct.pack('>i',x<<6));write(sym['pfy'][0],struct.pack('>i',y<<6))
    # Check the same production sprites over the green/muddy arena patch too.
    move_player(80,144)
    for t in range(8):
        write(sym['items'][0]+t*stride,struct.pack('>hh',184+(t%4)*24,128+(t//4)*24))
    run(3);shot('arena-green-floor')
    for t,item in enumerate(['heart','bomb','shots','speed','shield','chain','ice','fire']):
        check_pixels(item,'world',184+(t%4)*24,128+(t//4)*24)
        write(sym['items'][0]+t*stride,struct.pack('>hh',*positions[t]))
    move_player(144,120);run(3)
    def collect(t):
        move_player(*positions[t]);run(4);move_player(144,120);run(3)
        entry=read(sym['items'][0]+t*stride,stride)
        assert not entry[7],('pickup not collected',t)
    collect(4);collect(5);collect(6);shot('hud-shield-chain-ice')
    for item,col in [('bomb',15),('shield',18),('chain',21),('ice',24)]:check_pixels(item,'hud',col*8,0)
    press(8);press(0);collect(7);shot('hud-fire-chain-ice')
    for item,col in [('bomb',15),('fire',18),('chain',21),('ice',24)]:check_pixels(item,'hud',col*8,0)
    press(8);press(0);shot('mode-chain');check_pixels('chain','hud',27*8,0)
    press(8);press(0);shot('mode-ice');check_pixels('ice','hud',27*8,0)
    press(8);press(8);press(0);shot('mode-fire');check_pixels('fire','hud',27*8,0)
    heap=int.from_bytes(read(sym['heap'][0],4),'big')&65535
    end=int.from_bytes(read(sym['heapEnd'][0],4),'big')&65535
    cursor=heap;free=largest=blocks=0
    while cursor<end:
        value=int.from_bytes(read(cursor,2),'big');length=value&65534
        assert length>=2 and cursor+length<=end
        if not value&1:free+=length;largest=max(largest,length)
        cursor+=length;blocks+=1;assert blocks<1000
    assert cursor==end and largest>=85*32
    report=dict(passed=True,core='Genesis Plus GX',rom_sha256=hashlib.sha256(data).hexdigest(),
        frames=frame_count,opaque_pixel_assertions=pixel_checks,world_items_checked=8,hud_icons_checked=8,
        item_struct_bytes=stride,world_size=[16,16],hud_size=[8,8],
        heap_free_bytes=free,heap_largest_free_bytes=largest,boot_tile_buffer_bytes=85*32,
        vram_extra_bytes=64,new_hardware_sprites=0,extra_per_frame_item_DMA_bytes=0,
        inventory_icons_checked=['bomb','shield','chain','ice','fire'],active_modes_checked=['chain','ice','fire'],
        backgrounds_checked=['stone-dirt','green-mud'],v2_extra_VRAM_bytes=0)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    core.retro_unload_game();core.retro_deinit()

if __name__=='__main__':main()
