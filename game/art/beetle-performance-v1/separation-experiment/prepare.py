"""Snapshot identical isolated builds, changing only the separation routine."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[2]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
    base=args.output.resolve();base.mkdir(parents=True,exist_ok=False)
    build=base/'baseline';build.mkdir()
    for name in ('src','res','tools'):shutil.copytree(GAME/name,build/name)
    sdk=GAME.parent/'SGDK'
    source=(GAME/'Makefile').read_text()
    (build/'Makefile').write_text(re.sub(r'^COMMON_GDK :=.*$','COMMON_GDK := '+str(sdk),source,flags=re.M))
    for resource in (GAME/'res').glob('*.res'):
        for relative in re.findall(r'"(\.\./[^\"]+)"',resource.read_text()):
            original=(resource.parent/relative).resolve();target=build/original.relative_to(GAME)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
    cover=Path('art/menu-logo-v1/menu-3x.png');(build/cover).parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(GAME/cover,build/cover)
    path=Path('src/enemies/enemies.c');original=(build/path).read_text()
    start=original.index('static void ENEMIES_separate(void)')
    end=original.index('// empurra o inimigo PARA LONGE',start)
    (base/'original-separate.inc').write_text(original[start:end])
    fragment=(ROOT/'separate.inc').read_text()
    for variant in ('compact','compass'):
        shutil.copytree(build,base/variant)
        replacement=('#define SEPARATION_COMPASS\n' if variant=='compass' else '')+fragment
        (base/variant/path).write_text(original[:start]+replacement+'\n\n'+original[end:])
    metadata={'root':str(base),'production_enemies_sha256':hashlib.sha256((GAME/path).read_bytes()).hexdigest(),
              'production_rom_sha256':hashlib.sha256((GAME/'out/release/rom.bin').read_bytes()).hexdigest(),
              'source_change':'Only the ENEMIES_separate function in src/enemies/enemies.c differs.',
              'variants':['baseline','compact','compass']}
    (base/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n');print(base)


if __name__=='__main__':main()
