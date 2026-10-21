"""Composição de pranchas de conceito. Não exporta recursos para o jogo."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, json

ROOT = Path(__file__).resolve().parent
IVORY = '#F2DFC0'
GOLD = '#FFBF57'
BLUE = '#9EB7B6'
INK = '#151D20'
MUTED = '#B9AE96'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
MONO = '/System/Library/Fonts/Supplemental/Andale Mono.ttf'

# Identificadores, nomes e coordenadas do grafo, sem inventar novas saídas.
ROWS = [
 ('1','Pátio da igreja',0,1),('2A','Rua de serviço',1,0),
 ('2B','Baixio da igreja',1,2),('3','Abrigo de manutenção',2,1),
 ('4','Túneis de manutenção',3,1),('5','Sinalizador na Santa',4,1),
 ('6A','Perímetro do resgate',5,0),('6B','Retirada por terra',5,2),
 ('7','Rede de antenas',6,1),('8','Fornalha',7,1),
 ('9','Alfândega',8,1),('10A','Acesso dos técnicos',9,0),
 ('10B','Dreno térmico',9,2),('11','Depósito de demolição',10,1),
 ('12','Comporta de carga',11,1),('13A','Linha quente',12,0),
 ('13B','Decantação',12,2),('14','Pátio dos enxames',13,1),
 ('15','Galerias dos ninhos',14,1),('16','Câmara do Escorpião',15,1),
]
EDGES = [('1','2A'),('1','2B'),('2A','3'),('2B','3'),('3','4'),
 ('4','5'),('5','6A'),('5','6B'),('6A','7'),('6B','7'),('7','8'),
 ('8','9'),('9','10A'),('9','10B'),('10A','11'),('10B','11'),
 ('11','12'),('12','13A'),('12','13B'),('13A','14'),('13B','14'),
 ('14','15'),('15','16')]
VISITED = ['1','2B','3','4','5','6A','7','8','9']
TRAVERSED = set(zip(VISITED,VISITED[1:]))
CURRENT, NEXT = '9','10A'
POINTS = {n:(123+90.1*c,748-34.8*c+(r-1)*145) for n,_,c,r in ROWS}

def font(size,bold=False,mono=False):
 return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,size)

def text(draw, xy, s, size=22, color=IVORY, bold=False, anchor=None):
 draw.text(xy,s,font=font(size,bold),fill=color,anchor=anchor,stroke_width=0)

def dash(draw,a,b,fill,width=3,on=12,off=9):
 dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
 if not length:return
 for start in range(0,math.ceil(length),on+off):
  end=min(start+on,length)
  draw.line([(a[0]+dx*start/length,a[1]+dy*start/length),
             (a[0]+dx*end/length,a[1]+dy*end/length)],fill=fill,width=width)

def arrow(draw,a,b,color=GOLD,size=16,t=.63):
 x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
 ang=math.atan2(b[1]-a[1],b[0]-a[0]);ux,uy=math.cos(ang),math.sin(ang)
 draw.polygon([(x+ux*size,y+uy*size),(x-ux*size-uy*size*.65,y-uy*size+ux*size*.65),
 (x-ux*size+uy*size*.65,y-uy*size-ux*size*.65)],fill=color)

def pill(draw,xy,s,size=20,color=IVORY,outline=None):
 f=font(size,True);w=draw.textbbox((0,0),s,font=f)[2]+24;h=size+18
 x,y=xy;draw.rounded_rectangle((x,y,x+w,y+h),radius=7,fill=INK,outline=outline,width=2)
 draw.text((x+12,y+7),s,font=f,fill=color)
 return w,h

def route(draw,transform,scale=1):
 for a,b in EDGES:
  aa,bb=transform(POINTS[a]),transform(POINTS[b])
  draw.line([aa,bb],fill='#152023',width=max(3,round(9*scale)))
  if (a,b) in TRAVERSED:
   draw.line([aa,bb],fill=IVORY,width=max(2,round(4*scale)))
  elif (a,b)==(CURRENT,NEXT):
   draw.line([aa,bb],fill=GOLD,width=max(3,round(5*scale)))
   arrow(draw,aa,bb,size=12*scale)
  else:
   dash(draw,aa,bb,BLUE,max(2,round(3*scale)),round(10*scale),round(8*scale))

def nodes(draw,transform,scale=1):
 for n,_,_,_ in ROWS:
  x,y=transform(POINTS[n]);r=16*scale
  # Persistent shapes communicate state without relying on color alone.
  if n==CURRENT:
   draw.ellipse((x-r*1.7,y-r*1.7,x+r*1.7,y+r*1.7),outline=GOLD,width=max(2,round(2*scale)))
   draw.polygon([(x,y+r*1.6),(x-r*1.2,y-r),(x+r*1.2,y-r)],fill=GOLD,outline=INK,width=max(2,round(2*scale)))
  else:
   draw.ellipse((x-r,y-r,x+r,y+r),fill=IVORY if n in VISITED else INK,
    outline=IVORY if n in VISITED else BLUE,width=max(2,round(2*scale)))
   if n==NEXT:
    draw.ellipse((x-r*1.6,y-r*1.6,x+r*1.6,y+r*1.6),outline=GOLD,width=max(2,round(3*scale)))
   text(draw,(x,y),n,round(17*scale),INK if n in VISITED else IVORY,True,'mm')
  if n==CURRENT:text(draw,(x,y-4*scale),n,round(16*scale),INK,True,'mm')

def compose():
 bg=Image.open(ROOT/'paisagem-base.png').convert('RGB').resize((1536,1024),Image.Resampling.LANCZOS)
 board=Image.new('RGB',(1536,1390),INK)
 board.paste(bg,(0,112))
 d=ImageDraw.Draw(board)
 text(d,(40,23),'SÃO JERÔNIMO',38,bold=True)
 text(d,(41,72),'DA FUGA DA IGREJA AO CORAÇÃO DOS NINHOS',18,MUTED)
 text(d,(1496,35),'MAPA DA CAMPANHA  /  CONCEPT 01',18,MUTED,anchor='ra')
 text(d,(1496,68),'20 locais possíveis • 16 fases por partida',18,MUTED,anchor='ra')
 tf=lambda p:(p[0],p[1]+112)
 route(d,tf);nodes(d,tf)
 # Quiet map ground supports diegetic-looking sector headings.
 for x,y,a,b in [(44,162,'01 / COMUNIDADE','Igreja • abrigo • túneis'),
 (404,220,'02 / EVACUAÇÃO','Sinal • resgate • antenas'),
 (795,173,'03 / BASE INDUSTRIAL','Dutos • carga • manutenção'),
 (1170,800,'04 / NINHOS','Aço tomado pela infestação')]:
  pill(d,(x,y),a,18)
  pill(d,(x,y+42),b,16,MUTED)
 cx,cy=tf(POINTS[CURRENT]);nx,ny=tf(POINTS[NEXT])
 pill(d,(cx+45,cy+10),'DAMIÃO / AGORA',18,GOLD,GOLD)
 pill(d,(nx-93,ny-79),'PRÓXIMA / 10A',18,GOLD,GOLD)
 # Legend is composition/UI, not painted into the environment.
 d.rounded_rectangle((32,1036,1504,1110),12,fill=INK)
 for x,kind,label in [(57,'done','Percorrido'),(370,'now','Damião / agora'),(760,'next','Próximo destino'),(1160,'future','Outras rotas')]:
  if kind=='done':d.line((x,1073,x+48,1073),fill=IVORY,width=5)
  elif kind=='now':d.polygon([(x+24,1090),(x+5,1058),(x+43,1058)],fill=GOLD)
  elif kind=='next':
   for r in (13,21):d.ellipse((x+24-r,1073-r,x+24+r,1073+r),outline=GOLD,width=3)
  else:dash(d,(x,1073),(x+48,1073),BLUE,3)
  text(d,(x+62,1062),label,21)
 text(d,(40,1151),'LOCAIS DO PERCURSO',18,MUTED,bold=True)
 for i,(n,name,_,_) in enumerate(ROWS):
  col=i//5;row=i%5;x=40+col*376;y=1192+row*33
  text(d,(x,y),n,19,GOLD,bold=True)
  text(d,(x+48,y),name,19)
 text(d,(1496,1372),'PRÉ-PRODUÇÃO • SEM ALTERAÇÕES NO JOGO',15,MUTED,anchor='rs')
 board.save(ROOT/'mapa-campanha-concept-v1.png')

 # 10:7 concept screen matching the target 320×224 aspect ratio.
 screen=Image.new('RGB',(1600,1120),INK)
 crop=(636,150,1536,600)
 image=bg.crop(crop).resize((1600,800),Image.Resampling.LANCZOS)
 maplayer=image.copy();md=ImageDraw.Draw(maplayer)
 ui_tf=lambda p:((p[0]-crop[0])*1600/(crop[2]-crop[0]),(p[1]-crop[1])*800/(crop[3]-crop[1]))
 route(md,ui_tf,1.55);nodes(md,ui_tf,1.55)
 cx,cy=ui_tf(POINTS[CURRENT]);nx,ny=ui_tf(POINTS[NEXT])
 pill(md,(cx-95,cy+54),'DAMIÃO',29,GOLD,GOLD)
 pill(md,(nx+63,ny-23),'PRÓXIMA',27,GOLD,GOLD)
 screen.paste(maplayer,(0,100));sd=ImageDraw.Draw(screen)
 text(sd,(36,24),'SÃO JERÔNIMO / BASE',36,bold=True)
 text(sd,(1562,30),'9 / 16 CONCLUÍDAS',30,MUTED,anchor='ra')
 sd.line((0,98,1600,98),fill=MUTED,width=2)
 sd.line((0,902,1600,902),fill=GOLD,width=3)
 text(sd,(34,925),'AGORA: 9 • ALFÂNDEGA',30,GOLD,bold=True)
 text(sd,(34,974),'PRÓXIMA: 10A • ACESSO DOS TÉCNICOS',35,bold=True)
 text(sd,(34,1032),'Sem sofrer dano. Acesso de manutenção liberado.',28,MUTED)
 pill(sd,(1280,1037),'A  SEGUIR',28,GOLD,GOLD)
 screen.save(ROOT/'tela-entre-fases-concept-v1.png')
 screen.resize((320,224),Image.Resampling.LANCZOS).save(ROOT/'previa-escala-320x224.png')

 data={'current':CURRENT,'next':NEXT,'visited':VISITED,'edges':EDGES,
  'nodes':[{'id':n,'name':name,'col':c,'row':r} for n,name,c,r in ROWS],
  'status':'concept_only','gameImplemented':False,'generation':'integrated image_gen'}
 (ROOT/'mapa.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print('Pranchas geradas somente em',ROOT)

if __name__=='__main__':compose()
