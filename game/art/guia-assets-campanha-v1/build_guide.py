"""Guia de produção e referências para aprovação; não altera o jogo."""
from pathlib import Path
import html,json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OUT=ROOT/'output/pdf/plaguefall-guia-producao-visual-fases-v1.pdf'
MD=ROOT/'game/doc/historia/guia-producao-visual-fases.md'
PHASES=json.loads((BASE/'fases.json').read_text())
KITS=json.loads((BASE/'kits.json').read_text())
INVENTORY=json.loads((BASE/'inventario.json').read_text())
W,H=1190.55,841.89
FONT=Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('Body',str(FONT/'Arial.ttf')))
pdfmetrics.registerFont(TTFont('Bold',str(FONT/'Arial Bold.ttf')))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold')
INK=HexColor('#17272d');PAPER=HexColor('#f5f0e5');ACCENT=HexColor('#a34b2f');GRAY=HexColor('#526266')
BODY=ParagraphStyle('body',fontName='Body',fontSize=13,leading=18,textColor=INK)
SM=ParagraphStyle('small',parent=BODY,fontSize=11,leading=15)
TITLE=ParagraphStyle('title',parent=BODY,fontName='Bold',fontSize=21,leading=25)
SUB=ParagraphStyle('sub',parent=BODY,fontName='Bold',fontSize=15,leading=20)
AUDIT=[]

def p(c,text,x,y,width,style=BODY):
    box=Paragraph(text,style);_,height=box.wrap(width,H);box.drawOn(c,x,y-height)
    return y-height

def e(t):return html.escape(t)

def page(c,name,title):
    c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(ACCENT);c.rect(36,H-42,9,9,fill=1,stroke=0)
    c.setFillColor(INK);c.setFont('Bold',12);c.drawString(56,H-42,'PLAGUEFALL / GUIA DE PRODUÇÃO VISUAL')
    c.setFont('Body',11);c.drawRightString(W-36,H-42,name)
    p(c,e(title),36,H-76,W-72,TITLE)
    c.setStrokeColor(HexColor('#d4c5af'));c.line(36,39,W-36,39)
    c.setFillColor(GRAY);c.setFont('Body',9)
    c.drawString(36,24,'23 OUT 2026 | Proposta para aprovação | Arte nativa e fases serão produzidas depois da aprovação')
    c.drawRightString(W-36,24,f'{c.getPageNumber():02d}')

def end(c):c.showPage()

def section(c,title,text,x,y,width=650):
    y=p(c,e(title),x,y,width,SUB)-6
    return p(c,e(text),x,y,width,BODY)-17

def cover(c):
    page(c,'Escopo','O que produzir em cada fase')
    y=p(c,'19 fichas de fase + 5 kits ilustrados + 30 famílias de elementos de referência',36,H-118,W-72,SUB)
    c.drawImage(str(BASE/'imagens/03-objetivos.png'),36,225,width=690,height=465,preserveAspectRatio=True,anchor='c')
    x=765;y=H-165
    for a,b in [('Reutilizar','Manter arte existente que já resolve o cenário, o ator ou o objetivo.'),('Adaptar','Ajustar montagem, estados, leitura ou objetivo sem redesenhar tudo.'),('Criar','Produzir somente os elementos que faltam para o roteiro e sua leitura jogável.')]:
        y=section(c,a,b,x,y,W-x-36)
    y=section(c,'O padrão vem do jogo','Pátio e primeiras fases aprovadas: câmera elevada, escala dos atores, chão legível, módulos de cenário e paletas do Mega Drive.',x,y,W-x-36)
    p(c,'<b>Escopo desta entrega:</b> guia, inventário e pequenos estudos de peças. As pranchas ampliadas são referência visual; ainda não são sprites nativos, folhas finais de animação ou mapas prontos para a ROM.',36,178,W-72,BODY)
    p(c,'<b>Depois da aprovação:</b> normalizar cada peça na câmera e escala nativas, fechar atlas e paletas, montar as fases, integrar objetivos e diálogos e validar no emulador. A abertura existente permanece como início da história.',36,109,W-72,BODY)
    end(c)

