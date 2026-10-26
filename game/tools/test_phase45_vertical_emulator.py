"""Vertical arenas4/5: production pixels, controller bounds, NPC and load.

The shared libretro bootstrap is unchanged. RAM isolates graphics and seeds
load/contact cases; traversal, pause and physics use the normal controller.
"""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    from campaign_geometry import closest,faces,edges
    authored=json.loads((GAME/'art/campaign-pattern-v2/early/geometry.json').read_text())
    report['scope']='Phases4/5 vertical expansion. Controller movement/collision and pause; RAM isolates enemies, selects preparation nodes and seeds contact/load cases. Real production AI and rendering. Difficulty is not human-certified.'
    def ui(key,n=1):
        for _ in range(n):hold({key},8);run(8)
    def wait_camera():
        previous=None;stable=0
        for _ in range(fps*8):
            run();current=(u16('cameraX'),u16('cameraY'))
            stable=stable+1 if current==previous else 0;previous=current
            if stable>=8:return
        raise AssertionError('camera did not settle')
    def protect_player():
        for name,(address,size) in syms.items():
            if name.split('.lto_priv.')[0]=='invTimer' and size==2:write(address,struct.pack('>H',60000))
    def pixels(d,folder):
        cx,cy=u16('cameraX'),u16('cameraY');cols=d['width']//8
        data=(folder/'tiles.bin').read_bytes();rawmap=(folder/'map.bin').read_bytes()
        assert vr(785*32,len(data))==data,'atlas changed'
        checked=0
        for row in range((cy+24)//8,(cy+223)//8+1):
            for col in range(cx//8,(cx+319)//8+1):
                attr=struct.unpack_from('>H',rawmap,(row*cols+col)*2)[0]
                expected=(785+(attr&2047))|(attr&0x1800)
                actual=vw(u16('bgb_addr')+((row&31)*64+(col&63))*2)&0x1fff
                assert actual==expected,('map',col,row,hex(actual),hex(expected),cx,cy)
                checked+=1
        return {'camera':[cx,cy],'cells':checked,'bottom_world_row':(cy+223)//8}
    try:
        run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps)
        ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'preparation',fps*20)
        prep=snapshot();baselines={}
        for key,node,foldername,cap,roster in [('04',5,'04-warehouse',4,[1,0]),('05',6,'05-signal',3,[5,4])]:
            restore(prep);write(syms['pendingLevel'][0],bytes([node]));ui(1)
            until(lambda:state()==1 and u8('currentLevel')==node and not u8('transitioning'),'entry-'+key,fps*20)
            isolate();wait_camera();initial=snapshot();baselines[key]=initial
            d=authored[key];folder=GAME/'art/campaign-pattern-v2/early'/foldername
            assert (u16('arenaMinY'),u16('arenaMaxY'))==(d['bounds'][1],d['bounds'][3])
            assert d['height']==448 and d['bounds'][3]-d['bounds'][1]+1==288
            if key=='05':assert (u16('npcX'),u16('npcY'),u16('npcHp'))==(176,280,180)
            shot(key+'-entrada');check(key+'-entry',pixels(d,folder))
            views=[]
            for xx,yy in [(48,112),(448,112),(48,240),(448,240),(48,376),(448,376),(48,112)]:
                x,y=closest(d,xx,yy);pos(x,y);isolate();wait_camera();views.append(pixels(d,folder))
                shot(key+'-camera-'+str(x)+'-'+str(y))
            check(key+'-vertical-forward-reverse-exact-map',views)
            # Real DOWN input reaches the new southern edge and cannot enter
            # the decorative lower wall. Both limits and the last art row show.
            pos(48,296);isolate();hold({5},fps*3);wait_camera()
            assert u16('py')==d['bounds'][3]-15,(key,'south collision',u16('py'))
            assert u16('cameraY')==224,(key,'hidden south perimeter',u16('cameraY'))
            check(key+'-southern-wall-controller',pixels(d,folder));shot(key+'-limite-inferior')
            count=0
            for x,y,button,axis,limit,sign in faces(d):
                pos(x,y);isolate();hold({button},fps//2);value=u16(axis)
                assert value<=limit if sign==1 else value>=limit,(key,'prop collision',x,y,axis,value,limit)
                count+=1
            for x,y,button,axis,limit in edges(d):
                pos(x,y);isolate();hold({button},fps//2);assert u16(axis)==limit,(key,'edge',axis,u16(axis),limit)
            check(key+'-contact-and-perimeter-collisions',{'prop_faces':count,'perimeter_faces':4})
            pos(48,376);isolate();wait_camera();ui(3);until(lambda:state()==2,'pause-'+key);shot(key+'-pausa')
            ui(0);until(lambda:state()==1,'resume-'+key);run(3);check(key+'-pause-restores-expanded-map',pixels(d,folder))
            # At the authored cap, keep enemy behaviour and animation clocks.
            # Protect only HP/timing; seed inactive shot slots, never reset an
            # active projectile or enemy. Patrol through newly added rows.
            restore(initial);pos(176 if key=='04' else 112,240);isolate();protect_player()
            for i in range(cap):seed(i,roster[i%2],104+i*48,248,200,0)
            if key=='05':w16('surviveLeft',fps*120)
            direction=5
            def arrange():
                nonlocal direction
                protect_player()
                if u16('py')>=336:direction=4
                if u16('py')<=224:direction=5
                buttons.clear();buttons.add(direction)
                for i in range(cap):write(syms['enemies'][0]+i*46+31,bytes([200]))
                for name in ('pshots','eshots'):
                    for i in range(6):
                        at=syms[name][0]+i*20
                        if read(at+18,1)[0]:continue
                        buf=bytearray(20);struct.pack_into('>iiii',buf,0,(96+i%3*56)<<6,(u16('py')+i//3*24)<<6,24,0)
                        buf[17]=1;buf[18]=1;write(at,buf)
            for _ in range(fps*2):arrange();run()
            begin=frames();vb=u32('vtimer');max_visible=0;scan=[0,0,0];missed=0;last=begin;cams=set();ys=set()
            for _ in range(fps*20):
                assert state()==1 and not u8('settleKind'),('load left active play',key)
                arrange()
                for pool in ('pshots','eshots'):
                    assert sum(read(syms[pool][0]+i*20+18,1)[0]!=0 for i in range(16))==6
                run();now=frames();missed+=int(now-last!=1);last=now
                assert living()==cap
                cx,cy=u16('cameraX'),u16('cameraY');cams.add(cy);ys.add(u16('py'));visible=0
                for i in range(cap):
                    b=read(syms['enemies'][0]+i*46,46);ex,ey=struct.unpack_from('>hh',b)
                    visible+=int(ex+16>cx and ex<cx+320 and ey>cy+24 and ey-16<cy+224)
                max_visible=max(max_visible,visible)
                limits=sprite_limits();scan=[max(a,b) for a,b in zip(scan,limits)]
            buttons.clear();gameframes=frames()-begin;physical=u32('vtimer')-vb
            result={'enemy_cap':cap,'maximum_visible_enemies':max_visible,'projectiles_per_pool_seeded_to_cap':6,'game_frames':gameframes,'physical_frames':physical,'observed_fps':round(fps*gameframes/physical,3),'frames_without_game_update':missed,'player_y_range':[min(ys),max(ys)],'camera_y_range':[min(cams),max(cams)],'maximum_sat_sprites_scanline_sprites_pixels':scan,'RAM_health_contact_isolation':True}
            check(key+'-maximum-cap-vertical-patrol-load',result);shot(key+'-carga')
            assert max(ys)-min(ys)>=96 and max(cams)-min(cams)>=24,('patrol blocked',result)
            assert missed==0 and gameframes==physical,(key,'frame losses',result)
        # Native contact at the moved statue, including blink/floor restoration.
        restore(baselines['05']);isolate();pos(112,280);wait_camera();native_npc_hp=u16('npcHp')
        seed(0,5,160,272,200,60000)
        for _ in range(fps):
            run()
            if u16('npcHp')<native_npc_hp:break
        assert u16('npcHp')==168,('Santa contact after relocation',u16('npcHp'))
        shot('05-santa-contato');isolate();run(fps*4);check('05-relocated-santa-contact-blink-and-floor',pixels(authored['05'],GAME/'art/campaign-pattern-v2/early/05-signal'))
        # Use the complete120s clock without bypassing countdown; enemies are
        # isolated for the objective regression, not a difficulty certification.
        restore(baselines['05']);isolate();start=frames();remaining=u16('surviveLeft')
        until(lambda:state()==1 and u16('surviveLeft')<=1,'protect-last-tick',fps*125)
        last_alive_hp=u16('npcHp');assert last_alive_hp==180
        until(lambda:state()==4,'protect120s',fps*10)
        assert frames()-start>=remaining-1
        check('05-full-protect-clock',{'remaining_game_frames_on_entry':remaining,'active_game_frames_to_win':frames()-start,'npc_hp_before_win':last_alive_hp,'npc_cleared_on_result':u16('npcHp')==0,'enemies_isolated':True});shot('05-objetivo-vencido')
        report['passed']=True;save();print('PASS phase4/5 vertical expansion',report['romSHA256'],flush=True)
    except Exception as e:
        report['error']=repr(e);save();shot('FAIL-phase45');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''
def main():
    prefix=BOOT.read_text().split('    try:\n',1)[0]
    namespace={'__name__':'phase45_native_probe','__file__':str(BOOT)}
    exec(compile(prefix+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()
if __name__=='__main__':sys.path.insert(0,str(BOOT.parent));main()
