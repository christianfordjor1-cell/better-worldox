# Tiny World v79 — Provisional Sect Art Update 01

Open **Tiny World v79 — Provisional Sect Art Update 01.html** in a browser to play. It is the complete modular v79 game with its art embedded; the `assets/` folder contains the unmodified approved PixelLab PNG masters for inspection. The original `game/dist/Tiny-World-v79-Modular.html` is retained unchanged as a recovery copy.

Only three sect architectural IDs receive PixelLab replacements:

| ID | Sect style | PixelLab sprites used in the game |
| --- | --- | --- |
| 0 | Citadel | hall, gatehouse, mountain ridge |
| 1 | Sky Monastery | hall, mountain peak |
| 2 | Iron Foundry | hall, furnace tower, workshop |

The approved Sky Monastery bridge PNG is included as a reviewed source asset but is **not placed in the game**. v79 has no verified bridge span with matching endpoints and walkable tiles. Placing that image on an unrelated path would misrepresent movement. All other components of IDs 0–2, and every building in IDs 3–29, use the original generic v79 building renderer. The earlier generated 30-style sect sprite functions and procedural terrain overlay are retired from this release. The 30 sect IDs, existing layout generation, 30 elemental roots, gameplay data and save schema remain intact.

The three files in `screenshots/` are actual Chromium captures from the playable game at `cam.z=32`. The test uses the native world generator and native sect mountain carver to make reproducible ID 0, 1 and 2 scenes, then places their existing room types into the engine's building map. These scenes are isolated browser test worlds, not a replacement starter world or shipped save. Their generated ground and unsupported buildings retain default v79 visuals.

Validation reports are in this folder: `sect-art-validation.json` (12 checks, all 27 fallback IDs, actual asset draw counts and path movement), `browser-validation.json` (23 checks, legacy saves, offline assets and recovery), `gameplay-regression.json` (17 checks, existing systems and import/export), and `performance.json` (large-population smoke test). The managed browser blocks `file://`, so offline asset verification permitted only the initial local HTML response and blocked every subsequent network request.
