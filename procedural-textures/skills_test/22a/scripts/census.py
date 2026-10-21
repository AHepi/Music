# What this does: counts what is in the street copy (objects by kind, triangles, parents, scales, hidden things). Changes nothing, saves nothing.
import bpy, collections
sc = bpy.context.scene
kinds = collections.Counter(o.type for o in sc.objects)
print('KINDS', dict(kinds), 'total objects', len(sc.objects))
meshes = [o for o in sc.objects if o.type == 'MESH']
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
print('MESH OBJECTS', len(meshes), 'unique meshes', len({o.data.name for o in meshes}), 'triangles (sum over objects)', tris)
print('HIDDEN (viewport)', sum(1 for o in meshes if o.hide_viewport), 'HIDDEN (render)', sum(1 for o in meshes if o.hide_render), 'HIDE_GET', sum(1 for o in meshes if not o.visible_get()))
print('WITH PARENT', sum(1 for o in sc.objects if o.parent), 'EMPTIES', kinds.get('EMPTY', 0))
print('WITH MODIFIERS', [(o.name, [m.type for m in o.modifiers]) for o in meshes if o.modifiers][:20], 'count', sum(1 for o in meshes if o.modifiers))
odd = [(o.name, tuple(round(s, 3) for s in o.scale)) for o in meshes if any(abs(s - 1) > 1e-3 for s in o.scale)]
print('NON-UNIT SCALE', len(odd), odd[:20])
par = [(o.name, o.parent.name, tuple(round(s, 3) for s in o.parent.scale)) for o in meshes if o.parent and any(abs(s - 1) > 1e-3 for s in o.parent.scale)]
print('PARENT SCALE', len(par), par[:10])
neg = [o.name for o in meshes if o.matrix_world.determinant() < 0]
print('NEGATIVE DET', len(neg), neg[:20])
nouv = [o.name for o in meshes if not o.data.uv_layers]
print('NO UV', len(nouv), nouv[:30])
nomat = [o.name for o in meshes if not o.data.materials or None in list(o.data.materials)]
print('NO MATERIAL', len(nomat), nomat[:30])
big = sorted(meshes, key=lambda o: -len(o.data.polygons))[:10]
print('BIGGEST', [(o.name, len(o.data.polygons)) for o in big])
cols = collections.Counter()
for o in meshes:
    c = o.users_collection[0].name if o.users_collection else '-'
    cols[c] += 1
print('COLLECTIONS', dict(cols))
print('NAMES SAMPLE', sorted(o.name for o in meshes)[:400:8])
print('FRAMES', sc.frame_start, sc.frame_end, 'animated objs', sum(1 for o in sc.objects if o.animation_data))
