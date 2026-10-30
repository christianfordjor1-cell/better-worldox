# Intended sect architecture designs

## PixelLab visual review: Canopy Village (ID 3)

The [Canopy Village overview](canopy-village/previews/overview.png) shows nine actual PixelLab-generated transparent PNGs: two structurally different halls, a trunk residence, a hanging residence, a shrine, gateway, rope bridge, trunk stairs and an independent ancient tree. The [native-size and 3× sheet](canopy-village/previews/review-sheet.png) and [isolated v79 browser captures](canopy-village/browser-probe.json) show the assets at source size, nearest-neighbour enlargement and in the current game's rendering scale.

Read the [visual findings](canopy-village/visual-review.md), [technical validation](canopy-village/review-report.md), [asset manifest](canopy-village/manifest.json) and [exact PixelLab generation receipts](canopy-village/receipts/) before considering integration. The current game and published environment settings were not changed. The artwork is provisional. One hanging house requires width correction and attachment design; elevated traversal and settlement-growth variations are still absent.

The first set used 15 generations already present in the connected free PixelLab trial, with no credit purchase. The free generation allowance is now exhausted for this session. The other 26 supplied architectural styles remain in the design registry for staged production when free generation capacity becomes available. Full briefs for IDs 0–2 are pending from the user.

[design-registry.json](design-registry.json) records the user's intended designs for the 30 preserved architectural labels. It contains 27 complete supplied briefs, from Canopy Village (ID 3) through Floating Archives (ID 29). Citadel (ID 0), Sky Monastery (ID 1) and Iron Foundry (ID 2) await their full briefs; their authored fields remain `null`.

All supplied IDs and names match [the preserved v79 registry](../../game/reports/sect-registry.json) exactly. The preservation registry describes the implementation already present in v79. This directory describes the intended artwork and does not certify existing workshop assets or alter game code or published settings.

Each supplied entry preserves its exact heading, paragraphs and raw source text, alongside consistent `identity`, `landmark`, `supportingStructures`, `terrain`, `palette` and `signatureSilhouette` fields. Additional architectural and material details are retained separately. `sourceDocument` identifies the uploaded source and its SHA-256 hash. Concatenating entries 3–29 `source.rawText` with `technicalArtStandard.rawText` reproduces the source document exactly.

Every entry carries production targets for a principal hall, residential architecture, specialty structures, entrance structures, environmental decorations and functional navigation assets. At least **two meaningful architectural variations**, plus **settlement-growth variations**, are required for each design. Variations must change shapes, arrangements and construction details. The source does not prescribe a growth-stage count; the actual stages and variations still need to be authored. All targets are explicitly uncompleted, and `completedAssets` is empty. Artwork produced alongside this registry needs its own asset manifest and quality review before any target can be marked complete.

## Required technical art standard

Every architectural sprite must use a single consistent shallow three-quarter perspective, with a clear view of the roof and front façade. The lighting direction, outline thickness, pixel density, shadow treatment and material palettes must match across the entire project.

Buildings must be authored as properly scaled sprites, while complete settlements are assembled from independent parts aligned to the game's world grid. A multi-building sect must never be flattened into one small hall sprite.

At minimum, every sect type requires a principal hall, residential architecture, specialty structures, entrance structures, environmental decorations and functional navigation assets. Large landmarks such as mountains, enormous trees and waterfalls require their own world-aligned layers.

Individual sprites require transparent backgrounds and carefully defined ground anchors. Foundations must meet the real terrain. Large decorative masses cannot conceal traversable roads or entrances.

Every design should support at least two meaningful architectural variations, plus settlement-growth variations. These must change shapes, arrangements and construction details rather than merely adjusting colours.

Final quality requirement: When shown without colour, the Citadel, Sky Monastery, Canopy Village, River Delta and all other sects must still be recognisably different. When shown in the actual game at ordinary zoom, roofs, entrances, streets, major structures and characters must remain visually coherent.

These are the intended designs—not a claim that the existing workshop assets already meet the specification.
