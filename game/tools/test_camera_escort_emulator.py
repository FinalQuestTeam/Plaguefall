"""Gate interactions and full escorts with the revised camera, live VRAM checks."""
from pathlib import Path
import sys
import test_camera_motion_emulator as audit

TAIL = r'''
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2);baseline=snapshot()
        report['scope']='Real gate shooting/valve work and full controller escorts in6A/6B/12; player-first camera and live background pixels. RAM setup precedes each guarded trial. Combat isolated and shield/ally protection prepared before play.'
        for node,key in [(7,'06a'),(8,'06b'),(14,'12')]:
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'entry-'+key);protect();run(fps//2)
            initial=snapshot();d=geometry();route=maps[key]
            if key!='12':
                for i in (0,1):
                    restore(initial);protect();w16('dinorahPauseTimer',60000)
                    if key=='06b':
                        pos(*route['valve_approaches'][i]);settle_camera()
                        before=writes;ordinary=True
                        try:run(fps*2)
                        finally:ordinary=False
                        assert writes==before and read(syms['campaignRouteOps'][0]+10,1)[0]&(1<<i),('valve work',key,i)
                    pos(*route['gate_shot_approaches'][i]);hold({7},2);settle_camera()
                    before=writes;ordinary=True
                    try:
                        hold({1},fps*4);run(fps)
                        assert read(syms['campaignRouteOps'][0]+8+i,1)[0]==0,('gate not destroyed',key,i)
                        assert int.from_bytes(read(syms['campaignRouteOps'][0]+12+i*2,2),'big')==0
                        visible_pixels(d);sprite_limits()
                    finally:ordinary=False
                    assert writes==before
                    check(key+'-gate-'+str(i+1),dict(real_valve_work=key=='06b',real_player_projectiles=True,ram_writes_during_checks=0))
            restore(initial);protect();w16('dinorahPauseTimer',0)
            if key!='12':
                write(syms['campaignRouteOps'][0]+8,bytes([0,0,3]))
                for slot in (0,1):write(syms['objectiveVisuals'][0]+slot*12+9,b'\0')
            before=writes;ordinary=True;player_node=1;tick=0;cells=0;start=frames();vb=u32('vtimer')
            try:
                while state()==1 and tick<fps*210:
                    index=u8('dinorahNode');tx,ty=route['points'][min(player_node,len(route['points'])-1)];tx-=8;ty-=8
                    dx,dy=tx-u16('px'),ty-u16('py');buttons.clear()
                    if abs(dx)<=3 and abs(dy)<=3 and index>player_node:player_node+=1
                    if u16('px')-u16('dinorahX')<=64 or dx<0 or index>=len(route['points']):
                        if abs(dx)>3:buttons.add(7 if dx>0 else 6)
                        if abs(dy)>3:buttons.add(5 if dy>0 else 4)
                    run();tick+=1
                    if state()!=1:break
                    assert u16('dinorahHp')==100
                    cx,cy=signed('cameraX'),signed('cameraY');px0,py0=signed('px'),signed('py')
                    assert px0-8>=cx and px0+24<=cx+320 and py0-31>=cy+24 and py0+17<=cy+224,('escort framing',key,tick)
                    assert u16('sceneStreamFaults')==0
                    if tick%45==0:cells+=visible_pixels(d);sprite_limits()
                buttons.clear();assert state()==4,('escort did not arrive',key,state(),u8('dinorahNode'),u16('px'),u16('py'))
            finally:ordinary=False
            assert writes==before
            shot(key+'-arrived')
            check(key+'-complete-escort',dict(passed=True,seconds=round((u32('vtimer')-vb)/fps,2),fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),2),live_pixel_cells=cells,ram_writes_during_traversal=0,gates_seeded_open=key!='12',dinorah_hp=u16('dinorahHp')))
        report['passed']=True;save();print('PASS camera escorts',report['romSHA256'],flush=True)
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    prefix = audit.BOOT.read_text().split('    try:\n',1)[0]
    helpers = audit.TAIL.split('\n    try:\n',1)[0]
    namespace = {'__name__':'camera_escort_audit','__file__':str(audit.BOOT)}
    exec(compile(prefix+helpers+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).parent));main()
