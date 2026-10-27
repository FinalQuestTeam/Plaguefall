"""All 19 campaign briefings/guides/pauses, with live objective snapshots.

Reuse the production libretro harness. RAM selects stages and seeds partial
progress; controller input alone navigates preparation, guide, pause and resume.
"""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    import re
    copy=json.loads((GAME/'art/interface-ux-v2/campanha-v2.json').read_text())['phases']
    graph=(GAME/'src/levels/graph.c').read_text()
    guide=(GAME/'src/system/video/screens/mission_guide.h').read_text()
    requirements=[
        ('SOBREVIVA','PÁTIO'),('ELIMINE','PÁTIO'),('ELIMINE','PÁTIO'),
        ('ATRAVESSE','GALPÃO'),('ELIMINE','GALPÃO'),('PROTEJA','SANTA','COMUNICADOR'),
        ('ESCOLTE','DINORAH','2 PORTÕES'),('ESCOLTE','DINORAH','2 VÁLVULAS','2 PORTÕES'),
        ('ABRA','BAÚS','ENTREGUE','DEPÓSITO'),('DESTRUA','TRANSMISSORES'),
        ('ATRAVESSE','FÁBRICA'),('DESTRUA','NINHOS','OVOS'),('REAQUEÇA','ABRA','VÁLVULAS'),
        ('ESCOLTE','DINORAH','SINDICATO'),('ELIMINE','SINDICATO'),('ELIMINE','SINDICATO'),
        ('LIGUE','GERADORES'),('PROTEJA','NÚCLEO','RÁDIO'),('DERROTE','ESCORPIÃO'),
    ]
    def row_content(row):return textrow(row)[2:38].replace('.', ' ').strip()
    def content(row,count):return ' '.join(' '.join(row_content(r) for r in range(row,row+count)).split())
    def clean(value):return ' '.join(value.replace('.',' ').split())
    def pause():
        buttons.add(3);until(lambda:state()==2,'pause');buttons.clear();run(2)
    def seed_progress(phase):
        key=phase['id']
        if key in ('6A','6B'):
            base=syms['campaignRouteOps'][0]
            write(base+8,bytes([0,4,1])) # first gate/valve finished, second intact
            write(base+12,bytes(4)) # no gate-collapse animation still blocking
            w16('dinorahHp',73)
        elif key=='7':
            base=syms['campaignResistance'][0];write(base+18,bytes([2,0]))
        elif key=='8':write(syms['campaignResistance'][0]+20,b'\1')
        elif key in ('10','11'):write(syms['campaignFactory'][0]+35,b'\3')
        elif key=='14':write(syms['campaignLaunch'][0]+14,b'\5')
        elif key=='15':w16('npcHp',76)
        elif key=='5':w16('npcHp',123)
        elif key=='12':w16('dinorahHp',73)
        elif key in ('2A','2B','4','13A','13B'):w16('kills',7)
    progress={
        '1':('FALTAM','SEGUNDOS'), '2A':('7 DE 15',), '2B':('7 DE 15',),
        '3':('TRAVESSIA: 0%','SIGA A SETA'), '4':('7 DE 20',), '5':('SANTA: 123/180',),
        '6A':('DINORAH: 73/100','PORTÕES: 1/2'),
        '6B':('DINORAH: 73/100','PORTÕES: 1/2','VÁLVULAS: 1/2'),
        '7':('ENTREGAS: 2/5','CARREGANDO'), '8':('TRANSMISSORES: 1/3',),
        '9':('TRAVESSIA: 0%','SIGA A SETA'), '10':('NINHOS: 3/10',), '11':('VÁLVULAS: 3/6',),
        '12':('DINORAH: 73/100','ROTA: 0%'), '13A':('7 DE 30',), '13B':('7 DE 45',),
        '14':('GERADORES: 2/5',), '15':('RÁDIO: 76/100',), '16':('ESCORPIÃO: 25 DE 25',),
    }
    try:
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')
        baseline=snapshot()
        assert len(copy)==19
        for node,phase in enumerate(copy,1):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'setup-play')
            w16('hp',0);write(syms['gameOver'][0],b'\1')
            until(lambda:state()==3 and not u8('transitioning'),'defeat');run(fps);press(3)
            until(lambda:state()==6 or (state()==0 and 'A: COMEÇAR' in textrow(26)),'retry')
            if state()==6:run(fps);press(3)
            until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'briefing')
            key=phase['id'];goal=content(9,2)
            assert phase['name'] in textrow(5),(key,'name',textrow(5))
            for term in requirements[node-1]:assert term in goal,(key,term,goal)
            assert not row_content(11),(key,'goal overflow into separator',textrow(11))
            definition=re.search(r'\[N_'+key+r'\]\s*=\s*FASE(?:_FINAL)?\("[^"]+",\s*(\w+)',graph)[1]
            source=next(p.read_text() for p in (GAME/'src/levels/defs').glob('*.c') if re.search(r'\b'+definition+r'\s*=',p.read_text()))
            target=re.search(r'\.(?:killTarget|objTarget)\s*=\s*(\d+)',source)
            if target and key!='16':assert re.search(r'\b'+target[1]+r'\b',goal),(key,'target differs from gameplay',goal,target[1])
            threat=re.search(r'\[N_'+key+r'\]\s*=\s*(ENEMY_\w+)',guide)[1]
            roster=re.search(r'roster\[\]\s*=\s*\{([^}]+)',source)[1]
            assert threat in roster,(key,'threat absent from roster',threat,roster)
            assert content(22,2)==clean(phase['route'] or phase['attention']),(key,'tip clipped',content(22,2))
            shot('prep-'+key)
            press(0);assert 'GUIA DA FASE' in textrow(2)
            assert content(10,2)==goal,(key,'guide goal mismatch')
            assert content(16,3)==clean(phase['attention']),(key,'guide instructions clipped')
            assert content(21,3)==clean(phase['route']),(key,'guide tip clipped')
            shot('guide-'+key);press(0);press(1)
            until(lambda:state()==1 and not u8('transitioning'),'play')
            seed_progress(phase);pause()
            assert content(8,2)==goal,(key,'pause goal mismatch',content(8,2),goal)
            assert not row_content(10),(key,'pause goal overflow')
            status=content(12,2)
            for term in progress[key]:assert term in status,(key,'progress',term,status)
            frozen={name:read(*syms[name]) for name in ('phaseStats','campaignRouteOps','campaignResistance','campaignFactory','campaignLaunch','dinorahHp','npcHp')}
            run(fps)
            assert frozen=={name:read(*syms[name]) for name in frozen},(key,'pause advanced simulation')
            shot('pause-'+key);press(0);until(lambda:state()==1,'resume')
            check(key,dict(goal=goal,progress=status,targetMatchesGameplay=True,threatInRoster=True,allTextFits=True,pauseFrozen=True))
        report['scope']='All current campaign nodes; RAM only selects stages, defeat and partial objective setup. UI and pause use controller input.'
        report['passed']=True;save()
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''


def main():
    namespace = {'__name__': 'mission_objectives', '__file__': str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n', 1)[0] + TAIL, str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
