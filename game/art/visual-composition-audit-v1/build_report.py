"""Publish manual design findings alongside reproducible visual evidence."""
from pathlib import Path
from collections import Counter
import json,html,hashlib
A=Path(__file__).resolve().parent;G=A.parents[1]
evidence=json.loads((A/'evidence.json').read_text())
F={}
def row(p,status,priority,good,problems,fix,accept):F[p]=dict(status=status,priority=priority,strength=good,findings=problems,correction=fix,acceptance=accept)
row('1','ressalvas','P2','Igreja, muro e portão estabelecem o lugar; o espaço aberto atende à fase introdutória.',[
'O enquadramento inicial mostra apenas parte da igreja; ao descer, a arquitetura desaparece e resta quase só o piso.',
'A textura do chão se repete e há pouca indicação visual do trajeto de evacuação.'],
'Preservar o cenário aprovado. Revisar o enquadramento inicial e tornar a saída dos civis um ponto de atenção no perímetro, mantendo o centro livre.',
'No início, reconhecer igreja e portão; no combate, localizar o herói sem acrescentar decoração ao espaço de esquiva.')
row('2A','ressalvas','P2','A continuidade com o pátio da primeira fase é clara.',[
'A reutilização praticamente integral comunica pouco a mudança de situação.',
'Quando a câmera se afasta da borda norte, a preservação da igreja deixa de ser visível.'],
'Manter arte aprovada; reforçar a apresentação da igreja intacta e a leitura do novo inimigo por silhueta e sinal de ataque.',
'A igreja preservada deve ser reconhecida na apresentação da fase; o atirador deve se diferenciar durante a ação.')
row('2B','ressalvas','P2','Ruína e entulho diferenciam a consequência da bomba.',[
'Entulhos compartilham cores do chão, reduzindo a leitura dos volumes que bloqueiam os pés.',
'A destruição fica no topo e pode sair do enquadramento durante o combate.',
'A ruína é parcial: grande parte do telhado permanece inteira. A intensidade da consequência precisa corresponder à apresentação narrativa.'],
'Preservar a composição aprovada; reforçar contorno/sombra dos sólidos e apresentar a ruína antes da luta.',
'As pilhas sólidas devem ser distinguíveis das manchas decorativas, sem aumentar o ruído do piso.')
row('3','reprovada','P0','A igreja reaproveita a referência original e há quatro desvios principais.',[
'A faixa atrás dos telhados repete uma textura de chão em verde/laranja; parece terreno subindo e não um fundo distante.',
'Casas idênticas, igreja mais detalhada e veículos reduzidos com pouca definição quebram a consistência de escala e pixels.',
'Chão quase uniforme e repetição das fachadas deixam trechos visualmente vazios; o caminho testado tem um trecho final reto de cerca de700px.'],
'Recompor o quarteirão com fundo menos contrastado, muros/quintais/vegetação localizada e três ou quatro fachadas coerentes. Redesenhar a silhueta das barricadas e destacar o galpão na chegada.',
'Em entrada, meio e chegada, fundo separado do caminho, obstáculos reconhecíveis e um marco urbano identificável; a igreja mantém a referência.')
row('4','reprovada','P1','Paredes, prateleiras e portão estabelecem um interior de galpão no mapa completo.',[
'No enquadramento inicial, janelas e parte importante da parede ficam cortadas; ao mover, a fase volta a parecer um piso com caixas.',
'Grande área ocre quase lisa, caixas muito detalhadas e carrinho pouco definido não têm a mesma densidade visual.',
'As bordas dos recortes das caixas/carrinho deixam manchas de material diferentes do piso simplificado.'],
'Recompor o piso e a integração dos objetos a partir de uma única linguagem de materiais. Enquadrar o portão e usar pilares/racks do perímetro como contexto visível.',
'Reconhecer o galpão em todos os três enquadramentos sem depender de uma caixa isolada; nenhum retângulo ou halo de piso recortado ao redor dos objetos.')
row('5','ressalvas','P2','A Santa e o círculo de proteção criam o foco mais claro entre as missões de defesa.',[
'Piso texturado e várias setas competem entre si; a fachada do galpão aparece pouco nos enquadramentos inferiores.',
'O destaque amarelo do objetivo é eficaz, mas parte da sinalização é redundante.'],
'Preservar o cenário aprovado e o foco na Santa; reduzir sinalização redundante e manter uma vista de contexto do galpão na apresentação.',
'A Santa permanece localizável com combate ativo, sem confundir os marcadores com projéteis ou inimigos.')
row('6A','ajustes','P1','Arcos, canais e tubulações formam um esgoto reconhecível; a paleta não apresenta os buracos pretos do diagnóstico anterior.',[
'O piso apresenta uma grade muito repetida e forte; detalhes da parede competem com os personagens escuros.',
'As baias se repetem por grande parte do percurso, com poucos marcos para indicar avanço.'],
'Acalmar o piso, reduzir contraste dos detalhes de fundo e criar setores reconhecíveis de drenagem/inspeção. Melhorar separação entre Dinorah e a parede.',
'Herói e Dinorah distinguíveis sem depender apenas da barra amarela; entrada, meio e saída reconhecíveis pelo cenário.')
row('6B','reprovada','P0','A arquitetura de esgoto e a sequência de passagem estão presentes.',[
'O piso arroxeado e o padrão diagonal não mantêm a família de materiais da6A.',
'Nos quadros dos portões fechados, a barreira se lê como postes/linhas muito finas; a válvula depende do número/marcador para ser reconhecida.',
'A relação entre portão, parede, tubulação e área de operação não fica evidente no espaço.'],
'Unificar os materiais com6A. Compor cada portão como uma abertura arquitetônica completa e conectar visualmente a válvula à tubulação; distinguir fechado, liberado e destruído.',
'Com HUD e números ocultos, identificar o portão fechado, a válvula e a passagem liberada nos quadros de interação.')
row('7','ajustes','P1','Casas, escadas e barricadas definem uma área residencial com rotas de transporte.',[
'O piso tem manchas pequenas repetidas, e as portas azuis/laranjas do fundo atraem mais atenção que as cargas.',
'As cargas amarelo-marrons e o depósito marcado apenas comD têm pouca identidade própria em meio aos insetos.'],
'Reduzir o ruído do solo e fortalecer silhueta de caixa/suprimento. Dar ao depósito uma estrutura reconhecível e um ponto de entrega coerente com o abrigo.',
'Distinguir carga, item carregado e depósito sem leitura das letras; manter livre a leitura das rotas entre barricadas.')
row('8','reprovada','P0','Reutilizar a favela mantém a continuidade narrativa da base comprometida.',[
'Os alvos prioritários e os insetos comuns compartilham tons e formas, e o piso texturado reduz sua separação.',
'A composição não destaca visualmente os emissores como origem do enxame; o objetivo depende demais do HUD.'],
'Dar aos alvos prioritários silhueta e sinal de emissão próprios, com apoio visual no cenário. Acalmar o solo e reduzir a competição das fachadas.',
'Em uma captura de combate sem textos, apontar os alvos prioritários e diferenciá-los dos insetos comuns.')
row('9','reprovada','P1','Pista, fachadas industriais e pórtico final identificam o destino fabril.',[
'Entrada e meio têm a mesma fachada e a mesma seção de pista, com pouca mudança de composição.',
'A geometria atual registra street_solids=[]: a faixa caminhável é um corredor livre, apesar do contexto de abrir caminho.',
'A passagem ao azul da pista é brusca em relação à rua anterior; falta uma transição de materiais contextualizada.'],
'Dividir a aproximação em setores industriais reconhecíveis e compor obstáculos funcionais ligados ao cenário. Antecipar o pórtico da fábrica como marco de chegada e justificar os materiais da pista.',
'Entrada, meio e chegada diferentes à primeira vista; obstáculos visíveis correspondem ao percurso; o pórtico é reconhecido antes da saída.')
row('10','ajustes','P1','Piso relativamente calmo, caldeiras e esteiras dão uma base industrial legível.',[
'Ovos/ninhos e insetos se concentram em amarelo/marrom, dificultando a leitura rápida entre alvo estático e inimigo móvel.',
'A arquitetura se concentra na borda superior e repete o mesmo módulo; no miolo do mapa, as esteiras sustentam quase todo o contexto.'],
'Fortalecer a silhueta de ovos agrupados e seu contato com o piso. Variar os setores fabris sem aumentar a textura no espaço de tiro.',
'Identificar os ninhos em uma captura movimentada sem setas; reconhecer que o combate ocorre em uma fábrica ao afastar a câmera do topo.')
row('11','reprovada','P0','A mesma fábrica mantém a continuidade depois da destruição dos ninhos.',[
'As válvulas aparecem como pequenos objetos marrons no piso, separados da tubulação e difíceis de reconhecer.',
'A mudança de fábrica desligada para funcionamento não tem uma hierarquia visual forte nos quadros de ação examinados.'],
'Integrar válvulas e painéis à instalação fabril, preservando a área de interação. Diferenciar cada estado por forma, posição e sinal de funcionamento.',
'Reconhecer válvula e equipamento associado sem número; indicar visualmente o que passou a funcionar após cada interação.')
row('12','ajustes','P1','Oficinas e portas iluminadas definem um acesso industrial ao estaleiro.',[
'O piso repete um motivo diagonal alaranjado que parece um carimbo e pode ser confundido com pequenos objetos.',
'No mapa completo, faixas azuis e avermelhadas atrás das oficinas não formam um fundo espacial convincente.',
'Contraste e detalhes nas fachadas competem com a escolta; muitas baias têm a mesma aparência.',
'A chegada ao sindicato pouco se diferencia dos outros acessos industriais.'],
'Remover o motivo repetitivo do piso, controlar o contraste de fundo e organizar marcos de progressão. Dar ao sindicato uma fachada e entrada próprias.',
'Dinorah e caminho devem ser lidos antes das texturas; o sindicato deve ser reconhecível antes do marcador de chegada.')
row('13A','ressalvas','P2','O piso limpo, bancos e guichê permitem ler a sala e o espaço de combate.',[
'A grade grande do piso domina parte da composição e a paleta tende ao oliva acinzentado.',
'Dinorah no guichê e o símbolo sindical ficam próximos à borda superior, com pouca presença em parte dos enquadramentos.'],
'Preservar a organização da sala; suavizar as juntas do piso e apresentar o guichê e a identidade sindical com enquadramento mais favorável.',
'A sala continua legível em combate; reconhecer Dinorah no guichê e o caráter de sala dos trabalhadores na apresentação.')
row('13B','ajustes','P1','Manter a mesma sala é coerente com o local da variante13A.',[
'O memorial é pequeno e discreto no topo; nos quadros de movimento, a diferença visual mais evidente acaba sendo o contador45.',
'Os problemas de grade dominante e enquadramento superior da13A permanecem.'],
'Dar presença legível ao memorial no guichê, mantendo a sala compartilhada. Rever a apresentação da perda e suavizar as juntas do piso.',
'Ausência de Dinorah e presença do memorial devem ser perceptíveis sem depender de ler30/45 no HUD; preservar a continuidade do lugar.')
row('14','reprovada','P0','O perímetro industrial e as faixas no chão definem a área de operações.',[
'Os geradores se apresentam como pequenos volumes amarelo-marrons semelhantes aos insetos, em vez de máquinas reconhecíveis.',
'O padrão diagonal do piso é repetitivo e se mistura com pequenos projéteis/objetos.',
'As máquinas não formam um circuito visual evidente com o estaleiro.'],
'Redesenhar silhuetas de geradores/painéis e suas conexões. Limpar a textura do piso e criar hierarquia entre máquina, energia e arquitetura do perímetro.',
'Localizar as cinco máquinas e distinguir desligada/ligada sem texto, número ou confusão com insetos.')
row('15','reprovada','P0','O estado em chamas produz uma diferença de cor no perímetro.',[
'O rádio é pequeno e depende da letraR para ser identificado; falta um foco de defesa tão claro quanto a Santa na fase5.',
'A ignição se concentra nas bordas; o enquadramento mostra pouco dos motores que explicam o incêndio.',
'O piso repetitivo compete com a leitura dos objetos pequenos durante a defesa.'],
'Compor uma estação de rádio reconhecível, apoiada em um espaço de defesa legível. Enquadrar os motores na apresentação da ignição e reduzir o ruído do solo.',
'Sem HUD/letraR, identificar o objeto a proteger; na ignição, relacionar o fogo aos motores sem esconder os projéteis.')
row('16','ressalvas','P2','O Escorpião tem tamanho e silhueta distintos, com separação razoável do piso cinza.',[
'O motivo diagonal do piso permanece muito visível e o pedestal central pode competir com a leitura da área de esquiva.',
'Os motores ficam parcialmente fora do enquadramento, enfraquecendo a origem visual do chefe no fogo.'],
'Preservar o espaço aberto e a silhueta do chefe. Acalmar o chão e mostrar a relação entre motores, fogo e entrada do Escorpião na apresentação.',
'Distinguir chefe, projéteis e área segura em movimento; origem no fogo entendida na apresentação sem prejudicar a luta.')
labels={'ressalvas':'Aceitável com ressalvas','ajustes':'Precisa de ajustes','reprovada':'Reprovada nesta revisão'}
rows=[]
for s in evidence['variants']:
 d={**s,**F[s['phase']]};d['status_label']=labels[d['status']]
 for key in ('strength','correction','acceptance'):
  for a,b in [('com6A','com 6A'),('letraR','letra R'),('fase5','fase 5'),('ler30/45','ler 30/45')]:d[key]=d[key].replace(a,b)
 d['findings']=[x.replace('de700px','de 700 px').replace('da6A','da 6A').replace('comD','com D').replace('variante13A','variante 13A').replace('da13A','da 13A').replace('contador45','contador 45').replace('letraR','letra R') for x in d['findings']]
 rows.append(d)
