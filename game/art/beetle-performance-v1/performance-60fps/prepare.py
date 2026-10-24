"""Restore the captured compile inputs and optional experimental overlay."""
from pathlib import Path
import argparse,hashlib,json,shutil,tarfile,tempfile
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--variant',choices=['baseline','experimental','carga'],default='experimental');p.add_argument('--destination',type=Path);a=p.parse_args()
 manifest=json.loads((ROOT/'manifest.json').read_text());archive=ROOT/'baseline-source.tar.gz'
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['baseline_source_sha256']
 target=a.destination or Path(tempfile.mkdtemp(prefix='plaguefall-60-review-'))/a.variant
 target.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive) as tar:
  assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in tar.getmembers())
  tar.extractall(target)
 if a.variant in ('experimental','carga'):
  shutil.copytree(ROOT/'overlay',target,dirs_exist_ok=True)
  for item in manifest['changes']:
   assert hashlib.sha256((target/item['path']).read_bytes()).hexdigest()==item['after_sha256']
 if a.variant=='carga':
  child=json.loads((ROOT/'load-room/manifest.json').read_text())
  shutil.copytree(ROOT/'load-room/overlay',target,dirs_exist_ok=True)
  for item in child['changes']:
   assert hashlib.sha256((target/item['path']).read_bytes()).hexdigest()==item['after_sha256']
 print(json.dumps({'variant':a.variant,'path':str(target.resolve())}))
if __name__=='__main__':main()
