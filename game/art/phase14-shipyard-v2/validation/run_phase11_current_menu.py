from pathlib import Path
import sys
G=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(G/'tools'))
import test_phase11_factory_emulator as suite
old="""run(120);ui(3);run(fps*4);ui(5,3);ui(1);run(fps);ui(7);ui(5,3);ui(1)
        until(lambda:state()==0 and u8('pendingLevel')==4,'selector-prep',fps*20)"""
new="""run(120);press(3);run(fps*4);press(1);until(lambda:state()==6,'story');run(fps);press(3)
        until(lambda:state()==0 and 'A: COMEÇAR' in textrow(26) and not u8('transitioning'),'prep')"""
assert old in suite.TAIL
# Adapt only the historic menu entry to the current title flow; all phase11
# checks, operation, rendering and gameplay code remain the existing suite.
namespace={'__name__':'phase11_current_menu_regression','__file__':str(suite.BOOT)}
exec(compile(suite.BOOT.read_text().split('    try:\n',1)[0]+suite.TAIL.replace(old,new),str(p:=Path(__file__)),'exec'),namespace)
namespace['main']()
