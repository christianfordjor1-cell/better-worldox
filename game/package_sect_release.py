#!/usr/bin/env python3
"""Create the self-contained playable release archive after all browser checks pass."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import json

ROOT = Path(__file__).resolve().parent
RELEASE = ROOT/'releases/sect-art-01'
OUTPUT = ROOT/'releases/Tiny-World-v79-Provisional-Sect-Art-Update-01.zip'
HTML = 'Tiny World v79 — Provisional Sect Art Update 01.html'
ASSETS = (
    'citadel-hall-a', 'citadel-gatehouse', 'citadel-mountain',
    'sky-monastery-hall-a', 'sky-monastery-peak', 'sky-monastery-bridge',
    'iron-foundry-hall-a', 'iron-foundry-furnace-tower', 'iron-foundry-workshop',
)
SCREENSHOTS = ('0-citadel.png', '1-sky-monastery.png', '2-iron-foundry.png')
REPORTS = ('build.json', 'sect-art-validation.json', 'browser-validation.json',
           'gameplay-regression.json', 'performance.json')


def main() -> None:
    build = json.loads((RELEASE/'build.json').read_text())
    assert sha256((RELEASE/HTML).read_bytes()).hexdigest() == build['playableHtmlSha256']
    for report in REPORTS[1:]:
        assert json.loads((RELEASE/report).read_text())['passed'], f'Cannot package failed check: {report}'
    assert {p.stem for p in (RELEASE/'assets').glob('*.png')} == set(ASSETS)
    files = [RELEASE/HTML, RELEASE/'README.md', *(RELEASE/r for r in REPORTS),
             *(RELEASE/'assets'/f'{name}.png' for name in ASSETS),
             *(RELEASE/'screenshots'/name for name in SCREENSHOTS),
             ROOT/'src/provisional-sect-art-01.js', ROOT/'build_sect_release.py']
    assert all(p.is_file() for p in files)
    with ZipFile(OUTPUT, 'w', compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            name = str(path.relative_to(RELEASE)) if path.is_relative_to(RELEASE) else 'source/'+path.name
            info = ZipInfo(name, (2026, 11, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=6)
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files)
        assert not any('canopy' in name.lower() for name in archive.namelist())
    print(json.dumps({'zip': str(OUTPUT), 'bytes': OUTPUT.stat().st_size,
                      'sha256': sha256(OUTPUT.read_bytes()).hexdigest(), 'files': len(files)}))


if __name__ == '__main__':
    main()
