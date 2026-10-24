# What this does: reads the village run's finished scene (never saved) and, on a grid of points beside the road in View road_eye, finds the
# height of every ground object at that point (a ray from above into each object alone), to see whether one ground object lies over another.
# Run: blender -b --disable-autoexec FINISHED.blend -P probe_ground_layers.py
import json
import bpy
from mathutils import Vector

depsgraph = bpy.context.evaluated_depsgraph_get()
ground = [o for o in bpy.data.objects if o.type == 'MESH' and (o.get('place_role') or '').startswith('ground.')]
result = {'ground_objects': {}, 'points': []}
for obj in ground:
    evaluated = obj.evaluated_get(depsgraph)
    result['ground_objects'][obj.name] = {'role': obj.get('place_role'), 'faces': len(obj.data.polygons), 'modifiers': [m.type for m in obj.modifiers],
                                         'materials': [m.name for m in obj.data.materials if m], 'bounds_x': [round(min((obj.matrix_world @ Vector(c)).x for c in obj.bound_box), 1), round(max((obj.matrix_world @ Vector(c)).x for c in obj.bound_box), 1)],
                                         'displacement': [m.displacement_method for m in obj.data.materials if m]}
overlaps = 0
for x in [-58 + 1.0 * i for i in range(19)]:
    for y in [-9 + 1.0 * j for j in range(14)]:
        heights = {}
        for obj in ground:
            inverse = obj.matrix_world.inverted()
            origin = inverse @ Vector((x, y, 50.0))
            direction = (inverse.to_3x3() @ Vector((0, 0, -1))).normalized()
            evaluated = obj.evaluated_get(depsgraph)
            found, location, normal, index = evaluated.ray_cast(origin, direction)
            if found:
                heights[obj.name] = round((obj.matrix_world @ location).z, 3)
        if len(heights) > 1:
            overlaps += 1
            result['points'].append({'x': x, 'y': y, 'heights': heights})
result['overlap_points'] = overlaps
print('LAYERS ' + json.dumps(result, indent=1))
