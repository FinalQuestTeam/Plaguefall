"""Code-native SVG/HTML HUD proposal; does not export resources or change ROM."""
from pathlib import Path
import base64, hashlib, html, json, re, struct
from PIL import Image

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
OUT=ROOT/'propostas';OUT.mkdir(exist_ok=True)
ROM=GAME/'out/release/Plaguefall.bin'
rom_hash=hashlib.sha256(ROM.read_bytes()).hexdigest()
font_source=(GAME/'src/system/video/screens/result_font.h').read_text()
font=list(map(int,re.findall(r'\d+',re.search(r'RESULT_FONT\[768\] = \{(.*?)\};',font_source,re.S)[1])))
assert len(font)==768
words=struct.unpack('>16H',(GAME/'art/cangaco-itens-v2/palette-md.bin').read_bytes())
palette=['#%02x%02x%02x'%((v>>1&7)*34,(v>>5&7)*34,(v>>9&7)*34) for v in words]
items=GAME/'art/cangaco-itens-v2/native'
parts=[];bounds=[]

def rect(x,y,w,h,color):
    assert w>0 and h>0
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')

def pixels(rows,x,y,colors):
    for yy,row in enumerate(rows):
        for xx,c in enumerate(row):
            if c is not None:rect(x+xx,y+yy,1,1,colors[c])

def text(s,x,y,color):
    assert x>=0 and x+len(s)*8<=320 and 0<=y<=16,(s,x,y)
    bounds.append({'text':s,'rect':[x,y,len(s)*8,8]})
    for i,c in enumerate(s):
        assert 32<=ord(c)<128
        for yy,mask in enumerate(font[(ord(c)-32)*8:(ord(c)-31)*8]):
            for xx in range(8):
                if mask&(128>>xx):rect(x+i*8+xx,y+yy,1,1,color)

def item(name,x,y):
    im=Image.open(items/(name+'-hud.png')).convert('RGBA')
    assert im.size==(8,8)
    for yy in range(8):
        for xx in range(8):
            r,g,b,a=im.getpixel((xx,yy))
            if a:rect(x+xx,y+yy,1,1,'#%02x%02x%02x'%(r,g,b))

def saint(x,y):
    source=(GAME/'src/system/video/sprites/saint_data.h').read_text()
    block=re.search(r'SAINT_ICON_DATA\[8\] = \{(.*?)\};',source,re.S)[1]
    rows=[int(v,16) for v in re.findall(r'0x([0-9a-f]+)',block)]
    pixels([[((v>>(28-4*xx))&15) or None for xx in range(8)] for v in rows],x,y,palette)

def clock(x,y):
    pixels([[1 if c=='#' else None for c in row] for row in [
        '..####..','.#....#.','#..#...#','#..#...#','#..###.#','#.....#','.#....#.','..####..']],x,y,palette)

def skull(x,y):
    pixels([[1 if c=='#' else None for c in row] for row in [
        '........','..####..','.######.','.#.##.#.','.######.','..####..','..#.#.#.','........']],x,y,palette)

