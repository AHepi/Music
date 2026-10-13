# What this does: the building tools for making film models in Blender by script (no screen needed,
# using Blender's Python module `bpy`). It makes boxes, cylinders and custom shapes with softly
# bevelled edges, cuts real openings (for windows and doors), gives every part a material wearing a
# texture from textures.py at the right real size, bakes soft shading into corners ("ambient
# occlusion": the darkening where surfaces meet, worked out once by Blender's Cycles renderer), and
# writes a .glb file that the three.js stage loads with GLTFLoader.
#
# Conventions: Blender's z is up; the front of a model faces Blender -y, which becomes +z (towards the
# camera) in three.js. 1 Blender unit = 1 three.js unit. Named empties ("markers") travel with the
# model so a page can find spots on it (a chimney top for smoke, a door, a yard).
#
# Use from a model script:
#   import model_kit as mk
#   mk.reset()
#   wall = mk.box('wall', size=(3, 2, 1.3), at=(0, 0, 0.65), material=mk.material('brick-red'))
#   mk.cut(wall, [mk.box('hole', size=(0.3, 0.4, 0.6), at=(0, -1, 0.6))])
#   mk.marker('chimney_top', (1, 0.5, 3.1))
#   mk.finish('path/model.glb', bake_shading=True)

import math
import os
import sys
import tempfile

import bpy  # first: Blender's other modules (bmesh, mathutils) load with it
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textures  # noqa: E402

TEXTURE_FOLDER = tempfile.mkdtemp(prefix='model-textures-')
_materials = {}
_texture_cache = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()
    _texture_cache.clear()


# ----------------------------------------------------------------------------------- materials

def _image(name, picture, colour_data=True):
    """Save a Pillow picture and load it into Blender (packed into the .glb on export)."""
    # JPEG for everything (normal maps too): a tenth of the size, and the film's grain hides the rest
    path = os.path.join(TEXTURE_FOLDER, f'{name}.jpg')
    picture.save(path, quality=90 if colour_data else 94)
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'sRGB' if colour_data else 'Non-Color'
    return image


def _texture(kind):
    if kind not in _texture_cache:
        colour, normal, units = textures.ALL[kind]()
        _texture_cache[kind] = (_image(kind, colour), _image(f'{kind}-normal', normal, False) if normal else None, units)
    return _texture_cache[kind]


def material(kind=None, *, name=None, colour=(0.8, 0.8, 0.8), roughness=0.85, metallic=0.0,
             glow=None, glow_strength=0.0, picture=None, glow_picture=None, normal_strength=1.0):
    """A material. kind: a texture name from textures.ALL ('brick-red', 'stone', 'slate', ...) or
    None for a plain colour. picture / glow_picture: Pillow pictures mapped once over a part (windows,
    signs). glow: a colour that glows (lamps, lit windows; three.js can turn it up and down by the
    material's name). Names matter: the page finds lit windows by material name."""
    key = name or kind or f'plain-{colour}'
    if key in _materials: return _materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Base Color'].default_value = (*colour, 1)
    units = None
    if kind:
        image, normal, units = _texture(kind)
        tex = nodes.new('ShaderNodeTexImage'); tex.image = image
        links.new(tex.outputs['Color'], shader.inputs['Base Color'])
        if normal:
            ntex = nodes.new('ShaderNodeTexImage'); ntex.image = normal
            nmap = nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = normal_strength
            links.new(ntex.outputs['Color'], nmap.inputs['Color']); links.new(nmap.outputs['Normal'], shader.inputs['Normal'])
    if picture is not None:
        tex = nodes.new('ShaderNodeTexImage'); tex.image = _image(f'{key}-picture', picture)
        links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    if glow is not None or glow_picture is not None:
        shader.inputs['Emission Strength'].default_value = glow_strength or 1.0
        if glow_picture is not None:
            gtex = nodes.new('ShaderNodeTexImage'); gtex.image = _image(f'{key}-glow', glow_picture)
            links.new(gtex.outputs['Color'], shader.inputs['Emission Color'])
        else:
            shader.inputs['Emission Color'].default_value = (*glow, 1)
    m['tile_units'] = units or (0, 0)
    _materials[key] = m
    return m


# --------------------------------------------------------------------------------------- shapes

def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _finish_part(obj, material_, bevel, map_units):
    if material_ is not None: obj.data.materials.append(material_)
    if bevel:
        mod = obj.modifiers.new('bevel', 'BEVEL'); mod.width = bevel; mod.segments = 2
        mod.limit_method = 'ANGLE'; mod.harden_normals = False
    if map_units is not False: box_map(obj, map_units)
    return obj


