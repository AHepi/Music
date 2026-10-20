# What this does: draws the overview picture of guide "07 Reuse - which tools work on which surfaces".
# One row per surface (brick, wood, metal, mud, gravel). Three pictures per row: the reference (a guide only), the surface's own
# earlier recipe (its first new tile), and the layered tile (shared layers + the new parts the trial had to add, seed set 1).
# It only reads pictures and score files that already exist; it bakes nothing and starts no Blender.
# Every number printed in the picture is read from the independent re-check's score files in reuse_trials/verify/ (not typed in).
# Output: cookbook/pictures/07 Reuse - five surfaces.jpg  (JPEG, at most 1800 dots wide) and a list of the files used.
# Run with: python3 -I make_reuse_overview.py   (plain Python with Pillow; no Blender)
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROC_WORK = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REFERENCE = os.path.join(PROC_WORK, 'reference')
RECIPES = os.path.join(PROC_WORK, 'recipes')
TRIALS = os.path.join(PROC_WORK, 'reuse_trials')
VERIFY = os.path.join(TRIALS, 'verify')
OUTPUT_PICTURE = os.path.join(PROC_WORK, 'cookbook', 'pictures', '07 Reuse - five surfaces.jpg')
OUTPUT_LIST = os.path.join(HERE, 'reuse_overview_files_used.json')

CELL = 460          # dots per picture
GAP = 10
LABEL_WIDTH = 160
HEADER_HEIGHT = 50
CAPTION_HEIGHT = 64
FOOTER_HEIGHT = 76
MAX_WIDTH = 1800

BACKGROUND = (255, 255, 255)
TEXT = (30, 30, 30)
SOFT_TEXT = (90, 90, 90)
AHEAD = (24, 100, 40)
BEHIND = (160, 30, 30)

FONT_REGULAR = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'

# surface -> (earlier recipe picture inside recipes/, name of its tile for the caption, earlier-recipe score file,
#             does the layered tile read as the surface (from the independent re-check), seed sets baked)
SURFACES = [
    ('brick', 'variations/tile_11/colour.png', 'tile 11', 'baselines/brick_baseline_remade_normal.json', 'yes', 3),
    ('wood', 'variations/sample_101/colour.png', 'sample 101', 'baselines/wood_baseline.json', 'yes', 3),
    ('metal', 'variations/seed_1/colour.png', 'seed 1', 'baselines/metal_baseline.json', 'yes', 3),
    ('mud', 'variations/tile_101/colour.png', 'tile 101', 'baselines/mud_baseline.json', 'partly', 3),
    ('gravel', 'variations/out/sample_01/colour.png', 'sample 1', 'baselines/gravel_baseline_remade_normal.json', 'at a glance', 3),
]


def load_json(path):
    with open(path) as handle:
        return json.load(handle)


def font(path, size):
    return ImageFont.truetype(path, size)


def load_square(path):
    picture = Image.open(path).convert('RGB')
    if picture.size[0] != picture.size[1]:
        raise SystemExit('picture is not square: %s %s' % (path, picture.size))
    return picture.resize((CELL, CELL), Image.LANCZOS)


