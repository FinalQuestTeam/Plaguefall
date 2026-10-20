"""Organize existing exports by EnemyDef identifiers without changing image bytes."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import unicodedata

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c)).lower()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    backup = ROOT / "validation" / "manifest-before-organization.json"
    if not backup.exists():
        shutil.copy2(manifest_path, backup)
    source = (GAME / "src/enemies/enemies.c").read_text()
    table = re.search(r"ENEMY_DEFS\[ENEMY_TYPES\]\s*=\s*\{(.*?)\};", source, re.S).group(1)
    identifiers = re.findall(r"&ENEMYDEF_(\w+)", table)
    header = (GAME / "src/enemies/enemies.h").read_text().split("#define ENEMY_TYPES")[0]
    constants = {int(value): name for name, value in re.findall(r"#define\s+(ENEMY_\w+)\s+(\d+)", header)}
    by_name = {normalized(enemy["name"]): enemy for enemy in manifest["enemies"]}
    assert len(identifiers) == len(by_name) == 15
    migration = []
    catalog = []

    def move(old, new):
        before, after = ROOT / old, ROOT / new
        if before == after:
            return
        if not before.exists():
            assert after.exists(), f"Missing source and destination: {before}"
            return
        original_hash = digest(before)
        after.parent.mkdir(parents=True, exist_ok=True)
        if after.exists():
            assert digest(after) == original_hash, f"Conflicting destination: {after}"
            before.replace(after)
        else:
            shutil.move(str(before), str(after))
        assert digest(after) == original_hash, f"File contents changed during move: {after}"
        migration.append({"before": old, "after": new, "sha256": original_hash})

    for index, identifier in enumerate(identifiers):
        definition = GAME / "src/enemies/defs" / f"{identifier}.c"
        definition_text = definition.read_text()
        name = re.search(r'\.name\s*=\s*"([^"]+)"', definition_text).group(1)
        enemy = by_name[normalized(name)]
        legacy = enemy.get("legacy_art_id", enemy["id"])
        folder = f"enemies/{identifier}"
        paths = {
            "sheet": f"{folder}/{identifier}.png",
            "turntable": f"{folder}/{identifier}_turntable.png",
            "original": f"{folder}/originals/{identifier}.png",
            "preview_turntable": f"{folder}/previews/{identifier}_turntable.gif",
            "preview_run": f"{folder}/previews/{identifier}_run.gif",
            "directions": {d: f"{folder}/directions/{identifier}_{d}.png" for d in manifest["directions"]},
        }
        move(f"gfx/{legacy}.png", paths["sheet"])
        move(f"gfx/turntables/{legacy}.png", paths["turntable"])
        move(f"originals/{legacy}.png", paths["original"])
        move(f"previews/{legacy}-turntable.gif", paths["preview_turntable"])
        move(f"previews/{legacy}-run.gif", paths["preview_run"])
        for direction, path in paths["directions"].items():
            move(f"gfx/directions/{legacy}_{direction}.png", path)
        old_optimized = ROOT / "validation" / f"{legacy}_opt.png"
        if old_optimized.exists():
            move(f"validation/{legacy}_opt.png", f"{folder}/validation/{identifier}_opt.png")
        old_backup = ROOT / "originals" / f"{legacy}-before-cleanup.png"
        if old_backup.exists():
            move(f"originals/{legacy}-before-cleanup.png", f"{folder}/originals/{identifier}_before_cleanup.png")
        enemy.update({"id": identifier, "name": name, "legacy_art_id": legacy,
                      "definition_file": f"../../src/enemies/defs/{identifier}.c",
                      "definition_symbol": f"ENEMYDEF_{identifier}",
                      "enemy_type_symbol": constants[index], "enemy_type_index": index,
                      "sprite_symbol": f"enemy8_{identifier}", "assets": paths})
        catalog.append(enemy)
        readme = (f"# {identifier} — {name}\n\n"
                  f"Definição: [`{identifier}.c`](../../../../src/enemies/defs/{identifier}.c).\n\n"
                  f"- Tipo: `{constants[index]}` = `{index}`.\n"
                  f"- Dados: `ENEMYDEF_{identifier}`.\n"
                  f"- Recurso SGDK: `enemy8_{identifier}`.\n"
                  f"- Folha completa: [`{identifier}.png`]({identifier}.png), 192×768.\n"
                  "- Oito folhas de 192×96 em `directions/`: N, NE, L, SE, S, SO, O, NO.\n"
                  f"- Oito vistas: [`{identifier}_turntable.png`]({identifier}_turntable.png).\n"
                  "- GIFs em `previews/`; fonte da arte em `originals/`.\n\n"
                  "Células 32×48, quatro frames de repouso e seis de corrida por direção.\n"
                  "Paleta, mapeamento de animações e recursos ficam na raiz do pacote.\n")
        (ROOT / folder / "README.md").write_text(readme)
    manifest["enemies"] = catalog
    manifest["status"] = "organized-by-project-identifiers-pending-resource-validation"
    old_suffixes = manifest.get("enemy_prompt_suffixes", {})
    manifest["enemy_prompt_suffixes"] = {
        e["id"]: old_suffixes.get(e["legacy_art_id"], old_suffixes.get(e["id"])) for e in catalog
    }
    for i in range(1, 4):
        move(f"previews/directions-{i}.png", f"previews/catalog_{i:02}.png")
    old_zip = ROOT / "darkspace-enemies-8directions-sgdk.zip"
    if old_zip.exists():
        move(old_zip.name, "validation/darkspace-enemies-before-organization.zip")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    export_path = ROOT / "validation/export.json"
    exports = json.loads(export_path.read_text())
    aliases = {e["legacy_art_id"]: e["id"] for e in catalog}
    for item in exports:
        item["id"] = aliases.get(item["id"], item["id"])
    export_path.write_text(json.dumps(exports, indent=2) + "\n")
    (ROOT / "catalog.json").write_text(json.dumps([
        {k: e[k] for k in ["id", "name", "enemy_type_index", "enemy_type_symbol", "definition_symbol", "sprite_symbol", "assets"]}
        for e in catalog], ensure_ascii=False, indent=2) + "\n")
    # Only remove empty directories left behind by the moves.
    for directory in ["gfx/directions", "gfx/turntables", "gfx", "originals"]:
        path = ROOT / directory
        if path.exists() and not any(path.iterdir()):
            path.rmdir()
    (ROOT / "validation/organization.json").write_text(json.dumps({
        "project_order": identifiers, "moved_files": migration,
        "image_bytes_preserved": True}, ensure_ascii=False, indent=2) + "\n")
    print(f"Organized {len(catalog)} enemies; verified SHA-256 for {len(migration)} moved files")


if __name__ == "__main__":
    main()
