"""Assemble whole native scenes, independent geometry and actual emulator evidence."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,shutil,re
A=Path(__file__).resolve().parent;G=A.parents[1]
read=lambda p:json.loads(p.read_text())
for sub in ('maps','layouts','boards'):(A/sub).mkdir(exist_ok=True)
order=['1','2A','2B','3','4','5','6A','6B','7','8','9','10','11','12','13A','13B','14','15','16']
names=['Pátio da igreja','Igreja preservada','Igreja após a bomba','Rua até o galpão','Interior do galpão','Sinal na Santa','Esgotos: evacuação completa','Esgotos: perdas civis','Suprimentos do abrigo','Emissores do enxame','Rua industrial','Ovos na fábrica','Ativação da fábrica','Caminho do sindicato','Sindicato: Dinorah viva','Sindicato: memorial','Energia do estaleiro','Rádio e ignição','O Escorpião']
goals=['Sobreviver90s e evacuar os civis; bomba define o estado da igreja.','Eliminar15insetos, incluindo o novo atirador.','Eliminar15insetos entre destroços completos.','Abrir caminho até o galpão; percurso2560px.','Eliminar20insetos para receber os civis.','Defender a Santa por120s; resgate completo ou perdas civis.','Escoltar Dinorah pelos3072px de esgoto.','Escoltar Dinorah, liberar válvulas e romper2portões.','Transportar5suprimentos para o depósito.','Eliminar3emissores prioritários do enxame.','Chegar à fábrica após2560px de rua industrial.','Destruir10ovos.','Liberar3válvulas e atrair o enxame com calor.','Escoltar Dinorah pelos3072px até o sindicato.','Eliminar30insetos; Dinorah permanece viva.','Eliminar45insetos após a morte de Dinorah.','Ativar5máquinas conectadas à estação.','Defender o rádio por120s até a ignição.','Derrotar o chefe; diálogo varia com Dinorah viva ou morta.']
E=read(A/'early/geometry.json');R=read(A/'routes/export.json')
rows=[]
def rel(p):return str(p.relative_to(A))
def native(ph):
 if ph in ('1','2A'):return A/'early/01-courtyard/complete-native.png'
 if ph in ('2B','3','4','5'):return A/'early'/dict(zip(['2B','3','4','5'],['02B-ruins','03-street','04-warehouse','05-signal']))[ph]/'map-native.png'
 if ph in ('6A','6B','12'):return A/'routes/current'/({'6A':'06a','6B':'06b','12':'12'}[ph])/('complete-closed-objectives.png' if ph=='6B' else 'complete-native.png')
 raise KeyError(ph)
# Other thematic groups supply their exact objective overlays and bounds.
external={}
for folder in ('resistance','launch','factory'):
 p=A/folder/'review-manifest.json'
 if not p.exists():p=A/folder/'manifest.json'
 if p.exists():
  data=read(p);data=data.get('phases',data)
  for d in data:
   d=dict(d);d['complete']=d['complete'].removeprefix('art/campaign-pattern-v2/');d['sources']=d.get('sources',[d['source']] if d.get('source') else []);d['sources']=[x.removeprefix('art/campaign-pattern-v2/') for x in d['sources']]
   states=d.get('special_states',[])
   if isinstance(states,dict):states=[dict(label=k,path=v) for k,v in states.items()]
   for state in states:state['path']=state.get('path',state.get('complete')).removeprefix('art/campaign-pattern-v2/')
   d['special_states']=states
   external[d['phase']]=d
for i,ph in enumerate(order):
 special=[];objects=[];source=[]
 if ph in ('1','2A','2B','3','4','5'):
  key={'1':'01','2A':'02A','2B':'02B','3':'03','4':'04','5':'05'}[ph];d=E[key];image=native(ph)
  if ph in ('1','2A'):tiles=read(A/'early/01-courtyard/native/pack.json')['tiles'];source=['early/01-courtyard/source/whole-scene.png']
  else:
   tiles=d['tiles'];source=['early/source/'+{'2B':'../01-courtyard/source/whole-scene.png','3':'03-street-whole.png','4':'04-warehouse-whole.png','5':'05-signal-whole.png'}[ph]]
  bounds=d['bounds'];solids=d['solids'];start=d['start'];memory={'background_tiles':tiles,'total_tiles':tiles,'limit':640}
  if ph=='1':special=[{'label':'Após bomba','path':'early/01-courtyard/damaged-native.png'}]
  if ph=='3':special=[{'label':'Continuidade da igreja destruída','path':'early/03-street-ruined/map-native.png'}]
 elif ph in ('6A','6B','12'):
  d=R[{'6A':'06a','6B':'06b','12':'12'}[ph]];image=native(ph);bounds=d['bounds'];solids=d['solids'];start=d['start'];memory=d.get('memory',{});source=['routes/cycle-1/source/'+({'6A':'06a','6B':'06b','12':'12'}[ph])+'-whole.png']
  if ph=='6B':special=[{'label':'Colapso transitório','path':'routes/current/06b/complete-collapse-objectives.png'},{'label':'Aberto: passagem livre e apoios preservados','path':'routes/current/06b/complete-open-objectives.png'}]
 else:
  d=external[ph];image=A/d['complete'];bounds=d['bounds'];solids=d['solids'];start=d['start'];memory=d.get('memory',{});source=d.get('sources',[]);special=d.get('special_states',[]);objects=d.get('objects',[])
 memory=dict(memory);memory['total_tiles']=memory.get('total_tiles',memory.get('total_reserved_tiles',memory.get('scene_tiles')));memory['limit']=640
 if ph in ('1','2A'):memory.update(unique_tiles=636,upload_reserved_tiles=640,upload_bytes=20480)
 im=Image.open(image).convert('RGB');im.save(A/'maps'/f'{ph}-complete.png');layout=im.copy();draw=ImageDraw.Draw(layout);draw.rectangle(bounds,outline='#41e396',width=2)
 for v in solids:
  x,y,w,h=v[:4];draw.rectangle((x,y,x+w-1,y+h-1),outline='#ff7777',width=1)
 draw.rectangle((start[0],start[1],start[0]+15,start[1]+15),outline='#61c9ff',width=2);layout.save(A/'layouts'/f'{ph}.png')
 row=dict(phase=ph,node=i+1,name=names[i],goal=re.sub(r'([A-Za-zÀ-ÿ])(\d)',r'\1 \2',re.sub(r'(\d)([A-Za-zÀ-ÿ])',r'\1 \2',goals[i])),size=list(im.size),bounds=bounds,solids=solids,start=start,memory=memory,sources=source,complete=f'maps/{ph}-complete.png',layout=f'layouts/{ph}.png',special_states=special,objects=objects,native_source=rel(image),native_sha256=hashlib.sha256(im.tobytes()).hexdigest())
 if ph=='6B':row['gates']=d['gates']
 rows.append(row)
sha=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
(A/'manifest.json').write_text(json.dumps(dict(rom_sha256=sha,scope='19variações reconstruídas segundo regiões e objetivos próprios',method='Fonte inteira → módulos completos → reconstrução exata → composição com objetivos → câmeras reais. Imagem inteira é distinta da câmera em movimento.',phases=rows),ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(rows),'whole scenes',sha)
