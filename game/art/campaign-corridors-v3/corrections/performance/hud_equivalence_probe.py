"""Pixel-exact HUD transition audit against a previously captured ROM.

Runs only isolated UI scenarios. Actors/items are prepared through RAM, then
the production loop composes and commits its HUD. This is not gameplay QA.
"""
from pathlib import Path
import argparse
import hashlib
import sys
from types import SimpleNamespace
import steady_probe

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]

HUD_TAIL = '''
        enter(node12);isolate();w16('dinorahInvTimer',60000)
        write(syms['dinorahNode'][0],bytes([1]));w16('dinorahFireTimer',60000)
        w16('dinorahPauseTimer',60000);w16('shieldTimer',0)
        player_start=(u16('px'),u16('py'))
        w16('dinorahX',player_start[0]+160);w16('dinorahY',player_start[1])
        cases=[]
        for label in ('waiting','aiming','pausing','waiting','aiming','waiting'):
            cases.append(dict(label=label,shield=0,mode=0,charges=0))
        for seconds in (3,2,1,0):
            cases.append(dict(label='waiting',shield=seconds,mode=0,charges=0))
        for mode in (1,2,3):
            for seconds in (0,3):
                for charges in (3,2,1,0):
                    cases.append(dict(label='waiting',shield=seconds,mode=mode,charges=charges))
        cases.extend([dict(label='aiming',shield=2,mode=1,charges=2,bag='full'),
                      dict(label='waiting',shield=1,mode=1,charges=1,bag='empty'),
                      dict(label='pausing',shield=0,mode=0,charges=0)])
        report={'romSHA256':hashlib.sha256(original).hexdigest(),
                'region':'PAL' if args.pal else 'NTSC','passed':False,'cases':[],
                'method':'Identical explicit HUD semantic states; native UI update and DMA only. Compare all3840canvas bytes, committed120tiles and320x24display pixels. Insect combat isolated; this is UI equivalence, not timing or gameplay.'}
        reference=HUD_CONFIG['reference']
        reference_report=json.loads((reference/'report.json').read_text()) if reference else None
        if reference_report:
            report['referenceROM_SHA256']=reference_report['romSHA256']
            assert reference_report['region']==report['region']
        for i,case in enumerate(cases):
            label=case['label'];w16('dinorahFireTimer',60000);w16('dinorahPauseTimer',60000)
            w16('dinorahAimTimer',60000 if label=='aiming' else 0)
            if label=='pausing':pos(u16('dinorahX'),u16('dinorahY'))
            else:pos(*player_start)
            write(syms['waiting'][0],bytes([label=='waiting']))
            write(syms['shotMode'][0],bytes([case['mode']]))
            write(syms['modeCharges'][0],bytes([case['charges']]))
            w16('shieldTimer',case['shield']*fps)
            if case.get('bag'):
                assert syms['item'][1]==6
                write(syms['item'][0],bytes([5,5,6,3,7,4] if case['bag']=='full' else [255,0]*3))
            run(fps//2)
            assert state()==1 and u16('hp')>0
            expected_state={'waiting':1,'aiming':3,'pausing':2}[label]
            assert u8('dinorahState')==expected_state,(case,u8('dinorahState'))
            assert not any(read(syms['hudDirty'][0],syms['hudDirty'][1])),'uncommitted dirty HUD'
            canvas=read(syms['hudPixels'][0],syms['hudPixels'][1])
            tile_base=vw(u16('window_addr'))&2047
            committed=vr(tile_base*32,len(canvas))
            assert canvas==committed,('canvas differs from displayed tile patterns',case)
            pixels=rgb()[:320*24*3]
            name=f'{i:02d}-{label}-s{case["shield"]}-m{case["mode"]}-c{case["charges"]}'
            row=dict(case,index=i,name=name,canvasSHA256=hashlib.sha256(canvas).hexdigest(),
                     displayedRGB_SHA256=hashlib.sha256(pixels).hexdigest(),
                     committedTilesSHA256=hashlib.sha256(committed).hexdigest(),passed=True)
            for suffix,payload in [('canvas.bin',canvas),('vram.bin',committed),('rgb.bin',pixels)]:
                (out/(name+'-'+suffix)).write_bytes(payload)
                if reference:
                    expected=(reference/(name+'-'+suffix)).read_bytes()
                    if expected!=payload:
                        row['passed']=False
                        row.setdefault('differences',[]).append(dict(bank=suffix,
                            differentBytes=sum(a!=b for a,b in zip(expected,payload)),
                            expectedBytes=len(expected),actualBytes=len(payload)))
            png(out/(name+'.png'),320,24,pixels)
            report['cases'].append(row);save()
        report['passed']=all(row['passed'] for row in report['cases'])
        report['caseCount']=len(cases);save()
        print(json.dumps({'region':report['region'],'romSHA256':report['romSHA256'],
                          'cases':len(cases),'passed':report['passed'],
                          'differentCases':[r['name'] for r in report['cases'] if not r['passed']]},indent=2),flush=True)
    finally:
        core.retro_unload_game();core.retro_deinit()
    return 0 if report['passed'] else 3
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pal', action='store_true')
    parser.add_argument('--build-dir', type=Path, default=GAME / 'out/release')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    options = parser.parse_args()
    steady_probe.TAIL = HUD_TAIL
    code = compile(steady_probe.program(), str(HERE / 'adapted-hud-bootstrap.py'), 'exec')
    sys.path.insert(0, str(GAME / 'tools'))
    namespace = {'__name__': 'private_hud_probe', '__file__': str(steady_probe.BOOTSTRAP),
                 'PRIVATE_ARGS': SimpleNamespace(pal=options.pal, movie=False,
                     build_dir=options.build_dir.resolve(), output=options.output.resolve()),
                 'HUD_CONFIG': {'reference': options.reference.resolve() if options.reference else None}}
    exec(code, namespace)
    return namespace['main']()


if __name__ == '__main__':
    raise SystemExit(main())
