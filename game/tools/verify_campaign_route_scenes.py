"""Verify exact complete-scene exports and connected authored escort ground."""
from pathlib import Path
from collections import deque
import json,struct
from pack_campaign_ground_art import generate as packed_objectives
import numpy as np
from PIL import Image
G=Path(__file__).resolve().parents[1]
report=json.loads((G/'art/campaign-routes-v1/export.json').read_text())
for key,d in report.items():
 base=G/'res/campaign_routes'/key
 data=(base/'tiles.bin').read_bytes();count=len(data)//32
 tiles=np.array([[v for b in data[i:i+32] for v in (b>>4,b&15)] for i in range(0,len(data),32)],dtype=np.uint8)
 words=struct.unpack('>16H',(base/'palette.bin').read_bytes());assert words[0]==0 and all((v&~0xeee)==0 for v in words)
 colors=np.array([[((v>>s)&7)*255//7 for s in (1,5,9)] for v in words],dtype=np.uint8)
 width,height=d['width'],d['height'];cols,rows=width//8,height//8
 m=np.array(struct.unpack('>'+str(cols*rows)+'H',(base/'map.bin').read_bytes())).reshape(rows,cols)
 assert (m&2047).max()<count<=d['tileBudget']
 decoded=tiles[m&2047].reshape(rows,cols,8,8).copy()
 for yy in range(rows):
  for xx in range(cols):
   if m[yy,xx]&0x800:decoded[yy,xx]=decoded[yy,xx,:,::-1]
   if m[yy,xx]&0x1000:decoded[yy,xx]=decoded[yy,xx,::-1,:]
 native=colors[decoded.transpose(0,2,1,3).reshape(height,width)]
 expected=np.array(Image.open(G/d['art']['nativeImage']).convert('RGB'))
 assert np.array_equal(native,expected),(key,'native binary image mismatch')
 solids=d['solids'];left,top,width,height=d['walkable']
 def free(x,y):
  if not(left<=x<=left+width-16 and top<=y<=top+height-16):return False
  return not any(x<rx+rw and x+16>rx and y<ry+rh and y+16>ry for rx,ry,rw,rh,*_ in solids)
 start=tuple(d['start']);goal=(d['points'][-1][0]-8,d['points'][-1][1]-8)
 queue=deque([start]);seen={start}
 while queue:
  x,y=queue.popleft()
  for p in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
   if p not in seen and free(*p):seen.add(p);queue.append(p)
 assert goal in seen,(key,'arrival disconnected')
 assert any(r[0]>2048 and r[1]>=top for r in solids)
 if key=='06b':
  _,object_counts=packed_objectives();assert count+object_counts[3]+object_counts[4]<=640
 print(f'PASS {key}: {count} exact tiles,{d['width']}x{d['height']},16RGB333,zero pixel mismatches,{len(seen)} connected positions,arrival reachable')
