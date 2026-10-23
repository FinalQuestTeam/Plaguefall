"""Export Plaguefall's original PSG cue, 'Baiao de Ferrugem'.

Edit the sixteen 2/4 bars below; a column is a sixteenth note. Dots leave
the voice alone, and :N gives a lead note's duration in columns.
No samples, external compositions or audio drivers are required.
"""
from pathlib import Path
import argparse
import math
import re

GAME = Path(__file__).resolve().parents[1]
BARS = [
    "D5:2 . F#5 A5:2 . G5 F#5 .",
    "E5:2 . D5 . C5:2 . D5 .",
    "E5:2 . G5 A5:2 . G5 E5 .",
    "D5 . E5 G5:2 . E5 D5 .",
    "B4:2 . D5 G5:2 . A5 G5 .",
    "F#5 . E5 D5:2 . B4 D5 .",
    "F#5:2 . A5 C6:2 . A5 G#5 .",
    "A5 . G5 F#5 . E5 D5 .",
    "D5:2 . F#5 A5:2 . C6 A5 .",
    "G5 . F#5 E5:2 . D5 C5 .",
    "E5:2 . G5 C6:2 . B5 A5 .",
    "G5 . E5 D5:2 . E5 G5 .",
    "B4:2 . D5 G5 . A5 B5 .",
    "A5 . G5 F#5:2 . E5 D5 .",
    "F#5 . G#5 A5:2 . C6 A5 .",
    "G5 F#5 E5 . C5 . D5:2 .",
]
# Two 2/4 bars per harmony; the melody uses D mixolydian with G# pickups.
HARMONY = [
    ("D3", "A3", ["F#4", "A4", "C5", "A4"]),
    ("C3", "G3", ["E4", "G4", "C5", "G4"]),
    ("G3", "D4", ["B3", "D4", "G4", "D4"]),
    ("D3", "A3", ["F#4", "A4", "C5", "A4"]),
]

# Entardecer: a lower, more spacious answer in D dorian. The minor third
# (F natural) changes the colour; B natural retains some warmth in the mode.
MELANCHOLIC_BARS = [
    "D5:3 . . . F5:2 . E5 .",
    "C5:2 . A4:3 . . . D5 .",
    "E5:2 . D5 . C5:3 . . .",
    "G4:3 . . . E5:2 . D5 .",
    "B4:2 . A4 . G4:3 . . .",
    "D5:3 . . . B4:2 . A4 .",
    "C5:2 . E5:2 . D5 . C5 .",
    "B4:2 . A4:3 . . . . .",
    "D5:3 . . . F5:2 . A5 .",
    "G5:2 . F5 . E5:3 . . .",
    "E5:2 . G5:3 . . . E5 .",
    "D5:3 . . . C5:2 . G4 .",
    "B4:2 . D5:2 . A4:3 . . .",
    "G4:3 . . . B4:2 . D5 .",
    "E5:2 . D5 . C5:3 . . .",
    "B4:2 . A4:2 . D5:3 . . .",
]
MELANCHOLIC_HARMONY = [
    ("D3", "A3", ["F4", "A4", "D5", "E4"]),
    ("C3", "G3", ["E4", "G4", "C5", "D4"]),
    ("G3", "D4", ["B3", "D4", "G4", "A4"]),
    ("A3", "E4", ["C4", "E4", "G4", "E4"]),
]

# Breu: D-minor / phrygian colour, low register and an altered dominant.
# Eb against D and Bb against A add unease without losing the baiao pulse.
DARK_BARS = [
    "D4:4 . . . . Eb4 . D4",
    "A4:3 . . . F4:2 . Eb4 .",
    "Eb4:3 . . . G4:2 . F4 .",
    "Bb4:2 . A4 . G4:3 . . .",
    "F4:3 . . . D4:2 . C4 .",
    "Bb3:4 . . . D4:2 . F4 .",
    "E4:3 . . . G4:2 . Bb4 .",
    "A4:2 . G4 . Eb4:2 . C#4 .",
    "D4:4 . . . F4:2 . Eb4 .",
    "A4:3 . . . G4:2 . F4 .",
    "G4:2 . F4 . Eb4:3 . . .",
    "Bb4:3 . . . A4:2 . G4 .",
    "F4:4 . . . D4:2 . C4 .",
    "D4:3 . . . F4:2 . Eb4 .",
    "E4:2 . G4:2 . Bb4:3 . . .",
    "A4:2 . Eb4 . C#4:2 . D4 .",
]
DARK_HARMONY = [
    ("D3", "A3", ["F3", "A3", "Eb4", "A3"]),
    ("Eb3", "Bb3", ["G3", "Bb3", "Eb4", "F3"]),
    ("Bb2", "F3", ["D4", "F3", "Bb3", "C4"]),
    ("A2", "E3", ["C#4", "E4", "G3", "Bb3"]),
]

