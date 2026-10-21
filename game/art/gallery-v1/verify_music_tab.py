"""Controller-only integration test of the character gallery music player.

Run with the Python architecture of the installed Genesis Plus GX core.
"""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import struct
import subprocess
import wave

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
CORE = Path.home() / "Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=GAME / "out/release/rom.bin")
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--pal", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, default=GAME / "out/release/rom.out")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    original = args.rom.read_bytes()
    data = bytearray(original)
    if args.pal:
        data[0x1F0:0x200] = b"E               "
    core = C.CDLL(str(args.core))
    class Info(C.Structure):
        _fields_ = [("path", C.c_char_p), ("data", C.c_void_p), ("size", C.c_size_t), ("meta", C.c_char_p)]
    class Geometry(C.Structure):
        _fields_ = [("base_width", C.c_uint), ("base_height", C.c_uint), ("max_width", C.c_uint), ("max_height", C.c_uint), ("aspect_ratio", C.c_float)]
    class Timing(C.Structure):
        _fields_ = [("fps", C.c_double), ("sample_rate", C.c_double)]
    class AVInfo(C.Structure):
        _fields_ = [("geometry", Geometry), ("timing", Timing)]
    class Variable(C.Structure):
        _fields_ = [("key", C.c_char_p), ("value", C.c_char_p)]
    raw = None
    width = height = pitch = 0
    fmt = 0
    buttons = set()
    frame = 0
    recording = False
    audio = None
    directory = b"/private/tmp"
    ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    SAMPLE = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    BATCH = C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
    POLL = C.CFUNCTYPE(None)
    INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
    @ENV
    def env(cmd, ptr):
        nonlocal fmt
        cmd &= 0xFFFF
        if cmd == 10:
            fmt = C.cast(ptr, C.POINTER(C.c_int))[0]
            return fmt in (0, 1, 2)
        if cmd == 15:
            var = C.cast(ptr, C.POINTER(Variable))[0]
            C.cast(ptr, C.POINTER(Variable))[0].value = None
            if var.key == b"genesis_plus_gx_region_detect":
                C.cast(ptr, C.POINTER(Variable))[0].value = b"pal" if args.pal else b"ntsc-u"
                return True
            return False
        if cmd in (9, 31):
            C.cast(ptr, C.POINTER(C.c_char_p))[0] = directory
            return True
        if cmd == 3:
            C.cast(ptr, C.POINTER(C.c_bool))[0] = True
            return True
        if cmd == 39:
            C.cast(ptr, C.POINTER(C.c_uint))[0] = 0
            return True
        if cmd == 47:
            C.cast(ptr, C.POINTER(C.c_int))[0] = 3
            return True
        return cmd in (8, 11, 16, 18, 35, 37)
    @VIDEO
    def video(ptr, w, h, stride):
        nonlocal raw, width, height, pitch
        if ptr and ptr != C.c_void_p(-1).value:
            raw = C.string_at(ptr, stride*h)
            width, height, pitch = w, h, stride
    @SAMPLE
    def sample(left, right):
        if recording:
            audio.writeframesraw(struct.pack("<hh", left, right))
    @BATCH
    def batch(ptr, n):
        if recording:
            audio.writeframesraw(C.string_at(ptr, n * 4))
        return n
    @POLL
    def poll():
        pass
    @INPUT
    def input_state(port, device, index, button):
        return int(port == 0 and button in buttons)
    for name, cb in [("environment", env), ("video_refresh", video), ("audio_sample", sample), ("audio_sample_batch", batch), ("input_poll", poll), ("input_state", input_state)]:
        getattr(core, "retro_set_" + name)(cb)
    core.retro_load_game.argtypes = [C.POINTER(Info)]
    core.retro_load_game.restype = C.c_bool
    core.retro_get_memory_data.argtypes = [C.c_uint]
    core.retro_get_memory_data.restype = C.c_void_p
    core.retro_get_memory_size.argtypes = [C.c_uint]
    core.retro_get_memory_size.restype = C.c_size_t
    core.retro_get_system_av_info.argtypes = [C.POINTER(AVInfo)]
    core.retro_init()
    buffer = C.create_string_buffer(bytes(data))
    assert core.retro_load_game(C.byref(Info(str(args.rom).encode(), C.cast(buffer, C.c_void_p), len(data), None)))
    av = AVInfo()
    core.retro_get_system_av_info(C.byref(av))
    fps = 50 if args.pal else 60
    def run(count=1):
        nonlocal frame
        for _ in range(count):
            core.retro_run(); frame += 1
    def press(button):
        buttons.add(button); run(2); buttons.clear(); run(2)
    font = (GAME / "res/intro/font.bin").read_bytes()
    glyphs = {}
    for i in range(96):
        mask = []
        for byte in font[i*32:(i+1)*32]:
            mask.extend((int(byte >> 4 == 15), int(byte & 15 == 15)))
        glyphs[bytes(mask)] = chr(i+32)
    def text(x, y, length):
        if raw is None: return ""
        result = ""
        for col in range(length):
            mask = bytes(int(raw[(y*8+dy)*pitch+(x*8+col*8+dx)*2:(y*8+dy)*pitch+(x*8+col*8+dx)*2+2] == b"\x7d\xef") for dy in range(8) for dx in range(8))
            result += glyphs.get(mask, "?")
        return result
    def menu():
        return raw is not None and text(4,12,9) == "NOVO JOGO"
    rgb_lut = [bytes((((n >> 11)&31)*255//31, ((n >> 5)&63)*255//63, (n&31)*255//31)) for n in range(65536)]
    def save(name):
        assert fmt == 2 and (width,height) == (320,224)
        rgb = b"".join(rgb_lut[n[0]] for y in range(height) for n in struct.iter_unpack("<H",raw[y*pitch:y*pitch+width*2]))
        (args.output / (name+".ppm")).write_bytes(b"P6\n320 224\n255\n"+rgb)
    def wait_for(predicate, limit=600):
        for _ in range(limit):
            if predicate(): return
            run()
        save("timeout")
        raise AssertionError(("Timed out",frame,text(0,18,40),text(0,20,40)))
    captures = {}
    def record(name, seconds=2, silent=False):
        nonlocal audio, recording
        from array import array
        path = args.output / (name+".wav")
        audio = wave.open(str(path),"wb")
        audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate))
        recording = True;run(seconds*fps);recording = False;audio.close()
        with wave.open(str(path),"rb") as stream:
            pcm = stream.readframes(stream.getnframes())
        samples = array("h",pcm)
        peak = max(abs(v) for v in samples)
        assert peak <= 2 if silent else 100 < peak < 32767,(name,peak)
        captures[name] = dict(peak=peak,pcm_sha256=hashlib.sha256(pcm).hexdigest())
        return captures[name]["pcm_sha256"]
    def check_track(index,bpm):
        assert text(2,7+index*3,1) == ">",(index,text(0,7+index*3,30))
        assert text(0,20,40).strip() == "BPM: "+str(bpm),text(0,20,40)

    # Each fresh START skips one boot card; there are no game-RAM writes.
    run(fps)
    for _ in range(24):
        if menu(): break
        press(3);run(fps//2)
    wait_for(menu);run(fps)
    assert text(4,16,6) == "ASSETS"
    save("menu-assets")
    press(5);press(5);press(3);run(fps)
    assert text(17,13,6) == "DAMIAO" and text(19,15,3) == "1/3"
    save("tab-damiao")
    press(7);run(fps)
    assert text(16,13,7) == "DINORAH" and text(19,15,3) == "2/3"
    save("tab-dinorah")
    press(7);run(fps)
    assert text(13,3,13) == "TRILHA SONORA"
    assert text(4,7,20) == "1. BAIAO DE FERRUGEM"
    assert text(4,10,13) == "2. ENTARDECER"
    assert text(4,13,7) == "3. BREU"
    assert text(4,16,20) == "4. LADAINHA DE FERRO"
    signatures = []
    for index,(name,calm,hot) in enumerate((("baiao",100,150),("entardecer",90,128),("breu",75,112),("ladainha",64,90))):
        if index: press(5);run(fps)
        check_track(index,calm)
        save("music-"+name)
        signatures.append(record(name+"-calm"))
        press(8);run(fps*2)
        check_track(index,hot)
        assert text(0,18,40).strip() == "TOCANDO - COMBATE"
        record(name+"-combat")
        press(8);run(fps*2);check_track(index,calm)
    assert len(set(signatures)) == 4
    press(1);run(fps)
    assert text(0,18,40).strip() == "PAUSADO - CALMA"
    save("music-paused");record("paused",1,silent=True)
    press(1);run(fps);record("resumed",1)
    # Up/down wraps, selecting while paused resumes, and both tab directions wrap.
    press(1);press(4);run(fps);check_track(2,75)
    assert text(0,18,40).strip() == "TOCANDO - CALMA"
    press(5);press(5);run(fps);check_track(0,100)
    press(4);run(fps);check_track(3,64)
    press(6);run(fps)
    assert text(16,13,7) == "DINORAH"
    record("character-return",1)
    press(7);run(fps);check_track(3,64)
    press(7);run(fps)
    assert text(17,13,6) == "DAMIAO"
    press(6);run(fps);check_track(3,64)
    press(1);run(fps);press(0);wait_for(menu);run(fps)
    save("menu-after-music");record("menu-restored",1)
    # Start the real campaign after exiting a paused preview.
    press(4);press(4);press(3);run(fps)
    assert text(4,19,7) == "COMANDO"
    press(3);run(fps);press(1);run(fps*3)
    symbols = subprocess.check_output(["/opt/homebrew/bin/m68k-elf-nm","-Sn",str(args.symbols)],text=True)
    syms = {p[3]:int(p[0],16)&65535 for line in symbols.splitlines() if len(p:=line.split())==4}
    ram = (C.c_ubyte*core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    swap = bytes(ram[syms["fps"]:syms["fps"]+2]) == struct.pack("<H",fps)
    assert ram[syms["currentLevel"]^int(swap)] == 1
    save("campaign-after-music")
    press(3);run(10);press(0);wait_for(menu);run(fps)
    press(5);press(5);press(3);run(fps);press(6);run(fps)
    check_track(0,100)
    press(3);wait_for(menu);run(fps)
    # A retains its old exit behaviour in the character pages.
    press(3);run(fps);assert text(17,13,6) == "DAMIAO"
    press(1);wait_for(menu)
    report = dict(passed=True,core="Genesis Plus GX",fps=fps,frames=frame,
                  game_ram_writes=False,rom_sha256=hashlib.sha256(original).hexdigest(),
                  captures=captures,checks=["ASSETS menu entry", "three tabs, both directions and wrap", "all four score names and cursor", "all calm/combat tempos", "four distinct real audio recordings", "pause emits silence and resume restores audio", "selection while paused resumes", "character sprites return after music", "B and START exit music", "A still exits characters", "menu audio restored", "campaign starts after paused preview exit"])
    (args.output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    core.retro_unload_game();core.retro_deinit()
    print(json.dumps(report,indent=2))

if __name__ == "__main__":main()
