"""Summarize same-ROM evidence without treating bots as human difficulty QA."""
from pathlib import Path
import json,hashlib,subprocess
A=Path(__file__).resolve().parent;G=A.parents[1];P=A/'playtests'
read=lambda p:json.loads(p.read_text())
sha=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
execution=read(P/'execution.json');phases={};reports=[]
ids={'01':'1','02A':'2A','02B':'2B','03':'3','04':'4','05':'5'}
for group in ('early','escorts','factory','resistance','launch'):
 for region in ('ntsc','pal'):
  f=P/group/region/'report.json';d=read(f);digest=d.get('rom_sha256',d.get('romSHA256'));assert digest==sha,(group,region,'stale ROM')
  reports.append(dict(group=group,region=region,passed=d['passed'],path=str(f.relative_to(A))))
  if group=='early':
   for r in d['stages']:phases.setdefault(ids[r['phase']],{})[region]={'checks':r['checks'],'ordinary_matches':r['ordinary_matches'],'report':str(f.relative_to(A))}
  elif group=='escorts':
   for phase,key in [('6A','06a'),('6B','06b'),('12','12')]:phases.setdefault(phase,{})[region]={'checks':{k:v for k,v in d['checks'].items() if k.startswith(key+'-')},'report':str(f.relative_to(A))}
  else:
   for phase,r in d['nodes'].items():phases.setdefault(phase,{})[region]={**r,'report':str(f.relative_to(A))}
assert len(phases)==19,phases.keys()
configured=[];ordinary=[];extra_stress=[]
for ph,regions in phases.items():
 for region,d in regions.items():
  if ph in ('1','2A','2B','3','4','5'):
   c=d['checks'].get(next((k for k in d['checks'] if k.endswith('/load')),''),{}).get('details')
   if c:configured.append(dict(phase=ph,region=region,simulation_fps=c['fps'],cpu_mean=c['cpu_mean_pct'],cpu_p95=c['cpu_p95_pct'],enemies=c['peak_enemies'],shots_each=c['peak_player_shots']))
   ordinary.extend(dict(phase=ph,region=region,**x) for x in d.get('ordinary_matches',[]))
  elif ph in ('6A','6B','12'):
   for k,v in d['checks'].items():
    if k.endswith('-stress'):
     for x in v:extra_stress.append(dict(phase=ph,region=region,**x))
    if 'ordinary-' in k:ordinary.append(dict(phase=ph,region=region,**v))
  else:
   c=d.get('visible_maximum_stress')
   if c:configured.append(dict(phase=ph,region=region,simulation_fps=c['simulation_fps'],cpu_mean=c.get('cpu_mean_percent'),cpu_peak=c.get('cpu_peak_percent'),enemies=c.get('seeded_visible_enemies',c.get('seeded_enemies')),shots_each=c['seeded_player_shots']))
   if d.get('difficulty_sample'):ordinary.append(dict(phase=ph,region=region,**d['difficulty_sample']))
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
probes=sum(x.get('movement_face_probes',0) for x in walk(phases))
for x in walk(phases):
 if isinstance(x.get('probes'),list):probes+=len(x['probes'])
captures=[]
for region in ('ntsc','pal'):
 f=A/'captures'/region/'capture-report.json'
 if f.exists():
  c=read(f);assert c['rom_sha256']==sha
  captures.append(dict(region=region,phases=len(c['phases']),samples=sum(len(p['samples']) for p in c['phases'])))
summary=dict(status='passed' if all(x['exit_code']==0 for x in execution) and all(x['passed'] for x in reports) else 'needs-correction',rom_sha256=sha,rom_bytes=(G/'out/release/rom.bin').stat().st_size,physical_hardware_tested=False,totals=dict(phases=len(phases),region_suites=len(reports),passed_region_suites=sum(r['passed'] for r in reports),movement_bounds_and_interaction_probes=probes,camera_samples=captures),method=dict(configured_load='Explicit RAM formations at each configured cap and shot pool; real production update/render.',extra_stress='Escorts also test8/16 enemies beyond the authored cap. These are overload probes.',ordinary='Controller-only bots after isolated node setup. Samples describe pressure and outcomes; they are not a human difficulty rating.',visual='Whole scenes and real cameras reviewed separately; a passing test is not visual approval.'),configured_load=configured,escort_stress=extra_stress,ordinary_samples=ordinary,reports=reports,phases=phases)
(P/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':summary['status'],'rom_sha256':sha,'totals':summary['totals']},indent=2))
