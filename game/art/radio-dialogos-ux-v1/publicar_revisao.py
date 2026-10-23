"""Publish screenshots from the exact distributed ROM, preserve approval."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil,subprocess,re
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parents[1];VALID=ROOT/'integracao/validation-frozen'
romDir=ROOT/'integracao/rom';rom=romDir/'Plaguefall.bin';digest=hashlib.sha256(rom.read_bytes()).hexdigest()
defs=(romDir/'tile-defs.h').read_text()
objects=int(re.search(r'^#define NUM_TILES\s+(\d+)',defs,re.M).group(1))
base=16+objects;iconBase=base+320;sceneBase=iconBase+240+72+48
reports={}
for name in ['ntsc','pal']+[p+'-'+r for p in ['interface','map','results','objective'] for r in ['ntsc','pal']]:
 r=json.loads((VALID/name/'report.json').read_text())
 assert r['passed'] and r.get('romSHA256',r.get('rom_sha256'))==digest,(name,r.get('passed'),r.get('romSHA256',r.get('rom_sha256')),digest)
 reports[name]=r
for original,frozen in [('revisao.html','proposta-aprovada.html'),('avaliacao.json','conteudo-aprovado.json')]:
 if not (ROOT/frozen).exists():shutil.copyfile(ROOT/original,ROOT/frozen)
if not (VALID/'build-before.json').exists():shutil.copyfile(GAME/'doc/build-validation.json',VALID/'build-before.json')
for name in ['native','npc','stage','package']:
 data=Path('/tmp/plaguefall-radio-final-'+name+'.log').read_text();assert 'Traceback' not in data and data.strip(),name
 (VALID/(name+'-checks.txt')).write_text(data)
shutil.copyfile('/tmp/plaguefall-radio-build.log',VALID/'build.log')
for region in ['ntsc','pal']:
 for p in (VALID/region).glob('FAIL*.png'):p.unlink()
files=['radio-padre','radio-damiao','radio-digitando','radio-6B-1','radio-final-2','contagem-1-3','contagem-1-2','contagem-1-1','contagem-vai-1','contagem-3-3','contagem-16-3']
proposal=json.loads((ROOT/'conteudo-aprovado.json').read_text())
cases=[]
for c,file in zip(proposal['cases'],files):
 for region in ['ntsc','pal']:assert (VALID/region/(file+'.png')).is_file(),file
 cases.append({'id':c['id'],'label':c['label'],'approved':c['after'],'file':file,'note':c['note']})
cases[0]['note']='Padre no canto inferior direito, olhando para dentro; Damião permanece no alto à esquerda. A fala recebida tem janela própria. Retratos, nomes e fonte preservam os pixels existentes.'
cases[1]['note']='Na resposta, a janela ativa acompanha Damião no alto. O interlocutor permanece embaixo, no mesmo lugar. A completa a mensagem; uma nova pressão avança ou abre a missão.'
cases[2]['note']='Texto em máquina de escrever, com clique discreto de rádio em intervalos. A mostra a fala completa; START pula a cena. A área de leitura permanece estável.'
cases[3]['note']='Dinorah ocupa a mesma âncora remota do padre, sem espelhamento e com a paleta original. Seu nome muda junto do retrato, sobre o cenário nativo da retirada por terra.'
cases[4]['note']='O diálogo final continua antes da vitória. O fundo é o covil vazio, renderizado sem iniciar uma fase, alterar a rota ou mover atores da simulação.'
for i in [5,6,7,9,10]:cases[i]['note']='Contagem com algarismo grande, marcadores e pulsos sonoros curtos: 3/2/1 por um segundo cada. Usa a paleta existente dos objetos para preservar as cores do cenário, do HUD e dos atores. O cartão não cobre Damião.'
cases[8]['note']='No zero, a caixa grande some e movimento/tiro já estão liberados. VAI! permanece por cerca de 350 ms sem prolongar a espera. Os tiles emprestados são restaurados antes da pausa ou transição.'
sheet=Image.new('RGB',(1280,768),(34,29,24));d=ImageDraw.Draw(sheet)
for i,c in enumerate(cases):
 x=i%4*320;y=i//4*256;d.text((x+8,y+5),c['id'],fill=(255,219,146));sheet.paste(Image.open(VALID/'ntsc'/(c['file']+'.png')),(x,y+24))
sheet.save(ROOT/'integracao/visao-geral.png')
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rádio e contagem integrados — Plaguefall</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#211d18;color:#f0ddb7}*{box-sizing:border-box}body{max-width:1280px;margin:auto;padding:26px}h1{font-size:30px;margin:7px 0 12px}.eyebrow{color:#c5b182;letter-spacing:.14em;font-size:12px}.badge{display:inline-block;border:1px solid #84916c;color:#d3ddae;padding:6px 9px;border-radius:5px;font-size:12px}p{line-height:1.5}.muted{color:#bfb49d;font-size:13px}.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:20px 0 14px}button,select{font:inherit;color:inherit;background:#3a3126;border:1px solid #9a7445;border-radius:5px;padding:10px;cursor:pointer}button:hover,button:focus-visible{background:#655038}button[aria-pressed=true]{background:#8d552f;color:#fff4db}select{max-width:100%}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;padding:12px;background:#30291f;border:1px solid #65553b;border-radius:8px}figure img{width:100%;aspect-ratio:320/224;image-rendering:pixelated;display:block}figcaption{font-size:13px;color:#ceba94;margin-bottom:9px}.note{background:#30352b;border-left:3px solid #a7a16f;padding:14px 18px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}.grid button{padding:6px;text-align:left}.grid img{display:block;width:100%;image-rendering:pixelated;margin-bottom:6px}.grid span{font-size:13px}.native figure img{width:320px;max-width:100%}details{padding:15px;background:#30291f;margin-top:22px}li{line-height:1.5;margin:12px 0}a{color:#f1c480}@media(max-width:760px){body{padding:16px}.compare{grid-template-columns:1fr}.compare figure:last-child{order:-1}.grid{grid-template-columns:repeat(2,1fr)}}
</style><div class="eyebrow">PLAGUEFALL · TRANSMISSÕES E ENTRADA EM COMBATE</div><h1>Rádio e contagem integrados</h1><span class="badge">ROM VALIDADA · 51 FALAS · 20 FASES · NTSC E PAL</span>
<p>Damião no alto à esquerda; interlocutores embaixo à direita, olhando para dentro. Diálogos com identidade de rádio; menus, missões e resultados mantêm o painel atual. A contagem libera o controle no zero.</p>
<div class="toolbar"><label for="case">Situação</label><select id="case"></select><button id="ntsc" aria-pressed="true">NTSC</button><button id="pal" aria-pressed="false">PAL</button><button id="native" aria-pressed="false">Ver em 1×</button></div>
<div class="compare"><figure><figcaption>DESENHO APROVADO</figcaption><img id="approved" alt="Desenho aprovado de rádio ou contagem"></figure><figure><figcaption id="captureLabel">JOGO · CAPTURA NTSC</figcaption><img id="actual" alt="Interface em execução na ROM validada"></figure></div><p id="note" class="note" aria-live="polite"></p><div id="cards" class="grid"></div>
<details><summary>Verificação na ROM e detalhes da integração</summary><ul><li>51 falas em cada região: todas as quebras e cada pixel de glifo conferidos; retratos dos quatro personagens comparados aos dados originais, com posições e paletas exatas, sem espelhamento. A simulação permanece congelada durante a conversa.</li><li>20 contagens por região, com três intervalos exatos de 60 quadros em NTSC ou 50 em PAL. O movimento responde no quadro do zero. VAI! dura 21 quadros em NTSC e 18 em PAL, sem bloquear o combate.</li><li>O rádio usa geometria própria, quatro paletas e um compositor com cache de tiles. A contagem usa 180 tiles temporários da reserva de ícones e a paleta existente dos objetos; restaura os gráficos ao terminar ou abrir a pausa. Menus e papel continuam no módulo anterior.</li><li>Regressões aprovadas nos dois sistemas: preparação/pause/guia e resultados nas 20 localidades, VRAM restaurada exatamente ao retomar, 23 conexões do mapa e duas campanhas completas, proteção do sinalizador, contatos e ensaios de carga da fase 5.</li><li>As capturas vêm do Genesis Plus GX com a ROM identificada abaixo. A RAM prepara fases e antecipa morte/objetivo/chefe para acessar as cenas; falas e contagens são executadas pelo código normal. Não representa batalhas vencidas naturalmente nem ensaio em hardware físico/CRT.</li></ul></details>
<p><a href="integracao/rom/Plaguefall.bin">Baixar ROM validada</a> · <a href="proposta-aprovada.html">Proposta aprovada</a> · <a href="integracao/build-validation.json">Relatório consolidado</a> · <a href="integracao/validation-frozen/ntsc/report.json">Rádio e contagem NTSC</a> · <a href="integracao/validation-frozen/pal/report.json">Rádio e contagem PAL</a></p><p class="muted">SHA-256: HASH</p>
<script>const cases=CASES;let region='ntsc',index=0;const select=document.querySelector('#case');for(const [i,c] of cases.entries()){select.add(new Option(c.label,i));const b=document.createElement('button');b.innerHTML=`<img src="integracao/validation-frozen/ntsc/${c.file}.png?v=SHORT" alt=""><span>${c.label}</span>`;b.onclick=()=>show(i);document.querySelector('#cards').append(b)}function show(i){index=i;select.value=i;const c=cases[i];document.querySelector('#approved').src=c.approved;document.querySelector('#actual').src=`integracao/validation-frozen/${region}/${c.file}.png?v=SHORT`;document.querySelector('#captureLabel').textContent='JOGO · CAPTURA '+region.toUpperCase();document.querySelector('#note').textContent=c.note;document.querySelectorAll('#cards button').forEach((b,j)=>b.setAttribute('aria-pressed',i===j))}select.onchange=()=>show(+select.value);for(const r of ['ntsc','pal'])document.querySelector('#'+r).onclick=()=>{region=r;for(const k of ['ntsc','pal'])document.querySelector('#'+k).setAttribute('aria-pressed',k===r);show(index)};document.querySelector('#native').onclick=e=>{const on=document.body.classList.toggle('native');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Ampliar':'Ver em 1×'};show(0)</script></html>'''
(ROOT/'revisao.html').write_text(page.replace('HASH',digest).replace('SHORT',digest[:12]).replace('CASES',json.dumps(cases,ensure_ascii=False)))
report=json.loads((GAME/'doc/build-validation.json').read_text())
size=subprocess.check_output(['/opt/homebrew/bin/m68k-elf-size',str(romDir/'rom.out')],text=True).splitlines()[1].split()
report.update(revision='Two-anchor radio dialogue, 51 native lines, sprite countdown and zero-frame input release; existing menu/result panels preserved',rom_sha256=digest,rom_bytes=rom.stat().st_size,text_bytes=int(size[0]),data_bytes=int(size[1]),bss_bytes=int(size[2]),static_ram_bytes=int(size[1])+int(size[2]),previous_validation='../art/radio-dialogos-ux-v1/integracao/validation-frozen/build-before.json')
for region in ['ntsc','pal']:
 report['checks']['radio_'+region]={'passed':True,'report':f'../art/radio-dialogos-ux-v1/integracao/validation-frozen/{region}/report.json','dialogueLines':51,'countdownStages':20,'glyphsAndPortraitsExact':True,'threeSecondsExact':True,'movesAtZero':True,'graphicsRestored':True}
 for kind in ['interface','routemap','results']:
  dirname=('map' if kind=='routemap' else kind)+'-'+region
  report['checks'][kind+'_'+region]['report']=f'../art/radio-dialogos-ux-v1/integracao/validation-frozen/{dirname}/report.json'
 report['checks']['objective_'+region]={'passed':True,'report':f'../art/radio-dialogos-ux-v1/integracao/validation-frozen/objective-{region}/report.json','ordinaryMatches':3,'isolatedContactAndFeedback':True}
report['native_audio_player_resources']='../art/radio-dialogos-ux-v1/integracao/validation-frozen/native-checks.txt'
report['map_limits'].update(art_base=base,pin_base=base+800+192)
report['interface_limits'].update(artBase=base,scratchBase=base+545,lastBorrowedTile=base+545+112-1)
report['result_limits'].update(maxBackgroundTilesObserved=max(reports['results-'+r]['maxBackgroundTiles'] for r in ['ntsc','pal']),lastTileObserved=max(reports['results-'+r]['lastTileObserved'] for r in ['ntsc','pal']))
report['radio_limits']={'staticGeometryTiles':97,'portraits':2,'portraitTiles':72,'dynamicTileBudget':400,'maxDynamicTilesObserved':max(reports[r]['maxDynamicTiles'] for r in ['ntsc','pal']),'dynamicPixelBufferBytes':12800,'mapBufferBytes':2240,'lastReservedTile':587,'sceneryStartsAt':sceneBase,'palettes':{'ui':0,'damiao':1,'remote':2,'scene':3},'legacyDecor':'opaque wall/lava/mud colours remapped into the UI palette; floor stays in PAL3','wrapCharacters':26,'wrapLines':4,'lineSpacingPixels':16,'samePhaseSimulationReset':False}
report['countdown_limits']={'borrowedTiles':180,'borrowedBase':iconBase,'snapshotBytes':5760,'countdownSprites':15,'goSprites':3,'palette':'existing PAL1 object palette, unchanged','freezeSeconds':3,'goFrames':{'NTSC':21,'PAL':18},'controlsReleasedAtZero':True,'restoreOnPauseAndTransition':True}
report['rom']='../art/radio-dialogos-ux-v1/integracao/rom/Plaguefall.bin'
report['named_rom']=report['rom'];report['immutable_delivery_snapshot']=True
report['workspace_rom_sha256_at_publication']=hashlib.sha256((GAME/'out/release/Plaguefall.bin').read_bytes()).hexdigest()
(ROOT/'integracao/build-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'romSHA256':digest,'reports':len(reports),'gallery':'revisao.html'},indent=2))
