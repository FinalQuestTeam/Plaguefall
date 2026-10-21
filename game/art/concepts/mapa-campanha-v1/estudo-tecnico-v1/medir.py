"""Provas OFFLINE de resolução, quantização RGB333 e custo de tiles.

Reutiliza o quantizador do projeto; não redesenha arte e não exporta para res/.
As prévias são decodificadas dos próprios padrões 4bpp e atributos de paleta.
Não executa main() dos exportadores importados e não toca na ROM.
"""
from pathlib import Path
import hashlib, importlib.util, json, math, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[3]
SOURCE=ROOT.parent/'paisagem-base.png'
spec=importlib.util.spec_from_file_location('map_study_quantizer',GAME/'art/title-caatinga-v1/export_title.py')
quant=importlib.util.module_from_spec(spec);spec.loader.exec_module(quant)

def convert(im,banks):
 w,h=im.size;tw,th=w//8,h//8;count=tw*th
 pixels=np.asarray(im,dtype=np.int32)
 tiles=pixels.reshape(th,8,tw,8,3).transpose(0,2,1,3,4).reshape(count,64,3)
 light=tiles.mean(axis=(1,2))
 groups=np.digitize(light,np.quantile(light,np.arange(1,banks)/banks))
 for _ in range(8):
  pals=[quant.palette(tiles[groups==i]) for i in range(banks)]
  distances=[((tiles[:,:,None,:]-p[None,None,:,:])**2).sum(axis=3) for p in pals]
  costs=np.stack([d.min(axis=2).mean(axis=1) for d in distances],axis=1)
  chosen=costs.argmin(axis=1)
  if np.array_equal(chosen,groups):break
  assert len(set(chosen))==banks
  groups=chosen
 # Recompute assignments from the actual final palette set.
 indices=np.stack([d.argmin(axis=2) for d in distances])[chosen,np.arange(count)].astype(np.uint8)
 packed=((indices[:,::2]<<4)|indices[:,1::2]).astype(np.uint8)
 words=np.array([quant.words(p) for p in pals],dtype=np.uint16)
 assert not np.any(words&0xF111)
 assert all(int(w)<=0xEEE for w in words.ravel())
 # Deduplicate identical 4bpp patterns, allowing lossless H/V flips.
 atlas=[];lookup={};tilemap=[];flips=[]
 for t in packed:
  key=t.tobytes()
  if key not in lookup:
   number=len(atlas);atlas.append(key)
   pix=np.empty(64,dtype=np.uint8);pix[::2]=t>>4;pix[1::2]=t&15;pix=pix.reshape(8,8)
   for flip,pattern in [(0,pix),(0x800,pix[:,::-1]),(0x1000,pix[::-1]),(0x1800,pix[::-1,::-1])]:
    flat=pattern.reshape(64);b=((flat[::2]<<4)|flat[1::2]).astype(np.uint8).tobytes()
    if b not in lookup:lookup[b]=(number,flip)
  number,flip=lookup[key];tilemap.append(number);flips.append(flip)
 # Every cell references one palette only; palette 0 of each bank is transparent.
 attrs=[n|f|((int(p)+1)<<13) for n,f,p in zip(tilemap,flips,chosen)]
 patterns=np.frombuffer(b''.join(atlas),dtype=np.uint8).reshape(-1,32)
 decoded=[]
 for attr in attrs:
  t=patterns[attr&0x7FF];a=np.empty(64,dtype=np.uint8);a[::2]=t>>4;a[1::2]=t&15;a=a.reshape(8,8)
  if attr&0x800:a=a[:,::-1]
  if attr&0x1000:a=a[::-1]
  decoded.append(pals[((attr>>13)&3)-1][a])
 rgb=np.array(decoded).reshape(th,tw,8,8,3).transpose(0,2,1,3,4).reshape(h,w,3).astype(np.uint8)
 expected=np.stack(pals)[chosen[:,None],indices].reshape(th,tw,8,8,3).transpose(0,2,1,3,4).reshape(h,w,3)
 assert np.array_equal(rgb,expected)
 opaque=len({tuple(v) for p in pals for v in p[1:] if any(v)})
 return Image.fromarray(rgb),{
  'size':[w,h],'cells':count,'uniqueTilesWithoutFlip':len(set(packed[i].tobytes() for i in range(count))),
  'uniqueTilesWithFlip':len(atlas),'tileBytes':len(atlas)*32,'tilemapCompactBytes':count*2,
  'paletteBanks':banks,'paletteBytes':banks*32,'uniqueOpaquePaletteColors':opaque,
  'rmseRGB888':round(float(np.sqrt(np.mean((pixels.astype(float)-rgb.astype(float))**2))),3),
  'palettesRGB333Words':[[f'{int(v):03X}' for v in p] for p in words],
  'onePalettePerTile':True,'roundtrip4bppExact':True,'lossyTileSubstitutions':0,
  'fitsRecommended800ArtTiles':len(atlas)<=800,
  'fitsCurrentLayoutWith128UITiles':len(atlas)<=1211,
  'rawAssetBytes':len(atlas)*32+count*2+banks*32,
 }

