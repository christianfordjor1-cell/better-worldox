# v79 gameplay and persistence contract audit

Audited the untouched authoritative `baseline/Tiny-World-v79-original.html` on 2026-10-27. Its stale v78 title does not supersede the user's v79 authority confirmation. This report describes existing behavior; it does not introduce gameplay definitions.

## Browser evidence

Chromium opened the actual baseline in an isolated, temporary browser profile, generated its 384 × 240 world and spawned a native human. No JavaScript page exceptions occurred. The browser was paused before inspecting records. Existing user storage was never opened by the audit.

A baseline snapshot/restore round trip preserved time, dimensions, terrain, shade and the saved `person.tw79`, `creature.tw74Beast` and `creature.tw79Beast` identities. Whole-person deep equality is inappropriate: native restoration recomputes derived stats, lifespan, skills and rarity. An artificially assigned class without calling `derive()` produced those expected recomputations. Stable authored fields and saved identity records should be compared separately.

## Registries and actual coverage

| Contract | Untouched v79 behavior | Cursor manifest | Preservation/integration requirement |
| --- | --- | --- | --- |
| Citizen race mechanics | Four entries in global lexical `RACES`: human, elf, dwarf, orc (line 1010). `TW746.races` also has four (line 7185). | 19 visual race entries | Preserve all four existing mechanics and all 19 visual identities. Do not claim 19 distinct gameplay stat definitions already exist. |
| Late procedural race renderer | Nine private entries at line 7920: the four above plus sheepfolk, wolffolk, foxfolk, rabbitfolk, bearfolk | 19 visual race entries | Read original identity fields before fallback. More art coverage does not define new evolution or inheritance rules. |
| Registered actor types | 25 entries including human; 24 nonhuman | 17 beasts | Keep all existing creature registrations, including those without Cursor art. |
| Wildlife lifecycle | 14 `SPECIES` entries: sheep, wolf, deer, rabbit, boar, fox, chicken, tortoise, moonhart, emberfox, cow, cat, dog, bear | 17 beasts | Preserve existing diet, maturity, breeding and habitat rules. |
| Beast overlap | 12 Cursor species already registered: the 11 shared wildlife entries plus dragon | 17 | tiger, snake, eagle, spider and crow have art but no registered v79 creature mechanics. Preserve them in the anatomy/asset registry without inventing stats or population rules. Cow/cat/dog and monsters need existing-renderer fallback. |
| Classes | 15 global `CLS` families | 16 class rows including civilian | Civilian is an empty gameplay class, not a sixteenth trained class. |
| Specialisations | 48 global `SPECIAL` keys | 48 keys | Preserve camelCase keys and family assignments. Case-normalising lookup must return canonical manifest keys. |
| Elemental roots | 30 `tw74.ROOTS`; independently 30 lowercase `tw69.roots` | 30 | Keep roots distinct from architectural/sect types. |
| Techniques | 1,260 `tw74.TECHNIQUES` entries: 540 original + 720 later additions | Aura/root/branch visual assets | Preserve technique IDs, combat timing and existing learning state. |
| Sect architecture | 30 named style labels, grouped generation logic and later visual overrides | No sect-building replacement | See `sect-registry.md` / `.json`; preserve source definitions. |

The 15 class keys are warrior, tank, archer, mage, healer, rogue, bard, monk, engineer, alchemist, psychic, mime, gunslinger, hero and spellblade. The supplied adapter's `magic knight` alias must map to `spellblade`; a direct lowercase-only specialisation adapter loses keys such as `dragonKnight`, `natureMage` and `battlePriest`.

The 30 canonical v74 root labels are Fire, Water, Wood, Earth, Metal, Ice, Lightning, Wind, Magma, Mist, Shadow, Light, Poison, Blood, Gravity, Space, Time, Sound, Solar, Lunar, Star, Void, Soul, Dream, Illusion, Spirit, Bone, Crystal, Life and Death. v69 has a different ordering; use string matching, never positional equivalence.

The six v74 branches (Assault, Control, Defense, Movement, Cultivation, Support) belong to `tw74.TECHNIQUES[id].branch`. There is no canonical six-way per-person branch field. `person.tw74.techniques` stores technique IDs and `person.tw74.active` stores the last selected technique's name. Independent v69 `tw69Path` choices are offense/control/spirit, and older `person.path` a/b choices are class training paths. These three systems must not be conflated by the visual adapter.

## Runtime and rendering interfaces

