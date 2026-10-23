"""What this does: checks 3D models for the faults this project found by eye, one round at a time (logs 27-34), before
any plate is drawn from them:
  - squashed texture coordinates that paint as fine stripes (round 3: the gate piers looked like orange curtains;
    15, 27 and 33 striped parts in the two factories and the far town);
  - two surfaces on the same plane, facing the same way (lesson 85: a ceiling on the slab above flickered);
  - a floor laid just over another ground (round 2: the yards' setts 2 cm over the lane's ground showed dark patches);
  - '.001' names and roots not named as their file (lesson 119, round 1: eight props had 'name.001' roots);
  - glass whose see-through value comes from its picture (log 32: the gas lamps' glass ignored the value set on it);
  - glowing materials with a light base colour (lesson 89: a glow lit by its own lamp renders white);
  - sizes in props/index.json that do not match the saved model (round 1: the jacket "about 0.6 m wide" was 0.516);
  - each model's front (the way its lettering faces), measured, for the index;
  - in Blender: bevels without hardened normals (lesson 67) and materials shared by many objects (join by material);
  - with --surfaces: materials that are a plain colour, with no picture and no normal map (a warning: it passes the faults above, and the place audit fails it).
It reads .glb files with plain Python (numpy), or the scene open in Blender (bpy). Places and sizes are Blender
metres (x across, y forward, z up); a .glb's own axes (y up) are turned into Blender's on reading.

Use:
  python3 model_lint.py MODEL.glb [MODEL.glb ...]             each file on its own
  python3 model_lint.py --as-set LANE.glb FACTORY.glb ...      the files as one set (floors over another file's ground,
                                                              surfaces on the same plane across files)
  python3 model_lint.py --index props/index.json props/*.glb   also compare the index's sizes with the saved models
  python3 model_lint.py ... --write-index NEW-index.json       a copy of the index with measured sizes, front and
                                                              triangles written in (never overwrites --index itself)
  blender -b SCENE.blend --disable-autoexec --python model_lint.py -- [--report FILE] [--out FILE.json]
  blender -b BASE.blend --python ASSEMBLE.py --python model_lint.py -- ...   (after a place's assemble script)
  --only stripes,same-plane,floors,names,glass,glow,sizes,front   run only these checks
  --surfaces                                                  also warn about plain-colour materials (no picture, no normal map); a warning, never a failure
  --json / --out FILE / --report FILE / --settings FILE           as every calculator (kit/calculators)
The house numbers come from kit/film-settings.json (section views_and_models.model_lint and models); the report
names each one it used. Exit 1 when a check fails (striped parts, same-plane faces, floors over ground, '.001' names,
glass alpha from a picture), 0 otherwise; warnings (glowing light bases, sizes, fronts) do not fail.
"""
import argparse
import fnmatch
import json
import math
import os
import re
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.abspath(os.path.join(HERE, '..', '..', 'calculators'))
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402

CHECKS = ('stripes', 'same-plane', 'floors', 'names', 'glass', 'glow', 'sizes', 'front')
FAILING = {'stripes', 'same-plane', 'floors', 'names', 'glass'}
SECTION = 'views_and_models.model_lint'


