"""Validate the fixed delivery independently of concurrent workspace builds."""
from pathlib import Path
import subprocess,hashlib,json,os
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
BUILD=ROOT/'integracao/rom';VALID=ROOT/'integracao/validation-frozen'
initial=hashlib.sha256((BUILD/'Plaguefall.bin').read_bytes()).hexdigest();jobs=[]
env=dict(os.environ,PLAGUEFALL_TILE_DEFS=str(BUILD/'tile-defs.h'))
for region in ['ntsc','pal']:
 arg=['--pal'] if region=='pal' else []
 suite=[(region,'test_radio_emulator.py',[]),('interface-'+region,'test_interface_emulator.py',[]),('map-'+region,'test_routemap_emulator.py',[]),('results-'+region,'test_results_emulator.py',[]),('objective-'+region,'test_campaign_stages_emulator.py',['--nodes','6','--matches','3'])]
 for name,tool,extra in suite:
  cmd=['arch','-x86_64','/usr/bin/python3','game/tools/'+tool,*arg,*extra,'--build-dir',str(BUILD),'--output',str(VALID/name)]
  log=open('/tmp/plaguefall-radio-frozen-'+name+'.log','w');jobs.append((name,subprocess.Popen(cmd,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT),log))
failed=[]
for name,p,log in jobs:
 code=p.wait();log.close()
 print(name+': '+Path('/tmp/plaguefall-radio-frozen-'+name+'.log').read_text().splitlines()[-1],flush=True)
 if code:failed.append(name)
assert not failed,failed
assert hashlib.sha256((BUILD/'Plaguefall.bin').read_bytes()).hexdigest()==initial
subprocess.run(['python3',str(ROOT/'publicar_revisao.py')],cwd=REPO,check=True)