- `window.TW79_GAME` is the reliable game export (line 7910). `window.G` is undefined; `G` exists as a global lexical binding.
- Native actor creation is `g.spawn(key, x, y, true)` and emits all existing spawn hooks. Human records are separate: `g.person(actor)` reads `g.state.people[actor.id]` (line 640). Unknown actor keys are unsafe because `spawn()` dereferences the registration.
- Actor IDs and `uid` differ. Keep them separate. Human `id` references the person record; beast `uid` is used for indexing and identity.
- `TW79.identity(person)` mutates only missing `person.tw79` identity fields. `TW79.beastIdentity(actor)` owns `tw79Beast`; the gameplay bloodline record `tw74Beast` is separate and must survive unchanged.
- A saved person's canonical sources include `race`, `speciesForm`, `tw746`, `cls`, `spec`, `roots`, `tw69Root`, `tw69Path`, `tw74`, `gear` and `tw79`. The adapter should flatten a read-only rendering snapshot instead of changing these records to fit the pack.
- Native `g.sprite(person, stage, frame, cloth)` returns an 84 × 112 portrait canvas in the last procedural renderer (line 7930). Callers include portraits, battle replays and remains, so changing its returned dimensions/aspect requires a compatibility wrapper.
- Registered creature `sprite(ctx, actor, tileScale, game)` functions render in world coordinates before camera translation.
- `humanBounds(actor, z, game)` is the final authoritative selection/contact layout. It uses rendered position `rx/ry`, child/adult sizing, trait/body scaling and the pixel grid. Its final wrapper at line 4103 rounds width/height to `g.px` units. A sampled adult at z=12 had width 8 and height 10; do not assume a full 144-pixel cell should occupy a whole tile or replace inspector hitboxes arbitrarily.
- `twBodyScale()` (line 4102) already handles giant/tiny/strong/frail traits, build and `window.twCharScale`. Preserve these visual variations.
- World contact is approximately `(rx + .5) * z`, `(ry + 1) * z`. Pack anchor is (72,130), so position using the anchor, not the full 144 × 144 transparent box's lower edge.
- Camera is lexical `cam = {x,y,z}`; `zoomAt(screenX,screenY,factor)`, `fitCam()` and `focusPoint()` are existing controls. `z` is pixels per terrain tile in logical screen coordinates, not sprite frame size. Zoom snaps using `g.px`, maximum 40 (line 1168). The main canvas has `DPR = 1/(g.px||2)` (line 323).
- `citizenActionPose(actor, game)` (line 3225) returns `{kind,frame}` with kinds idle, walk, attack, shoot, cast, work, carry or hold and frame 0–7. It uses real attack start/end, active tasks, cargo and interpolated movement. `ActionMotion.clock` freezes on pause; it should drive the pack's frame mapping.
- `g.step()` moves an actor; it is not a world simulation tick. `advanceSimulation(elapsed,budgetMs)` (line 460) advances `g.time` and all system ticks. Rendering must not advance this clock or apply damage.
- Existing v74.9 / v79 installers replace sprite properties repeatedly. At line 7895 some are configurable getters with ignored setters; at line 7993 others are nonwritable, configurable values. Direct assignment by the supplied Cursor adapter cannot reliably install. The derived build needs an explicit, bounded handoff and should preserve original functions for fallback. Reinstalling renderers every frame would create a new performance problem.

## Save protection issue in the source baseline

The source contains historical reset code which conflicts with the user's current instruction to preserve saves:

| Location | Source condition | Effect |
| --- | --- | --- |
| Lines 4051–4054 (`WIPE_FLAG`) | Active when a flag is absent | Deletes every localStorage key starting `tinyworld` and clears IndexedDB's `worlds` store. |
| Lines 4357–4361 (`TW_DOCK_RELEASE`) | Already `false && ...` | Dormant old release reset. |
| Lines 4419–4423 (`TW_STRICT_RELEASE`) | Already `false && ...` | Dormant old release reset. |
| Lines 4517–4522 (`TW_FINAL_FRESH_KEY`) | Already `false && ...` | Dormant old release reset. |
| Lines 4606–4610 (`TW_INTEGRITY_RELEASE`) | Already `false && ...` | Dormant old release reset. |
| Lines 4814–4818 (`TW_V14_RESET`) | Active when a flag is absent | Deletes `tinyworld*` and `world-*` keys and clears IndexedDB `worlds`. |

In addition, `resumeWorldOrCreate()` at line 3000 unconditionally clears the seed and generates a new world. Disabling reset loops alone cannot preserve the current session across reopening: later autosaving could replace that session with the generated world. The derived build should protect storage and resume a valid existing current-world entry before generating a world for a genuinely empty profile. Keep the baseline untouched and document these precise changes.

Do not block normal existing save-slot rollback, rotating autosave cleanup or explicit user generation controls; those are separate from historical startup wipes.

## Save/load and import/export contracts

`g.snapshot()` (line 3670) returns a JSON string with schema version 4 and keys `version,time,W,H,map,shade,cre,bld,fire,state,opts,surface,calendarTicksPerYear`. Terrain and shade use packed strings, buildings/fire become entry arrays. The large mineral proxy is unwrapped. Keep this format and existing unknown fields.

`g.restore(snapshotString)` has many native migration/repair wrappers. They restore live creatures, rebuild indices, process chronology and derived stats, repair class specialisations and emit `newworld`. Do not replace this pipeline with a custom partial loader.

Existing routes:

