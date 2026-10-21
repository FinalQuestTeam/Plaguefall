"""Check native art, centered captions and absence of UI labels in real captures."""
from pathlib import Path
import json

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]


def main():
    scenes = json.loads((ROOT / "export.json").read_text())["scenes"]
    font = np.asarray(Image.open(GAME.parent / "SGDK/res/image/font_default.png"))
    logo = np.asarray(Image.open(GAME/"art/finalquest-logo-v2/logo-native.png").convert("RGB")).astype(np.int32)
    logo_hw=np.rint(logo*7/255).astype(np.int32)*34
    logo_rgb=np.empty_like(logo_hw)
    for channel,bits in enumerate((31,63,31)):
        logo_rgb[:,:,channel]=(logo_hw[:,:,channel]>>(2 if channel==1 else 3))*255//bits
    checks = []
    for region in ("ntsc", "pal"):
        runtime = json.loads((ROOT/f"emulator-{region}/report.json").read_text())
        expected_logo=np.zeros((224,320,3),dtype=np.uint8)
        expected_logo[48:176,64:256]=logo_rgb
        assert np.array_equal(np.asarray(Image.open(ROOT/f"emulator-{region}/logo.png")),expected_logo),(region,"logo mismatch")
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
                actual = np.asarray(Image.open(ROOT / f"emulator-{region}/{index:02}-{phase}.png"))
                mask=np.ones((176,320),dtype=bool)
                for particle in runtime["shots"][index-1]["captures"][phase]:
                    x,y=particle["x"],particle["y"]
                    mask[max(0,y-1):min(176,y+9),max(0,x-1):min(320,x+9)]=False
                diff=np.any(actual[:176]!=expected,axis=2)
                assert not np.any(diff&mask),(region,index,phase,"background moved")
                assert np.count_nonzero(diff)<=72,(region,index,phase,"too much image changed")
            # The entire lower screen must be black except for the centered
            # sentence. Any speaker, slide counter, prompt or border fails this.
            caption = np.zeros((48, 320, 3), dtype=np.uint8)
            for line, (x, y) in zip(shot["lines"], shot["text_origins"]):
                assert x == (40-len(line))//2
                for col, char in enumerate(line):
                    glyph_id = ord(char)-32
                    glyph = font[glyph_id//16*8:(glyph_id//16+1)*8, glyph_id%16*8:(glyph_id%16+1)*8]
                    yy, xx = (y-22)*8, (x+col)*8
                    caption[yy:yy+8, xx:xx+8] = np.where(glyph[:, :, None] == 15, 238, 0)
            assert np.array_equal(actual[176:224], caption), (region, index, "subtitle/UI mismatch")
            checks.append(dict(region=region, shot=index, background_pixels_mismatched=0,
                               centered_caption_exact=True, speaker_counter_and_hints_absent=True))
        menu = np.asarray(Image.open(ROOT / f"emulator-{region}/menu-after-natural.png"))
        for suffix in ("skip", "game"):
            assert np.array_equal(menu, np.asarray(Image.open(ROOT / f"emulator-{region}/menu-after-{suffix}.png")))
    report = dict(passed=True, method="exact native art and full centered subtitle region vs emulator captures",
                  image_captures=48, complete_captions=24, background_pixel_tolerance=0,particle_pixel_tolerance=72,
                  black_artwork_bottom_edge=True, reconstructed_logo_exact=True, menus_identical_after_natural_skip_and_gameplay=True, checks=checks)
    (ROOT / "pixel-validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print("PASS: 48 stationary backgrounds with particles, 24 centered captions, no speaker/counter/hints, menus unchanged.")


if __name__ == "__main__":
    main()
