"""Analytical orthographic projection diagram, not artwork or game sprites."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
ROOT=Path(__file__).resolve().parent
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
image=Image.new('RGB',(1400,700),(24,30,38));draw=ImageDraw.Draw(image)
a=math.radians(60);scale=145

def rotate(p,t):
 x,y,z=p
 return (x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t),z)
def project(p,cx,cy):
 x,y,z=p
 return (cx+x*scale,cy+(y*math.sin(a)-z*math.cos(a))*scale)

def block(x0,y0,z0,x1,y1,z1):
 return [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
faces=[(0,1,2,3),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
boxes=[block(-.31,-.17,.92,.31,.17,1.48),block(-.24,-.16,.72,.24,.16,.94),block(-.24,-.12,.08,-.04,.12,.73),block(.04,-.12,.08,.24,.12,.73),block(-.25,-.28,0,-.03,.16,.12),block(.03,-.28,0,.25,.16,.12),block(-.4,-.25,1.05,-.29,.15,1.43),block(.29,-.35,1.05,.4,.15,1.43),block(-.1,-.16,1.49,.1,.06,1.74),block(.03,-.86,1.12,.14,-.12,1.24)]
for i,label in enumerate(['N: back','NE: back/right','L: right','SE: front/right','S: front']):
 t=math.radians(i*45);cx=140+i*280;cy=400
 draw.text((cx-110,88),label,font=font,fill='white')
 # Ground-plane radial axis, horizontal circle and a static volume proxy.
 ground=[project((.65*math.cos(k*math.pi/90),.65*math.sin(k*math.pi/90),0),cx,cy) for k in range(181)]
 draw.line(ground,fill=(90,110,130),width=2)
 polygons=[]
 for b in boxes:
  v=[rotate(p,t) for p in b]
  for j,f in enumerate(faces):
   coords=[v[k] for k in f]
   depth=sum(p[1]*math.cos(a)+p[2]*math.sin(a) for p in coords)/4
   color=(45,185,203) if j==5 else (90,104,120) if j in [1,3] else (62,75,90)
   polygons.append((depth,[project(p,cx,cy) for p in coords],color))
 for _,points,color in sorted(polygons,key=lambda p:p[0]):draw.polygon(points,fill=color,outline=(180,207,216))
 # Horizontal head-plane circle: minor/major = sin(60 degrees) = 0.866.
 top=[project(rotate((.37*math.cos(k*math.pi/90),.37*math.sin(k*math.pi/90),1.75),t),cx,cy) for k in range(181)]
 draw.polygon(top,fill=(47,201,213),outline=(225,246,247))
 tip=project(rotate((0,-.73,1.75),t),cx,cy);origin=project((0,0,1.75),cx,cy)
 draw.line([origin,tip],fill=(243,188,57),width=4)
 draw.ellipse((tip[0]-4,tip[1]-4,tip[0]+4,tip[1]+4),fill=(243,188,57))
 draw.text((cx-110,510),'same fixed camera',font=small,fill=(210,220,230))
draw.text((30,20),'GEOMETRY REFERENCE: fixed orthographic camera, elevation 60 degrees ABOVE GROUND',font=font,fill='white')
draw.text((30,570),'Cyan = horizontal top surfaces. Yellow = facing direction / weapon heading.',font=font,fill='white')
draw.text((30,605),'Horizontal circle ellipse ratio 0.866. Vertical height projects at 0.500. No low side profiles.',font=font,fill='white')
draw.text((30,640),'Static analytical volume proxy only; use character concept for identity and materials.',font=small,fill=(200,210,220))
image.save(ROOT/'orthographic-60-guide.png')
