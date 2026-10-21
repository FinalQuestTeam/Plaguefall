from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
base=Path(__file__).resolve().parent.parent
out=base/'camera-60-audit'
entries=[dict(id='heroi',name='Damião',path=base/'cangaco-protagonista-v1/heroi/heroi.png')]
entries += [dict(id=e['id'],name=e['name'],path=base/'cangaco-insects-v1/enemies'/e['id']/(e['id']+'.png')) for e in json.loads((base/'cangaco-insects-v1/catalog.json').read_text())]
manifest=[]
for e in entries:
 im=Image.open(e['path']).convert('RGBA')
 card=Image.new('RGB',(700,540),(27,33,40));d=ImageDraw.Draw(card)
 d.text((10,6),e['id']+' / '+e['name']+' | 4 idle + 6 movimento | N, NE, L, SE, S',fill='white')
 for row,label in enumerate(['N','NE','L','SE','S']):
  d.text((8,65+row*100),label,fill='white')
  for p in range(10):
   cy,cx=(0,p) if p<4 else (1,p-4)
   crop=im.crop((cx*32,row*96+cy*48,cx*32+32,row*96+cy*48+48)).resize((64,96),Image.Resampling.NEAREST)
   card.paste(crop,(45+p*65,35+row*100),crop)
 dest=out/'contact-sheets'/(e['id']+'.png');card.save(dest)
 manifest.append({'id':e['id'],'name':e['name'],'sprite':str(e['path'].relative_to(base.parent.parent)), 'sha256':hashlib.sha256(e['path'].read_bytes()).hexdigest(),'contact_sheet':str(dest.relative_to(out)),'drawn_frames':50,'exported_frames':80,'mirrors':{'SO':'SE','O':'L','NO':'NE'}})
(out/'inventory.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print('14 contact sheets; 700 source poses; 1120 exported poses including horizontal mirrors.')
