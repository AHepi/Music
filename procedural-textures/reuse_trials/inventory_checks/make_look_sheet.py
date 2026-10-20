# What this does (plain words): joins the look check's six colour pictures and the wood and brick reference pictures (shrunk, as a guide only) into one
# labelled sheet, look_check/look_check_sheet.jpg (JPEG, for looking at). Plain Python with OpenCV; reads pictures, writes one JPEG.
# Use: python3 -I make_look_sheet.py
import os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'look_check')
CELL = 420
rows = [
    [('wood reference (guide only)', os.path.join(PROC, 'reference', 'wood', 'colour.png')),
     ('wood: bundle as for slate, colour+fade only', os.path.join(OUT, 'wood_plain_colour_and_fade_only_colour.png')),
     ('wood: bundle TURNED, colour+fade only', os.path.join(OUT, 'wood_turned_colour_and_fade_only_colour.png')),
     ('wood: bundle TURNED, all layers', os.path.join(OUT, 'wood_turned_all_layers_colour.png'))],
    [('brick reference (guide only)', os.path.join(PROC, 'reference', 'brick', 'colour.png')),
     ('brick 4 per course, b1, colour+fade only', os.path.join(OUT, 'brick_b1_colour_and_fade_only_colour.png')),
     ('brick, fade dir 0 + round patches, colour+fade', os.path.join(OUT, 'brick_flat_colour_and_fade_only_colour.png')),
     ('brick, the same, all layers', os.path.join(OUT, 'brick_flat_all_layers_colour.png'))],
]
sheet_rows = []
for row in rows:
    cells = []
    for text, path in row:
        picture = cv2.resize(cv2.imread(path), (CELL, CELL), interpolation=cv2.INTER_AREA)
        banner = np.full((30, CELL, 3), 245, np.uint8)
        cv2.putText(banner, text, (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
        cells.append(np.vstack([banner, picture]))
        cells.append(np.full((CELL + 30, 6, 3), 255, np.uint8))
    sheet_rows.append(np.hstack(cells[:-1]))
    sheet_rows.append(np.full((6, sheet_rows[-1].shape[1], 3), 255, np.uint8))
cv2.imwrite(os.path.join(OUT, 'look_check_sheet.jpg'), np.vstack(sheet_rows[:-1]), [cv2.IMWRITE_JPEG_QUALITY, 88])
print('written', os.path.join(OUT, 'look_check_sheet.jpg'))