# Ladainha de Ferro: original chapel-inspired phrases, organ-like held voices,
# pedal bass and occasional high bell notes. No pre-existing hymn is quoted.
CHURCH_BARS = [
    "D4:8 . . . . . . .",
    "F4:4 . . . E4:2 . D4:2 .",
    "F4:6 . . . . . D4:2 .",
    "C4:4 . . . D4:4 . . .",
    "D4:4 . . . G4:4 . . .",
    "F4:4 . . . E4:2 . D4:2 .",
    "E4:6 . . . . . C#4:2 .",
    "D4:4 . . . C#4:4 . . .",
    "F4:8 . . . . . . .",
    "A4:4 . . . G4:2 . F4:2 .",
    "F4:4 . . . D4:4 . . .",
    "C4:4 . . . Bb3:4 . . .",
    "D4:4 . . . G4:4 . . .",
    "F4:4 . . . E4:2 . D4:2 .",
    "E4:4 . . . C#4:4 . . .",
    "D4:8 . . . . . . .",
]
CHURCH_HARMONY = [
    ("D3", "A3", ["F4", "A4", "D6"]),
    ("Bb2", "F3", ["D4", "F4", "F6"]),
    ("G3", "D4", ["Bb3", "D4", "G5"]),
    ("A2", "E3", ["C#4", "E4", "A5"]),
]


def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
             "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
             "Eb": 3, "Bb": 10}
    midi = (int(note[-1]) + 1) * 12 + names[note[:-1]]
    return round(440 * math.pow(2, (midi - 69) / 12))


