"""Production bridge for the five authored corridor replacements.

Private artists export complete native scenes. This module validates their
binary contract, emits C without repacking pixels, and supplies legacy tooling
with the same geometry the game actually uses. Activation is explicit.
"""
from pathlib import Path
import hashlib, json, math, struct

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME / 'art/campaign-corridors-v3'
FOLDERS = {'3':'streets/3', '9':'streets/9', '6A':'sewers/6A', '6B':'sewers/6B', '12':'syndicate/12'}

def active(phase=None):
    p = ROOT / 'active.json'
    return p.exists() and (phase is None or phase in json.loads(p.read_text())['phases'])

def read(phase):
    configuration=json.loads((ROOT/'active.json').read_text())
    folder = (ROOT / configuration.get('scene_folders',{}).get(phase,FOLDERS[phase])).resolve()
    d = json.loads((folder/'manifest.json').read_text())
    d.update(phase=phase, width=d['size'][0], height=d['size'][1])
    d['points'] = d.get('route_points', d.get('points'))
    assert d['points'] and d['height']==320
    d['traversal_points'] = d.get('player_waypoints', [[x-8,y-8] for x,y in d['points']])
    d['pauses'] = d.get('pauses', [])
    d['sources']=[s['path'] if isinstance(s,dict) else s for s in d.get('sources',d.get('sourcePaths',[]))]
    l,t,r,b=d['bounds']; d['walkable']=[l,t,r-l+1,b-t+1]
    d['solids']=[list(v[:4])+[bool(v[4]) if len(v)>4 else True] for v in d['solids']]
    assert len(d['solids'])<256
    assert all(all(n%8==0 for n in v[:4]) for v in d['solids'])
    assert math.ceil(d['width']/256)*math.ceil(d['height']/8)<=512
    bank=folder/'native'
    tiles=(bank/'tiles.bin').read_bytes();mapping=(bank/'map.bin').read_bytes();palette=(bank/'palette.bin').read_bytes()
    assert len(tiles)%32==0 and len(mapping)==d['width']//8*d['height']//8*2 and len(palette)==32
    streamed=bool(d.get('streamed_tiles'))
    source_count=len(tiles)//32
    if streamed:d['source_tiles']=source_count
    d['tiles']=d['streamed_tiles'].get('resident_budget',640) if streamed else source_count
    objective_tiles=d.get('objective_tiles',256 if phase=='6B' else 0)
    d['tileBudget']=640-objective_tiles
    assert d['tiles']<=d['tileBudget']
    attrs=struct.unpack('>'+str(len(mapping)//2)+'H',mapping)
    assert max(attrs if streamed else (a&2047 for a in attrs))<source_count
    if streamed:assert d['streamed_tiles']['maximum_visible_tiles']<=d['tiles']
    d['memory']=dict(d.get('memory',{}),scene_tiles=d['tiles'],background_tiles=d['tiles'],objective_tiles=objective_tiles,total_tiles=d['tiles']+objective_tiles,limit=640,map_bytes=len(mapping),graphics_bytes=len(tiles))
    if streamed:d['memory'].update(graphics_bytes=d['tiles']*32,rom_graphics_bytes=len(tiles),map_stored_in_rom=True)
    if phase=='3':
        damaged=(folder/'damaged-native/tiles.bin').read_bytes()
        if not streamed:assert len(damaged)//32<=640
        d['memory'].update(damaged_scene_tiles=640 if streamed else len(damaged)//32,damaged_source_tiles=len(damaged)//32,total_tiles=max(d['tiles'],640 if streamed else len(damaged)//32),states_resident_simultaneously=False)
    d['nativeTileSHA256']=hashlib.sha256(tiles).hexdigest()
    d['native_bank']=str(bank.relative_to(GAME))
    d['camera_player_y']=d.get('camera_player_y',200 if phase=='12' else 184)
    for focus in d.get('camera_interest',[]):
        if focus.get('preferred_feet') and not focus.get('position'):focus['position']=focus['preferred_feet']
        if focus.get('player_feet') and not focus.get('position'):focus['position']=focus['player_feet']
        if not focus.get('name'):focus['name']=focus.get('id','Marco arquitetônico').replace('-',' ')
    from campaign_geometry import validate
    d['geometry_validation']=validate(d)
    d['geometry']=dict(d.get('geometry',{}),swept16pxSamples=d['geometry_validation']['swept16pxSamples'])
    d['swept16pxSamples']=d['geometry']['swept16pxSamples']
    return d,folder,tiles,mapping,palette

def native_path(folder,damaged=False):
    choices=['complete-damaged-native.png','damaged-native/complete.png','damaged-native/map-native.png'] if damaged else ['complete-native.png','native/complete.png','native/map-native.png']
    return next(folder/p for p in choices if (folder/p).exists())

def array(name,kind,data):
    unit=4 if kind=='u32' else 2
    vals=struct.unpack('>'+str(len(data)//unit)+('I' if unit==4 else 'H'),data)
    lines=[','.join(('0x%08xUL'%v if unit==4 else str(v)) for v in vals[i:i+16])+',' for i in range(0,len(vals),16)]
    alignment=' __attribute__((aligned(32)))' if kind=='u32' and name in ('street_tiles','street_damaged_tiles','streetTiles') else ''
    return 'static const '+kind+' '+name+'[]'+alignment+'={\n'+'\n'.join(lines)+'\n};\n'

def rects(name,solids):
    return 'static const ArenaRect '+name+'[]={'+','.join('{'+','.join(map(str,v[:4]))+(','+'TRUE' if v[4] else ',FALSE')+'}' for v in solids)+'};\n'

def arena(name,scene,solids,d):
    return 'const ArenaDef '+name+'={'+','.join(map(str,[*d['size'],*d['bounds'],*d['start']]))+','+solids+','+str(len(d['solids']))+',&'+scene+'};\n'

def route(name,pointsname,d):
    return ('static const RoutePoint '+pointsname+'[]={'+','.join('{%d,%d,%d}'%(x,y,int(i in d['pauses'])) for i,(x,y) in enumerate(d['points']))+'};\n'
            +'const RouteDef '+name+'={'+pointsname+','+str(len(d['points']))+',{'+','.join(map(str,d['exit']))+',FALSE}};\n')

def camera(name,d):
    boxes=[x['bbox']+[False] for x in d.get('camera_interest',[]) if x.get('camera_focus',True) and x['bbox'][2]<=320 and x['bbox'][3]<=200]
    if not boxes:return '', '.cameraFocus=NULL,.cameraFocusCount=0'
    return rects(name,boxes),f'.cameraFocus={name},.cameraFocusCount={len(boxes)}'

def early_files():
    d,p,tiles,mapping,palette=read('3')
    damaged=p/'damaged-native'
    dt=(damaged/'tiles.bin').read_bytes();dm=(damaged/'map.bin').read_bytes()
    assert (damaged/'palette.bin').read_bytes()==palette
    streamed=bool(d.get('streamed_tiles'))
    assert (streamed or len(dt)//32<=640) and len(dm)==len(mapping)
    code=array('street_tiles','u32',tiles)+array('street_palette','u16',palette)+array('street_map','u16',mapping)+array('street_damaged_tiles','u32',dt)+array('street_damaged_map','u16',dm)
    if streamed:code+=f'#define STREET_STREAMED 1\nstatic const ArenaStream street_stream={{{len(tiles)//32}}};\nstatic const ArenaStream street_damaged_stream={{{len(dt)//32}}};\n'
    focus_code,focus_fields=camera('streetCameraFocus',d);code+=focus_code
    layout=rects('streetSolids',d['solids'])+arena('EARLY_ARENA03','streetScene','streetSolids',d)+route('EARLY_ROUTE03','streetPoints',d)
    files={GAME/'src/levels/campaign_early_street.inc':code.encode(),GAME/'src/levels/campaign_early_street_layout.inc':layout.encode()}
    c=GAME/'src/levels/campaign_early.c'
    import re
    text=c.read_text()
    start=text.index('static ArenaScene streetScene');end=text.index('};',start)+2
    block=('static ArenaScene streetScene={\n    .tiles=street_tiles,.map=street_map,.palette=street_palette,\n'
           f'    .tileCount={640 if streamed else "sizeof(street_tiles)/32"},.rows=40,.cols=320,.cameraPlayerY={d["camera_player_y"]},{focus_fields}'+(', .stream=&street_stream' if streamed else '')+(f',.cameraSouthStart={d["camera_south_start"]}' if d.get('camera_south_start') else '')+'\n'+'};')
    text=text[:start]+block+text[end:]
    files[c]=text.encode()
    for path,key in [(GAME/'art/campaign-pattern-v2/early/geometry.json','03'),(GAME/'art/campaign-early-v1/manifest.json','03')]:
        doc=json.loads(path.read_text());stages=doc.get('stages',doc)
        stages[key].update(d,damaged_tiles=len(dt)//32,source=str(p.relative_to(GAME)),native_image=str(native_path(p).relative_to(GAME)))
        files[path]=(json.dumps(doc,indent=2,ensure_ascii=False)+'\n').encode()
    return files

def factory_override(files):
    """Called after historical factory generation; keeps10/11 byte identical."""
    if not active('9'):return
    d,p,tiles,mapping,palette=read('9')
    code=array('streetTiles','u32',tiles)+array('streetPalette','u16',palette)+array('streetMap','u16',mapping)
    focus_code,focus_fields=camera('streetCameraFocus',d);code+=focus_code
    extras=''
    if d.get('streamed_tiles'):
        code+=f'static const ArenaStream streetStream={{{len(tiles)//32}}};\n'
        extras+=',.stream=&streetStream'
    if d.get('camera_south_start'):extras+=f',.cameraSouthStart={d["camera_south_start"]}'
    code+=f'static const ArenaScene streetScene={{.tiles=streetTiles,.map=streetMap,.palette=streetPalette,.tileCount={d["tiles"]},.rows=40,.cols={d["width"]//8},.cameraPlayerY={d.get("camera_player_y",184)},{focus_fields}{extras}}};\n'
    code+=rects('streetSolids',d['solids'])+arena('CF_STREET','streetScene','streetSolids',d)+route('CF_ROUTE09','points09',d)
    path=GAME/'src/levels/campaign_factory_scenes.c'
    text=files[path]
    text=text[:text.index('static const u32 streetTiles[]')]+code
    files[path]=text
    for target in (GAME/'art/campaign-pattern-v2/factory/geometry.json',GAME/'art/campaign-factory-v1/geometry.json'):
        doc=json.loads(files[target])
        doc.update(street_controller_waypoints=d['traversal_points'][1:-1],street_route=d['points'],street_exit=d['exit'],street_finish=d['traversal_points'][-1],street_solids=[v[:4] for v in d['solids']],street_size=d['size'],street_start=d['start'],street_min_y=d['bounds'][1],street_max_y=d['bounds'][3],street_baseline_y=d['start'][1],street_native_bank=d['native_bank'],street_camera_interest=d.get('camera_interest',[]))
        doc['street_reachable']=d['geometry_validation']['reachable_positions']
        files[target]=json.dumps(doc,indent=2)+'\n'
    from PIL import Image
    image=Image.open(p/'complete-native.png')
    files[GAME/'art/campaign-pattern-v2/factory/cycle-2/street-native.png']=image
    files[GAME/'art/campaign-pattern-v2/factory/cycle-2/9-complete.png']=image
    files[GAME/'art/campaign-factory-v1/street-map.png']=image
    path=GAME/'art/campaign-pattern-v2/factory/export.json';doc=json.loads(files[path]);doc['scenes']['street']={**d,**d['memory']};files[path]=json.dumps(doc,indent=2)+'\n'
    path=GAME/'art/campaign-pattern-v2/factory/review-manifest.json';doc=json.loads(files[path]);row=next(v for v in doc['phases'] if v['phase']=='9')
    row.update(size=d['size'],bounds=d['bounds'],start=d['start'],solids=d['solids'],memory=d['memory'],sources=[str((p/x).relative_to(GAME)) for x in d.get('sources',[])])
    files[path]=json.dumps(doc,indent=2)+'\n'

def render_route(key):
    phase={'06a':'6A','06b':'6B','12':'12'}[key]
    d,p,t,m,pal=read(phase)
    raw=[t[i:i+32] for i in range(0,len(t),32)]
    return raw,list(struct.unpack('>'+str(len(m)//2)+'H',m)),list(struct.unpack('>16H',pal)),d

def route_files():
    files={};report={};source=['// Exact native corridor export.','#include "levels/campaign_routes.h"','#include <campaign_routes.h>'];header=['#ifndef LEVEL_CAMPAIGN_ROUTES_H','#define LEVEL_CAMPAIGN_ROUTES_H','#include "levels/levels.h"'];res=[];decl=[]
    for phase,key in [('6A','06a'),('6B','06b'),('12','12')]:
        if active(phase):d,p,t,m,pal=read(phase)
        else:
            d=json.loads((GAME/'art/campaign-routes-v1/export.json').read_text())[key]
            bank=GAME/'res/campaign_routes'/key;p=(GAME/d['art']['nativeImage']).parent
            t=(bank/'tiles.bin').read_bytes();m=(bank/'map.bin').read_bytes();pal=(bank/'palette.bin').read_bytes()
            d['solids']=[list(r[:4])+[bool(r[4]) if len(r)>4 else True] for r in d['solids']]
            d['camera_player_y']=0
        for kind,data in [('tiles',t),('map',m),('palette',pal)]:
            relative=f'campaign_routes/{key}/{kind}.bin';files[GAME/'res'/relative]=data;sym=f'campaign_route{key}_{kind}';res.append(f'BIN {sym} "{relative}" {(32 if d.get("streamed_tiles") else 4) if kind=="tiles" else 2}');decl.append(f'extern const u8 {sym}[{len(data)}];')
        focus_code,focus_fields=camera('cameraFocus'+key,d);source.append(focus_code)
        extras=''
        if d.get('streamed_tiles'):
            source.append(f'static const ArenaStream stream{key}={{{d["source_tiles"]}}};')
            extras+=f',.stream=&stream{key}'
            if d.get('gates'):extras+=',.streamOverlay=TRUE'
        if d.get('camera_south_start'):extras+=f',.cameraSouthStart={d["camera_south_start"]}'
        source.append(f'static const ArenaScene scene{key}={{.tiles=(const u32 *)campaign_route{key}_tiles,.map=(const u16 *)campaign_route{key}_map,.palette=(const u16 *)campaign_route{key}_palette,.tileCount={d["tiles"]},.rows={d["height"]//8},.cols={d["width"]//8},.cameraPlayerY={d.get("camera_player_y",200 if phase=="12" else 184)},{focus_fields}{extras}}};')
        source.append(rects('solids'+key,d['solids']))
        source.append(arena('CAMPAIGN_ARENA'+key.upper(),'scene'+key,'solids'+key,d))
        source.append(route('CAMPAIGN_ROUTE'+key.upper(),'points'+key,d))
        header.extend([f'extern const ArenaDef CAMPAIGN_ARENA{key.upper()};',f'extern const RouteDef CAMPAIGN_ROUTE{key.upper()};'])
        length=sum(math.dist(a,b) for a,b in zip(d['points'],d['points'][1:]))
        d.update(routeLengthPx=round(length,1),unopposedMinimumSeconds=round(length/36+len(d['pauses']),1),cap=3,spawn=2 if phase=='12' else 3)
        d['art']={'nativeImage':str((p/'complete-native.png').relative_to(GAME)),'method':'Whole scene first; complete modules; exact native export','lossyTileReplacements':0}
        report[key]=d
        d['source_directory']=str(p.relative_to(GAME))
        files[GAME/'art/campaign-pattern-v2/routes/current'/key/'manifest.json']=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
        for name in ('complete-native.png','complete-closed-objectives.png','complete-collapse-objectives.png','complete-open-objectives.png','layout.png'):
            if (p/name).exists():files[GAME/'art/campaign-pattern-v2/routes/current'/key/name]=(p/name).read_bytes()
        native=native_path(p).read_bytes()
        files[GAME/'art/campaign-whole-scenes-v1/routes'/f'{key}-native-complete.png']=native
        files[GAME/'art/campaign-whole-scenes-v1/routes'/f'{key}-composed-complete.png']=(p/'complete-closed-objectives.png').read_bytes() if d.get('gates') else native
        files[GAME/'art/campaign-routes-v1'/f'mapa-{key}.png']=native
    assert report['06a']['gates']==report['06b']['gates'],'shared6A/6B gate footprints must agree'
    source.append('const ArenaRect CAMPAIGN_ROUTE06_gates[2]={'+','.join('{'+','.join(map(str,r[:4]))+',TRUE}' for r in report['06b']['gates'])+'};')
    source.append('const RoutePoint CAMPAIGN_ROUTE06B_valves[2]={'+','.join('{%d,%d,0}'%(x,y) for x,y in report['06b']['valves'])+'};')
    header.extend(['extern const ArenaRect CAMPAIGN_ROUTE06_gates[2];','extern const RoutePoint CAMPAIGN_ROUTE06B_valves[2];','#endif'])
    files[GAME/'src/levels/campaign_routes.c']=('\n'.join(source)+'\n').encode();files[GAME/'src/levels/campaign_routes.h']=('\n'.join(header)+'\n').encode()
    files[GAME/'res/campaign_routes.res']=('\n'.join(res)+'\n').encode();files[GAME/'res/campaign_routes.h']=('#include <genesis.h>\n\n#ifndef _RES_CAMPAIGN_ROUTES_H_\n#define _RES_CAMPAIGN_ROUTES_H_\n\n'+'\n'.join(decl)+'\n\n#endif // _RES_CAMPAIGN_ROUTES_H_\n').encode()
    data=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    for folder in ('campaign-routes-v1','campaign-whole-scenes-v1/routes','campaign-pattern-v2/routes'):
        files[GAME/'art'/folder/'export.json']=data
    return files,report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,data in early_files().items():
        if args.check:assert path.read_bytes()==data,path
        else:path.write_bytes(data)
    print('Production corridor3 arrays and geometry match native source')
