"""Phase8 urban: exact shared scenery, controller kills, collision and6-enemy load."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''

    from campaign_geometry import faces,edges,closest,path
    root=GAME/'art/phase08-urban-v1';d=json.loads((root/'manifest.json').read_text());native=GAME/'art/phase07-urban-v2'
    patterns=(native/'native/tiles.bin').read_bytes();ids=struct.unpack('>6528H',(native/'native/map.bin').read_bytes())
    report['scope']='Urban phase8: asphalt, open sewer manhole and four white canvas stalls. Controller entry, three priority kills and movement; RAM isolates enemy pressure for functional checks. Exact visible VRAM and overlay pixels, cache, pause, collision. Native max6-enemy/6+6-projectile load retains AI/active trajectories. Natural combat sample has no RAM health or AI grants.'
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
        zeros('pshots');zeros('eshots');w16('hp',30000);w16('spawnTimer',60000)
        write(syms['campaignResistance'][0]+2,struct.pack('>H',60000))
        for i in range(3,16):write(syms['enemies'][0]+i*46+44,b'\0')
        for i in range(3):write(syms['enemies'][0]+i*46+16,struct.pack('>H',60000))
    def cr(offset):return read(syms['campaignResistance'][0]+offset,1)[0]
    def pixels():
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=560
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;used=set()
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*96+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<560
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',col,row)
                assert vw(u16('bga_addr')+at)==0,('foreign BG_A fragment',col,row)
                used.add(slot)
        return dict(camera=[cx,cy],visible_patterns=len(used),peak=u16('sceneStreamPeak'))
    def strips():
        import re
        h=(GAME/'src/system/video/phase08_transmitter.h').read_text()
        words=re.findall(r'0x([0-9A-Fa-f]+)UL',h);bank=b''.join(struct.pack('>I',int(v,16)) for v in words)
        indices=[int(v) for v in re.search(r'phase08TransmitterStrips\[\]=\{(.*?)\}',h)[1].split(',')]
        original=(GAME/'res/objectives/animations.bin').read_bytes()[3264*4:3264*4+3072]
        assert b''.join(bank[i*64:i*64+64] for i in indices)==original
        base=int.from_bytes(read(syms['objectiveArtBases'][0]+6,2),'big');assert base==785+560
        assert vr(base*32,len(bank))==bank
        sat=set();index=0
        for _ in range(80):
            at=u16('slist_addr')+index*8;link=vw(at+2)
            sat.add(((vw(at+6)&511)-128,(vw(at)&1023)-128,(link>>8)&15,vw(at+4)&2047))
            index=link&127
            if not index:break
        tested=0;cx,cy=u16('cameraX'),u16('cameraY')
        for i in range(3):
            x,y,age,art,frame,mode,visible,ground,primed=struct.unpack('>hhH6B',read(syms['objectiveVisuals'][0]+i*12,12))
            if not visible or x+16<=cx or x-16>=cx+320 or y+8<=cy+24 or y-24>=cy+224:continue
            # The CPU may have advanced animation RAM since the latest
            # VBlank SAT upload. Accept one complete current/previous pose,
            # never a mix of strips from different animation frames.
            sequence=(0,2,1,3)
            candidates=[frame,sequence[(sequence.index(frame)-1)%4]] if mode==0 and frame in sequence else [frame]
            matches=[]
            for pose in candidates:
                expected=[]
                for n in range(8):
                    strip=indices[pose*8+n];xx=x-16+(n//2)*8-cx;yy=y-24+(n%2)*16-cy
                    if not any(bank[strip*64:strip*64+64]) or xx>=320 or xx+8<=0 or yy>=224 or yy+16<=0:continue
                    expected.append((xx,yy,1,base+strip*2))
                if all(v in sat for v in expected):matches.append(len(expected))
            assert matches,('missing/mixed transmitter pose',i,frame,sorted(sat))
            tested+=max(matches)
        return dict(all_six_frames_exact=True,resident_tiles=len(bank)//32,total_reserved=636,sprite_strips_verified=tested)
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
                if cr(18)==5:buttons.clear();return
                assert state()==1 or cr(18)==5,('left transport',state(),u16('hp'))
            else:raise AssertionError(('navigation stalled',x,y,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps);ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)
        write(syms['pendingLevel'][0],bytes([10]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==10 and not u8('transitioning'),'phase8-entry',fps*20)
        initial=snapshot();quiet();wait_camera();shot('01-entry');check('entry-native-pixels',pixels());check('transmitter-strips',strips())
        assert (u16('arenaMinY'),u16('arenaMaxY'))==(176,479)
        for i,(x,y) in enumerate(d['targets']):
            assert struct.unpack('>hh',read(syms['enemies'][0]+i*46,4))==(x,y)
        views=[]
        for x in [64,224,392,552,704,552,392,224,64]:
            for y in [192,272,368,464]:
                xx,yy=closest(d,x,y);pos(xx,yy);wait_camera();views.append(pixels());strips();sprite_limits()
            shot('camera-'+str(x))
        check('full-map-scroll',dict(samples=len(views),zero_pixel_mismatches=True))
        for i,(x,y) in enumerate(d['targets']):
            pos(x-40,y);wait_camera();shot('target-'+str(i+1));pixels();sprite_limits()
        collisions=[]
        for x,y,button,axis,limit,sign in faces(d):
            pos(x,y);hold({button},fps//2);v=u16(axis)
            assert v<=limit if sign>0 else v>=limit,('prop face',x,y,button,v,limit)
            collisions.append([x,y,button,v])
        for x,y,button,axis,limit in edges(d):
            pos(x,y);hold({button},fps//2);assert u16(axis)==limit
        check('four-stall-collisions-and-bounds',dict(probes=collisions,edges=4))
        pos(392,464);wait_camera();shot('02-lower-boundary');ui(3);until(lambda:state()==2,'pause');assert not u32('location')
        ui(0);until(lambda:state()==1,'resume');wait_camera();check('pause-restores-native-pixels',pixels());strips()
        # Isolate reinforcements and return fire before the controller-only
        # run. Target HP, projectile hits, death and mission progress stay real.
        restore(initial);quiet();before_writes=writes;ordinary=True;deaths=[]
        for i,(x,y) in enumerate(d['targets']):
            navigation(x-48,y)
            hold({7},1)
            for t in range(fps*12):
                buttons.clear();buttons.add(1);run()
                if cr(20)&(1<<i):break
            else:raise AssertionError(('target not killed by fire',i,u16('px'),u16('py')))
            buttons.clear();deaths.append(i+1);shot('destroyed-'+str(i+1))
        until(lambda:state()==4,'priority-win');ordinary=False;assert cr(20)==7 and writes==before_writes
        check('three-controller-priority-kills',dict(killed=deaths,mask=cr(20),won=True,ram_writes_during_run=0,reinforcement_and_return_fire_isolated=True))
        restore(initial);quiet();w16('kills',999);run(2);assert state()==1 and cr(20)==0
        check('ordinary-kill-counter-ignored')
        loads=[]
        for label,x,y in [('upper',352,192),('market',392,304),('lower',512,440)]:
            restore(initial);quiet();pos(x,y);wait_camera()
            for i,kind in enumerate([5,4,2]):
                ex,ey=closest(d,x-80+i*48,y+32);seed(i+3,kind,ex,ey,200,0)
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+64:direction=6
                if u16('px')<=x-64:direction=7
                buttons.clear();buttons.add(direction);w16('hp',30000)
                for i in range(6):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(6):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*40)<<6,(u16('cameraY')+168+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(at,b)
            for _ in range(fps*3):arrange();run()
            start=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==6
                assert u16('sceneStreamFaults')==0
                cpu.append(u16('cpuFrameLoad')*100/2048)
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();sim,physical=frames()-start,u32('vtimer')-vb;wait_camera();pixels();strips();shot('load-'+label)
            loads.append(dict(section=label,enemies=6,shots_per_pool=6,seconds=20,game_fps=round(fps*sim/physical,3),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,setup='authored fixed3targets plus3real AI reinforcements; health protected; inactive shots replenished'))
        check('maximum-configured-load',loads)
        restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;ticks=0
        while state()==1 and ticks<fps*30:
            buttons.clear();buttons.update({1,[7,5,6,4][(ticks//(fps*2))%4]});run();ticks+=1;peak=max(peak,living())
        ordinary=False;buttons.clear();shot('natural-combat');check('natural-combat',dict(seconds=round(ticks/fps,2),state=state(),hp=u16('hp'),peak_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_grants=False,human_difficulty_certified=False))
        report['passed']=True;save();print('PASS phase8 urban',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase08');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase08_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
