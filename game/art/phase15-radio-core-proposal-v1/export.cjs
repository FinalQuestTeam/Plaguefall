// Export only this isolated art proposal; never touches phase resources or ROMs.
const fs = require('fs');
const path = require('path');
const sharp = require('/Users/fabiocantarimmelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
async function main() {
  const root = __dirname;
  const input = path.join(root, 'source/radio-core-master.png');
  const { data, info } = await sharp(input).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left=info.width, top=info.height, right=-1, bottom=-1;
  for (let y=0;y<info.height;y++) for(let x=0;x<info.width;x++) {
    if(data[(y*info.width+x)*4+3]>=160) {
      left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);
    }
  }
  if(right<left) throw new Error('Empty art');
  const frame = await sharp(input).extract({left,top,width:right-left+1,height:bottom-top+1})
    .resize(44,60,{fit:'contain',kernel:'nearest',background:{r:0,g:0,b:0,alpha:0}})
    .extend({top:2,bottom:2,left:2,right:2,background:{r:0,g:0,b:0,alpha:0}})
    .ensureAlpha().raw().toBuffer();
  for(let i=0;i<frame.length;i+=4) {
    frame[i+3]=frame[i+3]>=160?255:0;
    if(!frame[i+3]) frame[i]=frame[i+1]=frame[i+2]=0;
  }
  const native=path.join(root,'radio-core-native-48x64.png');
  await sharp(frame,{raw:{width:48,height:64,channels:4}})
    .png({palette:true,colours:16,dither:0}).toFile(native);
  await sharp(native).resize(384,512,{kernel:'nearest'}).png()
    .toFile(path.join(root,'radio-core-preview-8x.png'));
  const {data: pixels}=await sharp(native).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const colors=new Set(),alpha=new Set();
  for(let i=0;i<pixels.length;i+=4) {
    colors.add(Array.from(pixels.subarray(i,i+4)).join(','));alpha.add(pixels[i+3]);
  }
  if(colors.size>16||[...alpha].some(a=>a!==0&&a!==255)) throw new Error('Palette/alpha invalid');
  const manifest={status:'approved source; integrated in phases 15 and 16',native_size:[48,64],preview_scale:8,
    rgba_colors_including_transparency:colors.size,alpha_values:[...alpha].sort((a,b)=>a-b),
    generation:'built-in image_gen',export:'nearest-neighbor, hard alpha, 16-color indexed PNG',
    source_crop:{left,top,width:right-left+1,height:bottom-top+1},
    design:{protected_part:'radio core only',mast:'visual only; no intended collision or damage'},
    integration_note:'build_phase15_shipyard.py maps this source to existing PAL1; 32x16 base only, shared with phase16.'};
  fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  console.log(JSON.stringify(manifest));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
