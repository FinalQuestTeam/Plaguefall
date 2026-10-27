"""Exhaustive production password roundtrips and single-symbol errors, ASan/UBSan."""
from pathlib import Path
import os, shlex, subprocess, tempfile
from test_player_aim import STUBS, ROOT

def main():
    with tempfile.TemporaryDirectory(prefix='plaguefall-signal-') as tmp:
        folder=Path(tmp)
        for name,data in {'genesis.h':STUBS['genesis.h'],
                          'levels/levels.h':'typedef struct { int unused; } LevelDef;\n'}.items():
            path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data)
        binary=folder/'signal'
        subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c99','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-I'+str(folder),'-I'+str(ROOT/'game/src'),
            str(ROOT/'game/tests/signal_test.c'),str(ROOT/'game/src/core/signal.c'),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)

if __name__=='__main__':main()
