"""Export complete image-first3072px escort scenes and authored geometry.

Sources, module manifests, panoramas and separate visual reviews live in
art/campaign-pattern-v2/routes. Export is exact4bpp pattern deduplication.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,struct
GAME=Path(__file__).resolve().parents[1]
ROOT=GAME/'art/campaign-pattern-v2/routes'
SPEC=importlib.util.spec_from_file_location('campaign_pattern_route_art',ROOT/'build_art.py')
ART=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(ART)
LEGACY=GAME/'art/campaign-routes-v1'
CANON=GAME/'art/campaign-whole-scenes-v1/routes'
NAMES={'06a':'Pela passagem de baixo','06b':'O peso dos que ficaram','12':'A ultima travessia'}

def generate():
 from campaign_corridors import active,route_files
 if any(active(p) for p in ('6A','6B','12')):return route_files()
 from pack_campaign_ground_art import generate as objective_pack
 _,object_counts=objective_pack();objective_tiles=object_counts[3]+object_counts[4]
 files={};report={};source=['// Generated from whole scenes by tools/build_campaign_routes.py.','#include "levels/campaign_routes.h"','#include <campaign_routes.h>'];header=['#ifndef LEVEL_CAMPAIGN_ROUTES_H','#define LEVEL_CAMPAIGN_ROUTES_H','#include "levels/levels.h"'];res=[];decl=[]
 for key in ('06a','06b','12'):
  tiles,tilemap,palette,d=ART.render(key);width,height=d['size'];cols,rows=width//8,height//8;count=len(tiles);resident=objective_tiles if key=='06b' else 0
  assert count+resident<=640,(key,count,resident)
  d['memory'].update(scene_tiles=count,objective_tiles=resident,total_tiles=count+resident,graphics_bytes=(count+resident)*32,map_bytes=len(tilemap)*2,palette_bytes=32,free_tiles=640-count-resident,all_objective_frames_included=True)
  scene_dir=ART.OUT/key
  for kind,data in [('tiles',b''.join(tiles)),('map',struct.pack('>'+str(len(tilemap))+'H',*tilemap)),('palette',struct.pack('>16H',*palette))]:
   relative=f'campaign_routes/{key}/{kind}.bin';files[GAME/'res'/relative]=data;sym=f'campaign_route{key}_{kind}';res.append(f'BIN {sym} "{relative}" {4 if kind=="tiles" else 2}');decl.append(f'extern const u8 {sym}[{len(data)}];')
  for filename in ('complete-native.png','complete-closed-objectives.png','complete-collapse-objectives.png','complete-open-objectives.png','layout.png'):
   if (scene_dir/filename).exists():files[ROOT/'current'/key/filename]=(scene_dir/filename).read_bytes()
  files[scene_dir/'manifest.json']=(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode();files[ROOT/'current'/key/'manifest.json']=files[scene_dir/'manifest.json']
  files[CANON/f'{key}-native-complete.png']=(scene_dir/'complete-native.png').read_bytes();files[CANON/f'{key}-composed-complete.png']=files[CANON/f'{key}-native-complete.png'];files[CANON/f'{key}-modules.json']=(json.dumps(d['modules'],indent=2,ensure_ascii=False)+'\n').encode()
  files[CANON/'source'/f'{key}-complete.png']=(ART.SOURCE/f'{key}-whole.png').read_bytes();files[CANON/f'{key}-whole-scene.png']=files[CANON/'source'/f'{key}-complete.png'];files[LEGACY/f'mapa-{key}.png']=files[CANON/f'{key}-native-complete.png']
  for label in ('entrada','meio','saida'):files[LEGACY/f'{key}-{label}.png']=(scene_dir/f'camera-{label}-y24.png').read_bytes()
  source.append(f'static const ArenaScene scene{key}={{.tiles=(const u32 *)campaign_route{key}_tiles,.map=(const u16 *)campaign_route{key}_map,.palette=(const u16 *)campaign_route{key}_palette,.tileCount={count},.rows={rows},.cols={cols}}};')
  source.append(f'static const ArenaRect solids{key}[]={{'+','.join('{%d,%d,%d,%d,TRUE}'%tuple(r)for r in d['solids'])+'};')
  params=[width,height,*d['bounds'],*d['start']]
  source.append(f'const ArenaDef CAMPAIGN_ARENA{key.upper()}={{'+','.join(map(str,params))+f',solids{key},{len(d["solids"])},&scene{key}'+'};')
  source.append(f'static const RoutePoint points{key}[]={{'+','.join('{%d,%d,%d}'%(x,y,1 if i in d['pauses']else 0)for i,(x,y)in enumerate(d['points']))+'};')
  source.append(f'const RouteDef CAMPAIGN_ROUTE{key.upper()}={{points{key},{len(d["points"])},'+'{'+','.join(map(str,d['exit']))+',FALSE}};')
  header +=[f'extern const ArenaDef CAMPAIGN_ARENA{key.upper()};',f'extern const RouteDef CAMPAIGN_ROUTE{key.upper()};']
  length=sum(math.hypot(bx-ax,by-ay)for(ax,ay),(bx,by)in zip(d['points'],d['points'][1:]));left,top,right,bottom=d['bounds']
  report[key]={**d,'name':NAMES[key],'cap':3,'spawn':2 if key=='12' else 3,'width':width,'height':height,'walkable':[left,top,right-left+1,bottom-top+1],'tiles':count,'tileBudget':640-resident,'routeLengthPx':round(length,1),'unopposedMinimumSeconds':round(length/36+len(d['pauses']),1),'swept16pxSamples':d['geometry']['swept16pxSamples'],'nativeTileSHA256':hashlib.sha256(b''.join(tiles)).hexdigest(),'art':{'wholeImage':str((ART.SOURCE/f'{key}-whole.png').relative_to(GAME)),'wholeImageSHA256':hashlib.sha256((ART.SOURCE/f'{key}-whole.png').read_bytes()).hexdigest(),'nativeImage':str((scene_dir/'complete-native.png').relative_to(GAME)),'method':'Whole ImageGen scene first; intact structures and full cross-section materials; exact8x8 deduplication','sourceModules':d['modules'],'lossyTileReplacements':0,'visualReview':'art/campaign-pattern-v2/routes/review.json','status':'candidate_pending_integrated_emulator_review'}}
 gates=report['06b']['gates'];valves=report['06b']['valves']
 source.append('const ArenaRect CAMPAIGN_ROUTE06B_gates[2]={'+','.join('{%d,%d,%d,%d,TRUE}'%tuple(r)for r in gates)+'};');source.append('const RoutePoint CAMPAIGN_ROUTE06B_valves[2]={'+','.join('{%d,%d,0}'%(x,y)for x,y in valves)+'};')
 header +=['extern const ArenaRect CAMPAIGN_ROUTE06B_gates[2];','extern const RoutePoint CAMPAIGN_ROUTE06B_valves[2];','#endif']
 files[GAME/'src/levels/campaign_routes.c']=('\n'.join(source)+'\n').encode();files[GAME/'src/levels/campaign_routes.h']=('\n'.join(header)+'\n').encode();files[GAME/'res/campaign_routes.res']=('\n'.join(res)+'\n').encode();files[GAME/'res/campaign_routes.h']=('#include <genesis.h>\n\n#ifndef _RES_CAMPAIGN_ROUTES_H_\n#define _RES_CAMPAIGN_ROUTES_H_\n\n'+'\n'.join(decl)+'\n\n#endif // _RES_CAMPAIGN_ROUTES_H_\n').encode()
 data=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode()
 for path in (LEGACY/'export.json',CANON/'export.json',ROOT/'export.json'):files[path]=data
 return files,report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();files,report=generate()
 for path,data in files.items():
  if args.check:assert path.read_bytes()==data,path
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 print(json.dumps({key:{'size':[d['width'],d['height']],'tiles':d['tiles'],'resident':d['memory']['total_tiles'],'routeSamples':d['swept16pxSamples']}for key,d in report.items()}))
