# What this does: tells you where spots on a painted room with depth (a "relief") sit in the 3D world,
# so you can stand cut-outs and models on its floor or tables. It uses the same sums as
# CinemaKit.relief(): the relief camera is at the origin looking along -z, the painting fills a
# fov-degree view, and each spot is pushed back between `near` and `far` by its depth (light = near).
#
# Use:  python3 -I relief_points.py RELIEF_FOLDER NAME [--near 5] [--far 60] [--fov 40] [u,v ...]
# With no u,v pairs it prints a grid (u across 0..1 left to right, v up 0..1 bottom to top).
import sys, math
from PIL import Image

def main():
    args = sys.argv[1:]
    folder, name = args[0], args[1]
    near, far, fov = 5.0, 60.0, 40.0
    spots = []
    i = 2
    while i < len(args):
        if args[i] == '--near': near = float(args[i + 1]); i += 2
        elif args[i] == '--far': far = float(args[i + 1]); i += 2
        elif args[i] == '--fov': fov = float(args[i + 1]); i += 2
        else: spots.append(tuple(float(x) for x in args[i].split(','))); i += 1
    painting = Image.open(f'{folder}/{name}.jpg')
    depth = Image.open(f'{folder}/{name}-depth.png').convert('L')
    aspect = painting.width / painting.height
    tan_y = math.tan(math.radians(fov / 2)); tan_x = tan_y * aspect
    def depth_at(u, v):
        x = min(depth.width - 1, max(0, round(u * (depth.width - 1))))
        y = min(depth.height - 1, max(0, round((1 - v) * (depth.height - 1))))
        return depth.getpixel((x, y)) / 255
    def point_at(u, v):
        w = depth_at(u, v)
        d = 1 / (w / near + (1 - w) / far)
        return ((u * 2 - 1) * tan_x * d, (v * 2 - 1) * tan_y * d, -d)
    if not spots:
        spots = [(u / 10, v / 10) for v in range(9, -1, -1) for u in (1, 3, 5, 7, 9)]
    for u, v in spots:
        x, y, z = point_at(u, v)
        print(f'u={u:.2f} v={v:.2f}  ->  x={x:6.2f} y={y:6.2f} z={z:7.2f}')

main()
