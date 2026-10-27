const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('output/mapa-fases-01-16.html','utf8');
const payload=JSON.parse(html.match(/<script id="atlasData" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
let imageCount=0;
function verifyPng(url,width,height){const b=Buffer.from(url.split(',')[1],'base64');assert.equal(b.subarray(1,4).toString(),'PNG');assert.equal(b.readUInt32BE(16),width);assert.equal(b.readUInt32BE(20),height);imageCount++;}
for(const s of payload.stages){verifyPng(s.map,s.geometry.width,s.geometry.height);verifyPng(s.entry,320,224);if(s.previous_map)verifyPng(s.previous_map,s.geometry.width,s.geometry.height);for(const e of s.evidence)verifyPng(e.image,320,224);for(const v of s.views){verifyPng(v.image,320,224);assert.equal(v.current_node,s.node);assert.equal(v.stream_faults,0);assert(v.camera[0]>=0&&v.camera[0]<=s.geometry.width-320);assert(v.camera[1]>=0&&v.camera[1]<=s.geometry.height-224)}}
const elements=[];
const noop=()=>{};
const context2d=new Proxy({}, {get(t,k){return t[k]??noop},set(t,k,v){t[k]=v;return true}});
class El{
 constructor(tag='div',id=''){this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.attrs={};this.dataset={};this.value='';this.checked=['showPoints'].includes(id);this.clientWidth=id==='mapWrap'?820:320;this.clientHeight=490;this.width=320;this.height=224;this.textContent='';this.classes=new Set();this.classList={toggle:(c,on)=>{on=on??!this.classes.has(c);on?this.classes.add(c):this.classes.delete(c);return on},contains:c=>this.classes.has(c)};elements.push(this)}
 append(...items){this.children.push(...items)}replaceChildren(...items){this.children=items}setAttribute(k,v){this.attrs[k]=String(v)}removeAttribute(k){delete this.attrs[k]}getContext(){return context2d}addEventListener(){}setPointerCapture(){}getBoundingClientRect(){return {left:0,top:0,width:this.clientWidth,height:this.clientHeight}}click(){this.onclick?.({target:this})}
}
const ids={};for(const m of html.matchAll(/id="([^"]+)"/g))ids[m[1]]=new El(m[1]==='map'||m[1]==='screen'?'canvas':'div',m[1]);ids.atlasData.textContent=JSON.stringify(payload);
const document={getElementById:id=>{assert(ids[id],'Unknown element '+id);return ids[id]},createElement:tag=>new El(tag),querySelectorAll:selector=>elements.filter(e=>e.className===selector.slice(1)),addEventListener:noop};
const sandbox={document,Image:class{constructor(){this.complete=true;this.naturalWidth=320}set src(v){this.url=v}},ResizeObserver:class{observe(){}},devicePixelRatio:1,requestAnimationFrame:fn=>fn(),history:{replaceState:noop},location:{hash:''},window:{addEventListener:noop},console};
vm.createContext(sandbox);vm.runInContext(script,sandbox);
vm.runInContext(`
for(let i=0;i<STAGES.length;i++){
 select(i);if($('title').textContent!==STAGES[i].title)throw Error('wrong title');
 selectView('0');drawMap();drawScreen();
 setCamera(99999,99999);if(cameraX!==stage().geometry.width-320||cameraY!==stage().geometry.height-224)throw Error('camera bounds');
 $('baseMode').click();drawScreen();$('realMode').click();
 for(const id of ['showPoints','showBounds','showSolids','showRoute','showViews']){$(id).checked=true;$(id).onchange()}
 $('points').children.forEach(b=>b.click());
 stage().views.forEach((v,j)=>{selectView(String(j));drawScreen()});
 $('fit').click();$('two').click();$('zoomOut').click();$('expand').click();$('expand').click();
 $('entry').click();if(!entrySelected)throw Error('entry');
 if(stage().previous_map){$('compare').click();if(!showPrevious)throw Error('compare before');$('compare').click();if(showPrevious)throw Error('compare now')}
 stage().evidence.forEach((e,j)=>{chooseEvidence(j);if($('evidenceCaption').textContent!==e.title)throw Error('evidence caption')});
}
select(0);$('next').click();if(selected!==1)throw Error('next');$('previous').click();if(selected!==0)throw Error('previous');
map.onpointerdown({pointerId:1,clientX:20,clientY:30});map.onpointerup({clientX:40,clientY:50});
map.onpointerdown({pointerId:2,clientX:20,clientY:30});map.onpointermove({clientX:80,clientY:70});map.onpointerup({clientX:80,clientY:70});
`,sandbox);
console.log(JSON.stringify({passed:true,stage_versions:payload.stages.length,png_images_verified:imageCount,emulator_stills:payload.view_count,evidence_stills:payload.evidence_count,interaction_checks:'19 stages, all stills, camera clamping, objectives, layers, modes, zoom, expand, entry, previous/next pointer handlers, previous/current comparison and evidence gallery',verification:'Node DOM/canvas stubs; no browser layout claim'},null,2));
