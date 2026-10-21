"""Publish actual production-ROM captures, keeping the approved mockup as reference."""
from pathlib import Path
import html,json
ROOT=Path(__file__).resolve().parent

def main():
 data=json.loads((ROOT/'copy.json').read_text())['cases']
 report=json.loads((ROOT/'build-validation.json').read_text())
 assert report['passed']
 options=''.join('<option value="%d">%s → %s</option>'%(i,html.escape(c['current']),html.escape(c['next'])) for i,c in enumerate(data))
 page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaguefall — rodapé implementado</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#101719;color:#f2dfc0;font:16px/1.5 system-ui,sans-serif}main{max-width:1220px;margin:auto;padding:24px}.tag{font-size:12px;color:#ffbf57;letter-spacing:.1em}h1{font-size:30px;line-height:1.2;margin:8px 0 10px}p{color:#bec3b5;margin:8px 0}a{color:#ffbf57}nav{display:flex;gap:24px;align-items:end;flex-wrap:wrap;margin:20px 0}label{display:grid;gap:4px;font-size:13px;color:#bec3b5}select{font:16px system-ui;background:#202c2f;color:#f2dfc0;border:1px solid #586366;padding:8px 12px;border-radius:5px;min-width:190px}.frames{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}figcaption{font-size:14px;color:#ffbf57;margin-bottom:8px}img{display:block;width:100%;height:auto;image-rendering:pixelated;border:1px solid #475256}.checks{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}.checks span{padding:4px 10px;border:1px solid #415e4c;border-radius:20px;color:#b4d0ac;font-size:12px}footer{border-top:1px solid #354347;padding-top:14px;font-size:13px}code{overflow-wrap:anywhere;font-size:11px}@media(max-width:700px){main{padding:18px}.frames{grid-template-columns:1fr}h1{font-size:25px}nav{gap:12px}}</style>
<main><div class="tag">PLAGUEFALL / IMPLEMENTADO NA ROM</div><h1>Rodapé aprovado, agora no jogo.</h1><p>Nome da fase e explicações centralizados. Comandos à direita, com margem de 8 px. Capturas reais da ROM em 320 × 224.</p>
<nav><label>Transição<select id="route">'''+options+'''</select></label><label>Sistema<select id="system"><option value="ntsc">NTSC · 60 Hz</option><option value="pal">PAL · 50 Hz</option></select></label><a href="@ROM@" download>Baixar ROM atualizada</a></nav>
<div class="frames"><figure><figcaption>Antes de seguir</figcaption><img id="ready" src="@BASE@validation/ntsc/map-9-10A.png" alt="ROM: texto centralizado e comando de seguir à direita"></figure><figure><figcaption>Durante a viagem</figcaption><img id="travel" src="@BASE@validation/ntsc/travel-9-10A.png" alt="ROM: comando de pular viagem à direita"></figure></div>
<div class="checks"><span>23 transições por sistema</span><span>8 resultados de bifurcação</span><span>2 campanhas completas por sistema</span><span>Conteúdo, alinhamento e paletas verificados</span></div>
<footer><a href="@BASE@build-validation.json">Relatório da implementação</a> · <a href="@PROPOSAL@">Proposta visual aprovada</a><p>Genesis Plus GX em NTSC/PAL. Preparação das fases e resultados acelerada por RAM; mapa, viagem e saída verificados somente com controles. Sem teste em hardware físico ou CRT.<br>SHA-256: <code>'''+report['rom_sha256']+'''</code></p></footer></main>
<script>const cases='''+json.dumps(data)+''';const route=document.getElementById('route'),system=document.getElementById('system');function update(){const c=cases[+route.value],base='@BASE@validation/'+system.value+'/';document.getElementById('ready').src=base+'map-'+c.current+'-'+c.next+'.png';document.getElementById('travel').src=base+'travel-'+c.current+'-'+c.next+'.png';for(const id of ['ready','travel'])document.getElementById(id).alt='Captura da ROM '+system.value.toUpperCase()+': '+c.current+' → '+c.next+' — '+(id==='ready'?'antes de seguir':'durante a viagem');}route.addEventListener('change',update);system.addEventListener('change',update);</script></html>'''
 for path,base,rom,proposal in [(ROOT/'revisao.html','','../../../out/release/Plaguefall.bin','../proposta-aprovada.html'),(ROOT.parent/'revisao.html','integracao/','../../out/release/Plaguefall.bin','proposta-aprovada.html')]:
  path.write_text(page.replace('@BASE@',base).replace('@ROM@',rom).replace('@PROPOSAL@',proposal))
 print('Actual-ROM review published with all 23 transitions in NTSC/PAL.')

if __name__=='__main__':main()
