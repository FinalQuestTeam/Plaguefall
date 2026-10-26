// Native tile export. Only the unobstructed8px foliage band is regularized.
const fs=require('fs'),path=require('path'),{createRequire}=require('module');
const req=createRequire('/Users/fabiocantarimmelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json');
const {createCanvas,loadImage}=req('@napi-rs/canvas');
const root=__dirname,out=path.join(root,'integration-v1');fs.mkdirSync(out,{recursive:true});
const meta=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const palette=meta.palette,lookup=new Map(palette.map((p,i)=>[p.join(','),i]));
const check=process.argv.includes('--check'),banks=[];
const emit=(p,data)=>{if(check){if(!fs.existsSync(p)||!fs.readFileSync(p).equals(Buffer.isBuffer(data)?data:Buffer.from(data)))throw Error('Stale native export: '+p);}else fs.writeFileSync(p,data);};
const png=(c,p)=>emit(p,c.toBuffer('image/png'));
(async()=>{
const patch=await loadImage(path.join(root,'palette-preview/02-rua-repetivel.png'));
for(const state of ['intacto','destruido']){
const im=await loadImage(path.join(root,'palette-preview/05-panorama-'+state+'.png'));
const c=createCanvas(2560,320),g=c.getContext('2d');g.imageSmoothingEnabled=false;g.drawImage(im,0,0);
for(const origin of [512,1024,1536])for(const[a,b]of[[0,64],[232,280],[448,512]])for(let x=a;x<b;x+=32)g.drawImage(patch,0,24,Math.min(32,b-x),8,origin+x,24,Math.min(32,b-x),8);
const px=g.getImageData(0,0,2560,320).data,unique=new Map(),tiles=[],mapping=[];
for(let y=0;y<40;y++)for(let x=0;x<320;x++){
 const b=Buffer.alloc(32);let k=0;
 for(let yy=0;yy<8;yy++)for(let xx=0;xx<8;xx+=2){const a=((y*8+yy)*2560+x*8+xx)*4;const p=lookup.get([px[a],px[a+1],px[a+2]].join(','));const q=lookup.get([px[a+4],px[a+5],px[a+6]].join(','));if(p===undefined||q===undefined)throw Error('palette');b[k++]=(p<<4)|q;}
 const key=b.toString('hex');if(!unique.has(key)){unique.set(key,tiles.length);tiles.push(b);}mapping.push(unique.get(key));
}
let peak=0,at=[];for(let y=3;y<=14;y++)for(let x=0;x<=279;x++){const seen=new Set();for(let yy=y;yy<y+26;yy++)for(let xx=x;xx<x+41;xx++)seen.add(mapping[yy*320+xx]);if(seen.size>peak){peak=seen.size;at=[x,y];}}
if(peak>640)throw Error('Visible cache overflow '+peak);
const bank=state==='intacto'?'native':'damaged-native';fs.mkdirSync(path.join(out,bank),{recursive:true});
emit(path.join(out,bank,'tiles.bin'),Buffer.concat(tiles));const m=Buffer.alloc(mapping.length*2);mapping.forEach((v,i)=>m.writeUInt16BE(v,i*2));emit(path.join(out,bank,'map.bin'),m);
const pal=Buffer.alloc(32);palette.forEach(([r,gg,b],i)=>pal.writeUInt16BE((Math.round(b*7/255)<<9)|(Math.round(gg*7/255)<<5)|(Math.round(r*7/255)<<1),i*2));emit(path.join(out,bank,'palette.bin'),pal);
png(c,path.join(out,state==='intacto'?'complete-native.png':'complete-damaged-native.png'));
emit(path.join(out,bank,'memory.json'),JSON.stringify({source_tiles:tiles.length,resident_budget:640,maximum_visible_tiles:peak,peak_cell:at,window:[41,26],optimization:'Repeat existing32x8foliage patch only in background gaps; buildings, church, street props unchanged.'},null,2)+'\n');
banks.push({tiles:tiles.length,peak});
console.log(state,tiles.length,'ROM tiles;',peak,'maximum visible tiles');
}
const manifestPath=path.join(out,'manifest.json'),manifest=JSON.parse(fs.readFileSync(manifestPath));
manifest.streamed_tiles.source_count=manifest.memory.source_tiles=banks[0].tiles;
manifest.streamed_tiles.damaged_source_count=manifest.memory.damaged_source_tiles=banks[1].tiles;
manifest.streamed_tiles.maximum_visible_tiles=manifest.memory.maximum_visible_tiles=Math.max(...banks.map(b=>b.peak));
manifest.memory.resident_graphics_bytes=640*32;
manifest.memory.cache_heap_bytes={intact:(banks[0].tiles+640*4)*2,damaged:(banks[1].tiles+640*4)*2};
manifest.memory.native_rom_bytes=banks.reduce((sum,b)=>sum+b.tiles*32+320*40*2+32,0);
emit(manifestPath,JSON.stringify(manifest,null,2)+'\n');
})();
