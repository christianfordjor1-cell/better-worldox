# Canopy Village PixelLab visual findings

This is a provisional **ID 3 art review**, not a complete sect or a new game build. The source is the user's Canopy Village brief in `../design-registry.json`. The nine current master PNGs were generated through the authenticated PixelLab MCP service. `masters/` preserves the generated pixels; `palette-normalized/` applies a fixed 32-colour palette without resampling; `assets/` places visible pixels on documented review canvases. `iterations/` preserves the first, trunk-mounted house B that failed the hanging design, alongside the corrected PixelLab result.

## What the pictures establish

- [Overview](previews/overview.png): nine separate buildings and landmarks at 2× nearest-neighbour size. The halls have different construction: A wraps galleries around one huge trunk; B spans two unequal trunks with a long raised gallery. The residences differ structurally: one is trunk-mounted, one hangs from ropes below a branch.
- [Native and 3× comparison sheet](previews/review-sheet.png): source and adapted PNGs beside nearest-neighbour enlargements. [Silhouette sheet](previews/silhouettes.png) isolates the contours. Hall masks differ in 7,909 pixels; residence masks differ in 3,433 pixels on common comparison canvases. These measurements do not certify artistic quality.
- [v79 at 16 pixels per terrain tile](previews/v79-in-memory-16px.png) and [32 pixels per tile](previews/v79-in-memory-32px.png): temporary in-memory draw overrides in an isolated Chromium test world. The two hall silhouettes and tree-based construction remain visible at ordinary zoom. Small details on the residences, shrine and gateway compress at ordinary zoom. No game files or persistent user saves were changed.

## Technical results and limits

All nine deliverable asset PNGs are transparent with binary alpha and use colours from the declared 32-colour palette. Canvas placement does not resample or trim visible art; the shrine's four-pixel cleanup is documented separately below. Eight match their proposed existing game slot canvases. The hanging house is **96 × 99** versus the current **90 × 99** house canvas, so its technical slot check fails. Its overhead branch touches the source top and left edges and may be visually clipped. The browser probe compresses it to the game's current house width and therefore does **not** prove it is ready for integration.

The shrine originally exceeded its slot by one pixel in height. Four isolated root-tip pixels at y=78 were removed manually in the normalized candidate; `masters/tree-shrine.png` retains the original and `palette-normalization.json` records every changed coordinate. There is no interpolation or illustration downscaling.

The bridge and stairs are separate objects, but their visible ends have not been measured against building ports or proven connected. The current v79 renderer has ground-based building sorting and no elevated walking graph; the hanging house and branch paths have no functional navigation. At ordinary zoom the surrounding autumn terrain is much brighter than the forest sprites, so final scene art direction needs a full settlement composition review. Growth-stage variation, independent hanging-house access, building foundations on varied terrain, and the other 29 sect families remain pending.

Generation cost was **15 existing free PixelLab trial generations**: 6 for the first hall, then 9 one-generation Pixen jobs, including one rejected residence iteration that was corrected. The connected account reported **$0.00 credits** and no purchase was made. This package does not contain the account credential or private API responses.
