"""Exercise the production portable-terrain C renderer under sanitizers."""
from pathlib import Path
import subprocess
import tempfile

GAME = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='plaguefall-terrain-') as tmp:
        binary = str(Path(tmp)/'terrain-test')
        subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-I'+str(GAME/'tests/terrain'),
                        '-I'+str(GAME/'src'), str(GAME/'tests/terrain/terrain_test.c'),
                        '-o', binary], check=True)
        subprocess.run([binary], check=True)


if __name__ == '__main__':
    main()
