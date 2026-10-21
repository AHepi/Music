# What this does (plain words): opens a Blender file and only LISTS it: every material (how its nodes are wired into the Principled BSDF),
# every family of objects (count, size, faces, which way the faces point), the lights, cameras, empties and the world. It saves nothing.
# Run: blender -b --disable-autoexec FILE --python s1_list_street.py -- OUT.json
import json
import re
import sys
from collections import defaultdict

import bpy
import numpy as np

out_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
result = {'file': bpy.data.filepath, 'scene': scene.name}


def socket_summary(sock):
    """What feeds a socket: default value, or the chain of node names up to 3 steps back."""
    if sock.is_linked:
        link = sock.links[0]
        node = link.from_node
        desc = f'{node.bl_idname.replace("ShaderNode", "")}:{node.name}'
        if node.bl_idname == 'ShaderNodeTexImage' and node.image:
            desc += f'[{node.image.name}, {node.image.colorspace_settings.name}]'
        if node.bl_idname == 'ShaderNodeGroup' and node.node_tree:
            desc += f'[group {node.node_tree.name}]'
        if node.bl_idname == 'ShaderNodeNormalMap':
            src = node.inputs['Color'].links[0].from_node if node.inputs['Color'].links else None
            if src is not None and src.bl_idname == 'ShaderNodeTexImage' and src.image:
                desc += f'[{src.image.name}]'
        return desc + f'.{link.from_socket.name}'
    try:
        v = sock.default_value
        if hasattr(v, '__len__'):
            return [round(float(x), 3) for x in v]
        return round(float(v), 3)
    except Exception:
        return None


