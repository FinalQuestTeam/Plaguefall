"""Read-only checks of private banks and manifests. Writes only verification reports here."""
from pathlib import Path
from PIL import Image
import hashlib, json, struct, subprocess, sys
import numpy as np
A=Path(__file__).resolve().parent; V=A.parents[1]; G=V.parents[1]
sys.path.insert(0,str(G/'tools'))
from campaign_geometry import validate
result=subprocess.run([sys.executable,str(A/'build_materials.py'),'--check'],capture_output=True,text=True)
assert result.returncode==0,result.stdout+result.stderr
for key in ['6A','6B']:
    dest=V/'corrections'/(key+'-guidebook')
    m=json.loads((dest/'manifest.json').read_text());old=json.loads((V/'sewers'/key/'manifest.json').read_text())
    geometry=['size','bounds','start','route_points','pauses','exit','solids','gates','valves','valve_approaches','gate_shot_approaches','camera_interest','camera_player_y']
    assert all(m[k]==old[k] for k in geometry)
    d=dict(m,points=m['route_points']);checks=validate(d)
    bank={n:(dest/'native'/f'{n}.bin').read_bytes() for n in ['tiles','map','palette']}
    assert len(bank['palette'])==32 and len(bank['map'])==3072*320//32
    attrs=struct.unpack('>'+str(len(bank['map'])//2)+'H',bank['map'])
    tiles=np.array([[v for b in bank['tiles'][i:i+32] for v in (b>>4,b&15)] for i in range(0,len(bank['tiles']),32)],dtype=np.uint8).reshape(-1,8,8)
    decoded=np.zeros((320,3072),dtype=np.uint8)
    for i,a in enumerate(attrs):
        assert a&2047<len(tiles)
        t=tiles[a&2047]
        if a&2048:t=t[:,::-1]
        if a&4096:t=t[::-1,:]
        y,x=divmod(i,384);decoded[y*8:y*8+8,x*8:x*8+8]=t
    exact=Image.open(dest/'complete-indexed.png');assert np.array_equal(decoded,np.array(exact))
    rgb=Image.open(dest/'complete-native.png').convert('RGB')
    assert exact.convert('RGB').tobytes()==rgb.tobytes()
    words=struct.unpack('>16H',bank['palette']);assert words[0]==0 and len(set(words))==16
    expected=[tuple(exact.getpalette()[i:i+3]) for i in range(0,48,3)]
    restored=[tuple(int(v/7*255) for v in ((w>>1)&7,(w>>5)&7,(w>>9)&7)) for w in words]
    assert expected==restored
    reserve=256 if key=='6B' else 0;assert len(tiles)+reserve<=640
    assert all((dest/s['path']).resolve()==(G/s['game_path']).resolve() and hashlib.sha256((dest/s['path']).read_bytes()).hexdigest()==s['sha256'] for s in m['sources'])
    report={'phase':key,'status':'PASS private data contract; visual approval not implied','builder_check':{'exit_code':result.returncode,'byte_exact_outputs':38,'writes':0,'command':'python3 '+str((A/'build_materials.py').relative_to(G.parent))+' --check'},'native_decode':{'exact_index_pixels':True,'exact_rgb_pixels':True,'palette_rgb333_exact':True,'palette_zero_black':True,'width':3072,'height':320,'tile_count':len(tiles),'objective_reserve':reserve,'total_tiles':len(tiles)+reserve,'h_v_flip_decode_verified':True},'geometry_equal_fields':geometry,'geometry':checks,'objective_sprite_files_unchanged':[s for s in m['sources'] if 'objective-sprites' in s['game_path']],'files':{n:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for n,data in bank.items()},'full_native_png_sha256':hashlib.sha256((dest/'complete-native.png').read_bytes()).hexdigest(),'active_scene_edited':False,'rom_built_or_executed':False,'limits':['No new gameplay/performance measurements: this only validates isolated existing geometry and exported banks.','Cameras use old measured positions with composed actors/HUD. Private-ROM review must confirm streaming, palette loading and visibility.']}
    (dest/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(key,len(tiles),'tiles +',reserve,'objective; exact decode/builder/geometry/sources PASS')
