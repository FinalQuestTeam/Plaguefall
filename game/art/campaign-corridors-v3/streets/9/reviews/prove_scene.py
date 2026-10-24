from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
A=Path(__file__).resolve().parents[1];m=json.loads((A/'manifest.json').read_text());world=Image.open(A/'complete-native.png').convert('RGB');parts={a['id']:a['size']for a in m['assemblies']};points=m['route_points'];samples=[]
def pose(cx):
 for a,b in zip(points,points[1:]):
  if a[0]<=cx<=b[0]:
   t=(cx-a[0])/max(1,b[0]-a[0]);return round(cx)-8,round(a[1]+t*(b[1]-a[1]))-8
 return (m['start']if cx<points[0][0]else[points[-1][0]-8,points[-1][1]-8])
def target(px,py):
 x=px+8-160;y=py-200;nearest=65;focus=None
 for it in m['camera_interest']:
  a,b,w,h=it['bbox'];dx=max(a-px-8,px+8-a-w,0);dy=max(b-py-8,py+8-b-h,0)
  if dx+dy<nearest:nearest=dx+dy;focus=(a,b,w,h)
 if focus:
  a,b,w,h=focus;y=max(b+h-224,min(y,b-24));x=max(a+w-320,min(x,a))
 y=max(py+8-224,min(y,py-55));x=max(px+24-320,min(x,px-8));return max(0,min(2240,x)),max(0,min(96,y))
for wanted in range(0,2241,8):
 px,py=pose(wanted+160);cx,cy=target(px,py);found=[]
 for n,x,y in m['placements']:
  w,h=parts[n];roof=64 if n=='dock'else 56 if n in ['office','warehouse','utility','utility-low']else 0
  iw=max(0,min(cx+320,x+w)-max(cx,x));ih=max(0,min(cy+224,y+h)-max(cy+24,y+roof))
  if iw>=48 and ih>=32:found.append([n,x,y,iw,ih])
 samples.append({'wantedCameraX':wanted,'position':[px,py],'camera':[cx,cy],'legibleVolumes':found})
failed=[s for s in samples if not s['legibleVolumes']];assert not failed,failed
board=Image.new('RGB',(1280,756),'#18202a');d=ImageDraw.Draw(board)
for i,xwant in enumerate([0,160,320,480,640,800,960,1120,1360,1600,1920,2240]):
 s=min(samples,key=lambda s:abs(s['wantedCameraX']-xwant));cx,cy=s['camera'];v=world.crop((cx,cy,cx+320,cy+224));dr=ImageDraw.Draw(v);dr.rectangle((0,0,319,23),fill='#18202a');dr.text((4,6),f'NATIVE CAMERA {cx},{cy}',fill='white');x=(i%4)*320;y=(i//4)*252;board.paste(v,(x,y));d.text((x+4,y+228),f'feet {s["position"]}',fill='white')
board.save(A/'reviews/passage-cameras.png');(A/'reviews/route-camera-samples.json').write_text(json.dumps(samples,indent=2)+'\n')
r={'phase':'9','status':'candidate_ready_for_parent_whole_and_camera_review','visual_cycles':[{'cycle':1,'verdict':'Rejected before approval:1299tiles; full source-yard cuts were too expensive and two material samples introduced wrong repeated details.'},{'cycle':2,'verdict':'Parent rejected navy asphalt (read as water) and detached light equipment pads; neutral existing grayscale asphalt replaces only road material, bounded equipment courtyards now have complete rear/front fences and side supports joining the perimeter.'}],'composition':['Entrance office court, southern service shed and passage bending north of it.','Three-bay loading warehouse, entire truck and a real upper detour.','Closed machine enclosure north opposite red warehouse south, with48px service gap.','Twin tank enclosure, two lower utilities and closed factory-gate arrival.'],'source':'source/whole-folded-cycle3.png','module_integrity':'Whole closed buildings assembled from caps, repeatable roof/wall material and complete doors/windows. Truck remains a complete source extraction. Compressor/stack, cylinder caps/body/base, gate posts/header/leaves use exact authored parts inside physical enclosures. No4px resampling or approximate tile replacements.','palette':'16RGB333, literal black0. Neutral asphalt uses existing gray index5; source road-dash silhouette uses yellow index14 on the same gray. Steel blues remain on equipment and roofs.','geometry':{**m['geometry'],'eight_pixel_route_clearance':True,'minimum_service_neck':40,'exit_reachable':True,'solids_count':len(m['solids']),'closed_gate_solids':'Two24x144posts and176x72closedleaf. Air below the leaf is free, avoiding an invisible whole-bbox barrier.'},'memory':m['memory'],'route_camera_proof':{'samples':len(samples),'step':8,'failed':len(failed),'criterion':'Every settled player-only route camera has visible architecture/equipment at least48px wide and32px high, excluding building roofs.','limitation':'Synthetic framing model, not emulator footage. Final controller/camera/streaming tests remain root responsibility.'},'visual_reviewed':['complete-native.png','reviews/camera-*.png','reviews/passage-cameras.png'],'remaining_risks':['Repeated office/utility roof grammar is visible but changes of volume, north/south placement and industrial equipment distinguish sectors.','Compressor pipes are smaller than the loading bays; the full enclosures provide physical context and human-scale cylinders/truck remain legible.','No ROM was built or playtested by this private generator; native approval does not prove runtime.' ],'bank_hashes':{n:hashlib.sha256((A/n).read_bytes()).hexdigest()for n in ['build.py','manifest.json','complete-native.png','native/tiles.bin','native/map.bin','native/palette.bin']},'shared_C_resources_ROM_or_factory10_11_changed':False}
(A/'reviews/native-review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('camera windows',len(samples),'failed',len(failed))
