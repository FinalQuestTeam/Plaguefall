"""Regression: no autonomous pan at entry, after stopping, or on pause resume."""
from pathlib import Path
import sys
import test_camera_motion_emulator as audit

TAIL = r'''
    def stationary(label,seconds=5):
        nonlocal ordinary
        buttons.clear();before=writes;ordinary=True
        position=(signed('px'),signed('py'));cameras=[];cells=0;escort_positions=set()
        ideal=(clamp(position[0]-152,0,d['width']-320),clamp(position[1]-131,0,d['height']-224))
        try:
            for tick in range(fps*seconds):
                assert state()==1,('left gameplay',label,state())
                assert (signed('px'),signed('py'))==position,('player moved',label)
                cameras.append((signed('cameraX'),signed('cameraY')))
                escort_positions.add((signed('dinorahX'),signed('dinorahY')))
                if tick%45==0:cells+=visible_pixels(d);sprite_limits()
                run()
        finally:ordinary=False
        assert writes==before
        ranges=[max(c[i] for c in cameras)-min(c[i] for c in cameras) for i in (0,1)]
        error=max(max(abs(c[i]-ideal[i]) for i in (0,1)) for c in cameras)
        result=dict(passed=ranges==[0,0] and error==0,camera_range=ranges,max_center_error=error,
                    position=position,first_camera=cameras[0],last_camera=cameras[-1],seconds=seconds,
                    escort_positions=len(escort_positions),live_pixel_cells=cells,ram_writes=0)
        report['checks'][label]=result;save();print('IDLE',label,result,flush=True)
        return result
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2);baseline=snapshot()
        report['scope']='Stationary camera: first5s of controllable gameplay,5s after actual movement/stop and5s after pause/resume. Real moving escort, isolated enemies and pre-granted protection; no RAM writes during measured controller trials.'
        for node in [int(n) for n in args.nodes.split(',')]:
            label=labels[node-1];restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'entry-'+label)
            d=geometry();protect()
            if u16('dinorahHp'):w16('dinorahPauseTimer',0)
            initial=snapshot();stationary(label+'-entry')
            restore(initial);before=writes;ordinary=True
            try:hold({7},fps//3)
            finally:ordinary=False
            assert writes==before
            stationary(label+'-stop')
            before=writes;ordinary=True
            try:press(3);until(lambda:state()==2,'pause-'+label);run(fps//4);press(0);until(lambda:state()==1,'resume-'+label)
            finally:ordinary=False
            assert writes==before
            stationary(label+'-resume')
            if d['focus']:
                restore(initial);protect()
                if u16('dinorahHp'):w16('dinorahPauseTimer',0)
                fx,fy,fw,fh=d['focus'][0]
                pos(*closest(d,fx+fw//2,fy+fh+24));settle_camera()
                stationary(label+'-landmark')
            shot(label+'-idle')
        report['passed']=all(c['passed'] for c in report['checks'].values());save()
        assert report['passed'],'Autonomous camera movement or centering error detected; see report.json'
        print('PASS idle camera',report['romSHA256'],flush=True)
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    prefix=audit.BOOT.read_text().split('    try:\n',1)[0]
    prefix=prefix.replace("default='2,3,4,5,6,7,8'","default='4,6,7,8,11,14,15,16'")
    helpers=audit.TAIL.split('\n    try:\n',1)[0]
    namespace={'__name__':'camera_idle_audit','__file__':str(audit.BOOT)}
    exec(compile(prefix+helpers+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).parent));main()
