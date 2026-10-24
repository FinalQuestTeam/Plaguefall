"""Publish a named, byte-identical ROM and existing artwork after SGDK padding.

Artwork is a companion file for emulator libraries, not embedded Genesis data.
This command never changes an emulator library or the compiled ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

GAME = Path(__file__).resolve().parents[1]
ARTWORK = GAME / 'art/menu-logo-v1/menu-3x.png'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=GAME / 'out/release')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    rom = output / 'rom.bin'
    data = rom.read_bytes()
    rom_start = int.from_bytes(data[0x1a0:0x1a4], 'big')
    rom_end = int.from_bytes(data[0x1a4:0x1a8], 'big')
    if rom_start != 0 or rom_end + 1 < len(data):
        raise SystemExit('ROM header range does not cover the complete binary; fix rom_header.c and rebuild.')
    for offset in (0x120, 0x150):
        if data[offset:offset + 48].decode('ascii').strip() != 'PLAGUEFALL':
            raise SystemExit('ROM header title must be PLAGUEFALL before packaging.')
    # sizebnd -checksum uses SGDK's whole-ROM XOR, including the header with
    # its checksum field cleared (not the original Sega additive checksum).
    checksum = 0
    for i in range(0, len(data), 2):
        if i != 0x18e:
            checksum ^= int.from_bytes(data[i:i + 2], 'big')
    if checksum != int.from_bytes(data[0x18e:0x190], 'big'):
        raise SystemExit('ROM checksum is invalid; run the SGDK padROM target first.')
    copies = {output / 'Plaguefall.bin': data,
              output / 'Plaguefall.png': ARTWORK.read_bytes()}
    metadata = {
        'title': 'Plaguefall', 'rom': 'Plaguefall.bin',
        'rom_sha256': hashlib.sha256(data).hexdigest(), 'rom_bytes': len(data),
        'artwork': 'Plaguefall.png',
        'artwork_source': str(ARTWORK.relative_to(GAME)),
        'artwork_sha256': hashlib.sha256(copies[output / 'Plaguefall.png']).hexdigest(),
        'artwork_embedded_in_rom': False,
        'openemu': 'Import Plaguefall.bin; right-click the game > Add Cover Art and select Plaguefall.png. Existing entries retain their library names and artwork.',
    }
    copies[output / 'Plaguefall.json'] = (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode()
    for path, content in copies.items():
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise SystemExit(f'Missing or stale package file: {path}')
        elif not path.exists() or path.read_bytes() != content:
            if path.suffix == '.bin':
                shutil.copyfile(rom, path)
            else:
                path.write_bytes(content)
    print(f'Plaguefall: {len(data)} bytes, named ROM + library artwork {"verified" if args.check else "ready"}.')


if __name__ == '__main__':
    main()
