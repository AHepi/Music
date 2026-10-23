"""What this does: reads plain facts straight from Blender's own data in a scene file, for test_place_fixes.py (so the test never takes the kit's word about its own work). One probe per run:
    blender -b SCENE.blend --python probe_fixes.py -- PROBE OUT.json
Probes: outline (every ground object: faces, outline area, boundary loops, relief), positions (every mesh object's lowest and highest point), kinds (every object: type, hidden, made by the
kit, materials), sign (the lettered sign's material: is its picture still the colour, does its roughness vary, is there a normal map, how many nodes does the kit own), masks (the plan masks
of a quay and a sea: dampness and shade at points on a line), sizes (the true size of a wall turned 45 degrees), lights (the lights and the world).
A concrete example: probe 'outline' on the curved road scene says the road ribbon still has 1 boundary loop and an area within 5 percent of what it had.
"""
import json
import os
import sys

import bpy

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(arguments) < 2:
    print('usage: blender -b SCENE.blend --python probe_fixes.py -- PROBE OUT.json')
    sys.exit(2)
probe_name, out_path = arguments[0], arguments[1]
KIT = os.environ.get('EXPLAINER_FILM_KIT') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(KIT, 'place-kit'))
sys.path.insert(0, os.path.join(KIT, 'calculators'))


def probe_outline():
    from place_kit import scene_read
    from place_kit.surfaces import ground_mesh
    rows = {}
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or not (obj.get('place_role') or '').startswith('ground.'):
            continue
        facts = ground_mesh.outline_facts(obj)
        rows[obj.name] = {'faces': facts['faces'], 'area': round(facts['area'], 3), 'box_area': round(facts['box_area'], 3), 'boundary_loops': facts['boundary_loops'], 'pieces': facts['pieces'],
                          'plain_rectangle': facts['plain_rectangle'], 'area_before': obj.get(ground_mesh.AREA_KEY), 'relief': round(scene_read.relief_metres(obj), 4), 'mesh': obj.data.name,
                          'original_mesh': obj.get('pk_original_mesh')}
    return {'ground': rows}


def probe_positions():
    from place_kit import scene_read
    rows = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not obj.get('pk_scatter'):
            low, high = scene_read.world_bounds(obj)
            rows[obj.name] = {'low': round(float(low[2]), 4), 'high': round(float(high[2]), 4), 'role': obj.get('place_role')}
    return {'objects': rows}


def probe_kinds():
    rows = {}
    for obj in bpy.data.objects:
        rows[obj.name] = {'type': obj.type, 'hide_render': bool(obj.hide_render), 'hide_viewport': bool(obj.hide_viewport), 'made': bool(obj.get('pk_made')), 'role': obj.get('place_role'),
                          'converted_from': obj.get('pk_converted_from'), 'converted_to': obj.get('pk_converted_to'), 'scatter': bool(obj.get('pk_scatter')),
                          'materials': [s.material.name for s in obj.material_slots if s.material] if obj.type == 'MESH' else [],
                          'faces': len(obj.data.polygons) if obj.type == 'MESH' else None,
                          'size': [round(v, 3) for v in obj.dimensions] if obj.type == 'MESH' else None}
    return {'objects': rows}


def probe_sign():
    material = bpy.data.materials.get('lettered sign')
    if material is None:
        return {'material': None}
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
    from place_kit.checks import material_inspect
    # the wear layers sit between the picture and the colour plug, so "still the picture" means: the picture is upstream of the colour (not replaced by a recipe's palette)
    colour_from_image = any(n.type == 'TEX_IMAGE' and n.image is not None and n.image.name == 'sign_picture' for n in material_inspect.upstream_nodes(principled.inputs['Base Color']))
    facts = material_inspect.inspect_material(material)
    return {'material': material.name, 'colour_still_the_picture': colour_from_image, 'roughness_linked': bool(principled.inputs['Roughness'].links), 'normal_linked': bool(principled.inputs['Normal'].links),
            'roughness_varies': facts['roughness_variation'], 'normal_map': facts['normal_map']['has'], 'augment_nodes': sum(1 for n in tree.nodes if 'pk_augment' in n.keys()),
            'layer_groups': sorted(facts['layers']), 'users': material.users}


def probe_masks():
    from place_kit import settings_file
    from place_kit.wear import masks
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            hint = {'Quay paving': 'ground.stone_paving', 'Seabed': 'ground.earth', 'Sea': 'water.sea'}.get(obj.name)
            if hint:
                obj['place_role'] = hint
    settings = settings_file.Settings({'place': 'quay', 'state': 'wet', 'look': 'lived_in'})
    plan, record = masks.build_plan_masks(settings, quick=False)
    out = {}
    for x in (2.0, 5.0, 7.0, 7.9, 8.5, 9.5, 10.5, 11.5, 14.0, 20.0):
        point = [[x, 0.0, 0.0]]
        out[str(x)] = {name: round(float(plan.sample(name, point)[0]), 3) for name in ('dampness', 'shade', 'wall_dist', 'prop_dist')}
    return {'samples': out, 'cell': plan.cell}


def probe_sizes():
    from place_kit import scene_read
    rows = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            rows[obj.name] = {'oriented': [round(v, 3) for v in scene_read.oriented_size(obj)], 'world_box': [round(float(v), 3) for v in scene_read.object_size(obj)]}
    return {'objects': rows}


def probe_lights():
    return {'lights': sorted((o.name, o.data.type, bool(o.get('pk_made'))) for o in bpy.data.objects if o.type == 'LIGHT'),
            'worlds': sorted(w.name for w in bpy.data.worlds), 'scene_world': bpy.context.scene.world.name if bpy.context.scene.world else None}


PROBES = {'outline': probe_outline, 'positions': probe_positions, 'kinds': probe_kinds, 'sign': probe_sign, 'masks': probe_masks, 'sizes': probe_sizes, 'lights': probe_lights}
if probe_name not in PROBES:
    print('unknown probe', probe_name, 'choose one of', ', '.join(PROBES))
    sys.exit(2)
result = PROBES[probe_name]()
os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as handle:
    json.dump(result, handle, indent=1, default=str)
print('PROBE DONE', probe_name, out_path)
