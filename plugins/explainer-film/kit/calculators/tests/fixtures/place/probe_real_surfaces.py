"""What this does: reads plain facts straight from Blender's own data in a finished scene, for test_place_real_surfaces.py (so the test never takes the kit's word about its own
work). One probe per run:
    blender -b SCENE.blend --python probe_real_surfaces.py -- PROBE OUT.json
Probes: materials (every kit material: where its surface came from, its pictures, its normal picture, its displacement middle, its coat roughness, its wetness dials, and how many
seam-blend nodes it holds), objects (every mesh object: its role and whether it holds puddles), scatter (every scattered object: its kind, group, count, the sites written on it,
how much its faces look up, and whether its material lets light through), puddles (the standing water the kit laid), images (every picture the kit loaded from a scan).
A concrete example: probe 'materials' on a yard finished with the person's own library says the ground's material came from "own:earth" and reads the corrected normal picture.
"""
import json
import os
import sys

import bpy

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(arguments) < 2:
    print('usage: blender -b SCENE.blend --python probe_real_surfaces.py -- PROBE OUT.json')
    sys.exit(2)
probe_name, out_path = arguments[0], arguments[1]


def socket_value(node, name):
    socket = node.inputs.get(name)
    return float(socket.default_value) if socket is not None and not socket.links else None


def probe_materials():
    rows = {}
    for material in bpy.data.materials:
        if not material.name.startswith('PK ') or material.node_tree is None or material.users == 0:
            continue
        nodes = material.node_tree.nodes
        images = sorted({n.image.name for n in nodes if n.type == 'TEX_IMAGE' and n.image is not None})
        normal_pictures = []
        for node in nodes:
            if node.type == 'NORMAL_MAP':
                stack = [link.from_node for link in node.inputs['Color'].links]
                while stack:
                    current = stack.pop()
                    if current.type == 'TEX_IMAGE' and current.image is not None:
                        normal_pictures.append(current.image.name)
                    for socket in current.inputs:
                        stack.extend(link.from_node for link in socket.links)
        displacement = next((n for n in nodes if n.type == 'DISPLACEMENT'), None)
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        wetness = next((n for n in nodes if n.type == 'GROUP' and n.node_tree is not None and n.node_tree.name == 'PK Wetness'), None)
        rows[material.name] = {
            'source': material.get('pk_source'), 'surface': material.get('pk_surface'), 'images': images, 'normal_pictures': sorted(set(normal_pictures)),
            'displacement_midlevel': round(displacement.inputs['Midlevel'].default_value, 4) if displacement is not None else None,
            'method': material.displacement_method, 'coat_roughness': socket_value(principled, 'Coat Roughness') if principled is not None else None,
            'film_coat': socket_value(wetness, 'Film Coat') if wetness is not None else None, 'wet_roughness': socket_value(wetness, 'Wet Roughness') if wetness is not None else None,
            'wetness_masks': sorted(s.name for s in wetness.inputs if s.name.startswith('M ')) if wetness is not None else [],
            'seam_nodes': sum(1 for n in nodes if n.get('pk_layer') == 'seam'), 'mean_colour': list(material.get('pk_mean_colour') or []),
        }
    return {'materials': rows}


def probe_objects():
    return {'objects': {o.name: {'role': o.get('place_role'), 'holds_puddles': o.get('pk_holds_puddles'), 'materials': [s.material.name for s in o.material_slots if s.material]}
                        for o in bpy.data.objects if o.type == 'MESH'}}


def face_up_share(mesh):
    total = weighted = 0.0
    for polygon in mesh.polygons:
        area = polygon.area
        total += area
        weighted += area * abs(polygon.normal.z)
    return weighted / total if total else 0.0


def probe_scatter():
    rows = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or not obj.get('pk_scatter'):
            continue
        material = obj.data.materials[0] if obj.data.materials else None
        translucent = bool(material and material.node_tree and any(n.type == 'BSDF_TRANSLUCENT' for n in material.node_tree.nodes))
        rows.append({'name': obj.name, 'kind': obj.get('pk_scatter_kind'), 'group': obj.get('pk_scatter_group'), 'count': int(obj.get('pk_count', 0)), 'sites': obj.get('pk_sites'),
                     'face_up': round(face_up_share(obj.data), 3), 'material': material.name if material else None, 'translucent': translucent,
                     'triangles': sum(len(p.vertices) - 2 for p in obj.data.polygons)})
    return {'scatter': rows}


def probe_puddles():
    rows = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.get('pk_puddle'):
            material = obj.data.materials[0] if obj.data.materials else None
            rows.append({'name': obj.name, 'role': obj.get('place_role'), 'count': obj.get('pk_puddle_count'), 'area': obj.get('pk_puddle_area'),
                         'flat': (max(v.co.z for v in obj.data.vertices) - min(v.co.z for v in obj.data.vertices)) if len(obj.data.vertices) else None,
                         'normal_map': bool(material and any(n.type == 'NORMAL_MAP' for n in material.node_tree.nodes)), 'casts_shadow': obj.visible_shadow})
    return {'puddles': rows}


def probe_images():
    return {'images': [{'name': i.name, 'packed': bool(i.packed_file), 'colourspace': i.colorspace_settings.name, 'size': list(i.size), 'file': os.path.basename(i.filepath or ''),
                        'convention': i.get('pk_convention')} for i in bpy.data.images if i.name.startswith('pk_scan_')]}


PROBES = {'materials': probe_materials, 'objects': probe_objects, 'scatter': probe_scatter, 'puddles': probe_puddles, 'images': probe_images}
result = PROBES[probe_name]()
with open(out_path, 'w') as handle:
    json.dump(result, handle, indent=1, default=str)
print('probe written', out_path)
