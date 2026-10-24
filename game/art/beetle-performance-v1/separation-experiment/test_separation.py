"""Validate experimental separation routines against the captured production one."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[2]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('build_root',type=Path,nargs='?');args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='plaguefall-separation-native-') as tmp:
        reference=args.build_root/'original-separate.inc' if args.build_root else ROOT/'captured-reference.inc'
        shutil.copyfile(reference,Path(tmp)/'original-separate.inc')
        binary=str(Path(tmp)/'separation')
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined',
                        '-I'+str(GAME/'art/cangaco-insects-iso60-v2/tests'),
                        '-I'+str(GAME/'src'),'-I'+tmp,
                        str(ROOT/'separation_test.c'),'-o',binary],check=True)
        subprocess.run([binary],check=True)


if __name__=='__main__':main()
