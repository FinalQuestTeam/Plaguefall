"""Publish emulator evidence next to the frozen approved proposal."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parents[1]
VALID=ROOT/'integracao/validation'
rom=GAME/'out/release/Plaguefall.bin';digest=hashlib.sha256(rom.read_bytes()).hexdigest()
reports={}
for name in ('ntsc','pal','interface-ntsc','interface-pal','map-ntsc','map-pal'):
 report=json.loads((VALID/name/'report.json').read_text())
 assert report['passed'] and report['romSHA256']==digest,(name,report.get('passed'),report.get('romSHA256'),digest)
 reports[name]=report
if not (ROOT/'proposta-aprovada.html').exists():shutil.copyfile(ROOT/'revisao.html',ROOT/'proposta-aprovada.html')
if not (ROOT/'conteudo-aprovado.json').exists():shutil.copyfile(ROOT/'avaliacao.json',ROOT/'conteudo-aprovado.json')
if not (VALID/'build-before.json').exists():shutil.copyfile(GAME/'doc/build-validation.json',VALID/'build-before.json')
shutil.copyfile('/tmp/plaguefall-check-results.log',VALID/'native-checks.txt')
shutil.copyfile('/tmp/plaguefall-result-build.log',VALID/'build.log')
for region in ('ntsc','pal'):
 for bad in (VALID/region).glob('FAIL*.png'):bad.unlink()
cases=[
 {'id':'derrota','label':'Derrota / tentar novamente','file':'derrota-3','note':'Mesma fase como ponto de retorno. Vida cheia, equipamento básico, itens e melhorias reiniciados. START tenta novamente; A confirma a opção; B devolve o foco à primeira opção.'},
 {'id':'derrota-sair','label':'Derrota / selecionar saída','file':'derrota-sair','note':'Selecionar voltar ao título abre a confirmação. A campanha só é abandonada após escolher a saída na segunda caixa.'},
 {'id':'confirmar-saida','label':'Confirmação / preservar a partida','file':'confirmar-saida','note':'Caixa menor de 256 × 152 px, com opção inicial segura. A volta à derrota; B/START cancelam. A segunda opção permite sair ao título.'},
 {'id':'fase-concluida','label':'Fase concluída / caminho aberto','file':'fase-concluida','note':'Cartão de 256 × 128 px sobre o cenário. Avança automaticamente em 2 s ou com uma nova pressão de A/START após 350 ms; segurar o tiro não o descarta.'},
 {'id':'sinal-protegido','label':'Proteção / resgate confirmado','file':'sinal-protegido','note':'O objetivo nomeia o sinalizador protegido. O resgate confirmado mantém o caminho 6A e os diálogos/mapa existentes.'},
 {'id':'sinal-perdido','label':'Sinal perdido / retirada por terra','file':'sinal-perdido','note':'A missão continua pela rota 6B. O cartão informa a consequência durante 3 s, com atalho A/START e alerta sonoro diferente da derrota.'},
 {'id':'vitoria','label':'Vitória final / encerramento','file':'vitoria-final','note':'Caixa central de 256 × 176 px sobre o covil vazio. Surge após o diálogo final, mantém Entardecer e aguarda a escolha. A/START confirmam; B não abandona a tela.'},
 {'id':'vitoria-rejogar','label':'Vitória final / nova campanha','file':'vitoria-rejogar','note':'Jogar novamente inicia na fase 1 com vida, inventário, melhorias, rotas, estatísticas e cenas reiniciados. O diálogo inicial volta a aparecer.'}
]
for c in cases:
 for region in ('ntsc','pal'):assert (VALID/region/(c['file']+'.png')).is_file()
sheet=Image.new('RGB',(1280,560),(34,29,24));d=ImageDraw.Draw(sheet)
for i,c in enumerate(cases):
 x=(i%4)*320;y=(i//4)*280
 sheet.paste(Image.open(VALID/'ntsc'/(c['file']+'.png')),(x,y+24));d.text((x+8,y+7),c['id'],fill=(255,219,146))
sheet.save(ROOT/'integracao/visao-geral.png')
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resultados integrados — Plaguefall</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#211d18;color:#f0ddb7}*{box-sizing:border-box}body{max-width:1280px;margin:auto;padding:28px}h1{font-size:30px;margin:7px 0 12px}.eyebrow{color:#d7ac68;letter-spacing:.14em;font-size:12px}p{line-height:1.5}.muted{color:#bcae95;font-size:13px}.badge{border:1px solid #8b9760;padding:6px 10px;display:inline-block;border-radius:5px;font-size:12px;color:#dce3b8}.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:20px 0 14px}select,button{font:inherit;color:inherit;background:#3a3126;border:1px solid #9a7445;border-radius:5px;padding:10px;cursor:pointer}button:hover,button:focus-visible{background:#655038}button[aria-pressed=true]{background:#9e582b;color:#fff4db}select{max-width:100%}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px}.frame{margin:0;padding:13px;background:#30291f;border:1px solid #65553b;border-radius:8px}.frame img{display:block;width:100%;aspect-ratio:320/224;image-rendering:pixelated;background:#000}.frame figcaption{font-size:13px;color:#ceba94;margin-bottom:10px}.note{padding:15px 18px;background:#383322;border-left:3px solid #b48c4b}.casegrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}.casegrid button{text-align:left;padding:6px}.casegrid img{width:100%;image-rendering:pixelated;display:block;margin-bottom:7px}.casegrid span{font-size:13px}.native .frame img{width:320px;max-width:100%}a{color:#f1c480}details{padding:15px;background:#30291f}li{line-height:1.5;margin:10px 0}@media(max-width:760px){body{padding:16px}.compare{grid-template-columns:1fr}.casegrid{grid-template-columns:repeat(2,1fr)}}
</style><div class="eyebrow">PLAGUEFALL · PAINEL DA RESISTÊNCIA</div><h1>Resultados integrados ao jogo</h1><span class="badge">ROM ATUAL · NTSC E PAL VERIFICADOS</span>
<p>Texto centralizado, caixas de 256 px de largura e cenário visível ao redor. Compare o desenho aprovado com a captura real da ROM.</p>
<div class="toolbar"><label for="case">Situação</label><select id="case"></select><button id="ntsc" aria-pressed="true">NTSC</button><button id="pal" aria-pressed="false">PAL</button><button id="native" aria-pressed="false">Ver em 1×</button></div>
<div class="compare"><figure class="frame"><figcaption>DESENHO APROVADO</figcaption><img id="approved" alt="Desenho aprovado da caixa de resultado"></figure><figure class="frame"><figcaption id="captureLabel">JOGO · CAPTURA NTSC</figcaption><img id="actual" alt="Caixa de resultado em execução na ROM atual"></figure></div><p id="note" class="note" aria-live="polite"></p><div id="cards" class="casegrid"></div>
<details><summary>Verificação na ROM e limites da captura</summary><ul><li>Derrota, repetição da fase e pausa após repetir: 20 localidades em NTSC e PAL. Confirmados vida cheia, reinício dos equipamentos, caixa congelada e preservação dos padrões do cenário.</li><li>Confirmados saída/cancelamento, proteção e perda do sinal com rotas 6A/6B, avanço automático e por botão, prioridade da derrota e proteção contra o tiro mantido.</li><li>Confirmados diálogo final, vitória sem avanço automático, retorno ao título, nova campanha com cenas e rotas reiniciadas e repetição no treino.</li><li>Regressão em cada sistema: preparação/pause/guia nas 20 localidades, restauração exata da VRAM ao retomar, 23 conexões do mapa e duas campanhas completas. Recursos, música e testes nativos aprovados.</li><li>A RAM prepara as situações, estabiliza o brilho para comparação e antecipa morte/contadores/chefe. A entrada, desenho, navegação e transições são do código de produção. As capturas não representam batalhas vencidas naturalmente. Testado em Genesis Plus GX; sem ensaio físico ou CRT.</li></ul></details>
<p><a href="../../out/release/Plaguefall.bin">Baixar ROM atual</a> · <a href="proposta-aprovada.html">Proposta aprovada</a> · <a href="integracao/build-validation.json">Relatório consolidado</a> · <a href="integracao/validation/ntsc/report.json">Resultados NTSC</a> · <a href="integracao/validation/pal/report.json">Resultados PAL</a></p><p class="muted">ROM SHA-256: HASH</p>
<script>const cases=CASES;let region='ntsc',index=6;const select=document.querySelector('#case');for(const [i,c] of cases.entries()){select.add(new Option(c.label,i));const b=document.createElement('button');b.innerHTML=`<img src="integracao/validation/ntsc/${c.file}.png?rom=SHORT" alt=""><span>${c.label}</span>`;b.onclick=()=>show(i);document.querySelector('#cards').append(b)}function show(i){index=i;select.value=i;const c=cases[i];document.querySelector('#approved').src=`propostas/${c.id}.png`;document.querySelector('#actual').src=`integracao/validation/${region}/${c.file}.png?rom=SHORT`;document.querySelector('#captureLabel').textContent='JOGO · CAPTURA '+region.toUpperCase();document.querySelector('#note').textContent=c.note;document.querySelectorAll('#cards button').forEach((b,j)=>b.setAttribute('aria-pressed',j===i))}select.onchange=()=>show(+select.value);for(const r of ['ntsc','pal'])document.querySelector('#'+r).onclick=()=>{region=r;for(const k of ['ntsc','pal'])document.querySelector('#'+k).setAttribute('aria-pressed',k===r);show(index)};document.querySelector('#native').onclick=e=>{const on=document.body.classList.toggle('native');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Ampliar':'Ver em 1×'};show(index)</script></html>'''
page=page.replace('HASH',digest).replace('SHORT',digest[:12]).replace('CASES',json.dumps(cases,ensure_ascii=False))
(ROOT/'revisao.html').write_text(page)
old=json.loads((GAME/'doc/build-validation.json').read_text())
size=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-size',str(GAME/'out/release/rom.out')],text=True).splitlines()[1].split()
old.update(revision='Centred partial resistance result cards: defeat/retry, safe exit, objective completion, signal branches, final victory and new campaign',rom_sha256=digest,rom_bytes=rom.stat().st_size,text_bytes=int(size[0]),data_bytes=int(size[1]),bss_bytes=int(size[2]),static_ram_bytes=int(size[1])+int(size[2]),previous_validation='../art/resultados-ux-v1/integracao/validation/build-before.json')
for region in ('ntsc','pal'):
 old['checks']['results_'+region]={'passed':True,'report':f'../art/resultados-ux-v1/integracao/validation/{region}/report.json','localities':20,'samePhaseRetry':True,'equipmentReset':True,'routes':['6A','6B'],'replayFullReset':True,'sandboxRetry':True}
 old['checks']['interface_'+region]['report']=f'../art/resultados-ux-v1/integracao/validation/interface-{region}/report.json'
 old['checks']['routemap_'+region]['report']=f'../art/resultados-ux-v1/integracao/validation/map-{region}/report.json'
old['native_audio_player_resources']='../art/resultados-ux-v1/integracao/validation/native-checks.txt'
old['result_limits']={'width':256,'heights':{'defeat':184,'exit':152,'completion':128,'victory':176},'alignment':'exact pixel centre; original 8x8 glyphs','fontMaskBytes':768,'palette':'PAL2; actors hidden; original scenery PAL0/1/3 retained','backgroundTileCap':680,'maxBackgroundTilesObserved':max(reports[r]['maxBackgroundTiles'] for r in ('ntsc','pal')),'cardTilesMax':736,'lastTileLimit':1431,'lastTileObserved':max(reports[r]['lastTileObserved'] for r in ('ntsc','pal')),'temporaryCaptureBytesMax':34048,'cardBufferBytes':23552,'memoryLifetime':'capture buffers freed before card allocation; card freed on exit; object/floor patterns and actor cache rebuilt','transientBloodDecals':'hidden with actors in mapped arenas','inputGateMilliseconds':350,'automaticSeconds':{'completion':2,'signalLost':3,'defeat':None,'final':None}}
for dest in (GAME/'doc/build-validation.json',ROOT/'integracao/build-validation.json'):dest.write_text(json.dumps(old,indent=2)+'\n')
print(json.dumps({'passed':True,'romSHA256':digest,'reports':len(reports),'gallery':'revisao.html'},indent=2))