# ------------------------------------------------------------------------------------------------ reading a .glb
COMPONENT_TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMPONENT_COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    """The glTF JSON and the binary chunk of a .glb file."""
    with open(path, 'rb') as handle:
        data = handle.read()
    if data[:4] != b'glTF':
        raise ValueError(f'{path} is not a .glb file')
    offset, gltf, binary = 12, None, b''
    while offset + 8 <= len(data):
        length, kind = struct.unpack('<II', data[offset:offset + 8])
        chunk = data[offset + 8:offset + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + length
    if gltf is None:
        raise ValueError(f'{path} has no JSON chunk')
    return gltf, binary


def read_accessor(gltf, binary, index):
    accessor = gltf['accessors'][index]
    count, width = accessor['count'], COMPONENT_COUNTS[accessor['type']]
    dtype = np.dtype(COMPONENT_TYPES[accessor['componentType']])
    if 'bufferView' not in accessor:
        return np.zeros((count, width))
    view = gltf['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    item = dtype.itemsize * width
    stride = view.get('byteStride') or item
    if stride == item:
        values = np.frombuffer(binary, dtype=dtype, count=count * width, offset=start).reshape(count, width)
    else:
        raw = np.frombuffer(binary, dtype=np.uint8, count=stride * (count - 1) + item, offset=start)
        rows = np.lib.stride_tricks.as_strided(raw, shape=(count, item), strides=(stride, 1))
        values = np.frombuffer(np.ascontiguousarray(rows).tobytes(), dtype=dtype).reshape(count, width)
    values = values.astype(np.float64)
    if accessor.get('normalized') and dtype.kind in 'iu':
        values = values / float(np.iinfo(dtype).max)
    return values


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    t = node.get('translation', [0, 0, 0])
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    s = node.get('scale', [1, 1, 1])
    rotation = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    matrix = np.eye(4)
    matrix[:3, :3] = rotation * np.array(s)
    matrix[:3, 3] = t
    return matrix


GLTF_TO_BLENDER = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float64)   # (x, y, z) glTF -> (x, -z, y)


def png_has_alpha(data):
    """True if a PNG's colour type carries an alpha channel (4 grey + alpha, 6 RGBA)."""
    return len(data) > 26 and data[:8] == b'\x89PNG\r\n\x1a\n' and data[25] in (4, 6)


def image_bytes(gltf, binary, image_index, folder):
    image = gltf.get('images', [])[image_index]
    if 'bufferView' in image:
        view = gltf['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        return binary[start:start + view['byteLength']], image.get('mimeType', '')
    uri = image.get('uri', '')
    path = os.path.join(folder, uri)
    if uri and not uri.startswith('data:') and os.path.exists(path):
        with open(path, 'rb') as handle:
            return handle.read(), image.get('mimeType', '')
    return b'', image.get('mimeType', '')


def glb_materials(gltf, binary, folder):
    """Plain facts about each glTF material: name, base colour, its picture, alpha mode and source, glow."""
    found = []
    for material in gltf.get('materials', []):
        pbr = material.get('pbrMetallicRoughness', {})
        base = pbr.get('baseColorFactor', [1, 1, 1, 1])
        texture = pbr.get('baseColorTexture')
        # Blender's importer wires a blending material's Alpha to its picture: a value set on the input is then
        # ignored, and a picture without an alpha channel makes the glass solid (log 32)
        alpha_from_picture, picture_has_alpha = False, None
        if texture is not None and material.get('alphaMode', 'OPAQUE') != 'OPAQUE':
            alpha_from_picture = True
            source = gltf['textures'][texture['index']].get('source')
            if source is not None:
                data, mime = image_bytes(gltf, binary, source, folder)
                picture_has_alpha = png_has_alpha(data)
        emissive = list(material.get('emissiveFactor', [0, 0, 0]))
        strength = material.get('extensions', {}).get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
        glows = (max(emissive) * strength > 0) or ('emissiveTexture' in material and strength > 0)
        found.append({'name': material.get('name', ''), 'base_colour': list(base[:3]), 'base_picture': texture is not None, 'normal_picture': 'normalTexture' in material,
                      'alpha_mode': material.get('alphaMode', 'OPAQUE'), 'alpha_from_picture': alpha_from_picture,
                      'picture_has_alpha': picture_has_alpha,
                      'glows': bool(glows), 'glow_colour': [e * strength for e in emissive]})
    return found


def parts_from_glb(path, label=None):
    """The model as parts (one per mesh node and material): triangle corners in Blender metres, their texture
    coordinates, the object and root names, and the material facts."""
    gltf, binary = read_glb(path)
    folder = os.path.dirname(os.path.abspath(path))
    materials = glb_materials(gltf, binary, folder)
    nodes = gltf.get('nodes', [])
    scene = gltf.get('scenes', [{}])[gltf.get('scene', 0)] if gltf.get('scenes') else {'nodes': list(range(len(nodes)))}
    parts, names, roots = [], [], []
    stack = [(index, np.eye(4), index) for index in scene.get('nodes', [])]
    for index in scene.get('nodes', []):
        roots.append(nodes[index].get('name', f'node {index}'))
    while stack:
        index, parent, root = stack.pop()
        node = nodes[index]
        world = parent @ node_matrix(node)
        name = node.get('name', f'node {index}')
        names.append(name)
        for child in node.get('children', []):
            stack.append((child, world, root))
        if 'mesh' not in node:
            continue
        for primitive_index, primitive in enumerate(gltf['meshes'][node['mesh']].get('primitives', [])):
            if primitive.get('mode', 4) != 4 or 'POSITION' not in primitive.get('attributes', {}):
                continue
            positions = read_accessor(gltf, binary, primitive['attributes']['POSITION'])
            if 'indices' in primitive:
                triangles = read_accessor(gltf, binary, primitive['indices']).astype(np.int64).reshape(-1, 3)
            else:
                triangles = np.arange(len(positions) - len(positions) % 3).reshape(-1, 3)
            world_points = (positions @ world[:3, :3].T + world[:3, 3]) @ GLTF_TO_BLENDER.T
            uvs = read_accessor(gltf, binary, primitive['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in primitive['attributes'] else None
            material = materials[primitive['material']] if primitive.get('material') is not None else \
                {'name': '', 'base_colour': [1, 1, 1], 'base_picture': False, 'alpha_mode': 'OPAQUE', 'alpha_from_picture': False,
                 'glows': False, 'glow_colour': [0, 0, 0]}
            parts.append({'file': label or os.path.basename(path), 'object': name, 'root': nodes[root].get('name', ''),
                          'mesh_key': (node['mesh'], primitive_index), 'material': material, 'corners': world_points[triangles],
                          'uv_corners': uvs[triangles][:, :, :2] if uvs is not None else None})
    return {'file': label or os.path.basename(path), 'path': path, 'parts': parts, 'names': names, 'roots': roots,
            'blender_extras': {}}


# ------------------------------------------------------------------------------------------------ reading the open Blender scene
def parts_from_blender(scene=None):
    """The same parts from the scene open in Blender (evaluated meshes, world space), plus Blender-only facts."""
    import bpy   # noqa: F401 (only inside Blender)
    scene = scene or bpy.context.scene
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    parts, names, roots = [], [], []
    material_facts = {}
    bevels, users = [], {}
    for obj in scene.objects:
        names.append(obj.name)
        if obj.parent is None:
            roots.append(obj.name)
        if obj.type != 'MESH' or obj.hide_render:
            continue
        for modifier in obj.modifiers:
            if modifier.type == 'BEVEL' and not getattr(modifier, 'harden_normals', False):
                bevels.append(obj.name)
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            count = len(mesh.loop_triangles)
            if count == 0:
                continue
            vertices = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get('co', vertices)
            vertices = vertices.reshape(-1, 3)
            matrix = np.array(obj.matrix_world)
            vertices = vertices @ matrix[:3, :3].T + matrix[:3, 3]
            triangle_vertices = np.empty(count * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get('vertices', triangle_vertices)
            triangle_loops = np.empty(count * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get('loops', triangle_loops)
            material_index = np.empty(count, dtype=np.int64)
            mesh.loop_triangles.foreach_get('material_index', material_index)
            corners = vertices[triangle_vertices.reshape(-1, 3)]
            uv_corners = None
            if mesh.uv_layers.active is not None:
                loop_uvs = np.empty(len(mesh.loops) * 2)
                mesh.uv_layers.active.data.foreach_get('uv', loop_uvs)
                uv_corners = loop_uvs.reshape(-1, 2)[triangle_loops.reshape(-1, 3)]
            slots = [slot.material for slot in obj.material_slots] or [None]
            root = obj
            while root.parent is not None:
                root = root.parent
            for slot_index in np.unique(material_index):
                material = slots[slot_index] if slot_index < len(slots) else None
                key = material.name if material else ''
                if key not in material_facts:
                    material_facts[key] = blender_material_facts(material)
                if material is not None:
                    users.setdefault(material.name, set()).add(obj.name)
                chosen = material_index == slot_index
                parts.append({'file': scene.name, 'object': obj.name, 'root': root.name, 'material': material_facts[key],
                              'mesh_key': (obj.data.name, int(slot_index), tuple(np.round(matrix[:3, :3], 6).ravel())),
                              'corners': corners[chosen], 'uv_corners': uv_corners[chosen] if uv_corners is not None else None})
        finally:
            evaluated.to_mesh_clear()
    shared = {name: sorted(objects) for name, objects in users.items() if len(objects) > 1}
    return {'file': bpy.data.filepath or scene.name, 'path': bpy.data.filepath, 'parts': parts, 'names': names, 'roots': roots,
            'blender_extras': {'bevels_without_hardened_normals': sorted(set(bevels)), 'materials_shared': shared}}


def blender_material_facts(material):
    facts = {'name': material.name if material else '', 'base_colour': [1, 1, 1], 'base_picture': False, 'normal_picture': False, 'alpha_mode': 'OPAQUE',
             'alpha_from_picture': False, 'glows': False, 'glow_colour': [0, 0, 0]}
    if material is None or not material.use_nodes:
        return facts
    principled = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if principled is None:
        return facts
    base = principled.inputs['Base Color']
    facts['base_colour'] = list(base.default_value)[:3]
    facts['base_picture'] = base.is_linked
    normal = principled.inputs['Normal']
    facts['normal_picture'] = bool(normal.is_linked and any(link.from_node.type == 'NORMAL_MAP' and link.from_node.inputs['Color'].is_linked for link in normal.links))
    alpha = principled.inputs['Alpha']
    if alpha.is_linked:
        facts['alpha_mode'] = 'LINKED'
        facts['alpha_from_picture'] = any(link.from_node.type == 'TEX_IMAGE' for link in alpha.links)
    elif alpha.default_value < 1:
        facts['alpha_mode'] = 'BLEND'
    colour_socket = principled.inputs.get('Emission Color') or principled.inputs.get('Emission')
    strength_socket = principled.inputs.get('Emission Strength')
    strength = strength_socket.default_value if strength_socket is not None else 1.0
    colour = list(colour_socket.default_value)[:3] if colour_socket is not None else [0, 0, 0]
    linked = colour_socket is not None and colour_socket.is_linked
    facts['glows'] = bool(strength > 0 and (max(colour) > 0 or linked))
    facts['glow_colour'] = [c * strength for c in colour]
    return facts


# ------------------------------------------------------------------------------------------------ the checks
def triangle_areas(corners):
    return 0.5 * np.linalg.norm(np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]), axis=1)


def uv_areas(uv_corners):
    a, b, c = uv_corners[:, 0], uv_corners[:, 1], uv_corners[:, 2]
    return 0.5 * np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1]))


def find_stripes(model, settings):
    """Parts whose faces have texture coordinates squashed to a line: per part, a face whose picture area per square
    metre is under ratio x the part's median is striped; a part is reported when its striped faces cover more than
    the report area. These are the thresholds of round 3's find_stripes.py, which found 15, 27 and 33 parts."""
    ratio = settings.value(f'{SECTION}.stripe_ratio_of_median')
    report_area = settings.value(f'{SECTION}.stripe_report_area_square_metres')
    smallest = settings.value(f'{SECTION}.stripe_face_min_area_square_metres')
    found, copies, first = [], {}, []
    for part in model['parts']:
        key = part.get('mesh_key', id(part))
        copies[key] = copies.get(key, 0) + 1
        if copies[key] == 1:
            first.append(part)
    for part in first:   # a mesh placed many times is one fault to fix (round 3's tool counted it once too)
        if part['uv_corners'] is None:
            continue
        area = triangle_areas(part['corners'])
        keep = area > smallest
        if not keep.any():
            continue
        per_metre = uv_areas(part['uv_corners'])[keep] / area[keep]
        median = float(np.median(per_metre))
        striped = per_metre < ratio * max(median, 1e-9)
        striped_area, total = float(area[keep][striped].sum()), float(area[keep].sum())
        if striped_area > report_area:
            found.append({'file': part['file'], 'part': part['object'], 'material': part['material']['name'],
                          'striped_square_metres': round(striped_area, 2), 'of_square_metres': round(total, 2),
                          'share': round(striped_area / total, 3), 'placed_copies': copies[part.get('mesh_key', id(part))]})
    found.sort(key=lambda f: -f['striped_square_metres'])
    return found


def all_triangles(models, upward_only=False, settings=None):
    """Every triangle of every solid part, as flat arrays: corners, unit normals, areas, and which object it belongs to.
    See-through parts (glass, a soft shadow patch laid on the ground) are left out: they are meant to lie over things."""
    corners, owners, owner_names = [], [], []
    for model in models:
        for part in model['parts']:
            if part['material'].get('alpha_mode', 'OPAQUE') not in ('OPAQUE', 'LINKED') and not part['material'].get('alpha_from_picture'):
                continue
            name = f'{part["file"]}: {part["object"]}' if len(models) > 1 else part['object']
            if name not in owner_names:
                owner_names.append(name)
            corners.append(part['corners'])
            owners.append(np.full(len(part['corners']), owner_names.index(name)))
    if not corners:
        return None
    corners = np.concatenate(corners)
    owners = np.concatenate(owners)
    cross = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    doubled = np.linalg.norm(cross, axis=1)
    keep = doubled > 2e-8
    corners, owners, cross, doubled = corners[keep], owners[keep], cross[keep], doubled[keep]
    normals = cross / doubled[:, None]
    return {'corners': corners, 'owners': owners, 'names': owner_names, 'normals': normals, 'areas': doubled / 2}


def plane_basis(normal):
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    return u, np.cross(normal, u)


def clip_polygon(subject, clipper):
    """Sutherland-Hodgman: the part of convex polygon `subject` inside convex polygon `clipper` (both 2D, counter-clockwise)."""
    output = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        edge = (b[0] - a[0], b[1] - a[1])
        inputs, output = output, []
        if not inputs:
            break
        def inside(p):
            return edge[0] * (p[1] - a[1]) - edge[1] * (p[0] - a[0]) >= -1e-12
        for j in range(len(inputs)):
            p, q = inputs[j], inputs[(j + 1) % len(inputs)]
            if inside(q):
                if not inside(p):
                    output.append(intersect(p, q, a, b))
                output.append(q)
            elif inside(p):
                output.append(intersect(p, q, a, b))
    return output


def intersect(p, q, a, b):
    x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
    x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-18:
        return q
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def polygon_area(points):
    if len(points) < 3:
        return 0.0
    return 0.5 * abs(sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1]
                         for i in range(len(points))))


