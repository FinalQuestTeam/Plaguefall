"""Bundle the native assets, exact prompts, source art and verification reports."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parent

def main():
    dest=ROOT/'redrex-parceira-iso60-v1-sgdk.zip'
    selected=[ROOT/name for name in ['README.md','catalog.json','palette.json','palette.gpl','parceira.res','export_sprites.py','validate_sprites.py','package_assets.py']]
    for folder in ['parceira','previews','originals','prompts','runtime','validation']:
        selected.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix not in ('.s','.pyc') and '__pycache__' not in p.parts and not p.name.endswith('_opt.png'))
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(set(selected)):archive.write(file,file.relative_to(ROOT))
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None
        for required in ['parceira/parceira.png','parceira/parceira-compacta.png','runtime/frames.bin','palette.json','validation/report.json']:
            assert archive.read(required)==(ROOT/required).read_bytes()
    print(dest,len(selected),'files',dest.stat().st_size,'bytes')
if __name__=='__main__':main()
