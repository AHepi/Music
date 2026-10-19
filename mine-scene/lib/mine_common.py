# What this does: the shared toolbox every part of the coal-mine scene is built with, so all the parts fit together.
# It holds (1) LAYOUT: where each big thing stands, in metres, (2) surface materials made from the uploaded pictures and
# maps (colour + normal + height; brick, slate, wood, metal, mud, gravel) and a few plain ones (glow, coal, smoke),
# (3) MeshBuilder: a fast way to build many boxes, beams, cylinders, rings and rocks into ONE Blender object, with picture
# coordinates ("UV") worked out automatically so brick courses run level and slate courses run across the roof slope,
# (4) ground_height(x, y): how high the yard ground is at any spot, and (5) small helpers to light, point a camera and
# take quick preview photos of one part on its own.
# Use: in a Blender script, sys.path.insert(0, ".../lib"); import mine_common as mc
import math
import os
import random

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTURE_FOLDER = os.environ.get('MINE_TEXTURES', os.path.join(os.path.dirname(HERE), 'textures_ready'))

# --------------------------------------------------------------------------------------------------------------------
# LAYOUT: one shared plan. +X is to the right of the picture, +Y goes away from the camera, +Z is up. One unit = one metre.
# --------------------------------------------------------------------------------------------------------------------
LAYOUT = {
    # The engine house: a long brick building under a slate roof. Its short end ("gable end", with the big doorway) faces -Y.
    'engine_house': {
        'x_left': -3.9, 'x_right': 3.9,          # outer walls, so 7.8 m wide across the gable end
        'y_front': 0.0, 'y_back': 11.0,          # front wall face at y = 0, 11 m long
        'wall_height': 4.6,                      # to the eaves (where the roof starts)
        'ridge_height': 7.6,                     # top of the roof
        'roof_overhang': 0.35,
        'plinth_height': 0.5,                    # stone base course
        'door_centre_x': 0.0, 'door_width': 3.4, 'door_height': 4.0,
    },
    # The headframe (steel tower with two big spoked wheels on top) stands just in front of the doorway, straddling the track.
    'headframe': {
        'centre_x': 0.0, 'centre_y': -3.4,
        'base_half_x': 3.1, 'base_half_y': 2.7,  # leg footings at the four corners
        'top_deck_height': 14.6, 'top_half_x': 1.5, 'top_half_y': 1.25,
        'wheel_centre_height': 16.6, 'wheel_radius': 2.4, 'wheel_spacing_x': 1.55,  # two wheels on one axle running along X
    },
    # The tall brick chimney, standing against the back-left of the engine house.
    'chimney': {'centre_x': -6.0, 'centre_y': 7.0, 'base_width': 2.3, 'top_width': 1.25, 'height': 17.0},
    # Track: a curve (cubic Bezier, 4 points in x,y) from inside the doorway, straight out toward the camera, then bending a little to the left so it sweeps across the bottom of the picture.
    'track_bezier': [(0.0, 1.0), (0.0, -9.0), (-2.0, -15.0), (-10.0, -26.0)],
    'track_gauge': 1.1,                          # distance between the two rails' centres
    # Round yard where the ground is flat and muddy; beyond it the ground rises.
    'yard_radius': 30.0,
    # Rough places for the rest (parts may adjust within these areas).
    'village_area': {'x_min': 16.0, 'x_max': 42.0, 'y_min': 6.0, 'y_max': 40.0},
    'hills_distance': 110.0,
}


