#!/usr/bin/env python3
"""Preserve the user's second sect brief and fill IDs 0–2 without inventing art.

The uploaded text ends during ID 5. Its bytes are kept in references; only its
five complete sections are indexed. IDs 3 and 4 gain supplemental references
while their first, longer source descriptions remain intact.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/sect-descriptions-ids-0-5-partial.txt"
REGISTRY = ROOT / "design-registry.json"
EXPECTED_SHA256 = "978d4307cc4d15a81408e78921a698dd34beafc0287fe89a4f21bdfcba5bdfc8"

NORMALIZED = {
    0: {
        "identity": "Imperial mountain fortress.",
        "landmark": "A towering medieval castle built into an enormous rocky mountain, with four substantial corner towers, elevated battlements, narrow arched windows and multiple roof levels.",
        "supportingStructures": "Separate barracks, armouries, guardhouses, stables, a training courtyard, residences, defensive towers and a fortified gatehouse with a functional portcullis.",
        "terrain": "Massive stone walls follow mountain contours; winding cobblestone roads, broad stone stairways and fortified bridges connect distinct elevation levels.",
        "palette": "Weathered grey stone, dark-blue slate, dark iron, red and gold banners.",
        "signatureSilhouette": "A large castle compound with towers of different heights, substantial battlements and defensive walls climbing an enormous mountain.",
        "additionalArchitecture": ["Individually detailed stone blocks, iron reinforcement and multiple roof levels form the castle. Walls must follow natural mountain contours rather than a decorative rectangle."],
        "materialDetails": ["Weathered grey stone blocks", "Dark-blue slate roofs", "Iron reinforcements", "Red-and-gold ceremonial banners"],
    },
    1: {
        "identity": "Sacred monastery among towering mountain peaks.",
        "landmark": "The main meditation hall occupies the highest accessible summit among several separate, dramatic rock peaks.",
        "supportingStructures": "Prayer pavilions, monk residences, bell towers, secluded cultivation chambers and open-air meditation platforms.",
        "terrain": "Tall, irregular fractured mountains and vertical cliffs; suspended wooden bridges, narrow stone walkways and long stairs connect peaks, while waterfalls descend into mist-filled valleys.",
        "palette": "Pale stone, dark timber, weathered turquoise roofing and restrained gold ornamentation.",
        "signatureSilhouette": "Several elevated monasteries on separate mountain peaks connected by dramatic bridges.",
        "additionalArchitecture": ["Gracefully curved tiled roofs, ornamental ridge decorations, carved wooden balconies, exposed supporting beams and hanging bells."],
        "materialDetails": ["Pale stone", "Dark timber", "Weathered turquoise roof tiles", "Restrained gold ornamentation"],
    },
    2: {
        "identity": "Industrial fortress of blacksmiths and weapon makers.",
        "landmark": "A large reinforced main forge hall with a steep charcoal roof, thick stone walls, iron-framed windows and glowing furnace openings.",
        "supportingStructures": "Separate miners' quarters, workshops, weapon-storage buildings, smithing platforms, coal warehouses and cooling basins.",
        "terrain": "Ore-rich mountains, excavated rock faces, mine entrances and stone industrial yards; roads wide enough for ore carts and narrower workshop walks.",
        "palette": "Soot-blackened brick, dark iron, rusted metal, brown timber, copper and orange furnace light.",
        "signatureSilhouette": "A dense industrial complex with huge furnaces, tall chimneys and mechanical structures.",
        "additionalArchitecture": ["Giant mechanical hammers, smelting chambers, ore-processing equipment, overhead gantries, furnace towers and imposing brick chimneys remain separate architectural elements."],
        "materialDetails": ["Soot-blackened brick", "Dark iron and rusted metal", "Brown timber and copper", "Orange furnace light"],
    },
}


def main() -> None:
    source_bytes = REFERENCE.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != EXPECTED_SHA256:
        raise RuntimeError("The preserved second brief changed; inspect it before merging")
    content = source_bytes.decode("utf-8")
    headings = list(re.finditer(r"(?m)^## (\d+)\. ([A-Z ]+) \(ID (\d+)\)", content))
    sections = {}
    for index, heading in enumerate(headings):
        identifier = int(heading.group(3))
        body = content[heading.start():headings[index + 1].start() if index + 1 < len(headings) else len(content)]
        paragraphs = [part.strip() for part in re.split(r"\r?\n\r?\n", body) if part.strip()]
        sections[identifier] = {
            "heading": heading.group(0).removeprefix("## "),
            "paragraphs": paragraphs[1:],
            "rawText": body,
            "document": str(REFERENCE.relative_to(ROOT)),
            "documentSha256": source_hash,
            "complete": "**Signature silhouette:**" in body,
        }
    if set(sections) != set(range(6)) or not all(sections[i]["complete"] for i in range(5)) or sections[5]["complete"]:
        raise RuntimeError("Unexpected section boundaries or completeness")
    registry = json.loads(REGISTRY.read_text())
    if len(registry["registry"]) != 30:
        raise RuntimeError("Expected 30 preserved sect labels")
    for identifier, normalized in NORMALIZED.items():
        entry = registry["registry"][identifier]
        if entry["id"] != identifier or entry["source"] not in (None, sections[identifier]):
            raise RuntimeError(f"ID {identifier} is already authored differently")
        entry.update(normalized)
        entry["source"] = sections[identifier]
        entry["briefStatus"] = "user-supplied-intended-design"
        entry["productionTargets"]["designWorkStatus"] = "brief-recorded-art-production-pending"
        entry["productionTargets"]["note"] = "Full definition supplied in the second user document. Artwork and functional navigation remain pending."
    for identifier in (3, 4):
        entry = registry["registry"][identifier]
        if entry["id"] != identifier:
            raise RuntimeError("Registry IDs shifted")
        entry["supplementalSources"] = [sections[identifier]]
    registry["counts"].update({"suppliedFullBriefs": 30, "pendingFullBriefs": 0})
    registry["additionalSourceDocuments"] = [{
        "path": str(REFERENCE.relative_to(ROOT)),
        "sha256": source_hash,
        "authority": "User-supplied architectural descriptions",
        "completeBriefIds": list(range(5)),
        "truncatedBriefId": 5,
        "use": "Primary source for IDs 0–2; supplemental source for IDs 3–4. The partial ID 5 section does not replace the complete first brief.",
    }]
    registry["labelReconciliation"]["status"] = "All 30 ID/name pairs match v79; all 30 now have a full user-supplied intended design across two preserved documents."
    registry["labelReconciliation"]["note"] = "The existing v79 registry preserves implementation facts. The artwork design registry keeps both user sources distinct; no gameplay or sect style is changed."
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"fullBriefs": 30, "newFullBriefIds": [0, 1, 2],
                      "supplementalIds": [3, 4], "partialPreservedId": 5}))


if __name__ == "__main__":
    main()
