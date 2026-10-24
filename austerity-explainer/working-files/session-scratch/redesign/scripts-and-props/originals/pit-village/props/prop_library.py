# What this does: shared helpers for the pit-village prop scripts (run inside Blender): where the
# finished props go, counting triangles, measuring a prop's real size, making every prop stand on the
# ground (lowest point at height 0, centred over the origin), writing the .glb (glTF, Y-up for
# three.js) and adding the prop's line to index.json.
#
# Every prop .glb has one root empty named after the prop; all its parts hang under it.

import json
import os
import tempfile

import bpy
from mathutils import Vector

KIT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
PROPS_FOLDER = os.path.join(KIT, 'assets', 'models', 'pit-village', 'props')
INDEX_PATH = os.path.join(PROPS_FOLDER, 'index.json')
# downloads and in-between pictures (not kept); set PIT_VILLAGE_SCRATCH to choose the folder
SCRATCH = os.environ.get('PIT_VILLAGE_SCRATCH', os.path.join(tempfile.gettempdir(), 'pit-village-props'))
DOWNLOADS = os.path.join(SCRATCH, 'downloads')


def empty_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def count_triangles(objects=None):
    graph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objects or mesh_objects():
        evaluated = o.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    return total


def bounds(objects=None):
    """Lowest and highest corner (world space) of all the parts."""
    low = Vector((1e9, 1e9, 1e9)); high = Vector((-1e9, -1e9, -1e9))
    for o in objects or mesh_objects():
        for corner in o.bound_box:
            point = o.matrix_world @ Vector(corner)
            low = Vector(map(min, low, point)); high = Vector(map(max, high, point))
    return low, high


def stand_on_ground(prop_name, keep_names=()):
    """Bake every part's placement into its shape, move the whole prop so it stands on height 0
    centred over the origin, and hang the parts under one root empty called prop_name.
    keep_names: parts (wheels) that keep their own origin so they can turn on their axle."""
    bpy.context.view_layer.update()
    for o in mesh_objects():
        world = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = world
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objects():
        if o.name in keep_names: continue
        if o.data.users > 1: o.data = o.data.copy()
        o.select_set(True)
    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    low, high = bounds()
    shift = Vector((-(low.x + high.x) / 2, -(low.y + high.y) / 2, -low.z))
    root = bpy.data.objects.new(prop_name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in mesh_objects():
        o.location += shift
        o.parent = root
    bpy.context.view_layer.update()
    return root


def reduce_triangles(limit=28000):
    """Thin out the mesh (Blender's 'collapse' decimation) until the whole prop is under limit."""
    total = count_triangles()
    if total <= limit: return total
    ratio = limit / total
    for o in mesh_objects():
        modifier = o.modifiers.new('reduce', 'DECIMATE')
        modifier.ratio = ratio
        modifier.use_collapse_triangulate = True
    return count_triangles()


def texture_sizes():
    sizes = set()
    for image in bpy.data.images:
        if image.size[0] > 0: sizes.add(f'{image.size[0]}x{image.size[1]}')
    return sorted(sizes)


def save_prop(file_name, description, source, licence, extra=None):
    """Write the .glb and add or replace its line in index.json. Returns the index entry."""
    os.makedirs(PROPS_FOLDER, exist_ok=True)
    path = os.path.join(PROPS_FOLDER, f'{file_name}.glb')
    triangles = count_triangles()
    low, high = bounds()
    size = [round(high.x - low.x, 3), round(high.y - low.y, 3), round(high.z - low.z, 3)]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_extras=True, export_yup=True)
    entry = {
        'file': f'{file_name}.glb',
        'what': description,
        'size_metres': {'width_x': size[0], 'depth': size[1], 'height': size[2]},
        'triangles': triangles,
        'textures': texture_sizes(),
        'kilobytes': os.path.getsize(path) // 1024,
        'source': source,
        'licence': licence,
    }
    if extra: entry.update(extra)
    index = []
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f: index = json.load(f)
    index = [e for e in index if e['file'] != entry['file']] + [entry]
    index.sort(key=lambda e: e['file'])
    with open(INDEX_PATH, 'w') as f: json.dump(index, f, indent=1)
    print(f'PROP {file_name}: {triangles} triangles, size {size} m, {entry["kilobytes"]} KB, textures {entry["textures"]}')
    return entry
