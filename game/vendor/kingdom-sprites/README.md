# Tiny World — modular pixel layers

Open **Sprite-Workshop.html** to preview citizens, beasts and sect cultivators offline. Open **Tiny-World-Modular-Sprites.html** to play the uploaded game with the new PNG compositor. Neither file needs a server or internet connection. The ZIP contains editable, transparent PNG sheets, the manifest, compositor, adapter and reproducible source.

## Sheet contract

Every PNG is 2016 pixels wide, divided into fourteen **144 × 144** cells per row. No gutters, labels, grids, backgrounds or borders are present in the assets. The common registration point is **(72, 130)**. Transparent pixels have alpha 0 and visible pixels alpha 255. Curves, lighting and luminous effects use discrete pixels; there is no antialiasing, filtering, gradient or blurred glow. PNG palettes contain at most 32 colours, including transparency. Light comes from the upper left.

| Column | Pose |
| --- | --- |
| 0 | Idle |
| 1–6 | Six walk poses |
| 7 | Attack |
| 8 | Alternate idle / blink |
| 9 | Hurt |
| 10 | Fallen / death |
| 11–13 | Work / cast poses |

These are three-quarter, south-facing sprites suitable for an overhead map. Mirroring supplies the opposite horizontal facing. North-facing and four/eight-direction animation sets were not specified and are not included. The fixed registration point is unchanged in lifted poses and the shared fallen transformation; the feet do not stay planted during every animation.

## Contents

- 19 citizen races: human, elf, dwarf, orc and all 15 requested beast-folk.
- Each race has child, adult and elder body, face and head-style sheets. Both body sexes and four builds are included. Child geometry is 70% of its race's adult geometry; elders have forward, lowered heads and shoulders.
- Body heights before hairstyles: approximately human 100px, elf 105px, dwarf 85px and orc 110px. Hats, horns, antlers and weapons extend outside those body measurements, within the cell.
- Four face variants, four eye shapes, ten head styles and five beard states (none, short, full, long, braided). Elf ears, orc tusks, dwarf brows and species anatomy are included.
- 15 class outfits plus civilian clothes, fitted to every sex/build/race size/age. Magic Knight uses the game's `spellblade` key.
- All 48 specialisation keys found in the uploaded game. The six ranger overlays use its exact keys: `sniper`, `bowblade`, `beastmaster`, `dualRanger`, `trapper`, `magicRanger`.
- 21 weapon/tool types cover the 15 general weapons and all 12 cultivation weapons, with shared types reused. All follow the same right-hand socket; bow is stylised for a small overhead sprite, rather than a separate two-handed aiming rig.
- Six ornament states (earring, necklace, scar, tattoo, brooch, none); cape, quiver and banner back layers.
- Civilian clothing plus an independent kingdom-colour tunic.
- Six sect branch robes, 30 distinct element-root loops and six increasingly elaborate tier aura rows. Six tiers are an explicit art-pack choice; the prompt did not specify a tier count. The adapter clamps larger tier values to the final row.
- 17 beast species, baby/adult: body, five pattern states, four crest states, four tail states, four eye rows, four accent states and an ancient mark. Crest 0 and pattern 0 are plain. Eye rows share an eye mask and are recoloured with four eye colours; eye colour remains independently selectable. Baby geometry is 60% of adult geometry.

The 144px cell is a registration canvas, not a promise to fill it. Rabbit and bird species use smaller native silhouettes. The ancient mark and auras use crisp concentric motifs and sparks instead of soft glow.

## Manifest and rows

`manifest.json` is authoritative. Its `sheets` dictionary records path, dimensions, row keys, mask status, colour count and SHA-256. `races[race][age]` supplies race anatomy and identifies a body fit in `fits`.

Outfits, eyes, beards, ornaments, weapons and back layers are shared across compatible anatomy. All beast-folk use the human torso/limb fit so all outfits stack; their head anatomy is race-specific. Elf, dwarf and orc have their own complete fit sets. Shared fitting avoids shipping repeated identical images for every beast-folk race.

Body row: `sex * 4 + build`, where sex is 0 male or 1 female and build is 0 thin, 1 normal, 2 broad, 3 heavy.

Multi-variant layer row: `variant * 8 + bodyRow`. Large layers are paged every eight variants to keep sheet dimensions below browser limits. For a paged descriptor:

```js
const page = Math.floor(variant / descriptor.variantsPerPage);
const path = descriptor.pages[page];
const row = (variant % descriptor.variantsPerPage) * 8 + sex * 4 + build;
```

Beast sheets use one row per phenotype value, without sex/build rows. All fourteen poses are always in the same columns. Root aura columns 0–6 form a seven-frame loop; the remaining columns supply compatible action poses.

## Tint masks

Tintable sheets use neutral greys: dark outline, dark detail, shadow, base and highlight. Outline/detail pixels below shade 70 stay dark. For a selected RGB tint, the compositor maps each neutral shade `s >= 70` to `min(255, round(tintChannel * s / 176))`. Transparent pixels remain transparent. The source PNG is never modified. The manifest contains 8 skin, 4 orc-green, 8 hair, 4 eye, 4 material and 7 class palette choices. Material tint subtly modifies class colour. Weapons, ornaments, ancient marks and root/tier effects keep their original palettes.

Recommended stack: tier aura, root aura, back, body, outfit, tunic/robe, specialisation, face, eyes, hair, beard, ornament, held weapon. See each compositor plan for the exact active stack. Armour and hats intentionally cover some anatomy and hair. For unusually tall head styles, choose a compatible hat/style combination in the workshop.

## Using the compositor

Load `manifest.js`, set `globalThis.KINGDOM_PNGS` to a path-to-data-URL dictionary if desired, then load `compositor.js`. Without that dictionary, paths are relative to the hosting page; serve the pack directory over HTTP when reading pixels for tinting. The provided standalone HTMLs embed their assets and avoid local-file canvas restrictions.

```js
const plan = KingdomSprites.citizenLayers(person, 'adult', 7, '#739caf');
const { canvas } = await KingdomSprites.preload(plan);
context.imageSmoothingEnabled = false;
context.drawImage(canvas, x - 72, y - 130);
```

`KingdomSprites.beastLayers(beast, 'adult', frame)` returns a beast plan. `compose(plan, hiddenLayerNames)` supports layer isolation. Rendering uses existing PNGs, not character geometry drawn in JavaScript. Whole-sheet decoding is queued two images at a time, then reduced to requested row strips. Row strips, tinted cells and composites have bounded caches.

The Tiny World adapter reads direct identity fields and the optional `spriteIdentity` / `visualIdentity` objects. Existing values take priority. Missing visual fields get deterministic values derived from the existing citizen/creature ID, without modifying saves or consuming simulation randomness. `acc` is supported as the old ornament field and `speciesForm` maps uplifted animals to beast-folk.

The adapter changes visual rendering only. It does not add new gameplay classes, sect progression or species that are absent from the uploaded game. All assets can be previewed in the workshop regardless of whether that species or cultivation system exists in the current game. Existing embarked/dungeon display handling is preserved. Other scenery, monsters without a requested counterpart, UI and game systems remain in the original HTML.

## Source and validation

`build_sprites.py` uses Pillow and explicit integer-grid polygons to author the source pixels, with no image model, resampling, antialiasing or image upscaling. Change its `OUT` constant before rebuilding in another location. Python 3 and Pillow are required; the source uses the standard library otherwise. The export pass losslessly indexes the resulting PNGs and verifies round-trip equality.

`validation.json` records asset checks and browser smoke-test results. The workshop offers a frame PNG export and an identity JSON export.
