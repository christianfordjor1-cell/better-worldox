# Tiny World v79 — modular development build

This is the existing playable v79 game with a replaceable PNG rendering layer and save-startup protection. Development branch: `development/v79-modular-integration`. No paid software or services are required.

## Play

Download [Tiny-World-v79-Modular.html](dist/Tiny-World-v79-Modular.html) and open it in a modern browser. The approximately 49.6 MB HTML contains all 713 PNG sheets and works offline; no server, installation or asset download is required. Initial opening and first-use sprite decoding can take a moment.

Embedded assets were browser-tested with all later network requests blocked. This cloud browser blocks `file://` navigation by policy, so direct double-click launching could not be verified here. If your browser restricts local files, run `python -m http.server 8000` in the extracted package folder, then open `http://localhost:8000/dist/Tiny-World-v79-Modular.html`.

The **Art: provisional PNG** button switches between the supplied Cursor artwork and original v79 rendering. Both modes use the same simulation. Unloaded or unavailable PNGs fall back to existing artwork.

## Keep existing worlds

Before changing the game file, location, browser or hosting address, use the existing **World archive → Export current world** command and keep the resulting JSON backup. Open the updated game, then use **Import world file** if the world is not already available. Browser storage belongs to its origin; a different address or local file location may have separate storage. This build cannot read saves from another origin.

Existing save keys, archive slots and import/export formats remain in place. Destructive historical startup resets are disabled. Startup resumes the newest valid current-session record and stops automatic saving if an unreadable session cannot safely be recovered. It does not reset your world to apply new artwork. Original v79 files and the uploaded sprite pack are preserved unchanged in [baseline/](baseline/) and [vendor/kingdom-sprites/](vendor/kingdom-sprites/).

## Included and unfinished

- Rendering contracts cover **19 races and 17 beast species**, seeded appearances, independent colour channels, outfits, equipment and the fourteen existing animation slots.
- The unchanged baseline has **four mechanical races** and registers **12 of those 17 art species**. Tiger, snake, eagle, spider and crow have PNG assets but no corresponding gameplay definitions; this pass does not invent their mechanics.
- The existing **15 classes, 48 specialisations, 30 elemental roots, six branches and 1,260 techniques** remain intact. Six art-tier rows cannot represent every distinction in the nine-stage cultivation system; progression itself is unchanged.
- Cursor artwork is **provisional working artwork**. Complete preposed bodies are supplied; independently interchangeable torso, pelvis, head and limbs remain missing. Beastfolk clothing shares human fits. Directional coverage is a three-quarter view plus horizontal mirroring. Frame availability does not establish finished animation quality.
- The **30 architectural labels** are preserved separately from elemental roots. They do not establish 30 fully distinct sect architectures or gameplay types. See the [sect registry](reports/sect-registry.md) and [machine-readable definitions](reports/sect-registry.json).
- The provisional Blender warrior remains separate. No new artwork pack or main-game redesign is included.

See the [Cursor audit](reports/cursor-audit.md), [anatomy contract](reports/anatomy-compatibility.md), [game-system audit](reports/game-contract-audit.md) and [remaining production work](reports/production-roadmap.md).

## Rebuild and verify

From the repository root, using free Python 3:

```sh
python game/build.py
```

The build verifies the authoritative baseline SHA-256 and PNG checksums, then produces the offline HTML. [build.json](reports/build.json) records the output hash and explicit source patches. Baseline SHA-256: `83bc95867919490989d76beeea785a542f7af6496eef2f952a15fb05431de3eb`.

The browser checks use free Python Playwright and Chromium in isolated temporary profiles. With those installed, run:

```sh
node game/tests/test_anatomy.cjs
python game/tests/browser_validation.py
python game/tests/gameplay_regression.py
python game/tests/compositor_validation.py
python game/tests/performance_check.py
```

Tests exercise saved-world restoration, rendering, offline loading, actual import/export controls and native gameplay. Read the recorded [browser results](reports/browser-validation.json) and [gameplay results](reports/gameplay-regression.md) for the checks actually completed and their limits. These are regression checks, not proof of long-term balance or every possible world layout.

Free test dependencies are listed in `requirements-dev.txt`. Run `python -m pip install -r game/requirements-dev.txt` if needed; browser scripts use the system Chromium at `/usr/bin/chromium`. The packaged build itself needs only a browser.
