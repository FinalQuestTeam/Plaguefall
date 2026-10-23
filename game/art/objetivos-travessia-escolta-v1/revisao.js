'use strict';
// Standalone storyboard, never imports game runtime or writes a ROM.
const $=id=>document.getElementById(id),images={};
let mode='reach',playing=false,progress=.27,last=0,loaded=false,announced='';
const sources={tunel:'tunel',retirada:'retirada',damiao:'damiao',dinorah:'dinorah',enemy:'inimigo',shots:'disparos',font:'font'};
const copy={
 reach:{maptitle:'Fase 4 · Túneis de manutenção',title:'Chegue à saída',body:'Damião atravessa de A até B. Eliminar inimigos abre espaço, mas não é a condição de vitória.',camera:'A seta no HUD aponta para a saída quando ela está fora da câmera. Ao se aproximar, o marcador aparece sobre o destino.',briefing:'CHEGUE A SAIDA DOS TUNEIS.\nPROCURE O SINAL AMBAR.',win:'Os pés entram na área B e permanecem por 0,4 segundo. Conclusão automática, sem botão novo e sem exigir matar todos.'},
 escort:{maptitle:'Fase 6B · Retirada por terra',title:'Cubra Dinorah até a retirada',body:'Dinorah contorna os perigos, faz pausas e dá tiros de apoio. Damião precisa abrir espaço e acompanhar o avanço.',camera:'Enquadramento compartilhado, sem zoom. Dinorah espera quando Damião se afasta demais. A barra acompanha a personagem; o HUD identifica sua vida.',briefing:'ESCOLTE DINORAH ATE A RETIRADA.\nFIQUE PERTO E DE COBERTURA.',win:'Dinorah entra em B; Damião chega a até 64 px. Após 0,4 s com os dois vivos, a escolta termina, mesmo que ainda haja inimigos.'}
};
function timeline(){
 const m=PROPOSAL.models[mode],a=[];let distance=0,time=0;
 function add(type,from,to,duration,extra={}){a.push({type,from,to,start:time,end:time+duration,distance,...extra});time+=duration;}
 for(let i=0;i<m.points.length-1;i++){
  const from=m.points[i],to=m.points[i+1],len=Math.hypot(to[0]-from[0],to[1]-from[1]);
  add('move',from,to,len/(mode==='escort'?36:80),{leg:i,len});distance+=len;
  if(mode==='escort'){
   if(m.pauses[String(i+1)])add('pause',to,to,m.pauses[String(i+1)],{leg:i});
   if(i+1===4)add('fire',to,to,.6,{leg:i});
   if(i+1===5)add('wait',to,to,2,{leg:i});
  }
 }
 const end=m.points.at(-1);add('arrive',end,end,1.2);return {segments:a,total:time,distance};
}
function onRoute(distance){
 const pts=PROPOSAL.models[mode].points;
 for(let i=0;i<pts.length-1;i++){
  const a=pts[i],b=pts[i+1],len=Math.hypot(b[0]-a[0],b[1]-a[1]);
  if(distance<=len)return [a[0]+(b[0]-a[0])*Math.max(0,distance)/len,a[1]+(b[1]-a[1])*Math.max(0,distance)/len];
  distance-=len;
 }return pts.at(-1);
}
function pose(){
 const t=timeline(),moment=Math.min(t.total-.00001,progress*t.total),s=t.segments.find(s=>moment<s.end)||t.segments.at(-1),f=(moment-s.start)/(s.end-s.start);
 const focus=[s.from[0]+(s.to[0]-s.from[0])*f,s.from[1]+(s.to[1]-s.from[1])*f];
 const angle=Math.atan2(s.to[1]-s.from[1],s.to[0]-s.from[0]),dir=s.type==='move'?(Math.round(angle/(Math.PI/4))+10)%8:2;
 const distance=s.distance+(s.len||0)*f;
 let hero=focus;
 if(mode==='escort'){
  if(distance<32){const a=PROPOSAL.models[mode].points[0];hero=[a[0],a[1]+32*(1-distance/32)];}
  else hero=onRoute(Math.max(0,distance-(s.type==='wait'?180:36)));
 }
 const labels={move:mode==='escort'?'DINORAH AVANCANDO':'AVANCE ATE A SAIDA',pause:'CONFERINDO PASSAGEM · ME DA COBERTURA',fire:'TIRO DE APOIO · DEPOIS RETOMA',wait:'ESPERANDO DAMIAO · APROXIME-SE',arrive:mode==='escort'?'DINORAH CHEGOU EM SEGURANCA':'PASSAGEM ALCANCADA'};
 return {s,f,focus,hero,dir,distance,label:labels[s.type],moment};
}
function font(ctx,text,x,y){
 for(const c of text.toUpperCase()){
  const n=c.charCodeAt(0)-32;if(n>=0&&n<96)ctx.drawImage(images.font,(n%16)*8,Math.floor(n/16)*8,8,8,Math.round(x),Math.round(y),8,8);x+=8;
 }
}
function holes(ctx,m){
 for(const [x,y,w,h] of m.holes){
  ctx.fillStyle='#15201b';ctx.fillRect(x,y,w,h);ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();ctx.strokeStyle='#513f51';ctx.lineWidth=1;
  for(let k=-h;k<w;k+=8){ctx.beginPath();ctx.moveTo(x+k,y);ctx.lineTo(x+k+h,y+h);ctx.stroke();}
  ctx.restore();ctx.strokeStyle='#b58fba';ctx.setLineDash([3,3]);ctx.strokeRect(x+.5,y+.5,w-1,h-1);ctx.setLineDash([]);
 }
}
function zone(ctx,m){
 const [x,y,w,h]=m.exit;ctx.strokeStyle='#e5b76b';ctx.lineWidth=2;ctx.strokeRect(x,y,w,h);
 ctx.fillStyle='#e5b76b';ctx.fillRect(x+w/2-2,y+6,4,7);ctx.fillRect(x+w/2-5,y+11,10,3);font(ctx,'B',x+w/2-4,y+20);
}
function actor(ctx,name,p,dir,frame){
 const x=Math.round(p[0]-16),y=Math.round(p[1]-39);
 ctx.fillStyle='#172019';ctx.fillRect(x+10,y+44,12,3);
 ctx.drawImage(images[name],dir*32,frame*48,32,48,x,y,32,48);
 if($('collision').checked){ctx.strokeStyle=name==='dinorah'?'#ffb363':'#7fc9cd';ctx.lineWidth=1;ctx.strokeRect(p[0]-8+.5,p[1]-8+.5,15,15);}
}
function world(ctx,m,p,preview){
 ctx.imageSmoothingEnabled=false;ctx.drawImage(images[m.map],0,0);holes(ctx,m);zone(ctx,m);
 if(!preview&&$('route').checked){
  ctx.strokeStyle='#8ac5bd';ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.beginPath();m.points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();ctx.setLineDash([]);
  m.points.forEach(([x,y],i)=>{ctx.fillStyle='#8ac5bd';ctx.fillRect(x-2,y-2,4,4);if(m.pauses[String(i)]){ctx.strokeStyle='#e5b76b';ctx.strokeRect(x-7,y-7,14,14);}});
  font(ctx,'A',m.points[0][0]-4,m.points[0][1]+16);
 }
 const frame=p.s.type==='move'?2+Math.floor(p.moment*6)%4:Math.floor(p.moment*2)%2;
 const actors=mode==='escort'?[['dinorah',p.focus,p.dir,frame],['damiao',p.hero,p.dir,p.s.type==='wait'?0:frame]]:[['damiao',p.focus,p.dir,frame]];
 actors.sort((a,b)=>a[1][1]-b[1][1]);for(const a of actors)actor(ctx,...a);
 if(mode==='escort'){
  const [x,y]=p.focus;ctx.fillStyle='#e0d7ba';ctx.fillRect(Math.round(x-16),Math.round(y-49),32,5);ctx.fillStyle='#739146';ctx.fillRect(Math.round(x-15),Math.round(y-48),30,3);
  if(p.s.type==='fire'){
   const ex=x+72,ey=y;ctx.drawImage(images.enemy,0,64,16,16,ex-8,ey-16,16,16);
   const dist=12+p.f*44;ctx.drawImage(images.shots,0,0,8,8,x+dist,y-14,8,8);
   if(p.f<.25){ctx.fillStyle='#e0d7ba';ctx.fillRect(x+14,y-12,3,2);}
  }
 }
}
function camera(m,p){
 let x=p.hero[0]-160,y=p.hero[1]-120;
 if(mode==='escort'){x=(p.hero[0]+p.focus[0])/2-160;y=(p.hero[1]+p.focus[1])/2-120;}
 return [Math.max(0,Math.min(m.width-320,Math.round(x))),Math.max(0,Math.min(m.height-224,Math.round(y)))];
}
function draw(){
 if(!loaded)return;const m=PROPOSAL.models[mode],p=pose(),cam=camera(m,p),ctx=$('map').getContext('2d');
 ctx.fillStyle='#142018';ctx.fillRect(0,0,512,320);world(ctx,m,p,false);
 ctx.strokeStyle='#e0d7ba';ctx.setLineDash([6,3]);ctx.strokeRect(cam[0]+.5,cam[1]+.5,319,223);ctx.setLineDash([]);
 const vc=$('view').getContext('2d');vc.fillStyle='#142018';vc.fillRect(0,0,320,224);vc.save();vc.translate(-cam[0],-cam[1]);world(vc,m,p,true);vc.restore();
 vc.fillStyle='#142018';vc.fillRect(0,0,320,9);
 const [gx,gy,gw,gh]=m.exit;const off=gx<cam[0]||gx+gw>cam[0]+320||gy<cam[1]||gy+gh>cam[1]+224;
 const arrow=off?(gx>cam[0]+160?'>':'<'):'';font(vc,mode==='escort'?'DINA 100 '+arrow:'SAIDA '+arrow,8,0);font(vc,'B:2',144,0);font(vc,'HP:100',264,0);
 if(mode==='escort'&&p.s.type!=='move'){
  const words={pause:'CONFERINDO PASSAGEM',fire:'COBERTURA',wait:'APROXIME-SE',arrive:'DINORAH A SALVO'};
  vc.fillStyle='#142018';vc.fillRect(0,208,320,16);font(vc,words[p.s.type],8,212);
 }
 if(mode==='reach'&&p.s.type==='arrive'){vc.fillStyle='#142018';vc.fillRect(0,208,320,16);font(vc,'PASSAGEM ALCANCADA',8,212);}
 if(p.label!==announced){$('status').textContent=p.label;announced=p.label;}
 $('timeline').value=Math.round(progress*1000);
}
function presets(){
 const t=timeline(),items=mode==='escort'?[['Início',t.segments[0],0],['Contornar buraco',t.segments.find(s=>s.type==='move'&&s.leg===2),.5],['Pausa de cobertura',t.segments.find(s=>s.type==='pause'),.5],['Disparo',t.segments.find(s=>s.type==='fire'),.35],['Esperar Damião',t.segments.find(s=>s.type==='wait'),.5],['Chegada',t.segments.at(-1),.75]]:[['Início',t.segments[0],0],['Desvio',t.segments.find(s=>s.leg===4),.5],['Chegada',t.segments.at(-1),.75]];
 $('presets').replaceChildren();for(const [label,s,f] of items){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{playing=false;progress=(s.start+(s.end-s.start)*f)/t.total;syncPlay();draw();};$('presets').append(b);}
}
function syncPlay(){$('play').textContent=playing?'Pausar percurso':'Reproduzir percurso';}
function select(id){
 mode=id;progress=id==='escort'?.38:.27;playing=false;syncPlay();announced='';
 for(const n of ['reach','escort'])$(n).setAttribute('aria-pressed',String(n===id));
 const c=copy[id];$('maptitle').textContent=c.maptitle;$('goal-title').textContent=c.title;$('goal-copy').textContent=c.body;$('camera-copy').textContent=c.camera;$('briefing').innerText=c.briefing;$('win-copy').textContent=c.win;presets();draw();
}
$('reach').onclick=()=>select('reach');$('escort').onclick=()=>select('escort');
$('timeline').oninput=e=>{progress=Number(e.target.value)/1000;playing=false;syncPlay();draw();};
$('play').onclick=()=>{playing=!playing;syncPlay();};$('reset').onclick=()=>{progress=0;playing=false;syncPlay();draw();};
$('route').onchange=draw;$('collision').onchange=draw;
Promise.all(Object.entries(sources).map(([key,name])=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{images[key]=im;resolve();};im.onerror=()=>reject(new Error('Imagem ausente: '+name));im.src='assets/'+name+'.png';}))).then(()=>{loaded=true;document.body.dataset.ready='true';select('reach');}).catch(e=>{$('status').textContent=e.message;console.error(e);});
function loop(now){if(last&&playing){progress+=Math.min((now-last)/1000,.1)/timeline().total;if(progress>=1){progress=1;playing=false;syncPlay();}draw();}last=now;requestAnimationFrame(loop);}requestAnimationFrame(loop);
