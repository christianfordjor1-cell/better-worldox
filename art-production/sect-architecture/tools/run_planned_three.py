#!/usr/bin/env python3
"""Generate the three planned hall sprites only when FREE PixelLab quota covers all.

This command never purchases credits. It resumes accepted jobs before checking
for new allowance, refuses a partially funded batch, and makes no art-quality
claim. A human must inspect all three outputs before any review is published.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
import time

from pixellab_client import call


ROOT = Path(__file__).resolve().parents[1] / "planned-three"
PRIVATE = Path("/workspace/pixellab-session")
NAMES = ("citadel-hall-a", "sky-monastery-hall-a", "iron-foundry-hall-a")


def text_result(result: dict) -> str:
    return "\n".join(content.get("text", "") for content in result.get("content", [])
                     if content.get("type") == "text")


def job_id(result: dict) -> str:
    match = re.search(r"job_id:\s*([\w-]+)", text_result(result))
    if not match:
        raise RuntimeError("PixelLab did not return a job ID")
    return match.group(1)


def finish(name: str, job: str) -> None:
    start = time.monotonic()
    while time.monotonic() - start < 420:
        result = call("get_image", {"job_id": job}, timeout=55)
        (PRIVATE / f"{name}-result.json").write_text(json.dumps(result, indent=2) + "\n")
        images = [content for content in result.get("content", []) if content.get("type") == "image"]
        if images:
            if len(images) != 1 or result.get("isError"):
                raise RuntimeError(f"Unexpected PixelLab image result for {name}")
            (ROOT / "masters" / f"{name}.png").write_bytes(base64.b64decode(images[0]["data"]))
            (ROOT / "receipts" / f"{name}.json").write_text(json.dumps({
                "tool": "create_image_pixen", "job_id": job,
                "receipt": text_result(result), "isError": False,
            }, indent=2) + "\n")
            print(json.dumps({"name": name, "status": "completed", "job": job}), flush=True)
            return
        if result.get("isError") or "status: failed" in text_result(result).lower():
            raise RuntimeError(f"PixelLab generation failed for {name}")
        call("wait_for_jobs", {"timeout_seconds": 35, "min_finished": 1}, timeout=45)
    raise RuntimeError(f"Job {job} is still pending; rerun to resume it safely")


def free_available() -> int:
    balance = call("get_balance")
    if balance.get("isError"):
        raise RuntimeError("Could not verify the free PixelLab generation balance")
    text = text_result(balance)
    match = re.search(r"generations_remaining:\s*(\d+)", text)
    today = re.search(r"generations_today:\s*(\d+)", text)
    remaining = int(match.group(1)) if match else 0
    daily = int(today.group(1)) if today else 0
    return remaining if remaining else daily  # The daily count is not additive.


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
                finish(name, job_id(result))
    missing = [name for name in NAMES if not (ROOT / "masters" / f"{name}.png").exists()]
    available = free_available()
    if available < len(missing):
        print(json.dumps({"status": "waiting-for-free-quota", "missing": missing,
                          "freeGenerationsAvailable": available,
                          "neededForThree": len(missing), "purchasedCreditsUsed": False}))
        return 2
    for name in missing:
        recipe = json.loads((ROOT / "requests" / f"{name}.json").read_text())
        if recipe["tool"] != "create_image_pixen" or recipe["expectedFreeGenerations"] != 1:
            raise RuntimeError("Unbudgeted recipe")
        result = call(recipe["tool"], recipe["arguments"], timeout=55)
        (PRIVATE / f"{name}-submit.json").write_text(json.dumps(result, indent=2) + "\n")
        if result.get("isError"):
            raise RuntimeError(f"PixelLab rejected {name}; no fallback purchase attempted")
        job = job_id(result)
        print(json.dumps({"name": name, "status": "queued", "job": job}), flush=True)
        finish(name, job)
    print(json.dumps({"status": "three-source-sprites-ready-for-art-and-grid-validation",
                      "purchasedCreditsUsed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
