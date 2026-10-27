"""Build the reviewable camera proposal from actual libretro telemetry."""
from pathlib import Path
from collections import defaultdict
import csv
import html
import json

ROOT = Path(__file__).resolve().parents[1] / 'art/camera-motion-audit-v1'


def analyze(region):
    report = json.loads((ROOT / 'validation' / region / 'report.json').read_text())
    assert report['passed'] and len(report['stages']) == 14
    results = []
    for stage in report['stages']:
        trials = stage['trials']
        assert len(trials) == 13 and all(t['samples'] >= 50 for t in trials)
        for t in trials:
            if t['trial'].startswith('traverse'):
                assert not t['navigation_failures'] and t['remaining_corners'] == 0
        rows = list(csv.DictReader((ROOT / 'validation' / region / stage['phase'] / 'telemetry.csv').open()))
        camera = None
        previous = None
        model_clip = model_error = clipping_run = max_clipping_run = 0
        for row in rows:
            p = (int(row['px']), int(row['py']))
            ideal = (int(row['ideal_x']), int(row['ideal_y']))
            if previous != row['trial']:
                camera = ideal
                clipping_run = 0
            else:
                camera = tuple(a + max(-4, min(4, b-a)) for a, b in zip(camera, ideal))
            model_error = max(model_error, *(abs(a-b) for a, b in zip(camera, ideal)))
            model_clip += int(p[0]-8-camera[0] < 0 or p[0]+24-camera[0] > 320 or
                              p[1]-31-camera[1] < 24 or p[1]+17-camera[1] > 224)
            clipping_run = clipping_run + 1 if int(row['clip']) else 0
            max_clipping_run = max(max_clipping_run, clipping_run)
            previous = row['trial']
        worst = max(trials, key=lambda t: 1000*t['clipped_samples'] + t['max_error_x'] + t['max_error_y'])
        results.append(dict(phase=stage['phase'], region=region, samples=len(rows),
                            max_error_x=max(t['max_error_x'] for t in trials),
                            max_error_y=max(t['max_error_y'] for t in trials),
                            clips=sum(t['clipped_samples'] for t in trials),
                            longest_clipping_run=max_clipping_run,
                            target_jumps=sum(t['target_jumps_over12'] for t in trials),
                            escort_switches=sum(t['escort_switches'] for t in trials),
                            model_clips=model_clip, model_max_error=model_error,
                            seconds=sum(t['physical_seconds'] for t in trials),
                            worst=worst))
    return report, results


