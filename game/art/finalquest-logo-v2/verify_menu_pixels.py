"""Compare the developer credit and transparent backdrop in real menu captures."""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ART = ROOT.parent


def hardware(image):
    colors = np.rint(np.asarray(image.convert('RGB')).astype(np.int32)*7/255).astype(np.int32)*34
    result = np.empty_like(colors)
    for channel, bits in enumerate((31,63,31)):
        result[:,:,channel] = (colors[:,:,channel] >> (2 if channel == 1 else 3))*255//bits
    return result


def main():
    rom = (ART.parents[0]/'out/release/rom.bin').read_bytes()
    rom_hash = hashlib.sha256(rom).hexdigest()
    logo = Image.open(ROOT/'menu-credit-native.png')
    exported = json.loads((ROOT/'menu-credit-export.json').read_text())
    x,y = exported['position']
    w,h = exported['canvas']
    inks = np.asarray(logo)
    expected = hardware(Image.open(ART/'title-caatinga-v1/title-native.png'))[y:y+h,x:x+w].copy()
    expected[inks != 0] = hardware(logo)[inks != 0]
    checks = []
    for region in ('ntsc','pal'):
        captures = ART/f'intro-monologo-v1/emulator-{region}'
        report = json.loads((captures/'report.json').read_text())
        assert report['passed'] and report['rom_sha256'] == rom_hash
        for suffix in ('natural','skip','game','gallery','help'):
            path = captures/f'menu-after-{suffix}.png'
            actual = np.asarray(Image.open(path))
            assert np.array_equal(actual[y:y+h,x:x+w],expected), (region,suffix)
            checks.append(dict(region=region,returned_from=suffix,pixel_mismatches=0,
                               rom_sha256=report['rom_sha256']))
    result = dict(passed=True,rom_sha256=rom_hash,rom_bytes=len(rom),
                  position=[x,y],size=[w,h],transparent_index=0,checks=checks)
    (ROOT/'menu-credit-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    source = ART/'intro-monologo-v1/emulator-ntsc/menu-after-natural.png'
    with Image.open(source) as image:
        image.save(ROOT/'menu-credit-screen.png')
        image.resize((960,672),Image.Resampling.NEAREST).save(ROOT/'menu-credit-screen-3x.png')
    print('PASS: FinalQuest and transparent backdrop match exactly in 10 PAL/NTSC menu captures.')


if __name__ == '__main__':
    main()
