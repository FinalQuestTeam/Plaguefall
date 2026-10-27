"""Phase10 factory: native pixels, ten controller kills, persistence, collision and load."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''


    from campaign_geometry import faces,edges,closest,path
    root=GAME/'art/phase10-factory-v2';d=json.loads((root/'manifest.json').read_text());native=root
    patterns=(native/'native/tiles.bin').read_bytes();ids=struct.unpack('>6528H',(native/'native/map.bin').read_bytes())
    nest_raw=(GAME/'res/objectives/animations.bin').read_bytes()[:6912]
    report['scope']='Factory phase10: industrial interior, six prop groups and ten scattered clutches. Controller entry, ten clutch destructions and movement; RAM isolates enemy pressure for functional checks. Exact visible VRAM and overlay pixels, cache, pause, collision. Native max4-enemy/6+6-projectile load retains AI/active trajectories. Natural combat sample has no RAM health or AI grants.'
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
    def cr(offset):return read(syms['campaignFactory'][0]+offset,1)[0]
    def pixels():
        import re
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=d['memory']['cache_tiles']
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;used=set();objects=[]
        for i in range(7):
            b=read(syms['objectiveVisuals'][0]+i*12,12);xx,yy=struct.unpack('>hh',b[:4]);frame=b[7]
            if b[9] and b[10]:objects.append(((xx-24)//8,(yy-40)//8,frame))
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*96+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<d['memory']['cache_tiles']
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',col,row)
                expected=None
                for ox,oy,frame in objects:
                    if ox<=col<ox+6 and oy<=row<oy+6:
                        offset=(frame*36+(col-ox)*6+row-oy)*32;tile=nest_raw[offset:offset+32]
                        if any(tile):expected=tile
                overlay=vw(u16('bga_addr')+at)
                if expected:assert overlay&0xe000==0x2000 and vr((overlay&2047)*32,32)==expected,('nest pixels',col,row)
                else:assert overlay==0,('foreign BG_A fragment',col,row,overlay)
                used.add(slot)
        base=int.from_bytes(read(syms['objectiveArtBases'][0],2),'big');assert base==785+d['memory']['cache_tiles']
        header=(GAME/'src/system/video/campaign_ground_art.h').read_text();body=re.search(r'campaignNestTiles\[\]=\{(.*?)\};',header,re.S)[1]
        bank=b''.join(struct.pack('>I',int(v,16)) for v in re.findall(r'0x([0-9A-Fa-f]+)UL',body));assert vr(base*32,len(bank))==bank
        return dict(camera=[cx,cy],visible_patterns=len(used),peak=u16('sceneStreamPeak'),nests=len(objects))
    def navigation(tx,ty):
        dynamic=[]
        nav={**d,'solids':d['solids']+dynamic}
        sx,sy=u16('px'),u16('py');start=(round(sx/8)*8,round(sy/8)*8)
        corners=path(nav,start,(tx,ty),4)
        for x,y in corners:
            for _ in range(fps*20):
                dx,dy=x-u16('px'),y-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:break
                buttons.clear()
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
        write(syms['pendingLevel'][0],bytes([12]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==12 and not u8('transitioning'),'phase10-entry',fps*20)
        initial=snapshot();quiet();wait_camera();shot('01-entry');check('entry-native-pixels',pixels());assert cr(36)==1
        assert (u16('arenaMinY'),u16('arenaMaxY'))==(128,479)
        views=[]
        for x in [64,224,392,552,704,552,392,224,64]:
            for y in [160,272,368,464]:
                xx,yy=closest(d,x,y);pos(xx,yy);wait_camera();views.append(pixels());sprite_limits()
            shot('camera-'+str(x))
        check('full-map-scroll',dict(samples=len(views),zero_pixel_mismatches=True))
        collisions=[]
        for x,y,button,axis,limit,sign in faces(d):
            pos(x,y);hold({button},fps//2);v=u16(axis)
            assert v<=limit if sign>0 else v>=limit,('prop face',x,y,button,v,limit)
            collisions.append([x,y,button,v])
        for x,y,button,axis,limit in edges(d):
            pos(x,y);hold({button},fps//2);assert u16(axis)==limit
        check('six-prop-collisions-and-bounds',dict(probes=collisions,edges=4))
        restore(initial);quiet();w16('kills',999);run(2);assert state()==1 and cr(35)==0
        check('ordinary-kill-counter-ignored')
        restore(initial);quiet();before_writes=writes;ordinary=True;destroyed=[]
        for i,(x,y) in enumerate(d['eggs']):
            ax,ay=d['egg_approaches'][i][0];navigation(ax,ay);hold({7 if ax<x else 6},1)
            for t in range(fps*12):
                buttons.clear();buttons.add(1);run()
                if int.from_bytes(read(syms['campaignFactory'][0],2),'big')&(1<<i):break
            else:raise AssertionError(('nest not killed by fire',i,u16('px'),u16('py')))
            buttons.clear();run(fps);destroyed.append(i+1)
            if state()==1:wait_camera();pixels()
            shot('nest-'+str(i+1)+'-destroyed')
            if i==4:
                mask=int.from_bytes(read(syms['campaignFactory'][0],2),'big');navigation(56,160);wait_camera();pixels()
                assert int.from_bytes(read(syms['campaignFactory'][0],2),'big')==mask
                assert all(v==255 or v>=5 for v in read(syms['campaignFactory'][0]+28,7))
        until(lambda:state()==4,'all-nests-destroyed');ordinary=False;assert writes==before_writes and cr(35)==10
        check('ten-controller-nest-destructions',dict(destroyed=destroyed,ram_writes_during_run=0,reinforcements_isolated=True,scroll_persistence=True,won=True))
        restore(initial);quiet();wait_camera();w16('bombs',1);cx,cy=u16('cameraX'),u16('cameraY')
        expected=sum(1<<i for i,(x,y) in enumerate(d['eggs']) if cx<=x<cx+320 and cy+24<=y<cy+224)
        ordinary=True;ui(0);run(fps);ordinary=False;mask=int.from_bytes(read(syms['campaignFactory'][0],2),'big');assert mask==expected
        check('bomb-affects-only-visible-nests',dict(mask=mask,expected=expected))
        pos(392,464);wait_camera();ui(3);until(lambda:state()==2,'pause');assert not u32('location');shot('02-pause')
        ui(0);until(lambda:state()==1,'resume');wait_camera();assert int.from_bytes(read(syms['campaignFactory'][0],2),'big')==mask;check('pause-restores-pixels-and-progress',pixels())
        loads=[]
        for label,x,y in [('north',352,168),('machines',416,272),('south',392,456)]:
            restore(initial);quiet();pos(x,y);wait_camera()
            for i,kind in enumerate([5,4,2,5]):
                ex,ey=closest(d,x-80+i*48,y+32);seed(i,kind,ex,ey,200,0)
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+64:direction=6
                if u16('px')<=x-64:direction=7
                buttons.clear();buttons.add(direction);w16('hp',30000)
                for i in range(4):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(6):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*40)<<6,(u16('cameraY')+168+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(at,b)
            for _ in range(fps*3):arrange();run()
            start=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==4
                assert u16('sceneStreamFaults')==0
                cpu.append(u16('cpuFrameLoad')*100/2048)
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();sim,physical=frames()-start,u32('vtimer')-vb;wait_camera();pixels();shot('load-'+label)
            loads.append(dict(section=label,enemies=4,shots_per_pool=6,seconds=20,game_fps=round(fps*sim/physical,3),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,setup='real enemy AI; health protected; inactive shots replenished; nests remain active targets'))
        check('maximum-configured-load',loads)
        restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;ticks=0
        while state()==1 and ticks<fps*30:
            buttons.clear();buttons.update({1,[7,5,6,4][(ticks//(fps*2))%4]});run();ticks+=1;peak=max(peak,living())
        ordinary=False;buttons.clear();shot('natural-combat');check('natural-combat',dict(seconds=round(ticks/fps,2),state=state(),hp=u16('hp'),peak_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_grants=False,human_difficulty_certified=False))
        report['passed']=True;save();print('PASS phase10 factory',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase10');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase10_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
