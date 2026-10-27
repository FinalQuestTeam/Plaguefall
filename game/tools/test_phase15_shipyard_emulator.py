"""Phase15 native antenna, shared powered equipment, defense, ignition and cache."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import closest,path,faces,edges
    root=GAME/'art/phase15-shipyard-v2';d=json.loads((root/'manifest.json').read_text())
    cache=d['memory']['cache_tiles'];launch=syms['campaignLaunch'][0]
    maps={k:struct.unpack('>4608H',(root/f'native/{k}-map.bin').read_bytes()) for k in ['normal','fire']}
    banks={k:(root/f'native/{k}-tiles.bin').read_bytes() for k in ['normal','fire']}
    generator=(GAME/'art/phase14-shipyard-v2/native/generator-tiles.bin').read_bytes()
    generator_map=struct.unpack('>216H',(GAME/'art/phase14-shipyard-v2/native/generator-map.bin').read_bytes())
    radio=(root/'native/radio-tiles.bin').read_bytes();radio_map=struct.unpack('>288H',(root/'native/radio-map.bin').read_bytes())
    palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
    def left():return int.from_bytes(read(launch+10,2),'big')
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*20):
            run();now=(u16('cameraX'),u16('cameraY'));stable=stable+1 if previous==now else 0;previous=now
            if stable>=12:run(2);return
        raise AssertionError('phase15 camera never settles')
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
                    if expected[1]==1:assert overlay&0x8000,('radio foreground plane',col,row)
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
    def presentations():return read(syms['launchPresentation'][0],1)[0]
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');baseline=snapshot()
        write(syms['pendingLevel'][0],bytes([18]));press(1)
        until(lambda:state()==1 and u8('currentLevel')==18 and not u8('transitioning'),'phase15-entry')
        isolate();w16('shieldTimer',60000);wait_camera();initial=snapshot()
        assert 118*fps<left()<=120*fps and read(launch+14,1)[0]==31
        assert (u16('npcX')+12,u16('npcY')+12)==tuple(d['target'])
        shot('15-entry');check('shared-powered-equipment-native-entry',pixels())
        views=[]
        for x in [48,160,280,448]:
            for y in [128,192,256,320,384,448,496]:
                pos(*closest(d,x,y));wait_camera();views.append(pixels());sprite_limits();shot(f'15-view-{x}-{y}')
        check('28-real-native-camera-views',views)
        restore(initial);isolate();pos(384,336);wait_camera();poses=[]
        for frame in range(6):
            for i in range(5):write(syms['objectiveVisuals'][0]+i*12+7,bytes([3,6]))
            write(syms['objectiveVisuals'][0]+5*12+7,bytes([frame,6]))
            dummy=bytearray(12);dummy[6]=2;dummy[7]=255;dummy[9]=1;write(syms['objectiveVisuals'][0]+6*12,dummy)
            run(3);poses.append(pixels());shot('15-radio-pose-'+str(frame))
        check('six-radio-states-native-pixels',poses)
        restore(initial);isolate();before=left();start=frames();run(fps*3)
        assert before-left()==frames()-start
        check('defense-timer-uses-real-game-updates',dict(elapsed_updates=frames()-start,timer_decrement=before-left()))
        restore(initial);isolate();before=writes;ordinary=True
        for p in [(48,136),(432,136),(440,248),(440,400),(320,496),(48,496),(48,336),(184,352),(320,352),(48,232)]:navigate(*p)
        ordinary=False;assert writes==before;wait_camera();check('controller-traversal-without-ram-writes',pixels());shot('15-controller-traversal')
        contacts=[]
        for x,y,key,axis,limit,direction in faces(d):
            restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps)
            assert u16(axis)==limit,('solid face',x,y,key,axis,u16(axis),limit)
            contacts.append([x,y,key,u16(axis)])
        for x,y,key,axis,limit in edges(d):
            restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps);assert u16(axis)==limit
        check('antenna-generator-battery-faces-and-four-bounds',contacts)
        hits=[]
        a,c,w,h=d['protected_station_footprint']
        for edge,x,y in [('west',a-16,c),('east',a+w,c),('north',a,c-16),('south',a,c+h)]:
            restore(initial);isolate();seed(0,0,x,y,20,60000);before=u16('npcHp');run(2)
            assert u16('npcHp')==before-12,('protected antenna exterior contact',edge,u16('npcHp'))
            hits.append(dict(edge=edge,damage=12))
        check('antenna-damage-from-all-four-outside-edges',hits)
        # Walking through the elevated aerial must neither block nor hurt it.
        restore(initial);isolate();pos(216,272);wait_camera();before=u16('npcHp');hold({7},fps)
        assert u16('px')>280 and u16('npcHp')==before
        shot('15-pass-through-mast');check('mast-does-not-block-player',dict(x=u16('px'),hp=before))
        for x,y in [(248,264),(248,280),(216,288),(280,288),(200,264)]:
            restore(initial);isolate();seed(0,0,x,y,20,60000);before=u16('npcHp');run(2)
            assert u16('npcHp')==before,('mast/old console air received damage',x,y)
        check('mast-and-removed-console-never-receive-damage',True)
        # Read actor priority on both sides of the high-priority radio plane.
        depth=[]
        for x,y,front in [(248,280,False),(248,320,True)]:
            restore(initial);isolate();pos(x,y);wait_camera();run(2)
            attr=vw(u16('slist_addr')+4)
            assert bool(attr&0x8000)==front,('radio/player depth',x,y,attr)
            depth.append(dict(position=[x,y],foreground=front));shot('15-core-'+('front' if front else 'behind'))
        check('actor-depth-under-mast-and-in-front-of-core',depth)
        restore(initial);isolate();seed(0,0,a-16,c,20,60000);run(2)
        flashes=set()
        for _ in range(fps//2+3):
            cx,cy=d['antenna_position'];row=(cy+48)//8;col=(cx+16)//8
            flashes.add((vw(u16('bga_addr')+((row&31)*64+(col&63))*2)>>13)&3)
            run()
        assert flashes=={0,1},('core local hit flash',flashes)
        check('core-flashes-locally-after-damage',sorted(flashes));shot('15-core-damaged')
        restore(initial);isolate();press(3);until(lambda:state()==2,'pause');before=left();run(fps*2);assert left()==before;shot('15-pause')
        press(0);until(lambda:state()==1,'resume');wait_camera();check('pause-preserves-defense-and-native-cache',pixels())
        restore(initial);isolate();write(launch+10,struct.pack('>H',80*fps+1))
        seed(0,5,400,400,200,60000)
        projectile=bytearray(20);struct.pack_into('>iiii',projectile,0,96<<6,360<<6,16,0);projectile[17]=projectile[18]=1;write(syms['pshots'][0],projectile)
        until(lambda:presentations()==1 and u16('cameraY')==24,'ignition-focus',fps*8)
        run(3);frozen=(left(),u16('npcHp'),u16('px'),u16('py'),read(syms['enemies'][0],46),read(syms['pshots'][0],19))
        run(fps//4);assert frozen==(left(),u16('npcHp'),u16('px'),u16('py'),read(syms['enemies'][0],46),read(syms['pshots'][0],19))
        check('ignition-pauses-live-combat',pixels('fire'));shot('15-ignition-focus')
        until(lambda:presentations()==0,'ignition-return',fps*8);isolate();wait_camera();check('ignition-preserves-antenna-floor-and-equipment',pixels('fire'));shot('15-ignition-return')
        # Retry after ignition must use the original normal scene.
        w16('npcHp',0);run(fps*4);assert state()==3 and u8('resultActive') and u32('card');shot('15-defeat')
        run(fps);press(3)
        until(lambda:state() in (0,6) and not u8('transitioning'),'retry-story-or-prep',fps*20)
        if state()==6:run(fps);press(3)
        until(lambda:state()==0 and u8('pendingLevel')==18 and not u8('transitioning'),'retry-prep',fps*20)
        press(1);until(lambda:state()==1 and not u8('transitioning'),'retry15',fps*20);isolate();wait_camera()
        assert not u8('arenaDamaged') and left()>118*fps;check('retry-resets-ignition-and-timer',pixels())
        restore(initial);isolate();before=writes;ordinary=True
        until(lambda:state()==4,'full120second-defense',fps*145);ordinary=False
        assert writes==before and left()==0;run(fps*3);assert u8('resultActive') and u32('card');shot('15-complete')
        check('full120second-controller-free-hold-and-result',dict(seconds=120,ram_writes_during_defense=0,complete=True))
        run(fps);press(1)
        until(lambda:state() in (5,6) and not u8('transitioning'),'victory-story-or-map',fps*20)
        if state()==6:run(fps);press(3)
        until(lambda:state()==5 and u8('pendingLevel')==19 and not u8('transitioning'),'continue16');shot('15-continue16');check('continues-to16',True)
        loads=[]
        for section,x,y in [('engines',160,176),('antenna',384,336),('battery',352,464)]:
            restore(initial);isolate();pos(x,y);w16('hp',30000);w16('shieldTimer',60000);wait_camera()
            for i,kind in enumerate([4,5,2]):
                xx,yy=closest(d,80+i*128,y);seed(i,kind,xx,yy,200,60000)
            start=frames();vb=u32('vtimer');maximum=[0,0,0]
            for tick in range(fps*20):
                buttons.clear();buttons.update({1,[7,5,6,4][tick//(fps*2)%4]});w16('hp',30000);w16('npcHp',100)
                for i in range(3):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for pool in ['pshots','eshots']:
                    for i in range(4):
                        address=syms[pool][0]+i*20
                        if read(address+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+32+i*64)<<6,(u16('cameraY')+168+i%2*8)<<6,24,0);b[17]=b[18]=1;write(address,b)
                run();assert state()==1 and not u16('sceneStreamFaults')
                if tick%30==0:maximum=[max(a,b) for a,b in zip(maximum,sprite_limits())]
            buttons.clear();measured=round(fps*(frames()-start)/max(1,u32('vtimer')-vb),3);wait_camera();pixels();shot('15-load-'+section)
            loads.append(dict(section=section,seconds=20,game_fps=measured,cache_peak=u16('sceneStreamPeak'),cache_faults=u16('sceneStreamFaults'),sprite_limits=maximum))
        check('moving-three-enemy-four-plus-four-shot-load',loads)
        report['scope']='Phase15:shared phase14 floor/limits/generators, native antenna and6radio poses,28pixel-exact camera audits, controller traversal, collision/exterior damage, pause, ignition with frozen combat, normal retry, full120s defense/result/continue16 and three moving load sectors.'
        report['passed']=True;save();print('PASS phase15 shipyard',report['region'],report['romSHA256'])
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL-phase15');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'phase15_shipyard','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
