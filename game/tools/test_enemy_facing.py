"""Run the real enemy graphics loader with recorded ROM offsets and DMA."""
from pathlib import Path
import subprocess
import tempfile

GAME = Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='plaguefall-enemy-facing-') as tmp:
        binary = str(Path(tmp)/'enemy-facing')
        subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined',
                        '-I'+str(GAME/'art/cangaco-insects-iso60-v2/tests'),
                        '-I'+str(GAME/'src'), '-I'+str(GAME/'res'),
                        str(GAME/'tests/enemy_facing_test.c'), '-o', binary], check=True)
        subprocess.run([binary], check=True)

if __name__ == '__main__':
    main()
