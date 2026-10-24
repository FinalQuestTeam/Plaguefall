"""Read-only checks of the exact five shipped scenes and campaign invariants.

This produces technical evidence. It intentionally gives no aesthetic verdict.
"""
from pathlib import Path
from collections import deque
from PIL import Image
import json,sys,struct,hashlib
A=Path(__file__).resolve().parent;G=A.parents[1];sys.path.insert(0,str(G/'tools'))
from campaign_corridors import read,active,native_path
from campaign_geometry import free
result={'purpose':'native reconstruction, geometry, memory and unchanged-scene evidence; not visual approval','phases':{}}
import subprocess
subprocess.run([sys.executable,str(A/'verify_compiled.py')],check=True)
compiled=json.loads((A/'reviews/compiled-validation.json').read_text())
assert compiled['passed'] and compiled['rom_sha256']==hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
result['compiled_bank_comparisons']=compiled['passed_comparisons']
for phase in ('3','6A','6B','9','12'):
    assert active(phase),phase
    d,p,tiles,mapping,palette=read(phase);w,h=d['size'];cols=w//8
    colors=[tuple(((v>>s)&7)*255//7 for s in (1,5,9)) for v in struct.unpack('>16H',palette)]
    out=Image.new('RGB',(w,h))
    for i,attr in enumerate(struct.unpack('>'+str(len(mapping)//2)+'H',mapping)):
        raw=tiles[(attr&2047)*32:(attr&2047)*32+32]
        patch=Image.new('RGB',(8,8));patch.putdata([colors[v] for b in raw for v in (b>>4,b&15)])
        if attr&0x800:patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if attr&0x1000:patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        out.paste(patch,(i%cols*8,i//cols*8))
    expected=Image.open(native_path(p)).convert('RGB')
    assert out.tobytes()==expected.tobytes(),(phase,'binary reconstruction differs')
    record={'pixel_exact_native_reconstruction':True,'size':d['size'],'geometry':d['geometry_validation'],'memory':d['memory'],'tile_sha256':d['nativeTileSHA256']}
    if phase=='6B':
        def reachable(extra):
            q=deque([tuple(d['start'])]);seen=set(q)
            while q:
                x,y=q.popleft()
                for pt in ((x+8,y),(x-8,y),(x,y+8),(x,y-8)):
                    if pt not in seen and free(d,*pt,extra=extra):seen.add(pt);q.append(pt)
            return (d['points'][-1][0]-8,d['points'][-1][1]-8) in seen
        gates=d['gates']
        assert not reachable(gates) and not reachable(gates[1:]) and reachable([]),'gate bypass or blocked opening'
        record['gate_connectivity']={'both_closed':'blocked','first_open':'blocked','both_open':'connected'}
    result['phases'][phase]=record
baseline=json.loads((A/'baseline/manifest.json').read_text());current=json.loads((A/'manifest.json').read_text())
result['preserved_phases']=[]
for old in baseline['phases']:
    if old['phase'] in result['phases']:continue
    new=next(d for d in current['phases'] if d['phase']==old['phase'])
    assert new['native_sha256']==old['native_sha256'],old['phase']
    result['preserved_phases'].append(old['phase'])
assert len(result['preserved_phases'])==14
result['rom_sha256']=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest();result['passed']=True
(A/'reviews/native-validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('PASS5 exact native scenes, closed/open gate connectivity,14 unchanged compositions; visual judgment remains separate')
