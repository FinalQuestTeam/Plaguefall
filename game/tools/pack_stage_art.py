"""Stage art review exporter. Native generated modules, exact 8x8 deduplication.

Writes ONLY a stage's review folder. Does not register assets in the game/ROM.
"""
from pathlib import Path
from collections import deque
import argparse, hashlib, json, struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw

BUDGET=640
SCENE_BASE=785
FONT_BASE=1440
HUD_TILES=11
COLORS=[(0,0,0),(36,36,36),(36,36,73),(36,73,109),(73,109,146),
        (73,109,73),(109,109,36),(109,73,36),(146,109,73),
        (182,146,73),(219,182,109),(255,146,36),(182,73,36),
        (109,36,0),(219,219,182),(255,255,219)]
HARDWARE=np.array([[round(v*7/255)*34 for v in rgb] for rgb in COLORS],dtype=np.uint8)

def digest(data):return hashlib.sha256(data).hexdigest()
def overlap(a,b):
    x,y,w,h=a;xx,yy,ww,hh=b
    return x<xx+ww and x+w>xx and y<yy+hh and y+h>yy

def geometry(d):
    w,h=d['width'],d['height'];wx,wy,ww,wh=d['walkable']
    assert w%8==h%8==0 and 320<=w<=512 and 224<=h<=384
    assert wx>=16 and wy>=16 and wx+ww<=w-16 and wy+wh<=h-16
    for name in ('walkable',):assert all(n%8==0 for n in d[name]),name
    solids=[s.get('rect') if isinstance(s,dict) else s for s in d.get('solids',[])]
    hazards=[s['rect'] for s in d.get('hazards',[])]
    for rect in solids+hazards:
        x,y,rw,rh=rect
        assert all(v%8==0 for v in rect) and rw>0 and rh>0,rect
        assert 0<=x and 0<=y and x+rw<=w and y+rh<=h,rect
    # A 16x16 ground footprint, with eight-pixel steps, must be able to go
    # from the entry marker to the exit while staying on a completely dry lane.
    def free(p):
        x,y=p
        return wx<=x<=wx+ww-16 and wy<=y<=wy+wh-16 and not any(overlap((x,y,16,16),r) for r in solids+hazards)
    start=tuple(d['start']);goal=tuple(d['exit'])
    assert all(v%8==0 for v in start+goal),(start,goal)
    assert free(start) and free(goal),('entry/exit blocked',start,goal)
    seen={start};todo=deque([start])
    while todo:
        x,y=todo.popleft()
        for p in ((x-8,y),(x+8,y),(x,y-8),(x,y+8)):
            if p not in seen and free(p):seen.add(p);todo.append(p)
    assert goal in seen,'No connected dry route for a 16x16 actor'
    dry=sum(free((x,y)) for y in range(wy,wy+wh-15,8) for x in range(wx,wx+ww-15,8))
    assert len(seen)==dry,'Disconnected dry floor pockets'
    area={(x,y) for r in solids+hazards for y in range(max(wy,r[1]),min(wy+wh,r[1]+r[3]),8)
          for x in range(max(wx,r[0]),min(wx+ww,r[0]+r[2]),8)}
    occupied=len(area)*64
    return {'actor_footprint':[16,16],'path_step':8,'reachable_dry_positions':len(seen),
            'connected_dry_floor':True,'entry_exit_reachable':True,'walkable_pixels':ww*wh,
            'hazard_pixels':len({(x,y) for r in hazards for y in range(max(wy,r[1]),min(wy+wh,r[1]+r[3]),8)
                                for x in range(max(wx,r[0]),min(wx+ww,r[0]+r[2]),8)})*64,
            'dry_area_fraction':round(1-occupied/(ww*wh),4)}