def box(name, size, at=(0, 0, 0), material=None, bevel=0.0, rotate=(0, 0, 0), map_units=None):
    """A box of size (x, y, z) centred at `at`."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(mesh); bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj.location = at; obj.rotation_euler = rotate
    return _finish_part(obj, material, bevel, map_units)


def cylinder(name, radius, depth, at=(0, 0, 0), material=None, sides=16, bevel=0.0, rotate=(0, 0, 0), radius_top=None, map_units=None, cap=True):
    """An upright cylinder (or cone when radius_top differs) centred at `at`."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=sides, radius1=radius, radius2=radius if radius_top is None else radius_top, depth=depth)
    bm.to_mesh(mesh); bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj.location = at; obj.rotation_euler = rotate
    for poly in obj.data.polygons: poly.use_smooth = len(poly.vertices) == 4
    return _finish_part(obj, material, bevel, map_units)


def prism(name, outline, depth, at=(0, 0, 0), material=None, bevel=0.0, axis='y', map_units=None):
    """A flat outline [(a, b), ...] pushed out `depth` along an axis ('y': outline in x-z, like a
    gable seen from the front; 'z': outline in x-y, like a floor plan)."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = []
    for a, b in outline:
        verts.append(bm.verts.new((a, -depth / 2, b) if axis == 'y' else (a, b, -depth / 2)))
    face = bm.faces.new(verts)
    shift = Vector((0, depth, 0)) if axis == 'y' else Vector((0, 0, depth))
    result = bmesh.ops.extrude_face_region(bm, geom=[face])
    moved = [e for e in result['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=shift)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj.location = at
    return _finish_part(obj, material, bevel, map_units)


def plane(name, size, at=(0, 0, 0), material=None, rotate=(0, 0, 0), map_units=False):
    """A flat rectangle size (x, y) facing +z; with map_units=False its picture covers it once."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], 0))
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x / size[0] + 0.5, loop.vert.co.y / size[1] + 0.5)
    bm.to_mesh(mesh); bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj.location = at; obj.rotation_euler = rotate
    return _finish_part(obj, material, 0, map_units)


def corrugated_sheet(name, width, length, at=(0, 0, 0), material=None, pitch=0.045, depth=0.012, rotate=(0, 0, 0)):
    """A sheet of corrugated iron, ribs running along `length` (local y), waves across `width`."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    across = max(8, int(width / pitch * 6))
    uv = bm.loops.layers.uv.new('UVMap')
    rows = []
    for j in (0, 1):
        row = []
        for i in range(across + 1):
            x = -width / 2 + width * i / across
            z = depth / 2 * math.sin(x / pitch * 2 * math.pi)
            row.append(bm.verts.new((x, -length / 2 + length * j, z)))
        rows.append(row)
    for i in range(across):
        f = bm.faces.new([rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]])
        f.smooth = True
        for loop in f.loops: loop[uv].uv = (loop.vert.co.x, loop.vert.co.y)
    bm.to_mesh(mesh); bm.free()
    obj = _link(bpy.data.objects.new(name, mesh))
    obj.location = at; obj.rotation_euler = rotate
    solid = obj.modifiers.new('thick', 'SOLIDIFY'); solid.thickness = 0.006
    if material is not None: obj.data.materials.append(material)
    return obj


def array(obj, count, offset):
    """Repeat a part `count` times, each `offset` (x, y, z) further on."""
    mod = obj.modifiers.new('array', 'ARRAY'); mod.count = count
    mod.use_relative_offset = False; mod.use_constant_offset = True; mod.constant_offset_displace = offset
    return obj


def cut(target, cutters):
    """Cut openings: subtract each cutter shape from target (then the cutters are removed)."""
    if not cutters: return target
    joined = cutters[0]
    if len(cutters) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for c in cutters: c.select_set(True)
        bpy.context.view_layer.objects.active = joined
        bpy.ops.object.join()
    mod = target.modifiers.new('cut', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = joined; mod.solver = 'EXACT'
    apply_modifiers(target, only=['cut'])
    bpy.data.objects.remove(joined, do_unlink=True)
    return target


def apply_modifiers(obj, only=None):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        if only is None or mod.name in only:
            bpy.ops.object.modifier_apply(modifier=mod.name)


def box_map(obj, units=None):
    """Give a part texture coordinates by projecting each face from the side it faces, in real
    world size, so a brick is the same size on every wall. units: (x, y) world units per picture
    tile; by default the material's own tile size."""
    if units is None:
        units = tuple(obj.data.materials[0].get('tile_units', (1, 1))) if obj.data.materials else (1, 1)
        if not units or units[0] == 0: units = (1, 1)
    mesh = obj.data
    bm = bmesh.new(); bm.from_mesh(mesh)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    scale = obj.scale
    for f in bm.faces:
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in f.loops:
            co = loop.vert.co
            x, y, z = co.x * scale.x + obj.location.x, co.y * scale.y + obj.location.y, co.z * scale.z + obj.location.z
            if az >= ax and az >= ay: u, v = x, y
            elif ax >= ay: u, v = y, z
            else: u, v = x, z
            loop[uv].uv = (u / units[0], v / units[1])
    bm.to_mesh(mesh); bm.free()


