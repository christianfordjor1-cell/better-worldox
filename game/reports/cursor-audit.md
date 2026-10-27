# Cursor sprite-pack assessment

The uploaded `kingdom-sprites.zip` contains usable PNG rendering infrastructure and a broad provisional asset catalogue. Its existing adapter is **not safe to install unchanged** into authoritative v79: the final v79 renderer repeatedly installs non-writable sprite functions, and saved appearance is nested in v79 identity objects rather than the flat fields that adapter reads. The development adapter must resolve those contracts without changing simulation data.

The PNG artwork is legacy/provisional. This audit validates file structure and implementation behavior; it does not approve the art as finished, hand-refined production artwork. The Blender warrior remains a separate prototype.

## What exists

| Contract | Actual supplied value |
| --- | --- |
| Sheets | 713 indexed transparent PNGs |
| Logical frames | 256,396 cells across all rows |
| Cell / sheet width | 144 × 144 / 2016 pixels |
| Registration point | nominal body centre x=72, ground y=130 |
| Poses | idle, six walk poses, attack, alternate idle, hurt, fallen, three work/cast poses |
| Facing | three-quarter south; horizontal mirroring only |
| Citizen appearance races | 19, each child/adult/elder |
| Shared outfit anatomy fits | human, elf, dwarf, orc × three ages = 12 fit groups |
| Beast appearance species | 17, each baby/adult |
| Class rows | 15 gameplay families plus civilian |
| Specialisation / weapon entries | 48 / 21 |
| Elemental root effects | 30; these are not sect architectural types |
| Cultivation branch robes / visual tier rows | 6 / 6; not new progression mechanics |

Citizen layers separate whole preposed body, facial overlay, eyes, hair, beard, outfit, specialisation overlay, back item, ornament and weapon. Body includes torso and limbs together. Facial overlay is not an independently articulated or interchangeable head rig. Beast-folk share the human torso/limb fit, with racial features baked into body/face/hair. The pack does **not** provide independent wolf muzzles/ears, dragon wings/horns, spider limbs, or every species' anatomy as a full interchangeable rig.

Beast layers separate tail, whole body, pattern, crest, accent, eyes and ancient mark. Eye rows reuse the same mask and select colours. Horns/wings and body structures remain baked into the preposed body where applicable. They must not be advertised as independently articulated modules. Source artwork uses Pillow integer-grid polygons and discrete drawing primitives, rather than imported concept-art downsampling; this also means the assets do not establish the approved high-quality Blender art target.

## Independent file validation

All 713 files were decoded and checked against `manifest.json` rather than trusting the supplied `validation.json`.

- Every SHA-256 matches the manifest.
- Every image has the declared width, height, row count and 144-pixel grid.
- All 713 images are palette-indexed PNGs. Used alpha values are exactly 0 and 255.
- The largest used palette contains 11 colours including transparency. Colour counts match all sheet metadata.
- No visible pixel touches any outer or internal 144-pixel cell boundary across the 713 sheets.
- All 600 tintable sheets use neutral greys in visible pixels. Transparent palette pixels are black.
- Idle body bottom alignment: **486 of 490 body rows** have their lowest visible pixel at y=130. Snake baby/adult end at y=129; spider baby ends at y=128 and adult at y=127. The nominal anchor remains (72,130), but the supplied report's blanket `allBodyFeetAnchoredAt130` claim is too broad. No uploaded PNG was changed to hide these exceptions.
- Manifest-generated plans: all 7,296 combinations of citizen race × age × class × sex × build reference valid sheet rows. All 476 beast species × age × frame plans reference valid rows.

The alignment check concerns idle bodies. Walk, lifted, attack and fallen poses do not promise a planted foot in every frame. Technical alpha/grid correctness is not evidence that animation is artistically convincing or that anatomy separates without seams.

## Corrected compositor

`game/src/kingdom-compositor.js` retains the public methods `identity`, `citizenLayers`, `beastLayers`, `compose`, `preload`, `cell`, `hash`, `revision` and `stats`. It reads the unchanged supplied manifest and real PNGs. It adds `manifest`, `limits`, `validateManifest()`, `diagnostics()` and `resetFailures(paths)`.

Corrections relative to the supplied compositor:

