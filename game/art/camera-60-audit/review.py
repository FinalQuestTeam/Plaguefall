"""Expose the manual camera verdict only for the exact sprites that were reviewed."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent

def camera_review(asset_id,sprite):
    audit=json.loads((ROOT/'audit.json').read_text())
    entry=next((e for e in audit['assets'] if e['id']==asset_id),None)
    same=entry is not None and entry['sha256']==hashlib.sha256(Path(sprite).read_bytes()).hexdigest()
    return {'required_elevation_degrees':60,'method':'manual visual review; no measured 3D camera',
            'status':entry['status'] if same else 'unreviewed_asset_changed',
            'approved':False,'measured_elevation_degrees':None,
            'audit':'../camera-60-audit/README.md','sha256_matches_review':same,
            'findings':entry['findings'] if same else []}

def write_archive_review(archive,package_root):
    """Keep downloaded packages explicit about the failed camera requirement."""
    readme=(Path(package_root)/'README.md').read_text()
    archive.writestr('README.md',readme.replace('../camera-60-audit/README.md','camera-60-audit/README.md'))
    for path in ROOT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            archive.write(path,Path('camera-60-audit')/path.relative_to(ROOT))
