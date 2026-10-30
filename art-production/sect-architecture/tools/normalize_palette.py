#!/usr/bin/env python3
"""Map PixelLab RGB clusters to the declared Canopy palette without resampling.

The nine raw masters remain untouched. The four isolated root-tip pixels listed
below are an explicit pixel-level cleanup for the shrine's 77-pixel slot; the
original is kept in masters/tree-shrine.png. No other alpha pixel is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1] / "canopy-village"
SHRINE_REMOVED_PIXELS = ((37, 78), (38, 78), (39, 78), (50, 78))


def lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    linear = tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                   for v in (channel / 255 for channel in rgb))
    x, y, z = (
        .4124564 * linear[0] + .3575761 * linear[1] + .1804375 * linear[2],
        .2126729 * linear[0] + .7151522 * linear[1] + .0721750 * linear[2],
        .0193339 * linear[0] + .1191920 * linear[1] + .9503041 * linear[2],
    )
    x, y, z = x / .95047, y, z / 1.08883
    transform = lambda v: v ** (1 / 3) if v > .008856451679 else 7.787037037 * v + 16 / 116
    fx, fy, fz = transform(x), transform(y), transform(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def main() -> None:
    palette = [tuple(bytes.fromhex(value[1:])) for value in json.loads((ROOT / "palette.json").read_text())["colors"]]
    assert len(palette) == len(set(palette)) == 32
    palette_lab = [lab(color) for color in palette]
    output = ROOT / "palette-normalized"
    output.mkdir(exist_ok=True)
    records = []
    for path in sorted((ROOT / "masters").glob("*.png")):
        source = Image.open(path).convert("RGBA")
        assert set(source.getchannel("A").get_flattened_data()) <= {0, 255}
        image = Image.new("RGBA", source.size)
        source_pixels = source.load()
        target_pixels = image.load()
        mapping: dict[tuple[int, int, int], tuple[int, int, int]] = {}
        removed = set(SHRINE_REMOVED_PIXELS if path.stem == "tree-shrine" else ())
        for y in range(source.height):
            for x in range(source.width):
                r, g, b, a = source_pixels[x, y]
                if a == 0 or (x, y) in removed:
                    target_pixels[x, y] = (0, 0, 0, 0)
                    continue
                color = (r, g, b)
                if color not in mapping:
                    if color in palette:
                        mapping[color] = color
                    else:
                        point = lab(color)
                        choice = min(range(len(palette)), key=lambda i: sum((point[j] - palette_lab[i][j]) ** 2 for j in range(3)))
                        mapping[color] = palette[choice]
                target_pixels[x, y] = (*mapping[color], 255)
        if removed:
            assert all(source_pixels[x, y][3] == 255 for x, y in removed)
            assert image.getchannel("A").getbbox()[3] == 78
        assert all(source_pixels[x, y][3] == target_pixels[x, y][3]
                   for y in range(source.height) for x in range(source.width) if (x, y) not in removed)
        target_path = output / path.name
        image.save(target_path)
        visible = {pixel[:3] for pixel in image.get_flattened_data() if pixel[3]}
        assert visible <= set(palette) and len(visible) <= 32
        records.append({
            "asset": path.stem,
            "master": str(path.relative_to(ROOT)),
            "masterSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "output": str(target_path.relative_to(ROOT)),
            "outputSha256": hashlib.sha256(target_path.read_bytes()).hexdigest(),
            "inputVisibleColors": len(mapping), "outputVisibleColors": len(visible),
            "alphaChanges": [{"x": x, "y": y, "from": 255, "to": 0} for x, y in sorted(removed)],
            "method": "nearest CIELAB palette color per visible pixel; no resampling; alpha differs only at the explicitly listed cleanup coordinates",
        })
    (ROOT / "palette-normalization.json").write_text(json.dumps({"schemaVersion": 1, "palette": "palette.json", "assets": records}, indent=2) + "\n")
    print(json.dumps({"assets": len(records), "alphaChanges": sum(len(record["alphaChanges"]) for record in records),
                      "allWithinPalette": True}))


if __name__ == "__main__":
    main()
