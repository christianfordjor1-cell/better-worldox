# Tiny World — Phase 1 concept review

Every image in this package is CONCEPT ART, not a functional production sprite, animation sheet or interchangeable anatomical PNG layer. No game version was created and no game code or saves were modified.

## Review files

- eight-designs-concepts.png: eight original character/beast designs together. Generated inset scale sketches are illustrative, not exact resampling.
- modular-anatomy-concepts.png: proposed wolffolk and dragon anatomy, alternate forms, attachment sites and garment separation. Drawn part examples are not validated aligned layers. Some labels and examples require production cleanup.
- scale-review.html: standalone, offline review page. Shows the same eight main illustrations placed in 144 x 144 concept cells, alongside exact 3x nearest-neighbour enlargements. Open in a browser.
- native-and-enlarged-review.png and 01 through 08 scale previews: browser-rendered copies of those comparisons.
- preview-validation.json: eight designs loaded without browser errors; every enlarged RGBA value checked against its source pixel (5,971,968 comparisons).

## Scale assumptions and limits

Proposed character heights: human warrior 100 px, elf 105 px, dwarf 85 px, orc 110 px, wolffolk 105 px, cultivator 100 px. Wolf 85 px and dragon 124 px are provisional study sizes. Feet anchor y=130; horizontal centre x=72. Raster artwork is scaled into these cells; these are not hand-refined production pixel clusters. Artwork retains its illustrated background.

Native means the proposed asset cell at 1x. Actual gameplay screen size depends on camera zoom and the latest renderer, which is unavailable. Perspective, fine details, outlines, final limited palettes, transparent layers, and anatomy continuity still require production review. Resampling exposes loss of fine detail; it is not conversion to production-ready pixel art.

## Proposed anatomy contract

Wolffolk: torso, head/skull, muzzle/face, eyes/markings, ears, coat/fur, left/right arm segments, paw hands, digitigrade leg segments, paw feet and tail; separate fitted front/back garments, cloak, quiver and bow.

Dragon: torso, neck, head, eyes, horns, crest, left/right independent wings, four articulated legs/claws, tail/tip, base scales, markings and accents. Wings are separate from forelimbs.

Attachments: per-species, per-direction and per-frame coordinates for neck, shoulders, elbows, wrists/grips, hips, knees/hocks, feet, tail root and wing roots. Compatibility must constrain age, build, body proportions, garments, equipment clearance and tint channels. Direction-sensitive draw order and garment fits must be tested, not inferred from this illustration.

Existing seeded identities must map to compatible asset choices without adding mandatory fields or regenerating stored identities. Drawn variants suggest options only. No schema changes have been implemented.

No sect registry or named sect type was invented. The cultivator's robe palette and decorative motifs do not declare a sect identity. No elemental-root collection was created.

## Approval boundary

Await visual feedback on these concepts. No full sprite pack, production modular prototype, animation, game integration or later phase is authorized by this delivery. Integration requires the latest authoritative source.