def standards(c):
    page(c,'Padrão visual','Usar as primeiras fases como referência de produção')
    y=H-125
    for title,text in [
        ('Câmera e escala','Referência ortográfica elevada a cerca de 60° acima do chão: topo do chapéu, telhado e objetos visível; fachadas curtas. Atores em 32x48, Santa existente em 40x48. As pranchas conceituais precisam ser normalizadas antes da arte final.'),
        ('Módulos e desenho','Tiles de 8x8. Planejar módulos de 16/32/48/64 px e composições maiores em peças. Terra ocre, reboco, telhas, azul gasto, tijolo e metal oxidado. O cenário não deve competir com o tiro e os insetos.'),
        ('Paletas','No arranjo atual: PAL0 para texto e flashes, PAL1 para objetos/inimigos, PAL2 para Damião e Dinorah e PAL3 para cenário. O cenário usa 16 entradas; sprites normalmente reservam índice zero à transparência. Não prever uma quinta paleta.'),
        ('Referência não é sprite final','As medidas nos kits são caixas nativas propostas. A imagem gerada está ampliada e não certifica contagem de cores, registro, câmera exata ou transparência. Aprovar forma e material; exigir a conferência 1x/2x antes de integrar.'),
    ]:y=section(c,title,text,36,y,650)
    c.drawImage(str(ROOT/'game/art/phase01-courtyard-v2/intact-native.png'),734,386,width=420,height=315,preserveAspectRatio=True,anchor='c')
    p(c,'Pátio aprovado: base do cenário, dos materiais e da circulação.',734,365,420,SM)
    c.drawImage(str(ROOT/'game/art/cangaco-protagonista-iso60-v2/previews/heroi-repouso-4x.png'),734,235,width=420,height=105,preserveAspectRatio=True,anchor='c')
    p(c,'Silhuetas do ator existente: a nova peça precisa caber nessa escala e câmera.',734,211,420,SM)
    p(c,'<b>Volume visual e colisão:</b> desenhar o apoio no chão; distinguir o que bloqueia pés, tiros, ambos ou nenhum. Bancos, cabos e detalhes de piso não recebem colisão alta por conveniência.',734,150,420,BODY)
    end(c)

def budget(c):
    page(c,'Orçamento gráfico','Planejar cenário e objetivos dentro da mesma memória')
    y=H-125
    for title,text in [
        ('Reserva compartilhada','O cenário aprovado usa até 640 tiles, ou 20.480 bytes de padrões de 4bpp. O renderizador atual dos objetivos também usa parte dessa faixa. Não existe um orçamento de 640 tiles para cenário somado a outros 560 livres para objetos.'),
        ('Custo por família, não por instância','32x32 tem 16 tiles por pose; seis poses custam 96. 48x48 tem 36 tiles; seis poses custam 216. 64x64 tem 64 tiles; seis poses custam 384. Cinco geradores usam a mesma arte, não cinco cópias de todos os quadros.'),
        ('Combinações críticas','Portão de seis poses (384) + válvula de seis poses (96) = 480 tiles antes de deduplicar, deixando 160 nessa reserva para outros padrões. O cenário da Santa atual já usa 636/640. É preciso recompor atlas, reduzir redundância ou alterar a estratégia de carga; não basta somar PNGs.'),
        ('Instâncias e persistência','O renderizador de objetivos atual tem sete slots visuais. A fase 10 possui dez ovos: separar o estado lógico dos dez alvos da representação dos visíveis. Na fase 7, planejar cinco fontes, depósito e carga sem duplicar objetos nem perder estados ao rolar a câmera.'),
        ('Orçamento de ação','Como ponto de partida conservador dos protótipos: quatro insetos nas missões comuns, três na escolta e seis tiros por lado, com os tiros aliados de Dinorah contabilizados. Isso não é o limite global do vetor do jogo nem garantia de FPS no novo cenário. Medir NTSC/PAL na integração.'),
        ('Corredores','2.560 e 3.072 px são comprimento de mundo, não largura de uma textura única residente. Repetir piso com marcos próprios, janela circular de 64x32 tiles e estados preservados. Não repetir a mesma sala como cenário inteiro a cada trecho.'),
    ]:y=section(c,title,text,36,y,W-72)
    if y<60:raise RuntimeError('Orçamento excede página')
    end(c)

