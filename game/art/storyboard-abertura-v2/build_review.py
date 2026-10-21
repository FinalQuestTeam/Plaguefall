"""Render only the proposed storyboard. Never export game resources or a ROM."""
from pathlib import Path
import hashlib
import html
import json
import textwrap
import unicodedata
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
SPEC = json.loads((ROOT / 'storyboard.json').read_text())
INTEGRATED = SPEC.get('integrated', False)
STATUS = 'Aprovado e integrado à ROM' if INTEGRATED else 'Proposta para aprovação'
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
FONTS = {key: ImageFont.truetype(str(FONT_DIR / name), size) for key, name, size in [
    ('hero', 'Arial Bold.ttf', 49), ('heading', 'Arial Bold.ttf', 27),
    ('body', 'Arial.ttf', 25), ('small', 'Arial.ttf', 21), ('tiny', 'Arial.ttf', 19),
]}
BG, PAPER, INK, MUTED, ACCENT = '#ede6d8', '#faf7ef', '#232526', '#626666', '#9c411f'


def clock(seconds):
    return f'{int(seconds)//60:02}:{int(seconds)%60:02}'


def game_text(text):
    return unicodedata.normalize('NFKD', text.replace('…', '...')).encode('ascii', 'ignore').decode().upper()


def lines(text, width=36):
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)


def draw_wrapped(draw, text, xy, font, fill, max_width, line_height):
    x, y = xy
    row = ''
    for word in text.split():
        candidate = f'{row} {word}'.strip()
        if row and draw.textlength(candidate, font=font) > max_width:
            draw.text((x, y), row, font=font, fill=fill)
            y += line_height
            row = word
        else:
            row = candidate
    if row:
        draw.text((x, y), row, font=font, fill=fill)
        y += line_height
    return y


def prepare():
    t = 0
    caption_id = 0
    for shot in SPEC['shots']:
        shot['start'] = t
        source = shot['source']
        if 'sheet' in source:
            path = GAME / f'art/storyboard-abertura-v1/prancha-{source["sheet"]:02}.png'
        else:
            path = ROOT / source['file']
        image = Image.open(path).convert('RGB')
        if 'box' in source:
            image = image.crop(tuple(source['box']))
        framed = ImageOps.fit(image, (640, 352), Image.Resampling.LANCZOS, centering=tuple(source['center']))
        (ROOT / 'quadros').mkdir(exist_ok=True)
        shot['image'] = f'quadros/{shot["id"]:02}.png'
        framed.save(ROOT / shot['image'])
        for caption in shot['captions']:
            caption_id += 1
            caption['id'] = caption_id
            caption['start'] = t
            caption['lines'] = lines(game_text(caption['text']))
            caption['typed_seconds'] = round(sum(map(len, caption['lines'])) / 36, 2)
            assert len(caption['lines']) <= 4, caption
            assert all(len(line) <= 36 for line in caption['lines']), caption
            assert caption['seconds'] - caption['typed_seconds'] >= 1.5, caption
            t += caption['seconds']
            caption['end'] = t
        shot['end'] = t
        shot['seconds'] = t - shot['start']
    SPEC['total_seconds'] = t
    SPEC['caption_count'] = caption_id
    assert len(SPEC['shots']) == 14 and caption_id == 18 and t == 101


