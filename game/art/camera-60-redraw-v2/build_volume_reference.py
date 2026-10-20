"""Camera calibration with three analytical ellipsoids; no sprite artwork."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
ROOT=Path(__file__).resolve().parent
im=Image.new('RGB',(1400,630),(25,31,40));d=ImageDraw.Draw(im)
f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
s=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
a=math.radians(60);scale=140

def rot(p,t):
 x,y,z=p;return (x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t),z)
def screen(p,cx,cy):
 x,y,z=p;return (cx+x*scale,cy+(y*math.sin(a)-z*math.cos(a))*scale)
def ellipsoid(center,radius,t,cx,cy):
 faces=[];nu,nv=24,12
 def pos(u,v):
  return rot((center[0]+radius[0]*math.sin(v)*math.cos(u),center[1]+radius[1]*math.sin(v)*math.sin(u),center[2]+radius[2]*math.cos(v)),t)
 for v in range(nv):
  for u in range(nu):
   points=[pos(j*2*math.pi/nu,k*math.pi/nv) for j,k in [(u,v),(u+1,v),(u+1,v+1),(u,v+1)]]
   depth=sum(p[1]*math.cos(a)+p[2]*math.sin(a) for p in points)/4
   top=(v+.5)/nv<.5
   color=(44,190,205) if top else (71,86,106)
   faces.append((depth,[screen(p,cx,cy) for p in points],color))
 return faces
for i,label in enumerate(['N: front UP','NE: front UP-RIGHT','L: front RIGHT','SE: front DOWN-RIGHT','S: front DOWN']):
 t=math.radians(45*i);cx=140+280*i;cy=360
 d.text((cx-120,80),label,font=f,fill='white')
 polys=[]
 for center,radius in [((0,.55,.3),(.3,.4,.22)),((0,0,.32),(.2,.25,.2)),((0,-.5,.3),(.33,.3,.18))]:polys+=ellipsoid(center,radius,t,cx,cy)
 for _,pts,color in sorted(polys,key=lambda x:x[0]):d.polygon(pts,fill=color,outline=(45,104,122))
 arrow=[screen(rot(p,t),cx,cy) for p in [(0,-.7,.3),(0,-1.0,.3)]]
 d.line(arrow,fill=(255,205,64),width=4)
 d.ellipse((arrow[1][0]-4,arrow[1][1]-4,arrow[1][0]+4,arrow[1][1]+4),fill=(255,205,64))
 d.text((cx-110,470),'TOP visible in ALL views',font=s,fill='white')
d.text((20,20),'HORIZONTAL VOLUMES: fixed camera elevation60 ABOVE GROUND,30 from vertical',font=f,fill='white')
d.text((25,530),'Cyan = upper hemispheres. Gray = lower surfaces. Same three volumes, different ground headings.',font=f,fill='white')
d.text((25,565),'Match the third view when facing RIGHT: broad upper surfaces, NOT an eye-level side profile.',font=f,fill='white')
d.text((25,600),'Projection x=x; screen_y=y*sin60-z*cos60. This is a geometric construction guide, not creature art.',font=s,fill=(200,210,220))
im.save(ROOT/'horizontal-volumes-60-guide.png')
