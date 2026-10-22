import bpy, sys, numpy as np, math
p = sys.argv[sys.argv.index('--') + 1]
im = bpy.data.images.load(p); w, h = im.size
a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
# rows: image row 0 is the bottom (-90 deg), last row is the top (+90). Average over all columns and also report min/max across columns (to see sun-side glow)
for elev in (-60, -30, -10, 0, 5, 10, 15, 20, 25, 30, 35, 45, 60, 80):
    r = int(round((elev + 90) / 180 * (h - 1)))
    row = a[r, :, :3]
    print(f'elev {elev:4d} deg  mean RGB {row.mean(0).round(3)}  min {row.min(0).round(3)}  max {row.max(0).round(3)}')
print('PROFILE_DONE')
