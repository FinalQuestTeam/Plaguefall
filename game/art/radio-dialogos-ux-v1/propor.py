"""Proposal only: native UI composition, existing portraits and scene captures.
No game resources or ROM are changed.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,re,textwrap,hashlib,struct,html
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parents[1];OUT=ROOT/'propostas';OUT.mkdir(exist_ok=True)
FONT=Image.open(GAME.parent/'SGDK/res/image/font_default.png').convert('L')
METAL=Image.open(GAME/'art/interface-ux-v2/source/painel-nativo.png').convert('RGB')
PAL=[tuple(round(((c>>s)&7)*255/7) for s in (1,5,9)) for c in struct.unpack('>16H',(GAME/'res/interface/palette.bin').read_bytes())]
DARK=PAL[1];MAT=PAL[3];COPPER=PAL[4];RUST=PAL[12];DIM=PAL[9];LIGHT=PAL[15];TEXT=PAL[13]
PORTRAITS={k:Image.open(GAME/'art/dialogue-portraits-v1'/v).convert('RGBA') for k,v in {'DAMIAO':'damiao.png','PADRE':'comando.png','DINORAH':'parceira.png'}.items()}
checks=[];cases=[]
def text(im,s,x,y,c=TEXT,center=False,scale=1):
 if center:x=(320-len(s)*8*scale)//2
 assert x>=8 and x+len(s)*8*scale<=312 and y>=8 and y+8*scale<=216,(s,x,y)
 for i,ch in enumerate(s):
  g=ord(ch)-32;assert 0<=g<96
  glyph=FONT.crop((g%16*8,g//16*8,g%16*8+8,g//16*8+8)).point(lambda v:255 if v else 0)
  if scale!=1:glyph=glyph.resize((8*scale,8*scale),Image.Resampling.NEAREST)
  im.paste(c,(x+i*8*scale,y),glyph)
 checks.append({'text':s,'x':x,'y':y,'scale':scale})
def plate(im,box,active=False):
 x,y,w,h=box;d=ImageDraw.Draw(im)
 d.rectangle((x,y,x+w-1,y+h-1),fill=DARK,outline=COPPER if active else DIM,width=2)
 # Existing metal edge pixels, copied at 1:1; no paper in transmission windows.
 for px in range(0,w,8):
  sx=0 if px==0 else 312 if px>=w-8 else 8+((px-8)%304)
  im.paste(METAL.crop((sx,0,sx+8,8)),(x+px,y))
  im.paste(METAL.crop((sx,216,sx+8,224)),(x+px,y+h-8))
 if h>24:d.line((x+4,y+9,x+w-5,y+9),fill=COPPER)
 for xx in (x+4,x+w-6):
  for yy in (y+4,y+h-6):d.rectangle((xx,yy,xx+1,yy+1),fill=LIGHT)

def bars(im,x,y,active=True):
 d=ImageDraw.Draw(im)
 for i,h in enumerate((3,5,7,9)):
  d.rectangle((x+i*4,y+9-h,x+i*4+1,y+8),fill=LIGHT if active else DIM)

def portrait(im,who,x,y,active):
 plate(im,(x-8,y-8,64,64),active)
 im.paste(PORTRAITS[who],(x,y),PORTRAITS[who])

def scene(node=1,clean=False):return Image.open(ROOT/f"atuais/ntsc/{'fundo' if clean else 'cenario'}-{node}.png").convert('RGB')

def dialogue(speaker,words,remote='PADRE',node=1,phase='1',page='1/2',partial=False):
 im=scene(node,clean=True);d=ImageDraw.Draw(im)
 # Hide gameplay counters while preserving the full native stage behind the radio.
 d.rectangle((0,0,319,7),fill=DARK)
 left=speaker=='DAMIAO'
 if left:
  plate(im,(8,8,304,112),True)
  text(im,'TX / DAMIAO',80,24,LIGHT);text(im,'FALANDO',184,24,DIM);text(im,page,280,24,DIM)
  bars(im,260,22)
  portrait(im,'DAMIAO',16,40,True)
  portrait(im,remote,248,144,False)
  plate(im,(80,136,152,48));text(im,'RX / '+remote,88,148,LIGHT);text(im,'ESCUTANDO',88,164,DIM)
  x,y=80,40
 else:
  plate(im,(8,8,304,24))
  text(im,'RADIO / COMUNIDADE',16,16,LIGHT);text(im,'FASE '+phase,240,16,DIM)
  portrait(im,'DAMIAO',16,40,False)
  plate(im,(80,32,160,48));text(im,'TX / DAMIAO',88,44,LIGHT);text(im,'ESCUTANDO',88,60,DIM);bars(im,216,58,False)
  plate(im,(8,104,304,120),True)
  text(im,'RX / '+remote,16,120,LIGHT);text(im,'RECEBENDO',128,120,DIM);text(im,page,280,120,DIM);bars(im,248,118)
  portrait(im,remote,248,144,True)
  x,y=16,140
 lines=textwrap.wrap(words,width=26,break_long_words=False,break_on_hyphens=False)
 assert len(lines)<=4,(speaker,lines)
 if partial:lines=[lines[0][:17]]
 for i,s in enumerate(lines):text(im,s,x,y+i*16,TEXT)
 if partial:
  cx=x+len(lines[-1])*8
  d.rectangle((cx,y+len(lines)*16-16,cx+5,y+len(lines)*16-10),fill=LIGHT)
 plate(im,(8,200,304,24))
 text(im,'A: MOSTRAR TEXTO' if partial else 'A: VER MISSAO' if left and page=='2/2' else 'A: AVANCAR',16,208,LIGHT)
 text(im,'START: PULAR',208,208,LIGHT)
 return im

def save(im,id,group,label,before,note):
 assert im.size==(320,224);im.save(OUT/(id+'.png'))
 cases.append(dict(id=id,group=group,label=label,before=before,after='propostas/'+id+'.png',note=note))
padre='DAMIAO, AQUI E O PADRE. SEGURE O PATIO. TEM GENTE FUGINDO PELO FUNDO.'
damiao='TO INDO. HOJE NINGUEM VAI PRO CEU ANTES DA HORA.'
before='../resultados-ux-v1/integracao/validation/interface-ntsc/'
save(dialogue('PADRE',padre),'radio-padre','Diálogos','Padre / recebendo',before+'dialogue-padre.png','O padre volta ao canto inferior direito, com o olhar para o centro. Damião fica no alto à esquerda. A fala ativa tem nome, RX/TX e moldura destacada; quem escuta mantém o retrato no mesmo lugar. Texto de produção preservado.')
save(dialogue('DAMIAO',damiao,page='2/2'),'radio-damiao','Diálogos','Damião / transmitindo',before+'dialogue-damiao.png','A resposta abre a janela de transmissão no alto, ao lado de Damião. O padre continua embaixo à direita. Os retratos não saltam entre posições e o olhar segue para o interior da tela. Uma fala por vez, sem repetir a mensagem anterior.')
save(dialogue('PADRE',padre,partial=True),'radio-digitando','Diálogos','Recebimento / texto entrando',before+'dialogue-padre.png','Texto entra de forma estável; A revela a fala inteira e uma nova pressão avança. Ruído e pequenos indicadores ficam fora da área de leitura. Substituir o som atual de coleta por um clique discreto de rádio, sem reiniciar o áudio a cada caractere.')
save(dialogue('DINORAH','O SINAL CAIU, DAMIAO. EU TE PEDI UMA COISA: PROTEGER QUEM NAO PODIA LUTAR.',remote='DINORAH',node=8,phase='6B',page='1/4'),'radio-dinorah','Diálogos','Dinorah / troca de interlocutor',before+'dialogue-6B.png','O quadro remoto recebe Dinorah no mesmo ponto. O fundo é a arena nativa da fase 6B; na integração, desenhá-la sem iniciar simulação nem alterar progresso. A mudança de personagem usa nome e retrato, preservando o mesmo canal.')
save(dialogue('PADRE','O BRASIL AINDA TEM MUITO CHAO OCUPADO. MAS HOJE VOCE PODE VOLTAR PRA CASA.',node=20,phase='16',page='2/3'),'radio-final','Diálogos','Padre / transmissão final',before+'dialogue-16.png','O rádio também enquadra o final, antes da caixa de vitória já aprovada. A interface de papel e metal permanece nos menus, missões e resultados; o diálogo ganha identidade própria de comunicação.')

def countdown(n,node=1):
 im=scene(node)
 if n=='VAI':
  # A small tag after zero, away from the player. Controls are already active.
  plate(im,(112,16,96,32),True);text(im,'VAI!',0,28,LIGHT,True)
  return im
 plate(im,(88,8,144,80),True)
 text(im,'PREPARE-SE',120,20,LIGHT)
 text(im,str(n),0,32,LIGHT,True,4)
 d=ImageDraw.Draw(im)
 for i in range(3):
  x=136+i*20;lit=i<int(n)
  d.rectangle((x,72,x+11,75),fill=LIGHT if lit else MAT)
 return im
for n in (3,2,1):
 save(countdown(n),'contagem-'+str(n),'Início da fase','Contagem / '+str(n),'atuais/ntsc/contagem-1-'+str(n)+'.png','Um segundo por número, com algarismo de 32 × 32 px e três marcadores que se apagam. O cenário e Damião continuam visíveis. Título e numeral dão o estado sem depender da cor. O aviso fica acima do personagem, sem barra preta atrás do texto.')
save(countdown('VAI'),'contagem-vai','Início da fase','Liberação / VAI!','atuais/ntsc/cenario-1.png','Ao chegar a zero, liberar movimento e tiro no mesmo quadro em que aparece VAI!. A etiqueta dura cerca de 350 ms e não prolonga o congelamento de 3 s. Remover a caixa grande antes de liberar o controle.')
save(countdown(3,4),'contagem-industrial','Início da fase','Contagem / cenário industrial','atuais/ntsc/contagem-4-3.png','Mesmo indicador na fase com lava: não recolore o chão, não cobre Damião e não substitui o cenário. A leitura usa fundo sólido apenas no pequeno instrumento.')
save(countdown(3,20),'contagem-chefe','Início da fase','Contagem / covil do Escorpião','atuais/ntsc/contagem-20-3.png','O padrão também funciona na arena clássica do chefe. Proposta sonora: três pulsos curtos, um por segundo, e um sinal de liberação distinto. Preservar a trilha e seus instrumentos, sem roubar o áudio de combate depois do zero.')
# Audit every executable story line, excluding comments/examples.
source=re.sub(r'//[^\n]*','',(GAME/'src/levels/story.c').read_text())
story=re.findall(r'(?:ESQUERDA|DIREITA)\(P_\w+,\s*"([^"]*)"',source)
assert story and all(len(textwrap.wrap(t,width=26,break_long_words=False))<=4 for t in story)
review={'scope':'Proposta para aprovação. Sem alterações no código do jogo, recursos exportados ou ROM.','romSHA256':hashlib.sha256((GAME/'out/release/Plaguefall.bin').read_bytes()).hexdigest(),'sourceFinding':'StoryLine.side existe, mas startLine/portrait ignoram o campo e posicionam todos os retratos em 2,6. O retrato do padre já olha para a esquerda: no lado esquerdo, olha para fora.','dialogue':{'anchors':{'damiao':[16,40,48,48],'remote':[248,144,48,48]},'bodyWidthCharacters':26,'bodyLines':4,'lineSpacingPixels':16,'font':[8,8],'storyLinesChecked':len(story),'allFit':True,'direction':'Damião à esquerda olha à direita; padre à direita olha à esquerda, usando os desenhos existentes sem espelhar.','identity':'Caixas de rádio escuras, metal e cobre; letras claras. Papel reservado aos menus/missões/guia/resultados.','controls':'A completa a fala; nova pressão avança. START pula a cena. Sem timer que pressione a leitura.','motion':'Apenas indicadores pequenos: RX/TX, barras de sinal e cursor; sem tremor, ruído ou piscadas sobre letras/retratos.','cases':cases[:5]},'countdown':{'seconds':3,'digitPixels':[32,32],'boxPixels':[144,80],'goTagPixels':[96,32],'goDurationMilliseconds':350,'inputRelease':'No zero, no mesmo quadro de VAI; a etiqueta não bloqueia controles.','timing':'3/2/1 por 1 s cada, ajustados por fps (50/60).','skip':'Não adicionar uma confirmação extra nem prolongar a espera.','cases':cases[5:]},'implementationNotes':['Respeitar StoryLine.side para posicionar a fala. Manter as duas âncoras; ao trocar padre por Dinorah, trocar só o retrato/nome remoto. Escorpião entra como voz na interferência, conforme a cena existente, sem criar perda de sinal como mecânica nova.','O fundo da transmissão é uma vista nativa da fase, com simulação parada. Criar um caminho de desenho sem spawn, sem marcar visita e sem alterar currentLevel, estatísticas ou rota. O mockup não prova esse caminho no runtime.','Planejar quatro paletas: cenário, moldura/fonte, Damião e interlocutor. Ocultar atores/HUD durante o diálogo libera duas paletas para os retratos. A moldura usa apenas a paleta existente do painel; não há cinco paletas simultâneas.','O contador precisa de um pequeno recurso próprio; não carregar o painel completo sobre o mapa. Investigar o empréstimo temporário da reserva de ícones de inimigos, preservando seus dados e a paleta. Restaurar antes de liberar o controle; não sobrescrever tiles do cenário ou do herói.','VAI! deve usar recursos/paletas de jogo compatíveis com o combate ativo durante seus 350 ms; restaurar a paleta temporária da contagem no zero.','Antes de implementar, validar em ROM: posições e olhar dos quatro retratos, todas as falas, A/completar/avançar, START/pular, simulação congelada, vídeo/paletas na transição, 3 s exatos em PAL/NTSC e liberação de movimento/tiro no zero.'],'cases':cases,'textBoundsChecked':len(checks)}
(ROOT/'avaliacao.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
sheet=Image.new('RGB',(1280,3*256),(34,29,24));d=ImageDraw.Draw(sheet)
for i,c in enumerate(cases):
 x=i%4*320;y=i//4*256;d.text((x+8,y+5),c['id'],fill=LIGHT);sheet.paste(Image.open(ROOT/c['after']),(x,y+24))
sheet.save(ROOT/'visao-geral.png')
notes=''.join('<li>'+html.escape(t)+'</li>' for t in review['implementationNotes'])
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rádio e entrada em combate — proposta UX</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#211d18;color:#f0ddb7}*{box-sizing:border-box}body{max-width:1280px;margin:auto;padding:26px}h1{font-size:30px;margin:7px 0 12px}.eyebrow{color:#c5b182;letter-spacing:.14em;font-size:12px}.badge{display:inline-block;border:1px solid #9e8254;color:#e3ce9a;padding:6px 9px;border-radius:5px;font-size:12px}p{line-height:1.5}.muted{color:#bfb49d;font-size:13px}.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:20px 0 14px}button,select{font:inherit;color:inherit;background:#3a3126;border:1px solid #9a7445;border-radius:5px;padding:10px;cursor:pointer}button:hover,button:focus-visible{background:#655038}button[aria-pressed=true]{background:#8d552f;color:#fff4db}select{max-width:100%}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;padding:12px;background:#30291f;border:1px solid #65553b;border-radius:8px}figure img{width:100%;aspect-ratio:320/224;image-rendering:pixelated;display:block}figcaption{font-size:13px;color:#ceba94;margin-bottom:9px}.note{background:#30352b;border-left:3px solid #a7a16f;padding:14px 18px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}.grid button{padding:6px;text-align:left}.grid img{display:block;width:100%;image-rendering:pixelated;margin-bottom:6px}.grid span{font-size:13px}.native figure img{width:320px;max-width:100%}details{padding:15px;background:#30291f;margin-top:22px}li{line-height:1.5;margin:12px 0}a{color:#f1c480}.rules{display:grid;grid-template-columns:1fr 1fr;gap:18px}.rules div{background:#30291f;padding:16px;border-top:2px solid #887346}h2{font-size:20px;margin:4px 0 10px}#demoStatus{color:#d9d2af;font-size:13px}@media(max-width:760px){body{padding:16px}.compare,.rules{grid-template-columns:1fr}.compare figure:last-child{order:-1}.grid{grid-template-columns:repeat(2,1fr)}}
</style><div class="eyebrow">PLAGUEFALL · PROPOSTA DE UX E GAME DESIGN</div><h1>Vozes pelo rádio. Entrada em combate.</h1><span class="badge">PARA APROVAÇÃO · JOGO E ROM SEM ALTERAÇÕES</span>
<p>O diálogo recupera a composição entre personagens: <strong>Damião no alto à esquerda; padre e interlocutores embaixo à direita, olhando para dentro.</strong> A transmissão usa instrumentos de rádio, metal e letras claras. O painel de papel continua nos menus, missões e resultados.</p>
<div class="toolbar"><label for="case">Situação</label><select id="case"></select><button id="native" aria-pressed="false">Ver em 1×</button><button id="radioDemo">Simular conversa</button><button id="countDemo">Ver contagem de 3 s</button><span id="demoStatus" aria-live="polite"></span></div>
<div class="compare"><figure><figcaption>ATUAL · CAPTURA DA ROM</figcaption><img id="before" alt="Interface atual do jogo"></figure><figure><figcaption id="proposedLabel">PROPOSTA · 320 × 224</figcaption><img id="after" alt="Proposta nativa para diálogo por rádio ou contagem"></figure></div><p id="note" class="note" aria-live="polite"></p>
<div class="toolbar"><button id="advance">A / completar ou avançar</button><button id="skip">START / pular demonstração</button><span class="muted">Estes controles simulam a proposta, sem controlar o jogo.</span></div>
<div class="rules"><div><h2>Diálogo: recuperar a encenação</h2><p>Hoje o código ignora o lado definido para a fala e leva todos ao mesmo lugar. A nova proposta mantém os retratos fixos, destaca quem fala com RX/TX e desloca a janela da mensagem para perto desse personagem. Nome, retrato e moldura dão a mesma pista; a cor é complementar.</p><p>Uma fala por vez, sem pressão de tempo. A completa e depois avança; START pula a cena. Indicadores animam fora das letras. As 51 falas executáveis cabem em até quatro linhas de 26 caracteres, com a fonte original e 16 px entre linhas.</p></div><div><h2>Contagem: o instante de agir</h2><p>3 → 2 → 1 ocupa os mesmos três segundos de hoje. Um algarismo grande, três marcadores e pulsos sonoros curtos tornam o ritmo claro. Cenário, HUD e posição de Damião permanecem visíveis.</p><p>No zero, a caixa grande some, surge uma etiqueta “VAI!” por cerca de 350 ms e o controle já está liberado. A etiqueta não prolonga a espera. A trilha continua; o sinal de liberação é diferente dos três pulsos.</p></div></div>
<div id="cards" class="grid"></div><details><summary>Limitações e caminho de implementação</summary><ul>NOTES</ul></details><p class="muted">Composições em tamanho nativo, com retratos e cenários existentes. Nenhuma arte de personagem foi redesenhada. A simulação no navegador ilustra ritmo e navegação; não mede desempenho do Mega Drive. A captura atual foi feita com a ROM intacta; a RAM selecionou a fase, e a contagem executou seu tempo normal. Os fundos de diálogo são capturas nativas com sprites ocultos pela pausa, sem abrir o painel; o jogo não recebeu esse layout.</p><p><a href="avaliacao.json">Especificação da proposta</a> · <a href="atuais/ntsc/report.json">Registro das capturas atuais</a> · <a href="../resultados-ux-v1/revisao.html">Menus e resultados atuais</a></p>
<script>const cases=CASES;const select=document.querySelector('#case'),status=document.querySelector('#demoStatus');let index=0,timers=[],radioStep=-1;for(const [i,c] of cases.entries()){select.add(new Option(c.group+' / '+c.label,i));const b=document.createElement('button');b.innerHTML=`<img src="${c.after}" alt=""><span>${c.label}</span>`;b.onclick=()=>{stop();show(i)};document.querySelector('#cards').append(b)}function stop(){timers.forEach(clearTimeout);timers=[];radioStep=-1;status.textContent=''}function show(i){index=i;select.value=i;const c=cases[i];document.querySelector('#before').src=c.before;document.querySelector('#after').src=c.after;document.querySelector('#note').textContent=c.note;document.querySelectorAll('#cards button').forEach((b,j)=>b.setAttribute('aria-pressed',i===j))}select.onchange=()=>{stop();show(+select.value)};document.querySelector('#native').onclick=e=>{const on=document.body.classList.toggle('native');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Ampliar':'Ver em 1×'};document.querySelector('#radioDemo').onclick=()=>{stop();radioStep=0;show(2);status.textContent='RX: a fala está entrando. A mostra tudo.'};function advance(){stopTimersOnly();if(radioStep<0)radioStep=0;if(radioStep===0){show(0);radioStep=1;status.textContent='Fala completa. A passa à resposta de Damião.'}else if(radioStep===1){show(1);radioStep=2;status.textContent='TX: Damião responde. A conclui a conversa.'}else{radioStep=-1;status.textContent='Conversa encerrada → missão. Simulação concluída.'}}function stopTimersOnly(){timers.forEach(clearTimeout);timers=[]}document.querySelector('#advance').onclick=advance;document.querySelector('#skip').onclick=()=>{stop();status.textContent='Cena pulada → missão. O jogo não foi alterado.'};document.querySelector('#countDemo').onclick=()=>{stop();show(5);status.textContent='3 · controles congelados';[[1000,6,'2 · controles congelados'],[2000,7,'1 · controles congelados'],[3000,8,'VAI! · controles liberados no zero']].forEach(([ms,i,s])=>timers.push(setTimeout(()=>{show(i);status.textContent=s},ms)));timers.push(setTimeout(()=>{document.querySelector('#after').src='atuais/ntsc/cenario-1.png';status.textContent='Combate ativo · etiqueta removida; tempo total de congelamento: 3 s.'},3350))};document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key.toLowerCase()==='a'){e.preventDefault();advance()}});show(0)</script></html>'''
page=page.replace('NOTES',notes).replace('CASES',json.dumps(cases,ensure_ascii=False));(ROOT/'proposta-aprovada.html').write_text(page)
print(json.dumps({'cases':len(cases),'storyLinesChecked':len(story),'maxLines':4,'textBoundsChecked':len(checks),'romUnchanged':review['romSHA256']},indent=2))
if __name__=='__main__':pass
