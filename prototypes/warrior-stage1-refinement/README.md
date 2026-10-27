# Human warrior — Stage 1 visual refinement

This directory is limited to the user's requested static visual corrections. It preserves the approved Blender-to-pixel technical method and the original prototype. No rigging, animation, anatomical reconstruction, recolour system, sprite viewer, mass production or game integration is implemented.

The revised render is packaged: [open the simple visual review](artifacts/README.md) or [download Tiny-World-Warrior-Stage1-Refined-Review.zip](https://github.com/christianfordjor1-cell/better-worldox/raw/refs/heads/prototype/warrior-stage1-refinement/prototypes/warrior-stage1-refinement/artifacts/Tiny-World-Warrior-Stage1-Refined-Review.zip).

The review includes the native 144 × 144 PNG, exact 3×/6× previews, Blender-model PNG, editable `.blend`, validation report, three-way model comparison and equal-height pixel comparison. The approved concept is only a display reference; it is never fed into the geometry builder or native renderer.

## Reproduce

Free tools: Blender 4.3.2, Python and Pillow 12.3.0. Run from this directory:

```sh
blender --background --factory-startup --disable-autoexec \
  --python build_warrior.py -- --out /tmp/tiny-world-warrior-refined

blender --background --factory-startup --disable-autoexec \
  --python build_warrior.py -- --out /tmp/tiny-world-warrior-refined-repeat --skip-studio

python package_review.py \
  --build /tmp/tiny-world-warrior-refined \
  --repeat-build /tmp/tiny-world-warrior-refined-repeat \
  --out artifacts
```

The packager uses the preserved first prototype under `../blender-warrior-stage1/artifacts/` by default. It accepts explicit `--baseline` and `--reference` paths. It verifies the baseline files were not modified, checks that palette definitions are unchanged, checks native transparency and anchors, and compares every enlarged pixel with the native source.

A ZIP extraction contains the scripts under `source/`, the approved reference image, and the first-prototype comparison assets. To repackage from an extraction, pass `--baseline first-prototype --reference approved-phase1-reference.png` explicitly.

The pixel comparison displays the two actual sprite figures at their measured 100px height, with exact integer enlargement. The illustration's reduced reference study is labelled concept-only and is not a usable sprite asset.

**Artistic acceptance remains pending.** Technical passes cannot establish visual quality or readiness for later stages. Stop after the user's Stage 1 visual review.

[Shape-change report](artifacts/Changes-For-Review.md). The long-term requirements for 19 races, 17 beast species, 30 distinct sect types, 30 elemental roots and existing seeded appearances remain unchanged. No missing registry or new gameplay has been invented.
