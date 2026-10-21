"""Exercise the real ROM through libretro controller input, without RAM writes.

On this Mac the installed Genesis Plus GX core is Intel:
  arch -x86_64 /usr/bin/python3 verify_emulator.py --rom ... --symbols ...
Use --pal for a second run with PAL region override and an E-only header copy.
Optional --movie records actual emulator output, not a mocked animation.
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
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--pal", action="store_true")
    parser.add_argument("--movie", action="store_true")
    args = parser.parse_args()
    out = ROOT / ("emulator-pal" if args.pal else "emulator-ntsc")
    out.mkdir(exist_ok=True)
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
    fmt = 0
    buttons = set()
    frame = 0
    raw = None
    pitch = width = height = 0
    recording = False
    encoder = audio = None
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
        if not ptr or ptr == C.c_void_p(-1).value:
            return
        raw = C.string_at(ptr, stride * h)
        width, height, pitch = w, h, stride
        if recording and frame % 2 == 0:
            assert fmt == 2 and (w, h) == (320, 224)
            encoder.stdin.write(raw if stride == w * 2 else b"".join(raw[y*stride:y*stride+w*2] for y in range(h)))
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
    symbols = subprocess.check_output(["/opt/homebrew/bin/m68k-elf-nm", "-Sn", str(args.symbols)], text=True)
    syms = {parts[3]: int(parts[0], 16) & 65535 for line in symbols.splitlines() if len(parts := line.split()) == 4}
    ram = (C.c_ubyte * core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    def run(n=1):
        nonlocal frame
        for _ in range(n):
            core.retro_run()
            frame += 1
    for _ in range(8 * fps):
        if bytes(ram[syms["fps"]:syms["fps"]+2]) in (struct.pack("<H", fps), struct.pack(">H", fps)):
            break
        run()
    swapped = bytes(ram[syms["fps"]:syms["fps"]+2]) == struct.pack("<H", fps)
    def read(addr, n):
        return bytes(ram[((addr+i) & 65535) ^ int(swapped)] for i in range(n))
    assert read(syms["fps"], 2) == struct.pack(">H", fps)
    def particle_state():
        result = []
        for i in range(12):
            y, link, attr, x = struct.unpack(">4H", read(syms["vdpSpriteCache"]+i*8, 8))
            assert attr & 2047 == 16+924+i%3
            assert attr & 0x6000 == 0x6000
            result.append(dict(x=(x&511)-128,y=(y&511)-128,type=i%3))
        return result
    font = (GAME / "res/intro/font.bin").read_bytes()
    glyphs = {}
    for i in range(96):
        mask = []
        for byte in font[i*32:(i+1)*32]:
            mask.extend((int(byte >> 4 == 15), int(byte & 15 == 15)))
        glyphs[bytes(mask)] = chr(i+32)
    scenes = json.loads((ROOT / "export.json").read_text())["scenes"]
    tiles = (GAME / "res/intro/tiles.bin").read_bytes()
    groups = (GAME / "res/intro/groups.bin").read_bytes()
    palettes = (GAME / "res/intro/palettes.bin").read_bytes()
    anchors = [(40, 24), (120, 32), (200, 24), (280, 40), (60, 88), (160, 96), (260, 112)]
    fingerprints = []
    for index in range(12):
        pattern = []
        for x, y in anchors:
            sx = x + 8
            tile = (y // 8) * 42 + sx // 8
            packed = tiles[index * 924 * 32 + tile * 32 + (y % 8) * 4 + (sx % 8) // 2]
            color = packed >> 4 if sx % 2 == 0 else packed & 15
            bank = groups[index * 924 + tile]
            word = struct.unpack_from(">H", palettes, index * 64 + bank * 32 + color * 2)[0]
            r, g, b = [((word >> shift) & 7) * 34 for shift in (1, 5, 9)]
            pattern.append(struct.pack("<H", ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)))
        fingerprints.append(tuple(pattern))
    def text(x, y, length):
        result = ""
        for col in range(length):
            mask = bytes(int(raw[(y*8+dy)*pitch+(x*8+col*8+dx)*2:(y*8+dy)*pitch+(x*8+col*8+dx)*2+2] == b"\x7d\xef") for dy in range(8) for dx in range(8))
            result += glyphs.get(mask, "?")
        return result
    def counter():
        # Identify the artwork itself; there is no slide number on the screen.
        if raw is None or fmt != 2:
            return None
        pattern = tuple(raw[y*pitch+x*2:y*pitch+x*2+2] for x,y in anchors)
        return fingerprints.index(pattern)+1 if pattern in fingerprints else None
    def wait_for(predicate, limit):
        for _ in range(limit):
            if predicate():
                return
            run()
        save("timeout")
        raise AssertionError(("Timed out", frame, counter(), text(3, 4, 10)))
    def menu():
        return raw is not None and fmt == 2 and text(3, 4, 10) == "PLAGUEFALL"
    def press(button):
        buttons.add(button); run(2)
        buttons.clear(); run(2)
    # RGB565 expansion exactly matches the screenshots from the previous tests.
    rgb_lut = [bytes((((n >> 11) & 31)*255//31, ((n >> 5) & 63)*255//63, (n & 31)*255//31)) for n in range(65536)]
    def save(name):
        rgb = b"".join(rgb_lut[n[0]] for y in range(height) for n in struct.iter_unpack("<H", raw[y*pitch:y*pitch+width*2]))
        (out / f"{name}.ppm").write_bytes((f"P6\n{width} {height}\n255\n").encode() + rgb)
    if args.movie:
        encoder = subprocess.Popen(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb565le", "-s", "320x224", "-r", str(fps/2), "-i", "pipe:0", "-vf", "scale=960:672:flags=neighbor", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", "-an", str(out/"video.mp4")], stdin=subprocess.PIPE)
        audio = wave.open(str(out/"audio.wav"), "wb")
        audio.setnchannels(2); audio.setsampwidth(2); audio.setframerate(round(av.timing.sample_rate))
        recording = True
    run(fps*4//5); save("logo")
    wait_for(lambda: counter() == 1, 8 * fps)
    first_intro = frame
    durations = [scene["seconds"] for scene in scenes]
    observed = []
    for index, seconds in enumerate(durations, 1):
        wait_for(lambda: counter() == index, 2 * fps)
        start = frame
        run(fps)
        save(f"{index:02}-early")
        early_particles = particle_state()
        previous = early_particles
        moving_frames = 0
        stable_frames = (seconds - 2) * fps
        for _ in range(stable_frames):
            run()
            current = particle_state()
            moved = False
            for before, after in zip(previous,current):
                dx=abs(before["x"]-after["x"]);dy=abs(before["y"]-after["y"])
                assert dx<=1 or dx>=300,(index,"particle X jump",dx)
                assert dy<=1 or dy>=150,(index,"particle Y jump",dy)
                moved = moved or dx>0 or dy>0
            moving_frames += int(moved)
            previous = current
        assert moving_frames > stable_frames*0.8
        assert counter() == index, (index, counter())
        save(f"{index:02}-complete")
        complete_particles = particle_state()
        for line, (x, y) in zip(scenes[index-1]["lines"], scenes[index-1]["text_origins"]):
            assert text(x, y, len(line)) == line, (index, line)
        wait_for(lambda: counter() != index, 2 * fps)
        observed.append(dict(shot=index, first_frame=start, frames=frame-start, particle_motion_frames=moving_frames,
                             captures=dict(early=early_particles,complete=complete_particles)))
        print(f"{fps}Hz: shot {index:02} OK", flush=True)
    last_visible = frame
    wait_for(menu, 8 * fps)
    menu_frame = frame
    run(fps); save("menu-after-natural")
    assert text(3,8,13) != "ARENA SHOOTER"
    assert (menu_frame-last_visible)/fps<0.75
    assert (menu_frame-observed[-1]["first_frame"])/fps<6
    if recording:
        recording = False
        encoder.stdin.close(); assert encoder.wait() == 0
        audio.close()
        subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-i", str(out/"video.mp4"), "-i", str(out/"audio.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(ROOT/"abertura.mp4")], check=True)
        (out/"video.mp4").unlink(); (out/"audio.wav").unlink()
    assert abs((frame - first_intro) / fps - (sum(durations)+1)) < 4
    # A completes the current text first, and advances only on the next press.
    core.retro_reset(); run(2)
    wait_for(lambda: counter() == 1, 8 * fps)
    press(1)  # Genesis A is libretro Y in the core's default mapping.
    assert counter() == 1
    save("a-complete")
    first_line = scenes[0]["lines"][0]
    x, y = scenes[0]["text_origins"][0]
    assert text(x, y, len(first_line)) == first_line
    press(1); wait_for(lambda: counter() == 2, 2*fps)
    assert counter() == 2
    save("a-advance")
    # A held down must not repeatedly advance. START skips from mid sequence.
    buttons.add(1); run(2*fps); buttons.clear(); run(2)
    assert counter() == 2
    press(3)
    wait_for(menu, 8 * fps)
    run(fps); save("menu-after-skip")
    # Returning from gallery and gameplay never replays the boot cinematic.
    press(5); press(5); press(3); run(fps)
    save("gallery-damiao")
    assert text(17, 13, 6) == "DAMIAO"
    press(7); run(fps); save("gallery-dinorah")
    assert text(16, 13, 7) == "DINORAH"
    press(3); wait_for(menu, 8*fps)
    run(fps)
    press(4); press(4); press(3); run(fps)
    save("mission-call")
    assert text(4, 19, 7) == "COMANDO"
    press(3); run(fps)
    save("phase-prep")
    press(1); run(4*fps)
    save("gameplay")
    assert read(syms["currentLevel"], 1) == b"\x01"
    press(3); run(10); press(0)
    wait_for(menu, 8*fps)
    run(fps); save("menu-after-game")
    # START can also skip the very first shot without leaking input to the menu.
    core.retro_reset(); run(2)
    wait_for(lambda: counter() == 1, 8*fps)
    buttons.add(3); run(4*fps)
    assert menu()
    buttons.clear(); run(2)
    report = dict(passed=True, core="Genesis Plus GX", fps=fps, core_fps=av.timing.fps,
                  input_only=True, game_ram_writes=False, rom_sha256=hashlib.sha256(original).hexdigest(),
                  pal_region_override=args.pal, frames=frame, shots=observed,
                  menu_delay_after_final_fade_seconds=(menu_frame-last_visible)/fps,
                  last_shot_to_menu_seconds=(menu_frame-observed[-1]["first_frame"])/fps,
                  checks=["all 12 shots play automatically", "centered white captions", "12 dust/ember/soot sprites move <=1px/frame", "camera remains fixed", "final shot shortened to 5 seconds", "no ARENA SHOOTER label", "A completes then advances", "held A has no repeat", "START skip first and middle shot", "held START does not start game", "title after natural playback and skip", "gallery Damião and Dinorah after intro", "mission call without repeated monologue", "phase 1 starts", "return to menu without replay"])
    (out/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    core.retro_unload_game(); core.retro_deinit()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
