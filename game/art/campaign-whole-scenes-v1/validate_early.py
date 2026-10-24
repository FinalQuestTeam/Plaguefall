# The active production art supersedes the historical whole-scenes-v1 exports.
import runpy
from pathlib import Path
_active=Path(__file__).resolve().parents[1]/'campaign-pattern-v2/early/validate.py'
if _active.exists():
 runpy.run_path(str(_active),run_name='__main__')
 raise SystemExit(0)
"""Read-only native scenery, original church, geometry and approved-assets QA."""
from pathlib import Path
from collections import deque
import struct,json,hashlib,re
from PIL import Image
A=Path(__file__).resolve().parent;G=A.parents[1];R=G.parent
def decode(folder,mpname='map.bin',width=2560):
 data=(folder/'tiles.bin').read_bytes();raw=(folder/mpname).read_bytes();mp=struct.unpack('>'+str(len(raw)//2)+'H',raw);out=Image.new('P',(width,len(mp)//(width//8)*8))
 for n,v in enumerate(mp):
  b=data[(v&2047)*32:(v&2047)*32+32];assert len(b)==32
  patch=Image.frombytes('P',(8,8),bytes(c for b2 in b for c in (b2>>4,b2&15)))
  if v&0x800:patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&0x1000:patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.paste(patch,(n%(width//8)*8,n//(width//8)*8))
 return out
for path,sha in json.loads((A/'preserved.json').read_text()).items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==sha,path
for folder in ('03-street','03-street-ruined','04-warehouse'):
 p=A/'early'/folder;d=json.loads((p/'pack.json').read_text());assert d['tiles']<=640 and d['lossy_tile_replacements']==0
 im=Image.open(p/'map-native.png');actual=decode(p,width=im.width);assert actual.tobytes()==im.tobytes(),folder
for folder,damaged in (('03-street',False),('03-street-ruined',True)):
 im=decode(A/'early'/folder);church=decode(G/'res/courtyard','damaged.bin' if damaged else 'map.bin',512)
 assert im.crop((32,72,224,168)).tobytes()==church.crop((24,8,216,104)).tobytes(),folder
manifest=json.loads((G/'art/campaign-early-v1/manifest.json').read_text())['stages']
for key in ('03','04'):
 d=manifest[key];l,t,r,b=d['bounds'];solids=d['solids'];assert all(all(n%8==0 for n in v[:4]) for v in solids)
 def free(p):
  x,y=p;return l<=x<=r-15 and t<=y<=b-15 and not any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,*_ in solids)
 seen={tuple(d['start'])};q=deque(seen)
 while q:
  x,y=q.popleft()
  for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
   if p not in seen and free(p):seen.add(p);q.append(p)
 allfree={(x,y) for x in range(l,r-14,8) for y in range(t,b-14,8) if free((x,y))};assert seen==allfree
 if key=='03':
  path=d['traversal_points'];assert any(y>=244 for x,y in path) and any(y<=200 for x,y in path if 800<=x<=1312)
  assert not all(free((x,176)) for x in range(48,2481,8))
 print('PASS',key,d['tiles'],'tiles;',len(seen),'connected positions')
print('PASS: complete source images, exact reassembly, both churches pixel-identical;1/2/5 hashes unchanged')
