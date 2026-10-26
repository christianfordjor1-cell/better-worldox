# Human warrior — Blender-to-pixel Stage 1

**Static visual-review candidate. Artistic approval is pending.** This delivers Stage 1 only. No armature, animation, anatomical reconstruction, colour-mask system, compositor, sprite viewer, additional character or game integration has been created.

## Inspect the actual artwork

![Approved concept, Blender model and actual pixel sprite](artifacts/comparison.png)

- [Actual transparent 144 × 144 PNG](artifacts/warrior-144.png)
- [Exact 6× nearest-neighbour enlarged PNG](artifacts/warrior-nearest-6x.png)
- [Blender model render](artifacts/blender-model-render.png)
- [Large stepped-colour mesh render](artifacts/model-stepped-render.png)
- [Comparison against the approved Phase 1 warrior](artifacts/comparison.png)
- [Light, dark and checkerboard transparency review](artifacts/transparency-review.png)
- [Editable Blender model](artifacts/warrior-stage1.blend)
- [Technical validation](artifacts/validation.json)
- [Blender scene inspection](artifacts/blend-inspection.json)
- [Download complete Stage 1 package](https://github.com/christianfordjor1-cell/better-worldox/raw/refs/heads/prototype/blender-warrior-stage1/prototypes/blender-warrior-stage1/warrior-stage1-review.zip)

The standard 768px Blender model render uses normal renderer filtering. It is a model illustration, not the pixel sprite. The binary-alpha, exact-palette and no-antialiasing results apply to `warrior-144.png`.

## What was authored

The model uses custom mesh cross-sections, contoured armour shells, overlapping plates, pleated cloth, individually shaped fingers, sculpted facial features, close-cropped curl groups, a diamond-section sword, swept crossguard, wrapped grip and small metalwork details. It uses 234 mesh objects and 60,450 render triangles. There are no armatures or animation actions.

The native sprite is sampled **directly at 144 × 144** from the Blender triangle geometry. It is not reduced from the model render or an illustration. One deterministic orthographic centre ray is used per pixel. Surface lighting selects discrete authored material colours; contact shading is hard, and there is no floor mesh or baked ground shadow. A one-pixel silhouette outline is added.

After inspecting the native face, 17 pixels were deliberately corrected for eye, brow, nose and lip readability. These edits are explicit in `pixel-cleanup.json`, use the declared colours, and are reproduced by `package_review.py`. `warrior-raw-144.png` preserves the unretouched native render for comparison. No automatic quantisation, palette dithering or image-generation tool was used.

## Technical outcome

- Exact 144 × 144 RGBA PNG.
- Body origin projects to x=72 within 0.001 px in the saved orthographic camera.
- Visible figure is 100 px tall; lowest outlined boot contact is pixel row y=130.
- Alpha values are exclusively 0 and 255; no partially transparent pixels.
- 51 visible colours, all belonging to declared material ramps or contour colours.
- Fully inside the cell, with a single connected silhouette.
- Every enlarged pixel matches its exact native source pixel.
- A second independent Blender build reproduced the same raw native pixels.

These checks establish specific technical properties. They do not establish professional artistic quality, modular compatibility, animation readiness or acceptance against the concept.

## Artistic differences to review

The model retains auburn curls, brown skin, steel armour, gold bindings, oxblood scarf/tabard, leather belt/pouches and a sword. The shoulder construction is rounder, the costume ornament is simpler and the pose is more upright than the approved illustration. Facial and engraving detail is simplified at the native 100px figure height. Those differences are visible in the comparison and remain subject to Stage 1 feedback.

Normals and lighting were corrected after the first render. Repeated shoulder bands were reduced, upper-arm plates and toe armour were added, and facial clusters were refined. No claim is made that these iterations automatically match the approved illustration's quality.

## Reproduce with free tools

Used here: Blender 4.3.2, Python 3.12 and Pillow 12.3.0. No paid software, add-ons, purchased assets or outsourced work is required. Rendering runs on the CPU.

From this directory:

```sh
blender --background --factory-startup --disable-autoexec \
  --python build_warrior.py -- --out /tmp/tiny-world-warrior-stage1

blender --background --factory-startup --disable-autoexec \
  --python build_warrior.py -- --out /tmp/tiny-world-warrior-stage1-repeat --skip-studio

python package_review.py \
  --build /tmp/tiny-world-warrior-stage1 \
  --repeat-build /tmp/tiny-world-warrior-stage1-repeat \
  --reference ../../art-review/phase-1/eight-designs-concepts.png \
  --out /tmp/tiny-world-warrior-stage1-review
```

For a standalone ZIP extraction, the included reference crop can be used with `--reference artifacts/approved-warrior-reference-crop.png --reference-is-crop` instead of the full Phase 1 sheet.

The reference image is used only to prepare the comparison board. It is never read by the geometry builder or native renderer. The comparison crop is a display aid, not a production sprite.

The raw pixel buffers are intermediates written by Blender and consumed by the packaging script. The `.blend`, scripts and PNG review outputs are included in the package. The saved Blender file opens as a static model with its camera and CPU rendering configuration.

## Scope preservation and future gates

Only `prototypes/blender-warrior-stage1/` is added on the separate `prototype/blender-warrior-stage1` branch. The main branch, existing review files, uploaded HTML and saved-world data remain untouched.

The long-term requirements for 19 races, 17 beast species, existing identity variations, 30 distinct sect types and 30 elemental roots are retained. The missing sect registry has not been invented. No future-stage assets or systems are claimed here.

**Stop at Stage 1.** Anatomical reconstruction, rigging, walking, colour variations and the compositor/viewer require the user's next approval.