def main():
    scores = {}
    for name, _, _, baseline_file, _, sets in SURFACES:
        layered = [load_json(os.path.join(VERIFY, 'scores', '%s_seeds_%d_remadenormal.json' % (name, n))) for n in range(1, sets + 1)]
        earlier = load_json(os.path.join(VERIFY, baseline_file))
        scores[name] = {
            'set1_overall': layered[0]['overall'],
            'set1_colour': layered[0]['groups']['colour'],
            'mean_overall': sum(item['overall'] for item in layered) / len(layered),
            'mean_colour': sum(item['groups']['colour'] for item in layered) / len(layered),
            'earlier_overall': earlier['overall'],
            'earlier_colour': earlier['groups']['colour'],
        }

    width = LABEL_WIDTH + 3 * CELL + 4 * GAP
    row_height = CELL + CAPTION_HEIGHT + GAP
    height = HEADER_HEIGHT + len(SURFACES) * row_height + FOOTER_HEIGHT
    if width > MAX_WIDTH:
        raise SystemExit('picture too wide: %d' % width)
    canvas = Image.new('RGB', (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    f_head = font(FONT_BOLD, 21)
    f_name = font(FONT_BOLD, 26)
    f_label = font(FONT_REGULAR, 17)
    f_label_bold = font(FONT_BOLD, 17)
    f_caption = font(FONT_REGULAR, 19)
    f_caption_bold = font(FONT_BOLD, 19)
    f_foot = font(FONT_REGULAR, 16)

    columns = ['reference (a guide only)', 'own earlier recipe (its first new tile)', 'layered: shared layers + new parts']
    column_x = [LABEL_WIDTH + GAP + i * (CELL + GAP) for i in range(3)]
    for x, text in zip(column_x, columns):
        draw.text((x, 14), text, font=f_head, fill=TEXT)

    used = []
    for row_index, (name, earlier_picture, earlier_name, _, reads, sets) in enumerate(SURFACES):
        top = HEADER_HEIGHT + row_index * row_height
        s = scores[name]
        reference_path = os.path.join(REFERENCE, name, 'colour.png')
        earlier_path = os.path.join(RECIPES, name, earlier_picture)
        layered_path = os.path.join(TRIALS, name, 'final', 'seeds_1', 'colour.png')
        used.append({'surface': name, 'reference': reference_path, 'earlier': earlier_path, 'layered': layered_path})
        for x, path in zip(column_x, [reference_path, earlier_path, layered_path]):
            canvas.paste(load_square(path), (x, top))

        # left label
        draw.text((10, top + 8), name.upper(), font=f_name, fill=TEXT)
        difference = s['mean_overall'] - s['earlier_overall']
        word = 'layered ahead' if difference > 0 else 'layered behind'
        colour = AHEAD if difference > 0 else BEHIND
        draw.text((10, top + 50), word, font=f_label_bold, fill=colour)
        draw.text((10, top + 72), '%+.3f overall' % difference, font=f_label, fill=colour)
        draw.text((10, top + 100), 'reads as %s:' % name, font=f_label, fill=SOFT_TEXT)
        draw.text((10, top + 120), reads, font=f_label_bold, fill=TEXT)

        # captions
        cap_top = top + CELL + 4
        draw.text((column_x[0], cap_top), 'given', font=f_caption_bold, fill=TEXT)
        draw.text((column_x[0], cap_top + 24), '1254 x 1254 dots; not traced', font=f_caption, fill=SOFT_TEXT)
        draw.text((column_x[1], cap_top), 'same-kind %.3f  (colour %.3f)' % (s['earlier_overall'], s['earlier_colour']), font=f_caption_bold, fill=TEXT)
        draw.text((column_x[1], cap_top + 24), '%s of the earlier recipe' % earlier_name, font=f_caption, fill=SOFT_TEXT)
        draw.text((column_x[2], cap_top), 'set 1: %.3f  (colour %.3f)' % (s['set1_overall'], s['set1_colour']), font=f_caption_bold, fill=TEXT)
        draw.text((column_x[2], cap_top + 24), 'mean of %d seed sets: %.3f  (colour %.3f)' % (sets, s['mean_overall'], s['mean_colour']), font=f_caption, fill=SOFT_TEXT)

    foot_top = HEADER_HEIGHT + len(SURFACES) * row_height + 2
    draw.text((10, foot_top), 'Same-kind score = lib/texture_compare.py, 1254 dots, normal map remade from the height map; every number re-run by the independent check.', font=f_foot, fill=SOFT_TEXT)
    draw.text((10, foot_top + 20), 'Seed set 1 is the set the settings were tuned on, so the mean of three sets is the fairer layered number. "Reads as" is the independent check\'s judgement by eye.', font=f_foot, fill=SOFT_TEXT)
    combine_rule = {}
    for name in ('brick', 'metal', 'gravel'):
        combine_rule[name] = load_json(os.path.join(VERIFY, 'side', '%s_combine_rule%s.json' % (name, '_1' if name == 'metal' else '')))['overall']
    draw.text((10, foot_top + 40), 'Brick, metal and gravel layered tiles use a height rule fitted once to the reference height maps; with COMBINE\'s own rule set 1 scores brick %.3f, metal %.3f, gravel %.3f.' % (combine_rule['brick'], combine_rule['metal'], combine_rule['gravel']), font=f_foot, fill=SOFT_TEXT)

    os.makedirs(os.path.dirname(OUTPUT_PICTURE), exist_ok=True)
    canvas.save(OUTPUT_PICTURE, quality=86, optimize=True)
    with open(OUTPUT_LIST, 'w') as handle:
        json.dump({'picture': OUTPUT_PICTURE, 'size': canvas.size, 'files_used': used, 'scores': scores}, handle, indent=1)
    print('wrote', OUTPUT_PICTURE, canvas.size, os.path.getsize(OUTPUT_PICTURE), 'bytes')
    for name in scores:
        print(name, {key: round(value, 3) for key, value in scores[name].items()})


main()