def chart(phase, trial):
    rows = [r for r in csv.DictReader((ROOT / 'validation/ntsc' / phase / 'telemetry.csv').open()) if r['trial'] == trial]
    values = [[int(r[key]) for r in rows] for key in ('error_x', 'error_y')]
    stride = max(1, len(rows)//650)
    def line(v):
        return ' '.join(f'{48+i/max(1,len(v)-1)*850:.1f},{126-v[i]*.6:.1f}' for i in range(0, len(v), stride))
    return f'''<svg viewBox="0 0 940 255" role="img" aria-label="Desvio da câmera na fase {phase}">
      <rect width="940" height="255" fill="#101c2b"/>
      <path d="M48 30V222H904M48 126H904" stroke="#587087" fill="none"/>
      <text x="8" y="35" fill="#adbdcc" font-size="12">+160</text><text x="16" y="130" fill="#adbdcc" font-size="12">0</text><text x="8" y="221" fill="#adbdcc" font-size="12">−160</text>
      <polyline points="{line(values[0])}" fill="none" stroke="#53c9ff" stroke-width="2"/>
      <polyline points="{line(values[1])}" fill="none" stroke="#ffb75a" stroke-width="2"/>
      <text x="48" y="248" fill="#adbdcc" font-size="12">Início do teste</text><text x="705" y="248" fill="#adbdcc" font-size="12">{len(rows)} quadros de simulação</text>
      </svg><p class="muted">Azul: desvio horizontal. Laranja: desvio vertical. Zero é o centro possível após limitar a câmera às bordas do mapa.</p>'''


def main():
    reports, measurements = {}, {}
    for region in ('ntsc', 'pal'):
        reports[region], measurements[region] = analyze(region)
    assert reports['ntsc']['romSHA256'] == reports['pal']['romSHA256']
    combined = measurements['ntsc'] + measurements['pal']
    summary = dict(rom_sha256=reports['ntsc']['romSHA256'], phases=14, regions=2,
                   trials=364, samples=sum(r['samples'] for r in combined),
                   emulated_seconds=round(sum(r['seconds'] for r in combined), 2),
                   baseline_clipped_samples=sum(r['clips'] for r in combined),
                   model_clipped_samples=sum(r['model_clips'] for r in combined),
                   model_max_error=max(r['model_max_error'] for r in combined),
                   model_scope='Offline geometric replay of measured player positions with a clamped body-centered target, initialization at the target, and the existing4px/tick cap. Not an emulator test of modified production code; no DMA/VRAM/FPS claim. No escort or landmark bias in this baseline model.',
                   measurements=combined)
    (ROOT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    by_phase = defaultdict(dict)
    for r in combined:
        by_phase[r['phase']][r['region']] = r
    rows = []
    for phase, regions in by_phase.items():
        n, p = regions['ntsc'], regions['pal']
        cause = ('Acompanhamento consistente' if phase in ('1','2A','2B','4') else
                 'Enquadramento fixo da Santa' if phase == '5' else
                 'Escolta + fachada + âncora vertical' if phase in ('6A','6B','12') else
                 'Âncora vertical de184px' if phase in ('7','8','10','11') else
                 'Fachadas + âncora vertical')
        rows.append(f"<tr><td>{phase}</td><td>{max(n['max_error_x'],p['max_error_x'])} px</td><td>{max(n['max_error_y'],p['max_error_y'])} px</td><td>{n['clips']} / {p['clips']}</td><td>{cause}</td></tr>")
    evidence = []
    for phase in ('3','6B','9','10','12'):
        r = by_phase[phase]['ntsc'];t=r['worst'];w=t['worst']
        evidence.append(f'''<article><h3>Fase {phase} · {html.escape(t['trial'])}</h3>
          <img src="validation/ntsc/{phase}/{t['trial']}.png" alt="Quadro real da fase {phase}" width="640" height="448">
          <p>Posição {w['position']}; câmera {w['camera']}; desvio nesse quadro {w['error']} px. Caixa do personagem na tela: {w['sprite']}.</p>
          <p>{r['clips']} quadros com corte; sequência contínua máxima: {r['longest_clipping_run']} quadros de simulação. A captura é o pior quadro do teste, não o valor médio.</p>
          <details><summary>Vídeo de reversões e diagonais na região central</summary><video controls preload="metadata" width="640" src="replays/ntsc/{phase}/middle-reversals-speed100.mp4"></video><p>Captura real, velocidade +100%, cenário isolado. O vídeo central é um cenário diferente da captura de pior caso acima.</p></details>
          {chart(phase,'traverse-speed100')}</article>''')
    document = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Plaguefall — revisão da câmera, fases1–12</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#09121d;color:#e7eef5;font:17px/1.6 system-ui,sans-serif}}main{{max-width:1120px;padding:48px 28px;margin:auto}}h1{{font-size:38px;line-height:1.2}}h2{{margin-top:52px;color:#a9dcff}}h3{{margin-top:12px}}p{{max-width:90ch}}a{{color:#80d4ff}}code,pre{{background:#142335;padding:3px 7px;border-radius:4px}}pre{{padding:20px;white-space:pre-wrap}}table{{width:100%;border-collapse:collapse;font-size:15px}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #32465a}}th{{color:#a9dcff}}article{{padding:22px;margin:24px 0;background:#101c2b;border:1px solid #2c4154;border-radius:12px}}img,video{{max-width:100%;height:auto;image-rendering:pixelated;background:#000}}svg{{width:100%;margin-top:16px}}.muted{{color:#9dafc0;font-size:14px}}.callout{{border-left:4px solid #ffb75a;padding:12px 20px;background:#202334}}li{{margin:12px 0}}.metrics{{display:flex;gap:30px;flex-wrap:wrap}}.metrics strong{{font-size:30px;display:block;color:#79d9ff}}</style>
    <main><p class="muted">PLAGUEFALL · Auditoria de movimento ·26/10/2026</p><h1>A câmera precisa priorizar Damião durante o movimento.</h1>
    <p>As fases1,2A,2B e4 já acompanham o corpo do personagem com até1px de diferença do centro possível. Os corredores, a defesa da Santa e as arenas com âncora vertical desviam dessa regra. Na9 e na12, as prioridades de composição chegam a cortar a caixa de32×48 do personagem.</p>
    <div class="metrics"><div><strong>364</strong>testes automatizados</div><div><strong>{summary['samples']:,}</strong>quadros medidos</div><div><strong>{summary['emulated_seconds']/60:.1f}min</strong>de jogo emulado</div><div><strong>14×2</strong>versões de fase × regiões</div></div>
    <p class="callout">Proposta pronta para revisão; o código da câmera e a ROM de produção não foram alterados por esta auditoria. O modelo geométrico da proposta removeu os cortes nas trajetórias medidas. Ainda é necessária uma implementação na ROM e validação de streaming, efeitos, pausa e desempenho.</p>
    <h2>O que foi testado</h2><p>Fases1 a12, incluindo2A/2B e6A/6B, no Genesis Plus GX, em NTSC e PAL. Para cada versão/região: três percursos de ida e volta com bônus de velocidade0%,60% e100%; nove testes de parada, reversão, movimento vertical e diagonais em três setores; e um teste de combate com inimigos, tiros e escolta ativos.</p>
    <p>As42 travessias por região terminaram o percurso planejado sem falhas de navegação; as saídas que concluiriam a fase foram evitadas. A configuração usa RAM antes da tentativa para selecionar fase, proteger a vida, escolher equipamento e isolar combate. Durante os testes medidos, o controle move o personagem e uma trava impede escritas de RAM pelo teste. Os portões6A/6B foram preparados abertos. Na7, as bases das cargas entram no planejamento; na8, os emissores são preservados. O combate usa um escudo preparado antes da tentativa. Não é avaliação humana da dificuldade nem medição da carga máxima.</p>
    <p class="muted">ROM fixa: <code>{summary['rom_sha256']}</code>. Uma recompilação externa foi detectada durante os pilotos; os resultados finais usam uma única cópia fixa da ROM e dos símbolos correspondentes. PAL altera somente o cabeçalho regional em memória, conforme os testes existentes do projeto.</p>
    <h2>Resultados por fase</h2><p>Desvio em relação ao centro possível do corpo do personagem, com as bordas do mundo já descontadas. O centro visual é(px+8,py−7); o centro da área jogável, descontando o HUD de24px, é(160,124). Um personagem fora do centro por estar na extremidade do mapa não é contado como erro evitável. “Corte” considera a caixa completa de32×48 e pode incluir margens transparentes.</p>
    <table><thead><tr><th>Fase</th><th>Máx. horizontal</th><th>Máx. vertical</th><th>Quadros com corte NTSC/PAL</th><th>Principal causa</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
    <h2>Por que acontece</h2><ol>
    <li><strong>Âncoras verticais inconsistentes.</strong> <code>ARENA_camera</code> usa o centro do jogador no caso comum, mas substitui isso por <code>py−cameraPlayerY</code> em corredores e fábricas. O valor184 nas fases7/8/10/11 produz53px de desvio persistente em áreas sem restrição de borda. Existem também âncoras200 e240.</li>
    <li><strong>Construções assumem o enquadramento durante a corrida.</strong> O marco mais próximo dentro de65px limita X/Y para caber inteiro. A seleção muda por proximidade, sem histerese. Um prédio pode colocar Damião no extremo lateral mesmo longe da borda do mundo. Isso aparece nas fases3,9 e12.</li>
    <li><strong>A prioridade de segurança é insuficiente.</strong> No ramo dos corredores, o limite inferior usa <code>py+8−224</code>; o sprite real termina em <code>py+17</code>. Além disso, o limite protetor é aplicado ao alvo antes da aproximação de4px. A câmera interpolada ainda pode ficar atrás do alvo seguro e cortar o corpo durante a transição.</li>
    <li><strong>A escolta muda o alvo de forma binária.</strong> A câmera passa para a média dos dois atores quando a distância fica abaixo de200px em X e120px em Y. Cruzar esses limites pode acrescentar ou retirar quase100px no alvo horizontal. A velocidade máxima do jogador é4px por eixo/tick, igual ao teto da câmera: um desvio já existente pode persistir durante uma corrida.</li>
    <li><strong>O enquadramento da Santa também retém a câmera.</strong> A prioridade de mostrar o objetivo completo desvia o centro vertical na fase5. Ela precisa respeitar a segurança do personagem e usar os indicadores do HUD quando os dois não couberem bem.</li></ol>
    <p class="muted">Referências: <code>game/src/levels/arena.c:280–382</code>; <code>game/src/system/video/spritelist.c:143–146</code>; <code>game/src/actors/player.c:107–116</code>; configurações de cena em <code>campaign_early.c</code>, <code>campaign_routes.c</code> e <code>campaign_factory_phase10.inc</code>. Saltos medidos são do alvo desejado; o deslocamento efetivo continua limitado a4px por atualização.</p>
    <h2>Solução recomendada</h2><ol>
    <li><strong>Unificar o acompanhamento em movimento.</strong> Calcular o alvo pelo centro do corpo e pela área útil do HUD: <code>x=px−152</code>, <code>y=py−131</code>, limitado a0..largura−320 e0..altura−224. Usar essa regra em todas as fases1–12. O comportamento já aprovado do pátio serve de referência.</li>
    <li><strong>Manter a resposta imediata ao deslocamento.</strong> A base segue o deslocamento real de Damião no mesmo tick. Inicializar a câmera no alvo ao carregar/reiniciar a fase, antes de desenhar o cenário. Manter inicialmente o teto de4px por eixo: o modelo mostrou que ele é suficiente quando os focos não introduzem dívida de enquadramento.</li>
    <li><strong>Transformar fachada e escolta em ajustes opcionais pequenos.</strong> Durante movimento rápido, seu peso deve cair até zero. Em repouso por cerca de250ms, permitir uma composição suave e limitada, inicialmente até16px em X e12px em Y. Trocar marcos com histerese; o marco atual só cede quando o novo for claramente mais próximo. Para Dinorah, usar peso contínuo pela distância, com prioridade ao jogador e indicadores fora da tela. Esses ajustes são uma segunda etapa, fora do modelo validado abaixo.</li>
    <li><strong>Fazer a segurança vencer a composição.</strong> Considerar a caixa inteira(px−8,py−31,32,48) e uma margem de8px abaixo do HUD e das bordas, quando o mapa permitir. Conferir a posição efetivamente aplicada, depois de suavização e limitações de streaming. Se mostrar o prédio ou os dois atores exigir quebrar essa margem, reduzir o ajuste decorativo.</li>
    <li><strong>Preservar o compromisso entre câmera e VRAM.</strong> Continuar aplicando mapa, padrões e rolagem juntos em VBlank. Instrumentar uma recusa de <code>SCENESTREAM_move</code> com contador explícito e reservar orçamento para a janela visível antes de efeitos secundários. Não há evidência nesta auditoria para atribuir os desvios a recusas de DMA; o alvo de composição já explica os principais casos.</li></ol>
    <pre>// Baseline proposto, sem composição decorativa durante movimento.
targetX = clamp(px - 152, 0, worldWidth - 320);
targetY = clamp(py - 131, 0, worldHeight - 224);
nextX = approach(cameraX, targetX, 4);
nextY = approach(cameraY, targetY, 4);
// Validar sprite inteiro e janela residente; confirmar rolagem em VBlank.</pre>
    <h2>Comparação geométrica da proposta</h2><p>Reproduzi as posições reais dos {summary['samples']:,} quadros num modelo com alvo centralizado, limitação às bordas, inicialização no alvo e o mesmo teto de4px/tick. Resultado: <strong>{summary['baseline_clipped_samples']} quadros com corte no comportamento atual → {summary['model_clipped_samples']} no modelo</strong>; desvio corrigível máximo do modelo: <strong>{summary['model_max_error']}px</strong>.</p>
    <p>Essa é uma reprodução matemática das trajetórias medidas, não um playtest de uma ROM corrigida. Ela confirma que não é necessário acelerar a câmera para acompanhar essas trajetórias. A implementação ainda precisa passar pela VRAM, pelo orçamento de DMA e pelos efeitos reais. O modelo não inclui os ajustes opcionais de fachada/escolta.</p>
    <h2>Critérios para aceitar a implementação</h2><ul><li>Repetir os364 cenários com zero cortes da caixa do personagem, descontando somente limites físicos inevitáveis, e zero falhas de navegação.</li><li>Sem desvio persistente acima de8px por eixo durante corrida em área com câmera livre; sem oscilações ao atravessar os limites de escolta ou os marcos.</li><li>Testar morte da Dinorah, separação/reaproximação, pausa/retomada, reinício, transição entre fases e abertura real dos portões6A/6B.</li><li>Verificar pixels e emendas durante movimento, sem aguardar a câmera parar. Medir cache, falhas, recusas de streaming, sprites e NTSC/PAL sob a carga máxima configurada; comparar o desempenho com o mesmo build de referência.</li><li>Fazer revisão humana dos vídeos de corrida e combate para ajustar somente os pequenos desvios opcionais.</li></ul>
    <h2>Evidências por cenário</h2>{''.join(evidence)}
    <h2>Reproduzir e inspecionar os dados</h2><p><a href="summary.json">Resumo e comparação geométrica</a> · <a href="validation/ntsc/report.json">Relatório NTSC</a> · <a href="validation/pal/report.json">Relatório PAL</a>. Cada pasta de fase contém a telemetria CSV por quadro e13 capturas de pior enquadramento.</p>
    <pre>arch -x86_64 /usr/bin/python3 game/tools/test_camera_motion_emulator.py \
  --nodes 1,2,3,4,5,6,7,8,9,10,11,12,13,14 \
  --build-dir /copia-fixa-da-rom-e-simbolos --output /private/tmp/camera-ntsc
# Repetir com --pal e outro diretório.
# Vídeos curtos: --nodes 4,8,11,12,14 --movie --replays-only
python3 game/tools/build_camera_motion_report.py</pre>
    <p class="muted">Os nós técnicos1..14 correspondem a1,2A,2B,3,4,5,6A,6B,7,8,9,10,11,12. Arquivos de relatório preservam o hash da ROM testada. O gerador usa os resultados locais de validation/ntsc e validation/pal.</p></main></html>'''
    (ROOT / 'review.html').write_text(document)
    print(json.dumps({k:v for k,v in summary.items() if k!='measurements'}, indent=2))


if __name__ == '__main__':
    main()
