"""Check native art, centered captions and absence of UI labels in real captures."""
from pathlib import Path
import json
import argparse
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
sys.path.insert(0,str(GAME/'tools'))
from text_codec import encode


def particle_mask(particles):
    """The cached SAT can be one frame ahead of the rendered sprite.

    Include its prior position at the 320px/156px wrap boundary as well as
    the normal one-pixel motion, rather than allowing unrelated art changes.
    """
    mask = np.ones((176,320), dtype=bool)
    for particle in particles:
        x,y = particle['x'],particle['y']
        xs = [x] + ([x+320] if x <= 1 else [])
        ys = [y] + ([y-156] if y >= 154 else [])
        for xx in xs:
            for yy in ys:
                left,right = max(0,xx-1),min(320,xx+9)
                top,bottom = max(0,yy-1),min(176,yy+9)
                if left < right and top < bottom:
                    mask[top:bottom,left:right] = False
    return mask


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture-root',type=Path,help='Directory with intro-ntsc and intro-pal captures')
    args=parser.parse_args()
    scenes = json.loads((ROOT / "export.json").read_text())["scenes"]
    packed=np.frombuffer((GAME/'res/intro/font.bin').read_bytes(),dtype=np.uint8)
    font=np.stack((packed>>4,packed&15),axis=1).reshape(96,8,8)
    logo = np.asarray(Image.open(GAME/"art/finalquest-logo-v2/logo-native.png").convert("RGB")).astype(np.int32)
    logo_hw=np.rint(logo*7/255).astype(np.int32)*34
    logo_rgb=np.empty_like(logo_hw)
    for channel,bits in enumerate((31,63,31)):
        logo_rgb[:,:,channel]=(logo_hw[:,:,channel]>>(2 if channel==1 else 3))*255//bits
    checks = []
    for region in ("ntsc", "pal"):
        captures=args.capture_root/f'intro-{region}' if args.capture_root else ROOT/f'emulator-{region}'
        runtime = json.loads((captures/'report.json').read_text())
        expected_logo=np.zeros((224,320,3),dtype=np.uint8)
        expected_logo[48:176,64:256]=logo_rgb
        assert np.array_equal(np.asarray(Image.open(captures/'logo.png')),expected_logo),(region,"logo mismatch")
        for shot in scenes:
            index = shot["shot"]
            native = np.asarray(Image.open(ROOT / f"frames/{index:02}.png")).astype(np.int32)
            assert np.all(native[-1] == 0), (index, "bottom artwork edge is not black")
            # Genesis Plus GX 3-bit DAC values, expanded from RGB565 exactly.
            hw = np.rint(native * 7 / 255).astype(np.int32) * 34
            expected = np.empty_like(hw)
            for channel, bits in enumerate((31, 63, 31)):
                expected[:, :, channel] = (hw[:, :, channel] >> (2 if channel == 1 else 3)) * 255 // bits
            expected = expected[:, 8:328]
            for phase in ("early", "complete"):
                actual = np.asarray(Image.open(captures/f'{index:02}-{phase}.png'))
                mask=particle_mask(runtime["shots"][index-1]["captures"][phase])
                diff=np.any(actual[:176]!=expected,axis=2)
                assert not np.any(diff&mask),(region,index,phase,"background moved")
                assert np.count_nonzero(diff)<=72,(region,index,phase,"too much image changed")
            # Check every caption, including clearing the previous block while
            # the underlying image and its particles continue uninterrupted.
            for entry in shot['captions']:
                capture = next(c for c in runtime['shots'][index-1]['caption_captures'] if c['caption']==entry['caption'])
                actual = np.asarray(Image.open(captures/f'{capture["file"]}.png'))
                mask=particle_mask(capture['particles'])
                diff=np.any(actual[:176]!=expected,axis=2)
                assert not np.any(diff&mask),(region,index,entry['caption'],'caption reloaded artwork')
                assert np.count_nonzero(diff)<=72
                caption = np.zeros((48, 320, 3), dtype=np.uint8)
                for line, (x, y) in zip(entry['lines'], entry['text_origins']):
                    assert x == (40-len(line))//2
                    for col, char in enumerate(line):
                        glyph_id = encode(char)[0]-32
                        glyph = font[glyph_id]
                        yy, xx = (y-22)*8, (x+col)*8
                        caption[yy:yy+8, xx:xx+8] = np.where(glyph[:, :, None] == 15, 238, 0)
                assert np.array_equal(actual[176:224], caption), (region, index, entry['caption'], 'subtitle/UI mismatch or uncleared previous caption')
                checks.append(dict(region=region, shot=index, caption=entry['caption'],background_pixels_mismatched=0,
                                   centered_caption_exact=True, speaker_counter_and_hints_absent=True))
        menu = np.asarray(Image.open(captures/'menu-after-natural.png'))
        for suffix in ("skip", "game"):
            assert np.array_equal(menu, np.asarray(Image.open(captures/f'menu-after-{suffix}.png')))
    report = dict(passed=True, method="exact native art and full centered subtitle region vs emulator captures",
                  image_captures=len(scenes)*4, complete_captions=len(checks), background_pixel_tolerance=0,particle_pixel_tolerance=72,
                  black_artwork_bottom_edge=True, reconstructed_logo_exact=True, menus_identical_after_natural_skip_and_gameplay=True, checks=checks)
    output=args.capture_root if args.capture_root else ROOT
    (output / "pixel-validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print("PASS: 56 stationary backgrounds and 36 caption captures, no old text after caption changes, no speaker/counter/hints, menus unchanged.")


if __name__ == "__main__":
    main()
