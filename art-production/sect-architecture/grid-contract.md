# Canopy Village sprite and grid contract

This is an art-production contract for separate transparent sprites. It records the existing v79 renderer; it does not change terrain, placement, navigation, saves or the running game. Canopy Village is architectural registry ID **3** in `SECT77_NAMES`. The helper procedural branch groups IDs by `Math.floor(style / 3)`, so ID 3 receives its sacred-temple silhouette there. Later v73 wrappers normally take precedence and use tinted, type-specific `tw65Sprite` art instead. Neither path implements the requested Canopy Village identity. See also the existing `game/reports/sect-registry.md` precedence audit.

## Verified engine dimensions

The world is an **orthogonal square grid**. At camera zoom `z`, one world tile occupies `z × z` CSS pixels before the backing-canvas pixel factor. There is no diamond-grid projection, camera yaw or geometric elevation transform. The three-quarter appearance is authored inside each sprite: visible roof/platform tops, a broad front face and a narrower shaded right face. Do not rotate the whole settlement into a 2:1 isometric diamond.

Terrain and cached sect terrain artwork use **16 source pixels per tile**. `tw65Sprite` uses **32 source pixels per tile** for buildings. These are distinct sampling densities; neither is a fixed gameplay screen resolution. The original adult is about **0.85 world tile** tall. At 32 source pixels/tile this is about 27 pixels, useful as an external scale figure; the 144-pixel character atlas cell is not the building tile size.

`PLOTS[type]` is `[groundWidth, groundDepth, visualHeight]` in world tiles. The building renderer stretches the entire returned canvas into `groundWidth × visualHeight`, irrespective of transparent padding. Its source dimensions are `round(width × 32)` by `round(height × 32)`.

| Existing key | Ground footprint, tiles | Draw size, tiles | Existing sect source canvas | Canvas ground anchor, edge coordinates |
| --- | --- | --- | --- | --- |
| `house` | 2.8 × 1.8 | 2.8 × 3.1 | 90 × 99 px | (45, 99) |
| `hall` | 4.4 × 2.8 | 4.4 × 4.4 | 141 × 141 px | (70.5, 141) |
| `sectHall` | 4.6 × 2.7 | 4.6 × 4.4 | 147 × 141 px | (73.5, 141) |
| `sectAltar` | 1.8 × 1.5 | 1.8 × 2.4 | 58 × 77 px | (29, 77) |
| `sectGate` | 3.0 × 0.6 | 3.0 × 2.8 | 96 × 90 px | (48, 90) |

There is **no `gate` key** in this baseline's `PLOTS`. An unknown key falls back to `house`; do not claim that a generic gate has a separate existing footprint. The final source dimensions above include rounding: their scale is approximately, rather than exactly, 32 pixels/tile.

For an engine building stored at tile `(x, y)`, its rendered ground point is `((x + 0.5) × z, (y + 1) × z)`. Its draw rectangle is `((x + 0.5 - width/2) × z, (y + 1 - height) × z, width × z, height × z)`. Thus the binding point is **canvas bottom centre**, not the visible centre of the roots and not 93% of the canvas. Coordinates in the table describe canvas edges; the last actual pixel row is `height - 1`.

The `.93` ground-baseline comment inside `tw7423SectSprite` is an artwork convention and is not applied as an anchor correction by the renderer. The older `tw65Art` draws its plinth to the bottom edge and a shadow centred at `H - 3`. For new artwork, place the lowest stable root contact within the final 1–3 rows and leave only intentional lateral transparent padding. Square generation canvases must be composed into the final aspect ratio, preserving the object proportions; passing an arbitrary square directly into the existing draw slot distorts it.

## Separate asset recommendations

The first four rows are compatible *visual envelopes* for existing building slots. They are not instructions to install or substitute art in this pass. Use final canvases shown here, plus untouched larger generation masters where available. Both variations of a building share identical anchors and bridge-port positions.

| Asset | Final art canvas | Ground anchor | Suggested current slot / footprint | Required silhouette |
| --- | --- | --- | --- | --- |
| Canopy hall A and B | 147 × 141 px each | (73.5, 141) | `sectHall`, 4.6 × 2.7 tiles | One enormous living trunk bearing a ceremonial platform, at least two readable occupied levels, wraparound galleries and irregular canopy; variations alter branch structure and gallery arrangement. |
| Branch house A and B | 90 × 99 px each | (45, 99) | `house`, 2.8 × 1.8 tiles | One inhabited branch/trunk structure per sprite; A wraps a limb, B hangs below a visibly load-bearing limb. Keep roofs, woven walls, carved doors and balcony voids readable. |
| Tree shrine | 58 × 77 px | (29, 77) | `sectAltar`, 1.8 × 1.5 tiles | A small shrine carved/lashed into one living trunk; open worship niche and small timber landing. |
| Root-supported platform | 96 × 64 px | (48, 64) | Decorative module; **no current PLOTS key** | A timber deck carried by broad roots and curved braces, with an open connection at each side. |
| Straight rope bridge | 96 × 80 px | (48, 80) | Decorative 3-tile span; **no current PLOTS key** | Distinct timber treads, continuous side ropes, end posts and shallow sag. Keep its landing heights identical. |
| Trunk staircase | 64 × 112 px | (32, 112) | Decorative module; **no current PLOTS key** | Clearly supported stair winding against a trunk, visible treads and two identifiable landings. |
| Ancient forest landmark | 128 × 160 px | (64, 160) | Decorative module; **no current PLOTS key** | One old-growth tree with a distinctive crown, buttress roots and understory; no houses included. |