def counter_clockwise(points):
    signed = sum(points[i][0] * points[(i + 1) % 3][1] - points[(i + 1) % 3][0] * points[i][1] for i in range(3))
    return points if signed > 0 else points[::-1]


def find_same_plane(models, settings):
    """Pairs of faces from different objects on the same plane, facing the same way, overlapping: they flicker as
    the camera moves (lesson 85). Faces back to back (a prop's base on the ground) are not reported: one hides the other."""
    gap = settings.value(f'{SECTION}.same_plane_gap_metres')
    parallel = settings.value(f'{SECTION}.same_plane_normal_cos')
    least = settings.value(f'{SECTION}.same_plane_overlap_min_square_metres')
    triangles = all_triangles(models)
    if triangles is None:
        return []
    normals, corners, owners = triangles['normals'], triangles['corners'], triangles['owners']
    lowest = np.full(owners.max() + 1, np.inf)
    np.minimum.at(lowest, owners, corners[:, :, 2].min(axis=1))
    # a downward face at the very bottom of its object is its base, hidden by whatever it stands on
    base = (normals[:, 2] < -0.9) & (corners[:, :, 2].max(axis=1) <= lowest[owners] + 0.01)
    offsets = np.einsum('ij,ij->i', normals, corners[:, 0])
    normal_key = np.round(normals * 100).astype(np.int64)
    offset_key = np.floor(offsets / max(gap * 10, 1e-4)).astype(np.int64)
    keys = np.column_stack([normal_key, offset_key])
    order = np.lexsort(keys.T[::-1])
    keys_sorted = keys[order]
    starts = np.flatnonzero(np.r_[True, np.any(keys_sorted[1:] != keys_sorted[:-1], axis=1)])
    ends = np.r_[starts[1:], len(order)]
    by_key = {tuple(keys_sorted[s]): order[s:e] for s, e in zip(starts, ends)}
    pairs = {}
    for key, members in by_key.items():
        neighbour = by_key.get(key[:3] + (key[3] + 1,))
        candidates = members if neighbour is None else np.concatenate([members, neighbour])
        if len(np.unique(owners[candidates])) < 2:
            continue
        normal = normals[candidates[0]]
        u, v = plane_basis(normal)
        flat = np.stack([corners[candidates] @ u, corners[candidates] @ v], axis=2)
        low, high = flat.min(axis=1), flat.max(axis=1)
        sweep = np.argsort(low[:, 0])
        for a_position, a in enumerate(sweep):
            for b in sweep[a_position + 1:]:
                if low[b, 0] >= high[a, 0]:
                    break
                i, j = candidates[a], candidates[b]
                if owners[i] == owners[j] or low[b, 1] >= high[a, 1] or low[a, 1] >= high[b, 1] or (base[i] and base[j]):
                    continue
                if np.dot(normals[i], normals[j]) < parallel or abs(offsets[i] - offsets[j]) > gap:
                    continue
                overlap = polygon_area(clip_polygon(counter_clockwise([tuple(p) for p in flat[a]]),
                                                    counter_clockwise([tuple(p) for p in flat[b]])))
                if overlap <= 0:
                    continue
                pair = tuple(sorted((triangles['names'][owners[i]], triangles['names'][owners[j]])))
                record = pairs.setdefault(pair, {'objects': list(pair), 'square_metres': 0.0, 'at': corners[i].mean(axis=0).round(3).tolist(),
                                                 'facing': normal.round(3).tolist()})
                record['square_metres'] += overlap
    found = [dict(p, square_metres=round(p['square_metres'], 4)) for p in pairs.values() if p['square_metres'] >= least]
    found.sort(key=lambda p: -p['square_metres'])
    return found


