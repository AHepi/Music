"""What this does: finishes a still drawn by the paper stage at twice the size, so it looks like a
photograph of a real paper model.

1. Glow: warm, bright light (lit windows, an open door) gets a soft halo, as it would through a lens.
2. Shrink to 1080 x 1920, which smooths every edge.
3. Background blur (only if the drawing came with a distance picture, OUTPUT-distance.png): what is
   at the same distance as the focus point stays sharp; nearer and farther things soften, more the
   further they are from it, like a camera lens close up to a small model.
4. Soft darkening toward the corners, like a lamp-lit room, and a very fine grain.

Use: python3 -I tools/finish_one_page_still.py DRAWN.png FINISHED.png [--focus X Y]
     (X Y: the point to keep sharp, in the finished 1080 x 1920 picture; default the middle)
"""
import json
import sys
from pathlib import Path

import cv2
import numpy
from PIL import Image

arguments = sys.argv[1:]
drawn_path, finished_path = Path(arguments[0]), Path(arguments[1])
focus_point = (540, 960)
if '--focus' in arguments:
    where = arguments.index('--focus')
    focus_point = (int(arguments[where + 1]), int(arguments[where + 2]))

FINISHED_WIDTH, FINISHED_HEIGHT = 1080, 1920
drawn = numpy.asarray(Image.open(drawn_path).convert('RGB')).astype(numpy.float32)

# 1. glow around warm, bright light
red, green, blue = drawn[..., 0], drawn[..., 1], drawn[..., 2]
brightness = 0.3 * red + 0.59 * green + 0.11 * blue
warm_and_bright = numpy.clip((red - blue - 60) / 70, 0, 1) * numpy.clip((brightness - 150) / 70, 0, 1)
glow_source = drawn * warm_and_bright[..., None]
glow = cv2.GaussianBlur(glow_source, (0, 0), 26) * 0.9 + cv2.GaussianBlur(glow_source, (0, 0), 70) * 0.6
drawn = drawn + glow * numpy.array([1.0, 0.82, 0.6], dtype=numpy.float32)

# 2. shrink
picture = cv2.resize(numpy.clip(drawn, 0, 255), (FINISHED_WIDTH, FINISHED_HEIGHT), interpolation=cv2.INTER_AREA)

# 3. background blur from the distance picture
distance_picture_path = drawn_path.with_name(drawn_path.stem + '-distance.png')
distance_settings_path = drawn_path.with_name(drawn_path.stem + '-distance.json')
if distance_picture_path.exists() and distance_settings_path.exists():
    settings = json.loads(distance_settings_path.read_text())
    share = numpy.asarray(Image.open(distance_picture_path).convert('L')).astype(numpy.float32) / 255
    share = cv2.resize(share, (FINISHED_WIDTH, FINISHED_HEIGHT), interpolation=cv2.INTER_AREA)
    distance = settings['near'] + share * (settings['far'] - settings['near'])
    focus_x, focus_y = focus_point
    focus_distance = float(numpy.median(distance[focus_y - 6:focus_y + 7, focus_x - 6:focus_x + 7]))
    blur_amount = numpy.clip(6.0 * numpy.abs(distance - focus_distance) / focus_distance, 0, 1.4)
    blur_amount = cv2.GaussianBlur(blur_amount, (0, 0), 3)
    levels = [0.0, 1.0, 2.0, 3.0, 4.0]
    blurred = [picture if level == 0 else cv2.GaussianBlur(picture, (0, 0), level) for level in levels]
    result = numpy.zeros_like(picture)
    for index, level in enumerate(levels):
        weight = numpy.clip(1 - numpy.abs(blur_amount - level), 0, 1)
        result += blurred[index] * weight[..., None]
    picture = result
    print(f'focus at {focus_point}, {focus_distance:.2f} units from the camera')

# 4. soft corners and fine grain
rows, columns = numpy.mgrid[0:FINISHED_HEIGHT, 0:FINISHED_WIDTH]
distance_from_centre = numpy.sqrt(((rows - FINISHED_HEIGHT * 0.5) / (FINISHED_HEIGHT * 0.62)) ** 2 + ((columns - FINISHED_WIDTH * 0.5) / (FINISHED_WIDTH * 0.75)) ** 2)
picture *= (1.0 - 0.38 * numpy.clip(distance_from_centre - 0.35, 0, 1) ** 1.6)[..., None]
picture += numpy.random.default_rng(15).normal(0, 2.2, size=(FINISHED_HEIGHT, FINISHED_WIDTH, 1))

Image.fromarray(numpy.clip(picture, 0, 255).astype(numpy.uint8)).save(finished_path, optimize=True)
print(finished_path)
