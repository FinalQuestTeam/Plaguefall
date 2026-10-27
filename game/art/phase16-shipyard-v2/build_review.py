"""Publish the phase16 review against the tested production ROM."""
from pathlib import Path
import hashlib, html, json

A=Path(__file__).resolve().parent
G=A.parents[1]
d=json.loads((A/'manifest.json').read_text())
rom=G/'out/release/Plaguefall.bin'
digest=hashlib.sha256(rom.read_bytes()).hexdigest()
regions={}
for name in ['ntsc','pal']:
    r=json.loads((A/f'validation/{name}/report.json').read_text())
    assert r['passed'] and r['romSHA256']==digest
    regions[name]=dict(passed=True,report=f'validation/{name}/report.json',
                       camera_views=len(r['checks']['28-real-native-camera-views']),
                       boss_combat=r['checks']['controller-boss-combat'])
    for stage in [14,15]:
        report_path=f'../phase15-shipyard-v2/validation/'+(f'phase14-{name}' if stage==14 else name)+'/report.json'
        regression=json.loads((A/report_path).read_text())
        assert regression['passed'] and regression['romSHA256']==digest
        regions[name][f'phase{stage}_regression']=dict(passed=True,report=report_path)
delivery=dict(rom=str(rom.relative_to(G)),rom_sha256=digest,rom_bytes=rom.stat().st_size,
              size=d['size'],memory=d['memory'],unchanged_outside_windows=True,
              generated_resources_and_native_checks=True,regions=regions,
              limits=['Genesis Plus GX; hardware físico não testado.',
                      'Combate por controle com vida e proteção do jogador elevadas uma vez por RAM; chefe original.'])
(A/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')

def figure(src,label):
    return f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'

page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fase 16 — janelas nativas</title><style>
body{margin:0;background:#10171c;color:#e1e8eb;font:16px/1.6 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:32px}h1,h2{line-height:1.25}h1{font-size:38px}h2{margin-top:38px}a{color:#efc96d}p{max-width:940px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}figure{margin:0;padding:12px;background:#1c272f;border:1px solid #3d505c;border-radius:8px}img{display:block;max-width:100%;height:auto;image-rendering:pixelated}figcaption{font-size:14px;margin-top:10px;color:#bccbd1}.grid img{width:100%}.whole img{width:768px}td,th{padding:8px 16px;border-bottom:1px solid #3d505c;text-align:left}code{overflow-wrap:anywhere}</style><main>
<p>PLAGUEFALL / FASE 16 / REVISÃO LOCAL</p><h1>O mesmo estaleiro, com novas janelas</h1>
<p>Mesma sala de 512×576 das fases 14/15: piso rebitado, limites modulares, antena, bateria, conexões e cinco estações de energia ligadas. A fase 16 usa a mesma tabela de colisões da 15. Escorpião mantém seus ataques e vida originais.</p>
<p>Apenas os interiores das duas janelas superiores mudam. Módulo nativo 144×80, 16 cores e tiles 8×8, criado com ImageGen integrado a partir da janela existente. Moldura, soleira e todos os pixels externos conservam a arte aprovada da 15.</p>
<p><a href="README.md">Documentação</a> · <a href="manifest.json">Geometria e memória</a> · <a href="delivery.json">Validação e ROM</a> · <a href="../../out/release/Plaguefall.bin">ROM</a> · <a href="prompts/engine-window.txt">Prompt exato</a></p>
<h2>Cenário completo</h2><div class="whole">'''
page+=figure('complete.png','Composição nativa512×576. Somente o interior das janelas difere da sala 15.')+'</div><h2>Interior da janela</h2>'
page+=figure('objects/engine-interior-native.png','144×80pixels, paleta existente de 16 cores; a mesma peça aparece nas duas janelas.')
page+='<h2>Capturas reais da ROM em NTSC</h2><div class="grid">'
for src,label in [('16-view-160-128.png','Janela nativa e limite superior'),('16-view-280-256.png','Mesma antena e conexões da 15'),('16-view-280-496.png','Mesma bateria e limite inferior'),('16-boss-entry.png','Chefe original no estaleiro ampliado'),('16-pause.png','Pausa'),('16-boss-combat-result.png','Chefe derrotado por comandos do controle')]:
    page+=figure('validation/ntsc/'+src,label)
page+='</div><h2>Validação</h2><p>28 câmeras por região com comparação literal dos tiles e equipamentos em VRAM; zero falhas de cache. Travessia por controle, colisões, quatro limites, pausa, derrota/reinício e vitória contra o chefe passaram em NTSC/PAL. As regressões completas das fases 14 e 15 também passaram na mesma ROM, incluindo operação das estações e defesa de 120 segundos. Verificação geral de recursos, áudio, câmera e jogador aprovada.</p><table><tr><th>Região</th><th>Câmeras</th><th>Combate observado</th><th>Chefe derrotado</th></tr>'
for name,r in regions.items():
    page+=f'<tr><td>{name.upper()}</td><td>{r["camera_views"]}</td><td>{r["boss_combat"]["game_fps"]} FPS</td><td>Sim</td></tr>'
page+='</table><p>O ensaio de combate eleva vida e proteção do jogador uma vez por RAM; não altera vida nem IA do chefe. Esses FPS descrevem a tentativa observada, sem certificar todas as cargas possíveis. Hardware físico não testado.</p>'
page+=f'<p>{d["memory"]["cache_tiles"]} tiles de cache + {d["memory"]["generator_tiles"]} de geradores + {d["memory"]["radio_tiles"]} de rádio = {d["memory"]["total_resident_tiles"]}/640 residentes. Máximo conservador {d["memory"]["maximum_visible_patterns"]} padrões visíveis. Reconstrução exata e todos os pixels fora das janelas idênticos aos da 15. ROM SHA256: <code>{digest}</code>.</p></main></html>'
(A/'review.html').write_text(page)
print(json.dumps(delivery,ensure_ascii=False,indent=2))
