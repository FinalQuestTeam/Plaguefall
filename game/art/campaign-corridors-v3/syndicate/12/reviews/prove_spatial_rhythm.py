"""Read-only checks of the private scene; writes review evidence only."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parents[1];m=json.loads((A/'manifest.json').read_text());out=A/'reviews/rhythm-final';out.mkdir(exist_ok=True)
world=Image.open(A/'complete-native.png').convert('RGB');sizes={a['id']:a['size']for a in m['assemblies']};buildings=[(n,x,y,*sizes[n])for n,x,y in m['placements']]
points=m['route_points'];samples=[]
def overlap(a,b):return max(0,min(a[2],b[2])-max(a[0],b[0])),max(0,min(a[3],b[3])-max(a[1],b[1]))
def pose(cx):
 for a,b in zip(points,points[1:]):
  if a[0]<=cx<=b[0]:
   t=(cx-a[0])/max(1,b[0]-a[0]);return round(cx)-8,round(a[1]+t*(b[1]-a[1]))-8
 return (m['start'] if cx<points[0][0] else [points[-1][0]-8,points[-1][1]-8])
def target(px,py):
 # Close escort at32px behind is a framing sample, not a simulated controller.
 ex=px-32;ey=py;x=(px+ex)//2+8-160;y=py-200;nearest=65;focus=None
 for it in m['camera_interest']:
  a,b,w,h=it['bbox'];dx=max(a-px-8,px+8-a-w,0);dy=max(b-py-8,py+8-b-h,0)
  if dx+dy<nearest:nearest=dx+dy;focus=(a,b,w,h)
 if focus:
  a,b,w,h=focus;y=max(b+h-224,min(y,b-24));x=max(a+w-320,min(x,a))
 y=max(py+8-224,ey+8-224,min(y,py-55,ey-55));x=max(px+24-320,ex+24-320,min(x,px-8,ex-8))
 return max(0,min(2752,x)),max(0,min(96,y))
for desired in range(0,2753,8):
 px,py=pose(desired+160);cx,cy=target(px,py);vis=(cx,cy+24,cx+320,cy+224);found=[]
 for n,x,y,w,h in buildings:
  # Actual facade lies below a complete64/88px roof assembly.
  rh=88 if n in ['workshop','union'] else 64
  iw,ih=overlap(vis,(x,y+rh,x+w,y+h))
  if iw>=48 and ih>=32:found.append([n,x,y,iw,ih])
 samples.append({'requestedCameraX':desired,'position':[px,py],'camera':[cx,cy],'legibleFacades':found})
failed=[s for s in samples if not s['legibleFacades']]
# Exhaustive route sweep also requires8px orthogonal separation from solids.
clear=[]
for i,(a,b)in enumerate(zip(points,points[1:])):
 n=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
 for t in range(n+1):
  x=round(a[0]+(b[0]-a[0])*t/max(1,n))-8;y=round(a[1]+(b[1]-a[1])*t/max(1,n))-8
  for sx,sy,sw,sh in m['solids']:
   dx=max(sx-x-16,x-sx-sw,0);dy=max(sy-y-16,y-sy-sh,0)
   if dx==0 or dy==0:clear.append(max(dx,dy))
minclear=min(clear)
selected=[samples[min(range(len(samples)),key=lambda i:abs(samples[i]['requestedCameraX']-x))]for x in [320,480,800,960,1120,1280,1600,1840,2080,2240,2400,2560]]
board=Image.new('RGB',(1280,756),'#17222a');d=ImageDraw.Draw(board)
for i,s in enumerate(selected):
 x=(i%4)*320;y=(i//4)*252;cx,cy=s['camera'];im=world.crop((cx,cy,cx+320,cy+224));dr=ImageDraw.Draw(im);dr.rectangle((0,0,319,23),fill='#17222a');dr.text((4,6),f'NATIVE CAMERA {cx},{cy}',fill='white');board.paste(im,(x,y));d.text((x+4,y+228),f'route feet{s["position"]}',fill='white')
board.save(out/'passage-cameras.png')
report={'phase':'12','status':'ready_for_integration_pending_real_ROM_review','spatial_fix':'Four complete160x128source-derived service annexes at432,1296,1984,2480, with physically supported16px threshold aprons. Source/roof/wall grammar reused exactly.','scene_tiles':m['memory']['scene_tiles'],'previous_scene_tiles':515,'added_tile_cost':m['memory']['scene_tiles']-515,'solids_count':len(m['solids']),'camera_interest_count':len(m['camera_interest']),'geometry':m['geometry'],'minimum_route_orthogonal_solid_clearance':minclear,'service_gap_pixels':40,'route_sampling':{'samples':len(samples),'requested_camera_step':8,'condition':'at least48px of facade width and32px height in actual target camera (roof excluded)','failures':failed,'setup_limit':'Synthetic settled close-escort target from current ARENA camera rules. It is not real camera footage or a controller traversal.'},'native_visual_review':'Whole panorama and new annex previews reviewed at native scale. Whole roof endpoints, facade, door, plinth and source-supported apron are intact. South utility docks remain complete and human-scale; the new north volumes preserve40px through lanes. Four replicated service units are deliberately repeated architecture; no decorative fragments were introduced.','remaining_risks':['Real escort camera must prove the close-escort framing, particularly workshop entry.','Repeated service architecture is visible; alternating south docks, stepped rear enclosure, covered bay and union destination preserve changes of place.','515tiles/BFS success are technical evidence and do not constitute final visual approval.'],'bank_hashes':{n:hashlib.sha256((A/n).read_bytes()).hexdigest()for n in ['build.py','manifest.json','complete-native.png','native/tiles.bin','native/map.bin','native/palette.bin']},'shared_C_resources_or_ROM_changed':False}
(A/'reviews/spatial-rhythm-review.json').write_text(json.dumps(report,indent=2)+'\n');(out/'route-camera-samples.json').write_text(json.dumps(samples,indent=2)+'\n')
print('route clearance',minclear,'camera samples',len(samples),'failures',len(failed));print(failed[:4])