def heights_under(points, triangles):
    """For points (x, y) and triangles (N, 3, 3): every (point index, triangle index, the triangle's height there) where
    the point falls inside the triangle seen from above."""
    if len(points) == 0 or len(triangles) == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0)
    order = np.argsort(points[:, 0])
    xs = points[order, 0]
    found_points, found_triangles, found_heights = [], [], []
    for index, (a, b, c) in enumerate(triangles):
        low_x, high_x = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        start, end = np.searchsorted(xs, low_x), np.searchsorted(xs, high_x, side='right')
        if start >= end:
            continue
        chosen = order[start:end]
        ys = points[chosen, 1]
        chosen = chosen[(ys >= min(a[1], b[1], c[1])) & (ys <= max(a[1], b[1], c[1]))]
        if len(chosen) == 0:
            continue
        v0, v1 = b[:2] - a[:2], c[:2] - a[:2]
        denominator = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(denominator) < 1e-14:
            continue
        w = points[chosen, :2] - a[:2]
        s = (w[:, 0] * v1[1] - v1[0] * w[:, 1]) / denominator
        t = (v0[0] * w[:, 1] - w[:, 0] * v0[1]) / denominator
        inside = (s >= -1e-9) & (t >= -1e-9) & (s + t <= 1 + 1e-9)
        if not inside.any():
            continue
        found_points.append(chosen[inside])
        found_triangles.append(np.full(int(inside.sum()), index))
        found_heights.append(a[2] + s[inside] * (b[2] - a[2]) + t[inside] * (c[2] - a[2]))
    if not found_points:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0)
    return np.concatenate(found_points), np.concatenate(found_triangles), np.concatenate(found_heights)


