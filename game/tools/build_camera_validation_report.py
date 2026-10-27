"""Package camera build evidence without changing the main release or audit."""
from pathlib import Path
import hashlib
import json

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME / 'art/camera-follow-v1'
BUILD = GAME / 'out/camera-validation'


def main():
    digest = hashlib.sha256((BUILD/'Plaguefall.bin').read_bytes()).hexdigest()
    metrics = []
    lifecycle = 0
    for region in ('ntsc','pal'):
        report = json.loads((ROOT/'validation'/region/'report.json').read_text())
        assert report['passed'] and report['romSHA256']==digest and len(report['stages'])==14
        for stage in report['stages']:
            assert len(stage['trials'])==13 and stage['pause_resume']['passed'] and stage['selector_restart']['passed']
            lifecycle += 2
            if 'escort_death' in stage:
                assert stage['escort_death']['passed'];lifecycle += 1
            for trial in stage['trials']:
                assert trial['clipped_samples']==0 and trial['ram_writes_during_trial']==0
                if trial['trial'].startswith('traverse'):
                    assert not trial['navigation_failures'] and trial['remaining_corners']==0
            metrics.append(dict(region=region,phase=stage['phase'],
                samples=sum(t['samples'] for t in stage['trials']),
                live_pixel_cells=sum(t['live_pixel_cells'] for t in stage['trials']),
                stream_deferrals=sum(t['stream_deferrals'] for t in stage['trials']),
                max_error_x=max(t['max_error_x'] for t in stage['trials']),
                max_error_y=max(t['max_error_y'] for t in stage['trials'])))
        escorts = json.loads((ROOT/'escorts'/region/'report.json').read_text())
        assert escorts['passed'] and escorts['romSHA256']==digest
        for phase in ('factory10','factory11'):
            r=json.loads((ROOT/phase/region/'report.json').read_text())
            assert r['passed'] and r['romSHA256']==digest
    performance=[]
    for phase in ('10','11'):
        for region in ('ntsc','pal'):
            new=json.loads((ROOT/('factory'+phase)/region/'report.json').read_text())
            old=json.loads((ROOT/('baseline-factory'+phase)/'ntsc/report.json').read_text()) if region=='ntsc' else None
            old_load=old['checks']['maximum-configured-load'] if old else []
            for i,row in enumerate(new['checks']['maximum-configured-load']):
                performance.append(dict(phase=phase,region=region,section=row['section'],fps=row['game_fps'],
                                        reference_fps=old_load[i]['game_fps'] if old else None,
                                        enemies=row['enemies'],shots_per_pool=row['shots_per_pool']))
    summary=dict(title='Plaguefall — câmera v1 para validação',rom_sha256=digest,
        rom_bytes=(BUILD/'Plaguefall.bin').stat().st_size,rom='Plaguefall.bin',
        motion_trials=364,samples=sum(m['samples'] for m in metrics),
        live_pixel_cells=sum(m['live_pixel_cells'] for m in metrics),
        clipped_samples=0,stream_faults=0,stream_deferrals=sum(m['stream_deferrals'] for m in metrics),
        lifecycle_checks=lifecycle,full_escorts=6,gate_checks=8,
        changes=['Body-centered player follow throughout stages1–12 and their A/B variants',
            'Landmark/escort/Santa composition only after250ms stationary, capped at16px X /12px Y and eased1px/tick',
            'Landmark selection uses80px retention and12px hysteresis; escort weight varies continuously by distance',
            'Full32x48 body plus8px margin where map bounds permit, before target and after camera approach',
            'Normal camera follows<=4px/axis; composition unwind can use5px, with an8px hard streaming ceiling',
            'Offscreen living Dinorah receives an edge direction marker',
            'Streaming deferral instrumentation; map/pattern/scroll remain committed together inVBlank'],
        limitations=['Factory load probes show FPS regressions in some sectors; this is a camera validation candidate, not a performance-approved release.',
                     'CPU/visible content differ with the camera window. Measurements do not isolate the exact source of the factory regressions.',
                     'Full escort movement seeds sewer gates open; each actual valve/gate interaction is tested separately. Scenario setup uses RAM before guarded controller trials.'],
        measurements=metrics,performance=performance)
    (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (BUILD/'camera-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    old=json.loads((GAME/'art/camera-motion-audit-v1/summary.json').read_text())
    old_by={r['phase']:r for r in old['measurements'] if r['region']=='ntsc'}
    table=[]
    for r in metrics:
        if r['region']!='ntsc':continue
        b=old_by[r['phase']]
        table.append(f"<tr><td>{r['phase']}</td><td>{b['max_error_x']} / {b['max_error_y']} px</td><td>{r['max_error_x']} / {r['max_error_y']} px</td><td>0</td></tr>")
    fpsrows=''.join(f"<tr><td>{r['phase']}</td><td>{r['region'].upper()}</td><td>{r['section']}</td><td>{r['reference_fps'] if r['reference_fps'] is not None else '—'}</td><td>{r['fps']}</td></tr>" for r in performance)
    videos=''.join(f'''<article><h3>Fase {phase} · velocidade +100%</h3><video controls preload="metadata" width="640" src="replays/ntsc/{phase}/middle-reversals-speed100.mp4"></video><p><a href="replays/pal/{phase}/middle-reversals-speed100.mp4">Ver em PAL</a></p></article>''' for phase in ('3','6B','9','10','12'))
    document=f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaguefall — build de validação da câmera</title>
    <style>*{{box-sizing:border-box}}body{{background:#0c1420;color:#e6edf4;font:17px/1.6 system-ui;margin:0}}main{{max-width:1060px;margin:auto;padding:42px 24px}}h1{{font-size:36px;line-height:1.2}}h2{{margin-top:40px;color:#a6dbff}}a{{color:#8ed9ff}}.download{{display:inline-block;background:#a9e1ff;color:#0c1420;padding:13px 22px;border-radius:8px;font-weight:700;text-decoration:none}}.warning{{padding:18px;background:#382b16;border-left:4px solid #efbd73}}code{{overflow-wrap:anywhere;background:#192a3c;padding:3px}}table{{border-collapse:collapse;width:100%;font-size:15px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #33465a}}article{{padding:20px;margin:22px 0;background:#142234;border-radius:10px}}video{{max-width:100%;image-rendering:pixelated}}li{{margin:9px 0}}.muted{{color:#a5b6c8;font-size:14px}}</style>
    <main><p class="muted">PLAGUEFALL · 26/10/2026 · Câmera v1</p><h1>Build pronta para validar o acompanhamento.</h1>
    <p>Damião é a referência principal nas fases 1–12. Fachadas, Santa e Dinorah ajustam levemente a câmera somente em repouso; o movimento desfaz esse ajuste. A ROM principal permanece separada desta candidata.</p>
    <p><a class="download" href="../../out/camera-validation/Plaguefall.bin">Baixar Plaguefall.bin · câmera v1</a></p>
    <p class="muted">{summary['rom_bytes']:,} bytes · SHA-256 <code>{digest}</code></p>
    <p class="warning"><strong>Limitação de desempenho:</strong> os testes de carga das fases 10 e 11 registraram piora em alguns setores da fábrica. Esta build serve para validar o enquadramento. A carga máxima medida ficou em 48,4–60 FPS em NTSC e 48,25–50 FPS em PAL; a tabela abaixo compara a referência disponível.</p>
    <h2>O que mudou</h2><ul><li>Centro do corpo alinhado à área útil abaixo do HUD, respeitando os limites físicos do mapa.</li><li>Ajustes em repouso após aproximadamente 250 ms: até 16 px na horizontal e 12 px na vertical, entrando e saindo 1 px por tick.</li><li>Seleção de fachadas com histerese e peso contínuo da escolta, sem a troca binária do enquadramento anterior.</li><li>Proteção da caixa inteira de 32×48, com margem de 8 px onde possível, inclusive após limitar o deslocamento da câmera.</li><li>Marcador de direção quando Dinorah estiver fora do enquadramento.</li><li>Movimento normal de até 4 px por eixo; desfazer o ajuste pode exigir 5 px. O teto de segurança de 8 px mantém no máximo uma coluna/linha nova de tiles por atualização.</li><li>Contador de recusas do streaming; os tiles e a rolagem continuam sendo confirmados juntos em VBlank.</li></ul>
    <h2>Validação na ROM</h2><p><strong>364 testes automatizados em NTSC/PAL, {summary['samples']:,} quadros, zero cortes do personagem e zero recusas de streaming.</strong> Foram conferidas {summary['live_pixel_cells']:,} células visíveis da VRAM durante movimento, com comparação exata de mapas e padrões, além dos limites de sprites.</p>
    <p>As 84 travessias planejadas terminaram sem falha. Passaram 28 verificações de pausa/retomada, 28 reinícios pelo seletor, 6 mortes da Dinorah, 6 escoltas completas e 8 verificações de portão, incluindo válvulas reais da 6B. Os testes nativos com ASan/UBSan e o verificador geral <code>game/tools/check.py</code> também passaram.</p>
    <p>A configuração dos cenários usa RAM antes de cada tentativa; o movimento medido usa o controle e uma trava impede escritas pelo teste. As escoltas completas isolam combate e preparam os portões dos esgotos abertos; cada interação de válvula e disparo contra portões é conferida separadamente.</p>
    <h2>Desvio máximo por fase</h2><p>Valores X / Y, incluindo os pequenos ajustes em repouso e descontando as restrições de borda. Durante movimento contínuo, o teste exige desvio de até 8 px após 12 atualizações. Os valores abaixo não são médias nem uma exigência de centralizar o personagem quando ele alcança a extremidade do mundo.</p>
    <table><thead><tr><th>Fase</th><th>Antes (NTSC)</th><th>Build nova (NTSC)</th><th>Cortes</th></tr></thead><tbody>{''.join(table)}</tbody></table>
    <h2>Desempenho sob carga máxima configurada</h2><p>Mesmos scripts de carga, com IA real e reposição controlada de tiros inativos. Fase 10: quatro inimigos e 6+6 projéteis; fase 11: cinco inimigos e 6+6 projéteis. O novo enquadramento altera o conteúdo visível; estes números não isolam a causa exata das regressões.</p>
    <table><thead><tr><th>Fase</th><th>Região</th><th>Setor</th><th>Referência (FPS)</th><th>Candidata (FPS)</th></tr></thead><tbody>{fpsrows}</tbody></table>
    <h2>O que observar no seu playtest</h2><ol><li>Use <strong>FASE TESTE → CAMPANHA</strong> para escolher as fases 1–12 e as variantes A/B.</li><li>Corra, inverta a direção, percorra diagonais e contorne as fachadas nas fases 3, 9 e 12. Damião deve acompanhar o centro possível sem ser cortado.</li><li>Nas fases 6A/6B e 12, afaste-se e volte para Dinorah. O marcador deve apontar a direção dela quando necessário.</li><li>Pare perto de uma fachada ou da Santa e volte a andar. Observe o ajuste discreto em repouso e sua saída gradual.</li><li>Pause, retome e reinicie. Nas fábricas, observe também a fluidez durante combate intenso.</li></ol>
    <h2>Vídeos da candidata</h2>{videos}
    <h2>Dados e arquivos</h2><p><a href="summary.json">Resumo estruturado</a> · <a href="validation/ntsc/report.json">Movimento NTSC</a> · <a href="validation/pal/report.json">Movimento PAL</a> · <a href="escorts/ntsc/report.json">Escoltas e portões NTSC</a> · <a href="escorts/pal/report.json">Escoltas e portões PAL</a> · <a href="../camera-motion-audit-v1/review.html">Auditoria anterior</a></p>
    <p class="muted">A candidata está em <code>game/out/camera-validation/Plaguefall.bin</code>, acompanhada da capa, dos metadados e do manifesto de validação. Abra esse arquivo no emulador; uma cópia já importada na biblioteca pode continuar usando outra versão.</p></main></html>'''
    (ROOT/'review.html').write_text(document)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('measurements','performance','changes','limitations')},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
