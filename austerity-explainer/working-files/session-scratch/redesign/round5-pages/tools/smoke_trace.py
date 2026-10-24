# What this does: traces where each chimney's smoke plume lies on the film frame (1080 x 1920) in the Works' views,
# with the same sums as ChimneySmoke in works-effects.js (round 5: the wind across the view, small dense puffs near the
# chimney's mouth). It reads the chimney tops and camera spots from works-shot.json, so it follows the set helper's
# changes. For each view, chimney and age it prints the puff's middle (across, down: shares of the frame), its width
# (share of the frame's height) and how strong it is.
# Use: python3 smoke_trace.py WORKS_SHOT_JSON SETTINGS_JSON
#   SETTINGS_JSON: {"wind": [x, y, z] (three.js axes), "kinds": {"heavy": {life, rise, drift, mouth: {seconds, size},
#                   size: [a, b], opacity, fade}, ...}}
import json, math, sys

shot = json.load(open(sys.argv[1]))
settings = json.load(open(sys.argv[2]))
wx, wy, wz = settings['wind']
n = math.sqrt(wx * wx + wy * wy + wz * wz); wx, wy, wz = wx / n, wy / n, wz / n
tan_half = math.tan(math.radians(shot.get('film_fov_degrees', 60.4) / 2)); aspect = 1080 / 1920
tops = shot['chimney_tops']


def puff(kind, age):
    """the puff's offset from the chimney top (three.js axes), its width (metres) and strength at this age"""
    k = age / kind['life']
    climb = kind['rise'] * k ** kind.get('rise_power', 0.75)
    blown = kind['drift'] * k ** kind.get('drift_power', 1.25)
    mouth = kind.get('mouth', {'seconds': 0, 'size': kind['size'][0]})
    if age < mouth['seconds']:
        size = mouth['size'] + (kind['size'][0] - mouth['size']) * (age / mouth['seconds'])
    else:
        rest = (age - mouth['seconds']) / max(1e-6, kind['life'] - mouth['seconds'])
        size = kind['size'][0] + (kind['size'][1] - kind['size'][0]) * rest ** 0.8
    strength = kind['opacity'] * min(1, age / 0.2) * (1 - k) ** kind.get('fade', 1.0)
    return (wx * blown, 0.3 + climb + wy * blown, wz * blown), size, strength


def on_frame(camera, point):
    cx, cy, cz = camera                     # Blender
    X, Y, Z = point                         # three.js
    ahead = -Z - cy                         # metres ahead of the camera (Blender y)
    return (0.5 + 0.5 * (X - cx) / (ahead * tan_half * aspect), 0.5 - 0.5 * (Y - cz) / (ahead * tan_half)), ahead


for view, spots in shot['views'].items():
    if view == 'w4':
        continue
    for spot in ('plate', 'composed'):
        camera = spots.get(spot)
        if not camera:
            continue
        print(f'== {view} {spot} (camera {camera})')
        for kind_name, kind in settings['kinds'].items():
            for name, (x, y, z) in tops.items():
                top = (x, z, -y)
                row = []
                for age in (0, 0.5, 1, 2, 3, 4, 6, 8, kind['life'] * 0.95):
                    if age > kind['life']:
                        continue
                    (ox, oy, oz), size, strength = puff(kind, age)
                    (sx, sy), ahead = on_frame(camera, (top[0] + ox, top[1] + oy, top[2] + oz))
                    width = size / (2 * ahead * tan_half)
                    row.append(f'{age:g}s:({sx:.2f},{sy:.3f}) w{width:.3f} top{sy - width / 2:.3f} a{strength:.2f}')
                print(f'  {kind_name:6} {name:20} ' + '  '.join(row))
