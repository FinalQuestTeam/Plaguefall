"""Proposal only: compose approved native assets, never export ROM resources."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, html
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
OUT=ROOT/'propostas';OUT.mkdir(exist_ok=True)
BACK=Image.open(GAME/'art/interface-ux-v2/source/painel-nativo.png').convert('RGB')
FONT=Image.open(GAME.parent/'SGDK/res/image/font_default.png').convert('L')
INK=(48,28,16);RUST=(109,36,0);OLIVE=(56,66,36);LIGHT=(255,219,146)
checks=[];cases=[]
def text(im,s,x,y,c=INK,right=False):
 # All result copy shares the exact horizontal centre of the 320px viewport.
 px=(320-len(s)*8)//2
 assert 44<=px and px+len(s)*8<=276,(s,len(s))
 assert 1<=y<=26 and all(32<=ord(t)<128 for t in s),(s,y)
 for i,t in enumerate(s):
  g=ord(t)-32;glyph=FONT.crop((g%16*8,g//16*8,g%16*8+8,g//16*8+8))
  im.paste(c,(px+i*8,y*8),glyph.point(lambda v:255 if v else 0))
 checks.append(dict(text=s,xPixels=px,yPixels=y*8,alignment='center'))
def frame(im,x,y,w,h):
 # Crop central paper, preserving the native corners/metal edges at 1:1.
 card=Image.new('RGB',(w,h))
 xs=((0,0,w-16),(w-16,304,16));ys=((0,0,h-32),(h-32,192,32))
 for dx,sx,cw in xs:
  for dy,sy,ch in ys:card.paste(BACK.crop((sx,sy,sx+cw,sy+ch)),(dx,dy))
 d=ImageDraw.Draw(card)
 d.rectangle((13,14,w-14,25),fill=LIGHT)
 d.line((16,30,w-17,30),fill=(146,109,73))
 d.rectangle((12,h-22,w-13,h-5),fill=(73,36,0))
 im.paste(card,(x,y));return im

def backdrop(scene):
 if scene=='final':
  im=Image.open(GAME/'art/interface-ux-v2/integracao/validation/ntsc/resumed-16.png').convert('RGB')
  # Show only the native scene outside the modal; HUD is hidden on the result.
  im.paste(im.crop((0,8,320,16)),(0,0))
  return im
 return Image.open(ROOT/f'atuais/ntsc/{scene}.png').convert('RGB')
def base(title,right='',scene='derrota',top=16,height=184):
 im=frame(backdrop(scene),32,top,256,height)
 text(im,title,0,(top+16)//8,RUST)
 return im

def menu(im,entries,selected=0,start=16,controls=21):
 row=start+selected*2
 # Short centred selection band, with equal breathing room inside the frame.
 ImageDraw.Draw(im).rectangle((48,row*8-3,271,row*8+10),fill=RUST)
 for i,s in enumerate(entries):text(im,('> ' if i==selected else '')+s,0,start+i*2,LIGHT if i==selected else INK)
 text(im,'CIMA/BAIXO: ESCOLHER',0,controls,OLIVE)
def save(im,id,label,before,note):
 im.save(OUT/(id+'.png'))
 cases.append(dict(id=id,label=label,before='atuais/ntsc/'+before+'.png',after='propostas/'+id+'.png',note=note))
for selected in (0,1):
 im=base('FIM DA TENTATIVA')
 text(im,'DAMIAO CAIU.',0,6,RUST)
 text(im,'FASE 3',0,7,OLIVE);text(im,'ABRIGO DE MANUTENCAO',0,8)
 text(im,'INIMIGOS: 08/14 | 00:43',0,10,OLIVE)
 text(im,'RECOMECE A MESMA FASE.',0,12)
 text(im,'VIDA CHEIA. EQUIP. BASICO.',0,13)
 text(im,'ITENS E MELHORIAS ZERADOS.',0,14)
 menu(im,['TENTAR NOVAMENTE','VOLTAR AO TITULO'],selected)
 text(im,'A: OK   START: TENTAR',0,23,LIGHT)
 save(im,'derrota' if selected==0 else 'derrota-sair','Derrota / tentar novamente' if selected==0 else 'Derrota / selecionar saída','derrota','Caixa de 256 × 184 px, texto e opções centralizados. Prioridade em repetir a mesma fase. START repete diretamente; A confirma a seleção. Números ilustrativos, usando apenas dados disponíveis da fase. A saída abre a confirmação seguinte; B retorna o foco para tentar novamente.')
im=base('SAIR DA PARTIDA?',top=40,height=152)
text(im,'O PROGRESSO DESTA PARTIDA',0,10);text(im,'SERA PERDIDO.',0,12)
menu(im,['VOLTAR A TENTATIVA','SAIR PARA O TITULO'],start=15,controls=20)
text(im,'A: OK  B/START: CANCELAR',0,22,LIGHT)
save(im,'confirmar-saida','Confirmação / preservar a partida','derrota','Caixa de 256 × 152 px. Mesmo padrão do pause aprovado, com conteúdo centralizado: opção inicial preserva a partida. Voltar retorna à tela de derrota, sem iniciar a fase. B e START cancelam a confirmação.')

def compact(kind,title,line1,line2,stage,bg):
 scene={'1':'fase-concluida','5':'sinal-protegido' if title=='SINAL PROTEGIDO.' else 'sinal-perdido'}[bg]
 im=frame(backdrop(scene),32,48,256,128)
 text(im,kind+' / FASE '+stage,0,8,RUST)
 text(im,title,0,11,RUST);text(im,line1,0,13);text(im,line2,0,15,OLIVE)
 text(im,'A/START: SEGUIR',0,20,LIGHT)
 return im
im=compact('OBJETIVO CUMPRIDO','CAMINHO ABERTO.','10 INIMIGOS ELIMINADOS.','SIGA PARA O PROXIMO DESTINO.','1','1')
save(im,'fase-concluida','Fase concluída / confirmação breve','fase-concluida','Cartão de 256 × 128 px, com 32 px de cenário visível em cada lateral e texto centralizado. Proposta: 2 s automáticos, ou A/START após nova pressão e trava de 350 ms. O mapa continua explicando o destino e a bifurcação. Contagem ilustrativa igual à meta real da fase 1.')
im=compact('OBJETIVO CUMPRIDO','SINAL PROTEGIDO.','30 SEGUNDOS DE PROTECAO.','O RESGATE FOI CONFIRMADO.','5','5')
save(im,'sinal-protegido','Proteção / resgate confirmado','sinal-protegido','Mesmo cartão central de 256 × 128 px e ritmo da conclusão comum. Texto nomeia o sinalizador, em vez de sugerir que o alvo é uma pessoa. A consequência é compatível com a rota de resgate; o mapa apresenta o próximo destino.')
im=compact('MUDANCA DE ROTA','SINAL PERDIDO.','A RETIRADA SERA POR TERRA.','A MISSAO CONTINUA.','5','5')
save(im,'sinal-perdido','Sinal perdido / a missão continua','sinal-perdido','Cartão central de 256 × 128 px. Resultado de objetivo, sem menu de tentar novamente: Damião está vivo e segue por 6B. Proposta: 3 s automáticos para ler a consequência, com o mesmo atalho A/START. Som curto de alerta, diferente do som de derrota; significado também no texto, independente da cor.')
for selected in (0,1):
 im=base('VITORIA / ETAPA 16 DE 16',scene='final',top=24,height=176)
 text(im,'O ESCORPIAO CAIU.',0,8,RUST)
 text(im,'O SINAL DELE PAROU.',0,10)
 text(im,'HOJE, DA PRA VOLTAR PRA CASA.',0,12)
 text(im,'CAMPANHA CONCLUIDA.',0,14,OLIVE)
 menu(im,['VOLTAR AO TITULO','JOGAR NOVAMENTE'],selected)
 text(im,'A/START: CONFIRMAR',0,23,LIGHT)
 save(im,'vitoria' if selected==0 else 'vitoria-rejogar','Vitória final / encerramento' if selected==0 else 'Vitória final / jogar novamente','vitoria-final','Caixa de 256 × 176 px com todo o texto centralizado e cenário do covil visível ao redor. Fundo ilustrativo da fase 16, com o HUD oculto. Permanece após o diálogo final, sem avanço automático; música Entardecer continua. Retornar ao título preserva o fluxo atual; jogar novamente inicia campanha nova. Nova pressão após soltar o comando evita saída acidental.')

review={
 'scope':'Proposta visual para aprovação. Nenhuma alteração em src, recursos exportados ou ROM.',
 'basis':'Avaliação heurística de UX e game design, leitura do código e capturas da ROM atual em Genesis Plus GX/NTSC. Não é teste com jogadores ou em CRT.',
 'pattern':'Painel da resistência aprovado em interface-ux-v2: 320×224, fonte nativa 8×8, caixas centrais de 256 px de largura, margens externas de 32 px, texto centralizado, papel claro, ferrugem, oliva e seleção de alto contraste. A moldura preserva os pixels originais; não há redução da fonte. Sem novas imagens geradas.',
 'findings':[
  {'current':'GAME OVER + APERTE START','problem':'Diz o estado, mas não o que START faz nem quais recursos serão reiniciados.','proposal':'Damião caiu; repetir a mesma fase é a ação inicial. Informar vida cheia, equipamento básico e reinício de itens/melhorias.'},
  {'current':'FASE CONCLUIDA! por 3 s','problem':'A recompensa é genérica e a espera não pode ser pulada.','proposal':'Confirmação breve ligada ao objetivo, sobre o cenário. Avanço automático e atalho explícito, sem adicionar outra etapa obrigatória.'},
  {'current':'O ALIADO CAIU! / A MISSAO CONTINUA...','problem':'O alvo é o sinalizador na Santa. A linguagem de morte confunde uma bifurcação com derrota.','proposal':'Sinal perdido; retirada por terra; a missão continua. Ritmo e som próprios, sem oferecer retry neste caso.'},
  {'current':'PARABENS! FIM em fundo preto','problem':'Pouco retorno emocional depois do chefe e quebra o padrão artístico recém-aprovado. START não diz que volta ao título.','proposal':'O Escorpião caiu. Caixa central de 256 × 176 px sobre o cenário, continuidade da música final, retorno ao título nomeado e opção de nova campanha.'}],
 'implementation':[
  'Reusar o ciclo seguro de gerenciamento de fonte, paletas e VRAM do painel, adaptando-o à caixa parcial e preservando o cenário ao redor. O texto centralizado pode exigir deslocamento de 4 px em linhas de comprimento ímpar. Não desenhar diretamente na WINDOW do HUD.',
  'Centralizar resultados em flow/screens. loseHp deve emitir o estado de derrota; o módulo de ator não deve compor o menu.',
  'O cartão parcial precisa de compositor próprio com tiles do painel aprovado, cenário congelado e sprites ocultos/ocultados pelo cartão. Não é só reduzir a imagem inteira.',
  'Distinguir morte, objetivo cumprido, objetivo perdido com rota e chefe final. Não acionar dois resultados quando morte e meta ocorrerem no mesmo quadro: derrota tem prioridade.',
  'Ler kills, PhaseStats.frames/fps, currentLevel e a definição da fase. Não inventar tempo de campanha, pontuação, medalhas ou vidas extras.',
  'START fora da confirmação repete a fase na derrota; dentro da confirmação cancela. A confirma o foco. No final A/START confirma a opção selecionada.',
  'Nova campanha deve usar a rotina completa do menu: limpar rotas, cenas vistas, estatísticas e inventário. Não apenas chamar startPhase(1).',
  'Depois de aprovado, verificar retry com resets, saída/cancelamento, 6A/6B, vitória final, novas pressões e restauração de vídeo em NTSC/PAL. Temporizações propostas precisam de playtest.'
 ],
 'cases':cases,'textBoundsChecked':len(checks),
 'romSHA256':hashlib.sha256((GAME/'out/release/rom.bin').read_bytes()).hexdigest()
}
(ROOT/'avaliacao.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
# Contact sheet keeps pixel art integer-scaled.
sheet=Image.new('RGB',(1280,3*280),(34,29,24));d=ImageDraw.Draw(sheet)
for i,c in enumerate(cases):
 x=(i%4)*320;y=(i//4)*280
 sheet.paste(Image.open(ROOT/c['after']),(x,y+24));d.text((x+8,y+7),c['id'],fill=(255,219,146))
sheet.crop((0,0,1280,560)).save(ROOT/'visao-geral.png')
rows=''.join('<tr><td>'+html.escape(f['current'])+'</td><td>'+html.escape(f['problem'])+'</td><td>'+html.escape(f['proposal'])+'</td></tr>' for f in review['findings'])
notes=''.join('<li>'+html.escape(x)+'</li>' for x in review['implementation'])
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resultados — revisão UX</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#211d18;color:#f0ddb7}*{box-sizing:border-box}body{max-width:1400px;margin:auto;padding:28px}h1{font-size:30px;margin:4px 0 10px}h2{font-size:21px}.eyebrow{color:#d7ac68;letter-spacing:.14em;font-size:12px}p{line-height:1.55;max-width:1000px}.muted{color:#bcae95}.badge{border:1px solid #81704a;padding:5px 9px;display:inline-block;border-radius:5px;font-size:12px}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:24px 0 14px}select,button{font:inherit;color:inherit;background:#3a3126;border:1px solid #9a7445;border-radius:5px;padding:10px;cursor:pointer}button:hover,button:focus-visible{background:#655038}button[aria-pressed=true]{background:#9e582b;color:#fff4db}select{max-width:100%}.compare{display:grid;grid-template-columns:1fr 1fr;gap:24px}.frame{margin:0;padding:14px;background:#30291f;border:1px solid #65553b;border-radius:8px}.frame img{display:block;width:100%;aspect-ratio:320/224;image-rendering:pixelated;background:#000}.frame figcaption{font-size:13px;color:#ceba94;margin-bottom:10px}.note{padding:15px 18px;background:#383322;border-left:3px solid #b48c4b;min-height:85px}.flow{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}.flow span{padding:8px 12px;border:1px solid #75613c;border-radius:5px}.casegrid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}.casegrid button{text-align:left;padding:7px}.casegrid img{width:100%;image-rendering:pixelated;display:block;margin-bottom:7px}.casegrid span{font-size:13px}table{border-collapse:collapse;width:100%;line-height:1.5}td,th{border-bottom:1px solid #65553b;text-align:left;vertical-align:top;padding:14px}th{color:#dfb878}td:first-child{width:23%}details{margin:24px 0;padding:15px;background:#30291f}li{margin:12px 0;line-height:1.5}.native .compare{grid-template-columns:repeat(2,minmax(320px,1fr))}.native .frame img{width:320px;max-width:100%}.hidden{display:none}a{color:#f1c480}@media(max-width:760px){body{padding:16px}.compare,.native .compare{grid-template-columns:1fr}.casegrid{grid-template-columns:repeat(2,1fr)}td,th{padding:8px;font-size:13px}}
</style><div class="eyebrow">PLAGUEFALL · PAINEL DA RESISTÊNCIA</div><h1>Derrota, conclusão e vitória</h1><span class="badge">PROPOSTA PARA APROVAÇÃO · JOGO SEM ALTERAÇÕES</span>
<p>O resultado precisa responder rápido: <strong>o que aconteceu, qual a consequência e o que posso fazer agora</strong>. A proposta mantém papel, metal, fonte e hierarquia da interface aprovada. Texto, opções e comandos ficam centralizados. Todas as caixas têm 256 px de largura, deixando o cenário visível nas laterais; a altura acompanha o conteúdo.</p>
<div class="toolbar"><label for="case">Situação</label><select id="case"></select><button id="previous">Anterior</button><button id="next">Próxima</button><button id="native" aria-pressed="false">Ver em 1×</button></div>
<div class="compare"><figure class="frame"><figcaption>ATUAL · captura da ROM publicada</figcaption><img id="before" alt="Tela atual do jogo"></figure><figure class="frame"><figcaption>PROPOSTA · composição em 320 × 224</figcaption><img id="after" alt="Desenho proposto usando o painel aprovado"></figure></div>
<p id="note" class="note" aria-live="polite"></p><div class="toolbar"><button id="simulateA">Simular A / confirmar</button><button id="simulateStart">Simular START</button><button id="simulateB">Simular B / voltar</button><span id="action" class="muted" aria-live="polite">Simulação de navegação da proposta; não controla o jogo.</span></div>
<div class="flow"><span>Derrota → tentar a mesma fase</span><span>Objetivo → diálogo / mapa → próxima fase</span><span>Escorpião → diálogo final → vitória</span></div><div id="cards" class="casegrid"></div>
<h2>Avaliação de game design e UX</h2><table><thead><tr><th>Hoje</th><th>Problema</th><th>Proposta</th></tr></thead><tbody>ROWS</tbody></table>
<p><strong>Tom:</strong> direto e coerente com Damião, sem piada após a morte e sem transformar toda fase em um encerramento. A vitória reconhece o Escorpião derrotado, preservando a história de um Brasil ainda ocupado. Sem medalhas, placares ou estatísticas de campanha inventadas.</p>
<details><summary>Regras, limitações e trabalho para implementação</summary><ul>NOTES</ul></details>
<p class="muted">Avaliação heurística baseada no código e em capturas NTSC da ROM atual; não equivale a testes com jogadores ou em CRT. Na captura, a RAM foi usada apenas para selecionar situações e antecipar morte/objetivos/chefe. As telas atuais foram desenhadas pelo executável existente. Os números da proposta de derrota são ilustrativos. A proposta não alterou código do jogo, recursos exportados ou ROM.</p>
<p><a href="avaliacao.json">Avaliação e especificação</a> · <a href="atuais/ntsc/report.json">Registro das capturas</a> · <a href="../interface-ux-v2/revisao.html">Interface aprovada</a></p>
<script>const cases=CASES;const select=document.querySelector('#case');const action=document.querySelector('#action');let index=0;for(const [i,c] of cases.entries()){select.add(new Option(c.label,i));const b=document.createElement('button');b.innerHTML=`<img src="${c.after}" alt=""><span>${c.label}</span>`;b.onclick=()=>show(i);document.querySelector('#cards').append(b)}function show(i){index=(i+cases.length)%cases.length;const c=cases[index];select.value=index;document.querySelector('#before').src=c.before;document.querySelector('#after').src=c.after;document.querySelector('#note').textContent=c.note;document.querySelectorAll('#cards button').forEach((b,j)=>b.setAttribute('aria-pressed',j===index));action.textContent='Simulação da proposta; não controla o jogo.'}select.onchange=()=>show(+select.value);document.querySelector('#previous').onclick=()=>show(index-1);document.querySelector('#next').onclick=()=>show(index+1);document.querySelector('#native').onclick=e=>{const on=document.body.classList.toggle('native');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Ampliar em 2×':'Ver em 1×'};function simulate(key){const id=cases[index].id;if(id==='derrota-sair'&&key==='A'){show(2);return}if(id==='confirmar-saida'){show(1);action.textContent='Voltou à derrota. Para sair: selecionar SAIR PARA O TITULO e confirmar.';return}if(id.startsWith('derrota')){if(key==='B'){show(0);return}action.textContent='Abre a preparação da mesma fase: vida cheia, equipamento básico, itens e melhorias reiniciados.';return}if(id.startsWith('vitoria')){action.textContent=key==='B'?'B não confirma nem abandona esta tela.':id==='vitoria-rejogar'?'Inicia uma campanha nova na fase 1.':'Volta ao título.';return}action.textContent=key==='B'?'B não avança este cartão.':'Segue ao diálogo/mapa existente conforme o resultado desta fase.'}document.querySelector('#simulateA').onclick=()=>simulate('A');document.querySelector('#simulateStart').onclick=()=>simulate('START');document.querySelector('#simulateB').onclick=()=>simulate('B');document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key==='ArrowRight'){e.preventDefault();show(index+1)}if(e.key==='ArrowLeft'){e.preventDefault();show(index-1)}});show(0)</script></html>'''
page=page.replace('ROWS',rows).replace('NOTES',notes).replace('CASES',json.dumps(cases,ensure_ascii=False))
(ROOT/'proposta-aprovada.html').write_text(page)
print(json.dumps({'cases':len(cases),'textLinesChecked':len(checks),'sizes':'320x224','romSHA256':review['romSHA256']},indent=2))
