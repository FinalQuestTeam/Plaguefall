"""Measure moving-camera framing in production ROM, stages 1–13 + A/B.

Shares the libretro boot/setup helpers with the existing escort probes. RAM
sets the stage, speed, protection and starting point BEFORE each trial. All
measured movement uses D-pad inputs with an enforced RAM-write guard. This is
an audit, so framing problems are findings rather than failed infrastructure.
"""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    import csv, math
    from campaign_geometry import closest, path, free
    from collections import deque
    labels=['1','2A','2B','3','4','5','6A','6B','7','8','9','10','11','12','13A','13B']
    report.update(scope='Dynamic camera audit, selected campaign variants of stages 1–13',
        method='Genesis Plus GX production ROM. RAM only before trials: node, speed bonus, protection, enemy isolation and starting position. Every measured sample is real controller movement, guarded against RAM writes. Full 32x48 sprite uses (px-8,py-31). Visible gameplay rectangle is x=0..319,y=24..223. Boundary-constrained centering is measured separately from avoidable framing error. No gameplay code or ROM modified.',
        stages=[], findings_are_not_test_failures=True)
    def mem(addr,n):
        if addr>=0xe00000:return read(addr&65535,n)
        return bytes(data[addr:addr+n])
    def word_at(addr):return int.from_bytes(mem(addr,2),'big')
    def ptr_at(addr):return int.from_bytes(mem(addr,4),'big')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def geometry():
        address=u32('world');width,height=struct.unpack('>HH',mem(address,4))
        bounds=list(struct.unpack('>hhhh',mem(address+4,8)))
        count=mem(address+20,1)[0];solids=ptr_at(address+16)
        rects=[list(struct.unpack('>hhhh',mem(solids+i*10,8))) for i in range(count)]
        sc=u32('scene');anchor=word_at(sc+36);nfocus=mem(sc+42,1)[0];focusptr=ptr_at(sc+38)
        focus=[list(struct.unpack('>hhhh',mem(focusptr+i*10,8))) for i in range(nfocus)]
        assert 320<=width<=3072 and 224<=height<=768 and 0<=nfocus<=20,(width,height,nfocus)
        return dict(width=width,height=height,bounds=bounds,solids=rects,
            anchor=anchor,focus=focus,south_start=word_at(sc+50),streamed=bool(ptr_at(sc+44)))
    def clamp(x,a,b):return max(a,min(b,x))
    def percentile(values,p):
        v=sorted(values);return round(v[min(len(v)-1,math.floor((len(v)-1)*p))],2) if v else 0
    def visible_pixels(d):
        # Check the committed VDP scroll, which can trail the next queued RAM
        # camera by one host frame. This audits live movement without waiting
        # for a stationary camera, including entering rows/columns.
        vs=(C.c_uint16*64).in_dll(core,'vsram')
        # Genesis Plus GX exports the scroll latch; deriving horizontal scroll
        # from the configured table is reliable for whole-plane scrolling.
        regs=(C.c_ubyte*32).in_dll(core,'reg')
        hsbase=(regs[13]&63)<<10
        cx=(-vw(hsbase+2))&1023
        # H-scroll is10bit: choose the world ring nearest the logical camera.
        logical=signed('cameraX');cx+=round((logical-cx)/1024)*1024
        cy=vs[1]&1023
        if cx<0 or cy<0 or cx+320>d['width'] or cy+224>d['height']:return 0
        sc=u32('scene');tileptr=ptr_at(sc);mapaddr=ptr_at(sc+8) if u8('arenaDamaged') and ptr_at(sc+8) else ptr_at(sc+4)
        cols=word_at(sc+34) or 64;location=u32('location')&65535 if d['streamed'] else 0
        npc=ptr_at(sc+30);skip=struct.unpack('>4H',mem(npc,8)) if npc else None
        count=0
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                if skip and skip[0]<=col<skip[0]+skip[2] and skip[1]<=row<skip[1]+skip[3]:continue
                source=word_at(mapaddr+(row*cols+col)*2)
                if d['streamed']:
                    slot=int.from_bytes(read(location+source*2,2),'big')
                    assert slot<word_at(sc+16),('nonresident visible pattern',col,row,source,slot)
                    expected=0x6000+785+slot;sourceptr=tileptr+source*32
                else:
                    expected=0x6000|(source&0x1800)|(785+(source&2047));sourceptr=tileptr+(source&2047)*32
                actual=vw(u16('bgb_addr')+((row&31)*64+(col&63))*2)
                assert actual==expected,('live BG_B map',col,row,actual,expected,cx,cy,logical)
                assert vr((actual&2047)*32,32)==mem(sourceptr,32),('live BG_B pattern',col,row)
                count+=1
        return count
    def setup_speed(bonus):write(syms['speedPct'][0],bytes([bonus]))
    def protect():
        priority=read(syms['enemies'][0],46*3) if u8('currentLevel')==10 else None
        isolate();w16('hp',30000);w16('shieldTimer',60000)
        if priority is not None:
            # Transmitters are objective entities. Clearing them would win
            # stage8 before any camera samples could be taken.
            write(syms['enemies'][0],priority)
            for i in range(3):write(syms['enemies'][0]+46*i+16,struct.pack('>H',60000))
        if u8('currentLevel') in (9,10):write(syms['campaignResistance'][0]+2,struct.pack('>H',60000))
        if u16('dinorahHp'):
            w16('dinorahHp',100);w16('dinorahInvTimer',60000);w16('dinorahPauseTimer',60000)
        if 'npcHp' in syms:w16('npcHp',30000)
    def settle_camera():
        buttons.clear();same=0;previous=None
        for _ in range(fps*20):
            run();current=(signed('cameraX'),signed('cameraY'))
            same=same+1 if current==previous else 0;previous=current
            if same>=8:return
        raise AssertionError('camera did not settle')
    fields=['trial','frame','vblank','px','py','cx','cy','target_x','target_y','dx','dy','dcx','dcy','follow_npc','focus','center_x','center_y','ideal_x','ideal_y','error_x','error_y','clip','stream_blocked','load']
    def execute(label,d,trial,controller,limit,writer,folder):
        nonlocal ordinary,raw,record,encoder
        before=writes;ordinary=True;previous=None;rows=[];peak=None;best=-1;begin=frames();vb=u32('vtimer');move_ticks=0;pixel_cells=0
        deferrals=u16('sceneStreamDeferrals') if 'sceneStreamDeferrals' in syms else 0
        if args.movie:
            encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(folder/(trial+'.mp4'))],stdin=subprocess.PIPE)
            record=True
        try:
            for tick in range(limit):
                keys=controller(tick)
                if keys is None:break
                buttons.clear();buttons.update(keys);run()
                if state()!=1:break
                p=(signed('px'),signed('py'));c=(signed('cameraX'),signed('cameraY'));f=frames()
                if previous and f==previous[0]:continue
                dx,dy,dcx,dcy=(0,0,0,0) if previous is None else (p[0]-previous[1][0],p[1]-previous[1][1],c[0]-previous[2][0],c[1]-previous[2][1])
                # Body center is (px+8,py-7); gameplay center is (160,124).
                # Projection offset16 applies to shots/enemies, not emitActor.
                ideal=(clamp(p[0]-152,0,d['width']-320),clamp(p[1]-131,0,d['height']-224))
                ex,ey=ideal[0]-c[0],ideal[1]-c[1]
                move_ticks=move_ticks+1 if dx or dy else 0
                clip=p[0]-8-c[0]<0 or p[0]+24-c[0]>320 or p[1]-31-c[1]<24 or p[1]+17-c[1]>224
                follow=bool(u16('dinorahHp') and abs(p[0]-signed('dinorahX'))<200 and abs(p[1]-signed('dinorahY'))<120)
                nearest=65;which=-1
                for i,(a,b,ww,hh) in enumerate(d['focus']):
                    distance=max(a-p[0]-8,0,p[0]+8-a-ww)+max(b-p[1]-8,0,p[1]+8-b-hh)
                    if distance<nearest:nearest=distance;which=i
                tx,ty=signed('cameraTargetX'),signed('cameraTargetY')
                bounded_target=(clamp(tx,0,d['width']-320),clamp(ty,0,d['height']-224))
                blocked=bool(d['streamed'] and (abs(bounded_target[0]-c[0])>1 or abs(bounded_target[1]-c[1])>1) and dcx==0 and dcy==0 and (dx or dy))
                row=[trial,f,u32('vtimer'),*p,*c,tx,ty,dx,dy,dcx,dcy,int(follow),which,p[0]+8-c[0],p[1]-7-c[1],*ideal,ex,ey,int(clip),int(blocked),u16('cpuFrameLoad')]
                writer.writerow(row);rows.append(row)
                if args.assert_centered:
                    assert ex==0 and ey==0,('unrequested framing adjustment',label,trial,ex,ey)
                if args.assert_framing:
                    assert not clip,('player clipped',label,trial,p,c)
                    if move_ticks>=12:assert abs(ex)<=8 and abs(ey)<=8,('persistent moving drift',label,trial,ex,ey)
                    assert abs(dcx)<=8 and abs(dcy)<=8,('camera exceeds one-tile step',dcx,dcy)
                    assert u16('sceneStreamFaults')==0,('streaming fault',label,trial)
                    if tick%45==0:pixel_cells+=visible_pixels(d);sprite_limits()
                score=max(abs(ex),abs(ey))+200*clip
                if score>best:
                    best=score;peak=dict(position=p,camera=c,error=[ex,ey],sprite=[p[0]-8-c[0],p[1]-31-c[1],32,48],frame=f)
                    # Capture only improvements; keep the final worst frame.
                    peak_raw=raw
                previous=(f,p,c)
            buttons.clear()
        finally:
            ordinary=False
            if encoder:
                record=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
        assert writes==before,'RAM writes inside measured trial'
        assert len(rows)>=50,('insufficient actual gameplay',label,trial,len(rows),state())
        if peak:
            current_raw=raw;raw=peak_raw
            png(folder/(trial+'.png'),w,h,rgb());raw=current_raw
        moving=[r for r in rows if r[9] or r[10]]
        jumps=sum(1 for a,b in zip(rows,rows[1:]) if abs(b[7]-a[7])>12 or abs(b[8]-a[8])>12)
        flips=sum(a[13]!=b[13] for a,b in zip(rows,rows[1:]))
        focusflips=sum(a[14]!=b[14] for a,b in zip(rows,rows[1:]))
        result=dict(trial=trial,samples=len(rows),moving_samples=len(moving),ram_writes_during_trial=0,
            simulated_seconds=round((frames()-begin)/fps,2),physical_seconds=round((u32('vtimer')-vb)/fps,2),
            fps=round(fps*(frames()-begin)/max(1,u32('vtimer')-vb),2),
            max_error_x=max((abs(r[19]) for r in rows),default=0),max_error_y=max((abs(r[20]) for r in rows),default=0),
            moving_p95_error_x=percentile([abs(r[19]) for r in moving],.95),moving_p95_error_y=percentile([abs(r[20]) for r in moving],.95),
            clipped_samples=sum(r[21] for r in rows),target_jumps_over12=jumps,escort_switches=flips,landmark_switches=focusflips,
            possible_stream_holds=sum(r[22] for r in rows),worst=peak,end_state=state())
        result.update(live_pixel_cells=pixel_cells,stream_deferrals=(u16('sceneStreamDeferrals')-deferrals)&65535)
        return result
    def navigater(d,points,bonus):
        queue=deque();failure=[];current_goal=None;stuck=0;oldpos=None;stop=0
        # Plan from actual lattice and then use only controller corrections.
        start=closest(d,signed('px'),signed('py'))
        for target in points:
            goal=closest(d,*target,margin=4)
            if goal==start:continue
            try:corners=path(d,start,goal,4)
            except AssertionError:corners=path(d,start,goal,0)
            queue.extend(corners[1:]);start=goal
        def controller(tick):
            nonlocal current_goal,stuck,oldpos,stop
            p=(signed('px'),signed('py'))
            if current_goal is None:
                if not queue:
                    stop+=1;return set() if stop<=fps//2 else None
                current_goal=queue.popleft()
            dx,dy=current_goal[0]-p[0],current_goal[1]-p[1]
            tolerance=2 if bonus<100 else 3
            if abs(dx)<=tolerance and abs(dy)<=tolerance:
                current_goal=None;stuck=0;return set()
            stuck=stuck+1 if p==oldpos else 0;oldpos=p
            if stuck>fps*2:
                failure.append(dict(position=p,goal=current_goal));return None
            keys=set()
            if abs(dx)>tolerance:keys.add(7 if dx>0 else 6)
            if abs(dy)>tolerance:keys.add(5 if dy>0 else 4)
            step=4 if bonus==100 else 3.2 if bonus else 2
            # Tight16px passages require correcting the other axis even when
            # that coordinate is already within the waypoint tolerance.
            if dx and not free(d,p[0]+(step if dx>0 else -step),p[1]):
                keys.discard(7);keys.discard(6)
                if dy:keys.add(5 if dy>0 else 4)
            if dy and not free(d,p[0],p[1]+(step if dy>0 else -step)):
                keys.discard(5);keys.discard(4)
                if dx:keys.add(7 if dx>0 else 6)
            return keys
        return controller,failure,queue
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2);baseline=snapshot()
        wanted=[int(x) for x in args.nodes.split(',')]
        for node in wanted:
            label=labels[node-1];restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'stage-'+label);protect();run(fps//2)
            d=geometry()
            if label=='7':
                # Cargo cases have dynamic contact bases outside ArenaDef.
                # Retain those bases conservatively throughout navigation.
                import re
                full_symbols={p[3]:int(p[0],16) for line in symbols.splitlines() if len(p:=line.split())==4}
                source_address=next(a for n,a in full_symbols.items() if n.split('.lto_priv.')[0]=='PHASE07_SOURCES')
                sources=struct.unpack('>10h',mem(source_address,20))
                d['cargo_contact_bases']=[[sources[i]-16,sources[i+1],32,8] for i in range(0,10,2)]
                d['solids']+=d['cargo_contact_bases']
            if label in ('6A','6B'):
                # Isolate gate progression from this camera audit, as in the
                # dedicated full-escort suite. Closed gates get separate burst
                # coverage in that suite, not artificial traversal failures.
                write(syms['campaignRouteOps'][0]+8,bytes([0,0,3]))
                for slot in (0,1):write(syms['objectiveVisuals'][0]+slot*12+9,b'\0')
                d['gates_seeded_open_before_trials']=True
            initial=snapshot();stage=dict(phase=label,node=node,geometry=d,trials=[]);report['stages'].append(stage)
            folder=out/label;folder.mkdir(exist_ok=True)
            with (folder/'telemetry.csv').open('w') as csvfile:
                writer=csv.writer(csvfile);writer.writerow(fields)
                l,t,r,b=d['bounds']
                # Traverse full map and return without finishing an escort.
                # Stop before the exit trigger; still visit the final sector.
                xlo=l+24;xhi=r-256 if d['width']>1024 else r-40
                xs=[round((xlo+(xhi-xlo)*i/4)/8)*8 for i in range(5)]
                upper=t+32;lower=b-32
                routepoints=[(x,lower if i%2==0 else upper) for i,x in enumerate(xs)]
                routepoints += [(x,upper if i%2==0 else lower) for i,x in enumerate(reversed(xs))]
                for bonus in ((100,) if args.replays_only else (0,60,100)):
                    if not args.replays_only:
                        restore(initial);protect();setup_speed(bonus);pos(*closest(d,xlo,(t+b)//2,margin=4));settle_camera()
                        navigate,fail,queue=navigater(d,routepoints,bonus)
                        result=execute(label,d,'traverse-speed'+str(bonus),navigate,fps*150,writer,folder)
                        result['navigation_failures']=fail;result['remaining_corners']=len(queue)
                        stage['trials'].append(result)
                    for section,fraction in ([('middle',.5)] if args.replays_only else [('west',.15),('middle',.5),('east',.85)]):
                        restore(initial);protect();setup_speed(bonus)
                        pos(*closest(d,l+(r-l)*fraction,(t+b)//2));settle_camera()
                        sequence=[({7},fps//2),({6},fps),({7},fps//2),(set(),fps//3),({4},fps//3),({5},fps*2//3),({4},fps//3),(set(),fps//3),({7,5},fps//3),({6,4},fps*2//3),({7,5},fps//3),(set(),fps)]
                        def controller(tick):
                            for keys,length in sequence:
                                if tick<length:return keys
                                tick-=length
                            return None
                        stage['trials'].append(execute(label,d,section+'-reversals-speed'+str(bonus),controller,fps*12,writer,folder))
                # Real spawns, AI, projectiles and active escort. Protection is
                # setup only; movement/fire runs without per-frame RAM grants.
                if not args.replays_only:
                    restore(initial);setup_speed(100);w16('hp',100);w16('shieldTimer',fps*40);w16('spawnTimer',1)
                    if u16('dinorahHp'):w16('dinorahPauseTimer',0)
                    def combat(tick):return {1,[7,5,6,4][tick//(fps*2)%4]}
                    stage['trials'].append(execute(label,d,'combat-speed100',combat,fps*24,writer,folder))
            if args.assert_framing and not args.replays_only:
                restore(initial);protect();setup_speed(100);settle_camera();run(fps)
                before=writes;ordinary=True
                try:
                    press(3);until(lambda:state()==2,'camera-pause-'+label)
                    run(fps//4);press(0);until(lambda:state()==1,'camera-resume-'+label)
                    for _ in range(16):run();visible_pixels(d);sprite_limits()
                finally:ordinary=False
                assert writes==before
                stage['pause_resume']=dict(passed=True,ram_writes_during_check=0,live_pixels=True)
                # Real test-selector restart path, including its mission call
                # and countdown. Seed only the selector mode before input.
                restore(initial);protect();write(syms['testCampaignMode'][0],b'\1')
                pos(*closest(d,(l+r)//2,(t+b)//2));settle_camera()
                before=writes;ordinary=True
                try:
                    press(3);until(lambda:state()==2,'restart-pause-'+label)
                    press(5);press(1)
                    for _ in range(20):
                        if state()==1 and u8('currentLevel')==node and not u8('transitioning'):break
                        if state()==6:press(3)
                        elif state()==0:press(1)
                        run(fps//2)
                    assert state()==1 and u8('currentLevel')==node,('restart failed',label,state())
                    assert abs(signed('cameraX')-clamp(signed('px')-152,0,d['width']-320))<=16
                    assert abs(signed('cameraY')-clamp(signed('py')-131,0,d['height']-224))<=12
                    visible_pixels(d)
                finally:ordinary=False
                assert writes==before
                stage['selector_restart']=dict(passed=True,ram_writes_during_check=0)
                if label in ('6A','6B','12'):
                    restore(initial);protect();w16('dinorahInvTimer',0);w16('dinorahHp',1)
                    seed(0,4,u16('dinorahX'),u16('dinorahY'),200,60000)
                    before=writes;ordinary=True
                    try:
                        for _ in range(fps*5):
                            run()
                            if state()!=1:break
                            assert signed('py')-31-signed('cameraY')>=24
                            assert signed('py')+17-signed('cameraY')<=224
                        assert state()==(4 if label=='12' else 3),('escort death outcome',label,state())
                    finally:ordinary=False
                    assert writes==before
                    stage['escort_death']=dict(passed=True,expected_state=state(),ram_writes_during_check=0)
            save();print('STAGE',label,'trials',len(stage['trials']),'max-errors',max(t0['max_error_x'] for t0 in stage['trials']),max(t0['max_error_y'] for t0 in stage['trials']),'clips',sum(t0['clipped_samples'] for t0 in stage['trials']),flush=True)
        report['passed']=True;save();print('PASS camera audit',report['romSHA256'],flush=True)
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    namespace = {'__name__': 'camera_motion_audit', '__file__': str(BOOT)}
    prefix = BOOT.read_text().split('    try:\n', 1)[0]
    prefix = prefix.replace("default='2,3,4,5,6,7,8'",
                            "default='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16'")
    prefix = prefix.replace('args=parser.parse_args()',
                            "parser.add_argument('--replays-only',action='store_true');parser.add_argument('--assert-framing',action='store_true');parser.add_argument('--assert-centered',action='store_true');args=parser.parse_args()")
    exec(compile(prefix + TAIL,
                 str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