counts=Counter(r['status'] for r in rows)
report=dict(rom_sha256=evidence['rom_sha256'],scope='Todas as19variantes de campanha; inclui1,2A,2B e5 como referências preservadas.',review_type='Revisão manual de composição; evidências de playtests previamente gravados nestaROM. Os rótulos são julgamento de design, não resultados automáticos nem validação com jogadores externos.',criteria=['Cores e separação entre fundo, piso, personagens e objetivos','Profundidade e integração dos recortes','Escala, perspectiva e densidade de pixels','Repetição e marcos de orientação','Enquadramento inicial e durante movimentação','Legibilidade do objetivo de cada fase e de seus estados'],counts=dict(counts),evidence_frames=sum(len(r['frames']) for r in rows),runtime_or_art_changed=False,variants=rows)
(A/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# No generated art; the overview reproduces emulator screenshots for audit.
esc=html.escape
nav=''.join(f'<a class="{r["status"]}" href="#p{r["phase"]}">{r["phase"]}</a>' for r in rows)
table=''.join('<tr><td><a href="#p'+r['phase']+'">'+r['phase']+'</a></td><td>'+esc(r['status_label'])+'</td><td>'+r['priority']+'</td><td>'+esc(r['findings'][0])+'</td></tr>' for r in rows)
sections=[]
frame_labels={'ntsc-entry':'Entrada · NTSC','ntsc-middle':'Movimentação / meio · NTSC','ntsc-action':'Ação · NTSC','ntsc-end':'Chegada · NTSC','pal-entry':'Entrada · PAL'}
for r in rows:
 cards=''.join('<figure><a href="'+f['path']+'"><img loading="lazy" src="'+f['path']+'" alt="Fase '+r['phase']+' '+f['label']+'"></a><figcaption>'+esc(frame_labels.get(f['label'],'Estado especial · NTSC'))+(' · '+str(f['time_seconds'])+'s do vídeo' if 'time_seconds' in f else ' · captura do emulador')+'</figcaption></figure>' for f in r['frames'])
 sections.append('<section id="p'+r['phase']+'"><h2>Fase '+r['phase']+' · '+esc(r['name'])+'</h2><p class="badge '+r['status']+'">'+esc(r['status_label'])+' · '+r['priority']+'</p><p><b>Objetivo:</b> '+esc(r['goal'])+'</p><p><b>O que funciona:</b> '+esc(r['strength'])+'</p><ul>'+''.join('<li>'+esc(x)+'</li>' for x in r['findings'])+'</ul><p><b>Correção indicada:</b> '+esc(r['correction'])+'</p><p class="accept"><b>Critério de aceitação:</b> '+esc(r['acceptance'])+'</p><div class="frames">'+cards+'</div><details><summary>Mapa nativo completo · mantenha a proporção e role para explorar</summary><div class="map"><img loading="lazy" src="'+r['native']+'" alt="Mapa completo da fase '+r['phase']+'"></div></details><a href="#top">Voltar ao índice</a></section>')
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Plaguefall · Auditoria de composição visual</title><style>*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#111714;color:#e7e9df;font:16px/1.6 system-ui}main{max-width:1380px;margin:auto;padding:28px}h1{font-size:36px;line-height:1.15}p{max-width:1080px}a{color:#eac578}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}nav a,.badge{padding:5px 12px;border:1px solid #748471;border-radius:4px;text-decoration:none}.ressalvas{background:#263f34}.ajustes{background:#4c4226}.reprovada{background:#542d2b}.metrics{display:flex;gap:12px;flex-wrap:wrap}.metrics p{padding:14px 22px;border-radius:6px;margin:4px 0}.note,.accept{border-left:4px solid #c9a259;background:#202b24;padding:12px 18px}table{width:100%;border-collapse:collapse}td,th{padding:10px;text-align:left;border-bottom:1px solid #3d4c40;vertical-align:top}td:first-child{white-space:nowrap}section{border-top:1px solid #71806a;padding-top:18px;margin-top:42px;scroll-margin-top:10px}section h2{margin-bottom:8px}.badge{display:inline-block}.frames{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}figure{margin:0}figure img{width:100%;image-rendering:pixelated}figcaption{font-size:12px;color:#b5c2b2}.map{overflow:auto;background:#080e0b;padding:8px}.map img{display:block;image-rendering:pixelated;max-width:none;width:auto}summary{cursor:pointer;color:#eac578;padding:10px 0}.small{font-size:12px;color:#a4b5a2;overflow-wrap:anywhere}.scroll{overflow:auto}@media(max-width:850px){.frames{grid-template-columns:repeat(2,minmax(0,1fr))}main{padding:16px}h1{font-size:27px}}</style><main id="top"><p class="note"><b>Auditoria histórica da versão anterior.</b> As correções posteriores, comparações e novos playtests estão na <a href="../visual-composition-fixes-v1/review.html">revisão das fases corrigidas</a>.</p><h1>Teste de composição visual · Todas as fases</h1><p>19 variações examinadas a partir dos mapas nativos completos e das capturas reais de entrada, movimento e ação. Inclui comparação de entrada em PAL, igreja destruída, portões e ignição. As referências 1, 2A/2B e5 permanecem preservadas.</p><div class="metrics"><p class="ressalvas"><b>6</b> aceitáveis com ressalvas</p><p class="ajustes"><b>5</b> precisam de ajustes</p><p class="reprovada"><b>8</b> reprovadas nesta revisão</p></div><p class="note">Aprovação técnica e aprovação visual são critérios separados. Os testes anteriores confirmam objetivos, colisões e gráficos na memória do console. Esta auditoria examina composição, legibilidade e coerência artística. Nenhuma fase recebe aprovação visual final automática por passar nos testes técnicos.</p><p>Foram inspecionados FRAMECOUNT quadros derivados dos playtests já gravados destaROM. Os pareceres abaixo são julgamentos manuais de design; não são notas produzidas por algoritmo nem resultados de um estudo com jogadores. AROM e os assets do jogo não foram alterados nesta revisão.</p><p><a href="report.json">Pareceres e prioridades em JSON</a> · <a href="evidence.json">Origem dos quadros e método</a> · <a href="../campaign-whole-scenes-v1/review.html">Fontes, recortes e revisão técnica</a></p><p><b>P0:</b> identificação do objetivo ou composição fundamental comprometida. <b>P1:</b> integração, repetição ou orientação que exige revisão. <b>P2:</b> polimento preservando a base.</p><nav>NAV</nav><div class="scroll"><table><thead><tr><th>Fase</th><th>Parecer</th><th>Prioridade</th><th>Principal observação</th></tr></thead><tbody>TABLE</tbody></table></div><p><b>Ordem recomendada:</b> 3 → 6B → 8 → 11 → 14 → 15; depois4/9 e os ajustes de6A/7/10/12/13B. Nas referências aprovadas, aplicar somente os ajustes de enquadramento e leitura registrados; preservar as composições existentes.</p>SECTIONS<p class="small">ROM examinada: SHA. Esta auditoria não recompila nem altera o jogo.</p></main></html>'''
page=page.replace('FRAMECOUNT',str(report['evidence_frames'])).replace('NAV',nav).replace('TABLE',table).replace('SECTIONS',''.join(sections)).replace('SHA',report['rom_sha256'])
# Editorial spacing in prose, preserving paths/identifiers.
for a,b in [('e5','e 5'),('destaROM','desta ROM'),('AROM','A ROM'),('cerca de700px','cerca de 700 px'),('da6A','da 6A'),('com6A','com 6A'),('comD','com D'),('da13A','da 13A'),('variante13A','variante 13A'),('contador45','contador 45'),('ler30/45','ler 30/45'),('letraR','letra R'),('fase5','fase 5'),('de6A/7/10/12/13B','de 6A/7/10/12/13B'),('depois4/9','depois 4/9')]:page=page.replace(a,b)
(A/'review.html').write_text(page)
assert hashlib.sha256((G/'out/release/Plaguefall.bin').read_bytes()).hexdigest()==evidence['rom_sha256']
print('Published manual audit:',dict(counts),'frames',report['evidence_frames'],'ROM unchanged')
