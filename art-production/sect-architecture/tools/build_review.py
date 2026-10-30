#!/usr/bin/env python3
"""Build provisional Canopy Village review artifacts without editing source art.

Requires Pillow. Run after generation and optional palette normalization::

    python3 art-production/sect-architecture/tools/build_review.py

Each palette-normalized/<id>.png is preferred when present, otherwise its master
is used. Only transparent padding is removed. The remaining RGBA rectangle is
pasted, without a mask or resampling, into the declared canvas at bottom centre.
An object that does not fit is rejected; its master remains untouched. The only
resampling in this tool is nearest-neighbour enlargement of review previews.
Exit status 1 means at least one technical check failed. A zero exit status is
not artistic approval, anchor approval, or approval to install art in the game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "canopy-village"
SPECS = (
    {"id": "hall-a", "role": "principal hall", "variant": "A", "source": (144, 144),
     "target": (147, 141), "slot": "sectHall", "footprint": (4.6, 2.7),
     "ports": {"left": (12, 93), "right": (135, 93)}},
    {"id": "hall-b", "role": "principal hall", "variant": "B", "source": (144, 144),
     "target": (147, 141), "slot": "sectHall", "footprint": (4.6, 2.7),
     "ports": {"left": (12, 93), "right": (135, 93)}},
    {"id": "house-a", "role": "branch house", "variant": "A", "source": (96, 100),
     "target": (90, 99), "slot": "house", "footprint": (2.8, 1.8),
     "ports": {"left": (8, 51), "right": (82, 51)}},
    {"id": "house-b", "role": "hanging branch house", "variant": "B", "source": (96, 100),
     "target": (96, 99), "slot": "house", "footprint": (2.8, 1.8),
     "ports": {"left": (8, 51), "right": (82, 51)}},
    {"id": "tree-shrine", "role": "tree shrine", "variant": None, "source": (64, 80),
     "target": (58, 77), "slot": "sectAltar", "footprint": (1.8, 1.5),
     "ports": {"leftOptional": (6, 29), "rightOptional": (52, 29)}},
    {"id": "root-gate", "role": "root-supported entrance", "variant": None,
     "source": (96, 96), "target": (96, 90), "slot": "sectGate",
     "footprint": (3.0, 0.6), "ports": {}},
    {"id": "rope-bridge", "role": "decorative rope bridge", "variant": None,
     "source": (96, 64), "target": (96, 80), "slot": None, "footprint": None,
     "ports": {"left": (0, 32), "right": (96, 32)}},
    {"id": "trunk-stairs", "role": "decorative trunk staircase", "variant": None,
     "source": (64, 96), "target": (64, 112), "slot": None, "footprint": None,
     "ports": {"lower": (32, 112), "upper": (32, 64)}},
    {"id": "ancient-tree", "role": "decorative forest landmark", "variant": None,
     "source": (128, 160), "target": (128, 160), "slot": None,
     "footprint": None, "ports": {}},
)
LIMITATIONS = (
    "Provisional art-production review; no source approval or human approval is implied.",
    "The current game, renderer, gameplay data and published settings are unchanged; these assets are not installed.",
    "A palette-subset check verifies the supplied palette.json, not whether that palette or the visual result is artistically approved.",
    "Canvas bottom-centre anchors come from grid-contract.md. Integer placement can put an even-width object half a pixel from an odd-width canvas centre; no pixels are resampled.",
    "Measured architectural ports are unknown. Contract port coordinates are recommendations, not measured artwork geometry or functioning connections.",
    "Bridge, stairs and the landmark have no existing gameplay type or collision footprint. There is no elevated navigation implementation or functional path claim.",
    "Exact image bounds prove that this adaptation did not clip the input. Source edge contact is reported, but a PNG alone cannot establish whether its generating process clipped an object.",
    "Native-size readability, clear ground contact, perspective, lighting, architectural variation, silhouette identity and art quality require human review in context.",
    "The hanging house is 96 pixels wide against the existing 90-pixel house slot. Its 96x99 PNG is a review canvas, not a drop-in game asset. Its branch touches the source top and left edges, so source clipping needs artistic review.",
    "Four isolated bottom-edge root-tip pixels of the shrine were removed manually to fit its 58x77 slot. The original PixelLab master and exact coordinates are preserved in palette-normalization.json.",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str | None:
    return sha256(path.read_bytes()) if path.is_file() else None


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def load_png(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        if opened.format != "PNG":
            raise ValueError("Expected PNG input")
        opened.load()
        return opened.convert("RGBA")


def alpha_counts(image: Image.Image) -> dict[str, int]:
    return {str(value): count for count, value in (image.getchannel("A").getcolors() or [])}


def edge_contacts(image: Image.Image) -> dict[str, int]:
    alpha = image.getchannel("A")
    w, h = image.size
    return {
        "top": sum(value != 0 for value in alpha.crop((0, 0, w, 1)).tobytes()),
        "right": sum(value != 0 for value in alpha.crop((w - 1, 0, w, h)).tobytes()),
        "bottom": sum(value != 0 for value in alpha.crop((0, h - 1, w, h)).tobytes()),
        "left": sum(value != 0 for value in alpha.crop((0, 0, 1, h)).tobytes()),
    }


def visible_colors(image: Image.Image) -> set[tuple[int, int, int]]:
    pixels = image.tobytes()
    return {tuple(pixels[i:i + 3]) for i in range(0, len(pixels), 4) if pixels[i + 3]}


def hex_color(color: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in color)


def load_palette(root: Path) -> tuple[set[tuple[int, int, int]], dict[str, Any]]:
    path = root / "palette.json"
    metadata: dict[str, Any] = {"file": "palette.json", "sha256": file_hash(path)}
    try:
        values = json.loads(path.read_text())["colors"]
        if not isinstance(values, list):
            raise ValueError("colors must be a list")
        colors = []
        for value in values:
            if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
                raise ValueError("Each palette color must be #RRGGBB")
            if any(char not in "0123456789abcdefABCDEF" for char in value[1:]):
                raise ValueError("Each palette color must contain six hexadecimal digits")
            colors.append(tuple(bytes.fromhex(value[1:])))
        metadata.update({"declaredColorCount": len(colors), "uniqueColorCount": len(set(colors)),
                         "exactly32UniqueColors": len(colors) == len(set(colors)) == 32})
        return set(colors), metadata
    except (OSError, ValueError, KeyError, TypeError) as exc:
        metadata.update({"exactly32UniqueColors": False, "error": str(exc)})
        return set(), metadata


def inspect_asset(spec: dict[str, Any], root: Path, palette: set[tuple[int, int, int]]) -> tuple[dict, dict, Image.Image | None, Image.Image | None]:
    asset_id = spec["id"]
    master_path = root / "masters" / f"{asset_id}.png"
    normalized_path = root / "palette-normalized" / f"{asset_id}.png"
    source_path = normalized_path if normalized_path.is_file() else master_path
    target_path = root / "assets" / f"{asset_id}.png"
    checks: dict[str, bool] = {"masterPresent": master_path.is_file(), "inputPresent": source_path.is_file()}
    existing_slot_canvas = {"sectHall": (147, 141), "house": (90, 99),
                            "sectAltar": (58, 77), "sectGate": (96, 90)}.get(spec["slot"])
    if existing_slot_canvas is not None:
        checks["existingGameSlotCanvasMatches"] = spec["target"] == existing_slot_canvas
    result: dict[str, Any] = {
        "id": asset_id, "checks": checks, "errors": [], "warnings": [],
        "master": {"file": relative(master_path, root), "sha256Before": file_hash(master_path)},
        "input": {"file": relative(source_path, root), "stage": "palette-normalized" if source_path == normalized_path else "master",
                  "sha256Before": file_hash(source_path)},
        "expectedSourceCanvas": list(spec["source"]), "targetCanvas": list(spec["target"]),
        "existingGameSlotCanvas": list(existing_slot_canvas) if existing_slot_canvas else None,
        "output": None,
    }
    manifest: dict[str, Any] = {
        "id": asset_id, "role": spec["role"], "variant": spec["variant"], "status": "provisional",
        "generationRequest": "requests/house-b-correction.json" if asset_id == "house-b" else f"requests/{asset_id}.json",
        "generationReceipt": f"receipts/{asset_id}.json",
        "rejectedIteration": "iterations/house-b-trunk-mounted.png" if asset_id == "house-b" else None,
        "currentGameSlot": spec["slot"],
        "groundFootprintTiles": {"width": spec["footprint"][0], "depth": spec["footprint"][1]} if spec["footprint"] else None,
        "footprintSource": "../grid-contract.md" if spec["footprint"] else None,
        "canvas": list(spec["target"]), "groundAnchor": [spec["target"][0] / 2, spec["target"][1]],
        "existingGameSlotCanvas": list(existing_slot_canvas) if existing_slot_canvas else None,
        "existingGameSlotCanvasMatches": spec["target"] == existing_slot_canvas if existing_slot_canvas else None,
        "anchorCoordinates": "canvas edges; bottom centre; last pixel row is height - 1",
        "anchorSource": "../grid-contract.md", "anchorHumanReview": "pending",
        "anchorMeaning": "canvas placement reference; physical ground contact is unverified",
        "attachmentRequired": asset_id == "house-b",
        "recommendedPorts": {name: list(point) for name, point in spec["ports"].items()},
        "recommendedPortsSource": "../grid-contract.md" if spec["ports"] else None,
        "measuredPorts": None, "portHumanReview": "pending",
        "gameplayNavigation": "not implemented" if spec["slot"] is None else "existing slot is a visual compatibility suggestion only",
        "sourceMaster": relative(master_path, root), "input": relative(source_path, root),
        "inputStage": result["input"]["stage"], "file": None,
        "artQualityReview": "pending", "nativeReadabilityReview": "pending",
    }
    source = target = None
    master = None
    try:
        if checks["masterPresent"]:
            master = load_png(master_path)
            result["master"]["canvas"] = list(master.size)
            checks["masterExpectedCanvas"] = master.size == spec["source"]
        if not checks["inputPresent"]:
            raise ValueError("Input PNG is missing")
        source = load_png(source_path)
        checks["inputPngReadable"] = True
        result["input"]["canvas"] = list(source.size)
        checks["expectedSourceCanvas"] = source.size == spec["source"]
        if source_path == normalized_path:
            expected_alpha = master.getchannel("A").copy() if master is not None else None
            expected_cleanup = [(37, 78), (38, 78), (39, 78), (50, 78)] if asset_id == "tree-shrine" else []
            if expected_alpha is not None:
                for point in expected_cleanup:
                    expected_alpha.putpixel(point, 0)
            checks["normalizedGeometryMatchesMasterAndDocumentedCleanup"] = (
                master is not None and source.size == master.size and
                source.getchannel("A").tobytes() == expected_alpha.tobytes())
            result["documentedRemovedPixels"] = [list(point) for point in expected_cleanup]
        alpha = source.getchannel("A")
        counts = alpha_counts(source)
        result["alphaValueCounts"] = counts
        checks["binaryAlpha"] = set(counts).issubset({"0", "255"})
        bbox = alpha.getbbox()
        checks["nonempty"] = bbox is not None
        result["input"]["alphaBoundingBox"] = list(bbox) if bbox else None
        result["sourceEdgeContacts"] = edge_contacts(source)
        if any(result["sourceEdgeContacts"].values()):
            result["warnings"].append("Visible source pixels touch a canvas edge; inspect for intentional contacts or source clipping.")
        colors = visible_colors(source)
        outside = colors - palette
        result["visibleColorCount"] = len(colors)
        result["colorsOutsidePalette"] = sorted(hex_color(color) for color in outside)
        checks["paletteSubset"] = not outside
        checks["atMost32VisibleColors"] = len(colors) <= 32
        if bbox:
            crop = source.crop(bbox)
            tw, th = spec["target"]
            cw, ch = crop.size
            checks["alphaBoundingBoxFitsTarget"] = cw <= tw and ch <= th
            if not checks["alphaBoundingBoxFitsTarget"]:
                result["errors"].append(f"Visible bounds {cw}x{ch} do not fit target {tw}x{th}; no target was written.")
            elif checks["expectedSourceCanvas"]:
                x, y = (tw - cw) // 2, th - ch
                target = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
                target.paste(crop, (x, y))  # No mask: preserve all four channels exactly.
                recovered = target.crop((x, y, x + cw, y + ch))
                source_crop_hash = sha256(crop.tobytes())
                output_crop_hash = sha256(recovered.tobytes())
                checks["cropRgbaPreservedExactly"] = source_crop_hash == output_crop_hash
                checks["allVisiblePixelsPreserved"] = sum(value != 0 for value in alpha.tobytes()) == sum(value != 0 for value in target.getchannel("A").tobytes())
                checks["noOutputClipping"] = target.getchannel("A").getbbox() == (x, y, x + cw, y + ch)
                target.save(target_path)
                saved = load_png(target_path)
                checks["savedRgbaPreservedExactly"] = saved.size == target.size and saved.tobytes() == target.tobytes()
                result["adaptation"] = {
                    "method": "crop transparent padding; integer paste at ground-bottom centre",
                    "cropBox": list(bbox), "pasteTopLeft": [x, y], "pastedRectangle": [x, y, x + cw, y + ch],
                    "horizontalCentreOffsetPixels": x + cw / 2 - tw / 2,
                    "resampled": False, "repainted": False,
                    "inputCropRgbaSha256": source_crop_hash, "outputCropRgbaSha256": output_crop_hash,
                }
                result["targetEdgeContacts"] = edge_contacts(target)
                result["output"] = {"file": relative(target_path, root), "sha256": file_hash(target_path),
                                    "rgbaSha256": sha256(target.tobytes()), "canvas": list(target.size)}
                manifest.update({"file": relative(target_path, root), "sha256": result["output"]["sha256"],
                                 "adaptation": result["adaptation"]})
    except (OSError, ValueError) as exc:
        checks["inputPngReadable"] = False
        result["errors"].append(str(exc))
    if target is None and target_path.exists():
        target_path.unlink()  # Remove this tool's stale candidate after a failed rebuild.
    result["master"]["sha256After"] = file_hash(master_path)
    result["input"]["sha256After"] = file_hash(source_path)
    checks["masterFileUnchanged"] = result["master"]["sha256Before"] == result["master"]["sha256After"]
    checks["inputFileUnchanged"] = result["input"]["sha256Before"] == result["input"]["sha256After"]
    checks["targetWritten"] = target is not None
    result["technicalPass"] = all(checks.values())
    result["failedChecks"] = [name for name, passed in checks.items() if not passed]
    manifest.update({"sourceMasterSha256": result["master"]["sha256Before"],
                     "inputSha256": result["input"]["sha256Before"],
                     "technicalValidation": "pass" if result["technicalPass"] else "fail"})
    return result, manifest, source, target


def silhouette(image: Image.Image) -> Image.Image:
    mask = Image.new("RGBA", image.size, (48, 52, 49, 0))
    mask.putalpha(image.getchannel("A"))
    return mask


def compare_silhouettes(images: dict[str, Image.Image | None], a: str, b: str) -> dict[str, Any]:
    first, second = images[a], images[b]
    result: dict[str, Any] = {"pair": [a, b], "method": "alpha > 0 masks bottom-centred on a common comparison canvas; no scaling",
                              "artisticVariationReview": "pending"}
    if first is None or second is None:
        result.update({"technicalPass": False, "error": "Both target canvases are required"})
        return result
    common_size = (max(first.width, second.width), max(first.height, second.height))
    def pad(image: Image.Image) -> Image.Image:
        canvas = Image.new("RGBA", common_size)
        canvas.paste(image, ((common_size[0] - image.width) // 2,
                             common_size[1] - image.height))
        return canvas
    first, second = pad(first), pad(second)
    aa = bytes(1 if value else 0 for value in first.getchannel("A").tobytes())
    bb = bytes(1 if value else 0 for value in second.getchannel("A").tobytes())
    intersection = sum(x and y for x, y in zip(aa, bb))
    union = sum(x or y for x, y in zip(aa, bb))
    difference = sum(x != y for x, y in zip(aa, bb))
    result.update({"canvas": list(first.size), "maskSha256": {a: sha256(aa), b: sha256(bb)},
                   "differentPixels": difference, "intersectionPixels": intersection, "unionPixels": union,
                   "symmetricDifferenceOverUnion": difference / union if union else 0,
                   "intersectionOverUnion": intersection / union if union else 1,
                   "identicalSilhouettes": aa == bb, "technicalPass": difference > 0,
                   "interpretation": "Nonzero difference establishes distinct masks only; meaningful architectural variation needs human review."})
    return result


def checker(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (226, 226, 218, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], 8):
        for x in range(0, size[0], 8):
            if (x // 8 + y // 8) % 2:
                draw.rectangle((x, y, x + 7, y + 7), fill=(206, 206, 199, 255))
    return image


def draw_preview(sheet: Image.Image, image: Image.Image | None, left: int, top: int,
                 box_width: int, title: str, scale: int = 1) -> None:
    draw = ImageDraw.Draw(sheet)
    draw.text((left, top), title, fill=(43, 49, 44), font=ImageFont.load_default())
    if image is None:
        draw.text((left, top + 26), "Unavailable; see validation", fill=(128, 49, 40))
        return
    preview = image if scale == 1 else image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    x = left + (box_width - preview.width) // 2
    y = top + 24
    background = checker(preview.size)
    background.alpha_composite(preview)
    sheet.paste(background, (x, y))
    draw.rectangle((x - 1, y - 1, x + preview.width, y + preview.height), outline=(111, 119, 109))


def build_sheet(root: Path, sources: dict, targets: dict, records: list[dict], *, masks: bool = False) -> Path:
    # All artwork is shown at one native pixel or exactly three nearest-neighbour pixels.
    width, source_x, target_x, enlarged_x = 874, 20, 204, 390
    heights = [max(spec["source"][1], 3 * spec["target"][1]) + 79 for spec in SPECS]
    sheet = Image.new("RGBA", (width, 70 + sum(heights)), (244, 244, 235, 255))
    draw = ImageDraw.Draw(sheet)
    title = "CANOPY VILLAGE - SILHOUETTE QA" if masks else "CANOPY VILLAGE - PROVISIONAL ART REVIEW"
    draw.text((20, 14), title, fill=(32, 46, 36))
    draw.text((20, 34), "Native source | native target | 3x nearest neighbour. Human review pending; no installation.", fill=(61, 71, 61))
    y = 70
    for spec, record, height in zip(SPECS, records, heights):
        asset_id = spec["id"]
        source, target = sources[asset_id], targets[asset_id]
        if masks:
            source = silhouette(source) if source is not None else None
            target = silhouette(target) if target is not None else None
        draw.text((20, y), f"{asset_id} | technical {'PASS' if record['technicalPass'] else 'FAIL'} | input: {record['input']['stage']} | art review pending", fill=(32, 46, 36))
        source_size = f"{source.width}x{source.height}" if source is not None else "missing"
        draw_preview(sheet, source, source_x, y + 23, 160, f"Source 1x: {source_size}")
        tw, th = spec["target"]
        draw_preview(sheet, target, target_x, y + 23, 160, f"Target 1x: {tw}x{th}")
        draw_preview(sheet, target, enlarged_x, y + 23, 460, "Target 3x: nearest neighbour", scale=3)
        y += height
        draw.line((20, y - 15, width - 20, y - 15), fill=(181, 189, 176))
    path = root / "previews" / ("silhouettes.png" if masks else "review-sheet.png")
    sheet.convert("RGB").save(path)
    return path


def write_report(root: Path, validation: dict[str, Any], manifest: dict[str, Any]) -> None:
    state = "PASS" if validation["technicalPass"] else "FAIL"
    passed_assets = sum(entry["technicalPass"] for entry in validation["assets"])
    lines = ["# Canopy Village provisional review", "", f"Technical checks: **{state}** overall; **{passed_assets}/{len(validation['assets'])}** assets pass their declared checks. Artistic approval and native readability: **pending human review**.", "",
             "[Native and 3× review sheet](previews/review-sheet.png) · [Silhouette QA sheet](previews/silhouettes.png) · [Validation details](validation.json) · [Manifest](manifest.json)", "",
             "The builder cropped transparent padding and pasted the remaining RGBA pixels at the declared canvas bottom centre. It did not resample or repaint assets. Only preview enlargements use nearest neighbour.", "",
             "| Asset | Input stage | Target | Technical result |", "| --- | --- | --- | --- |"]
    for entry in validation["assets"]:
        target = " × ".join(str(value) for value in entry["targetCanvas"])
        detail = "pass" if entry["technicalPass"] else "fail: " + ", ".join(entry["failedChecks"])
        lines.append(f"| {entry['id']} | {entry['input']['stage']} | {target} px | {detail} |")
    lines += ["", "Silhouette comparisons use the same normalized target canvases and ground alignment. A different mask is a technical difference, not a claim of sufficient architectural variation.", ""]
    for pair in validation["silhouetteComparisons"]:
        a, b = pair["pair"]
        if "differentPixels" in pair:
            lines.append(f"- {a} / {b}: {pair['differentPixels']} differing pixels; XOR/union {pair['symmetricDifferenceOverUnion']:.6f}; IoU {pair['intersectionOverUnion']:.6f}; {'identical' if pair['identicalSilhouettes'] else 'different'} mask hashes.")
        else:
            lines.append(f"- {a} / {b}: comparison failed ({pair['error']}).")
    warnings = [(entry["id"], warning) for entry in validation["assets"] for warning in entry["warnings"]]
    if warnings:
        lines += ["", "Source boundary review:", ""]
        lines += [f"- {asset_id}: {warning}" for asset_id, warning in warnings]
    errors = [(entry["id"], error) for entry in validation["assets"] for error in entry["errors"]]
    if errors:
        lines += ["", "Build failures:", ""]
        lines += [f"- {asset_id}: {error}" for asset_id, error in errors]
    lines += ["", "Limits and pending review:", ""] + [f"- {value}" for value in LIMITATIONS]
    lines += ["", "Source coordinate certainty: the canvas sizes, existing slot footprints and bottom-centre anchors are taken from `../grid-contract.md`. Visible contact points and ports have not been measured or approved. The 144 × 144 hall masters and all other sources appear at native pixel size beside their adapted canvases in the review sheet.", ""]
    (root / "review-report.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Canopy Village production directory")
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    (root / "previews").mkdir(exist_ok=True)
    (root / "previews" / "silhouettes").mkdir(exist_ok=True)
    palette, palette_metadata = load_palette(root)
    records, entries = [], []
    sources, targets = {}, {}
    for spec in SPECS:
        record, entry, source, target = inspect_asset(spec, root, palette)
        records.append(record)
        entries.append(entry)
        sources[spec["id"]], targets[spec["id"]] = source, target
        enlarged_path = root / "previews" / f"{spec['id']}-3x.png"
        silhouette_path = root / "previews" / "silhouettes" / f"{spec['id']}.png"
        if target is not None:
            target.resize((target.width * 3, target.height * 3), Image.Resampling.NEAREST).save(enlarged_path)
            silhouette(target).save(silhouette_path)
        else:
            for stale in (enlarged_path, silhouette_path):
                if stale.exists():
                    stale.unlink()
    comparisons = [compare_silhouettes(targets, "hall-a", "hall-b"), compare_silhouettes(targets, "house-a", "house-b")]
    passed = palette_metadata["exactly32UniqueColors"] and all(record["technicalPass"] for record in records) and all(pair["technicalPass"] for pair in comparisons)
    validation = {"schemaVersion": 1, "status": "provisional", "technicalPass": passed,
                  "globalChecks": {"paletteHasExactly32UniqueColors": palette_metadata["exactly32UniqueColors"]},
                  "palette": palette_metadata, "assets": records, "silhouetteComparisons": comparisons,
                  "humanReview": {"status": "pending", "artQuality": "pending", "nativeReadability": "pending", "anchorsAndPorts": "pending"},
                  "limitations": list(LIMITATIONS)}
    manifest = {"schemaVersion": 1, "name": "Canopy Village", "registryId": 3, "status": "provisional",
                "currentGameChanged": False, "integrationStatus": "not installed", "palette": palette_metadata,
                "coordinateSource": "../grid-contract.md", "humanReview": "pending", "assets": entries,
                "limitations": list(LIMITATIONS)}
    build_sheet(root, sources, targets, records)
    build_sheet(root, sources, targets, records, masks=True)
    write_json(root / "manifest.json", manifest)
    write_json(root / "validation.json", validation)
    write_report(root, validation, manifest)
    failures = {entry["id"]: entry["failedChecks"] for entry in records if not entry["technicalPass"]}
    print(json.dumps({"technicalPass": passed, "humanReview": "pending", "assetsWritten": sum(image is not None for image in targets.values()),
                      "failedAssetChecks": failures, "silhouetteComparisonsPass": all(pair["technicalPass"] for pair in comparisons),
                      "reviewReport": str(root / "review-report.md")}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
