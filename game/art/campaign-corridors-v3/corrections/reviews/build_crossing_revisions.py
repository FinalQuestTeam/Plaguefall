"""Private crossing-context revisions only. No canonical scene/C/ROM writes."""
from pathlib import Path
import copy, hashlib, importlib.util, json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parent
COR=R.parent
G=COR.parents[2]
sys.path.insert(0,str(G/'tools'))
import campaign_geometry as geom
import campaign_corridors as bridge
spec=importlib.util.spec_from_file_location('nativepack',G/'art/campaign-whole-scenes-v1/pack.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
hero=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA')
din=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/dinorah-production-frame.png').convert('RGBA')
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',10)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def camera(m,px,py,npc=None):
    x=(px+npc[0])//2-152 if npc else px-152
    y=((py+npc[1])//2 if npc else py)-m.get('camera_player_y',200)
    closest=65;focus=None
    for item in m['camera_interest']:
        a,b,w,h=item['bbox'];dist=max(a-px-8,px+8-a-w,0)+max(b-py-8,py+8-b-h,0)
        if dist<closest:closest=dist;focus=(a,b,w,h)
    if focus:
        a,b,w,h=focus;y=min(b-24,max(b+h-224,y));x=min(a,max(a+w-320,x))
    for ax,ay in [(px,py)]+([npc] if npc else []):
        y=min(ay-71,max(ay+8-224,y));x=min(ax-8,max(ax+24-320,x))
    return [max(0,min(m['size'][0]-320,x)),max(0,min(96,y))]

def route_feet(m):
    return m.get('player_waypoints') or [[x-8,y-8] for x,y in m['route_points']]

def sample_route(m):
    dense=[]
    points=route_feet(m)
    for a,b in zip(points,points[1:]):
        steps=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
        for i in range(steps+1):
            p=[round(a[0]+(b[0]-a[0])*i/max(1,steps)),round(a[1]+(b[1]-a[1])*i/max(1,steps))]
            if geom.free(m,*p):dense.append(p)
    return [min(dense,key=lambda p:abs(p[0]-x)) for x in range(0,m['size'][0],160)]

def view(im,m,feet,escort=True):
    px,py=feet
    npc=geom.closest(m,px-32,py) if escort else None
    cx,cy=camera(m,px,py,npc)
    frame=im.convert('RGBA').crop((cx,cy,cx+320,cy+224))
    for ax,ay,sprite in sorted([(px,py,hero)]+([(npc[0],npc[1],din)] if npc else []),key=lambda a:a[1]):
        frame.alpha_composite(sprite,(ax-8-cx,ay-31-cy))
    draw=ImageDraw.Draw(frame);draw.rectangle((0,0,319,23),fill='#181818')
    draw.text((4,6),'PRÉVIA, NÃO ROM / '+m['phase'],font=font,fill='#dadaaf')
    return frame.convert('RGB'),[cx,cy],npc

def cameras(dest,im,m,escort=True):
    folder=dest/'cameras-continuous';folder.mkdir(exist_ok=True)
    data=[]
    for i,feet in enumerate(sample_route(m)):
        frame,cam,npc=view(im,m,feet,escort)
        name=f'x{i*160:04}.png';frame.save(folder/name)
        data.append(dict(path='cameras-continuous/'+name,feet=feet,camera=cam,follower_feet=npc,
                         label='prévia, não ROM',actor_y_anchor='py-31; same as renderer'))
    for page in range((len(data)+5)//6):
        sheet=Image.new('RGB',(960,496),(24,24,24));d=ImageDraw.Draw(sheet)
        for j,row in enumerate(data[page*6:(page+1)*6]):
            x=j%3*320;y=j//3*248
            sheet.paste(Image.open(dest/row['path']),(x,y+24))
            d.text((x+4,y+6),f'{row["feet"]} cam{row["camera"]}',font=font,fill='#dddab6')
        sheet.save(dest/f'continuous-page-{page+1}.png')
    write(dest/'continuous-cameras.json',data)
    return data

for key in ['6A','6B']:
    base=COR/(key+'-guidebook');dest=base/'revisions/01-crossing-context';dest.mkdir(parents=True,exist_ok=True)
    m=copy.deepcopy(json.loads((base/'manifest.json').read_text()))
    protected=[base/'manifest.json',base/'complete-native.png',*(base/'native').glob('*.bin')]
    before={str(p):sha(p) for p in protected}
    im=Image.open(base/'complete-indexed.png');assert im.mode=='P'
    original=im.copy();pal=[tuple(im.getpalette()[i:i+3]) for i in range(0,48,3)]
    # Exact whole machine, including its complete opaque frame and plinth.
    src=[1672,128,128,104] if key=='6A' else [808,64,96,80]
    target=[688,104] if key=='6A' else [696,112]
    placements=[dict(id='closed-pump-recess',source_bbox_xywh=src,position=target),
                dict(id='entry-maintenance-bay',source_bbox_xywh=[2848,72,48,48],position=[512,48]),
                dict(id='middle-north-maintenance-bay',source_bbox_xywh=[2848,72,48,56],position=[1168,24]),
                dict(id='middle-maintenance-bay',source_bbox_xywh=[2848,72,48,56],position=([2000,24] if key=='6A' else [1792,24])),
                dict(id='late-maintenance-bay',source_bbox_xywh=[2848,72,48,56],position=[2704,32])]
    for p in placements:
        x,y,w,h=p['source_bbox_xywh'];dx,dy=p['position']
        assert not any(geom.free(m,xx,yy) for xx in range(dx,dx+w,8) for yy in range(dy,dy+h,8)),p
        im.paste(original.crop((x,y,x+w,y+h)),(dx,dy))
        p.update(complete_module=True,source='../../complete-indexed.png',
                 geometry='Wholly inside the existing blocked northern region; no new feet/shot collider.')
    im.save(dest/'complete-indexed.png')
    limit=384 if key=='6B' else 640
    _,stats=pack.pack({'map':im},pal,dest/'native',key.lower()+'_crossing',limit)
    shutil.copy2(dest/'native/map-native.png',dest/'complete-native.png')
    m['status']='isolated crossing-context revision; needs whole-map/continuous-camera review; no activation'
    m['complete']='complete-native.png'
    m['native']=dict(tiles='native/tiles.bin',map='native/map.bin',palette='native/palette.bin')
    m['memory']=dict(scene_tiles=stats['tiles'],objective_tiles=256 if key=='6B' else 0,
                     total_tiles=stats['tiles']+(256 if key=='6B' else 0),budget=640,
                     exact_native_tile_reuse=True,lossy_tile_substitutions=0,map_bytes=30720)
    m['sources']=[dict(path=os.path.relpath(base/'complete-indexed.png',dest),
                       game_path=str((base/'complete-indexed.png').relative_to(G)),
                       sha256=sha(base/'complete-indexed.png'))]
    m['revision_placements']=placements
    m['revision_scope']='Resident whole pump and maintenance unit only. Bounds/solids/route/camera/objectives unchanged.'
    m['preview_cameras']=[]
    for i,it in enumerate(m['camera_interest']):
        feet=it.get('preferred_feet',it.get('position'));frame,cam,npc=view(im,m,feet)
        filename=f'camera-{i+1}.png';frame.save(dest/filename)
        m['preview_cameras'].append(dict(id=it['name'],position=feet,camera=cam,
                                        follower_feet=npc,preview=filename,actor_y_anchor='py-31'))
    frames={}
    if key=='6B':
        path=G/'art/objective-sprites-v1/frames'
        for state in ['closed','collapse','open']:
            out=im.convert('RGBA')
            if state!='open':
                gate=Image.open(path/('gate-0.png' if state=='closed' else 'gate-5.png')).convert('RGBA')
                for gx,gy,*_ in m['gates']:out.alpha_composite(gate,(gx-16,gy))
            valve=Image.open(path/('valve-0.png' if state=='closed' else 'valve-3.png')).convert('RGBA')
            for vx,vy in m['valves']:out.alpha_composite(valve,(vx-16,vy-24))
            out.convert('RGB').save(dest/f'complete-{state}-objectives.png');frames[state]=out
        # Replace five preview images with closed objectives composed at runtime coordinates.
        for i,it in enumerate(m['camera_interest']):
            frame,cam,npc=view(frames['closed'],m,it['preferred_feet'])
            frame.save(dest/f'camera-{i+1}.png')
    continuous=cameras(dest,frames.get('closed',im),m)
    m['continuous_preview_step_world_x']=160
    m['continuous_previews']='continuous-cameras.json'
    geometry=geom.validate(dict(m,points=m['route_points']))
    m['revision_geometry_validation']=geometry
    write(dest/'manifest.json',m)
    bridge.FOLDERS[key]='corrections/'+key+'-guidebook/revisions/01-crossing-context'
    bridge.read(key)
    assert all(sha(Path(p))==digest for p,digest in before.items())
    write(dest/'review.json',dict(status='awaiting critical visual review',phase=key,
          memory=m['memory'],geometry=geometry,placements=placements,
          baseline_files_unchanged=before,actor_anchor_corrected_to_renderer=True,
          native_exact_reassembly=True,continuous_cameras=len(continuous),
          limits=['Composed native previews, not runtime evidence.','Maintenance canopy repeats four times; stop here unless whole-scene review finds an actual remaining defect.','No story/roster/geometry/active C/ROM changes.']))
    print(key,m['memory'])

# Latest9 is reviewed read-only, at the same interval and true actor anchor.
p9=COR/'9-guidebook';m9=json.loads((p9/'manifest.json').read_text())
d9=R/'9-revision3-continuous';d9.mkdir(exist_ok=True)
cameras(d9,Image.open(p9/'complete-native.png'),m9,False)
write(d9/'source.json',dict(path=os.path.relpath(p9/'complete-native.png',d9),
                          sha256=sha(p9/'complete-native.png'),scope='read-only offline camera audit'))