def make_boards():
    for index, selected in enumerate((SPEC['shots'][:8], SPEC['shots'][8:], SPEC['shots'][8:10]), 1):
        rows = (len(selected) + 1) // 2
        sheet = Image.new('RGB', (1536, 206 + rows * 684 + 65), BG)
        d = ImageDraw.Draw(sheet)
        d.text((48, 28), 'PLAGUEFALL', font=FONTS['small'], fill=ACCENT)
        d.text((48, 62), (f'O sonho atendido / prancha {index:02}' if index < 3 else 'O preço / Por quem ele fica'), font=FONTS['hero'], fill=INK)
        d.text((48, 126), f'{STATUS} • 14 planos • 18 cartelas • 1min41s • 21/10/2026', font=FONTS['small'], fill=MUTED)
        d.text((48, 160), 'Leitura: esquerda → direita, de cima para baixo. Tempos incluem os fades.', font=FONTS['tiny'], fill=MUTED)
        for n, shot in enumerate(selected):
            x, y = 48 + n % 2 * 744, 206 + n // 2 * 684
            d.rounded_rectangle((x, y, x + 696, y + 662), radius=9, fill=PAPER)
            label = f'{shot["id"]:02}  {shot["title"]}'
            d.text((x + 18, y + 14), label, font=FONTS['heading'], fill=INK)
            meta = f'{clock(shot["start"])}–{clock(shot["end"])}  /  {shot["seconds"]}s'
            if shot.get('new_art'):
                meta += '  /  CARD NOVO'
            d.text((x + 18, y + 52), meta, font=FONTS['small'], fill=ACCENT)
            sheet.paste(Image.open(ROOT / shot['image']), (x + 28, y + 88))
            cursor = y + 456
            for caption in shot['captions']:
                label = f'{clock(caption["start"])}–{clock(caption["end"])} · {caption["speaker"]}'
                d.text((x + 20, cursor), label, font=FONTS['tiny'], fill=MUTED)
                cursor = draw_wrapped(d, caption['text'], (x + 20, cursor + 27), FONTS['body'], INK, 653, 30) + 11
            assert cursor < y + 657, (shot['id'], cursor - y)
        d.text((48, sheet.height - 48), ('Storyboard aprovado; versão nativa e vídeo real em art/intro-monologo-v2.' if INTEGRATED else 'Artes de direção; jogo aguardando aprovação.'), font=FONTS['tiny'], fill=MUTED)
        sheet.save(ROOT / (f'prancha-{index:02}.png' if index < 3 else 'revisao-09-10.png'))


