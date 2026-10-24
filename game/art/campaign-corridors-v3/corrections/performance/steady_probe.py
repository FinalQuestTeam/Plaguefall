"""Same-ROM policy comparison using the established escort libretro bootstrap.

Only this diagnostic writes RAM. Production files/ROM are read-only. The old
policy erases complete enemy/projectile records every physical frame. The two
preserving policies seed enemies once and replenish only inactive bullets;
native_cadence additionally permits normal initial fire/shield/dash clocks.
Neither policy changes the authored roster, caps, physics, rendering or audio.
"""
from pathlib import Path
import argparse
import hashlib
import re
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]
BOOTSTRAP = GAME / 'tools/test_campaign_escorts_emulator.py'

TAIL = '''
        report={'romSHA256':hashlib.sha256(original).hexdigest(),
                'bootstrapSHA256':PERF_CONFIG['bootstrap_sha256'],
                'region':'PAL' if args.pal else 'NTSC','passed':False,
                'requiredFPS':fps,'physicalFramesPerCase':PERF_CONFIG['frames'],
                'warmupSeconds':4,'shieldClock':PERF_CONFIG['shield_clock'],
                'motion':PERF_CONFIG['motion'],
                'measuredPhases':PERF_CONFIG['phases'],'policies':PERF_CONFIG['policies'],
                'instrumentedTimingDiagnosticOnly':any(name in syms for name in ('playProfileTicks','renderProfileTicks','logicProfileTicks')),
                'cases':[],
                'method':'Same production ROM and node snapshot per policy. Invulnerability and enemy HP isolate timing; Dinorah waits. Legacy resets complete records each VBlank; preserving policies retain AI/render clocks and velocities. No transition or death settling is included. '+('Real controller patrol exercises camera streaming; not a complete route/difficulty playthrough.' if PERF_CONFIG['motion']=='patrol' else 'Static camera load; not route difficulty.')}
        if PERF_CONFIG['sample_pc']:
            # This core exports Musashi's one-argument register API. PC=16,
            # A7=15; confirmed against its dispatch table, not RAM offsets.
            core.m68k_get_reg.argtypes=[C.c_int];core.m68k_get_reg.restype=C.c_uint
            linked_functions=[]
            for line in symbols.splitlines():
                fields=line.split()
                if len(fields)==4 and fields[2] in ('T','t'):
                    address,size=int(fields[0],16),int(fields[1],16)
                    if address<len(original):linked_functions.append((address,size,fields[3]))
            def pc_sample():
                pc=core.m68k_get_reg(16);sp=core.m68k_get_reg(15)
                function=next((name for address,size,name in linked_functions if address<=pc<address+size),None)
                return {'pc':pc,'pcHex':hex(pc),'symbol':function,'spHex':hex(sp),
                        'stackTopHex':read(sp&65535,32).hex()}
        specifications={
            '3':(4,[1,0],4,6),'6A':(7,[4,5],3,4),
            '6B':(8,[4,5,7],3,4),'9':(11,[4,2,9],3,4),
            '12':(node12,[4,5,2],3,4)}
        def current_active(escort):
            return state()==1 and u16('hp')>0 and (not escort or u16('dinorahHp')>0)
        def event_snapshot(cap,shotcap):
            bases={'px','py','dinorahX','dinorahY','cameraX','cameraY','residentLeft','residentTop','dinorahState','dinorahAimTimer',
                   'dinorahFireTimer','dinorahPauseTimer','dinorahAnimTick','dinorahNode','shieldTimer',
                   'loadedPose','loadedDir','running','frame','nextSlot','evictionCursor','pinnedSlots',
                   'queueIndex','queueTransferSize','queueSize','hudPending','hudLast','hudSignature',
                   'lastShieldSeconds','lastModeCharges','shotCooldown','cpuFrameLoad','nextFrame','sightCount','sightNext'}
            scalar={name:int.from_bytes(read(address,size),'big') for name,(address,size) in syms.items()
                    if name.split('.lto_priv.')[0] in bases and size<=4}
            enemies_trace=[]
            for index in range(cap):
                b=read(syms['enemies'][0]+index*46,46)
                enemies_trace.append(dict(index=index,x=int.from_bytes(b[0:2],'big',signed=True),
                    y=int.from_bytes(b[2:4],'big',signed=True),vx=int.from_bytes(b[12:14],'big',signed=True),
                    vy=int.from_bytes(b[14:16],'big',signed=True),fireTimer=int.from_bytes(b[16:18],'big'),
                    retarget=int.from_bytes(b[18:20],'big'),tA=int.from_bytes(b[24:26],'big'),
                    tB=int.from_bytes(b[26:28],'big'),mode=b[28],type=b[30],hp=b[31],active=b[44],raw=b.hex()))
            arrays={name:read(address,size).hex() for name,(address,size) in syms.items()
                    if name.split('.lto_priv.')[0] in ('slots','blockOwner','hudDirty','campaignRouteOps','sightRays') and size<=512}
            pools={name:[read(syms[name][0]+i*20,20).hex() for i in range(shotcap)] for name in ('pshots','eshots')}
            return {'gameFrames':frames(),'vtimer':u32('vtimer'),'scalars':scalar,'enemies':enemies_trace,
                    'shots':pools,'arraysHex':arrays}
        for phase in PERF_CONFIG['phases']:
            node,roster,cap,shotcap=specifications[phase]
            enter(node);initial=snapshot();escort=phase in ('6A','6B','12')
            if PERF_CONFIG['motion']=='patrol':
                folder={'3':'streets/3','6A':'sewers/6A','6B':'sewers/6B','9':'streets/9','12':'syndicate/12'}[phase]
                if PERF_CONFIG['geometry_dir']:
                    provenance=json.loads((PERF_CONFIG['geometry_dir']/'provenance.json').read_text())
                    assert provenance['romSHA256']==report['romSHA256']
                    authored=json.loads((PERF_CONFIG['geometry_dir']/(phase+'.json')).read_text())
                    report['geometrySnapshot']=str(PERF_CONFIG['geometry_dir'])
                else:authored=json.loads((PERF_CONFIG['art_root']/folder/'manifest.json').read_text())
                points=authored.get('route_points',authored.get('points'))
                patrol_left,patrol_y=authored['start']
                patrol_right=min(patrol_left+240,points[1][0]-8)
                assert points[1][1]-8==patrol_y and patrol_right-patrol_left>=128
            # Identical local placement in all policies. Only the state-reset
            # policy changes; no enemy is frozen or has its type substituted.
            origins=[(80+i%4*48,200+i//4*24) for i in range(cap)]
            for policy in PERF_CONFIG['policies']:
                restore(initial);isolate()
                shield_duration=fps*PERF_CONFIG['shield_tenths']//10
                w16('shieldTimer',0 if PERF_CONFIG['shield_clock']=='absent' else
                    shield_duration if PERF_CONFIG['shield_clock']=='item' else 60000)
                item_grant_clock=0
                patrol_rightward=True
                if PERF_CONFIG['shield_clock']=='absent':
                    # The approved beetle benchmark protects through the
                    # player hit timer, which has no countdown in the HUD.
                    hit_timers={address for name,(address,size) in syms.items()
                                if name.split('.lto_priv.')[0]=='invTimer' and size==2}
                    assert hit_timers,'player hit timer symbols missing'
                    for address in hit_timers:write(address,struct.pack('>H',60000))
                if escort:
                    w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000)
                for i,(x,y) in enumerate(origins):
                    seed(i,roster[i%len(roster)],x,y,200,
                         0 if policy=='native_cadence' else 60000)
                def arrange():
                    nonlocal item_grant_clock,patrol_rightward
                    if PERF_CONFIG['motion']=='patrol':
                        if u16('px')>=patrol_right:patrol_rightward=False
                        if u16('px')<=patrol_left:patrol_rightward=True
                        buttons.clear();buttons.add(7 if patrol_rightward else 6)
                    if PERF_CONFIG['shield_clock']=='fixed':w16('shieldTimer',60000)
                    if PERF_CONFIG['shield_clock']=='item':
                        # A repeated diagnostic grant uses the exact production
                        # item duration, with a real visible3..2..1countdown.
                        if item_grant_clock>=shield_duration-1:
                            w16('shieldTimer',shield_duration);item_grant_clock=0
                        item_grant_clock+=1
                    if policy=='legacy_reset':
                        w16('hp',100);w16('spawnTimer',60000)
                        for i,(x,y) in enumerate(origins):
                            seed(i,roster[i%len(roster)],x,y,200,60000)
                    else:
                        # Health alone is refreshed. Never reset an active
                        # enemy's velocity, retarget, pose or behaviour clocks.
                        for i in range(cap):
                            write(syms['enemies'][0]+i*46+31,bytes([200]))
                    for name in ('pshots','eshots'):
                        for i in range(shotcap):
                            at=syms[name][0]+i*20
                            if policy!='legacy_reset' and read(at+18,1)[0]:continue
                            buf=bytearray(20)
                            struct.pack_into('>iiii',buf,0,(80+i%3*64)<<6,
                                             (216+i//3*32)<<6,24,0)
                            buf[17]=1;buf[18]=1;write(at,buf)
                for _ in range(fps*4):
                    arrange();run();assert current_active(escort),('warmup left play',phase,policy)
                begin=frames();vb=u32('vtimer');loads=[];active=[];cameras=[]
                timers=set();poses=set();sat=[0,0,0];poolmin=[shotcap,shotcap]
                profiles={name:[] for name in ('playProfileTicks','renderProfileTicks','logicProfileTicks') if name in syms}
                player_positions=[];visible_enemies=[];visible_pools=[[],[]]
                discontinuities=[];last=begin;hud_transitions=[];recent_trace=[]
                last_dinorah=u8('dinorahState')
                for tick in range(PERF_CONFIG['frames']):
                    assert current_active(escort),('measurement left play',phase,policy,tick)
                    arrange()
                    for index,name in enumerate(('pshots','eshots')):
                        count=sum(read(syms[name][0]+i*20+18,1)[0]!=0 for i in range(16))
                        poolmin[index]=min(poolmin[index],count)
                        assert count==shotcap,(phase,policy,name,count,shotcap)
                    if PERF_CONFIG['event_trace']:before_event=event_snapshot(cap,shotcap)
                    run()
                    assert current_active(escort),('death/transition entered sample',phase,policy,tick)
                    now=frames()
                    dinorah_state=u8('dinorahState')
                    if dinorah_state!=last_dinorah:
                        hud_transitions.append({'physicalOffset':tick,'gameFrame':now,
                                                'previous':last_dinorah,'current':dinorah_state})
                        last_dinorah=dinorah_state
                    if now-last!=1:
                        event={'physicalOffset':tick,'gameDelta':now-last,
                            'dinorahState':dinorah_state,'shieldTimer':u16('shieldTimer')}
                        if PERF_CONFIG['sample_pc']:event['cpu']=pc_sample()
                        if PERF_CONFIG['event_trace']:
                            event['eventTrace']=recent_trace[-3:]+[{'physicalOffset':tick,'before':before_event,'after':event_snapshot(cap,shotcap)}]
                        if profiles:
                            event['lastProfileSubTicks']={name:list(struct.unpack('>'+str(syms[name][1]//2)+'H',read(*syms[name]))) for name in profiles}
                        discontinuities.append(event)
                    if PERF_CONFIG['event_trace']:
                        recent_trace.append({'physicalOffset':tick,'before':before_event,'after':event_snapshot(cap,shotcap)})
                        recent_trace=recent_trace[-3:]
                    last=now;loads.append(u16('cpuFrameLoad')*100/2048)
                    for profile_name,profile_samples in profiles.items():
                        address,byte_count=syms[profile_name]
                        profile_samples.append(struct.unpack('>'+str(byte_count//2)+'H',read(address,byte_count)))
                    active.append(living());cameras.append((u16('cameraX'),u16('cameraY')))
                    player_positions.append((u16('px'),u16('py')))
                    cx,cy=cameras[-1];visible=0
                    for enemy_index in range(cap):
                        enemy=read(syms['enemies'][0]+enemy_index*46,46)
                        ex,ey=struct.unpack_from('>hh',enemy)
                        size=32 if enemy[30] in (2,10) else 24 if enemy[30] in (8,9,11) else 16
                        visible+=int(enemy[44]!=0 and ex+size>cx and ex<cx+320 and ey-16+size>cy+24 and ey-16<cy+224)
                    visible_enemies.append(visible)
                    for pool_index,pool_name in enumerate(('pshots','eshots')):
                        visible=0
                        for shot_index in range(shotcap):
                            projectile_record=read(syms[pool_name][0]+shot_index*20,20)
                            sx,sy=struct.unpack_from('>ii',projectile_record);sx>>=6;sy=(sy>>6)-16
                            visible+=int(projectile_record[18]!=0 and sx+8>cx and sx<cx+320 and sy+8>cy+24 and sy<cy+224)
                        visible_pools[pool_index].append(visible)
                    timers.add(int.from_bytes(read(syms['enemies'][0]+18,2),'big'))
                    poses.add(read(syms['pshots'][0]+19,1)[0])
                    if tick%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
                game,physical=frames()-begin,u32('vtimer')-vb
                assert min(active)==max(active)==cap,(phase,policy,'population drift',min(active),max(active))
                assert physical==PERF_CONFIG['frames'],('unexpected physical timing',physical)
                if PERF_CONFIG['motion']=='patrol':
                    assert max(v[0] for v in player_positions)-min(v[0] for v in player_positions)>=128,'player patrol not exercised'
                    assert max(v[0] for v in cameras)-min(v[0] for v in cameras)>=16,'camera streaming not exercised'
                row={'phase':phase,'policy':policy,'roster':roster,'enemyCap':cap,
                     'shotCapPerPool':shotcap,'enemyPositionsAtSetup':origins,
                     'physicalFrames':physical,'gameFrames':game,
                     'gameFPS':round(fps*game/physical,5),'targetMet':game==physical,
                     'meanCPULoadPct':round(statistics.mean(loads),3),
                     'p95CPULoadPct':round(sorted(loads)[int(len(loads)*.95)],3),
                     'maximumCPULoadPct':round(max(loads),3),
                     'populationRange':[min(active),max(active)],
                     'minimumShotsBeforeStep':poolmin,'retargetValues':sorted(timers),
                     'playerShotCachedPoseValues':sorted(poses),
                     'cameraRange':[[min(v[i] for v in cameras),max(v[i] for v in cameras)] for i in (0,1)],
                     'playerPositionRange':[[min(v[i] for v in player_positions),max(v[i] for v in player_positions)] for i in (0,1)],
                     'visibleEnemiesRange':[min(visible_enemies),max(visible_enemies)],
                     'visibleProjectilesRange':[[min(v),max(v)] for v in visible_pools],
                     'satMaximumSampled':sat,'nonUnitGameFrameSteps':discontinuities,
                     'dinorahStateTransitions':hud_transitions,
                     'instrumented':bool(profiles),
                     'profileSubTicks':{name:{'mean':[round(statistics.mean(s[i] for s in samples),3) for i in range(len(samples[0]))],
                         'maximum':[max(s[i] for s in samples) for i in range(len(samples[0]))],
                         'p95':[sorted(s[i] for s in samples)[int(len(samples)*.95)] for i in range(len(samples[0]))]}
                         for name,samples in profiles.items()},
                     'phaseStayedActive':True,'deathTailIncluded':False}
                report['cases'].append(row);save()
                print(json.dumps({k:row[k] for k in ('phase','policy','gameFPS','targetMet','meanCPULoadPct','maximumCPULoadPct','cameraRange')},ensure_ascii=False),flush=True)
                shot(phase+'-'+policy+'-steady')
        acceptance=[x for x in report['cases'] if x['policy']!='legacy_reset']
        report['passed']=bool(acceptance) and all(x['targetMet'] for x in acceptance)
        report['status']='target-met' if report['passed'] else 'needs-optimization'
        save()
    finally:
        core.retro_unload_game();core.retro_deinit()
    return 0 if report['passed'] else 3
'''


