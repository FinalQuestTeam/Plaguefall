"""Run captured graphics/audio/effect tests against the candidate's real C sources."""
from pathlib import Path
import argparse,subprocess,tempfile
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);a=p.parse_args();src=a.candidate/'src';fixture=ROOT/'native'
 flags=['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
 with tempfile.TemporaryDirectory(prefix='plaguefall-60-runtime-') as folder:
  target=Path(folder)
  for name,test in [('facing','facing_test.c'),('deaths','death_count_test.c')]:
   binary=target/name
   subprocess.run(flags+['-I'+str(fixture/'gfx'),'-I'+str(src),str(fixture/test),'-o',str(binary)],check=True)
   subprocess.run([str(binary)],check=True)
  binary=target/'music'
  subprocess.run(flags+['-I'+str(fixture/'audio'),'-I'+str(src/'system/audio'),str(fixture/'music_test.c'),str(src/'system/audio/music.c'),str(src/'system/audio/audio.c'),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True)
if __name__=='__main__':main()
