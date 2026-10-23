"""Selected option 1 flow with the mission briefing inside the radio monitor.

Native UI preview only. Existing runtime resources and ROM are never written.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parent
ART = ROOT.parent
GAME = ART.parent
spec = importlib.util.spec_from_file_location('native_countdown', ART/'countdown-native-v3/render.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def objective():
    im = native.RADIO.copy()
    native.monitor(im, 8, 32, 304, 168)
    text = native.text
    palette = native.RP
    text(im, 'PREPARAÇÃO', 160, 16, palette[15], centered=True)
    text(im, 'FASE 1: PÁTIO DA IGREJA', 24, 48, palette[15])
    text(im, '1/16', 264, 48, palette[15])
    text(im, 'SUA MISSÃO', 24, 72, palette[15])
    text(im, 'ELIMINE 10 INIMIGOS.', 24, 88, palette[13])
    ImageDraw.Draw(im).line((24, 104, 295, 104), fill=palette[6])
    text(im, 'AMEAÇA PRINCIPAL', 24, 112, palette[15])
    text(im, 'SERRA-PAU VERMELHO', 24, 128, palette[13])
    text(im, 'TIROS À DISTÂNCIA.', 24, 144, palette[13])
    text(im, 'MOVA-SE PARA DESVIAR DOS TIROS.', 24, 160, palette[13])
    text(im, 'BOMBA DANIFICA A IGREJA.', 24, 176, palette[13])
    text(im, 'B: GUIA', 24, 208, palette[15])
    text(im, 'A: COMEÇAR', 216, 208, palette[15])
    return im


def main():
    rom = GAME/'out/release/Plaguefall.bin'
    before = sha(rom)
    source_folder = ART/'dialogue-holodeck-v1/validation/ntsc'
    conversations = [source_folder/'radio-padre.png', source_folder/'radio-damiao.png']
    frames = [Image.open(p).convert('RGB') for p in conversations]
    frames.append(objective())
    old = ART/'countdown-native-v3'
    for digit in (3,2,1):
        frames.append(Image.open(old/f'01-monitor-radio-{digit}-native.png').convert('RGB'))
    names = ['01-padre','02-damiao','03-objetivo-radio','04-contagem-3','05-contagem-2','06-contagem-1']
    for name, frame in zip(names,frames):
        assert frame.size == (320,224)
        frame.save(ROOT/f'{name}-native.png')
    large = [im.resize((960,672),Image.Resampling.NEAREST) for im in frames]
    large[2].save(ROOT/'objetivo-radio.png')
    durations = [6000,5000,6000,1000,1000,1000]
    output = ROOT/'sequencia-conversa-objetivo-contagem.gif'
    large[0].save(output,save_all=True,append_images=large[1:],duration=durations,loop=0,disposal=2,optimize=False)
    gif = Image.open(output)
    assert gif.n_frames == len(frames)
    for index, expected in enumerate(large):
        gif.seek(index)
        assert gif.info['duration'] == durations[index]
        assert ImageChops.difference(gif.convert('RGB'), expected).getbbox() is None
    # The selected countdown and both conversations retain every source pixel.
    for i, path in enumerate(conversations):
        assert frames[i].tobytes() == Image.open(path).convert('RGB').tobytes()
    for i, digit in enumerate((3,2,1),3):
        assert frames[i].tobytes() == Image.open(old/f'01-monitor-radio-{digit}-native.png').convert('RGB').tobytes()
    # Mission and countdown share the exact option 1 monitor frame and header.
    assert ImageChops.difference(frames[2].crop((0,0,320,40)), frames[3].crop((0,0,320,40))).getbbox() is None
    assert ImageChops.difference(frames[2].crop((0,32,24,200)), frames[3].crop((0,32,24,200))).getbbox() is None
    assert ImageChops.difference(frames[2].crop((296,32,320,200)), frames[3].crop((296,32,320,200))).getbbox() is None
    assert sha(rom) == before
    report = {'status':'preview_only','selectedOption':1,'romChanged':False,'romSHA256':before,'sequence':['Conversa: Padre','Conversa: Damião','Objetivo dentro do rádio','3','2','1'],'durationsMs':durations,'missionText':['FASE 1: PÁTIO DA IGREJA','ELIMINE 10 INIMIGOS.','SERRA-PAU VERMELHO','TIROS À DISTÂNCIA.','MOVA-SE PARA DESVIAR DOS TIROS.','BOMBA DANIFICA A IGREJA.'],'checks':{'allGifFramesPixelExact':True,'originalConversationsPreserved':True,'option1CountdownPreserved':True,'sameRadioMonitorFrameAndHeader':True},'note':'Conversa capturada no emulador; objetivo e contagem são prévias compostas com os recursos nativos. O avanço automático das falas e objetivo vale apenas para a animação; no jogo continuam por A.'}
    (ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'frames':gif.n_frames,'durationSeconds':sum(durations)//1000,'selectedOption':1,'romChanged':False}))


if __name__ == '__main__':
    main()
