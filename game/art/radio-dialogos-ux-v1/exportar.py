"""Export approved UI geometry; original portrait resources stay unchanged."""
from pathlib import Path
from PIL import Image
import argparse,struct,re,json,runpy
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
 # Reuse the proposal's native UI composition, without running its publisher.
 ns={'__file__':str(ROOT/'propor.py')};source=(ROOT/'propor.py').read_text().split("padre='DAMIAO")[0];exec(compile(source,'approved-layout','exec'),ns)
 ns['scene']=lambda node=1,clean=False:Image.new('RGBA',(320,224),(0,0,0,0))
 original_text=ns['text'];ns['text']=lambda *a,**k:None
 ns['portrait']=lambda im,who,x,y,active:ns['plate'](im,(x-8,y-8,64,64),active)
 frames=[ns['dialogue']('PADRE',''),ns['dialogue']('DAMIAO','')]
 # Small combat countdown, opaque everywhere within its rectangle; no BG_A
 # clearing is needed when the countdown is drawn through hardware sprites.
 ns['text']=original_text
 # Render the approved digits directly through the countdown definition.
 tail=(ROOT/'propor.py').read_text().split('def countdown(')[1].split('\nfor n in (3,2,1):')[0]
 exec('def countdown('+tail,ns)
 countdown=[ns['countdown'](n).crop((88,8,232,88)) for n in (3,2,1)]
 go=ns['countdown']('VAI').crop((112,16,208,48))
 pal=ns['PAL'];lookup={rgb:i for i,rgb in enumerate(pal)}
 def index(rgb):return lookup.get(rgb,min(range(1,16),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,pal[i]))))
 def encode(images):
  tiles=[bytes(32)];seen={tiles[0]:0};maps=[]
  for im in images:
   im=im.convert('RGBA');mp=[]
   for y in range(0,im.height,8):
    for x in range(0,im.width,8):
     pixels=[0 if im.getpixel((x+dx,y+dy))[3]==0 else index(im.getpixel((x+dx,y+dy))[:3]) for dy in range(8) for dx in range(8)]
     tile=bytes(pixels[i]<<4|pixels[i+1] for i in range(0,64,2))
     if tile not in seen:seen[tile]=len(tiles);tiles.append(tile)
     mp.append(seen[tile])
   maps+=mp
  return b''.join(tiles),struct.pack('>'+str(len(maps))+'H',*maps),len(tiles)
 rt,rm,rc=encode(frames);ct,cm,cc=encode(countdown+[go])
 # The countdown uses the existing object palette (PAL1), not a fifth palette.
 # Quantize the UI's 15 material colours to that existing palette once.
 words=struct.unpack('>16H',(GAME/'res/insects/palette.bin').read_bytes()) if (GAME/'res/insects/palette.bin').exists() else None
 if words is None:
  files=list((GAME/'res').rglob('*palette*.bin'))
  resource=(GAME/'res/insects.res').read_text() if (GAME/'res/insects.res').exists() else ''
  match=re.search(r'BIN insect_palette "([^"]+)"',resource)
  if match:words=struct.unpack('>16H',(GAME/'res'/match[1]).read_bytes())
 if words is None:raise RuntimeError('Locate native object palette')
 object_rgb=[tuple(round(((c>>s)&7)*255/7) for s in (1,5,9)) for c in words]
 mapping=[min(range(1,16),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,object_rgb[i]))) for rgb in pal]
 def sprite_data(im):
  im=im.convert('RGBA');data=bytearray()
  for by in range(0,im.height,32):
   for bx in range(0,im.width,32):
    for tx in range(bx,min(bx+32,im.width),8):
     for ty in range(by,min(by+32,im.height),8):
      for y in range(8):
       for x in range(0,8,2):
        values=[mapping[index(im.getpixel((tx+x+i,ty+y))[:3])] for i in (0,1)]
        data.append(values[0]<<4|values[1])
  return bytes(data)
 ct=b''.join(sprite_data(im) for im in countdown+[go]);cc=180
 outputs={GAME/'res/radio/tiles.bin':rt,GAME/'res/radio/map.bin':rm,GAME/'res/radio/countdown_tiles.bin':ct}
 # The selected holodeck replaces radio geometry only; countdown is unchanged.
 outputs.update(runpy.run_path(str(GAME/'art/dialogue-holodeck-v1/exportar.py'))['resources']())
 rc=len(outputs[GAME/'res/radio/tiles.bin'])//32
 outputs[GAME/'res/radio_data.res']=b'BIN radio_tiles "radio/tiles.bin" 4\nBIN radio_map "radio/map.bin" 2\nBIN radio_palette "radio/palette.bin" 2\nBIN countdown_tiles "radio/countdown_tiles.bin" 4\n'
 header=f'#ifndef RADIO_DATA_H\n#define RADIO_DATA_H\n#define RADIO_TILE_COUNT {rc}\n#define COUNTDOWN_TILE_COUNT {cc}\n#endif\n'
 outputs[GAME/'src/system/video/screens/radio_layout.h']=header.encode()
 assert cc<=15*16,cc
 for p,v in outputs.items():
  if args.check:assert p.read_bytes()==v,p
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
 print(json.dumps({'radioTiles':rc,'countdownTiles':cc,'countdownBytes':len(ct),'palettesAdded':0}))
if __name__=='__main__':main()
