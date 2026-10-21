# What this does: lists every object in the street copy (name, type, location, size, material names, vertex counts), so I know where the gutter is. Changes and saves nothing.
import bpy
sc = bpy.context.scene
print('FILE', bpy.data.filepath, 'engine', sc.render.engine, 'unit scale', sc.unit_settings.scale_length, 'frame', sc.frame_current)
for o in sorted(sc.objects, key=lambda o: o.name):
    mats = [s.material.name for s in o.material_slots if s.material]
    extra = ''
    if o.type == 'MESH':
        extra = f'v={len(o.data.vertices)} f={len(o.data.polygons)} mods={[m.type for m in o.modifiers]}'
    print('OBJ', o.type, o.name, tuple(round(v, 2) for v in o.location), 'dim', tuple(round(v, 2) for v in o.dimensions), 'parent', o.parent.name if o.parent else None, mats[:3], extra)
print('COLLECTIONS', [(c.name, len(c.objects)) for c in bpy.data.collections])
