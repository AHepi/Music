# What this does: prints the materials the doorway workers wear and the lights that reach them (scratch, round 5).
import bpy
for name in ('no-1-worker-1', 'no-2-worker-1'):
    holder = bpy.data.objects[name]
    mats = set()
    for o in holder.children_recursive:
        if o.type == 'MESH':
            for slot in o.material_slots:
                mats.add((slot.link, slot.material.name if slot.material else None))
    print('WORKER', name, sorted(mats))
for light in bpy.data.objects:
    if light.type == 'LIGHT' and not light.hide_render and light.data.energy > 0:
        rc = light.light_linking.receiver_collection
        print('LIGHT', light.name, light.data.type, round(light.data.energy, 1), 'linked' if rc else '')
