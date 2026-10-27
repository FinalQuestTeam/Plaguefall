"""Current19-node result capture and retry, including dense streamed scenes."""
from pathlib import Path
import sys
BOOT=Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL=r'''
    try:
        import re
        graph=(GAME/'src/levels/graph.h').read_text().split('N_1 = 1,',1)[1].split('NODE_MAX',1)[0]
        names=['N_1']+re.findall(r'N_\d+[AB]?',graph)
        run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep');baseline=snapshot()
        rows=[]
        for node,name in enumerate(names,1):
            restore(baseline);write(syms['pendingLevel'][0],bytes([node]));press(1)
            until(lambda:state()==1 and not u8('transitioning'),'play');isolate();w16('hp',0)
            until(lambda:state()==3 and u8('resultActive'),'defeat-card',limit=fps*12);run(2)
            end=u16('cardBase')+32*u16('cardHeight')
            assert end<=1536 and not u16('resultCaptureFault'),('result capture',name,end,u16('resultCaptureFault'))
            assert u32('work')==0 and u32('persistent')==0,'finished scene cache retained'
            shot(name+'-defeat');run(fps);press(3)
            until(lambda:state() in (0,6) and not u8('transitioning'),'retry-preparation')
            assert u8('pendingLevel')==node and not u8('resultActive')
            if state()==6:run(fps);press(3)
            until(lambda:state()==0 and not u8('transitioning'),'retry-mission');press(1)
            until(lambda:state()==1 and not u8('transitioning'),'retry-gameplay')
            assert u8('currentLevel')==node and u16('hp')==100 and not u16('sceneStreamFaults')
            rows.append(dict(node=name,card_end=end,defeat_card=True,retry_same_node=True,live_cache_released=True,reloaded_without_cache_faults=True))
            check('all-current-campaign-result-captures',rows)
        report['scope']='Every current campaign node: RAM sets node/zero health, production death settlement/result card and controller retry. Pattern writes stay below BG_B at tile1536; finished cache is freed; retry reloads the same phase and cache without faults. Card borrows/restores font tiles; source metadata is derived from the current graph.'
        report['passed']=True;save();print('PASS current campaign result captures',report['region'])
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:core.retro_unload_game();core.retro_deinit()
'''

def main():
    namespace={'__name__':'result_capture_current','__file__':str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n',1)[0]+TAIL,str(__file__),'exec'),namespace)
    return namespace['main']()

if __name__=='__main__':
    sys.path.insert(0,str(BOOT.parent));main()
