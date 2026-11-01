# Three sect PixelLab art review

Nine separate PixelLab-generated transparent PNGs across Citadel, Sky Monastery and Iron Foundry. Artwork is provisional and no game files were changed.

[Overview](previews/overview.png) · [Native and 3× view](previews/native-and-3x.png) · [Hall silhouettes](previews/silhouette-comparison.png) · [Validation data](validation.json) · [Manifest](manifest.json)

Technical canvas checks: **9/9 pass**. These checks do not approve art quality or in-game navigation.

| Asset | Intended canvas | Review canvas | Source colors → 32-color family palette | Fit |
| --- | --- | --- | --- | --- |
| citadel-hall-a | 147×141 | 147×141 | 75 → 23 | pass |
| citadel-gatehouse | 96×90 | 96×90 | 59 → 19 | pass |
| citadel-mountain | 160×160 | 160×160 | 83 → 26 | pass |
| sky-monastery-hall-a | 147×141 | 147×141 | 76 → 27 | pass |
| sky-monastery-peak | 128×160 | 128×160 | 67 → 20 | pass |
| sky-monastery-bridge | 96×80 | 96×80 | 47 → 25 | pass |
| iron-foundry-hall-a | 147×141 | 147×141 | 31 → 25 | pass |
| iron-foundry-furnace-tower | 96×128 | 96×128 | 56 → 30 | pass |
| iron-foundry-workshop | 106×109 | 106×109 | 46 → 30 | pass |

Source-edge contacts, exact checks and file hashes are recorded in `validation.json`. All palette-normalized inputs preserve source alpha exactly; placing art in review canvases preserves every visible RGBA pixel without resampling. Source edge contact may indicate PixelLab clipping and needs visual review.

Three older 48×48 account objects were examined but were too small and generic for these designs; they are not included or counted.

Remaining scope: independent residences, more specialty buildings, meaningful architectural and growth variations, mountain and bridge attachment measurements, collision/path support, native game-scale composition and art approval.
