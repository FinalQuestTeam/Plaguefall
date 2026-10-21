"""Offline RGB333/4bpp export; no runtime framebuffer or lossy tile substitution."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, struct
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
OUT=GAME/'res/routemap'
spec=importlib.util.spec_from_file_location('map_palette',GAME/'art/title-caatinga-v1/export_title.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
W,H=320,160

def convert(im):
 pixels=np.asarray(im,dtype=np.int32)
 tiles=pixels.reshape(20,8,40,8,3).transpose(0,2,1,3,4).reshape(800,64,3)
 light=tiles.mean(axis=(1,2));groups=(light>np.median(light)).astype(int)
 for _ in range(8):
  pals=[q.palette(tiles[groups==i]) for i in range(2)]
  distances=[((tiles[:,:,None,:]-p[None,None,:,:])**2).sum(axis=3) for p in pals]
  costs=np.stack([d.min(axis=2).mean(axis=1) for d in distances],axis=1)
  chosen=costs.argmin(axis=1)
  if np.array_equal(chosen,groups):break
  assert len(set(chosen))==2
  groups=chosen
 indices=np.stack([d.argmin(axis=2) for d in distances])[chosen,np.arange(800)].astype(np.uint8)
 packed=((indices[:,::2]<<4)|indices[:,1::2]).astype(np.uint8).tobytes()
 words=[v for p in pals for v in q.words(p)]
 assert all((v&0xF111)==0 for v in words)
 # Decode packed data, including one palette per cell, to verify production preview.
 raw=np.frombuffer(packed,dtype=np.uint8).reshape(800,32)
 decoded=np.empty((800,64),dtype=np.uint8);decoded[:,::2]=raw>>4;decoded[:,1::2]=raw&15
 assert np.array_equal(decoded,indices)
 rgb=np.stack(pals)[chosen[:,None],decoded].reshape(20,40,8,8,3).transpose(0,2,1,3,4).reshape(H,W,3)
 return packed,chosen.astype(np.uint8).tobytes(),struct.pack('>32H',*words),Image.fromarray(rgb.astype(np.uint8))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
 source=ROOT/'source/atlas.png';atlas=Image.open(source).convert('RGB');sw,sh=atlas.size
 blobs=[bytearray(),bytearray(),bytearray()];previews=[]
 for i in range(4):
  x,y=i%2,i//2
  box=(round(x*sw/2),round(y*sh/2),round((x+1)*sw/2),round((y+1)*sh/2))
  native=atlas.crop(box).resize((W,H),Image.Resampling.LANCZOS)
  tiles,groups,pals,preview=convert(native)
  for dest,data in zip(blobs,(tiles,groups,pals)):dest.extend(data)
  path=ROOT/f'region-{i+1}-native.png'
  if args.check:assert Image.open(path).convert('RGB').tobytes()==preview.tobytes()
  else:preview.save(path)
  previews.append(preview)
 files={OUT/f'{name}.bin':bytes(blob) for name,blob in zip(('tiles','groups','palettes'),blobs)}
 files[GAME/'res/routemap_data.res']=b'// Four 320x160 regional map backgrounds; PAL1/PAL2 per tile.\nBIN routemap_tiles "routemap/tiles.bin" 4\nBIN routemap_groups "routemap/groups.bin" 2\nBIN routemap_palettes "routemap/palettes.bin" 2\n'
 for path,data in files.items():
  if args.check:assert path.read_bytes()==data,path
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 report={'regions':4,'size':[W,H],'tilesPerRegion':800,'artVRAMBytes':25600,'paletteBanksPerRegion':2,
 'onePalettePerTile':True,'rgb333':True,'lossyTileSubstitutions':0,'roundtripExact':True,
 'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'files':{str(p.relative_to(GAME)):{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for p,v in files.items()}}
 if not args.check:
  (ROOT/'export.json').write_text(json.dumps(report,indent=2)+'\n')
  board=Image.new('RGB',(640,320))
  for i,im in enumerate(previews):board.paste(im,(i%2*W,i//2*H))
  board.resize((1280,640),Image.Resampling.NEAREST).save(ROOT/'regions-native-2x.png')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
