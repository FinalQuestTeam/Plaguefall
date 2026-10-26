/* Visual proposal only. Composes generated art and existing game objects;
 * does not write production art, C geometry, ROM or active campaign metadata. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {createRequire}=require('module');
const req=createRequire('/Users/fabiocantarimmelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json');
const {createCanvas,loadImage,GlobalFonts}=req('@napi-rs/canvas');
GlobalFonts.registerFromPath('/System/Library/Fonts/Supplemental/Arial.ttf','ReviewFont');
const root=__dirname,game=path.resolve(root,'../..');
require('child_process').execFileSync('python3',[path.join(root,'export-existing-gate.py')],{stdio:'pipe'});
const gateOrigin=JSON.parse(fs.readFileSync(path.join(root,'gate-investigation.json')));
const C=(w,h)=>{const c=createCanvas(w,h);c.getContext('2d').imageSmoothingEnabled=false;return c;};
const g=c=>c.getContext('2d');
const crop=(im,x,y,w,h)=>{const c=C(w,h);g(c).drawImage(im,x,y,w,h,0,0,w,h);return c;};
const scale=(im,w,h)=>{const c=C(w,h);g(c).drawImage(im,0,0,w,h);return c;};
const stamp=(c,im,x,y)=>g(c).drawImage(im,x,y);
const tile=(c,im,x,y,w,h)=>{const q=g(c);q.save();q.beginPath();q.rect(x,y,w,h);q.clip();for(let yy=y;yy<y+h;yy+=im.height)for(let xx=x;xx<x+w;xx+=im.width)stamp(c,im,xx,yy);q.restore();};
const save=(name,c)=>{const p=path.join(root,name);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,(c.toBuffer?c:scale(c,c.width,c.height)).toBuffer('image/png'));};
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function silhouette(im,maxW,maxH){
 const c=scale(im,im.width,im.height),p=g(c).getImageData(0,0,c.width,c.height);let l=c.width,t=c.height,r=0,b=0;
 for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(p.data[(y*c.width+x)*4+3]>=184){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+1);b=Math.max(b,y+1);}
 if(r<=l)throw Error('Empty silhouette');
 for(let i=3;i<p.data.length;i+=4)p.data[i]=p.data[i]>=184?255:0;g(c).putImageData(p,0,0);
 const factor=Math.min(maxW/(r-l),maxH/(b-t));return scale(crop(c,l,t,r-l,b-t),Math.round((r-l)*factor),Math.round((b-t)*factor));
}
function route(solids,waypoints,bounds=[24,80,3047,271]){
 const [l,t,r,b]=bounds;const free=(x,y,margin=0)=>x>=l+margin&&y>=t+margin&&x+15<=r-margin&&y+15<=b-margin&&!solids.some(([a,c,w,h])=>x<a+w+margin&&x+16>a-margin&&y<c+h+margin&&y+16>c-margin);
 let result=[waypoints[0]];
 for(let i=1;i<waypoints.length;i++){
  const start=result.at(-1),goal=waypoints[i];if(!free(...start)||!free(...goal))throw Error('Invalid route endpoint '+JSON.stringify([start,goal]));
  const key=p=>p.join(','),prev=new Map([[key(start),null]]),queue=[start];let head=0;
  while(head<queue.length){const p=queue[head++];if(key(p)==key(goal))break;for(const n of [[p[0]+8,p[1]],[p[0]-8,p[1]],[p[0],p[1]+8],[p[0],p[1]-8]])if(!prev.has(key(n))&&free(...n,8)){prev.set(key(n),p);queue.push(n);}}
  if(!prev.has(key(goal)))throw Error('No safe route '+goal);
  const chunk=[];for(let p=goal;p;p=prev.get(key(p)))chunk.push(p);chunk.reverse();result.push(...chunk.slice(1));
 }
 const corners=result.filter((p,i)=>i==0||i==result.length-1||(p[0]-result[i-1][0])!=(result[i+1][0]-p[0])||(p[1]-result[i-1][1])!=(result[i+1][1]-p[1]));
 let checked=0;for(const p of result){if(!free(...p))throw Error('Route hits solid');checked++;}
 // Count every free8px grid position, then prove one connected component.
 const all=new Set();for(let y=t;y<=b-15;y+=8)for(let x=l;x<=r-15;x+=8)if(free(x,y))all.add(x+','+y);
 const visited=new Set([result[0].join(',')]),todo=[result[0]];let n=0;
 while(n<todo.length){const p=todo[n++];for(const q of [[p[0]+8,p[1]],[p[0]-8,p[1]],[p[0],p[1]+8],[p[0],p[1]-8]]){const k=q.join(',');if(all.has(k)&&!visited.has(k)){visited.add(k);todo.push(q);}}}
 if(visited.size!==all.size)throw Error('Disconnected open arena '+visited.size+'/'+all.size);
 return {points:corners.map(([x,y])=>[x+8,y+8]),checked_8px_steps:checked,connected_free_positions:visited.size,actor_feet:[16,16],extra_route_margin:8};
}
(async()=>{
 const load=p=>loadImage(path.join(game,p));
 const raw=await loadImage(path.join(root,'source/02-galeria-repetivel.png'));
 const native=scale(raw,512,320);
 // Complete two-arch panel keeps uniform scale, including its wall caps.
 // Broad plain material margins make the repeated module connect naturally.
 const wall=scale(crop(raw,0,0,raw.width,360),352,80);
 const wallProfile=crop(wall,0,0,16,80);
 const floor=crop(await load('art/phase04-tunnels-v1/map-native.png'),360,208,16,16);
 const curb=crop(native,0,248,64,8),water=crop(native,0,280,128,32),near=crop(native,0,256,64,8);
 const B=C(512,320);tile(B,wallProfile,0,0,512,80);stamp(B,wall,80,0);tile(B,floor,0,80,512,192);g(B).fillStyle='#242424';g(B).fillRect(0,0,512,12);
 tile(B,curb,0,272,512,8);tile(B,water,0,280,512,32);tile(B,near,0,312,512,8);
 const entry=silhouette(await loadImage(path.join(root,'source/01-acesso-escada-frontal.png')),104,144);
 const exit=silhouette(await loadImage(path.join(root,'source/03-acesso-abrigo.png')),128,120);
 const pump=silhouette(await loadImage(path.join(root,'source/04-bomba-transparente.png')),96,80);
 const crate=await load('art/phase03-three-segments-v1/objects/caixas.png');
 const rubble=await load('art/phase03-three-segments-v1/objects/entulho.png');
 const barrels=await load('art/phase01-pattern-v1/modules/barrels.png');
 const left=await load('art/campaign-corridors-v3/corrections/6A-guidebook/modules/side.png');
 const A=scale(B,512,320),D=scale(B,512,320);stamp(A,entry,56,24);stamp(D,exit,320,24);
 tile(A,left,0,80,16,192);tile(D,left,496,80,16,192);
 // The current shared export was replaced by a diagonal cycle2 asset.
 // Restore the previously authored vertical source, using its own registration.
 const gateClosed=await loadImage(path.join(root,'references/gate-vertical-0.png')),gateOpen=await loadImage(path.join(root,'references/gate-vertical-5.png'));
 // Guard the rendered dependency too: metadata alone did not prevent the
 // earlier diagonal replacement from carrying a vertical description.
 function postCenter(im,top,height){const p=g(scale(im,64,64)).getImageData(0,0,64,64).data;let lo=64,hi=-1;for(let y=top;y<top+height;y++)for(let x=0;x<64;x++)if(p[(y*64+x)*4+3]>=128){lo=Math.min(lo,x);hi=Math.max(hi,x);}if(hi<lo)throw Error('Missing gate support');return (lo+hi)/2;}
 const gateAxis={north:postCenter(gateClosed,0,9),south:postCenter(gateClosed,55,9)};
 if(Math.abs(gateAxis.north-gateAxis.south)>1)throw Error('Closed gate is no longer vertical');
 const valveClosed=await load('art/objective-sprites-v1/frames/valve-0.png'),valveOpen=await load('art/objective-sprites-v1/frames/valve-5.png');
 const objects={escada:entry,abrigo:exit,bomba:pump,caixas:crate,entulho:rubble,barris:barrels,portao:gateClosed,valvula:valveClosed};
 const defs={bomba:{foot:[8,24,pump.width-16,pump.height-24],shots:true},caixas:{foot:[2,18,28,12],shots:true},entulho:{foot:[6,16,36,12],shots:false},barris:{foot:[0,16,40,24],shots:false}};
 const placements=[{asset:'caixas',x:320,y:208},{asset:'bomba',x:648,y:88},{asset:'caixas',x:880,y:224},{asset:'entulho',x:1168,y:232},{asset:'caixas',x:1376,y:112},{asset:'bomba',x:1664,y:88},{asset:'entulho',x:1968,y:232},{asset:'caixas',x:2184,y:224},{asset:'barris',x:2368,y:112}];
 const baseSolids=[[56,80,entry.width,entry.height-56,true],[2880,80,exit.width,exit.height-56,true]];
 const propSolids=placements.map(p=>{const f=defs[p.asset].foot;return [p.x+f[0],p.y+f[1],f[2],f[3],defs[p.asset].shots];});
 const gates=[[832,112,32,64],[1856,192,32,64]],valves=[[792,128],[1816,208]],barriers=[];
 for(const [x,y,w,h] of gates){if(y>80)barriers.push([x,80,w,y-80,true]);if(y+h<272)barriers.push([x,y+h,w,272-y-h,true]);}
 const base=C(3072,320);[A,B,B,B,B,D].forEach((im,i)=>stamp(base,im,i*512,0));
 const masonry=crop(wall,0,24,16,32);
 function scene(variant,props=true,open=false){const out=scale(base,3072,320);if(props)for(const p of placements)stamp(out,objects[p.asset],p.x,p.y);
  if(variant==='6B'){
   for(const [x,y,w,h] of barriers){tile(out,masonry,x,y,w,h);tile(out,curb,x,y,w,8);}
   for(let i=0;i<2;i++){const [x,y,w,h]=gates[i],[vx,vy]=valves[i];stamp(out,open?gateOpen:gateClosed,x-16,y);stamp(out,open?valveOpen:valveClosed,vx-16,vy-16);}
  }return out;}
 const scenes={'6A':scene('6A'),'6B':scene('6B'), '6B-aberta':scene('6B',true,true),'sem-objetos':base,'6B-sem-objetos':scene('6B',false),'6B-aberta-sem-objetos':scene('6B',false,true)};
 const gatePixels=g(scale(gateClosed,64,64)).getImageData(0,0,64,64).data,closedPixels=g(scenes['6B']).getImageData(0,0,3072,320).data;
 let checkedGatePixels=0;for(const [x,y] of gates)for(let yy=0;yy<64;yy++)for(let xx=0;xx<64;xx++){const a=(yy*64+xx)*4,b=((y+yy)*3072+x-16+xx)*4;if(gatePixels[a+3]<128)continue;for(let k=0;k<3;k++)if(gatePixels[a+k]!==closedPixels[b+k])throw Error('Restored gate pixels changed in panorama');checkedGatePixels++;}
 const comparison=C(512,256);g(comparison).fillStyle='#18231f';g(comparison).fillRect(0,0,512,256);g(comparison).font='14px ReviewFont';g(comparison).fillStyle='#ead29f';g(comparison).fillText('Export atual · diagonal',16,24);g(comparison).fillText('Original restaurado · vertical',264,24);g(comparison).drawImage(await load('art/objective-sprites-v1/frames/gate-0.png'),32,40,192,192);g(comparison).drawImage(gateClosed,288,40,192,192);save('gate-orientation-before-after.png',comparison);
 const routes={};routes['6A']=route([...baseSolids,...propSolids],[[104,192],[560,216],[800,216],[1120,176],[1328,176],[1584,216],[1808,216],[2080,176],[2528,176],[2936,176]]);
 routes['6B']=route([...baseSolids,...propSolids,...barriers],[[104,192],[560,216],[784,152],[808,136],[896,136],[1120,176],[1584,216],[1808,232],[1832,216],[1912,216],[2080,176],[2528,176],[2936,176]]);
 const palette=JSON.parse(fs.readFileSync(path.join(game,'art/campaign-corridors-v3/corrections/6A-guidebook/material-checkpoint.json'))).palette;
 const lookup=new Map();function indexed(c){const o=scale(c,c.width,c.height),p=g(o).getImageData(0,0,o.width,o.height);for(let i=0;i<p.data.length;i+=4){if(!p.data[i+3])continue;const key=(p.data[i]<<16)|(p.data[i+1]<<8)|p.data[i+2];let chosen=lookup.get(key);if(chosen===undefined){let best=Infinity;chosen=0;palette.forEach((rgb,j)=>{const d=rgb.reduce((s,v,k)=>s+(v-p.data[i+k])**2,0);if(d<best){best=d;chosen=j;}});lookup.set(key,chosen);}for(let k=0;k<3;k++)p.data[i+k]=palette[chosen][k];}g(o).putImageData(p,0,0);return o;}
 function stats(c){const p=g(c).getImageData(0,0,c.width,c.height).data,tiles=new Set(),colors=new Set(),index=new Map(palette.map((rgb,i)=>[rgb.join(','),i]));for(let y=0;y<c.height;y+=8)for(let x=0;x<c.width;x+=8){let rows=[];for(let yy=0;yy<8;yy++){let s='';for(let xx=0;xx<8;xx++){const at=((y+yy)*c.width+x+xx)*4,rgb=Array.from(p.slice(at,at+3)).join(',');colors.add(rgb);s+=index.get(rgb).toString(16);}rows.push(s);}const a=rows.join(''),b=rows.map(r=>r.split('').reverse().join('')).join(''),d=rows.toReversed().join(''),e=rows.toReversed().map(r=>r.split('').reverse().join('')).join('');tiles.add([a,b,d,e].sort()[0]);}return {palette_colors:colors.size,unique_tiles_including_hv_reuse:tiles.size,scenery_only_4bpp_equivalent_bytes:tiles.size*32};}
 for(const [name,c] of Object.entries({A,B,C:D})){save('segments/'+name+'.png',c);save('palette-preview/segments/'+name+'.png',indexed(c));}
 for(const [name,c] of Object.entries(objects)){save('objects/'+name+'.png',c);save('palette-preview/objects/'+name+'.png',indexed(c));}
 const memory={};for(const [name,c] of Object.entries(scenes)){save('panorama-'+name+'.png',c);const p=indexed(c);save('palette-preview/panorama-'+name+'.png',p);memory[name]=stats(p);}
 const triple=C(2048,320);for(let i=0;i<4;i++)stamp(triple,B,i*512,0);save('meio-quatro-repeticoes.png',triple);save('palette-preview/meio-quatro-repeticoes.png',indexed(triple));
 const sheet=C(640,256);g(sheet).fillStyle='#18211f';g(sheet).fillRect(0,0,640,256);let n=0;for(const [name,im]of Object.entries(objects)){const x=16+(n%4)*160,y=8+Math.floor(n/4)*128;stamp(sheet,im,x,y);g(sheet).font='12px ReviewFont';g(sheet).fillStyle='#ead29f';g(sheet).fillText(name,x,y+116);n++;}save('objetos.png',sheet);
 const hero=crop(await load('art/cangaco-protagonista-iso60-v2/heroi/heroi.png'),0,192,32,48),dinorah=crop(await load('art/cangaco-parceira-iso60-v1/parceira/parceira.png'),0,192,32,48);save('references/damiao.png',hero);save('references/dinorah.png',dinorah);
 const cameras=[];for(const key of ['6A','6B','6B-aberta']){
  for(let x=0;x<=2752;x+=160)for(const y of [0,48,96]){const view=crop(scenes[key],x,y,320,224);g(view).fillStyle='#111a19';g(view).fillRect(0,0,320,24);g(view).font='10px ReviewFont';g(view).fillStyle='#ead29f';g(view).fillText('PRÉVIA VISUAL '+key+' · ESCOLTE DINORAH',8,15);const file=`cameras/${key}-x${x}-y${y}.png`;save(file,view);cameras.push({variant:key,x,y,file});}
  // Exact final frame is not a multiple of160.
  const view=crop(scenes[key],2752,0,320,224);g(view).fillStyle='#111a19';g(view).fillRect(0,0,320,24);g(view).fillStyle='#ead29f';g(view).font='10px ReviewFont';g(view).fillText('PRÉVIA VISUAL '+key+' · CHEGADA',8,15);save(`cameras/${key}-chegada.png`,view);
 }
 const label=(c,t,x,y)=>{g(c).font='14px ReviewFont';g(c).fillStyle='#ead29f';g(c).fillText(t,x,y);};
 const board=C(1536,1104);g(board).fillStyle='#111a19';g(board).fillRect(0,0,1536,1104);
 for(const [i,[key,name]] of [['A','A · ENTRADA DOS ESGOTOS'],['B','B · GALERIA REPETÍVEL'],['C','C · ACESSO AO ABRIGO']].entries()){const im={A,B,C:D}[key];label(board,name,i*512+16,24);stamp(board,im,i*512,40);}
 label(board,'6A · A + B + B + B + B + C · 3072 × 320',16,394);g(board).drawImage(scenes['6A'],0,408,1536,160);
 label(board,'6B · MESMA BASE + DOIS CONJUNTOS DE PRESSÃO',16,610);g(board).drawImage(scenes['6B'],0,624,1536,160);
 label(board,'ENTRADA · DETALHE NATIVO',16,830);label(board,'MEIO · DETALHE NATIVO',528,830);label(board,'CHEGADA · DETALHE NATIVO',1040,830);
 for(const [i,x]of [0,560,2752].entries())g(board).drawImage(scenes['6A'],x,0,320,224,i*512,848,320,224);save('representacao-visual.png',board);
 // Show every join at native pixel resolution, and compare repeated copies.
 const standard=C(256,320);stamp(standard,crop(B,384,0,128,320),0,0);stamp(standard,crop(B,0,0,128,320),128,0);
 const standardBytes=Buffer.from(g(standard).getImageData(0,0,256,320).data);
 const proof=[];for(const x of [512,1024,1536,2048,2560]){const join=crop(base,x-128,0,256,320);save(`seams/emenda-${x}.png`,join);proof.push({x,matches_canonical_B_to_B_join:Buffer.from(g(join).getImageData(0,0,256,320).data).equals(standardBytes)});}
 if(proof.some(p=>!p.matches_canonical_B_to_B_join))throw Error('A/B or B/C connection differs from B/B');
 const manifest={status:'visual_proposal_not_integrated',world:[3072,320],module:[512,320],sequence:['A','B','B','B','B','C'],bounds:[24,80,3047,271],start:[104,192],exit:[2912,144,64,48],segments:{A:{file:'segments/A.png',landmark:[56,24,entry.width,entry.height]},B:{file:'segments/B.png',repeat:4},C:{file:'segments/C.png',landmark:[2880,24,exit.width,exit.height]}},objects:defs,placements,base_solids:baseSolids,prop_solids:propSolids,pressure:{gates,valves,barriers,wait_points:[[752,208],[1776,144]],working_feet:[[784,152],[1808,232]],native_frames_reused:true,gate_source:gateOrigin.restored_source,gate_source_sha256:gateOrigin.restored_source_sha256,current_diagonal_export_reused:false,gate_support_centers:gateAxis,restored_gate_pixels_checked:checkedGatePixels},routes,seams:proof,palette,memory_estimate:memory,memory_target:{scene_tiles_6A:640,scene_tiles_6B:384,mechanism_reserved_tiles_6B:256,resident_total:640,not_proven_by_RGB_proposal:true,full_map_bytes:30720},camera_samples:cameras,source_generation:{tool:'built-in image_gen.imagegen',prompts:'prompts/',rejected:['source/01-acesso-escada.png: incompatible diagonal camera; replaced by frontal module'],generated_art_saved:'source/'},assembly:'Node canvas: shared material strips, complete transparent landmarks, identical repeated B, native prop reuse, nearest scaling, alpha threshold184 and separate fixed16color palette preview.',implementation_changed:false,production_rom_sha256:hash(path.join(game,'out/release/Plaguefall.bin'))};
 fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({seams:proof,memory,routes},null,2));
})().catch(e=>{console.error(e);process.exit(1);});
