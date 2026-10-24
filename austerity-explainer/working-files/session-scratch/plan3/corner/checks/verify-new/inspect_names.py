# What this does: lists the top-level objects and children of the props I plan to move (for verify-new).
import bpy
pre = ('notice', 'tacks', 'gas-lamp', 'wooden-barrel', 'dustbins', 'coal-sacks', 'kitchen-chair', 'brazier', 'hurricane', 'lantern', 'wooden-pail', 'handcart')
for o in bpy.context.scene.objects:
    if o.name.startswith(pre):
        bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
        lo = [min(p[i] for p in bb) for i in range(3)]; hi = [max(p[i] for p in bb) for i in range(3)]
        print('OBJ', o.name, 'type', o.type, 'parent', o.parent.name if o.parent else None, 'loc', tuple(round(v, 3) for v in o.matrix_world.translation),
              'lo', tuple(round(v, 3) for v in lo), 'hi', tuple(round(v, 3) for v in hi))
