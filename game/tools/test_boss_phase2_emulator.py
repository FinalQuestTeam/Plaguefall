"""Production-ROM boss phase2: real damage, warnings, recovery, fans and summons."""
from pathlib import Path
import sys
from test_phase16_shipyard_emulator import TAIL as SHIPYARD
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=SHIPYARD.split('    try:\n',1)[0]+r'''
    boss=syms['enemies'][0]
    def field(offset,n=2):return int.from_bytes(read(boss+offset,n),'big')
    def put(offset,value,n=2):write(boss+offset,value.to_bytes(n,'big'))
    def mode():return field(28,1)
    def xy():return struct.unpack('>hh',read(boss,4))
    def velocity():return struct.unpack('>hh',read(boss+12,4))
    def step():
        before=frames()
        until(lambda:frames()>before,'simulation-step',fps)
        assert frames()==before+1
    def shots():return [struct.unpack('>iiiiBBBB',read(syms['eshots'][0]+i*20,20)) for i in range(16)]
    def hit():
        x,y=xy()
        write(syms['pshots'][0],struct.pack('>iiiiBBBB',(x+20)<<6,(y+20)<<6,0,0,0,0,1,0))
        before=field(31,1);step();assert field(31,1)==before-1
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        write(syms['pendingLevel'][0],bytes([19]));press(1)
        until(lambda:state()==1 and u8('currentLevel')==19 and not u8('transitioning'),'phase16-entry')
        baseline=snapshot()
        def fresh(health=12):
            restore(baseline);isolate();pos(280,384)
            w16('hp',30000);w16('shieldTimer',60000);wait_camera()
            seed(0,14,160,352,health,0)
        fresh(13);run(12);step();assert not field(26)&0x8000
        hit();assert mode()==3 and field(26)&0x8000 and not field(42,1)
        start=frames()-1;position=xy();bright=dark=False;bright_frames=dark_frames=0
        while mode()==3:
            assert xy()==position and velocity()==(0,0) and not field(42,1)
            bright_frames=bright_frames+1 if field(38) else 0
            dark_frames=dark_frames+1 if not field(38) else 0
            if bright_frames>=2 and not bright:shot('phase2-transition-bright');bright=True
            if dark_frames>=2 and not dark:shot('phase2-transition-dark');dark=True
            step()
        assert bright and dark and frames()-start==4*fps//5
        check('real-hit-at12hp-triggers-once-with-stationary-local-flash',dict(duration_updates=frames()-start,bright=bright,dark=dark))
        until(lambda:mode()==1,'first-warning',fps*2)
        warnings=[];charges=[]
        for index in range(2):
            assert mode()==1 and bool(field(26)&0x4000)==bool(index)
            initial=xy();v=velocity();left=field(18)
            pos(112 if index==0 else 280,400);shot('phase2-warning-'+str(index+1))
            for _ in range(left):
                assert xy()==initial and velocity()==v;step()
            assert mode()==2;warnings.append(dict(updates=left,locked_velocity=v))
            begin=frames();shot('phase2-charge-'+str(index+1))
            while mode()==2:step()
            assert frames()-begin==fps//2
            assert mode()==(1 if index==0 else 4)
            charges.append(dict(updates=frames()-begin,position=xy()))
        assert warnings[0]['locked_velocity'][0]>0 and warnings[1]['locked_velocity'][0]<0
        check('two-reaimed-charges-each-with-locked-stationary-warning',dict(warnings=warnings,charges=charges))
        start=frames();position=xy();assert field(18)==6*fps//5
        hit();assert mode()==4 and field(31,1)==11 and not field(42,1)
        shot('phase2-vulnerable-recovery')
        while mode()==4:
            assert xy()==position and velocity()==(0,0) and not field(42,1);step()
        assert frames()-start==6*fps//5 and mode()==5
        check('exact1.2second-stationary-recovery-takes-real-projectile-damage',dict(updates=frames()-start,hp=field(31,1)))
        fans=[]
        for divisor in [2,6]:
            until(lambda:sum(s[6] for s in shots())==5,'fury-fan-'+str(divisor),fps*2)
            fan=[s for s in shots() if s[6]];vx,vy=fan[2][2:4]
            assert len(fan)==5 and all(s[4:6]==(4,13) for s in fan)
            for i,s in enumerate(fan):
                offset=i-2
                assert s[2:4]==(vx-int(vy*offset/divisor),vy+int(vx*offset/divisor))
            fans.append(dict(divisor=divisor,velocities=[s[2:4] for s in fan]));shot('phase2-fan-'+str(divisor));zeros('eshots');step()
        check('alternating-wide-and-narrow-complete-five-shot-fans',fans)
        put(24,12*fps-1);hit();assert not field(42,1)
        check('periodic-armor-stays-off-and-boss-remains-damageable',True)
        # Pending fan preserves its alternating state while the pool is full.
        put(28,5,1);put(18,3*fps);put(16,0);put(26,0x8000)
        for i in range(6):write(syms['eshots'][0]+i*20,struct.pack('>iiiiBBBB',64<<6,(352+i*8)<<6,0,0,1,10,1,0))
        step();assert sum(s[6] for s in shots())==6 and not field(26)&0x2000 and not field(16)
        write(syms['eshots'][0]+18,b'\0');step()
        assert sum(s[6] for s in shots())==10 and field(26)&0x2000
        check('fury-alternation-waits-for-whole-fan-without-skipping-pattern',True)
        fresh();put(24,10*fps-1);step()
        hunters=lambda:[i for i in range(16) if read(boss+i*46+44,1)[0] and read(boss+i*46+30,1)[0]==5]
        assert len(hunters())==2
        for _ in range(3):put(24,10*fps-1);step();assert len(hunters())==2
        write(boss+hunters()[0]*46+44,b'\0');put(24,10*fps-1);step();assert len(hunters())==2
        check('summons-never-exceed-two-live-hunters-and-refill-one-vacancy',True)
        # Recovery remains stationary even with player contact and separation.
        put(28,4,1);put(18,6*fps//5);put(12,0,4);position=xy();pos(position[0]+16,position[1]+16)
        step();assert mode()==4 and xy()==position and not field(20)
        check('contact-and-minion-separation-cannot-cancel-recovery',True)
        press(3);until(lambda:state()==2,'fury-pause');paused=(field(18),field(24),xy());run(fps*2)
        assert paused==(field(18),field(24),xy());shot('phase2-pause')
        press(0);until(lambda:state()==1,'fury-resume');assert field(26)&0x8000
        check('pause-freezes-fury-state-and-resumes-same-phase',True)
        # An actual retry starts at25HP with no latched phase2 flags.
        w16('hp',0);run(fps*4);assert state()==3
        run(fps);press(3);until(lambda:state() in (0,6) and not u8('transitioning'),'retry-story',fps*20)
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and not u8('transitioning'),'retry-prep',fps*20)
        press(1);until(lambda:state()==1 and not u8('transitioning'),'retry-boss',fps*20)
        assert field(31,1)==25 and not field(26)&0x8000;shot('phase2-reset-to-phase1')
        check('defeat-retry-clears-fury-and-restores25hp',True)
        fresh();step();put(31,200,1) # latch phase2, then protect the boss once for the load fixture
        w16('spawnTimer',0);before=writes;ordinary=True;start=frames();vb=u32('vtimer')
        most_hunters=most_shots=0;limits=[0,0,0];modes=set()
        for tick in range(30*fps):
            buttons.clear();buttons.update({1,[7,5,6,4][tick//(fps*2)%4]});run()
            assert state()==1 and not u16('sceneStreamFaults') and field(26)&0x8000 and not field(42,1)
            most_hunters=max(most_hunters,len(hunters()));most_shots=max(most_shots,sum(s[6] for s in shots()));modes.add(mode())
            assert most_hunters<=2 and most_shots<=10
            if tick%30==0:limits=[max(a,b) for a,b in zip(limits,sprite_limits())]
        buttons.clear();ordinary=False;assert writes==before and modes=={0,1,2,3,4,5}
        shot('phase2-moving-load')
        check('30second-moving-fury-load-with-two-hunters-and-full-shot-pools',dict(
              seconds=30,game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),
              max_hunters=most_hunters,max_enemy_shots=most_shots,sprite_limits=limits,
              modes=sorted(modes),cache_peak=u16('sceneStreamPeak'),ram_writes_during_load=0))
        report['scope']='Boss phase2 real-ROM isolated probes: real damage threshold, local flash, double locked charges, vulnerable recovery, wide/narrow complete fans, no armor, two hunters, contact, pause and retry. RAM prepares isolated situations; production AI/physics/damage execute.'
        report['passed']=True;save();print('PASS boss phase2',report['region'],report['romSHA256'])
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL-boss-phase2');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'boss_phase2','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
