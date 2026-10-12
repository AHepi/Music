# What this does: says where things will land in the tall 1080 x 1920 frame for a camera position,
# without drawing anything, so a shot can be framed in seconds instead of by rendering stills.
# For each named point it prints its pixel position and whether it is inside the frame and clear of
# the edges (140 pixels at the sides and top, 380 at the bottom where phone buttons sit).
#
# Use: python3 -I frame_check.py CAMERA_X,Y,Z TARGET_X,Y,Z FOV NAME=X,Y,Z [NAME=X,Y,Z ...]
#   e.g. python3 -I frame_check.py 0.55,1.45,8.9 -1.15,0.85,3.0 40 board=-0.15,1.05,3.75 door=-1.4,0.3,3.2
# FOV is the vertical lens angle in degrees (as in kit.stillShot).

import math
import sys

WIDTH, HEIGHT = 1080, 1920


def parse(text): return [float(v) for v in text.split(',')]


def project(camera, target, fov, point):
    forward = [t - c for t, c in zip(target, camera)]
    n = math.sqrt(sum(v * v for v in forward)); forward = [v / n for v in forward]
    right = [forward[1] * 0 - forward[2] * 1, forward[2] * 0 - forward[0] * 0, forward[0] * 1 - forward[1] * 0]
    right = [-forward[2], 0.0, forward[0]]
    n = math.sqrt(sum(v * v for v in right)); right = [v / n for v in right]
    up = [right[1] * forward[2] - right[2] * forward[1], right[2] * forward[0] - right[0] * forward[2], right[0] * forward[1] - right[1] * forward[0]]
    d = [p - c for p, c in zip(point, camera)]
    depth = sum(a * b for a, b in zip(d, forward))
    if depth <= 0: return None, None, depth
    tan_y = math.tan(math.radians(fov / 2)); tan_x = tan_y * WIDTH / HEIGHT
    x = sum(a * b for a, b in zip(d, right)) / depth / tan_x
    y = sum(a * b for a, b in zip(d, up)) / depth / tan_y
    return (x + 1) / 2 * WIDTH, (1 - y) / 2 * HEIGHT, depth


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Use: python3 -I frame_check.py CAMERA_X,Y,Z TARGET_X,Y,Z FOV NAME=X,Y,Z ...'); sys.exit(1)
    camera, target, fov = parse(sys.argv[1]), parse(sys.argv[2]), float(sys.argv[3])
    for item in sys.argv[4:]:
        name, value = item.split('=')
        px, py, depth = project(camera, target, fov, parse(value))
        if px is None:
            print(f'{name:>14}: behind the camera'); continue
        inside = 0 <= px <= WIDTH and 0 <= py <= HEIGHT
        clear = 140 <= px <= WIDTH - 140 and 140 <= py <= HEIGHT - 380
        print(f'{name:>14}: x {px:6.0f}  y {py:6.0f}  distance {depth:5.2f}  {"clear" if clear else "inside, near an edge" if inside else "OUT OF FRAME"}')
