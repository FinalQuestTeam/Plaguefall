"""Current phase7: exact scene/overlays, five real cargo trips and native load.

Controller entry, opening, pickup, delivery, collision and pause are real.
RAM isolates enemies during geometry/transport; separate natural combat is
unmodified. Load preserves active AI/projectiles, protecting health only.
"""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import faces,edges,closest,path
    root=GAME/'art/phase07-urban-v2';d=json.loads((root/'manifest.json').read_text())
    patterns=(root/'native/tiles.bin').read_bytes();ids=struct.unpack('>6528H',(root/'native/map.bin').read_bytes())
    cargo_raw=(GAME/'res/objectives/animations.bin').read_bytes()[2496*4:3264*4]
    report['scope']='Urban phase7: asphalt, open sewer manhole and four white canvas stalls. Controller entry, five cargo openings/pickups/deliveries and movement; RAM isolates enemy pressure for functional checks. Exact visible VRAM and overlay pixels, cache, pause, collision. Native max4-enemy/6+6-projectile load retains AI/active trajectories. Natural combat sample has no RAM health or AI grants.'
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
        isolate();write(syms['campaignResistance'][0]+2,struct.pack('>H',60000))
    def cr(offset):return read(syms['campaignResistance'][0]+offset,1)[0]
    def pixels():
        assert u16('sceneStreamFaults')==0
        assert u16('sceneStreamPeak')<=560
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;objects=[];used=set();ink=0
        for i in range(6):
            b=read(syms['objectiveVisuals'][0]+i*12,12);xx,yy=struct.unpack('>hh',b[:4]);frame=b[7]
            if b[9]:objects.append(((xx-16)//8,(yy-24)//8,frame))
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*96+col];slot=int.from_bytes(read(loc+source*2,2),'big')
                assert slot<560,('missing slot',cx,cy,col,row,source,slot)
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',col,row)
                overlay=vw(u16('bga_addr')+at);expected=None
                for ox,oy,frame in objects:
                    if ox<=col<ox+4 and oy<=row<oy+4:
                        offset=(frame*16+(col-ox)*4+row-oy)*32;tile=cargo_raw[offset:offset+32]
                        if any(tile):expected=tile
                if expected:
                    assert overlay&0xe000==0x2000 and vr((overlay&2047)*32,32)==expected,('cargo overlay',col,row,overlay)
                    ink+=1
                else:assert overlay==0,('BG_A fragment',col,row,hex(overlay))
                used.add(slot)
        return dict(camera=[cx,cy],visible_patterns=len(used),peak=u16('sceneStreamPeak'),cargo_cells=ink)
    def navigation(tx,ty):
        dynamic=[r for i,r in enumerate(d['cargo_solids']) if not(cr(17)&(1<<i))]
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
                if cr(18)==5:buttons.clear();return
                assert state()==1 or cr(18)==5,('left transport',state(),u16('hp'))
            else:raise AssertionError(('navigation stalled',x,y,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps);ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)
        write(syms['pendingLevel'][0],bytes([9]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==9 and not u8('transitioning'),'phase7-entry',fps*20)
        initial=snapshot();quiet();wait_camera();shot('01-entrada');check('entry-exact-pixels',pixels())
        assert (u16('arenaMinY'),u16('arenaMaxY'))==(176,479)
        # The open manhole is the phase6 exit landmark, not a new trap/solid.
        before_writes=writes;ordinary=True;hold({7},fps//2);ordinary=False
        assert u16('px')>=104 and writes==before_writes,'manhole landing blocks exit'
        wait_camera();shot('01-bueiro-saida');check('open-manhole-landing-controller',dict(landing=[64,192],exit_position=[u16('px'),u16('py')],no_RAM_writes=True,pixels=pixels()))
        views=[]
        for x in [64,224,392,552,704,552,392,224,64]:
            for y in [192,272,368,464]:
                xx,yy=closest(d,x,y,extra=d['cargo_solids']);pos(xx,yy);wait_camera();views.append(pixels())
            shot('camera-'+str(x))
        check('full-map-forward-reverse-and-vertical',dict(samples=len(views),maximum_visible=max(v['visible_patterns'] for v in views),zero_pixel_mismatches=True))
        pos(392,432);hold({5},fps*2);wait_camera()
        assert u16('py')==464 and u16('cameraY')==320,('lower wall hidden',u16('py'),u16('cameraY'))
        check('southern-limit-and-full-lower-art',pixels());shot('02-limite-inferior')
        collisions=[]
        for x,y,button,axis,limit,sign in faces(d):
            pos(x,y);hold({button},fps//2);v=u16(axis)
            assert v<=limit if sign>0 else v>=limit,('prop face',x,y,button,v,limit)
            collisions.append([x,y,button,v])
        for x,y,button,axis,limit in edges(d):
            pos(x,y);hold({button},fps//2);assert u16(axis)==limit,('world edge',button,u16(axis),limit)
        check('static-contact-and-boundaries',dict(prop_faces=collisions,edges=4))
        pos(392,464);wait_camera();ui(3);until(lambda:state()==2,'pause')
        assert not u32('location'),'stream cache work retained through pause'
        shot('03-pausa');ui(0);until(lambda:state()==1,'resume');wait_camera();check('pause-restores-pixels',pixels())
        # Five full trips: opening, pickup, single load and depot are untouched.
        restore(initial);quiet();before_writes=writes;ordinary=True;trips=[]
        for i,(x,y) in enumerate(d['cargo']):
            rx,ry,rw,rh=d['cargo_solids'][i]
            navigation(rx-24,ry);hold({1,7},fps//3);assert u16('px')+16<=rx,('case not solid',i)
            navigation(x-8,y+16);run(fps)
            assert cr(16)&(1<<i),('cargo did not open',i)
            navigation(x+24,y+16);run(8)
            assert cr(19)==i and cr(17)&(1<<i),('cargo did not collect',i,cr(19),cr(17))
            wait_camera();pixels();shot('carga-'+str(i+1)+'-coletada')
            navigation(rx-24,ry);hold({1,7},fps);assert u16('px')>=rx+rw,('collected case blocks floor',i)
            # Passing other cases while loaded can never collect a second load.
            navigation(96,384);run(8);assert cr(18)==i+1 and cr(19)==255,('delivery count',i,cr(18),cr(19))
            trips.append(dict(source=i+1,opened=True,collected=True,solid_released=True,delivered=i+1));shot('entrega-'+str(i+1))
        ordinary=False;buttons.clear();assert writes==before_writes and state()==4
        check('five-controller-cargo-trips',dict(trips=trips,ram_writes_during_trips=0,combat_isolated=True,won=True))
        loads=[]
        for label,x,y in [('casas',352,192),('deposito',224,288),('inferior',512,440)]:
            restore(initial);quiet();pos(x,y)
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
            wait_camera()
            for i,kind in enumerate([5,4,2,5]):
                ex,ey=closest(d,x-80+i*48,y+32,extra=d['cargo_solids']);seed(i,kind,ex,ey,200,0)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+64:direction=6
                if u16('px')<=x-64:direction=7
                buttons.clear();buttons.add(direction)
                for i in range(4):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(6):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*40)<<6,(u16('cameraY')+168+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(at,b)
            for _ in range(fps*3):arrange();run()
            start=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0];cams=[]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==4,('load drift',label,t,living(),state())
                assert u16('sceneStreamFaults')==0
                cpu.append(u16('cpuFrameLoad')*100/2048);cams.append(u16('cameraX'))
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();sim,physical=frames()-start,u32('vtimer')-vb;wait_camera();pixels();shot('carga-maxima-'+label)
            loads.append(dict(section=label,enemies=4,shots_per_pool=6,seconds=20,game_frames=sim,physical_frames=physical,game_fps=round(fps*sim/physical,3),mean_cpu_pct=round(statistics.mean(cpu),2),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,camera_x_range=[min(cams),max(cams)],active_AI_and_trajectories_retained=True,health_protected=True))
        check('authored-maximum-load',loads)
        restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;minimum=u16('hp');ticks=0
        while state()==1 and ticks<fps*30:
            buttons.clear();buttons.add(1);buttons.add([7,5,6,4][(ticks//(fps*2))%4]);run();ticks+=1
            peak=max(peak,living());minimum=min(minimum,u16('hp'))
        ordinary=False;buttons.clear();shot('combate-natural')
        check('natural-combat-smoke',dict(seconds=round(ticks/fps,2),state=state(),minimum_hp=minimum,peak_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_health_AI_grants=False,scope='30s automated movement and fire; not human difficulty approval or complete natural transport'))
        report['performance_target_met']=all(v['game_frames']==v['physical_frames'] for v in loads);report['human_difficulty_approved']=False
        report['passed']=True;save();print('PASS phase7 spacious',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase07');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase07_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
