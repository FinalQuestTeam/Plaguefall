"""Phase11: shared factory art, six valves, visible work bar and five-enemy pressure."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''



    from campaign_geometry import faces,edges,closest,path
    root=GAME/'art/phase11-factory-v2';d=json.loads((root/'manifest.json').read_text());native=GAME/'art/phase10-factory-v2'
    patterns=(native/'native/tiles.bin').read_bytes();ids=struct.unpack('>6528H',(native/'native/map.bin').read_bytes())
    valve_raw=(GAME/'res/objectives/animations.bin').read_bytes()[4032*4:4032*4+3072]
    report['scope']='Factory phase11: industrial interior, six prop groups and six dispersed valve stations. Controller entry, six sustained valve interactions and movement; RAM isolates enemy pressure for functional checks. Exact visible VRAM and overlay pixels, cache, pause, collision. Native max5-enemy/6+6-projectile load retains AI/active trajectories. Natural combat sample has no RAM health or AI grants.'
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
        palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[48:64]==list(map(packed,palette)),'phase11 blue palette mismatch'
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=d['memory']['cache_tiles']
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;used=set();objects=[]
        for i in range(7):
            b=read(syms['objectiveVisuals'][0]+i*12,12);xx,yy=struct.unpack('>hh',b[:4]);frame=b[7]
            if b[9] and b[10]:objects.append(((xx-16)//8,(yy-24)//8,frame))
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*96+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<d['memory']['cache_tiles']
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',col,row)
                expected=None
                for ox,oy,frame in objects:
                    if ox<=col<ox+4 and oy<=row<oy+4:
                        offset=(frame*16+(col-ox)*4+row-oy)*32;tile=valve_raw[offset:offset+32]
                        if any(tile):expected=tile
                overlay=vw(u16('bga_addr')+at)
                if expected:assert overlay&0xe000==0x2000 and vr((overlay&2047)*32,32)==expected,('valve pixels',col,row)
                else:assert overlay==0,('foreign BG_A fragment',col,row,overlay)
                used.add(slot)
        base=int.from_bytes(read(syms['objectiveArtBases'][0]+8,2),'big');assert base==785+d['memory']['cache_tiles']
        header=(GAME/'src/system/video/campaign_ground_art.h').read_text();body=re.search(r'campaignValveTiles\[\]=\{(.*?)\};',header,re.S)[1]
        bank=b''.join(struct.pack('>I',int(v,16)) for v in re.findall(r'0x([0-9A-Fa-f]+)UL',body));assert vr(base*32,len(bank))==bank
        return dict(camera=[cx,cy],visible_patterns=len(used),peak=u16('sceneStreamPeak'),valves=len(objects))
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
    def hud_value():return read(syms['objectiveValue'][0],20).split(b'\0',1)[0].decode('ascii')
    def opened():return int.from_bytes(read(syms['campaignFactory'][0]+2,2),'big')
    def work(i):return int.from_bytes(read(syms['campaignFactory'][0]+4+i*2,2),'big')
    def bar():
        index=0;found=[]
        for _ in range(80):
            at=u16('slist_addr')+index*8;link=vw(at+2);tile=vw(at+4)&2047
            if tile==785+636:found.append(dict(x=(vw(at+6)&511)-128,y=(vw(at)&1023)-128,size=(link>>8)&15))
            index=link&127
            if not index:break
        assert found,('missing work bar',u16('px'),u16('py'))
        assert all(v['size']==12 for v in found)
        return dict(sprites=found,pattern_sha=hashlib.sha256(vr((785+636)*32,128)).hexdigest())
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps);ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)
        write(syms['pendingLevel'][0],bytes([13]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==13 and not u8('transitioning'),'phase11-entry',fps*20)
        initial=snapshot();quiet();wait_camera();shot('01-entry');check('entry-native-pixels',pixels());assert cr(36)==1
        assert (u16('arenaMinY'),u16('arenaMaxY'))==(128,479)
        assert hud_value()=='0/6',hud_value()
        # Keep fire held for isolated rendering probes to prevent valve work.
        views=[];buttons.add(1)
        for x in [64,224,392,552,704,552,392,224,64]:
            for y in [160,272,368,464]:
                xx,yy=closest(d,x,y);pos(xx,yy);wait_camera();views.append(pixels());sprite_limits()
            shot('camera-'+str(x))
        buttons.clear();check('full-map-scroll',dict(samples=len(views),zero_pixel_mismatches=True))
        collisions=[]
        for x,y,button,axis,limit,sign in faces(d):
            pos(x,y);hold({button,1},fps//2);v=u16(axis)
            assert v<=limit if sign>0 else v>=limit,('prop face',x,y,button,v,limit)
            collisions.append([x,y,button,v])
        for x,y,button,axis,limit in edges(d):
            pos(x,y);hold({button,1},fps//2);assert u16(axis)==limit
        check('six-prop-collisions-and-bounds',dict(probes=collisions,edges=4))
        restore(initial);quiet();before_writes=writes;ordinary=True
        navigation(*d['valve_approaches'][0]);before=work(0);buttons.add(1);run(fps);assert work(0)==before and opened()==0
        buttons.clear();run(fps//2);assert 0<work(0)<(fps*5+1)//2;first_bar=bar();shot('02-working-bar')
        navigation(56,160);saved_work=work(0);run(fps);assert work(0)==saved_work and opened()==0
        ui(3);until(lambda:state()==2,'pause');assert not u32('location');shot('03-pause')
        ui(0);until(lambda:state()==1,'resume');wait_camera();assert work(0)==saved_work;pixels()
        check('fire-blocks-work-and-partial-work-survives-retreat-pause',dict(saved_frames=saved_work,bar=first_bar,ram_writes_during_controls=writes-before_writes))
        navigation(*d['valve_approaches'][0]);run(fps//4);second_bar=bar();assert first_bar['pattern_sha']!=second_bar['pattern_sha'],'bar does not advance'
        until(lambda:opened()&1,'first-valve-open',fps*5);run(fps);assert cr(35)==1 and hud_value()=='1/6';pixels();shot('opened-1')
        for i in range(1,6):
            navigation(*d['valve_approaches'][i]);until(lambda i=i:opened()&(1<<i),'valve-'+str(i+1),fps*5)
            if i<5:run(fps);wait_camera();pixels();shot('opened-'+str(i+1))
        until(lambda:state()==4,'all-six-valves-open');ordinary=False;shot('04-completed')
        assert writes==before_writes and opened()==63 and cr(35)==6
        check('six-controller-valve-operations',dict(mask=opened(),done=cr(35),ram_writes_during_run=0,combat_isolated=True,won=True))
        restore(initial);quiet();pos(*d['valve_approaches'][5]);before_writes=writes;ordinary=True;until(lambda:opened()&32,'sixth-valve-first',fps*5);ordinary=False
        assert opened()==32 and cr(35)==1 and writes==before_writes
        check('sixth-valve-works-first',dict(mask=opened(),done=cr(35),ram_writes_during_run=0))
        # Production spawn cadence, no shooting: verify the larger pool fills.
        restore(initial);start=frames();vb=u32('vtimer');peak=0
        for tick in range(fps*20):
            if tick%fps==0:w16('hp',30000)
            run();peak=max(peak,living());assert living()<=5
        assert peak==5,('new enemy cap not reached',peak)
        check('production-spawning-reaches-five',dict(peak=peak,seconds=20,health_reseeded=True,spawn_logic_unmodified=True))
        loads=[]
        for label,x,y in [('north',352,168),('machines',416,272),('south',392,456)]:
            restore(initial);quiet();pos(x,y);wait_camera()
            for i,kind in enumerate([4,9,10,4,9]):
                ex,ey=closest(d,x-96+i*48,y+32);seed(i,kind,ex,ey,200,0)
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+64:direction=6
                if u16('px')<=x-64:direction=7
                buttons.clear();buttons.add(direction);w16('hp',30000)
                for i in range(5):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(6):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*40)<<6,(u16('cameraY')+168+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(at,b)
            for _ in range(fps*3):arrange();run()
            start=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==5
                assert u16('sceneStreamFaults')==0
                cpu.append(u16('cpuFrameLoad')*100/2048)
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();sim,physical=frames()-start,u32('vtimer')-vb;wait_camera();pixels();shot('load-'+label)
            loads.append(dict(section=label,enemies=5,roster=[4,9,10,4,9],shots_per_pool=6,seconds=20,game_fps=round(fps*sim/physical,3),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,setup='authored roster with live AI; health protected; inactive shots replenished; valves remain functional'))
        check('maximum-configured-load',loads)
        restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;ticks=0
        while state()==1 and ticks<fps*30:
            buttons.clear();buttons.update({1,[7,5,6,4][(ticks//(fps*2))%4]});run();ticks+=1;peak=max(peak,living())
        ordinary=False;buttons.clear();shot('natural-combat');check('natural-combat',dict(seconds=round(ticks/fps,2),state=state(),hp=u16('hp'),peak_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_grants=False,human_difficulty_certified=False))
        report['passed']=True;save();print('PASS phase11 factory',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase11');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase11_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
