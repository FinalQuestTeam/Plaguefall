"""Exercise the preserved shared-cache prototypes without changing production."""
from pathlib import Path
import argparse
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('shared', 'synchronized'), default='shared')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='plaguefall-shared-cache-test-') as tmp:
        binary = str(Path(tmp) / 'shared-cache')
        subprocess.run([
            'cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
            '-fsanitize=address,undefined',
            '-I' + str(GAME / 'art/cangaco-insects-iso60-v2/tests'),
            '-I' + str(ROOT / args.variant / 'src'),
            '-I' + str(GAME / 'src'), '-I' + str(GAME / 'res'),
            str(ROOT / 'tests/enemy_facing_test.c'), '-o', binary,
        ], check=True)
        subprocess.run([binary], check=True)


if __name__ == '__main__':
    main()
