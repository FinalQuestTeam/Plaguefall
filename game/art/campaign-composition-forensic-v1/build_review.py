"""Publish a read-only visual reassessment, not a game asset generator."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import Counter
import json, html, os, hashlib, re

A=Path(__file__).resolve().parent
ROOT=A.parents[2]
load=lambda p:json.loads((A/p).read_text())
manifest=load('manifest.json')
captures=load('captures/ntsc/capture-report.json')
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',16)
large=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',24)
rows={r['phase']:{**r,'findings':[],'suspicions':[],'normal_camera_notes':[]} for r in manifest['phases']}

def relative(path):
    p=Path(path)
    if p.is_absolute(): return os.path.relpath(p,A)
    if str(p).startswith('game/'): return os.path.relpath(ROOT/p,A)
    if str(p).startswith(('art/','tools/','src/','res/')): return os.path.relpath(ROOT/'game'/p,A)
    return str(p)

def evidence(items):
    result=[]
    for item in items:
        d={'path':item} if isinstance(item,str) else item.copy()
        if 'path' in d: d['path']=relative(d['path'])
        result.append(d)
    return result

def add(ph,id,title,description,rects=(),proof=(),priority='P1',classification='visual_confirmed',code=()):
    f=dict(id=id,title=title,description=description,world_rects=rects,evidence=evidence(proof),priority=priority,classification=classification,code=evidence(code))
    rows[ph]['findings'].append(f)

for ph in ('1','2A','2B'):
    rows[ph]['status']='acceptable'
    rows[ph]['summary']='Arquitetura contínua, silhuetas completas e piso legível. Nesta inspeção não encontrei fragmentos internos que justifiquem reprovar o cenário.'
    rows[ph]['normal_camera_notes']=['A igreja existe inteira no mapa; nas vistas central e inferior ela sai da tela porque o mundo tem384px de altura. Isso é recorte do viewport, não imagem amputada.','A entrada central não mostra a largura inteira da igreja. Para uma apresentação narrativa completa, convém um enquadramento inicial próprio; não conto isso como defeito do asset.']
rows['2B']['summary']='A igreja mantém contorno coerente; telhado rompido e três pilhas de escombros comunicam dano sem fragmentos soltos comprovados. A intensidade da destruição ainda pode ser aumentada por direção de arte.'
add('3','EARLY-3-01','Casas com aberturas vizinhas cortadas e telhado recomposto','As fachadas foram recortadas de três posições diferentes e unidas a um telhado comum. Há aberturas parciais nas bordas, beirais sem continuidade e repetição de um miolo16×16 no telhado. O erro está nos módulos dentro do mapa, além de qualquer corte da câmera.',[[240,72,2112,96]],['../phase03-clipping-review-v1/evidence.png','../phase03-clipping-review-v1/report.json'],code=[{'path':'game/art/campaign-whole-scenes-v1/build_early.py','line':27},{'path':'game/art/campaign-whole-scenes-v1/build_early.py','line':30}])
add('3','EARLY-3-02','Faixa azul e repetição comprimem a leitura de uma rua','O plano azul uniforme tem72px de altura e termina numa fileira quase ininterrupta do mesmo telhado. Falta transição de profundidade, separação entre lotes e variação de quarteirões. Nas rotas inferiores o HUD esconde ainda mais a arquitetura; os carros e barreiras existem, mas não resolvem o pano de fundo.',[[0,0,2560,168]],['maps/3-complete.png','captures/ntsc/3/x2-y2.png'],priority='P2',classification='art_direction',code=[{'path':'game/art/campaign-whole-scenes-v1/build_early.py','line':42}])
add('4','EARLY-4-01','Parede sul é uma fatia de porta e pilares','O fechamento sul reutiliza as linhas80..111 da parede norte e as espelha. O resultado deixa pedaços de persiana e pilares cortados no eixo vertical, sem topo/implantação de uma parede sul própria. A montagem aparece inteira no panorama e no pé da tela durante a movimentação.',[[32,352,448,32]],['details/4-south.png','maps/4-complete.png','captures/ntsc/4/x1-y2.png'],code=[{'path':'game/art/campaign-whole-scenes-v1/build_early.py','line':116}])
add('5','EARLY-5-01','Exterior não mantém a identidade visual do galpão','O interior4 usa tijolos escuros, pilares metálicos e uma grande persiana azul. O pátio5 troca essa linguagem por arcos, panos pendurados e módulos densos de outra construção. A Santa está bem destacada, mas o conjunto não comunica claramente a frente do mesmo galpão. O topo no limite do mapa não é, por si só, prova de recorte defeituoso.',[[16,0,352,80]],['maps/4-complete.png','maps/5-complete.png','details/5-north.png'],priority='P2',classification='spatial_continuity',code=[{'path':'game/art/campaign-early-v1/build.py','line':122}])

route=load('reviews/routes.json')
for p in route['phases']:
    ph=p['phase']
    for f in p['findings']:
        add(ph,f['id'],f['title'],f['description'],[f['world_rect']] if f.get('world_rect') else [],f.get('evidence',[]),f.get('priority','P1'),f.get('confidence','confirmed'),f.get('code',[]))
    rows[ph]['suspicions']=p.get('unproven_suspicions',[])
    rows[ph]['summary']=p.get('judgment','')

factory=load('reviews/factory.json')
for f in factory['findings']:
    for ph in f['phases']:
        if f.get('status','').startswith('confirmed'):
            add(ph,f['id'],f['title'],f['description'],f.get('world_rects_xywh',[]),f.get('evidence',[]),f.get('severity','P1'),f['status'])
        else: rows[ph]['suspicions'].append(f)
for p in factory['phases']: rows[p['phase']]['summary']=p['summary']

late=load('reviews/resistance-launch.json')
for f in late['findings']:
    for ph in f['phases']:
        add(ph,f['id'],f['title'],f['description'],f.get('world_regions',[]),f.get('evidence',[]),f['severity'],f['classification'],f.get('code',[]))
for p in late['cases']:
    rows[p['phase']]['summary']=p['specific_review']
    rows[p['phase']]['normal_camera_notes']=p['normal_camera_limits']
for s in late['suspicions']:
    for ph in s.get('phases',[s.get('phase')]):
        if ph: rows[ph]['suspicions'].append(s)

# A clipped viewport can weaken framing, but does not prove a clipped asset.
for ph,ident in [('12','12-03'),('11','FACTORY-11-02')]:
    for f in rows[ph]['findings']:
        if f['id']==ident:
            f['classification']='framing_judgment'
            f['description']+=' Trata-se de um problema de enquadramento/contexto; esse corte de viewport não comprova, isoladamente, uma imagem amputada no asset.'

# Cross-review: a cut at the world perimeter is not proof of an amputated prop.
f=rows['4']['findings'][0]
f.update(title='Fechamento sul precisa de leitura mais clara como parede de primeiro plano',description='A faixa y352..384 reutiliza a parte baixa da persiana e dos pilares norte. Ela fecha o mundo, liga-se às laterais e coincide com o limite dos pés: pode representar uma parede de primeiro plano continuando para fora do mapa. Não há prova suficiente de objeto amputado dentro da arena. Recomendo melhorar o coroamento e a separação do piso para tornar essa leitura inequívoca; é um ajuste de acabamento, não uma reprovação por fragmentos.',priority='P2',classification='art_direction')
f=rows['5']['findings'][0]
f['title']='Ligação visual fraca entre o interior e o exterior do galpão'
f['description']+=' A necessidade de maior semelhança é uma avaliação editorial de continuidade, não prova de que sejam prédios fisicamente incompatíveis.'
for ph in ('10','11'):
    updated=[]
    for f in rows[ph]['findings']:
        if f['id']=='FACTORY-COLLISION-01':
            f['description']='As bases dos três gabinetes não constam nos sólidos da fábrica. Isso é um fato da geometria; a necessidade de bloqueio e a possível sobreposição visual devem ser verificadas por movimento e oclusão. Não houve nova prova de travessia desses gabinetes nesta auditoria e a ausência do sólido, isoladamente, não comprova composição defeituosa.'
            f['classification']='static_geometry_risk_requires_movement';rows[ph]['suspicions'].append(f);continue
        if f['id']=='FACTORY-SCENE-02':
            f['title']='Recorte lateral trunca a face e a luminária dos pilares inferiores'
            f['description']=f['description'].replace('não são pilares completos','a face e a luminária não ficam inteiras')
        if f['id']=='FACTORY-11-01':
            f['title']='Válvula sobre a esteira sem montagem física resolvida'
            f['description']='A válvula3 cobre pixels da esteira preservada. A válvula2 está na região já sobrescrita pelo falso tubo, portanto não conto sua sobreposição como um segundo defeito independente. Os objetivos não apresentam uma montagem física clara entre roda, carcaça e tapete. Contagens feitas apenas contra a caixa retangular da esteira não medem a interseção de silhuetas e foram retiradas do parecer final.'
        if f['id']=='FACTORY-11-02':f['priority']='P2'
        updated.append(f)
    rows[ph]['findings']=updated
rows['10']['summary']='Os ninhos são legíveis e apoiados no piso. Persistem fragmentos de carcaça azul sobre as esteiras e cortes laterais nos pilares; a relação de colisão dos gabinetes ainda requer confirmação em movimento.'
rows['11']['summary']='Os fragmentos de carcaça e pilares se repetem; uma válvula cobre a arte preservada da esteira. O enquadramento reduz o contexto arquitetônico, mas não comprova um asset cortado.'
rejected={'3','6A','6B','10','11','12','13A','14','15','16'}
adjust={'4','5','7','8','9','13B'}
labels={'rejected':'Reprovada','adjustments':'Precisa de ajustes','acceptable':'Aceitável nesta revisão'}
colors={'rejected':'#ef817d','adjustments':'#e4bd65','acceptable':'#87cbb6'}
actions={
 '3':'Refazer casas completas e suas divisas; eliminar a colagem de telhado/fachada e compor profundidade por quarteirão.',
 '4':'Melhorar o coroamento da parede sul e sua separação do piso; preservar a conexão plausível com o perímetro.',
 '5':'Compor o exterior com a mesma linguagem do interior4 e manter a Santa como foco principal.',
 '6A':'Extrair arcos e tubulações inteiros; resolver o encaixe do marco central e implantar piso com marcos discretos.',
 '6B':'Refazer os vãos completos das comportas, apoiar a folha nos batentes e conectar a válvula a uma junção mecânica.',
 '7':'Substituir as barricadas por recortes completos, preservando caixas, contorno e sombra.',
 '8':'Aplicar a mesma correção das barricadas7 e conferir o emissor contra as novas silhuetas.',
 '9':'Corrigir o limite do recorte do portão e conferir os pixels pretos no piso da saída.',
 '10':'Trocar o falso tubo por um módulo inteiro, recuperar pilares completos e testar a profundidade dos gabinetes em movimento.',
 '11':'Aplicar a correção10; reposicionar válvulas fora das esteiras e reenquadrar a arquitetura do interior.',
 '12':'Substituir obstáculos ampliados por peças completas; alinhar treliças/canos e a chegada sindical.',
 '13A':'Dar apoio físico a Dinorah ou usar uma pose de busto; reconstruir o chanfro direito do guichê.',
 '13B':'Preservar o memorial e reconstruir o chanfro direito do guichê.',
 '14':'Alinhar colisão/profundidade da estação e terminar os conduítes em junções coerentes.',
 '15':'Preservar as cinco máquinas ligadas, corrigir a estação e manter continuidade com o mapa14.',
 '16':'Recuperar o jato inteiro e a estação do mapa15; reduzir o carimbo repetitivo do piso.',
}
def prose(s):
    s=re.sub(r'\bem([xy])(?=\d)',r'em \1',s)
    s=re.sub(r'(?<=[a-zà-ž])(?=\d)', ' ', s)
    s=re.sub(r'(?<=\d)(?=[a-zà-ž])', ' ', s)
    return s
for r in rows.values():
    for key in ('summary','goal'):
        if key in r:r[key]=prose(r[key])
    r['normal_camera_notes']=[prose(n) for n in r['normal_camera_notes']]
    for f in r['findings']:
        f['title']=prose(f['title']);f['description']=prose(f['description'])
    for s in r['suspicions']:
        if 'description' in s:s['description']=prose(s['description'])
for ph,r in rows.items():
    if ph in rejected:r['status']='rejected'
    elif ph in adjust:r['status']='adjustments'
    r['status_label']=labels[r['status']]
    r['next_action']=prose(actions.get(ph,'Manter a composição; conferir novamente após mudanças globais de câmera ou enquadramento narrativo.'))
    if not r.get('summary'):r['summary']=r['findings'][0]['description']
    c=next(p for p in captures['phases'] if p['phase']==ph)
    r['camera_samples']=c['samples']
    r['camera_board']=f'boards/{ph}-cameras.png'
    ncol=max(s['col'] for s in c['samples'])+1
    sheet=Image.new('RGB',(max(1024,ncol*320),3*258+48),(18,24,26));dr=ImageDraw.Draw(sheet)
    dr.text((12,8),f'FASE {ph} · CÂMERAS REAIS · NTSC ·3 faixas verticais',font=large,fill='white')
    for s in c['samples']:
        x=s['col']*320;y=48+s['row']*258
        dr.text((x+6,y+2),f"{s['label']} · c{tuple(s['camera'])}",font=font,fill=(201,211,210))
        sheet.paste(Image.open(A/'captures/ntsc'/s['path']),(x,y+30))
    sheet.save(A/r['camera_board'])
    # Findings are an annotation COPY; the complete unmarked image is retained.
    marked=Image.open(A/r['complete']).convert('RGB');dr=ImageDraw.Draw(marked)
    for n,f in enumerate(r['findings'],1):
        for rect in f['world_rects']:
            if len(rect)!=4:continue
            x,y,w,h=rect;dr.rectangle((x,y,x+w-1,y+h-1),outline=(255,73,98),width=2)
            dr.rectangle((x,y,x+24,y+20),fill=(57,14,28));dr.text((x+3,y),str(n),font=font,fill='white')
    marked.save(A/f'details/{ph}-marked.png')
    r['marked']=f'details/{ph}-marked.png'

report={
 'rom_sha256':manifest['rom_sha256'],'runtime_or_art_changed':False,
 'cross_review_addendum':'reviews/factory-critical-addendum.json',
 'previous_approvals_superseded':True,'scope':'Todas as 19 variações, incluindo 1, 2A, 2B, 5, 13A e 16 antes preservadas.',
 'counts':dict(Counter(r['status'] for r in rows.values())),
 'camera_samples':sum(len(r['camera_samples']) for r in rows.values()),
 'criteria':['Integridade de cada construção e objeto','Continuidade das emendas e perspectiva','Apoio no piso, escala e profundidade dos atores','Relação do objetivo com arquitetura e área de combate','Enquadramentos superior, central e inferior','Continuidade entre fases e estados'],
 'method':manifest['method'],
 'limits':['Panoramas são reconstruções dos recursos da produção e objetivos em suas coordenadas, não uma captura simultânea do framebuffer.','Os10 ninhos lógicos são mostrados juntos; o runtime transmite no máximo7 slots de objetivos visíveis.','Dinorah móvel e Damião são examinados nas capturas reais. A fase 16 mostra uma pose representativa do boss na posição inicial.','Varredura de câmera usa RAM para preparar nós, reposicionar pés em locais livres e suspender combate/progresso; não é playthrough nem teste de dificuldade.','255 amostras NTSC novas e38 entradas NTSC/PAL da mesma ROM. Uma amostragem discreta não prova todos os enquadramentos entre os pontos.','Suspeitas não contam como defeitos comprovados. Geometria estática e movimento observado são identificados separadamente.'],
 'unique_findings':len({f['id'] for r in rows.values() for f in r['findings']}),
 'phases':list(rows.values())}
(A/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

# One overview contains every complete scenario, in campaign order and without cropping.
overview=Image.new('RGB',(1600,19*310+110),(17,24,27));dr=ImageDraw.Draw(overview)
dr.text((24,16),'CAMPANHA INTEIRA ·19 COMPOSIÇÕES · REAVALIAÇÃO CRÍTICA',font=large,fill='white')
dr.text((24,58),'3 aceitáveis · 6 precisam de ajustes · 10 reprovadas | mapas completos sem cortar as bordas',font=font,fill=(193,203,205))
for i,r in enumerate(rows.values()):
    y=110+i*310;dr.text((24,y+8),f"{r['phase']} · {r['name']} — {r['status_label']}",font=large,fill=colors[r['status']])
    im=Image.open(A/r['complete']);scale=min(1552/im.width,244/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
    overview.paste(im,((1600-im.width)//2,y+52))
overview.save(A/'overview.png')

esc=html.escape
def link(path,label=None):
    return f'<a href="{esc(relative(path),quote=True)}" target="_blank">{esc(label or path)}</a>'
def image(path,alt):return f'<img loading="lazy" src="{esc(path,quote=True)}" alt="{esc(alt,quote=True)}">'
def links(items):
    return ' · '.join(link(i['path'],i.get('note',Path(i['path']).name)) for i in items if 'path' in i)
table=''.join(f'<tr><td><a href="#p{r["phase"]}">{r["phase"]}</a></td><td>{esc(r["name"])}</td><td class="{r["status"]}">{r["status_label"]}</td><td>{len(r["findings"])}</td></tr>' for r in rows.values())
cards=[]
for r in rows.values():
    ph=r['phase'];findinghtml=''
    for n,f in enumerate(r['findings'],1):
        coords='; '.join(str(v) for v in f['world_rects']) or 'Ver prova vinculada'
        findinghtml+=f'<li><h3>{esc(f["title"])} <small>{f["priority"]} ·{esc(f["classification"])}</small></h3><p>{esc(f["description"])}</p><small>Região do mundo[x,y,w,h]:{coords}</small><p class="links">{links(f["evidence"]+f["code"])}</p></li>'
    suspects=''.join('<li>'+esc(s.get('description',str(s)))+'</li>' for s in r['suspicions'])
    notes=''.join('<li>'+esc(n)+'</li>' for n in r['normal_camera_notes'])
    specials=''.join(f'<h3>{esc(s["label"])}</h3><div class="panorama">{image(s["path"],s["label"])}</div>' for s in r['special_states'])
    cameras=''
    for rowindex,title in enumerate(('Faixa superior','Campo central','Faixa inferior')):
        samples=''.join(f'<figure>{image("captures/ntsc/"+s["path"],title)}<figcaption>Pés{tuple(s["position"])} · câmera{tuple(s["camera"])}</figcaption></figure>' for s in r['camera_samples'] if s['row']==rowindex)
        cameras+=f'<h3>{title}</h3><div class="camera-row">{samples}</div>'
    entry=''.join(f'<figure>{image(f["path"],f["label"])}<figcaption>{f["label"]}</figcaption></figure>' for f in r['frames'])
    cards.append(f'''<article id="p{ph}"><header><div><small>FASE {ph} ·{r['size'][0]}×{r['size'][1]}px</small><h2>{esc(r['name'])}</h2></div><b class="badge {r['status']}">{r['status_label']}</b></header>
<p>{esc(r['summary'])}</p><p><b>Objetivo:</b> {esc(r['goal'])}</p>
<h3>Cenário completo · composição de produção</h3><div class="panorama">{image(r['complete'],'Cenário completo da fase '+ph)}</div>
<p class="links">{link(r['complete'],'Abrir imagem inteira')} ·{link('boards/'+ph+'-whole.png','Prancha completa + geometria')} ·{link(r['marked'],'Regiões numeradas')} ·{link(r['background'],'Fundo sem objetivos')}</p>
<details><summary>Regiões dos problemas e geometria</summary><div class="panorama">{image(r['marked'],'Regiões dos problemas')}</div><div class="panorama">{image(r['layout'],'Geometria')}</div><p>Verde: limites dos pés · vermelho: sólidos · amarelo: objetivos · ciano: início16×16. Os contornos são diagnóstico, não arte do jogo.</p></details>
<ol class="findings">{findinghtml or '<li>Sem fragmentos internos comprovados nesta revisão.</li>'}</ol>
{('<details><summary>Cortes normais de câmera / ressalvas</summary><ul>'+notes+'</ul></details>') if notes else ''}
{('<details><summary>Suspeitas separadas — não entram na contagem de defeitos</summary><ul>'+suspects+'</ul></details>') if suspects else ''}
<p class="action"><b>Próxima correção:</b> {esc(r['next_action'])}</p>
{('<details><summary>Estados alternativos completos</summary>'+specials+'</details>') if specials else ''}
<details><summary>Varredura real de câmera · {len(r['camera_samples'])} amostras novas</summary><p>Combate/progresso suspensos para inspeção. Desloque cada faixa horizontalmente para ver todos os pontos.</p>{cameras}<p>{link(r['camera_board'],'Prancha única das câmeras')}</p></details>
<details><summary>Entradas reais NTSC e PAL · mesma ROM</summary><div class="camera-row">{entry}</div></details></article>''')

nav=''.join(f'<a class="{r["status"]}" href="#p{r["phase"]}">{r["phase"]}</a>' for r in rows.values())
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campanha · reavaliação integral de composição</title><style>
:root{color-scheme:dark;--bg:#11191d;--panel:#1b272c;--line:#37464c;--ink:#e5ecec;--muted:#afc0c4}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1600px;margin:auto;padding:36px 28px}h1{font-size:clamp(30px,4vw,52px);line-height:1.12;max-width:1100px}h2{font-size:28px;line-height:1.2;margin:4px 0}h3{font-size:18px;margin:18px 0 8px}small,figcaption{color:var(--muted)}a{color:#a7d5e9}nav{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}nav a,.badge{padding:6px 14px;border:1px solid var(--line);border-radius:5px;text-decoration:none}.rejected{color:#ef817d}.adjustments{color:#e4bd65}.acceptable{color:#87cbb6}.notice{border-left:4px solid #ef817d;background:#30282b;padding:20px}article{border:1px solid var(--line);background:var(--panel);padding:24px;margin:32px 0;border-radius:8px;scroll-margin-top:90px}header{display:flex;justify-content:space-between;gap:16px;align-items:center}.panorama{overflow:auto;background:#070c10;padding:8px;border:1px solid var(--line);margin:12px 0}.panorama img{display:block;max-width:100%;height:auto;image-rendering:pixelated;margin:auto}body.native .panorama img{max-width:none;width:auto;margin:0}button{font:inherit;padding:8px 16px;background:#29404b;color:white;border:1px solid #587380;border-radius:4px;cursor:pointer}.toolbar{position:sticky;top:0;background:#11191def;padding:10px;z-index:2;border-bottom:1px solid var(--line)}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{text-align:left;border-bottom:1px solid var(--line);padding:8px 12px}.camera-row{display:flex;gap:12px;overflow:auto}.camera-row figure{margin:0;flex:0 0 320px}.camera-row img{width:320px;height:224px;image-rendering:pixelated}figcaption{font-size:12px}.links{font-size:13px;overflow-wrap:anywhere}details{padding:12px 0;border-top:1px solid var(--line)}summary{cursor:pointer;color:#bcd8e4}.findings{padding-left:24px}.findings li{padding:6px 0 18px;border-bottom:1px solid var(--line)}.findings small{font-size:12px}.action{border-left:3px solid #e4bd65;padding:10px 18px;background:#2c3030}.overview{width:100%;max-width:1000px;display:block;margin:auto}.stats{font-size:22px;color:#e4bd65}code{overflow-wrap:anywhere}@media(max-width:700px){main{padding:20px 12px}article{padding:14px}header{display:block}.badge{display:inline-block;margin:10px 0}td,th{padding:5px}}
</style><main><small>PLAGUEFALL · AUDITORIA DA COMPOSIÇÃO EM PRODUÇÃO ·23/10/2026</small><h1>Todos os cenários completos, antes do parecer.</h1>
<p class="notice"><b>Esta reavaliação substitui as aprovações visuais anteriores.</b> Foram revisadas as 19 variações, incluindo as que antes estavam preservadas. Nenhuma arte, código do jogo ou ROM foi alterada nesta auditoria.</p>
<p class="stats">3 aceitáveis nesta revisão · 6 precisam de ajustes · 10 reprovadas</p><p>O parecer distingue defeitos nos próprios módulos, problemas de apoio/profundidade, continuidade entre fases e cortes normais do viewport. A aprovação técnica anterior não é evidência de qualidade visual.</p>
<div class="toolbar"><button id="scale">Ver pixels nativos / rolar mapas</button> <a href="#overview">Visão conjunta</a> ·<a href="#index">Pareceres individuais</a></div>
<nav>'''+nav+'''</nav><details><summary>Método, critérios e limites da evidência</summary><p>Os 19 panoramas foram preparados antes dos pareceres, usando os pixels nativos e objetivos nas coordenadas do runtime. A reconstrução mostra a cena inteira, com proporções corretas, sem HUD nem corte de câmera.</p><ul>'''+''.join('<li>'+esc(x)+'</li>' for x in report['limits'])+'''</ul><p><b>Critérios:</b> '''+'; '.join(report['criteria'])+'''</p><p>ROM SHA256:<code>'''+report['rom_sha256']+'''</code></p><p>'''+link('report.json','Relatório integral')+' ·'+link('reviews/factory-critical-addendum.json','Contraprova e refinamentos dos pareceres')+' ·'+link('manifest.json','Origem e posição de cada recurso')+' ·'+link('captures/ntsc/capture-report.json','Coordenadas das 255 capturas')+'''</p></details>
<h2 id="overview">Visão conjunta · todas as imagens inteiras</h2><p>Cada mapa está inteiro, sem transformar uma miniatura em prova de acabamento. Os defeitos e ampliações são descritos por fase abaixo.</p><a href="overview.png" target="_blank"><img class="overview" src="overview.png" alt="Todas as 19 composições completas com os novos pareceres"></a>
<h2 id="index">Resultado de cada fase</h2><table><thead><tr><th>Fase</th><th>Cenário</th><th>Parecer atual</th><th>Achados</th></tr></thead><tbody>'''+table+'''</tbody></table>'''+''.join(cards)+'''<footer><p>Auditoria visual concluída; correções de cenários continuam pendentes. A revisão não valida dificuldade nem desempenho. Fontes completas, estados e movimento devem ser revistos após cada futura correção.</p></footer></main><script>document.querySelector('#scale').onclick=()=>{document.body.classList.toggle('native');document.querySelector('#scale').textContent=document.body.classList.contains('native')?'Ajustar mapas inteiros à tela':'Ver pixels nativos / rolar mapas'}</script></html>'''
(A/'review.html').write_text(page)
(A/'README.md').write_text('''# Reavaliação integral de composição visual

Este parecer substitui as aprovações visuais anteriores. Foram produzidos os 19 cenários completos antes da avaliação: 3 aceitáveis nesta revisão, 6 precisam de ajustes e 10 reprovados. Não houve alteração de arte, C, recursos binários ou ROM.

[Revisão visual por fase](review.html) ·[Todas as imagens completas](overview.png) ·[Relatório integral](report.json) ·[Manifesto de origem e geometria](manifest.json).

Os panoramas são reconstruções do mapa nativo e objetivos nas coordenadas do runtime. Há255 novas amostras NTSC de câmera nas faixas superior, central e inferior, mais38 entradas NTSC/PAL da mesma ROM. A varredura prepara nós, suspende combate/progresso e posiciona o personagem via RAM; não é um playthrough nem calibração de dificuldade. Os10 ninhos são mostrados juntos no panorama; no jogo existem7 slots simultâneos. O boss no panorama é uma pose representativa no spawn; atores móveis são avaliados nas capturas reais.

`prepare.py` congela mapas e estados; `capture.py --build-dir game/out/release` captura a câmera real com o núcleo libretro, via Python Intel; `build_review.py` publica pareceres previamente inspecionados e pranchas. Nenhum deles compila ou modifica o jogo. As decisões são humanas/visuais; o script não concede aprovação por testes verdes.

Os relatórios independentes estão em `reviews/`. As suspeitas permanecem separadas dos defeitos comprovados. Capturas e mapas sem marcações são preservados ao lado das cópias anotadas. Pranchas completas e pranchas de câmera estão em `boards/`.

ROM de produção SHA256: `'''+report['rom_sha256']+'''`.
''')
assert hashlib.sha256((ROOT/'game/out/release/Plaguefall.bin').read_bytes()).hexdigest()==report['rom_sha256']
print(json.dumps({k:report[k] for k in ('counts','camera_samples','unique_findings','rom_sha256')},indent=2))
