"""Phase6A/6B production-ROM scenery, mechanism, escort and native-load probes.

Entry and traversal use controllers. RAM setup explicitly isolates collision,
rendering and load cases; unmodified combat is measured separately.
"""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import faces
    from collections import Counter
    import bisect
    core.m68k_get_reg.argtypes=[C.c_int];core.m68k_get_reg.restype=C.c_uint
    linked=sorted((int(v[0],16),int(v[1],16),v[3]) for line in symbols.splitlines() if len(v:=line.split())==4 and v[2] in ('T','t') and int(v[0],16)<len(original))
    addresses=[v[0] for v in linked]
    def pc_function():
        pc=core.m68k_get_reg(16);i=bisect.bisect_right(addresses,pc)-1
        return linked[i][2] if i>=0 and pc<linked[i][0]+linked[i][1] else hex(pc)
    root=GAME/'art/phase06-three-segments-v1/integration-v1'
    report['scope']='6A/6B controller entry, escort traversal and pause; RAM isolates contact/camera/mechanism cases. Exact visible VRAM checked against source patterns. Load retains native AI clocks and active trajectories. Natural combat has no RAM health/AI grants.'
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*15):
            run();current=(u16('cameraX'),u16('cameraY'))
            if state()!=1:return
            stable=stable+1 if current==previous else 0;previous=current
            if stable>=8:return
        raise AssertionError('camera stalled')
    def protect():
        isolate();w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',0)
        for name in syms:
            if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,0)
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps)
        ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)
        prep=snapshot()
        for key,node in [('06a',7),('06b',8)]:
            if key not in wanted_phases:continue
            restore(prep);write(syms['pendingLevel'][0],bytes([node]));ui(1)
            until(lambda:state()==1 and u8('currentLevel')==node and not u8('transitioning'),'entry-'+key,fps*20)
            initial=snapshot();d=maps[key];cols=384
            patterns=(GAME/f'res/campaign_routes/{key}/tiles.bin').read_bytes()
            ids=struct.unpack('>15360H',(GAME/f'res/campaign_routes/{key}/map.bin').read_bytes())
            gate_raw=(root/'mechanisms/gate-frames.bin').read_bytes()
            valve_raw=(GAME/'res/objectives/animations.bin').read_bytes()[4032*4:4800*4]
            def visuals():
                result=[]
                if d.get('gates'):
                    for slot in range(4 if key=='06b' else 2):
                        b=read(syms['objectiveVisuals'][0]+slot*12,12)
                        xx,yy=struct.unpack('>hh',b[:4]);art,frame,visible=b[6],b[7],b[9]
                        if not visible:continue
                        width,height,raw=(8,8,gate_raw) if art==5 else (4,4,valve_raw)
                        result.append(((xx-width*4)//8,(yy-height*8+8)//8,width,height,frame,raw))
                return result
            def cache_pixels():
                assert u16('sceneStreamFaults')==0,('stream fault',key,u16('sceneStreamFaults'))
                assert u16('sceneStreamPeak')<=456
                cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;objects=visuals();used=set();ink=0
                for row in range((cy+24)//8,(cy+223)//8+1):
                    for col in range(cx//8,(cx+319)//8+1):
                        source=ids[row*cols+col];slot=int.from_bytes(read(loc+source*2,2),'big')
                        assert slot<456,('missing slot',key,cx,cy,col,row,source,slot)
                        attr=vw(u16('bgb_addr')+((row&31)*64+(col&63))*2)
                        assert attr==0x6000+785+slot,('BG_B map',key,cx,cy,col,row,hex(attr),slot)
                        assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('BG_B pixels',key,cx,cy,col,row,source,slot)
                        expected=None
                        for ox,oy,ww,hh,frame,raw in objects:
                            if ox<=col<ox+ww and oy<=row<oy+hh:
                                local=(col-ox)*hh+row-oy;offset=(frame*ww*hh+local)*32;tile=raw[offset:offset+32]
                                if any(tile):expected=tile
                        overlay=vw(u16('bga_addr')+((row&31)*64+(col&63))*2)
                        if expected:
                            assert overlay&0xe000==0x2000,('mechanism palette',key,col,row,overlay)
                            assert vr((overlay&2047)*32,32)==expected,('mechanism pixels',key,col,row,overlay)
                            ink+=1
                        else:assert overlay==0,('BG_A stale fragment',key,cx,cy,col,row,hex(overlay))
                        used.add(slot)
                return dict(camera=[cx,cy],resident=len(used),peak=u16('sceneStreamPeak'),mechanism_cells=ink)
            if not os.environ.get('PHASE06_ONLY_LOAD'):
                protect();wait_camera();shot(key+'-01-entrada')
                check(key+'-entry-exact-pixels',cache_pixels())
                ui(3);until(lambda:state()==2,'pause-'+key)
                assert not u32('location'),'cache work retained during pause'
                shot(key+'-02-pausa');ui(0);until(lambda:state()==1,'resume-'+key);run(3)
                check(key+'-pause-restores-cache-and-mechanisms',cache_pixels())
                views=[]
                for x in [264,512,720,800,960,1200,1440,1664,1808,1920,2112,2400,2720,2936,2400,1808,800,264]:
                    for y in [136,200,256]:
                        xx,yy=closest(d,x,y,extra=d.get('gates',[]));pos(xx,yy);wait_camera();run(2);views.append(cache_pixels())
                    if x in [800,1440,1808,2936]:shot(key+'-camera-'+str(x))
                check(key+'-full-forward-reverse-vertical-scroll',dict(samples=len(views),maximum_visible_tiles=max(v['resident'] for v in views),zero_pixel_mismatches=True))
                lower=[]
                for x in [264,800,1320,1808,2400,2800]:
                    xx,yy=closest(d,x,232,extra=d.get('gates',[]));pos(xx,yy);hold({5},fps*2);wait_camera()
                    assert u16('py')==256 and u16('cameraY')==96,('southern boundary',key,x,u16('py'),u16('cameraY'))
                    lower.append(cache_pixels())
                shot(key+'-03-limite-inferior');check(key+'-lower-scenery-visible-nonwalkable',lower)
                restore(initial);protect();contacts=[]
                for x,y,button,axis,limit,direction in faces(d):
                    # Physical gates are tested separately; ordinary prop faces remain isolated.
                    if d.get('gates') and any(x<gx+gw and x+16>gx and y<gy+gh and y+16>gy for gx,gy,gw,gh in d['gates']):continue
                    pos(x,y);hold({button},fps//2);value=u16(axis)
                    assert value<=limit if direction>0 else value>=limit,('contact',key,x,y,button,axis,limit,value)
                    assert u16('sceneStreamFaults')==0;contacts.append([x,y,button,value])
                check(key+'-all-prop-and-boundary-contact-faces',len(contacts))
                restore(initial);protect()
                if d.get('gates'):
                    op=syms['campaignRouteOps'][0]
                    bar_samples=[];hint_samples=[]
                    marker_raw=(GAME/'res/routes/markers.bin').read_bytes()
                    marker_at=vr(0,65536).find(marker_raw)
                    assert marker_at>=0 and marker_at%32==0,'resident marker bank missing'
                    marker_base=marker_at//32
                    def gate_hint(i,hits):
                        sprites=[];index=0;base=u16('slist_addr')
                        for _ in range(80):
                            at=base+index*8;sl=vw(at+2);attr=vw(at+4)
                            tile=attr&2047
                            if marker_base+24<=tile<marker_base+45:
                                sprites.append((tile,(vw(at+6)&511)-128,(vw(at)&1023)-128,(((sl>>10)&3)+1)*8,(((sl>>8)&3)+1)*8,attr))
                            index=sl&127
                            if not index:break
                        if hits is None:
                            assert not sprites,('unexpected shoot hint',key,i,sprites)
                            return
                        gx,gy,gw,gh=d['gates'][i];cx,cy=u16('cameraX'),u16('cameraY')
                        x=gx+gw//2-12;y=gy-24
                        if y<cy+26:x=gx+gw//2+12;y=max(gy+8,cy+26)
                        x=max(cx+2,min(x,cx+294));y=min(y,cy+198)
                        expected=[(marker_base+30+hits*3,x-cx,y+16-cy,24,8)]
                        if hits<4:expected.insert(0,(marker_base+24,x-cx,y-cy,24,16))
                        assert [v[:5] for v in sprites]==expected,('gate hint state/position',key,i,hits,sprites,expected)
                        for tile,sx,sy,ww,hh,attr in sprites:
                            assert attr&0xe000==0x2000 and sx>=0 and sy>=26 and sx+ww<=320 and sy+hh<=224,('hint palette/bounds',hex(attr),sx,sy,ww,hh)
                            size=ww*hh//2;offset=(tile-marker_base)*32
                            assert vr(tile*32,size)==marker_raw[offset:offset+size]
                        return dict(hits=hits,sprites=[list(v[:5]) for v in sprites],exact_resident_pixels=True)
                    def valve_bar(i):
                        vx,vy=d['valves'][i];cx,cy=u16('cameraX'),u16('cameraY')
                        base=u16('slist_addr');index=0;found=False
                        for _ in range(80):
                            at=base+index*8;sl=vw(at+2);attr=vw(at+4)
                            if attr&2047==1421:
                                assert (vw(at+6)&511)-128==vx-16-cx
                                assert (vw(at)&1023)-128==vy-28-cy
                                assert ((sl>>10)&3)==3 and ((sl>>8)&3)==0
                                found=True;break
                            index=sl&127
                            if not index:break
                        assert found,('valve progress bar missing from SAT',i)
                        rawbar=vr(1421*32,128)
                        assert rawbar!=vr(1436*32,128),'valve and ally bars share pixels'
                        def color(x,y):
                            byte=rawbar[(x//8)*32+y*4+(x%8)//2]
                            return byte&15 if x%2 else byte>>4
                        assert all(color(x,1)==1 and color(x,5)==1 for x in range(32))
                        fill=[color(x,2) for x in range(1,31)]
                        filled=fill.count(4)
                        assert fill==[4]*filled+[11]*(30-filled),('bar pixels broken',i,fill)
                        work=int.from_bytes(read(op+i*2,2),'big');percent=work*100/((fps*3+1)//2)
                        assert abs(filled*100/30-percent)<=12,('bar does not follow valve work',i,filled,percent)
                        return dict(work=work,percent=round(percent,1),filled_pixels=filled,world_position=[vx-16,vy-28],visible_sprite=True)
                    for i,gate in enumerate(d['gates']):
                        gx,gy,gw,gh=gate
                        pos(gx-16,gy+16);hold({7},fps//2)
                        assert u16('px')<=gx-16,('closed gate collision',key,i,u16('px'),gx)
                        if key=='06b':
                            vx,vy=d['valves'][i]
                            # Real steam damage, followed by the safe valve pocket.
                            write(op+4,struct.pack('>H',fps));write(op+6,b'\0\0')
                            for name in syms:
                                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,0)
                            before_steam=u16('hp');run(3);assert u16('hp')==before_steam-5
                            pos(*d['gate_shot_approaches'][i]);hold({7},2);hold({1},fps//2)
                            assert read(op+8+i,1)[0]==4,'pressure gate damaged before valve operation'
                            pos(*d['valve_approaches'][i]);buttons.add(1);wait_camera();run(2);buttons.clear()
                            assert int.from_bytes(read(op+i*2,2),'big')<(fps*3+1)//8,('unexpected pre-work',i,read(op,4).hex())
                            gate_hint(i,None)
                            start_hp=u16('hp');samples=[];target=(fps*3+1)//2
                            for threshold in [target//4,target//2,target*3//4]:
                                until(lambda:int.from_bytes(read(op+i*2,2),'big')>=threshold,'valve-progress-'+str(i))
                                run(2);sample=valve_bar(i);samples.append(sample)
                                ptr=u32('objectiveLabel');assert original[ptr:ptr+7]==b'ABRINDO'
                                shot(key+'-valvula-'+str(i+1)+'-progresso-'+str(len(samples)))
                                if len(samples)==1:
                                    # A freezes operation; releasing it resumes the same work value.
                                    before=int.from_bytes(read(op+i*2,2),'big');hold({1},fps//4)
                                    assert int.from_bytes(read(op+i*2,2),'big')<=before+2
                                    sample=valve_bar(i)
                                    ui(3);until(lambda:state()==2,'valve-work-pause')
                                    paused=int.from_bytes(read(op+i*2,2),'big');run(fps//2)
                                    assert int.from_bytes(read(op+i*2,2),'big')==paused
                                    ui(0);until(lambda:state()==1,'valve-work-resume');run(2);valve_bar(i)
                            assert all(a['filled_pixels']<b['filled_pixels'] for a,b in zip(samples,samples[1:]))
                            until(lambda:read(op+10,1)[0]&(1<<i),'valve-complete')
                            assert int.from_bytes(read(op+i*2,2),'big')==target
                            assert u16('hp')==start_hp,'valve pocket unsafe'
                            run(2);cache_pixels();shot(key+'-valvula-'+str(i+1))
                            bar_samples.append(dict(valve=i+1,samples=samples,paused_work_preserved=True,shooting_stops_work=True))
                        else:
                            assert read(op+10,1)[0]==3 and read(op,4)==bytes(4)
                            assert int.from_bytes(read(syms['objectiveArtBases'][0]+8,2),'big')==0,'6A loaded valve graphics'
                            assert not any(read(syms['objectiveVisuals'][0]+j*12+9,1)[0] for j in [2,3])
                            check(key+'-no-valves-or-steam',dict(pressure_mask=3,valve_tiles=0))
                        pos(*d['gate_shot_approaches'][i]);hold({7},2);wait_camera();run(2)
                        samples=[gate_hint(i,0)];shot(key+'-portao-'+str(i+1)+'-atire-A')
                        for hits in range(1,5):
                            buttons.add(1)
                            until(lambda:read(op+8+i,1)[0]==4-hits,'gate-hit-'+str(hits),fps*3)
                            buttons.clear();run(2);samples.append(gate_hint(i,hits))
                            shot(key+'-portao-'+str(i+1)+'-acertos-'+str(hits))
                            if hits<4:run(fps//3)
                        hint_samples.append(dict(gate=i+1,states=samples,real_projectile_hits=True))
                        assert read(op+8+i,1)[0]==0,('gate shots',key,i,read(op,16).hex())
                        clear_ticks=int.from_bytes(read(op+12+i*2,2),'big');assert 0<clear_ticks<=fps*4//5
                        address=syms['objectiveVisuals'][0]+i*12;saw_final=False
                        for _ in range(fps):
                            run()
                            if read(address+9,1)[0] and read(address+7,1)[0]==5 and not saw_final:
                                run(2);cache_pixels();shot(key+'-portao-'+str(i+1)+'-colapso');saw_final=True
                            if not read(address+9,1)[0]:break
                        assert saw_final and not read(address+9,1)[0]
                        run(2);cache_pixels();gate_hint(i,None);shot(key+'-portao-'+str(i+1)+'-aberto')
                        pos(gx-16,gy+16);hold({7},fps//2);assert u16('px')>gx+gw
                        check(key+'-gate-'+str(i+1),dict(pressure_seconds=1.5 if key=='06b' else 0,required_hits=4,collapse_seconds=.8,vertical_frames_exact=True,opening_crossed=True))
                    check(key+'-shoot-hint-four-real-hits',hint_samples)
                    if bar_samples:check(key+'-world-valve-progress-bars',bar_samples)
                    before=read(op,16);ui(3);until(lambda:state()==2,'pause-open-gates');ui(0);until(lambda:state()==1,'resume-open-gates');run(2)
                    assert read(op,4)==before[:4] and read(op+8,3)==before[8:11];wait_camera();run(2);cache_pixels()
                    pos(*d['gate_shot_approaches'][0]);wait_camera();poses=[]
                    for pose in range(6):
                        for slot in ([0,2] if key=='06b' else [0]):write(syms['objectiveVisuals'][0]+slot*12+7,bytes([pose,2,1]))
                        xx,yy=closest(d,760+(0 if pose%2 else 16),152);pos(xx,yy);wait_camera();run(2)
                        poses.append(cache_pixels());shot(key+'-mecanismos-pose-'+str(pose))
                    check(key+'-six-native-poses',dict(poses=len(poses),selection='RAM',renderer='production'))
                # Insect contact kills Dinorah: phase6 retries, rather than permanent phase12 death.
                restore(initial);protect();w16('dinorahInvTimer',0);w16('dinorahHp',1)
                seed(0,4,u16('dinorahX'),u16('dinorahY'),200,60000);run(fps*3)
                assert state()==3,('Dinorah death should retry',key,state())
                check(key+'-escort-death-retries')
                # Full route uses normal input and original NPC logic. Combat and gates are isolated.
                restore(initial);protect();w16('dinorahPauseTimer',0)
                if d.get('gates'):
                    write(syms['campaignRouteOps'][0]+8,bytes([0,0,3]))
                    for slot in [0,1]:write(syms['objectiveVisuals'][0]+slot*12+9,b'\0')
                writes_before=writes;ordinary=True;player_node=1;ticks=0;sampled=0;states=set()
                while state()==1 and ticks<fps*180:
                    index=u8('dinorahNode');states.add(u8('dinorahState'))
                    tx,ty=d['points'][min(player_node,len(d['points'])-1)];tx-=8;ty-=8
                    dx,dy=tx-u16('px'),ty-u16('py');ax,ay=tx-u16('dinorahX'),ty-u16('dinorahY')
                    buttons.clear()
                    if abs(dx)<=3 and abs(dy)<=3 and index>player_node:player_node+=1
                    if u16('px')-u16('dinorahX')<=64 or dx<0 or index>=len(d['points']):
                        if abs(dx)>3:buttons.add(7 if dx>0 else 6)
                        if abs(dy)>3:buttons.add(5 if dy>0 else 4)
                    run();ticks+=1
                    assert u16('sceneStreamFaults')==0
                    if ticks%180==0 and state()==1:
                        buttons.clear();wait_camera();run(2)
                        if state()==1:cache_pixels();sampled+=1
                        if u16('px')>1400 and u16('px')<1550:shot(key+'-04-travessia-meio')
                    if u16('px')>2860 and ticks%120==0:shot(key+'-05-acesso-abrigo')
                ordinary=False;buttons.clear()
                assert writes==writes_before
                assert state()==4,('route stuck',key,ticks,u16('px'),u16('py'),u16('dinorahX'),u16('dinorahY'),u8('dinorahNode'))
                assert u16('dinorahHp')==100;shot(key+'-06-chegada')
                check(key+'-controller-escort-to-arrival',dict(seconds=round(ticks/fps,2),states=sorted(states),pixel_samples=sampled,ram_writes_during_traversal=0,combat_isolated=True,gates_seeded_open=bool(d.get('gates'))))
            # Authored maximum population and full pools, active enemy AI/trajectories retained.
            loads=[]
            for section,x,y in [('entrada',264,192),('meio',1424,232),('portao',1744,232)]:
                restore(initial);protect();w16('dinorahInvTimer',60000)
                for name in syms:
                    if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
                xx,yy=closest(d,x,y,extra=d.get('gates',[]));pos(xx,yy)
                for i,g in enumerate(d.get('gates',[])):
                    if xx>g[0]+g[2]:
                        op=syms['campaignRouteOps'][0];write(op+8+i,b'\0');write(op+10,bytes([read(op+10,1)[0]|(1<<i)]))
                        write(syms['objectiveVisuals'][0]+i*12+9,b'\0')
                        if key=='06b':write(syms['objectiveVisuals'][0]+(i+2)*12+7,bytes([5,2,1]))
                write(syms['running.lto_priv.0'][0],b'\0');w16('dinorahX',xx+24);w16('dinorahY',yy);write(syms['dinorahFx'][0],struct.pack('>i',(xx+24)<<6));write(syms['dinorahFy'][0],struct.pack('>i',yy<<6))
                wait_camera()
                roster=[4,5,7] if key=='06b' else [4,5]
                for i in range(3):
                    ex,ey=closest(d,xx+48+i*32,yy,extra=d.get('gates',[]));seed(i,roster[i%len(roster)],ex,ey,200,0)
                direction=1;cpu=[];sat=[0,0,0];visible=[];cams=[];retarget=set();miss_pc=Counter();all_pc=Counter();profiles={n:[] for n in ['playProfileTicks','renderProfileTicks'] if n in syms}
                def arrange():
                    nonlocal direction
                    if u16('px')>=xx+96:direction=-1
                    if u16('px')<=xx-32:direction=1
                    buttons.clear();buttons.add(7 if direction>0 else 6)
                    for i in range(3):write(syms['enemies'][0]+i*46+31,b'\xc8')
                    for name in ['pshots','eshots']:
                        for i in range(4):
                            at=syms[name][0]+i*20
                            if read(at+18,1)[0]:continue
                            b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+40+i*48)<<6,(u16('cameraY')+184)<<6,24,0);b[17]=b[18]=1;write(at,b)
                for _ in range(fps*4):arrange();run()
                start=frames();vb=u32('vtimer')
                for tick in range(fps*15):
                    before_frame=frames();arrange();run();pc=pc_function();all_pc[pc]+=1
                    if frames()-before_frame!=1:miss_pc[pc]+=1
                    assert state()==1 and living()==3,(key,section,tick,'load population drift',living(),state(),[u16(n) for n in ['px','py','dinorahX','dinorahY','cameraX','cameraY']],[read(syms['enemies'][0]+i*46,46).hex() for i in range(3)])
                    assert u16('sceneStreamFaults')==0
                    
                    for n,v in profiles.items():v.append(struct.unpack('>4H',read(*syms[n])))
                    cpu.append(u16('cpuFrameLoad')*100/2048);cams.append(u16('cameraX'));retarget.add(int.from_bytes(read(syms['enemies'][0]+18,2),'big'))
                    if tick%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
                buttons.clear();game,physical=frames()-start,u32('vtimer')-vb
                wait_camera();run(2);cache_pixels();shot(key+'-carga-'+section)
                loads.append(dict(section=section,enemies=3,shots_per_pool=4,physical_frames=physical,game_frames=game,game_fps=round(fps*game/physical,3),mean_cpu_pct=round(statistics.mean(cpu),2),p95_cpu_pct=round(sorted(cpu)[int(len(cpu)*.95)],2),maximum_cpu_pct=round(max(cpu),2),camera_range=[min(cams),max(cams)],retarget_values=len(retarget),sprite_limits=sat,active_AI_and_trajectories_retained=True,miss_pc=miss_pc.most_common(12),all_pc=all_pc.most_common(12),profile_means={n:[round(statistics.mean(s[i] for s in v),2) for i in range(4)] for n,v in profiles.items()}))
            check(key+'-authored-cap-load',loads)
            # Natural stationary defense with native spawns/fire/damage; no RAM writes after entry.
            restore(initial);ordinary=True;start=frames();vb=u32('vtimer');peak=0;minimum_hp=u16('hp');ticks=0;buttons.add(1)
            while state()==1 and ticks<fps*30:
                run();ticks+=1;peak=max(peak,living());minimum_hp=min(minimum_hp,u16('hp'))
            ordinary=False;buttons.clear();shot(key+'-combate-natural')
            check(key+'-natural-combat-smoke',dict(seconds=round(ticks/fps,2),state=state(),minimum_player_hp=minimum_hp,dinorah_hp=u16('dinorahHp'),maximum_enemies=peak,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),ram_health_AI_grants=False,scope='stationary defense, not a complete combat escort or human difficulty approval'))
        report['performance_target_met']=all(row['game_frames']==row['physical_frames'] for name,rows in report['checks'].items() if name.endswith('-authored-cap-load') for row in rows)
        report['human_difficulty_approved']=False
        report['passed']=True;save();print('PASS phase6 integration',report['romSHA256'],flush=True)
    except Exception as e:
        ordinary=False;report['error']=repr(e);save();shot('FAIL-phase06');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase06_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':
    sys.path.insert(0,str(BOOT.parent));main()
