# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Makes the SHEETS (big pictures for looking) from the pictures the runs drew (plain Python with OpenCV and numpy; no Blender):
#   rubbish_mask.jpg            the mask itself: seen from above (street copy and lockout shot file), drawn on the street from the film's cameras, and what each place's dial does to it
#   rubbish_all_lights.jpg      the lighting test set (22 pictures: dry / wet / heavy, five lightings, three cameras), each as round 2, with the setts' JOINTS layer, and with the rubbish, with the numbers
#   rubbish_closeups_100pct.jpg a gutter, a wall foot and a doorstep (100 % crops of 1600 x 1200 pictures) and two 100 % crops of the full-size lockout plate, without and with the rubbish
#   rubbish_controls.jpg        what every control does, one change at a time
#   rubbish_final_plate_half_size.jpg   the final full-size lockout plate (wet, setts and rubbish) at half size
# Use: python3 -I make_sheets.py            (the run folders are named in RUNS below)
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import sheet_tools as st  # noqa: E402

RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
WORK = os.path.join(RUBBISH, 'work')
SHEETS = os.path.abspath(os.path.join(RUBBISH, '..', 'sheets'))
os.makedirs(SHEETS, exist_ok=True)
TEST, CTRL, CTRL3, PLATES, EXTRAS = (os.path.join(WORK, n) for n in ('testset02', 'controls02', 'controls03', 'plates02', 'extras01'))
BG = st.BG


def rot(img):
    """A plan picture has the street's far end (y = 42 m) at the top and the right-hand pavement (x = +4.5 m) on the right. Turned clockwise, the street runs left to right (y = 0 at the left) with the LEFT pavement
    at the top and the RIGHT pavement at the bottom."""
    return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)


def plan_tile(path, text, width=1000, y_max_m=22.0, y_min_m=0.0):
    """A plan picture (street along x): the street from y_min_m to y_max_m metres (the plan pictures cover 0 to 42 m)."""
    img = rot(cv2.imread(path))                 # 450 x 2100 -> street along the width, y 0 at the left (42 m over 2100 dots)
    img = img[:, int(img.shape[1] * y_min_m / 42.0):int(img.shape[1] * y_max_m / 42.0)]
    return st.caption(cv2.resize(img, (width, int(img.shape[0] * width / img.shape[1])), interpolation=cv2.INTER_AREA), text, height=30, scale=0.55)


def tiles_grid(tiles, cols, gap=6):
    rows = []
    for i in range(0, len(tiles), cols):
        r = tiles[i:i + cols]
        h = max(t.shape[0] for t in r)
        r = [np.vstack([t, np.full((h - t.shape[0], t.shape[1], 3), BG, np.uint8)]) for t in r]
        line = []
        for t in r:
            line += [t, np.full((h, gap, 3), BG, np.uint8)]
        rows.append(np.hstack(line[:-1]))
        rows.append(np.full((gap, rows[-1].shape[1], 3), BG, np.uint8))
    w = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], w - r.shape[1], 3), BG, np.uint8)]) for r in rows]
    return np.vstack(rows)


def text_block(lines, width, height_per=26, scale=0.6, colour=(225, 228, 235), title=None):
    h = height_per * len(lines) + (42 if title else 10)
    img = np.full((h, width, 3), BG, np.uint8)
    y = 28
    if title:
        cv2.putText(img, title, (8, 28), st.FONT, 0.85, (240, 230, 190), 2, cv2.LINE_AA)
        y = 62
    for line in lines:
        cv2.putText(img, line, (8, y), st.FONT, scale, colour, 1, cv2.LINE_AA)
        y += height_per
    return img


