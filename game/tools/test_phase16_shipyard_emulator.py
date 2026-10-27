"""Phase16 shared shipyard, native windows, streaming, collisions and boss combat."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import closest,path,faces,edges
    root=GAME/'art/phase16-shipyard-v2';d=json.loads((root/'manifest.json').read_text())
    cache=d['memory']['cache_tiles'];launch=syms['campaignLaunch'][0]
    maps={'normal':struct.unpack('>4608H',(root/'native/map.bin').read_bytes())}
    banks={'normal':(root/'native/tiles.bin').read_bytes()}
    generator=(GAME/'art/phase14-shipyard-v2/native/generator-tiles.bin').read_bytes()
    generator_map=struct.unpack('>216H',(GAME/'art/phase14-shipyard-v2/native/generator-map.bin').read_bytes())
    radio_root=GAME/'art/phase15-shipyard-v2/native'
    radio=(radio_root/'radio-tiles.bin').read_bytes();radio_map=struct.unpack('>288H',(radio_root/'radio-map.bin').read_bytes())
    palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*20):
            run();now=(u16('cameraX'),u16('cameraY'));stable=stable+1 if previous==now else 0;previous=now
            if stable>=12:run(2);return
        raise AssertionError('phase16 camera never settles')
    def pixels(kind='normal'):
        for _ in range(10):
            poses=tuple(read(syms['objectiveVisuals'][0]+i*12+7,1)[0] for i in range(6));run(2)
            if poses==tuple(read(syms['objectiveVisuals'][0]+i*12+7,1)[0] for i in range(6)):break
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=cache
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[48:64]==list(map(packed,palette))
        gb=int.from_bytes(read(syms['objectiveArtBases'][0]+2,2),'big');rb=int.from_bytes(read(syms['objectiveArtBases'][0]+14,2),'big')
        assert gb==785+cache and rb==gb+len(generator)//32
        assert vr(gb*32,len(generator))==generator and vr(rb*32,len(radio))==radio
        objects=[]
        for i in range(6):
            b=read(syms['objectiveVisuals'][0]+i*12,12);x,y=struct.unpack('>hh',b[:4]);height=48 if i<5 else 64
            assert b[6]==(1 if i<5 else 7) and b[9] and b[10]
            assert [x,y]==(d['machines'][i] if i<5 else d['radio'])
            objects.append(((x-24)//8,(y-height+8)//8,height//8,b[7],generator if i<5 else radio,generator_map if i<5 else radio_map,3 if i<5 else 1))
        cx,cy=u16('cameraX'),u16('cameraY');loc=u32('location')&65535;used=set();cells=0;overlay_cells=0
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=maps[kind][row*64+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<cache
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('BG_B map',kind,col,row)
                assert vr((785+slot)*32,32)==banks[kind][source*32:(source+1)*32],('BG_B native pixels',kind,col,row)
                expected=None
                for x,y,rows,frame,raw,indices,pal in objects:
                    if x<=col<x+6 and y<=row<y+rows:
                        tile=indices[frame*6*rows+(col-x)*rows+row-y];ink=raw[tile*32:(tile+1)*32]
                        if any(ink):expected=(ink,pal)
                overlay=vw(u16('bga_addr')+at)
                if expected:
                    assert overlay&0x6000==expected[1]<<13 and vr((overlay&2047)*32,32)==expected[0],('native equipment overlay',col,row)
                    if expected[1]==1:assert overlay&0x8000
                    overlay_cells+=1
                else:assert overlay==0,('foreign BG_A fragment',col,row,overlay)
                used.add(slot);cells+=1
        return dict(kind=kind,camera=[cx,cy],cells=cells,overlay_cells=overlay_cells,visible_patterns=len(used),cache_peak=u16('sceneStreamPeak'),cache_faults=u16('sceneStreamFaults'))
    def navigate(tx,ty):
        sx,sy=u16('px'),u16('py')
        for x,y in path(d,(round(sx/8)*8,round(sy/8)*8),closest(d,tx,ty),4):
            for _ in range(fps*15):
                dx,dy=x-u16('px'),y-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:break
                buttons.clear()
                if abs(dx)>2:buttons.add(7 if dx>0 else 6)
                if abs(dy)>2:buttons.add(5 if dy>0 else 4)
                run();assert state()==1
            else:raise AssertionError(('navigation stalled',x,y,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');baseline=snapshot()
        write(syms['pendingLevel'][0],bytes([19]));press(1)
        until(lambda:state()==1 and u8('currentLevel')==19 and not u8('transitioning'),'phase16-entry')
        assert [u16(n) for n in ['arenaMinX','arenaMinY','arenaMaxX','arenaMaxY']]==d['bounds']
        bosses=lambda:[i for i in range(16) if read(syms['enemies'][0]+i*46+44,1)[0] and read(syms['enemies'][0]+i*46+30,1)[0]==14]
        assert len(bosses())==1
        combat=snapshot();shot('16-boss-entry');check('original-boss-spawns-in-shared-room',True)
        # Isolate the real boss firing state in clear floor. RAM only prepares
        # time/position/pool occupancy; the production AI creates every bullet.
        def enemy_shots():
            return [struct.unpack('>iiiiBBBB',read(syms['eshots'][0]+i*20,20)) for i in range(16)]
        restore(combat);isolate();seed(0,14,160,352,25,0);pos(360,384);w16('shieldTimer',60000)
        write(syms['enemies'][0]+24,struct.pack('>H',4*fps-1));ready=snapshot()
        until(lambda:sum(s[6] for s in enemy_shots())==5,'complete-five-shot-fan',fps)
        first=[s for s in enemy_shots() if s[6]]
        assert len(first)==5 and all(s[4:6]==(4,13) for s in first)
        assert len(set(s[2:4] for s in first))==5
        assert all(first[i][2]+first[4-i][2]==2*first[2][2] and first[i][3]+first[4-i][3]==2*first[2][3] for i in [0,1])
        check('five-distinct-symmetric-boss-projectiles',dict(count=5,damage=13,velocities=[s[2:4] for s in first]))
        # Keep the first real volley in flight as a pool-occupancy fixture;
        # otherwise its outer bullets can hit the room before the next salvo.
        for i in range(5):write(syms['eshots'][0]+i*20+8,bytes(8))
        until(lambda:sum(s[6] for s in enemy_shots())==10,'two-complete-fans-coexist',fps*2)
        assert all(s[4:6]==(4,13) for s in enemy_shots() if s[6])
        sprite_limits();shot('16-two-five-shot-fans');check('two-five-shot-fans-fit-without-overwrite',True)
        restore(ready)
        for i in range(6):
            write(syms['eshots'][0]+i*20,struct.pack('>iiiiBBBB',64<<6,(352+i*8)<<6,0,0,1,10,1,0))
        write(syms['enemies'][0]+16,b'\0\0')
        run(6)
        assert sum(s[6] for s in enemy_shots())==6 and int.from_bytes(read(syms['enemies'][0]+16,2),'big')==0,('partial-pool wait',enemy_shots(),read(syms['enemies'][0]+16,2))
        old=[read(syms['eshots'][0]+i*20,19) for i in range(1,6)]
        write(syms['eshots'][0]+18,b'\0')
        until(lambda:sum(s[6] for s in enemy_shots())==10,'retry-whole-fan-on-five-free-slots',fps)
        assert old==[read(syms['eshots'][0]+i*20,19) for i in range(1,6)]
        assert sum(s[6] and s[4]==4 for s in enemy_shots())==5
        check('full-pool-waits-and-retries-without-clipped-fan-or-erasing-shots',True)
        restore(ready);isolate();write(syms['shotPower'][0],b'\x05');buttons.add(1);player_peak=0
        for _ in range(fps):
            run();player=[struct.unpack('>iiiiBBBB',read(syms['pshots'][0]+i*20,20)) for i in range(16)]
            player_peak=max(player_peak,sum(s[6] for s in player))
            assert not any(s[6] for s in player[4:])
        buttons.clear();assert player_peak==4,('player peak',player_peak)
        check('player-retains-four-shot-pool',True)
        restore(combat)
        isolate();w16('shieldTimer',60000);wait_camera();initial=snapshot()
        assert read(launch+14,1)[0]==31
        check('shared-powered-native-equipment-entry',pixels());shot('16-entry')
        views=[]
        for x in [48,160,280,448]:
            for y in [128,192,256,320,384,448,496]:
                pos(*closest(d,x,y));wait_camera();views.append(pixels());sprite_limits();shot(f'16-view-{x}-{y}')
        check('28-real-native-camera-views',views)
        restore(initial);isolate();before=writes;ordinary=True
        for p in [(48,136),(432,136),(440,248),(440,400),(320,496),(48,496),(48,336),(184,352),(320,352),(48,232)]:navigate(*p)
        ordinary=False;assert writes==before;wait_camera();check('controller-traversal-without-ram-writes',pixels());shot('16-controller-traversal')
        contacts=[]
        for x,y,key,axis,limit,direction in faces(d):
            restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps)
            assert u16(axis)==limit,('solid face',x,y,key,axis,u16(axis),limit)
            contacts.append([x,y,key,u16(axis)])
        for x,y,key,axis,limit in edges(d):
            restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps);assert u16(axis)==limit
        check('shared-equipment-faces-and-four-bounds',contacts)
        restore(initial);isolate();press(3);until(lambda:state()==2,'pause');shot('16-pause')
        press(0);until(lambda:state()==1,'resume');wait_camera();check('pause-restores-native-windows-and-cache',pixels())
        w16('hp',0);run(fps*4);assert state()==3 and u8('resultActive') and u32('card');shot('16-defeat')
        run(fps);press(3)
        until(lambda:state() in (0,6) and not u8('transitioning'),'retry-story-or-prep',fps*20)
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and u8('pendingLevel')==19 and not u8('transitioning'),'retry-prep',fps*20)
        press(1);until(lambda:state()==1 and not u8('transitioning'),'retry16',fps*20)
        assert len(bosses())==1;isolate();wait_camera();check('retry-keeps-new-windows-and-respawns-boss',pixels())
        # Original25HP, real two-phase AI; protect the player once, then use
        # ordinary controller input through threshold, transition and victory.
        restore(combat);w16('hp',30000);w16('shieldTimer',60000)
        before=writes;ordinary=True;start=frames();vb=u32('vtimer');minimum=25;peak=0;fury_seen=False
        for tick in range(fps*120):
            active=bosses()
            if not active or state()!=1:break
            address=syms['enemies'][0]+active[0]*46
            bx,by=struct.unpack('>hh',read(address,4));minimum=min(minimum,read(address+31,1)[0])
            fury_seen|=bool(int.from_bytes(read(address+26,2),'big')&0x8000)
            dx=bx+24-u16('px')-8;dy=by+24-u16('py')-8
            buttons.clear();buttons.add(1)
            if abs(dx)>20:buttons.add(7 if dx>0 else 6)
            if abs(dy)>20:buttons.add(5 if dy>0 else 4)
            run();assert not u16('sceneStreamFaults');peak=max(peak,u16('sceneStreamPeak'))
        buttons.clear();ordinary=False;assert writes==before
        assert minimum<25 and u8('bossDefeated') and fury_seen,('controller did not defeat two-phase boss',minimum,fury_seen)
        check('controller-boss-combat',dict(minimum_boss_hp=minimum,defeated=bool(u8('bossDefeated')),
              game_fps=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3),cache_peak=peak,phase2_seen=fury_seen,ram_writes_during_combat=0))
        run(fps);shot('16-boss-combat-result')
        report['scope']='Phase16: complete five-shot boss fans, two coexisting volleys, wait/retry on insufficient slots without erasing live shots; phase15 room/equipment/collisions;28pixel-exact camera views; controller traversal, collisions, pause, defeat/retry and boss victory.'
        report['passed']=True;save();print('PASS phase16 shipyard',report['region'],report['romSHA256'])
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL-phase16');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'phase16_shipyard','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