def find_floors_over_ground(models, settings):
    """Two upward surfaces of different objects within a few centimetres of each other, one over the other: the lower
    one shows through in patches, or pokes through where it is uneven (round 2: the yards' setts 2 cm over the lane's
    rutted ground). Exactly level pairs are the same-plane check's; a lower face hidden inside the upper object
    (a stone band round a wall's top) is left out."""
    within = settings.value('models.ground_under_raised_area_metres')
    gap = settings.value(f'{SECTION}.same_plane_gap_metres')
    upward = settings.value(f'{SECTION}.upward_normal_z_min')
    least = settings.value(f'{SECTION}.floor_min_square_metres')
    triangles = all_triangles(models)
    if triangles is None:
        return []
    names = triangles['names']
    up = triangles['normals'][:, 2] >= upward
    down = triangles['normals'][:, 2] <= -upward
    up_corners, up_owners, up_areas = triangles['corners'][up], triangles['owners'][up], triangles['areas'][up]
    if len(up_corners) == 0:
        return []
    # sample each upward face at its middle and near its three corners (pulled 10% toward the middle)
    middles = up_corners.mean(axis=1)
    samples = [middles] + [up_corners[:, k] * 0.9 + middles * 0.1 for k in range(3)]
    points = np.concatenate(samples)
    point_triangle = np.tile(np.arange(len(up_corners)), 4)
    point_index, under_index, under_height = heights_under(points[:, :2], up_corners)
    keep = up_owners[point_triangle[point_index]] != up_owners[under_index]
    point_index, under_index, under_height = point_index[keep], under_index[keep], under_height[keep]
    rise = points[point_index, 2] - under_height
    near = (np.abs(rise) > gap) & (np.abs(rise) <= within)
    point_index, under_index, under_height, rise = point_index[near], under_index[near], under_height[near], rise[near]
    if len(point_index) == 0:
        return []
    point_owner = up_owners[point_triangle[point_index]]
    under_owner = up_owners[under_index]
    upper_owner = np.where(rise > 0, point_owner, under_owner)
    lower_height = np.minimum(points[point_index, 2], under_height)
    # leave out lower faces inside the upper object: it has a downward face below them at that spot
    down_corners, down_owners = triangles['corners'][down], triangles['owners'][down]
    hidden = np.zeros(len(point_index), dtype=bool)
    for owner in np.unique(upper_owner):
        mine = np.flatnonzero(upper_owner == owner)
        faces = down_corners[down_owners == owner]
        if len(faces) == 0:
            continue
        hit_point, _, hit_height = heights_under(points[point_index[mine], :2], faces)
        below = hit_height < lower_height[mine][hit_point] - gap
        hidden[mine[hit_point[below]]] = True
    pairs = {}
    for k in np.flatnonzero(~hidden):
        a, b = int(point_owner[k]), int(under_owner[k])
        key = tuple(sorted((a, b)))
        upper = int(upper_owner[k])
        record = pairs.setdefault(key, {'objects': [names[key[0]], names[key[1]]], 'upper_counts': {}, 'gaps': [], 'area': 0.0,
                                        'at': points[point_index[k]].round(2).tolist()})
        record['upper_counts'][names[upper]] = record['upper_counts'].get(names[upper], 0) + 1
        record['gaps'].append(float(abs(rise[k])))
        record['area'] += float(up_areas[point_triangle[point_index[k]]]) / 4
    found = []
    for record in pairs.values():
        if record['area'] < least:
            continue
        counts = record['upper_counts']
        floor = max(counts, key=counts.get)
        ground = record['objects'][1] if record['objects'][0] == floor else record['objects'][0]
        found.append({'floor': floor, 'over': ground, 'square_metres': round(record['area'], 3),
                      'gap_metres': [round(min(record['gaps']), 3), round(max(record['gaps']), 3)],
                      'pokes_through': len(counts) > 1, 'at': record['at']})
    found.sort(key=lambda r: -r['square_metres'])
    return found


DOT_NUMBER = re.compile(r'\.\d{3}$')


def check_names(model, settings, one_prop=False):
    """'.001' names and, for a prop file, one root named as the file. A copy number on a root fails (round 1: eight
    props had 'name.001' roots; lesson 119: the checker and the page took the second gas lamp for the first). On a
    part under a root of its own name it only warns: groups found through their root still tell the copies apart, but
    anything that looks a part up by its own name gets the wrong one."""
    numbered = sorted({n for n in model['names'] if DOT_NUMBER.search(n)})
    numbered_roots = sorted(n for n in set(model['roots']) if DOT_NUMBER.search(n))
    numbered_parts = [n for n in numbered if n not in numbered_roots]
    problems = [f'root "{n}" ends in a copy number' for n in numbered_roots]
    problems += [f'{len(numbered_parts)} part(s) end in a copy number ({", ".join(numbered_parts[:5])}'
                 + (', ...' if len(numbered_parts) > 5 else '') + ')'] if numbered_parts else []
    root_note = None
    if one_prop:
        stem = os.path.splitext(os.path.basename(model['file']))[0]
        if len(model['roots']) != 1:
            root_note = f'{len(model["roots"])} roots ({", ".join(model["roots"][:6])}); a prop file has one root named "{stem}"'
        elif model['roots'][0] != stem:
            root_note = f'its root is "{model["roots"][0]}", not "{stem}" (named as the file)'
    # a prop file whose own root carries a copy number fails; in a whole scene or set they are counted and only warned
    # about (an imported model whose root and mesh share a name always gets one there)
    return {'numbered_roots': numbered_roots, 'numbered_parts': numbered_parts, 'root_problem': root_note,
            'fails': bool(numbered_roots) and bool(one_prop), 'problems': problems + ([root_note] if root_note else [])}


def material_matches(name, patterns):
    lowered = name.lower()
    return any(fnmatch.fnmatch(lowered, p) for p in patterns)


def check_materials(models, settings, only):
    """Glass whose alpha comes from its picture (log 32) and glowing materials with a light base (lesson 89)."""
    glass_words = settings.value(f'{SECTION}.glass_material_patterns') if 'glass' in only else []
    brightest_base = settings.value(f'{SECTION}.glowing_base_brightness_max') if 'glow' in only else None
    glass, glows, seen, glows_over_pictures = [], [], set(), []
    for model in models:
        for part in model['parts']:
            material = part['material']
            key = (model['file'], material['name'])
            if key in seen:
                continue
            seen.add(key)
            if 'glass' in only and material['alpha_from_picture'] and material_matches(material['name'], glass_words):
                glass.append({'file': model['file'], 'material': material['name'], 'alpha_mode': material['alpha_mode'],
                              'picture_has_alpha': material.get('picture_has_alpha')})
            if 'glow' in only and material['glows']:
                r, g, b = material['base_colour']
                brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
                if material['base_picture']:
                    glows_over_pictures.append(material['name'])   # lit windows, glowing brick: meant to show their picture
                elif brightness > brightest_base:
                    glows.append({'file': model['file'], 'material': material['name'], 'base_brightness': round(brightness, 3),
                                  'base_from_picture': False})
    return glass, glows, sorted(set(glows_over_pictures))


