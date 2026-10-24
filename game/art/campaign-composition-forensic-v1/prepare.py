"""Freeze complete production compositions and inspectable geometry.
Only decodes/copies/composites existing production pixels; no new game art.
The unannotated composition, geometry layer, and real frames remain separate.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,struct,hashlib,shutil
A=Path(__file__).resolve().parent;G=A.parents[1];W=G/'art/campaign-whole-scenes-v1';B=G/'art/campaign-integrated-v1'
for d in ('maps','layouts','boards','frames','reviews','details'): (A/d).mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
summary=read(B/'summary.json');sha=hashlib.sha256((G/'out/release/Plaguefall.bin').read_bytes()).hexdigest();assert summary['rom_sha256']==sha
native={r['phase']:W/r['native'] for r in read(W/'review-data.json')['stages']}
early=read(G/'art/campaign-early-v1/manifest.json')['stages'];routes=read(G/'art/campaign-routes-v1/export.json');factory=read(G/'art/campaign-factory-v1/geometry.json');res=read(W/'resistance/geometry.json');launch=read(W/'launch/geometry.json')
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',16);large=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',22)
def decode(folder,width,filename='map.bin'):
 ts=(folder/'tiles.bin').read_bytes();raw=(folder/filename).read_bytes();mp=struct.unpack('>'+str(len(raw)//2)+'H',raw);pal=struct.unpack('>16H',(folder/'palette.bin').read_bytes());colors=[tuple(((v>>sh)&7)*255//7 for sh in (1,5,9)) for v in pal]
 out=Image.new('RGB',(width,len(mp)//(width//8)*8))
 for n,v in enumerate(mp):
  tile=ts[(v&2047)*32:(v&2047)*32+32];p=Image.new('RGB',(8,8));p.putdata([colors[c] for b in tile for c in (b>>4,b&15)])
  if v&0x800:p=p.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&0x1000:p=p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.paste(p,(n%(width//8)*8,n//(width//8)*8))
 return out
for ph,folder,width in [('1',G/'res/courtyard',512),('2A',G/'res/courtyard',512),('2B',G/'art/campaign-early-v1/church_ruins',512),('5',G/'art/campaign-early-v1/signal',384)]:
 p=A/'maps'/f'{ph}-background.png';decode(folder,width).save(p);native[ph]=p

def image_asset(name,frame):return Image.open(G/f'art/objective-sprites-v1/frames/{name}-{frame}.png').convert('RGBA')

def overlay(out,name,cx,cy,frame=0,ground=True):
 im=image_asset(name,frame);x=cx-im.width//2;y=cy-im.height+8
 if ground:x=x//8*8;y=y//8*8
 out.alpha_composite(im,(x,y));bbox=im.getchannel('A').getbbox();return {'asset':name,'frame':frame,'center':[cx,cy],'canvas':[x,y,im.width,im.height],'ink_bbox':[x+bbox[0],y+bbox[1],x+bbox[2],y+bbox[3]],'ground_snapped_8px':ground}

def geometry(ph):
 if ph in ('1','2A','2B','3','4','5'):
  d=early[{'1':'01','2A':'02A','2B':'02B','3':'03','4':'04','5':'05'}[ph]];return d['bounds'],d['solids'],d['start']
 if ph in ('6A','6B','12'):
  d=routes[{'6A':'06a','6B':'06b','12':'12'}[ph]];return [16,192,3055,303],d['solids'],[48,208]
 if ph in ('7','8'):return res['favela_bounds'],res['favela_solids'],[80,176]
 if ph in ('9','10','11'):
  street=ph=='9';return [16,factory['street_min_y'] if street else factory['factory_min_y'],2543 if street else 751,factory['street_max_y'] if street else factory['factory_max_y']],factory['street_solids'] if street else factory['factory_solids'],[48,176] if street else [48,112]
 if ph in ('13A','13B'):return res['union_bounds'],res['union_solids'],res['dead_start'] if ph=='13B' else [48,176]
 return launch['bounds'],launch['solids'],[64,208]

rows=[]
for s in summary['stages']:
 ph=s['phase'];bg=Image.open(native[ph]).convert('RGB');bg.save(A/'maps'/f'{ph}-background.png');out=bg.convert('RGBA');objects=[]
 def put(name,x,y,frame=0,ground=True):objects.append(overlay(out,name,x,y,frame,ground))
 if ph=='6B':
  d=routes['06b']
  for x,y,w,h in d['gates']:put('gate',x+w//2,y+h-8)
  for x,y in d['valves']:put('valve',x,y)
 if ph=='7':
  for x,y in res['cargo']:put('cargo',x,y)
  put('cargo',*res['depot'],5)
 if ph=='8':
  for x,y in res['transmitters']:put('transmitter',x+8,y-8,2,False)
 if ph=='10':
  for x,y in factory['eggs']:put('nest',x,y)
 if ph=='11':
  for x,y in factory['valves']:put('valve',x,y)
 if ph=='14':
  for x,y in launch['machines']:put('generator',x,y)
 if ph=='15':put('radio',256,187,2)
 # Boss example is a documented native pose at the defined spawn, not a
 # fabricated encounter screenshot. Actual boss views are separately captured.
 if ph=='16':
  boss=Image.open(G/'art/cangaco-insects-sized-v3/enemies/boss/boss.png').convert('RGBA').crop((0,0,48,48));out.alpha_composite(boss,(140,128-16));objects.append({'asset':'boss','frame':'native direction0 pose0','canvas':[140,112,48,48],'representative_spawn_pose':True})
 out.convert('RGB').save(A/'maps'/f'{ph}-complete.png');bounds,solids,start=geometry(ph)
 layout=out.convert('RGB');d=ImageDraw.Draw(layout);l,t,r,b=bounds;d.rectangle((l,t,r,b),outline=(54,235,151),width=2)
 for rect in solids:
  x,y,w,h=rect[:4];d.rectangle((x,y,x+w-1,y+h-1),outline=(255,87,87),width=1)
 for obj in objects:
  if obj.get('ink_bbox'):d.rectangle(obj['ink_bbox'],outline=(255,212,69),width=1)
 d.rectangle((start[0],start[1],start[0]+15,start[1]+15),outline=(69,217,255),width=2)
 layout.save(A/'layouts'/f'{ph}.png')
 special=[]
 if ph=='3':
  p=A/'maps/3-ruined-complete.png';Image.open(W/'early/03-street-ruined/map-native.png').convert('RGB').save(p);special.append({'label':'Igreja em ruínas','path':str(p.relative_to(A))})
 if ph=='6B':
  im=bg.convert('RGBA')
  for x,y,w,h in routes['06b']['gates']:overlay(im,'gate',x+w//2,y+h-8,5)
  for x,y in routes['06b']['valves']:overlay(im,'valve',x,y,5)
  p=A/'maps/6B-open-complete.png';im.convert('RGB').save(p);special.append({'label':'Portões rompidos / válvulas liberadas','path':str(p.relative_to(A))})
 if ph=='14':
  im=bg.convert('RGBA')
  for x,y in launch['machines']:overlay(im,'generator',x,y,3)
  p=A/'maps/14-on-complete.png';im.convert('RGB').save(p);special.append({'label':'Cinco máquinas ligadas','path':str(p.relative_to(A))})
 if ph=='15':
  im=Image.open(W/'launch/previews/15-radio-fire-native-reconstructed.png').convert('RGBA');overlay(im,'radio',256,187,3)
  p=A/'maps/15-fire-complete.png';im.convert('RGB').save(p);special.append({'label':'Rádio e cenário após ignição','path':str(p.relative_to(A))})
 frames=[]
 for region in ('ntsc','pal'):
  src=B/s['measurements'][region]['image'];p=A/'frames'/f'{ph}-{region}-entry.png';shutil.copy2(src,p);frames.append({'path':str(p.relative_to(A)),'label':'Entrada real · '+region.upper(),'source':str(src.relative_to(G))})
 row={'phase':ph,'node':len(rows)+1,'name':s['name'],'goal':s['goal'],'group':s['group'],'size':list(bg.size),'background':f'maps/{ph}-background.png','complete':f'maps/{ph}-complete.png','layout':f'layouts/{ph}.png','bounds':bounds,'solids':solids,'start':start,'objects':objects,'special_states':special,'frames':frames,'source_native':str(native[ph].relative_to(G)),'native_sha256':hashlib.sha256(bg.tobytes()).hexdigest()};rows.append(row)
 # First prepare complete scene boards for every phase. Later reviews annotate
 # copies of these images; this never edits runtime resources.
 width=max(1024,bg.width);board=Image.new('RGB',(width,bg.height*2+128),(17,25,23));dr=ImageDraw.Draw(board);dr.text((12,8),f"FASE {ph} · {s['name']} · {bg.width}×{bg.height}",font=large,fill=(236,215,161));dr.text((12,42),'Composição de pixels nativos + objetivos nas coordenadas do jogo; sem HUD/câmera.',font=font,fill=(191,205,190));board.paste(out.convert('RGB'),(0,74));dr.text((12,bg.height+84),'Verde: área dos pés · Vermelho: sólidos · Amarelo: objetos · Ciano: início16×16',font=font,fill=(191,205,190));board.paste(layout,(0,bg.height+120));board.save(A/'boards'/f'{ph}-whole.png')
manifest={'rom_sha256':sha,'scope':'19 variantes da campanha, todas reavaliadas sem aprovação herdada','method':'Imagens completas reconstruídas dos pixels nativos e sprites exportados nas posições estáticas do runtime; overlays de geometria em arquivo separado. Capturas reais são a prova do enquadramento e da profundidade dos atores. Nenhuma imagem nova de conceito substitui o cenário real.','runtime_art_changed':False,'sprite_ground_placement':'objectivegfx.c: x=(centerX-width/2)/8*8; y=(centerY-height+8)/8*8. Sprites móveis usam projeção16px.','phases':rows}
(A/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Prepared19complete scenes before visual judgments.',sha)
