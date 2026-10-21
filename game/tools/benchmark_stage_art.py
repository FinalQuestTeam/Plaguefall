"""Isolated renderer benchmark. Run with arch -x86_64 /usr/bin/python3.

Copies sources/resources into /private/tmp, substitutes stage exports there,
and benchmarks real Genesis Plus GX VBlanks. Production files are untouched.
Joypad enters the game; documented RAM setup maintains a repeatable load.
This measures renderer/camera/actors. --thermal also tests production lava damage
and a controller-driven dry route; new stage objectives are not simulated.
"""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import re
import shutil
import statistics
import struct
import subprocess
import tempfile
import zlib

GAME = Path(__file__).resolve().parents[1]
SDK = GAME.parent / 'SGDK'
CORE = Path.home() / 'Library/Application Support/RetroArch/cores/genesis_plus_gx_libretro.dylib'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(path):
    h = hashlib.sha256()
    for p in sorted(path.rglob('*')):
        if p.is_file():
            h.update(str(p.relative_to(path)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def png(path, width, height, rgb):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    rows = b''.join(b'\0' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def emulate(rom, symbols_path, stage, design, export, pal, thermal=False):
    fps = 50 if pal else 60
    original = rom.read_bytes()
    data = bytearray(original)
    if pal:
        data[0x1f0:0x200] = b'E               '
    core = C.CDLL(str(CORE))
    class Info(C.Structure):
        _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]
    class Geometry(C.Structure):
        _fields_ = [('base_width', C.c_uint), ('base_height', C.c_uint), ('max_width', C.c_uint), ('max_height', C.c_uint), ('aspect_ratio', C.c_float)]
    class Timing(C.Structure):
        _fields_ = [('fps', C.c_double), ('sample_rate', C.c_double)]
    class AVInfo(C.Structure):
        _fields_ = [('geometry', Geometry), ('timing', Timing)]
    class Variable(C.Structure):
        _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]
    ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
    VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    SAMPLE = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
    BATCH = C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
    POLL = C.CFUNCTYPE(None)
    INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
    fmt = 0
    raw = None
    width = height = pitch = 0
    buttons = set()
    @ENV
    def env(command, ptr):
        nonlocal fmt
        command &= 65535
        if command == 10:
            fmt = C.cast(ptr, C.POINTER(C.c_int))[0]
            return fmt in (0, 1, 2)
        if command == 15:
            v = C.cast(ptr, C.POINTER(Variable))
            v[0].value = None
            if v[0].key == b'genesis_plus_gx_region_detect':
                v[0].value = b'pal' if pal else b'ntsc-u'
                return True
            return False
        if command in (9, 31):
            C.cast(ptr, C.POINTER(C.c_char_p))[0] = b'/private/tmp'
            return True
        if command == 3:
            C.cast(ptr, C.POINTER(C.c_bool))[0] = True
            return True
        if command == 39:
            C.cast(ptr, C.POINTER(C.c_uint))[0] = 0
            return True
        if command == 47:
            C.cast(ptr, C.POINTER(C.c_int))[0] = 3
            return True
        return command in (8, 11, 16, 18, 35, 37)
    @VIDEO
    def video(ptr, w, h, stride):
        nonlocal raw, width, height, pitch
        if ptr and ptr != C.c_void_p(-1).value:
            width, height, pitch = w, h, stride
            raw = C.string_at(ptr, stride * h)
    @SAMPLE
    def sample(left, right):
        pass
    @BATCH
    def batch(ptr, n):
        return n
    @POLL
    def poll():
        pass
    @INPUT
    def input_state(port, device, index, button):
        return int(port == 0 and button in buttons)
    for name, callback in [('environment', env), ('video_refresh', video), ('audio_sample', sample), ('audio_sample_batch', batch), ('input_poll', poll), ('input_state', input_state)]:
        getattr(core, 'retro_set_' + name)(callback)
    core.retro_load_game.argtypes = [C.POINTER(Info)]
    core.retro_load_game.restype = C.c_bool
    core.retro_get_memory_data.argtypes = [C.c_uint]
    core.retro_get_memory_data.restype = C.c_void_p
    core.retro_get_memory_size.argtypes = [C.c_uint]
    core.retro_get_memory_size.restype = C.c_size_t
    core.retro_init()
    buffer = C.create_string_buffer(bytes(data))
    assert core.retro_load_game(C.byref(Info(str(rom).encode(), C.cast(buffer, C.c_void_p), len(data), None)))
    av = AVInfo()
    core.retro_get_system_av_info.argtypes = [C.POINTER(AVInfo)]
    core.retro_get_system_av_info(C.byref(av))
    syms = {}
    for line in subprocess.check_output(['/opt/homebrew/bin/m68k-elf-nm', '-Sn', str(symbols_path)], text=True).splitlines():
        parts = line.split()
        if len(parts) == 4:
            addr, size, kind, name = parts
            syms[name.split('.lto_priv.')[0]] = (int(addr, 16) & 65535, int(size, 16))
    ram = (C.c_ubyte * core.retro_get_memory_size(2)).from_address(core.retro_get_memory_data(2))
    def run(n=1):
        for _ in range(n):
            core.retro_run()
    for _ in range(8 * fps):
        if bytes(ram[syms['fps'][0]:syms['fps'][0] + 2]) in (struct.pack('<H', fps), struct.pack('>H', fps)):
            break
        run()
    swapped = bytes(ram[syms['fps'][0]:syms['fps'][0] + 2]) == struct.pack('<H', fps)
    def read(address, n):
        return bytes(ram[((address + i) & 65535) ^ int(swapped)] for i in range(n))
    def write(address, value):
        for i, v in enumerate(value):
            ram[((address + i) & 65535) ^ int(swapped)] = v
    def u8(name):
        return read(syms[name][0], 1)[0]
    def u16(name):
        return int.from_bytes(read(syms[name][0], 2), 'big')
    def u32(name):
        return int.from_bytes(read(syms[name][0], 4), 'big')
    def w16(name, value):
        write(syms[name][0], struct.pack('>H', value & 65535))
    def pos(x, y):
        w16('px', x)
        w16('py', y)
        write(syms['pfx'][0], struct.pack('>i', x << 6))
        write(syms['pfy'][0], struct.pack('>i', y << 6))
    def press(key):
        buttons.add(key)
        run(2)
        buttons.clear()
        run(2)
    run(120)
    press(3)
    run(fps * 4)
    for _ in range(6):
        if u8('arenaActive'):
            break
        press(3)
        run(fps)
        if u8('arenaActive'):
            break
        press(1)
        run(fps * 4)
    assert u8('arenaActive') and u8('currentLevel') == 1, 'controller entry failed'
    assert u16('fps') == fps, ('wrong emulator region', u16('fps'), fps)
    # Compare the actual hardware tile upload, not just a resource filename.
    vram = (C.c_ubyte * 65536).in_dll(core, 'vram')
    atlas = (stage / 'hardware/tiles.bin').read_bytes()
    uploaded = bytes(vram[(781 * 32 + i) ^ 1] for i in range(len(atlas)))
    assert uploaded == atlas, 'stage atlas differs from real VDP VRAM'
    left, top, floor_w, floor_h = design['walkable']
    right, bottom = left + floor_w - 16, top + floor_h - 16
    assert u16('arenaMaxX') == left + floor_w - 1
    enemy_addr, enemy_bytes = syms['enemies']
    stride = enemy_bytes // 16
    assert stride == 46
    def triangle(tick, low, high):
        span = high - low
        t = (tick * 3) % (span * 2)
        return low + (t if t <= span else 2 * span - t)
    def load(case, tick, enemies, shots):
        w16('hp', 100)
        w16('kills', 0)
        w16('spawnTimer', 60000)
        w16('freezeTimer', 0)
        x = triangle(tick, left, right) if case == 'horizontal' else (left + right) // 2
        y = triangle(tick, top, bottom) if case == 'vertical' else (top + bottom) // 2
        pos(x, y)
        for i in range(16):
            buf = bytearray(stride)
            if i < enemies:
                ex = left + 32 + (i % 2) * max(48, floor_w - 96)
                ey = top + 24 + (i // 2) * max(32, floor_h - 80)
                struct.pack_into('>hhii', buf, 0, ex, ey, ex << 6, ey << 6)
                struct.pack_into('>hhHH', buf, 12, 32, 0, 600, 600)
                buf[30], buf[31], buf[43], buf[44] = i % 2, 20, 1, 1
            write(enemy_addr + i * stride, buf)
        for name in ('pshots', 'eshots'):
            address, size = syms[name]
            assert size == 320
            for i in range(16):
                buf = bytearray(20)
                if i < shots:
                    sx = left + 24 + (i % 3) * 48
                    sy = top + 24 + (i // 3) * 40
                    struct.pack_into('>iiii', buf, 0, sx << 6, sy << 6, 32, 0)
                    buf[17], buf[18] = 1, 1
                write(address + i * 20, buf)
    results = []
    buttons.add(1)
    for case, enemies, shots in [('idle', 0, 0), ('horizontal', 4, 6), ('vertical', 4, 6)]:
        for tick in range(90):
            load(case, tick, enemies, shots)
            run()
        begin = int.from_bytes(read(syms['phaseStats'][0] + 4, 4), 'big')
        vbegin = u32('vtimer')
        loads, camera_x, camera_y = [], [], []
        for tick in range(90, 390):
            load(case, tick, enemies, shots)
            run()
            loads.append(u16('cpuFrameLoad') * 100 / 2048)
            camera_x.append(u16('cameraX'))
            camera_y.append(u16('cameraY'))
        drawn = (int.from_bytes(read(syms['phaseStats'][0] + 4, 4), 'big') - begin) & 0xffffffff
        elapsed = (u32('vtimer') - vbegin) & 0xffffffff
        result = {'case': case, 'enemies': enemies, 'shots_per_pool': shots, 'physical_frames': elapsed, 'game_frames': drawn, 'fps': round(fps * drawn / elapsed, 2), 'cpu_mean_pct': round(statistics.mean(loads), 2), 'cpu_p95_pct': round(sorted(loads)[285], 2), 'camera_x_range': [min(camera_x), max(camera_x)], 'camera_y_range': [min(camera_y), max(camera_y)]}
        results.append(result)
        assert result['fps'] >= fps * .99, result
        if case == 'horizontal':
            assert result['camera_x_range'] == [0, max(0, design['width'] - 320)], result
        if case == 'vertical':
            assert result['camera_y_range'] == [0, max(0, design['height'] - 224)], result
    buttons.clear()
    terrain_checks=None
    if thermal:
        # Production LAVA_update, proposed rectangles. RAM prepares only the
        # initial state; the dry crossing below uses the controller alone.
        w16('spawnTimer',60000);w16('kills',0)
        for i in range(16):write(enemy_addr+i*stride+44,b'\0')
        for name in ('pshots','eshots'):write(syms[name][0],bytes(syms[name][1]))
        start=tuple(design['start']);pos(*start);w16('hp',100);run(fps)
        assert u16('hp')==100,'dry entry causes terrain damage'
        pool=next(h['rect'] for h in design['hazards'] if h['kind']=='thermal')
        pos(pool[0]+24,pool[1]+24);w16('hp',100);run(fps)
        hot_hp=u16('hp');assert 0<hot_hp<100,('lava failed to damage',hot_hp)
        pos(*start);w16('hp',100);run(fps)
        assert u16('hp')==100,'lava continues damaging after leaving'
        rects=[h['rect'] for h in design['hazards'] if h['kind']=='thermal']
        middle=((rects[0][0]+rects[0][2]+rects[1][0]-16)//16)*8
        goal=tuple(design['exit']);waypoints=[(middle,start[1]),(middle,goal[1]),goal]
        path_frames=0
        for gx,gy in waypoints:
            for _ in range(1000):
                ax,ay=u16('px'),u16('py')
                if (ax,ay)==(gx,gy):break
                buttons.clear();buttons.add((7 if ax<gx else 6) if ax!=gx else (5 if ay<gy else 4))
                run();path_frames+=1
                assert u16('hp')==100,('dry route intersects lava',ax,ay,gx,gy)
            else:raise AssertionError(('dry route stalled',gx,gy,u16('px'),u16('py')))
        buttons.clear()
        terrain_checks={'production_lava_update':True,'lava_hp_after_one_second':hot_hp,'dry_entry_hp':100,
                        'damage_stops_on_exit':True,'controller_dry_route':True,'route_frames':path_frames,
                        'waypoints':[list(start)]+[list(p) for p in waypoints],
                        'ram_writes_during_controller_route':False}
    # Capture the real hardware frame near the top, showing architecture and HUD.
    for tick in range(30):
        load('vertical', 0, 4, 6)
        pos(min(right, left + 160), top)
        run()
    rgb = bytearray(width * height * 3)
    assert raw
    for y in range(height):
        for x in range(width):
            if fmt == 1:
                b, g, r, _ = raw[y * pitch + x * 4:y * pitch + x * 4 + 4]
            else:
                value = struct.unpack_from('<H', raw, y * pitch + x * 2)[0]
                if fmt == 2:
                    r, g, b = (value >> 11 & 31) * 255 // 31, (value >> 5 & 63) * 255 // 63, (value & 31) * 255 // 31
                else:
                    r, g, b = (value >> 10 & 31) * 255 // 31, (value >> 5 & 31) * 255 // 31, (value & 31) * 255 // 31
            rgb[(y * width + x) * 3:(y * width + x + 1) * 3] = bytes((r, g, b))
    out = stage / 'validation'
    out.mkdir(exist_ok=True)
    region_name = 'pal' if pal else 'ntsc'
    screenshot = 'emulator-' + region_name + '.png'
    png(out / screenshot, width, height, bytes(rgb))
    core.retro_unload_game()
    core.retro_deinit()
    return {'passed': True, 'region': 'PAL' if pal else 'NTSC', 'isolated_preview_build': True, 'renderer_camera_actors_only': not thermal, 'hazards_and_objectives_simulated': False, 'terrain_damage_enabled':thermal, 'terrain_checks':terrain_checks, 'world': [design['width'], design['height']], 'scene_tiles': export['tiles'], 'scene_tile_bytes': export['tile_bytes'], 'atlas_hardware_upload_matches': True, 'benchmark': results, 'screenshot': screenshot, 'screenshot_dimensions': [width, height], 'core': str(CORE), 'core_fps': av.timing.fps, 'rom_sha256': hashlib.sha256(original).hexdigest(), 'emulated_rom_sha256': hashlib.sha256(data).hexdigest(), 'ram_setup': 'Per frame: HP, kills=0, spawn cooldown, enemy/projectile formations, gradual actor coordinates (3 px/frame); joypad entry and A held. No production ROM patches.', 'method': 'Game phaseStats.frames versus vtimer physical VBlanks; cpuFrameLoad is SGDK eight-frame sum / 2048. 90 warm-up plus 300 measured frames per case. Host execution speed is not used.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, action='append')
    parser.add_argument('--thermal',action='store_true',help='Enable actual lava damage and a controller-driven dry route in the isolated build')
    args = parser.parse_args()
    assert (SDK / 'makefile.gen').exists(), SDK
    assert CORE.exists(), CORE
    stages = args.stage or sorted((GAME / 'art').glob('phase*/design.json'))
    stages = [p.parent if p.name == 'design.json' else p.resolve() for p in stages]
    canonical = GAME / 'out/release/rom.bin'
    production_hash = digest(canonical)
    source_hashes = {name: tree_digest(GAME / name) for name in ('src', 'res')}
    build = Path(tempfile.mkdtemp(prefix='plaguefall-stage-preview-', dir='/private/tmp'))
    for name in ('src', 'res'):
        shutil.copytree(GAME / name, build / name)
    shutil.copy2(GAME / 'Makefile', build / 'Makefile')
    # One actor resource lives in art rather than res. Copy only referenced
    # files, preserving relative paths, rather than linking production assets.
    for resource in (GAME / 'res').glob('*.res'):
        for relative in re.findall(r'"(\.\./[^\"]+)"', resource.read_text()):
            source = (resource.parent / relative).resolve()
            target = build / source.relative_to(GAME)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    # The temporary directory is intentionally not a Git checkout. GDK is
    # supplied explicitly, so remove the unused Git fallback in this copy.
    makefile = build / 'Makefile'
    makefile.write_text(re.sub(r'^COMMON_GDK :=.*$', 'COMMON_GDK := ' + str(SDK), makefile.read_text(), flags=re.M))
    arena_source = (build / 'src/levels/arena.c').read_text()
    header_source = (build / 'src/levels/courtyard_data.h').read_text()
    level_source=(build/'src/levels/defs/level01.c').read_text()
    for stage in stages:
        design = json.loads((stage / 'design.json').read_text())
        export = json.loads((stage / 'export.json').read_text())
        assert export['within_vram_budget']
        for source, target in [('tiles.bin', 'tiles.bin'), ('palette.bin', 'palette.bin'), ('map-vdp.bin', 'map.bin'), ('map-vdp.bin', 'damaged.bin')]:
            shutil.copyfile(stage / 'hardware' / source, build / 'res/courtyard' / target)
        header = re.sub(r'#define COURTYARD_TILE_COUNT \d+', '#define COURTYARD_TILE_COUNT ' + str(export['tiles']), header_source)
        (build / 'src/levels/courtyard_data.h').write_text(header)
        x, y, width, height = design['walkable']
        sx, sy = design['start']
        declaration = 'const ArenaDef COURTYARD_arena = {\n    %d, %d, %d, %d, %d, %d, %d, %d, NULL, 0\n};' % (design['width'], design['height'], x, y, x + width - 1, y + height - 1, sx, sy)
        arena = re.sub(r'const ArenaDef COURTYARD_arena = \{.*?\n\};', declaration, arena_source, flags=re.S)
        (build / 'src/levels/arena.c').write_text(arena)
        level=level_source
        if args.thermal:
            rects=[h['rect'] for h in design.get('hazards',[]) if h['kind']=='thermal']
            assert rects,'--thermal requires thermal hazard rectangles'
            declaration='static const TileRect preview_lava[] = {'+','.join('{%d,%d,%d,%d}'%tuple(v//8 for v in r) for r in rects)+'};\n'
            level=level.replace('const LevelDef LEVEL01_def',declaration+'const LevelDef LEVEL01_def')
            level=level.replace('    .killTarget','    .lava = preview_lava,\n    .lavaCount = '+str(len(rects))+',\n    .killTarget')
        (build/'src/levels/defs/level01.c').write_text(level)
        log = build / ('build-' + design['id'] + '.log')
        with log.open('w') as output:
            subprocess.run(['make', '-s', '-C', str(build), 'GDK=' + str(SDK), '-j4'], stdout=output, stderr=subprocess.STDOUT, check=True)
        for pal in (False, True):
            report = emulate(build / 'out/release/rom.bin', build / 'out/release/rom.out', stage, design, export, pal,args.thermal)
            unchanged = digest(canonical) == production_hash
            assert unchanged
            assert all(tree_digest(GAME / name) == value for name, value in source_hashes.items())
            report.update(production_rom_unchanged=unchanged, production_sources_unchanged=True, production_rom_sha256=production_hash, source_export_sha256={p.name: digest(p) for p in (stage / 'hardware').glob('*.bin')}, design_sha256=digest(stage / 'design.json'), benchmark_source_sha256=digest(Path(__file__)), isolated_build_directory=str(build))
            destination = stage / 'validation' / ('emulator-pal.json' if pal else 'emulator-ntsc.json')
            destination.write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({'stage': design['id'], 'region': report['region'], 'benchmark': report['benchmark'], 'output': str(destination)}), flush=True)
    print(json.dumps({'production_rom_unchanged': digest(canonical) == production_hash, 'isolated_build_directory': str(build)}), flush=True)


if __name__ == '__main__':
    main()
