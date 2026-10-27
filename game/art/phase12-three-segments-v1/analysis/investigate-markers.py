from pathlib import Path
G=Path(__file__).resolve().parents[3];boot=G/'tools/test_campaign_escorts_emulator.py'
tail=r'''
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        write(syms['pendingLevel'][0],b'\x0e');press(1);until(lambda:state()==1 and not u8('transitioning'),'phase12-entry')
        isolate();w16('hp',100);w16('shieldTimer',60000);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);run(fps)
        pos(2880,208);w16('dinorahX',2776);w16('dinorahY',208)
        write(syms['dinorahFx'][0],struct.pack('>i',2776<<6));write(syms['dinorahFy'][0],struct.pack('>i',208<<6))
        previous=None;stable=0
        for _ in range(fps*20):
            run();camera=(u16('cameraX'),u16('cameraY'));stable=stable+1 if camera==previous else 0;previous=camera
            if stable>=8:break
        assert u16('cameraX')<=2720 and u16('cameraX')+320>=3024
        for _ in range(16):
            run()
            if (u16('dinorahInvTimer')>>2)&1:break
        shot('01-controlled-blink')
        before=dict(position=[u16('dinorahX'),u16('dinorahY')],player=[u16('px'),u16('py')],camera=[u16('cameraX'),u16('cameraY')],state=u8('dinorahState'),hp=u16('dinorahHp'),invincibilityFrames=u16('dinorahInvTimer'),hiddenByBlink=bool((u16('dinorahInvTimer')>>2)&1))
        w16('dinorahInvTimer',0);run(2);shot('02-Dinorah-visible')
        visible=dict(position=[u16('dinorahX'),u16('dinorahY')],invincibilityFrames=u16('dinorahInvTimer'),hp=u16('dinorahHp'))
        check('same-position-blink-and-visible',dict(before=before,after=visible,explanation='Test invincibility hides the body on alternating frames while her health bar and pause/wait alert remain visible over the facade. Her collision footprint is on the street, y208, south of building bottom200.'))
        # Show the same view with Dinorah farther south, preserving the exit
        # and player so the affiliation of the bar/alert is unambiguous.
        w16('dinorahY',256);write(syms['dinorahFy'][0],struct.pack('>i',256<<6));run(2);shot('03-NPC-indicators-follow-Dinorah')
        check('indicators-follow-NPC-not-building',dict(escortY=256,buildingBottomY=200))
        report['passed']=True;save();print('PASS diagnosis',report['romSHA256'])
    except Exception as exc:
        report['error']=repr(exc);save();raise
    finally:core.retro_unload_game();core.retro_deinit()
'''
import sys
sys.path.insert(0,str(boot.parent))
ns={'__name__':'ste_marker_investigation','__file__':str(boot)}
exec(compile(boot.read_text().split('    try:\n',1)[0]+tail,str(__file__),'exec'),ns)
ns['main']()
