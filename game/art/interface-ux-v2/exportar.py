"""Approved backing/copy -> RGB333 VDP tiles and data-only mission metadata."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,struct,re,textwrap
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parents[1]
import sys
sys.path.insert(0,str(GAME/'tools'))
from text_codec import encode
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
 im=Image.open(ROOT/'source/painel-nativo.png').convert('RGB');d=ImageDraw.Draw(im)
 d.rectangle((13,14,306,25),fill=(255,219,146));d.rectangle((12,202,307,219),fill=(73,36,0));d.line((12,202,307,202),fill=(146,73,36));d.line((16,30,303,30),fill=(146,109,73))
 def snap(p):return tuple(round(c*7/255) for c in p)
 # All changes are material colors already present in the approved palette.
 colors=list(dict.fromkeys(snap(p) for p in Image.open(ROOT/'source/painel-nativo.png').convert('RGB').getdata()))
 light=snap((255,219,146));colors.remove(light);colors.append(light)
 assert len(colors)==15
 def index(p):return 1+min(range(15),key=lambda i:sum((a-b)**2 for a,b in zip(snap(p),colors[i])))
 px=list(map(index,im.getdata()));tiles=[];lookup={};mapping=[]
 for y in range(28):
  for x in range(40):
   tile=bytes((px[(y*8+r)*320+x*8+c]<<4)|px[(y*8+r)*320+x*8+c+1] for r in range(8) for c in range(0,8,2))
   if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
   mapping.append(lookup[tile])
 pal=[0]+[sum(c<<s for c,s in zip(p,(1,5,9))) for p in colors]
 rust=index((109,36,0))
 outputs={GAME/'res/interface/tiles.bin':b''.join(tiles),GAME/'res/interface/map.bin':struct.pack('>1120H',*mapping),GAME/'res/interface/palette.bin':struct.pack('>16H',*pal)}
 outputs[GAME/'res/interface_data.res']=b'// Shared resistance panel. Background PAL3; transparent font and native icons.\nBIN interface_tiles "interface/tiles.bin" 4\nBIN interface_map "interface/map.bin" 2\nBIN interface_palette "interface/palette.bin" 2\n'
 constants=f'#ifndef PANEL_DATA_H\n#define PANEL_DATA_H\n#define PANEL_TILE_COUNT {len(tiles)}\n#define PANEL_RUST_INDEX {rust}\n#endif\n'
 outputs[GAME/'src/system/video/screens/panel_data.h']=constants.encode()
 phases=json.loads((ROOT/'conteudo-aprovado.json').read_text())['phases']
 header='#ifndef MISSION_COPY_H\n#define MISSION_COPY_H\ntypedef struct { const char *name, *attention, *route; } MissionCopy;\nstatic const MissionCopy MISSION_COPY[NODE_MAX] = {\n'
 for p in phases:
  header+=f'    [N_{p["id"]}] = {{ {json.dumps(p["name"],ensure_ascii=False)}, {json.dumps(p["attention"],ensure_ascii=False)}, {json.dumps(p["route"],ensure_ascii=False) if p["route"] else "NULL"} }},\n'
 header+='};\n#endif\n';outputs[GAME/'src/system/video/screens/mission_copy.h']=header.encode()
 help_cases=[c for c in json.loads((ROOT/'conteudo-aprovado.json').read_text())['cases'] if c['group']=='Como jogar']
 help_header='#ifndef HELP_COPY_H\n#define HELP_COPY_H\ntypedef struct { const char *text; u8 x,y,palette; } HelpLine;\n'
 for i,c in enumerate(help_cases):
  help_header+=f'static const HelpLine HELP_LINES_{i}[] = {{\n'
  for line in c['lines']:
   pal={'body':'PANEL_BODY','accent':'PANEL_ACCENT','light':'PANEL_LIGHT'}[line['palette']]
   help_header+=f'    {{ {json.dumps(line["text"],ensure_ascii=False)}, {line["x"]}, {line["y"]}, {pal} }},\n'
  help_header+='};\n'
 help_header+=f'#define HELP_PAGE_COUNT {len(help_cases)}\n'
 help_header+='static const HelpLine *const HELP_LINES[] = {'+','.join('HELP_LINES_'+str(i) for i in range(len(help_cases)))+'};\n'
 help_header+='static const u8 HELP_LINE_COUNT[] = {'+','.join(str(len(c['lines'])) for c in help_cases)+'};\n#endif\n'
 outputs[GAME/'src/system/video/screens/help_copy.h']=help_header.encode()
 story=re.sub(r'//[^\n]*','',(GAME/'src/levels/story.c').read_text())
 for text in re.findall(r'(?:ESQUERDA|DIREITA)\(\w+,\s*"([^"]*)"',story):
  assert encode(text) and text==text.upper(),text
  assert len(textwrap.wrap(text,width=34,break_long_words=False))<=4,text
 for path,content in outputs.items():
  if args.check:assert path.read_bytes()==content,str(path)
  else:path.write_bytes(content)
 print(f'Interface: {len(tiles)} tiles / {len(tiles)*32} bytes; 15 opaque colors; 20 mission records.')
if __name__=='__main__':main()
