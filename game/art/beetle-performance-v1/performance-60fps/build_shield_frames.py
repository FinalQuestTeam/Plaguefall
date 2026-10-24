"""Compose the existing shield badge into the native purple actor tile frames."""
from pathlib import Path
import argparse,re,hashlib
PATTERN=['.bbbbbb.','b111111b','b144441b','b144441b','.b1441b.','.b1441b.','..b11b..','...bb...']
def main():
 p=argparse.ArgumentParser();p.add_argument('build_root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();root=a.build_root
 packed=bytearray((root/'res/insects/frames.bin').read_bytes())
 layout=[tuple(map(int,v)) for v in re.findall(r'\{(\d+),(\d+),(\d+),(\d+)\}',(root/'src/system/video/enemy_asset_layout.h').read_text())]
 for kind in [2,6,10]:
  offset,words,size,tiles=layout[kind]
  for frame in range(30):
   for y,row in enumerate(PATTERN):
    for x,c in enumerate(row):
     if c=='.':continue
     xx=size-8+x
     address=(offset+frame*words)*4+((xx//8)*(size//8)+y//8)*32+(y%8)*4+(xx%8)//2
     ink=11 if c=='b' else int(c);shift=0 if xx&1 else 4
     packed[address]=(packed[address]&~(15<<shift))|(ink<<shift)
 target=root/'res/insects/shield_frames.bin'
 if a.check:assert bytes(packed)==target.read_bytes()
 else:target.write_bytes(packed)
 print('shield_frames_sha256',hashlib.sha256(packed).hexdigest())
if __name__=='__main__':main()
