from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
A=Path(__file__).resolve().parent
size=[3072,320];bounds=[16,96,3055,303];start=[48,176]
structures=[('oficina',[80,24,384,112]),('oficina-servico',[720,24,240,160]),('doca-baixa',[1008,224,240,88]),('anexo-servico',[1344,24,256,128]),('doca-coberta',[1632,224,320,88]),('cobertura-oficina',[1808,128,96,48]),('anexo-sindicato',[2192,24,256,112]),('pavilhao-baixo',[2272,232,192,80]),('sindicato',[2656,24,352,112])]
props=[('banco-oficina',[224,232,96,32]),('carro-servico',[448,176,80,40]),('banco-patio',[2496,224,96,32])]
solids=[r for n,r in structures+props]
points=[[56,184],[336,184],[424,232],[592,232],[704,232],[920,232],[1048,184],[1264,184],[1496,160],[1744,200],[1936,200],[2168,200],[2384,184],[2576,160],[2808,160],[2920,160]];pauses=[3,7,13];exit=[2888,128,64,72]
d={'phase':'12','size':size,'bounds':bounds,'start':start,'structures':structures,'props':props,'solids':solids,'points':points,'pauses':pauses,'exit':exit,'point_semantics':'CENTERS; each has8px actor margin','regions':[{'name':'Oficinas e doca de partida','x':[0,704]},{'name':'Travessia de serviço em cotovelo','x':[704,1344]},{'name':'Recuo e doca de cobertura','x':[1344,2208]},{'name':'Pátio e entrada do sindicato','x':[2208,3072]}]}
(A/'blockout.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
im=Image.new('RGB',size,'#b1aa8d');draw=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12)
draw.rectangle((0,0,3071,31),fill='#273b36');draw.rectangle((0,304,3071,319),fill='#273b36');draw.rectangle((0,0,15,319),fill='#273b36');draw.rectangle((3056,0,3071,319),fill='#273b36')
for i,(name,(x,y,w,h)) in enumerate(structures):
 draw.rectangle((x,y,x+w-1,y+h-1),fill='#486a78'if name!='sindicato'else'#b67746',outline='#162c33',width=2);draw.text((x+6,y+8),name,font=font,fill='white')
for name,(x,y,w,h)in props:draw.rectangle((x,y,x+w-1,y+h-1),fill='#77664a',outline='#162c33',width=2)
draw.line([tuple(p)for p in points],fill='#e1ff93',width=3)
for i,(x,y)in enumerate(points):draw.ellipse((x-8,y-8,x+7,y+7),fill='#fff7c3'if i in pauses else'#36d6a0',outline='#0c5144');draw.text((x+10,y-5),str(i),font=font,fill='#112723')
x,y,w,h=exit;draw.rectangle((x,y,x+w,y+h),outline='#fff1a2',width=3)
im.save(A/'blockout.png');sheet=Image.new('RGB',(3072,1024),'#101818');sheet.paste(im,(0,352));sd=ImageDraw.Draw(sheet);sd.text((32,304),'LEVEL12 - 3072 x 320 - CONTEUDO SOMENTE NESTA FAIXA CENTRAL - escala de porta32x48',font=font,fill='#fff7c3');sheet.save(A/'source/blockout-sheet.png');print(A)
