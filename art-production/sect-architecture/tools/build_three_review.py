#!/usr/bin/env python3
"""Validate and package the three provisional sect identities without game edits.

Raw PixelLab PNGs remain in masters/. Palette mapping changes RGB only; it
does not change alpha or positions. Canvas adaptation crops only transparent
padding and pastes visible pixels intact. An oversize item receives a larger
review canvas and a failed game-slot check rather than losing pixels.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from normalize_palette import lab


ROOT = Path(__file__).resolve().parents[1] / "planned-three"
SPECS = [
    ("citadel-hall-a", 0, "principal hall", (144, 144), (147, 141), "sectHall"),
    ("citadel-gatehouse", 0, "gatehouse", (96, 100), (96, 90), "sectGate"),
    ("citadel-mountain", 0, "separate mountain landmark", (160, 160), (160, 160), None),
    ("sky-monastery-hall-a", 1, "principal hall", (144, 144), (147, 141), "sectHall"),
    ("sky-monastery-peak", 1, "separate mountain peak", (128, 160), (128, 160), None),
    ("sky-monastery-bridge", 1, "suspended bridge", (96, 64), (96, 80), None),
    ("iron-foundry-hall-a", 2, "principal hall", (144, 144), (147, 141), "sectHall"),
    ("iron-foundry-furnace-tower", 2, "furnace tower", (96, 128), (96, 128), None),
    ("iron-foundry-workshop", 2, "weapons workshop", (96, 100), (106, 109), "blacksmith"),
]
FAMILIES = {0: "Citadel", 1: "Sky Monastery", 2: "Iron Foundry"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_colors(image: Image.Image) -> Counter[tuple[int, int, int]]:
    return Counter(pixel[:3] for pixel in image.get_flattened_data() if pixel[3])


def palette_for(images: list[Image.Image]) -> list[tuple[int, int, int]]:
    counts: Counter[tuple[int, int, int]] = Counter()
    for image in images:
        counts.update(visible_colors(image))
    samples = []
    for color, count in sorted(counts.items()):
        samples.extend([color] * max(1, min(20, round(math.sqrt(count) / 2))))
    sample = Image.new("RGB", (len(samples), 1))
    sample.putdata(samples)
    quantized = sample.quantize(colors=32, method=Image.Quantize.MEDIANCUT,
                                dither=Image.Dither.NONE)
    raw = quantized.getpalette()
    colors = [tuple(raw[index * 3:index * 3 + 3]) for index in sorted({value for _, value in quantized.getcolors()})]
    colors = list(dict.fromkeys(colors))
    # A quantizer may return fewer than 32 distinct entries for a sparse source.
    for color, _ in counts.most_common():
        if len(colors) == 32:
            break
        if color not in colors:
            colors.append(color)
    if len(colors) != 32:
        raise RuntimeError("Could not construct a 32-colour family palette")
    return colors


def normalized(image: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    points = [lab(color) for color in palette]
    mapping = {}
    output = Image.new("RGBA", image.size)
    pixels = []
    for red, green, blue, alpha in image.get_flattened_data():
        if not alpha:
            pixels.append((0, 0, 0, 0))
            continue
        color = (red, green, blue)
        if color not in mapping:
            if color in palette:
                mapping[color] = color
            else:
                point = lab(color)
                best = min(range(32), key=lambda index: sum((point[j] - points[index][j]) ** 2 for j in range(3)))
                mapping[color] = palette[best]
        pixels.append((*mapping[color], alpha))
    output.putdata(pixels)
    return output


def edge_contacts(image: Image.Image) -> dict[str, int]:
    alpha = image.getchannel("A")
    width, height = image.size
    return {"top": sum(bool(v) for v in alpha.crop((0, 0, width, 1)).tobytes()),
            "right": sum(bool(v) for v in alpha.crop((width - 1, 0, width, height)).tobytes()),
            "bottom": sum(bool(v) for v in alpha.crop((0, height - 1, width, height)).tobytes()),
            "left": sum(bool(v) for v in alpha.crop((0, 0, 1, height)).tobytes())}


def checker(size: tuple[int, int]) -> Image.Image:
    out = Image.new("RGBA", size, "#e1e3d9")
    draw = ImageDraw.Draw(out)
    for y in range(0, size[1], 8):
        for x in range(0, size[0], 8):
            if (x // 8 + y // 8) % 2:
                draw.rectangle((x, y, x + 7, y + 7), fill="#cbd1c5")
    return out


def overview(images: dict[str, Image.Image], records: list[dict]) -> None:
    card_w, card_h = 420, 395
    out = Image.new("RGB", (1320, 1270), "#ebede3")
    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    draw.text((24, 15), "PIXELLAB | THREE SECT ARCHITECTURAL IDENTITIES | PROVISIONAL", fill="#202931", font=font)
    draw.text((24, 33), "Actual transparent PNGs shown at 2x nearest-neighbour. No game installation.", fill="#445359", font=font)
    for index, record in enumerate(records):
        name = record["id"]
        image = images[name]
        col, row = index % 3, index // 3
        x, y = 15 + col * 435, 65 + row * card_h
        draw.rounded_rectangle((x, y, x + card_w, y + card_h - 8), radius=6,
                               fill="#d9e0d7", outline="#99a99a", width=2)
        label = f"{FAMILIES[record['registryId']]} | {record['role']} | {image.width}x{image.height}"
        draw.text((x + 12, y + 11), label, fill="#202931", font=font)
        preview = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        px = x + (card_w - preview.width) // 2
        py = y + 40 + (326 - preview.height) // 2
        out.paste(preview, (px, py), preview)
        draw.text((x + 12, y + card_h - 25), name, fill="#465c50", font=font)
    draw.text((24, 1250), "Technical fit and artistic limitations are in review-report.md", fill="#465c50", font=font)
    out.save(ROOT / "previews/overview.png")


def native_sheet(sources: dict[str, Image.Image], assets: dict[str, Image.Image], records: list[dict]) -> None:
    widths = 1080
    row_h = 560
    out = Image.new("RGB", (widths, 70 + row_h * len(records)), "#f0f0e7")
    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    draw.text((20, 15), "THREE SECTS | NATIVE SOURCE | NATIVE REVIEW CELL | 3x NEAREST", fill="#20302c", font=font)
    draw.text((20, 34), "PixelLab artwork, palette-normalized; anchors are provisional. A larger review cell indicates a fit failure.", fill="#43544a", font=font)
    for index, record in enumerate(records):
        y = 70 + index * row_h
        name = record["id"]
        draw.text((20, y + 4), f"{name} | {record['role']} | {'PASS' if record['technicalPass'] else 'CHECK FIT'}", fill="#20302c", font=font)
        for col, (image, scale) in enumerate(((sources[name], 1), (assets[name], 1), (assets[name], 3))):
            left = [20, 210, 405][col]
            title = ["PixelLab source 1x", "Review cell 1x", "Review cell 3x nearest"][col]
            draw.text((left, y + 23), title, fill="#53655b", font=font)
            pic = image if scale == 1 else image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
            background = checker(pic.size)
            background.alpha_composite(pic)
            out.paste(background.convert("RGB"), (left, y + 47))
        draw.line((20, y + row_h - 10, widths - 20, y + row_h - 10), fill="#b7beb2")
    out.save(ROOT / "previews/native-and-3x.png")


def silhouette_sheet(assets: dict[str, Image.Image]) -> None:
    names = ("citadel-hall-a", "sky-monastery-hall-a", "iron-foundry-hall-a")
    out = Image.new("RGB", (1080, 400), "#e7e9e0")
    draw = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    draw.text((20, 15), "THREE PRINCIPAL HALLS | ALPHA SILHOUETTES AT 2x NEAREST", fill="#24332d", font=font)
    draw.text((20, 33), "Distinct masks are a shape check; recognisability still needs human judgement.", fill="#526156", font=font)
    for index, name in enumerate(names):
        image = assets[name]
        mask = Image.new("RGBA", image.size, (35, 47, 44, 0))
        mask.putalpha(image.getchannel("A"))
        mask = mask.resize((mask.width * 2, mask.height * 2), Image.Resampling.NEAREST)
        left = 25 + index * 350
        out.paste(mask, (left + (300 - mask.width) // 2, 70), mask)
        draw.text((left + 20, 366), name, fill="#24332d", font=font)
    out.save(ROOT / "previews/silhouette-comparison.png")


def main() -> int:
    for directory in ("assets", "palette-normalized", "previews"):
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    raw: dict[str, Image.Image] = {}
    for name, *_ in SPECS:
        path = ROOT / "masters" / f"{name}.png"
        if not path.is_file():
            raise RuntimeError(f"Missing PixelLab source: {name}")
        with Image.open(path) as opened:
            if opened.format != "PNG":
                raise RuntimeError(f"Not a PNG: {name}")
            raw[name] = opened.convert("RGBA")
    palettes: dict[int, list[tuple[int, int, int]]] = {}
    for family in FAMILIES:
        images = [raw[name] for name, ident, *_ in SPECS if ident == family]
        palettes[family] = palette_for(images)
    (ROOT / "palettes.json").write_text(json.dumps({"schemaVersion": 1, "method": "family-shared 32-colour median cut candidate palette derived from all three raw sprites per identity; CIELAB mapping without dithering or alpha changes",
                                              "palettes": {FAMILIES[k]: ["#" + bytes(c).hex() for c in colors] for k, colors in palettes.items()}}, indent=2) + "\n")
    records = []
    sources, assets = {}, {}
    for name, family, role, expected_source, desired_cell, slot in SPECS:
        original = raw[name]
        result = normalized(original, palettes[family])
        source_path = ROOT / "palette-normalized" / f"{name}.png"
        result.save(source_path)
        bbox = result.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"Empty image: {name}")
        crop = result.crop(bbox)
        desired_width, desired_height = desired_cell
        canvas_size = (max(desired_width, crop.width), max(desired_height, crop.height))
        canvas = Image.new("RGBA", canvas_size)
        paste_at = ((canvas.width - crop.width) // 2, canvas.height - crop.height)
        canvas.paste(crop, paste_at)
        output_path = ROOT / "assets" / f"{name}.png"
        canvas.save(output_path)
        alpha_equal = original.getchannel("A").tobytes() == result.getchannel("A").tobytes()
        rgba_equal = canvas.crop((*paste_at, paste_at[0] + crop.width, paste_at[1] + crop.height)).tobytes() == crop.tobytes()
        colors = set(visible_colors(result))
        alpha_binary = set(original.getchannel("A").get_flattened_data()) <= {0, 255}
        fits = crop.width <= desired_width and crop.height <= desired_height
        checks = {"sourceCanvasExpected": original.size == expected_source,
                  "binaryAlpha": alpha_binary,
                  "normalizationAlphaUnchanged": alpha_equal,
                  "familyPaletteSubset": colors <= set(palettes[family]),
                  "atMost32Colours": len(colors) <= 32,
                  "allVisibleRgbaPixelsPreservedInCanvasAdaptation": rgba_equal,
                  "fitsDeclaredCanvas": fits}
        record = {"id": name, "registryId": family, "sect": FAMILIES[family], "role": role,
                  "status": "provisional", "sourceMaster": f"masters/{name}.png",
                  "sourceSha256": sha(ROOT / "masters" / f"{name}.png"),
                  "generationRequest": "requests/citadel-mountain-correction.json" if name == "citadel-mountain" else f"requests/{name}.json",
                  "generationReceipt": f"receipts/{name}.json",
                  "rejectedIteration": "iterations/citadel-mountain-square-block.png" if name == "citadel-mountain" else None,
                  "paletteNormalized": f"palette-normalized/{name}.png", "file": f"assets/{name}.png",
                  "sha256": sha(output_path), "sourceCanvas": list(original.size),
                  "sourceVisibleBounds": list(bbox), "declaredCanvas": list(desired_cell),
                  "reviewCanvas": list(canvas.size), "anchor": [canvas.width / 2, canvas.height],
                  "anchorMeaning": "bottom-centre review reference; actual physical contact needs human review",
                  "currentGameSlot": slot, "currentGameSlotFit": fits if slot else None,
                  "sourceEdgeContacts": edge_contacts(original), "sourceVisibleColorCount": len(visible_colors(original)),
                  "normalizedVisibleColorCount": len(colors), "checks": checks,
                  "technicalPass": all(checks.values()), "artQualityReview": "pending",
                  "navigationReview": "not implemented"}
        records.append(record)
        sources[name], assets[name] = result, canvas
        canvas.resize((canvas.width * 3, canvas.height * 3), Image.Resampling.NEAREST).save(ROOT / "previews" / f"{name}-3x.png")
    overview(assets, records)
    native_sheet(sources, assets, records)
    silhouette_sheet(assets)
    validation = {"schemaVersion": 1, "technicalPass": all(item["technicalPass"] for item in records),
                  "assets": records, "humanArtReview": "pending",
                  "limitations": ["Three identities have provisional principal and support art, not complete architecture packs.",
                                  "No residence, growth-stage, measured port, elevated path, collision or integrated terrain system is claimed.",
                                  "An isolated source PNG cannot prove a clean foundation or that generated artwork was not clipped at its own edge.",
                                  "The current v79 game, renderer, saves and published environment were not changed."]}
    manifest = {"schemaVersion": 1, "name": "Three sect architectural identities", "status": "provisional",
                "registryIds": [0, 1, 2], "currentGameChanged": False,
                "integrationStatus": "not installed", "humanArtReview": "pending", "assets": records}
    (ROOT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    lines = ["# Three sect PixelLab art review", "", "Nine separate PixelLab-generated transparent PNGs across Citadel, Sky Monastery and Iron Foundry. Artwork is provisional and no game files were changed.", "",
             "[Overview](previews/overview.png) · [Native and 3× view](previews/native-and-3x.png) · [Hall silhouettes](previews/silhouette-comparison.png) · [Validation data](validation.json) · [Manifest](manifest.json)", "",
             f"Technical canvas checks: **{sum(item['technicalPass'] for item in records)}/{len(records)} pass**. These checks do not approve art quality or in-game navigation.", "",
             "| Asset | Intended canvas | Review canvas | Source colors → 32-color family palette | Fit |", "| --- | --- | --- | --- | --- |"]
    for item in records:
        lines.append(f"| {item['id']} | {item['declaredCanvas'][0]}×{item['declaredCanvas'][1]} | {item['reviewCanvas'][0]}×{item['reviewCanvas'][1]} | {item['sourceVisibleColorCount']} → {item['normalizedVisibleColorCount']} | {'pass' if item['technicalPass'] else 'needs correction'} |")
    lines += ["", "Source-edge contacts, exact checks and file hashes are recorded in `validation.json`. All palette-normalized inputs preserve source alpha exactly; placing art in review canvases preserves every visible RGBA pixel without resampling. Source edge contact may indicate PixelLab clipping and needs visual review.", "",
              "Three older 48×48 account objects were examined but were too small and generic for these designs; they are not included or counted.", "",
              "Remaining scope: independent residences, more specialty buildings, meaningful architectural and growth variations, mountain and bridge attachment measurements, collision/path support, native game-scale composition and art approval.", ""]
    (ROOT / "review-report.md").write_text("\n".join(lines))
    print(json.dumps({"assets": len(records), "technicalPassCount": sum(item["technicalPass"] for item in records),
                      "artReview": "pending", "report": str(ROOT / "review-report.md")}, indent=2))
    return 0 if validation["technicalPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
