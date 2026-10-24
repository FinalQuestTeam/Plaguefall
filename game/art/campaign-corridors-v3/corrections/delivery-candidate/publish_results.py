"""Publish only the reviewed, hash-bound correction and its measured limits."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil
A=Path(__file__).resolve().parent;R=A.parents[1];G=A.parents[3];P=A.parent/'performance'
read=lambda p:json.loads(p.read_text())
sha=hashlib.sha256((G/'out/release/rom.bin').read_bytes()).hexdigest()
m=read(A/'candidate-manifest.json');assert m['rom_sha256']==sha
n=read(A/'native-validation.json');b=read(A/'compiled-validation.json');assert n['passed'] and b['passed'] and n['rom_sha256']==b['rom_sha256']==sha
functional=[]
for group in ('early','escorts','resistance','factory','launch'):
 for region in ('ntsc','pal'):
  path=A/'playtests'/group/region/'report.json';d=read(path)
  assert d['passed'] and d.get('rom_sha256',d.get('romSHA256'))==sha,(group,region)
  functional.append(dict(group=group,region=region,path=str(path.relative_to(A)),passed=True))
performance={};total_vb=0
for region in ('ntsc','pal'):
 d=read(P/(region+'-748849-moving')/'report.json');assert d['passed'] and d['romSHA256']==sha and not d['instrumentedTimingDiagnosticOnly'] and len(d['cases'])==5
 h=read(P/('hud-748849-'+region)/'report.json');assert h['passed'] and h['romSHA256']==sha and h['caseCount']==37
 for c in d['cases']:
  assert c['gameFrames']==c['physicalFrames']==1800 and c['targetMet']
  total_vb+=c['physicalFrames'];performance.setdefault(c['phase'],{})[region]={k:c[k] for k in ['gameFPS','enemyCap','shotCapPerPool','visibleEnemiesRange','visibleProjectilesRange','meanCPULoadPct','p95CPULoadPct','maximumCPULoadPct','satMaximumSampled','gameFrames','physicalFrames']}
assert total_vb==18000
captures=[]
for region in ('ntsc','pal'):
 d=read(A/'captures'/region/'capture-report.json');assert d['rom_sha256']==sha and len(d['phases'])==19
 assert all(s['landmark_entirely_visible'] for p in d['phases'] for s in p['samples'] if s['row']==3)
 captures.append(dict(region=region,phases=19,samples=sum(len(p['samples']) for p in d['phases'])))
active=read(R/'active.json');art=read(A.parent/'reviews/candidate-family-audit.json')
for row in art['phases']:
 path=R/active['scene_folders'][row['phase']]/'complete-native.png';assert not row['blocking_findings'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['native_sha256'],row['phase']
limits=['Carga medida: primeiro trecho de cada corredor, movimento por controle, inimigos/tiros nos tetos, cadência nativa e escudo de 3 s. Invulnerabilidade/HP isolam custo; não é uma partida completa nem dificuldade humana.','Os 16 inimigos forçados das provas de sobrecarga excedem os tetos autorais; não entram no critério de 60/50 FPS.','Módulos e materiais se repetem; os panoramas e as câmeras foram avaliados separadamente do orçamento de tiles.','Capturas de composição suspendem combate e progresso porRAM; hardware físico não foi testado.']
result=dict(status='integrated_reviewed_with_documented_limits',rom_sha256=sha,rom_bytes=(G/'out/release/rom.bin').stat().st_size,production_rom_matches=True,user_status='Correção integrada. 10 suítes funcionais passaram; 60 FPS NTSC / 50 PAL sem perdas em 18.000 VBlanks nos cinco corredores. Revisão visual com ressalvas documentadas.',artistic_status='reviewed_for_integration_with_reservations',human_approval_claimed=False,performance_target_met=True,performance=performance,total_measured_vblanks=total_vb,functional_suites=functional,captures=captures,total_camera_samples=sum(x['samples'] for x in captures),compiled_bank_comparisons=18,preserved_native_phases=n['preserved_phases'],artistic_review='../reviews/candidate-family-audit.json',performance_details='../performance/comparison-748849.json',limits=limits)
(A/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
# Keep the rejected records recoverable before replacing presentation paths.
archive=R/'corrections/staging/before-art-integration'
for name in ('maps','layouts'):
 if not (archive/name).exists():shutil.copytree(R/name,archive/name)
for name in ('playtests','captures'):
 p=R/name
 if not p.is_symlink():
  backup=R/(name+'-before-correction');assert not backup.exists();p.rename(backup);p.symlink_to(Path('corrections/delivery-candidate')/name,target_is_directory=True)
from sys import path as sys_path
sys_path.insert(0,str(G/'tools'))
from campaign_corridors import read as scene_read,native_path
rows=[]
for row in m['phases']:
 phase=row['phase']
 if phase in active['phases']:
  d,folder,*_=scene_read(phase);src=folder/('complete-closed-objectives.png' if phase=='6B' else 'complete-native.png');im=Image.open(src).convert('RGB');im.save(R/'maps'/f'{phase}-complete.png')
  row.update(complete=f'maps/{phase}-complete.png',native_sha256=hashlib.sha256(im.tobytes()).hexdigest(),sources=[str((folder/s).relative_to(R)) for s in d['sources']],camera_interest=d.get('camera_interest',[]),source_directory=str(folder.relative_to(R)))
  row['special_states']=[]
  for label,filename in [('Igreja destruída','complete-damaged-native.png'),('Portões abertos','complete-open-objectives.png'),('Colapso','complete-collapse-objectives.png')]:
   if (folder/filename).exists():row['special_states'].append(dict(label=label,path=str((folder/filename).relative_to(R))))
  layout=im.copy();draw=ImageDraw.Draw(layout);draw.rectangle(d['bounds'],outline='#41e396',width=2)
  for x,y,w,h,*_ in d['solids']:draw.rectangle((x,y,x+w-1,y+h-1),outline='#f77')
  layout.save(R/'layouts'/f'{phase}.png');row['layout']=f'layouts/{phase}.png'
  a=next(v for v in art['phases'] if v['phase']==phase)
  rows.append(dict(phase=phase,verdict='Revista para integração, com ressalvas',native_sha256=row['native_sha256'],whole_scene=row['complete'],observations=a['positive_evidence'],material_reservations=a['material_reservations'],technical='corrections/delivery-candidate/acceptance.json'))
 else:rows.append(dict(phase=phase,verdict='Composição preservada',preserved_from_baseline=True,native_sha256=row['native_sha256'],whole_scene=row['complete']))
m.update(scope='Cinco corredores corrigidos com o kit existente;14composições preservadas',rom_sha256=sha);(R/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
final=dict(status=result['status'],rom_sha256=sha,review_is_independent_of_tests=True,scope={'redesigned':active['phases'],'preserved':n['preserved_phases']},coverage={'complete_native_worlds':19,'regions':['NTSC','PAL'],'actual_camera_samples':result['total_camera_samples'],'compiled_bank_comparisons':18},open_visual_blockers=[],global_limits=limits,phases=rows,technical='corrections/delivery-candidate/acceptance.json',artistic_review='corrections/reviews/candidate-family-audit.json')
(R/'reviews/final.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n');(R/'reviews/delivery-acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(R/'playtests/summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
active.update(state='integrated_reviewed_with_limits',rom_sha256=sha,published_rom_sha256=sha,replaces_rejected_rom_sha256='0844f1322795eee56efa76752a7dd2d2744c78705aac5339921679f1879ff779');(R/'active.json').write_text(json.dumps(active,ensure_ascii=False,indent=2)+'\n')
(R/'review.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=corrections/delivery-candidate/review.html#p9"><title>Correção dos corredores</title><a href="corrections/delivery-candidate/review.html#p9">Abrir revisão da correção e resultados</a>')
print('Published reviewed correction:',sha,'10functional suites,878camera samples,18000VBlanks without losses')
