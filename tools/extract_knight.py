#!/usr/bin/env python3
"""Extract transparent black and white knight sprites from the chess-piece sheet."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


BASE = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = BASE / "Pastel Pink Pixel Chessboard(1).png"


def _axis_grid(image: Image.Image, axis: str) -> tuple[float, float]:
    """Estimate the eight-cell grid origin and pitch from checker color changes."""
    width, height = image.size
    length = width if axis == "x" else height
    cross_length = height if axis == "x" else width
    # Scan through the empty middle ranks/files, away from the labels and frame.
    cross_center = int(cross_length * 0.45)
    scan_radius = max(2, int(cross_length * 0.018))
    low_origin = int(length * (0.074 if axis == "x" else 0.080))
    high_origin = int(length * (0.081 if axis == "x" else 0.086))
    low_pitch = length * (0.104 if axis == "x" else 0.101)
    high_pitch = length * (0.108 if axis == "x" else 0.106)

    rgb = image.convert("RGB")
    profile = []
    for pos in range(length):
        samples = []
        for delta in range(-scan_radius, scan_radius + 1, max(1, scan_radius // 4)):
            cross = max(0, min(cross_length - 1, cross_center + delta))
            samples.append(rgb.getpixel((pos, cross) if axis == "x" else (cross, pos)))
        profile.append(tuple(sum(c[i] for c in samples) / len(samples) for i in range(3)))

    # The checkerboard alternates between two flat pink colors. The correct
    # lattice makes same-parity cell-center samples similar and opposites far apart.
    best: tuple[float, float, float] | None = None
    step_origin = 0.5
    step_pitch = 0.25
    for pitch_i in range(round(low_pitch / step_pitch), round(high_pitch / step_pitch) + 1):
        pitch = pitch_i * step_pitch
        for origin_i in range(round(low_origin / step_origin), round(high_origin / step_origin) + 1):
            origin = origin_i * step_origin
            centers = [int(origin + (i + 0.5) * pitch) for i in range(8)]
            if centers[-1] >= length:
                continue
            groups = [[], []]
            for i, center in enumerate(centers):
                # Median neighborhood smooths antialiasing and small source noise.
                neighborhood = profile[max(0, center - 2):center + 3]
                value = tuple(sum(p[k] for p in neighborhood) / len(neighborhood) for k in range(3))
                groups[i % 2].append(value)
            means = [tuple(sum(p[k] for p in group) / len(group) for k in range(3)) for group in groups]
            separation = sum((means[0][k] - means[1][k]) ** 2 for k in range(3)) ** 0.5
            scatter = sum(
                sum((p[k] - means[g][k]) ** 2 for k in range(3)) ** 0.5
                for g, group in enumerate(groups) for p in group
            ) / 8
            # Prefer a strong checker contrast and consistent centers, with a
            # gentle tie-break toward a full 8-cell span inside the detected image.
            target_span = 0.852 if axis == "x" else 0.829
            score = separation - scatter * 1.25 - abs((pitch * 8) / length - target_span) * 80
            if best is None or score > best[0]:
                best = (score, origin, pitch)
    if best is None:
        raise RuntimeError(f"Could not detect the {axis}-axis board grid")
    return best[1], best[2]


def detect_grid(image: Image.Image) -> tuple[float, float, float, float]:
    """Return (left, top, square_width, square_height) in source pixels."""
    x0, dx = _axis_grid(image, "x")
    y0, dy = _axis_grid(image, "y")
    return x0, y0, dx, dy


def _strongest_edge(image: Image.Image, axis: str, expected: float,
                    cross: float, radius: int) -> int:
    """Snap a predicted grid line to the strongest nearby pixel-color edge."""
    rgb = image.convert("RGB")
    length = rgb.width if axis == "x" else rgb.height
    cross_length = rgb.height if axis == "x" else rgb.width
    cross_pos = int(cross_length * cross)
    half = max(3, int(cross_length * 0.012))
    profile = []
    for pos in range(length):
        colors = [rgb.getpixel((pos, c) if axis == "x" else (c, pos))
                  for c in range(max(0, cross_pos - half), min(cross_length, cross_pos + half + 1), 2)]
        profile.append(tuple(sum(color[k] for color in colors) / len(colors) for k in range(3)))

    def edge_score(pos: int) -> float:
        before = [profile[i] for i in range(pos - 4, pos)]
        after = [profile[i] for i in range(pos + 1, pos + 5)]
        return sum((sum(c[k] for c in after) / len(after) -
                    sum(c[k] for c in before) / len(before)) ** 2 for k in range(3)) ** 0.5

    center = round(expected)
    candidates = range(max(5, center - radius), min(length - 5, center + radius + 1))
    return max(candidates, key=edge_score)


def _transparent_background(tile: Image.Image) -> Image.Image:
    """Flood-fill the tile's edge-connected pink background while preserving ink."""
    rgba = tile.convert("RGBA")
    rgb = rgba.convert("RGB")
    w, h = rgb.size
    # Sample inset corner patches: the outermost edge is a dark grid line, not
    # the square background, and a piece may overlap the lower-right corner.
    inset = max(6, round(min(w, h) * 0.06))
    patch = max(6, round(min(w, h) * 0.08))
    # The b-file knight can reach the lower-right tile corner; use the other
    # three corners to estimate the square color without sampling the piece.
    starts = ((inset, inset), (w - inset - patch, inset),
              (inset, h - inset - patch))
    border = [
        rgb.getpixel((x0 + dx, y0 + dy))
        for x0, y0 in starts
        for dx in range(patch) for dy in range(patch)
    ]
    # The most common quantized color family in the corner patches is the
    # flat square background; ink and piece shading occupy fewer pixels.
    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for color in border:
        key = tuple(channel // 16 for channel in color)
        buckets.setdefault(key, []).append(color)
    dominant = max(buckets.values(), key=len)
    bg = tuple(sorted(c[i] for c in dominant)[len(dominant) // 2] for i in range(3))

    # Permit modest pixel-art shading and compression noise around the flat color.
    tolerance = 37
    pixels = rgb.load()
    mask = bytearray(w * h)
    queue = deque()

    def background(x: int, y: int) -> bool:
        c = pixels[x, y]
        return sum((c[i] - bg[i]) ** 2 for i in range(3)) ** 0.5 <= tolerance

    for x0, y0 in starts:
        for x in range(x0, x0 + patch):
            for y in range(y0, y0 + patch):
                idx = y * w + x
                if not mask[idx] and background(x, y):
                    mask[idx] = 1
                    queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not mask[idx] and background(nx, ny):
                    mask[idx] = 1
                    queue.append((nx, ny))

    alpha = Image.new("L", (w, h), 255)
    alpha.putdata([0 if value else 255 for value in mask])
    # The source has a one-pixel dark square outline that can touch the crop
    # edge; discard its antialiased fringe after the background flood-fill.
    alpha_draw = Image.new("L", (w, h), 255)
    # Keep the operation deliberately narrow so it cannot reach either piece.
    from PIL import ImageDraw
    ImageDraw.Draw(alpha_draw).rectangle((0, 0, w - 1, 1), fill=0)
    ImageDraw.Draw(alpha_draw).rectangle((0, 0, 1, h - 1), fill=0)
    ImageDraw.Draw(alpha_draw).rectangle((w - 2, 0, w - 1, h - 1), fill=0)
    ImageDraw.Draw(alpha_draw).rectangle((0, h - 2, w - 1, h - 1), fill=0)
    alpha = Image.new("L", (w, h), 0)
    # A pixel remains only when neither the flood-fill nor edge cleanup marked it.
    alpha.putdata([0 if mask[i] or alpha_draw.getpixel((i % w, i // w)) == 0 else 255
                   for i in range(w * h)])
    rgba.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError("Background removal erased the entire knight")
    return rgba.crop(bbox)


def extract(source: Path = DEFAULT_SOURCE, output_dir: Path = BASE) -> list[Path]:
    sheet = Image.open(source).convert("RGB")
    left, top, cell_w, cell_h = detect_grid(sheet)
    outputs = []
    # Black: top rank, b-file; White: bottom rank, b-file.
    for name, row in (("knight_black.png", 0), ("knight_white.png", 7)):
        margin = 8  # stay inside the heavy grid lines around each source square
        expected_left = left + cell_w
        expected_right = left + cell_w * 2
        # The source sheet's outside files are slightly wider than the middle
        # files, so snap the b-file's two boundaries independently.
        x0 = _strongest_edge(sheet, "x", expected_left, 0.45, 18) + margin
        x1 = _strongest_edge(sheet, "x", expected_right, 0.45, 18) - margin
        if row == 0:
            y0 = round(top) + 2
            y1 = _strongest_edge(sheet, "y", top + cell_h, (x0 + 8) / sheet.width, 16) - margin
        else:
            y0 = _strongest_edge(sheet, "y", top + cell_h * row,
                                 (x0 + 8) / sheet.width, 18) + margin
            y1 = _strongest_edge(sheet, "y", top + cell_h * (row + 1),
                                 (x0 + 8) / sheet.width, 12) - margin
        sprite = _transparent_background(sheet.crop((x0, y0, x1, y1)))
        path = output_dir / name
        sprite.save(path)
        outputs.append(path)
    print(f"Detected grid: x={left:.1f}, y={top:.1f}, cell={cell_w:.1f}x{cell_h:.1f}")
    for path in outputs:
        with Image.open(path) as sprite:
            print(f"Saved {path.name}: {sprite.size}, alpha={sprite.mode == 'RGBA'}")
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="piece-sheet PNG")
    parser.add_argument("--output-dir", type=Path, default=BASE, help="destination directory")
    args = parser.parse_args()
    extract(args.source, args.output_dir)


if __name__ == "__main__":
    main()
