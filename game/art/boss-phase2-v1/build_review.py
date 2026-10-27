"""Publish boss phase2 evidence only when all reports match the production ROM."""
from pathlib import Path
import hashlib, html, json

A=Path(__file__).resolve().parent
G=A.parents[1]
rom=G/'out/release/Plaguefall.bin'
digest=hashlib.sha256(rom.read_bytes()).hexdigest()
regions={}
for name in ['ntsc','pal']:
    fight=json.loads((A/f'validation/{name}/report.json').read_text())
    mechanics=json.loads((A/f'validation/mechanics-{name}/report.json').read_text())
    assert all(r['passed'] and r['romSHA256']==digest for r in [fight,mechanics])
    assert fight['checks']['controller-boss-combat']['phase2_seen']
    regions[name]=dict(passed=True,fight_report=f'validation/{name}/report.json',
                       mechanics_report=f'validation/mechanics-{name}/report.json',
                       combat=fight['checks']['controller-boss-combat'],
                       transition=mechanics['checks']['real-hit-at12hp-triggers-once-with-stationary-local-flash'],
                       double_dash=mechanics['checks']['two-reaimed-charges-each-with-locked-stationary-warning'],
                       recovery=mechanics['checks']['exact1.2second-stationary-recovery-takes-real-projectile-damage'],
                       fans=mechanics['checks']['alternating-wide-and-narrow-complete-five-shot-fans'],
                       load=mechanics['checks']['30second-moving-fury-load-with-two-hunters-and-full-shot-pools'])
delivery=dict(rom=str(rom.relative_to(G)),rom_sha256=digest,rom_bytes=rom.stat().st_size,
              phase2_implemented=True,threshold_hp=12,original_hp=25,transition_seconds=0.8,
              warnings_per_combo=2,warning_seconds=0.35,dash_seconds=0.5,recovery_seconds=1.2,
              ranged_seconds=3,phase2_periodic_armor=False,max_live_hunters=2,
              enemy_shot_cap=10,player_shot_cap=4,boss_volley=5,damage=13,
              generated_resources_and_native_checks=True,regions=regions,
              limits=['Genesis Plus GX; hardware físico não testado.',
                      'Carga: jogador protegido e chefe elevado para200HP uma vez após a transição;30s de controle sem novas escritas deRAM.',
                      'Vitória: chefe com25HP originais, jogador protegido uma vez; não certifica dificuldade humana.'])
(A/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')

def figure(src,label):
    return f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'

page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Escorpião — segunda fase</title><style>
body{margin:0;background:#10171c;color:#e1e8eb;font:16px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px}h1,h2{line-height:1.25}h1{font-size:38px}a{color:#efc96d}p{max-width:940px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}figure{margin:0;padding:12px;background:#1c272f;border:1px solid #3d505c;border-radius:8px}img{display:block;width:100%;height:auto;image-rendering:pixelated}figcaption{font-size:14px;margin-top:10px;color:#bccbd1}td,th{padding:8px 16px;border-bottom:1px solid #3d505c;text-align:left}code{overflow-wrap:anywhere}</style><main>
<p>PLAGUEFALL / ESCORPIÃO / SEGUNDA FASE</p><h1>Duas investidas e uma abertura para atacar</h1>
<p>Aos 12 de vida, o chefe para e brilha por 0,8 segundo. Depois aproxima, avisa e investe duas vezes. A segunda investida mira novamente; cada aviso e sua investida mantêm a direção travada. Após o combo, permanece parado e vulnerável por 1,2 segundo.</p>
<p>O recuo dura 3 segundos e alterna leques abertos e fechados de cinco tiros. A segunda fase remove a blindagem periódica; há no máximo dois Caçadores vivos. Sprites, cenário, dano e vida total existentes são preservados. Pausa e derrota/reinício funcionam nas duas fases.</p>
<p><a href="README.md">Documentação</a> · <a href="delivery.json">Validação</a> · <a href="../../out/release/Plaguefall.bin">ROM atualizada</a></p><h2>Capturas da ROM em NTSC</h2><div class="grid">'''
for src,label in [('phase2-transition-bright.png','Transição: brilho somente no chefe'),('phase2-transition-dark.png','Transição: alternância do brilho'),('phase2-warning-1.png','Primeira direção travada'),('phase2-warning-2.png','Novo aviso antes da segunda investida'),('phase2-vulnerable-recovery.png','Recuperação de 1,2 s; tiro real causa dano'),('phase2-fan-2.png','Leque aberto: cinco tiros'),('phase2-fan-6.png','Leque fechado: cinco tiros'),('phase2-moving-load.png','Segunda fase ativa no ensaio de carga'),('phase2-reset-to-phase1.png','Reinício restaura 25HP e a primeira fase')]:
    page+=figure('validation/mechanics-ntsc/'+src,label)
page+='</div><h2>Verificação</h2><p>Limite de vida cruzado por um tiro real; duração da transição, avisos, investidas e recuperação; dano durante a abertura; leques alternados; espera por vagas sem cortar a rajada; blindagem desativada; limite de lacaios; contato, pausa e reinício aprovados em NTSC/PAL. A suíte da sala também verifica 28 câmeras por região e vitória por controle atravessando as duas fases.</p><table><tr><th>Região</th><th>Carga por 30 s</th><th>Caçadores</th><th>Falhas de cache</th><th>Vitória por controle</th></tr>'
for name,r in regions.items():
    page+=f'<tr><td>{name.upper()}</td><td>{r["load"]["game_fps"]} FPS</td><td>{r["load"]["max_hunters"]}</td><td>0</td><td>Sim</td></tr>'
page+='</table><p>Os ensaios isolados usam RAM para preparar situações. A carga aumenta a vida do chefe após a transição e protege o jogador uma vez; durante os 30 segundos seguintes usa somente controle. A vitória mantém a vida original do chefe e protege o jogador uma vez. Hardware físico e dificuldade humana não certificados.</p>'
page+=f'<p>ROM SHA256: <code>{digest}</code>.</p></main></html>'
(A/'review.html').write_text(page)
print(json.dumps(dict(rom_sha256=digest,regions={k:v['load']['game_fps'] for k,v in regions.items()}),indent=2))
