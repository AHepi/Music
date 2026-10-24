# What this does: lists, for a checker, how a finished village stores its scattered pieces, its grounds and its buildings (read only, never saved).
import bpy, collections
scene = bpy.context.scene
scatter = [o for o in scene.objects if o.get('pk_scatter')]
print('scatter objects', len(scatter))
for o in scatter[:40]:
    print('  ', o.name, o.get('pk_scatter_kind'), o.get('pk_scatter_group'), o.get('pk_count'), 'roots text:', bool(bpy.data.texts.get('pk_roots_' + o.name)), len(o.data.vertices), o.get('pk_sites'))
keys = collections.Counter()
for o in scene.objects:
    for k in o.keys():
        keys[k] += 1
print('custom keys', keys.most_common(40))
roles = collections.Counter(o.get('pk_role') for o in scene.objects)
print('roles', roles.most_common(80))
for o in scene.objects:
    if o.name.startswith('Ground') or 'verge' in o.name.lower():
        print('ground', o.name, o.type, o.get('pk_role'), [m.name for m in o.data.materials] if o.type == 'MESH' else None, len(o.data.vertices) if o.type=='MESH' else None, [ (m.type, m.name) for m in o.modifiers])
print('collections', [c.name for c in bpy.data.collections])
print('texts', len(bpy.data.texts), [t.name for t in bpy.data.texts][:10])
