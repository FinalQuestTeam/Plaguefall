"""Publish the focused phase3review from the final ROM emulator reports."""
from pathlib import Path
import json,hashlib,subprocess
A=Path(__file__).resolve().parent;G=A.parents[1];rom=G/'out/release/Plaguefall.bin';sha=hashlib.sha256(rom.read_bytes()).hexdigest();layout=json.loads((A/'layout.json').read_text());reports={};facts={}
for region in ['ntsc','pal']:
    folder=A/'validation'/region;d=json.loads((folder/'report.json').read_text());assert d['passed'] and d['rom_sha256']==sha
    s=next(s for s in d['stages'] if s['phase']=='03');reports[region]=s
    movie=folder/'03-playtest-1.mp4'
    for seconds,label in [(4,'north'),(13,'south')]:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(seconds),'-i',str(movie),'-frames:v','1',str(folder/f'03-obstacle-{label}.png')],check=True)
    load=s['checks']['03/load']['details'];match=s['ordinary_matches'][0]
    facts[region]=dict(load_fps=load['fps'],cpu_p95=load['cpu_p95_pct'],peak_enemies=load['peak_enemies'],collision_probes=s['checks']['03/collision']['details']['movement_face_probes'],match=match)
summary=dict(status='implemented-verified',rom_sha256=sha,obstacles=len(layout['solids']),tiles=layout['tiles'],connected_16px_positions=layout['connected_positions'],church_exact_native_tiles=288,church_outcomes=2,regions=facts)
(A/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
text=f'''# Fase3 — rua até o galpão, revisão2

A igreja usa os mesmos288tiles da fachada original da fase1, sem redimensionar ou redesenhar. O estado preservado/destruído acompanha a decisão da primeira fase. A rua mantém2560×320pixels e o objetivo de chegar ao galpão.

## Cenário e transposição

- Calçadas contínuas, meio-fio, pavimentação escura, fachadas de casas e postes.
- Quinze veículos abandonados e cinco barricadas:20obstáculos com colisões reais. Os quatro engavetamentos principais alternam os lados da rua e exigem desvios. Há um carro já no primeiro enquadramento.
- Veículos bloqueiam o movimento e os disparos; barreiras baixas bloqueiam os pés. As aberturas continuam acessíveis ao corpo16×16.
- {layout['tiles']}/640tiles, uma paleta compartilhada com a igreja e {layout['connected_positions']}posições livres conectadas. Nenhum tile foi substituído por aproximação para caber naVRAM.

## Testes

ROM: `{sha}`.

| Região | Colisões por controle | Carga forçada | Partida por controle |
|---|---:|---:|---|
'''
for region,f in facts.items():text+=f"| {region.upper()} | {f['collision_probes']}sondas | {f['load_fps']}FPS | {f['match']['result']}, {f['match']['game_seconds']}s lógicos, {f['match']['hp']}HP |\n"
text+='''
Entrada, atlas/câmera, sólidos, travessia completa, tetos de carga e as duas igrejas passaram no Genesis Plus GX. A preparação de cada prova usaRAM e está identificada noJSON; as tentativas por controle não escrevemRAM enquanto jogam. Carga injeta quatro insetos e seis tiros por lado continuamente. A vitória automática não substitui avaliação humana de dificuldade.

## Fontes e reprodução

`source/street-kit.png` foi criado e ajustado pelo ImageGen para este projeto. A conversão faz recorte de alpha, redução por vizinho mais próximo e mapeamento à paleta original da igreja. O piso usa somente dois tons escuros dessa paleta para preservar a leitura dos personagens.

1. `python3 game/art/campaign-early-v1/build.py`
2. `python3 game/art/phase03-street-v2/validate.py`
3. `make -C game -j4`
4. `arch -x86_64 /usr/bin/python3 game/art/campaign-early-v1/test_emulator.py --build-dir game/out/release --nodes 4 --matches 1 --movie --output game/art/phase03-street-v2/validation/ntsc`
5. Repita com `--pal` e saída `validation/pal`; execute `python3 game/art/phase03-street-v2/build_review.py`.

[Revisão e vídeo](review.html) · [Dados de geometria](layout.json) · [Resumo dos ensaios](summary.json)
'''
for a,b in [('Fase3','Fase 3'),('revisão2','revisão 2'),('mesmos288tiles','mesmos 288 tiles'),('fase1','fase 1'),('mantém2560×320pixels','mantém 2560×320 pixels'),(':20obstáculos',': 20 obstáculos'),('corpo16×16','corpo 16×16'),('/640tiles','/640 tiles'),('posições livres',' posições livres'),('naVRAM','na VRAM'),('sondas',' sondas'),('FPS',' FPS'),('s lógicos',' s lógicos'),('HP',' HP'),('usaRAM','usa RAM'),('noJSON','no JSON'),('escrevemRAM','escrevem RAM')]:text=text.replace(a,b)
(A/'README.md').write_text(text)
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Plaguefall · Fase 3 refeita</title><style>*{box-sizing:border-box}body{margin:0;background:#101a23;color:#eee4ca;font:17px/1.55 system-ui}main{max-width:1100px;margin:auto;padding:30px}h1{margin:0;font-size:36px}p{max-width:950px;color:#c7c4b7}a{color:#f3c56b}select,button{font:inherit;background:#27343b;color:#f3e5c1;border:1px solid #6b715b;padding:8px 14px;border-radius:4px;cursor:pointer}video{width:100%;image-rendering:pixelated;background:#070b12;max-height:620px}img{width:100%;image-rendering:pixelated;border:1px solid #645e44}.tags{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}.tag{background:#2b3b41;border-radius:4px;padding:5px 10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.strip{overflow:auto}.strip img{width:2560px;max-width:none}table{border-collapse:collapse;width:100%}td{padding:8px;border-bottom:1px solid #3c4b4c}small{color:#afb9b5}@media(max-width:720px){main{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:28px}}</style><main><h1>Fase 3 · Rua até o galpão</h1><p>A igreja original agora continua na rua. Calçadas, fachadas, postes e veículos caracterizam o caminho; os engavetamentos alternados obrigam a mudar de lado para avançar.</p><div class="tags"><span class="tag">20 obstáculos sólidos</span><span class="tag">2.560 pixels</span><span class="tag">Igreja preservada ou destruída</span><span class="tag">615 / 640 tiles</span></div><p><a href="../../out/playtest/Plaguefall.bin">ROM de playtest</a> · <a href="README.md">Alterações e testes</a> · <a href="../campaign-integrated-v1/review.html">Campanha completa</a></p><p><small>Na ROM de playtest, C no controle troca a fase durante a preparação; escolha 3 e use A para começar.</small></p><label>Região <select id="region"><option value="ntsc">NTSC · 60 Hz</option><option value="pal">PAL · 50 Hz</option></select></label><h2>Partida no emulador</h2><video id="movie" controls autoplay muted loop playsinline></video><p id="match"></p><div class="grid"><div><h2>Entrada pela igreja</h2><img id="entry"></div><div><h2>Primeiro bloqueio</h2><img id="north"></div><div><h2>Outro desvio</h2><img id="south"></div><div><h2>Após destruir a igreja na fase 1</h2><img id="ruined"></div></div><h2>O que foi verificado</h2><table id="stats"></table><p><small>RAM prepara os cenários isolados de teste. A partida do vídeo usa somente controles durante a execução; a carga forçada reinsere quatro insetos e seis tiros por lado. FPS de carga são quadros de simulação por VBlank. As duas variantes da igreja foram comparadas aos tiles originais, e os 20 sólidos foram testados por controles após preparação das posições.</small></p><p><a id="report">JSON completo da região</a> · <a href="summary.json">Resumo</a> · <a href="layout.json">Geometria</a></p><h2>Mapa completo</h2><p><small>Role horizontalmente para percorrer a rua inteira.</small></p><div class="strip"><img src="../campaign-early-v1/street/map-native.png"></div><p><small>ROM de produção: HASH</small></p></main><script>const facts=FACTS;const el=id=>document.getElementById(id);function show(){const r=el('region').value,f=facts[r],p='validation/'+r+'/';el('movie').src=p+'03-playtest-1.mp4';el('movie').poster=p+'03-entry.png';el('entry').src=p+'03-entry.png';el('north').src=p+'03-obstacle-north.png';el('south').src=p+'03-obstacle-south.png';el('ruined').src=p+'03-church-ruined.png';el('report').href=p+'report.json';el('match').textContent='Partida concluída em '+f.match.game_seconds+' s lógicos · '+f.match.hp+' de vida ao chegar · '+f.match.fps+' FPS médios nessa tentativa.';el('stats').innerHTML='<tr><td>Colisões por controle</td><td>'+f.collision_probes+' sondas aprovadas</td></tr><tr><td>Carga contínua máxima</td><td>'+f.load_fps+' FPS; pico de '+f.peak_enemies+' insetos</td></tr><tr><td>Travessia e câmera</td><td>Passaram</td></tr><tr><td>Igreja da fase 1</td><td>288 tiles idênticos; duas variantes verificadas</td></tr>';}el('region').onchange=show;show();</script></html>'''.replace('HASH',sha).replace('FACTS',json.dumps(facts,ensure_ascii=False)).replace('615 / 640',str(layout['tiles'])+' / 640')
(A/'review.html').write_text(page)
print('PASS: phase3review matches current ROM',sha)
