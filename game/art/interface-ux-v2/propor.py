"""Native-size UI proposals only. Reads ROM captures/assets; never exports game resources."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,html,json,re,textwrap
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
OUT=ROOT/'propostas';OUT.mkdir(exist_ok=True)
CURRENT=ROOT.parent/'interface-ux-v1/atuais/ntsc'
FONT=Image.open(GAME.parent/'SGDK/res/image/font_default.png').convert('L')
BG=(219,182,109);INK=(48,28,16);GOLD=(109,36,0);MUTED=(56,66,36)
LIGHT=(255,219,146)
BACKING=Image.open(ROOT/'source/painel-nativo.png').convert('RGB')
checks=[];cases=[];lineStart=0

def text(im,s,x,y,color=INK,right=False):
 if right:x=38-len(s)
 if y==26:color=LIGHT
 assert isinstance(x,int) and 2<=x and x+len(s)<=38,(s,x,len(s))
 assert 1<=y<=26 and all(32<=ord(c)<128 for c in s),(s,y)
 for i,c in enumerate(s):
  g=ord(c)-32
  glyph=FONT.crop((g%16*8,g//16*8,g%16*8+8,g//16*8+8))
  im.paste(color,((x+i)*8,y*8),glyph.point(lambda v:255 if v else 0))
 checks.append(dict(text=s,x=x,y=y,length=len(s),palette='light' if color==LIGHT else 'accent' if color==GOLD else 'body'))

def paragraph(im,s,y,color=INK,width=36,x=2,step=1):
 lines=textwrap.wrap(s,width=width,break_long_words=False,break_on_hyphens=False)
 for i,line in enumerate(lines):text(im,line,x,y+i*step,color)
 return y+len(lines)

def base(title,right=''):
 im=BACKING.copy()
 d=ImageDraw.Draw(im)
 d.rectangle((13,14,306,25),fill=(255,219,146))
 d.rectangle((12,202,307,219),fill=(73,36,0))
 d.line((12,202,307,202),fill=(146,73,36))
 text(im,title,2,2,GOLD)
 if right:text(im,right,2,2,MUTED,True)
 ImageDraw.Draw(im).line((16,30,303,30),fill=(146,109,73))
 return im

def save(im,id,group,label,before,note):
 global lineStart
 assert im.size==(320,224)
 im.save(OUT/(id+'.png'))
 cases.append(dict(id=id,group=group,label=label,before='../interface-ux-v1/propostas/'+id+'.png',rom='../interface-ux-v1/atuais/ntsc/'+before+'.png',after='propostas/'+id+'.png',note=note,lines=checks[lineStart:]))
 lineStart=len(checks)

def copy_icon(im,source,box,pos):
 icon=Image.open(CURRENT/(source+'.png')).convert('RGB').crop(box)
 # Keep the existing sprite pixels. Only replace the flat black screen background.
 mask=Image.new('L',icon.size);mask.putdata([0 if p==(0,0,0) else 255 for p in icon.getdata()])
 im.paste(icon,pos,mask)

source=(GAME/'src/system/video/screens/routemap.c').read_text()
places=re.findall(r'"([^"]*)"',source.split('PLACE[NODE_MAX] = {')[1].split('};')[0])
names=['','1','2A','2B','3','4','5','6A','6B','7','8','9','10A','10B','11','12','13A','13B','14','15','16']
files=['','01','02','02b','03','04','05','06','06b','07','08','09','10','10b','11','12','13','13b','14','15','16']
cols=[0,0,1,1,2,3,4,5,5,6,7,8,9,9,10,11,12,12,13,14,15]
branch={
 '1':'BOMBA DANIFICA A IGREJA.',
 '5':'SE O SINAL CAIR, A FUGA SEGUE POR TERRA.',
 '9':'SEM PERDER VIDA: ACESSO DOS TECNICOS.',
 '12':'ANTES DE 60 S: PASSAGEM DIRETA.'}
tips={
 '1':'MANTENHA ESPACO PARA DESVIAR.',
 '2A':'OS LARANJAS AVANCAM RAPIDO.',
 '2B':'A LAMA REDUZ SEU MOVIMENTO.',
 '3':'DESVIE DOS VAZAMENTOS QUENTES.',
 '4':'ESPERE O ESCUDO DOS ROXOS BAIXAR.',
 '5':'OS INSETOS ATACAM A SANTA.',
 '6A':'O PISO QUENTE CAUSA DANO.',
 '6B':'O PISO QUENTE CAUSA DANO.',
 '7':'OS ROXOS ERGUEM ESCUDOS EM CICLOS.',
 '8':'NAO FIQUE PARADO JUNTO AO CALOR.',
 '9':'DANO CURADO TAMBEM CONTA NA ROTA.',
 '10A':'CUIDADO COM AS INVESTIDAS.',
 '10B':'DESVIE DO CALOR E DA LAMA.',
 '11':'AS SAUVAS ROXAS CHAMAM LACAIOS.',
 '12':'CALOR E LAMA ATRAPALHAM A PASSAGEM.',
 '13A':'O PISO QUENTE CAUSA DANO.',
 '13B':'A LAMA REDUZ SEU MOVIMENTO.',
 '14':'AS SAUVAS PODEM DIVIDIR OU INVOCAR.',
 '15':'NAO DEIXE O ENXAME CERCAR VOCE.',
 '16':'DESVIE DOS TIROS E DOS LACAIOS.'}
phases=[]
for node in range(1,21):
 name=names[node];raw=(GAME/f'src/levels/defs/level{files[node]}.c').read_text()
 target=re.search(r'\.killTarget\s*=\s*(\d+)',raw)
 goal='DERROTE O ESCORPIAO.' if name=='16' else 'PROTEJA O SINALIZADOR POR 30 S.' if name=='5' else f'ELIMINE {target[1]} INIMIGOS.'
 roster=re.search(r'roster\[\]\s*=\s*\{([^}]+)',raw)[1]
 enemies=[s.strip() for s in roster.split(',') if s.strip()]
 stage=dict(id=name,node=node,name=places[node],step=cols[node]+1,goal=goal,attention=tips[name],route=branch.get(name),roster=enemies,source=f'src/levels/defs/level{files[node]}.c')
 phases.append(stage)
 im=base('FASE '+name,'ETAPA '+str(cols[node]+1)+'/16')
 text(im,places[node],2,5,GOLD)
 text(im,'OBJETIVO',2,8,GOLD);paragraph(im,goal,10)
 text(im,'ATENCAO',2,13,GOLD);paragraph(im,tips[name],15)
 if name in branch:paragraph(im,branch[name],17)
 text(im,'AMEACAS',2,20,GOLD)
 if name=='16':
  text(im,'ESCORPIAO E LACAIOS',2,23)
 else:
  copy_icon(im,'prep-'+name,(64,104,300,136),(16,168))
 text(im,'A: COMECAR',2,26,GOLD,True)
 save(im,'prep-'+name,'Fases',name+' / '+places[node],'prep-'+name,'Objetivo e perigos vêm da fase real. A dica de rota aparece apenas nas quatro bifurcações. A faixa de inimigos usa a arte residente; o chefe recebe identificação explícita.')

for name in ('1','5','9','12','16'):
 im=base('PAUSADO','FASE '+name)
 node=names.index(name);text(im,places[node],2,5,GOLD)
 text(im,'OBJETIVO',2,7,GOLD)
 paragraph(im,phases[node-1]['goal'],8)
 text(im,'EM ANDAMENTO',2,11,GOLD)
 progress={'1':'INIMIGOS: 06 DE 10','5':'FALTAM 23 S / SINAL: 76 DE 100','9':'INIMIGOS: 12/24 / DANO NA FASE: 0','12':'INIMIGOS: 18/30 / TEMPO: 38 S','16':'ESCORPIAO: 18 DE 25 DE VIDA'}[name]
 text(im,progress,2,12)
 text(im,'VIDA: 084/100     BOMBAS: 2',2,14)
 text(im,'ITEM SELECIONADO: GELO (3 TIROS)',2,15,MUTED)
 ImageDraw.Draw(im).rectangle((12,132,307,147),fill=(109,36,0))
 for y,label in [(17,'> CONTINUAR'),(19,'  COMO JOGAR'),(21,'  VOLTAR AO TITULO')]:text(im,label,2,y,LIGHT if y==17 else INK)
 text(im,'CIMA/BAIXO: ESCOLHER',2,24,MUTED)
 text(im,'A: CONFIRMAR   B/START: RETOMAR',2,26,GOLD,True)
 save(im,'pause-'+name,'Pause','Pause / fase '+name,'pause-'+name,'Progresso e recursos ilustrativos, não lidos desta captura. Continuar é a seleção inicial. B e START retomam; sair exige selecionar a opção e confirmar. Sem redesenhar os inimigos aqui.')
im=base('SAIR DA PARTIDA?')
text(im,'O PROGRESSO DESTA PARTIDA',2,8);text(im,'SERA PERDIDO.',2,10)
ImageDraw.Draw(im).rectangle((12,124,307,139),fill=(109,36,0))
text(im,'> CONTINUAR JOGANDO',2,16,LIGHT);text(im,'  SAIR PARA O TITULO',2,19)
text(im,'CIMA/BAIXO: ESCOLHER',2,24,MUTED)
text(im,'A: CONFIRMAR   B/START: CANCELAR',2,26,GOLD,True)
save(im,'pause-sair','Pause','Confirmação de saída','pause-1','Confirmação apenas para abandonar a partida. Foco inicial na opção que preserva o progresso; B/START cancelam e retornam ao pause.')

# Six short reference pages; inputs share a stable footer.
def help_base(title,page):
 im=base('COMO JOGAR',str(page)+'/6')
 text(im,title,2,5,GOLD)
 text(im,'ESQ/DIR: PAGINA   A: PROXIMA',2,24,MUTED)
 text(im,'B/START: VOLTAR',2,26,GOLD,True)
 return im
im=help_base('CONTROLES',1)
for y,l,r in [(8,'DIRECIONAL','MOVER E MIRAR'),(10,'A','ATIRAR (SEGURE)'),(12,'C','SELECIONAR ITEM'),(14,'B','USAR ITEM'),(16,'START','PAUSAR')]:text(im,l,2,y,GOLD);text(im,r,14,y)
text(im,'MIRE EM UMA DAS 8 DIRECOES.',2,19)
text(im,'SOLTE O DIRECIONAL PARA PARAR.',2,20)
text(im,'O TIRO MANTEM A ULTIMA DIRECAO.',2,21)
save(im,'help-controles','Como jogar','1 / Controles','help-1','Corrige o corte na borda e explica a mira parada, inclusive diagonal. A passa à próxima página; B/START voltam à origem: menu ou pause.')
im=help_base('ITENS / AO COLETAR',2)
for row,old,label,effect in [(8,6,'MARMITA','CURA 15 DE VIDA (MAX. 100)'),(12,10,'DIVISOR DE DISPARO','+1 BALA POR TIRO (MAX. 5)'),(16,14,'SERVO DE PASSADA','+20% DE VELOCIDADE (MAX. +100%)')]:
 copy_icon(im,'help-4',(24,old*8,40,old*8+16),(16,row*8));text(im,label,5,row,GOLD);text(im,effect,5,row+1)
text(im,'ESTES EFEITOS NAO PRECISAM DO B.',2,20)
text(im,'A VIDA ATUAL PASSA PARA OUTRA FASE.',2,21)
save(im,'help-coletar','Como jogar','2 / Efeitos ao coletar','help-4','Efeito aparece junto do item, antes de qualquer nome narrativo longo. Mantém valores reais e reforça a diferença entre coletar e ativar.')
im=help_base('INVENTARIO / C ESCOLHE, B USA',3)
for row,old,label,effect in [(7,5,'BOMBA / CARGA DE DESMONTE','LIMPA A TELA'),(10,8,'ESCUDO / CAPACITOR','3 S SEM SOFRER DANO'),(13,11,'RAIO / BOBINA','5 DISPAROS EM CADEIA'),(16,14,'GELO / REFIL FRIO','3 DISPAROS / CONGELA POR 5 S'),(19,17,'FOGO / REFIL QUENTE','4 DISPAROS / QUEIMA POR 6 S')]:
 copy_icon(im,'help-5',(24,old*8,40,old*8+16),(16,row*8));text(im,label,5,row,GOLD);text(im,effect,5,row+1)
text(im,'RAIO/GELO/FOGO: 1 CARGA POR DISPARO.',2,22)
save(im,'help-inventario','Como jogar','3 / Inventário','help-5','Distingue quantidade guardada e disparos especiais. A regra de gastar carga refere-se a raio/gelo/fogo. Sem espaço, o item coletado é perdido; explicar isso no índice de itens e com feedback contextual, sem mais texto nesta página.')
im=help_base('INIMIGOS / COR E FAMILIA',4)
for y,old,label in [(8,7,'VERMELHO: TIRO A DISTANCIA'),(10,9,'AMARELO: PERSEGUE VOCE'),(12,11,'ROXO: ESCUDO EM CICLOS'),(14,13,'LARANJA: INVESTIDA RAPIDA')]:
 copy_icon(im,'help-2',(24,old*8,32,old*8+8),(16,y*8));text(im,label,4,y)
for y,old,label in [(17,17,'SERRA-PAU / RESISTENTE'),(19,19,'MUTUCA / MENOS VIDA'),(21,21,'SAUVA / HABILIDADE ESPECIAL')]:
 copy_icon(im,'help-2',(24,(old-1)*8,48,(old+2)*8),(16,(y-1)*8));text(im,label,7,y)
save(im,'help-inimigos','Como jogar','4 / Inimigos','help-2','Nomes, arte e comportamento se complementam; a cor não é a única pista. Os ícones das famílias são os insetos reais, sem voltar à nomenclatura antiga de formas geométricas.')
im=help_base('SAUVAS / HABILIDADES',5)
for y,old,label,effect in [(8,7,'ARTILHEIRO','ABRE UM LEQUE DE TIROS'),(11,9,'ALCATEIA','SE DIVIDE EM DOIS'),(14,11,'FORTALEZA','INVOCA LACAIOS'),(17,13,'METEORO','TELEPORTA E AVANCA')]:
 copy_icon(im,'help-3',(24,old*8,32,old*8+8),(16,y*8));text(im,label,4,y,GOLD);text(im,effect,4,y+1)
text(im,'ROXOS: ATAQUE COM O ESCUDO BAIXO.',2,21)
save(im,'help-elite','Como jogar','5 / Sauvas','help-3','Mantém as quatro habilidades em consulta opcional, com uma ação que ajuda a lidar com a ameaça.')
im=help_base('MISSOES E ROTAS',6)
text(im,'16 ETAPAS. O CAMINHO PODE MUDAR.',2,8)
text(im,'ELIMINE A META, PROTEJA O SINAL',2,10)
text(im,'OU DERROTE O CHEFE DA FASE FINAL.',2,11)
text(im,'CONFIRA A MISSAO ANTES DE COMECAR.',2,13)
for y,s in [(16,'1: BOMBAS AFETAM A IGREJA.'),(17,'5: PROTEJA O SINALIZADOR.'),(18,'9: EVITE PERDER VIDA.'),(19,'12: TERMINE ANTES DE 60 S.')]:text(im,s,2,y)
text(im,'A ROTA E AUTOMATICA. NAO HA ESCOLHA.',2,21)
save(im,'help-rotas','Como jogar','6 / Missões e rotas','help-1','Explica as 16 etapas por partida e as ações que decidem rotas. As 20 localidades possíveis não são 20 fases numa única partida. A frase sobre chefes vale para o final atual; não sugere objetivos ainda ausentes da campanha.')

for id,name,asset,speech,idx,total in [
 ('dialogue-padre','PADRE / RADIO','comando','DAMIAO, AQUI E O PADRE. SEGURE O PATIO. TEM GENTE FUGINDO PELO FUNDO.',1,2),
 ('dialogue-damiao','DAMIAO','damiao','TO INDO. HOJE NINGUEM VAI PRO CEU ANTES DA HORA.',2,2)]:
 im=base('PATIO DA IGREJA',str(idx)+'/'+str(total))
 portrait=Image.open(GAME/'art/dialogue-portraits-v1'/(asset+'.png')).convert('RGBA')
 assert portrait.size==(48,48)
 im.paste(portrait,(16,48),portrait)
 text(im,name,10,7,GOLD)
 text(im,'FASE 1',10,9,MUTED)
 paragraph(im,speech,14,width=34,step=2)
 text(im,'A: AVANCAR' if idx<total else 'A: VER MISSAO',2,24,GOLD)
 text(im,'START: PULAR CENA',2,26,MUTED,True)
 save(im,id,'Diálogos',name.title(),'dialogue-padre' if idx==1 else 'dialogue-damiao','Mantém as falas e os retratos existentes. Um único foco de leitura, até 34 colunas e quatro linhas, nome do padre e progresso. Durante a digitação, a legenda seria A: MOSTRAR TEXTO; após completar, A: AVANCAR ou A: VER MISSAO.')

findings=[
 dict(priority='Alta',screen='Como jogar',problem='Informação incorreta sobre a campanha.',evidence='A página 1 diz 15 fases e orienta eliminar inimigos em todas. O grafo tem 16 etapas por partida, proteção na 5 e chefe na 16.',change='Corrigir para 16 etapas e explicar os três objetivos presentes na campanha.',source='src/system/video/screens/help.c:50'),
 dict(priority='Alta',screen='Como jogar',problem='O controle C perde texto na borda direita.',evidence='TROCAR ITEM (INVENTARIO) começa na coluna 18 e ultrapassa as 40 colunas; o corte aparece na captura.',change='Trocar por SELECIONAR ITEM e reservar margem de 16 px.',source='src/system/video/screens/help.c:46'),
 dict(priority='Alta',screen='Preparação',problem='A fase final apresenta uma regra que não representa a luta.',evidence='FASE 16 mostra META: MATE 1 INIMIGOS e INTERVALO DE SPAWN: 99 S. O chefe é criado no começo; não há spawn regular nessa fase. Seu ícone é ignorado por ser maior que 32 px.',change='DERROTE O ESCORPIAO. Mostrar chefe e lacaios como ameaça; retirar intervalo de spawn.',source='src/levels/defs/level16.c:12'),
 dict(priority='Alta',screen='Pause',problem='Um toque em B abandona a partida.',evidence='ST_PAUSE volta ao título ao receber B, sem confirmação; B é também o botão de usar item no combate.',change='Menu com continuar selecionado; B/START retomam. Confirmar somente a saída para o título.',source='src/core/flow.c:464'),
 dict(priority='Alta',screen='Preparação',problem='Atalhos de desenvolvimento ficam ativos na partida.',evidence='C percorre preparações e A+B+C pula a fase durante o jogo. O combo coincide com os três comandos normais de combate.',change='Separar atalhos por flag de desenvolvimento e desativá-los na versão do jogador; manter o modo de teste no ambiente de desenvolvimento.',source='src/core/flow.c:407'),
 dict(priority='Média',screen='Pause',problem='A tela não responde quanto falta para vencer.',evidence='Mostra a meta inicial e o intervalo de spawn, sem progresso de mortes, segundos restantes ou vida do sinalizador.',change='Compartilhar um resumo do objetivo entre HUD, preparação e pause; no pause exibir o estado congelado.',source='src/system/video/screens/pause.c:27'),
 dict(priority='Média',screen='Pause',problem='Inimigos aparece como uma seção vazia.',evidence='LEVEL_drawInfo retorna quando arenaActive está ligado, após desenhar o rótulo INIMIGOS. O fundo também compete com o texto.',change='Retirar a seção do pause e usar um painel opaco com objetivo, progresso, recursos e ações.',source='src/levels/levels.c:130'),
 dict(priority='Média',screen='Preparação',problem='Dados internos ocupam espaço de informação tática.',evidence='INTERVALO DE SPAWN não explica o que fazer; perigos do terreno e condições das bifurcações não aparecem no briefing.',change='Priorizar nome do lugar, objetivo concreto, perigo e dica de rota. Derivar objetivos da definição da fase, sem duplicar números manualmente.',source='src/levels/levels.c:125'),
 dict(priority='Média',screen='Como jogar',problem='Consulta longe do momento de necessidade.',evidence='Ajuda só abre pelo título; no pause é preciso sair da partida para consultar. Não explica a mira diagonal parada nem a diferença entre estoque e cargas de tiro.',change='Oferecer consulta no pause, voltar à tela de origem e ensinar mover/mirar, C seleciona, B ativa e A dispara.',source='src/system/video/screens/title.c:98'),
 dict(priority='Média',screen='Diálogos',problem='O olhar muda de canto e os comandos são pouco específicos.',evidence='Retratos e falas alternam topo esquerdo/fundo direito, deixando grande área vazia. A AVANCA também completa texto em digitação; os comandos ficam na última linha.',change='Um retrato e uma caixa fixos; PADRE / RADIO em vez de COMANDO; contador de falas e legenda que acompanha a ação. Manter o texto autoral.',source='src/system/video/screens/story.c:23'),
 dict(priority='Baixa',screen='Fluxo',problem='A sequência exige várias confirmações antes de voltar à ação.',evidence='Entre fases há conclusão, mapa/viagem, diálogo, preparação e contagem de 3 segundos. O mapa já foi aprovado e permanece como referência.',change='Manter leitura sob controle do jogador. No último diálogo sinalizar VER MISSAO; avaliar reduzir a contagem para 1 segundo somente após teste de jogo.',source='src/core/flow.c:153')]

rom=GAME/'out/release/Plaguefall.bin'
audit=dict(status='proposal_only',romChanged=False,romSHA256=hashlib.sha256(rom.read_bytes()).hexdigest(),artDirection='Resistance field panel: aged ochre paper, rusty steel, olive brackets, copper radio wiring; image_gen reference-based backing, separate 8x8 text.',basis='Source inspection plus 38 current-ROM screenshots using controls only, including all 20 preparation cards. Heuristic review, not a user study.',findings=findings,phases=phases,cases=cases,
 navigation=dict(pause='Cima/baixo escolhe; A confirma; B/START retoma. Saída abre confirmação com continuar selecionado.',help='ESQ/DIR ou A percorrem; B/START voltam ao menu ou ao pause, conforme a origem. Página/tópico visível.',story='A mostra texto / avança / abre missão. START pula a cena. Nunca pula a preparação.',prep='A começa. Texto não avança por tempo. Dicas descrevem ações reais e não prometem resgate jogável.'),
 implementation=[
 'Nenhuma mudança em fonte do jogo, ROM, balanceamento ou controles foi aplicada nesta proposta.',
 'Fonte 8x8 existente, agora transparente sobre a arte; 40x28 tiles; área de texto de 36 colunas entre x16 e x304; comandos na linha 26 (8 px acima da borda). As prévias não estão exportadas como recursos VDP.',
 'Preparação: nome e dica estáticos por nó; objetivo e valores derivados de LevelDef/GRAPH. Exceção explícita para chefe. Os avisos de rota consultam as condições existentes.',
 'Pause: expor consulta somente de leitura dos contadores de objetivo (restante/coleta/NPC) hoje privados e da vida do chefe. Dano e tempo de rota vêm de PhaseStats; não inferir dano a partir da vida atual. Timer, NPC, inimigos e inventário ficam congelados também no guia.',
 'A nova arte cobre a tela: deve emprestar e restaurar padrões e paletas sem reiniciar a fase. O fundo foi reduzido a até 15 cores RGB333 para estudar um único banco. Fonte transparente, cor de destaque e ícones/retratos precisam de organização por tela. O orçamento e a restauração devem ser validados na implementação.',
 'Ajuda via pause exige restaurar planos, fonte, paletas e cache de inimigos. HELP_run atual foi feito para o título e não pode ser chamado de dentro da fase sem adaptar o ciclo de recursos.',
 'Inventário no pause é consulta; seleção e ativação continuam no combate. Um modo de tiro especial por vez. Inventário tem bomba mais três slots; repetidos ocupam slots; coleta sem slot livre é perdida.',
 'Diálogo: reutilizar um retrato de 36 tiles e manter máximo de quatro linhas. Separar contador de fala do número de fase. Conferir quebra de todas as falas e retorno correto após pular.',
 'A confirmação de saída é o único novo passo obrigatório e só ocorre ao abandonar a partida.',
 'Após aprovação: validar NTSC/PAL, controle de 3 botões, objetivos, recursos no pause, restauração ao fechar ajuda, retomada sem consumir item e ausência dos atalhos de desenvolvimento no release.'
 ])
metadata='proposta-regenerada.json' if (ROOT/'integracao/build-validation.json').exists() else 'avaliacao.json'
(ROOT/metadata).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
story_source=re.sub(r'//[^\n]*','',(GAME/'src/levels/story.c').read_text())
dialogues=re.findall(r'(?:ESQUERDA|DIREITA)\(\w+,\s*"([^"]*)"',story_source)
assert all(len(textwrap.wrap(t,width=34,break_long_words=False))<=4 for t in dialogues)
assert all((ROOT/c[key]).is_file() for c in cases for key in ('before','after'))
(ROOT/'validacao-layout.json').write_text(json.dumps(dict(proposalOnly=True,nativeSize=[320,224],font=[8,8],cases=len(cases),renderedTextLines=len(checks),maxCharacters=max(c['length'] for c in checks),allTextWithinSafeArea=True,allReferencedImagesExist=True,dialogueLinesChecked=len(dialogues),dialogueWidth=34,dialogueMaxLines=4,dialogueLineSpacingPixels=16,gameResourcesWritten=False,romSHA256=audit['romSHA256']),indent=2)+'\n')

# Self-contained review with current captures on the left and proposal on the right.
buttons=''.join('<button data-group="'+g+'">'+g+'</button>' for g in ['Pause','Como jogar','Fases','Diálogos'])
rows=''.join('<tr><td>'+html.escape(f['priority'])+'</td><td>'+html.escape(f['screen'])+'</td><td><strong>'+html.escape(f['problem'])+'</strong><p>'+html.escape(f['evidence'])+'</p></td><td>'+html.escape(f['change'])+'</td></tr>' for f in findings)
stages=''.join('<tr><td>'+c['id']+'</td><td>'+c['name']+'</td><td>'+c['goal']+'</td><td>'+c['attention']+('<p>'+c['route']+'</p>' if c['route'] else '')+'</td></tr>' for c in phases)
tech=''.join('<li>'+html.escape(s)+'</li>' for s in audit['implementation'][1:])
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaguefall — proposta artística das interfaces</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{background:#101719;color:#f2dfc0;margin:0;font:16px/1.55 system-ui,sans-serif}main{max-width:1320px;margin:auto;padding:24px}a{color:#ffbf57}.tag{color:#ffbf57;font-size:12px;letter-spacing:.08em}h1{font-size:32px;line-height:1.2;margin:10px 0}h2{font-size:23px;margin:28px 0 14px}p{color:#bac1b4}header p{max-width:1050px;margin:8px 0}.badge{display:inline-block;padding:4px 10px;border:1px solid #766042;border-radius:20px;font-size:12px;color:#ffbf57}.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:18px 0}button,select{font:15px system-ui;background:#202c2f;color:#f2dfc0;border:1px solid #536266;border-radius:5px;padding:8px 12px}button{cursor:pointer}button[aria-pressed=true]{background:#ffbf57;color:#101719}label{font-size:13px;color:#bac1b4}.controls select{min-width:240px;max-width:100%}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}figcaption{font-size:14px;margin-bottom:8px}figure:last-child figcaption{color:#ffbf57}img{width:100%;height:auto;display:block;image-rendering:pixelated;border:1px solid #475256}#note{background:#192326;padding:12px 16px;border-left:3px solid #ffbf57;margin:16px 0;font-size:14px}.decision{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:24px 0}.card{padding:16px;background:#192326;border:1px solid #354347;border-radius:7px}.card strong{color:#ffbf57}.card p{font-size:14px;margin:6px 0}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #354347;padding:12px}th{color:#ffbf57}td p{margin:6px 0}details{border-top:1px solid #475256;margin:24px 0;padding-top:16px}summary{cursor:pointer;font-size:18px;color:#ffbf57}li{color:#bac1b4;margin:10px 0}footer{border-top:1px solid #475256;margin-top:28px;padding-top:16px;font-size:13px}code{overflow-wrap:anywhere}@media(max-width:720px){main{padding:18px}.comparison,.decision{grid-template-columns:1fr}h1{font-size:26px}.controls select{min-width:0;width:100%}}</style>
<main><header><div class="tag">PLAGUEFALL / UX E GAME DESIGN / PROPOSTA 02 / DIRECAO DE ARTE</div><h1>Um painel da resistência, dentro do mundo do jogo.</h1><span class="badge">Para avaliação · jogo e ROM sem alterações</span><p>Papel ocre gasto, aço enferrujado, cobre e suportes verde-oliva. A moldura parte da arte do sertão industrial do jogo; a leitura usa tinta escura sobre papel claro e uma faixa de seleção cor de ferrugem. As 34 prévias mantêm o conteúdo da avaliação de UX, sem aplicar mudanças à ROM.</p></header>
<div class="controls" role="group" aria-label="Tipo de tela">'''+buttons+'''</div><div class="controls"><label for="case">Exemplo</label><select id="case"></select></div>
<div class="comparison"><figure><figcaption>Proposta anterior · estrutura de UX</figcaption><img id="before" src="../interface-ux-v1/propostas/pause-5.png" alt="Proposta anterior do pause com fundo escuro"></figure><figure><figcaption>Proposta 02 · painel da resistência</figcaption><img id="after" src="propostas/pause-5.png" alt="Proposta do pause da fase 5"></figure></div><p id="note"></p><p><a id="rom-capture" href="../interface-ux-v1/atuais/ntsc/pause-5.png">Ver captura da ROM atual deste exemplo</a></p>
<div class="decision"><div class="card"><strong>1. Pause para consultar</strong><p>Objetivo, progresso e recursos. Continuar vem selecionado; o guia abre sem perder a partida. Confirmação só ao sair.</p></div><div class="card"><strong>2. Guia para aprender</strong><p>Controles → coletar → inventário → inimigos → sauvas → missões. Consulta opcional, com retorno à tela de origem.</p></div><div class="card"><strong>3. Missão para agir</strong><p>Nome do lugar, meta real, perigo e dica de rota. O diálogo conta a história; a preparação explica a tarefa.</p></div></div>
<h2>O que precisa melhorar</h2><p>Avaliação heurística: as prioridades abaixo são hipóteses de design apoiadas no comportamento observado, sem teste com jogadores.</p><div class="tablewrap"><table><thead><tr><th>Prioridade</th><th>Tela</th><th>Problema e evidência</th><th>Proposta</th></tr></thead><tbody>'''+rows+'''</tbody></table></div>
<details><summary>Textos propostos para todas as 20 localidades</summary><p>São 16 etapas por partida. A/B indicam lugares alternativos da mesma etapa. Meta e valores vêm da fase atual; nada aqui adiciona resgate, exploração ou colocação de cargas como ações jogáveis.</p><div class="tablewrap"><table><thead><tr><th>Fase</th><th>Lugar</th><th>Objetivo</th><th>Atenção / rota</th></tr></thead><tbody>'''+stages+'''</tbody></table></div></details>
<details><summary>Limitações e plano de implementação</summary><ul>'''+tech+'''</ul><p>Direção visual: um painel de campo improvisado da resistência, com papel técnico gasto e ferragens. A arte é uma nova base ilustrada; texto, seleção e ícones são compostos separadamente para preservar nitidez. Primeiro aprovar a direção; depois exportar os recursos e adaptar pause/guia. Fonte, tiles e cores precisam passar pela exportação e pela validação da ROM após aprovação. O fundo nativo usa um único banco de 15 cores; a arte ainda não foi carregada na VRAM do jogo.</p></details>
<footer><a href="avaliacao.json">Avaliação e textos completos</a> · <a href="validacao-layout.json">Conferência de espaço</a> · <a href="../interface-ux-v1/atuais/ntsc/report.json">Registro das capturas atuais</a><p>Comparação visual; os valores de progresso no novo pause são ilustrativos. A ROM permaneceu igual: <code>'''+audit['romSHA256']+'''</code>. Sem teste em CRT ou hardware físico.</p></footer></main>
<script>const cases='''+json.dumps(cases,ensure_ascii=False)+''';const selector=document.getElementById('case');function show(){const c=cases[+selector.value];for(const id of ['before','after']){const image=document.getElementById(id);image.src=c[id];image.alt=(id==='before'?'Proposta anterior: ':'Nova direção artística: ')+c.label;}document.getElementById('note').textContent=c.note;document.getElementById('rom-capture').href=c.rom;}function group(name){for(const b of document.querySelectorAll('[data-group]'))b.setAttribute('aria-pressed',String(b.dataset.group===name));selector.replaceChildren();for(let i=0;i<cases.length;i++)if(cases[i].group===name){const o=document.createElement('option');o.value=i;o.textContent=cases[i].label;selector.append(o);}if(name==='Pause')selector.value=cases.findIndex(c=>c.id==='pause-5');show();}for(const b of document.querySelectorAll('[data-group]'))b.addEventListener('click',()=>group(b.dataset.group));selector.addEventListener('change',show);group('Pause');</script></html>'''
destination='proposta-aprovada.html' if (ROOT/'integracao/build-validation.json').exists() else 'revisao.html'
(ROOT/destination).write_text(page)
print(json.dumps(dict(proposalOnly=True,cases=len(cases),textLines=len(checks),maxCharacters=max(c['length'] for c in checks),phaseCards=len(phases))))
