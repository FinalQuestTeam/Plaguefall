/* Review renderer: compose imagegen assets and the original church sprite.
 * Does not write production resources, phase geometry or ROMs.
 */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {createRequire}=require('module');
const bundled=process.env.CODEX_NODE_MODULES || '/Users/fabiocantarimmelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const req=createRequire(path.join(bundled,'package.json'));
const {createCanvas,loadImage,GlobalFonts}=req('@napi-rs/canvas');
GlobalFonts.registerFromPath('/System/Library/Fonts/Supplemental/Arial.ttf','ReviewFont');
const root=__dirname,game=path.resolve(root,'../..');
for(const d of ['segments','objects','cameras','seams'])fs.mkdirSync(path.join(root,d),{recursive:true});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const canvas=(w,h)=>{const c=createCanvas(w,h);c.getContext('2d').imageSmoothingEnabled=false;return c;};
const cx=c=>c.getContext('2d');
const save=(name,c)=>fs.writeFileSync(path.join(root,name),c.toBuffer('image/png'));
const pixels=c=>cx(c).getImageData(0,0,c.width,c.height).data;
const crop=(im,x,y,w,h)=>{const c=canvas(w,h);cx(c).drawImage(im,x,y,w,h,0,0,w,h);return c;};
const scaled=(im,w,h)=>{const c=canvas(w,h);cx(c).drawImage(im,0,0,w,h);return c;};
const tile=(c,im,x,y,w,h)=>{const g=cx(c);g.save();g.beginPath();g.rect(x,y,w,h);g.clip();for(let yy=y;yy<y+h;yy+=im.height)for(let xx=x;xx<x+w;xx+=im.width)g.drawImage(im,xx,yy);g.restore();};
const stamp=(c,im,x,y)=>cx(c).drawImage(im,x,y);
const title=(c,t,x,y)=>{const g=cx(c);g.fillStyle='#f8e7bd';g.font='14px ReviewFont';g.fillText(t,x,y);};

