"""Publish the phase1-only composition pilot and its reusable workflow."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html,hashlib,re
A=Path(__file__).resolve().parent;G=A.parents[1]
load=lambda path:json.loads((A/path).read_text())
m=load('manifest.json');workflow=load('workflow.json');rom=load('rom/manifest.json')
checks={r:load(f'captures/{r}/capture-report.json') for r in ('ntsc','pal')}
assert all(d['rom_sha256']==rom['prototype_rom_sha256'] for d in checks.values())
assert all(d['validation']['collision_probes_passed']==20 for d in checks.values())
assert all(d['validation']['vram_graphic_bytes_verified']==m['memory']['graphic_bytes'] for d in checks.values())
assert hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()==m['production_rom_sha256']
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',15)
large=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',22)
colors={'upper':'#84cbe3','lower':'#edbd71','sides':'#beb0e6','field':'#f28f94'}
labels={'upper':'Área superior','lower':'Área inferior','sides':'Limitadores laterais','field':'Elementos do campo'}

# Diagram and sprite boards are explanatory copies, never inputs to the ROM.
im=Image.open(A/'complete-native.png').convert('RGB');im.resize((1536,1152),Image.Resampling.NEAREST).save(A/'complete-3x.png')
diagram=Image.new('RGB',(1136,962),'#111a20');d=ImageDraw.Draw(diagram)
d.text((40,18),'SEU PADRÃO → FASE1 ·512×384',font=large,fill='white')
base=im.resize((1024,768),Image.Resampling.NEAREST);diagram.paste(base,(56,104))
def box(rect,color):
    x,y,w,h=rect;d.rectangle((56+x*2,104+y*2,56+(x+w)*2-1,104+(y+h)*2-1),outline=color,width=4)
box((0,0,512,112),colors['upper']);box((0,352,512,32),colors['lower'])
for x in (0,496):box((x,112,16,240),colors['sides'])
for x,y,w,h,*_ in m['solids']:box((x,y,w,h),colors['field'])
for i,(key,label) in enumerate(labels.items()):
    x=56+(i%2)*520;y=62 if i<2 else 900
    d.rectangle((x,y+3,x+13,y+16),fill=colors[key]);d.text((x+23,y),label,font=large,fill=colors[key])
diagram.save(A/'pattern-applied.png')
atlas=Image.new('RGB',(1200,((len(m['modules'])+3)//4)*250+72),'#111a20');d=ImageDraw.Draw(atlas)
d.text((20,16),'MÓDULOS COMPLETOS · materiais repetíveis e peças singulares',font=large,fill='white')
for i,mod in enumerate(m['modules']):
    x=i%4*300;y=i//4*250+64
    d.rounded_rectangle((x+7,y+4,x+292,y+240),radius=8,outline='#3b505a',fill='#202d34')
    d.text((x+18,y+14),mod['id'],font=font,fill=colors[mod['region']]);d.text((x+18,y+38),f"{mod['size'][0]}×{mod['size'][1]} ·{mod['repeat']}",font=font,fill='#a8b9c0')
    sprite=Image.open(A/mod['path']).convert('RGBA');scale=min(2,260/sprite.width,150/sprite.height)
    sprite=sprite.resize((round(sprite.width*scale),round(sprite.height*scale)),Image.Resampling.NEAREST)
    atlas.paste(sprite,(x+18,y+76),sprite)
atlas.save(A/'module-atlas.png')

camera_boards={}
for region,report in checks.items():
    board=Image.new('RGB',(984,3*264+64),'#111a20');d=ImageDraw.Draw(board)
    d.text((12,12),f'FASE1 · CÂMERA REAL ·{region.upper()} ·320×224',font=large,fill='white')
    for s in report['phases'][0]['samples']:
        x=s['col']*328;y=64+s['row']*264
        d.text((x+4,y),f"{s['label']} ·{tuple(s['camera'])}",font=font,fill='#bdcbd0')
        board.paste(Image.open(A/'captures'/region/s['path']),(x,y+28))
    board.save(A/f'camera-board-{region}.png');camera_boards[region]=f'camera-board-{region}.png'

# Enlargement of real corners and full silhouettes helps spot slicing errors.
detail=Image.new('RGB',(1136,530),'#111a20');d=ImageDraw.Draw(detail)
for i,(label,rect) in enumerate([('Junção inferior esquerda',(0,328,64,384)),('Junção inferior direita',(448,328,512,384)),('Banco inteiro',(120,168,208,224)),('Barris inteiros',(336,200,392,256))]):
    x=i*284;d.text((x+8,14),label,font=font,fill='white');crop=im.crop(rect);scale=min(268/crop.width,410/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST);detail.paste(crop,(x+8,70))
detail.save(A/'junctions-and-props.png')
review={
 'status':'candidate_for_user_review','scope':'Fase1; expansão para a campanha depende da avaliação deste protótipo.',
 'production_rom_changed':False,'production_rom_sha256':m['production_rom_sha256'],'prototype_rom_sha256':rom['prototype_rom_sha256'],
 'visual_decision':'Pronto para avaliação do usuário, sem aprovação automática.',
 'applied_pattern':[
  {'region':'Área superior','result':'Igreja inteira e portão de evacuação mantêm a identidade da primeira fase. Materiais de muro e vegetação se repetem no restante da faixa.'},
  {'region':'Área inferior','result':'Muro próprio de primeiro plano com coroamento, dois pilares e dois cantos que fecham as laterais.'},
  {'region':'Limitadores laterais','result':'Paredes contínuas com materiais compatíveis, conectadas ao limite inferior; os módulos esquerdo e direito conservam sua iluminação própria.'},
  {'region':'Elementos do campo','result':'Dois bancos e dois pares de barris, extraídos inteiros. As posições deixam a passagem central e os contornos conectados.'}
 ],
 'native_art_review':[
  'Os quatro setores existem no cenário completo; cada elemento de campo tem silhueta e apoio visíveis.',
  'A igreja é reutilizada inteira, sem combinar telhado e fachadas de construções diferentes.',
  'As peças inferiores foram extraídas da parede completa da nova cena, incluindo seu coroamento e cantos.',
  'O piso nativo é mais discreto que o da imagem de desenho, para reduzir textura repetida e manter leitura de personagens.',
  'A vegetação superior tem repetição perceptível na resolução nativa. É material de fundo; não é uma sequência de edifícios ou objetos truncados.'
 ],
 'technical':{region:dict(camera_samples=len(v['phases'][0]['samples']),collision_probes=v['validation']['collision_probes_passed'],vram_bytes=v['validation']['vram_graphic_bytes_verified'],damage=v['validation']['church_damage_triggered']) for region,v in checks.items()},
 'memory':m['memory'],'geometry':m['geometry'],
 'limits':[
  '512×384 é o tamanho do mundo; o jogo mostra320×224 por vez. Todas as quatro bordas não aparecem simultaneamente durante a movimentação.',
  '638de640tiles deixam apenas2tiles livres. O repertório deste piloto está fechado; adicionar mais desenhos exige reaproveitamento ou revisão do orçamento.',
  'As caixas físicas dos objetos baixos cobrem conservadoramente a silhueta completa, em grade8×8. É a escolha deste piloto para impedir passagem por dentro da arte sem adicionar oclusão dinâmica.',
  'Os testes usam RAM para preparar posições e suspender combate. Não são uma vitória humana nem uma nova calibração da dificuldade.',
  'A ROM é um protótipo isolado com dados substituídos e tabela própria de obstáculos. Somente a fase1foi validada; outras fases dessa cópia podem usar recursos da igreja compartilhados.',
  'Nada foi integrado à campanha de produção. A avaliação visual do usuário precede a extensão do padrão.'
 ]}
(A/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
esc=html.escape
def clean(s):
    return re.sub(r'(?<=\d)(?=[a-zà-ž])',' ',re.sub(r'(?<=[a-zà-ž])(?=\d)',' ',s))
steps=''.join(f'<li><b>{s["step"]:02d}</b><div><h3>{esc(s["title"])}</h3><p>{esc(clean(s["deliverable"]))}</p></div></li>' for s in workflow['steps'])
rules=''.join('<li>'+esc(clean(x))+'</li>' for x in workflow['repeat_rules'])
acceptance=''.join('<li>'+esc(clean(x))+'</li>' for x in workflow['acceptance'])
applied=''.join(f'<div><h3>{r["region"]}</h3><p>{esc(r["result"])}</p></div>' for r in review['applied_pattern'])
modules=''.join(f'<tr><td>{esc(x["id"])}</td><td>{labels[x["region"]]}</td><td>{x["size"][0]}×{x["size"][1]}</td><td>{x["repeat"]}</td></tr>' for x in m['modules'])
frames=''
for region in ('ntsc','pal'):
    cells=''.join(f'<figure><a href="captures/{region}/{s["path"]}" target="_blank"><img loading="lazy" src="captures/{region}/{s["path"]}" alt="{s["label"]}"></a><figcaption>{s["label"]} · câmera{tuple(s["camera"])}</figcaption></figure>' for s in checks[region]['phases'][0]['samples'])
    frames+=f'<details><summary>{region.upper()} ·9 enquadramentos reais +20 testes de contato</summary><div class="cameras">{cells}</div><p><a href="camera-board-{region}.png" target="_blank">Prancha das9 câmeras</a> ·<a href="captures/{region}/capture-report.json">Relatório dos testes</a> ·<a href="captures/{region}/damaged-church.png" target="_blank">Bomba e igreja danificada</a></p></details>'
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fase1 · padrão de composição</title><style>
:root{color-scheme:dark;--bg:#10191e;--panel:#1c2a31;--line:#3a4b55;--ink:#eceddf;--muted:#abb9bf;--blue:#84cbe3;--gold:#edbd71}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:44px 28px}h1{max-width:1000px;font-size:clamp(34px,4.8vw,62px);line-height:1.08;margin:18px 0 22px}h2{font-size:30px;line-height:1.15;margin:0 0 20px}h3{font-size:18px;margin:0 0 8px}p{max-width:1050px}a{color:var(--blue)}small,figcaption{color:var(--muted)}section{padding:28px;background:var(--panel);border:1px solid var(--line);border-radius:9px;margin:30px 0;scroll-margin-top:20px}nav{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}nav a{padding:7px 14px;border:1px solid var(--line);border-radius:4px;text-decoration:none}.chips{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}.chips span{border:1px solid currentColor;border-radius:4px;padding:5px 12px}.upper{color:#84cbe3}.lower{color:#edbd71}.sides{color:#beb0e6}.field{color:#f28f94}.native{background:#071015;padding:12px;border:1px solid var(--line);overflow:auto}.native img{display:block;width:100%;max-width:1024px;height:auto;margin:auto;image-rendering:pixelated}.diagram{width:100%;height:auto;max-width:1136px;display:block;margin:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid>div{border-top:2px solid var(--line);padding-top:16px}.steps{list-style:none;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:20px}.steps li{display:flex;gap:18px;padding:18px;background:#142027;border:1px solid var(--line);border-radius:6px}.steps b{font:24px ui-monospace;color:var(--gold)}.steps p{margin:6px 0;color:var(--muted);font-size:14px}figure{margin:0}figcaption{font-size:12px;padding:7px 0}.cameras{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.cameras img{width:100%;image-rendering:pixelated;display:block}.notice{border-left:4px solid var(--gold);padding:14px 20px;background:#30322d}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0}.metrics>div{padding:16px;background:#15232a;border:1px solid var(--line)}.metrics strong{font-size:30px;color:var(--gold);display:block}.metrics span{color:var(--muted);font-size:13px}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid var(--line);text-align:left;padding:9px}details{border-top:1px solid var(--line);padding:16px 0}summary{color:var(--blue);cursor:pointer;margin-bottom:12px}button,select{font:inherit;background:#304652;border:1px solid #668393;border-radius:4px;padding:8px 14px;color:white;cursor:pointer}.links{font-size:14px;display:flex;gap:18px;flex-wrap:wrap}.split{display:grid;grid-template-columns:1fr 2fr;gap:24px;align-items:center}.split img{width:100%}.bar{height:14px;background:#354954;border-radius:8px;overflow:hidden}.bar div{height:100%;width:99.6875%;background:var(--gold)}code{word-break:break-word;font-size:12px}.rules li{margin:12px 0}@media(max-width:800px){main{padding:26px 12px}section{padding:18px}.grid,.steps,.split{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.cameras{grid-template-columns:1fr}h1{font-size:38px}}
</style><main><small>PLAGUEFALL · PILOTO DE COMPOSIÇÃO · APENAS A FASE1</small><h1>Seu padrão, aplicado ao pátio da igreja.</h1><p>A arquitetura define as bordas. O campo contém objetos inteiros. Os materiais se repetem por regras de encaixe e escala. Esta é uma proposta para sua avaliação antes de levar o padrão às demais fases.</p>
<div class="chips"><span class="upper">Área superior</span><span class="lower">Área inferior</span><span class="sides">Limitadores laterais</span><span class="field">Elementos do campo</span></div>
<nav><a href="#scene">Cena inteira</a><a href="#pattern">Padrão aplicado</a><a href="#workflow">Fluxo de trabalho</a><a href="#modules">Módulos</a><a href="#memory">Memória</a><a href="#camera">No jogo</a><a href="#review">Parecer</a></nav>
<section id="scene"><h2>Fase1 · composição nativa completa</h2><p>512×384 pixels, com a paleta do jogo. A igreja e o portão preservam sua identidade; o limite inferior e os objetos do campo vêm da nova cena completa.</p><div class="native"><img src="complete-3x.png" alt="Fase1completa com igreja, muros conectados, dois bancos e dois conjuntos de barris"></div><p class="links"><a href="complete-native.png" target="_blank">Imagem inteira em resolução nativa</a><a href="damaged-native.png" target="_blank">Estado danificado</a><a href="source/whole-scene.png" target="_blank">Desenho completo do ImageGen</a></p><p><b>Objetivo:</b> segurar os insetos por90segundos enquanto os civis terminam de sair. Quatro obstáculos baixos criam pequenos desvios e deixam o eixo central aberto.</p></section>
<section id="pattern"><h2>As quatro partes do seu desenho</h2><div class="split"><figure><img src="source/user-pattern.png" alt="Esquema original do usuário"><figcaption>Seu esquema de composição</figcaption></figure><figure><img src="pattern-applied.png" alt="Padrão aplicado com marcações coloridas"><figcaption>As cores identificam as partes; não fazem parte da arte do jogo.</figcaption></figure></div><div class="grid">'''+applied+'''</div></section>
<section id="workflow"><h2>Fluxo de trabalho para as próximas fases</h2><p>Cada etapa gera uma prova verificável. A aprovação visual acontece depois da montagem na resolução do jogo.</p><ol class="steps">'''+steps+'''</ol><details><summary>Regras para repetição harmoniosa</summary><ul class="rules">'''+rules+'''</ul></details><p><a href="workflow.json">Fluxo completo reutilizável</a> ·<a href="prompts.json">Prompt e referências da imagem</a></p></section>
<section id="modules"><h2>Peças inteiras e conexões previstas</h2><p>O banco e os barris são objetos completos. Muros e piso são materiais repetíveis; igreja, portão, pilares e cantos cumprem papéis próprios. As laterais foram extraídas separadamente para manter a luz consistente.</p><img class="diagram" loading="lazy" src="module-atlas.png" alt="Atlas de módulos da fase1"><details><summary>Tamanhos e eixos de repetição</summary><table><thead><tr><th>Peça</th><th>Região</th><th>Pixels</th><th>Repete em</th></tr></thead><tbody>'''+modules+'''</tbody></table><p>none=peça singular; x=horizontal; y=vertical; xy=material de superfície. O custo total é contado depois da montagem; não é a soma das áreas do atlas.</p></details><h3>Junções e silhuetas ampliadas</h3><img class="diagram" loading="lazy" src="junctions-and-props.png" alt="Ampliações dos cantos inferiores e objetos completos"><p class="links"><a href="layout.png" target="_blank">Regiões e caixas de colisão</a><a href="native/sprites-8x8.png" target="_blank">Tiles reais8×8</a><a href="manifest.json">Origem e posição de cada peça</a></p></section>
<section id="memory"><h2>Repetição com custo medido</h2><div class="metrics"><div><strong>638/640</strong><span>tiles únicos, com os dois estados</span></div><div><strong>20.416B</strong><span>gráficos na VRAM</span></div><div><strong>6.144B</strong><span>mapa por estado na ROM</span></div><div><strong>32B</strong><span>paleta de16cores</span></div></div><div class="bar"><div></div></div><p class="notice">Restam2tiles. O piloto cabe no orçamento atual, mas qualquer peça nova precisa de uma nova contagem. A igreja danificada já está incluída.</p><p>O PNG de desenho pode ser grande; seu tamanho em disco não determina o consumo do jogo. O cenário usa gráficos reutilizados, mapas de índices e uma janela de streaming64×32tiles na VRAM.</p><h3>Se o cenário crescer usando o mesmo repertório</h3><label for="world">Dimensões do mundo: </label><select id="world"><option value="512,384">512×384 · piloto</option><option value="1024,384">1024×384 · arena maior</option><option value="2560,320">2560×320 · corredor</option><option value="3072,320">3072×320 · corredor longo</option></select><p id="estimate"></p><small>Estimativa de mapas, mantendo os mesmos638tiles. Novas construções ou estados acrescentam gráficos. Essa simulação não significa que essas outras fases foram implementadas.</small></section>
<section id="camera"><h2>O padrão visto pela câmera real</h2><p>O mundo tem512×384 e a tela mostra320×224 por vez. Portanto, a imagem completa serve para revisar o conjunto; os enquadramentos abaixo mostram o que o jogador realmente vê em cada posição.</p>'''+frames+'''<p class="notice">As40provas de contato passaram: quatro lados de cada objeto e quatro limites, em NTSC e PAL. Os20.416bytes gráficos na VRAM correspondem ao exportado e o uso da bomba aciona a arte danificada. RAM prepara posições e suspende combate; isto não é um teste de dificuldade.</p><p class="links"><a href="rom/Plaguefall-Phase01-Pattern.bin">Baixar ROM do protótipo</a><a href="rom/manifest.json">Origem da ROM e limites do protótipo</a></p></section>
<section id="review"><h2>Pronto para sua avaliação</h2><p>Este piloto implementa o padrão nas quatro regiões e preserva a história introdutória. A composição nativa, os cantos e os objetos estão disponíveis sem marcações para julgamento visual.</p><ul class="rules">'''+''.join('<li>'+esc(clean(x))+'</li>' for x in review['native_art_review'])+'''</ul><details><summary>Critérios para estender o padrão à campanha</summary><ul class="rules">'''+acceptance+'''</ul></details><details><summary>Limites registrados</summary><ul>'''+''.join('<li>'+esc(clean(x))+'</li>' for x in review['limits'])+'''</ul></details><p><b>Aguardando sua avaliação do padrão.</b> As outras fases e a ROM de produção permanecem sem alterações nesta validação.</p><p><a href="review.json">Parecer e verificações</a> ·<a href="build.py">Montagem reproduzível</a> ·<a href="make_rom.py">Preparação do protótipo isolado</a></p></section>
</main><script>const sizes=document.querySelector('#world');function update(){const[w,h]=sizes.value.split(',').map(Number),map=w/8*h/8*2;document.querySelector('#estimate').textContent=`Gráficos:20.416B na VRAM · mapa:${map.toLocaleString('pt-BR')}B por estado na ROM · dois estados:${(map*2).toLocaleString('pt-BR')}B · janela de streaming:4.096B.`}sizes.onchange=update;update()</script></html>'''
# Cosmetic spacing without altering IDs, paths, dimensions or code syntax.
for a,b in [('FASE1','FASE 1'),('Fase1','Fase 1'),('fase1','fase 1'),('por90segundos','por 90 segundos'),('de16cores','de 16 cores'),('Restam2tiles','Restam 2 tiles'),('streaming64×32tiles','streaming 64×32 tiles'),('mesmos638tiles','mesmos 638 tiles'),('tem512×384','tem 512×384'),('mostra320×224','mostra 320×224'),('As40provas','As 40 provas'),('Os20.416bytes','Os 20.416 bytes'),('As20','As 20'),('tiles reais8×8','tiles reais 8×8'),('câmera{','câmera {'),('NTSC ·9','NTSC · 9'),('PAL ·9','PAL · 9')]:page=page.replace(a,b)
(A/'review.html').write_text(page)
print(json.dumps(dict(status=review['status'],tiles=m['memory']['unique_tiles'],camera_samples=18,movement_probes=40,production_rom_unchanged=True),indent=2))
