"""Assemble existing emulator captures and countdown proposals into a review flow."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
ART = ROOT.parents[1]
GAME = ART.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rom = GAME / 'out/release/Plaguefall.bin'
    before = sha(rom)
    sources = [
        (ART/'dialogue-holodeck-v1/validation/ntsc/radio-padre.png', '01-conversa-padre.png', 'Conversa · Padre', 6000),
        (ART/'dialogue-holodeck-v1/validation/ntsc/radio-damiao.png', '02-conversa-damiao.png', 'Conversa · Damião', 5000),
        (ART/'mission-ux-v1/validation/ntsc/prep-1.png', '03-objetivo.png', 'Objetivo da missão', 6000),
    ]
    shared = []
    for src, name, label, duration in sources:
        shutil.copy2(src, ROOT/name)
        im = Image.open(src).convert('RGB')
        assert im.size == (320,224)
        shared.append((im, duration))
    models = []
    for number, name in ((1,'monitor-radio'),(2,'cartao-missao'),(3,'console-dividido')):
        frames = shared[:]
        counts = []
        for digit in (3,2,1):
            src = ROOT.parent/f'{number:02d}-{name}-{digit}-native.png'
            dest = f'{number:02d}-{name}-{digit}.png'
            shutil.copy2(src, ROOT/dest)
            im = Image.open(src).convert('RGB')
            assert im.size == (320,224)
            frames.append((im,1000))
            counts.append(dest)
        output = ROOT/f'sequencia-{number:02d}-{name}.gif'
        large = [im.resize((960,672),Image.Resampling.NEAREST) for im,_ in frames]
        large[0].save(output,save_all=True,append_images=large[1:],duration=[ms for _,ms in frames],loop=0,disposal=2,optimize=False)
        check = Image.open(output)
        assert check.n_frames == 6
        for i, (im, duration) in enumerate(frames):
            check.seek(i)
            assert check.info['duration'] == duration
            assert ImageChops.difference(check.convert('RGB'),large[i]).getbbox() is None
        models.append({'id':number,'name':name,'countdownFrames':counts,'animation':output.name})
    assert sha(rom) == before
    report = {'status':'preview_only','romChanged':False,'romSHA256':before,'sequence':['Padre','Damião','Objetivo','3','2','1'],'durationsMs':[6000,5000,6000,1000,1000,1000],'note':'As falas e o objetivo avançam por tempo somente nesta prévia; no jogo dependem de A. A contagem mantém um segundo por número. Conversa e objetivo são capturas existentes do emulador; contagens são propostas compostas com recursos nativos. Não é uma gravação da ROM com a proposta integrada.','sources':[{ 'path':str(src.relative_to(GAME)), 'sha256':sha(src),'copy':name } for src,name,_,_ in sources],'models':models}
    (ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'sequences':3,'framesPerSequence':6,'durationSeconds':20,'pixelsPreserved':True,'romChanged':False}))


if __name__ == '__main__':
    main()
