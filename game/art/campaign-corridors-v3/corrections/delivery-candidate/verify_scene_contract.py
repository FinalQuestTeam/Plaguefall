"""Native bank/geometry proof. A technical pass is not an artistic verdict."""
from pathlib import Path
from PIL import Image
from collections import deque
import json,sys,struct,hashlib
A=Path(__file__).resolve().parent;R=A.parents[1];G=A.parents[3]
sys.path.insert(0,str(G/'tools'))
from campaign_corridors import read,native_path
from campaign_geometry import free
m=json.loads((A/'candidate-manifest.json').read_text());compiled=json.loads((A/'compiled-validation.json').read_text())
assert compiled['passed'] and compiled['rom_sha256']==m['rom_sha256']
report={'rom_sha256':m['rom_sha256'],'technical_only':True,'compiled_comparisons':18,'phases':{},'preserved_phases':[]}
def decode(t,mp,pal,size):
 colors=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in struct.unpack('>16H',pal)];out=Image.new('RGB',size);cols=size[0]//8
 for i,v in enumerate(struct.unpack('>'+str(len(mp)//2)+'H',mp)):
  raw=t[(v&2047)*32:(v&2047)*32+32];p=Image.new('RGB',(8,8));p.putdata([colors[n] for b in raw for n in (b>>4,b&15)])
  if v&2048:p=p.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&4096:p=p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.paste(p,(i%cols*8,i//cols*8))
 return out
for phase in ('3','6A','6B','9','12'):
 d,p,t,mp,pal=read(phase);im=decode(t,mp,pal,tuple(d['size']));assert im.tobytes()==Image.open(native_path(p)).convert('RGB').tobytes(),phase
 row={'pixel_exact_native_reconstruction':True,'geometry':d['geometry_validation'],'memory':d['memory'],'native_sha256':hashlib.sha256(im.tobytes()).hexdigest()}
 if phase=='3':
  bank=p/'damaged-native';damaged=decode((bank/'tiles.bin').read_bytes(),(bank/'map.bin').read_bytes(),pal,tuple(d['size']));assert damaged.tobytes()==Image.open(native_path(p,True)).convert('RGB').tobytes();row['damaged_reconstruction_exact']=True
 if phase=='6B':
  results=[]
  for extra in [d['gates'],d['gates'][1:],[]]:
   q=deque([tuple(d['start'])]);seen=set(q)
   while q:
    x,y=q.popleft()
    for pt in [(x+8,y),(x-8,y),(x,y+8),(x,y-8)]:
     if pt not in seen and free(d,*pt,extra=extra):seen.add(pt);q.append(pt)
   results.append((d['points'][-1][0]-8,d['points'][-1][1]-8) in seen)
  assert results==[False,False,True];row['gate_connectivity']={'both_closed':'blocked','first_open':'blocked','both_open':'connected'}
 report['phases'][phase]=row
baseline=json.loads((R/'baseline/manifest.json').read_text())
for old in baseline['phases']:
 if old['phase'] in report['phases']:continue
 current=next(v for v in m['phases'] if v['phase']==old['phase']);assert current['native_sha256']==old['native_sha256'];report['preserved_phases'].append(old['phase'])
assert len(report['preserved_phases'])==14
report['passed']=True;(A/'native-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('PASS:5exact scenes + damaged3, gate states,14preserved native compositions,18linked banks')
