"""What this does: keeps the shadows a painter put on the ground round the near props in the "behind" painting (the
copy with the near props painted out). The film switches the ground round the near props to that painting as soon
as the camera moves; the painter took the props' shadows away with the props, so the long shadows the fire threw
from the pail and the chair faded off the pavement 2 seconds into the notice corner's slide (log 32). This keeps
the main painting everywhere except inside the near props' own outlines (widened a little, so the painter's ink
lines round them don't stay behind on the road), and the behind painting inside, with a soft join, darkened by the
shadows round it (carried inward), so no pale strip shows between a prop and its shadow.

Use: python3 -I keep_painted_shadows.py CHECK_FILE PLATE_FACTS PAINTING BEHIND_PAINTING OUT [WIDEN_PIXELS=10] [GROUP ...]
PLATE_FACTS is shot_facts.py's folder for the plate's camera; the GROUPs are the near props (default: the check
file's subject, support and story props, and its lamp post if it has one). WIDEN_PIXELS is in the painting's pixels.
"""
import os
import sys
import types

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_shot  # noqa: E402

check_file, facts, painting_path, behind_path, out_path = sys.argv[1:6]
widen = int(sys.argv[6]) if len(sys.argv) > 6 else 10
groups = sys.argv[7:]
shot = check_shot.Shot(types.SimpleNamespace(check=check_file, facts=facts, picture=None, out='/tmp', title='', render_log=None))
groups = groups or [g for g in shot.core + ['lamp post'] if g in shot.visible]
painting, behind = cv2.imread(painting_path), cv2.imread(behind_path)
h, w = painting.shape[:2]
props = np.zeros((shot.height, shot.width), np.uint8)
for g in groups:
    props |= shot.visible[g].astype(np.uint8)
props = cv2.resize(props, (w, h), interpolation=cv2.INTER_NEAREST)
props = cv2.dilate(props, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * widen + 1, 2 * widen + 1)))
weight = cv2.GaussianBlur(props.astype(np.float32), (0, 0), max(1.0, widen / 3))[:, :, None]   # 1 inside: the behind painting
# inside the outlines the behind painting has no shadows, so a pale strip showed between a prop and its shadow once
# the camera moved (log 32): carry the shadows' darkening in from just outside. How much darker the painting is
# than the behind painting is measured outside the outlines and spread inward (filling in, at a quarter size),
# then applied to the behind painting there; the painter's ink lines round the props are not carried
main_f, behind_f = painting.astype(np.float32), behind.astype(np.float32)
grey = lambda image: cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
ratio = np.clip((grey(painting) + 8) / (grey(behind) + 8), 0.25, 1.0)   # only darkening is carried
ratio = cv2.GaussianBlur(ratio, (0, 0), 3)
small = (w // 4, h // 4)
hole = cv2.resize(cv2.dilate(props, np.ones((5, 5), np.uint8)), small, interpolation=cv2.INTER_NEAREST)
filled = cv2.inpaint((cv2.resize(ratio, small, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8), hole, 12, cv2.INPAINT_TELEA)
filled = cv2.GaussianBlur(cv2.resize(filled.astype(np.float32) / 255, (w, h), interpolation=cv2.INTER_LINEAR), (0, 0), 4)
mixed = behind_f * filled[:, :, None] * weight + main_f * (1 - weight)
cv2.imwrite(out_path, np.clip(mixed + 0.5, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
print(f'kept the painting outside {", ".join(groups)} (widened {widen} pixels): {float((weight > 0.5).mean()):.1%} of the picture '
      f'uses the behind painting; saved {out_path}')
