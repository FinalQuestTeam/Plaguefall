"""Compõe PDF e roteiro do storyboard sem editar as imagens geradas."""
from pathlib import Path
import json
import html
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PDF = ROOT / 'output/pdf/plaguefall-storyboard-campanha-v1.pdf'
MD = ROOT / 'game/doc/historia/storyboard-campanha.md'
DATA = json.loads((HERE / 'quadros.json').read_text())
OPENING = json.loads((ROOT / 'game/art/storyboard-abertura-v2/storyboard.json').read_text())
INTRO_CAPTURES = ROOT / 'game/art/intro-monologo-v2/emulator-ntsc'
FONT = Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('Body', str(FONT / 'Arial.ttf')))
pdfmetrics.registerFont(TTFont('Bold', str(FONT / 'Arial Bold.ttf')))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
W, H = 1190.55, 841.89
INK, PAPER, MUTED, ACCENT = map(HexColor, ['#172529', '#f6f0e5', '#546568', '#9e432e'])
ST = ParagraphStyle('body', fontName='Body', fontSize=13, leading=18, textColor=INK)
SM = ParagraphStyle('small', parent=ST, fontSize=11, leading=15)
TITLE = ParagraphStyle('title', parent=ST, fontName='Bold', fontSize=18, leading=22)
checks = []

def para(c, text, x, y, width, style=ST):
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, y-height)
    return y-height

def esc(text):
    return html.escape(text)