def inventory(c):
    page(c,'Inventário','Recursos que já existem no projeto')
    y=H-125
    for code,title,description,path in INVENTORY:
        y=p(c,f'<b>{code} / {e(title)}</b> - {e(description)}',36,y,W-72,BODY)-5
        y=p(c,e(path),36,y,W-72,SM)-13
    if y<60:raise RuntimeError('Inventário excede página')
    end(c)

def kit_page(c,k,index):
    page(c,f'Kit {index+1} / 5',k['title'])
    c.drawImage(str(BASE/'imagens'/f"{k['slug']}.png"),36,221,width=720,height=480,preserveAspectRatio=True,anchor='c')
    y=H-135
    for element in k['elements']:
        code,title,size,phases,status,note=element
        y=p(c,f'<b>{code} / {e(title)}</b>',792,y,W-828,SUB)-5
        y=p(c,f'{e(size)} px propostos | {status}<br/>Fases: {e(phases)}. {e(note)}',792,y,W-828,SM)-18
    p(c,'<b>Ordem das peças:</b> A, B e C na linha superior; D, E e F na inferior. Um par ou trio na mesma célula mostra estados da mesma família, não itens novos independentes.',36,170,720,BODY)
    p(c,'Estudo ampliado para avaliar silhueta, materiais e estados. Antes da produção, ajustar câmera, escala e paleta ao pátio e aos sprites reais; montar folhas nativas com âncora e colisão explícitas.',36,100,W-72,SM)
    if y<60:raise RuntimeError(f'Legenda excede kit {index}')
    end(c)

def phase_page(c,q):
    page(c,f"Fase {q['id']} / Ficha de produção",f"{q['id']}  {q['title']}")
    y=H-124;left=670
    y=p(c,f"<b>Objetivo:</b> {e(q['goal'])}<br/><b>Mundo:</b> {e(q['world'])}",36,y,left,BODY)-15
    y=p(c,f"<b>História:</b> {e(q['story'])}",36,y,left,BODY)-16
    for title,key in [('REUTILIZAR','reuse'),('ADAPTAR','adapt'),('CRIAR','create'),('ESTADOS E ANIMAÇÕES','states')]:
        y=p(c,title,36,y,left,SUB)-5
        for item in q[key]:y=p(c,'- '+e(item),36,y,left,BODY)-4
        y-=11
    y=p(c,f"<b>Colisão e leitura:</b> {e(q['collision'])}",36,y,left,BODY)-10
    y=p(c,f"<b>HUD e sinais:</b> {e(q['ui'])}",36,y,left,BODY)-10
    if y<65:raise RuntimeError(f"Ficha {q['id']} excede: {y}")
    AUDIT.append({'fase':q['id'],'margem_inferior_pt':round(y,1)})
    x=748;width=W-x-36;k=KITS[q['kit']]
    p(c,e(k['title']),x,H-125,width,SUB)
    c.drawImage(str(BASE/'imagens'/f"{k['slug']}.png"),x,418,width=width,height=263,preserveAspectRatio=True,anchor='c')
    yy=p(c,'<b>Referências:</b> '+e(', '.join(q['refs'])),x,400,width,BODY)-18
    yy=section(c,'Consequência da fase',q['impact'],x,yy,width)
    yy=section(c,'Entrega mínima para produzir',q['delivery'],x,yy,width)
    yy=section(c,'Atenção de produção',q['risk'],x,yy,width)
    if yy<65:raise RuntimeError(f"Lateral {q['id']} excede: {yy}")
    end(c)

