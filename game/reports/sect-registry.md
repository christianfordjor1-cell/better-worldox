# Preserved v79 sect architecture registry

The authoritative v79 contains **30 named architectural style labels**. These are not a verified registry of 30 gameplay sect types. The labels are declared once and are not referenced elsewhere in the baseline. The definitions that actually run are procedural code, not a prose description attached to each name. The table below records that code without inventing meanings for the names.

The styles combine **ten helper sprite families × three profiles**, **four real terrain families**, **eight footprint configuration bands**, **eight palettes**, and **four physical building-list archetypes**. They are more than recolours: terrain, mountain footprints and proposed building lists vary. They are also less than 30 separately authored architectures. Later v73 rendering normally bypasses the ten-family helper and uses detailed type-specific `tw65Sprite` artwork recoloured for each sect.

The 30 elemental roots remain a separate registry. No roots have been renamed or treated as sect types.

| ID | Exact existing label | Helper sprite family | Profile | Real terrain family | Configuration |
|---:|---|---|---:|---|---:|
| 0 | Citadel | masonry fortress | 0 | fortress | 0 |
| 1 | Sky Monastery | masonry fortress | 1 | sanctuary | 0 |
| 2 | Iron Foundry | masonry fortress | 2 | forge | 0 |
| 3 | Canopy Village | sacred temple | 0 | ranger | 0 |
| 4 | Step Pyramid | sacred temple | 1 | fortress | 1 |
| 5 | Cliff Dwellings | sacred temple | 2 | sanctuary | 1 |
| 6 | Crystal Spires | factory | 0 | forge | 1 |
| 7 | River Delta | factory | 1 | ranger | 1 |
| 8 | Watch Fortress | factory | 2 | fortress | 2 |
| 9 | Sun Basilica | tree dwellings | 0 | sanctuary | 2 |
| 10 | Steamworks | tree dwellings | 1 | forge | 2 |
| 11 | Living Grove | tree dwellings | 2 | ranger | 2 |
| 12 | Mesa Stronghold | pyramid | 0 | fortress | 3 |
| 13 | Moon Observatory | pyramid | 1 | sanctuary | 3 |
| 14 | Copper Mill | pyramid | 2 | forge | 3 |
| 15 | Root Sanctuary | cliff network | 0 | ranger | 3 |
| 16 | Obsidian Keep | cliff network | 1 | fortress | 4 |
| 17 | Desert Ziggurat | cliff network | 2 | sanctuary | 4 |
| 18 | Glass Conservatory | crystal spires | 0 | forge | 4 |
| 19 | Hanging Gardens | crystal spires | 1 | ranger | 4 |
| 20 | Castle of Blades | crystal spires | 2 | fortress | 5 |
| 21 | Star Lanterns | river / stilt settlement | 0 | sanctuary | 5 |
| 22 | Volcanic Kilns | river / stilt settlement | 1 | forge | 5 |
| 23 | Mangrove Homes | river / stilt settlement | 2 | ranger | 5 |
| 24 | Storm Bastion | domed civic hall | 0 | fortress | 6 |
| 25 | Crescent Shrine | domed civic hall | 1 | sanctuary | 6 |
| 26 | Mechanical Yard | domed civic hall | 2 | forge | 6 |
| 27 | Mushroom Commune | sky archive / pagoda | 0 | ranger | 6 |
| 28 | Snow Ramparts | sky archive / pagoda | 1 | fortress | 7 |
| 29 | Floating Archives | sky archive / pagoda | 2 | sanctuary | 7 |

## What each definition means

Profile 0 draws the family default. Profile 1 adds a hanging lamp at the right; profile 2 adds an illuminated left post and a right vertical post. Individual families also change tower, chimney, step, ledge, spire, pilaster or storey counts with profile. Some families reuse their main structural drawing and rely on the global profile details for differentiation. Snow and eight colourways are independent switches.

- **Helper family 0: masonry fortress.** Broad masonry body with battlements, 2 + profile roofed towers and a central arch.
- **Helper family 1: sacred temple.** Tall roof and central tower; 3 + profile pilasters; roof peak rises with profile.
- **Helper family 2: factory.** Asymmetric masonry works with 2 + profile chimneys, gabled wing and lit windows.
- **Helper family 3: tree dwellings.** Two raised timber rooms and a connecting bridge; profiles 1 and 2 add a central tree.
- **Helper family 4: pyramid.** 4 + profile stepped levels with a glowing summit and three dark entrance openings.
- **Helper family 5: cliff network.** Carved cliff silhouette, 3 + profile ledges and openings; profiles 1 and 2 add a roof.
- **Helper family 6: crystal spires.** Mineral foundation and 3 + profile polygonal spires with alternating heights.
- **Helper family 7: river / stilt settlement.** Two roofed buildings on stilts connected by decking over a blue water strip.
- **Helper family 8: domed civic hall.** Large polygonal dome, 3 + profile pilasters and an arched entrance.
- **Helper family 9: sky archive / pagoda.** 2 + profile stacked roofed storeys, central tower and three lit windows.

