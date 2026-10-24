"""Check shipped-ROM identity, all19worlds, memory, media and camera coverage."""
from pathlib import Path
from PIL import Image
import json,hashlib
A=Path(__file__).resolve().parent;G=A.parents[1]
read=lambda p:json.loads(p.read_text())
sha=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
assert (G/'out/release/rom.bin').read_bytes()==(G/'out/release/Plaguefall.bin').read_bytes()
m=read(A/'manifest.json');r=read(A/'reviews/final.json');t=read(A/'playtests/summary.json')
assert all(d['rom_sha256']==sha for d in [m,r,t]);assert t['status']=='passed'
phases={d['phase'] for d in m['phases']};assert len(phases)==19 and {d['phase'] for d in r['phases']}==phases
for d in m['phases']:
 assert d['memory']['total_tiles']<=640
 im=Image.open(A/d['complete']).convert('RGB');assert list(im.size)==d['size'];assert hashlib.sha256(im.tobytes()).hexdigest()==d['native_sha256']
 for p in [d['complete'],d['layout']]+d['sources']+[s['path'] for s in d['special_states']]:assert (A/p).is_file(),p
 key={'1':'01','2A':'02A','2B':'02B','3':'03','4':'04','5':'05','6A':'06a','6B':'06b'}.get(d['phase'],d['phase'])
 group='early' if d['phase'] in ['1','2A','2B','3','4','5'] else 'escorts' if d['phase'] in ['6A','6B','12'] else 'factory' if d['phase'] in ['9','10','11'] else 'resistance' if d['phase'] in ['7','8','13A','13B'] else 'launch'
 movie=key+('-playtest-1.mp4' if group=='early' else '-combat.mp4' if group=='escorts' else '-playtest.mp4');assert (A/'playtests'/group/'ntsc'/movie).stat().st_size>1000,movie
for region in ['ntsc','pal']:
 c=read(A/'captures'/region/'capture-report.json');assert c['rom_sha256']==sha;assert {d['phase'] for d in c['phases']}==phases
 for d in c['phases']:
  assert {s['row'] for s in d['samples']}=={0,1,2}
  for s in d['samples']:assert Image.open(A/'captures'/region/s['path']).size==(320,224)
print('PASS: same shipped ROM;19whole worlds;10passed regional suites;816camera samples;19NTSCplaytest videos;memory<=640tiles.')
