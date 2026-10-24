"""Production player/autofire and projectile pools under ASan/UBSan."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

from test_death_rules import ROOT, STUBS


def main():
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    src = ROOT / 'game/src'
    with tempfile.TemporaryDirectory(prefix='plaguefall-player-shots-') as tmp:
        folder = Path(tmp)
        for name, data in STUBS.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
        binary = folder / 'player-shots'
        subprocess.run([*compiler, '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-I'+str(folder), '-I'+str(src),
                        str(ROOT / 'game/tests/player_shots_test.c'),
                        *[str(src / name) for name in ('actors/player.c', 'actors/shots.c',
                                                     'actors/shots_player.c')],
                        '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
