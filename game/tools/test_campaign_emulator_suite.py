"""Run the five campaign groups in NTSC/PAL against the built release ROM."""
from pathlib import Path
import subprocess,concurrent.futures,json
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--movie',action='store_true');parser.add_argument('--build-dir',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--groups',default='early,escorts,resistance,factory,launch');parser.add_argument('--regions',default='ntsc,pal');args=parser.parse_args()
root=Path(__file__).resolve().parents[2];out=args.output or root/'game/art/campaign-pattern-v2/playtests'
scripts={'early':'game/art/campaign-early-v1/test_emulator.py','escorts':'game/tools/test_campaign_escorts_emulator.py','resistance':'game/tools/test_campaign_resistance_emulator.py','factory':'game/tools/test_campaign_factory_emulator.py','launch':'game/tools/test_campaign_launch_emulator.py'}
def run(job):
 group,region=job;dest=out/group/region;dest.mkdir(parents=True,exist_ok=True)
 cmd=['arch','-x86_64','/usr/bin/python3',scripts[group],'--build-dir',str(args.build_dir or root/'game/out/release'),'--output',str(dest)]
 if region=='pal':cmd+=['--pal']
 if args.movie and region=='ntsc':cmd+=['--movie']
 if group=='early':cmd+=['--matches','1']
 with (dest/'execution.log').open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
 report_path=dest/'report.json'
 report_passed=report_path.exists() and json.loads(report_path.read_text()).get('passed') is True
 exit_code=r.returncode or (0 if report_passed else 1)
 print(group,region,exit_code,flush=True);return dict(group=group,region=region,exit_code=exit_code,process_exit_code=r.returncode,report_passed=report_passed)
selected=[(g,r) for g in args.groups.split(',') for r in args.regions.split(',')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(run,selected))
previous=out/'execution.json'
if previous.exists():results=[r for r in json.loads(previous.read_text()) if (r['group'],r['region']) not in selected]+results
(out/'execution.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(any(r['exit_code'] for r in results))
