"""Revision3: expand two physical buildings using ONLY exact tiles already in rev2.
No new raster source, palette, tile approximation, active scene edit or ROM build.
"""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import hashlib,json,sys,os
A=Path(__file__).resolve().parent;G=A.parents[3];sys.path.insert(0,str(G/'tools'))
import build_campaign_factory as pack
from campaign_geometry import free,route,validate

H=A/'history/revision-2';old=Image.open(H/'complete-native.png');out=old.copy();palette=old.getpalette()
floor=Image.open(A/'modules/dust-floor.png');wall=Image.open(A/'modules/complete-industrial-wall.png')
def repeat(src,rect):pack.repeat(out,src,(0,0,*src.size),rect)
# Restore the moved truck and the old final small shop with existing ground/wall tiles.
repeat(floor,(1216,160,96,64));repeat(wall,(1792,32,128,80));repeat(floor,(1792,112,128,48))

def extend_whole(src,width):
    # Complete left/front support48px + intermediate shutter/roof16px + full right end48px.
    # The extended center is roof clay and one continuous industrial shutter, not repeated complete buildings.
    assert width%16==0 and src.size==(128,128)
    result=Image.new('P',(width,128));result.putpalette(palette)
    result.paste(src.crop((0,0,48,128)),(0,0))
    middle=src.crop((48,0,64,128))
    for x in range(48,width-48,16):result.paste(middle,(x,0))
    result.paste(src.crop((80,0,128,128)),(width-48,0))
    return result

full_n=old.crop((128,32,256,160));full_s=old.crop((640,160,768,288))
dock=extend_whole(full_n,288);warehouse=extend_whole(full_s,288)
out.paste(dock,(1152,32));out.paste(warehouse,(1728,144))
truck=old.crop((1216,160,1312,224));out.paste(truck,(1248,192))
dock.save(A/'modules/extended-loading-shed.png');warehouse.save(A/'modules/extended-south-warehouse.png')

# Explicitly prove every8x8pixel tile comes from the previously reviewed resident630tile bank.
oldtiles,*_=pack.pack(old);tiles,mapping,reused=pack.pack(out)
assert all(t in set(oldtiles) for t in tiles),'new tile introduced by extension'
assert len(tiles)<=630
assert out.crop((2392,48,2472,112)).tobytes()==old.crop((2392,48,2472,112)).tobytes()
out.save(A/'complete-native.png');(A/'native/tiles.bin').write_bytes(b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles));(A/'native/map.bin').write_bytes(b''.join(v.to_bytes(2,'big') for v in mapping));(A/'native/palette.bin').write_bytes((H/'native/palette.bin').read_bytes())

