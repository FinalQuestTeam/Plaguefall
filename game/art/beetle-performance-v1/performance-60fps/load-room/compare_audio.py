from pathlib import Path
import subprocess,tempfile
import argparse
a=argparse.ArgumentParser();a.add_argument('parent',type=Path);a.add_argument('candidate',type=Path);args=a.parse_args()
p=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='plaguefall-load-audio-') as tmp:
 t=Path(tmp);(t/'trace.c').write_text('#define main checks_main\n#include "'+str(p/'native/music_test.c')+'"\n#undef main\nint main(void){for(pal=0;pal<2;pal++)for(u8 track=0;track<MUSIC_TRACK_COUNT;track++){vtimer=0;AUDIO_silenceAll();MUSIC_selectTrack(track);MUSIC_setRamp(1,16,8,4);MUSIC_init();MUSIC_setEnemies(8);printf("%u %u %08x\\n",pal,track,forward(10000));}return 0;}\n')
 logs=[]
 for name,build_root in [('parent',args.parent),('candidate',args.candidate)]:
  src=build_root/'src/system/audio';binary=t/name
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(p/'native/audio'),'-I'+str(src),str(t/'trace.c'),str(src/'music.c'),str(src/'audio.c'),'-o',str(binary)],check=True)
  logs.append(subprocess.check_output([str(binary)],text=True))
 assert logs[0]==logs[1],logs
 print('80,000 audio frames: identical PSG voice/envelope hashes at 50/60Hz in all four tracks.\n'+logs[1])
