"""O Sonho Atendido: original PSG score for the twelve storyboard shots.

Times are quarter seconds (a sixteenth at 60 BPM). Storyboard sections
are assembled into one uninterrupted score, starting on the Plaguefall logo.
No existing song, samples, or external audio driver is used.
"""
from pathlib import Path
import argparse
import math
import re

GAME = Path(__file__).resolve().parents[1]
DURATIONS = [5, 5, 8, 4, 7, 8, 10, 9, 10, 7, 11, 5]
NAMES = ["A pergunta", "A promessa", "O sonho", "Agora", "Quem nao voltou",
         "Baratas", "A carga de retorno", "O trabalhador que ficou",
         "O preco de ficar", "Reza e municao", "O chamado", "Ficar no chao"]
PAD, REED, BELL, PLUCK = range(4)


def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5,
             "F#": 6, "G": 7, "G#": 8, "A": 9, "Bb": 10, "B": 11}
    midi = (int(note[-1]) + 1) * 12 + names[note[:-1]]
    return round(440 * math.pow(2, (midi - 69) / 12))


def compose():
    cues = [[] for _ in DURATIONS]

    def note(cue, at, pitch, length, voice=0, volume=6, style=REED):
        assert 0 <= cue < 12 and 0 <= at < DURATIONS[cue] * 4
        assert length > 0 and at + length <= DURATIONS[cue] * 4
        assert 0 <= voice < 4 and 0 <= volume <= 15
        cues[cue].append((at, hz(pitch) if voice < 3 else pitch,
                          length, voice, volume, style))

    def line(cue, entries, volume=6):
        for at, pitch, length in entries:
            note(cue, at, pitch, length, volume=volume)

    def pedal(cue, pitch, volume=8):
        note(cue, 0, pitch, DURATIONS[cue]*4, 2, volume, PAD)

    def pulse(cue, roots, volume=8):
        # A restrained root / anticipated fifth pattern recalls the baiao.
        for bar in range((DURATIONS[cue]*4+7)//8):
            root, fifth = roots[min(bar//2, len(roots)-1)]
            for offset, pitch in ((0, root), (3, fifth), (4, root), (6, fifth)):
                at = bar*8+offset
                if at < DURATIONS[cue]*4:
                    note(cue, at, pitch, 1, 2, volume, PLUCK)

    # 01: a question in the dark. Leave the first second to wind/radio texture.
    note(0, 4, "D3", 14, 2, 10, PAD)
    line(0, [(6,"D4",5), (14,"A4",4)], 9)
    note(0, 0, 2, 1, 3, 13, PLUCK)
    note(0, 11, 0, 1, 3, 13, PLUCK)

    # 02: the promise falters; a semitone and a deliberate final silence.
    pedal(1,"A2",10)
    line(1, [(1,"F4",4), (6,"E4",4), (12,"Eb4",3)], 9)
    note(1, 0,"C#4",8,1,11,PAD)
    note(1, 13,0,1,3,12,PLUCK)

    # 03: warm D dorian, rising toward the rocket, with a small baiao figure.
    line(2, [(0,"D4",4),(4,"F4",3),(8,"A4",6),(16,"B4",4),
             (20,"A4",3),(24,"G4",3),(28,"E4",3)], 6)
    pulse(2,[("D3","A3"),("G3","D4")],9)
    for at,pitch in ((1,"A4"),(7,"D5"),(11,"F5"),(17,"B4"),(23,"D5"),(27,"G4")):
        note(2,at,pitch,2,1,10,PLUCK)

    # 04: hard return to the remade body; no triumphant fanfare.
    pedal(3,"D3",8)
    line(3,[(0,"D4",6),(8,"Eb4",2),(11,"D4",4)],8)
    note(3,0,2,2,3,10,PLUCK)

    # 05: empty suit, absent crew. An exposed falling phrase, then a click.
    pedal(4,"Bb2",10)
    line(4,[(2,"F4",6),(12,"E4",4),(20,"D4",5)],9)
    note(4,4,"A4",12,1,12,PAD)
    note(4,23,0,1,3,11,PLUCK)

    # 06: insects reveal themselves: displaced repeated notes and metal ticks.
    pedal(5,"D3",9)
    line(5,[(0,"D4",4),(8,"Eb4",3),(15,"A4",2),
             (20,"F4",4),(27,"Eb4",3)],8)
    for at in (3,7,11,18,23,29):
        note(5,at,"Eb5" if at%2 else "A4",1,1,11,PLUCK)
        note(5,at,0,1,3,12,PLUCK)

    # 07: the returning engine and the nests: increasing industrial density.
    pulse(6,[("D3","A3"),("Bb2","F3"),("A2","E3")],7)
    line(6,[(0,"D4",6),(8,"Eb4",6),(16,"F4",6),
             (24,"E4",4),(30,"C#4",4),(36,"A3",3)],7)
    for at in range(1,39,3):
        note(6,at,"A4" if at<20 else "Bb4",1,1,9,PLUCK)
    for at in (0,8,16,24,28,32,36,38):
        note(6,at,2 if at%8==0 else 0,1,3,10,PLUCK)

    # 08: the worker behind the fence. The dream returns, now with Bb not B.
    line(7,[(0,"D4",4),(4,"F4",3),(8,"A4",6),(16,"Bb4",4),
             (21,"A4",3),(26,"F4",3),(31,"E4",4)],7)
    pulse(7,[("D3","A3"),("Bb2","F3"),("A2","E3")],9)
    for at,pitch in ((2,"A4"),(10,"D5"),(18,"F5"),(26,"C#5")):
        note(7,at,pitch,3,1,11,PLUCK)

    # 09: injury becomes a choice to protect. Open fifths replace the friction.
    line(8,[(0,"D4",6),(8,"F4",4),(14,"G4",5),(20,"A4",6),
             (28,"G4",4),(34,"F4",5)],6)
    pulse(8,[("Bb2","F3"),("G3","D4"),("D3","A3")],8)
    for at,pitch in ((0,"F4"),(8,"A4"),(16,"D5"),(24,"A4"),(32,"D5")):
        note(8,at,pitch,6,1,10,PAD)
    for at in (0,8,16,24,32):
        note(8,at,2,1,3,12,PLUCK)

    # 10: the rosary. A brief chapel-like answer, no supernatural sting.
    pedal(9,"D3",10)
    line(9,[(0,"F4",6),(8,"E4",4),(14,"D4",10)],8)
    note(9,0,"A5",3,1,10,BELL)
    note(9,8,"A4",8,1,11,PAD)
    note(9,16,"F4",10,1,11,PAD)

    # 11: give the radio entrance two seconds, then build a protective pulse.
    line(10,[(8,"D4",4),(14,"F4",3),(20,"A4",5),(28,"G4",4),
              (34,"E4",3),(39,"C#4",4)],7)
    for at in range(8,44):
        phase=at%8
        if phase in (0,3,4,6):
            note(10,at,"D3" if phase in (0,4) else "A3",1,2,8,PLUCK)
        if phase in (1,5):
            note(10,at,"F4" if at<32 else "E4",1,1,10,PLUCK)
        if phase in (0,6):
            note(10,at,2 if phase==0 else 0,1,3,11,PLUCK)

    # 12: resolve to Dm, commit to the passage, then release before the menu.
    line(11,[(0,"D4",3),(4,"F4",3),(8,"A4",3),(12,"D5",7)],6)
    for at in (0,3,4,6,8,11):
        note(11,at,"D3" if at%4==0 else "A3",1,2,7,PLUCK)
    note(11,12,"D3",7,2,8,PAD)
    note(11,0,"A4",3,1,10,PLUCK)
    note(11,8,"F5",3,1,10,PLUCK)
    note(11,12,"A4",7,1,10,PAD)
    for at in (0,6,8):
        note(11,at,2,1,3,11,PLUCK)

    for cue,events in enumerate(cues):
        events.sort(key=lambda e:(e[0],e[3]))
        for voice in range(4):
            end=0
            for at,_,length,v,_,_ in events:
                if v==voice:
                    assert at>=end,(cue,voice,at,end)
                    end=at+length
    return cues


def continuous_score():
    # Four-second title prelude, followed by all storyboard sections on the
    # same clock. Shot changes never reset this clock or the sounding voices.
    events = [(0,hz("D3"),20,2,9,PAD),
              (0,hz("D4"),8,0,8,REED),
              (8,hz("A4"),8,0,8,REED),
              (2,hz("F4"),12,1,11,PAD)]
    offset = 16
    for seconds,section in zip(DURATIONS,compose()):
        events += [(at+offset,freq,length,voice,volume,style)
                   for at,freq,length,voice,volume,style in section]
        offset += seconds*4
    # Carry the bass across rests and section boundaries. Keep short groove
    # attacks, and fill the spaces with held notes rather than musical restarts.
    bass = sorted((i for i,e in enumerate(events) if e[3]==2),key=lambda i:events[i][0])
    for current,following in zip(bass,bass[1:]):
        at,freq,length,voice,volume,style=events[current]
        gap=events[following][0]-at-length
        if gap >= 1:
            events[current]=(at,freq,events[following][0]-at,voice,max(volume,9),PAD)
    # A held final chord tolerates the few loading frames between images.
    for i,(at,freq,length,voice,volume,style) in enumerate(events):
        if at>=16+sum(DURATIONS[:-1])*4+12 and voice<3:
            events[i]=(at,freq,384-at,voice,volume,PAD)
    events.sort(key=lambda e:(e[0],e[3]))
    return events


def export():
    events=continuous_score()
    lines=['// Generated by tools/compose_opening.py. Original: O Sonho Atendido.',
           '#ifndef OPENING_DATA_H','#define OPENING_DATA_H',
           '#define OPENING_STEP_TICKS 75',
           '#define OPENING_DURATION_TICKS 28800',
           f'#define OPENING_EVENT_COUNT {len(events)}','',
           'static const OpeningEvent OPENING_EVENTS[OPENING_EVENT_COUNT] = {']
    lines += ['    { '+', '.join(map(str,event))+' },' for event in events]
    lines += ['};','#endif','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    shots=(GAME/'src/system/video/screens/intro_shots.h').read_text()
    durations=list(map(int,re.findall(r'^    \{ (\d+),',shots,re.M)))
    assert durations==DURATIONS,'Storyboard shot timing changed: update the score'
    target=GAME/'src/system/audio/opening_data.h'
    source=export()
    if args.check:
        assert target.read_text()==source,'Opening score is stale'
    else:
        target.write_text(source)
    print('O Sonho Atendido: continuous score, 4-second logo prelude + 89-second storyboard + 3-second tail; '+
          ('score verified.' if args.check else 'score exported.'))


if __name__=='__main__':
    main()
