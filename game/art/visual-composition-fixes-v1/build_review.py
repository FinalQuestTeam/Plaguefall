"""Publish human composition judgments beside native maps and emulator evidence."""
from pathlib import Path
import json, html

HERE = Path(__file__).resolve().parent
ART = HERE.parent
baseline = json.loads((ART/'visual-composition-audit-v1/report.json').read_text())
targets = [v for v in baseline['variants'] if v['status'] in ('ajustes', 'reprovada')]
report_path = HERE/'report.json'
report = json.loads(report_path.read_text()) if report_path.exists() else {'complete':False,'phases':[]}
if report.get('superseded_by'):
    destination=html.escape(report['superseded_by'],quote=True)
    (HERE/'review.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisão substituída · composição visual</title><style>body{background:#11191d;color:#e5ecec;font:18px/1.6 system-ui;margin:48px auto;padding:24px;max-width:1000px}a{color:#a7d5e9}.notice{border-left:4px solid #ef817d;padding:20px;background:#30282b}</style><h1>A revisão integral substituiu este parecer.</h1><p class="notice">As aprovações visuais deste painel foram retiradas. A nova avaliação inclui todas as19variações:3aceitáveis nesta revisão,6precisam de ajustes e10reprovadas.</p><p><a href="'''+destination+'''">Abrir todos os cenários completos e pareceres atuais →</a></p><p><a href="review-before-integral-audit.html">Consultar histórico marcado como substituído</a></p></html>'''.replace('as19variações:3aceitáveis','as 19 variações: 3 aceitáveis').replace(',6precisam',', 6 precisam').replace('e10reprovadas','e 10 reprovadas'))
    print('Review superseded by integral campaign audit.')
    raise SystemExit(0)
reviews = {r['phase']:r for r in report['phases']}
escape = html.escape

def figure(path, caption, cls=''):
    return f'<figure class="{cls}"><a href="{escape(path)}" target="_blank"><img loading="lazy" src="{escape(path)}" alt="{escape(caption)}"></a><figcaption>{escape(caption)}</figcaption></figure>'

cards = []
for base in targets:
    phase = base['phase']
    r = reviews.get(phase, {})
    status = r.get('status_label', 'Correção e revisão em andamento')
    before = '../visual-composition-audit-v1/'+base['frames'][0]['path']
    content = figure(before, 'Antes · captura da ROM auditada')
    for frame in r.get('frames', [])[:3]:
        content += figure(frame['path'], frame['label'])
    detail = ''.join(f'<li>{escape(x)}</li>' for x in r.get('changes', []))
    observations = ''.join(f'<li>{escape(x)}</li>' for x in r.get('review', []))
    history = ''.join(f'<tr><td>{c["cycle"]}</td><td>{escape(c["verdict"])}</td><td>{escape(c["finding"])}</td></tr>' for c in r.get('cycles', []))
    resources = ''
    for key, label in [('source', 'Imagem completa de referência'), ('native', 'Mapa nativo completo'), ('movie', 'Abrir vídeo do playtest'), ('test_report', 'Relatório técnico')]:
        if r.get(key): resources += f'<a href="{escape(r[key])}" target="_blank">{label} ↗</a>'
    video = f'<video controls preload="none" poster="{escape(r["frames"][0]["path"])}" src="{escape(r["movie"])}"></video>' if r.get('movie') and r.get('frames') else ''
    cards.append(f'''<article id="p{phase}" data-status="{escape(r.get('status','pending'))}">
      <div class="title"><div><small>{escape(base['goal'])}</small><h2>{phase} · {escape(base['name'])}</h2></div><span class="badge">{escape(status)}</span></div>
      <div class="comparison">{content}</div>
      <div class="notes"><div><h3>Correção</h3><ul>{detail or '<li>Grupo trabalhando nas correções identificadas.</li>'}</ul></div><div><h3>Revisão de composição</h3><ul>{observations or '<li>Aguardando capturas da versão corrigida; sem aprovação antecipada.</li>'}</ul></div></div>
      <div class="links">{resources}</div>{video}
      {f'<details><summary>Histórico dos ciclos</summary><table><thead><tr><th>Ciclo</th><th>Decisão</th><th>Motivo</th></tr></thead><tbody>{history}</tbody></table></details>' if history else ''}
    </article>''')