1. Validate manifest shape, catalogue keys, sheet dimensions, declared rows, safe paths, mask flags and palette metadata before attempting composition.
2. Validate individual row accesses and clamp/normalise frame indices and numeric variation values.
3. Coalesce repeated requests into one promise per pending sheet-row. Repeated render calls do not append unbounded resolver arrays.
4. Bound both pending sheets and pending rows. Decode one full PNG at a time; retain only requested row strips afterward.
5. Give image loads a 15-second timeout and record errors. Failed sheets remain failed until an explicit `resetFailures()` call, avoiding endless network/decode retries.
6. Check decoded image dimensions against the manifest. Surface failure details to the caller instead of permanently returning an unexplained incomplete result.
7. Use bounded LRU caches: 48 row strips, 384 cells, 256 completed composites. Completed composite keys do not contain a global revision number, so loading an unrelated PNG does not invalidate every rendered actor.
8. Skip allocating a new output canvas when a completed composite is already cached. Extract requested tinted cells as individual preload rows resolve, reducing eviction while unrelated rows load.
9. Restrict recolouring to sheets declared tintable. Preserve source PNGs and dark outlines, and compute all RGB channels using the original source shade.
10. Accept known case-insensitive class/specialisation/root keys while keeping unknown classes on a reported civilian fallback.

Maximum retained pixel storage estimated by these caches is **108,822,528 bytes (103.78 MiB)**. This is a canvas-cache bound, not a measurement or bound for the entire browser process. One decoded 2016×9216 PNG can temporarily require another 70.875 MiB, plus browser image internals, embedded asset strings, game canvases and other memory.

Failure/coalescing probe: 10,000 repeated compositions of the same unloaded eight-layer human plan produced eight pending rows and eight sheet requests. Simulated failures settled every promise; a further 1,000 compositions started no new requests. The syntax check and manifest-plan enumeration also pass. End-to-end browser rendering, gameplay performance and save/import regressions are reported separately for the integrated build.

`compose(plan, hidden)` returns `{canvas, ready, failed, failures, pending, plan}`. `preload(plan)` waits for its requested row loads and returns the same result shape; callers should check `ready` because failures, queue pressure or concurrent cache eviction can leave a result incomplete. An incomplete or failed PNG render should use the preserved legacy renderer rather than make an actor disappear.

## Integration boundaries

- Read nested existing appearance and cultivation data into temporary render snapshots; do not rewrite race, seed, age, equipment, saved identity or progression while rendering.
- Preserve unregistered species and class behavior. An asset-catalogue entry is not proof that the authoritative game's spawn/biology rules exist for it.
- Resolve v79's configurable renderer locks deliberately. Do not repeatedly fight legacy installers with another permanent timer.
- Preserve dungeon/embarked visibility, actor ground coordinates, selection marks and inspector aspect ratio.
- Keep six visual tier rows separate from actual cultivation progression and preserve all 30 elemental root definitions.
- Preserve the 30 named architectural style definitions independently of root effects and the six robe branches.
- Future anatomy rigs, additional directions, truly interchangeable species anatomy and higher artistic quality require further asset work; this integration cannot manufacture those qualities from the supplied sheets.

## Browser cache stress check

A headless system Chromium page loaded the actual external PNG sheets and this corrected compositor, then rendered 20 varied citizen identities through six walking frames. It requested the currently visible frame every 40 ms, advanced the walk column every 130 ms and coalesced in-flight preloads per identity/frame. This is a compositor stress probe, not an integrated-game FPS measurement.

- At 1 second, 9 of 20 current-frame composites were ready; at 2 seconds, 16 were ready; by 3 seconds, all 20 were ready.
- The 120 completed identity/frame combinations remained available through the end of the 22-second run.
- Actual PNG load attempts stopped at 61 by 3 seconds and remained at 61 through 22 seconds. No continuing decode thrash occurred after warmup in this case.
- Caches stabilised at 48 raw rows, 384 cells and 120 completed composites, below the stated bounds.
- No JavaScript errors or sheet-load failures occurred.

The integrated adapter should preserve a last complete frame or use legacy art while a new identity/pose loads. Very large numbers of distinct visible appearances or simultaneous preview requests can exceed these finite caches; the cache bounds intentionally do not promise unlimited high-resolution animation at zero memory cost.