def export(stage,check=False):
    stage=Path(stage).resolve();d=json.loads((stage/'design.json').read_text());w,h=d['width'],d['height']
    geom=geometry(d);source_path=stage/d['source'];source=Image.open(source_path).convert('RGB')
    # Exactly one native downsample. Every later operation is an 8px module
    # copy/repetition; no coarse intermediate, blur, quantization of tile IDs,
    # medoid replacements or procedural painting.
    source=source.resize((w,h),Image.Resampling.LANCZOS)
    rgb=np.asarray(source,dtype=np.int32)
    selected=d.get('palette',COLORS)
    assert len(selected)==16 and all(len(c)==3 and all(0<=v<=255 for v in c) for c in selected)
    hardware=np.array([[round(v*7/255)*34 for v in rgb] for rgb in selected],dtype=np.uint8)
    colors=hardware.astype(np.int32)
    index=((rgb[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3).argmin(axis=2).astype(np.uint8)
    canvas=np.zeros((h,w),dtype=np.uint8);covered=np.zeros((h,w),dtype=bool);catalog=[];module_indexes=[]
    extra_sources={};index_cache={}
    assert d.get('modules'),'design.json requires an ordered modules list'
    for m in d['modules']:
        sx,sy,sw,sh=m['source'];x,y,dw,dh=m['dest']
        module_index=index
        if m.get('source_image'):
            key=(m['source_image'],tuple(m['source_size']))
            if key not in index_cache:
                path=stage/m['source_image'];size=tuple(m['source_size'])
                external=np.asarray(Image.open(path).convert('RGB').resize(size,Image.Resampling.LANCZOS),dtype=np.int32)
                index_cache[key]=((external[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3).argmin(axis=2).astype(np.uint8)
                extra_sources[m['source_image']]=digest(path.read_bytes())
            module_index=index_cache[key]
        mh,mw=module_index.shape
        assert all(n%8==0 for n in m['source']+m['dest']),m['name']
        assert sw>0 and sh>0 and dw>0 and dh>0,m['name']
        assert 0<=sx<=mw-sw and 0<=sy<=mh-sh and 0<=x<=w-dw and 0<=y<=h-dh,m['name']
        patch=module_index[sy:sy+sh,sx:sx+sw]
        if m.get('flip_x'):patch=np.fliplr(patch)
        if m.get('flip_y'):patch=np.flipud(patch)
        canvas[y:y+dh,x:x+dw]=np.tile(patch,((dh+sh-1)//sh,(dw+sw-1)//sw))[:dh,:dw]
        covered[y:y+dh,x:x+dw]=True
        catalog.append({**m,'source_index_sha256':digest(patch.tobytes())})
        module_indexes.append(patch)
    assert covered.all(),'Some map pixels have no module'
    rows,cols=h//8,w//8
    cells=canvas.reshape(rows,8,cols,8).transpose(0,2,1,3).reshape(-1,64)
    tiles,inverse=np.unique(cells,axis=0,return_inverse=True);tilemap=inverse.reshape(rows,cols)
    binary=bytes((int(t[i])<<4)|int(t[i+1]) for t in tiles for i in range(0,64,2))
    words=[sum(round(v*7/255)<<(1+4*c) for c,v in enumerate(rgb)) for rgb in selected]
    assert len(set(words))==16,'Palette slots must be sixteen distinct hardware colors'
    decoded=tiles[tilemap].reshape(rows,cols,8,8).transpose(0,2,1,3).reshape(h,w)
    assert np.array_equal(decoded,canvas)
    # A padded 64x48 map can be fed to the phase1 ring in an isolated preview
    # build; compact map.bin retains the real dimensions for later integration.
    padded=np.zeros((48,64),dtype='>u2');padded[:rows,:cols]=tilemap
    files={'tiles.bin':binary,'map.bin':tilemap.astype('>u2').tobytes(),
           'map-vdp.bin':padded.tobytes(),'palette.bin':struct.pack('>16H',*words)}
    for m in catalog:
        x,y,dw,dh=m['dest'];m['tile_ids']=sorted(set(int(v) for v in tilemap[y//8:(y+dh)//8,x//8:(x+dw)//8].flat))
    ts=ET.Element('tileset',version='1.10',name=d['id'],tilewidth='8',tileheight='8',tilecount=str(len(tiles)),columns='16')
    ET.SubElement(ts,'image',source='tileset.png',width='128',height=str(((len(tiles)+15)//16)*8))
    tm=ET.Element('map',version='1.10',orientation='orthogonal',renderorder='right-down',width=str(cols),height=str(rows),tilewidth='8',tileheight='8',infinite='0')
    ET.SubElement(tm,'tileset',firstgid='1',source='tileset.tsx')
    layer=ET.SubElement(tm,'layer',id='1',name='Cenario',width=str(cols),height=str(rows))
    ET.SubElement(layer,'data',encoding='csv').text='\n'+',\n'.join(','.join(str(int(v)+1) for v in row) for row in tilemap)+'\n'
    ident=1
    for group_name,objects in [('Area caminhavel',[{'name':'Piso livre','rect':d['walkable']}]),
                               ('Solidos',d.get('solids',[])),('Perigos',d.get('hazards',[])),('Historia',d['story_elements'])]:
        group=ET.SubElement(tm,'objectgroup',name=group_name,visible='0')
        for obj in objects:
            if not isinstance(obj,dict):obj={'rect':obj}
            x,y,rw,rh=obj['rect'];ident+=1
            item=ET.SubElement(group,'object',id=str(ident),name=obj.get('name',obj.get('kind',group_name)),x=str(x),y=str(y),width=str(rw),height=str(rh))
            if obj.get('meaning'):
                props=ET.SubElement(item,'properties');ET.SubElement(props,'property',name='narrativa',value=obj['meaning'])
    editor={'tileset.tsx':ET.tostring(ts,encoding='utf-8',xml_declaration=True),
            'stage.tmx':ET.tostring(tm,encoding='utf-8',xml_declaration=True)}
    report={'id':d['id'],'title':d['title'],'status':'awaiting-art-approval','integrated':False,
            'world':[w,h],'camera_degrees':60,'tiles':len(tiles),'tile_bytes':len(binary),'palette_colors':16,
            'tilemap_bytes':rows*cols*2,'padded_vdp_map_bytes':6144,'tile_budget':BUDGET,
            'vram_scene_base':SCENE_BASE,'vram_end_with_hud':SCENE_BASE+len(tiles)+HUD_TILES,
            'font_vram_base':FONT_BASE,'within_vram_budget':len(tiles)<=BUDGET,
            'native_pixel_scale':1,'lossy_tile_replacements':0,'source_sha256':digest(source_path.read_bytes()),
            'design_sha256':digest((stage/'design.json').read_bytes()),'module_source_sha256':extra_sources,
            'export_sha256':{n:digest(b) for n,b in files.items()},
            'geometry':geom,'emulator_performance_measured':False}
    atlas=np.zeros((((len(tiles)+15)//16)*8,128),dtype=np.uint8)
    for i,t in enumerate(tiles):atlas[i//16*8:(i//16+1)*8,i%16*8:(i%16+1)*8]=t.reshape(8,8)
    if check:
        for n,b in files.items():assert (stage/'hardware'/n).read_bytes()==b,n
        for n,b in editor.items():assert (stage/n).read_bytes()==b,n
        assert np.array_equal(np.asarray(Image.open(stage/'map-native.png')),hardware[canvas])
        assert np.array_equal(np.asarray(Image.open(stage/'tileset.png')),hardware[atlas])
        assert json.loads((stage/'modules.json').read_text())==catalog
        old=json.loads((stage/'export.json').read_text());assert old['export_sha256']==report['export_sha256']
        for key in ('source_sha256','design_sha256','geometry','tiles','tile_bytes'):assert old[key]==report[key],key
        assert old.get('module_source_sha256',{})==extra_sources
    else:
        (stage/'hardware').mkdir(exist_ok=True)
        for n,b in files.items():(stage/'hardware'/n).write_bytes(b)
        for n,b in editor.items():(stage/n).write_bytes(b)
        Image.fromarray(hardware[canvas]).save(stage/'map-native.png')
        Image.fromarray(hardware[atlas]).save(stage/'tileset.png')
        (stage/'modules.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
        sheet=Image.new('RGB',(512,((len(catalog)+3)//4)*128),(17,24,28));draw=ImageDraw.Draw(sheet)
        for i,m in enumerate(catalog):
            patch=Image.fromarray(hardware[module_indexes[i]])
            if patch.width>120 or patch.height>100:patch.thumbnail((120,100),Image.Resampling.NEAREST)
            xx=(i%4)*128;yy=(i//4)*128;sheet.paste(patch,(xx,yy+20));draw.text((xx+2,yy+2),str(i+1)+'. '+m['name'].encode('ascii','replace').decode()[:16],fill=(219,182,109))
        sheet.save(stage/'modules.png')
        (stage/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('id','world','tiles','tile_bytes','within_vram_budget','geometry')},ensure_ascii=False))
    assert len(tiles)<=BUDGET, f'{len(tiles)} tiles exceed {BUDGET}: reuse generated architectural modules; never approximate tile contents'
    assert SCENE_BASE+len(tiles)+HUD_TILES<=FONT_BASE
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();export(args.stage,args.check)
