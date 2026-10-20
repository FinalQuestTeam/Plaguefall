"""Package the organized native assets, using their project identifiers."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    files = {ROOT / name for name in [
        "README.md", "enemies.res", "directions.h", "directions.json",
        "palette.gpl", "palette.json", "manifest.json", "catalog.json",
        "validation/report.json", "validation/rescomp.log",
        "validation/export.json", "validation/organization.json",
    ]}
    files.update((ROOT / "previews").glob("*.png"))
    for enemy in manifest["enemies"]:
        files.add(ROOT / "enemies" / enemy["id"] / "README.md")
        for key in ["sheet", "turntable", "preview_turntable", "preview_run"]:
            files.add(ROOT / enemy["assets"][key])
        files.update(ROOT / path for path in enemy["assets"]["directions"].values())
    output = ROOT / "redrex-enemies-sgdk.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len([name for name in archive.namelist() if "/directions/" in name and name.endswith(".png")]) == 120
    print(f"Created {output.name}: {len(files)} files, {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
