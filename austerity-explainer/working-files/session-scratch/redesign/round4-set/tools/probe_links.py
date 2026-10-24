import bpy
for name in ('no-1-yard-dusk', 'no-1-room-light', 'no-2-room-light'):
    light = bpy.data.objects.get(name)
    c = light.light_linking.receiver_collection if light else None
    print('PROBE', name, light is not None, c.name if c else None, [o.name for o in c.objects] if c else None)
print('PROBE mill names', sorted(o.name for o in bpy.data.objects if o.name.startswith('no-1-mill') or o.name.startswith('no-1-yard') or o.name.startswith('no-1-loading') or o.name.startswith('no-1-doorway')))
