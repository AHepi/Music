# What this does: reads the village run's finished scene (read-only, never saved) and prints what lies under chosen pixels of the
# view cameras (by casting a ray), and the facts about the scatter pieces and the thatch material, to find the causes of the
# dark specks, the white sparkles on the thatch and the flat brown rectangles beside the road.
# Run: blender -b --disable-autoexec FINISHED.blend -P probe_village.py
import json
import bpy
from mathutils import Vector

scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def ray_from_pixel(camera, px, py, width, height):
    """World ray through pixel (px, py) of a picture width x height (y from the top)."""
    frame = camera.data.view_frame(scene=scene)
    # frame corners: top-right, bottom-right, bottom-left, top-left (camera space)
    tr, br, bl, tl = frame
    u = px / width
    v = py / height
    top = tl.lerp(tr, u)
    bottom = bl.lerp(br, u)
    point = top.lerp(bottom, v)
    world_point = camera.matrix_world @ point
    origin = camera.matrix_world.translation
    return origin, (world_point - origin).normalized()


def hit(camera_name, px, py, width=1200, height=800):
    camera = bpy.data.objects[camera_name]
    origin, direction = ray_from_pixel(camera, px, py, width, height)
    found, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, origin, direction)
    if not found:
        return {'pixel': [px, py], 'hit': None}
    slot = None
    try:
        mesh = obj.evaluated_get(depsgraph).data
        poly = mesh.polygons[index]
        slot = obj.material_slots[poly.material_index].material.name if obj.material_slots and obj.material_slots[poly.material_index].material else None
    except Exception as problem:
        slot = f'? {problem}'
    return {'pixel': [px, py], 'object': obj.name, 'role': obj.get('place_role'), 'owner': obj.get('place_owner'), 'material': slot,
            'distance': round((location - origin).length, 2), 'location': [round(v, 2) for v in location], 'normal': [round(v, 2) for v in normal]}


report = {}
# the flat brown rectangles in View road_eye (left about x 0-230, y 545-650; right about x 930-1200, y 565-700)
report['road_eye_brown'] = [hit('View road_eye', x, y) for x, y in ((60, 600), (150, 580), (200, 620), (1000, 600), (1100, 640), (1150, 680))]
report['road_eye_grass'] = [hit('View road_eye', x, y) for x, y in ((60, 700), (1100, 520))]
report['road_eye_road'] = [hit('View road_eye', x, y) for x, y in ((600, 700),)]
# the dark specks in View road_eye: (440, 512), (695, 505), (590, 580), (230, 690)
report['road_eye_specks'] = [hit('View road_eye', x, y) for x, y in ((440, 512), (695, 506), (592, 580), (230, 692), (775, 460))]
# the thatch in View wide
report['wide_thatch'] = [hit('View wide', x, y) for x, y in ((250, 470), (720, 560))]

scatter = []
for obj in bpy.data.objects:
    if obj.get('pk_scatter'):
        mesh = obj.data
        attrs = [(a.name, a.domain, a.data_type) for a in mesh.attributes if not a.name.startswith('.')]
        scatter.append({'name': obj.name, 'kind': obj.get('pk_scatter_kind'), 'count': obj.get('pk_count'), 'verts': len(mesh.vertices), 'faces': len(mesh.polygons),
                        'materials': [m.name for m in mesh.materials if m], 'attributes': attrs, 'colour_attributes': [c.name for c in mesh.color_attributes],
                        'active_colour': mesh.color_attributes.active_color_name if hasattr(mesh.color_attributes, 'active_color_name') else None,
                        'modifiers': [m.type for m in obj.modifiers], 'shade_smooth_faces': sum(1 for p in mesh.polygons[:200] if p.use_smooth)})
report['scatter'] = scatter[:40]
material = bpy.data.materials.get('PK Scatter')
if material:
    report['scatter_material'] = [(n.bl_idname, n.name, getattr(n, 'attribute_name', None), getattr(n, 'attribute_type', None)) for n in material.node_tree.nodes]
    report['scatter_material_settings'] = {'blend': getattr(material, 'surface_render_method', None), 'backface_culling': material.use_backface_culling,
                                           'thickness': getattr(material, 'thickness_mode', None), 'displacement': material.displacement_method}

thatch = {}
for m in bpy.data.materials:
    if 'thatch' in m.name.lower() and m.users:
        nodes = m.node_tree.nodes if m.node_tree else []
        principled = [n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
        groups = [n.node_tree.name for n in nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree]
        thatch[m.name] = {'users': m.users, 'nodes': len(nodes), 'groups': groups, 'displacement': m.displacement_method,
                          'principled': [{'roughness_linked': bool(p.inputs['Roughness'].links), 'roughness': p.inputs['Roughness'].default_value,
                                          'specular_ior_level': p.inputs['Specular IOR Level'].default_value if 'Specular IOR Level' in p.inputs else None,
                                          'coat': p.inputs['Coat Weight'].default_value if 'Coat Weight' in p.inputs else None,
                                          'coat_linked': bool(p.inputs['Coat Weight'].links) if 'Coat Weight' in p.inputs else None,
                                          'normal_linked': bool(p.inputs['Normal'].links)} for p in principled]}
report['thatch'] = thatch
report['engine'] = scene.render.engine
report['view_transform'] = scene.view_settings.view_transform
print('PROBE ' + json.dumps(report, indent=1, default=str))