def sheet_mask():
    W = 2300
    legend = ['Red = the gutter (channel stones, kerb, foot of the kerb) and the road\'s outer strip.   Green = the foot of the house walls.   Blue = the foot of each front step, rain pipe and lamp post, and inside corners.',
              'Yellow = round the props (fire drum, sacks, handcart, dustbins, pails, barrel: only in the lockout shot file).   Black = clean.   The middle of the road (the crown) stays black.']
    top = text_block(legend, W, title='The rubbish mask: where rubbish gathers')
    p1 = plan_tile(os.path.join(CTRL, 'plan_default.jpg'), 'seen from above, street copy: the first 22 m of the street run left to right; left-hand pavement at the top, right-hand pavement at the bottom, the road between them (black = clean)', W, 22.0)
    p2 = plan_tile(os.path.join(CTRL3, 'lockplan_default.jpg'), 'seen from above, the lockout shot file (with its props: the fire drum, sacks, handcart and dustbins have yellow rings)', W, 22.0)
    lock = cv2.imread(os.path.join(EXTRAS, 'maskview_lockout_B_wet.jpg'))
    views = st.row([('street main camera, wet', os.path.join(EXTRAS, 'maskview_main_A_wet.jpg')), ('lockout plate camera, wet', lock),
                    ('the gutter close view', os.path.join(EXTRAS, 'maskview_gutter_A_wet.jpg')), ('the doorstep close view', os.path.join(EXTRAS, 'maskview_doorstep_A_wet.jpg'))], height=640)
    names = ['default', 'gutter_only', 'wall_foot_only', 'corners_only', 'amount_0.5', 'amount_2', 'patchiness_0', 'patchiness_1', 'seed_5', 'seed_11', 'gutter_width_0.25', 'gutter_width_1.6_crown_clear_1',
             'gutter_width_1.6_crown_clear_0', 'wall_width_0.4', 'wall_width_1.4']
    cols = 3
    tw = (W - 12) // cols
    crop_top = lambda t: t   # noqa: E731
    grid = tiles_grid([crop_top(plan_tile(os.path.join(CTRL, f'plan_{n}.jpg'), n.replace('_', ' '), tw, 14.0)) for n in names], cols)
    lockgrid = tiles_grid([crop_top(plan_tile(os.path.join(CTRL3, f'lockplan_{n}.jpg'), 'lockout file: ' + n.replace('_', ' '), tw, 18.0, 4.0)) for n in ('default', 'props_only', 'props_width_0.4', 'props_width_1.2', 'amount_2', 'seed_5')], cols)
    parts = [top, p1, p2, text_block(['The mask drawn on the ground, seen from the film\'s cameras (the street in its own colours):'], W), views,
             text_block(['What each dial does to the mask (street copy, the first 14 m of the street; left pavement at the top; one change at a time from the defaults):'], W), grid,
             text_block(['The same for the props (lockout shot file, 4 to 18 m along the street):'], W), lockgrid]
    sheet = st.stack(parts, gap=10)
    st.save(os.path.join(SHEETS, 'rubbish_mask.jpg'), sheet, 86, max_width=2400)
    return sheet.shape


def sheet_all_lights():
    from_json = json.load(open(os.path.join(TEST, 'measurements.json')))
    order = [('main', ['A_dry', 'A_wet', 'A_heavy', 'C_dry', 'C_wet', 'D_dry', 'D_wet', 'E_dry', 'E_wet', 'E_heavy']), ('close', ['A_dry', 'A_wet', 'A_heavy', 'C_wet', 'D_wet', 'E_wet']),
             ('lockout', ['B_dry', 'B_wet', 'B_heavy', 'C_wet', 'D_wet', 'E_wet'])]
    names_light = {'A': 'dusk lamps', 'B': 'brazier glare', 'C': 'low side light', 'D': 'flat overhead', 'E': 'light from behind'}
    blocks = []
    for cam, conds in order:
        cells = []
        for cond in conds:
            light, state = cond.split('_')
            col = []
            for look, label in (('round2', 'round 2'), ('joints', '+ JOINTS'), ('rubbish', '+ rubbish')):
                name = f'{cam}_{light}_{state}_{look}'
                path = os.path.join(TEST, name + '.jpg')
                img = cv2.imread(path)
                if cam in ('main', 'lockout'):
                    img = img[int(img.shape[0] * 0.45):, :]
                r = from_json.get(name)
                near = f"{r['near']['contrast']:.2f}" if r and r['near']['contrast'] is not None else '-'
                mid = f"{r['middle']['contrast']:.2f}" if r and r['middle']['contrast'] is not None else '-'
                ok = 'PASS' if r and r.get('pass') else 'FAIL'
                sub = f"joints near {near} mid {mid} {ok}" + (f"  dirt {r['dirt_share'] * 100:.0f}%" if look == 'rubbish' and r else '')
                col.append(st.caption(cv2.resize(img, (330, int(img.shape[0] * 330 / img.shape[1])), interpolation=cv2.INTER_AREA), f'{label}', height=26, scale=0.5, sub=sub))
            head = np.full((30, 330, 3), BG, np.uint8)
            cv2.putText(head, f'{names_light[light]}, {state}', (6, 21), st.FONT, 0.55, (240, 230, 190), 1, cv2.LINE_AA)
            cells.append(np.vstack([head] + col))
        h = max(c.shape[0] for c in cells)
        cells = [np.vstack([c, np.full((h - c.shape[0], c.shape[1], 3), BG, np.uint8)]) for c in cells]
        line = []
        for c in cells:
            line += [c, np.full((h, 6, 3), BG, np.uint8)]
        blocks.append(np.hstack(line[:-1]))
    title = text_block(['Three ways for each of the 22 pictures of the lighting test set: round 2 (no JOINTS layer, no rubbish), with the JOINTS layer, and with the rubbish. Main and lockout pictures show the lower part (the ground).',
                        'Numbers: the joints between the setts, measured as in the setts round (near and middle bands of the road; dots under puddles and under rubbish left out; PASS line unchanged); dirt = share of the road that is rubbish.'],
                       3600, title='The rubbish in every light: dry, wet and heavy rain')
    sheet = st.stack([title] + blocks, gap=12)
    st.save(os.path.join(SHEETS, 'rubbish_all_lights.jpg'), sheet, 85, max_width=3600)
    return sheet.shape


def crop(img, box):
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1]


