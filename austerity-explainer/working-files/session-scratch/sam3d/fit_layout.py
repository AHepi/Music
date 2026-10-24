"""What this does: works out how SAM 3D's layout (each object's size, turn and position in its own
camera) maps onto the painting. It tries the two likely ways the model files are oriented, finds
SAM's lens width that best fits, and reports how well each object's outline box lands on the box we
marked in the painting (1.0 = exactly).
Use: blender-env/bin/python fit_layout.py METADATA.json FOLDER_WITH_OBJECT_GLBS"""
import json, sys, glob
import numpy as np
import bpy

W, H = 1536, 2736
BOXES = [(15, 1415, 655, 1885), (290, 1245, 645, 1460), (740, 1245, 860, 1575), (880, 1275, 1030, 1645), (1065, 1200, 1250, 1705)]
meta = json.load(open(sys.argv[1]))['objects']
files = sorted(glob.glob(sys.argv[2] + '/object-*.glb'))

def vertices(path):
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=path)
    o = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    m = np.array(o.matrix_world)
    v = np.array([(m @ np.array([*p.co, 1.0]))[:3] for p in o.data.vertices])
    return v                         # Blender frame (z up)

def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

blender = [vertices(f) for f in files]
g = [np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1) for v in blender]   # glTF frame (y up)
def turn(axis, degrees):
    a = np.radians(degrees); c, s_ = np.cos(a), np.sin(a)
    return {'x': np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]]), 'y': np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]]),
            'z': np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])}[axis]
frames = {}
for axis in 'xyz':
    for deg in (0, 90, 180, 270):
        if deg == 0 and axis != 'x': continue
        frames[f'gltf turned {deg} about {axis}'] = [(turn(axis, deg) @ v.T).T for v in g]
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy; ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua
best = None
for name, verts in frames.items():
    for wxyz in (False, True):
        for inverse in (False, True):
          for x_left in (True, False):
            for tan_x in np.linspace(0.2, 0.42, 23):
                tan_y = tan_x * H / W
                scores, boxes = [], []
                for k, v in enumerate(verts):
                    q = meta[k]['rotation'][0]
                    if wxyz: q = [q[1], q[2], q[3], q[0]]
                    R = quat_matrix(q)
                    if inverse: R = R.T
                    p = (R @ (v * meta[k]['scale'][0][0]).T).T + np.array(meta[k]['translation'][0])
                    sx = -1 if x_left else 1
                    u = (0.5 + 0.5 * sx * (p[:, 0] / p[:, 2]) / tan_x) * W
                    yy = (0.5 - 0.5 * (p[:, 1] / p[:, 2]) / tan_y) * H
                    box = (u.min(), yy.min(), u.max(), yy.max()); boxes.append(box)
                    scores.append(iou(box, BOXES[k]))
                score = float(np.mean(scores))
                if best is None or score > best[0]:
                    best = (score, name, ('w first' if wxyz else 'w last') + (', inverse' if inverse else ''), 'x left' if x_left else 'x right', tan_x, scores, boxes)
    print(f'{name}: best so far {best[0]:.3f}')
score, name, order, xs, tan_x, scores, boxes = best
print(f'BEST: model frame {name}, quaternion {order}, {xs}, lens tanX {tan_x:.3f} (vertical field {2*np.degrees(np.arctan(tan_x*H/W)):.1f} degrees), mean box match {score:.3f}')
for k in range(len(scores)):
    print(f'  object {k+1}: match {scores[k]:.3f}, projected box {tuple(int(x) for x in boxes[k])}, marked {BOXES[k]}')
