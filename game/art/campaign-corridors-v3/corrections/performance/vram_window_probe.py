"""Exact escort atlas/resident-ring audit after streaming optimizations.

Uses production update/DMA and isolated legal camera positions. It compares
all64x32resident cells, including H/V flags, map padding and full pattern data.
Santa's hidden-floor overlay is outside these escort scenes and is not claimed.
"""
from pathlib import Path
import argparse
import sys
from types import SimpleNamespace
import steady_probe

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]

VRAM_TAIL = '''
        report={'romSHA256':hashlib.sha256(original).hexdigest(),
                'region':'PAL' if args.pal else 'NTSC','passed':False,'phases':{},
                'method':'RAM selects legal feet positions, suspends enemies and Dinorah traversal. Production camera interpolation, ring streaming and DMA continue. Compare complete resident64x32map cells and native pattern bytes, including H/V and padded out-of-world cells. Not a playthrough or difficulty test.',
                'notCovered':['Santa hidden-floor overlay; these phases contain Dinorah, not the Santa.']}
        if EXPECTED_DIR:
            maps=json.loads((EXPECTED_DIR/'maps.json').read_text())
            provenance=json.loads((EXPECTED_DIR/'provenance.json').read_text())
            assert provenance['romSHA256']==report['romSHA256']
            report['expectedBanksProvenance']=provenance
        for node,key in ((7,'06a'),(8,'06b'),(node12,'12')):
            enter(node);isolate();w16('dinorahPauseTimer',60000)
            w16('dinorahInvTimer',60000);w16('shieldTimer',60000)
            d=maps[key];width,height=d['size'];cols,rows=width//8,height//8
            bank=(EXPECTED_DIR/key) if EXPECTED_DIR else GAME/'res/campaign_routes'/key
            atlas=(bank/'tiles.bin').read_bytes()
            raw_map=struct.unpack('>'+str(cols*rows)+'H',(bank/'map.bin').read_bytes())
            samples=[('entry',d['start'])]
            for interest in d.get('camera_interest',[]):
                p=interest.get('position',interest.get('preferred_feet',interest.get('player_feet')))
                if p:samples.append((interest.get('name',interest.get('id','interest')),p))
            l,t,r,b=d['bounds']
            samples.extend((name,closest(d,x,y,extra=d.get('gates',[]))) for name,x,y in
                [('NW',l,t),('NE',r-15,t),('SW',l,b-15),('SE',r-15,b-15),
                 ('middle-high',width//2,t),('middle-low',width//2,b-15),('return',l,t)])
            result={'passed':False,'samples':[],'mapHVClasses':sorted(set(a&0x1800 for a in raw_map))}
            report['phases'][key]=result;seen_flips=set()
            for name,requested in samples:
                x,y=closest(d,*requested,extra=d.get('gates',[]));pos(x,y)
                previous=None;stable=0
                for _ in range(fps*20):
                    run();cam=(u16('cameraX'),u16('cameraY'))
                    stable=stable+1 if cam==previous else 0;previous=cam
                    if stable>=10:break
                else:raise AssertionError((key,name,'camera did not settle'))
                assert state()==1 and vr(785*32,len(atlas))==atlas,(key,name,'atlas changed')
                left,top=cam[0]//8,cam[1]//8;checked=0;flips=set()
                for world_y in range(top,top+32):
                    for world_x in range(left,left+64):
                        if world_x<cols and world_y<rows:
                            source=raw_map[world_y*cols+world_x]
                            expected=0x6000|(785+(source&2047))|(source&0x1800)
                            flips.add(source&0x1800)
                        else:expected=0
                        actual=vw(u16('bgb_addr')+((world_y&31)*64+(world_x&63))*2)
                        assert actual==expected,(key,name,world_x,world_y,hex(actual),hex(expected))
                        checked+=1
                seen_flips.update(flips)
                shot(key+'-'+str(len(result['samples']))+'-'+name.replace('/','-'))
                result['samples'].append({'name':name,'feet':[x,y],'camera':list(cam),
                                          'exactCells':checked,'HVClasses':sorted(flips),'atlasExact':True})
                save()
            result['inspectedHVClasses']=sorted(seen_flips)
            result['passed']=True;save()
        report['passed']=all(d['passed'] for d in report['phases'].values());save()
        print(json.dumps({'romSHA256':report['romSHA256'],'region':report['region'],
              'passed':report['passed'],'samples':sum(len(d['samples']) for d in report['phases'].values()),
              'exactCells':sum(s['exactCells'] for d in report['phases'].values() for s in d['samples'])},indent=2),flush=True)
    finally:
        core.retro_unload_game();core.retro_deinit()
    return 0 if report['passed'] else 3
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pal', action='store_true')
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-dir', type=Path,
                        help='Frozen ROM-verified banks, maps.json and provenance.json')
    options = parser.parse_args()
    steady_probe.TAIL = VRAM_TAIL
    code = compile(steady_probe.program(), str(HERE / 'adapted-vram-bootstrap.py'), 'exec')
    sys.path.insert(0, str(GAME / 'tools'))
    namespace = {'__name__': 'private_vram_probe', '__file__': str(steady_probe.BOOTSTRAP),
                 'EXPECTED_DIR': options.expected_dir.resolve() if options.expected_dir else None,
                 'PRIVATE_ARGS': SimpleNamespace(pal=options.pal, movie=False,
                     build_dir=options.build_dir.resolve(), output=options.output.resolve())}
    exec(code, namespace)
    return namespace['main']()


if __name__ == '__main__':
    raise SystemExit(main())