def compose(variant="original"):
    assert variant in ("original", "melancolico", "sombrio", "igreja")
    melancholy = variant == "melancolico"
    dark = variant == "sombrio"
    church = variant == "igreja"
    bars = CHURCH_BARS if church else DARK_BARS if dark else MELANCHOLIC_BARS if melancholy else BARS
    harmony = CHURCH_HARMONY if church else DARK_HARMONY if dark else MELANCHOLIC_HARMONY if melancholy else HARMONY
    melody, gates, arp, bass, drums = [], [], [], [], []
    for index, bar in enumerate(bars):
        notes = bar.split()
        assert len(notes) == 8, (index, notes)
        root, fifth, chord = harmony[(index // 2) % 4]
        if church and index == 15:
            root, fifth, chord = CHURCH_HARMONY[0] # final cadence resolves to D minor
        for col, token in enumerate(notes):
            parts = token.split(":")
            duration = int(parts[1]) if len(parts) == 2 else 1
            assert col + duration <= 8
            assert all(notes[n] == "." for n in range(col + 1, col + duration))
            melody.append(0 if token == "." else hz(parts[0]))
            gates.append(0 if token == "." else duration)
            if church:
                bell = (index % 4 == 0)
                upper = chord[2]
                arp.append(hz(upper if bell else chord[0]) if col == 0 else hz(chord[1]) if col == 4 else 0)
                bass.append(hz(root) if col == 0 else 0)
                drums.append(3 if index in (7, 15) and col == 7 else 0)
                continue
            arp.append(hz(chord[col // 2]) if col & 1 else 0)
            # Root / anticipated fifth / root / fifth: leave breathing room.
            bass.append(hz(root) if col in (0, 4) else hz(fifth) if col in (3, 6) else 0)
            # 1: low thump, 2: dry slap, 3: periodic metallic tick, 4: iron fill.
            pattern = [1, 0, 3, 2, 1, 0, 2, 0] if dark else [1, 3, 0, 2, 1, 0, 2, 3] if melancholy else [1, 3, 0, 2, 1, 3, 2, 3]
            drum = pattern[col]
            if index in (7, 15) and col == 7:
                drum = 2 if melancholy else 4
            drums.append(drum)
    assert len(melody) == 128
    header = """// Generated by tools/compose_music.py; edit the bar score there.
#ifndef SONG_DATA_H
#define SONG_DATA_H
#include <genesis.h>

// Baiao de Ferrugem: original northeastern / industrial PSG cue.
// 16 bars of 2/4, 8 sixteenths per bar; A / A' with a short turnaround.
// D mixolydian; G# pickup notes add tension against the D pedal.
// Harmony: D7 / C / G / D7, two bars each, repeated with melodic variation.
#define SEQ_STEPS 128
#define SONG_BAR_STEPS 8

"""
    if melancholy:
        header = header.replace("Baiao de Ferrugem: original northeastern / industrial PSG cue.",
                                "Baiao de Ferrugem - Entardecer: melancholic northeastern / industrial PSG cue.")
        header = header.replace("D mixolydian; G# pickup notes add tension against the D pedal.",
                                "D dorian; lower melodic register, longer phrases and more breathing room.")
        header = header.replace("Harmony: D7 / C / G / D7, two bars each, repeated with melodic variation.",
                                "Harmony: Dm(add9) / C(add9) / G(add9) / Am7, two bars each.")
    if dark:
        header = header.replace("Baiao de Ferrugem: original northeastern / industrial PSG cue.",
                                "Baiao de Ferrugem - Breu: darker northeastern / industrial PSG cue.")
        header = header.replace("D mixolydian; G# pickup notes add tension against the D pedal.",
                                "D-minor / phrygian colour; Eb tension, low register, sparse long notes.")
        header = header.replace("Harmony: D7 / C / G / D7, two bars each, repeated with melodic variation.",
                                "Harmony: Dm(b9) / Eb(add9) / Bb(add9) / A7(b9), two bars each.")
    if church:
        header = header.replace("Baiao de Ferrugem: original northeastern / industrial PSG cue.",
                                "Ladainha de Ferro: original church-inspired / industrial PSG cue.")
        header = header.replace("D mixolydian; G# pickup notes add tension against the D pedal.",
                                "D minor; long chant-like phrases, held harmony, pedal bass and bells.")
        header = header.replace("Harmony: D7 / C / G / D7, two bars each, repeated with melodic variation.",
                                "Harmony: Dm / Bb / Gm / A7; final bar resolves to Dm.")
    for kind, name, values in [("u16", "MEL", melody), ("u8", "MEL_GATE", gates),
                               ("u16", "ARP", arp), ("u16", "BASS", bass),
                               ("u8", "DRUM", drums)]:
        header += f"static const {kind} {name}[SEQ_STEPS] = {{\n"
        for start in range(0, 128, 8):
            header += "    " + ", ".join(str(n) for n in values[start:start+8]) + f", // bar {start // 8 + 1:02}\n"
        header += "};\n\n"
    return header + "#endif // SONG_DATA_H\n"


def catalog():
    """Pack each original score under a separate name for runtime selection."""
    header = """// Generated by tools/compose_music.py --catalog.
#ifndef SONG_CATALOG_DATA_H
#define SONG_CATALOG_DATA_H
#define SEQ_STEPS 128
#define SONG_BAR_STEPS 8

"""
    tracks = [("original", "BAIAO", "BAIÃO DE FERRUGEM", 9, 6),
              ("melancolico", "ENTARDECER", "ENTARDECER", 10, 7),
              ("sombrio", "BREU", "BREU", 12, 8),
              ("igreja", "LADAINHA", "LADAINHA DE FERRO", 14, 10)]
    for variant, prefix, _, _, _ in tracks:
        arrays = re.findall(r"static const (?:u8|u16) (?:MEL_GATE|MEL|ARP|BASS|DRUM)\[SEQ_STEPS\] = \{.*?\n\};", compose(variant), re.S)
        assert len(arrays) == 5
        for array in arrays:
            header += re.sub(r"\b(MEL_GATE|MEL|ARP|BASS|DRUM)\b", lambda m: prefix + "_" + m.group(), array) + "\n\n"
    header += "static const MusicScore MUSIC_SCORES[MUSIC_TRACK_COUNT] = {\n"
    for _, prefix, name, calm, hot in tracks:
        arrays = ", ".join(prefix + "_" + voice for voice in ("MEL", "MEL_GATE", "ARP", "BASS", "DRUM"))
        header += f'    {{ "{name}", {arrays}, {calm}, {hot} }},\n'
    return header + "};\n#endif // SONG_CATALOG_DATA_H\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--catalog", action="store_true", help="Export all scores for the in-game player")
    parser.add_argument("--variant", choices=("original", "melancolico", "sombrio", "igreja"), default="original")
    args = parser.parse_args()
    name = {"original": "song_data.h", "melancolico": "song_data_melancholic.h", "sombrio": "song_data_dark.h", "igreja": "song_data_church.h"}[args.variant]
    target = GAME / "src/system/audio" / ("song_catalog_data.h" if args.catalog else name)
    score = catalog() if args.catalog else compose(args.variant)
    if args.check:
        assert target.read_text() == score, "Run tools/compose_music.py to export the edited score"
    else:
        target.write_text(score)
    # Individual exports also refresh the runtime player, so an edited score
    # cannot silently leave the game's catalog out of date.
    if not args.catalog:
        runtime_target = GAME / "src/system/audio/song_catalog_data.h"
        runtime = catalog()
        if args.check:
            assert runtime_target.read_text() == runtime, "Refresh the runtime catalog with --catalog"
        else:
            runtime_target.write_text(runtime)
    label = "catalog / 4 tracks" if args.catalog else args.variant
    print(f"Baiao de Ferrugem / {label}: 16 bars, 128 steps; " + ("score verified." if args.check else "exported."))
