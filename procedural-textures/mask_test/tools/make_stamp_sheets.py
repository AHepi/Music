# What this does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------
# It draws two contact sheets of the stamp work:
#   sheets/stamp_atlases.jpg         the atlases (grids of separate stamps): moss C and moss A+B and chips C, as white shapes on black,
#                                    with the cell size and the number of stamps written under each;
#   sheets/generated_originals.jpg   the six pictures the image generator made (the originals) next to what was kept from them.
# Run:  python3 -I make_stamp_sheets.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
ATLAS = os.path.join(ROOT, 'stamps', 'atlas')
ORIGINALS = os.path.join(ROOT, 'stamps', 'originals')
CLEANED = os.path.join(ROOT, 'stamps', 'cleaned')
SHEETS = os.path.join(ROOT, 'sheets')


def caption(picture, text, height=None):
    """Text under a picture; a '|' in the text starts a second line."""
    lines = text.split('|')
    height = height or (8 + 22 * len(lines))
    bar = np.full((height, picture.shape[1], 3), 245, np.uint8)
    for k, line in enumerate(lines):
        cv2.putText(bar, line.strip(), (8, 20 + 22 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([picture, bar])


def to_bgr(grey):
    return cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)


def atlas_panel(name, label, scale, tint=(255, 255, 255)):
    info = json.load(open(os.path.join(ATLAS, name + '_atlas.json')))
    view = cv2.imread(os.path.join(ATLAS, name + '_atlas_mask_view.png'), 0)
    view = cv2.resize(view, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    panel = to_bgr(view)
    # thin grid lines so the separate cells can be seen
    cell_w, cell_h = info['cell_width'] * scale, info['cell_height'] * scale
    for c in range(1, info['columns']):
        cv2.line(panel, (int(c * cell_w), 0), (int(c * cell_w), panel.shape[0]), (90, 60, 20), 1)
    for r in range(1, info['rows']):
        cv2.line(panel, (0, int(r * cell_h)), (panel.shape[1], int(r * cell_h)), (90, 60, 20), 1)
    text = f"{label}|{info['stamp_count']} stamps, cells {info['cell_width']} x {info['cell_height']} dots, grid {info['columns']} x {info['rows']}"
    return caption(panel, text)


def stack_to_height(panels, height):
    out = []
    for p in panels:
        if p.shape[0] < height:
            p = cv2.copyMakeBorder(p, 0, height - p.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(245, 245, 245))
        out.append(p)
    return out


def atlases_sheet():
    panels = [atlas_panel('moss_C', 'moss C (hanging drips): used', 0.5), atlas_panel('moss_AB', 'moss A+B (round, splats): tried', 0.25),
              atlas_panel('chips_C', 'chips C (cut strips): used', 0.6)]
    second = [atlas_panel('chips_A', 'chips A (chunky): not used', 0.4), atlas_panel('chips_B', 'chips B (squarish): not used', 0.4)]
    row1 = np.hstack(stack_to_height([p for pair in zip(panels, [np.full((panels[0].shape[0], 8, 3), 245, np.uint8)] * 3) for p in pair][:-1], max(p.shape[0] for p in panels)))
    row2 = np.hstack(stack_to_height([second[0], np.full((second[0].shape[0], 8, 3), 245, np.uint8), second[1]], max(p.shape[0] for p in second)))
    width = max(row1.shape[1], row2.shape[1])
    pad = lambda r: cv2.copyMakeBorder(r, 0, 0, 0, width - r.shape[1], cv2.BORDER_CONSTANT, value=(245, 245, 245))
    sheet = np.vstack([pad(row1), pad(row2)])
    cv2.imwrite(os.path.join(SHEETS, 'stamp_atlases.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('stamp_atlases.jpg', sheet.shape)


ORIGINAL_NOTES = [
    ('moss_sheet_A_flux-dev_seed4101.png', 'moss_A_sheet_mask.png', 'moss A: 16 round fuzzy clumps - usable'),
    ('moss_sheet_B_flux-dev_seed4103.png', 'moss_B_sheet_mask.png', 'moss B: 16 ink splats, cream ground - usable'),
    ('moss_sheet_C_flux-dev_seed4106.png', 'moss_C_sheet_mask.png', 'moss C: hanging drips, rod removed - usable'),
    ('chips_sheet_A_flux-dev_seed4102.png', 'chips_A_sheet_mask.png', 'chips A: chunky flakes - poor shape'),
    ('chips_sheet_B_flux-dev_seed4104.png', 'chips_B_sheet_mask.png', 'chips B: squarish pieces - poor shape'),
    ('chips_sheet_C_flux-dev_seed4105.png', 'chips_C_sheet_mask.png', 'chips C: ragged strips - usable when cut'),
]


def originals_sheet():
    tiles = []
    for original, cleaned, note in ORIGINAL_NOTES:
        a = cv2.resize(cv2.imread(os.path.join(ORIGINALS, original)), (420, 420), interpolation=cv2.INTER_AREA)
        b = to_bgr(cv2.resize(cv2.imread(os.path.join(CLEANED, cleaned), 0), (420, 420), interpolation=cv2.INTER_AREA))
        tiles.append(caption(np.hstack([a, np.full((420, 4, 3), 245, np.uint8), b]), note))
    rows = [np.hstack([tiles[i], np.full((tiles[i].shape[0], 10, 3), 245, np.uint8), tiles[i + 1]]) for i in (0, 2, 4)]
    sheet = np.vstack(rows)
    cv2.imwrite(os.path.join(SHEETS, 'generated_originals.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
    print('generated_originals.jpg', sheet.shape)


if __name__ == '__main__':
    os.makedirs(SHEETS, exist_ok=True)
    atlases_sheet()
    originals_sheet()