def sheet_closeups():
    pairs = []
    spec = [('gutter', 'closeup_gutter_A_wet', (900, 500, 1600, 1000), 'a gutter and kerb (low view along the right gutter; wet)'),
            ('wall foot', 'closeup_wall_A_wet', (800, 650, 1600, 1200), 'the foot of a house wall (pavement along the right wall; wet)'),
            ('doorstep', 'closeup_doorstep_A_wet', (760, 620, 1560, 1170), 'a doorstep (the pavement in front of a front step; wet)')]
    for key, base, box, text in spec:
        a = crop(cv2.imread(os.path.join(PLATES, base.replace('_wet', '_wet') + '_joints.jpg')), box)
        b = crop(cv2.imread(os.path.join(PLATES, base + '_rubbish.jpg')), box)
        pairs.append(st.row([(text + ': joints only', a), (text + ': with rubbish', b)], height=a.shape[0]))
    plate = cv2.imread(os.path.join(PLATES, 'plate_lockout_B_wet_joints.jpg'))
    plate2 = cv2.imread(os.path.join(PLATES, 'plate_lockout_B_wet_rubbish.jpg'))
    for text, box in (('plate: right gutter and wall foot', (880, 1640, 1536, 2100)), ('plate: handcart, sacks, road', (0, 1900, 760, 2730))):
        pairs.append(st.row([(text + ': joints only', crop(plate, box)), (text + ': with rubbish', crop(plate2, box))], height=box[3] - box[1]))
    title = text_block(['Every picture is a 100 % crop: one dot of the picture is one dot of the sheet (the close views are 1600 x 1200, the lockout plate 1536 x 2730; 64 samples, EEVEE with ray tracing, shadow rays 4, steps 16).'], 1700,
                       title='Close-ups at full size: a gutter, a wall foot, a doorstep')
    sheet = st.stack([title] + pairs, gap=12)
    st.save(os.path.join(SHEETS, 'rubbish_closeups_100pct.jpg'), sheet, 90)
    return sheet.shape


def sheet_controls():
    def grid(prefix, names, folder, cols, h=300, crop_ground=True):
        tiles = []
        for n in names:
            img = cv2.imread(os.path.join(folder, f'{prefix}_{n}.jpg'))
            if crop_ground:
                img = img[int(img.shape[0] * 0.30):, :]
            tiles.append(st.caption(st.fit(img, height=h), n.replace('_', ' '), height=26, scale=0.5))
        return tiles_grid(tiles, cols)
    kinds = ['amount_0', 'default', 'amount_2', 'dust_off', 'ash_off', 'mud_off', 'straw_off', 'paper_off', 'leaves_off', 'pieces_off', 'dust_only', 'pieces_only', 'relief_0', 'grit_size_2', 'grit_size_0.6',
             'wet_look_0', 'dust_darkness_0.3', 'dust_darkness_1', 'pieces_density_2', 'piece_size_1.6']
    places = ['default', 'corners_0', 'corners_2', 'wall_foot_0', 'wall_foot_2', 'gutter_0', 'gutter_2', 'patchiness_0', 'patchiness_1', 'seed_5', 'seed_11', 'wall_width_1.4', 'gutter_width_1']
    parts = [text_block(['Each picture changes ONE control from the defaults. Wet, the low side light (C) for the street views so that the ground can be seen, the lockout shot (B) for the drum view. Lower part of each view.'], 2400,
                        title='What every control does'),
             text_block(['The kinds of rubbish and the look dials, drum view (lockout shot file):'], 2400), grid('drum', kinds, CTRL, 5, 260, crop_ground=True),
             text_block(['The kinds of rubbish and the look dials, doorstep view (street copy):'], 2400), grid('doorstepC', kinds, EXTRAS, 5, 260, crop_ground=True),
             text_block(['The places, the patchiness, the seed and the widths, gutter view (street copy):'], 2400), grid('gutterC', places, EXTRAS, 5, 260, crop_ground=True),
             text_block(['The places, the patchiness, the seed and the widths, wall foot view (street copy):'], 2400), grid('wallC', places, EXTRAS, 5, 260, crop_ground=True),
             text_block(['Round the props (drum view, lockout shot file):'], 2400), grid('drumprops', ['props_0', 'default', 'props_2', 'seed_5'], CTRL, 4, 260, crop_ground=True)]
    sheet = st.stack(parts, gap=10)
    st.save(os.path.join(SHEETS, 'rubbish_controls.jpg'), sheet, 84, max_width=2400)
    return sheet.shape


def sheet_final():
    img = cv2.imread(os.path.join(PLATES, 'final_lockout_plate_wet_setts_and_rubbish.png'))
    half = cv2.resize(img, (768, 1365), interpolation=cv2.INTER_AREA)
    st.save(os.path.join(SHEETS, 'rubbish_final_plate_half_size.jpg'), half, 92)
    return half.shape


if __name__ == '__main__':
    which = sys.argv[1:] or ['mask', 'lights', 'closeups', 'controls', 'final']
    for name, fn in (('mask', sheet_mask), ('lights', sheet_all_lights), ('closeups', sheet_closeups), ('controls', sheet_controls), ('final', sheet_final)):
        if name in which:
            print(name, fn(), flush=True)
