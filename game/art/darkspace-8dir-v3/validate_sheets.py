"""Check all eight drawn facings and compile the final 16-animation resources."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
DIRECTIONS = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert manifest["directions"] == DIRECTIONS
    reference_palette = None
    results = []
    for enemy in manifest["enemies"]:
        path = ROOT / enemy["assets"]["sheet"]
        image = Image.open(path)
        assert image.size == (192, 768) and image.mode == "P", path
        assert path.read_bytes()[24] == 4 and image.info.get("transparency") == 0, path
        palette = image.getpalette()[:48]
        if reference_palette is None:
            reference_palette = palette
        assert palette == reference_palette, path
        assert set(image.tobytes()) <= set(range(16)), path
        assert set(image.convert("RGBA").getchannel("A").tobytes()) <= {0, 255}, path
        facings = []
        directions = []
        for direction, label in enumerate(DIRECTIONS):
            per_direction = Image.open(ROOT / enemy["assets"]["directions"][label])
            assert per_direction.size == (192, 96) and per_direction.mode == "P"
            assert per_direction.info.get("transparency") == 0
            assert per_direction.getpalette()[:48] == reference_palette
            assert per_direction.tobytes() == image.crop((0, direction * 96, 192, (direction + 1) * 96)).tobytes()
            sequences, baselines = [], []
            for state, length in enumerate([4, 6]):
                frames, feet = [], []
                for col in range(6):
                    y = direction * 96 + state * 48
                    cell = image.crop((col * 32, y, (col + 1) * 32, y + 48))
                    box = cell.getbbox()
                    if col >= length:
                        assert box is None, f"{enemy['id']} {label}: idle padding not empty"
                        continue
                    assert box and box[0] >= 1 and box[2] <= 31 and box[1] >= 1 and box[3] <= 47
                    frames.append(cell.tobytes())
                    feet.append(box[3] - 1)
                assert len(frames) == length
                if state == 0:
                    assert feet == [46] * 4, f"{enemy['id']} {label}: idle baseline drift"
                sequences.append(frames)
                baselines.append(feet)
            facings.append(sequences[0][0])
            run = sequences[1]
            transition = [sum(a != b for a, b in zip(run[i], run[(i + 1) % 6])) for i in range(6)]
            directions.append({"direction": direction, "label": label, "animations": [direction * 2, direction * 2 + 1],
                               "frames": [4, 6], "unique_idle_poses": len(set(sequences[0])),
                               "unique_run_poses": len(set(run)), "baselines": baselines,
                               "run_pixel_differences_including_seam": transition})
        assert len(set(facings)) == 8, f"{enemy['id']}: repeated directional artwork"
        assert facings[0] != facings[4], f"{enemy['id']}: front and back identical"
        results.append({"id": enemy["id"], "size": [192, 768], "directions": directions,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    expected = len(manifest["enemies"]) * 8
    assert len(list((ROOT / "enemies").glob("*/directions/*.png"))) == expected
    jar = ROOT.parents[2] / "SGDK" / "bin" / "rescomp.jar"
    compilation = subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(jar),
                                  str(ROOT / "enemies.res"), str(ROOT / "validation" / "enemies.s")],
                                 capture_output=True, text=True, cwd=ROOT)
    log = compilation.stdout + compilation.stderr
    (ROOT / "validation" / "rescomp.log").write_text(log)
    assert compilation.returncode == 0, "ResComp failed; read validation/rescomp.log"
    hardware = re.findall(r"Sprite frame '([^']+)' - (\d+) VDP sprites and (\d+) tiles", log)
    assembly = (ROOT / "validation" / "enemies.s").read_text()
    compiled = []
    for enemy in manifest["enemies"]:
        for animation in range(16):
            symbol = f"{enemy['sprite_symbol']}_animation{animation}"
            # SGDK packs u8 numFrame and u8 loop in the first big-endian word.
            match = re.search(r"^" + re.escape(symbol) + r":\s*\n\s*dc\.w\s+(\d+)", assembly, re.MULTILINE)
            assert match, f"Missing compiled animation {symbol}"
            count = int(match.group(1)) >> 8
            assert count == (4 if animation % 2 == 0 else 6), (symbol, count)
            compiled.append(count)
    for enemy in manifest["enemies"]:
        source = (ROOT / enemy["assets"]["sheet"]).with_name(f"{enemy['id']}_opt.png")
        if source.exists():
            target = source.parent / "validation" / source.name
            target.parent.mkdir(exist_ok=True)
            source.replace(target)
    report = {"technical_checks_passed": True, "enemy_count": len(manifest["enemies"]),
              "direction_count": 8, "per_direction_sheets": expected, "combined_sheets": len(results),
              "compiled_animations": len(compiled), "compiled_frame_references": sum(compiled),
              "shared_palette": True, "transparency_index": 0,
              "hardware_sprites_per_frame": [min(int(h[1]) for h in hardware), max(int(h[1]) for h in hardware)],
              "sgdk_rescomp_returncode": compilation.returncode, "runtime_integration_tested": False,
              "camera": manifest["camera"],
              "art_limitations": ["2D camera elevation is an art target, not a calibrated render.",
                  "Originals generated above native resolution; final files use nearest-neighbour reduction.",
                  "Subtle yaw/anatomy and weapon alignment can drift in running poses; visual cleanup remains necessary.",
                  "Pixel and compiler checks do not certify directional or anatomical accuracy of every drawn pose."],
              "sheets": results}
    (ROOT / "validation" / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["sheets", "art_limitations"]}, indent=2))


if __name__ == "__main__":
    main()