def check_surfaces(models):
    """The --surfaces check (a warning, never a failure): a material that is a plain colour with no picture and no normal map is what a model builds when it is only asked for a shape.
    Returns {file: [material names]} and {file: number of materials used}."""
    plain, used = {}, {}
    for model in models:
        seen, bare = set(), []
        for part in model['parts']:
            material = part['material']
            if material['name'] in seen:
                continue
            seen.add(material['name'])
            if material.get('glows') or material.get('alpha_mode') not in ('OPAQUE', None):
                continue                                           # glass and lights are not surfaces to texture
            if not material.get('base_picture') and not material.get('normal_picture'):
                bare.append(material['name'])
        plain[model['file']] = bare
        used[model['file']] = len(seen)
    return plain, used


def measured_size(model):
    corners = np.concatenate([p['corners'].reshape(-1, 3) for p in model['parts']]) if model['parts'] else np.zeros((1, 3))
    low, high = corners.min(axis=0), corners.max(axis=0)
    return {'width_x': float(high[0] - low[0]), 'depth': float(high[1] - low[1]), 'height': float(high[2] - low[2]),
            'low': low.round(4).tolist(), 'high': high.round(4).tolist()}


def front_of(model, settings):
    """The way the model's lettering faces (area-weighted mean normal of its lettered faces), as the nearest axis."""
    patterns = settings.value('views_and_models.lettering_material_patterns')
    total, absolute, area = np.zeros(3), np.zeros(3), 0.0
    for part in model['parts']:
        if not material_matches(part['material']['name'], patterns):
            continue
        c = part['corners']
        vector_areas = np.cross(c[:, 1] - c[:, 0], c[:, 2] - c[:, 0]) / 2
        total += vector_areas.sum(axis=0)
        absolute += np.abs(vector_areas).sum(axis=0)
        area += float(np.linalg.norm(vector_areas, axis=1).sum())
    if area < 1e-9:
        return None
    if np.linalg.norm(total) < 0.5 * area:
        # lettered on opposite faces (a hanging sign, a crate's two sides): name the axis, both ways
        axis = int(np.argmax(absolute))
        return {'front': '+-' + 'xyz'[axis], 'both_faces': True, 'direction': None, 'degrees_off_axis': None}
    direction = total / np.linalg.norm(total)
    axis = int(np.argmax(np.abs(direction)))
    name = ('+' if direction[axis] > 0 else '-') + 'xyz'[axis]
    return {'front': name, 'both_faces': False, 'direction': direction.round(3).tolist(),
            'degrees_off_axis': round(math.degrees(math.acos(min(1.0, abs(direction[axis])))), 1)}


SIZE_WORDS = re.compile(r'about (\d+(?:\.\d+)?) ?m (wide|across|high|tall|long)')


def check_index_entry(entry, size, settings):
    """The index's recorded size against the measured one, and plain-words size claims in its description."""
    match = settings.value('models.index_size_match_metres')
    tolerance = settings.value(f'{SECTION}.size_claim_tolerance_share')
    problems = []
    recorded = entry.get('size_metres') or {}
    for key in ('width_x', 'depth', 'height'):
        if key in recorded and abs(recorded[key] - size[key]) > match:
            problems.append(f'index {key} {recorded[key]} m, measured {size[key]:.3f} m')
    text = entry.get('what', '')
    for number, word in SIZE_WORDS.findall(text):
        claimed = float(number)
        before = text[max(0, text.find(f'about {number}') - 80):text.find(f'about {number}')].lower()
        if any(word in before for word in ('letter', 'capital', 'stencil', 'word')):
            continue   # letter heights need the lettering's own measure (lettering-sizes.json), not the outline
        measured = {'wide': size['width_x'], 'across': max(size['width_x'], size['depth']), 'long': max(size['width_x'], size['depth']),
                    'high': size['height'], 'tall': size['height']}[word]
        if abs(claimed - measured) > tolerance * measured:
            problems.append(f'its description says "about {number} m {word}", the saved model measures {measured:.3f} m')
    return problems