def make_markdown():
    out = ['# Storyboard revisado — o sonho atendido', '',
        f'**Status:** {STATUS.lower()} em 21/10/2026.', '',
        '**Duração:** 1min41s de monólogo, com 14 planos ilustrados e 18 cartelas de texto. Logos anteriores não entram nessa conta. A execução foi conferida no Genesis Plus GX em 50/60Hz; veja os relatórios da integração.', '',
        'O texto segue integralmente a última versão enviada pelo usuário, incluindo as duas perguntas sobre o Diabo. O ritmo passa por provocação, sonho, ofício, retorno das naves, ovos, ausência, invasores, custo pessoal, proteção, reza, rádio e decisão.', '',
        '## Pranchas', '',
        '![Planos 01–08](../../art/storyboard-abertura-v2/prancha-01.png)', '',
        '![Planos 09–14](../../art/storyboard-abertura-v2/prancha-02.png)', '',
        '[Prévia com tempos e navegação](../../art/storyboard-abertura-v2/revisao.html) · [Fonte das falas e tempos](../../art/storyboard-abertura-v2/storyboard.json)', '',
        '## Ritmo e leitura', '',
        '- Os tempos abaixo já incluem entrada e saída visual de 0,4s por plano; não somar fades novamente.',
        '- Nos planos 08, 11, 12 e 13, trocar somente a legenda no instante indicado, conservando a imagem e a música. São 14 imagens e 18 cartelas, não 18 cargas de imagem.',
        '- As falas foram separadas em blocos de até 36 colunas × 4 linhas. A simulação usa a cadência atual de 36 caracteres por segundo e conserva pelo menos 1,5s após completar cada bloco; a janela útil depende também da leitura durante a digitação.',
        '- Prévia sem áudio. Voz, chiado e efeitos descritos são direção, não gravações produzidas nesta etapa. A ROM atual apresenta as falas em texto.',
        '- A mãe permanece fora de quadro e sem indícios que confirmem vida ou morte. Na lembrança de trabalho, Damião tem dois braços biológicos; no presente, a prótese é esquerda. O padre fica sem chapéu.', '',
        '## Montagem plano a plano', '']
    for shot in SPEC['shots']:
        out += [f'### {shot["id"]:02} · {shot["title"]} · {clock(shot["start"])}–{clock(shot["end"])}', '',
                f'![{shot["title"]}](../../art/storyboard-abertura-v2/{shot["image"]})', '',
                f'**Imagem e ação:** {shot["direction"]}', '']
        for caption in shot['captions']:
            out += [f'**{caption["speaker"]} — {clock(caption["start"])}–{clock(caption["end"])} ({caption["seconds"]}s):**', '',
                    f'> {caption["text"]}', '', '**Quebra proposta para a tela:**', '', '```text', *caption['lines'], '```', '']
        out += [f'**Som e interpretação:** {shot["sound"]}', '',
                '**Arte:** ' + ('card novo de pré-produção.' if shot.get('new_art') else 'arte existente com novo lugar na sequência ou novo enquadramento.'), '']
    if INTEGRATED:
        out += ['## Integração ao jogo', '',
            'A montagem foi aprovada e integrada em 21/10/2026. O exportador usa este JSON para gerar 14 imagens e 18 cartelas, com duas legendas sobre uma mesma imagem nos planos 08, 11, 12 e 13.', '',
            'A trilha foi reordenada e estendida para 4s de logo, 101s de monólogo e 3s de sustentação. A música não reinicia nas trocas de imagem ou texto.', '',
            '[Implementação, vídeo e verificação em 50/60Hz](../../art/intro-monologo-v2/README.md). Os testes conferem as 18 cartelas e os 14 planos, incluindo a limpeza do texto anterior, START, menu e início da fase 1.', '']
    else:
        out += ['## Depois da aprovação', '',
            '1. Adaptar o exportador e o formato das falas para várias cartelas por imagem; a estrutura atual tem uma legenda por plano e 12 imagens fixas.',
            '2. Converter os quatro cards novos para as paletas e tiles do hardware, conferir os novos enquadramentos e atualizar os recursos somente após aprovação.',
            '3. Ajustar a trilha contínua: a reserva atual é de 96s incluindo 4s de logo. A proposta exige pelo menos 105s desde o logo, mais margem para cargas e saída; reorganizar os trechos de sonho, ameaça, reza e decisão sem reinícios por imagem.',
            '4. Conferir reprodução em 50/60Hz, leitura das 18 cartelas, continuidade musical, START e chegada ao menu. Medir a duração final incluindo cargas.', '',
            'A aprovação solicitada é do roteiro visual, da ordem dos 14 planos e dos tempos de leitura. A implementação continua na versão anterior até a aprovação do usuário.', '']

    (GAME / 'doc/historia/storyboard-abertura-v2.md').write_text('\n'.join(out))


def make_html():
    payload = json.dumps(SPEC, ensure_ascii=False).replace('</', '<\\/')
    template = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plaguefall — revisão da abertura</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#151719;color:#eee9df;font:16px/1.5 system-ui,sans-serif}main{max-width:1170px;margin:auto;padding:32px 28px}small,.meta{color:#b5ada2}h1{font-size:35px;line-height:1.15;margin:9px 0 12px}h2{font-size:22px}.eyebrow{color:#df9c59;font-size:12px;letter-spacing:.14em}.intro{max-width:820px;color:#ccc4b8}.player{margin-top:26px;display:grid;grid-template-columns:minmax(0,2fr) minmax(240px,1fr);gap:24px}.screen{position:relative;background:black;aspect-ratio:320/224;overflow:hidden}.art{display:block;width:100%;height:78.5714%;object-fit:cover}.caption{height:21.4286%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font:clamp(10px,1.65vw,19px)/1.17 monospace;text-align:center;white-space:pre;overflow:hidden}.stagewrap{min-width:0}.controls{display:flex;gap:8px;margin-top:12px;align-items:center;flex-wrap:wrap}button,a.action{background:#323435;color:#fff;border:1px solid #565654;padding:9px 13px;border-radius:5px;font:inherit;cursor:pointer;text-decoration:none}button:hover,button[aria-current=true]{border-color:#e2a569;color:#ffca91}#play{background:#aa522b;border-color:#d17b43}input[type=range]{width:100%;accent-color:#d17b43;margin:16px 0 5px}.time{font-variant-numeric:tabular-nums;white-space:nowrap}.detail{font-size:14px}.detail p{color:#c6bdb2}.new{color:#ffd39b;font-size:12px}nav{display:grid;grid-template-columns:repeat(7,1fr);gap:7px;margin-top:24px}nav button{font-size:13px;padding:9px 5px;text-align:center}.notice{background:#272622;border-left:3px solid #c38955;padding:14px 17px;margin:24px 0;font-size:14px;color:#d9d0c4}.boards{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}.boards img{width:100%;display:block}.boards a{color:#efb373;text-decoration:none}.footer{font-size:13px;color:#a69d90;margin-top:30px}@media(max-width:850px){.player{grid-template-columns:1fr}.caption{font-size:clamp(10px,2.5vw,18px)}nav{grid-template-columns:repeat(4,1fr)}.boards{grid-template-columns:1fr}}@media print{body{background:white;color:black}.player,nav,.notice,.footer,.intro{display:none}.boards{display:block}.boards a{display:block;break-after:page}.boards img{max-height:95vh;width:auto;max-width:100%;margin:auto}main{padding:0}h1,.eyebrow{display:none}}
