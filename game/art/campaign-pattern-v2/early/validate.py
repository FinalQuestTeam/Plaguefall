"""Read-only exact native reconstruction, production exports and geometry QA."""
from pathlib import Path
from collections import deque
from PIL import Image
import json,struct,re
E=Path(__file__).resolve().parent;G=E.parents[2]
import sys
sys.path.insert(0,str(G/'tools'))
from campaign_corridors import active,read as corridor_read,native_path
def decode(folder,name,width):
 data=(folder/'tiles.bin').read_bytes();raw=(folder/(name+'.bin')).read_bytes();mp=struct.unpack('>'+str(len(raw)//2)+'H',raw);out=Image.new('P',(width,len(mp)//(width//8)*8))
 for n,v in enumerate(mp):
  tile=data[(v&2047)*32:(v&2047)*32+32];assert len(tile)==32
  p=Image.frombytes('P',(8,8),bytes(c for b in tile for c in (b>>4,b&15)))
  if v&0x800:p=p.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&0x1000:p=p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.paste(p,(n%(width//8)*8,n//(width//8)*8))
 return out
paths={'01':'01-courtyard/native','02A':'01-courtyard/native','02B':'02B-ruins','03':'03-street','04':'04-warehouse','05':'05-signal'}
geo=json.loads((E/'geometry.json').read_text())
for phase,d in geo.items():
 folder=E/paths[phase];imagepath=E/'01-courtyard/complete-native.png' if phase in ('01','02A') else folder/'map-native.png'
 if phase=='03' and active('3'):
  cd,cp,*_=corridor_read('3');folder=cp/'native';imagepath=native_path(cp)
 actual=decode(folder,'map',d['width']);image=Image.open(imagepath)
 if image.mode!='P':
  pal=struct.unpack('>16H',(folder/'palette.bin').read_bytes());actual.putpalette([c for v in pal for c in [((v>>s)&7)*255//7 for s in (1,5,9)]]+[0]*720);actual=actual.convert('RGB');image=image.convert('RGB')
 assert actual.tobytes()==image.tobytes(),phase
 assert len((folder/'tiles.bin').read_bytes())<=20480
 l,t,r,b=d['bounds'];sol=d['solids']
 def free(x,y):return l<=x<=r-15 and t<=y<=b-15 and not any(x<a+w and x+16>a and y<c+h and y+16>c for a,c,w,h,*_ in sol)
 seen={tuple(d['start'])};q=deque(seen)
 while q:
  x,y=q.popleft()
  for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
   if p not in seen and free(*p):seen.add(p);q.append(p)
 assert seen=={(x,y) for y in range(t,b-14,8) for x in range(l,r-14,8) if free(x,y)}
 print('PASS phase',phase,'exact tiles;',len(seen),'connected16px-foot positions')
for name in ('map.bin','damaged.bin','palette.bin'):assert (G/'res/courtyard'/name).read_bytes()==(E/'01-courtyard/native'/name).read_bytes()
d=(E/'01-courtyard/native/tiles.bin').read_bytes();assert (G/'res/courtyard/tiles.bin').read_bytes()==d+bytes(20480-len(d))
for state,folder in [('map','03-street'),('damaged','03-street-ruined')]:
 source=E/folder;bbox=[24,0,200,112];original=[16,0,200,112]
 if active('3'):
  cd,cp,*_=corridor_read('3');source=cp/('native' if state=='map' else 'damaged-native');bbox=cd['church_bbox'];original=cd.get('church_original_bbox',original)
 street=decode(source,'map',2560);church=decode(G/'res/courtyard',state,512)
 box=lambda v:(v[0],v[1],v[0]+v[2],v[1]+v[3])
 assert street.crop(box(bbox)).tobytes()==church.crop(box(original)).tobytes()
assert re.search(r'COURTYARD_TILE_COUNT 640',(G/'src/levels/courtyard_data.h').read_text())
print('PASS church continuity, intact/damaged;640tile shared reservation; no fuzzy tile replacement')
