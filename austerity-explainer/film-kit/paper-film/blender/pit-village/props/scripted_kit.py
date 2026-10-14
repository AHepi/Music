# What this does: the building tools for the scripted pit-village props (run inside Blender).
# Materials that wear Poly Haven surface textures (colour, surface relief "normal" map, and roughness)
# at their real size; materials that wear one painted picture (the signs, the sacks' stencils) with
# optional see-through parts; and shapes: bevelled boxes, cylinders, rings (wheel rims and tyres),
# tapered rods (spokes, handles), rows of rivets and bolt heads, chain links and coal lumps.
#
# Every shape is a Blender object; its texture coordinates are laid out by projecting each face from
# the side it faces, in metres, so a plank's grain is the same size everywhere.

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import prop_library as library

SURFACES = os.path.join(library.DOWNLOADS, 'surfaces')
PICTURES = os.path.join(library.SCRATCH, 'pictures')

_materials = {}


def reset():
    library.empty_scene()
    _materials.clear()


# ------------------------------------------------------------------------------------ materials

def _load(path, colour_data=True):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if colour_data else 'Non-Color'
    return image


def tinted_image(asset_id, tint, name, strength=1.0):
    """A copy of a Poly Haven colour picture multiplied by a colour (brass from steel plate, green
    paint from grey planks), so glTF carries the tint inside the picture itself."""
    key = f'tint-{name}'
    if key in bpy.data.images: return bpy.data.images[key]
    import numpy as np
    source = _load(os.path.join(SURFACES, asset_id, 'Diffuse.jpg'))
    width, height = source.size
    pixels = np.empty(width * height * 4, np.float32)
    source.pixels.foreach_get(pixels)
    pixels = pixels.reshape(-1, 4)
    grey = pixels[:, :3].mean(axis=1, keepdims=True)
    mixed = pixels[:, :3] * (1 - strength) + grey * strength
    pixels[:, :3] = np.clip(mixed * np.array(tint, np.float32) * 2.0, 0, 1)
    image = bpy.data.images.new(key, width, height)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = os.path.join(library.SCRATCH, 'tinted', f'{key}.jpg')
    os.makedirs(os.path.dirname(image.filepath_raw), exist_ok=True)
    image.file_format = 'JPEG'
    image.save()
    return image


