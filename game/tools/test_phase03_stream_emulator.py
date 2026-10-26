"""Production-ROM phase3 cache, route, props and pause checks in Genesis Plus GX.

Reuses the established libretro bootstrap. Entry, walking and pause use input;
isolated graphics/contact/branch probes declare their RAM setup in the report.
"""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    import sys
    from campaign_geometry import faces,closest
    folder=GAME/'art/phase03-three-segments-v1/integration-v1'
    authored=json.loads((folder/'manifest.json').read_text())
    report['scope']='Phase3 only. Controller entry/route/pause and lower-boundary approach; RAM isolates enemies and branch/contact probes. The640-slot stress case seeds a cached camera target. Actual visible VRAM patterns checked against native source IDs.'
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def native_state(bank):
        return struct.unpack('>12800H',(folder/bank/'map.bin').read_bytes()),(folder/bank/'tiles.bin').read_bytes()
    sources={name:native_state(bank) for name,bank in [('intact','native'),('damaged','damaged-native')]}
    import re
    body=re.search(r'RESULT_FONT\[768\]\s*=\s*\{(.*?)\};',(GAME/'src/system/video/screens/result_font.h').read_text(),re.S)[1]
    font=[int(n,0) for n in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b',body)]
    def hud_digits():
        value=read(syms['objectiveValue'][0],4).split(b'\0',1)[0]
        assert len(value)==3 and value.isdigit(),value
        start=authored['route_points'][0][0];end=authored['exit'][0]+authored['exit'][2]//2
        expected=max(0,min(end-start,u16('px')+8-start))*100//(end-start)
        assert int(value)==expected,('route HUD did not catch up',value,expected)
        pixels=read(syms['hudPixels'][0],3840)
        for i,glyph in enumerate(value):
            for yy in range(8):
                bits=font[(glyph-32)*8+yy]
                for xx in range(8):
                    x=20+i*8+xx;y=13+yy;offset=((y//8*40+x//8)*8+y%8)*4
                    word=int.from_bytes(pixels[offset:offset+4],'big');color=word>>(28-(x%8)*4)&15
                    assert color==(4 if bits&(128>>xx) else 11),('HUD digit pixel',value,i,xx,yy,color)
    def cache_pixels(variant='intact'):
        assert u16('sceneStreamFaults')==0,('cache fault',u16('sceneStreamFaults'))
        assert u16('sceneStreamPeak')<=640
        hud_digits()
        ids,patterns=sources[variant]
        x,y=u16('cameraX'),u16('cameraY');address=u32('location')&65535
        assert address
        checked=0;used=set()
        for row in range((y+24)//8,(y+223)//8+1):
            for col in range(x//8,(x+319)//8+1):
                source=ids[row*320+col];slot=int.from_bytes(read(address+source*2,2),'big')
                assert slot<640,('missing slot',col,row,source,slot)
                attr=vw(u16('bgb_addr')+((row&31)*64+(col&63))*2)
                assert attr==0x6000+785+slot,('map cell',x,y,col,row,hex(attr),slot)
                actual=vr((785+slot)*32,32)
                if actual!=patterns[source*32:(source+1)*32]:
                    owner=u32('owner')&65535;refs=u32('refs')&65535
                    debug={'source':source,'slot':slot,'owner':int.from_bytes(read(owner+slot*2,2),'big'),'refs':int.from_bytes(read(refs+slot*2,2),'big'),'actualSource':patterns.find(actual)//32,'actual':actual.hex(),'state':state()}
                    (out/'failure-ram.bin').write_bytes(read(0,65536))
                    raise AssertionError(('pattern',x,y,col,row,debug))
                used.add(slot);checked+=1
        return {'camera':[x,y],'cells':checked,'resident':len(used),'peak':u16('sceneStreamPeak')}
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*15):
            run();current=(u16('cameraX'),u16('cameraY'))
            if state()!=1:return
            stable=stable+1 if current==previous else 0;previous=current
            if stable>=8:return
        raise AssertionError('camera stalled')
    def freeze_combat():
        isolate()
        for name in syms:
            if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,60000)
    def heap_blocks():
        p=u32('heap')&65535;blocks=[]
        for _ in range(80):
            size=int.from_bytes(read(p,2),'big')
            if not size:break
            blocks.append([p,size&~1,bool(size&1)]);p+=size&~1
        return blocks
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps)
        ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'phase3-prep',fps*20)
        prep=snapshot()
        ui(1);until(lambda:state()==1 and u8('currentLevel')==4 and not u8('transitioning'),'phase3-entry',fps*20)
        freeze_combat();wait_camera();initial=snapshot();shot('01-igreja-na-rom')
        check('entry-native-pixels',cache_pixels())
        check('heap-before-pause',heap_blocks())
        # Pause must release cache heap memory, restore exact slots/maps,
        # and retain room for the existing32KiB reversible panel snapshot.
        ui(3);until(lambda:state()==2,'pause');shot('02-pausa')
        assert not u32('location'),'stream work retained during pause'
        ui(0);until(lambda:state()==1,'resume');run(3)
        check('pause-restores-exact-cache',cache_pixels())
        # Pan through every module and reverse the scroll direction. Positions
        # only seed isolated camera probes; the production renderer does all work.
        views=[]
        for x in [264,512,672,832,1024,1200,1400,1600,1840,2080,2240,2304,2080,1600,1024,512,264]:
            for requested_y in [152,208,256]:
                xx,yy=closest(authored,x,requested_y);pos(xx,yy);freeze_combat();wait_camera()
                views.append(cache_pixels());
                if requested_y==208:shot('camera-'+str(x))
            shot('camera-'+str(x)+'-sul')
        check('forward-reverse-and-vertical-stream',{'samples':len(views),'peak':max(v['peak'] for v in views)})
        lower=[]
        for label,x in [('igreja',264),('rua1',800),('rua2',1320),('rua3',1840),('galpao',2304)]:
            xx,yy=closest(authored,x,232);pos(xx,yy);freeze_combat()
            hold({5},fps*2);wait_camera();view=cache_pixels()
            assert u16('py')==248 and view['camera'][1]==96,('lower framing',label,u16('py'),view)
            assert (view['camera'][1]+223)//8==39
            hold({5},fps//2);assert u16('py')==248,'walked into lower scenery'
            lower.append({'section':label,'player':[u16('px'),u16('py')],**view})
            # Enemies are isolated here. Clear diagnostic hit invulnerability
            # so its blink cannot hide the hero in the boundary evidence.
            for name in syms:
                if name.split('.lto_priv.')[0]=='invTimer' and syms[name][1]==2:w16(name,0)
            run(3)
            shot('07-limite-inferior-'+label)
        check('lower-border-visible-and-nonwalkable',{'views':lower,'nonwalkable_y':264,'last_world_row':39})
        # Isolate the exporter's worst41x26 camera window, independently of
        # the new player-to-camera framing. The production renderer runs it.
        pos(713,217);freeze_combat()
        for name,value in [('cameraPlayerX',713),('cameraPlayerY',217),('cameraTargetX',561),('cameraTargetY',1),('cameraTargetValid',1),('cameraFollowNpc',0)]:
            write(syms[name][0],value.to_bytes(syms[name][1],'big'))
        wait_camera();worst=cache_pixels()
        assert worst['camera']==[561,1] and worst['resident']==640,worst
        check('full640-slot-viewport-without-overflow',worst);shot('06-limite640-tiles')
        ui(3);until(lambda:state()==2,'pause-full-cache')
        ui(0);until(lambda:state()==1,'resume-full-cache');wait_camera()
        check('pause-restores-full640-slot-cache',cache_pixels())
        restore(initial);freeze_combat()
        probes=faces(authored);contacts=[]
        for x,y,button,axis,limit,direction in probes:
            pos(x,y);hold({button},fps);value=int.from_bytes(read(syms[axis][0],2),'big',signed=True)
            assert value<=limit if direction>0 else value>=limit,('collision',x,y,button,axis,limit,value)
            assert u16('sceneStreamFaults')==0
            contacts.append([x,y,button,value])
        check('street-prop-contact-faces',{'contacts':len(contacts),'solids':len(authored['solids'])})
        # Player and enemy shots use the same declared high/low footprints.
        shot_cases=[]
        for rect in [next(s for s in authored['solids'] if s[4] and s[2]>=64),next(s for s in authored['solids'] if not s[4] and s[2]>=32)]:
            a,b,ww,hh,blocked=rect
            restore(initial);freeze_combat();pos(264,184)
            # Spawn one native projectile32px left of the contact footprint.
            shotdata=struct.pack('>iiiiBBBB',(a-32)<<6,(b+hh//2+16)<<6,3<<6,0,0,0,1,0)
            write(syms['pshots'][0],shotdata);run(20)
            live=read(syms['pshots'][0]+18,1)[0]!=0
            assert live!=blocked,('shot obstruction',rect,live)
            shot_cases.append({'rect':rect,'shot_survives':live})
        check('high-props-stop-shots-low-rubble-does-not',shot_cases)
        restore(initial);freeze_combat();route_frames=0;route_checks=0
        for tx,ty in authored['player_waypoints'][1:]:
            for _ in range(fps*60):
                x=int.from_bytes(read(syms['px'][0],2),'big',signed=True);y=int.from_bytes(read(syms['py'][0],2),'big',signed=True)
                if abs(tx-x)<=2 and abs(ty-y)<=2:break
                keys=set()
                if x<tx-1:keys.add(7)
                elif x>tx+1:keys.add(6)
                if y<ty-1:keys.add(5)
                elif y>ty+1:keys.add(4)
                buttons.clear();buttons.update(keys);run();route_frames+=1
                assert u16('sceneStreamFaults')==0
                if state()!=1:break
                if route_frames%160==0:
                    buttons.clear();wait_camera()
                    if state()==1:cache_pixels();route_checks+=1
            else:raise AssertionError(('route blocked',tx,ty,x,y))
            buttons.clear()
            if state()!=1:break
            wait_camera()
            if state()==1:cache_pixels();route_checks+=1
        until(lambda:state()==4,'reach-warehouse',fps*10);shot('03-galpao-chegada')
        check('complete-route-with-controls',{'frames':route_frames,'seconds':round(route_frames/fps,2),'pixel_samples':route_checks,'objective_finished':True})
        # Isolated consequence load: only the flag of the earlier church bomb
        # is seeded while already on phase3's real preparation screen.
        restore(prep);write(syms['campaignFlags'][0],bytes([1]));ui(1)
        until(lambda:state()==1 and u8('currentLevel')==4 and not u8('transitioning'),'damaged-entry',fps*20)
        freeze_combat();wait_camera();shot('04-igreja-destruida-na-rom')
        check('persistent-church-damage-native-pixels',cache_pixels('damaged'))
        check('source-palettes-match-both-states',(folder/'native/palette.bin').read_bytes()==(folder/'damaged-native/palette.bin').read_bytes())
        # Real difficulty smoke test: clean selector snapshot, controller
        # movement/fire, native enemies and damage; no RAM health/AI grants.
        restore(prep);ui(1)
        until(lambda:state()==1 and not u8('transitioning'),'native-combat-entry',fps*20)
        natural_begin=frames();natural_vb=u32('vtimer');population=0;minimum_hp=u16('hp');natural_frames=0
        for tx,ty in authored['player_waypoints'][1:]:
            for _ in range(fps*60):
                x=u16('px');y=u16('py')
                if abs(tx-x)<=2 and abs(ty-y)<=2:break
                keys={1}
                if x<tx-1:keys.add(7)
                elif x>tx+1:keys.add(6)
                if y<ty-1:keys.add(5)
                elif y>ty+1:keys.add(4)
                buttons.clear();buttons.update(keys);run();natural_frames+=1
                population=max(population,living());minimum_hp=min(minimum_hp,u16('hp'))
                assert u16('sceneStreamFaults')==0
                if state()!=1 or u8('settleKind'):break
            else:raise AssertionError(('native route did not progress',tx,ty,x,y))
            if state()!=1 or u8('settleKind'):break
        buttons.clear();natural_game=frames()-natural_begin;natural_physical=u32('vtimer')-natural_vb
        until(lambda:state() in (3,4),'native-combat-outcome',fps*10);shot('05-combate-natural-resultado')
        check('native-combat-controller-smoke',{'outcome':'completed' if state()==4 else 'defeated','minimum_hp':minimum_hp,'maximum_enemies':population,'active_game_frames':natural_game,'physical_frames':natural_physical,'observed_game_fps':round(fps*natural_game/max(1,natural_physical),3),'health_or_ai_RAM_grants':False,'difficulty_human_reviewed':False})
        report['passed']=True;save();print('PASS phase3 complete',report['romSHA256'],flush=True)
    except Exception as e:
        report['error']=repr(e);save();shot('FAIL-phase03');raise
    finally:
        core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase03_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':
    sys.path.insert(0,str(BOOT.parent));main()
