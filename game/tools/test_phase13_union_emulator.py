"""Phase13A/B: detailed room, visible tile cache, controller traversal and result."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import closest,path,faces,edges,validate
    root=GAME/'art/phase13-union-v2';d=json.loads((root/'manifest.json').read_text())
    cols,rows=[n//8 for n in d['size']]
    patterns=(root/'native/tiles.bin').read_bytes();palette=struct.unpack('>16H',(root/'native/palette.bin').read_bytes())
    def canonical_prop(label):
        # Existing escort reservation, canonical actor palette, exact ROM bytes.
        sat=u16('slist_addr');found=None;index=0
        for _ in range(80):
            at=sat+index*8;attr=vw(at+4)
            x=(vw(at+6)&511)-128+u16('cameraX');y=(vw(at)&511)-128+u16('cameraY')
            if attr&0x6000==0x4000 and [x,y]==([300,76] if label=='13A' else [304,92]):found=attr&2047;break
            index=vw(at+2)&127
            if not index:break
        assert found is not None,('canonical prop missing',label)
        if label=='13A':
            data=(GAME/'art/cangaco-parceira-iso60-v1/runtime/frames.bin').read_bytes()[4*6*768:4*6*768+512]
        else:data=(root/'native/headgear.bin').read_bytes()
        assert vr(found*32,len(data))==data,'canonical prop pixels changed'
        pal=struct.unpack('>16H',(GAME/'art/cangaco-parceira-iso60-v1/runtime/palette.bin').read_bytes())
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[32:48]==list(map(packed,pal)),'actor palette changed'
        return dict(canonical_pixels_exact=True,palette='original PAL2',extra_vram_bytes=0,prop_tiles=len(data)//32)
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*20):
            run();now=(u16('cameraX'),u16('cameraY'));stable=stable+1 if now==previous else 0;previous=now
            if stable>=12:run(2);return
        raise AssertionError('camera never settles')
    def pixels(ids):
        assert u16('sceneStreamFaults')==0 and u16('sceneStreamPeak')<=640,'cache fault'
        packed=lambda c:(c>>1&7)|((c>>5&7)<<3)|((c>>9&7)<<6)
        assert list((C.c_uint16*64).in_dll(core,'cram'))[48:64]==list(map(packed,palette))
        loc=u32('location')&65535;cx,cy=u16('cameraX'),u16('cameraY');used=set();cells=0
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                source=ids[row*cols+col];slot=int.from_bytes(read(loc+source*2,2),'big');assert slot<640
                at=((row&31)*64+(col&63))*2
                assert vw(u16('bgb_addr')+at)==0x6000+785+slot,('map mismatch',col,row)
                assert vr((785+slot)*32,32)==patterns[source*32:(source+1)*32],('pixels mismatch',col,row)
                assert vw(u16('bga_addr')+at)==0,('foreign foreground fragment',col,row)
                used.add(slot);cells+=1
        return dict(camera=[cx,cy],cells=cells,visible_patterns=len(used),cache_peak=u16('sceneStreamPeak'),cache_faults=u16('sceneStreamFaults'))
    def navigate(x,y):
        x,y=closest(d,x,y);sx,sy=u16('px'),u16('py')
        route=path(d,(round(sx/8)*8,round(sy/8)*8),(x,y),4)
        for tx,ty in route:
            for _ in range(fps*10):
                dx,dy=tx-u16('px'),ty-u16('py')
                if abs(dx)<=2 and abs(dy)<=2:break
                buttons.clear()
                if abs(dx)>2:buttons.add(7 if dx>0 else 6)
                if abs(dy)>2:buttons.add(5 if dy>0 else 4)
                run();assert state()==1
            else:raise AssertionError(('navigation stuck',tx,ty,u16('px'),u16('py')))
        buttons.clear()
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');baseline=snapshot()
        for label,node,mapname,target in [('13A',15,'alive',30),('13B',16,'dead',45)]:
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'room-entry');isolate();w16('shieldTimer',60000);w16('hp',100);wait_camera()
            ids=struct.unpack('>'+str(cols*rows)+'H',(root/f'native/{mapname}.bin').read_bytes());initial=snapshot()
            shot(label+'-entry');check(label+'-native-entry',pixels(ids));check(label+'-canonical-prop',canonical_prop(label));assert not u16('dinorahHp'),'escort actor unexpectedly active'
            check(label+'-connected-floor',validate(dict(d,points=[])))
            poses=[]
            for x in [32,160,280,456]:
                for y in [160,216,280,344,408,472]:
                    pos(*closest(d,x,y));wait_camera();poses.append(pixels(ids));sprite_limits();shot(label+f'-view-{x}-{y}')
            check(label+'-whole-room24-views',poses)
            restore(initial);isolate();w16('shieldTimer',60000);before=writes;ordinary=True
            for point in [(48,168),(440,168),(440,280),(328,344),(440,448),(280,464),(48,464),(48,280),(192,368),(280,168)]:navigate(*point)
            ordinary=False;assert writes==before;wait_camera();check(label+'-controller-navigation',dict(ramWritesDuringTraversal=False,final_position=[u16('px'),u16('py')],pixels=pixels(ids)))
            press(3);until(lambda:state()==2,'pause');shot(label+'-pause');press(0);until(lambda:state()==1,'resume');wait_camera()
            check(label+'-pause-resumes-exact-cache',pixels(ids))
            check(label+'-canonical-prop-after-pause',canonical_prop(label))
            contacts=[]
            for x,y,key,axis,limit,direction in faces(d):
                restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps)
                assert u16(axis)==limit,('bench collision',label,x,y,key,axis,u16(axis),limit)
                contacts.append(dict(face=[x,y,key],axis=axis,stopped=u16(axis)))
            for x,y,key,axis,limit in edges(d):
                restore(initial);isolate();pos(x,y);wait_camera();hold({key},fps)
                assert u16(axis)==limit,('room boundary',label,key,axis,u16(axis),limit)
                contacts.append(dict(boundary=key,axis=axis,stopped=u16(axis)))
            check(label+'-bench-faces-and-room-boundaries',contacts)
            # Moving pressure test keeps live authored AI and trajectories,
            # replenishes only inactive shots and follows real controller input.
            restore(initial);isolate();w16('hp',30000);w16('shieldTimer',60000)
            for i,kind in enumerate([4,5,2,4,5]):seed(i,kind,48+i*80,168,200,0)
            directions=[7,5,6,4];begin=frames();vb=u32('vtimer');maximum=[0,0,0];peak=0
            for tick in range(fps*20):
                buttons.clear();buttons.add(directions[(tick//(fps*2))%4]);w16('hp',30000)
                for i in range(5):write(syms['enemies'][0]+i*46+31,b'\xc8')
                for name in ['pshots','eshots']:
                    for i in range(6):
                        address=syms[name][0]+i*20
                        if read(address+18,1)[0]:continue
                        b=bytearray(20);struct.pack_into('>iiii',b,0,(u16('cameraX')+24+i*48)<<6,(u16('cameraY')+176+i%2*8)<<6,24,0);b[17]=b[18]=1;write(address,b)
                run();assert state()==1 and living()==5;assert not u16('sceneStreamFaults');peak=max(peak,u16('sceneStreamPeak'))
                if tick%30==0:maximum=[max(a,b) for a,b in zip(maximum,sprite_limits())]
            buttons.clear();measured=round(fps*(frames()-begin)/max(1,u32('vtimer')-vb),3);wait_camera();pixels(ids);shot(label+'-moving-load')
            check(label+'-moving-five-enemy-six-plus-six-shot-load',dict(seconds=20,game_fps=measured,cache_peak=peak,cache_faults=u16('sceneStreamFaults'),sprite_limits=maximum,setup='live AI/controller patrol; health protected; only inactive shot slots replenished'))
            restore(initial);isolate();w16('kills',target-1);run(fps//2);assert state()==1
            w16('kills',target);run(fps*3);assert state()==4
            assert u8('resultActive') and u32('card')!=0,('result card allocation/render failed',u16('resultCaptureFault'),u16('resultCaptureTileCount'))
            shot(label+'-objective-complete');check(label+'-kill-target-and-result-card',dict(target=target,resultCardActive=True))
            run(fps);press(1);until(lambda:state()==5 and u8('pendingLevel')==17 and not u8('transitioning'),'continue-to14')
            assert vr(1440*32,96*32)==(GAME/'res/intro/font.bin').read_bytes(),'route-map font not loaded after result'
            shot(label+'-continue14')
            check(label+'-continue14-and-correct-map-font',True)
            restore(initial);isolate();w16('hp',0);run(fps*4);assert state()==3
            assert u8('resultActive') and u32('card')!=0,'defeat result card failed'
            shot(label+'-defeat-card');check(label+'-defeat-card',True)

        report['scope']='Both expanded union interiors:24 real camera pixel audits each, connected floor, bench faces and room edges, controller-only navigation after isolated setup, pause/cache restore, moving5-enemy/6+6-shot pressure,30/45kill boundaries and result cards. Canonical Dinorah pixels and PAL2 verified in VRAM. Protected prop uses existing escort reservation; escort AI remains inactive.'
        report['passed']=True;save();print('PASS union interior',report['region'],report['romSHA256'])
    except Exception as exc:
        ordinary=False;report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'phase13_union','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':
    sys.path.insert(0,str(BOOT.parent));main()
