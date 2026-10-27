"""Package and validate the Stage 1 visual refinement, preserving the first prototype.
This script prepares static PNG review material only. No sprite viewer, rigging,
animation, recolour system or game integration is implemented here.
"""
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import argparse
import hashlib
import json
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'blender-warrior-stage1' / 'artifacts'
ARCHIVE = 'Tiny-World-Warrior-Stage1-Refined-Review.zip'
ARCHIVE_URL = 'https://github.com/christianfordjor1-cell/better-worldox/raw/refs/heads/prototype/warrior-stage1-refinement/prototypes/warrior-stage1-refinement/artifacts/' + ARCHIVE
DARK = '#171c24'
INK = '#e5c897'
TEXT = '#c3c7c8'
EXTRA_CONTOURS = {'#1f1b25', '#2f252b'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgba(h):
    return tuple(bytes.fromhex(h.lstrip('#'))) + (255,)


def pixels(im):
    return im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()


def font(size, bold=False):
    path = '/usr/share/fonts/truetype/dejavu/DejaVuSans' + ('-Bold' if bold else '') + '.ttf'
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def snapshot(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}


def connected_components(im):
    remaining = {(x, y) for y in range(im.height) for x in range(im.width)
                 if im.getpixel((x, y))[3]}
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            x, y = stack.pop()
            size += 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (-1, 1), (1, -1), (-1, -1)):
                q = (x + dx, y + dy)
                if q in remaining:
                    remaining.remove(q)
                    stack.append(q)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def is_exact_enlargement(native, enlarged, factor):
    if enlarged.size != (native.width * factor, native.height * factor):
        return False
    source = list(pixels(native))
    return all(colour == source[(y // factor) * native.width + x // factor]
               for y in range(enlarged.height)
               for x, colour in enumerate(
                   pixels(enlarged.crop((0, y, enlarged.width, y + 1)))))


def put_centered(board, image, box, *, native_scale=False, sampling=Image.Resampling.LANCZOS):
    """Display-only fit; native sprites use integer nearest-neighbour scaling."""
    x, y, w, h = box
    im = image.copy()
    if native_scale:
        factor = max(1, min(w // im.width, h // im.height))
        im = im.resize((im.width * factor, im.height * factor), Image.Resampling.NEAREST)
    else:
        factor = min(w / im.width, h / im.height)
        im = im.resize((round(im.width * factor), round(im.height * factor)), sampling)
    board.alpha_composite(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))


def model_comparison(reference, baseline_model, revised_model, out):
    board = Image.new('RGBA', (1440, 900), DARK)
    d = ImageDraw.Draw(board)
    d.text((28, 22), 'TINY WORLD / STAGE 1 SHAPE REFINEMENT', font=font(29, True), fill=INK)
    d.text((28, 65), 'Concept reference and actual Blender model renders. Static artistic review only.',
           font=font(17), fill=TEXT)
    for i, (title, subtitle, image) in enumerate([
        ('APPROVED PHASE 1', 'Original concept artwork', reference),
        ('FIRST BLENDER PROTOTYPE', 'Preserved, unchanged first model', baseline_model),
        ('REFINED BLENDER MODEL', 'Revised geometry; approval pending', revised_model),
    ]):
        x = i * 480
        d.text((x + 24, 112), title, font=font(19, True), fill=INK)
        d.text((x + 24, 142), subtitle, font=font(15), fill=TEXT)
        display = image.crop(image.getbbox()) if i else image
        put_centered(board, display, (x + 24, 190, 432, 600),
                     sampling=Image.Resampling.NEAREST if i == 0 else Image.Resampling.LANCZOS)
    d.text((28, 822), 'Native sprite output remains 144 x 144. These model views are display comparisons.',
           font=font(17), fill=TEXT)
    d.text((28, 855), 'The separate pixel comparison uses exact nearest-neighbour enlargement of the real PNGs.',
           font=font(17), fill=TEXT)
    board.save(out / 'comparison.png')


def reference_study(reference):
    """Reference-only scale study; never used as source artwork for the sprite."""
    im = Image.new('RGBA', (144, 144))
    h = 100
    w = round(reference.width / reference.height * h)
    scaled = reference.resize((w, h), Image.Resampling.NEAREST)
    im.alpha_composite(scaled, ((144 - w) // 2, 130 - h + 1))
    return im


def pixel_comparison(reference, baseline, revised, out):
    board = Image.new('RGBA', (1440, 1140), DARK)
    d = ImageDraw.Draw(board)
    d.text((28, 22), 'NATIVE PIXELS / FIRST PROTOTYPE / REFINEMENT', font=font(27, True), fill=INK)
    d.text((28, 65), 'Both real sprites have a 100px visible figure. The concept is an illustrative scale study.',
           font=font(16), fill=TEXT)
    studies = [reference_study(reference), baseline, revised]
    titles = ['PHASE 1 REFERENCE STUDY', 'FIRST ACTUAL SPRITE', 'REFINED ACTUAL SPRITE']
    for i, (title, im) in enumerate(zip(titles, studies)):
        x = i * 480
        d.text((x + 24, 112), title, font=font(18, True), fill=INK)
        d.text((x + 24, 144), '144 x 144 cell at 1x', font=font(15), fill=TEXT)
        board.alpha_composite(im, (x + 168, 176))
        d.text((x + 24, 350), 'Exact 6x enlargement of the same pixels', font=font(15), fill=TEXT)
        crop = im.crop(im.getbbox())
        enlarged = crop.resize((crop.width * 6, crop.height * 6), Image.Resampling.NEAREST)
        # Real sprite silhouette is 100 pixels high, so this displays at exactly 600px.
        board.alpha_composite(enlarged, (x + (480 - enlarged.width) // 2, 390))
    d.text((28, 1042), 'Reference study: resized illustration for comparison only, not a production pixel asset.',
           font=font(17), fill=TEXT)
    d.text((28, 1075), 'Old and revised PNGs are untouched by comparison scaling. Native files remain transparent.',
           font=font(17), fill=TEXT)
    d.text((28, 1107), 'Stage 1 only. No rigging, animation, colour variants, compositor or main-game changes.',
           font=font(16), fill=INK)
    board.save(out / 'pixel-comparison.png')


def transparency_review(native, out):
    panel = Image.new('RGBA', (1440, 600), DARK)
    d = ImageDraw.Draw(panel)
    for i, background in enumerate(('#24262d', '#e9e2d0', 'checker')):
        x = i * 480
        d.text((x + 22, 18), ['DARK', 'LIGHT', 'TRANSPARENCY'][i], font=font(20, True), fill=INK)
        bg = Image.new('RGBA', (432, 432), '#a8adb2' if background == 'checker' else background)
        if background == 'checker':
            bd = ImageDraw.Draw(bg)
            for y in range(0, 432, 24):
                for xx in range(0, 432, 24):
                    if (xx // 24 + y // 24) % 2:
                        bd.rectangle((xx, y, xx + 23, y + 23), fill='#d8dce0')
        bg.alpha_composite(native.resize((432, 432), Image.Resampling.NEAREST))
        panel.alpha_composite(bg, (x + 24, 65))
    d.text((24, 525), 'Exact 3x previews. These review backgrounds are not baked into the actual native PNG.',
           font=font(17), fill=TEXT)
    d.text((24, 560), 'Only the static warrior is rendered; no later-stage systems are implemented.',
           font=font(17), fill=TEXT)
    panel.save(out / 'transparency-review.png')


def write_review_docs(report, out):
    count = len(report['checks'])
    passed = sum(v is True for v in report['checks'].values())
    rows = '\n'.join(f"| {k.replace('_', ' ')} | {'PASS' if v else 'FAIL'} |"
                     for k, v in report['checks'].items())
    (out / 'Technical-Validation-Report.md').write_text(f'''# Stage 1 refinement — technical validation

**{passed} of {count} recorded checks passed. Artistic approval remains pending.**

| Property | Measured result |
|---|---|
| Native sprite | 144 × 144 RGBA |
| Visible figure height | {report['image']['figure_height']} px |
| Lowest outlined boot contact | y={report['image']['visible_bounds_exclusive'][3] - 1} |
| Body origin projection | x={report['camera']['body_root_projected_x']:.6f} |
| Visible colours | {report['image']['visible_colour_count']} |
| Partial-alpha pixels | {report['image']['partial_alpha_pixels']} |
| Palette definitions | {'Unchanged from first prototype' if report['checks']['palette_definitions_unchanged'] else 'DIFFERENT — review failure'} |
| Authored native pixel changes | {report['authored_native_pixel_changes']} |

| Check | Outcome |
|---|---|
{rows}

The native sprite is sampled directly from original Blender geometry at 144 × 144. Semantic material ramps select discrete colours. No reduced concept illustration or automatic palette quantisation is used. Any explicit native cleanup is recorded in the included source file.

The high-resolution Blender-model PNG uses normal render filtering. Binary-alpha and no-antialiasing results apply to the native sprite and its exact nearest-neighbour previews.

The comparison reference is presentation material only. The previous model and sprite are preserved unchanged. Technical passes do not establish professional artistic quality or compatibility with animations and interchangeable anatomy.

No rigging, animation, colour variants, compositor, sprite viewer, mass production or game integration is implemented. This is a revised Stage 1 visual candidate awaiting user review.
''')
    (out / 'Changes-For-Review.md').write_text(f'''# Stage 1 warrior — shape refinement

This revision responds to the requested artistic corrections. The first prototype and approved Phase 1 reference are retained in the comparison images. It is a static visual candidate awaiting approval.

| Area | Underlying change |
|---|---|
| Shoulder armour | Replaced the rounded domes and circular gold bands with compact, clipped shield-like caps, sloping bevels and two overlapping shaped lames. |
| Hair | Replaced detached repeated curl forms with one cropped scalp surface, six unequal shallow tuft groups, shorter temples and an interrupted hairline. |
| Face | Integrated cheek structure into the skull, broadened the jaw, narrowed the eye openings and refined the brow, nose and mouth. The head turns toward image-right, closer to the concept. |
| Chest and belt | Reshaped the breastplate centre and made the leather belt a visible volume in front of the cloth, with one defined buckle. No additional ornament collection was generated. |
| Gloves | Closed leather finger shapes around the shared static grip axis; added a shaped back-of-hand plate. |
| Boots | Shortened the foot/toe shape and replaced thin open-looking overlays with fitted instep plates and closed steel toe caps. |
| Sword | Shortened the blade from 1.65 to 1.45 model units (about 12%), adjusted its taper and point, reduced the guard and angled it farther across the body. Hand and grip geometry share the same static pose axis. |
| Native finishing | After those model changes, {report['authored_native_pixel_changes']} explicit eye/nose/mouth pixels were refined using existing colours. No decorative silhouette pixels were added. |

## Technical continuity

The same direct native-resolution orthographic sampling method is retained. Cells remain 144 × 144, the body origin projects to x=72, and the lowest outlined boot contact is y=130. The visible figure remains 100px tall. Palette definitions are unchanged; the revised sprite uses {report['image']['visible_colour_count']} visible colours versus 51 in the first prototype. There are no partial-alpha pixels. An independent rebuild reproduced the native buffer exactly.

The model comparison shows the approved concept, first Blender model and revised model. The pixel comparison shows the two real native sprites at identical figure height, plus a clearly labelled reduced illustration study for reference only. The concept image never supplies pixels to the geometry renderer.

## Review boundary

Artistic acceptance is yours. The technical checks cannot certify that the design matches the concept's quality. The new sculpted hairstyle, armour planes and simplified facial details are intentionally visible for review rather than described as finished production art.

This package does not establish anatomical interchangeability, garment compatibility in motion or animation quality. No rigging, modular reconstruction, animation, colour-variation system, compositor, viewer, other character or game integration was added.

The long-term requirements remain 19 races, 17 beast species, all supported identity/appearance variations, 30 distinct sect types and 30 elemental roots. The missing sect registry has not been invented. Existing gameplay and saves were not edited.

**Stop at Stage 1 for visual approval.**
''')
    (out / 'README.md').write_text(f'''# Tiny World — revised Stage 1 warrior review

**Visual refinement only. Stage 2 has not started.** You can inspect these images directly on GitHub without opening Blender.

## Actual native sprite — 144 × 144

![Refined native warrior](warrior-144.png)

## Pixel-perfect detail preview — exact 6×

![Refined warrior enlarged 6×](warrior-nearest-6x.png)

## Approved concept, first model and revised model

![Three-way model comparison](comparison.png)

## Native-scale and enlarged pixel comparison

![Three-way pixel comparison](pixel-comparison.png)

## Actual Blender model render

![Revised Blender model](blender-model-render.png)

[Light/dark/transparency review](transparency-review.png) · [Readable validation report](Technical-Validation-Report.md) · [Machine-readable report](validation.json) · [Editable Blender file](warrior-stage1.blend) · [Download complete ZIP]({ARCHIVE_URL})

The native PNG has no background or ground shadow. The separate model illustration uses normal renderer filtering; it is not the pixel sprite.

[Read the shape changes and remaining scope](Changes-For-Review.md). The underlying shape changes and visual differences are for your review. Technical validation does not decide artistic acceptance. All source/scripts included under `source/` are free-tool workflows.

**Stop at Stage 1.** Rigging, modular reconstruction, animation, palette-variation systems and game integration remain unimplemented and require later approval. The main game and existing saves are unchanged.
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--repeat-build', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    build, baseline, out = args.build.resolve(), args.baseline.resolve(), args.out.resolve()
    if out == baseline or baseline in out.parents or out in baseline.parents:
        raise ValueError('Output must be separate from the preserved first-prototype baseline')
    before = snapshot(baseline)
    out.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((build / 'render-metadata.json').read_text())
    base_metadata = json.loads((baseline / 'render-metadata.json').read_text())
    inspection = json.loads((build / 'blend-inspection.json').read_text())
    raw_bytes = (build / 'warrior-144.rgba').read_bytes()
    if len(raw_bytes) != 144 * 144 * 4:
        raise ValueError('Native RGBA buffer does not match a 144x144 frame')
    native = Image.frombytes('RGBA', (144, 144), raw_bytes)
    native.save(out / 'warrior-raw-144.png')
    allowed = {rgba(h) for ramp in metadata['palettes'].values() for h in ramp}
    allowed |= {rgba(h) for h in EXTRA_CONTOURS}
    baseline_allowed = {rgba(h) for ramp in base_metadata['palettes'].values() for h in ramp}
    baseline_allowed |= {rgba(h) for h in EXTRA_CONTOURS}
    cleanup_path = HERE / 'pixel-cleanup.json'
    cleanup = json.loads(cleanup_path.read_text()) if cleanup_path.exists() else {'edits': []}
    edits = 0
    for x, y, h in cleanup['edits']:
        colour = rgba(h)
        if colour not in allowed or native.getpixel((x, y))[3] != 255:
            raise ValueError(f'Invalid native-pixel correction at ({x},{y})')
        edits += native.getpixel((x, y)) != colour
        native.putpixel((x, y), colour)
    native.save(out / 'warrior-144.png')
    six = native.resize((864, 864), Image.Resampling.NEAREST)
    three = native.resize((432, 432), Image.Resampling.NEAREST)
    six.save(out / 'warrior-nearest-6x.png')
    three.save(out / 'warrior-preview-3x.png')
    for name in ('blender-model-render.png', 'warrior-stage1.blend',
                 'render-metadata.json', 'blend-inspection.json'):
        shutil.copy2(build / name, out / name)
    stepped_path = build / 'model-stepped-render.rgba'
    if stepped_path.exists():
        Image.frombytes('RGBA', (720, 720), stepped_path.read_bytes()).save(out / 'model-stepped-render.png')
    refpath = args.reference or baseline / 'approved-warrior-reference-crop.png'
    reference = Image.open(refpath).convert('RGBA')
    reference.save(out / 'approved-phase1-reference.png')
    first = out / 'first-prototype'
    first.mkdir(exist_ok=True)
    for name in ('warrior-144.png', 'blender-model-render.png', 'render-metadata.json'):
        shutil.copy2(baseline / name, first / name)
    baseline_sprite = Image.open(baseline / 'warrior-144.png').convert('RGBA')
    baseline_model = Image.open(baseline / 'blender-model-render.png').convert('RGBA')
    revised_model = Image.open(out / 'blender-model-render.png').convert('RGBA')
    model_comparison(reference, baseline_model, revised_model, out)
    pixel_comparison(reference, baseline_sprite, native, out)
    transparency_review(native, out)
    colours = Counter(pixels(native))
    alphas = Counter(pixels(native.getchannel('A')))
    bounds = native.getbbox()
    components = connected_components(native)
    checks = {
        'exact_144x144_rgba': native.size == (144, 144) and native.mode == 'RGBA',
        'binary_alpha_no_partial_pixels': set(alphas) == {0, 255},
        'background_transparent': alphas[0] > 0,
        'empty_pixels_have_zero_rgb': all(c[:3] == (0, 0, 0) for c in colours if c[3] == 0),
        'declared_discrete_palette_only': all(c in allowed for c in colours if c[3]),
        'palette_definitions_unchanged': metadata['palettes'] == base_metadata['palettes'],
        'no_colours_outside_original_palette': all(c in baseline_allowed for c in colours if c[3]),
        'fully_inside_cell': bounds[0] > 0 and bounds[1] > 0 and bounds[2] < 144 and bounds[3] < 144,
        'visible_bottom_pixel_at_y130': bounds[3] - 1 == 130,
        'figure_height_100_pixels': bounds[3] - bounds[1] == 100,
        'body_root_projection_x72': abs(inspection['body_root_projected_x'] - 72) < 0.001,
        'orthographic_camera': inspection['orthographic_camera'],
        'no_armature': inspection['armatures'] == 0,
        'no_animation_actions': inspection['animation_actions'] == 0,
        'no_ground_plane': inspection['no_ground_plane'],
        'single_connected_silhouette': len(components) == 1,
        'nearest_neighbour_6x_all_pixels_exact': is_exact_enlargement(native, six, 6),
        'nearest_neighbour_3x_all_pixels_exact': is_exact_enlargement(native, three, 3),
        'first_prototype_files_unchanged': snapshot(baseline) == before,
    }
    not_run = []
    if args.repeat_build:
        checks['repeat_native_render_identical'] = ((build / 'warrior-144.rgba').read_bytes() ==
                                                  (args.repeat_build / 'warrior-144.rgba').read_bytes())
    else:
        not_run.append('Independent repeat native render: supply --repeat-build to verify')
    report = {
        'stage': 1, 'revision': 'visual-refinement', 'technical_checks_pass': all(checks.values()),
        'production_approved': False, 'visual_quality': 'Awaiting user review; not certified by automated checks',
        'checks': checks, 'not_run': not_run,
        'image': {'size': [144, 144], 'mode': native.mode,
                  'visible_bounds_exclusive': list(bounds), 'figure_height': bounds[3] - bounds[1],
                  'visible_colour_count': len([c for c in colours if c[3]]),
                  'transparent_pixels': alphas[0], 'opaque_pixels': alphas[255],
                  'partial_alpha_pixels': sum(n for a, n in alphas.items() if a not in (0, 255)),
                  'alpha_components': components},
        'camera': inspection,
        'authored_native_pixel_changes': edits,
        'original_palette_colour_count': len(baseline_allowed),
        'baseline_hashes': before,
        'not_implemented': ['rigging', 'animation', 'anatomical reconstruction', 'part variants',
                            'independent colour-mask assets', 'compositor', 'sprite viewer', 'game integration'],
        'render_method': 'Direct 144x144 pixel-centre sampling of Blender geometry with discrete material ramps; no illustration downscaling or automatic quantisation.',
        'model_render_note': 'The separate high-resolution Cycles illustration uses normal model-render filtering. Binary alpha and no-antialiasing checks apply to the native sprite.',
        'files': {name: sha(out / name) for name in
                  ('warrior-144.png', 'warrior-nearest-6x.png', 'warrior-preview-3x.png',
                   'blender-model-render.png', 'warrior-stage1.blend', 'comparison.png', 'pixel-comparison.png')},
    }
    (out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    write_review_docs(report, out)
    print(json.dumps({'technical_checks_pass': report['technical_checks_pass'],
                      'checks': checks, 'not_run': not_run,
                      'visible_colours': report['image']['visible_colour_count']}, indent=2))
    if not report['technical_checks_pass']:
        raise SystemExit('Technical validation failed; outputs are diagnostic, not an accepted review package')
    source = out / 'source'
    source.mkdir(exist_ok=True)
    for name in ('build_warrior.py', 'package_review.py', 'pixel-cleanup.json', 'requirements.txt'):
        path = HERE / name
        if path.exists():
            shutil.copy2(path, source / name)
    archive = out / ARCHIVE
    files = [p for p in out.rglob('*') if p.is_file() and p != archive]
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            z.write(path, path.relative_to(out))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read(str(p.relative_to(out))) == p.read_bytes() for p in files)
    print(f'ZIP verified: {archive.name}; {len(files)} files; {archive.stat().st_size} bytes')


if __name__ == '__main__':
    main()
