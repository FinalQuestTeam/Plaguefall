"""The game's 96-slot font: a..l hold Portuguese uppercase accented glyphs.

Author text in NFC UTF-8. Only the compiler's preprocessed string literals are
encoded; source files, identifiers, format specifiers and pixel art stay intact.
"""
import re
import unicodedata

ACCENTS = 'ÀÁÂÃÉÊÍÓÔÕÚÇ'
ENCODE = {c: chr(97 + i) for i, c in enumerate(ACCENTS)}
DECODE = {v: k for k, v in ENCODE.items()}


def encode(text):
    text = unicodedata.normalize('NFC', text)
    result = ''.join(ENCODE.get(c, c) for c in text)
    if any(not 32 <= ord(c) < 128 for c in result):
        raise ValueError(f'Unsupported text character: {text!r}')
    return result.encode('ascii')


def decode(text):
    if isinstance(text, bytes):
        text = text.decode('ascii')
    return ''.join(DECODE.get(c, c) for c in text)


# Comments and character literals must be skipped too: native tests also use
# this on small, unpreprocessed inputs to exercise the lexical boundaries.
TOKENS = re.compile(r'//[^\n]*|/\*.*?\*/|\'(?:\\.|[^\'\\])*\'|"(?:\\.|[^"\\])*"', re.S)
UNIVERSAL = re.compile(r'\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})')


def encode_c(source):
    def literal(match):
        token = match.group()
        if not token.startswith('"'):
            return token
        # Work escape by escape so a literal backslash followed by u00c3 is
        # never mistaken for an actual universal character escape.
        parts = re.findall(r'\\(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|.|\n)|[^\\]+', token[1:-1])
        out = []
        for part in parts:
            if UNIVERSAL.fullmatch(part):
                part = chr(int(part[2:], 16))
            elif part.startswith('\\'):
                out.append(part)
                continue
            part = unicodedata.normalize('NFC', part)
            for c in part:
                if c in ENCODE:
                    out.append(f'\\{ord(ENCODE[c]):03o}')
                elif ord(c) > 127:
                    raise ValueError(f'Unsupported character {c!r} in {token}')
                else:
                    out.append(c)
        return '"' + ''.join(out) + '"'
    return TOKENS.sub(literal, source)