(async()=>{
 const source={};
 for(const [key,file] of Object.entries({A:'01-inicio-fundo',B:'02-rua-repetivel',C:'03-chegada-galpao'}))source[key]=scaled(await loadImage(path.join(root,'source',file+'.png')),512,320);
 const church=await loadImage(path.join(root,'references/igreja-original.png'));
 const damaged=crop(await loadImage(path.join(root,'references/patio-destruido-original.png')),16,0,200,112);
 const borderLeft=await loadImage(path.join(game,'art/phase01-pattern-v1/modules/side-left.png'));
 const borderRight=await loadImage(path.join(game,'art/phase01-pattern-v1/modules/side-right.png'));
 // Every segment shares the same street renderer. Only its upper architecture differs.
 // Fixed repeating strips keep pavement/curbs in the same phase at all four joins.
 const road=crop(source.B,32,160,64,32);
 const upperCurb=crop(source.B,32,132,64,12);
 const lowerCurb=crop(source.B,32,264,64,8);
 const foreground=crop(source.B,16,272,128,48);
 const connection=crop(source.B,0,0,32,132);
 function module(key){
  const c=canvas(512,320);stamp(c,source[key],0,0);
  tile(c,road,0,144,512,120);tile(c,upperCurb,0,132,512,12);
  tile(c,lowerCurb,0,264,512,8);tile(c,foreground,0,272,512,48);
  stamp(c,connection,0,0);stamp(c,connection,480,0);
  return c;
 }
 const B=module('B'),A=module('A'),AD=module('A'),C=module('C');
 stamp(A,church,48,24);stamp(AD,damaged,48,24);
 tile(A,borderLeft,0,132,16,188);tile(AD,borderLeft,0,132,16,188);
 tile(C,borderRight,496,132,16,188);
 const base={A,AD,B,C};
 for(const [file,c] of Object.entries({'01-inicio-igreja-inteira':A,'01-inicio-igreja-destruida':AD,'02-rua-repetivel':B,'03-chegada-galpao':C}))save('segments/'+file+'.png',c);
 // Alpha-test at export removes the generator's soft halo: the game requires solid pixels.
 const atlas=await loadImage(path.join(root,'source/04-objetos-rua.png'));
 const defs={
  van:{src:[24,224,568,424],size:[80,56],foot:[8,38,64,16],shots:true},
  poste:{src:[696,24,160,624],size:[16,80],foot:[2,68,12,12],shots:false},
  cacamba:{src:[1016,248,512,416],size:[48,40],foot:[4,24,40,12],shots:true},
  entulho:{src:[24,672,528,336],size:[48,32],foot:[6,16,36,12],shots:false},
  caixas:{src:[592,648,432,368],size:[32,32],foot:[2,18,28,12],shots:true},
  fragmentos:{src:[1096,736,416,272],size:[24,16],foot:null,shots:false}
 };
 const objects={};
 for(const [name,d] of Object.entries(defs)){
  const s=crop(atlas,...d.src);const g=cx(s),im=g.getImageData(0,0,s.width,s.height);
  for(let i=3;i<im.data.length;i+=4)im.data[i]=im.data[i]>=184 ? 255 : 0;
  g.putImageData(im,0,0);objects[name]=scaled(s,...d.size);save('objects/'+name+'.png',objects[name]);
 }
 const placements=[
  {asset:'entulho',x:344,y:216},{asset:'poste',x:440,y:72},
  {asset:'poste',x:560,y:72},{asset:'van',x:648,y:160},{asset:'fragmentos',x:792,y:220},{asset:'entulho',x:936,y:240},
  {asset:'entulho',x:1120,y:240},{asset:'poste',x:1288,y:72},{asset:'cacamba',x:1408,y:164},{asset:'fragmentos',x:1480,y:232},
  {asset:'van',x:1664,y:212},{asset:'poste',x:1840,y:72},{asset:'caixas',x:1944,y:160},{asset:'fragmentos',x:1784,y:236},
  {asset:'entulho',x:2128,y:208},{asset:'poste',x:2192,y:72}
 ];
 function panorama(destroyed,props){const c=canvas(2560,320);[destroyed?AD:A,B,B,B,C].forEach((s,i)=>stamp(c,s,i*512,0));if(props)for(const p of [...placements].sort((a,b)=>(a.y+defs[a.asset].size[1])-(b.y+defs[b.asset].size[1])))stamp(c,objects[p.asset],p.x,p.y);return c;}
 const intact=panorama(false,true),ruined=panorama(true,true),empty=panorama(false,false),emptyDamaged=panorama(true,false);
 save('05-panorama-intacto.png',intact);save('05-panorama-destruido.png',ruined);save('05-panorama-sem-objetos.png',empty);save('05-panorama-intacto-sem-objetos.png',empty);save('05-panorama-destruido-sem-objetos.png',emptyDamaged);
 const triple=canvas(1536,320);for(let i=0;i<3;i++)stamp(triple,B,i*512,0);save('02-rua-tres-repeticoes.png',triple);
 const propSheet=canvas(512,224);const pg=cx(propSheet);pg.fillStyle='#22312e';pg.fillRect(0,0,512,224);
 let j=0;for(const [name,obj] of Object.entries(objects)){const x=24+(j%3)*168,y=24+Math.floor(j/3)*104;stamp(propSheet,obj,x,y);title(propSheet,name,x,y+92);j++;}save('04-objetos-rua.png',propSheet);
 const coll=canvas(2560,320);stamp(coll,intact,0,0);const cg=cx(coll);cg.fillStyle='#080e18aa';cg.fillRect(0,0,2560,320);
 const solids=[];
 for(const p of placements){const d=defs[p.asset];if(!d.foot)continue;const [fx,fy,w,h]=d.foot;const rect=[p.x+fx,p.y+fy,w,h];solids.push({...p,rect,blocksShots:d.shots});cg.fillStyle=d.shots?'#ff9250a0':'#e9c66ba0';cg.fillRect(...rect);cg.strokeStyle=d.shots?'#ff9250':'#e9c66b';cg.strokeRect(...rect);}
 const route=[[264,184],[400,184],[560,224],[792,224],[1000,208],[1256,208],[1472,232],[1600,184],[1832,184],[2056,184],[2288,184],[2424,176]];
 cg.strokeStyle='#70e9c4';cg.lineWidth=3;cg.beginPath();route.forEach(([x,y],i)=>i?cg.lineTo(x,y):cg.moveTo(x,y));cg.stroke();
 cg.font='16px monospace';cg.fillStyle='#70e9c4';cg.fillText('INÍCIO',264,168);cg.fillText('CHEGADA',2380,160);
 for(let x=512;x<2560;x+=512){cg.strokeStyle='#ffffff66';cg.beginPath();cg.moveTo(x,0);cg.lineTo(x,320);cg.stroke();}
 save('06-colisoes.png',coll);
 const cameraList=[];
 for(const y of [0,48,96])for(let x=0;x<=2240;x+=160){const camera=crop(intact,x,y,320,224);const g=cx(camera);g.fillStyle='#151a20';g.fillRect(0,0,320,24);g.font='10px monospace';g.fillStyle='#e9c66b';g.fillText('REVISÃO VISUAL · FASE 3',8,15);const file=`cameras/x${String(x).padStart(4,'0')}-y${y}.png`;save(file,camera);cameraList.push({x,y,file});}
 const landmarks=[{name:'Igreja',x:0,y:0},{name:'Rua B1',x:544,y:0},{name:'Rua B2',x:1120,y:0},{name:'Rua B3',x:1632,y:0},{name:'Galpão',x:2240,y:0}];
 const board=canvas(1600,272);const bg=cx(board);bg.fillStyle='#151a20';bg.fillRect(0,0,1600,272);
 landmarks.forEach((v,i)=>{title(board,v.name,i*320+8,20);const view=crop(intact,v.x,v.y,320,224);cx(view).fillStyle='#151a20';cx(view).fillRect(0,0,320,24);stamp(board,view,i*320,32);});save('07-cameras-principais.png',board);
 for(const x of [512,1024,1536,2048])save(`seams/emenda-${x}.png`,crop(intact,x-160,0,320,320));
 // Pixel identity is checked on rendered copies, not inferred from an AI prompt.
 const churchPixels=pixels(scaled(church,200,112));
 const renderedChurch=pixels(crop(intact,48,24,200,112));
 const exactChurch=Buffer.from(churchPixels).equals(Buffer.from(renderedChurch));
 const exactDamaged=Buffer.from(pixels(damaged)).equals(Buffer.from(pixels(crop(ruined,48,24,200,112))));
 // Technical color preview: exact existing palette, no dithering or fuzzy tile replacement.
 // This makes color/style review possible without calling an RGB draft a ROM resource.
 const palette=[[0,0,0]],seen=new Set(['0,0,0']);
 for(let i=0;i<churchPixels.length;i+=4){const c=Array.from(churchPixels.slice(i,i+3)),key=c.join(',');if(!seen.has(key)){seen.add(key);palette.push(c);}}
 const lookup=new Map();
 function indexed(c){const out=canvas(c.width,c.height),g=cx(out),im=cx(c).getImageData(0,0,c.width,c.height);for(let i=0;i<im.data.length;i+=4){const key=(im.data[i]<<16)|(im.data[i+1]<<8)|im.data[i+2];let chosen=lookup.get(key);if(chosen===undefined){let best=Infinity;chosen=0;palette.forEach((p,j)=>{const d=2*(p[0]-im.data[i])**2+3*(p[1]-im.data[i+1])**2+2*(p[2]-im.data[i+2])**2;if(d<best){best=d;chosen=j;}});lookup.set(key,chosen);}for(let n=0;n<3;n++)im.data[i+n]=palette[chosen][n];}g.putImageData(im,0,0);return out;}
 fs.mkdirSync(path.join(root,'palette-preview'),{recursive:true});
 const indexedIntact=indexed(intact),indexedDamaged=indexed(ruined);
 for(const x of [512,1024,1536,2048])save(`palette-preview/emenda-${x}.png`,crop(indexedIntact,x-160,0,320,320));
 for(const [name,c] of Object.entries({'05-panorama-intacto':intact,'05-panorama-destruido':ruined,'05-panorama-sem-objetos':empty,'05-panorama-intacto-sem-objetos':empty,'05-panorama-destruido-sem-objetos':emptyDamaged,'02-rua-tres-repeticoes':triple,'07-cameras-principais':board,'01-inicio-igreja-inteira':A,'01-inicio-igreja-destruida':AD,'02-rua-repetivel':B,'03-chegada-galpao':C}))save('palette-preview/'+name+'.png',indexed(c));
 // Count tiles/colors in the visual proposal without claiming a 4bpp export exists.
 function count(c){const bytes=pixels(c),colors=new Set(),tiles=new Set();for(let y=0;y<c.height;y+=8)for(let x=0;x<c.width;x+=8){const b=Buffer.alloc(8*8*4);let k=0;for(let yy=0;yy<8;yy++)for(let xx=0;xx<8;xx++){const p=((y+yy)*c.width+x+xx)*4;colors.add(bytes.slice(p,p+4).join(','));for(let n=0;n<4;n++)b[k++]=bytes[p+n];}tiles.add(hash(b));}return {colors:colors.size,unique_unflipped_rgba_tiles:tiles.size,not_a_4bpp_budget:true};}
 const report={status:'visual_proposal_not_integrated',phase:3,world:[2560,320],sequence:['A','B','B','B','C'],module:[512,320],church:{source:'references/igreja-original.png',position:[48,24],size:[200,112],exact_rendered_pixels:exactChurch,damaged_exact_rendered_pixels:exactDamaged,palette_preview_exact:Buffer.from(pixels(crop(indexedIntact,48,24,200,112))).equals(Buffer.from(churchPixels))},repetition:{identical_base_B:true,props_vary:true},palette,objects:defs,placements,collision_proposal:solids,proposed_route:route,camera_samples:cameraList,visual_memory:{rgb_intact:count(intact),rgb_damaged:count(ruined),palette_intact:count(indexedIntact),palette_damaged:count(indexedDamaged),target:{palette_colors:16,resident_tiles:640},note:'Visual draft and same-palette preview. No exact640-tile atlas has been exported or accepted. The current tile count requires further optimization before integration.'},implementation_changed:false,generation_tool:'built-in image_gen.imagegen',assembly:'Node canvas scene renderer; original church copied at native scale. Props exported with hard alpha test184; no production asset overwritten.'};
 if(!exactChurch||!exactDamaged)throw Error('Original church pixels changed');
 fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({church:report.church,memory:report.visual_memory,cameras:cameraList.length},null,2));
})();
