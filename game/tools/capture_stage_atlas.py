"""Capture stages 1–16 (all A/B branches) from the current production ROM.

Run: arch -x86_64 /usr/bin/python3 game/tools/capture_stage_atlas.py
Reuses the project's Genesis Plus GX harness. RAM setup selects each stage,
protects the actors and places the player for inspection; this is a visual
inventory, not a playthrough or a performance benchmark. ROM is never changed.
"""
from pathlib import Path
import hashlib
import shutil
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    from campaign_geometry import closest
    import math
    labels=['1','2A','2B','3','4','5','6A','6B','7','8','9','10','11','12','13A','13B','14','15','16']
    report.update(scope='Visual inventory: stages 1–16, all A/B variants',stages=[],
        method='Genesis Plus GX, unmodified production ROM, NTSC. RAM setup selects each node, protects actors and positions the player before each still. Each view restores the same entry state. Not a controller traversal, completion test or FPS benchmark. Full base maps are decoded from the live ArenaScene ROM pointers; dynamic objects and HUD are visible in emulator stills.')
    def mem(addr,n):
        return read(addr&65535,n) if addr>=0xe00000 else bytes(data[addr:addr+n])
    def word(addr):return int.from_bytes(mem(addr,2),'big')
    def pointer(addr):return int.from_bytes(mem(addr,4),'big')
    def signed(name):return int.from_bytes(read(syms[name][0],2),'big',signed=True)
    def geometry():
        a=u32('world');width,height=struct.unpack('>HH',mem(a,4))
        bounds=list(struct.unpack('>hhhh',mem(a+4,8)))
        start=list(struct.unpack('>hh',mem(a+12,4)))
        solids=pointer(a+16);count=mem(a+20,1)[0]
        return dict(width=width,height=height,bounds=bounds,start=start,
            solids=[list(struct.unpack('>hhhh',mem(solids+i*10,8)))+[bool(word(solids+i*10+8))] for i in range(count)])
    def settle_camera():
        previous=None;stable=0
        for tick in range(fps*12):
            run();now=(signed('cameraX'),signed('cameraY'))
            stable=stable+1 if now==previous else 0;previous=now
            if stable>=12:run(3);return
        raise AssertionError('Camera did not settle')
    def protect():
        w16('hp',30000);w16('shieldTimer',60000);w16('spawnTimer',60000)
        if u16('dinorahHp'):
            w16('dinorahHp',100);w16('dinorahInvTimer',60000);w16('dinorahPauseTimer',60000)
        if 'npcHp' in syms and u16('npcHp'):
            w16('npcHp',100 if u8('currentLevel') in (18,19) else 30000)
            if 'radioInv' in syms:w16('radioInv',60000)
    def decode_map(d,folder):
        sc=u32('scene');tileptr=pointer(sc);mp=pointer(sc+8) if u8('arenaDamaged') and pointer(sc+8) else pointer(sc+4)
        palette=list(struct.unpack('>16H',mem(pointer(sc+12),32)))
        cols=word(sc+34) or 64;rows=word(sc+18)
        ids=list(struct.unpack('>'+str(cols*rows)+'H',mem(mp,cols*rows*2)))
        streamed=bool(pointer(sc+44));source_count=word(pointer(sc+44)) if streamed else word(sc+16)
        tiles=mem(tileptr,source_count*32)
        assert len(tiles)==source_count*32
        assert cols*8==d['width'] and rows*8==d['height'],(cols,rows,d)
        levels=[0,52,87,116,144,172,206,255]
        colors=[]
        for c in palette:
            rr,gg,bb=levels[(c>>1)&7],levels[(c>>5)&7],levels[(c>>9)&7]
            colors.append(bytes(((rr>>3)*255//31,(gg>>2)*255//63,(bb>>3)*255//31)))
        pixels=bytearray(d['width']*d['height']*3)
        cache={}
        for row in range(rows):
            for col in range(cols):
                attr=ids[row*cols+col];idx=attr if streamed else attr&2047
                assert idx<source_count,(idx,source_count)
                # Streamed sources use full 16-bit pattern IDs, not VDP flips.
                flipx=not streamed and attr&2048;flipy=not streamed and attr&4096
                key=(idx,bool(flipx),bool(flipy))
                if key not in cache:
                    tile=tiles[idx*32:idx*32+32];lines=[]
                    for yy in range(8):
                        line=bytearray()
                        for xx in range(8):
                            x=7-xx if flipx else xx;y=7-yy if flipy else yy
                            pair=tile[y*4+x//2];color=(pair&15) if x%2 else pair>>4
                            line.extend(colors[color])
                        lines.append(bytes(line))
                    cache[key]=lines
                for yy,line in enumerate(cache[key]):
                    at=((row*8+yy)*d['width']+col*8)*3;pixels[at:at+24]=line
        png(folder/'map.png',d['width'],d['height'],bytes(pixels))
        return dict(scene_address=hex(sc),map_address=hex(mp),tiles_address=hex(tileptr),
            source_patterns=source_count,resident_tile_budget=word(sc+16),streamed=streamed,
            map_sha256=hashlib.sha256(mem(mp,cols*rows*2)).hexdigest(),
            tiles_sha256=hashlib.sha256(tiles).hexdigest(),palette=palette)
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        run(2);baseline=snapshot()
        for node,label in enumerate(labels,1):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and u8('currentLevel')==node and not u8('transitioning'),'stage-'+label)
            until(lambda:u16('freezeTimer')==0,'unfreeze-'+label)
            run(6)  # Commit gameplay sprites and HUD after the radio/countdown.
            folder=out/label;folder.mkdir(exist_ok=True)
            # Untouched health, actors, objectives and entrance framing.
            png(folder/'entry.png',w,h,rgb())
            entry_camera=[signed('cameraX'),signed('cameraY')]
            d=geometry();source=decode_map(d,folder);protect();entry=snapshot()
            views=[];seen=set()
            def capture(x,y,name):
                # Reach missions finish at the far-right exit. Keep the actor
                # before its trigger so the still remains a gameplay view.
                if label in ('3','9'):x=min(x,d['width']-280)
                restore(entry);protect();pos(*closest(d,x,y))
                settle_camera();assert state()==1,('left stage',label,state())
                cx,cy=signed('cameraX'),signed('cameraY')
                if (cx,cy) in seen:return
                seen.add((cx,cy));file=name+'.png';png(folder/file,w,h,rgb())
                views.append(dict(file=label+'/'+file,camera=[cx,cy],player=[signed('px'),signed('py')],
                    frame=frames(),current_node=u8('currentLevel'),stream_faults=u16('sceneStreamFaults')))
                assert views[-1]['stream_faults']==0
            capture(*d['start'],'view-entry')
            nx=max(1,math.ceil((d['width']-320)/240));ny=max(1,math.ceil((d['height']-224)/152))
            for iy in range(ny+1):
                for ix in range(nx+1):
                    cx=round(ix*(d['width']-320)/nx);cy=round(iy*(d['height']-224)/ny)
                    capture(cx+152,cy+131,'view-'+str(ix)+'-'+str(iy))
            s=dict(id=label,node=node,geometry=d,source=source,entry=label+'/entry.png',
                map=label+'/map.png',views=views,entered=True,entry_camera=entry_camera)
            report['stages'].append(s);save()
            print('CAPTURED',label,str(d['width'])+'x'+str(d['height']),len(views),'views',flush=True)
        assert len(report['stages'])==19
        assert len({s['node'] for s in report['stages']})==19
        report['passed']=True;save()
    finally:
        save();core.retro_unload_game();core.retro_deinit()
'''

if __name__ == '__main__':
    if '--output' not in sys.argv:
        sys.argv += ['--output', str(BOOT.parents[1] / 'art/stage-atlas-01-16/captures')]
    if '--build-dir' not in sys.argv:
        # Other work can rebuild the shared release while the atlas runs.
        # Keep a matched immutable ROM/symbol snapshot for this capture.
        release = BOOT.parents[1] / 'out/release'
        snapshot = BOOT.parents[1] / 'art/stage-atlas-01-16/build-snapshot'
        snapshot.mkdir(parents=True, exist_ok=True)
        before = {name: hashlib.sha256((release/name).read_bytes()).hexdigest() for name in ('rom.bin','rom.out')}
        for name in before:
            shutil.copyfile(release/name, snapshot/name)
        after = {name: hashlib.sha256((release/name).read_bytes()).hexdigest() for name in before}
        assert before == after, 'Release changed while copying: retry capture'
        assert all(hashlib.sha256((snapshot/name).read_bytes()).hexdigest() == digest for name,digest in before.items())
        sys.argv += ['--build-dir', str(snapshot)]
    source = BOOT.read_text().split('\n    try:\n', 1)[0] + '\n' + TAIL + '\nif __name__=="__main__":main()\n'
    exec(compile(source, str(BOOT), 'exec'))