def beginning_ending(c):
    page(c,'Abertura e epílogo','Produzir os estados da história sem refazer a abertura')
    y=H-125
    for title,text in [
        ('Abertura existente','Preservar animação, 14 planos, 18 cartelas e 101 s. Fluxo: animação → menu → nova partida → chamada curta → pátio. Nenhuma nova descoberta na oficina. A captura do início é referência aprovada, não uma peça a gerar novamente.'),
        ('Igreja no retorno','Duas composições do mesmo lugar: inteira e destruída com reconstrução apenas começando. Reutilizar os módulos das fases 1, 2A e 2B. Destroços continuam quando a rota os exige.'),
        ('Civis no retorno','Resgate completo mostra os civis daquela retirada voltando; resgate parcial inclui ausências e memorial. Civis podem aparecer em imagens/interlúdios, sem criar uma nova mecânica de escolta de multidão.'),
        ('Dinorah no retorno','Viva: conversa e organização da reconstrução. Morta: chapéu e ferramentas no memorial e falas de Damião e padre. Reutilizar retratos e, quando útil, a morte de quatro poses já existente. O memorial civil não implica a morte dela.'),
        ('Composição dos oito finais','Igreja inteira/destruída × resgate completo/parcial × Dinorah viva/morta. Produzir componentes combináveis, não oito mapas ou oito chefes. As fases finais com Dinorah viva precisam de falas e painel operado; sem ela, sequência automática preparada por Damião.'),
    ]:y=section(c,title,text,36,y,665)
    c.drawImage(str(ROOT/'game/art/intro-monologo-v2/emulator-ntsc/01-complete.png'),748,468,width=405,height=240,preserveAspectRatio=True,anchor='c')
    p(c,'Primeiro plano da animação existente: preservar.',748,449,405,SM)
    c.drawImage(str(BASE/'imagens/05-estados-narrativos.png'),748,150,width=405,height=270,preserveAspectRatio=True,anchor='c')
    p(c,'Objetos e estados ajudam a comunicar consequências; não substituem as variantes de diálogo.',748,132,405,SM)
    if y<65:raise RuntimeError('Abertura/epílogo excede página')
    end(c)

def production(c):
    page(c,'Aprovação e produção','O que revisar agora e como transformar em fases')
    y=H-125
    for title,text in [
        ('Revisar este pacote','Avaliar os cinco kits, a seleção do que reutilizar/adaptar/criar, a identidade dos novos lugares e a leitura dos objetos. Os tamanhos propostos, alturas de mapas e contagens de três transmissores/três válvulas são pontos de partida, não mudança dos objetivos já definidos.'),
        ('Pacote nativo de cada família','Entregar PNG indexado com transparência de índice zero quando aplicável, paleta existente ou proposta compatível, atlas, folhas por estado, células e âncoras, apoio no chão e base de colisão. Separar fonte ampliada da arte nativa. Não preencher poses restantes com quadros que inventam outra identidade.'),
        ('Pacote de cada fase','Mapa nativo e recortes 320x224 em 1x/2x, tileset 8x8, módulos reutilizáveis, planta de sólidos e perigos, pontos de objetivo, rota de chegada/saída e estados narrativos. Se usar Tiled, preservar arquivos de inspeção e registrar o caminho real de exportação; não pressupor um importador já pronto.'),
        ('Ordem sugerida depois da aprovação','Lote 1: igreja/rua/galpão/resgate, fases 1-5. Lote 2: esgotos/favela/objetivos, fases 6-8. Lote 3: corredor/fábrica/calor, fases 9-11. Lote 4: estaleiro, Dinorah e confronto final, fases 12-16. Cada lote reaproveita famílias aprovadas, sem redesenhar atores e HUD.'),
        ('Critério de conclusão na implementação','Objetivo correto; colisão coincidindo com a imagem; leitura a 1x; estados persistentes ao rolar e pausar; falhas e rotas coerentes; combinação real de cenário e objetos dentro da VRAM; enquadramento, carga de sprites e DMA medidos no emulador NTSC/PAL.'),
        ('Continuidade obrigatória','Morte de Dinorah na fase 6 reinicia; na 12, com Damião vivo, leva à 13B. Fase 5 pode continuar com perdas. Rádio da 15 destruído reinicia. A bomba na 1 altera a igreja e não mata civis por regra narrativa. Dinorah viva participa de 14, 15 e 16; morta, não reaparece.'),
    ]:y=section(c,title,text,36,y,W-72)
    if y<65:raise RuntimeError('Produção excede página')
    end(c)

