"""Exact reachable Santa hidden-floor/ring test on an immutable ROM.

Identifies the NPC invulnerability timer through real contact damage, then
holds its hidden blink phase while production camera/DMA execute normally.
No npcVisible, map, VRAM or HP patch is used.
"""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
import steady_probe

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]

TAIL = '''
        report={'romSHA256':hashlib.sha256(original).hexdigest(),'region':'PAL' if args.pal else 'NTSC',
          'passed':False,'method':'Real contact identifies NPC blink timer, then diagnostic hold of its hidden phase only. Player feet positions are isolated RAM setup. Production camera, rendering, stream and DMA remain active. No HP/npcVisible/VRAM/map writes.',
          'limit':'Santa cols22..26 remain resident in every legal384px-world camera; the generic streamColumn hidden-overlay branch is unreachable. This proves reachable full-ring content while hidden and legal camera scrolling, not that unreachable branch.',
          'samples':[]}
        full_symbols={};symbol_sizes={}
        for line in symbols.splitlines():
            fields=line.split()
            if len(fields) in (3,4):
                name=fields[-1].split('.lto_priv.')[0];full_symbols[name]=int(fields[0],16)
                if len(fields)==4:symbol_sizes[name]=int(fields[1],16)
        banks={}
        for name in ('tiles','map','palette'):
            symbol='signal_'+name;address=full_symbols[symbol];size=symbol_sizes[symbol]
            banks[name]=original[address:address+size]
            assert len(banks[name])==size
        report['expectedBanksFromImmutableROMSymbols']=True
        address=full_symbols['signalNpc'];npc=original[address:address+symbol_sizes['signalNpc']]
        col,row,npc_cols,npc_rows=struct.unpack_from('>4H',npc)
        floor_address=int.from_bytes(npc[8:12],'big')
        floor=struct.unpack('>'+str(npc_cols*npc_rows)+'H',original[floor_address:floor_address+npc_cols*npc_rows*2])
        rx,ry,rw,rh=col*8,row*8,npc_cols*8,npc_rows*8;visual={'floor_tiles':floor};columns=48;rows=40
        assert len(banks['map'])==columns*rows*2
        world_map=struct.unpack('>'+str(columns*rows)+'H',banks['map'])
        timers={address for name,(address,size) in syms.items() if name.startswith('invTimer') and size==2}
        enter(6);isolate();pos(64,232);run(fps//2)
        before={a:int.from_bytes(read(a,2),'big') for a in timers}
        initial_hp=u16('npcHp');assert initial_hp==u16('npcHpMax')
        enemy=bytearray(46);struct.pack_into('>hhii',enemy,0,160,208,160<<6,208<<6)
        struct.pack_into('>hhHH',enemy,12,32,0,600,600);enemy[30]=0;enemy[31]=20;enemy[43]=1;enemy[44]=1
        write(syms['enemies'][0],enemy)
        for _ in range(fps):
            run()
            if u16('npcHp')<initial_hp:break
        assert u16('npcHp')==initial_hp-12,('real contact did not damage Santa by12',initial_hp,u16('npcHp'),u16('npcX'),u16('npcY'),state())
        candidates=[a for a in timers if before[a]==0 and fps*2<=int.from_bytes(read(a,2),'big')<=fps*3]
        assert len(candidates)==1,('NPC timer identity ambiguous',candidates,before)
        timer=candidates[0];isolate();report['initialHP']=initial_hp;report['realContactHP']=initial_hp-12;report['npcTimerAddress']=hex(timer)
        def hidden_run():
            write(timer,struct.pack('>H',60006));run()
            assert state()==1 and u16('npcHp')==initial_hp-12 and not u8('npcVisible')
        for _ in range(10):hidden_run()
        positions=[('south-west',32,248),('south-east',344,248),('north-east',344,128),('north-west',32,128),('return',64,232)]
        camera_values=[];cells=0;frames_checked=0
        for name,x,y in positions:
            pos(x,y);previous=None;stable=0
            for _ in range(fps*20):
                committed_cam=(u16('cameraX'),u16('cameraY'))
                hidden_run();cam=(u16('cameraX'),u16('cameraY'));camera_values.append(cam)
                actual_atlas=vr(785*32,len(banks['tiles']))
                assert actual_atlas==banks['tiles'],('atlas changed',[(i,a,b) for i,(a,b) in enumerate(zip(actual_atlas,banks['tiles'])) if a!=b][:30])
                # DMA_QUEUE_COPY is consumed at the next VBlank. The current
                # camera target has already advanced the next logical frame;
                # compare the ring against the preceding committed camera.
                left,top=committed_cam[0]//8,committed_cam[1]//8
                for yy in range(top,top+32):
                    for xx in range(left,left+64):
                        if xx<columns and yy<rows:
                            tile=world_map[yy*columns+xx]
                            if rx//8<=xx<(rx+rw)//8 and ry//8<=yy<(ry+rh)//8:
                                tile=visual['floor_tiles'][(yy-ry//8)*(rw//8)+xx-rx//8]
                            expected=0x6000|(785+(tile&2047))|(tile&0x1800)
                        else:expected=0
                        actual=vw(u16('bgb_addr')+((yy&31)*64+(xx&63))*2)
                        assert actual==expected,(name,cam,xx,yy,hex(actual),hex(expected))
                        cells+=1
                frames_checked+=1
                stable=stable+1 if cam==previous else 0;previous=cam
                if stable>=10:break
            else:raise AssertionError(('camera did not settle',name))
            shot(name);report['samples'].append({'name':name,'feet':[x,y],'camera':list(cam),'hidden':True});save()
        report.update(passed=True,framesCompared=frames_checked,exactCells=cells,
                      cameraRange=[[min(c[i] for c in camera_values),max(c[i] for c in camera_values)] for i in (0,1)])
        save();print(json.dumps(report,indent=2),flush=True)
    finally:
        core.retro_unload_game();core.retro_deinit()
    return 0 if report['passed'] else 3
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pal',action='store_true')
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check-syntax',action='store_true')
    args=parser.parse_args()
    steady_probe.TAIL=TAIL
    code=compile(steady_probe.program(),str(HERE/'adapted-santa-bootstrap.py'),'exec')
    if args.check_syntax:
        print('adapted Santa bootstrap syntax OK')
        return 0
    sys.path.insert(0,str(GAME/'tools'))
    namespace={'__name__':'private_santa_probe','__file__':str(steady_probe.BOOTSTRAP),
               'PRIVATE_ARGS':SimpleNamespace(pal=args.pal,movie=False,build_dir=args.build_dir.resolve(),output=args.output.resolve())}
    exec(code,namespace)
    return namespace['main']()


if __name__=='__main__':
    raise SystemExit(main())
