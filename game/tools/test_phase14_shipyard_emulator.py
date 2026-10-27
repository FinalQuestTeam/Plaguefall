"""Phase14: exact streamed art, modular boundaries and controller generator work."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import closest,path,faces,edges,validate
    from campaign_objective_probe import inspect_objectives
    root=GAME/'art/phase14-shipyard-v2';d=json.loads((root/'manifest.json').read_text())
    cols,rows=[n//8 for n in d['size']]
    patterns=(root/'native/tiles.bin').read_bytes()
    ids=struct.unpack('>'+str(cols*rows)+'H',(root/'native/map.bin').read_bytes())
    palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
    generator_tiles=(root/'native/generator-tiles.bin').read_bytes()
    generator_map=struct.unpack('>216H',(root/'native/generator-map.bin').read_bytes())
    cap=d['memory']['cache_tiles'];launch=syms['campaignLaunch'][0]
    activation_seconds=d['activation']['seconds'];required_work=fps*activation_seconds
    def mask():return read(launch+14,1)[0]
    def work(i):return int.from_bytes(read(launch+i*2,2),'big')
    def decay(i):return int.from_bytes(read(launch+16+i*2,2),'big')
    def seed_work(i,value,timer=0):
        write(launch+i*2,struct.pack('>H',value));write(launch+16+i*2,struct.pack('>H',timer))
    def progress_bar(i):
        base=785+636-i*4;index=0;found=None
        for _ in range(80):
            at=u16('slist_addr')+index*8;link=vw(at+2);attr=vw(at+4)
            if attr&2047==base:
                found=dict(x=(vw(at+6)&511)-128+u16('cameraX'),y=(vw(at)&1023)-128+u16('cameraY'),size=(link>>8)&15,base=base)
                assert attr&0x6000==0x2000,'bar must use PAL1'
                break
            index=link&127
            if not index:break
        assert found,('station progress bar absent',i,work(i),u16('cameraX'),u16('cameraY'))
        x,y=d['machines'][i];assert [found['x'],found['y'],found['size']]==[x-16,y-48,12]
        value=(work(i)*20//required_work)*5;fill=value*30//100;words=[0]*32
        for x in range(32):
            for y in range(1,6):
                color=1 if y in (1,5) or x in (0,31) else 4 if x<=fill else 11
                words[x//8*8+y]|=color<<((7-x%8)*4)
        expected=struct.pack('>32I',*words)
        assert vr(base*32,128)==expected,('bar fill differs from station work',i,work(i))
        return dict(found,work_frames=work(i),percent=value,pattern_sha=hashlib.sha256(expected).hexdigest())
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*20):
            run();now=(u16('cameraX'),u16('cameraY'));stable=stable+1 if now==previous else 0;previous=now
            if stable>=12:run(2);return
        raise AssertionError('camera never settles')
    def pixels():
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=cap,'cache fault'
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[48:64]==list(map(packed,palette))
        loc=u32('location')&65535;cx,cy=u16('cameraX'),u16('cameraY');used=set();cells=0
        objects=[]
        for i in range(7):
            b=read(syms['objectiveVisuals'][0]+i*12,12);x,y=struct.unpack('>hh',b[:4])
            if b[9] and b[10]:objects.append(((x-24)//8,(y-40)//8,b[7]))
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*cols+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<cap
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('map mismatch',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('native pixel mismatch',col,row)
                expected=None
                for x,y,frame in objects:
                    if x<=col<x+6 and y<=row<y+6:
                        tile=generator_map[frame*36+(col-x)*6+row-y]
                        ink=generator_tiles[tile*32:(tile+1)*32]
                        if any(ink):expected=ink
                overlay=vw(u16('bga_addr')+at)
                if expected:
                    assert overlay&0xe000==0x6000,('generator palette mismatch',col,row)
                    assert vr((overlay&2047)*32,32)==expected,('native generator pixels differ',col,row)
                else:assert overlay==0,('foreign foreground fragment',col,row)
                used.add(slot);cells+=1
        base=int.from_bytes(read(syms['objectiveArtBases'][0]+2,2),'big');assert base==785+cap
        assert vr(base*32,len(generator_tiles))==generator_tiles,'generator atlas not resident'
        return dict(camera=[cx,cy],cells=cells,visible_patterns=len(used),cache_peak=u16('sceneStreamPeak'),cache_faults=u16('sceneStreamFaults'))
    def navigate(tx,ty):
        sx,sy=u16('px'),u16('py');start=(round(sx/8)*8,round(sy/8)*8)
        for x,y in path(d,start,(tx,ty),4):
            for _ in range(fps*15):
                dx,dy=x-u16('px'),y-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:break
                buttons.clear()
                if abs(dx)>2:buttons.add(7 if dx>0 else 6)
                if abs(dy)>2:buttons.add(5 if dy>0 else 4)
                run()
                if state()==4:buttons.clear();return
                assert state()==1,('left phase',state())
            else:raise AssertionError(('controller stuck',x,y,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');baseline=snapshot()
        write(syms['pendingLevel'][0],bytes([17]));press(1)
        until(lambda:state()==1 and u8('currentLevel')==17 and not u8('transitioning'),'phase14-entry')
        isolate();w16('hp',100);buttons.add(1);wait_camera();initial=snapshot()
        shot('14-entry');check('native-entry',pixels());check('connected-floor-and-seams',dict(geometry=validate(d),seams=d['seams'],energy=d['energy']))
        views=[]
        for x in [48,160,280,448]:
            for y in [128,192,256,320,384,448,496]:
                pos(*closest(d,x,y));wait_camera();views.append(pixels());sprite_limits();shot(f'14-view-{x}-{y}')
        check('28-real-camera-views',views)
        restore(initial);isolate();buttons.add(1);pos(384,336);wait_camera();poses=[]
        for frame in range(6):
            for i in range(5):
                address=syms['objectiveVisuals'][0]+i*12
                write(address+7,bytes([frame,6]))
            # An unused, nonresident cargo animation requests a real redraw.
            # It emits no sprite; the six generator poses stay fixed for DMA.
            dummy=bytearray(12);dummy[6]=2;dummy[7]=255;dummy[9]=1
            write(syms['objectiveVisuals'][0]+6*12,dummy)
            run(3);poses.append(pixels());shot('14-generator-pose-'+str(frame))
        check('six-native48px-generator-poses',dict(size=d['generator']['size'],frames=6,pixel_exact=True,probes=poses))
        restore(initial);isolate();buttons.add(1);wait_camera();contacts=[]
        for x,y,key,axis,limit,direction in faces(d):
            restore(initial);isolate();pos(x,y);buttons.add(1);wait_camera();hold({key,1},fps)
            assert u16(axis)==limit,('prop collision',x,y,key,axis,u16(axis),limit)
            contacts.append(dict(face=[x,y,key],axis=axis,stopped=u16(axis)))
        for x,y,key,axis,limit in edges(d):
            restore(initial);isolate();pos(x,y);buttons.add(1);wait_camera();hold({key,1},fps)
            assert u16(axis)==limit,('boundary collision',key,axis,u16(axis),limit)
            contacts.append(dict(boundary=key,axis=axis,stopped=u16(axis)))
        check('prop-faces-and-four-boundaries',contacts)
        restore(initial);isolate();buttons.add(1);wait_camera();press(3);until(lambda:state()==2,'pause');shot('14-pause')
        press(0);until(lambda:state()==1,'resume');buttons.add(1);wait_camera();check('pause-restores-exact-cache',pixels())
        # Exact gameplay-time boundaries, isolated from enemy pressure. The
        # five-station objective below remains controller-only after setup.
        restore(initial);isolate();buttons.add(1);pos(56,192);wait_camera()
        run(fps);assert work(0)==0 and mask()==0;check('fire-blocks-activation-empty-bar',progress_bar(0))
        buttons.clear();until(lambda:work(0)==required_work-1,'activation-duration-minus-one-update',fps*(activation_seconds+2))
        assert mask()==0,'station powered before required duration'
        buttons.add(1);run(3);almost=progress_bar(0);shot('14-progress-almost-full')
        buttons.clear();until(lambda:mask()&1,'activation-duration-threshold',fps)
        assert work(0)==required_work;check('exact-activation-duration',dict(required_updates=required_work,before_last_update=almost,completed_work=work(0)))
        buttons.add(1);pos(120,192);run(fps*6)
        assert mask()&1 and work(0)==required_work;check('completed-station-never-decays',True)
        restore(initial);isolate();buttons.add(1);pos(120,192);wait_camera();seed_work(0,fps*2+fps//2)
        until(lambda:decay(0)==fps-1,'decay-one-update-before-second',fps*2)
        assert work(0)==fps*2+fps//2;before=work(0)
        until(lambda:work(0)<before,'first-second-decay',fps)
        assert work(0)==before-fps and decay(0)==0
        run(2);reduced=progress_bar(0);shot('14-progress-decay')
        # Pause freezes both stored work and the incomplete one-second clock.
        press(3);until(lambda:state()==2,'progress-pause');paused=(work(0),decay(0));run(fps*2)
        assert (work(0),decay(0))==paused
        press(0);until(lambda:state()==1,'progress-resume');buttons.add(1)
        check('away-progress-and-timer-freeze-during-pause',dict(paused_work=paused[0],paused_decay_clock=paused[1]))
        until(lambda:work(0)==fps//2,'second-second-decay',fps*2)
        until(lambda:work(0)==0,'decay-clamps-to-zero',fps*2)
        run(fps*2);assert work(0)==0 and mask()==0
        check('decay-every-full-second-with-zero-clamp',dict(interval_updates=fps,removed_work_updates=fps,first_reduction=reduced,final_work=0))
        restore(initial);isolate();buttons.add(1);pos(56,192);wait_camera();seed_work(0,fps*2)
        buttons.clear();until(lambda:work(0)>=fps*3,'resume-partial-work',fps*2)
        buttons.add(1);run(3);shot('14-progress-working');check('return-resumes-stored-progress',progress_bar(0))
        # Two simultaneous partial stations use distinct pattern banks and
        # individual retreat timers, rather than sharing the last drawn fill.
        restore(initial);isolate();buttons.add(1);pos(384,344);wait_camera()
        seed_work(2,fps*2);seed_work(3,fps*4,fps//2);run(3)
        bars=[progress_bar(i) for i in [2,3]]
        assert bars[0]['pattern_sha']!=bars[1]['pattern_sha'];shot('14-progress-independent-bars')
        until(lambda:work(3)==fps*3,'independent-decay-clock',fps)
        assert work(2)==fps*2
        check('independent-station-bars-and-decay-clocks',bars)
        restore(initial);isolate();buttons.clear();before=writes;ordinary=True;activated=[]
        for i,(x,y) in enumerate(d['machines']):
            navigate(x-8,y+24)
            for _ in range(fps*(activation_seconds+1)):
                run()
                if mask()&(1<<i):break
            assert mask()&(1<<i),('generator did not activate',i,mask(),u16('px'),u16('py'))
            activated.append(dict(generator=i+1,mask=mask(),position=[u16('px'),u16('py')]))
            if state()==1:wait_camera();pixels();shot('14-generator-'+str(i+1))
        until(lambda:state()==4,'five-generators-win');ordinary=False
        assert writes==before and mask()==31
        run(fps*3)
        assert u8('resultActive') and u32('card')!=0,('result card allocation failed',u16('resultCaptureFault'),u16('resultCaptureTileCount'))
        shot('14-complete');check('all-five-generators-by-controller-and-result',dict(activated=activated,ram_writes_during_objective=0,result_card=True))
        run(fps);press(1);until(lambda:state()==5 and u8('pendingLevel')==18 and not u8('transitioning'),'continue15');shot('14-continue15')
        check('continue-to15',True)
        # Keep controls moving at configured cap; seed health and inactive shots
        # solely for repeatable load, never to claim natural difficulty.
        restore(initial);isolate();w16('hp',30000);w16('shieldTimer',60000)
        for i,kind in enumerate([4,5,2,4]):seed(i,kind,64+i*96,192,200,0)
        start=frames();vb=u32('vtimer');maximum=[0,0,0]
        for tick in range(fps*20):
            buttons.clear();buttons.update({1,[7,5,6,4][(tick//(fps*2))%4]});w16('hp',30000)
            for i in range(4):write(syms['enemies'][0]+i*46+31,b'\xc8')
            for pool in ['pshots','eshots']:
                for i in range(4):
                    address=syms[pool][0]+i*20
                    if read(address+18,1)[0]:continue
                    b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+32+i*64)<<6,(u16('cameraY')+168+i%2*8)<<6,24,0);b[17]=b[18]=1;write(address,b)
            run();assert state()==1 and not u16('sceneStreamFaults')
            if tick%30==0:maximum=[max(a,b) for a,b in zip(maximum,sprite_limits())]
        buttons.clear();measured=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3);wait_camera();pixels();shot('14-moving-load')
        check('moving-four-enemy-four-plus-four-shot-load',dict(seconds=20,game_fps=measured,cache_peak=u16('sceneStreamPeak'),cache_faults=u16('sceneStreamFaults'),sprite_limits=maximum))
        restore(initial);isolate();w16('hp',0);buttons.clear();run(fps*4);assert state()==3
        assert u8('resultActive') and u32('card')!=0;shot('14-defeat');check('defeat-card',True)
        # All shipyard stages use the expanded room and native equipment.
        for label,node,kind in [('15',18,'normal'),('16',19,'fire')]:
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and u8('currentLevel')==node and not u8('transitioning'),'regression-'+label)
            isolate();run(fps);shot(label+'-regression-entry')
            if label in ('15','16'):
                current=json.loads((GAME/f'art/phase{label}-shipyard-v2/manifest.json').read_text())
                assert u16('arenaMaxY')==current['bounds'][3]
                for i,xy in enumerate(current['machines']):assert list(struct.unpack('>hh',read(syms['objectiveVisuals'][0]+i*12,4)))==xy
                assert list(struct.unpack('>hh',read(syms['objectiveVisuals'][0]+5*12,4)))==current['radio']
                base=int.from_bytes(read(syms['objectiveArtBases'][0]+2,2),'big')
                assert vr(base*32,len(generator_tiles))==generator_tiles
                check(label+'-shares-native-generators-and-antenna-anchors',True)
                continue
        report['scope']='Phase14:28 real camera audits, six native48px poses, exact cache/overlay, collisions, ten-second activation threshold, per-station bars, one-second-away decay/zero clamp, resume/pause/completed persistence; all5 generators by controller, results, transition15, artificial load;15/16 regression.'
        report['passed']=True;save();print('PASS phase14 shipyard',report['region'],report['romSHA256'])
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL-phase14');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'phase14_shipyard','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':
    sys.path.insert(0,str(BOOT.parent));main()
