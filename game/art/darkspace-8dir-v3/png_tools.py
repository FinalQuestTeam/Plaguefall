"""Technical PNG export of generated artwork; no drawing or pose synthesis.

Copies the untouched image_gen originals, extracts their ten supplied poses,
registers feet, downsamples with nearest neighbour, and maps to a fixed palette.
Run with Python + Pillow from any working directory.
"""

from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json
import math
import shutil
from collections import deque

ROOT = Path(__file__).resolve().parent
LEVELS = [0, 36, 73, 109, 146, 182, 219, 255]


def spans(values):
    result = []
    start = None
    for x, value in enumerate(values + [False]):
        if value and start is None:
            start = x
        elif not value and start is not None:
            result.append([start, x])
            start = None
    return result


def extract_row(image, row, count=None, row_count=2, row_bounds=None):
    width, height = image.size
    y0, y1 = row_bounds or (round(row * height / row_count), round((row + 1) * height / row_count))
    strip = image.crop((0, y0, width, y1))
    alpha = strip.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    # Source poses can overlap in their horizontal projection (rifle vs. boot),
    # so split connected silhouettes in two dimensions instead of clipping cells.
    remaining = bytearray(alpha.tobytes())
    components = []
    for seed in range(len(remaining)):
        if not remaining[seed]:
            continue
        stack = [seed]
        remaining[seed] = 0
        pixels = []
        while stack:
            pos = stack.pop()
            pixels.append(pos)
            x, y = pos % width, pos // width
            for ny in range(max(0, y - 1), min(strip.height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    other = ny * width + nx
                    if remaining[other]:
                        remaining[other] = 0
                        stack.append(other)
        xs, ys = [p % width for p in pixels], [p // width for p in pixels]
        components.append({"pixels": pixels, "box": [min(xs), min(ys), max(xs) + 1, max(ys) + 1]})
    components.sort(key=lambda c: len(c["pixels"]), reverse=True)
    if count is None:
        largest = len(components[0]["pixels"])
        count = sum(len(c["pixels"]) >= largest * .35 for c in components)
        if not 10 <= count <= 12:
            raise ValueError(f"Row {row}: expected 10-12 source poses, detected {count}")
    primary = sorted(components[:count], key=lambda c: c["box"][0])
    if len(primary) != count or min(len(c["pixels"]) for c in primary) < 1000:
        raise ValueError(f"Row {row}: cannot identify {count} distinct complete source poses")
    groups = [[c] for c in primary]
    centers = [((c["box"][0] + c["box"][2]) / 2, (c["box"][1] + c["box"][3]) / 2) for c in primary]
    # Ignore tiny disconnected alpha flecks (or fragments from an adjacent row),
    # while retaining detached equipment/boots large enough to be meaningful.
    minimum_fragment = max(16, round(max(len(c["pixels"]) for c in primary) * .03))
    for component in components[count:]:
        if len(component["pixels"]) < minimum_fragment:
            continue
        box = component["box"]
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        closest = min(range(count), key=lambda i: (cx - centers[i][0]) ** 2 + (cy - centers[i][1]) ** 2)
        # A thin detached strip entirely below the main silhouette is a row
        # fragment/presentation mark, rather than a detached boot or equipment.
        if box[1] >= primary[closest]["box"][3] and box[2] - box[0] >= 2.5 * (box[3] - box[1]):
            continue
        groups[closest].append(component)
    frames = []
    source_bounds = []
    source_pixels = strip.load()
    for group in groups:
        bounds = (min(c["box"][0] for c in group), min(c["box"][1] for c in group),
                  max(c["box"][2] for c in group), max(c["box"][3] for c in group))
        frame = Image.new("RGBA", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
        destination = frame.load()
        for component in group:
            for pos in component["pixels"]:
                x, y = pos % width, pos // width
                destination[x - bounds[0], y - bounds[1]] = source_pixels[x, y][:3] + (255,)
        frames.append(frame)
        source_bounds.append([bounds[0], bounds[1] + y0, bounds[2], bounds[3] + y0])
    return frames, source_bounds


def foot_center(image):
    mask = image.getchannel("A")
    band = mask.crop((0, max(0, image.height - max(2, round(image.height * .09))), image.width, image.height))
    box = band.getbbox()
    return (box[0] + box[2] - 1) / 2 if box else (image.width - 1) / 2


def indexed(image, colors):
    result = Image.new("P", image.size, 0)
    flat = [v for color in colors for v in color]
    result.putpalette(flat + [0] * (768 - len(flat)))
    cache = {}
    values = []
    for pixel in image.getdata():
        if pixel[3] < 128:
            values.append(0)
            continue
        rgb = pixel[:3]
        if rgb not in cache:
            cache[rgb] = min(range(1, 16), key=lambda i: sum((rgb[c] - colors[i][c]) ** 2 for c in range(3)))
        values.append(cache[rgb])
    result.putdata(values)
    result.info["transparency"] = 0
    return result