# ------------------------------------------------------------------------------------------------ the run
def lint(models, settings, only=CHECKS, as_set=False, index=None, one_prop=None, surfaces=False):
    """Runs the checks; returns the result dict and plain report lines. surfaces=True also lists the plain-colour materials (a warning)."""
    result = {'files': [m['file'] for m in models], 'checks_run': list(only), 'stripes': [], 'same_plane': [], 'floors_over_ground': [],
              'names': {}, 'glass_alpha_from_picture': [], 'glowing_light_base': [], 'sizes': {}, 'fronts': {}, 'triangles': {}, 'blender': {}}
    lines = []
    for model in models:
        result['triangles'][model['file']] = int(sum(len(p['corners']) for p in model['parts']))
        if 'stripes' in only:
            result['stripes'] += find_stripes(model, settings)
        if 'names' in only:
            prop = one_prop if one_prop is not None else (model['file'].endswith('.glb') and (len(model['roots']) == 1 or index is not None))
            result['names'][model['file']] = check_names(model, settings, prop)
        if 'front' in only:
            result['fronts'][model['file']] = front_of(model, settings)
        if model.get('blender_extras'):
            result['blender'][model['file']] = model['blender_extras']
    groups = [models] if as_set else [[m] for m in models]
    for group in groups:
        if 'same-plane' in only:
            result['same_plane'] += find_same_plane(group, settings)
        if 'floors' in only:
            result['floors_over_ground'] += find_floors_over_ground(group, settings)
    if surfaces:
        result['plain_colour_materials'], materials_used = check_surfaces(models)
    glass, glows, over_pictures = check_materials(models, settings, only)
    result['glass_alpha_from_picture'], result['glowing_light_base'] = glass, glows
    result['glowing_over_a_picture'] = over_pictures
    if 'sizes' in only and index is not None:
        entries = index if isinstance(index, list) else index.get('props', index.get('models', []))
        by_file = {e.get('file'): e for e in entries if isinstance(e, dict)}
        for model in models:
            size = measured_size(model)
            entry = by_file.get(os.path.basename(model['file']))
            result['sizes'][model['file']] = {'measured': {k: round(v, 4) if isinstance(v, float) else v for k, v in size.items()},
                                              'problems': check_index_entry(entry, size, settings) if entry else ['not in the index']}
    failures = []
    lines.append(f'model_lint: {len(models)} file(s){" as one set" if as_set and len(models) > 1 else ""}: '
                 f'{", ".join(os.path.basename(m["file"]) for m in models)}')
    for model in models:
        lines.append(f'  {os.path.basename(model["file"])}: {result["triangles"][model["file"]]:,} triangles, {len(model["parts"])} parts')
    if 'stripes' in only:
        allowed = settings.value('models.striped_parts_allowed')
        by_file = {}
        for s in result['stripes']:
            by_file.setdefault(s['file'], []).append(s)
        lines.append('')
        lines.append('Stripes (squashed texture coordinates):')
        for model in models:
            found = by_file.get(model['file'], [])
            verdict = 'PASS' if len(found) <= allowed else 'FAIL'
            if verdict == 'FAIL':
                failures.append('stripes')
            lines.append(f'  {verdict} {os.path.basename(model["file"])}: {len(found)} striped part(s) (allowed {allowed})')
            for s in found[:12]:
                copies = f', its mesh placed {s["placed_copies"]} times' if s['placed_copies'] > 1 else ''
                lines.append(f'      {s["part"]} ({s["material"]}): {s["striped_square_metres"]} of {s["of_square_metres"]} square metres '
                             f'({100 * s["share"]:.0f}%{copies})')
            if len(found) > 12:
                lines.append(f'      ... and {len(found) - 12} more')
        if result['stripes']:
            lines.append('  Fix: unwrap those faces again (a box or cube projection); a squashed texture paints as streaks the painter copies.')
    if 'same-plane' in only:
        lines.append('')
        found = result['same_plane']
        lines.append(f'{"FAIL" if found else "PASS"} Surfaces on the same plane, facing the same way: {len(found)} pair(s) of objects')
        if found:
            failures.append('same-plane')
            offset = settings.value('models.coplanar_gap_metres')
            for p in found[:12]:
                lines.append(f'      {p["objects"][0]}  and  {p["objects"][1]}: {p["square_metres"]} square metres overlap, facing '
                             f'{p["facing"]}, near {p["at"]}')
            lines.append(f'  Fix: move one surface {offset} m apart (models.coplanar_gap_metres); they swap colour as the camera moves.')
    if 'floors' in only:
        lines.append('')
        found = result['floors_over_ground']
        within = settings.value('models.ground_under_raised_area_metres')
        lines.append(f'{"FAIL" if found else "PASS"} Floors laid just over another ground (0 to {within} m above it): {len(found)}')
        if found:
            failures.append('floors')
            for r in found[:12]:
                pokes = '; the lower one pokes through in places' if r['pokes_through'] else ''
                lines.append(f'      {r["floor"]} over {r["over"]}: {r["square_metres"]} square metres, {r["gap_metres"][0]} to '
                             f'{r["gap_metres"][1]} m apart{pokes}, near {r["at"]}')
            lines.append('  Fix: lower or cut the ground under the raised floor (round 3 lowered the lane under the yards).')
    if 'names' in only:
        lines.append('')
        lines.append('Names:')
        for file_name, named in result['names'].items():
            bad = named['problems']
            if named['fails']:
                failures.append('names')
            lines.append(f'  {"FAIL" if named["fails"] else ("WARN" if bad else "PASS")} {os.path.basename(file_name)}: '
                         + ('; '.join(bad[:6]) + (f' (and {len(bad) - 6} more)' if len(bad) > 6 else '') if bad else 'no copy numbers'))
        if any(n['numbered_roots'] or n['numbered_parts'] for n in result['names'].values()):
            lines.append("  Fix: rename a second copy's parts '<instance>-<part>' at import; the checker and the page take a '.001' part for the first copy.")
    if 'glass' in only:
        lines.append('')
        found = result['glass_alpha_from_picture']
        lines.append(f'{"FAIL" if found else "PASS"} Glass whose see-through value comes from its picture: {len(found)}')
        if found:
            failures.append('glass')
            for g in found:
                note = {True: 'a picture with an alpha channel', False: 'a picture with NO alpha channel: the glass renders solid',
                        None: 'its picture'}[g.get('picture_has_alpha')]
                lines.append(f'      {os.path.basename(g["file"])}: {g["material"]} (alpha {g["alpha_mode"]}, read from {note})')
            lines.append('  Fix: unhook the picture from Alpha and set the value (set_dressing.see_through); a value set on the input is ignored otherwise (log 32).')
    if 'glow' in only:
        lines.append('')
        found = result['glowing_light_base']
        lines.append(f'{"WARN" if found else "PASS"} Glowing materials with a light plain base colour: {len(found)}')
        for g in found:
            lines.append(f'      {os.path.basename(g["file"])}: {g["material"]} (base brightness {g["base_brightness"]})')
        if result['glowing_over_a_picture']:
            names = result['glowing_over_a_picture']
            lines.append(f'  Not judged: {len(names)} glowing material(s) over a picture (lit windows, glowing brick: meant to show it): '
                         + ', '.join(names[:6]) + (' ...' if len(names) > 6 else ''))
        if found:
            lines.append('  Look: a glow lit by a lamp near it renders white (lesson 89); give it a black base, unless it is coloured glass '
                         'meant to show its colour (then keep its own light off it, as the notice corner lantern does).')
    if 'sizes' in only and index is not None:
        lines.append('')
        lines.append('Sizes against the index:')
        for file_name, sized in result['sizes'].items():
            m = sized['measured']
            state = 'WARN' if sized['problems'] else 'PASS'
            lines.append(f'  {state} {os.path.basename(file_name)}: measured {m["width_x"]:.3f} x {m["depth"]:.3f} x {m["height"]:.3f} m'
                         + (f'; {"; ".join(sized["problems"])}' if sized['problems'] else ''))
    if 'front' in only:
        lines.append('')
        lines.append("Fronts (the way each model's lettering faces):")
        for file_name, front in result['fronts'].items():
            if front and front['both_faces']:
                text = f'lettered both ways along {front["front"][2]} ({front["front"]})'
            elif front:
                text = f'{front["front"]} ({front["degrees_off_axis"]} degrees off that axis)'
            else:
                text = 'no lettered material (declare its front in the index)'
            lines.append(f'  {os.path.basename(file_name)}: {text}')
    for file_name, extra in result['blender'].items():
        if extra.get('bevels_without_hardened_normals'):
            lines.append('')
            lines.append(f'WARN Bevels without hardened normals (shade as hard facets, lesson 67): '
                         f'{", ".join(extra["bevels_without_hardened_normals"][:10])}')
        if extra.get('materials_shared'):
            busy = sorted(extra['materials_shared'].items(), key=lambda kv: -len(kv[1]))[:5]
            lines.append('')
            lines.append('Note: materials used by several objects (when building one model, join its parts by material: lesson 67): '
                         + '; '.join(f'{name} ({len(objects)})' for name, objects in busy))
    if surfaces:
        lines.append('')
        for file_name, bare in result['plain_colour_materials'].items():
            used = materials_used[file_name]
            lines.append(f'{"WARN" if bare else "PASS"} Plain-colour materials in {os.path.basename(file_name)}: {len(bare)} of {used} (no picture and no normal map)'
                         + (': ' + ', '.join(bare[:8]) + (' ...' if len(bare) > 8 else '') if bare else ''))
        if any(result['plain_colour_materials'].values()):
            lines.append('  Look: a place built of plain colours reads as boxes. Inside Blender run `explainer-film-place finish` (real normal maps, variation, wear); for a .glb, give each surface a base picture and a normal map '
                         '(the model lint passes plain colours, the place audit does not).')
    result['failed'] = sorted(set(failures))
    lines.append('')
    lines.append('Verdict: ' + ('FAIL (' + ', '.join(result['failed']) + ')' if failures else 'PASS'))
    return result, lines