def smoothstep(low, high, value):
    t = min(max((value - low) / (high - low), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ground_height(x, y):
    """Height of the yard ground in metres. Gently lumpy and flat around the mine; rises into banks at the sides and back.
    Every part uses this so things sit on the ground instead of floating or sinking."""
    lumps = 0.10 * math.sin(x * 0.21 + 0.7) * math.cos(y * 0.17 + 0.3) + 0.05 * math.sin(x * 0.53 + y * 0.41 + 1.1)
    away = math.hypot(x - 4.0, y - 4.0)
    bank = 0.012 * (min(away, 60.0) - 26.0) ** 1.6 + min(0.04 * max(0.0, away - 60.0), 1.5) if away > 26.0 else 0.0   # about 3.4 m at 60 m, never above ~5 m
    flat_near_the_mine = smoothstep(11.0, 24.0, away)      # exactly level around the buildings so they sit cleanly
    return lumps * flat_near_the_mine * smoothstep(70.0, 30.0, away) + bank


def track_point(t):
    """Point (x, y) on the track curve, t from 0 (inside the doorway) to 1 (far right of the picture)."""
    p0, p1, p2, p3 = [Vector(p) for p in LAYOUT['track_bezier']]
    point = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return float(point.x), float(point.y)


def track_direction(t):
    """Unit direction (x, y) of the track at t."""
    p0, p1, p2, p3 = [Vector(p) for p in LAYOUT['track_bezier']]
    d = 3 * (1 - t) ** 2 * (p1 - p0) + 6 * (1 - t) * t * (p2 - p1) + 3 * t ** 2 * (p3 - p2)
    d = d.normalized()
    return float(d.x), float(d.y)


# --------------------------------------------------------------------------------------------------------------------
# Materials made from the uploaded pictures
# --------------------------------------------------------------------------------------------------------------------
SURFACES = {
    # tile = how many metres one picture covers; depth = total height of the relief in metres (peak to peak);
    # splash = height up the wall that is splashed with mud; shine_map / metal_map = use the extra maps made for them
    'brick': {'tile': 1.5, 'depth': 0.030, 'normal_strength': 1.0, 'roughness': 0.85, 'splash': 0.9},
    'slate': {'tile': 2.0, 'depth': 0.040, 'normal_strength': 1.0, 'roughness': 0.55, 'splash': 0.0},
    'wood': {'tile': 1.2, 'depth': 0.030, 'normal_strength': 1.0, 'roughness': 0.80, 'splash': 0.6},
    'metal': {'tile': 2.0, 'depth': 0.016, 'normal_strength': 1.0, 'roughness': 0.6, 'splash': 0.5, 'shine_map': True, 'metal_map': True},
    'mud': {'tile': 5.0, 'depth': 0.06, 'normal_strength': 0.8, 'roughness': 0.9, 'splash': 0.0, 'shine_map': True},
    'gravel': {'tile': 1.4, 'depth': 0.04, 'normal_strength': 0.8, 'roughness': 0.75, 'splash': 0.5},
}
MUD_SPLASH_COLOUR = (0.075, 0.045, 0.028, 1.0)
_material_cache = {}


def _load_image(file_name, is_colour):
    path = os.path.join(TEXTURE_FOLDER, file_name)
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if is_colour else 'Non-Color'
    return image


def _image_node(nodes, image, mapping_output, location):
    node = nodes.new('ShaderNodeTexImage')
    node.image = image
    node.extension = 'REPEAT'
    node.interpolation = 'Linear'
    node.location = location
    return node


def surface_material(surface, tint=(1.0, 1.0, 1.0), true_displacement=False, variation=0.25, tile=None, depth=None,
                     roughness=None, normal_strength=None, splash=None):
    """A material that uses the uploaded picture + normal map (+ height map for real displacement) for one kind of surface.
    surface: 'brick', 'slate', 'wood', 'metal', 'mud' or 'gravel'.
    tint: multiplies the picture's colour (use it to make one object darker or warmer).
    true_displacement: also push the surface in and out using the height map; only the objects given a fine subdivision
    (see use_real_displacement) show it, the rest stay flat.
    variation: how much big slow patches of light and dark break up the repeating tile (0 = none).
    tile: metres per picture (default per surface). depth: relief height in metres. splash: metres of mud splash up the base."""
    spec = SURFACES[surface]
    tile = spec['tile'] if tile is None else tile
    depth = spec['depth'] if depth is None else depth
    roughness = spec['roughness'] if roughness is None else roughness
    normal_strength = spec['normal_strength'] if normal_strength is None else normal_strength
    splash = spec['splash'] if splash is None else splash
    key = (surface, tuple(round(c, 3) for c in tint), true_displacement, round(variation, 3), tile, depth, roughness, normal_strength, splash)
    if key in _material_cache:
        return _material_cache[key]
    name = f"{surface}{'+displaced' if true_displacement else ''} {len(_material_cache)}"
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material['mine_tile_metres'] = float(tile)
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial'); output.location = (1400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1100, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    coords = nodes.new('ShaderNodeTexCoord'); coords.location = (-900, 0)

    colour_image = _image_node(nodes, _load_image(f'{surface}_colour.png', True), None, (-600, 300))
    links.new(coords.outputs['UV'], colour_image.inputs['Vector'])
    colour = colour_image.outputs['Color']

    if tuple(tint) != (1.0, 1.0, 1.0):
        tinted = nodes.new('ShaderNodeMix'); tinted.data_type = 'RGBA'; tinted.blend_type = 'MULTIPLY'; tinted.location = (-300, 300)
        tinted.inputs['Factor'].default_value = 1.0
        tinted.inputs['B'].default_value = (tint[0], tint[1], tint[2], 1.0)
        links.new(colour, tinted.inputs['A'])
        colour = tinted.outputs['Result']

    position = nodes.new('ShaderNodeNewGeometry'); position.location = (-900, -400)
    if variation > 0:
        noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-600, -300)
        noise.inputs['Scale'].default_value = 0.35; noise.inputs['Detail'].default_value = 4.0
        links.new(position.outputs['Position'], noise.inputs['Vector'])
        patches = nodes.new('ShaderNodeMapRange'); patches.location = (-300, -300)
        patches.inputs['To Min'].default_value = 1.0 - variation; patches.inputs['To Max'].default_value = 1.0 + variation * 0.5
        links.new(noise.outputs['Fac'], patches.inputs['Value'])
        varied = nodes.new('ShaderNodeMix'); varied.data_type = 'RGBA'; varied.blend_type = 'MULTIPLY'; varied.location = (0, 300)
        varied.inputs['Factor'].default_value = 1.0
        links.new(colour, varied.inputs['A'])
        links.new(patches.outputs['Result'], varied.inputs['B'])
        colour = varied.outputs['Result']

    if splash > 0:
        split = nodes.new('ShaderNodeSeparateXYZ'); split.location = (-600, -600)
        links.new(position.outputs['Position'], split.inputs['Vector'])
        wetness = nodes.new('ShaderNodeMapRange'); wetness.location = (-300, -600); wetness.clamp = True
        wetness.inputs['From Min'].default_value = 0.0; wetness.inputs['From Max'].default_value = splash
        wetness.inputs['To Min'].default_value = 0.7; wetness.inputs['To Max'].default_value = 0.0
        links.new(split.outputs['Z'], wetness.inputs['Value'])
        splashed = nodes.new('ShaderNodeMix'); splashed.data_type = 'RGBA'; splashed.blend_type = 'MIX'; splashed.location = (300, 300)
        links.new(wetness.outputs['Result'], splashed.inputs['Factor'])
        links.new(colour, splashed.inputs['A'])
        splashed.inputs['B'].default_value = MUD_SPLASH_COLOUR
        colour = splashed.outputs['Result']
    links.new(colour, bsdf.inputs['Base Color'])

    normal_image = _image_node(nodes, _load_image(f'{surface}_normal.png', False), None, (-600, -50))
    links.new(coords.outputs['UV'], normal_image.inputs['Vector'])
    normal_map = nodes.new('ShaderNodeNormalMap'); normal_map.location = (700, -50)
    normal_map.space = 'TANGENT'; normal_map.uv_map = 'UVMap'
    normal_map.inputs['Strength'].default_value = normal_strength * (0.6 if true_displacement else 1.0)
    links.new(normal_image.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])

    if spec.get('shine_map'):
        shine_image = _image_node(nodes, _load_image(f'{surface}_roughness.png', False), None, (-600, -800))
        links.new(coords.outputs['UV'], shine_image.inputs['Vector'])
        links.new(shine_image.outputs['Color'], bsdf.inputs['Roughness'])
    else:
        bsdf.inputs['Roughness'].default_value = roughness
    if spec.get('metal_map'):
        metal_image = _image_node(nodes, _load_image(f'{surface}_metallic.png', False), None, (-600, -1100))
        links.new(coords.outputs['UV'], metal_image.inputs['Vector'])
        links.new(metal_image.outputs['Color'], bsdf.inputs['Metallic'])

    if true_displacement:
        height_image = _image_node(nodes, _load_image(f'{surface}_height.png', False), None, (-600, -1400))
        links.new(coords.outputs['UV'], height_image.inputs['Vector'])
        displacement = nodes.new('ShaderNodeDisplacement'); displacement.location = (1100, -500)
        displacement.inputs['Midlevel'].default_value = 0.5
        displacement.inputs['Scale'].default_value = depth
        links.new(height_image.outputs['Color'], displacement.inputs['Height'])
        links.new(displacement.outputs['Displacement'], output.inputs['Displacement'])
        material.displacement_method = 'DISPLACEMENT'
        material.max_vertex_displacement = depth
    _material_cache[key] = material
    return material


