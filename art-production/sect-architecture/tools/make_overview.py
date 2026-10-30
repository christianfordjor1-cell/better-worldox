#!/usr/bin/env python3
"""Create a compact, pixel-perfect visual index of the nine review PNGs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "canopy-village"
ASSETS = [
    ("hall-a", "Principal hall A"), ("hall-b", "Principal hall B"),
    ("house-a", "Trunk residence"), ("house-b", "Hanging residence *"),
    ("tree-shrine", "Tree shrine"), ("root-gate", "Root gateway"),
    ("rope-bridge", "Rope bridge"), ("trunk-stairs", "Trunk stairs"),
    ("ancient-tree", "Ancient tree landmark"),
]


def main() -> None:
    width, card_w, card_h = 1324, 420, 380
    board = Image.new("RGB", (width, 1225), "#e9eadf")
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    draw.text((30, 16), "CANOPY VILLAGE  |  PIXELLAB ART REVIEW", fill="#182522", font=font)
    draw.text((30, 34), "Actual transparent PNG assets shown at 2x nearest-neighbour. Art approval pending.",
              fill="#365439", font=font)
    for index, (name, label) in enumerate(ASSETS):
        col, row = index % 3, index // 3
        left, top = 20 + col * 435, 64 + row * card_h
        draw.rounded_rectangle((left, top, left + card_w, top + card_h - 8), radius=7,
                               fill="#dce1d3", outline="#a6b29f", width=2)
        image = Image.open(ROOT / "assets" / f"{name}.png").convert("RGBA")
        draw.text((left + 15, top + 12), f"{label}  |  {image.width}x{image.height}  |  {name}",
                  fill="#182522", font=font)
        enlarged = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        x = left + (card_w - enlarged.width) // 2
        y = top + 38 + (324 - enlarged.height) // 2
        board.paste(enlarged, (x, y), enlarged)
    draw.text((30, 1210), "* Hanging residence is 6px wider than the current house slot; see validation report.",
              fill="#68482e", font=font)
    path = ROOT / "previews" / "overview.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
