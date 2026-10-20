"""Associate manual visual review with exact final PNG hashes, not a 3D measurement."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent

def camera_review(asset_id,sprite):
    audit_path=ROOT/'audit.json'
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'assets':[]}
    entry=next((e for e in audit['assets'] if e['id']==asset_id),None)
    same=entry is not None and entry['sha256']==hashlib.sha256(Path(sprite).read_bytes()).hexdigest()
    accepted=same and entry['status']=='visually_matches_60_degree_reference'
    return {'required_elevation_degrees':60,'method':'visual comparison against analytically projected orthographic reference',
            'status':entry['status'] if same else 'unreviewed_asset_changed',
            'approved':accepted,'measured_elevation_degrees':None,
            'limitation':'Exact numeric elevation cannot be certified from a stylized 2D raster alone.',
            'audit':'../camera-60-redraw-v2/README.md','sha256_matches_review':same,
            'findings':entry['findings'] if same else []}

def write_archive_review(archive,package_root):
    readme=(Path(package_root)/'README.md').read_text()
    archive.writestr('README.md',readme.replace('../camera-60-redraw-v2/README.md','camera-60-redraw-v2/README.md'))
    for path in ROOT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            archive.write(path,Path('camera-60-redraw-v2')/path.relative_to(ROOT))