accepted = sum(r.get('status') == 'accepted' for r in reviews.values())
nav = ''.join(f'<a href="#p{v["phase"]}">{v["phase"]}</a>' for v in targets)
summary = escape(report.get('summary', 'Correções em paralelo; cada solução passa por revisão do mapa nativo e do enquadramento real. Limite de três ciclos por fase.'))
sha = report.get('rom_sha256', '')
page = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Plaguefall · Correções de composição visual</title>
<style>
:root{color-scheme:dark;--bg:#111917;--panel:#1c2723;--line:#39473e;--ink:#e7ebdc;--muted:#aab6a6;--accent:#d9b554}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:38px 28px}h1{font-size:clamp(30px,4vw,54px);line-height:1.1;margin:14px 0 24px;max-width:1000px}h2{font-size:27px;line-height:1.15;margin:4px 0}h3{font-size:16px;color:var(--accent);margin:0 0 8px}small,figcaption{color:var(--muted)}a{color:#e3c77c}nav{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0 30px}nav a{border:1px solid var(--line);border-radius:4px;padding:7px 16px;text-decoration:none}article{scroll-margin-top:22px;border:1px solid var(--line);background:var(--panel);padding:24px;margin:28px 0;border-radius:8px}.title{display:flex;gap:20px;align-items:center;justify-content:space-between;margin-bottom:24px}.badge{padding:8px 12px;background:#3c3828;color:#efd795;border-radius:4px;font-size:13px;max-width:280px}article[data-status=accepted] .badge{background:#284437;color:#bee1bd}article[data-status=rejected] .badge{background:#63302c;color:#ffd0b8}figure{margin:0;min-width:0}img{width:100%;display:block;image-rendering:pixelated;background:#070d0b}figcaption{font-size:12px;padding:7px 0 4px}.comparison{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}.notes{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:24px}ul{margin:0;padding-left:20px}li{margin:6px 0}.links{display:flex;gap:20px;flex-wrap:wrap;margin:22px 0}video{width:min(100%,640px);display:block;image-rendering:pixelated;margin:20px 0}details{border-top:1px solid var(--line);padding-top:15px;margin-top:20px}summary{cursor:pointer;color:#d8dfd0}table{width:100%;border-collapse:collapse;font-size:14px;margin-top:16px}td,th{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}.intro{max-width:1000px;color:#c1cabc}.provenance{font:12px/1.6 ui-monospace,monospace;overflow-wrap:anywhere;color:var(--muted)}.objects{margin-top:40px;border:1px solid var(--line);padding:24px;background:var(--panel)}.objects img{width:min(100%,852px)}@media(max-width:750px){main{padding:24px 14px}.comparison,.notes{grid-template-columns:1fr}article{padding:16px}.title{align-items:flex-start;flex-direction:column}}
</style><main>'''
page += f'''<small>PLAGUEFALL / REVISÃO DE ARTE NO JOGO</small><h1>Correções de composição visual</h1><p class="intro">{summary}</p><p><b>{accepted} / 13</b> variações aceitáveis nesta revisão manual · até três ciclos de correção.</p><p class="intro">Comparação entre a versão auditada e capturas reais da versão corrigida. Testes técnicos e julgamento visual são apresentados separadamente. As fases 1, 2A, 2B, 5, 13A e 16 são referências preservadas.</p>'''
if sha: page += f'<p class="provenance">ROM verificada: {escape(sha)}</p>'
page += '<p><a href="../../out/playtest/Plaguefall.bin">ROM para playtest ↗</a> · <a href="../../out/release/Plaguefall.bin">ROM da campanha ↗</a> · <a href="README.md">Resultados e controles ↗</a> · <a href="report.json">Pareceres completos ↗</a></p>'
page += f'<nav>{nav}</nav>'+''.join(cards)
page += '<section class="objects"><h2>Objetivos com silhuetas claras</h2><p>Equipamentos e recursos usam formas amplas e cores diferentes dos insetos. Os estados de operação mantêm a mesma silhueta.</p>'
page += figure('objectives/final-atlas.png', 'Objetivos da campanha após conversão para a paleta real do jogo')
page += '<p><a href="objectives/prompts.json">Prompts e método de produção ↗</a> · <a href="../visual-composition-audit-v1/review.html">Auditoria original ↗</a></p></section></main></html>'
(HERE/'review.html').write_text(page)
print(f'Composition review published: {accepted}/13 acceptable; complete={report.get("complete",False)}')
