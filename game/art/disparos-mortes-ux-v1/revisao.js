'use strict';
// Local art review only. No production game scripts are imported.
const $=id=>document.getElementById(id);
const profiles=[['player','Damião','Metal + latão','rgba(145,72,36,1)'],['torreao','Torreão','Espinho vermelho · tiro único','#b62424'],['fuzileiro','Fuzileiro','Espinho âmbar · atira em movimento','#db6d00'],['artilheiro','Artilheiro','Espinho violeta · leque de 3','#6d4891'],['boss','Escorpião','Espinho ciano · leque do chefe','#24b6db']];
const assets={};
const sources={bg:'cenario',a:'disparos-8direcoes',b:'disparos-osseo',oldp:'atual-player',olde:'atual-enemy',leve:'morte-leve',blindado:'morte-blindado',...Object.fromEntries(profiles.map(p=>[p[0],p[0]==='player'?'hero':p[0]]))};
let style='a',running=!matchMedia('(prefers-reduced-motion: reduce)').matches,clock=0,last=0,ready=false;
for(const [r,[id,name,description,color]] of profiles.entries()){
 const card=document.createElement('article');card.className='sample';
 card.innerHTML=`<div class="portrait"><img class="enemy" src="assets/${id==='player'?'hero':id}.png" alt="${name}, sprite existente" style="width:${id==='player'?64:id==='boss'?96:id==='artilheiro'?72:48}px"></div><h3>${name}</h3><canvas id="shot-${r}" width="8" height="8" aria-label="Projétil de ${name}, ampliado oito vezes"></canvas><p><i class="swatch" style="background:${color}"></i>${description}</p>`;
 $('samples').append(card);
}
function drawShot(ctx,r,d,x,y,size=8){
 if(style==='actual'){ctx.drawImage(r===0?assets.oldp:assets.olde,Math.round(x),Math.round(y),size,size);return;}
 ctx.drawImage(assets[style],d*8,r*8,8,8,Math.round(x),Math.round(y),size,size);
}
function drawBoards(){
 const ctx=$('native').getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle='#354236';ctx.fillRect(0,0,320,58);ctx.font='10px monospace';ctx.fillStyle='#e0d7ba';
 profiles.forEach((p,r)=>{drawShot(ctx,r,0,28+r*62,17);ctx.fillText(['DAM','TOR','FUZ','ART','ESC'][r],22+r*62,44);const c=$('shot-'+r).getContext('2d');c.clearRect(0,0,8,8);drawShot(c,r,0,0,0);});
}
function paint(){
 if(!ready)return;
 const ctx=$('scene').getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(assets.bg,0,0);
 const mobs=[[48,73],[244,72],[49,170],[248,166]],target=[157,116];
 mobs.forEach(([x,y],n)=>{
  const im=assets[profiles[n+1][0]],s=im.width;ctx.drawImage(im,x-s/2,y-s/2);
  const angle=Math.atan2(target[1]-y,target[0]-x),d=(Math.round(angle/(Math.PI/4))+8)%8;
  const age=(clock*60+n*25)%80,dist=age*2;
  const len=Math.hypot(target[0]-x,target[1]-y);
  if(dist<len-10)drawShot(ctx,n+1,d,x+Math.cos(angle)*dist-4,y+Math.sin(angle)*dist-4);
 });
 const picked=$('direction').value,d=picked==='all'?Math.floor(clock/1.1)%8:Number(picked),a=d*Math.PI/4;
 const dist=(clock*60%42)*3;drawShot(ctx,0,d,target[0]+Math.cos(a)*dist-4,target[1]+Math.sin(a)*dist-4);
 // Review label sits in HUD space, outside the illustrated action.
 ctx.fillStyle='#17221d';ctx.fillRect(4,12,119,11);ctx.fillStyle='#e0d7ba';ctx.font='8px monospace';ctx.fillText('ESTUDO VISUAL / '+(style==='actual'?'ATUAL':style.toUpperCase()),7,20);
 const t=clock%1.8,frame=t<.69?0:t<.77?1:t<.95?2:3;
 const dc=$('death').getContext('2d');dc.imageSmoothingEnabled=false;dc.fillStyle='#303b32';dc.fillRect(0,0,320,70);
 for(const [id,s,x,scale] of [['leve',16,50,4],['blindado',32,205,2]])dc.drawImage(assets[id],frame*s,0,s,s,x,3,s*scale,s*scale);
 const cc=$('cheap').getContext('2d');cc.imageSmoothingEnabled=false;cc.fillStyle='#303b32';cc.fillRect(0,0,320,70);
 if(t<.65)cc.drawImage(assets.fuzileiro,132,3,64,64);
 else if(t<.85){
  const phase=Math.min(3,Math.floor((t-.65)/.05));const c=['#b62424','#914824','#49'+'9124'];
  for(let i=0;i<6;i++){const angle=i*Math.PI/3,rad=2+phase*1.5,x=7+Math.round(Math.cos(angle)*rad),y=7+Math.round(Math.sin(angle)*rad);cc.fillStyle=c[i%3];cc.fillRect(132+x*4,3+y*4,4,4);}
 }else cc.drawImage(assets.leve,48,0,16,16,132,3,64,64);
}
for(const id of ['actual','a','b'])$(id).onclick=()=>{style=id;for(const v of ['actual','a','b'])$(v).setAttribute('aria-pressed',String(v===id));$('description').textContent=id==='actual'?'Atual · Dois círculos sólidos, sem orientação ou material.':id==='a'?'A · Corpo colorido, ponta de quitina clara, bala curta de metal.':'B · Espinho de osso com ponta maior; bala metálica mais comprida.';drawBoards();paint();};
$('motion').textContent=running?'Pausar animação':'Reproduzir animação';
$('motion').onclick=()=>{running=!running;$('motion').textContent=running?'Pausar animação':'Reproduzir animação';};
$('direction').onchange=paint;
Promise.all(Object.entries(sources).map(([id,name])=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{assets[id]=im;resolve();};im.onerror=()=>reject(new Error('Imagem ausente: '+name));im.src='assets/'+name+'.png';}))).then(()=>{ready=true;document.body.dataset.ready='true';drawBoards();paint();}).catch(e=>{$('description').textContent=e.message;console.error(e);});
function loop(now){if(last&&running)clock+=Math.min((now-last)/1000,.05);last=now;paint();requestAnimationFrame(loop);}requestAnimationFrame(loop);