- `#bSave` and `#bLoad` both open the existing archive (`openOverview('saves')`, line 1985). Save slots use `saveSlot(index)`, `loadSlot(index)`, and `tinyworld-slot-N` keys. The live archive UI says 31 slots.
- `tinyworld2` is the legacy quicksave, available through the archive's legacy recovery control.
- `#session-status` calls `saveCurrentSession(true)`. Current-session storage is `tinyworld-current-session-v1` plus IndexedDB database `tinyworld-world-sessions`, object store `worlds`, key `latest`.
- A session entry is `{savedAt,revision,time,paused,speed,snapshot}`. `parseSessionSnapshot()` validates dimensions, terrain lengths, creature/building arrays and state. Preserve an invalid entry for explicit recovery; do not silently discard it.
- `exportWorld()` downloads `tiny-world-WxH.json`. World import uses the existing hidden `.panel.World input[type=file]` and calls `g.restore(text)` only after validation (lines 985–986).
- `tw52ExportCharacters(single)` downloads `{format:'tiny-world-characters',version:1,worldTime,worldSize,characters:[{creature,person}]}`. Buttons are `#tw52-export-all` and `#tw52-export-one` (line 3822).
- `tw54ImportCharacters()` creates a temporary file picker and asks for explicit confirmation. It imports only human actors, spawns natively for world-local IDs and copies person/actor data while excluding foreign family, town, sect and task links (line 3850). Saved `tw79` and `tw74` are transferred, so an adapter should preserve these seeds across new local IDs.
- Keep existing world-generation controls, `G.opts`, simulation laws, tool selection and powers. Visual mode preferences should use a new key, never overwrite a world slot.

## Cultivation and sect preservation

Nine realm entries exist after the late additions: Initiate, Apprentice, Adept, Specialist, Expert, Master, Grandmaster, Sovereign and Heavenly Sage. The original seven-realm progression and ten substages remain at lines 5168–5267; Sovereign/Sage additions and special breakthroughs occur later (line 5478 onward). Some old labels still mention five/seven ranks; those are existing UI inconsistencies and do not justify deleting later progression. Preserve `tier`, `cultStage`, foundation, debt, training, roots, manuals, qi, laws, ascension and all later wrappers.

`foundSect()`, spirit veins, contribution, department/manual systems, seclusion builders, peak construction, mountain geometry and later faction identity already operate in v79. Keep them and their saved state. Registry auditing should not regenerate existing sects or reassign style IDs.

## Actionable regression setup

Use a fresh isolated browser context and execute this setup only inside tests:

```js
const g = window.TW79_GAME;
g.paused = true;
const i = g.map.findIndex((_, i) => g.terr(i).walk && !g.bld.has(i));
const warrior = g.spawn('human', i % g.W, Math.floor(i / g.W), true);
const person = g.person(warrior);
warrior.age = adultAge(warrior) + 100;
person.cls = 'warrior'; person.tier = 2;
person.spec = 'knight'; person.preferredSpec = 'knight';
person.cultStage = 3; person.roots = ['Water'];
derive(warrior, person);
tw74.initHuman(person, warrior);
TW79.identity(person);
const wolf = g.spawn('wolf', warrior.x, warrior.y, true);
tw74.initBeast(wolf, g); TW79.beastIdentity(wolf);
const saved = g.snapshot();
g.restore(saved);
g.paused = true;
```

Assert dimensions/time/map/shade, person name/class/spec/root/stage/gear/genome, saved seeds/channels, beast bloodline and `tw79Beast`, buildings/sects and existing simulation controls. Render each pose without changing those authored fields. Test imports through actual file inputs/downloads, not only by calling restoration.

Final speed control is `tw52Speed(rate)` with rates `[1,2,3,4,5,10,25,50,100,250]`; slider `#hud-speed` ranges 0–10, where zero pauses. Space toggles pause, `+/-` zoom, `i` inspect, and right/middle drag pans. Set test pause through `tw52Speed(0)` when testing after speed selection, since the chosen-rate loop can otherwise reapply a prior speed.

Storage regression should preload sentinel quicksave/slot/autosave and current-session entries before first navigation, then reopen and verify the entries and world remain intact. Also test localStorage unavailable, IndexedDB unavailable, malformed current-session JSON and explicit recovery. Rendering failure must retain usable legacy sprites and controls.

## Checked-in baseline fixture

Run `python game/tests/baseline_fixture.py` to regenerate `tests/fixtures/v79-world.json` using the untouched baseline in a temporary Chromium context. The script hosts its own local server and never accesses the user's browser profile.

The compact 96 × 64 fixture contains four adults created through native spawning/race powers (human, elf, dwarf, orc), native warrior/knight, mage/wizard, tank/guardian and archer/sniper classes, three native wolf/deer/dragon actors, a native town, campfire and houses. Calling the existing cultivation mentoring system founded `Sect of Regression Human`; its source state records an independent site without fabricating a style or sect type. The world is paused at tick 120. `v79-world.expected.json` records authored fields and saved identities, plus original/fixture SHA-256 hashes. Dragon has no baseline `tw79Beast` entry, so its expected `tw79Beast` is null and existing `tw74Beast` is retained. The generator completed without JavaScript exceptions.
