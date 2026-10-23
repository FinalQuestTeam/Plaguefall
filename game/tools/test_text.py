"""Exercise the compiler encoding, font variants and unchanged ASCII artwork."""
from pathlib import Path
import subprocess
import tempfile
from build_text_font import font_rows, tile_data, GAME
from text_codec import ACCENTS, encode, decode, encode_c


def main():
    assert decode(encode(ACCENTS)) == ACCENTS
    assert len(encode('MISSÃO')) == 6
    assert encode('MISSA\u0303O') == encode('MISSÃO')
    assert encode('0123456789 ABC XYZ!?') == b'0123456789 ABC XYZ!?'
    for invalid in ('ação', '€', '—'):
        try:
            encode(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    source = r'''#include <stdio.h>
    // This comment must stay: Damião.
    int main(void) {
        const char *pixel_art = "abcdef0123";
        const char *literal_escape = "\\u00c3";
        printf("%s|%s|%s|%s|%d", "DAMIÃO: MISSÃO, VOCÊ, PROTEÇÃO", "\u00c0ÁÂÃÉÊÍÓÔÕÚÇ",
               pixel_art, literal_escape, 'a');
    }
    '''
    with tempfile.TemporaryDirectory(prefix='plaguefall-text-') as folder:
        cfile, binary = Path(folder) / 'text.c', Path(folder) / 'text'
        result = encode_c(source)
        assert 'Damião' in result and 'pixel_art' in result
        cfile.write_text(result)
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', str(cfile), '-o', str(binary)], check=True)
        actual = subprocess.check_output([str(binary)])
        expected = encode('DAMIÃO: MISSÃO, VOCÊ, PROTEÇÃO') + b'|' + encode(ACCENTS) + b'|abcdef0123|\\u00c3|97'
        assert actual == expected, (actual, expected)
    rows = font_rows()
    assert len(rows) == 768
    assert len(set(bytes(rows[(c-32)*8:(c-31)*8]) for c in range(97,109))) == 12
    for opaque in (False, True):
        pixels = tile_data(rows, opaque)
        assert len(pixels) == 3072
        assert {v for b in pixels for v in (b >> 4, b & 15)} == {int(opaque), 15}
        # Native compositors and both VDP variants must agree pixel for pixel.
        for y, row in enumerate(rows):
            for x in range(8):
                actual = (pixels[y*4+x//2] >> (0 if x & 1 else 4)) & 15
                assert actual == (15 if row & (128 >> x) else int(opaque))
    from PIL import Image
    original = Image.open(GAME.parent / 'SGDK/res/image/font_default.png').convert('L')
    for ch in range(32,128):
        if 97 <= ch <= 108:
            continue
        for y in range(8):
            expected = sum(128 >> x for x in range(8) if original.getpixel(((ch-32)%16*8+x,(ch-32)//16*8+y)))
            assert rows[(ch-32)*8+y] == expected
    print('Text: compiled encoding, NFC, escapes, ASCII art, 12 distinct accents and both 96-tile font variants passed.')


if __name__ == '__main__':
    main()
