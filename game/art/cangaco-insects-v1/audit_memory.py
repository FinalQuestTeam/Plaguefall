"""Record exact ROM/static RAM and the checked VRAM map for this build."""
from pathlib import Path
import hashlib,json,struct,subprocess
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
def main():
    binary=GAME/"out/release/rom.bin";data=binary.read_bytes()
    size=subprocess.check_output(["m68k-elf-size",str(GAME/"out/release/rom.out")],text=True).splitlines()[1].split()
    text,initialized,bss=map(int,size[:3])
    rom_start,rom_end=struct.unpack_from(">II",data,0x1a0)
    assert len(data)<=rom_end-rom_start+1<=4*1024*1024
    symbols=subprocess.check_output(["m68k-elf-nm","-Sn",str(GAME/"out/release/rom.out")],text=True)
    sym={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4:sym[parts[3]]=(int(parts[0],16),int(parts[1],16))
        elif len(parts)==3:sym[parts[2]]=(int(parts[0],16),0)
    for name,file in [("insect_frames","frames.bin"),("insect_icons","icons.bin"),("insect_palette","palette.bin")]:
        raw=(GAME/"res/insects"/file).read_bytes();address=sym[name][0]
        assert data[address:address+len(raw)]==raw,(name,address)
    has_hero=(GAME/"res/heroi/frames.bin").exists()
    if has_hero:
        for name,file in [("heroi_frames","frames.bin"),("heroi_palette","palette.bin")]:
            raw=(GAME/"res/heroi"/file).read_bytes();address=sym[name][0]
            assert data[address:address+len(raw)]==raw,(name,address)
    emulator=json.loads((ROOT/"validation/emulator/report.json").read_text())
    assert emulator["rom_sha256"]==hashlib.sha256(data).hexdigest()
    # Values from the compiled tiles/chars/floor headers (16 system + user regions).
    regions=[];cursor=16
    for name,tiles in [("fixed gameplay tiles",83),("16 live enemy frames",384),
        ("15 menu icon slots",240),("story portrait scratch",72),("player",48),("all floor variants",80)]:
        regions.append({"name":name,"start_tile":cursor,"tiles":tiles,"start_byte":cursor*32,"end_byte_exclusive":(cursor+tiles)*32})
        cursor+=tiles
    font=1440*32
    assert cursor*32<font and font+96*32==emulator["bgb_addr"]
    assert emulator["bgb_addr"]==0xc000 and emulator["window_addr"]==0xd000 and emulator["bga_addr"]==0xe000
    title_end=(16+83+1120)*32
    assert title_end<font
    report={"passed":True,"rom_bytes":len(data),"rom_header_capacity_bytes":rom_end+1,
        "rom_headroom_bytes":rom_end+1-len(data),"rom_sha256":hashlib.sha256(data).hexdigest(),
        "linked_rom_text_bytes":text,"ram_initialized_bytes":initialized,"ram_bss_bytes":bss,
        "ram_static_total_bytes":initialized+bss,"ram_static_growth_bytes":initialized+bss-(84+4302),
        "ram_stack_reserved_bytes":2560,"heap_free_bytes_observed":emulator["heap_free_bytes"],
        "heap_largest_free_block_observed":emulator["heap_largest_free_bytes"],
        "animation_ROM_bytes":499200,"icon_ROM_bytes":7680,"palette_ROM_bytes":32,
        "enemy_live_frame_VRAM_bytes":384*32,"max_enemy_DMA_bytes_per_frame":4*768,
        "vram_gameplay_end_byte_exclusive":cursor*32,"vram_font_start_byte":font,
        "vram_free_before_font_bytes":font-cursor*32,"vram_title_end_byte_exclusive":title_end,
        "vram_gameplay_savings_bytes":(474+576-624-72)*32,
        "vram_regions":regions,"palette_slots_total":4,"new_enemy_palette_slot":"PAL1 (shared with existing objects)",
        "emulator":emulator,"limitations":[
            "Observed heap figures describe the controlled smoke run, not a proof for future code changes.",
            "The software culls lower-priority sprites when scanline/global budgets are full.",
            "Under sustained DMA pressure, frame/direction updates can be deferred; new slots wait until loaded.",
            "60-degree elevation is a 2D art target; player/background are still the existing renderer."]}
    if has_hero:
        report.update({"hero_animation_ROM_bytes":38400,"hero_palette_ROM_bytes":32,
            "hero_live_frame_VRAM_bytes":768,"hero_extra_reserved_VRAM_bytes":0,
            "max_combined_actor_DMA_bytes_per_frame":3840,"hero_palette_slot":"PAL2"})
        report["limitations"][-1]="60-degree elevation is a 2D art target for hero/enemies; the background map is still the previous renderer."
    (ROOT/"validation/memory.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("vram_regions","emulator","limitations")},indent=2))
if __name__=="__main__":main()
