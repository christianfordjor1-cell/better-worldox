# Canopy Village provisional review

Technical checks: **FAIL** overall; **8/9** assets pass their declared checks. Artistic approval and native readability: **pending human review**.

[Native and 3× review sheet](previews/review-sheet.png) · [Silhouette QA sheet](previews/silhouettes.png) · [Validation details](validation.json) · [Manifest](manifest.json)

The builder cropped transparent padding and pasted the remaining RGBA pixels at the declared canvas bottom centre. It did not resample or repaint assets. Only preview enlargements use nearest neighbour.

| Asset | Input stage | Target | Technical result |
| --- | --- | --- | --- |
| hall-a | palette-normalized | 147 × 141 px | pass |
| hall-b | palette-normalized | 147 × 141 px | pass |
| house-a | palette-normalized | 90 × 99 px | pass |
| house-b | palette-normalized | 96 × 99 px | fail: existingGameSlotCanvasMatches |
| tree-shrine | palette-normalized | 58 × 77 px | pass |
| root-gate | palette-normalized | 96 × 90 px | pass |
| rope-bridge | palette-normalized | 96 × 80 px | pass |
| trunk-stairs | palette-normalized | 64 × 112 px | pass |
| ancient-tree | palette-normalized | 128 × 160 px | pass |

Silhouette comparisons use the same normalized target canvases and ground alignment. A different mask is a technical difference, not a claim of sufficient architectural variation.

- hall-a / hall-b: 7909 differing pixels; XOR/union 0.561799; IoU 0.438201; different mask hashes.
- house-a / house-b: 3433 differing pixels; XOR/union 0.527100; IoU 0.472900; different mask hashes.

Source boundary review:

- house-b: Visible source pixels touch a canvas edge; inspect for intentional contacts or source clipping.

Limits and pending review:

- Provisional art-production review; no source approval or human approval is implied.
- The current game, renderer, gameplay data and published settings are unchanged; these assets are not installed.
- A palette-subset check verifies the supplied palette.json, not whether that palette or the visual result is artistically approved.
- Canvas bottom-centre anchors come from grid-contract.md. Integer placement can put an even-width object half a pixel from an odd-width canvas centre; no pixels are resampled.
- Measured architectural ports are unknown. Contract port coordinates are recommendations, not measured artwork geometry or functioning connections.
- Bridge, stairs and the landmark have no existing gameplay type or collision footprint. There is no elevated navigation implementation or functional path claim.
- Exact image bounds prove that this adaptation did not clip the input. Source edge contact is reported, but a PNG alone cannot establish whether its generating process clipped an object.
- Native-size readability, clear ground contact, perspective, lighting, architectural variation, silhouette identity and art quality require human review in context.
- The hanging house is 96 pixels wide against the existing 90-pixel house slot. Its 96x99 PNG is a review canvas, not a drop-in game asset. Its branch touches the source top and left edges, so source clipping needs artistic review.
- Four isolated bottom-edge root-tip pixels of the shrine were removed manually to fit its 58x77 slot. The original PixelLab master and exact coordinates are preserved in palette-normalization.json.

Source coordinate certainty: the canvas sizes, existing slot footprints and bottom-centre anchors are taken from `../grid-contract.md`. Visible contact points and ports have not been measured or approved. The 144 × 144 hall masters and all other sources appear at native pixel size beside their adapted canvases in the review sheet.
