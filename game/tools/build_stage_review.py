"""Regenerate the local integrated-stage gallery from stage designs and measured reports.

Uses inline JSON and local PNG image elements, so file:// needs no fetch/server.
Never edits maps, resources or the game ROM.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'art/phases02-06-v1'
STAGES = [
    'phase02a-service-v1', 'phase02b-detour-v1', 'phase03-shelter-v1',
    'phase04-tunnels-v1', 'phase05-beacon-v1', 'phase06a-rescue-v1',
    'phase06b-withdrawal-v1',
]
MUSIC = {
    '02A': 'A Ladainha mantém o vínculo com a igreja que foi preservada.',
    '02B': 'Entardecer dá peso às perdas materiais e ao desvio após a explosão.',
    '03': 'Entardecer acompanha a fragilidade do abrigo e a espera do grupo.',
    '04': 'Breu acompanha o isolamento nos túneis de manutenção.',
    '05': 'A Ladainha une a Santa, a comunidade e a esperança do resgate.',
    '06A': 'Entardecer acompanha o alívio e a despedida de quem embarcou.',
    '06B': 'Breu acompanha a falha do sinal e a ruptura com Dinorah.',
}

HTML = r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plaguefall — capítulos 2 a 6 integrados</title>
<style>
:root{color-scheme:dark;--bg:#111615;--panel:#19201e;--line:#35413b;--ink:#eae9dc;--muted:#a8b2a6;--warm:#e1b46c;--mint:#83cfb5;--rose:#ed937a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input{font:inherit}button,a,input{touch-action:manipulation}a{color:var(--mint);text-underline-offset:4px}button{cursor:pointer;background:#232d28;color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:8px 13px}button:hover{border-color:var(--warm)}button:focus-visible,a:focus-visible,input:focus-visible,canvas:focus-visible{outline:2px solid var(--mint);outline-offset:4px}button[aria-pressed=true],button.active{background:var(--warm);border-color:var(--warm);color:#1b211c}header,main,footer{max-width:1480px;margin:auto;padding:28px 36px}header{padding-bottom:20px;border-bottom:1px solid var(--line)}.topline{display:flex;justify-content:space-between;gap:20px;align-items:center}.brand{letter-spacing:.2em;font-size:12px;color:var(--warm);font-weight:700}.pill{display:inline-block;border:1px solid var(--line);border-radius:30px;padding:4px 12px;font-size:12px;color:var(--muted)}h1{font:clamp(30px,4vw,52px)/1.12 Georgia,serif;letter-spacing:-.025em;margin:22px 0 14px}h2{font:30px/1.2 Georgia,serif;margin:0 0 12px}h3{font:21px/1.25 Georgia,serif;margin:0 0 14px}p{margin:0 0 14px}.lead{max-width:880px;color:var(--muted);font-size:16px}.chapters{display:flex;gap:8px;margin:4px 0 16px;flex-wrap:wrap}.chapters button{text-align:left;min-width:140px;flex:1}.chapters small{display:block;font-size:11px;letter-spacing:.1em;opacity:.75}.variantline{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:24px;min-height:40px}.variantline .note{color:var(--muted);font-size:13px}.variants{display:flex;gap:7px}.stagehead{display:flex;justify-content:space-between;gap:20px;align-items:start;margin:22px 0}.eyebrow{color:var(--warm);font-size:12px;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px}.spec{color:var(--muted);white-space:nowrap;font-size:13px}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:20px;align-items:start}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px;flex-wrap:wrap}.toolbar span{color:var(--muted);font-size:13px}.segmented{display:flex;gap:5px}.segmented button{padding:5px 12px}.scrollmap{overflow:auto;min-height:350px;background:#0b100e;border-radius:7px;padding:16px;display:grid;place-items:start center;max-height:800px}.scrollmap canvas{display:block;image-rendering:pixelated;cursor:crosshair;max-width:none}.overlaybar{display:flex;gap:14px;flex-wrap:wrap;margin-top:16px;font-size:12px}.overlaybar label{display:flex;align-items:center;gap:6px;color:var(--muted)}input[type=checkbox]{accent-color:var(--mint);width:15px;height:15px}.hint{color:var(--muted);font-size:12px;margin:12px 0 0}.camera{width:100%;height:auto;image-rendering:pixelated;display:block;background:#0b100e;border:1px solid #52655b;border-radius:4px}.controls{display:grid;gap:10px;margin-top:14px}.controls label{display:grid;grid-template-columns:35px 1fr 38px;gap:8px;align-items:center;color:var(--muted);font-size:12px}.controls output{text-align:right}.controls input{width:100%;accent-color:var(--warm)}.camera-tools{display:flex;gap:7px;margin-top:12px}.camera-tools button{flex:1;padding:6px 8px;font-size:12px}.side-note{color:var(--muted);font-size:12px;margin-top:14px}.storyrow{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:20px;margin-top:20px}.narrative{font-size:16px;max-width:850px}.objective{border-left:3px solid var(--warm);padding:10px 14px;background:#25291e;font-size:14px;margin:20px 0}.music{color:var(--muted);font-size:14px}.music strong{color:var(--mint)}.points{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:20px}.point{text-align:left;background:#131c17;padding:14px;display:grid;grid-template-columns:28px 1fr;gap:8px;align-items:start}.point .number{width:24px;height:24px;border-radius:50%;border:1px solid var(--warm);color:var(--warm);font-size:12px;display:grid;place-items:center}.point strong{display:block;font-size:13px;margin-bottom:5px}.point em{font-style:normal;color:var(--muted);font-size:12px;line-height:1.5;display:block}.point.active .number{border-color:#263025;color:#263025}.point.active em{color:#344332}.status{font-size:13px}.status dl{display:grid;grid-template-columns:1fr auto;gap:9px;margin:0}.status dt{color:var(--muted)}.status dd{margin:0;text-align:right}.rule{height:1px;background:var(--line);margin:18px 0}.good{color:var(--mint)}.pending{color:var(--warm)}.warning{border-left:2px solid var(--warm);padding-left:12px;color:var(--muted);font-size:12px;margin-top:18px}.evidence{margin-top:20px}.evidence img{image-rendering:pixelated;max-width:100%;display:block;border-radius:5px;margin:12px 0}.evidence ul{padding-left:20px;color:var(--muted);font-size:13px}.assets{margin-top:24px}.assets summary{cursor:pointer;color:var(--warm);font-size:16px;padding:16px 0}.assetgrid{display:grid;grid-template-columns:2fr 1fr;gap:20px;align-items:start}.assetbox{background:#0e1511;border:1px solid var(--line);border-radius:8px;padding:16px;overflow:auto}.assetbox img{display:block;image-rendering:pixelated;max-width:100%;height:auto}.assetbox h3{font-size:18px}.links{display:flex;flex-wrap:wrap;gap:10px 20px;padding:18px 0;font-size:13px}.technical{font-size:12px;color:var(--muted);max-width:900px}footer{border-top:1px solid var(--line);margin-top:30px;color:var(--muted);font-size:12px}.legend{color:var(--muted);font-size:12px;margin-top:12px}.legend b{font-weight:400}.green{color:#83cfb5}.orange{color:#ff9866}.yellow{color:#f3d891}.white{color:#f4f4e6}.empty{color:var(--muted)}
@media(max-width:1050px){header,main,footer{padding:22px}.workspace,.storyrow{grid-template-columns:minmax(0,1fr) 310px}.panel{padding:15px}.points{grid-template-columns:1fr}.chapters button{min-width:120px}.assetgrid{grid-template-columns:1fr}}@media(max-width:760px){.workspace,.storyrow{grid-template-columns:1fr}.topline,.stagehead{display:block}.topline .pill{margin-top:12px}.spec{margin-top:10px}.chapters{display:grid;grid-template-columns:repeat(2,1fr)}.chapters button{min-width:0}.scrollmap{place-items:start;min-height:280px}.camera{max-width:640px}.points{grid-template-columns:1fr}.assetgrid{grid-template-columns:1fr}.variantline{gap:8px}.variantline .note{width:100%}header,main,footer{padding:20px 16px}}
</style></head><body>
<header><div class="topline"><span class="brand">PLAGUEFALL / CENÁRIOS</span><a class="pill" href="../phase01-courtyard-v2/revisao.html">Fase 1 aprovada ↗</a></div>
<h1>Cinco capítulos.<br>Sete cenários no jogo.</h1><p class="lead">Da igreja ao resgate, cada cenário guarda uma parte da fuga. Explore os capítulos 2 a 6, compare as bifurcações e veja como os objetos contam a história.</p><span class="pill">Arte aprovada · integrada à ROM principal</span></header>
<main><nav class="chapters" id="chapters" aria-label="Capítulos"></nav><div class="variantline"><div class="variants" id="variants" aria-label="Variantes do capítulo"></div><span class="note" id="branchNote"></span></div>
<div class="stagehead"><div><div class="eyebrow" id="eyebrow"></div><h2 id="title"></h2></div><div class="spec" id="spec"></div></div>
<div class="workspace"><section class="panel"><div class="toolbar"><span>Planta completa · clique para posicionar a câmera</span><div class="segmented" aria-label="Ampliação do mapa"><button id="zoom1" aria-pressed="true">1×</button><button id="zoom2" aria-pressed="false">2×</button></div></div><div class="scrollmap" id="scrollmap"><canvas id="world" tabindex="0" aria-label="Mapa da fase; use as setas para mover a câmera"></canvas></div><div class="overlaybar"><label><input type="checkbox" id="showWalk">Área de movimento</label><label><input type="checkbox" id="showHazards">Perigos</label><label><input type="checkbox" id="showObjective">Objetivo e passagem</label><label><input type="checkbox" id="showStory">Pistas da história</label><label><input type="checkbox" id="showCamera" checked>Janela da câmera</label><label><input type="checkbox" id="showActor" checked>Personagem em escala real</label></div><div class="legend"><b class="green">Verde: movimento</b> · <b class="orange">Laranja/roxo: perigo</b> · <b class="yellow">Dourado: história</b> · <b class="white">Branco: objetivo</b></div><p class="hint">A imagem usa os tiles exportados em resolução nativa. A janela ao lado mostra o recorte de 320×224; o personagem mostra a escala32×48. Esta ferramenta é uma revisão da planta, sem simulação do jogo.</p></section>
<aside class="panel"><h3>O que cabe na tela</h3><canvas id="camera" class="camera" width="320" height="224" aria-label="Recorte da câmera em 320 por 224 pixels"></canvas><div class="controls"><label>X <input id="camX" type="range" min="0" value="0" step="1" aria-label="Posição horizontal da câmera"><output id="outX">0</output></label><label>Y <input id="camY" type="range" min="0" value="0" step="1" aria-label="Posição vertical da câmera"><output id="outY">0</output></label></div><div class="camera-tools"><button id="entryCamera">Entrada</button><button id="centerCamera">Centro</button><button id="exitCamera">Saída</button></div><p class="side-note">Clique nas pistas da história para aproximar a câmera de cada elemento. No mapa, as setas movem o recorte em passos de 8 pixels.</p></aside></div>
<div class="storyrow"><section class="panel"><div class="eyebrow">O ambiente conta</div><p id="narrative" class="narrative"></p><div class="objective" id="objective"></div><p id="music" class="music"></p><div class="points" id="points"></div></section><aside class="panel status"><h3>Estado da integração</h3><dl id="metrics"></dl><div class="rule"></div><div id="perf"></div><p class="warning">Cenários aprovados e ativos na campanha. A lava ocupa áreas de dano reais; a galeria permite conferir a escala do personagem e os percursos secos.</p></aside></div>
<section class="panel evidence" id="evidence" hidden></section>
<details class="assets"><summary>Peças do cenário e arquivos de produção</summary><div class="assetgrid"><div class="assetbox"><h3>Muros, chão e elementos</h3><a id="modulesLink"><img id="modulesImg" alt="Peças recortadas da fonte que formam o cenário"></a></div><div class="assetbox"><h3>Atlas de tiles</h3><a id="atlasLink"><img id="atlasImg" alt="Atlas exato de tiles de 8 por 8 pixels"></a></div></div><div class="links" id="links"></div><p class="technical" id="technical"></p></details>
</main><footer>Plaguefall · Cenários aprovados e integrados. Sete telas cobrem cinco capítulos e suas duas bifurcações. A galeria é regenerada a partir das plantas e relatórios, sem serviços externos.</footer>
<script>
'use strict';
const STAGES=__DATA__;
const $=id=>document.getElementById(id), chapterNames={2:'A retirada',3:'O novo abrigo',4:'Pelos túneis',5:'O sinal',6:'A resposta'};
let selected=0,scale=1,image=null,camX=0,camY=0,focusPoint=-1,loadSerial=0;
const world=$('world'),ctx=world.getContext('2d'),camera=$('camera'),cctx=camera.getContext('2d');
const actorScale=new Image();actorScale.onload=()=>draw();actorScale.src='../cangaco-protagonista-iso60-v2/heroi/heroi.png';
function text(el,value){el.textContent=value}
function current(){return STAGES[selected]}
function idOf(s){return String(s.design.id).toUpperCase()}
function path(s,name){return '../'+s.directory+'/'+name}
function makeLink(label,href){const a=document.createElement('a');a.textContent=label;a.href=href;return a}
function format(n){return Number(n).toLocaleString('pt-BR')}
function objectiveText(d){const o=d.objective||{},kind=o.kind||o.type;if(kind==='protect')return 'Proteja o sinalizador na Santa por '+o.target_seconds+' segundos. A proteção bem-sucedida conduz à rota 6A; a falha conduz à 6B.';return 'Abra a passagem derrotando '+o.target+' inimigos. Depois, siga para o capítulo '+Number((d.next||[])[0]||7)+'.'}
function branchText(d){if(d.chapter===2)return 'Duas consequências da decisão no pátio da igreja.';if(d.chapter===6)return 'Duas consequências da proteção do sinalizador.';return 'Uma arena para este capítulo.'}
function variantText(s){const id=idOf(s);return ({'02A':'2A · Igreja preservada','02B':'2B · Igreja danificada','06A':'6A · Resgate confirmado','06B':'6B · Retirada por terra'})[id]||'Capítulo '+s.design.chapter}
function setCamera(x,y){const d=current().design;camX=Math.max(0,Math.min(d.width-320,Math.round(x)));camY=Math.max(0,Math.min(d.height-224,Math.round(y)));$('camX').value=camX;$('camY').value=camY;text($('outX'),camX);text($('outY'),camY);draw()}
function pointCamera(p){setCamera(p[0]-160,p[1]-112)}
function overlay(c){const d=current().design;c.lineWidth=1;
 const box=(r,stroke,fill)=>{if(!r)return;c.fillStyle=fill;c.strokeStyle=stroke;c.fillRect(...r);c.strokeRect(r[0]+.5,r[1]+.5,r[2]-1,r[3]-1)};
 if($('showWalk').checked){box(d.walkable,'#83cfb5','rgba(74,195,143,.10)');(d.solids||[]).forEach(s=>box(s.rect||s,'#edc780','rgba(25,20,15,.55)'))}
 if($('showHazards').checked)(d.hazards||[]).forEach(h=>{box(h.rect,h.kind==='mud'?'#c6a4ef':'#ff9866',h.kind==='mud'?'rgba(152,95,209,.32)':'rgba(255,86,39,.30)')});
 if($('showObjective').checked){box(d.objective.rect,'#ffffe8','rgba(255,255,230,.22)');[[d.start,'ENTRADA','#83cfb5'],[d.exit,'PASSAGEM','#ebc586']].forEach(([p,label,col])=>{c.strokeStyle=col;c.lineWidth=2;c.strokeRect(p[0],p[1],16,16);c.font='bold 8px sans-serif';c.fillStyle='#10201b';c.fillRect(p[0]-1,p[1]-12,label.length*5+4,10);c.fillStyle=col;c.fillText(label,p[0]+1,p[1]-4)})}
 if($('showActor').checked&&actorScale.complete&&actorScale.naturalWidth)c.drawImage(actorScale,0,192,32,48,d.start[0]-8,d.start[1]-31,32,48);
 if($('showStory').checked)(d.story_elements||[]).forEach((e,i)=>{const [x,y,w,h]=e.rect;if(i===focusPoint)box(e.rect,'#ffe9a9','rgba(255,233,169,.18)');const px=x+w/2,py=y+h/2;c.beginPath();c.fillStyle='#142018';c.strokeStyle='#f3d891';c.lineWidth=1;c.arc(px,py,8,0,Math.PI*2);c.fill();c.stroke();c.font='bold 9px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillStyle='#f3d891';c.fillText(i+1,px,py+.5);c.textAlign='start';c.textBaseline='alphabetic'})
}
function draw(){const d=current().design;ctx.clearRect(0,0,world.width,world.height);ctx.imageSmoothingEnabled=false;if(image&&image.complete)ctx.drawImage(image,0,0);overlay(ctx);cctx.clearRect(0,0,320,224);cctx.imageSmoothingEnabled=false;cctx.drawImage(world,camX,camY,320,224,0,0,320,224);if($('showCamera').checked){ctx.strokeStyle='#ffffff';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.strokeRect(camX+.5,camY+.5,319,223);ctx.setLineDash([])}}
function showEvidence(s){const sec=$('evidence');sec.replaceChildren();const measured=s.validation.filter(v=>v.report&&v.current);sec.hidden=!measured.length;if(!measured.length)return;const h=document.createElement('h3');h.textContent='Testes na ROM principal';sec.append(h);const intro=document.createElement('p');intro.className='technical';intro.textContent='Partidas com vida, inimigos e controles normais. Os ensaios isolados preparam posições e cargas em RAM para conferir limites, tiros, perigos, câmera, pausa e VRAM. Não houve escrita de RAM durante as partidas nem durante a travessia seca.';sec.append(intro);measured.forEach(v=>{sec.append(makeLink('Relatório '+v.region.toUpperCase(),path(s,v.file)));const p=document.createElement('p');p.className='technical';p.textContent=describeReport(v.report);sec.append(p);if(v.movie){const video=document.createElement('video');video.src=path(s,v.movie);video.controls=true;video.muted=true;video.loop=true;video.style.width='100%';sec.append(video)}if(v.screenshot){const link=makeLink('',path(s,v.screenshot)),img=document.createElement('img');img.src=path(s,v.screenshot);img.alt='Captura real '+v.region.toUpperCase()+' — '+s.design.title;link.append(img);sec.append(link)}})}
function describeReport(r){const b=r.benchmark||[],m=r.ordinary_matches||[];return m.length+' partidas: '+m.map(v=>({completed:'concluída',defeat:'derrota',timeout:'tempo esgotado'})[v.result]||v.result).join(', ')+'. Carga de 4 inimigos e 6 tiros por grupo: '+[...new Set(b.map(v=>v.fps))].join(' / ')+' quadros/s. Colisões, perigos e pausa: '+(r.passed?'verificados.':'conferência pendente.')}
function select(index){selected=index;focusPoint=-1;const s=current(),d=s.design,r=s.export;const serial=++loadSerial;image=null;
document.querySelectorAll('#chapters button').forEach(b=>{const on=Number(b.dataset.chapter)===d.chapter;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on)});
$('variants').replaceChildren();STAGES.forEach((v,i)=>{if(v.design.chapter!==d.chapter)return;const b=document.createElement('button');b.textContent=variantText(v);b.setAttribute('aria-pressed',i===index);b.onclick=()=>select(i);$('variants').append(b)});
text($('branchNote'),branchText(d));text($('eyebrow'),'Capítulo '+d.chapter+' / Fase '+idOf(s));text($('title'),d.title);text($('spec'),d.width+' × '+d.height+' px · câmera a 60°');text($('narrative'),d.narrative);text($('objective'),objectiveText(d));
$('music').replaceChildren(document.createTextNode('Música existente: '));const music=document.createElement('strong');music.textContent=d.music;$('music').append(music,document.createTextNode('. '+s.music_reason));
$('points').replaceChildren();(d.story_elements||[]).forEach((e,i)=>{const b=document.createElement('button');b.className='point';b.setAttribute('aria-label',e.name+': '+e.meaning);const number=document.createElement('span');number.className='number';number.textContent=i+1;const wrap=document.createElement('span'),name=document.createElement('strong'),meaning=document.createElement('em');name.textContent=e.name;meaning.textContent=e.meaning;wrap.append(name,meaning);b.append(number,wrap);b.onclick=()=>{focusPoint=i;$('showStory').checked=true;document.querySelectorAll('.point').forEach((p,j)=>p.classList.toggle('active',i===j));pointCamera([e.rect[0]+e.rect[2]/2,e.rect[1]+e.rect[3]/2])};$('points').append(b)});
const metrics=[['Arte','Aprovada e integrada'],['Formato',d.width===d.height?'Praça ampla':'Corredor retangular'],['Área livre',(r.geometry.dry_area_fraction*100).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%'],['Passagem seca',r.geometry.entry_exit_reachable?'Verificada':'Pendente'],['Espaço dos tiles',r.tiles+' / '+r.tile_budget],['Paleta',r.palette_colors+' cores']];$('metrics').replaceChildren();metrics.forEach(([k,v])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;$('metrics').append(dt,dd)});
const measured=s.validation.filter(v=>v.report&&v.current);$('perf').replaceChildren();const perfTitle=document.createElement('strong');perfTitle.className=measured.length===2?'good':'pending';perfTitle.textContent=measured.length===2?'Testes na campanha: NTSC e PAL':'Testes na campanha: em andamento';const perfP=document.createElement('p');perfP.className='technical';perfP.style.marginTop='8px';perfP.textContent=measured.map(v=>v.region.toUpperCase()+': '+describeReport(v.report)).join(' ');$('perf').append(perfTitle,perfP);
for(const [img,link,file] of [['modulesImg','modulesLink','modules.png'],['atlasImg','atlasLink','tileset.png']]){$(img).src=path(s,file);$(link).href=path(s,file)}
$('links').replaceChildren();[['Mapa nativo','map-native.png'],['Fonte em alta resolução',d.source],['Projeto Tiled','stage.tmx'],['Tiles binários','hardware/tiles.bin'],['Mapa binário','hardware/map.bin'],['Paleta','hardware/palette.bin'],['Relatório de exportação','export.json'],['Planta e colisões','design.json'],['Documentação','README.md'],['Prompt e referências',s.prompt_file]].forEach(([label,file])=>$('links').append(makeLink(label,path(s,file))));
text($('technical'),format(r.tile_bytes)+' bytes de tiles + '+format(r.tilemap_bytes)+' bytes de mapa. '+r.geometry.reachable_dry_positions+' posições secas conectadas verificadas com uma base de 16×16 pixels. Uma redução da fonte até a resolução nativa; módulos copiados sem escala, tiles exatos e nenhuma substituição por aproximação. A janela de câmera desta página é uma ferramenta visual, sem medição de FPS.');
world.width=d.width;world.height=d.height;world.style.width=(d.width*scale)+'px';world.style.height=(d.height*scale)+'px';$('camX').max=d.width-320;$('camY').max=d.height-224;pointCamera(d.start);const next=new Image();next.onload=()=>{if(serial!==loadSerial)return;image=next;draw()};next.onerror=()=>{if(serial!==loadSerial)return;ctx.fillStyle='#e1b46c';ctx.font='14px sans-serif';ctx.fillText('Não foi possível abrir o mapa local.',20,30)};next.src=path(s,'map-native.png');showEvidence(s);history.replaceState(null,'','#fase-'+idOf(s).toLowerCase())
}
for(const ch of [2,3,4,5,6]){const b=document.createElement('button');b.dataset.chapter=ch;const small=document.createElement('small');small.textContent='CAPÍTULO '+ch;b.append(small,document.createTextNode(chapterNames[ch]));b.onclick=()=>select(STAGES.findIndex(s=>s.design.chapter===ch));$('chapters').append(b)}
for(const zoom of [1,2])$('zoom'+zoom).onclick=()=>{scale=zoom;for(const z of [1,2])$('zoom'+z).setAttribute('aria-pressed',z===zoom);world.style.width=world.width*scale+'px';world.style.height=world.height*scale+'px'};
for(const id of ['showWalk','showHazards','showObjective','showStory','showCamera','showActor'])$(id).onchange=draw;
$('camX').oninput=()=>setCamera(Number($('camX').value),camY);$('camY').oninput=()=>setCamera(camX,Number($('camY').value));
$('entryCamera').onclick=()=>pointCamera(current().design.start);$('exitCamera').onclick=()=>pointCamera(current().design.exit);$('centerCamera').onclick=()=>pointCamera([world.width/2,world.height/2]);
world.onclick=e=>{const r=world.getBoundingClientRect();pointCamera([(e.clientX-r.left)*world.width/r.width,(e.clientY-r.top)*world.height/r.height])};
world.onkeydown=e=>{const moves={ArrowLeft:[-8,0],ArrowRight:[8,0],ArrowUp:[0,-8],ArrowDown:[0,8]};if(moves[e.key]){e.preventDefault();const [dx,dy]=moves[e.key];setCamera(camX+dx,camY+dy)}};
const initial=STAGES.findIndex(s=>'#fase-'+idOf(s).toLowerCase()===location.hash);select(initial<0?0:initial);
</script></body></html>'''


def load():
    stages = []
    for directory in STAGES:
        folder = ROOT / 'art' / directory
        design = json.loads((folder / 'design.json').read_text())
        report = json.loads((folder / 'export.json').read_text())
        validation = []
        rom_hash = hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()
        for region in ('ntsc', 'pal'):
            rel = f'../phases02-06-v1/validation/{region}/report.json'
            file = folder/rel
            campaign = json.loads(file.read_text()) if file.exists() else None
            node = next((v for v in campaign.get('stages',[]) if v['id'].upper()==design['id'].upper()), None) if campaign else None
            measured = None
            if node:
                probes=node['isolated_probes']
                measured={'passed':all(v['passed'] for v in probes.values()),'region':region.upper(),
                          'benchmark':next((v['details'] for k,v in probes.items() if k.endswith('/stress') and v['passed']),[]),
                          'ordinary_matches':node['ordinary_matches'],'isolated_probes':probes}
            current = bool(campaign and campaign['passed'] and campaign['rom_sha256']==rom_hash and measured and measured['passed'])
            base = f'../phases02-06-v1/validation/{region}/{design["id"]}'
            screenshot=base+'-entry.png' if (folder/(base+'-entry.png')).exists() else None
            movie=base+'-glow.mp4' if region=='ntsc' and (folder/(base+'-glow.mp4')).exists() else None
            validation.append({'region':region,'file':rel,'report':measured,'current':current,'screenshot':screenshot,'movie':movie})
        prompt_file = 'prompts.json' if (folder / 'prompts.json').exists() else 'source/prompts.json'
        stages.append({'directory': directory, 'design': design, 'export': report, 'prompt_file': prompt_file,
                       'music_reason': MUSIC[str(design['id']).upper()], 'validation': validation})
    return stages


def build():
    stages = load()
    DEST.mkdir(exist_ok=True)
    inline = json.dumps(stages, ensure_ascii=False).replace('</', '<\\/')
    (DEST / 'revisao.html').write_text(HTML.replace('__DATA__', inline))
    manifest = {'status': 'approved-and-integrated', 'integrated': True,
                'approved_reference': '../phase01-courtyard-v2/revisao.html',
                'chapters': [2, 3, 4, 5, 6], 'screen_count': len(stages), 'stages': stages}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    checks=[]
    rom_hash=hashlib.sha256((ROOT/'out/release/rom.bin').read_bytes()).hexdigest()
    for s in stages:
        folder=ROOT/'art'/s['directory'];r=s['export'];d=s['design']
        binaries=all(hashlib.sha256((folder/'hardware'/name).read_bytes()).hexdigest()==value for name,value in r['export_sha256'].items())
        sources=hashlib.sha256((folder/'design.json').read_bytes()).hexdigest()==r['design_sha256'] and hashlib.sha256((folder/d['source']).read_bytes()).hexdigest()==r['source_sha256']
        sources=sources and all(hashlib.sha256((folder/name).read_bytes()).hexdigest()==value for name,value in r.get('module_source_sha256',{}).items())
        measured=all(v['current'] for v in s['validation'])
        checks.append({'id':d['id'],'tiles':r['tiles'],'native_world':r['world'],'binaries_and_sources_match':binaries and sources,
                       'within_budget':r['within_vram_budget'],'dry_path_connected':r['geometry']['connected_dry_floor'],'both_emulator_reports_current':measured})
    reports=[v['report'] for s in stages for v in s['validation'] if v['current']]
    cases=[b for r in reports for b in r['benchmark']]
    summary={'passed':all(all(c[k] for k in ('binaries_and_sources_match','within_budget','dry_path_connected','both_emulator_reports_current')) for c in checks),
             'production_rom_sha256':rom_hash,'production_rom_used':True,
             'integrated':True,'approval_date':'2026-10-21','chapters':[2,3,4,5,6],'screen_count':len(stages),'stages':checks,
             'emulator_report_count':len(reports),'measured_cases':len(cases),'measured_physical_frames':sum(c['physical_frames'] for c in cases),
             'ordinary_match_count':sum(len(r['ordinary_matches']) for r in reports),'scope':'Production ROM. Ordinary controller matches forbid RAM writes. Isolated probes/stress use explicit setup; terrain tests include lava damage/reset, mud slowdown/reset, dry controller routes, and exclusive-tile lava shimmer. Objective branches and legacy transition verified separately in campaign reports.',
             'regions':{region:{'fps_values':sorted(set(b['fps'] for r in reports if r['region']==region for b in r['benchmark'])),
                                'cpu_p95_max_pct':max((b['cpu_p95_pct'] for r in reports if r['region']==region for b in r['benchmark']),default=None)} for region in ('NTSC','PAL')}}
    (DEST/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    rows = '\n'.join(f"| {s['design']['id'].upper()} | {s['design']['title']} | {s['design']['width']}×{s['design']['height']} | {s['export']['tiles']} / 640 | {s['design']['music']} |" for s in stages)
    readme = f'''# Capítulos 2 a 6 — aprovados e integrados

[Abrir revisão interativa](revisao.html). As sete telas dos cinco capítulos foram aprovadas em21/10/2026 e integradas à campanha principal, incluindo2A/2B e6A/6B. [ROM principal](../../out/release/Plaguefall.bin).

| Fase | Cenário | Mundo | Tiles | Música existente |
|---|---|---|---|---|
{rows}

A galeria inclui mapa nativo em 1×/2×, câmera ajustável de 320×224, área de movimento, perigos, objetivo, passagem e pistas ambientais numeradas. Os links de cada tela levam ao atlas, aos módulos, à fonte, ao projeto Tiled e aos binários. A câmera é uma ferramenta de revisão visual; não simula combate ou mede performance. [Validação consolidada](validation.json).

Os relatórios de exportação verificam640 tiles,16 cores, reconstrução exata e passagem seca para base16×16. A instalação reordena os tiles sem alterar a imagem e reserva padrões exclusivos à lava: um brilho lento atualiza até128 bytes por quadro, sem mudar paletas, paredes, HUD ou personagens.

[Partidas e ensaios NTSC](validation/ntsc/report.json) · [Partidas e ensaios PAL](validation/pal/report.json). As partidas não permitem alterações em RAM; os ensaios isolados preparam carga/posições para conferir colisões, dano e recuperação, câmera, pausa, VRAM e FPS. Na fase5, a Santa usa a arte do mapa e um alvo lógico40×40; os inimigos conseguem atacá-la pelos quatro lados. As duas rotas de saída foram verificadas.

Os relatórios `validation/emulator-*.json` dentro das pastas individuais e [a consolidação anterior](validation/isolated-before-integration.json) são históricos de builds isolados. Os relatórios acima usam a ROM principal.

## Regenerar

Execute, na raiz do repositório:

```sh
python3 game/tools/build_stage_review.py
```

O gerador relê `design.json`, `export.json` e os relatórios da campanha em `validation/ntsc` e `validation/pal`. Escreve apenas esta galeria, README e [manifest.json](manifest.json). A página lê dados JSON embutidos e imagens locais por `Image`, sem `fetch`, dependências externas ou servidor.
'''
    (DEST / 'README.md').write_text(readme)
    print(json.dumps({'gallery': str(DEST / 'revisao.html'), 'screens': len(stages),
                      'html_sha256': hashlib.sha256((DEST / 'revisao.html').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    build()
