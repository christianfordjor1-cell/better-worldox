# Technical validation — Stage 1 warrior

All 16 recorded technical checks passed. The packaged originals were checked again against the hashes in `validation.json`; each matches. The compact 3× preview was also checked pixel-for-pixel against the native PNG.

| Property | Actual result |
|---|---|
| Native image | 144 × 144 RGBA |
| Visible figure | 100 pixels tall |
| Body centre | x=72, within 0.001 px in the Blender camera |
| Bottom outlined boot contact | y=130 |
| Alpha | Only 0 and 255; zero partially transparent pixels |
| Visible colours | 51, all in declared ramps/contours |
| Large preview | 864 × 864; exact 6× nearest-neighbour |
| Compact preview | 432 × 432; exact 3× nearest-neighbour |
| Scene | 234 mesh objects, zero armatures, zero animation actions |
| Repeatability | Independent native render matched |

| Recorded check | Outcome |
|---|---|
| exact 144x144 rgba | PASS |
| binary alpha no partial pixels | PASS |
| background transparent | PASS |
| empty pixels have zero rgb | PASS |
| declared discrete palette only | PASS |
| fully inside cell | PASS |
| visible bottom pixel at y130 | PASS |
| figure height 100 pixels | PASS |
| body root projection x72 | PASS |
| orthographic camera | PASS |
| no armature | PASS |
| no animation actions | PASS |
| no ground plane | PASS |
| single connected silhouette | PASS |
| nearest neighbour all pixels exact | PASS |
| repeat native render identical | PASS |

## Interpretation

The native PNG is the actual transparent sprite. Review backgrounds and the concept illustration are not part of that asset. The separate Blender-model PNG is a filtered, high-resolution model render; the binary-alpha and pixel-grid checks apply to the native sprite.

The 3D model, native render and enlarged PNGs are actual existing Stage 1 outputs. The sprite uses direct native-resolution geometry sampling, discrete colour ramps and 17 explicitly authored facial-pixel corrections. No reduced concept illustration is used as the sprite.

**Artistic approval is still pending.** Rounder shoulder armour and simpler ornament differ from the approved Phase 1 design. Technical passes do not establish aesthetic quality, animation, interchangeable anatomy or production readiness.

No Stage 2, rigging, animation, colour-variation system, compositor, sprite viewer or game integration has been implemented.
