# Anatomy and asset compatibility

`game/src/anatomy-contract.js` provides a read-only visual sidecar, `TinyWorldAnatomy`. It does not register creatures, change combat traits, modify saves, create sprites or claim that new anatomical artwork exists.

The catalog covers the requested 19 races and 17 beasts. Biped, quadruped, avian, serpentine, eight-legged arachnid and four-legged winged dragon contracts permit different structures instead of forcing every future species onto human limbs. Snakefolk and spiderfolk expose alternative future body-plan contracts; these are extension points, not newly approved character designs. Race-specific ears, muzzles, horns, tusks, beaks, shells, wings, tails, scales and feathers are recorded as attachments. Motion names are requirements for future production, not assertions that the supplied poses achieve convincing gaits.

## What the current artwork supplies

The Cursor manifest supplies complete preposed bodies, facial overlays, hair/head details, eyes, beards, outfits, robes, specialisation details, backs, ornaments and weapons. Beast overlays supply bodies, tails, patterns, crests, accents, eyes and ancient markings. All are provisional working artwork. Pack frames expose fourteen slots and one three-quarter south view with horizontal mirroring. Slot presence alone does not establish animation quality.

The manifest explicitly states that every beastfolk outfit shares human torso/limb fits. A visible race-specific body silhouette is not independent torso, pelvis, head, arm, hand, leg, foot, muzzle, ear or wing interchangeability. Independently split anatomical artwork remains missing. `capability(kind,species,manifest)` reports these limits; it never labels the pack as production-approved or anatomically complete. The provisional Blender warrior remains a separate project and is not included by this sidecar.

## Contract and checks

All future usable parts declare `kind`, `species`, `age`, `bodyPlan`, `fit`, `slot`, `id`, `cell:[144,144]`, `anchor:[72,130]` and the exact fourteen `frames`. Optional `sex` and `build` must match the assembly. `status` is one of approved production artwork, provisional working artwork, legacy artwork or missing artwork; missing artwork cannot be assembled.

`validatePart(part,context)` checks the contract. `validateAssembly(parts,context)` additionally requires unique ids and slots, a complete body plan, and no overlay of split anatomical parts over a complete preposed body. Passing `requireSplitAnatomy:true` explicitly rejects a complete preposed body. Separate species require explicit metadata; a shared clothing fit does not authorize applying arbitrary human limbs to a beast.

Attachment metadata uses `mount:{parent:'part-id',socket:'parent-socket',socketOnPart:'child-socket'}`. Each named socket contains fourteen integer `[x,y]` pairs in the common native cell. An attachment must align in every pose. Checks reject absent sockets, mismatched pose alignment, duplicate parts and cyclic attachment ancestry. This is a full-cell preposed layer contract, not a skeletal articulation solver; poses still require authored anatomical artwork and visual seam/clipping review.

`deriveAppearance(kind,seed,saved)` creates a deterministic snapshot with separately hashed channels. Existing valid values, including zero, are preserved. Race channels are skin 0–7, hair 0–7, style 0–9, eyes 0–3, face 0–3, build 0–3, ornament 0–5 and material 0–3. Beast channels are pattern 0–4 and crest, eye, accent and tail 0–3. The function does not write missing values into saves. Colour-channel independence still depends on separate masks in the artwork; metadata cannot recover independent skin/fur or wing pixels from a flattened body.

## Validation

Run `node game/tests/test_anatomy.cjs`. The tests exercise catalog counts, snake/spider/dragon body plans, identity preservation, deterministic missing fields, age/species/anchor/slot compatibility, required anatomy, complete-body rejection and per-pose socket misalignment.

The 30 sect types, 30 elemental roots, cultivation progression, beast spawning rules and all existing gameplay definitions remain outside this anatomy contract.
