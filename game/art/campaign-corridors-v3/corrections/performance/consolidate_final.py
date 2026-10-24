"""Rebuild the final candidate's evidence ledger without running emulation."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
SHORT='748849'
SHA='748849ea836635630f8a595634a34c21323fe1bc24df115ff6629f1babac6c77'


def read(name,key='romSHA256'):
    path=HERE/name
    data=json.loads(path.read_text())
    assert data['passed'],path
    if key:assert data[key]==SHA,(path,data.get(key))
    return data,str(path)


def main():
    result={'romSHA256':SHA,'passed':False,'performanceTargetMet':False,
      'publishedROMModifiedByThisAgent':False,'configuredRostersCapsCadenceUnchanged':True,
      'performance':{},'hudEquivalence':{},'residentVRAM':{},'santaHiddenFloor':{},
      'terrainFallback':{},'hostProofs':{},'physicalVBlanks':0,'gameUpdates':0,
      'expectedBanks':str(HERE/f'expected-{SHORT}/provenance.json'),
      'method':{
        'warmupSeconds':4,'physicalVBlanksPerCase':1800,
        'motion':'Real controller patrol in the first authored horizontal segment. Player excursion >=128px and camera excursion >=16px.',
        'policy':'native_cadence; AI and render caches retained; only inactive projectiles replenished.',
        'shield':'Exact PLAYER_SHIELD_TENTHS30 duration. Diagnostic repeat grants retain the native visible3-to2-to1countdown.',
        'timing':'phaseStats.frames/vtimer while ST_PLAY only. Every lost update fails; no rounding tolerance or death/transition tail.',
        'isolation':'EnemyHP refreshed and player shield granted. Dinorah pause/invulnerability timers held. These are RAM-isolated timing workloads.'},
      'limits':[
        'Steady timing covers five first-segment patrol workloads at configured caps. It does not establish every-coordinate or whole-route difficulty, or universal60/50performance.',
        'SAT limits are sampled every30physicalframes. Visible counts are reported separately from seeded pool caps.',
        'Current escort maps contain noHflip orVflip attrs. Comparisons include flag bits, but no flipped current-art cells were observed.',
        'Santa remains in the64-column resident ring at every legal384px-world camera. Its generic hidden-overlay streamColumn branch is unreachable here; reachable hidden-floor/ring behavior was tested.',
        'Terrain fallback was exercised in legacy training routes7/8. The current five campaign corridors do not enable modularTERRAIN.',
        'Host proofs test arithmetic, pixels and source contracts. They are not native68000timing measurements.',
        'This is technical QA, not visual composition approval, a complete campaign playthrough or publishing authorization.']}
    expected={'3':([1,0],4,6),'6A':([4,5],3,4),'6B':([4,5,7],3,4),'9':([4,2,9],3,4),'12':([4,5,2],3,4)}
    for region in ['ntsc','pal']:
        report,path=read(f'{region}-{SHORT}-moving/report.json')
        assert len(report['cases'])==5 and {c['phase'] for c in report['cases']}==set(expected)
        for case in report['cases']:
            assert (case['roster'],case['enemyCap'],case['shotCapPerPool'])==expected[case['phase']]
            assert case['targetMet'] and case['physicalFrames']==case['gameFrames']==1800
            assert case['policy']=='native_cadence' and case['phaseStayedActive'] and not case['deathTailIncluded']
            result['physicalVBlanks']+=case['physicalFrames'];result['gameUpdates']+=case['gameFrames']
        result['performance'][region]={'passed':True,'exitCode':0,'evidence':path,'cases':report['cases']}
        report,path=read(f'hud-{SHORT}-{region}/report.json')
        result['hudEquivalence'][region]={'passed':True,'evidence':path,'cases':len(report['cases']),
          'canvasBytesPerCase':3840,'displaySize':[320,24],'referenceROM_SHA256':report['referenceROM_SHA256']}
        report,path=read(f'vram-{SHORT}-{region}/report.json')
        result['residentVRAM'][region]={'passed':True,'evidence':path,
          'poses':sum(len(p['samples']) for p in report['phases'].values()),
          'exactCells':sum(s['exactCells'] for p in report['phases'].values() for s in p['samples']),
          'observedHVClasses':{k:p['inspectedHVClasses'] for k,p in report['phases'].items()},'fullAtlasesExact':True}
        report,path=read(f'santa-{SHORT}-{region}/report.json')
        result['santaHiddenFloor'][region]={'passed':True,'evidence':path,**{k:report[k] for k in
          ['framesCompared','exactCells','initialHP','realContactHP','cameraRange']}}
        report,path=read(f'terrain-routes-{SHORT}-{region}/report.json','rom_sha256')
        result['terrainFallback'][region]={'passed':True,'evidence':path,'checks':report['checks'],'failures':report['failures']}
    proofs={
      'glyphs':f'hud-value-glyph-{SHORT}.json','numberStringsAndFallback':f'objective-number-{SHORT}.json',
      'inventoryFields':'inventory-matches-equivalence.json','rayDDA':'dda-equivalence.json',
      'sightCache':'sight-cache-equivalence.json','gateEnvelope':'gate-envelope-equivalence.json',
      'collisionMasks':'occupied-equivalence.json','velocityMath':'velocity-divs-proof.json',
      'pulse':'pulse-equivalence.json','shieldSeconds':'shield-seconds-divu-proof.json'}
    for key,name in proofs.items():
        report,path=read(name,None)
        result['hostProofs'][key]={'passed':True,'evidence':path,'sourceROM_SHA256':report.get('romSHA256',report.get('compiledROM_SHA256'))}
    result['missedGameFrames']=result['physicalVBlanks']-result['gameUpdates']
    assert result['physicalVBlanks']==18000 and result['missedGameFrames']==0
    result['passed']=result['performanceTargetMet']=True
    path=HERE/f'comparison-{SHORT}.json';path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'romSHA256':SHA,'physicalVBlanks':result['physicalVBlanks'],
      'missedGameFrames':result['missedGameFrames'],'evidence':str(path)},indent=2))


if __name__=='__main__':main()
