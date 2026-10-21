"""Capture the real listening-bench ROM through Genesis Plus GX.

Run with a Python matching the installed libretro core architecture:
  arch -x86_64 /usr/bin/python3 game/tools/music-bench/render_audio.py --output /private/tmp/cue.wav
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
CORE = Path.home() / "Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=ROOT / "out/release/rom.bin")
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--pal", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--enemies", type=int, default=0)
    parser.add_argument("--track", type=int, choices=range(4), help="Select a runtime track (0..3), independent of ROM default")
    args = parser.parse_args()
    assert args.seconds > 0 and 0 <= args.enemies <= 15
    args.output.parent.mkdir(parents=True, exist_ok=True)
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
        pass
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
    def run(count):
        nonlocal frame
        for _ in range(count):
            core.retro_run(); frame += 1
    def press(button):
        buttons.add(button);run(2);buttons.clear();run(2)
    if args.track is not None:
        run(120);press(0) # bench B selects the first track
        for _ in range(args.track):press(7)
        press(3) # restart the selected score for a complete loop capture
    if args.enemies:
        run(120)
        for _ in range(args.enemies):press(4)
        run(120)
    audio = wave.open(str(args.output), "wb")
    audio.setnchannels(2);audio.setsampwidth(2)
    audio.setframerate(round(av.timing.sample_rate))
    recording = True
    run(round(args.seconds * (50 if args.pal else 60)))
    recording = False
    audio.close()
    # Fail loudly when frontend options accidentally mute the recording.
    from array import array
    with wave.open(str(args.output), "rb") as captured:
        samples = array("h", captured.readframes(captured.getnframes()))
    assert any(samples), "Silent capture: check the core/frontend audio options"
    core.retro_unload_game();core.retro_deinit()
    print(json.dumps({"output":str(args.output),"seconds":args.seconds,"sample_rate":av.timing.sample_rate,"enemies":args.enemies,"track":args.track,"rom_sha256":hashlib.sha256(original).hexdigest()}))

if __name__ == "__main__":main()