def write_index(index, models, settings, path):
    """A copy of the index with the measured size, the front and the triangle count written into each entry."""
    entries = index if isinstance(index, list) else index.get('props', index.get('models', []))
    by_file = {os.path.basename(m['file']): m for m in models}
    for entry in entries:
        model = by_file.get(entry.get('file'))
        if model is None:
            continue
        size = measured_size(model)
        entry['size_metres'] = {k: round(size[k], 3) for k in ('width_x', 'depth', 'height')}
        entry['size_from'] = 'measured from the saved model by model_lint.py'
        front = front_of(model, settings)
        entry['front'] = front['front'] if front else entry.get('front', 'not measured: no lettered material')
        entry['triangles'] = int(sum(len(p['corners']) for p in model['parts']))
    with open(path, 'w') as handle:
        json.dump(index, handle, indent=1)


def main(argv=None):
    inside_blender = 'bpy' in sys.modules
    if argv is None:
        argv = sys.argv[sys.argv.index('--') + 1:] if inside_blender and '--' in sys.argv else (sys.argv[1:] if not inside_blender else [])
    parser = argparse.ArgumentParser(description='Checks 3D models (.glb files, or the scene open in Blender) for the faults this '
                                                 'project found by eye: stripes, same-plane faces, floors just over ground, copy-number '
                                                 'names, glass alpha from a picture, glowing light bases, index sizes and fronts. See the '
                                                 'note at the top of this file.')
    parser.add_argument('files', nargs='*', help='.glb files (none inside Blender: the open scene is checked)')
    parser.add_argument('--as-set', action='store_true', help='treat the files as one set (floors and same-plane faces across files)')
    parser.add_argument('--index', help='a props index.json to compare sizes with')
    parser.add_argument('--write-index', help='write a copy of the index with measured sizes, fronts and triangles here')
    parser.add_argument('--only', help='comma list of checks: ' + ','.join(CHECKS))
    parser.add_argument('--prop', action='store_true', help='each file is one prop: it must have one root named as the file')
    parser.add_argument('--lint-files', action='store_true', help='inside Blender: check the .glb files given instead of the open scene')
    parser.add_argument('--surfaces', action='store_true', help='also warn about materials that are a plain colour (no picture, no normal map); never a failure')
    add_output_options(parser)
    args, _unknown = parser.parse_known_args(argv) if inside_blender else (parser.parse_args(argv), [])
    settings = load_settings(args.settings)
    only = tuple(args.only.split(',')) if args.only else CHECKS
    unknown = [c for c in only if c not in CHECKS]
    if unknown:
        raise SystemExit(f'model_lint: unknown check(s) {", ".join(unknown)}; choose from {", ".join(CHECKS)}')
    if inside_blender and not args.lint_files:
        models = [parts_from_blender()]   # inside Blender the open scene is checked (other words after -- belong to other scripts)
    elif args.files:
        models = [parts_from_glb(path) for path in args.files]
    else:
        parser.error('give .glb files, or run inside Blender on a scene')
    index = None
    if args.index:
        with open(args.index) as handle:
            index = json.load(handle)
    result, lines = lint(models, settings, only, args.as_set, index, True if args.prop else None, surfaces=args.surfaces)
    if args.write_index:
        if not index:
            raise SystemExit('model_lint: --write-index needs --index')
        if args.index and os.path.abspath(args.write_index) == os.path.abspath(args.index):
            raise SystemExit('model_lint: --write-index must name a new file, not the index itself (look at the copy first)')
        write_index(index, models, settings, args.write_index)
        lines.append(f'Wrote the index with measured sizes and fronts: {args.write_index}')
    finish('model_lint', result, lines, settings, args)
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    code = main()
    if 'bpy' not in sys.modules:
        sys.exit(code)