def page(c, section, subtitle=''):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(ACCENT); c.rect(36, H-42, 9, 9, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont('Bold', 13)
    c.drawString(56, H-42, 'PLAGUEFALL  /  STORYBOARD DA CAMPANHA')
    c.setFont('Body', 11); c.drawRightString(W-36, H-42, section)
    if subtitle:
        para(c, esc(subtitle), 36, H-65, W-72, SM)
    c.setStrokeColor(HexColor('#d5c9b7')); c.line(36, 39, W-36, 39)
    c.setFont('Body', 9); c.setFillColor(MUTED)
    c.drawString(36, 24, '23 OUT 2026  |  Abertura já integrada  |  Campanha proposta em pré-produção')
    c.drawRightString(W-36, 24, f'{c.getPageNumber():02d}')

def finish(c):
    c.showPage()

def cover(c):
    page(c, 'Visão geral')
    y = H-115
    c.setFillColor(INK); c.setFont('Bold', 42); c.drawString(36, y, 'Da abertura do jogo ao estaleiro')
    y = para(c, '14 planos da abertura existente + 28 quadros da campanha | 16 fases por partida', 38, y-25, W-76, TITLE)
    image = INTRO_CAPTURES / '01-complete.png'
    c.drawImage(str(image), 36, 178, width=655, height=438, preserveAspectRatio=True, anchor='c', mask='auto')
    x = 728
    y = 610
    for title, text in [
        ('00  A animação de abertura', 'A história começa na animação que já abre o jogo: 14 planos, 18 cartelas e 1min41s. Depois vêm o menu, a chamada curta e a fase 1.'),
        ('01  A retirada', 'Damião protege o povo, abre caminho e sustenta a evacuação. A igreja pode cair; as pessoas ainda podem escapar.'),
        ('02  O Último Chão', 'Nos esgotos e na base comprometida, Damião e Dinorah recuperam meios para continuar e atacam o chamado do enxame.'),
        ('03  Queimar a origem', 'A fábrica vira distração. O estaleiro vira arma. O destino de Dinorah muda quem conduz a operação final.'),
    ]:
        y = para(c, esc(title), x, y, W-x-40, TITLE)-12
        y = para(c, esc(text), x, y, W-x-40)-30
    para(c, '<b>Como ler:</b> cada prancha usa A no alto à esquerda, B no alto à direita, C embaixo à esquerda e D embaixo à direita. A página seguinte detalha os quatro quadros. Alternativas de rota não são acontecimentos consecutivos.', 36, 143, W-72)
    para(c, 'As durações e distâncias nas legendas pertencem à missão jogável. Os quadros indicam enquadramento e encenação, sem impor duração de cutscene ou câmera nova ao jogo.', 36, 88, W-72, SM)
    finish(c)

def stamp(seconds):
    return f'{seconds//60:02d}:{seconds%60:02d}'

def opening_pages(c):
    clock = 0
    shots = OPENING['shots']
    for start in range(0, len(shots), 4):
        group = shots[start:start+4]
        page(c, f'Abertura existente / {start+1:02d} a {start+len(group):02d}',
             'Capturas da animação integrada ao jogo; ordem, falas e tempos preservados. Total: 14 planos, 18 cartelas, 1min41s.')
        for i,shot in enumerate(group):
            x = 36+(i%2)*((W-96)/2+24)
            top = H-112-(i//2)*339
            width = (W-96)/2
            duration = sum(cap['seconds'] for cap in shot['captions'])
            para(c, f"{shot['id']:02d}  {esc(shot['title'])}  |  {stamp(clock)}-{stamp(clock+duration)}",x,top,width,TITLE)
            y=top-35
            capture=INTRO_CAPTURES/f"{shot['id']:02d}-complete.png"
            c.drawImage(str(capture),x,y-161,width=230,height=161,preserveAspectRatio=True,anchor='c',mask='auto')
            right=y
            for cap in shot['captions']:
                right=para(c,f"<b>{esc(cap['speaker'])} | {cap['seconds']} s</b><br/>{esc(cap['text'])}",x+246,right,width-246,ST)-10
            if right<y-186:
                raise RuntimeError(f"Cartelas excedem abertura {shot['id']}")
            direction=shot['direction'].split('. ')[0].rstrip('.')+'.'
            para(c,esc(direction),x,y-182,width,SM)
            c.setStrokeColor(HexColor('#d5c9b7'));c.line(x,top-318,x+width,top-318)
            clock+=duration
        if start==12:
            para(c,'<b>Transição já existente:</b> o plano 14 encerra o monólogo e segue para o menu. Ao iniciar uma nova partida, a chamada curta do padre retoma a defesa do pátio. Não há uma nova cena de oficina antes da fase 1.',36,350,W-72,ST)
        finish(c)
    assert clock==101

def routes(c):
    page(c, 'Rotas e continuidade')
    para(c, 'Três resultados independentes acompanham a partida', 36, H-98, W-72, TITLE)
    xs = [64, 205, 345, 485, 625, 765, 905, 1045]
    y = 575
    labels = ['1', '2A / 2B', '3 e 4', '5', '6A / 6B', '7 a 12', '13A / 13B', '14 a 16']
    c.setStrokeColor(ACCENT); c.setLineWidth(2)
    c.line(xs[0]+40, y, xs[-1]+40, y)
    for x, label in zip(xs, labels):
        c.setFillColor(INK); c.roundRect(x, y-25, 95, 50, 7, fill=1, stroke=0)
        c.setFillColor(PAPER); c.setFont('Bold', 13); c.drawCentredString(x+47.5, y-5, label)
    blocks = [
        ('Igreja', 'Fase 1: usar bomba destrói a igreja e cria destroços na 2B. Sem bomba, 2A preservada. Todos os civis saem nas duas rotas.'),
        ('Resgate', 'Fase 5: defender por 2 minutos salva todos. A falha causa perdas entre os grupos ainda no chão; o primeiro grupo já embarcou. Dinorah continua na operação nas duas rotas.'),
        ('Dinorah', 'Fase 12: chegar viva leva à 13A. Morrer com Damião vivo leva à 13B. Na fase 6, a morte dela reinicia a missão. A morte de Damião sempre reinicia.'),
    ]
    for i,(title,text) in enumerate(blocks):
        x=36+i*380
        yy=470
        yy=para(c, esc(title), x, yy, 352, TITLE)-15
        para(c, esc(text), x, yy, 352)
    para(c, '<b>Última etapa:</b> viva, Dinorah prepara os circuitos, opera a ignição e orienta a retirada por rádio. Morta, Damião configura a sequência automática e o padre o acompanha. O combate e os objetivos das fases 14 a 16 permanecem os mesmos.', 36, 285, W-72)
    para(c, '<b>Final:</b> compor igreja inteira ou destruída + resgate completo ou parcial + Dinorah viva ou morta. São oito combinações de encerramento. A vitória regional não apaga perdas anteriores.', 36, 200, W-72)
    para(c, 'Roteiro de referência: game/doc/historia/tratamento-proposto.md. Os quadros de consequências se combinam; não acrescentam fases 17 ou novas bifurcações.', 36, 110, W-72, SM)
    finish(c)

def art_page(c, board, number):
    page(c, f'Prancha {number:02d} / 07', board['title'])
    img=HERE / 'imagens' / board.get('image',f"{board['slug']}.png")
    c.drawImage(str(img), 36, 101, width=W-72, height=H-205, preserveAspectRatio=True, anchor='c', mask='auto')
    labels='  |  '.join(f"{chr(65+i)}  {q['stage']}" for i,q in enumerate(board['frames']))
    para(c, esc(labels), 36, 82, W-72, SM)
    finish(c)

def notes(c, board, number):
    page(c, f'Prancha {number:02d} / Encenação', board['title'])
    colw=(W-96)/2
    for i,q in enumerate(board['frames']):
        col, row=i%2,i//2
        x=36+col*(colw+24); top=H-112-row*339
        y=para(c, f"{chr(65+i)}  {esc(q['stage'])} - {esc(q['title'])}", x, top, colw, TITLE)-12
        for label,key in [('Câmera','camera'),('Ação','action'),('Objetivo','objective'),('Fala','dialogue'),('Impacto e corte','impact')]:
            y=para(c, f'<b>{label}:</b> {esc(q[key])}', x, y, colw, ST)-7
        limit=top-318
        if y<limit:
            raise RuntimeError(f"Texto excedeu o quadro: {q['stage']} ({y} < {limit})")
        checks.append({'stage':q['stage'],'remaining_points':round(y-limit,1)})
        c.setStrokeColor(HexColor('#d5c9b7')); c.line(x, limit, x+colw, limit)
    finish(c)

def endings(c):
    page(c, 'Composição do epílogo')
    y=para(c, 'Oito combinações do mesmo desfecho regional', 36, H-105, W-72, TITLE)-30
    columns=[36,228,440,650]
    for x,label in zip(columns,['Igreja','Resgate','Dinorah','Quadros que compõem o final']):
        para(c, f'<b>{label}</b>',x,y,[180,200,195,465][columns.index(x)])
    y-=40
    for church in ['Preservada','Destruída']:
        for rescue in ['Completo','Parcial']:
            for din in ['Viva','Morta']:
                tags=f"07{'A' if church=='Preservada' else 'B'} + 07{'C' if rescue=='Completo' else 'D'} + 06{'C' if din=='Viva' else 'D'}"
                for x,text in zip(columns,[church,rescue,din,tags]):
                    para(c,esc(text),x,y, W-x-36 if x==650 else 185)
                c.setStrokeColor(HexColor('#d5c9b7')); c.line(36,y-30,W-36,y-30)
                y-=52
    y-=12
    y=para(c, '<b>Resultado comum:</b> os ovos da fábrica foram destruídos, os motores queimaram os criadouros dos foguetes e Escorpião caiu. Damião se retira. Nos dias seguintes, a resistência limpa os focos restantes e liberta São Jerônimo. O planeta continua infestado.',36,y,W-72)-20
    para(c, '<b>Direção visual:</b> a igreja destruída continua em ruínas no retorno; o memorial de civis não determina a morte de Dinorah; o memorial de Dinorah não implica falha do resgate. Mostrar reconstrução e perdas no mesmo mundo, sem restaurar tudo por causa da vitória.',36,y,W-72)
    finish(c)

def markdown():
    text=['# Storyboard da campanha de Plaguefall','', 'A história começa com a animação que já abre o jogo: 14 planos, 18 cartelas e 1min41s, preservados abaixo com capturas da ROM. Depois vêm o menu, a chamada curta de missão e as sete pranchas com 28 quadros da campanha. São 19 versões de fase e 16 fases por partida.', '', '[PDF para revisão](../../../output/pdf/plaguefall-storyboard-campanha-v1.pdf) · [História completa](tratamento-proposto.md) · [Prompts e arquivos de produção](../../art/storyboard-campanha-v1/README.md)', '', '## Início da história com a animação existente','', 'FinalQuest → APRESENTA → logo Plaguefall → animação de abertura → menu → nova partida → chamada curta do padre → fase 1. A animação toca uma vez por boot e pode ser pulada com START, conforme o fluxo existente. O monólogo não se repete ao começar a fase.', '', '[Vídeo da animação no jogo](../../art/intro-monologo-v2/emulator-ntsc/abertura.mp4) · [Storyboard aprovado da abertura](storyboard-abertura-v2.md)', '']
    clock=0
    for shot in OPENING['shots']:
        duration=sum(cap['seconds'] for cap in shot['captions'])
        text += [f"### Plano {shot['id']:02d} {shot['title']}",'',f"**Tempo:** {stamp(clock)}-{stamp(clock+duration)} ({duration} s).",'',f"![Plano {shot['id']:02d} da animação existente](../../art/intro-monologo-v2/emulator-ntsc/{shot['id']:02d}-complete.png)",'']
        for cap in shot['captions']:
            text += [f"**{cap['speaker']} ({cap['seconds']} s):** {cap['text']}",'']
        text += [f"**Encenação existente:** {shot['direction']}",'']
        clock+=duration
    text += ['### Do menu à primeira fase','', 'O plano 14 encerra a animação e leva ao menu. Ao escolher nova partida, o padre retoma a missão com a fala curta: “Damião, aqui é o padre. Segure o pátio. Tem gente fugindo pelo fundo.” Damião responde: “Tô indo. Hoje ninguém vai pro céu antes da hora.” A primeira prancha começa nessa retomada, sem outro prólogo na oficina.', '', '## Leitura das pranchas da campanha','', 'A: alto à esquerda. B: alto à direita. C: embaixo à esquerda. D: embaixo à direita. Variantes indicadas como alternativas não acontecem uma depois da outra. Duração e distância nas legendas são parâmetros da missão, não tempo de cutscene. As pranchas seguintes são conceitos; as imagens da abertura acima são capturas do jogo.', '']
    for i,b in enumerate(DATA,1):
        image_name=b.get('image',f"{b['slug']}.png")
        text += [f"## Prancha {i} {b['title']}",'',f"![{b['title']}](../../art/storyboard-campanha-v1/imagens/{image_name})",'']
        for j,q in enumerate(b['frames']):
            text += [f"### {chr(65+j)} {q['stage']} {q['title']}",'']
            for label,key in [('Câmera','camera'),('Ação','action'),('Objetivo','objective'),('Fala','dialogue'),('Impacto e corte','impact')]:
                text += [f"**{label}:** {q[key]}",'']
    text += ['## Composição dos encerramentos','', '| Igreja | Resgate | Dinorah | Quadros |','|---|---|---|---|']
    for church in ['Preservada','Destruída']:
        for rescue in ['Completo','Parcial']:
            for din in ['Viva','Morta']:
                tags=f"07{'A' if church=='Preservada' else 'B'} + 07{'C' if rescue=='Completo' else 'D'} + 06{'C' if din=='Viva' else 'D'}"
                text.append(f'| {church} | {rescue} | {din} | {tags} |')
    text += ['', 'A igreja, as perdas civis e o destino de Dinorah são independentes. Dinorah viva participa das conversas e da operação nas fases 14, 15 e 16; morta, Damião e padre conduzem a etapa final. A morte dela na fase 6 reinicia a missão; na 12, com Damião vivo, leva à 13B. A morte de Damião sempre tem prioridade de derrota.', '', 'As quantidades de três transmissores na fase 8 e três válvulas na fase 11 são sugestões de balanceamento. A ilustração de quantidades é indicativa; os contadores e as legendas definem os totais da missão. Os quadros amplos são direção de encenação e ambiente, sem definir a câmera final ou a escala de sprites do Mega Drive.', '']
    MD.write_text('\n'.join(text),encoding='utf-8')

def main():
    PDF.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(PDF),pagesize=(W,H),pageCompression=1)
    c.setTitle('Plaguefall - Storyboard da campanha e impactos das rotas')
    c.setAuthor('Plaguefall / RedRex')
    cover(c); opening_pages(c); routes(c)
    for i,b in enumerate(DATA,1):
        art_page(c,b,i); notes(c,b,i)
    endings(c); c.save(); markdown()
    (HERE/'qa/layout.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    print(PDF); print(MD); print(f'14 planos da abertura + {len(DATA)*4} quadros da campanha; 21 páginas; folga mínima {min(x["remaining_points"] for x in checks)} pt')

if __name__=='__main__':
    main()