def plain_material(name, colour, roughness=0.7, metallic=0.0, glow=None, glow_strength=0.0):
    """A material with one flat colour. glow: colour that the surface itself gives off (windows, lamps)."""
    key = ('plain', name, tuple(round(c, 3) for c in colour), roughness, metallic, glow, glow_strength)
    if key in _material_cache:
        return _material_cache[key]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (colour[0], colour[1], colour[2], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if glow is not None:
        bsdf.inputs['Emission Color'].default_value = (glow[0], glow[1], glow[2], 1.0)
        bsdf.inputs['Emission Strength'].default_value = glow_strength
    material['mine_tile_metres'] = 1.0
    _material_cache[key] = material
    return material


def glow_material(name, colour, strength):
    """Lit window glass, lamp flame: a colour that shines by itself."""
    return plain_material(name, (0.02, 0.012, 0.006), roughness=0.4, glow=colour, glow_strength=strength)


def use_real_displacement(obj, pixel_size=1.0):
    """Make an object show true bumps from its displacement material: Blender cuts its faces finer and finer up close
    ('adaptive subdivision', about one cut per picture dot). Faces keep their flat shape (simple subdivision)."""
    modifier = obj.modifiers.new('Real displacement', 'SUBSURF')
    modifier.subdivision_type = 'SIMPLE'
    modifier.use_adaptive_subdivision = True
    modifier.adaptive_pixel_size = pixel_size
    modifier.levels = 1
    modifier.render_levels = 1
    return modifier


# --------------------------------------------------------------------------------------------------------------------
# MeshBuilder: many shapes -> one Blender object
# --------------------------------------------------------------------------------------------------------------------
_icosphere_cache = {}


def _icosphere_template(subdivisions):
    if subdivisions not in _icosphere_cache:
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
        index = {v: i for i, v in enumerate(bm.verts)}
        vertices = np.array([tuple(v.co) for v in bm.verts])
        faces = np.array([[index[v] for v in f.verts] for f in bm.faces])
        bm.free()
        _icosphere_cache[subdivisions] = (vertices, faces)
    return _icosphere_cache[subdivisions]


def rotation_from_yaw(yaw_radians):
    c, s = math.cos(yaw_radians), math.sin(yaw_radians)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def basis_from_direction(direction, up_hint=(0.0, 0.0, 1.0)):
    """Three perpendicular unit vectors (forward = direction, side, up) as the columns of a 3x3 matrix."""
    forward = np.array(direction, dtype=float)
    forward /= np.linalg.norm(forward)
    up = np.array(up_hint, dtype=float)
    side = np.cross(up, forward)
    if np.linalg.norm(side) < 1e-6:
        side = np.cross(np.array([0.0, 1.0, 0.0]), forward)
    side /= np.linalg.norm(side)
    true_up = np.cross(forward, side)
    return np.stack([forward, side, true_up], axis=1)


class MeshBuilder:
    """Collects shapes and turns them into a single Blender object.
    materials: list of Blender materials (the 'slot' number you pass to add_* picks one of them).
    Every shape gets its own corners (flat look) except cylinders / spheres, whose sides are shaded smooth.
    Picture coordinates: walls get bricks level, slopes get courses level across the slope, flat tops use X and Y;
    pass uv_axes=(u_direction, v_direction) to override for a face."""

    def __init__(self, name, materials):
        self.name = name
        self.materials = list(materials)
        self._vertex_blocks = []
        self._vertex_total = 0
        self._faces = []  # (vertex_indices, slot, smooth, uv_axes, uv_shift, explicit_uv)

    # ---- raw faces ----
    def add_polygon(self, points, slot=0, smooth=False, uv_axes=None, uv_shift=(0.0, 0.0), uv_metres=None):
        """One flat face. points: 3 or more (x, y, z), counter-clockwise seen from OUTSIDE (so the front faces outward)."""
        points = np.asarray(points, dtype=float).reshape(-1, 3)
        start = self._vertex_total
        self._vertex_blocks.append(points)
        self._vertex_total += len(points)
        self._faces.append((np.arange(start, start + len(points)), slot, smooth, uv_axes, uv_shift, uv_metres))

    def add_indexed_faces(self, vertices, faces, slot=0, smooth=False, uv_axes=None, uv_shift=(0.0, 0.0)):
        """Many faces over a shared list of vertices. faces: list of index lists (3 or 4 each)."""
        vertices = np.asarray(vertices, dtype=float).reshape(-1, 3)
        start = self._vertex_total
        self._vertex_blocks.append(vertices)
        self._vertex_total += len(vertices)
        for face in faces:
            self._faces.append((np.asarray(face) + start, slot, smooth, uv_axes, uv_shift, None))

    # ---- shapes ----
    def add_box(self, centre, size, slot=0, yaw=0.0, rotation=None, slots=None, uv_axes=None, uv_shift=(0.0, 0.0), skip=()):
        """A box. size = (x, y, z) lengths before rotating. rotation: 3x3 matrix (overrides yaw).
        slots: optional dict {'top','bottom','left','right','front','back'} -> slot, where front is -Y, back +Y, left -X, right +X (before rotating).
        skip: names of faces not to build (e.g. ('bottom',))."""
        sx, sy, sz = [s / 2.0 for s in size]
        rot = np.asarray(rotation) if rotation is not None else rotation_from_yaw(yaw)
        centre = np.asarray(centre, dtype=float)
        corners = np.array([[x, y, z] for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)])
        world = corners @ rot.T + centre  # index = x_bit + 2*y_bit + 4*z_bit
        faces = {
            'bottom': (0, 2, 3, 1), 'top': (4, 5, 7, 6), 'front': (0, 1, 5, 4), 'back': (2, 6, 7, 3), 'left': (0, 4, 6, 2), 'right': (1, 3, 7, 5),
        }
        for face_name, ids in faces.items():
            if face_name in skip:
                continue
            face_slot = slots.get(face_name, slot) if slots else slot
            self.add_polygon(world[list(ids)], slot=face_slot, uv_axes=uv_axes, uv_shift=uv_shift)

    def add_beam(self, start, end, width, depth, slot=0, up_hint=(0.0, 0.0, 1.0), extend=0.0, uv_shift=(0.0, 0.0)):
        """A straight rectangular bar from start to end. width is measured sideways, depth along the 'up' direction."""
        start = np.asarray(start, dtype=float)
        end = np.asarray(end, dtype=float)
        direction = end - start
        length = np.linalg.norm(direction)
        basis = basis_from_direction(direction, up_hint)
        centre = (start + end) / 2.0
        self.add_box(centre, (length + 2 * extend, width, depth), slot=slot, rotation=basis, uv_shift=uv_shift)

    def add_cylinder(self, start, end, radius, sides=12, slot=0, radius_end=None, caps=True, smooth=True, uv_shift=(0.0, 0.0)):
        """A round bar or tapered post from start to end. radius_end makes it a cone-like taper."""
        start = np.asarray(start, dtype=float)
        end = np.asarray(end, dtype=float)
        radius_end = radius if radius_end is None else radius_end
        basis = basis_from_direction(end - start)
        side, up = basis[:, 1], basis[:, 2]
        angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
        ring = np.outer(np.cos(angles), side) + np.outer(np.sin(angles), up)
        bottom_ring = start + ring * radius
        top_ring = end + ring * radius_end
        length = np.linalg.norm(end - start)
        for i in range(sides):
            j = (i + 1) % sides
            around_i, around_j = angles[i] * radius, (angles[i] + 2 * np.pi / sides) * radius
            self.add_polygon([bottom_ring[i], bottom_ring[j], top_ring[j], top_ring[i]], slot=slot, smooth=smooth,
                             uv_metres=[(around_i, 0.0), (around_j, 0.0), (around_j, length), (around_i, length)])
        if caps:
            if radius > 1e-6:
                self.add_polygon(bottom_ring[::-1], slot=slot, uv_axes=(basis[:, 1], basis[:, 2]), uv_shift=uv_shift)
            if radius_end > 1e-6:
                self.add_polygon(top_ring, slot=slot, uv_axes=(basis[:, 1], basis[:, 2]), uv_shift=uv_shift)

    def add_ring(self, centre, axis, outer_radius, inner_radius, thickness, sides=32, slot=0, smooth=True):
        """A flat ring (like a wheel rim or washer) lying across 'axis', thickness measured along the axis."""
        centre = np.asarray(centre, dtype=float)
        basis = basis_from_direction(axis)
        along, side, up = basis[:, 0], basis[:, 1], basis[:, 2]
        angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
        unit = np.outer(np.cos(angles), side) + np.outer(np.sin(angles), up)
        half = along * thickness / 2.0
        outer_a, outer_b = centre - half + unit * outer_radius, centre + half + unit * outer_radius
        inner_a, inner_b = centre - half + unit * inner_radius, centre + half + unit * inner_radius
        for i in range(sides):
            j = (i + 1) % sides
            around_i, around_j = angles[i] * outer_radius, (angles[i] + 2 * np.pi / sides) * outer_radius
            self.add_polygon([outer_a[i], outer_a[j], outer_b[j], outer_b[i]], slot=slot, smooth=smooth,
                             uv_metres=[(around_i, 0), (around_j, 0), (around_j, thickness), (around_i, thickness)])
            self.add_polygon([inner_b[i], inner_b[j], inner_a[j], inner_a[i]], slot=slot, smooth=smooth,
                             uv_metres=[(around_i, 0), (around_j, 0), (around_j, thickness), (around_i, thickness)])
            self.add_polygon([outer_b[i], outer_b[j], inner_b[j], inner_b[i]], slot=slot, uv_axes=(side, up))
            self.add_polygon([inner_a[i], inner_a[j], outer_a[j], outer_a[i]], slot=slot, uv_axes=(side, up))

    def add_blob(self, centre, radii, slot=0, subdivisions=1, rotation=None, jitter=0.0, seed=0, smooth=False):
        """A rounded lump (stretched sphere). jitter > 0 makes it a rough rock or a coal lump (0.2 = very rough)."""
        template_vertices, template_faces = _icosphere_template(subdivisions)
        vertices = template_vertices.copy()
        if jitter > 0:
            generator = np.random.default_rng(seed)
            vertices = vertices * (1.0 + generator.uniform(-jitter, jitter, (len(vertices), 1)))
        vertices = vertices * np.asarray(radii, dtype=float)
        if rotation is not None:
            vertices = vertices @ np.asarray(rotation).T
        vertices = vertices + np.asarray(centre, dtype=float)
        self.add_indexed_faces(vertices, template_faces.tolist(), slot=slot, smooth=smooth)

    # ---- finishing ----
    def finish(self, collection_name='Mine', smooth_by_angle=None):
        """Create the Blender object (all points already in world coordinates, object sits at the origin)."""
        vertices = np.concatenate(self._vertex_blocks).astype(np.float64)
        face_count = len(self._faces)
        sizes = np.array([len(f[0]) for f in self._faces])
        loop_vertex = np.concatenate([f[0] for f in self._faces])
        starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
        mesh = bpy.data.meshes.new(self.name)
        mesh.vertices.add(len(vertices))
        mesh.vertices.foreach_set('co', vertices.ravel())
        mesh.loops.add(len(loop_vertex))
        mesh.loops.foreach_set('vertex_index', loop_vertex)
        mesh.polygons.add(face_count)
        mesh.polygons.foreach_set('loop_start', starts)
        mesh.polygons.foreach_set('use_smooth', np.array([f[2] for f in self._faces], dtype=bool))
        mesh.polygons.foreach_set('material_index', np.array([f[1] for f in self._faces], dtype=np.int32))
        mesh.update(calc_edges=True)
        for material in self.materials:
            mesh.materials.append(material)
        self._write_uvs(mesh, vertices, loop_vertex, starts, sizes)
        obj = bpy.data.objects.new(self.name, mesh)
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        collection.objects.link(obj)
        return obj

    def _write_uvs(self, mesh, vertices, loop_vertex, starts, sizes):
        face_count = len(self._faces)
        loop_count = len(loop_vertex)
        loop_points = vertices[loop_vertex]
        face_of_loop = np.repeat(np.arange(face_count), sizes)
        # face normals (Newell's method, vectorised with cumulative sums)
        next_loop = np.arange(loop_count) + 1
        last_loops = starts + sizes - 1
        next_loop[last_loops] = starts
        current, following = loop_points, loop_points[next_loop]
        normal_parts = np.stack([
            (current[:, 1] - following[:, 1]) * (current[:, 2] + following[:, 2]),
            (current[:, 2] - following[:, 2]) * (current[:, 0] + following[:, 0]),
            (current[:, 0] - following[:, 0]) * (current[:, 1] + following[:, 1])], axis=1)
        normals = np.zeros((face_count, 3))
        np.add.at(normals, face_of_loop, normal_parts)
        length = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.maximum(length, 1e-12)
        up = np.array([0.0, 0.0, 1.0])
        slope = normals @ up
        flat_top = np.abs(slope) > 0.95
        steepest = up - slope[:, None] * normals
        steepest /= np.maximum(np.linalg.norm(steepest, axis=1, keepdims=True), 1e-12)
        sideways = np.cross(steepest, normals)
        u_axis = np.where(flat_top[:, None], np.array([1.0, 0.0, 0.0]), sideways)
        v_axis = np.where(flat_top[:, None], np.array([0.0, 1.0, 0.0]), steepest)
        shifts = np.zeros((face_count, 2))
        slots = np.zeros(face_count, dtype=int)
        explicit = {}
        for index, face in enumerate(self._faces):
            slots[index] = face[1]
            shifts[index] = face[4]
            if face[3] is not None:
                u_axis[index], v_axis[index] = np.asarray(face[3][0], dtype=float), np.asarray(face[3][1], dtype=float)
            if face[5] is not None:
                explicit[index] = face[5]
        tiles = np.array([float(m.get('mine_tile_metres', 1.0)) if m else 1.0 for m in self.materials])
        tile_per_face = tiles[np.minimum(slots, len(tiles) - 1)]
        u = np.einsum('ij,ij->i', loop_points, u_axis[face_of_loop]) / tile_per_face[face_of_loop] + shifts[face_of_loop, 0]
        v = np.einsum('ij,ij->i', loop_points, v_axis[face_of_loop]) / tile_per_face[face_of_loop] + shifts[face_of_loop, 1]
        for index, uv_metres in explicit.items():
            a = starts[index]
            for k, (um, vm) in enumerate(uv_metres):
                u[a + k] = um / tile_per_face[index] + shifts[index, 0]
                v[a + k] = vm / tile_per_face[index] + shifts[index, 1]
        layer = mesh.uv_layers.new(name='UVMap')
        layer.data.foreach_set('uv', np.stack([u, v], axis=1).ravel())


