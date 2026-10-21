"""Technical nearest-neighbour/RGB333 preview of the image_gen backing."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parent
COLORS=[(36,36,36),(73,36,0),(109,36,0),(146,73,36),(182,109,36),(219,146,73),(219,182,109),(255,219,146),(255,219,182),(255,182,109),(73,73,36),(109,109,73),(146,146,109),(73,73,73),(182,109,73)]
# Preserve the distinct metal/olive accents rather than spending all palette
# entries on the much larger paper surface.
COLORS=[tuple(round(c*7/255)*255//7 for c in p) for p in COLORS]
palette=Image.new('P',(1,1));palette.putpalette([c for p in COLORS for c in p]+list(COLORS[0])*(256-len(COLORS)))
source=Image.open(ROOT/'painel-resistencia.png').convert('RGB')
native=source.resize((320,224),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB')
native.save(ROOT/'painel-nativo.png')
tiles={native.crop((x,y,x+8,y+8)).tobytes() for y in range(0,224,8) for x in range(0,320,8)}
(ROOT/'medicoes.json').write_text(json.dumps(dict(size=[320,224],colors=len(native.getcolors()),uniqueTiles=len(tiles),patternBytes=len(tiles)*32,palette='RGB333, up to 15 colors',method='fixed material-aware palette; nearest-neighbour size conversion; no dithering',note='Background preview only; tile arrangement and runtime restoration not yet implemented.'),indent=2)+'\n')