def surface_material(name, asset_id, tile_metres=1.0, tint=None, tint_strength=1.0, metallic=None,
                     roughness=None, normal_strength=1.0):
    """A material wearing a Poly Haven surface. tile_metres: how many metres one copy of the picture
    covers. metallic / roughness: None to use the picture's own maps, or a number."""
    if name in _materials: return _materials[name]
    folder = os.path.join(SURFACES, asset_id)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = nodes['Principled BSDF']
    colour = nodes.new('ShaderNodeTexImage')
    colour.image = tinted_image(asset_id, tint, name, tint_strength) if tint else _load(os.path.join(folder, 'Diffuse.jpg'))
    links.new(colour.outputs['Color'], shader.inputs['Base Color'])
    packed = nodes.new('ShaderNodeTexImage')  # red: shading, green: roughness, blue: metal
    packed.image = _load(os.path.join(folder, 'arm.jpg'), False)
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(packed.outputs['Color'], split.inputs['Color'])
    if roughness is None:
        links.new(split.outputs['Green'], shader.inputs['Roughness'])
    else:
        shader.inputs['Roughness'].default_value = roughness
    if metallic is None:
        links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    else:
        shader.inputs['Metallic'].default_value = metallic
    relief = nodes.new('ShaderNodeTexImage')
    relief.image = _load(os.path.join(folder, 'nor_gl.jpg'), False)
    normal_map = nodes.new('ShaderNodeNormalMap'); normal_map.inputs['Strength'].default_value = normal_strength
    links.new(relief.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    m['tile_metres'] = tile_metres
    _materials[name] = m
    return m


def picture_material(name, picture_file, see_through=False, normal_file=None, roughness=0.85, metallic=0.0,
                     tile_metres=None, double_sided=False):
    """A material wearing one painted picture. see_through=True: the picture's transparency cuts the
    shape (glTF 'alpha mask': torn paper corners); see_through='blend': partly see-through (gauze)."""
    if name in _materials: return _materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    picture = nodes.new('ShaderNodeTexImage'); picture.image = _load(os.path.join(PICTURES, picture_file))
    links.new(picture.outputs['Color'], shader.inputs['Base Color'])
    if see_through == 'blend':
        # see-through by degrees (glTF 'alpha blend'): fine wire gauze seen from a distance
        links.new(picture.outputs['Alpha'], shader.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
    elif see_through:
        # the glTF exporter reads a Round node between picture alpha and shader alpha as "alpha mask"
        cut = nodes.new('ShaderNodeMath'); cut.operation = 'ROUND'
        links.new(picture.outputs['Alpha'], cut.inputs[0])
        links.new(cut.outputs['Value'], shader.inputs['Alpha'])
    if normal_file:
        relief = nodes.new('ShaderNodeTexImage'); relief.image = _load(os.path.join(PICTURES, normal_file), False)
        normal_map = nodes.new('ShaderNodeNormalMap')
        links.new(relief.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    m.use_backface_culling = not double_sided
    if tile_metres: m['tile_metres'] = tile_metres
    _materials[name] = m
    return m


def plain_material(name, colour, roughness=0.6, metallic=0.0, glow=None, glow_strength=0.0):
    """A one-colour material: brass, flame, glass. glow: a colour that shines (the lamp flame)."""
    if name in _materials: return _materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    shader = m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if glow:
        shader.inputs['Emission Color'].default_value = (*glow, 1)
        shader.inputs['Emission Strength'].default_value = glow_strength
    _materials[name] = m
    return m


# --------------------------------------------------------------------------- texture coordinates

def project_by_facing(obj, tile_metres=None):
    """Lay out texture coordinates by projecting each face from the side it faces, in metres of world
    space (taking the object's placement into account), divided by the material's tile size."""
    if tile_metres is None:
        material = obj.data.materials[0] if obj.data.materials else None
        tile_metres = material.get('tile_metres', 1.0) if material else 1.0
    world = obj.matrix_world
    rotation = world.to_3x3()
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        n = rotation @ face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            p = world @ loop.vert.co
            if az >= ax and az >= ay: u, v = p.x, p.y
            elif ax >= ay: u, v = p.y, p.z
            else: u, v = p.x, p.z
            loop[uv].uv = (u / tile_metres, v / tile_metres)
    bm.to_mesh(obj.data); bm.free()


def project_along_length(obj, tile_metres=0.5):
    """For long round parts (spokes, handles, shafts): wrap the grain along the part's own length."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            angle = math.atan2(co.y, co.x)
            loop[uv].uv = (angle * 0.03 / tile_metres, co.z / tile_metres)
    bm.to_mesh(obj.data); bm.free()


# ---------------------------------------------------------------------------------------- shapes

def _object(name, bm, material, at, rotate, bevel, smooth=False):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at; obj.rotation_euler = rotate
    if material is not None: obj.data.materials.append(material)
    if smooth:
        for poly in mesh.polygons: poly.use_smooth = True
    if bevel:
        modifier = obj.modifiers.new('bevel', 'BEVEL'); modifier.width = bevel; modifier.segments = 2
        modifier.limit_method = 'ANGLE'
        apply_all(obj)
    bpy.context.view_layer.update()
    return obj


def apply_all(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def box(name, size, at=(0, 0, 0), material=None, bevel=0.0, rotate=(0, 0, 0), map_tile=None):
    """A box of size (x, y, z) centred at `at`, edges softly bevelled, textured at real size."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    obj = _object(name, bm, material, at, rotate, bevel)
    if material is not None: project_by_facing(obj, map_tile)
    return obj


def cylinder(name, radius, depth, at=(0, 0, 0), material=None, sides=24, rotate=(0, 0, 0), radius_top=None,
             bevel=0.0, map_tile=None, smooth=True):
    """An upright cylinder (a cone when radius_top differs) centred at `at`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=radius,
                          radius2=radius if radius_top is None else radius_top, depth=depth)
    obj = _object(name, bm, None, at, rotate, 0)
    if material is not None: obj.data.materials.append(material)
    for poly in obj.data.polygons: poly.use_smooth = smooth and len(poly.vertices) == 4
    if bevel:
        modifier = obj.modifiers.new('bevel', 'BEVEL'); modifier.width = bevel; modifier.segments = 2
        modifier.limit_method = 'ANGLE'; apply_all(obj)
    if material is not None: project_by_facing(obj, map_tile)
    return obj


def rod(name, start, end, radius, material=None, sides=8, radius_end=None, map_tile=0.5):
    """A round rod from one point to another (a spoke, a handle, an axle), optionally tapering."""
    start, end = Vector(start), Vector(end)
    length = (end - start).length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=radius,
                          radius2=radius if radius_end is None else radius_end, depth=length)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, length / 2))
    obj = _object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
    project_along_length(obj, map_tile)
    direction = (end - start).normalized()
    obj.matrix_world = Matrix.Translation(start) @ direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bpy.context.view_layer.update()
    return obj


def ring(name, inner_radius, outer_radius, width, at=(0, 0, 0), material=None, segments=48, rotate=(0, 0, 0),
         map_tile=None):
    """A flat ring (washer shape) lying in x-y, `width` thick in z: wheel rims, iron tyres, hoops."""
    bm = bmesh.new()
    rows = []
    for radius, z in ((inner_radius, -width / 2), (outer_radius, -width / 2), (outer_radius, width / 2), (inner_radius, width / 2)):
        rows.append([bm.verts.new((radius * math.cos(2 * math.pi * i / segments), radius * math.sin(2 * math.pi * i / segments), z))
                     for i in range(segments)])
    for side in range(4):
        a, b = rows[side], rows[(side + 1) % 4]
        for i in range(segments):
            j = (i + 1) % segments
            face = bm.faces.new([a[i], a[j], b[j], b[i]])
            face.smooth = side in (0, 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _object(name, bm, material, at, rotate, 0)
    if material is not None: project_by_facing(obj, map_tile)
    return obj


def studs(name, points, radius, material, normal=(0, -1, 0), height_ratio=0.55, sides=8):
    """Many round rivet or bolt heads (domes) at the given points, facing `normal`, in one object."""
    bm = bmesh.new()
    facing = Vector(normal).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    for point in points:
        piece = bmesh.new()
        bmesh.ops.create_uvsphere(piece, u_segments=sides, v_segments=4, radius=radius)
        for v in piece.verts:
            v.co.z = max(v.co.z, 0) * height_ratio
        bmesh.ops.remove_doubles(piece, verts=piece.verts, dist=radius * 0.01)
        bmesh.ops.transform(piece, matrix=Matrix.Translation(point) @ facing, verts=piece.verts)
        mesh = bpy.data.meshes.new('piece'); piece.to_mesh(mesh); piece.free()
        bm.from_mesh(mesh); bpy.data.meshes.remove(mesh)
    obj = _object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
    project_by_facing(obj, 0.2)
    return obj


def hex_bolts(name, points, size, material, normal=(0, -1, 0)):
    """Square-ish bolt heads with a nut look (six-sided, short), facing `normal`."""
    bm = bmesh.new()
    facing = Vector(normal).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    for point in points:
        piece = bmesh.new()
        bmesh.ops.create_cone(piece, cap_ends=True, segments=6, radius1=size, radius2=size * 0.9, depth=size * 0.7)
        bmesh.ops.translate(piece, verts=piece.verts, vec=(0, 0, size * 0.35))
        bmesh.ops.transform(piece, matrix=Matrix.Translation(point) @ facing, verts=piece.verts)
        mesh = bpy.data.meshes.new('piece'); piece.to_mesh(mesh); piece.free()
        bm.from_mesh(mesh); bpy.data.meshes.remove(mesh)
    obj = _object(name, bm, material, (0, 0, 0), (0, 0, 0), 0)
    project_by_facing(obj, 0.2)
    return obj


def chain_link(name, at, rotate, material, length=0.07, width=0.04, thickness=0.009):
    """One oval iron chain link."""
    bm = bmesh.new()
    segments, around = 20, 6
    rows = []
    for i in range(segments):
        t = 2 * math.pi * i / segments
        centre = Vector(((length / 2 - width / 2) * (1 if math.cos(t) > 0 else -1) + width / 2 * math.cos(t), width / 2 * math.sin(t), 0))
        outward = Vector((math.cos(t), math.sin(t), 0))
        rows.append([bm.verts.new(centre + outward * thickness * math.cos(2 * math.pi * k / around) +
                                  Vector((0, 0, thickness * math.sin(2 * math.pi * k / around)))) for k in range(around)])
    for i in range(segments):
        a, b = rows[i], rows[(i + 1) % segments]
        for k in range(around):
            bm.faces.new([a[k], a[(k + 1) % around], b[(k + 1) % around], b[k]]).smooth = True
    obj = _object(name, bm, material, at, rotate, 0)
    project_by_facing(obj, 0.2)
    return obj


def lump(name, size, seed, material, detail=2):
    """One angular lump of coal: a rough ball with flat broken faces."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=detail, radius=1.0)
    stretch = Vector((rng.uniform(0.8, 1.4), rng.uniform(0.7, 1.1), rng.uniform(0.5, 0.85)))
    for v in bm.verts:
        v.co = Vector((v.co.x * stretch.x, v.co.y * stretch.y, v.co.z * stretch.z)) * rng.uniform(0.8, 1.15)
    # knock off a few flat faces, the way coal breaks
    for _ in range(3):
        cut_normal = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        limit = rng.uniform(0.55, 0.8)
        for v in bm.verts:
            reach = v.co.dot(cut_normal)
            if reach > limit: v.co -= cut_normal * (reach - limit)
    bmesh.ops.scale(bm, vec=(size, size, size), verts=bm.verts)
    obj = _object(name, bm, material, (0, 0, 0), (0, 0, 0), 0)
    project_by_facing(obj, 0.15)
    return obj


def scatter_copies(name, originals, placements, material=None):
    """Copies of the given shapes at (location, rotation, scale) placements, joined into one object."""
    bm = bmesh.new()
    for index, (location, rotation, scale) in enumerate(placements):
        source = originals[index % len(originals)]
        matrix = Matrix.LocRotScale(Vector(location), rotation, Vector((scale, scale, scale)))
        piece = source.data.copy()
        piece.transform(matrix)
        bm.from_mesh(piece); bpy.data.meshes.remove(piece)
    obj = _object(name, bm, material or originals[0].data.materials[0], (0, 0, 0), (0, 0, 0), 0)
    for poly in obj.data.polygons: poly.use_smooth = False
    project_by_facing(obj, 0.15)
    return obj


def join(name, parts):
    """Join parts that never move separately into one object (fewer draw calls in three.js)."""
    parts = [p for p in parts if p is not None]
    for p in parts:
        apply_all(p)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined


def remove(obj):
    bpy.data.objects.remove(obj, do_unlink=True)
