# What this does: opens the scene (read-only) and writes a JSON snapshot of object names + material names + a few world/light/render fields, so before/after can be compared.
import bpy, sys, json, math
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
def objinfo(o):
    d = {'type': o.type, 'loc': [round(v,3) for v in o.location], 'rot': [round(v,4) for v in o.rotation_euler], 'scale': [round(v,3) for v in o.scale],
         'hide_render': o.hide_render, 'mats': [s.material.name if s.material else None for s in o.material_slots],
         'owner': o.get('garden_owner'), 'role': o.get('garden_role'), 'data': o.data.name if o.data else None}
    if o.type == 'MESH':
        d['nv'] = len(o.data.vertices); d['nf'] = len(o.data.polygons)
        d['vsum'] = round(sum(sum(v.co) for v in o.data.vertices), 4)
    if o.type == 'LIGHT':
        d['energy'] = o.data.energy; d['color'] = [round(v,3) for v in o.data.color]; d['ltype'] = o.data.type
    return d
R = {'objects': {o.name: objinfo(o) for o in bpy.data.objects}, 'materials': sorted(m.name for m in bpy.data.materials),
     'collections': sorted(c.name for c in bpy.data.collections), 'world': sc.world.name if sc.world else None,
     'camera': sc.camera.name if sc.camera else None, 'engine': sc.render.engine, 'res': [sc.render.resolution_x, sc.render.resolution_y],
     'view': [sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure]}
json.dump(R, open(out, 'w'), indent=1)
print('SNAP', out, len(R['objects']), len(R['materials']))
