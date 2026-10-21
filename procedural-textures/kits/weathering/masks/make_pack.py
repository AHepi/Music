# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Rebuilds a scene's PACK from the reader's raw arrays WITHOUT Blender (plain Python: numpy and OpenCV). Use it when only the finishing changes: the rubbish picture arrived (a
# plan view drawn on the rented machine: habitat fields avoid litter), a habitat weight changed in the set file, or the pack format changed.
#     python3 -I masks/make_pack.py SET_ID SCENE_ID RAW_DIR [--rubbish PICTURE.png]
# The rubbish picture is the 'plan:rubbish_heap' view (red = rubbish mask) over the ground bounds; it is resized to the ground grid.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402

from apply import settings as settings_module  # noqa: E402
from masks import pack  # noqa: E402


def load_rubbish(path, grid_shape):
    import cv2
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    red = im[..., 2].astype(np.float32) / scale                   # OpenCV reads BGR
    red = np.flipud(red)                                          # file top = high y; arrays have row 0 = low y
    return cv2.resize(red, (grid_shape[1], grid_shape[0]), interpolation=cv2.INTER_AREA)


def main(argv):
    flags = [a for a in argv if a.startswith('--')]
    pos = [a for a in argv if not a.startswith('--')]
    set_id, scene_id, raw_dir = pos[0], pos[1], pos[2]
    settings = settings_module.load_set(set_id)
    rubbish = None
    if '--rubbish' in argv:
        picture = argv[argv.index('--rubbish') + 1]
        info = json.load(open(os.path.join(raw_dir, 'raw.json')))
        shape = (info['grid']['size'][1], info['grid']['size'][0])
        rubbish = load_rubbish(picture, shape)
    out = pack.pack_dir(KIT_ROOT, settings.id, scene_id)
    old = os.path.join(out, 'manifest.json')
    prev = json.load(open(old)) if os.path.exists(old) else {}
    checks = json.load(open(os.path.join(raw_dir, 'checks_geometry.json'))) if os.path.exists(os.path.join(raw_dir, 'checks_geometry.json')) else {}
    manifest, gp = pack.build(settings, KIT_ROOT, scene_id, raw_dir, out, rubbish_heap=rubbish, checks=checks.get('checks', prev.get('checks', {})), timings=checks.get('timings', prev.get('timings', [])))
    manifest['stats'] = json.load(open(os.path.join(raw_dir, 'raw.json'))).get('stats', {})
    from masks import checks as checks_module
    checks_module.resolve_stone_pieces(manifest)
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print('pack written', out, manifest['bytes'], 'bytes')


if __name__ == '__main__':
    main(sys.argv[1:])