def marker(name, at):
    """A named empty: a spot the page can find (three.js: model.getObjectByName(name))."""
    empty = bpy.data.objects.new(name, None)
    empty.location = at
    return _link(empty)


def group(name, parts):
    """Put parts under one named empty, so a page can find, move, show or hide them together."""
    parent = marker(name, (0, 0, 0))
    for p in parts: p.parent = parent
    return parent


# ------------------------------------------------------------------------------ finishing

def _ensure_gltf_output_group():
    """The node group the glTF exporter looks for to find the baked shading ('Occlusion')."""
    name = 'glTF Material Output'
    if name in bpy.data.node_groups: return bpy.data.node_groups[name]
    tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    tree.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    tree.nodes.new('NodeGroupInput')
    return tree


def bake_shading(objects, size=1024, samples=32, margin=4, reach=0.6):
    """Bake soft corner shading for the given parts into one picture and attach it to their
    materials as glTF 'occlusion' (three.js applies it as the aoMap). The parts get a second set of
    texture coordinates ('shading') laid out without overlaps."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples
    scene.render.bake.margin = margin
    # how far away something can be and still darken a corner (Blender's default, 10, darkens everything)
    if scene.world is None: scene.world = bpy.data.worlds.new('world')
    scene.world.light_settings.distance = reach
    image = bpy.data.images.new('shading', size, size)
    meshes = [o for o in objects if o.type == 'MESH']
    for o in meshes:
        apply_modifiers(o)
        layer = o.data.uv_layers.new(name='shading')
    # lay out all parts' 'shading' coordinates together in one picture
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
        o.data.uv_layers.active = o.data.uv_layers['shading']
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.003, angle_limit=math.radians(66))
    bpy.ops.uv.pack_islands(margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    group_tree = _ensure_gltf_output_group()
    done = set()
    for o in meshes:
        for m in o.data.materials:
            if m is None or m.name in done: continue
            done.add(m.name)
            nodes, links = m.node_tree.nodes, m.node_tree.links
            uvnode = nodes.new('ShaderNodeUVMap'); uvnode.uv_map = 'shading'
            tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.name = 'shading'
            links.new(uvnode.outputs['UV'], tex.inputs['Vector'])
            nodes.active = tex
            out = nodes.new('ShaderNodeGroup'); out.node_tree = group_tree
            sep = nodes.new('ShaderNodeSeparateColor')
            links.new(tex.outputs['Color'], sep.inputs['Color'])
            links.new(sep.outputs['Red'], out.inputs['Occlusion'])
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.bake(type='AO', margin=margin, use_clear=True)
    image.filepath_raw = os.path.join(TEXTURE_FOLDER, 'shading.png'); image.file_format = 'PNG'; image.save()
    for o in meshes: o.data.uv_layers.active = o.data.uv_layers['UVMap'] if 'UVMap' in o.data.uv_layers else o.data.uv_layers[0]
    return image


def count_triangles(objects=None):
    graph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objects or bpy.context.scene.objects:
        if o.type != 'MESH': continue
        mesh = o.evaluated_get(graph).to_mesh()
        mesh.calc_loop_triangles(); total += len(mesh.loop_triangles)
        o.evaluated_get(graph).to_mesh_clear()
    return total


def finish(path, bake=False, bake_size=1024, bake_samples=32, bake_skip=()):
    """Apply all modifiers, optionally bake corner shading, and write the .glb."""
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes: apply_modifiers(o)
    print(f'{os.path.basename(path)}: {len(meshes)} parts, {count_triangles(meshes)} triangles')
    if bake:
        to_bake = [o for o in meshes if not any(o.name.startswith(s) for s in bake_skip)]
        skipped = [o for o in meshes if o not in to_bake]
        # a part left out of the bake must not share a material with a baked part (the material will
        # point at shading coordinates the left-out part does not have): give it its own copies
        baked_materials = {m.name for o in to_bake for m in o.data.materials if m}
        copies = {}
        for o in skipped:
            for i, m in enumerate(o.data.materials):
                if m and m.name in baked_materials:
                    copies.setdefault(m.name, m.copy())
                    copies[m.name].name = f'{m.name}-unshaded'
                    o.data.materials[i] = copies[m.name]
        bake_shading(to_bake, size=bake_size, samples=bake_samples)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_extras=True, export_yup=True)
    print(f'wrote {path} ({os.path.getsize(path) // 1024} KB)')
