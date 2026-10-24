import bpy
out = {}
for g in ('barrels', 'crates', 'lamp-post', 'cart'):
    grp = bpy.data.objects[g]; gm = grp.matrix_world.inverted()
    pts = [gm @ o.matrix_world @ v.co for o in grp.children_recursive if o.type == 'MESH' for v in o.data.vertices]
    out[g] = [[round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]]
result = out
