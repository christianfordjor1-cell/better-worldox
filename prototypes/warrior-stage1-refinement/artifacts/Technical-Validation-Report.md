# Stage 1 refinement — technical validation

**20 of 20 recorded checks passed. Artistic approval remains pending.**

| Property | Measured result |
|---|---|
| Native sprite | 144 × 144 RGBA |
| Visible figure height | 100 px |
| Lowest outlined boot contact | y=130 |
| Body origin projection | x=72.000009 |
| Visible colours | 46 |
| Partial-alpha pixels | 0 |
| Palette definitions | Unchanged from first prototype |
| Authored native pixel changes | 11 |

| Check | Outcome |
|---|---|
| exact 144x144 rgba | PASS |
| binary alpha no partial pixels | PASS |
| background transparent | PASS |
| empty pixels have zero rgb | PASS |
| declared discrete palette only | PASS |
| palette definitions unchanged | PASS |
| no colours outside original palette | PASS |
| fully inside cell | PASS |
| visible bottom pixel at y130 | PASS |
| figure height 100 pixels | PASS |
| body root projection x72 | PASS |
| orthographic camera | PASS |
| no armature | PASS |
| no animation actions | PASS |
| no ground plane | PASS |
| single connected silhouette | PASS |
| nearest neighbour 6x all pixels exact | PASS |
| nearest neighbour 3x all pixels exact | PASS |
| first prototype files unchanged | PASS |
| repeat native render identical | PASS |

The native sprite is sampled directly from original Blender geometry at 144 × 144. Semantic material ramps select discrete colours. No reduced concept illustration or automatic palette quantisation is used. Any explicit native cleanup is recorded in the included source file.

The high-resolution Blender-model PNG uses normal render filtering. Binary-alpha and no-antialiasing results apply to the native sprite and its exact nearest-neighbour previews.

The comparison reference is presentation material only. The previous model and sprite are preserved unchanged. Technical passes do not establish professional artistic quality or compatibility with animations and interchangeable anatomy.

No rigging, animation, colour variants, compositor, sprite viewer, mass production or game integration is implemented. This is a revised Stage 1 visual candidate awaiting user review.