materials = {}
for mat in bpy.data.materials:
    if not mat.use_nodes or mat.node_tree is None:
        materials[mat.name] = {'nodes': False, 'users': mat.users}
        continue
    tree = mat.node_tree
    info = {'users': mat.users, 'node_count': len(tree.nodes), 'groups': sorted({n.node_tree.name for n in tree.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree}),
            'images': sorted({n.image.name for n in tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image}),
            'texcoords': sorted({(n.bl_idname.replace('ShaderNode', '')) for n in tree.nodes if n.bl_idname in ('ShaderNodeTexCoord', 'ShaderNodeUVMap', 'ShaderNodeNewGeometry', 'ShaderNodeObjectInfo')}),
            'shaders': sorted({n.bl_idname.replace('ShaderNode', '') for n in tree.nodes if n.bl_idname in (
                'ShaderNodeBsdfPrincipled', 'ShaderNodeEmission', 'ShaderNodeBsdfDiffuse', 'ShaderNodeMixShader', 'ShaderNodeBsdfGlass', 'ShaderNodeBsdfTransparent', 'ShaderNodeAddShader')}),
            'procedural': sorted({n.bl_idname.replace('ShaderNode', '') for n in tree.nodes if n.bl_idname.startswith('ShaderNodeTex') and n.bl_idname != 'ShaderNodeTexImage' and n.bl_idname != 'ShaderNodeTexCoord'})}
    principled = [n for n in tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    info['principled_count'] = len(principled)
    if principled:
        p = principled[0]
        info['principled'] = {name: socket_summary(p.inputs[name]) for name in ('Base Color', 'Roughness', 'Metallic', 'Specular IOR Level', 'Coat Weight', 'Normal', 'Emission Color', 'Emission Strength', 'Alpha')
                              if name in p.inputs}
    out = [n for n in tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' and n.is_active_output]
    if out:
        info['output_surface'] = socket_summary(out[0].inputs['Surface'])
    materials[mat.name] = info
result['materials'] = materials

# ---------------- objects by family
FAMILY_RES = [
    (re.compile(r'^(left|right)_row_([ab])_cottage_\d+_(\w+?)(_\d+)?$'), lambda m: f'{m.group(1)}_row_cottage_{m.group(3)}'),
    (re.compile(r'^gas_lamp_\d+_(\w+)$'), lambda m: f'gas_lamp_{m.group(1)}'),
    (re.compile(r'^gas_lamp_\d+$'), lambda m: 'gas_lamp'),
    (re.compile(r'^(.*?)(_\d+|\.\d+)$'), lambda m: m.group(1) + '_N'),
]


def family(name):
    for rx, f in FAMILY_RES:
        m = rx.match(name)
        if m:
            return f(m)
    return name


deps = bpy.context.evaluated_depsgraph_get()
families = defaultdict(lambda: {'objects': [], 'faces': 0, 'mats': set(), 'uv': set(), 'xmin': 1e9, 'xmax': -1e9, 'ymin': 1e9, 'ymax': -1e9, 'zmin': 1e9, 'zmax': -1e9,
                                'up': 0.0, 'wall': 0.0, 'down': 0.0, 'area': 0.0, 'mods': set(), 'hidden': 0})
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    fam = families[family(obj.name)]
    fam['objects'].append(obj.name)
    if obj.hide_render:
        fam['hidden'] += 1
    ev = obj.evaluated_get(deps)
    mesh = ev.to_mesh()
    fam['faces'] += len(mesh.polygons)
    for m in obj.material_slots:
        if m.material:
            fam['mats'].add(m.material.name)
    for u in mesh.uv_layers:
        fam['uv'].add(u.name)
    for mod in obj.modifiers:
        fam['mods'].add(mod.type)
    if len(mesh.vertices):
        co = np.empty(len(mesh.vertices) * 3, np.float64)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        mw = np.array(obj.matrix_world)
        w = co @ mw[:3, :3].T + mw[:3, 3]
        fam['xmin'], fam['xmax'] = min(fam['xmin'], w[:, 0].min()), max(fam['xmax'], w[:, 0].max())
        fam['ymin'], fam['ymax'] = min(fam['ymin'], w[:, 1].min()), max(fam['ymax'], w[:, 1].max())
        fam['zmin'], fam['zmax'] = min(fam['zmin'], w[:, 2].min()), max(fam['zmax'], w[:, 2].max())
        mesh.calc_normals_split() if hasattr(mesh, 'calc_normals_split') else None
        n = np.empty(len(mesh.polygons) * 3, np.float64)
        mesh.polygons.foreach_get('normal', n)
        n = n.reshape(-1, 3) @ mw[:3, :3].T
        norm = np.linalg.norm(n, axis=1, keepdims=True)
        n = n / np.maximum(norm, 1e-9)
        a = np.empty(len(mesh.polygons), np.float64)
        mesh.polygons.foreach_get('area', a)
        scale = abs(np.linalg.det(mw[:3, :3])) ** (2 / 3)
        a = a * scale
        fam['area'] += a.sum()
        fam['up'] += a[n[:, 2] > 0.9].sum()
        fam['down'] += a[n[:, 2] < -0.5].sum()
        fam['wall'] += a[np.abs(n[:, 2]) <= 0.5].sum()
    ev.to_mesh_clear()
fams = {}
for name, f in sorted(families.items()):
    fams[name] = {'count': len(f['objects']), 'first': f['objects'][0], 'faces': f['faces'], 'materials': sorted(f['mats']), 'uv': sorted(f['uv']), 'modifiers': sorted(f['mods']),
                  'hidden_in_render': f['hidden'], 'bbox': [round(f['xmin'], 2), round(f['xmax'], 2), round(f['ymin'], 2), round(f['ymax'], 2), round(f['zmin'], 2), round(f['zmax'], 2)],
                  'area_m2': round(f['area'], 1), 'up_m2': round(f['up'], 1), 'wall_m2': round(f['wall'], 1), 'down_m2': round(f['down'], 1)}
result['families'] = fams

# ---------------- which materials sit on which object names
by_mat = defaultdict(list)
for obj in scene.objects:
    if obj.type == 'MESH':
        for slot in obj.material_slots:
            if slot.material:
                by_mat[slot.material.name].append(obj.name)
result['material_users'] = {k: {'n': len(v), 'sample': v[:4]} for k, v in sorted(by_mat.items())}

# ---------------- lights, cameras, empties, world
lights = []
for o in scene.objects:
    if o.type == 'LIGHT':
        d = o.data
        entry = {'name': o.name, 'type': d.type, 'energy': round(d.energy, 1), 'loc': [round(v, 2) for v in o.matrix_world.translation], 'colour': [round(c, 3) for c in d.color]}
        if d.type == 'POINT':
            entry['radius'] = round(d.shadow_soft_size, 3)
        if d.type in ('SUN', 'SPOT', 'AREA'):
            direction = o.matrix_world.to_quaternion() @ __import__('mathutils').Vector((0, 0, -1))
            entry['points_along'] = [round(v, 3) for v in direction]
        if d.type == 'SUN':
            entry['angle'] = round(d.angle, 4)
        if d.type == 'AREA':
            entry['size'] = [round(d.size, 2), round(getattr(d, 'size_y', d.size), 2)]
        lights.append(entry)
result['lights'] = lights
result['cameras'] = [{'name': o.name, 'loc': [round(v, 3) for v in o.matrix_world.translation], 'fov_v_deg': round(__import__('math').degrees(o.data.angle_y), 1), 'sensor_fit': o.data.sensor_fit,
                      'rot_quat': [round(v, 4) for v in o.matrix_world.to_quaternion()]} for o in scene.objects if o.type == 'CAMERA']
result['active_camera'] = scene.camera.name if scene.camera else None
empties = [o.name for o in scene.objects if o.type == 'EMPTY']
result['empties'] = {'count': len(empties), 'sample': empties[:60]}
result['other_types'] = {t: sum(1 for o in scene.objects if o.type == t) for t in sorted({o.type for o in scene.objects})}
world = scene.world
wi = {}
if world and world.use_nodes:
    wi = {n.name: n.bl_idname for n in world.node_tree.nodes}
    bg = world.node_tree.nodes.get('Background')
    if bg:
        wi['background_colour'] = [round(v, 3) for v in bg.inputs['Color'].default_value]
        wi['background_strength'] = bg.inputs['Strength'].default_value
        wi['background_colour_linked'] = bg.inputs['Color'].is_linked
result['world'] = wi
r = scene.render
e = scene.eevee
result['render'] = {'engine': r.engine, 'res': [r.resolution_x, r.resolution_y, r.resolution_percentage], 'view_transform': scene.view_settings.view_transform, 'look': scene.view_settings.look,
                    'exposure': scene.view_settings.exposure, 'samples': getattr(e, 'taa_render_samples', None), 'raytracing': getattr(e, 'use_raytracing', None),
                    'shadow_rays': getattr(e, 'shadow_ray_count', None), 'shadow_steps': getattr(e, 'shadow_step_count', None)}
result['node_groups'] = [g.name for g in bpy.data.node_groups]
result['collections'] = {c.name: len(c.objects) for c in bpy.data.collections}
json.dump(result, open(out_path, 'w'), indent=1, default=str)
print('LISTED', len(materials), 'materials', len(fams), 'families', len(lights), 'lights')