</style><main><div class="eyebrow">PLAGUEFALL / STORYBOARD PARA APROVAÇÃO</div><h1>O sonho atendido</h1><div class="meta">14 planos · 18 cartelas · 1min41s · revisão de 21/10/2026</div><p class="intro">A provocação sobre o Diabo abre a sequência. O sonho vira trabalho, a volta das naves revela os ovos e o rádio transforma o desabafo em uma decisão. Os novos cards mostram os ovos, a prótese esquerda, as pessoas abrigadas e a retirada dos civis.</p>
<div class="player"><div class="stagewrap"><div class="screen"><img id="art" class="art" alt=""><div id="caption" class="caption" aria-live="off"></div></div><input id="seek" aria-label="Posição na abertura" type="range" min="0" max="101" step="0.05" value="0"><div class="controls"><button id="prev" aria-label="Plano anterior">←</button><button id="play">Reproduzir</button><button id="next" aria-label="Próximo plano">→</button><button id="reset">Reiniciar</button><span class="time" id="time"></span></div><small>Prévia sem áudio · tempos incluem fades · arraste a barra ou selecione um plano.</small></div><aside class="detail"><div class="new" id="new"></div><h2 id="title"></h2><div class="meta" id="shotTime"></div><p id="direction"></p><p id="sound"></p></aside></div><nav aria-label="Planos do storyboard" id="nav"></nav>
<div class="notice">Proposta de pré-produção. Artes ainda sem conversão para as paletas do Mega Drive. O texto segue a versão integral aprovada na conversa; código, recursos e ROM aguardam sua aprovação. A música precisará de extensão para acompanhar a nova duração.</div><h2>Pranchas para leitura</h2><div class="boards"><a href="prancha-01.png"><img src="prancha-01.png" alt="Prancha 1: planos 01 a 08"></a><a href="prancha-02.png"><img src="prancha-02.png" alt="Prancha 2: planos 09 a 14"></a></div><p class="footer"><a class="action" href="../../doc/historia/storyboard-abertura-v2.md">Roteiro e direção completos</a> <a class="action" href="storyboard.json">Falas e tempos</a></p></main>
<script>const spec=__SPEC__;
const shots=spec.shots;const $=id=>document.getElementById(id);let t=0,playing=false,then=0,lastShot=-1;const clock=s=>Math.floor(s/60).toString().padStart(2,'0')+':'+Math.floor(s%60).toString().padStart(2,'0');
const indexAt=x=>Math.max(0,shots.findIndex((s,i)=>x<s.end||i===shots.length-1));
shots.forEach((s,i)=>{const b=document.createElement('button');b.textContent=String(s.id).padStart(2,'0')+' · '+clock(s.start);b.title=s.title;b.onclick=()=>jump(s.start);$('nav').append(b);const img=new Image();img.src=s.image;});
function render(){const i=indexAt(t),s=shots[i];if(i!==lastShot){$('art').src=s.image;$('art').alt=s.title;$('title').textContent=String(s.id).padStart(2,'0')+' · '+s.title;$('shotTime').textContent=clock(s.start)+'–'+clock(s.end)+' / '+s.seconds+'s';$('direction').textContent=s.direction;$('sound').textContent=s.sound;$('new').textContent=s.new_art?'CARD NOVO':'ARTE EXISTENTE · MONTAGEM REVISADA';[...$('nav').children].forEach((b,j)=>b.setAttribute('aria-current',String(i===j)));lastShot=i;}const c=s.captions.find(c=>t<c.end)||s.captions.at(-1);let chars=playing?Math.floor(Math.max(0,t-c.start)*spec.typing_characters_per_second):Infinity;$('caption').replaceChildren(...c.lines.map(line=>{const div=document.createElement('div');div.textContent=line.slice(0,Math.max(0,chars));chars-=line.length;return div;}));const local=t-s.start,remaining=s.end-t;const a=playing?Math.max(0,Math.min(1,local/spec.fade_seconds,remaining/spec.fade_seconds)):1;$('art').style.opacity=a;$('seek').value=t;$('time').textContent=clock(t)+' / '+clock(spec.total_seconds);$('play').textContent=playing?'Pausar':'Reproduzir';}
function jump(x){t=Math.min(spec.total_seconds,Math.max(0,x));then=performance.now();render();}
$('play').onclick=()=>{if(t>=spec.total_seconds)t=0;playing=!playing;then=performance.now();render();};$('reset').onclick=()=>{playing=false;jump(0)};$('prev').onclick=()=>jump(shots[Math.max(0,indexAt(t)-1)].start);$('next').onclick=()=>jump(shots[Math.min(shots.length-1,indexAt(t)+1)].start);$('seek').oninput=e=>jump(Number(e.target.value));function tick(now){if(playing){t=Math.min(spec.total_seconds,t+(now-then)/1000);if(t>=spec.total_seconds)playing=false;render()}then=now;requestAnimationFrame(tick)}render();requestAnimationFrame(tick);
</script></html>'''
    if INTEGRATED:
        template = template.replace('STORYBOARD PARA APROVAÇÃO', 'STORYBOARD APROVADO E INTEGRADO')
        template = template.replace('Proposta de pré-produção. Artes ainda sem conversão para as paletas do Mega Drive. O texto segue a versão integral aprovada na conversa; código, recursos e ROM aguardam sua aprovação. A música precisará de extensão para acompanhar a nova duração.', 'Storyboard aprovado e integrado à ROM. Esta página conserva as artes de direção. A versão nativa, o vídeo real e os relatórios em 50/60Hz estão em <a href="../intro-monologo-v2/README.md">abertura integrada</a>.')
    (ROOT / 'revisao.html').write_text(template.replace('__SPEC__', payload))


def verify():
    baseline = json.loads((ROOT / 'game-baseline.json').read_text())
    unchanged = all(hashlib.sha256((GAME.parent / path).read_bytes()).hexdigest() == digest for path, digest in baseline.items())
    if not INTEGRATED:
        assert unchanged, 'Game changed during storyboard preparation'
    report = {
        'status': STATUS, 'shots': len(SPEC['shots']),
        'caption_count': SPEC['caption_count'], 'seconds': SPEC['total_seconds'],
        'new_illustrated_shots': [s['id'] for s in SPEC['shots'] if s.get('new_art')],
        'max_rows': max(len(c['lines']) for s in SPEC['shots'] for c in s['captions']),
        'max_columns': max(len(row) for s in SPEC['shots'] for c in s['captions'] for row in c['lines']),
        'min_seconds_after_typing': min(round(c['seconds'] - c['typed_seconds'], 2) for s in SPEC['shots'] for c in s['captions']),
        'game_files_hash_checked': len(baseline), 'game_files_unchanged': unchanged, 'integrated': INTEGRATED,
        'caption_timeline': [c for s in SPEC['shots'] for c in s['captions']],
        'preview': 'silenciosa, arte de direção; sem quantização VDP',
    }
    (ROOT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'caption_timeline'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    prepare()
    make_boards()
    make_markdown()
    make_html()
    verify()