All helper building types reuse the same family drawing scaled to the original building canvas dimensions; the helper does not contain 30 distinct hand-authored versions of every building. The older `TW65ART` route does contain dedicated artwork functions for building types, including sect hall, altar and gate.

## Terrain and mountain generation

`tw64Plan` selects `sectStyle = (hs >>> 13) % 30`, where `hs` hashes the sect name. The terrain family is `sectStyle % 4`:

- **0: fortress.** Broad stepped citadel with paired bastions, defensive gatehouse extensions and upper cliff posts. Three-tier base half-widths: `[13, 11, 9]`; two-tier fallback: `[12, 9]`.
- **1: sanctuary.** Shrine landform with paired ceremonial side courts, upper side chapels and a four-tile approach. Three-tier base half-widths: `[12, 7, 10]`; two-tier fallback: `[11, 8]`.
- **2: forge.** Asymmetric seven-tile industrial wing and tall narrow summit crest; bottom tier gains two extra half-width tiles. Three-tier base half-widths: `[14, 10, 6]`; two-tier fallback: `[13, 7]`.
- **3: ranger.** Separated side lookout platforms with narrow branch paths. Three-tier base half-widths: `[11, 7, 11]`; two-tier fallback: `[10, 9]`.

Each family retains stacked hall ground, walkable terraces, cliffs and alternating switchback stairs. Widths, jagged edges, entry side, trees and rock details depend on other seed bits. `floor(sectStyle / 4)` selects configuration 0–7, changing side path length, elevation and bank treatment; configurations 2–7 also add an upper annex. These are real terrain tiles included in placement safety checks. Style labels do not consistently describe the selected helper family or terrain family; that mismatch is preserved rather than silently corrected.

`tw64Find` searches safe walkable land, avoids coasts, existing sect ground, buildings and dungeons, and checks full generated footprints and region access. Carving tries three terraces and falls back to two. `shape` is declared but unused.

## Physical buildings and construction

Buildings use registered engine types and real `PLOTS`, `G.bld`, ownership, collision and construction machinery. All archetypes propose a gate and ancestral hall. The four building-list vocabularies are:

- **Fortress:** houses, barracks, ranges, towers and blacksmith, with additional summit towers and altar.
- **Sanctuary:** houses, temples, ranges and altars, with temple/altar summit.
- **Forge:** multiple blacksmiths, houses, towers and barracks, with blacksmith/tower/altar summit.
- **Ranger:** houses, ranges and temples, with temple/altar summit.

The exact per-tier building lists and priorities are preserved in `sect-registry.json`. These are proposed lists; best-fit packing and later construction determine which buildings physically exist.

A named style does **not** fix one building vocabulary. Building style uses `(hs >>> 13) % 8`, whereas the architectural label uses `% 30`. Thus even architectural IDs can use fortress or forge lists, and odd IDs can use sanctuary or ranger lists, depending on seed. The separate eight-entry theme pool currently has `replaces = 0`, so it does not replace buildings.

## Which renderer actually appears in the game

The earlier `sectstyleNcolorM` wrappers call `tw7423SectSprite`, whose ten families produce 30 different helper silhouettes. Later v73 wrappers take priority:

1. `buildingRace` recognises an existing sect room and assigns `v73:<sect.name>`.
2. `tw65Place` writes that same identity for newly constructed sect buildings.
3. `migrate` updates existing sect buildings without moving them.
4. `styleSprite` calls the dedicated `tw65Sprite(type, snow, seededVariant)` and applies a persistent sect-specific palette transform.

The v73 identity also stores independent site, plan, doctrine and architectural-description strings. Those descriptors do not implement 30 separate generators. Normal rendering therefore preserves detailed per-building art and faction colours, but does not normally display the 30-style helper silhouettes. This is an existing precedence issue, not a new integration change.

## Validation and preservation

An isolated Chromium run of the untouched baseline rendered `sectHall` through `tw7423SectSprite` for all 30 style IDs with the same palette and snow setting. All **30 pixel hashes differed**. Direct `tw64Plan` calls for all 30 IDs also returned terrain and proposed building data. The JSON records those hashes and the plan probe. This confirms executable helper differences; it does not prove that all are active normal-render architectures or unique gameplay sect types.

Preserve the exact numeric order, palettes, seed formulas, `mt.sectStyle`, `mt.colorVariant`, `mt.snow`, terrain tiles, room records, building styles and `v73Identity` data. This report does not rename sects, remap saves, regenerate mountains or relocate structures.

Source references in the untouched baseline:

- Lines 6285–6341: labels, palettes and helper sprite families.
- Lines 6343–6351: terrain/building registration and initial rendering wrappers.
- Lines 6357–6418: terrain families and configuration rules.
- Lines 6419–6470: building lists, inactive theme substitutions and plot packing.
- Lines 6471–6489: safe site selection, carving and original building-style assignment.
- Lines 6852–6904: v73 identity and later rendering override.

Authoritative source SHA-256: `83bc95867919490989d76beeea785a542f7af6496eef2f952a15fb05431de3eb`.
