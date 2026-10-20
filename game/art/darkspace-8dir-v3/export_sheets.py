"""Export generated eight-direction atlases; never synthesize rotated facings."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json
import shutil
from png_tools import extract_row, foot_center, indexed, LEVELS

ROOT = Path(__file__).resolve().parent
DIRECTIONS = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]


def row_boundaries(image):
    """Find inter-row gaps near the requested eight-row layout."""
    mask = image.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    data = mask.tobytes()
    width, height = image.size
    counts = [data[y * width:(y + 1) * width].count(255) for y in range(height)]
    edges = [0]
    step = height / 8
    for row in range(1, 8):
        target = row * step
        low, high = round(target - step * .22), round(target + step * .22)
        edge = min(range(low, high), key=lambda y: (counts[y], abs(y - target)))
        edges.append(edge)
    return edges + [height]


def export_enemy(enemy, colors):
    original = ROOT / enemy["assets"]["original"]
    if not original.exists():
        shutil.copy2(enemy["source"], original)
    source = Image.open(original).convert("RGBA")
    edges = row_boundaries(source)
    directions, metadata = [], []
    for direction in range(8):
        frames, bounds = extract_row(source, direction, row_count=8,
                                    row_bounds=(edges[direction], edges[direction + 1]))
        # Some AI atlases contain an extra idle pose despite the ten-cell prompt.
        # Keep four idle poses and the final six running poses; record omissions.
        count = len(frames)
        selected = list(range(4)) + list(range(count - 6, count))
        directions.append([frames[i] for i in selected])
        metadata.append({"direction": DIRECTIONS[direction], "source_pose_count": count,
                         "source_indices_selected": selected,
                         "source_indices_omitted": sorted(set(range(count)) - set(selected)),
                         "source_bounds": [bounds[i] for i in selected]})
    frames = [frame for poses in directions for frame in poses]
    # One scale across all eight views and every animation frame of this enemy.
    scale = min(42 / max(f.height for f in frames), 30 / max(f.width for f in frames))
    combined = Image.new("RGBA", (192, 768), (0, 0, 0, 0))
    contact = Image.new("RGBA", (256, 48), (0, 0, 0, 0))
    registrations = []
    for direction, poses in enumerate(directions):
        sheet = Image.new("RGBA", (192, 96), (0, 0, 0, 0))
        for i, frame in enumerate(poses):
            state, col = (0, i) if i < 4 else (1, i - 4)
            size = max(1, round(frame.width * scale)), max(1, round(frame.height * scale))
            small = frame.resize(size, Image.Resampling.NEAREST)
            small = small.crop(small.getchannel("A").getbbox())
            x = min(31 - small.width, max(1, round(16 - foot_center(small))))
            lift = [0, 0, 1, 3, 0, 1][col] if state else 0
            y = 47 - lift - small.height
            assert 0 <= x and x + small.width <= 32 and 0 <= y and y + small.height <= 48
            sheet.paste(small, (col * 32 + x, state * 48 + y))
            registrations.append({"direction": direction, "state": state, "frame": col,
                                  "feet_center_x": x + foot_center(small),
                                  "baseline_y": y + small.height - 1})
        combined.paste(sheet, (0, direction * 96))
        contact.paste(sheet.crop((0, 0, 32, 48)), (direction * 32, 0))
        native = indexed(sheet, colors)
        native.save(ROOT / enemy["assets"]["directions"][DIRECTIONS[direction]],
                    transparency=0, bits=4)
    indexed(combined, colors).save(ROOT / enemy["assets"]["sheet"], transparency=0, bits=4)
    indexed(contact, colors).save(ROOT / enemy["assets"]["turntable"], transparency=0, bits=4)
    return {"id": enemy["id"], "source_size": list(source.size), "source_rows": edges,
            "scale_shared_across_all_directions": scale, "directions": metadata,
            "registration": registrations,
            "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest()}


def previews(enemies):
    # Labels and backgrounds exist only in these presentation files.
    for start in range(0, len(enemies), 5):
        page = Image.new("RGB", (8 * 100 + 150, 5 * 170 + 35), "#171b22")
        draw = ImageDraw.Draw(page)
        for direction, label in enumerate(DIRECTIONS):
            draw.text((150 + direction * 100 + 42, 10), label, fill="#dedbc8")
        for row, enemy in enumerate(enemies[start:start + 5]):
            draw.text((10, 35 + row * 170 + 65), enemy["id"], fill="#dedbc8")
            draw.text((10, 35 + row * 170 + 85), enemy["name"], fill="#dedbc8")
            views = Image.open(ROOT / enemy["assets"]["turntable"]).convert("RGBA")
            views = views.resize((768, 144), Image.Resampling.NEAREST)
            # Paste each cell separately, preserving its 3x nearest-neighbour grid.
            for direction in range(8):
                sprite = views.crop((direction * 96, 0, (direction + 1) * 96, 144))
                page.paste(sprite, (150 + direction * 100 + 2, 35 + row * 170), sprite)
        page.save(ROOT / "previews" / f"catalog_{start // 5 + 1:02}.png")
    for enemy in enemies:
        sheet = Image.open(ROOT / enemy["assets"]["sheet"]).convert("RGBA")
        # Turntable plays all eight drawn idle facings in the game's order.
        turn = []
        for direction in range(8):
            frame = Image.new("RGB", (192, 288), "#171b22")
            sprite = sheet.crop((0, direction * 96, 32, direction * 96 + 48))
            sprite = sprite.resize((192, 288), Image.Resampling.NEAREST)
            frame.paste(sprite, (0, 0), sprite)
            turn.append(frame)
        turn[0].save(ROOT / enemy["assets"]["preview_turntable"], save_all=True,
                     append_images=turn[1:], duration=350, loop=0, disposal=2)
        # All eight running directions simultaneously, six animation frames.
        run = []
        for phase in range(6):
            frame = Image.new("RGB", (8 * 128, 192), "#171b22")
            for direction in range(8):
                y = direction * 96 + 48
                sprite = sheet.crop((phase * 32, y, (phase + 1) * 32, y + 48))
                sprite = sprite.resize((128, 192), Image.Resampling.NEAREST)
                frame.paste(sprite, (direction * 128, 0), sprite)
            run.append(frame)
        run[0].save(ROOT / enemy["assets"]["preview_run"], save_all=True,
                    append_images=run[1:], duration=100, loop=0, disposal=2)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for folder in ["enemies", "previews", "validation"]:
        (ROOT / folder).mkdir(exist_ok=True)
    for enemy in manifest["enemies"]:
        for key in ["sheet", "turntable", "original", "preview_turntable", "preview_run"]:
            (ROOT / enemy["assets"][key]).parent.mkdir(parents=True, exist_ok=True)
        for path in enemy["assets"]["directions"].values():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    colors = [(0, 0, 0)] + [tuple(bytes.fromhex(s[1:])) for s in manifest["palette"][1:]]
    assert len(colors) == 16 and all(v in LEVELS for c in colors for v in c)
    reports = []
    for enemy in manifest["enemies"]:
        reports.append(export_enemy(enemy, colors))
        print(f"Exported {enemy['id']}: 8 directions x 10 poses", flush=True)
    previews(manifest["enemies"])
    mapping = [{"dir": i, "label": label, "idle_animation": 2 * i, "run_animation": 2 * i + 1,
                "idle_frame_count": 4, "run_frame_count": 6} for i, label in enumerate(DIRECTIONS)]
    (ROOT / "directions.json").write_text(json.dumps(mapping, indent=2) + "\n")
    res = "// Game directions: 0=N,1=NE,2=L,3=SE,4=S,5=SO,6=O,7=NO.\n"
    res += "// Animation row = 2*direction + state (0=idle,1=run); 4/6 frames.\n"
    res += "\n".join(f'SPRITE {e["sprite_symbol"]} "{e["assets"]["sheet"]}" 4 6 FAST 6 NONE BALANCED FAST'
                      for e in manifest["enemies"]) + "\n"
    (ROOT / "enemies.res").write_text(res)
    for file in ["palette.json", "palette.gpl"]:
        shutil.copy2(ROOT.parent / "darkspace-iso60-v2" / file, ROOT / file)
    (ROOT / "validation" / "export.json").write_text(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()
