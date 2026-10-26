"""Phase9 modular street: exact cache, full controller traversal, collision and load."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''


    from campaign_geometry import faces,edges,closest,path
    root=GAME/'art/phase09-three-segments-v1';d=json.loads((root/'manifest.json').read_text());native=root
    patterns=(native/'native/tiles.bin').read_bytes();ids=struct.unpack('>12800H',(native/'native/map.bin').read_bytes())
    report['scope']='Modular phase9: industrial perimeter, four workshop buildings and three trucks. Controller entry, full controller-only traversal and movement; RAM isolates enemy pressure for functional checks. Exact visible VRAM and overlay pixels, cache, pause, collision. Native max3-enemy/4+4-projectile load retains AI/active trajectories. Natural combat sample has no RAM health or AI grants.'
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*15):
            run();current=(u16('cameraX'),u16('cameraY'))
            if state()!=1:return
            stable=stable+1 if current==previous else 0;previous=current
            if stable>=8:run(2);return
        raise AssertionError('camera stalled')
    def quiet():
        isolate();w16('hp',30000)
    def cr(offset):return read(syms['campaignResistance'][0]+offset,1)[0]
    def pixels():
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=448
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;used=set()
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*320+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<448
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',col,row)
                assert vw(u16('bga_addr')+at)==0,('foreign BG_A fragment',col,row)
                used.add(slot)
        return dict(camera=[cx,cy],visible_patterns=len(used),peak=u16('sceneStreamPeak'))
    def navigation(tx,ty):
        dynamic=[]
        nav={**d,'solids':d['solids']+dynamic}
        sx,sy=u16('px'),u16('py');start=(round(sx/8)*8,round(sy/8)*8)
        corners=path(nav,start,(tx,ty),4)
        for x,y in corners:
            for _ in range(fps*20):
                dx,dy=x-u16('px'),y-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:break
                buttons.clear();buttons.add(1)
                if abs(dx)>2:buttons.add(7 if dx>0 else 6)
                if abs(dy)>2:buttons.add(5 if dy>0 else 4)
                run()
                if state()==4:buttons.clear();return
                assert state()==1,('left transport',state(),u16('hp'))
            else:raise AssertionError(('navigation stalled',x,y,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps);ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)
        write(syms['pendingLevel'][0],bytes([11]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==11 and not u8('transitioning'),'phase9-entry',fps*20)
        initial=snapshot();quiet();wait_camera();shot('01-entry');check('entry-native-pixels',pixels())
        assert (u16('arenaMinY'),u16('arenaMaxY'))==(96,287)
        views=[]
        for x in list(range(64,2305,128))+list(reversed(range(64,2305,128))):
            for y in [120,184,264]:
                xx,yy=closest(d,x,y);pos(xx,yy);wait_camera();views.append(pixels());sprite_limits()
        pos(2368,104);wait_camera();pixels();shot('02-factory-entry')
        pos(2216,248);wait_camera();pixels();shot('05-final-truck')
        check('full-map-forward-reverse-vertical',dict(samples=len(views)+1,zero_pixel_mismatches=True,maximum_peak=u16('sceneStreamPeak')))
        collisions=[]
        for x,y,button,axis,limit,sign in faces(d):
            pos(x,y);hold({button},fps//2);v=u16(axis)
            assert v<=limit if sign>0 else v>=limit,('prop face',x,y,button,v,limit)
            collisions.append([x,y,button,v])
        for x,y,button,axis,limit in edges(d):
            pos(x,y);hold({button},fps//2);assert u16(axis)==limit
        check('seven-prop-collisions-and-bounds',dict(probes=collisions,edges=4))
        pos(1056,272);wait_camera();shot('03-lower-boundary');ui(3);until(lambda:state()==2,'pause');assert not u32('location')
        ui(0);until(lambda:state()==1,'resume');wait_camera();check('pause-restores-native-pixels',pixels())
        restore(initial);quiet();before_writes=writes;ordinary=True;visited=[];start=frames();vb=u32('vtimer')
        for i,(x,y) in enumerate(d['player_waypoints'][1:]):
            navigation(x,y);visited.append([u16('px'),u16('py')])
            if state()==1:
                wait_camera();pixels()
                if i in (1,3,5,7,9):shot('path-'+str(i))
        until(lambda:state()==4,'factory-reached');ordinary=False
        assert writes==before_writes
        shot('04-completed');check('full-controller-traversal',dict(won=True,visited=visited,ram_writes=0,combat_isolated=True,physical_seconds=round((u32('vtimer')-vb)/fps,2),method='controller navigation; camera pixel probes and brief camera settling at bends; no position/progress writes'))
        loads=[]
        for label,x,y in [('arrival',352,184),('loading',1072,176),('warehouse',1640,120),('final-truck',2184,120)]:
            restore(initial);quiet();pos(x,y);wait_camera()
            for i,kind in enumerate([5,4,2]):
                ex,ey=closest(d,x-80+i*48,y+32);seed(i,kind,ex,ey,200,0)
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+64:direction=6
                if u16('px')<=x-64:direction=7
                buttons.clear();buttons.add(direction);w16('hp',30000)
                for i in range(3):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(4):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*40)<<6,(u16('cameraY')+168+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(at,b)
            for _ in range(fps*3):arrange();run()
            start=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==3
                assert u16('sceneStreamFaults')==0
                cpu.append(u16('cpuFrameLoad')*100/2048)
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();sim,physical=frames()-start,u32('vtimer')-vb;wait_camera();pixels();shot('load-'+label)
            loads.append(dict(section=label,enemies=3,shots_per_pool=4,seconds=20,game_fps=round(fps*sim/physical,3),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,setup='authored positions; real enemy AI; health protected; inactive shots replenished'))
        check('maximum-configured-load',loads)
        restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;ticks=0
        while state()==1 and ticks<fps*30:
            buttons.clear();buttons.update({1,[7,5,6,4][(ticks//(fps*2))%4]});run();ticks+=1;peak=max(peak,living())
        ordinary=False;buttons.clear();shot('natural-combat');check('natural-combat',dict(seconds=round(ticks/fps,2),state=state(),hp=u16('hp'),peak_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_grants=False,human_difficulty_certified=False))
        report['passed']=True;save();print('PASS phase9 modular',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase09');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase09_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
