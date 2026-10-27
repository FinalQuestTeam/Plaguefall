"""Label and join the eight actual-ROM captures; keep every slide and its audio."""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

GAME = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=GAME/'art/ending-slides-v1/videos')
    args = parser.parse_args()
    dest = args.directory.resolve()
    font = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    ffmpeg, ffprobe = '/opt/homebrew/bin/ffmpeg', '/opt/homebrew/bin/ffprobe'
    chapters, entries, segments = [';FFMETADATA1'], [], []
    elapsed = 0
    with tempfile.TemporaryDirectory(prefix='plaguefall-ending-video-') as folder:
        work = Path(folder)
        for flags in range(8):
            source = dest/f'final-{flags+1:02}.mp4'
            label = ' | '.join(('IGREJA EM RUÍNAS' if flags&1 else 'IGREJA PRESERVADA',
                'POPULAÇÃO COM PERDAS' if flags&2 else 'POPULAÇÃO SALVA',
                'DINORAH MORTA' if flags&4 else 'DINORAH VIVA'))
            header = work/f'{flags}.png'
            image = Image.new('RGB',(960,88),'black')
            draw = ImageDraw.Draw(image)
            draw.text((24,12),f'FINAL {flags+1:02} / 08',font=ImageFont.truetype(str(font),24),fill='white')
            draw.text((24,48),label,font=ImageFont.truetype(str(font),22),fill='white')
            image.save(header)
            segment = work/source.name
            filters = '[0:v]pad=iw:ih+88:0:88:color=black[video];[video][1:v]overlay=0:0:format=auto[v]'
            subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(source),'-i',str(header),
                '-filter_complex',filters,'-map','[v]','-map','0:a:0',
                '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','copy',str(segment)],check=True)
            info = json.loads(subprocess.check_output([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(segment)],text=True))
            seconds = float(info['format']['duration'])
            end = elapsed+round(seconds*1000)
            chapters += ['[CHAPTER]','TIMEBASE=1/1000',f'START={elapsed}',f'END={end}',f'title=Final {flags+1:02} - {label}']
            entries.append(dict(final=flags+1,flags=flags,conditions=label,start_seconds=elapsed/1000,seconds=seconds,video=source.name))
            elapsed=end;segments.append(segment)
        listing=work/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in segments))
        metadata=work/'chapters.txt';metadata.write_text('\n'.join(chapters)+'\n')
        output=dest/'todos-os-finais.mp4'
        subprocess.run([ffmpeg,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),
            '-i',str(metadata),'-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(output)],check=True)
    report=json.loads((dest/'report.json').read_text())
    assert report['passed'] and report['game_ram_writes']==0
    (dest/'index.json').write_text(json.dumps(dict(rom_sha256=report['romSHA256'],video=output.name,
        source='Genesis Plus GX, production ROM, controller-only test selector',chapters=entries),ensure_ascii=False,indent=2)+'\n')
    print(f'{output}: {elapsed/1000:.2f}s, 8 complete endings, audio and chapter labels')


if __name__=='__main__':
    main()
