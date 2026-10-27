"""Validate phase12 arrival, escort proximity and actual13A/13B resolution."""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    def place_npc(x,y):
        w16('dinorahX',x);w16('dinorahY',y)
        write(syms['dinorahFx'][0],struct.pack('>i',x<<6))
        write(syms['dinorahFy'][0],struct.pack('>i',y<<6))
    def setup(player,escort):
        restore(initial);isolate();w16('hp',100)
        w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000)
        # Let an already committed animation step finish before posing the NPC.
        w16('shieldTimer',60000);run(fps);pos(*player);place_npc(*escort)
    def failed():return bool(read(syms['phaseStats'][0]+8,1)[0])
    def confirm_branch(expected,dead):
        until(lambda:state()==4,'result');run(fps);press(1)
        until(lambda:u8('pendingLevel')==expected and state() in (5,6),'resolved-route')
        assert bool(u8('campaignFlags')&4)==dead
        return dict(nextNode=expected,dinorahDeadFlag=dead)
    try:
        run(120);press(3);run(fps*4);press(1)
        until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        write(syms['pendingLevel'][0],b'\x0e');press(1)
        until(lambda:state()==1 and not u8('transitioning'),'phase12-entry')
        initial=snapshot()
        # Arriving alone, walking past an escort, and killing enemies must not
        # bypass the escort objective. Positions are isolated test setup.
        for label,player,escort in [
            ('player-alone-at-union',(2848,216),(2700,216)),
            ('Dinorah-arrived-player-too-far',(2700,216),(2848,216)),
            ('both-outside-arrival-zone',(2760,216),(2776,216)),
        ]:
            setup(player,escort);w16('kills',1000);run(fps*2)
            assert state()==1 and not failed(),label
            check(label,dict(stillPlaying=True,kills=1000))
        # A short visit followed by leaving must reset the stable-arrival
        # timer. Returning together must then complete without a kill quota.
        setup((2824,216),(2848,216));holdFrames=(fps*2+4)//5
        run(holdFrames//2);assert state()==1
        place_npc(2776,216);run(2);assert state()==1
        place_npc(2848,216);run(holdFrames//2);assert state()==1
        check('arrival-hold-reset-on-leaving',dict(requiredGameFrames=holdFrames,region=report['region']))
        run(fps*3);assert state()==4 and not failed() and u16('kills')==0,('alive completion',state(),failed(),u16('kills'),u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'))
        shot('success-at-STE');check('alive-arrival-resolves13A',confirm_branch(15,False))
        # Actual insect contact kills the escort; surviving Damião must
        # continue through the game's result screen to the13B branch.
        setup((320,208),(48,208));w16('dinorahInvTimer',0);w16('dinorahHp',1)
        seed(0,4,48,208,health=200,fire=60000);run(fps*3)
        assert state()==4 and failed() and u16('hp')>0
        shot('escort-death');check('escort-death-resolves13B',confirm_branch(16,True))
        setup((2824,216),(2848,216));w16('hp',0);w16('dinorahHp',0);run(fps*4)
        assert state()==3 and not (u8('campaignFlags')&4)
        check('Damião-death-priority-over-arrival-and-branch',dict(gameOver=True))
        report['scope']='Phase12 objective conditions and actual result-to-route transitions. Isolated RAM setup for positions, health and enemies; objective checks and branch resolution run in production code. Not a normal combat completion.'
        report['passed']=True;save();print('PASS phase12 objectives',report['region'],report['romSHA256'])
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    namespace = {'__name__': 'phase12_objectives', '__file__': str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n', 1)[0] + TAIL, str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
