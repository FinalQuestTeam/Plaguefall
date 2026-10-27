"""Publish v2 evidence for the stationary-camera regression."""
from pathlib import Path
import hashlib
import json

GAME=Path(__file__).resolve().parents[1]
ROOT=GAME/'art/camera-follow-v2'
BUILD=GAME/'out/camera-validation-v2'


def main():
    digest=hashlib.sha256((BUILD/'Plaguefall.bin').read_bytes()).hexdigest()
    baseline=json.loads((ROOT/'before/ntsc/report.json').read_text())
    assert not baseline['passed'],'The v1 regression must reproduce before calling this a fix'
    motion=[];idle=[];escorts=[];phases=[]
    for region in ('ntsc','pal'):
        r=json.loads((ROOT/'validation'/region/'report.json').read_text())
        assert r['passed'] and r['romSHA256']==digest and len(r['stages'])==14
        for stage in r['stages']:
            assert len(stage['trials'])==13 and stage['pause_resume']['passed'] and stage['selector_restart']['passed']
            for trial in stage['trials']:
                assert trial['max_error_x']==0 and trial['max_error_y']==0 and trial['clipped_samples']==0
                if trial['trial'].startswith('traverse'):assert not trial['navigation_failures'] and trial['remaining_corners']==0
            motion.extend(stage['trials'])
            phases.append(dict(region=region,phase=stage['phase'],max_error=[0,0],clipped_samples=0))
        r=json.loads((ROOT/'idle'/region/'report.json').read_text())
        assert r['passed'] and r['romSHA256']==digest
        for name,result in r['checks'].items():
            assert result['passed'] and result['camera_range']==[0,0] and result['max_center_error']==0
            idle.append(dict(region=region,name=name,**result))
        r=json.loads((ROOT/'escorts'/region/'report.json').read_text())
        assert r['passed'] and r['romSHA256']==digest
        escorts.append(dict(region=region,checks=r['checks']))
    summary=dict(title='Plaguefall — câmera estável v2',rom_sha256=digest,
        rom_bytes=(BUILD/'Plaguefall.bin').stat().st_size,motion_trials=len(motion),
        stationary_trials=len(idle),motion_samples=sum(t['samples'] for t in motion),
        live_pixel_cells=sum(t['live_pixel_cells'] for t in motion)+sum(t['live_pixel_cells'] for t in idle),
        clipped_samples=0,max_center_error=0,stationary_camera_range=[0,0],
        stream_deferrals=sum(t['stream_deferrals'] for t in motion),
        full_escorts=6,gate_checks=8,
        baseline_rom_sha256=baseline['romSHA256'],
        changes=['Remove all idle landmark/Santa/escort composition in stages1–12 and their A/B variants',
                 'Stateless target depends only on player body position and map bounds',
                 'Restore4px per-axis camera limit; no delayed bias to unwind',
                 'Retain full-body safety, HUD clearance, offscreen escort marker and atomic VBlank streaming'],
        limitations=['Factory maximum-load FPS fromv1 has not been rebenchmarked forv2; this change does not claim to fix that issue.',
                     'Test scenarios isolate enemies and prepare protection before guarded controller trials. Full sewer escorts seed gates open; actual gate/valve interactions are checked separately.'],
        phases=phases,stationary_checks=idle,escort_checks=escorts)
    (ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (BUILD/'camera-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    before_rows=[]
    for label in ('3','5','6A','6B','9','12'):
        checks=[v for name,v in baseline['checks'].items() if name.startswith(label+'-')]
        old_range=[max(v['camera_range'][axis] for v in checks) for axis in (0,1)]
        old_error=max(v['max_center_error'] for v in checks)
        before_rows.append(f'<tr><td>{label}</td><td>{old_range[0]} / {old_range[1]} px</td><td>{old_error} px</td><td>0 / 0 px</td><td>0 px</td></tr>')
    page=f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaguefall — câmera estável v2</title>
    <style>body{{margin:0;background:#0d1724;color:#e8eff6;font:17px/1.65 system-ui}}main{{max-width:1000px;margin:auto;padding:44px 24px}}h1{{line-height:1.2;font-size:36px}}h2{{margin-top:40px;color:#adddff}}a{{color:#91d6ff}}.button{{display:inline-block;padding:14px 20px;border-radius:8px;background:#b2e4ff;color:#0d1724;text-decoration:none;font-weight:bold}}table{{border-collapse:collapse;width:100%;font-size:15px}}td,th{{padding:11px;text-align:left;border-bottom:1px solid #36495c}}code{{overflow-wrap:anywhere;background:#182b40;padding:3px}}li{{margin:10px 0}}.note{{border-left:4px solid #d4a96a;padding:14px;background:#2b261e}}.muted{{font-size:14px;color:#a6b8ca}}</style>
    <main><p class="muted">PLAGUEFALL · Câmera v2 · 26/10/2026</p><h1>Câmera estável quando Damião está parado.</h1>
    <p>Removi o reenquadramento automático de fachadas, Santa e Dinorah. Nas fases 1–12, a câmera agora depende apenas da posição do corpo de Damião e dos limites do mapa. Esperar, entrar na fase, aproximar-se de um prédio ou ver Dinorah se mover não inicia um segundo deslocamento.</p>
    <p><a class="button" href="../../out/camera-validation-v2/Plaguefall.bin">Baixar Plaguefall.bin · câmera v2</a></p>
    <p class="muted">{summary['rom_bytes']:,} bytes · SHA-256 <code>{digest}</code></p>
    <h2>Causa corrigida</h2><p>A v1 aplicava um ajuste de composição após aproximadamente 250 ms parado. Ele podia deslocar o enquadramento até 16 px na horizontal e 12 px na vertical. A validação anterior aceitava esse desvio, mas ele produziu as correções estranhas relatadas. A v2 remove o temporizador e o estado desse ajuste, mantendo o teto de 4 px por eixo durante movimento.</p>
    <h2>Reprodução e comparação</h2><p>O novo teste falha na ROM v1 e passa na v2. Confere cinco segundos de entrada, parada após movimento e retomada da pausa, além de espera junto a fachadas. Na fase 9, a correção foi reproduzida junto à fachada; não apareceu no ponto exato de nascimento usado pelo teste.</p>
    <table><thead><tr><th>Fase</th><th>Variação da câmera v1 X/Y</th><th>Desvio v1</th><th>Variação v2 X/Y</th><th>Desvio v2</th></tr></thead><tbody>{''.join(before_rows)}</tbody></table>
    <p class="muted">A variação mede movimento durante a espera. O desvio mede distância ao centro possível do personagem. Uma câmera já deslocada pode ter variação zero e ainda estar enquadrando incorretamente. A comparação v1 cobre as seis fases relatadas em NTSC; a v2 cobre todas as 14 variantes em NTSC e PAL.</p>
    <h2>Validação da v2</h2><ul><li><strong>{len(idle)} testes de estabilidade:</strong> câmera sem deslocamento em repouso e sem desvio corrigível, incluindo escolta realmente se movendo.</li><li><strong>{len(motion)} testes de movimento:</strong> fases 1–12 e variantes A/B em NTSC/PAL, com velocidades normal, +60% e +100%, reversões, diagonais e combate. {summary['motion_samples']:,} quadros; zero cortes e desvio zero em todos os quadros medidos, respeitando as bordas do mundo.</li><li><strong>{summary['live_pixel_cells']:,} células da VRAM</strong> comparadas durante os testes de movimento e estabilidade; zero recusas de streaming.</li><li>Pausa, reinício, morte de Dinorah, seis escoltas completas e oito verificações de portão/valvulas passaram nas duas regiões.</li><li>Testes nativos com ASan/UBSan e <code>game/tools/check.py</code> passaram.</li></ul>
    <p>Continuam ativos a proteção da caixa inteira do personagem, o espaço do HUD, o indicador de Dinorah fora do enquadramento e a confirmação conjunta de tiles e rolagem em VBlank.</p>
    <p class="note">A carga máxima da fábrica não foi medida novamente nesta revisão. A v2 não declara resolvidas as quedas de FPS registradas na v1.</p>
    <h2>Arquivo certo para validar</h2><p>Abra a nova ROM em <code>game/out/camera-validation-v2/Plaguefall.bin</code>. Uma cópia já importada no emulador pode continuar usando a v1. Valide especialmente a entrada das fases 3, 5, 6A, 6B, 9 e 12, depois de soltar o direcional e ao retomar a pausa.</p>
    <h2>Relatórios</h2><p><a href="summary.json">Resumo</a> · <a href="before/ntsc/report.json">Reprodução na v1</a> · <a href="idle/ntsc/report.json">Estabilidade NTSC</a> · <a href="idle/pal/report.json">Estabilidade PAL</a> · <a href="validation/ntsc/report.json">Movimento NTSC</a> · <a href="validation/pal/report.json">Movimento PAL</a> · <a href="escorts/ntsc/report.json">Escoltas NTSC</a> · <a href="escorts/pal/report.json">Escoltas PAL</a></p></main></html>'''
    (ROOT/'review.html').write_text(page)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('phases','stationary_checks','escort_checks','changes','limitations')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
