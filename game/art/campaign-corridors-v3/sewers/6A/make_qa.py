"""Static native comparison with production hero pixels; never an emulator claim."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,struct
P=Path(__file__).resolve().parent;ROOT=P.parent;G=P.parents[3]
words=struct.unpack('>16H',(G/'res/heroi/palette.bin').read_bytes());colors=[tuple(((v>>s)&7)*255//7 for s in [1,5,9])for v in words];b=(G/'res/heroi/frames.bin').read_bytes()[12*768:13*768];actor=Image.new('RGBA',(32,48));pix=actor.load()
for base,high,dy in [(0,4,0),(16,2,32)]:
 for x in range(4):
  for y in range(high):
   raw=b[(base+x*high+y)*32:(base+x*high+y+1)*32]
   for ry in range(8):
    for rx in range(8):
     v=raw[ry*4+rx//2];i=v&15 if rx%2 else v>>4;pix[x*8+rx,dy+y*8+ry]=(*colors[i],255 if i else 0)
for key in ['6A','6B']:
 folder=ROOT/key;d=json.loads((folder/'manifest.json').read_text());bg=Image.open(folder/('complete-closed-objectives.png'if key=='6B'else'complete-native.png')).convert('RGBA');poses=[];board=Image.new('RGB',(640,3*252),(16,25,30));dr=ImageDraw.Draw(board)
 for i,interest in enumerate(d['camera_interest']):
  x,y,w,h=interest['bbox'];px,py=interest['preferred_feet'];cx=max(0,min(2752,(x+w//2-160)//8*8));lo=max(0,y+h-224,py+16-224);hi=min(96,y-24,py-31-24);assert lo<=hi,(key,interest,lo,hi);cy=max(lo,min(hi,(y+h//2-124)//8*8));image=bg.copy();image.alpha_composite(actor,(px-8,py-31));frame=image.crop((cx,cy,cx+320,cy+224)).convert('RGB');fd=ImageDraw.Draw(frame);fd.rectangle((0,0,319,23),fill='#080e12');fd.text((4,6),'ESTUDO NATIVO + SPRITE REAL (sem emulador)',fill='white');poses.append({'name':interest['name'],'camera':[cx,cy],'feet':[px,py],'file':f'qa-interest-{i}.png'});frame.save(folder/f'qa-interest-{i}.png');bx=i%2*320;by=i//2*252;dr.text((bx+4,by+4),f'{key} {interest["name"]} cam{cx},{cy}',fill='white');board.paste(frame,(bx,by+24))
 board.save(folder/'qa-interest.png');(folder/'qa-interest.json').write_text(json.dumps({'kind':'static native background+real production hero frame, not emulator','poses':poses},ensure_ascii=False,indent=2)+'\n')
 if key=='6B':
  board=Image.new('RGB',(960,2*252),(16,25,30));dr=ImageDraw.Draw(board)
  for row,(gx,gy,_,_)in enumerate(d['gates']):
   cx=gx-160;cy=max(0,min(96,gy-48))
   for col,state in enumerate(['closed','collapse','open']):
    frame=Image.open(folder/f'complete-{state}-objectives.png').crop((cx,cy,cx+320,cy+224));x,y=col*320,row*252;dr.text((x+4,y+6),f'6B gate{row+1} {state} (estudo nativo)',fill='white');board.paste(frame,(x,y+24))
  board.save(folder/'qa-gate-states.png')
print('Static legal camera/actor interest poses assembled for both phases.')
