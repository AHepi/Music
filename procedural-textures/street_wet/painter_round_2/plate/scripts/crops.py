# What this does (plain words): cuts a crop out of a picture (at a given scale) and writes a JPEG. Use: python3 -I crops.py IN OUT x0 y0 w h [scale]
import sys, cv2
src, out, x0, y0, w, h = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
im = cv2.imread(src)
c = im[y0:y0+h, x0:x0+w]
if scale != 1.0:
    c = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
cv2.imwrite(out, c, [cv2.IMWRITE_JPEG_QUALITY, 88])