def program():
    source = BOOTSTRAP.read_text()
    marker = "        for node,key in ((7,'06a'),(8,'06b'),(node12,'12')):"
    if source.count(marker) != 1:
        raise ValueError('escort bootstrap anchor changed; review the diagnostic adapter')
    prefix = source.split(marker)[0]
    parser_lines = [line for line in prefix.splitlines() if line.lstrip().startswith('parser=argparse.ArgumentParser();')]
    if len(parser_lines) != 1:
        raise ValueError('escort argument parser anchor changed')
    return prefix.replace(parser_lines[0], '    args=PRIVATE_ARGS') + TAIL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pal', action='store_true')
    parser.add_argument('--build-dir', type=Path, default=GAME / 'out/release')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--phases', default='3,6A,6B,12,9')
    parser.add_argument('--policies', default='legacy_reset,preserve_caches,native_cadence')
    parser.add_argument('--frames', type=int, default=1800)
    parser.add_argument('--shield-clock', choices=('running', 'fixed', 'absent', 'item'), default='running',
                        help='fixed/absent isolate the HUD shield countdown; no production code changes')
    parser.add_argument('--check-syntax', action='store_true')
    parser.add_argument('--sample-pc', action='store_true')
    parser.add_argument('--event-trace', action='store_true', help='Read-only host pre/post RAM observations on misses')
    parser.add_argument('--geometry-dir',type=Path,help='Frozen current bridge geometry with ROM provenance')
    parser.add_argument('--motion', choices=('static','patrol'), default='static')
    options = parser.parse_args()
    if options.frames < 1800:
        parser.error('steady measurements require at least1800physical VBlanks')
    phases = options.phases.split(',')
    policies = options.policies.split(',')
    if set(phases) - {'3', '6A', '6B', '9', '12'} or set(policies) - {'legacy_reset', 'preserve_caches', 'native_cadence'}:
        parser.error('unknown phase or policy')
    code = compile(program(), str(HERE / 'adapted-escort-bootstrap.py'), 'exec')
    if options.check_syntax:
        print('PASS isolated diagnostic syntax; no emulation or production writes')
        return 0
    sys.path.insert(0, str(GAME / 'tools'))
    namespace = {'__name__': 'private_performance_probe', '__file__': str(BOOTSTRAP),
                 'PRIVATE_ARGS': SimpleNamespace(pal=options.pal, movie=False,
                     build_dir=options.build_dir.resolve(),
                     output=(options.output or HERE / ('pal' if options.pal else 'ntsc')).resolve()),
                 'PERF_CONFIG': {'frames': options.frames, 'phases': phases,
                     'policies': policies,
                     'shield_clock': options.shield_clock,
                     'sample_pc': options.sample_pc,
                     'event_trace': options.event_trace,
                     'geometry_dir':options.geometry_dir.resolve() if options.geometry_dir else None,
                     'motion': options.motion,
                     'art_root': HERE.parents[1],
                     'shield_tenths': int(re.search(r'#define PLAYER_SHIELD_TENTHS\s+(\d+)',
                         (GAME / 'src/actors/player.h').read_text())[1]),
                     'bootstrap_sha256': hashlib.sha256(BOOTSTRAP.read_bytes()).hexdigest()}}
    exec(code, namespace)
    return namespace['main']()


if __name__ == '__main__':
    raise SystemExit(main())
