"""Phase3 maximum authored population and projectile pools while scrolling.

Adapts the established steady probe with current phase3 geometry and visible
initial placements. AI, cadence, movement, rendering and audio run unchanged.
RAM grants health/shield and replenishes only inactive projectile records.
"""
from pathlib import Path
import importlib.util

GAME=Path(__file__).resolve().parents[1]
SOURCE=GAME/'art/campaign-corridors-v3/corrections/performance/steady_probe.py'
spec=importlib.util.spec_from_file_location('phase03_steady',SOURCE)
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def replace_once(text,old,new):
    assert text.count(old)==1,('review diagnostic adapter',old)
    return text.replace(old,new)

probe.TAIL=replace_once(probe.TAIL,
    'origins=[(80+i%4*48,200+i//4*24) for i in range(cap)]',
    'origins=[(264+i*40,192) for i in range(cap)]')
probe.TAIL=replace_once(probe.TAIL,
    "(80+i%3*64)<<6,\n                                             (216+i//3*32)<<6,24,0)",
    "(u16('cameraX')+40+i%3*64)<<6,\n                                             (u16('cameraY')+176+i//3*24)<<6,24,0)")
probe.TAIL=replace_once(probe.TAIL,
    "assert current_active(escort),('death/transition entered sample',phase,policy,tick)",
    "assert current_active(escort),('death/transition entered sample',phase,policy,tick)\n                    assert u16('sceneStreamFaults')==0,('stream fault',tick)")
probe.TAIL=replace_once(probe.TAIL,
    "'phaseStayedActive':True,'deathTailIncluded':False}",
    "'phaseStayedActive':True,'deathTailIncluded':False,\n                     'streamFaults':u16('sceneStreamFaults'),'streamPeakTiles':u16('sceneStreamPeak'),\n                     'projectileSetup':'Replenished inactive records inside current viewport; active records retain native trajectory.'}")

probe.TAIL=replace_once(probe.TAIL,
    "'lastShieldSeconds','lastModeCharges'",
    "'sceneStreamUploads','sceneStreamFaults','freeCount','warmCol','warmRow','lastShieldSeconds','lastModeCharges'")
probe.TAIL=replace_once(probe.TAIL,
    'timers=set();poses=set();sat=[0,0,0];poolmin=[shotcap,shotcap]',
    'timers=set();poses=set();routeValues=set();sat=[0,0,0];poolmin=[shotcap,shotcap]')
probe.TAIL=replace_once(probe.TAIL,
    "last=now;loads.append(u16('cpuFrameLoad')*100/2048)",
    "last=now;loads.append(u16('cpuFrameLoad')*100/2048)\n                    routeValues.add(read(syms['objectiveValue'][0],4).split(b'\\0',1)[0].decode('ascii'))")
probe.TAIL=replace_once(probe.TAIL,
    "row={'phase':phase,'policy':policy,'roster':roster,'enemyCap':cap,",
    "if PERF_CONFIG['motion']=='patrol':assert len(routeValues)>=5,('route HUD stopped updating',routeValues)\n                row={'phase':phase,'policy':policy,'roster':roster,'enemyCap':cap,'routeHUDValues':sorted(routeValues),")

if __name__=='__main__':
    import sys
    if '--phases' not in sys.argv:sys.argv.extend(['--phases','3'])
    if '--policies' not in sys.argv:sys.argv.extend(['--policies','native_cadence'])
    raise SystemExit(probe.main())