def main():
 bg=Image.open(SOURCE).convert('RGB')
 cases=[
  ('01-mapa-inteiro-2pal',None,(320,160),2,'MAPA INTEIRO / 2 PALETAS'),
  ('02-trecho-base-2pal',(636,150,1536,600),(320,160),2,'TRECHO AMPLIADO / 2 PALETAS'),
  ('03-trecho-base-3pal',(636,150,1536,600),(320,160),3,'MESMO TRECHO / 3 PALETAS'),
  ('04-panoramico-512-2pal',None,(512,160),2,'PANORAMA 512 / 2 PALETAS'),
  ('05-panoramico-640-2pal',None,(640,160),2,'PANORAMA 640 / 2 PALETAS'),
 ]
 report={'purpose':'offline investigation only; not a final game asset',
  'source':str(SOURCE.relative_to(GAME)),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  'method':'Project median-cut + RGB333 palette refinement, one bank per 8x8 cell, lossless exact pattern deduplication including flips; no dithering',
  'cropsAreNewArt':False,'gameImplemented':False,'tests':{}}
 previews=[]
 for name,crop,size,banks,label in cases:
  im=(bg.crop(crop) if crop else bg).resize(size,Image.Resampling.LANCZOS)
  native,stats=convert(im,banks);stats['sourceCrop']=crop;report['tests'][name]=stats
  native.save(ROOT/(name+'.png'));print(name,stats['uniqueTilesWithFlip'],'tiles',stats['rawAssetBytes'],'bytes',stats['rmseRGB888'],'RMSE',flush=True)
  if size==(320,160):previews.append((native,stats,label))
 canvas=Image.new('RGB',(1100,1220),'#11191c');d=ImageDraw.Draw(canvas)
 f='/System/Library/Fonts/Supplemental/Arial.ttf';b='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
 d.text((35,20),'O LIMITE É A LEITURA, NÃO SÓ A COR',font=ImageFont.truetype(b,31),fill='#f2dfc0')
 d.text((36,65),'Provas técnicas em 320 × 160 • ampliadas 2× sem suavização • fora do jogo',font=ImageFont.truetype(f,19),fill='#b9ae96')
 for i,(im,stats,label) in enumerate(previews):
  y=115+i*365;canvas.paste(im.resize((640,320),Image.Resampling.NEAREST),(35,y))
  d.text((700,y+12),label,font=ImageFont.truetype(b,19),fill='#ffbf57')
  lines=[f"{stats['uniqueTilesWithFlip']} tiles únicos",f"{stats['tileBytes']:,} bytes de padrões".replace(',','.'),
   f"{stats['uniqueOpaquePaletteColors']} cores opacas disponíveis",f"RMSE de cor: {stats['rmseRGB888']}",
   'Mesma densidade de objetos.' if i==2 else 'Detalhes competem a poucos pixels.' if i==0 else 'Marcos maiores preservam a leitura.']
  for j,line in enumerate(lines):d.text((700,y+63+j*38),line,font=ImageFont.truetype(f,18),fill='#f2dfc0')
 d.text((35,1200),'Medição de conversão; não representa arte final nem teste em emulador/console.',font=ImageFont.truetype(f,17),fill='#b9ae96')
 canvas.save(ROOT/'comparativo-tecnico.png')
 (ROOT/'medicoes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
