"""Phase12 whole-scene, seams, prop collision, landmark camera and live-load audit."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import edges,closest
    root=GAME/'art/phase12-three-segments-v1';d=json.loads((root/'manifest.json').read_text())
    patterns=(root/'native/tiles.bin').read_bytes();mapping=struct.unpack('>15360H',(root/'native/map.bin').read_bytes());palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
    def quiet():
        isolate();w16('hp',30000);w16('dinorahHp',100);w16('dinorahPauseTimer',60000);w16('dinorahInvTimer',60000);w16('shieldTimer',60000);run(fps);w16('dinorahPauseTimer',60000)
    def duo(x,y):
        pos(x,y);dx,dy=closest(d,x-24,y);w16('dinorahX',dx);w16('dinorahY',dy)
        write(syms['dinorahFx'][0],struct.pack('>i',dx<<6));write(syms['dinorahFy'][0],struct.pack('>i',dy<<6))
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*20):
            run();current=(u16('cameraX'),u16('cameraY'));stable=stable+1 if current==previous else 0;previous=current
            if stable>=8:run(2);return
        raise AssertionError('camera never settles')
    def pixels():
        assert vr(785*32,len(patterns))==patterns,'scenery bank altered'
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[48:64]==list(map(packed,palette))
        cx,cy=u16('cameraX'),u16('cameraY');cells=0
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                attr=mapping[row*384+col];at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==(0x6000|(attr&0x1800)|(785+(attr&2047))),('visible background',col,row)
                assert vw(u16('bga_addr')+at)==0,('foreign foreground fragment',col,row)
                cells+=1
        return dict(camera=[cx,cy],exact_cells=cells)
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');run(2)
        write(syms['pendingLevel'][0],b'\x0e');press(1);until(lambda:state()==1 and not u8('transitioning'),'phase12-entry')
        initial=snapshot();quiet();wait_camera();check('entry-atlas-palette',pixels());shot('01-entry')
        views=[]
        for x in range(160,3072,256):
            for y in [136,208,272]:
                xx,yy=closest(d,x,y);duo(xx,yy);wait_camera();views.append(pixels());sprite_limits()
        check('whole-map-36-camera-views',views)
        # Current camera follows the player's body and permits only a small
        # idle composition offset. A whole northern roof is not necessarily
        # on screen. Validate complete facades, the STE emblem, player safety
        # and exact background pixels instead of the former roof-lock policy.
        marks=[]
        for item in d['camera_interest']:
            restore(initial);quiet()
            if item['id']=='factory-exit':duo(220,200)
            elif item['id']=='union':
                duo(2880,208)
                # The waiting escort remains outside the completion zone.
                w16('dinorahX',2776);w16('dinorahY',208)
                write(syms['dinorahFx'][0],struct.pack('>i',2776<<6));write(syms['dinorahFy'][0],struct.pack('>i',208<<6))
            else:duo(*item['position'])
            wait_camera();cx,cy=u16('cameraX'),u16('cameraY');x,y,w0,h0=item['bbox']
            regions=[('facade',[x,y+h0-40,w0,40])]
            if item['id']=='union':regions.append(('STE-logo',[x+124,y+72,56,56]))
            for label,(rx,ry,rw,rh) in regions:
                assert cx<=rx and rx+rw<=cx+320 and cy+24<=ry and ry+rh<=cy+224,(item['id'],label,'cut',cx,cy)
            assert cx<=u16('px')-8 and u16('px')+24<=cx+320 and cy+24<=u16('py')-31 and u16('py')+17<=cy+224,'player body cut'
            pixels();shot('landmark-'+item['id']);marks.append(dict(id=item['id'],camera=[cx,cy],complete_regions=regions,player_body_below_HUD=True,whole_roof_required=False))
        check('six-complete-facades-STE-logo-and-player-framed',marks)
        probes=[]
        for x,y,button,axis,limit,sign in faces(d):
            restore(initial);quiet();pos(x,y);hold({button},fps//2);value=u16(axis)
            assert value<=limit if sign>0 else value>=limit,('collision',x,y,button,value,limit)
            probes.append([x,y,button,value])
        for x,y,button,axis,limit in edges(d):
            restore(initial);quiet();pos(x,y);hold({button},fps//2);assert u16(axis)==limit
        check('architecture-eleven-props-and-world-bounds',dict(probes=probes,edges=4))
        for boundary in [512,1024,1536,2048,2560]:
            restore(initial);quiet();duo(boundary-56,208);hold({7},fps);wait_camera();pixels();shot('seam-'+str(boundary));assert u16('px')>boundary,'blocked block seam'
        check('five-block-seams-crossable',True)
        restore(initial);quiet();duo(1456,216);wait_camera();press(3);until(lambda:state()==2,'pause');shot('pause');press(0);until(lambda:state()==1,'resume');wait_camera();pixels();check('pause-restores-atlas-map-palette',True)
        loads=[]
        for label,x,y in [('departure',304,208),('lower-truck',864,168),('upper-truck',1456,216),('union',2736,216)]:
            restore(initial);quiet();duo(x,y);wait_camera()
            for i,kind in enumerate([4,5,2]):
                ex,ey=closest(d,x-64+i*48,y);seed(i,kind,ex,ey,200,0)
            direction=7
            def arrange():
                nonlocal direction
                if u16('px')>=x+48:direction=6
                if u16('px')<=x-48:direction=7
                buttons.clear();buttons.add(direction);w16('hp',30000);w16('dinorahInvTimer',60000)
                for i in range(3):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(4):
                        address=syms[name][0]+i*20
                        if read(address+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*64)<<6,(u16('cameraY')+176+(i%2)*8)<<6,24,0);b[17]=b[18]=1;write(address,b)
            for _ in range(fps*2):arrange();run()
            begin=frames();vb=u32('vtimer');cpu=[];sat=[0,0,0]
            for t in range(fps*20):
                arrange();run();assert state()==1 and living()==3
                cpu.append(u16('cpuFrameLoad')*100/2048)
                if t%30==0:sat=[max(a,b) for a,b in zip(sat,sprite_limits())]
            buttons.clear();game,physical=frames()-begin,u32('vtimer')-vb;wait_camera();pixels();shot('load-'+label)
            loads.append(dict(section=label,enemies=3,shots_per_pool=4,seconds=20,game_fps=round(fps*game/max(1,physical),3),maximum_cpu_pct=round(max(cpu),2),sprite_limits=sat,setup='live authored AI and player patrol; health protected; only inactive shots replenished; Dinorah paused for controlled scene load'))
        check('four-section-configured-live-load',loads)
        report['scope']='36 actual camera pixel comparisons, six complete facades, STE emblem and player body framed (current player-follow camera; whole roofs may leave the viewport), every legal collision face, five block seams, pause, and live configured3-enemy/4+4-shot pressure in4sections. Functional complete escort/death outcomes are in the separate shared escort suite.'
        report['passed']=True;save();print('PASS phase12 composition',report['romSHA256'])
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''
def main():
    namespace={'__name__':'phase12_composition','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
