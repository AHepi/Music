# Measures the brazier drum prop: its width and height, and its wall's inner radius near the top.
import bpy, sys, os
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/blender/pit-village')
from set_dressing import PROPS_FOLDER
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(PROPS_FOLDER, 'brazier-drum.glb'))
points = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        points += [o.matrix_world @ v.co for v in o.data.vertices]
xs = [p.x for p in points]; ys = [p.y for p in points]; zs = [p.z for p in points]
print('width x', min(xs), max(xs), 'depth y', min(ys), max(ys), 'height', min(zs), max(zs))
top = max(zs)
for band in (0.0, 0.03, 0.08, 0.15, 0.25):
    ring = [p for p in points if abs(p.z - (top - band)) < 0.02]
    if ring:
        radii = sorted(((p.x ** 2 + p.y ** 2) ** 0.5) for p in ring)
        print(f'{band:.2f} below top: radii {radii[0]:.3f} .. {radii[-1]:.3f} ({len(ring)} points)')
