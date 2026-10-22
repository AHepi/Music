# Where is the lantern window on the 960x640 picture, and how many stops brighter is it than the stone around it (linear EXR, Combined layer)?
import bpy, sys, json, math
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import OpenImageIO as oiio
a = sys.argv[sys.argv.index('--')+1:]; exr = a[0]; W, H = int(a[1]), int(a[2])
sc = bpy.context.scene; cam = bpy.data.objects.get('photo') or bpy.data.objects['Camera']; sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
win = bpy.data.objects['Lantern window glow']
dg = bpy.context.evaluated_depsgraph_get(); me = win.evaluated_get(dg).to_mesh()
pts = [world_to_camera_view(sc, cam, win.matrix_world @ v.co) for v in me.vertices]
xs = [p.x * W for p in pts]; ys = [(1 - p.y) * H for p in pts]
box = (min(xs), min(ys), max(xs), max(ys)); print('window box px', [round(v, 1) for v in box])
inp = oiio.ImageInput.open(exr); parts = []; i = 0
while inp.seek_subimage(i, 0): parts.append(inp.spec().getattribute('name') or ''); i += 1
inp.close()
k = parts.index('ViewLayer.Combined')
inp = oiio.ImageInput.open(exr); inp.seek_subimage(k, 0); sp = inp.spec()
C = np.array(inp.read_image(k, 0, 0, 3, 'float'), dtype=np.float32).reshape(sp.height, sp.width, 3); inp.close()
lum = 0.2126*C[..., 0] + 0.7152*C[..., 1] + 0.0722*C[..., 2]
x0, y0, x1, y1 = [int(round(v)) for v in box]
inner = lum[y0:y1+1, x0:x1+1]
pad = 12
outer = lum[max(0,y0-pad):y1+pad+1, max(0,x0-pad):x1+pad+1].copy()
mask = np.ones_like(outer, bool); mask[pad:pad+(y1-y0+1), pad:pad+(x1-x0+1)] = False
ring = outer[mask]
print('window pixels', inner.shape, 'mean lum %.3f max %.3f' % (inner.mean(), inner.max()))
print('surround ring mean %.3f median %.3f' % (ring.mean(), np.median(ring)))
print('STOPS window-mean over surround-median: %.2f ; over surround-mean: %.2f' % (math.log2(inner.mean()/np.median(ring)), math.log2(inner.mean()/ring.mean())))
# pond region: reflection of lantern? brightest pond pixels vs median
pw = bpy.data.objects['Pond water']; me2 = pw.evaluated_get(dg).to_mesh()
pp = [world_to_camera_view(sc, cam, pw.matrix_world @ v.co) for v in me2.vertices]
px0, px1 = max(0, int(min(p.x for p in pp)*W)), min(W-1, int(max(p.x for p in pp)*W)); py0, py1 = max(0, int((1-max(p.y for p in pp))*H)), min(H-1, int((1-min(p.y for p in pp))*H))
reg = lum[py0:py1, px0:px1]; print('pond screen box', px0, py0, px1, py1, 'median %.4f p99 %.3f max %.3f' % (np.median(reg), np.percentile(reg, 99), reg.max()))
