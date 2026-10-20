# What this does: makes the "reference on the left, my recipe on the right" pictures used in the guide (plain Python, run with python3 -I).
#   python3 -I make_comparison.py SURFACE BAKED_FOLDER OUT_PNG [--label "text under the right picture"] [--cell 512]
# and, with several surfaces, one overview:
#   python3 -I make_comparison.py --overview OUT_PNG  brick:out/final_brick  slate:out/final_slate ...
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, '..', '..', 'reference')


def labelled(image, text, height=30):
    banner = np.full((height, image.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, text[:70], (6, height - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([banner, image])


def load(path, cell):
    image = cv2.imread(path)
    return cv2.resize(image, (cell, cell), interpolation=cv2.INTER_AREA)


def pair(surface, folder, cell, label):
    reference = load(os.path.join(REFERENCE, surface, 'colour.png'), cell)
    mine = load(os.path.join(folder, 'colour.png'), cell)
    return np.hstack([labelled(reference, f'reference {surface}'), labelled(mine, label or f'procedural recipe ({surface})')])


if __name__ == '__main__':
    args = sys.argv[1:]
    cell = int(args[args.index('--cell') + 1]) if '--cell' in args else 512
    if args[0] == '--overview':
        out = args[1]
        rows = [pair(item.split(':')[0], item.split(':')[1], cell, None) for item in args[2:] if ':' in item]
        columns = 2
        while len(rows) % columns:
            rows.append(np.full_like(rows[0], 255))
        grid = np.vstack([np.hstack(rows[i:i + columns]) for i in range(0, len(rows), columns)])
        cv2.imwrite(out, grid)
    else:
        surface, folder, out = args[0], args[1], args[2]
        label = args[args.index('--label') + 1] if '--label' in args else None
        cv2.imwrite(out, pair(surface, folder, cell, label))
    print('wrote', out)
