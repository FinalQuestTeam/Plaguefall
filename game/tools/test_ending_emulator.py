"""Exercise all eight epilogues from boss settlement through the victory menu.

Reuse the project's libretro harness. RAM seeds the boss result and campaign
consequences; slide playback, input, fades and replay use production code.
"""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==8 and not u8('transitioning'),'entry-code');press(1)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        write(syms['pendingLevel'][0],bytes([19]));press(1)
        until(lambda:state()==1 and not u8('transitioning'),'boss');isolate()
        baseline=snapshot()
        exported=json.loads((GAME/'art/ending-slides-v1/export.json').read_text())
        tiles=(GAME/'res/ending/tiles.bin').read_bytes()
        signatures=[tiles[i*924*32:i*924*32+64] for i in range(6)]
        def current_shot():
            signature=vr(16*32,64)
            return signatures.index(signature) if signature in signatures else -1
        def win(flags):
            restore(baseline);write(syms['campaignFlags'][0],bytes([flags]))
            write(syms['bossDefeated'][0],b'\1')
        def verify_text(caption):
            import textwrap
            from text_codec import encode
            font=(GAME/'res/intro/font.bin').read_bytes()
            assert vr(1440*32,3072)==font,'caption font overwritten'
            lines=textwrap.wrap(caption.upper(),width=36,break_long_words=False,break_on_hyphens=False)
            first=22+(6-len(lines))//2
            pixels=rgb()
            for row,line in enumerate(lines):
                assert line in textrow(first+row),(caption,textrow(first+row))
                x=(40-len(line))//2*8;y=(first+row)*8
                for col,char in enumerate(encode(line).decode('ascii')):
                    glyph=font[(ord(char)-32)*32:(ord(char)-31)*32]
                    for gy in range(8):
                        for gx in range(8):
                            packed=glyph[gy*4+gx//2]
                            ink=(packed>>4 if gx%2==0 else packed&15)==15
                            offset=((y+gy)*w+x+col*8+gx)*3
                            visible=all(c>200 for c in pixels[offset:offset+3])
                            assert visible==ink,('caption pixel',char,gx,gy,ink,pixels[offset:offset+3])
        for flags,sequence in enumerate(exported['sequences']):
            win(flags)
            for slide,index in enumerate(sequence):
                until(lambda:current_shot()==index,'slide-'+str(flags)+'-'+str(slide),limit=fps*12)
                # A/B/C have no action; let captions type while holding them.
                hold({0,1,8},fps*4)
                assert current_shot()==index,('unexpected slide advance',flags,slide)
                assert vr(16*32,924*32)==tiles[index*924*32:(index+1)*924*32]
                verify_text(exported['scenes'][index]['captions'][0]['text'])
                shot(str(flags)+'-'+str(slide)+'-'+exported['scenes'][index]['panel'])
                sat=u16('slist_addr');before=vr(sat,12*8);run(fps//2);after=vr(sat,12*8)
                assert before!=after,'stationary particles'
                # Traverse the hardware SAT to check all12 dust sprites.
                assert sprite_limits()[0]==12
                if index==4:
                    run(fps*3)
                    verify_text(exported['scenes'][index]['captions'][1]['text'])
                    shot(str(flags)+'-dinorah-reply')
            until(lambda:state()==7 and u8('resultActive') and not u8('transitioning'),'victory',limit=fps*12)
            assert u8('campaignFlags')==flags and not u16('resultCaptureFault')
            assert u16('cardBase')+32*u16('cardHeight')<=1536
            shot(str(flags)+'-victory');run(fps)
            check('ending-'+str(flags),dict(panels=[exported['scenes'][i]['panel'] for i in sequence],
                native_patterns=True,captions=True,moving_particles=12,victory_menu=True))
        # A fresh START skips every variant, and a held button cannot confirm
        # the victory menu. Release it before testing the replay choice.
        for flags,sequence in enumerate(exported['sequences']):
            win(flags);until(lambda:current_shot()==sequence[0],'skip-entry')
            run(fps);buttons.add(3);run(fps*2)
            assert state()==7 and u8('resultActive') and u8('campaignFlags')==flags
            run(fps);assert state()==7 and u8('resultActive'),'held START confirmed victory'
            buttons.clear();run(fps)
        press(5);press(1)
        until(lambda:state()==6 and not u8('transitioning'),'replay-story')
        assert u8('campaignFlags')==0 and u8('pendingLevel')==1
        run(fps);press(3)
        until(lambda:state()==8 and not u8('transitioning'),'replay-code');press(1)
        until(lambda:state()==0 and not u8('transitioning'),'replay-mission');press(1)
        until(lambda:state()==1 and not u8('transitioning'),'replay-gameplay')
        assert u8('currentLevel')==1 and u16('hp')==100 and not u16('sceneStreamFaults')
        shot('replay-phase1');check('skip-all-eight-held-start-and-replay-reset')
        report['scope']='All8 flags: production boss settlement, 3 storyboard slides, exact native patterns, Portuguese captions,12 moving particles, A/B/C ignored, START skip, held input guard, victory card, fresh phase1 on replay. RAM only seeds boss defeat and independent consequences.'
        report['passed']=True;save();print('PASS ending slideshow',report['region'])
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    namespace = {'__name__': 'ending_slideshow', '__file__': str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n', 1)[0]+TAIL, str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
