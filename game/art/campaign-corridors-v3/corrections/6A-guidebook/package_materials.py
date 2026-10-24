"""Package isolated material-only proposals; never activates a scene or builds ROM."""
from pathlib import Path
from PIL import Image, ImageDraw
import copy, hashlib, json, os, sys

A=Path(__file__).resolve().parent; V=A.parents[1]; G=V.parents[1]
sys.path.insert(0,str(G/'tools'))
from campaign_geometry import validate, free, closest
import campaign_corridors as bridge

capture=json.loads((V/'captures/ntsc/capture-report.json').read_text())
hero=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/damiao-production-frame.png').convert('RGBA')
dinorah=Image.open(G/'art/campaign-pattern-v2/routes/review-evidence/dinorah-production-frame.png').convert('RGBA')
frame_folder=G/'art/objective-sprites-v1/frames'
frames={f'{name}-{n}':Image.open(frame_folder/f'{name}-{n}.png').convert('RGBA') for name,n in [('gate',0),('gate',5),('valve',0),('valve',3)]}
geometry_keys=['size','bounds','start','route_points','pauses','exit','solids','gates','valves','valve_approaches','gate_shot_approaches','camera_interest','camera_player_y']

for key in ['6A','6B']:
    dest=V/'corrections'/(key+'-guidebook'); canonical=V/'sewers'/key
    original=json.loads((canonical/'manifest.json').read_text()); m=copy.deepcopy(original)
    checkpoint=json.loads((dest/'material-checkpoint.json').read_text())
    m['complete']='complete-native.png'
    m['native']={'tiles':'native/tiles.bin','map':'native/map.bin','palette':'native/palette.bin','image':'complete-native.png','objectives':'complete-closed-objectives.png' if key=='6B' else 'complete-objectives.png'}
    m['status']='isolated material-only proposal, pending root whole-map/five-camera review and private ROM trial; not approved or activated'
    m['memory']={'scene_tiles':checkpoint['scene_tiles'],'objective_tiles':checkpoint['objective_tiles'],'total_tiles':checkpoint['total_tiles'],'budget':640,'approximate_tile_replacements':0}
    sources=[canonical/'manifest.json',canonical/'complete-native.png',canonical/'complete-indexed.png',G/'art/phase04-tunnels-v1/map-native.png']
    source_modules=canonical/('cycle3-candidate' if key=='6A' else 'candidate')
    sources += [source_modules/p.name for p in sorted((dest/'modules').glob('*.png'))]
    sources += [G/'art/campaign-pattern-v2/routes/review-evidence'/n for n in ['damiao-production-frame.png','dinorah-production-frame.png']]
    if key=='6B':sources += [frame_folder/(n+'.png') for n in frames]
    m['sources']=[{'path':os.path.relpath(p,dest),'game_path':str(p.relative_to(G)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]
    m.pop('sourcePaths',None)
    m['material_revision']={'source':'art/phase04-tunnels-v1/map-native.png','concrete_rect':[360,208,16,16],'grain_grid':1,'texture_resampling':False,'channel':'same existing quiet source grain, dark charcoal palette; mouth water pigments normalized without reshaping','architecture':'existing complete module alpha, cap, face and joint positions unchanged','first_discarded_trial':'Wet sludge crop repeated too visibly; rejected before review handoff.','objective_palette_changed':False,'actor_palette_changed':False}
    assert all(m[k]==original[k] for k in geometry_keys)
    gd=copy.deepcopy(m);gd['points']=gd['route_points'];checks=validate(gd)
    m['material_geometry_validation']=checks
    m['geometry_unchanged_from_canonical']=True

    raw=Image.open(dest/'complete-native.png').convert('RGBA')
    states=['closed','collapse','open'] if key=='6B' else ['closed']
    worlds={}
    for state in states:
        world=raw.copy()
        if key=='6B':
            if state!='open':
                for gx,gy,gw,gh in m['gates']:world.alpha_composite(frames['gate-0' if state=='closed' else 'gate-5'],(gx-16,gy))
            for vx,vy in m['valves']:world.alpha_composite(frames['valve-0' if state=='closed' else 'valve-3'],(vx-16,vy-24))
        worlds[state]=world
        filename=f'complete-{state}-objectives.png' if key=='6B' else 'complete-objectives.png'
        world.convert('RGB').save(dest/filename)

    samples=[s for p in capture['phases'] if p['phase']==key for s in p['samples'] if 'landmark-' in s['path']]
    assert len(samples)==5
    (dest/'cameras').mkdir(exist_ok=True)
    camera_records=[]
    for state in states:
        sheet=Image.new('RGB',(960,496),(20,23,28));sd=ImageDraw.Draw(sheet)
        for i,s in enumerate(samples):
            cx,cy=s['camera'];fx,fy=s['position']
            assert free(m,fx,fy)
            world=worlds[state]
            view=world.crop((cx,cy,cx+320,cy+224))
            # A separate existing actor frame. This is a composed preview, not new art or an emulator capture.
            follower=closest(m,fx-40,fy+24)
            if abs(follower[0]-fx)+abs(follower[1]-fy)<24:follower=closest(m,fx+40,fy+24)
            actors=[(fx,fy,hero),(follower[0],follower[1],dinorah)]
            for ax,ay,sprite in sorted(actors,key=lambda q:q[1]):view.alpha_composite(sprite,(ax-8-cx,ay-47-cy))
            actual=Image.open(V/'captures/ntsc'/s['path']).convert('RGBA')
            view.paste(actual.crop((0,0,320,24)),(0,0))
            filename=f'{i+1:02}-{state}.png';view.convert('RGB').save(dest/'cameras'/filename)
            tx=(i%3)*320;ty=(i//3)*248;sheet.paste(view.convert('RGB'),(tx,ty+24));sd.text((tx+4,ty+5),f'{i+1}. {s["label"]}',fill='white')
            if state=='closed':camera_records.append({**s,'preview':'cameras/'+filename,'follower_feet':list(follower),'evidence':'composed native preview using prior real camera coordinates and unchanged existing sprite/HUD; not a new running-ROM capture'})
        sheet.save(dest/('camera-sheet.png' if state=='closed' else f'camera-sheet-{state}.png'))
    m['preview_cameras']=camera_records
    m['art_limitations']=['This changes materials only: existing long corridor composition, native outlines, pumps, bays and gates remain. It does not claim to redesign the spatial macrocomposition.','The 16x16 material is repeated exactly; sparse 1px grain can still reveal repetition at enlarged viewing scale.','Dark drainage is conveyed by charcoal pigment and depth of existing banks; blue pipework remains on mechanical equipment.','Cameras are native composed previews at previously measured legal runtime coordinates. Actor placement is illustrative; no new emulator or gameplay measurement is claimed.','Root/user whole-map and private-ROM review is still required; tile and geometry checks are not visual approval.']
    (dest/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
    # Exercise the production reader against the private path through an in-memory folder override only.
    old=bridge.FOLDERS.copy();bridge.FOLDERS={**old,key:'corrections/'+key+'-guidebook'}
    b,*_=bridge.read(key);bridge.FOLDERS=old
    report={'phase':key,'status':'isolated candidate, awaiting whole-map and five-camera review','scope':'Material-only; no active metadata, shared generator, C, sprite palette or ROM edits','memory':m['memory'],'geometry_unchanged':True,'geometry':checks,'production_reader_private_validation':True,'native_decode_exact':True,'lossy_tile_substitutions':0,'palette_zero_black':True,'cameras':camera_records,'limits':m['art_limitations'],'sources':m['sources']}
    (dest/'review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    html=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Materiais '+key+'</title><style>body{background:#171b22;color:#eee;font:16px system-ui;margin:24px}p{max-width:1100px}a{color:#89d4ef}img{image-rendering:pixelated}.pan{overflow:auto;border:1px solid #555}.pan img{width:3072px;height:320px}li{margin:8px}</style><h1>'+key+' · proposta isolada de materiais</h1><p>Concreto e carvão com grão de 1 px extraído do native04. Geometria e sprites de objetivos preservados. Ainda não aprovada nem ativada.</p><p><a href="manifest.json">Manifesto</a> · <a href="review.json">Ressalvas/provas</a></p><h2>Cenário completo em1x</h2><div class="pan"><img src="complete-native.png"></div><h2>Cinco câmeras normais</h2><p>Composições nativas com HUD/atores existentes; não são novas capturas do emulador.</p><img src="camera-sheet.png">']
    if key=='6B':html += ['<h2>Transição das portas e válvulas existentes</h2><p>Mesmas coordenadas e mesmos sprites globais. Colapso temporário e passagem aberta.</p><img src="camera-sheet-collapse.png"><img src="camera-sheet-open.png">']
    html += ['<h2>Limites</h2><ul>']+['<li>'+x+'</li>' for x in m['art_limitations']]+['</ul></html>']
    (dest/'review.html').write_text('\n'.join(html))
    print(key,report['memory'],checks)
