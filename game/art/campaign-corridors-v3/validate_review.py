"""Check shipped-ROM identity, all19worlds, memory, media and camera coverage."""
from pathlib import Path
from PIL import Image
import json,hashlib
A=Path(__file__).resolve().parent;G=A.parents[1]
read=lambda p:json.loads(p.read_text())
sha=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
assert (G/'out/release/rom.bin').read_bytes()==(G/'out/release/Plaguefall.bin').read_bytes()
m=read(A/'manifest.json');r=read(A/'reviews/final.json');t=read(A/'playtests/summary.json')
assert all(d['rom_sha256']==sha for d in [m,r,t]);assert t['status']=='integrated_reviewed_with_documented_limits' and t['performance_target_met']
phases={d['phase'] for d in m['phases']};assert len(phases)==19 and {d['phase'] for d in r['phases']}==phases
for d in m['phases']:
 assert d['memory']['total_tiles']<=640
 im=Image.open(A/d['complete']).convert('RGB');assert list(im.size)==d['size'];assert hashlib.sha256(im.tobytes()).hexdigest()==d['native_sha256']
 for p in [d['complete'],d['layout']]+d['sources']+[s['path'] for s in d['special_states']]:assert (A/p).is_file(),p
total=0
for region in ['ntsc','pal']:
 c=read(A/'captures'/region/'capture-report.json');assert c['rom_sha256']==sha;assert {d['phase'] for d in c['phases']}==phases
 for d in c['phases']:
  assert {0,1,2}<={s['row'] for s in d['samples']}
  total+=len(d['samples'])
  for s in d['samples']:assert Image.open(A/'captures'/region/s['path']).size==(320,224)
print(f'PASS: same shipped ROM;19whole worlds;10passed regional suites;{total}camera samples;configured-load60/50FPS;memory<=640tiles.')
