"""Publish modular phase14 assets and the matching production-ROM evidence."""
from pathlib import Path
import hashlib, html, json
A=Path(__file__).resolve().parent
G=A.parents[1]
manifest=json.loads((A/'manifest.json').read_text())
rom=G/'out/release/Plaguefall.bin'
digest=hashlib.sha256(rom.read_bytes()).hexdigest()
regions={k:json.loads((A/f'validation/{k}/report.json').read_text()) for k in ['ntsc','pal']}
assert all(r['passed'] and r['romSHA256']==digest for r in regions.values())
delivery=dict(rom=str(rom.relative_to(G)),rom_sha256=digest,rom_bytes=rom.stat().st_size,size=manifest['size'],memory=manifest['memory'],energy=manifest['energy'],generator=manifest['generator'],activation=manifest['activation'],floor=manifest['floor'],regions={})
for name,r in regions.items():
    delivery['regions'][name]=dict(passed=True,report=f'validation/{name}/report.json',load=r['checks']['moving-four-enemy-four-plus-four-shot-load'],camera_views=len(r['checks']['28-real-camera-views']))
    delivery['regions'][name]['six_native_generator_poses']=r['checks']['six-native48px-generator-poses']['pixel_exact']
    delivery['regions'][name]['activation_checks']={k:v for k,v in r['checks'].items() if any(term in k for term in ['activation-duration','freeze-during','second-with','return-resumes','independent-station','never-decays'])}
    phase11=A/f'validation/phase11-{name}/report.json'
    if phase11.exists():
        regression=json.loads(phase11.read_text())
        if regression['passed'] and regression['romSHA256']==digest:
            delivery['regions'][name]['phase11_shared_progress_bar_regression']=dict(passed=True,report=str(phase11.relative_to(A)))
    p=A/f'validation/launch-{name}/report.json'
    if p.exists():
        regression=json.loads(p.read_text())
        assert regression['passed'] and regression['rom_sha256']==digest
        delivery['regions'][name]['launch_14_15_16_regression']=dict(passed=True,report=str(p.relative_to(A)))
(A/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
def figure(src,label):return f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Fase14 — estaleiro modular</title><style>
body{margin:0;background:#10171c;color:#e1e8eb;font:16px/1.6 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:32px}h1,h2{line-height:1.25}h1{font-size:38px}h2{margin-top:42px}p{max-width:950px}a{color:#efc96d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}.pieces{display:flex;align-items:flex-start;flex-wrap:wrap;gap:16px}.pieces figure{min-width:150px;max-width:512px}figure{margin:0;padding:12px;background:#1c272f;border:1px solid #3d505c;border-radius:8px}img{display:block;max-width:100%;height:auto;image-rendering:pixelated}figcaption{font-size:14px;margin-top:10px;color:#bccbd1}.whole img{width:768px}.grid img{width:100%}.pieces img{min-width:128px;max-height:224px;object-fit:contain}code{overflow-wrap:anywhere}td,th{text-align:left;padding:8px 16px;border-bottom:1px solid #3d505c}</style><main>
<p>PLAGUEFALL / FASE 14 / REVISÃO LOCAL</p><h1>Estaleiro em peças independentes</h1>
<p>Motores no topo, porta na base e console como prop central. Cinco estações de energia interligadas à bateria e ao console, com curvas, uniões e terminais. Geradores novos de48×48pixels, seis estados na paleta do cenário. Mapa512×576; detalhe nativo de1pixel.</p>
<p>Cada estação exige10segundos próximos ao painel sem atirar. Ao se afastar, perde1segundo de progresso a cada segundo completo (10%). Barras individuais permanecem sobre estações com progresso; voltar retoma o restante, pausar congela os relógios e estações ligadas permanecem ligadas.</p>
<p>Piso de placas de ferro64×64com quatro rebites nos cantos, juntas contínuas e detalhe nativo de1pixel. O módulo se repete sob os conduítes e equipamentos.</p>
<p><a href="manifest.json">Geometria e memória</a> · <a href="delivery.json">Validação e ROM</a> · <a href="README.md">Documentação</a> · <a href="prompts/iron-floor.txt">Prompt do piso (ImageGen integrado)</a> · <a href="prompts/generator-native.txt">Prompt dos geradores</a> · <a href="prompts/control-station.txt">Prompt do console</a></p>
<h2>Composição completa</h2><div class="whole">'''
page+=figure('complete-with-generators.png','Montagem do exportador: conexões completas e cinco geradores nativos48×48. Não é captura do emulador.')+'</div><h2>Peças e limitadores</h2><div class="pieces">'
for p,label in [('modules/iron-floor-plate.png','Piso de ferro64×64: quatro rebites e emendas contínuas'),('generator-states.png','Gerador: seis estados nativos48×48'),('connections.png','Rede de energia: seis ramais e12terminais'),('upper.png','Parte superior: motores'),('lower.png','Parte inferior: porta e limitadores'),('objects/control-station.png','Prop central128×112'),('objects/tank-island.png','Bateria96×64'),('modules/left-boundary.png','Limitador esquerdo32×64'),('modules/right-boundary.png','Limitador direito32×64'),('modules/lower-boundary.png','Limitador inferior112×64')]:page+=figure(p,label)
page+='</div><h2>Câmeras reais NTSC</h2><div class="grid">'
for p,label in [('14-progress-working.png','Ativação: progresso de10segundos'),('14-progress-decay.png','Progresso reduz durante o afastamento'),('14-progress-independent-bars.png','Estações com barras independentes'),('14-view-48-128.png','Topo'),('14-view-280-256.png','Prop central'),('14-view-280-496.png','Base'),('14-moving-load.png','Carga em movimento'),('14-pause.png','Pausa'),('14-complete.png','Cinco geradores concluídos')]:page+=figure('validation/ntsc/'+p,label)
page+='</div><h2>Verificação</h2><p>28câmeras e seis estados48×48: pixels exatos emVRAM e zero falhas de cache. Ativação somente na atualização600/500(NTSC/PAL), redução somente após60/50atualizações afastado, limite zero, retomada, relógios independentes, pausa e persistência de estações ligadas verificados. Piso, cinco geradores por controle, colisões, resultados e regressões15/16 passaramNTSC/PAL.</p><table><tr><th>Região</th><th>Carga artificial</th><th>Falhas de cache</th><th>Relatório</th></tr>'
for name,r in regions.items():
    load=r['checks']['moving-four-enemy-four-plus-four-shot-load']
    page+=f'<tr><td>{name.upper()}</td><td>{load["game_fps"]} FPS</td><td>{load["cache_faults"]}</td><td><a href="validation/{name}/report.json">Abrir</a></td></tr>'
page+='</table><p>Carga de20s: quatro inimigos e4+4tiros, com vida protegida e projéteis inativos repostos porRAM. Hardware físico e dificuldade humana não certificados.</p>'
memory=manifest['memory']
page+=f'<p>Cache{memory["cache_tiles"]} + geradores{manifest["generator"]["tiles"]} + barras{memory["progress_bar_tiles"]} ={memory["total_resident_tiles"]}/640tiles; pico conservador{memory["maximum_visible_patterns"]}. Fonte{memory["source_tiles"]}tiles naROM; nenhuma substituição aproximada. ROM SHA256: <code>{digest}</code>.</p></main></html>'
(A/'review.html').write_text(page)
print(json.dumps(delivery,indent=2))