m=json.loads((H/'manifest.json').read_text())
# Same visible walls/courts. Replace only relocated truck/final shop physical volumes and add the dock.
m['solids']=[s for s in m['solids'] if s[:4] not in [[1792,32,128,128],[1216,160,96,64]]]
m['solids'] += [[1152,32,288,128,True],[1728,144,288,128,True],[1248,192,96,64,True]]
# Existing dock wall panel at1432was covered for8px by the wide roof; remaining whole panel is restored at1472.
# No need for a new fragment: retain complete wall service panel in the opposite unoccupied bay.
panel=Image.open(A/'modules/complete-valve-service-wall.png')
repeat(wall,(1440,32,96,80));out.paste(panel,(1472,32))
# Repack after the existing full wall panel move, again requiring only old exact tiles.
tiles,mapping,reused=pack.pack(out);assert all(t in set(oldtiles) for t in tiles) and len(tiles)<=630
out.save(A/'complete-native.png');(A/'native/tiles.bin').write_bytes(b''.join(bytes((t[i]<<4)|t[i+1] for i in range(0,64,2)) for t in tiles));(A/'native/map.bin').write_bytes(b''.join(v.to_bytes(2,'big') for v in mapping))
keys=[[288,184],[320,128],[848,128],[1056,184],[1112,184],[1112,264],[1376,264],[1552,264],[1560,184],[1680,184],[1680,120],[2048,120],[2160,128],[2424,136]]
way=route(m,keys);m['player_waypoints']=way;m['route_points']=[[x+8,y+8] for x,y in way];m['points']=m['route_points'];m['geometry_validation']=validate(m)
margin_samples=0
for p,q in zip(way,way[1:]):
    n=max(abs(p[0]-q[0]),abs(p[1]-q[1]))
    for i in range(n+1):
        x=p[0]+((q[0]-p[0])*i//n if n else 0);y=p[1]+((q[1]-p[1])*i//n if n else 0)
        assert free(m,x,y,8),('margin8',p,q,x,y)
        margin_samples+=1
m['geometry_validation'].update(margin_pixels=8,swept_margin_samples=margin_samples)
l,t,r,b=m['bounds'];legal={(x,y) for x in range(l,r-14,8) for y in range(t,b-14,8) if free(m,x,y,8)};seen={tuple(m['start'])};q=deque(seen)
while q:
    x,y=q.popleft()
    for n in [(x-8,y),(x+8,y),(x,y-8),(x,y+8)]:
        if n in legal and n not in seen:seen.add(n);q.append(n)
assert seen==legal
m['geometry_validation'].update(margin_free_positions=len(legal),all_margin_positions_connected=True)
focus=[('repair-workshop',[128,32,128,128],[184,184],[32,0]),('south-workshop',[640,160,128,128],[608,272],[456,72]),('loading-shed',[1152,32,288,128],[1280,168],[1128,0]),('south-warehouse',[1728,144,288,128],[1864,280],[1712,80]),('factory-entry',[2392,48,80,64],[2456,184],[2240,0])]
m['camera_interest']=[]
for name,bbox,feet,cam in focus:
    assert free(m,*feet,8),(name,'invalid pose',feet)
    x,y,w,h=bbox;cx,cy=cam
    assert cx<=x and x+w<=cx+320 and cy+24<=y and y+h<=cy+224
    m['camera_interest'].append({'id':name,'name':name,'bbox':bbox,'player_feet':feet,'position':feet,'camera':cam,'whole_below_HUD':True})
m['composition_revision']=3;m['status']='isolated revision3; two extended sheds from resident tiles; pending independent whole-map/five-camera review; not integrated or approved'
m['memory'].update(tiles=len(tiles),scene_tiles=len(tiles),background_tiles=len(tiles),total_tiles=len(tiles),tile_bytes=len(tiles)*32,graphics_bytes=len(tiles)*32,free_tiles=640-len(tiles),exact_flip_reused=reused)
m['landmarks']=['repair workshops','wide loading shed with continuous roof/shutter and loaded truck','wide southern storage shed with32pxrear service lane','rusty original factory perimeter and exact10/11door']
m['art_limitations']=['Two wide288pxsheds extend one existing128pxworkshop by exact intermediate roof/shutter strips. Their common clay-roof family remains visible; these are not newly generated industrial hangar assets.','All used8x8tiles and palette are from previous630tileproposal; exact tile reuse proves provenance/memory only, not composition quality.','The loading truck is now32pxahead of the wide north shed; rear/south warehouse has32pxservice depth before lowerwall.','Root must inspect whether the broad shutter/roof repetition reads as coherent working sheds rather than duplicated facade fragments.','Native actor/HUD previews are composed, not running-ROM captures. Active9andsharedC/ROMremainunchanged.']
m['revision3_tile_proof']={'all_tiles_from_revision2_bank':True,'previous_tiles':len(oldtiles),'new_unique_tiles':0,'palette_bytes_unchanged':True,'whole_ends_preserved':{'left':48,'right':48,'intermediate_strip':16},'new_buildings':[[1152,32,288,128],[1728,144,288,128]],'truck':[1248,192,96,64]}
m['module_provenance']['extended-loading-shed']={'source':'art/campaign-corridors-v3/corrections/9-guidebook/history/revision-2/complete-native.png','crop':[128,32,128,128],'extension':'left48 + repeated exact center16 + right48','size':[288,128]}
m['module_provenance']['extended-south-warehouse']={'source':'art/campaign-corridors-v3/corrections/9-guidebook/history/revision-2/complete-native.png','crop':[640,160,128,128],'extension':'left48 + repeated exact center16 + right48','size':[288,128]}
source=H/'complete-native.png'
m['sources'].append({'path':os.path.relpath(source,A),'game_path':str(source.relative_to(G)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
m['source_paths_game']=[s['game_path'] for s in m['sources']]
m['limits']=m['art_limitations'];m['review_status']=m['status'];m['native_sha256']=hashlib.sha256(out.convert('RGB').tobytes()).hexdigest()
m['views']=[{'file':f'cameras/{i+1:02}.png','feet':f['position'],'camera':f['camera']} for i,f in enumerate(m['camera_interest'])]
(A/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');(A/'memory.json').write_text(json.dumps(m['memory'],indent=2)+'\n')
hero=Image.open(G/'art/cangaco-protagonista-iso60-v2/heroi/heroi.png').crop((0,0,32,48)).convert('RGBA');hud=Image.open(G/'art/campaign-corridors-v3/captures/ntsc/9/landmark-0.png').crop((0,0,320,24)).convert('RGBA')
sheet=Image.new('RGB',(960,488),(20,24,28));draw=ImageDraw.Draw(sheet)
for i,focus in enumerate(m['camera_interest']):
    fx,fy=focus['position'];cx,cy=focus['camera'];world=out.convert('RGBA');world.alpha_composite(hero,(fx-8,fy-47));view=world.crop((cx,cy,cx+320,cy+224));view.alpha_composite(hud,(0,0));view.save(A/f'cameras/{i+1:02}.png');tx=i%3*320;ty=i//3*244;sheet.paste(view,(tx,ty+20));draw.text((tx+2,ty+3),str(i+1)+'. '+focus['name'],fill='white')
sheet.save(A/'camera-sheet.png')
# Keep the private overlay and optional C contract synchronized; shared files remain untouched.
overlay=out.convert('RGBA');draw=ImageDraw.Draw(overlay)
for x,y,w,h,*_ in m['solids']:draw.rectangle((x,y,x+w-1,y+h-1),outline=(255,40,40),width=1)
draw.line([tuple(p) for p in m['route_points']],fill=(0,255,255),width=2);overlay.convert('RGB').save(A/'layout.png')
import campaign_corridors as bridge
previous=bridge.FOLDERS.copy();bridge.FOLDERS={**previous,'9':'corrections/9-guidebook'}
bd,*_=bridge.read('9');bridge.FOLDERS=previous
m['bridge_validation']={'read_via_unmodified_root_bridge':True,'tile_count':bd['tiles'],'map_bytes':len(mapping)*2,'palette_bytes':32,'source_paths_resolve':all((A/s['path']).resolve().is_file() for s in m['sources']),'all_free_positions_connected':True,'no_activation_or_shared_writes':True}
code='/* PRIVATE revision3. Root/user review required before publishing. */\n'+bridge.array('streetTiles','u32',(A/'native/tiles.bin').read_bytes())+bridge.array('streetPalette','u16',(A/'native/palette.bin').read_bytes())+bridge.array('streetMap','u16',(A/'native/map.bin').read_bytes())
cam,fields=bridge.camera('streetCameraFocus',m);code+=cam+f'static const ArenaScene streetScene={{.tiles=streetTiles,.map=streetMap,.palette=streetPalette,.tileCount={len(tiles)},.rows=40,.cols=320,.cameraPlayerY=200,{fields}}};\n'+bridge.rects('streetSolids',m['solids'])+bridge.arena('CF_STREET','streetScene','streetSolids',m)+bridge.route('CF_ROUTE09','points09',m)
(A/'code.inc').write_text(code);(A/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
report={'phase':'9','revision':3,'status':m['status'],'critical_limits':m['art_limitations'],'memory':m['memory'],'geometry':m['geometry_validation'],'native_tile_provenance':m['revision3_tile_proof'],'bridge':m['bridge_validation'],'new_emulator_or_performance_test':False,'active_or_shared_files_edited':False}
(A/'review.json').write_text(json.dumps(report,indent=2)+'\n')
html=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Fase9 · revisão3 privada</title><style>body{background:#171b22;color:#eee;font:16px system-ui;margin:24px}p{max-width:1100px}a{color:#89d4ef}img{image-rendering:pixelated}.pan{overflow:auto;border:1px solid #555}.pan img{width:2560px;height:320px}li{margin:8px}</style><h1>Fase9 · revisão3 isolada</h1><p>Dois galpões largos com pontas/apoios completos e persiana contínua. Apenas tiles residentes do banco anterior:630/640, nenhum tile novo. Isso não equivale a aprovação visual.</p><p><a href="manifest.json">Manifesto</a> · <a href="review.json">Parecer e limites</a> · <a href="layout.png">Geometria e rota</a></p><h2>Panorama1x</h2><div class="pan"><img src="complete-native.png"></div><h2>Cinco câmeras normais</h2><p>Prévias compostas com ator/HUD existentes; não são capturas novas do emulador. Cada construção principal aparece inteira abaixo do HUD em uma destas vistas; o caminhão da baía pode cruzar a borda da câmera.</p><img src="camera-sheet.png"><h2>Limites para revisão independente</h2><ul>']+['<li>'+x+'</li>' for x in m['art_limitations']]+['</ul></html>']
(A/'review.html').write_text('\n'.join(html))
print(json.dumps({'tiles':len(tiles),'new_tiles':0,'geometry':m['geometry_validation'],'waypoints':len(way),'status':'pending visual review'},indent=2))