cases=[
    {'id':'proteger','camera_shift':16,'label':'Proteger a Santa','source':'art/hud-resistencia-v1/referencias/reference-05.png','hp':76,'signal':100,'seconds':28,'selected':3,'mode':True},
    {'id':'eliminar','camera_shift':0,'label':'Eliminar inimigos','source':'art/hud-resistencia-v1/referencias/reference-03.png','hp':100,'kills':8,'target':14,'selected':0,'mode':False},
    {'id':'vida-baixa','camera_shift':16,'label':'Vida baixa','source':'art/hud-resistencia-v1/referencias/reference-05.png','hp':24,'signal':100,'seconds':12,'selected':1,'mode':True},
]
for case in cases:
    parts=[];bounds=[]
    background=GAME/case['source'];encoded=base64.b64encode(background.read_bytes()).decode()
    # Model the extra headroom needed above the protected statue. This is
    # a camera illustration on the SVG, not a change to game simulation.
    parts.append('<defs><clipPath id="world"><rect x="0" y="24" width="320" height="200"/></clipPath></defs>')
    parts.append(f'<image x="0" y="{case['camera_shift']}" width="320" height="224" clip-path="url(#world)" style="image-rendering:pixelated" href="data:image/png;base64,{encoded}"/>')
    rect(0,0,320,24,palette[10]);rect(1,1,318,21,palette[9])
    rect(2,2,316,19,palette[11]);rect(2,1,316,1,palette[4])
    rect(2,22,316,1,palette[9]);rect(0,23,320,1,palette[11])
    for x in (103,237):rect(x,3,1,18,palette[9]);rect(x+1,3,1,18,palette[10])
    if 'signal' in case:
        text('PROTEJA',8,3,palette[1]);saint(8,13)
        text(str(case['signal']).zfill(3),20,13,palette[1]);clock(60,13)
        text(str(case['seconds']).zfill(2),72,13,palette[4])
    else:
        text('ELIMINE',8,3,palette[1]);skull(8,13)
        text(f"{case['kills']:02d}/{case['target']:02d}",20,13,palette[4])
    for i,(name,count) in enumerate([('bomb',2),('shield',1),('chain',2),('ice',3)]):
        x=108+i*26
        rect(x,3,24,18,palette[4] if i==case['selected'] else palette[10])
        rect(x+1,4,22,16,palette[11])
        if i==case['selected']:rect(x+2,19,20,1,palette[4])
        item(name,x+3,8);text(str(count),x+14,8,palette[1])
    if case['mode']:
        rect(214,4,20,16,palette[6]);rect(215,5,18,14,palette[11])
        item('ice',216,8);text('3',225,8,palette[2])
    text(f"VIDA {case['hp']:03d}",242,3,palette[1])
    rect(242,15,68,6,palette[6]);rect(243,16,66,4,palette[11])
    fill=max(1,round(66*case['hp']/100))
    rect(243,16,fill,4,palette[3] if case['hp']<=25 else palette[14])
    rect(243,16,fill,1,palette[4] if case['hp']<=25 else palette[1])
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="672" viewBox="0 0 320 224" shape-rendering="crispEdges">'+''.join(parts)+'</svg>'
    (OUT/(case['id']+'.svg')).write_text(svg)
    case['text_bounds']=bounds
    case['capture_sha256']=hashlib.sha256(background.read_bytes()).hexdigest()

