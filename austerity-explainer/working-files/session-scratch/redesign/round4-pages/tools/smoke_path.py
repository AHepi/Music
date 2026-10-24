# What this does: works out where a chimney's smoke plume lands on the film frame in W1, W2 and W3 for given smoke
# settings (the same sums as works-effects.js ChimneySmoke), so the wind and plume can be chosen before drawing.
# Use: python3 smoke_path.py WIND_X WIND_Y_UP WIND_TOWARD_CAMERA RISE DRIFT  (wind in three.js axes)
import sys, math
wx, wy, wz, rise, drift = map(float, sys.argv[1:6])
n = math.sqrt(wx*wx + wy*wy + wz*wz); wx, wy, wz = wx/n, wy/n, wz/n
tops = {'no-1': (-5.3, 57.0, 26.3), 'no-2-a': (5.3, 57.0, 25.3), 'no-2-b': (8.6, 60.5, 23.3)}
cams = {'w1': (-4.1, 10.2, 1.841), 'w2': (4.1, 10.2, 1.841), 'w3': (0.0, -7.95, 4.74)}
t = math.tan(math.radians(60.4 / 2)); a = 1080 / 1920
for view, (cx, cy, cz) in cams.items():
    print('==', view)
    for name, (x, y, z) in tops.items():
        pts = []
        for k in (0, 0.15, 0.3, 0.5, 0.7, 1.0):
            climb = rise * k ** 0.75; blown = drift * k ** 1.25
            # three.js: X = x, Y = z, Z = -y ; wind in three.js axes
            X = x + wx * blown; Y = z + 0.3 + climb + wy * blown; Z = -y + wz * blown
            d = -Z - cy   # distance ahead of the camera (Blender y)
            sx = 0.5 + 0.5 * (X - cx) / (d * t * a); sy = 0.5 - 0.5 * (Y - cz) / (d * t)
            pts.append(f'k{k}:({sx:.2f},{sy:.2f})')
        print(' ', name, ' '.join(pts))
