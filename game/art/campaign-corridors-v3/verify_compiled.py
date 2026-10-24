"""Compare authored corridor banks with the bytes actually linked into the ROM.

This never builds or modifies production resources. It writes only its JSON
report, and returns nonzero for incomplete activation or any failed comparison.
An exact bank comparison is technical provenance, not visual approval.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
PHASES = ('3', '6A', '6B', '9', '12')
FOLDERS = {
    '3': 'streets/3', '6A': 'sewers/6A', '6B': 'sewers/6B',
    '9': 'streets/9', '12': 'syndicate/12',
}
activation_file=HERE/'active.json'
if activation_file.exists():FOLDERS.update(json.loads(activation_file.read_text()).get('scene_folders',{}))
SYMBOLS = {
    '3': ('street_tiles', 'street_map', 'street_palette'),
    '6A': tuple('campaign_route06a_' + k for k in ('tiles', 'map', 'palette')),
    '6B': tuple('campaign_route06b_' + k for k in ('tiles', 'map', 'palette')),
    '9': ('streetTiles', 'streetMap', 'streetPalette'),
    '12': tuple('campaign_route12_' + k for k in ('tiles', 'map', 'palette')),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(name):
    return name.split('.lto_priv.', 1)[0]


def parse_symbols(text):
    """Keep full ROM addresses; BIN resources can have a separate _size symbol."""
    symbols = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 4:
            address, size, kind, name = fields
        elif len(fields) == 3:
            address, kind, name = fields
            size = None
        else:
            continue
        try:
            entry = dict(name=name, address=int(address, 16),
                         size=int(size, 16) if size is not None else None,
                         kind=kind)
        except ValueError:
            continue
        symbols.setdefault(normalize(name), []).append(entry)
    return symbols


def resolve_symbol(symbols, name):
    candidates = [dict(s) for s in symbols.get(name, []) if s['kind'] not in 'AaUu']
    for candidate in candidates:
        if candidate['size'] is None:
            sizes = {s['address'] for s in symbols.get(name + '_size', [])
                     if s['kind'] in 'Aa'}
            if len(sizes) != 1:
                raise ValueError(f'{name}: no unique absolute _size symbol')
            candidate['size'] = sizes.pop()
            candidate['size_source'] = name + '_size'
        else:
            candidate['size_source'] = 'nm -S'
    unique = {(s['address'], s['size']) for s in candidates}
    if len(unique) != 1:
        raise ValueError(f'{name}: expected one linked array, found {len(unique)}')
    return sorted(candidates, key=lambda s: (s['name'] != name, s['name']))[0]


def compare_bank(rom, symbols, expected_path, symbol_name):
    record = dict(expected_path=str(expected_path.relative_to(HERE)),
                  symbol=symbol_name, passed=False)
    try:
        expected = expected_path.read_bytes()
        record.update(expected_bytes=len(expected), expected_sha256=digest(expected))
        linked = resolve_symbol(symbols, symbol_name)
        address, size = linked['address'], linked['size']
        record.update(linked_symbol=linked['name'], address=address,
                      address_hex=f'0x{address:08x}', linked_bytes=size,
                      size_source=linked['size_source'])
        if not expected:
            raise ValueError('empty expected bank')
        if size != len(expected):
            raise ValueError(f'linked size {size} differs from authored size {len(expected)}')
        if address < 0 or address + size > len(rom):
            raise ValueError('linked array is outside the raw ROM image')
        actual = rom[address:address + size]
        record['compiled_sha256'] = digest(actual)
        if actual != expected:
            offset = next(i for i, (a, b) in enumerate(zip(actual, expected)) if a != b)
            record['first_difference'] = dict(bank_offset=offset,
                                            rom_address_hex=f'0x{address + offset:08x}',
                                            expected=expected[offset], actual=actual[offset])
            raise ValueError('compiled bytes differ from authored bank')
        record['passed'] = True
    except (OSError, ValueError) as error:
        record['error'] = str(error)
    return record


def verify(build, nm):
    report = dict(purpose='Exact authored-to-linked-ROM provenance; not visual approval',
                  passed=False, status='incomplete', required_phases=list(PHASES),
                  phases={}, comparisons=[])
    activation = json.loads((HERE / 'active.json').read_text())
    active = set(activation['phases'])
    report['active_phases'] = [p for p in PHASES if p in active]
    report['inactive_phases'] = [p for p in PHASES if p not in active]
    report['activation_state'] = activation.get('state')
    rom_path, elf_path = build / 'rom.bin', build / 'rom.out'
    rom = rom_path.read_bytes()
    report.update(rom_sha256=digest(rom), rom_bytes=len(rom),
                  elf_sha256=digest(elf_path.read_bytes()),
                  build_directory=str(build))
    symbols_text = subprocess.check_output([nm, '-Sn', str(elf_path)], text=True)
    symbols = parse_symbols(symbols_text)
    report['symbol_table_sha256'] = digest(symbols_text.encode())
    for phase in PHASES:
        if phase not in active:
            report['phases'][phase] = dict(status='inactive', passed=False)
            continue
        rows = []
        variants = [('native', SYMBOLS[phase])]
        if phase == '3':
            # Both church states use the same linked palette. Comparing
            # it twice also proves the damaged bank respects that contract.
            variants.append(('damaged-native',
                             ('street_damaged_tiles', 'street_damaged_map', 'street_palette')))
        for variant, variant_names in variants:
            for kind, symbol in zip(('tiles', 'map', 'palette'), variant_names):
                path = HERE / FOLDERS[phase] / variant / (kind + '.bin')
                row = compare_bank(rom, symbols, path, symbol)
                row.update(phase=phase, state=variant, bank=kind)
                rows.append(row)
        report['comparisons'].extend(rows)
        passed = all(row['passed'] for row in rows)
        report['phases'][phase] = dict(passed=passed,
                                      status='passed' if passed else 'failed',
                                      comparisons=len(rows))
    report['total_comparisons'] = len(report['comparisons'])
    report['passed_comparisons'] = sum(row['passed'] for row in report['comparisons'])
    if not report['inactive_phases']:
        report['passed'] = (len(report['comparisons']) == 18
                            and all(row['passed'] for row in report['comparisons']))
        report['status'] = 'passed' if report['passed'] else 'failed'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=GAME / 'out/release')
    parser.add_argument('--output', type=Path, default=HERE / 'reviews/compiled-validation.json')
    parser.add_argument('--nm', default=shutil.which('m68k-elf-nm') or '/opt/homebrew/bin/m68k-elf-nm')
    args = parser.parse_args()
    try:
        report = verify(args.build_dir.resolve(), args.nm)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        report = dict(passed=False, status='failed', error=str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'passed', 'rom_sha256',
                                          'total_comparisons', 'passed_comparisons',
                                          'inactive_phases', 'error') if k in report}, indent=2))
    return 0 if report['passed'] else 2 if report['status'] == 'incomplete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