page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plaguefall · proposta do HUD</title>
<style>*{box-sizing:border-box}body{margin:0;background:#151712;color:#eadfc8;font:16px system-ui;padding:32px;max-width:1460px;margin:auto}h1{font-size:32px;margin:8px 0 12px}p{line-height:1.6;max-width:1000px}.eyebrow{color:#c6a25b;font-size:12px;letter-spacing:2px}button{font:inherit;padding:10px 16px;margin:0 8px 10px 0;background:#29291f;color:#eadfc8;border:1px solid #766139;cursor:pointer;border-radius:4px}button[aria-pressed=true]{background:#ba8d36;color:#171810}.controls{margin:24px 0 8px}.frames{display:grid;grid-template-columns:1fr;gap:24px}.frames.compare{grid-template-columns:1fr 1fr}figure{margin:0;padding:12px;border:1px solid #574c34;background:#22241c}figcaption{font-size:13px;color:#baa87d;margin-bottom:12px}img{display:block;width:100%;height:auto;image-rendering:pixelated}#beforeBox{display:none}.compare #beforeBox{display:block}.legend{display:grid;grid-template-columns:1fr 1.25fr 1fr;gap:20px;margin:24px 0}.legend>div{border-top:2px solid #9d792f;padding-top:12px}.legend p{font-size:14px;color:#c1baa7}.muted{color:#aaa58f;font-size:14px}a{color:#e4bd6d}@media(max-width:800px){body{padding:18px}.frames.compare,.legend{grid-template-columns:1fr}h1{font-size:25px}}</style>
<div class="eyebrow">PLAGUEFALL · PAINEL DA RESISTÊNCIA</div><h1>Uma faixa de equipamento para o combate</h1>
<p>Painel de <strong>24 px</strong>, com metal escuro e bordas em cobre. Objetivo à esquerda, inventário no centro e vida à direita. Ícones e fonte mantêm a escala nativa de <strong>8×8</strong>.</p>
<div class="controls" id="cases"></div><button id="comparison" aria-pressed="false">Comparar com o HUD atual</button>
<div class="frames" id="frames"><figure id="beforeBox"><figcaption>ATUAL · captura anterior da ROM</figcaption><img id="before" alt="Interface superior atual"></figure><figure><figcaption id="caption">PROPOSTA · composição visual</figcaption><img id="after" alt="Proposta do HUD de 24 pixels"></figure></div>
<div class="legend"><div><strong>01 · Objetivo</strong><p>Na proteção: vida do sinalizador e tempo restante. No combate: quantidade eliminada e meta.</p></div><div><strong>02 · Equipamento</strong><p>Quatro espaços fixos; a borda dourada marca a seleção. A pequena caixa azul à direita mostra o modo de tiro ativo e suas cargas.</p></div><div><strong>03 · Vida</strong><p>Número exato e barra curta. A barra esvazia e fica vermelha em vida baixa; o número mantém a informação legível sem depender da cor.</p></div></div>
<p class="muted">Proposta visual para avaliação. Os valores são ilustrativos e os espaços de inventário aparecem preenchidos para testar a densidade máxima. O painel ocupa 16 px a mais no topo que o HUD atual. Na proteção, o cenário é deslocado 16 px para baixo nesta composição, ilustrando a folga necessária acima da Santa. A câmera e os marcadores ainda precisam ser ajustados e testados na implementação. A composição não mede performance nem confirma orçamento final de tiles. A ROM e os fontes do jogo permanecem iguais.</p>
<p><a id="download" href="propostas/proteger.png">Abrir desenho ampliado</a> · <a href="especificacao.json">Especificação e fontes</a></p>
<script>const cases=CASES;let index=0;const root=document.querySelector('#cases');for(const [i,c] of cases.entries()){const b=document.createElement('button');b.textContent=c.label;b.onclick=()=>show(i);root.appendChild(b)}function show(i){index=i;const c=cases[i];document.querySelector('#after').src='propostas/'+c.id+'.png';document.querySelector('#before').src='../../'+c.source;document.querySelector('#caption').textContent='PROPOSTA · '+c.label+' · 320×224, ampliada sem suavização';document.querySelector('#download').href='propostas/'+c.id+'.png';[...root.children].forEach((b,j)=>b.setAttribute('aria-pressed',i===j))}document.querySelector('#comparison').onclick=e=>{const on=document.querySelector('#frames').classList.toggle('compare');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Ver somente a proposta':'Comparar com o HUD atual'};show(0)</script></html>'''
page=page.replace('CASES',json.dumps(cases,ensure_ascii=False))
(ROOT/'revisao.html').write_text(page)
(ROOT/'especificacao.json').write_text(json.dumps({'status':'proposal_only','hud_height':24,'native_size':[320,224],'export_size':[960,672],'font':'SGDK native 8x8 from result_font.h','rom_changed':False,'rom_sha256':rom_hash,'background_shift_y':'Per case: 16px for protection; 0px for kill objective','palette':'Existing item palette, icons retain native colours','cases':cases},ensure_ascii=False,indent=2)+'\n')
assert hashlib.sha256(ROM.read_bytes()).hexdigest()==rom_hash
print(json.dumps({'cases':len(cases),'rom_changed':False,'rom_sha256':rom_hash}))