These are per-object sprites, not a complete village painted onto a terrain island. Keep suspended gardens, rope lanterns and lookout nests as additional small components where produced. The hall can contain its own balconies and attached rooms; it must not absorb unrelated houses, bridges, forest floor or an entire settlement background. An optional broad environmental composition belongs in the review, not in a building source PNG.

The hall's current 4.4-tile height is a real compatibility limit: a taller art canopy needs a separately declared larger render envelope in a future art adapter. Do not silently enlarge `PLOTS`, compress a tall tree until its architecture is unreadable, or imply that a larger review master already fits the existing slot.

## Platform ports and bridge alignment

Use a shared visual deck level **48 source pixels above the ground anchor** for the first elevated connection. Recommended local landing centre points are hall `(12, 93)` and `(135, 93)`; branch house `(8, 51)` and `(82, 51)`; shrine `(6, 29)` and `(52, 29)`; root platform `(0, 16)` and `(96, 16)`; bridge `(0, 32)` and `(96, 32)`. The art should expose a short clear deck edge at these points. Tree shrine ports are optional if its worship niche needs the space. Record actual measured ports if generation does not match the target; do not certify prompt coordinates as measured geometry.

For a bridge endpoint `q` and a building port `p`, align the image origins so `bridgeOrigin + q = buildingOrigin + p`. At review zoom multiply all source coordinates by the same scale. Match the walking-surface centres first; railings can overlap the landing posts by 1–2 pixels. The 96-pixel bridge is measured between its endpoints, not between canopy silhouettes. Sag belongs between the endpoints and must not lower one landing. Rotating a horizontal bridge to create another view also rotates its shading and rail geometry; author separate north/south or diagonal modules if those are required.

For the stair recommendation, identify a lower landing near `(32, 112)` and an upper landing near `(32, 64)`, a 48-pixel screen rise. This is an art alignment convention, not a derived world-height measurement. The current engine has no elevated bridge navigation graph, platform collision volume or floor-height field. A review can show convincing elevated circulation, but must not label decorative bridges or stairs as functioning walkable links.

## Foundation and occlusion constraints

Placement uses a ground rectangle distinct from the visual sprite: `left/right = x + 0.5 ± width/2`, `top = y + 0.7 - depth`, `bottom = y + 0.7`. Ordinary buildings reject overlaps with a default 0.5-tile gap. Sect room placement uses the same footprints and a 0.1-tile gap against rooms in that sect. The visual anchor is **0.3 tile below** the footprint's front edge. Root tips and contact shading should make that difference look intentional; canopy size is not a collision footprint.

Ground foundations are painted before roads, scenery and sorted actors. `architectureGround` adds a soil-toned patch around `foot = (y + 1) × z` for walkable land at `z ≥ 4`, plus a slim contact strip. Avoid an opaque square forest-floor backing or a heavy baked oval shadow in every new PNG. Use transparent exterior pixels and modest root contact shading, because a future installation would otherwise double the existing ground treatment.

Buildings and creatures are sorted by `(y + 1)`; buildings draw before creatures at equal depth. A building sprite is a single drawable object, with no per-branch depth separation. Background scene systems, including cached sect landforms and their decorative trees, draw before that sorted pass. `foregroundVegetation` additionally redraws eligible nearby scenery over the subject's clipped bounds at `z ≥ 6`; reserved plots and road tiles exclude those scenery occluders, and selected/followed people reduce that redraw's alpha to 0.58. It does not split an individual hall into front and rear canopy layers.

Therefore keep the doorway and main bridge ports visible in a single-sprite review. If actors must pass behind one root but in front of another balcony, a future renderer needs explicitly authored rear/front layers with the same anchor; a flattened PNG cannot supply that behaviour. No such renderer change is part of this art pass.

## Source evidence

- `game/baseline/Tiny-World-v79-original.html:435` — square-grid drawing, `z`, camera translation and sorted scene pass.
- `game/baseline/Tiny-World-v79-original.html:1760` — adult scale, `PLOTS`, `plot` and overlap/build-fit contracts.
- `game/baseline/Tiny-World-v79-original.html:2054` — final developed-architecture rectangle/ground anchor used through later wrappers.
- `game/baseline/Tiny-World-v79-original.html:3687` — ground foundation; `:3698` — foreground vegetation; `:3704` — building occlusion wrapper.
- `game/baseline/Tiny-World-v79-original.html:6178` — original sect plinth/contact conventions; `:6280` — 32-pixel building unit; `:6288` — registry order; `:6303` — current family grouping.
- `game/baseline/Tiny-World-v79-original.html:6346` — sect footprints; `:6486` — sect room placement; `:6520` — 16-pixel terrain and decorative-tree cache.
- `game/src/tiny-world-visual-adapter.js:69` — independent character anchor and atlas scaling. This adapter installs person/beast art, not a sect-building asset renderer.
- `prototypes/warrior-stage1-refinement/build_warrior.py:34` — the separate warrior study uses an orthographic direction approximately 30° above horizontal. This can guide artistic continuity; it is not an engine camera projection requirement.
