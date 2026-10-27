"""Exercise the production boss state machine at50/60Hz under ASan/UBSan."""
from pathlib import Path
import os, shlex, subprocess, tempfile
from test_player_aim import STUBS, ROOT

def main():
    with tempfile.TemporaryDirectory(prefix='plaguefall-boss-phase2-') as tmp:
        folder=Path(tmp)
        stubs={'genesis.h':STUBS['genesis.h'].replace('#endif','u32 getApproximatedDistance(s16,s16);\n#endif'),
               'core/game.h':'#include <genesis.h>\nextern u16 fps;extern s16 px,py;\n'}
        for name,data in stubs.items():
            p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
        binary=folder/'boss'
        subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c99','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-I'+str(folder),'-I'+str(ROOT/'game/src'),
                        str(ROOT/'game/tests/boss_phase2_test.c'),str(ROOT/'game/src/enemies/enemy_boss.c'),
                        '-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)

if __name__=='__main__':main()
