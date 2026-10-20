"""Validate delivery files, then compile the exact same files with SGDK rescomp."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    reference_palette = None
    results = []
    for enemy in manifest["enemies"]:
        path = ROOT / "gfx" / f"{enemy['id']}.png"
        image = Image.open(path)
        assert image.size == (192, 96), path
        assert image.mode == "P" and image.info.get("transparency") == 0, path
        assert path.read_bytes()[24] == 4, f"{path}: expected 4-bit indexed PNG"
        palette = image.getpalette()[:48]
        if reference_palette is None:
            reference_palette = palette
        assert palette == reference_palette, f"{path}: palette mismatch"
        pixels = list(image.getdata())
        assert set(pixels) <= set(range(16)), path
        assert set(image.convert("RGBA").getchannel("A").getdata()) <= {0, 255}, path
        animations, boxes, feet = [], [], []
        for row in range(2):
            frames, frame_boxes, frame_feet = [], [], []
            for col in range(6):
                cell = image.crop((col * 32, row * 48, (col + 1) * 32, (row + 1) * 48))
                box = cell.getbbox()
                if row == 0 and col >= 4:
                    assert box is None, f"{path}: idle padding is not empty"
                    continue
                assert box is not None, f"{path}: missing animation pose"
                assert box[0] >= 1 and box[2] <= 31 and box[1] >= 1 and box[3] <= 47, path
                frames.append(bytes(cell.getdata()))
                frame_boxes.append(box)
                frame_feet.append(box[3] - 1)
            assert len(set(frames)) == len(frames), f"{path}: duplicated poses"
            animations.append(frames)
            boxes.append(frame_boxes)
            feet.append(frame_feet)
        assert feet[0] == [46] * 4, f"{path}: idle baseline drift"
        # Report every adjacent run transition INCLUDING the loop seam. A pixel
        # metric records abrupt changes, but cannot certify anatomical motion.
        run = animations[1]
        differences = [sum(a != b for a, b in zip(run[i], run[(i + 1) % 6])) for i in range(6)]
        results.append({"id": enemy["id"], "size": list(image.size), "mode": image.mode,
                        "bit_depth": 4, "visible_colors_used": len(set(pixels) - {0}),
                        "transparency_index": 0, "frames": [4, 6], "idle_baseline": feet[0],
                        "frame_bounds": boxes, "run_pixel_differences_including_seam": differences,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    # AWT headless mode avoids the macOS GUI initialization used by ImageIO.
    jar = ROOT.parents[2] / "SGDK" / "bin" / "rescomp.jar"
    command = ["java", "-Djava.awt.headless=true", "-jar", str(jar),
               str(ROOT / "enemies.res"), str(ROOT / "validation" / "enemies.s")]
    compilation = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    log = compilation.stdout + compilation.stderr
    (ROOT / "validation" / "rescomp.log").write_text(log)
    assert compilation.returncode == 0, f"SGDK rescomp failed; read validation/rescomp.log"
    hardware = re.findall(r"Sprite frame '([^']+)' - (\d+) VDP sprites and (\d+) tiles", log)
    assert len(hardware) == 150, f"Expected 150 compiled poses, got {len(hardware)}"
    for enemy in manifest["enemies"]:
        for row, length in enumerate([4, 6]):
            actual = [h for h in hardware if h[0].startswith(f"enemy_{enemy['id']}_animation{row}_frame")]
            assert len(actual) == length, f"{enemy['id']}: compiled frame count differs"
    for path in (ROOT / "gfx").glob("*_opt.png"):
        shutil.move(str(path), ROOT / "validation" / path.name)
    report = {"technical_checks_passed": True, "enemy_count": 15, "total_frames": 150,
              "shared_palette": True, "sgdk_rescomp_returncode": compilation.returncode,
              "hardware_sprites_per_frame": [min(int(h[1]) for h in hardware), max(int(h[1]) for h in hardware)],
              "runtime_integration_tested": False,
              "artistic_limitations": ["AI source art was larger than native resolution; final files are nearest-neighbour reductions.",
                  "Technical validation does not prove anatomical consistency or flawless motion; review animation previews before production.",
                  "Camera elevation 60 degrees is an art target, not a measured 3D render calibration.",
                  "Existing game renderer rotates square character maps; these southeast-facing 32x48 elevated-view sheets need a separate renderer integration."],
              "camera_art_target": manifest.get("camera"),
              "sheets": results}
    (ROOT / "validation" / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["sheets", "artistic_limitations"]}, indent=2))


if __name__ == "__main__":
    main()
