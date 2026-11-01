#!/usr/bin/env python3
"""Generate six distinct support sprites only when free quota covers the batch."""
from __future__ import annotations

import base64
import json

from pixellab_client import call
from run_planned_three import PRIVATE, ROOT, finish, free_available, job_id


NAMES = (
    "citadel-gatehouse", "citadel-mountain",
    "sky-monastery-peak", "sky-monastery-bridge",
    "iron-foundry-furnace-tower", "iron-foundry-workshop",
)


def recipe(name: str) -> dict:
    return json.loads((ROOT / "requests" / f"{name}.json").read_text())


def main() -> int:
    (ROOT / "masters").mkdir(parents=True, exist_ok=True)
    (ROOT / "receipts").mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        if (ROOT / "masters" / f"{name}.png").exists():
            continue
        submission = PRIVATE / f"{name}-submit.json"
        if submission.exists():
            result = json.loads(submission.read_text())
            if not result.get("isError"):
                finish(name, job_id(result), recipe(name)["tool"])
    missing = [name for name in NAMES if not (ROOT / "masters" / f"{name}.png").exists()]
    available = free_available()
    if available < len(missing):
        print(json.dumps({"status": "waiting-for-free-quota", "missing": missing,
                          "freeGenerationsAvailable": available, "needed": len(missing),
                          "purchasedCreditsUsed": False}))
        return 2
    for name in missing:
        request = recipe(name)
        tool = request["tool"]
        if tool not in {"create_image_pixen", "edit_image_pixen"} or request["expectedFreeGenerations"] != 1:
            raise RuntimeError("Unbudgeted support recipe")
        arguments = dict(request["arguments"])
        if tool == "edit_image_pixen":
            arguments["image_base64"] = base64.b64encode((ROOT / request["sourceFile"]).read_bytes()).decode()
        result = call(tool, arguments, timeout=55)
        (PRIVATE / f"{name}-submit.json").write_text(json.dumps(result, indent=2) + "\n")
        if result.get("isError"):
            raise RuntimeError(f"PixelLab rejected {name}; no credit purchase attempted")
        job = job_id(result)
        print(json.dumps({"name": name, "status": "queued", "job": job}), flush=True)
        finish(name, job, tool)
    print(json.dumps({"status": "six-support-source-sprites-ready-for-art-and-grid-validation",
                      "purchasedCreditsUsed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