# --------------------------------------------------------------------------------------------------------------------
# Lights, camera and quick one-part previews
# --------------------------------------------------------------------------------------------------------------------
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _material_cache.clear()
    _icosphere_cache.clear()


def make_camera(location, target, lens=35.0, name='Camera', sensor_width=36.0, shift_y=0.0, aperture=None, focus=None):
    camera_data = bpy.data.cameras.new(name)
    camera_data.lens = lens
    camera_data.sensor_width = sensor_width
    camera_data.shift_y = shift_y
    if aperture:
        camera_data.dof.use_dof = True
        camera_data.dof.aperture_fstop = aperture
        camera_data.dof.focus_distance = focus or (Vector(target) - Vector(location)).length
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = Vector(location)
    camera.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = camera
    return camera


def set_sun(elevation_degrees, azimuth_degrees, strength=3.0, colour=(1.0, 0.82, 0.62), name='Sun', angle_degrees=1.5):
    """A sun light. azimuth 0 = shining toward +Y (north on our map), 90 = toward -X... use look_from for clarity."""
    sun_data = bpy.data.lights.new(name, 'SUN')
    sun_data.energy = strength
    sun_data.color = colour
    sun_data.angle = math.radians(angle_degrees)
    sun = bpy.data.objects.new(name, sun_data)
    bpy.context.scene.collection.objects.link(sun)
    direction = Vector((math.sin(math.radians(azimuth_degrees)) * math.cos(math.radians(elevation_degrees)),
                        math.cos(math.radians(azimuth_degrees)) * math.cos(math.radians(elevation_degrees)),
                        -math.sin(math.radians(elevation_degrees))))
    sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return sun


