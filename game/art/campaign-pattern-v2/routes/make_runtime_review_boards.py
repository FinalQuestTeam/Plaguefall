"""Assemble real shared-ROM screenshots without changing their pixels."""
from pathlib import Path
import json,hashlib,argparse
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parent;C=A.parent/'captures';OUT=A/'runtime-evidence';OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--sha',default='61372627b51f4c2bbc04dfe5b4680726681180a5e64b6a75658255017bdab05b');parser.add_argument('--output',type=Path);args=parser.parse_args();SHA=args.sha
if args.output:OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
index=[]
for standard in ['ntsc','pal']:
 r=C/standard/'capture-report.json'
 if not r.exists():continue
 report=json.loads(r.read_text());assert report['rom_sha256']==SHA
 for phase in ['6A','6B','12']:
  row=next((p for p in report['phases']if p['phase']==phase),None)
  if not row or not row['samples']:continue
  samples=sorted(row['samples'],key=lambda s:(s['row'],s['col']))
  assert all((C/standard/s['path']).exists()for s in samples)
  columns_all=sorted(set(s['col']for s in samples));count=len(columns_all)
  if len(samples)!=3*count:continue
  groups=[('all',range(count))]+[(f'sector-{i//3+1}',range(i,min(i+3,count)))for i in range(0,count,3)]
  for group,columns in groups:
   n=len(columns);board=Image.new('RGB',(n*320,3*250+36),(17,24,27));draw=ImageDraw.Draw(board);draw.text((8,8),f'{phase} {standard.upper()} real ROM {SHA[:12]} | {group}',fill='white')
   for s in samples:
    if s['col']not in columns:continue
    x=(s['col']-columns.start)*320;y=s['row']*250+36;im=Image.open(C/standard/s['path']).convert('RGB');assert im.size==(320,224);draw.text((x+4,y+4),f"x{s['col']}y{s['row']} cam{s['camera']} {s['label']}",fill='white');board.paste(im,(x,y+22))
   dest=OUT/f'{phase}-{standard}-{group}.png';board.save(dest)
  index.append({'phase':phase,'standard':standard,'screenshots':len(samples),'report':str(r),'source_sha256':{s['path']:hashlib.sha256((C/standard/s['path']).read_bytes()).hexdigest()for s in samples},'boards':[f'{phase}-{standard}-{g}.png'for g in [g for g,_ in groups]]})
(OUT/'index.json').write_text(json.dumps({'rom_sha256':SHA,'purpose':'Real emulator camera screenshot review. Combat/route progress suppressed by shared capture setup; not completion/load proof.','groups':index},ensure_ascii=False,indent=2)+'\n')
print([(r['phase'],r['standard'],r['screenshots'])for r in index])
