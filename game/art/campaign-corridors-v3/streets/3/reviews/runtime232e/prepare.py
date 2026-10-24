from pathlib import Path
from PIL import Image,ImageDraw
import json,math,hashlib
A=Path(__file__).resolve().parent;V=A.parents[3];expected='232eac030e985dfc2ea029722ed20ae8ffff5da5131daadae8c53e296fd3b2e0'
for region in ['ntsc','pal']:
 root=V/'captures'/region;report=json.loads((root/'capture-report.json').read_text());assert report['rom_sha256']==expected
 phase=next(x for x in report['phases'] if x['phase']=='3');samples=phase['samples'];assert len(samples)==57
 (A/f'{region}-samples.json').write_text(json.dumps({'rom_sha256':expected,'region':region,'samples':samples},indent=2))
 for row in range(4):
  ss=[s for s in samples if s['row']==row];cols=3 if row==3 else 4;sheet=Image.new('RGB',(cols*320,math.ceil(len(ss)/cols)*244),(20,24,28));draw=ImageDraw.Draw(sheet)
  for i,s in enumerate(ss):
   im=Image.open(root/s['path']).convert('RGB');assert im.size==(320,224);x=i%cols*320;y=i//cols*244;sheet.paste(im,(x,y+20));draw.text((x+2,y+3),s['path'].split('/')[-1]+' feet'+str(s['position'])+' cam'+str(s['camera']),fill='white')
  sheet.save(A/(f'{region}-'+('landmarks' if row==3 else 'row-'+str(row))+'.png'))
 # Source image files hash inventory, preserving exact review evidence references.
 (A/f'{region}-capture-hashes.json').write_text(json.dumps({s['path']:hashlib.sha256((root/s['path']).read_bytes()).hexdigest() for s in samples},indent=2))
print(V, 'sheets ready')
