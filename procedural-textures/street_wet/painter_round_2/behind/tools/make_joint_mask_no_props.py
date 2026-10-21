# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Draws the plate step's JOINT MEASURING MASK (red = a sett joint, green = a stone face, blue = road) for the lockout plate camera at 1536 x 2730 WITH THE FILM'S NEAR PROPS HIDDEN, so the
# joints can be measured on the road where the props stood. It uses the plate step's own mask drawing function (study/tools/b02_lighting_and_variants.py render_mask) unchanged; the
# film's lockout shot file is opened READ-ONLY (never saved). Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec LOCKOUT.blend --python make_joint_mask_no_props.py -- OUT.png
import sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/study/tools')
sys.dont_write_bytecode = True
import bpy
import b02_lighting_and_variants as lv
from mathutils import Vector

out_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
W, H = 1536, 2730
FILM_NEAR_PROPS = ['handcart', 'coal-sacks', 'coal-pile', 'wooden-pail', 'hurricane-lantern', 'spade', 'brazier', 'dustbins', 'notice-on-board', 'Cube']
FILM_NEAR_METRES = 16.0
PLATE_CAMERA_AT = (-1.0, 1.2, 1.69709)


def top(obj):
    while obj.parent is not None:
        obj = obj.parent
    return obj


roots = {}
for obj in scene.objects:
    if obj.type in ('LIGHT', 'CAMERA'):
        continue
    r = top(obj)
    if r.type in ('LIGHT', 'CAMERA'):
        continue
    roots.setdefault(r.name, [r, []])[1].append(obj)
hidden = 0
for name, (root, members) in sorted(roots.items()):
    if not any(name.startswith(p) for p in FILM_NEAR_PROPS):
        continue
    pts = []
    for m in members:
        if m.type == 'MESH':
            pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    centre = sum(pts, Vector()) / len(pts) if pts else root.matrix_world.translation
    if (centre - Vector(PLATE_CAMERA_AT)).length < FILM_NEAR_METRES:
        for m in members:
            m.hide_render = True
            hidden += 1
print('hidden objects', hidden, flush=True)

cam = scene.camera
print('camera', cam.name, tuple(round(v, 4) for v in cam.matrix_world.translation), flush=True)
lv.render_mask(out_path, W, H)
print('WROTE', out_path, flush=True)