def markdown():
    out=['# Guia de produção visual de cada fase','', 'Proposta para aprovação em 23 de outubro de 2026. São 19 fichas de fase, cinco kits ilustrados e 30 famílias de elementos de referência. O guia parte das primeiras fases aprovadas e considera os objetivos e a [história completa](tratamento-proposto.md). A produção e a implementação das fases ficam para depois da aprovação do usuário.', '', '[PDF para revisão](../../../output/pdf/plaguefall-guia-producao-visual-fases-v1.pdf) · [Imagens e prompts](../../art/guia-assets-campanha-v1/README.md) · [Storyboard da história](storyboard-campanha.md)', '', '## Como ler','', '**Reutilizar:** recurso existente que resolve a função. **Adaptar:** montagem, estados, objetivo ou leitura precisam mudar. **Criar:** arte ausente. Os kits são estudos ampliados; não são folhas nativas prontas para ROM. As dimensões são caixas propostas, a conferir em 1x/2x com os atores e o cenário real.', '', 'A câmera final segue o pátio e os personagens existentes, com visão ortográfica elevada próxima de 60° acima do chão. As peças geradas ainda precisam de normalização de câmera, escala, paleta, âncora e colisão. Não aprovar uma peça só por funcionar ampliada.', '', '## Padrão técnico e visual','', '- Tiles de 8x8; atores humanos em 32x48; Santa existente em 40x48; carga de bornal em 16x16.', '- Cenário em PAL3; objetos/inimigos em PAL1; Damião e Dinorah em PAL2; texto e flashes em PAL0, conforme o arranjo atual. Não prever paleta adicional.', '- Separar chão, arquitetura alta, decoração baixa, objetos de objetivo, sprites móveis, efeitos e HUD. Cada elemento declara se bloqueia pés, tiros, ambos ou nenhum.', '- A reserva de 640 tiles do cenário é compartilhada com o caminho atual de objetos animados. Não somar 640 de cenário a outros 560 como se fossem memória livre.', '- 32x32 em seis poses: até 96 tiles; 48x48: 216; 64x64: 384. São custos sem deduplicação, calculados por família. Cinco instâncias de um gerador compartilham seus quadros.', '- Portão + válvula, com seis poses atuais, somam até 480 tiles e deixam 160 nessa faixa. A Santa atual já ocupa cenário de 636/640. Esses casos pedem planejamento de atlas/carga antes de integração.', '- O renderizador de objetivos atual tem sete slots visuais. Dez ovos exigem estado lógico dos dez alvos separado dos visuais ativos; cinco cargas, fontes e depósito também precisam de planejamento.', '- Quatro insetos comuns e três na escolta são pontos de partida conservadores das missões experimentais, não o limite global do vetor. Seis tiros por lado e tiros aliados de Dinorah precisam entrar na medição integrada.', '- Corredores de 2.560/3.072 px usam módulos, marcos e rolagem circular; não uma nova textura inteira residente nem a repetição evidente da mesma sala.', '', '## Inventário do que já existe','', '| Código | Recurso | Aplicação | Fonte |','|---|---|---|---|']
    for code,title,desc,path in INVENTORY:
        target='../../'+path[5:] if path.startswith('game/art/') else ('../'+path[9:] if path.startswith('game/doc/') else path)
        # O arquivo de leitura fica em game/doc/historia.
        if path.startswith('game/doc/historia/'):target=Path(path).name
        out.append(f'| {code} | {title} | {desc} | [Fonte]({target}) |')
    out += ['', '## Kits de pequenos elementos de referência','']
    for k in KITS:
        out += ['### '+k['title'],'',f"![{k['title']}](../../art/guia-assets-campanha-v1/imagens/{k['slug']}.png)",'','Ordem: A, B e C no alto; D, E e F embaixo. Pares ou trios na mesma célula representam estados da mesma família.','','| ID | Elemento | Caixa nativa proposta | Fases | Situação | Leitura |','|---|---|---|---|---|---|']
        for row in k['elements']:out.append('| '+' | '.join(row)+' |')
        out.append('')
    out += ['## Guia por fase','']
    for q in PHASES:
        out += [f"### Fase {q['id']} {q['title']}",'',f"**Objetivo:** {q['goal']}",'',f"**Mundo:** {q['world']}",'',f"**História:** {q['story']}",'']
        for label,key in [('Reutilizar','reuse'),('Adaptar','adapt'),('Criar','create'),('Estados e animações','states')]:
            out += [f'**{label}**','']+['- '+s for s in q[key]]+['']
        for label,key in [('Colisão e leitura','collision'),('HUD e sinais','ui'),('Consequência','impact'),('Entrega mínima','delivery'),('Atenção de produção','risk')]:out += [f'**{label}:** '+q[key],'']
        out += ['**Referências visuais:** '+', '.join(q['refs'])+'.','']
    out += ['## Abertura e epílogo','', 'A história começa com a animação existente: 14 planos, 18 cartelas e 101 s. Preservar ordem, texto e imagens. Depois vêm menu, nova partida, chamada curta e fase 1; não criar outro prólogo na oficina.', '', 'O epílogo combina igreja inteira/destruída, resgate completo/parcial e Dinorah viva/morta. Reutilizar o cenário da igreja e produzir componentes de retorno, reparos e memória, sem oito mapas independentes. Civis novos em interlúdios são opcionais; não introduzem escolta de multidão. O chapéu e as ferramentas de Dinorah só aparecem como memória na rota em que ela morreu.', '', '## Pacote de produção depois da aprovação','', '1. Normalizar os elementos na câmera do jogo e conferir 1x/2x ao lado dos atores existentes.', '2. Preparar PNGs nativos indexados, paletas, folhas de estados, âncoras, base de colisão, tileset e metadados; preservar fontes ampliadas e prompts.', '3. Montar mapas, pontos de objetivo, rotas, perigos, estados persistentes e conversas conforme a ficha de cada fase.', '4. Validar a combinação de cenário/objetivos em VRAM, colisões, rolagem, pausa, reinício, falhas narrativas e desempenho no emulador NTSC/PAL.', '', '**Lotes sugeridos:** 1-5 (igreja/rua/galpão/resgate), 6-8 (esgotos/favela), 9-11 (fábrica) e 12-16 (estaleiro). A aprovação deste pacote orienta a produção; as imagens desta entrega são referências, não fases já implementadas.', '']
    MD.write_text('\n'.join(out),encoding='utf-8')

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
    c.setTitle('Plaguefall - Guia de produção visual de cada fase')
    c.setAuthor('Plaguefall / RedRex')
    cover(c);standards(c);budget(c);inventory(c)
    for i,k in enumerate(KITS):kit_page(c,k,i)
    for q in PHASES:phase_page(c,q)
    beginning_ending(c);production(c)
    count=c.getPageNumber()-1;c.save();markdown()
    (BASE/'qa/layout.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2)+'\n')
    print(OUT);print(MD);print(f'{count} páginas, {len(PHASES)} fichas e {sum(len(k["elements"]) for k in KITS)} famílias de referência.')

if __name__=='__main__':main()