def set_flat_world(colour=(0.55, 0.62, 0.72), strength=1.0):
    world = bpy.data.worlds.new('Preview world') if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (colour[0], colour[1], colour[2], 1.0)
    background.inputs['Strength'].default_value = strength


def preview_stage(ground_colour=(0.16, 0.11, 0.08), ground_size=60.0):
    """Neutral lighting + a plain muddy-coloured floor, so one part can be judged on its own."""
    set_flat_world((0.55, 0.62, 0.72), 0.9)
    set_sun(32, 215, strength=3.2, colour=(1.0, 0.86, 0.68))
    floor_mesh = bpy.data.meshes.new('Preview floor')
    half = ground_size / 2.0
    floor_mesh.from_pydata([(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new('Preview floor', floor_mesh)
    bpy.context.scene.collection.objects.link(floor)
    floor_mesh.materials.append(plain_material('Preview floor', ground_colour, roughness=0.9))
    return floor


def render_preview(path, camera_location, camera_target, lens=35.0, size=(900, 900), samples=32):
    """Take a quick photo (Cycles, a few samples, denoised) of whatever is in the scene."""
    scene = bpy.context.scene
    make_camera(camera_location, camera_target, lens=lens, name='Preview camera')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.render.filepath = path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    return path


def say(message):
    print(f'[mine] {message}', flush=True)
