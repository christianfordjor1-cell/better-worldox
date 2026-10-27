# Playable v79 validation — 2026-10-27

**PASS:** 23 browser/save checks, 17 native gameplay checks, 15 compositor assertions, anatomy-contract unit checks and full-game performance smoke test. Chromium 154.0.8037.57; isolated temporary profiles. No normal JavaScript page exceptions.

The delivered HTML SHA-256 is `5dc749ce392bdb4495efbb9311a611ef65859e05af5f10a394beff2ffa636c9a`. The untouched authoritative v79 SHA-256 is `83bc95867919490989d76beeea785a542f7af6496eef2f952a15fb05431de3eb`. All 720 extracted Cursor files match the supplied ZIP byte for byte; all 713 PNGs independently pass checksum, grid, palette and binary-alpha validation.

## What was exercised

- Restore a real untouched-v79 fixture containing four races/classes, buildings, a sect, wolf/deer/dragon and saved identities; preserve authored values through native migrations.
- Startup keeps archive/quick/autosave keys, resumes current localStorage or IndexedDB worlds, and blocks automatic overwriting of unreadable current-world data. Browser storage unavailable: world remains playable.
- Actual archive buttons, world JSON downloads/file imports and character roster downloads/file imports. Appearance seeds survive imported local ID changes.
- Native class assignment, cultivation substage/breakthrough, combat damage/hurt timing, sect foundation and mountain carving, beast spawning, Beastmaster contracts, independent Summoner conjurations, speed slider and pause.
- Real PNGs through the game renderer, independent colour masks, fourteen frame slots, all19 race/age/frame plans, seventeen beast body images, missing-PNG legacy fallback, explicit recovery and bounded caches. "Ancient" and firearm aliases tested.
- Offline embedded assets with later network requests blocked. Direct `file://` navigation **could not be verified** because managed browser policy blocks it. Local HTTP was tested; no asset server or remote font is needed after the HTML loads.

## Performance sample

The full 96×64 game held 100 citizens and 30 beasts. On this cloud CPU, 60 paused draw samples had median 2.20 ms original / 1.70 ms provisional, p95 2.90 / 2.40 ms. These measure synchronous draw CPU time, not display FPS. One hundred live simulation ticks completed in 371.4 ms. Caches stayed bounded; cold sprites can temporarily use original artwork. Entire-browser memory and large-population walking are not bounded by this sample.

## Remaining work

Artwork is provisional, with whole preposed bodies and shared human clothing fits for beastfolk. The pack is not finished independently interchangeable anatomy. Fourteen columns yield twelve distinct human images; two walk-pass columns repeat idle. Only one three-quarter view plus mirroring exists. Snake/spider idle ground exceptions are documented.

The visual registry covers19 races and17 beasts; v79 defines four race mechanics and registers twelve of those beasts. Tiger, snake, eagle, spider and crow lack gameplay definitions and were not invented. All original creature registrations,15 classes,48 specialisations,30 elemental roots,1260 techniques and progression remain intact.

All30 architectural names and their actual shared generation rules are preserved in [sect-registry.md](sect-registry.md) and [sect-registry.json](sect-registry.json), separately from roots. They are not thirty verified distinct sect philosophies/building systems. The Blender prototype remains separate.

Detailed evidence: [browser](browser-validation.json), [gameplay](gameplay-regression.md), [compositor](compositor-validation.json), [performance](performance.json), [asset audit](cursor-audit.md). Smoke tests do not prove every ability, long-run balance, every possible save or every generated layout.
