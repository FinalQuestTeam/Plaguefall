"""Priority transmitters resist controller-triggered bombs in the production ROM.

Run with arch -x86_64 /usr/bin/python3. RAM isolates enemy pressure and seeds
ordinary reinforcements/projectiles; bomb activation and damage use game code.
"""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def cr():return read(syms['campaignResistance'][0]+20,1)[0]
    def enemy(i):return read(syms['enemies'][0]+i*46,46)
    def quiet():
        zeros('pshots');zeros('eshots');w16('hp',30000)
        w16('spawnTimer',60000)
        write(syms['campaignResistance'][0]+2,struct.pack('>H',60000))
        for i in range(3,16):write(syms['enemies'][0]+i*46+44,b'\0')
        for i in range(3):write(syms['enemies'][0]+i*46+16,struct.pack('>H',60000))
    def bomb():
        nonlocal ordinary
        w16('bombs',1);before=writes;ordinary=True;ui(0);ordinary=False
        assert writes==before and u16('bombs')==0,'bomb was not used through controller'
    def hit(i):
        # A stationary normal projectile inside the target's collision box.
        # The normal SHOTS_updatePlayer -> ENEMIES_damageBox path applies it.
        x,y=struct.unpack('>hh',enemy(i)[:4]);d=bytearray(20)
        struct.pack_into('>iiii',d,0,(x+4)*64,(y+4)*64,0,0);d[18]=1
        write(syms['pshots'][0],d);run(4)
    try:
        run(120);ui(3);run(fps*4);ui(4);ui(1)
        until(lambda:'FASES DA CAMPANHA' in textrow(2),'phase-selector')
        run(fps//2);ui(1)
        until(lambda:state()==0 and not u8('transitioning'),'selector-prep',fps*20)
        selection=snapshot()
        def enter(node):
            restore(selection);write(syms['pendingLevel'][0],bytes([node]));ui(1)
            until(lambda:state()==1 and u8('currentLevel')==node and not u8('transitioning'),'stage-entry',fps*20)
            until(lambda:u16('freezeTimer')==0 and frames()>=5,'stage-ready')
            quiet();run(2)
        enter(10) # N_8: three authored priority Torreoes, each with four HP.
        assert cr()==0 and all(enemy(i)[30]==0 and enemy(i)[31]==4 and enemy(i)[44] for i in range(3))
        initial=snapshot()
        for i,kind in enumerate((0,4,5),3):seed(i,kind,600+(i-3)*24,440,health=3)
        bomb()
        assert state()==1 and cr()==0,'bomb advanced the mission'
        assert all(enemy(i)[44] and enemy(i)[31]==4 for i in range(3)),'bomb killed/damaged a transmitter'
        assert all(not enemy(i)[44] for i in range(3,6)),'ordinary reinforcements survived'
        check('bomb-preserves-three-targets-and-kills-reinforcements')
        bomb()
        assert cr()==0 and all(enemy(i)[44] and enemy(i)[31]==4 for i in range(3))
        check('repeated-bomb-does-not-progress-objective')
        # Completing a target releases its slot for ordinary reinforcements.
        for hits in range(1,5):
            hit(0)
            assert enemy(0)[31]==4-hits
        assert cr()==1 and not enemy(0)[44]
        seed(0,0,600,440,health=3);bomb()
        assert not enemy(0)[44] and cr()==1
        assert all(enemy(i)[44] and enemy(i)[31]==4 for i in (1,2))
        check('completed-target-slot-is-not-bomb-protected')
        # All three mission targets remain killable by normal projectiles.
        restore(initial);quiet()
        for i in range(3):
            for hits in range(1,5):
                hit(i);assert enemy(i)[31]==4-hits
            assert cr()==(1<<(i+1))-1 and not enemy(i)[44]
        until(lambda:state()==4,'projectile-victory')
        check('four-real-projectile-hits-per-target-still-win')
        enter(2) # N_2A: the same type in low slots outside the priority mission.
        isolate()
        for i in range(3):seed(i,0,200+i*32,240,health=3)
        bomb()
        assert all(not enemy(i)[44] for i in range(3))
        check('ordinary-torreoes-in-other-stage-remain-vulnerable')
        report['passed']=True;save();print('PASS priority bomb',report['region'],report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-priority-bomb');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''


def main():
    prefix = BOOT.read_text().split('    try:\n', 1)[0]
    namespace = {'__name__': 'priority_bomb_probe', '__file__': str(BOOT)}
    exec(compile(prefix + TAIL, str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
