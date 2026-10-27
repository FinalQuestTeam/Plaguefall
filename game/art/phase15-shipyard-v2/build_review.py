"""Publish phase15 native art and matching NTSC/PAL production-ROM validation."""
from pathlib import Path
import hashlib, html, json
A=Path(__file__).resolve().parent;G=A.parents[1]
manifest=json.loads((A/'manifest.json').read_text())
rom=G/'out/release/Plaguefall.bin';digest=hashlib.sha256(rom.read_bytes()).hexdigest()
regions={k:json.loads((A/f'validation/{k}/report.json').read_text()) for k in ['ntsc','pal']}
assert all(r['passed'] and r['romSHA256']==digest for r in regions.values())
delivery=dict(rom=str(rom.relative_to(G)),rom_sha256=digest,rom_bytes=rom.stat().st_size,size=manifest['size'],memory=manifest['memory'],objective_seconds=120,generators_powered_on_entry=True,regions={})
for name,r in regions.items():
    delivery['regions'][name]=dict(passed=True,report=f'validation/{name}/report.json',camera_views=len(r['checks']['28-real-native-camera-views']),load=r['checks']['moving-three-enemy-four-plus-four-shot-load'],full_defense=r['checks']['full120second-controller-free-hold-and-result'])
    for kind,report_path in [('phase14',f'validation/phase14-{name}/report.json'),('phase16',f'../phase16-shipyard-v2/validation/{name}/report.json')]:
        regression=json.loads((A/report_path).read_text());assert regression['passed'] and regression['romSHA256']==digest
        delivery['regions'][name][kind+'_regression']=dict(passed=True,report=report_path)
    delivery['regions'][name]['core_collision_and_feedback']={k:r['checks'][k] for k in ['antenna-damage-from-all-four-outside-edges','mast-does-not-block-player','mast-and-removed-console-never-receive-damage','actor-depth-under-mast-and-in-front-of-core','core-flashes-locally-after-damage']}
(A/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
def figure(src,label):return f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fase 15 — antena e estaleiro</title><style>
body{margin:0;background:#10171c;color:#e1e8eb;font:16px/1.6 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:32px}h1,h2{line-height:1.25}h1{font-size:38px}h2{margin-top:42px}a{color:#efc96d}p{max-width:950px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}figure{margin:0;padding:12px;background:#1c272f;border:1px solid #3d505c;border-radius:8px}img{display:block;max-width:100%;height:auto;image-rendering:pixelated}figcaption{font-size:14px;margin-top:10px;color:#bccbd1}.grid img{width:100%}.whole img{width:768px}.props{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}.props img{min-width:256px}td,th{padding:8px 16px;border-bottom:1px solid #3d505c;text-align:left}code{overflow-wrap:anywhere}</style><main>
<p>PLAGUEFALL / FASE 15 / REVISÃO LOCAL</p><h1>Antena no padrão das estações de energia</h1>
<p>Mesmo piso rebitado, limites modulares, bateria, conexões e geradores nativos da sala 14. Os cinco geradores já estão ligados. A missão continua sendo defender o rádio por 120 segundos.</p>
<p>Rádio compacto de 48×64, com visor ciano e seis estados na paleta PAL1 existente. Somente a base de 32×16 bloqueia passagem e recebe dano. O mastro é visual e permite passagem; a barra junto ao núcleo e o piscar local identificam a integridade do objetivo. Atores passam atrás da antena e à frente do núcleo conforme a posição no chão.</p>
<p><a href="README.md">Documentação</a> · <a href="manifest.json">Geometria e memória</a> · <a href="delivery.json">Validação e ROM</a> · <a href="../phase15-radio-core-proposal-v1/prompt.txt">Prompt exato</a></p><h2>Cenário completo</h2><div class="whole">'''
page+=figure('normal-complete.png','Composição nativa: geradores ligados, bateria conectada e nova antena. Não é captura do emulador.')+'</div><h2>Antena e estados do rádio</h2><div class="props">'
page+=figure('objects/radio-antenna.png','Prop completo48×64; base sólida32×16')+figure('radio-states.png','Seis estados nativos48×64')+'</div><h2>Capturas reais NTSC</h2><div class="grid">'
for p,label in [('15-core-behind.png','Passagem atrás do mastro sem colisão'),('15-core-front.png','Personagem à frente da base; barra de integridade'),('15-view-280-256.png','Núcleo e estações'),('15-view-280-496.png','Bateria e piso'),('15-ignition-focus.png','Motor em ignição: combate e relógio pausados'),('15-complete.png','Defesa completa e resultado')]:page+=figure('validation/ntsc/'+p,label)
page+='</div><h2>Validação</h2><p>28 câmeras por região com cenário e equipamentos idênticos em VRAM, seis estados do rádio, zero falhas de cache, travessia por controle e colisões. Dano somente nos quatro lados da base, passagem livre pelo mastro, ausência de dano fora do núcleo, profundidade dos atores e piscar local verificados. Pausa, ignição, reinício normal, defesa completa de120s e continuação para16 também passaram.</p><table><tr><th>Região</th><th>Setor</th><th>Carga artificial</th><th>Falhas de cache</th></tr>'
for name,r in regions.items():
    for load in r['checks']['moving-three-enemy-four-plus-four-shot-load']:page+=f'<tr><td>{name.upper()}</td><td>{load["section"]}</td><td>{load["game_fps"]} FPS</td><td>{load["cache_faults"]}</td></tr>'
page+='</table><p>Carga de20s por setor: três inimigos e4+4tiros, com proteção de vida e reposição de projéteis inativos porRAM. Hardware físico e dificuldade humana não certificados.</p>'
page+=f'<p>{manifest["memory"]["cache_tiles"]} tiles de cache + {manifest["memory"]["generator_tiles"]} geradores + {manifest["memory"]["radio_tiles"]} rádio = {manifest["memory"]["total_resident_tiles"]}/640 tiles. Nenhuma aproximação de padrões. ROM SHA256: <code>{digest}</code>.</p></main></html>'
(A/'review.html').write_text(page);print(json.dumps(delivery,indent=2))
