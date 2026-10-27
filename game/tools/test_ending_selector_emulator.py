"""Controller-only access to all endings, with optional real-ROM movie capture.

Run with arch -x86_64 /usr/bin/python3; --movie records eight complete videos.
"""
from pathlib import Path
import sys

BOOT = Path(__file__).with_name('test_campaign_escorts_emulator.py')
TAIL = r'''
    try:
        ordinary=True  # Forbid all game RAM writes, including scenario setup.
        def ui(key):
            hold({key},8);run(8)
        run(120);ui(3);run(fps*4);ui(4);ui(1)
        until(lambda:'FASES DA CAMPANHA' in textrow(2),'phase-selector');run(fps//2)
        ui(7);until(lambda:'FINAIS DA CAMPANHA' in textrow(2),'ending-tab')
        shot('ending-selector')
        # Both categories wrap; each remembers its selection within this menu.
        ui(4);assert '> 8.' in textrow(19);ui(5);assert '> 1.' in textrow(5)
        ui(6);assert 'FASES DA CAMPANHA' in textrow(2)
        ui(7);assert 'FINAIS DA CAMPANHA' in textrow(2)
        exported=json.loads((GAME/'art/ending-slides-v1/export.json').read_text())
        tiles=(GAME/'res/ending/tiles.bin').read_bytes()
        signatures=[tiles[i*924*32:i*924*32+64] for i in range(6)]
        def current_shot():
            signature=vr(16*32,64)
            return signatures.index(signature) if signature in signatures else -1
        def start_movie(name):
            nonlocal record,encoder,audio
            if not args.movie:return
            encoder=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error',
                '-f','rawvideo','-pixel_format','rgb565le','-video_size','320x224','-framerate',str(fps),
                '-i','pipe:0','-vf','scale=960:672:flags=neighbor','-an','-c:v','libx264',
                '-preset','fast','-crf','18','-pix_fmt','yuv420p',str(out/(name+'-video.mp4'))],stdin=subprocess.PIPE)
            audio=wave.open(str(out/(name+'-audio.wav')),'wb')
            audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(round(av.timing.sample_rate))
            record=True
        def end_movie(name):
            nonlocal record,encoder,audio
            if not args.movie:return
            record=False;encoder.stdin.close();assert encoder.wait()==0
            audio.close();encoder=audio=None
            subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error',
                '-i',str(out/(name+'-video.mp4')),'-i',str(out/(name+'-audio.wav')),
                '-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',
                str(out/(name+'.mp4'))],check=True)
            (out/(name+'-video.mp4')).unlink();(out/(name+'-audio.wav')).unlink()
        for flags,sequence in enumerate(exported['sequences']):
            name='final-'+str(flags+1).zfill(2)
            start_movie(name);before=u32('vtimer');ui(1)
            for slide,index in enumerate(sequence):
                until(lambda:current_shot()==index,name+'-slide-'+str(slide),limit=fps*12)
                assert u8('campaignFlags')==flags
                hold({0,1,8},fps*4)
                assert current_shot()==index
                assert vr(16*32,924*32)==tiles[index*924*32:(index+1)*924*32]
                assert any(rgb()[176*320*3:]),'invisible captions'
                shot(name+'-'+exported['scenes'][index]['panel'])
            until(lambda:'FINAIS DA CAMPANHA' in textrow(2),name+'-return',limit=fps*12);run(fps//2)
            seconds=(u32('vtimer')-before)/fps
            assert 25<=seconds<=28,(name,seconds)
            # Same row stays selected after normal playback.
            assert ('> '+str(flags+1)+'.') in textrow(5+flags*2)
            end_movie(name)
            check(name,dict(flags=flags,panels=[exported['scenes'][i]['panel'] for i in sequence],
                seconds=seconds,returned_to_same_selection=True,movie=name+'.mp4' if args.movie else None))
            if flags<7:ui(5)
        # START skips without leaking through to the selector's cancel action.
        ui(1);until(lambda:current_shot()==1,'skip-entry');run(fps)
        buttons.add(3);run(fps*2)
        assert 'FINAIS DA CAMPANHA' in textrow(2)
        run(fps);assert 'FINAIS DA CAMPANHA' in textrow(2)
        buttons.clear();run(2);ui(0)
        until(lambda:'NOVO JOGO' in textrow(12),'cancel-to-title')
        # Normal new game clears the preview consequences and test mode.
        ui(5);ui(1)
        until(lambda:state()==6,'new-game-story')
        assert u8('campaignFlags')==0 and not u8('testCampaignMode')
        assert writes==0
        check('controller-only-wrap-tabs-held-start-cancel-and-new-game',True)
        report.update(passed=True,game_ram_writes=0,scope='Controller-only: title > test > endings, all8 complete previews, ordered artwork, captions,25s duration, selection restored, tab/wrap navigation, START skip/held guard, cancel to title and normal campaign reset.')
        save();print('PASS ending selector',report['region'])
    except Exception as exc:
        report['error']=repr(exc);save();shot('FAIL');raise
    finally:
        record=False
        if encoder:encoder.stdin.close();encoder.wait()
        if audio:audio.close()
        core.retro_unload_game();core.retro_deinit()
'''


def main():
    namespace = {'__name__': 'ending_selector', '__file__': str(BOOT)}
    exec(compile(BOOT.read_text().split('    try:\n', 1)[0]+TAIL, str(__file__), 'exec'), namespace)
    return namespace['main']()


if __name__ == '__main__':
    sys.path.insert(0, str(BOOT.parent))
    main()
