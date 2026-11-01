#!/usr/bin/env python3
"""Build the three-approved-sect release from the complete, untouched v79 modular HTML."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'dist/Tiny-World-v79-Modular.html'
REVIEW_ZIP = ROOT.parent/'art-production/Tiny-World-Three-Sect-PixelLab-Review.zip'
RELEASE = ROOT / 'releases/sect-art-01'
ART = RELEASE / 'assets'
OUTPUT = RELEASE / 'Tiny World v79 — Provisional Sect Art Update 01.html'
SOURCE_SHA256 = '5dc749ce392bdb4495efbb9311a611ef65859e05af5f10a394beff2ffa636c9a'
REVIEW_ZIP_SHA256 = '1684f1dfb05fcc10ab943d7e7139cb78e9fc8793557430e00e51062c257b1c4c'
NAMES = (
    'citadel-hall-a', 'citadel-gatehouse', 'citadel-mountain',
    'sky-monastery-hall-a', 'sky-monastery-peak', 'sky-monastery-bridge',
    'iron-foundry-hall-a', 'iron-foundry-furnace-tower', 'iron-foundry-workshop',
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    assert sha(source_bytes) == SOURCE_SHA256, 'Authoritative modular v79 changed; inspect before building'
    assert sha(REVIEW_ZIP.read_bytes()) == REVIEW_ZIP_SHA256, 'Approved PixelLab review ZIP changed'
    html = source_bytes.decode('utf-8')
    capture_after = "raceBuilding=function(c,type,i,z){const x=i%G.W,y=i/G.W|0,race=buildingRace(i),[w,d,h]=PLOTS[type]||PLOTS.house,m=structure(i),im=developedArchitecture(type,race,m?.level||0,i%2);c.drawImage(im,(x+.5-w/2)*z,(y+1-h)*z,w*z,h*z)};"
    assert html.count(capture_after) == 1
    html = html.replace(capture_after, capture_after + '\nwindow.TW79_CORE_DEVELOPED_ARCHITECTURE=developedArchitecture;window.TW79_CORE_ARCHITECTURE_SPRITE=architectureSprite;')
    # Retire the source code that manufactured the rejected sect sprite packs.
    # Keep the 30 names, landforms, building lists and gameplay rules intact.
    def strip_visual_code(begin: str, end: str, replacement: str) -> None:
        nonlocal html
        assert html.count(begin) == 1 and html.count(end) == 1, (begin, end)
        start, finish = html.index(begin), html.index(end)
        assert start < finish
        html = html[:start] + replacement + '\n' + html[finish:]
    strip_visual_code('function tw65Art(', 'const TW65ART={',
                      '/* Retired provisional sect pixel geometry. */')
    strip_visual_code('const TW65ART={', 'function tw65Sprite(',
                      '/* Retired provisional sect building sprite table. */')
    strip_visual_code('function tw65Sprite(', '// Section silhouettes are drawn into dedicated sprite canvases',
                      "function tw65Sprite(type,snow,variant){return window.TW79_CORE_ARCHITECTURE_SPRITE(type,'human',variant)}")
    strip_visual_code('\nfunction tw7423SectSprite(', '/* ---- v65: sect mountain',
                      "function tw7423SectSprite(type,snow,variant,style){return window.TW79_CORE_ARCHITECTURE_SPRITE(type,'human',variant)}")
    strip_visual_code('function tw65Paint(', 'function tw64Draw(',
                      '/* Retired procedural sect terrain overlay. */')
    strip_visual_code('function tw64Draw(', '/* v45: direct woodcutter harvest',
                      'function tw64Draw(){}')
    # These four tiny embedded sect-hut PNGs belong to a retired procedural
    # visual route. Removing their literal data URLs keeps them out of release.
    html, removed = re.subn(r'const sectHutUrls=\[.*?\];', 'const sectHutUrls=[];', html)
    assert removed == 1, f'Expected one retired sect-hut bundle, found {removed}'
    title = 'Tiny World v79 — Provisional Sect Art Update 01'
    html = html.replace('<title>Tiny World v79 — Modular Development Build</title>', f'<title>{title}</title>', 1)
    assert f'<title>{title}</title>' in html
    manifest = json.loads((ROOT.parent/'art-production/sect-architecture/planned-three/manifest.json').read_text())
    approved = {item['id']: item for item in manifest['assets']}
    assert set(approved) == set(NAMES)
    assert {p.stem for p in ART.glob('*.png')} == set(NAMES), 'Release asset folder must contain precisely nine approved PNGs'
    pngs, boxes, source_hashes = {}, {}, {}
    for name in NAMES:
        data = (ART/f'{name}.png').read_bytes()
        assert sha(data) == approved[name]['sourceSha256'], f'Approved PixelLab master mismatch: {name}'
        with Image.open(ART/f'{name}.png') as image:
            assert image.mode == 'RGBA', f'{name} must retain transparency'
            box = image.getbbox()
            assert box, f'{name} has no visible artwork'
            boxes[name] = {'canvas': image.size, 'visible': box}
        pngs[name] = 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
        source_hashes[name] = sha(data)
    adapter = (ROOT/'src/provisional-sect-art-01.js').read_text()
    assert '</script' not in adapter.lower()
    assert html.count('</body>') == 1
    injection = ('\n<script>\nwindow.TW_SECT_PIXEL_PNGS=' + json.dumps(pngs, separators=(',', ':'))
                 + ';window.TW_SECT_PIXEL_BOXES=' + json.dumps(boxes, separators=(',', ':'))
                 + ';\n</script>\n<script>\n' + adapter + '\n</script>\n')
    html = html.replace('</body>', injection + '</body>')
    RELEASE.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html)
    report = {'release': title, 'baseline': str(SOURCE.relative_to(ROOT)),
              'baselineSha256': SOURCE_SHA256, 'playableHtml': OUTPUT.name,
              'playableHtmlSha256': sha(OUTPUT.read_bytes()),
              'approvedReviewZipSha256': REVIEW_ZIP_SHA256,
              'approvedAssetSha256': source_hashes, 'approvedSectIds': [0, 1, 2],
              'otherSectIds': '3–29 retain original v79 default building rendering',
              'originalBaselineUnchanged': sha(SOURCE.read_bytes()) == SOURCE_SHA256}
    (RELEASE/'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'html': str(OUTPUT), 'bytes': OUTPUT.stat().st_size,
                      'sha256': report['playableHtmlSha256'], 'pngs': len(pngs)}))


if __name__ == '__main__':
    main()
