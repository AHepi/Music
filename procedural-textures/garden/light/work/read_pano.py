import bpy, sys, math
a = sys.argv[sys.argv.index('--')+1:]
img = bpy.data.images.load(a[0]); W, H = img.size
px = list(img.pixels)
def lum(x, y):
    i = (y * W + x) * 4; return 0.2126 * px[i] + 0.7152 * px[i+1] + 0.0722 * px[i+2]
def rgb(x, y):
    i = (y * W + x) * 4; return tuple(round(v, 3) for v in px[i:i+3])
best = max(((lum(x, y), x, y) for y in range(H) for x in range(W)))
l, x, y = best
az = 90 - ((x + 0.5) / W - 0.5) * 360; el = ((y + 0.5) / H - 0.5) * 180
print('BRIGHTEST lum %.2f at pixel (%d,%d) -> azimuth %.1f elevation %.1f  (sun lamp: az -165.5=194.5, el 12.9)' % (l, x, y, az % 360, el))
# profile at opposite-sun azimuth (anti-solar, e.g. az 14.5 = hero view side) and at the sun azimuth, by elevation
for name, azdeg in (('anti-solar az 14', 14.5), ('hero az 57', 57.0), ('sun az 194', 194.5), ('side az 285', 285.0)):
    u = 0.5 + (90 - azdeg) / 360.0; x = int((u % 1.0) * W)
    row = []
    for eld in (-10, -1, 1, 3, 6, 10, 15, 20, 30, 45, 60, 80):
        y = int((0.5 + eld / 180.0) * H); y = min(H-1, max(0, y))
        row.append('%d:%s' % (eld, rgb(x, y)))
    print(name, ' | '.join(row))
