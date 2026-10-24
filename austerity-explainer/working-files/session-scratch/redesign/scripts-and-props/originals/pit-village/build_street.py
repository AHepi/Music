# What this does: builds the pit village street set for chapter 3 (a British coalfield village in
# 1926, the miners' lockout, at dusk) in Blender by script, and writes:
#   assets/models/pit-village/street.blend   (the set, with lights and both cameras, for plate renders)
#   assets/models/pit-village/street.glb     (the same set for the three.js stage; textures inside)
#   assets/models/pit-village/camera.json    (the main camera in Blender space and in three.js space)
# and, when asked, preview renders of the main view and of a view 2 m to the side.
#
# The set: a cobbled street of granite setts, 5 m wide, running away from the camera (Blender +y)
# and up a 4 degree slope, with a dished gutter channel, jointed stone kerbs and narrow flagstone
# pavements. Two terraces of two-storey miners' cottages on each side (8 cottages, a back lane, then
# 6 more), red brick on the left and rubble sandstone on the right, stepping up the slope: slate
# roofs with clay ridges, chimney stacks with oversailing courses and clay pots, four-panel front
# doors with fanlights, brass furniture and stone steps, six-over-six sash windows with stone sills
# and lintels, lace curtains (some lit warm from inside), fascia boards, cast-iron gutters and
# downpipes. Gas lamps on cast-iron posts along the kerbs. At the top of the street (about 80 m
# away) the colliery: a 20 m steel lattice headframe with two spoked winding wheels side by side
# (separate objects winding_wheel_left / winding_wheel_right, origin on the axle; they turn about
# Blender y, which is three.js -z, so wheel.rotation.z in three.js), the heapstead under it, a
# brick engine house with tall round-headed windows, a tall round brick chimney, a black spoil heap
# behind and dark moorland hills, all under a dusk sky dome.
#
# Space is left clear for props: the pavements and the street surface carry nothing but lamps.
#
# Units are metres. Blender is z-up; the .glb is written y-up (three.js), so a Blender point
# (x, y, z) is (x, z, -y) in three.js.
#
# Run (needs the textures first, see fetch_street_textures.py beside this file):
#   DISPLAY=:92 blender -b --python build_street.py -- [--preview FOLDER] [--samples N]
# With --preview FOLDER it also renders preview.png (main camera) and preview_side.png (2 m to the
# right) at 540 x 960 with EEVEE (needs a virtual screen: Xvfb :92 -screen 0 1920x1080x24 &).

import json
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

# ------------------------------------------------------------------------------------ settings

KIT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))   # the kit's top folder
OUTPUT_FOLDER = os.path.join(KIT_FOLDER, 'assets/models/pit-village')
TEXTURE_FOLDER = os.path.join(OUTPUT_FOLDER, 'textures')
BLEND_PATH = os.path.join(OUTPUT_FOLDER, 'street.blend')
GLB_PATH = os.path.join(OUTPUT_FOLDER, 'street.glb')
CAMERA_JSON_PATH = os.path.join(OUTPUT_FOLDER, 'camera.json')

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW_FOLDER = arguments[arguments.index('--preview') + 1] if '--preview' in arguments else None
PREVIEW_SAMPLES = int(arguments[arguments.index('--samples') + 1]) if '--samples' in arguments else 16

SLOPE = math.radians(4.0)
RISE_PER_METRE = math.tan(SLOPE)
STREET_HALF_WIDTH = 2.5           # kerb face to kerb face is 5 m
CHANNEL_WIDTH = 0.3               # the dished gutter channel along each kerb
KERB_WIDTH = 0.18
KERB_HEIGHT = 0.13                # kerb top above the channel
HOUSE_FRONT_X = 4.15              # the cottage fronts (pavement is about 1.3 m wide)
STREET_END_Y = 72.0               # where the setts stop and the colliery yard begins
PLATEAU_Y = 76.0                  # the colliery stands on level ground from here
COTTAGE_WIDTH = 4.5
COTTAGE_DEPTH = 7.0
EAVES_HEIGHT = 6.0
ROOF_PITCH = math.radians(35)
RIDGE_HEIGHT = EAVES_HEIGHT + COTTAGE_DEPTH / 2 * math.tan(ROOF_PITCH)

CAMERA_Y = 3.0
CAMERA_EYE_HEIGHT = 1.6
CAMERA_VERTICAL_FOV = 40.0
CAMERA_PITCH_UP = 6.5             # degrees above level, so the headframe sits in the upper middle
CAMERA_NEAR, CAMERA_FAR = 0.1, 1500.0
FRAME_WIDTH, FRAME_HEIGHT = 1080, 1920


def ground_height(y):
    """Height of the street's channel line (and of the ground) at distance y up the street."""
    return min(max(y, -30.0), PLATEAU_Y) * RISE_PER_METRE


def road_height(x, y):
    """The cobbled carriageway: cambered 8 cm higher in the middle than at the channels."""
    inner = STREET_HALF_WIDTH - CHANNEL_WIDTH
    camber = 0.08 * max(0.0, 1 - (x / inner) ** 2)
    return ground_height(y) + camber


def pavement_height(y):
    return ground_height(y) + KERB_HEIGHT


random = np.random.default_rng(1926)

# ------------------------------------------------------------------------------------ scene reset

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0      # no street.blend1 backup copies
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

collections = {}


def collection(name):
    if name not in collections:
        new = bpy.data.collections.new(name)
        scene.collection.children.link(new)
        collections[name] = new
    return collections[name]


# ------------------------------------------------------------------------------------ materials

materials = {}
images = {}


def load_image(file_name, colour_data=True):
    key = (file_name, colour_data)
    if key not in images:
        image = bpy.data.images.load(os.path.join(TEXTURE_FOLDER, file_name))
        image.colorspace_settings.name = 'sRGB' if colour_data else 'Non-Color'
        images[key] = image
    return images[key]


def textured_material(name, texture, tile_metres, tint=(1, 1, 1), roughness=0.85, metallic=0.0,
                      normal_strength=1.0):
    """A material wearing a Poly Haven texture. tile_metres: how many metres one copy of the
    picture covers (Poly Haven's measured size), used when giving parts texture coordinates.
    tint multiplies the colour (exported to glTF as baseColorFactor)."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    colour = nodes.new('ShaderNodeTexImage')
    colour.image = load_image(f'{texture}_colour.jpg')
    colour.location = (-700, 300)
    multiply = nodes.new('ShaderNodeMix')
    multiply.data_type = 'RGBA'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs['Factor'].default_value = 1.0
    multiply.inputs[7].default_value = (*tint, 1)
    multiply.location = (-350, 300)
    links.new(colour.outputs['Color'], multiply.inputs[6])
    links.new(multiply.outputs[2], shader.inputs['Base Color'])
    normal_picture = nodes.new('ShaderNodeTexImage')
    normal_picture.image = load_image(f'{texture}_normal.jpg', colour_data=False)
    normal_picture.location = (-700, -100)
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.inputs['Strength'].default_value = normal_strength
    normal_map.location = (-350, -100)
    links.new(normal_picture.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    material['tile_metres'] = tile_metres
    materials[name] = material
    return material


def picture_material(name, picture, glow_strength=0.0, roughness=0.15, colour_scale=1.0):
    """A material whose picture is laid once over a part (window views, lamp glass, the sky).
    With glow_strength the picture also glows (lit windows, lamps, the sky)."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = roughness
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = load_image(picture)
    texture.location = (-500, 200)
    if colour_scale != 1.0:
        multiply = nodes.new('ShaderNodeMix')
        multiply.data_type = 'RGBA'
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs['Factor'].default_value = 1.0
        multiply.inputs[7].default_value = (colour_scale, colour_scale, colour_scale, 1)
        links.new(texture.outputs['Color'], multiply.inputs[6])
        links.new(multiply.outputs[2], shader.inputs['Base Color'])
    else:
        links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    if glow_strength:
        links.new(texture.outputs['Color'], shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value = glow_strength
    material['tile_metres'] = 0.0      # 0 = the part's own coordinates cover the picture once
    materials[name] = material
    return material


def make_materials():
    # walls
    textured_material('cottage_brick', 'red_brick', 1.4, tint=(0.62, 0.5, 0.46))
    textured_material('cottage_stone', 'stone_brick_wall_001', 2.5, tint=(0.72, 0.68, 0.6))
    textured_material('colliery_brick', 'castle_brick_02_red', 1.5, tint=(0.72, 0.6, 0.55))
    textured_material('dressed_stone', 'rock_surface', 2.0, tint=(0.86, 0.8, 0.7), roughness=0.9)
    textured_material('dark_dressed_stone', 'rock_surface', 2.0, tint=(0.55, 0.52, 0.48), roughness=0.9)
    # street
    textured_material('street_setts', 'square_cobblestone', 2.0, tint=(0.62, 0.62, 0.64), roughness=0.75, normal_strength=1.4)
    textured_material('channel_stones', 'large_sandstone_blocks', 1.5, tint=(0.6, 0.6, 0.6), roughness=0.7)
    textured_material('kerb_stone', 'large_sandstone_blocks', 3.0, tint=(0.78, 0.76, 0.72), roughness=0.85)
    textured_material('pavement_flags', 'large_grey_tiles', 3.0, tint=(0.72, 0.7, 0.66), roughness=0.85)
    # roofs
    textured_material('roof_slate', 'roof_slates_03', 3.0, tint=(0.42, 0.45, 0.52), roughness=0.5, normal_strength=1.2)
    textured_material('ridge_clay', 'grey_plaster_02', 1.0, tint=(0.5, 0.3, 0.24), roughness=0.8)
    textured_material('chimney_pot_clay', 'grey_plaster_02', 0.8, tint=(0.78, 0.44, 0.3), roughness=0.85)
    textured_material('chimney_pot_sooted', 'grey_plaster_02', 0.8, tint=(0.42, 0.28, 0.22), roughness=0.9)
    # paint over timber
    for paint_name, colour in (('paint_bottle_green', (0.18, 0.3, 0.22)), ('paint_maroon', (0.36, 0.13, 0.12)),
                               ('paint_navy', (0.14, 0.18, 0.3)), ('paint_brown', (0.3, 0.2, 0.13)),
                               ('paint_cream', (0.8, 0.76, 0.64)), ('paint_black', (0.07, 0.07, 0.07))):
        textured_material(paint_name, 'grey_plaster_02', 1.0, tint=colour, roughness=0.45, normal_strength=0.4)
    textured_material('boarded_green', 'green_rough_planks', 1.5, tint=(0.75, 0.8, 0.75), roughness=0.7)
    textured_material('boarded_blue', 'blue_painted_planks', 1.0, tint=(0.7, 0.75, 0.8), roughness=0.7)
    textured_material('fascia_board', 'distressed_painted_planks', 1.6, tint=(0.4, 0.38, 0.35), roughness=0.7)
    # metals
    textured_material('cast_iron', 'rusty_metal_02', 1.0, tint=(0.16, 0.16, 0.16), roughness=0.55, metallic=0.6)
    textured_material('headframe_steel', 'rusty_metal_02', 1.0, tint=(0.24, 0.21, 0.19), roughness=0.6, metallic=0.5)
    textured_material('wheel_iron', 'rusty_metal_02', 0.6, tint=(0.2, 0.18, 0.17), roughness=0.5, metallic=0.6)
    textured_material('brass', 'rusty_metal_02', 0.5, tint=(0.85, 0.62, 0.3), roughness=0.3, metallic=0.9, normal_strength=0.3)
    textured_material('wire_rope', 'rusty_metal_02', 0.3, tint=(0.12, 0.12, 0.12), roughness=0.4, metallic=0.7)
    # ground
    textured_material('colliery_yard', 'muddy_tracks', 2.25, tint=(0.38, 0.34, 0.31), roughness=0.8)
    textured_material('spoil_heap', 'rocks_ground_02', 2.0, tint=(0.16, 0.15, 0.15), roughness=0.75)
    textured_material('moor', 'muddy_tracks', 12.0, tint=(0.16, 0.18, 0.15), roughness=0.95)
    textured_material('plaster_dark', 'grey_plaster_02', 1.0, tint=(0.22, 0.2, 0.18), roughness=0.9)
    # pictures laid once over a part
    for index in range(3):
        picture_material(f'window_lit_glow_{index}', f'window_lit_{index}.jpg', glow_strength=4.0, roughness=0.1)
        picture_material(f'window_dark_{index}', f'window_dark_{index}.jpg', roughness=0.08)
    picture_material('lamp_glass_glow', 'lamp_glass.jpg', glow_strength=8.0, roughness=0.1)
    picture_material('sky_dome_glow', 'dusk_sky.jpg', glow_strength=1.0, roughness=1.0, colour_scale=0.0)
    # inside of open doorways and the shaft: deep warm-dark plaster
    textured_material('interior_dark', 'grey_plaster_02', 1.0, tint=(0.07, 0.06, 0.05), roughness=1.0)
    # engine house windows, lit
    picture_material('engine_window_glow', 'window_lit_2.jpg', glow_strength=1.6, roughness=0.1)


# ------------------------------------------------------------------------------------ mesh building

class MeshBuilder:
    """Collects boxes, lofts, lathed shapes and quads into one mesh with several materials, so a
    whole part (a window, a door, a lamp) becomes one object. Texture coordinates are given per
    face at the end: real-size box projection for textured materials, or explicit coordinates."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv_layer = self.bm.loops.layers.uv.new('UVMap')
        self.material_names = []
        self.explicit_uv_faces = set()

    def material_index(self, material_name):
        if material_name not in self.material_names:
            self.material_names.append(material_name)
        return self.material_names.index(material_name)

    def _faces_from(self, faces, material_name):
        index = self.material_index(material_name)
        for face in faces:
            face.material_index = index
        return faces

    def box(self, minimum, maximum, material_name, matrix=None):
        """An axis-aligned box from corner `minimum` to corner `maximum` (then moved by matrix)."""
        (x0, y0, z0), (x1, y1, z1) = minimum, maximum
        corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if matrix is not None:
            corners = [tuple(matrix @ Vector(c)) for c in corners]
        verts = [self.bm.verts.new(c) for c in corners]
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        faces = [self.bm.faces.new([verts[i] for i in quad]) for quad in quads]
        return self._faces_from(faces, material_name)

    def centred_box(self, centre, size, material_name, matrix=None):
        half = Vector(size) / 2
        return self.box(tuple(Vector(centre) - half), tuple(Vector(centre) + half), material_name, matrix)

    def beam(self, start, end, width, depth, material_name, up=(0, 0, 1)):
        """A straight member of rectangular section from point start to point end (girders,
        braces, spokes, bars)."""
        start, end = Vector(start), Vector(end)
        direction = end - start
        length = direction.length
        axis = direction.normalized()
        up = Vector(up)
        if abs(axis.dot(up)) > 0.95:
            up = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
        side = axis.cross(up).normalized()
        real_up = side.cross(axis).normalized()
        rotation = Matrix((side, real_up, axis)).transposed().to_4x4()
        matrix = Matrix.Translation(start) @ rotation
        return self.box((-width / 2, -depth / 2, 0), (width / 2, depth / 2, length), material_name, matrix)

    def rod(self, start, end, radius, material_name, sides=8, end_radius=None):
        """A round bar or pipe from start to end (ropes, pipes, axles, lamp posts)."""
        start, end = Vector(start), Vector(end)
        axis = (end - start).normalized()
        helper = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
        side = axis.cross(helper).normalized()
        other = axis.cross(side).normalized()
        end_radius = radius if end_radius is None else end_radius
        rings = []
        for point, r in ((start, radius), (end, end_radius)):
            ring = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides
                ring.append(self.bm.verts.new(point + (side * math.cos(angle) + other * math.sin(angle)) * r))
            rings.append(ring)
        faces = []
        for i in range(sides):
            j = (i + 1) % sides
            faces.append(self.bm.faces.new([rings[0][i], rings[0][j], rings[1][j], rings[1][i]]))
        faces.append(self.bm.faces.new(list(reversed(rings[0]))))
        faces.append(self.bm.faces.new(rings[1]))
        for face in faces[:sides]:
            face.smooth = True
        return self._faces_from(faces, material_name)

    def lathe(self, profile, material_name, sides=12, centre=(0, 0, 0), axis='z', smooth=True):
        """A turned shape: profile [(radius, height), ...] from bottom to top spun round an axis
        through centre ('z' upright; 'y' for wheels lying in the x-z plane)."""
        centre = Vector(centre)
        rings = []
        for radius, height in profile:
            ring = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides
                a, b = math.cos(angle) * radius, math.sin(angle) * radius
                if axis == 'z':
                    offset = Vector((a, b, height))
                else:   # axis y: the shape lies in the x-z plane, height runs along y
                    offset = Vector((a, height, b))
                ring.append(self.bm.verts.new(centre + offset))
            rings.append(ring)
        faces = []
        for k in range(len(rings) - 1):
            for i in range(sides):
                j = (i + 1) % sides
                if axis == 'z':
                    quad = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
                else:
                    quad = [rings[k][i], rings[k + 1][i], rings[k + 1][j], rings[k][j]]
                face = self.bm.faces.new(quad)
                face.smooth = smooth
                faces.append(face)
        if profile[0][0] > 0.0001:
            faces.append(self.bm.faces.new(list(reversed(rings[0])) if axis == 'z' else rings[0]))
        if profile[-1][0] > 0.0001:
            faces.append(self.bm.faces.new(rings[-1] if axis == 'z' else list(reversed(rings[-1]))))
        return self._faces_from(faces, material_name)

    def quad(self, corners, material_name, uvs=None):
        """One flat four-cornered face; uvs: explicit picture coordinates for its corners."""
        verts = [self.bm.verts.new(c) for c in corners]
        face = self.bm.faces.new(verts)
        if uvs is not None:
            for loop, uv in zip(face.loops, uvs):
                loop[self.uv_layer].uv = uv
            self.explicit_uv_faces.add(face)
        return self._faces_from([face], material_name)

    def prism(self, outline, a0, a1, material_name, axis='y'):
        """A flat outline pushed from a0 to a1 along an axis. axis 'y': outline in (x, z), like a
        gable seen from the front; 'x': outline in (y, z); 'z': outline in (x, y)."""
        def point(u, v, a):
            if axis == 'y':
                return (u, a, v)
            if axis == 'x':
                return (a, u, v)
            return (u, v, a)
        near = [self.bm.verts.new(point(u, v, a0)) for u, v in outline]
        far = [self.bm.verts.new(point(u, v, a1)) for u, v in outline]
        faces = [self.bm.faces.new(near), self.bm.faces.new(list(reversed(far)))]
        count = len(outline)
        for i in range(count):
            j = (i + 1) % count
            faces.append(self.bm.faces.new([near[i], near[j], far[j], far[i]]))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return self._faces_from(faces, material_name)

    def finish(self, name, collection_name, location=(0, 0, 0), rotation_z=0.0, bevel=0.0,
               uv_offset=(0.0, 0.0, 0.0), world_uv=False):
        """Make the object. bevel: soft edge width (applied, with hardened normals). world_uv:
        texture coordinates from world position (so long parts that are placed with no rotation
        line up across joints); otherwise from the part's own coordinates plus uv_offset."""
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=0.0001)
        offset = Vector(uv_offset) + (Vector(location) if world_uv else Vector())
        for face in self.bm.faces:
            if face in self.explicit_uv_faces:
                continue
            material = materials[self.material_names[face.material_index]]
            tile = material.get('tile_metres', 1.0) or 1.0
            normal = face.normal
            ax, ay, az = abs(normal.x), abs(normal.y), abs(normal.z)
            for loop in face.loops:
                co = loop.vert.co + offset
                if az >= ax and az >= ay:
                    u, v = co.x, co.y
                elif ax >= ay:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z
                loop[self.uv_layer].uv = (u / tile, v / tile)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for material_name in self.material_names:
            mesh.materials.append(materials[material_name])
        part = bpy.data.objects.new(name, mesh)
        part.location = location
        part.rotation_euler = (0, 0, rotation_z)
        collection(collection_name).objects.link(part)
        if bevel:
            soften(part, bevel)
        return part


def soften(part, width, angle=40):
    """Soft edges that catch the light: a bevel with hardened normals, applied."""
    modifier = part.modifiers.new('bevel', 'BEVEL')
    modifier.width = width
    modifier.segments = 1
    modifier.limit_method = 'ANGLE'
    modifier.angle_limit = math.radians(angle)
    modifier.use_clamp_overlap = True
    modifier.harden_normals = True
    for polygon in part.data.polygons:
        polygon.use_smooth = True
    apply_all_modifiers(part)


def apply_all_modifiers(part):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = part
    part.select_set(True)
    for modifier in list(part.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def cut_openings(part, cutter_boxes):
    """Cut openings (windows, doors) out of a wall: cutter_boxes is a list of (min, max)."""
    builder = MeshBuilder()
    for minimum, maximum in cutter_boxes:
        builder.box(minimum, maximum, 'interior_dark')
    cutter = builder.finish(part.name + '_cutter', 'cutters')
    cutter.location = part.location
    cutter.rotation_euler = part.rotation_euler
    modifier = part.modifiers.new('openings', 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = cutter
    modifier.solver = 'EXACT'
    apply_all_modifiers(part)
    bpy.data.objects.remove(cutter, do_unlink=True)


def remap_uv(part, mode='box'):
    """Re-give texture coordinates after a boolean cut (box projection in the part's space)."""
    mesh = part.data
    layer = mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap')
    for polygon in mesh.polygons:
        material = mesh.materials[polygon.material_index]
        tile = material.get('tile_metres', 1.0) or 1.0
        normal = polygon.normal
        ax, ay, az = abs(normal.x), abs(normal.y), abs(normal.z)
        for loop_index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if az >= ax and az >= ay:
                u, v = co.x, co.y
            elif ax >= ay:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            layer.data[loop_index].uv = (u / tile, v / tile)


def linked_copy(source, name, location, rotation_z, collection_name):
    """Another object sharing the same mesh (the .glb stores the mesh once)."""
    copy = bpy.data.objects.new(name, source.data)
    copy.location = location
    copy.rotation_euler = (0, 0, rotation_z)
    collection(collection_name).objects.link(copy)
    return copy


def marker(name, location, collection_name='markers'):
    """A named empty that the stage can find (smoke tops, lamp heads, doorways)."""
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    empty.empty_display_size = 0.3
    collection(collection_name).objects.link(empty)
    return empty


# ==================================================================================== the street

def build_street():
    """Setts, channels, kerbs and pavements from just behind the camera to the colliery yard."""
    y_start, y_end = -12.0, STREET_END_Y
    inner = STREET_HALF_WIDTH - CHANNEL_WIDTH
    # the cambered carriageway
    builder = MeshBuilder()
    across, along = 16, int(y_end - y_start)
    grid = []
    for j in range(along + 1):
        y = y_start + (y_end - y_start) * j / along
        grid.append([builder.bm.verts.new((-inner + 2 * inner * i / across, y, road_height(-inner + 2 * inner * i / across, y)))
                     for i in range(across + 1)])
    for j in range(along):
        for i in range(across):
            face = builder.bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
            face.material_index = builder.material_index('street_setts')
            face.smooth = True
    builder.finish('street_setts', 'street')
    # channels (dished, granite blocks), kerbs (separate jointed stones) and pavements
    channel = MeshBuilder()
    kerbs = MeshBuilder()
    pavements = MeshBuilder()
    steps = along
    for side in (-1, 1):
        # the channel: a shallow dish 3 cm deep, made as a loft of a 4-point section
        section = [(inner, 0.0), (inner + 0.1, -0.025), (inner + 0.2, -0.025), (STREET_HALF_WIDTH, 0.0)]
        rows = []
        for j in range(steps + 1):
            y = y_start + (y_end - y_start) * j / steps
            rows.append([channel.bm.verts.new((side * sx, y, ground_height(y) + sz)) for sx, sz in section])
        for j in range(steps):
            for i in range(len(section) - 1):
                quad = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
                if side < 0:
                    quad.reverse()
                face = channel.bm.faces.new(quad)
                face.material_index = channel.material_index('channel_stones')
        # kerb stones: about 0.9 m long each, set to the slope, with small joints
        y = y_start
        while y < y_end - 0.1:
            length = min(0.75 + 0.3 * random.random(), y_end - y)
            mid = y + length / 2
            tilt = Matrix.Translation((side * (STREET_HALF_WIDTH + KERB_WIDTH / 2), mid, ground_height(mid))) @ Matrix.Rotation(SLOPE, 4, 'X')
            kerbs.box((-KERB_WIDTH / 2, -length / 2 + 0.006, -0.35), (KERB_WIDTH / 2, length / 2 - 0.006, KERB_HEIGHT), 'kerb_stone', tilt)
            y += length
        # the pavement: a loft between kerb back and a little under the house fronts
        x0, x1 = STREET_HALF_WIDTH + KERB_WIDTH - 0.01, HOUSE_FRONT_X + 0.25
        rows = []
        for j in range(steps + 1):
            y = y_start + (y_end - y_start) * j / steps
            fall = 0.03   # a slight cross-fall towards the kerb
            rows.append([pavements.bm.verts.new((side * x0, y, pavement_height(y) - 0.002)),
                         pavements.bm.verts.new((side * x1, y, pavement_height(y) + fall))])
        for j in range(steps):
            quad = [rows[j][0], rows[j][1], rows[j + 1][1], rows[j + 1][0]]
            if side < 0:
                quad.reverse()
            face = pavements.bm.faces.new(quad)
            face.material_index = pavements.material_index('pavement_flags')
    channel.finish('street_channels', 'street')
    kerbs_object = kerbs.finish('street_kerbs', 'street', bevel=0.02)
    pavements.finish('street_pavements', 'street')
    return kerbs_object


def build_ground():
    """The land under and around everything: the muddy colliery yard and the slopes behind the
    cottages, following the street's rise and then levelling out for the colliery."""
    builder = MeshBuilder()
    xs = np.concatenate([np.linspace(-160, -12, 12), np.linspace(-11, 11, 12), np.linspace(12, 160, 12)])
    ys = np.concatenate([np.linspace(-40, STREET_END_Y - 1, 12), np.linspace(STREET_END_Y, 140, 40), np.linspace(145, 260, 10)])
    noise_random = np.random.default_rng(5)
    grid = []
    for y in ys:
        row = []
        for x in xs:
            z = ground_height(y) - 0.04
            if abs(x) > 11 and y < STREET_END_Y:
                z -= 0.4                          # back yards and gardens sit a little lower
            if y > STREET_END_Y + 2 and abs(x) > 3:
                z += 0.12 * noise_random.random()  # trodden, rutted yard
            if abs(x) < 2.3 and y < STREET_END_Y:
                z -= 0.3                          # stay under the setts
            row.append(builder.bm.verts.new((float(x), float(y), z)))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            face = builder.bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
            face.material_index = builder.material_index('colliery_yard')
            face.smooth = True
    builder.finish('ground', 'ground')


# ==================================================================================== the cottages
#
# A cottage is built in its own space: the front wall face at x = 0 facing -x (the street), the
# house running back to x = COTTAGE_DEPTH, its width along y from -2.25 to +2.25, its ground floor
# at z = 0. The right-hand row is placed as is; the left-hand row is turned half round.

HALF_WIDTH = COTTAGE_WIDTH / 2
WALL_THICKNESS = 0.35
DOOR_WIDTH, DOOR_HEIGHT, FANLIGHT_HEIGHT = 0.9, 2.1, 0.42
GROUND_WINDOW = dict(width=1.05, height=1.55, sill=0.85)
UPPER_WINDOW = dict(width=0.95, height=1.35, sill=3.55)
FACADE_LAYOUTS = {
    # door centre y, ground-floor window centre y, the two upstairs window centres
    'door_left': dict(door=-1.15, window=0.95, upper=(-1.15, 0.95)),
    'door_right': dict(door=1.15, window=-0.95, upper=(1.15, -0.95)),
}

cottage_meshes = {}


def build_cottage_shell(wall_material, layout_name):
    """The walls (with openings cut), gables, roofs, ridge, sills, lintels, plinth, door step,
    fascia, gutter, downpipe and chimney stack of one cottage: one mesh per wall type and facade
    layout, shared by every cottage that looks the same."""
    key = (wall_material, layout_name)
    if key in cottage_meshes:
        return cottage_meshes[key]
    layout = FACADE_LAYOUTS[layout_name]
    name = f'cottage_shell_{wall_material}_{layout_name}'
    # the house body (front wall to back wall) and its two gables, then cut the openings
    walls = MeshBuilder()
    walls.box((0, -HALF_WIDTH, -0.9), (COTTAGE_DEPTH, HALF_WIDTH, EAVES_HEIGHT), wall_material)
    walls.prism([(0.05, EAVES_HEIGHT - 0.01), (COTTAGE_DEPTH - 0.05, EAVES_HEIGHT - 0.01), (COTTAGE_DEPTH / 2, RIDGE_HEIGHT - 0.05)],
                -HALF_WIDTH, HALF_WIDTH, wall_material, axis='y')
    shell = walls.finish(name + '_walls', 'cottage_kit')
    cutters = []
    door_y = layout['door']
    cutters.append(((-0.1, door_y - DOOR_WIDTH / 2, 0.0), (0.24, door_y + DOOR_WIDTH / 2, DOOR_HEIGHT + FANLIGHT_HEIGHT + 0.06)))
    window_y = layout['window']
    w = GROUND_WINDOW
    cutters.append(((-0.1, window_y - w['width'] / 2, w['sill']), (0.24, window_y + w['width'] / 2, w['sill'] + w['height'])))
    for upper_y in layout['upper']:
        w = UPPER_WINDOW
        cutters.append(((-0.1, upper_y - w['width'] / 2, w['sill']), (0.24, upper_y + w['width'] / 2, w['sill'] + w['height'])))
    cut_openings(shell, cutters)
    remap_uv(shell)
    # the inside of the openings, a dark back plane (the room behind the glass)
    # stone dressings, roof and rainwater goods
    trim = MeshBuilder()
    # plinth: a dressed stone base course along the front
    trim.box((-0.04, -HALF_WIDTH, -0.9), (0.02, HALF_WIDTH, 0.0), 'dark_dressed_stone')
    # door: threshold, two steps, stone lintel and stone jambs (a plain architrave)
    trim.box((-0.06, door_y - 0.5, -0.08), (0.24, door_y + 0.5, 0.0), 'dressed_stone')
    trim.box((-0.36, door_y - 0.56, -0.26), (0.0, door_y + 0.56, -0.08), 'dressed_stone')
    trim.box((-0.66, door_y - 0.62, -0.95), (-0.3, door_y + 0.62, -0.26), 'dressed_stone')
    door_head = DOOR_HEIGHT + FANLIGHT_HEIGHT + 0.06
    trim.box((-0.05, door_y - DOOR_WIDTH / 2 - 0.2, door_head), (0.08, door_y + DOOR_WIDTH / 2 + 0.2, door_head + 0.3), 'dressed_stone')
    for jamb_side in (-1, 1):
        jy = door_y + jamb_side * (DOOR_WIDTH / 2 + 0.07)
        trim.box((-0.04, jy - 0.07, 0.0), (0.06, jy + 0.07, door_head), 'dressed_stone')
    # window sills (projecting, with a drip) and lintels
    def window_dressings(centre_y, window):
        width, sill, top = window['width'], window['sill'], window['sill'] + window['height']
        trim.box((-0.08, centre_y - width / 2 - 0.1, sill - 0.1), (0.24, centre_y + width / 2 + 0.1, sill), 'dressed_stone')
        trim.box((-0.04, centre_y - width / 2 - 0.16, top), (0.06, centre_y + width / 2 + 0.16, top + 0.28), 'dressed_stone')
    window_dressings(window_y, GROUND_WINDOW)
    for upper_y in layout['upper']:
        window_dressings(upper_y, UPPER_WINDOW)
    # a band course of stone at first-floor level, and a moulded eaves course
    trim.box((-0.03, -HALF_WIDTH, 2.98), (0.02, HALF_WIDTH, 3.1), 'dressed_stone')
    trim.box((-0.07, -HALF_WIDTH, EAVES_HEIGHT - 0.22), (0.02, HALF_WIDTH, EAVES_HEIGHT - 0.1), 'dressed_stone')
    # fascia board under the slates, front and back
    trim.box((-0.3, -HALF_WIDTH, EAVES_HEIGHT - 0.12), (-0.27, HALF_WIDTH, EAVES_HEIGHT + 0.1), 'fascia_board')
    trim.box((COTTAGE_DEPTH + 0.27, -HALF_WIDTH, EAVES_HEIGHT - 0.12), (COTTAGE_DEPTH + 0.3, HALF_WIDTH, EAVES_HEIGHT + 0.1), 'fascia_board')
    trim_object = trim.finish(name + '_trim', 'cottage_kit', bevel=0.012)

    roof = MeshBuilder()
    # slate slopes: 7 cm thick, overhanging the walls by 0.3 m at the eaves
    overhang = 0.32
    slope_length = (COTTAGE_DEPTH / 2 + overhang) / math.cos(ROOF_PITCH)
    for direction in (-1, 1):
        # front slope (direction -1) runs from the front eaves up to the ridge
        eaves_x = COTTAGE_DEPTH / 2 + direction * (COTTAGE_DEPTH / 2 + overhang)
        eaves_z = EAVES_HEIGHT + 0.02 - overhang * math.tan(ROOF_PITCH)
        ridge = (COTTAGE_DEPTH / 2, RIDGE_HEIGHT + 0.08)
        thickness = 0.07
        lower = [(eaves_x, eaves_z), ridge]
        upper = [(eaves_x, eaves_z + thickness / math.cos(ROOF_PITCH)), (ridge[0], ridge[1] + thickness / math.cos(ROOF_PITCH))]
        outline = [lower[0], lower[1], upper[1], upper[0]]
        faces = roof.prism(outline, -HALF_WIDTH, HALF_WIDTH, 'roof_slate', axis='y')
        # slates: courses parallel to the eaves (along y), rising up the slope
        for face in faces:
            for loop in face.loops:
                co = loop.vert.co
                along_slope = math.hypot(co.x - eaves_x, co.z - eaves_z)
                loop[roof.uv_layer].uv = (co.y / 3.0, along_slope / 3.0)
            roof.explicit_uv_faces.add(face)
    # clay ridge tiles: a rounded roll along the ridge, with lapped joints every 45 cm
    ridge_z = RIDGE_HEIGHT + 0.08 + 0.07 / math.cos(ROOF_PITCH)
    y = -HALF_WIDTH
    while y < HALF_WIDTH - 0.01:
        end = min(y + 0.45, HALF_WIDTH)
        roof.rod((COTTAGE_DEPTH / 2, y, ridge_z - 0.02), (COTTAGE_DEPTH / 2, end - 0.01, ridge_z - 0.02), 0.12, 'ridge_clay', sides=10)
        roof.rod((COTTAGE_DEPTH / 2, end - 0.06, ridge_z - 0.02), (COTTAGE_DEPTH / 2, end, ridge_z - 0.02), 0.13, 'ridge_clay', sides=10)
        y = end
    roof_object = roof.finish(name + '_roof', 'cottage_kit')

    rain = MeshBuilder()
    # cast-iron half-round gutter on the fascia (a rolled lip shown as a round section), with
    # brackets, and a downpipe with a hopper head, wall brackets and a shoe at the foot
    gutter_x, gutter_z = -0.38, EAVES_HEIGHT - 0.05
    rain.rod((gutter_x, -HALF_WIDTH, gutter_z), (gutter_x, HALF_WIDTH, gutter_z), 0.065, 'cast_iron', sides=10)
    for bracket_y in (-1.6, -0.5, 0.6, 1.7):
        rain.box((gutter_x - 0.07, bracket_y - 0.015, gutter_z - 0.075), (-0.28, bracket_y + 0.015, gutter_z - 0.05), 'cast_iron')
    pipe_y = HALF_WIDTH - 0.18
    rain.rod((gutter_x, pipe_y, gutter_z - 0.05), (-0.2, pipe_y, gutter_z - 0.3), 0.04, 'cast_iron', sides=8)
    rain.box((-0.3, pipe_y - 0.12, gutter_z - 0.62), (-0.04, pipe_y + 0.12, gutter_z - 0.3), 'cast_iron')
    rain.rod((-0.15, pipe_y, gutter_z - 0.62), (-0.15, pipe_y, -0.55), 0.045, 'cast_iron', sides=8)
    rain.rod((-0.15, pipe_y, -0.55), (-0.32, pipe_y, -0.75), 0.045, 'cast_iron', sides=8)
    for ear_z in (0.6, 2.4, 4.2):
        rain.box((-0.2, pipe_y - 0.075, ear_z), (0.0, pipe_y + 0.075, ear_z + 0.06), 'cast_iron')
    rain_object = rain.finish(name + '_rainwater', 'cottage_kit', bevel=0.008)

    chimney = MeshBuilder()
    # the stack straddles the party wall at +y, on the ridge: brick shaft, two oversailing
    # courses, a stone cap, and four clay pots of different heights (two for each house)
    stack_x0, stack_x1 = COTTAGE_DEPTH / 2 - 0.6, COTTAGE_DEPTH / 2 + 0.6
    stack_y0, stack_y1 = HALF_WIDTH - 0.48, HALF_WIDTH + 0.48
    stack_bottom, stack_top = RIDGE_HEIGHT - 1.2, RIDGE_HEIGHT + 1.35
    chimney.box((stack_x0, stack_y0, stack_bottom), (stack_x1, stack_y1, stack_top), wall_material)
    chimney.box((stack_x0 - 0.06, stack_y0 - 0.06, stack_top - 0.36), (stack_x1 + 0.06, stack_y1 + 0.06, stack_top - 0.27), wall_material)
    chimney.box((stack_x0 - 0.1, stack_y0 - 0.1, stack_top - 0.27), (stack_x1 + 0.1, stack_y1 + 0.1, stack_top - 0.18), wall_material)
    chimney.box((stack_x0 - 0.04, stack_y0 - 0.04, stack_top - 0.18), (stack_x1 + 0.04, stack_y1 + 0.04, stack_top - 0.05), 'dressed_stone')
    for index, pot_x in enumerate((-0.42, -0.14, 0.14, 0.42)):
        height = (0.62, 0.48, 0.7, 0.55)[index]
        material_name = 'chimney_pot_sooted' if index % 2 else 'chimney_pot_clay'
        base = stack_top - 0.05
        profile = [(0.0, 0.0), (0.15, 0.0), (0.15, 0.06), (0.12, 0.1), (0.1, height - 0.12), (0.125, height - 0.07),
                   (0.125, height), (0.095, height), (0.095, height - 0.25)]
        chimney.lathe(profile, material_name, sides=12, centre=(COTTAGE_DEPTH / 2 + pot_x, HALF_WIDTH, base))
        # flaunching: the mortar collar round the pot's foot
        chimney.lathe([(0.21, -0.001), (0.15, 0.08), (0.0, 0.08)], 'plaster_dark', sides=12, centre=(COTTAGE_DEPTH / 2 + pot_x, HALF_WIDTH, base))
    chimney_object = chimney.finish(name + '_chimney', 'cottage_kit', bevel=0.012)
    parts = [shell, trim_object, roof_object, rain_object, chimney_object]
    cottage_meshes[key] = parts
    return parts


window_meshes = {}


def build_sash_window(window, frame_paint='paint_cream'):
    """A six-over-six sliding sash window that fits an opening: a painted box frame set back in
    the reveal, an upper sash in front and a lower sash behind, each with stiles, rails and
    glazing bars (three panes across, two up), and a meeting rail. The glass is a separate part.
    Built in the cottage's space with the opening centred at y = 0, sill at z = 0."""
    key = (window['width'], window['height'], frame_paint)
    if key in window_meshes:
        return window_meshes[key]
    width, height = window['width'], window['height']
    builder = MeshBuilder()
    frame_front, frame_back = 0.1, 0.22
    frame = 0.06
    half = width / 2
    # box frame: head, sill (a sloped timber sill shown as a box), and two pulley-stile jambs
    builder.box((frame_front, -half, height - frame), (frame_back, half, height), frame_paint)
    builder.box((frame_front - 0.03, -half, 0.0), (frame_back, half, 0.05), frame_paint)
    builder.box((frame_front, -half, 0.0), (frame_back, -half + frame, height), frame_paint)
    builder.box((frame_front, half - frame, 0.0), (frame_back, half, height), frame_paint)
    inner_half = half - frame
    meeting = 0.05 + (height - frame - 0.05) / 2
    stile, top_rail, bottom_rail, meeting_rail, bar = 0.045, 0.05, 0.08, 0.03, 0.018

    def sash(z0, z1, x0, x1, bottom, top):
        builder.box((x0, -inner_half, z0), (x1, -inner_half + stile, z1), frame_paint)
        builder.box((x0, inner_half - stile, z0), (x1, inner_half, z1), frame_paint)
        builder.box((x0, -inner_half, z0), (x1, inner_half, z0 + bottom), frame_paint)
        builder.box((x0, -inner_half, z1 - top), (x1, inner_half, z1), frame_paint)
        pane_width = (2 * inner_half - 2 * stile) / 3
        for k in (1, 2):
            y = -inner_half + stile + pane_width * k
            builder.box((x0 + 0.008, y - bar / 2, z0 + bottom), (x1 - 0.008, y + bar / 2, z1 - top), frame_paint)
        z_mid = (z0 + bottom + z1 - top) / 2
        builder.box((x0 + 0.008, -inner_half + stile, z_mid - bar / 2), (x1 - 0.008, inner_half - stile, z_mid + bar / 2), frame_paint)

    # upper sash at the front, lower sash behind; they overlap at the meeting rails
    sash(meeting - meeting_rail / 2, height - frame, 0.12, 0.16, meeting_rail, top_rail)
    sash(0.05, meeting + meeting_rail / 2, 0.16, 0.2, bottom_rail, meeting_rail)
    # sash horns and a brass catch on the meeting rail
    builder.box((0.12, -0.03, meeting + 0.01), (0.105, 0.03, meeting + 0.03), 'brass')
    part = builder.finish(f'sash_window_{width}x{height}_{frame_paint}', 'cottage_kit', bevel=0.004)
    window_meshes[key] = part
    return part


def build_window_glass(window, material_name):
    builder = MeshBuilder()
    width, height = window['width'], window['height']
    x = 0.17
    builder.quad([(x, width / 2, 0.05), (x, -width / 2, 0.05), (x, -width / 2, height - 0.06), (x, width / 2, height - 0.06)],
                 material_name, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # the dark inside reveal behind the glass edge, so the gap between frame and wall reads deep
    return builder


door_meshes = {}


def build_front_door(paint):
    """A four-panel front door: stiles, rails, a centre muntin, raised-and-fielded panels, a
    painted frame, a fanlight with glazing bars over a transom, and brass furniture (knob,
    letter plate, knocker, keyhole escutcheon). Centred at y = 0, threshold at z = 0."""
    if paint in door_meshes:
        return door_meshes[paint]
    builder = MeshBuilder()
    half = DOOR_WIDTH / 2
    face_x = 0.16                   # the door's outer face, set back in the reveal
    thick = 0.05
    frame = 0.06
    # door frame and transom
    builder.box((face_x - 0.03, -half, 0.0), (0.24, -half + frame, DOOR_HEIGHT + FANLIGHT_HEIGHT + 0.06), paint)
    builder.box((face_x - 0.03, half - frame, 0.0), (0.24, half, DOOR_HEIGHT + FANLIGHT_HEIGHT + 0.06), paint)
    builder.box((face_x - 0.04, -half, DOOR_HEIGHT), (0.24, half, DOOR_HEIGHT + 0.07), paint)
    builder.box((face_x - 0.03, -half, DOOR_HEIGHT + FANLIGHT_HEIGHT), (0.24, half, DOOR_HEIGHT + FANLIGHT_HEIGHT + 0.06), paint)
    # fanlight bars (four lights)
    for k in (1, 2, 3):
        y = -half + frame + (DOOR_WIDTH - 2 * frame) * k / 4
        builder.box((face_x, y - 0.01, DOOR_HEIGHT + 0.07), (face_x + 0.03, y + 0.01, DOOR_HEIGHT + FANLIGHT_HEIGHT), paint)
    # the leaf: a back board, then stiles, rails and muntin standing proud, with fielded panels
    leaf_half = half - frame
    builder.box((face_x + 0.015, -leaf_half, 0.01), (face_x + thick, leaf_half, DOOR_HEIGHT - 0.005), paint)
    stile, muntin = 0.11, 0.1
    rails = [(0.01, 0.24), (0.88, 1.06), (DOOR_HEIGHT - 0.12, DOOR_HEIGHT - 0.005)]
    builder.box((face_x, -leaf_half, 0.01), (face_x + 0.015, -leaf_half + stile, DOOR_HEIGHT - 0.005), paint)
    builder.box((face_x, leaf_half - stile, 0.01), (face_x + 0.015, leaf_half, DOOR_HEIGHT - 0.005), paint)
    for z0, z1 in rails:
        builder.box((face_x, -leaf_half, z0), (face_x + 0.015, leaf_half, z1), paint)
    builder.box((face_x, -muntin / 2, 0.24), (face_x + 0.015, muntin / 2, DOOR_HEIGHT - 0.12), paint)
    # fielded panels: a raised centre with sloped margins (a lathe-free way: a box on a box)
    panels = [(0.24, 0.88), (1.06, DOOR_HEIGHT - 0.12)]
    for z0, z1 in panels:
        for y0, y1 in ((-leaf_half + stile, -muntin / 2), (muntin / 2, leaf_half - stile)):
            builder.box((face_x + 0.009, y0 + 0.045, z0 + 0.045), (face_x + 0.015, y1 - 0.045, z1 - 0.045), paint)
            builder.box((face_x + 0.012, y0 + 0.01, z0 + 0.01), (face_x + 0.015, y1 - 0.01, z1 - 0.01), paint)
    # brass furniture on the lock rail and the middle of the door
    builder.rod((face_x, leaf_half - 0.07, 0.98), (face_x - 0.06, leaf_half - 0.07, 0.98), 0.012, 'brass', sides=8)
    builder.lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.02), (0.0, 0.045)], 'brass', sides=10, centre=(face_x - 0.06, leaf_half - 0.07, 0.98), axis='y')
    builder.box((face_x - 0.008, -0.14, 0.95), (face_x, 0.14, 1.0), 'brass')                 # letter plate
    builder.box((face_x - 0.004, -0.11, 0.962), (face_x - 0.008, 0.11, 0.988), 'paint_black')  # its slot
    builder.box((face_x - 0.01, -0.035, 1.42), (face_x, 0.035, 1.52), 'brass')                 # knocker plate
    builder.rod((face_x - 0.03, -0.045, 1.4), (face_x - 0.03, 0.045, 1.4), 0.012, 'brass', sides=8)  # knocker ring bar
    builder.box((face_x - 0.006, leaf_half - 0.085, 0.82), (face_x, leaf_half - 0.055, 0.88), 'brass')  # escutcheon
    part = builder.finish(f'front_door_{paint}', 'cottage_kit', bevel=0.004)
    door_meshes[paint] = part
    return part


def place_cottage_row(side, first_y, count, wall_material, row_name):
    """A terrace of cottages on one side of the street, each stepping up the slope.
    side: +1 right of the camera (fronts face -x), -1 left (fronts face +x)."""
    rotation = 0.0 if side > 0 else math.pi
    house_x = side * HOUSE_FRONT_X
    lit_count = 0
    paints = ['paint_bottle_green', 'paint_maroon', 'paint_navy', 'paint_brown']
    for index in range(count):
        centre_y = first_y + COTTAGE_WIDTH * (index + 0.5)
        # ground floor sits 15 cm above the pavement at the uphill end of the house
        floor_z = pavement_height(centre_y + HALF_WIDTH) + 0.15
        layout_name = 'door_left' if index % 2 == 0 else 'door_right'
        location = (house_x, centre_y, floor_z)
        name = f'{row_name}_cottage_{index + 1:02d}'
        for part in build_cottage_shell(wall_material, layout_name):
            linked_copy(part, f'{name}_{part.name.split("_")[-1]}', location, rotation, 'cottages')
        layout = FACADE_LAYOUTS[layout_name]
        # in the left row the cottage is turned half round, so its own +y points down the street
        def world(local):
            local = Vector(local)
            if side < 0:
                local = Vector((-local.x, -local.y, local.z))
            return Vector(location) + local

        door_paint = paints[int(random.integers(0, len(paints)))]
        door = linked_copy(build_front_door(door_paint), f'{name}_door', world((0, layout['door'], 0)), rotation, 'cottages')
        marker(f'{name}_doorway', tuple(world((-0.7, layout['door'], 0))))
        windows = [(layout['window'], GROUND_WINDOW, 'ground')] + [(y, UPPER_WINDOW, f'upper_{k}') for k, y in enumerate(layout['upper'])]
        for window_y, window, label in windows:
            frame = build_sash_window(window)
            linked_copy(frame, f'{name}_window_{label}', world((0, window_y, window['sill'])), rotation, 'cottages')
            lit = random.random() < (0.6 if label == 'ground' else 0.35)
            picture_index = int(random.integers(0, 3))
            glass_material = f'window_lit_glow_{picture_index}' if lit else f'window_dark_{picture_index}'
            glass = build_window_glass(window, glass_material).finish(f'{name}_glass_{label}', 'cottages',
                                                                     location=tuple(world((0, window_y, window['sill']))), rotation_z=rotation)
            if lit:
                lit_count += 1
                spill = bpy.data.lights.new(f'{name}_window_light_{label}', 'POINT')
                spill.energy = 45.0
                spill.color = (1.0, 0.66, 0.34)
                spill.shadow_soft_size = 0.5
                light_object = bpy.data.objects.new(spill.name, spill)
                light_object.location = world((-0.45, window_y, window['sill'] + window['height'] * 0.5))
                collection('preview_lights').objects.link(light_object)
        # the first cottage of each row also has a chimney stack on its downhill gable
        if index == 0:
            stack = build_cottage_shell(wall_material, layout_name)[4]
            linked_copy(stack, f'{name}_end_chimney', world((0, -COTTAGE_WIDTH, 0)) - Vector((0, 0, 0)), rotation, 'cottages')
        marker(f'{name}_chimney_top', tuple(world((COTTAGE_DEPTH / 2, HALF_WIDTH, RIDGE_HEIGHT + 2.1))))
    return lit_count


# ==================================================================================== gas lamps

lamp_parts = {}


def build_gas_lamp():
    """A cast-iron gas lamp: a fluted base, a tapering post with collars, the ladder bar, and a
    four-sided tapered lantern (corner posts, glowing glass, a gas mantle inside), with a domed
    roof, a vent and a finial. Origin at its foot."""
    if lamp_parts:
        return lamp_parts['iron'], lamp_parts['glass']
    iron = MeshBuilder()
    iron.lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.06), (0.17, 0.09), (0.16, 0.42), (0.18, 0.46), (0.13, 0.52), (0.09, 0.62),
                (0.07, 0.75), (0.0, 0.75)], 'cast_iron', sides=16)
    # flutes on the base: thin ribs
    for k in range(8):
        angle = 2 * math.pi * k / 8
        x, y = math.cos(angle) * 0.163, math.sin(angle) * 0.163
        iron.centred_box((x, y, 0.27), (0.025, 0.025, 0.3), 'cast_iron')
    iron.rod((0, 0, 0.72), (0, 0, 2.7), 0.06, 'cast_iron', sides=12, end_radius=0.045)
    for collar_z in (1.05, 2.45):
        iron.lathe([(0.0, -0.03), (0.07, -0.03), (0.08, 0.0), (0.07, 0.03), (0.0, 0.03)], 'cast_iron', sides=12, centre=(0, 0, collar_z))
    # the ladder bar with ball ends
    iron.box((-0.33, -0.018, 2.62), (0.33, 0.018, 2.66), 'cast_iron')
    for end in (-0.34, 0.34):
        iron.lathe([(0.0, -0.035), (0.03, -0.02), (0.035, 0.0), (0.03, 0.02), (0.0, 0.035)], 'cast_iron', sides=10, centre=(end, 0, 2.64))
    # lantern seat (a cone spreading to the lantern's floor)
    iron.lathe([(0.0, 2.7), (0.05, 2.7), (0.13, 2.82), (0.13, 2.85), (0.0, 2.85)], 'cast_iron', sides=12)
    # lantern: tapered (narrow at the bottom), 0.24 wide at the bottom, 0.36 at the top
    bottom_z, top_z = 2.85, 3.38
    bottom_half, top_half = 0.12, 0.18
    corners_bottom = [(bottom_half, bottom_half), (-bottom_half, bottom_half), (-bottom_half, -bottom_half), (bottom_half, -bottom_half)]
    corners_top = [(top_half, top_half), (-top_half, top_half), (-top_half, -top_half), (top_half, -top_half)]
    for (bx, by), (tx, ty) in zip(corners_bottom, corners_top):
        iron.beam((bx, by, bottom_z), (tx, ty, top_z), 0.025, 0.025, 'cast_iron')
    iron.box((-bottom_half - 0.02, -bottom_half - 0.02, bottom_z - 0.02), (bottom_half + 0.02, bottom_half + 0.02, bottom_z + 0.02), 'cast_iron')
    iron.box((-top_half - 0.02, -top_half - 0.02, top_z - 0.02), (top_half + 0.02, top_half + 0.02, top_z + 0.02), 'cast_iron')
    # the roof: a low pyramid with an overhang, then a round vent cap and a finial
    roof_half = 0.24
    apex = (0, 0, top_z + 0.18)
    base = [(roof_half, roof_half, top_z + 0.02), (-roof_half, roof_half, top_z + 0.02), (-roof_half, -roof_half, top_z + 0.02), (roof_half, -roof_half, top_z + 0.02)]
    for k in range(4):
        a, b = base[k], base[(k + 1) % 4]
        face_verts = [iron.bm.verts.new(a), iron.bm.verts.new(b), iron.bm.verts.new(apex)]
        face = iron.bm.faces.new(face_verts)
        face.material_index = iron.material_index('cast_iron')
    underside = iron.bm.faces.new([iron.bm.verts.new(c) for c in reversed(base)])
    underside.material_index = iron.material_index('cast_iron')
    iron.lathe([(0.0, top_z + 0.12), (0.07, top_z + 0.12), (0.07, top_z + 0.22), (0.1, top_z + 0.24), (0.0, top_z + 0.27)], 'cast_iron', sides=12)
    iron.lathe([(0.0, top_z + 0.27), (0.02, top_z + 0.27), (0.012, top_z + 0.32), (0.03, top_z + 0.35), (0.0, top_z + 0.39)], 'cast_iron', sides=8)
    # the gas pipe and mantle inside
    iron.rod((0, 0, bottom_z), (0, 0, bottom_z + 0.18), 0.012, 'brass', sides=6)
    iron_object = iron.finish('gas_lamp_iron', 'lamp_kit', bevel=0.004)
    glass = MeshBuilder()
    inset = 0.004
    for k in range(4):
        b0, b1 = corners_bottom[k], corners_bottom[(k + 1) % 4]
        t0, t1 = corners_top[k], corners_top[(k + 1) % 4]
        glass.quad([(b0[0] * (1 - inset), b0[1] * (1 - inset), bottom_z + 0.02), (b1[0] * (1 - inset), b1[1] * (1 - inset), bottom_z + 0.02),
                    (t1[0] * (1 - inset), t1[1] * (1 - inset), top_z - 0.02), (t0[0] * (1 - inset), t0[1] * (1 - inset), top_z - 0.02)],
                   'lamp_glass_glow', uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    glass.lathe([(0.0, bottom_z + 0.17), (0.035, bottom_z + 0.18), (0.04, bottom_z + 0.24), (0.0, bottom_z + 0.27)], 'lamp_glass_glow', sides=8)
    glass_object = glass.finish('gas_lamp_glass', 'lamp_kit')
    lamp_parts['iron'], lamp_parts['glass'] = iron_object, glass_object
    return iron_object, glass_object


def place_gas_lamps():
    iron, glass = build_gas_lamp()
    spots = [(1, 11.0), (-1, 25.0), (1, 39.0), (-1, 53.0), (1, 64.5)]
    for index, (side, y) in enumerate(spots):
        x = side * (STREET_HALF_WIDTH + KERB_WIDTH + 0.35)
        location = (x, y, pavement_height(y))
        linked_copy(iron, f'gas_lamp_{index}_post', location, 0.0, 'lamps')
        linked_copy(glass, f'gas_lamp_{index}_glass', location, 0.0, 'lamps')
        marker(f'lamp_{index}', (x, y, pavement_height(y) + 3.1))
        light = bpy.data.lights.new(f'gas_lamp_{index}_light', 'POINT')
        light.energy = 260.0
        light.color = (1.0, 0.72, 0.4)
        light.shadow_soft_size = 0.12
        light_object = bpy.data.objects.new(light.name, light)
        light_object.location = (x, y, pavement_height(y) + 3.08)
        collection('preview_lights').objects.link(light_object)


# ==================================================================================== colliery

COLLIERY_GROUND = PLATEAU_Y * RISE_PER_METRE
HEADFRAME_Y = 86.0
SHEAVE_DECK_Z = 16.0
WHEEL_RADIUS = 2.1
WHEEL_GAP = 0.35
STAY_FOOT_X = -12.0                       # the raking back stays lean towards the engine house
ENGINE_HOUSE = (-22.0, -11.0, HEADFRAME_Y + 5.0, HEADFRAME_Y + 15.0)   # x0, x1, y0, y1
CHIMNEY_XY = (-9.5, HEADFRAME_Y + 22.0)   # seen in the sky left of the headframe


def build_headframe():
    """A riveted steel lattice headframe: four splayed legs braced with horizontal girders and
    X-bracing on all four faces, gusset plates at the joints, a ladder with hoops, a sheave deck
    with a handrail, bearing blocks, the two winding wheels (separate objects) and their ropes."""
    base_z = COLLIERY_GROUND
    builder = MeshBuilder()
    base_half_x, base_half_y = 4.6, 3.2
    top_half_x, top_half_y = 2.9, 1.9
    levels = [0.0, 3.6, 7.0, 10.2, 13.2, SHEAVE_DECK_Z]

    def corner(sx, sy, z):
        t = z / SHEAVE_DECK_Z
        hx = base_half_x + (top_half_x - base_half_x) * t
        hy = base_half_y + (top_half_y - base_half_y) * t
        return Vector((sx * hx, HEADFRAME_Y + sy * hy, base_z + z))

    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    # legs: built-up box legs (a wide member with a second plate face, so they read heavy)
    for sx, sy in corners:
        builder.beam(corner(sx, sy, 0), corner(sx, sy, SHEAVE_DECK_Z), 0.42, 0.42, 'headframe_steel')
        # leg foot: a concrete-and-stone pier
        foot = corner(sx, sy, 0)
        builder.box((foot.x - 0.5, foot.y - 0.5, base_z - 1.0), (foot.x + 0.5, foot.y + 0.5, base_z + 0.25), 'dark_dressed_stone')
    for level_index, z in enumerate(levels):
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            p0, p1 = corner(*a, z), corner(*b, z)
            if z > 0:
                builder.beam(p0, p1, 0.3, 0.22, 'headframe_steel')
            if level_index < len(levels) - 1:
                z_next = levels[level_index + 1]
                q0, q1 = corner(*a, z_next), corner(*b, z_next)
                # X-bracing in this panel (angle-iron diagonals)
                builder.beam(p0, q1, 0.14, 0.1, 'headframe_steel')
                builder.beam(p1, q0, 0.14, 0.1, 'headframe_steel')
                # a small plate where the diagonals cross
                middle = (p0 + q1 + p1 + q0) / 4
                outward = Vector((middle.x - 0, middle.y - HEADFRAME_Y, 0))
                outward.normalize()
                builder.centred_box(middle, (0.32 if abs(outward.x) < 0.5 else 0.06, 0.32 if abs(outward.x) >= 0.5 else 0.06, 0.32), 'headframe_steel')
        # gusset plates at the leg joints
        if z > 0:
            for sx, sy in corners:
                point = corner(sx, sy, z)
                builder.centred_box(point, (0.6, 0.6, 0.5), 'headframe_steel')
    # rivet rows suggested by thin cover plates along the legs
    for sx, sy in corners:
        start, end = corner(sx, sy, 0.3), corner(sx, sy, SHEAVE_DECK_Z - 0.3)
        offset = Vector((sx * 0.0, -0.23, 0)) if sy < 0 else Vector((0, 0.23, 0))
        builder.beam(start + offset, end + offset, 0.26, 0.04, 'headframe_steel')
    # raking back stays towards the engine house (to the left), as on the reference painting
    for sy in (-1, 1):
        top = corner(-1, sy, SHEAVE_DECK_Z - 1.0)
        foot = Vector((STAY_FOOT_X, HEADFRAME_Y + sy * 3.6, base_z))
        builder.beam(top, foot, 0.4, 0.4, 'headframe_steel')
        builder.box((foot.x - 0.6, foot.y - 0.6, base_z - 1.0), (foot.x + 0.6, foot.y + 0.6, base_z + 0.3), 'dark_dressed_stone')
        # braces from the stays to the legs
        for t in (0.35, 0.65):
            on_stay = top.lerp(foot, t)
            on_leg = corner(-1, sy, (on_stay.z - base_z))
            builder.beam(on_stay, on_leg, 0.16, 0.12, 'headframe_steel')
    # a cross brace between the two stays
    builder.beam(corner(-1, -1, SHEAVE_DECK_Z - 1.0).lerp(Vector((STAY_FOOT_X, HEADFRAME_Y - 3.6, base_z)), 0.5),
                 corner(-1, 1, SHEAVE_DECK_Z - 1.0).lerp(Vector((STAY_FOOT_X, HEADFRAME_Y + 3.6, base_z)), 0.5), 0.16, 0.12, 'headframe_steel')
    # sheave deck: a plate floor on girders, a handrail with posts all round
    deck_z = base_z + SHEAVE_DECK_Z
    builder.box((-top_half_x - 0.6, HEADFRAME_Y - top_half_y - 0.6, deck_z), (top_half_x + 0.6, HEADFRAME_Y + top_half_y + 0.6, deck_z + 0.12), 'headframe_steel')
    for x0, y0, x1, y1 in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
        a = Vector((x0 * (top_half_x + 0.55), HEADFRAME_Y + y0 * (top_half_y + 0.55), deck_z + 0.12))
        b = Vector((x1 * (top_half_x + 0.55), HEADFRAME_Y + y1 * (top_half_y + 0.55), deck_z + 0.12))
        builder.rod(a + Vector((0, 0, 1.0)), b + Vector((0, 0, 1.0)), 0.025, 'headframe_steel', sides=6)
        builder.rod(a + Vector((0, 0, 0.5)), b + Vector((0, 0, 0.5)), 0.02, 'headframe_steel', sides=6)
        posts = max(2, int((b - a).length / 1.2))
        for k in range(posts + 1):
            p = a.lerp(b, k / posts)
            builder.rod(p, p + Vector((0, 0, 1.0)), 0.025, 'headframe_steel', sides=6)
    # two heavy main girders across the deck carry the wheel bearings
    wheel_centre_z = deck_z + 0.9 + WHEEL_RADIUS
    for gy in (-0.75, 0.75):
        builder.box((-top_half_x - 0.4, HEADFRAME_Y + gy - 0.2, deck_z + 0.12), (top_half_x + 0.4, HEADFRAME_Y + gy + 0.2, deck_z + 0.62), 'headframe_steel')
    wheel_xs = (-(WHEEL_RADIUS + WHEEL_GAP / 2), WHEEL_RADIUS + WHEEL_GAP / 2)
    for wx in wheel_xs:
        # A-frame bearing pedestals either side of each wheel, up to the axle
        for gy in (-0.75, 0.75):
            builder.beam((wx - 0.7, HEADFRAME_Y + gy, deck_z + 0.62), (wx, HEADFRAME_Y + gy, wheel_centre_z - 0.2), 0.22, 0.22, 'headframe_steel')
            builder.beam((wx + 0.7, HEADFRAME_Y + gy, deck_z + 0.62), (wx, HEADFRAME_Y + gy, wheel_centre_z - 0.2), 0.22, 0.22, 'headframe_steel')
            builder.box((wx - 0.25, HEADFRAME_Y + gy - 0.17, wheel_centre_z - 0.3), (wx + 0.25, HEADFRAME_Y + gy + 0.17, wheel_centre_z + 0.18), 'headframe_steel')
            builder.lathe([(0.0, -0.18), (0.16, -0.18), (0.16, 0.18), (0.0, 0.18)], 'headframe_steel', sides=12, centre=(wx, HEADFRAME_Y + gy, wheel_centre_z), axis='y')
    # a ladder up the front right leg with safety hoops
    ladder_bottom, ladder_top = corner(1, -1, 0.0) + Vector((-0.9, -0.35, 0)), corner(1, -1, SHEAVE_DECK_Z) + Vector((-0.9, -0.35, 0))
    for side_offset in (-0.22, 0.22):
        builder.rod(ladder_bottom + Vector((side_offset, 0, 0)), ladder_top + Vector((side_offset, 0, 0)), 0.02, 'headframe_steel', sides=6)
    rungs = int((ladder_top - ladder_bottom).length / 0.3)
    for k in range(1, rungs):
        p = ladder_bottom.lerp(ladder_top, k / rungs)
        builder.rod(p + Vector((-0.22, 0, 0)), p + Vector((0.22, 0, 0)), 0.014, 'headframe_steel', sides=5)
    for k in range(4, rungs, 6):
        p = ladder_bottom.lerp(ladder_top, k / rungs)
        builder.lathe([(0.34, -0.03), (0.36, 0.0), (0.34, 0.03)], 'headframe_steel', sides=12, centre=(p.x, p.y - 0.25, p.z))
    builder.finish('headframe_lattice', 'colliery', bevel=0.01)
    # the winding wheels
    wheel_parts = []
    for name, wx in (('winding_wheel_left', wheel_xs[0]), ('winding_wheel_right', wheel_xs[1])):
        wheel_parts.append(build_winding_wheel(name, (wx, HEADFRAME_Y, wheel_centre_z)))
    # ropes: from the inner side of each wheel straight down the shaft (to the cages), and from
    # the outer top of each wheel down to the engine house drum (to the left) or the second
    # winding house (to the right)
    ropes = MeshBuilder()
    engine_drum = Vector((ENGINE_HOUSE[1] - 0.5, (ENGINE_HOUSE[2] + ENGINE_HOUSE[3]) / 2, base_z + 6.0))
    second_drum = Vector((22.0, HEADFRAME_Y + 1.0, base_z + 5.5))
    for wx, drum in ((wheel_xs[0], engine_drum), (wheel_xs[1], second_drum)):
        inner_x = wx + (WHEEL_RADIUS - 0.08) * (1 if wx < 0 else -1)
        ropes.rod((inner_x, HEADFRAME_Y, wheel_centre_z), (inner_x, HEADFRAME_Y, base_z + 2.6), 0.028, 'wire_rope', sides=6)
        direction = (drum - Vector((wx, HEADFRAME_Y, wheel_centre_z)))
        direction.y = 0
        direction.normalize()
        # the tangent point on the wheel facing the drum, a little above the axle
        normal = Vector((-direction.z, 0, direction.x)) if direction.x > 0 else Vector((direction.z, 0, -direction.x))
        tangent_point = Vector((wx, HEADFRAME_Y, wheel_centre_z)) + normal * (WHEEL_RADIUS - 0.08)
        ropes.rod(tangent_point, drum, 0.028, 'wire_rope', sides=6)
    ropes.finish('winding_ropes', 'colliery')
    marker('wheel_left_axle', (wheel_xs[0], HEADFRAME_Y, wheel_centre_z))
    marker('wheel_right_axle', (wheel_xs[1], HEADFRAME_Y, wheel_centre_z))
    return wheel_parts


def build_winding_wheel(name, centre):
    """One spoked winding wheel (sheave) lying in the x-z plane, turning about the y axis: a
    grooved rim (lathed section), a hub with flanges, 16 spokes in two dished sets meeting the
    hub's two flanges, and the axle. Origin at the axle centre."""
    builder = MeshBuilder()
    radius = WHEEL_RADIUS
    rim_segments = 48
    # rim cross-section (in the radial / axial plane), with the rope groove on the outside
    section = [(radius - 0.16, -0.12), (radius - 0.02, -0.12), (radius + 0.04, -0.09), (radius - 0.04, -0.03),
               (radius - 0.04, 0.03), (radius + 0.04, 0.09), (radius - 0.02, 0.12), (radius - 0.16, 0.12)]
    rings = []
    for i in range(rim_segments):
        angle = 2 * math.pi * i / rim_segments
        c, s = math.cos(angle), math.sin(angle)
        rings.append([builder.bm.verts.new((r * c, a, r * s)) for r, a in section])
    rim_index = builder.material_index('wheel_iron')
    for i in range(rim_segments):
        j = (i + 1) % rim_segments
        count = len(section)
        for k in range(count):
            m = (k + 1) % count
            face = builder.bm.faces.new([rings[i][k], rings[j][k], rings[j][m], rings[i][m]])
            face.material_index = rim_index
            face.smooth = True
    # hub with two flanges, and the axle running through to the bearings
    builder.lathe([(0.0, -0.3), (0.32, -0.3), (0.32, -0.24), (0.2, -0.22), (0.2, 0.22), (0.32, 0.24), (0.32, 0.3), (0.0, 0.3)],
                  'wheel_iron', sides=16, axis='y')
    builder.lathe([(0.0, -0.95), (0.1, -0.95), (0.1, 0.95), (0.0, 0.95)], 'wheel_iron', sides=12, axis='y')
    # spokes: 16, alternating between the two flanges, so they are dished like a real sheave
    spokes = 16
    for k in range(spokes):
        angle = 2 * math.pi * (k + 0.5) / spokes
        c, s = math.cos(angle), math.sin(angle)
        flange = -0.26 if k % 2 == 0 else 0.26
        builder.beam((0.28 * c, flange, 0.28 * s), ((radius - 0.15) * c, flange * 0.15, (radius - 0.15) * s), 0.075, 0.05, 'wheel_iron', up=(0, 1, 0))
    # a ring of tie bars half-way out, as on many sheaves
    tie_radius = radius * 0.55
    for k in range(spokes):
        a0, a1 = 2 * math.pi * (k + 0.5) / spokes, 2 * math.pi * (k + 1.5) / spokes
        builder.rod((tie_radius * math.cos(a0), 0, tie_radius * math.sin(a0)), (tie_radius * math.cos(a1), 0, tie_radius * math.sin(a1)), 0.022, 'wheel_iron', sides=6)
    wheel = builder.finish(name, 'colliery', location=centre, bevel=0.006)
    return wheel


def build_heapstead():
    """The heapstead: the brick building at the foot of the headframe round the shaft top, with a
    slate roof, a tall arched opening onto the pit bank and boarded doors."""
    base_z = COLLIERY_GROUND
    builder = MeshBuilder()
    x0, x1, y0, y1 = -5.8, 5.8, HEADFRAME_Y - 4.4, HEADFRAME_Y + 5.0
    height = 6.5
    builder.box((x0, y0, base_z - 0.5), (x1, y1, base_z + height), 'colliery_brick')
    builder.prism([(x0 - 0.01, base_z + height - 0.01), (x1 + 0.01, base_z + height - 0.01), (0, base_z + height + 3.0)], y0, y1, 'colliery_brick', axis='y')
    walls = builder.finish('heapstead_walls', 'colliery')
    # the big arched opening facing the street, and two windows
    cutters = [((-1.8, y0 - 0.5, base_z), (1.8, y0 + 0.6, base_z + 4.4))]
    cut_openings(walls, cutters)
    remap_uv(walls)
    trim = MeshBuilder()
    # dark inside of the opening and a stone arch head (voussoirs suggested by a deep lintel)
    trim.box((-1.8, y0 + 0.5, base_z), (1.8, y0 + 0.6, base_z + 4.4), 'interior_dark')
    trim.box((-2.2, y0 - 0.08, base_z + 4.4), (2.2, y0 + 0.1, base_z + 5.0), 'dressed_stone')
    for side in (-1, 1):
        trim.box((side * 1.8 - 0.2, y0 - 0.06, base_z), (side * 1.8 + 0.2, y0 + 0.1, base_z + 4.4), 'dressed_stone')
    # boarded doors folded back against the reveal
    trim.box((-1.78, y0 + 0.12, base_z), (-1.7, y0 + 0.48, base_z + 4.0), 'boarded_blue')
    trim.box((1.7, y0 + 0.12, base_z), (1.78, y0 + 0.48, base_z + 4.0), 'boarded_blue')
    # roof slopes
    pitch = math.atan2(3.0, (x1 - x0) / 2)
    for direction in (-1, 1):
        eaves = (direction * ((x1 - x0) / 2 + 0.3), base_z + height - 0.3 * math.tan(pitch))
        ridge = (0.0, base_z + height + 3.06)
        outline = [eaves, ridge, (ridge[0], ridge[1] + 0.08), (eaves[0], eaves[1] + 0.08)]
        faces = trim.prism(outline, y0 - 0.3, y1 + 0.3, 'roof_slate', axis='y')
        for face in faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[trim.uv_layer].uv = (co.y / 3.0, math.hypot(co.x - eaves[0], co.z - eaves[1]) / 3.0)
            trim.explicit_uv_faces.add(face)
    # a round stone-ringed window high in the gable, with a cast-iron cross of glazing bars
    vent_centre = (0.0, y0 - 0.05, base_z + height + 1.2)
    trim.lathe([(0.55, -0.1), (0.78, -0.1), (0.78, 0.12), (0.55, 0.12)], 'dressed_stone', sides=20, centre=vent_centre, axis='y')
    trim.lathe([(0.0, -0.03), (0.56, -0.03), (0.56, -0.01), (0.0, -0.01)], 'interior_dark', sides=20, centre=vent_centre, axis='y')
    trim.box((-0.56, y0 - 0.13, vent_centre[2] - 0.03), (0.56, y0 - 0.09, vent_centre[2] + 0.03), 'cast_iron')
    trim.box((-0.03, y0 - 0.13, vent_centre[2] - 0.56), (0.03, y0 - 0.09, vent_centre[2] + 0.56), 'cast_iron')
    # a louvred vent on the ridge
    trim.box((-0.6, y0 + 2.0, base_z + height + 3.0), (0.6, y0 + 4.0, base_z + height + 3.6), 'boarded_blue')
    trim.box((-0.75, y0 + 1.9, base_z + height + 3.6), (0.75, y0 + 4.1, base_z + height + 3.7), 'roof_slate')
    trim.finish('heapstead_trim', 'colliery', bevel=0.01)


def build_engine_house():
    """The winding engine house to the left of the headframe: a tall brick hall with a slate roof,
    stone quoins and band courses, tall round-headed windows with cast-iron glazing bars (two of
    them lit), a pair of boarded doors, and a small lean-to boiler house beside it."""
    base_z = COLLIERY_GROUND
    x0, x1, y0, y1 = ENGINE_HOUSE
    height = 10.5
    builder = MeshBuilder()
    builder.box((x0, y0, base_z - 0.5), (x1, y1, base_z + height), 'colliery_brick')
    # gable facing the street (ridge runs along y), so the front shows a big gable end
    builder.prism([(x0 - 0.01, base_z + height - 0.01), (x1 + 0.01, base_z + height - 0.01), ((x0 + x1) / 2, base_z + height + 4.2)],
                  y0, y1, 'colliery_brick', axis='y')
    walls = builder.finish('engine_house_walls', 'colliery')
    # tall round-headed windows: three on the front gable, three on the side facing the headframe
    window_width, sill, spring = 1.5, 2.2, 7.4
    front_xs = [x0 + 2.5, (x0 + x1) / 2, x1 - 2.5]
    side_ys = [y0 + 2.0, (y0 + y1) / 2, y1 - 2.0]
    cutter_builder = MeshBuilder()
    for wx in front_xs:
        cutter_builder.box((wx - window_width / 2, y0 - 0.5, base_z + sill), (wx + window_width / 2, y0 + 0.3, base_z + spring), 'interior_dark')
        cutter_builder.lathe([(0.0, -0.5), (window_width / 2, -0.5), (window_width / 2, 0.3), (0.0, 0.3)], 'interior_dark', sides=24,
                             centre=(wx, y0, base_z + spring), axis='y')
    for wy in side_ys:
        cutter_builder.box((x1 - 0.3, wy - window_width / 2, base_z + sill), (x1 + 0.5, wy + window_width / 2, base_z + spring), 'interior_dark')
    # door opening in the front gable, under the middle window
    cutter_builder.box((front_xs[1] - 1.1, y0 - 0.5, base_z), (front_xs[1] + 1.1, y0 + 0.3, base_z + 1.9), 'interior_dark')
    cutter = cutter_builder.finish('engine_house_cutter', 'cutters')
    for wy in side_ys:
        side_head = MeshBuilder()
        side_head.lathe([(0.0, -0.5), (window_width / 2, -0.5), (window_width / 2, 0.3), (0.0, 0.3)], 'interior_dark', sides=24, axis='y')
        side_head_object = side_head.finish('engine_side_head', 'cutters', location=(x1, wy, base_z + spring), rotation_z=math.pi / 2)
        modifier = walls.modifiers.new('side_head', 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.object = side_head_object
        modifier.solver = 'EXACT'
        apply_all_modifiers(walls)
        bpy.data.objects.remove(side_head_object, do_unlink=True)
    modifier = walls.modifiers.new('openings', 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.object = cutter
    modifier.solver = 'EXACT'
    apply_all_modifiers(walls)
    bpy.data.objects.remove(cutter, do_unlink=True)
    remap_uv(walls)
    trim = MeshBuilder()
    windows_glass = MeshBuilder()

    def arched_window(centre_u, plane, facing):
        """Glass, cast-iron glazing bars (verticals and horizontals stopping at the arch) and a
        stone sill and arch ring for one round-headed window. plane: the wall coordinate (y for
        the front gable, x for the side). facing: 'front' (faces -y) or 'side' (faces +x)."""
        half = window_width / 2

        def point(u, depth, z):
            # u runs along the wall, depth into the wall (positive = inside), z up
            if facing == 'front':
                return (u, plane + depth, z)
            return (plane - depth, u, z)

        lit = (facing == 'front' and centre_u == front_xs[0]) or (facing == 'side' and centre_u == side_ys[1])
        glass_name = 'engine_window_glow' if lit else 'window_dark_1'
        # glass: a rectangle up to the springing line and a fan of triangles for the arch
        g = 0.18
        windows_glass.quad([point(centre_u - half, g, base_z + sill), point(centre_u + half, g, base_z + sill),
                            point(centre_u + half, g, base_z + spring), point(centre_u - half, g, base_z + spring)][::(1 if facing == 'front' else -1)],
                           glass_name, uvs=[(0, 0), (1, 0), (1, 0.8), (0, 0.8)][::(1 if facing == 'front' else -1)])
        segments = 12
        for k in range(segments):
            a0, a1 = math.pi * k / segments, math.pi * (k + 1) / segments
            p0 = point(centre_u + half * math.cos(a0), g, base_z + spring + half * math.sin(a0))
            p1 = point(centre_u + half * math.cos(a1), g, base_z + spring + half * math.sin(a1))
            pc = point(centre_u, g, base_z + spring)
            corners = [pc, p0, p1, pc] if facing == 'side' else [pc, p1, p0, pc]
            verts = [windows_glass.bm.verts.new(c) for c in corners[:3]]
            face = windows_glass.bm.faces.new(verts)
            face.material_index = windows_glass.material_index(glass_name)
            for loop in face.loops:
                co = loop.vert.co
                along = (co.x - (centre_u - half)) if facing == 'front' else (co.y - (centre_u - half))
                loop[windows_glass.uv_layer].uv = (along / window_width, 0.8 + 0.2 * (co.z - base_z - spring) / half)
            windows_glass.explicit_uv_faces.add(face)
        # glazing bars: 4 verticals, horizontals every 0.45 m, stopping at the arch
        bar = 0.035
        for k in range(1, 5):
            u = centre_u - half + window_width * k / 5
            du = u - centre_u
            top = base_z + spring + math.sqrt(max(0.0, half * half - du * du))
            a, b = point(u - bar / 2, g - 0.04, base_z + sill), point(u + bar / 2, g + 0.0, top)
            trim.box(tuple(min(a[i], b[i]) for i in range(3)), tuple(max(a[i], b[i]) for i in range(3)), 'cast_iron')
        z = base_z + sill + 0.45
        while z < base_z + spring + half - 0.1:
            reach = half if z <= base_z + spring else math.sqrt(max(0.0, half * half - (z - base_z - spring) ** 2))
            a, b = point(centre_u - reach, g - 0.04, z - bar / 2), point(centre_u + reach, g, z + bar / 2)
            trim.box(tuple(min(a[i], b[i]) for i in range(3)), tuple(max(a[i], b[i]) for i in range(3)), 'cast_iron')
            z += 0.45
        # stone sill
        a, b = point(centre_u - half - 0.15, -0.12, base_z + sill - 0.15), point(centre_u + half + 0.15, 0.2, base_z + sill)
        trim.box(tuple(min(a[i], b[i]) for i in range(3)), tuple(max(a[i], b[i]) for i in range(3)), 'dressed_stone')
        # arch ring of stone voussoirs: 9 blocks round the head, with gaps for joints
        for k in range(9):
            a0 = math.pi * k / 9 + 0.01
            a1 = math.pi * (k + 1) / 9 - 0.01
            inner, outer = half, half + 0.32
            pts = []
            for angle, r in ((a0, inner), (a1, inner), (a1, outer), (a0, outer)):
                pts.append((centre_u + r * math.cos(angle), base_z + spring + r * math.sin(angle)))
            if facing == 'front':
                trim.prism(pts, plane - 0.06, plane + 0.12, 'dressed_stone', axis='y')
            else:
                faces = trim.prism(pts, plane - 0.12, plane + 0.06, 'dressed_stone', axis='x')

    for wx in front_xs:
        arched_window(wx, y0, 'front')
    for wy in side_ys:
        arched_window(wy, x1, 'side')
    # quoins: alternating long and short stones up the corners
    z = base_z
    k = 0
    while z < base_z + height - 0.1:
        long_side = 0.7 if k % 2 == 0 else 0.4
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1)):
            trim.box((min(cx, cx + sx * long_side) - (0.04 if sx > 0 else -0.0), cy - 0.04 if sy > 0 else cy - 0.4, z + 0.01),
                     (max(cx, cx + sx * long_side) + (0.04 if sx < 0 else 0.0), cy + 0.4 if sy > 0 else cy + 0.04, z + 0.33), 'dressed_stone')
        z += 0.34
        k += 1
    # band courses and a stone gable coping with kneelers
    for band_z in (base_z + 1.9, base_z + height - 0.3):
        trim.box((x0 - 0.06, y0 - 0.06, band_z), (x1 + 0.06, y1 + 0.06, band_z + 0.2), 'dressed_stone')
    for side in (-1, 1):
        start = Vector((x0 if side < 0 else x1, y0 - 0.1, base_z + height))
        apex = Vector(((x0 + x1) / 2, y0 - 0.1, base_z + height + 4.2))
        trim.beam(start + Vector((0, 0, 0.1)), apex + Vector((0, 0, 0.1)), 0.45, 0.3, 'dressed_stone', up=(0, -1, 0))
    # boarded double doors, set in the opening
    trim.box((front_xs[1] - 1.1, y0 + 0.12, base_z), (front_xs[1] + 1.1, y0 + 0.2, base_z + 1.9), 'boarded_green')
    trim.box((front_xs[1] - 1.3, y0 - 0.05, base_z + 1.9), (front_xs[1] + 1.3, y0 + 0.1, base_z + 2.15), 'dressed_stone')
    # roof slopes
    pitch = math.atan2(4.2, (x1 - x0) / 2)
    for direction in (-1, 1):
        eaves = ((x0 + x1) / 2 + direction * ((x1 - x0) / 2 + 0.35), base_z + height - 0.35 * math.tan(pitch))
        ridge = ((x0 + x1) / 2, base_z + height + 4.25)
        outline = [eaves, ridge, (ridge[0], ridge[1] + 0.09), (eaves[0], eaves[1] + 0.09)]
        faces = trim.prism(outline, y0 - 0.25, y1 + 0.3, 'roof_slate', axis='y')
        for face in faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[trim.uv_layer].uv = (co.y / 3.0, math.hypot(co.x - eaves[0], co.z - eaves[1]) / 3.0)
            trim.explicit_uv_faces.add(face)
    trim.rod(((x0 + x1) / 2, y0 - 0.25, base_z + height + 4.33), ((x0 + x1) / 2, y1 + 0.3, base_z + height + 4.33), 0.13, 'ridge_clay', sides=10)
    # the boiler house: a lower lean-to on the far side with a corrugated look in slate
    trim.box((x0 - 6.0, y0 + 1.0, base_z - 0.5), (x0, y1, base_z + 5.0), 'colliery_brick')
    lean = [(x0 - 6.3, base_z + 4.7), (x0 + 0.05, base_z + 6.6), (x0 + 0.05, base_z + 6.7), (x0 - 6.3, base_z + 4.8)]
    faces = trim.prism(lean, y0 + 0.8, y1 + 0.2, 'roof_slate', axis='y')
    trim.finish('engine_house_trim', 'colliery', bevel=0.01)
    windows_glass.finish('engine_house_glass', 'colliery')
    marker('engine_house_door', (front_xs[1], y0 - 1.0, base_z))


def build_chimney():
    """The colliery chimney: a square stone-capped brick pedestal, then a tall round brick shaft
    tapering upwards, iron bands every few metres, and a corbelled cap with a soot-black lip."""
    base_z = COLLIERY_GROUND
    cx, cy = CHIMNEY_XY
    builder = MeshBuilder()
    builder.box((cx - 2.4, cy - 2.4, base_z - 0.5), (cx + 2.4, cy + 2.4, base_z + 6.0), 'colliery_brick')
    builder.box((cx - 2.6, cy - 2.6, base_z + 6.0), (cx + 2.6, cy + 2.6, base_z + 6.5), 'dressed_stone')
    builder.box((cx - 2.6, cy - 2.6, base_z - 0.5), (cx + 2.6, cy + 2.6, base_z + 0.8), 'dressed_stone')
    shaft_height = 34.0
    profile = [(0.0, 6.5), (1.9, 6.5)]
    steps = 12
    for k in range(steps + 1):
        t = k / steps
        profile.append((1.9 - 0.75 * t, 6.5 + shaft_height * t))
    profile += [(1.35, 6.5 + shaft_height + 0.4), (1.45, 6.5 + shaft_height + 0.9), (1.45, 6.5 + shaft_height + 1.3),
                (1.0, 6.5 + shaft_height + 1.3), (1.0, 6.5 + shaft_height - 2.0)]
    shaft_faces = builder.lathe(profile, 'colliery_brick', sides=28, centre=(cx, cy, base_z))
    # iron bands
    for k in range(1, 8):
        t = k / 8
        radius = 1.9 - 0.75 * t + 0.03
        z = base_z + 6.5 + shaft_height * t
        builder.lathe([(radius, -0.06), (radius + 0.03, -0.04), (radius + 0.03, 0.04), (radius, 0.06)], 'cast_iron', sides=28, centre=(cx, cy, z))
    chimney = builder.finish('colliery_chimney', 'colliery')
    # brick texture wrapped round the shaft: u along the circumference, v up
    mesh = chimney.data
    layer = mesh.uv_layers.active
    for polygon in mesh.polygons:
        material = mesh.materials[polygon.material_index]
        tile = material.get('tile_metres', 1.0) or 1.0
        if abs(polygon.normal.z) > 0.7:
            continue
        for loop_index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            dx, dy = co.x - cx, co.y - cy
            radius = math.hypot(dx, dy)
            if radius < 2.0 and co.z > base_z + 6.4:
                angle = math.atan2(dy, dx)
                layer.data[loop_index].uv = (angle * 1.6 / tile, co.z / tile)
    # fix the seam where the angle wraps: shift u on faces that straddle it
    for polygon in mesh.polygons:
        us = [layer.data[i].uv.x for i in polygon.loop_indices]
        if max(us) - min(us) > 2.0:
            for i in polygon.loop_indices:
                if layer.data[i].uv.x < 0:
                    layer.data[i].uv.x += 2 * math.pi * 1.6 / 1.5
    marker('chimney_smoke_top', (cx, cy, base_z + 6.5 + shaft_height + 1.4))


def build_second_winding_house():
    """A smaller winding house to the right of the headframe, for the second wheel's rope."""
    base_z = COLLIERY_GROUND
    x0, x1, y0, y1 = 18.0, 26.0, HEADFRAME_Y - 3.0, HEADFRAME_Y + 5.0
    builder = MeshBuilder()
    builder.box((x0, y0, base_z - 0.5), (x1, y1, base_z + 7.0), 'colliery_brick')
    builder.prism([(x0 - 0.01, base_z + 6.99), (x1 + 0.01, base_z + 6.99), ((x0 + x1) / 2, base_z + 9.6)], y0, y1, 'colliery_brick', axis='y')
    walls = builder.finish('second_winding_house_walls', 'colliery')
    cut_openings(walls, [((x0 + 1.4, y0 - 0.5, base_z + 2.0), (x0 + 2.6, y0 + 0.3, base_z + 5.2)),
                         ((x1 - 2.6, y0 - 0.5, base_z + 2.0), (x1 - 1.4, y0 + 0.3, base_z + 5.2))])
    remap_uv(walls)
    trim = MeshBuilder()
    glass = MeshBuilder()
    for wx in (x0 + 2.0, x1 - 2.0):
        glass.quad([(wx - 0.6, y0 + 0.2, base_z + 2.0), (wx + 0.6, y0 + 0.2, base_z + 2.0), (wx + 0.6, y0 + 0.2, base_z + 5.2), (wx - 0.6, y0 + 0.2, base_z + 5.2)],
                   'window_dark_2', uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
        for k in range(1, 3):
            trim.box((wx - 0.6 + 1.2 * k / 3 - 0.02, y0 + 0.1, base_z + 2.0), (wx - 0.6 + 1.2 * k / 3 + 0.02, y0 + 0.16, base_z + 5.2), 'cast_iron')
        for k in range(1, 6):
            trim.box((wx - 0.6, y0 + 0.1, base_z + 2.0 + 3.2 * k / 6 - 0.02), (wx + 0.6, y0 + 0.16, base_z + 2.0 + 3.2 * k / 6 + 0.02), 'cast_iron')
        trim.box((wx - 0.75, y0 - 0.1, base_z + 1.85), (wx + 0.75, y0 + 0.15, base_z + 2.0), 'dressed_stone')
        trim.box((wx - 0.8, y0 - 0.06, base_z + 5.2), (wx + 0.8, y0 + 0.1, base_z + 5.55), 'dressed_stone')
    pitch = math.atan2(2.6, (x1 - x0) / 2)
    for direction in (-1, 1):
        eaves = ((x0 + x1) / 2 + direction * ((x1 - x0) / 2 + 0.3), base_z + 7.0 - 0.3 * math.tan(pitch))
        ridge = ((x0 + x1) / 2, base_z + 9.65)
        outline = [eaves, ridge, (ridge[0], ridge[1] + 0.08), (eaves[0], eaves[1] + 0.08)]
        faces = trim.prism(outline, y0 - 0.25, y1 + 0.25, 'roof_slate', axis='y')
        for face in faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[trim.uv_layer].uv = (co.y / 3.0, math.hypot(co.x - eaves[0], co.z - eaves[1]) / 3.0)
            trim.explicit_uv_faces.add(face)
    trim.finish('second_winding_house_trim', 'colliery', bevel=0.01)
    glass.finish('second_winding_house_glass', 'colliery')


def build_spoil_heap_and_hills():
    """The black spoil heap (a long tipped ridge with gullies) behind the colliery, a smaller
    older heap to the right, and dark moorland hills on the skyline."""
    noise_random = np.random.default_rng(11)

    def heap(name, peak, ridge_end, radius, height, material_name, cells=56, roughness=0.05):
        """A tipped heap: a cone round its peak, drawn out along a falling ridge to ridge_end, with
        straight tipped sides (about 31 degrees), gullies down the flanks and a lumpy surface."""
        builder = MeshBuilder()
        peak, ridge_end = np.array(peak, float), np.array(ridge_end, float)
        low = np.minimum(peak, ridge_end) - radius
        high = np.maximum(peak, ridge_end) + radius
        xs = np.linspace(low[0], high[0], cells)
        ys = np.linspace(low[1], high[1], int(cells * 0.6))
        ridge = ridge_end - peak
        ridge_length2 = float(ridge @ ridge)
        gully_phase = noise_random.random() * 6
        grid = []
        for y in ys:
            row = []
            for x in xs:
                point = np.array([x, y])
                t = float(np.clip((point - peak) @ ridge / ridge_length2, 0, 1))
                distance = float(np.linalg.norm(point - (peak + t * ridge)))
                top = height * (1 - 0.45 * t)
                local_radius = radius * (top / height)
                shape = max(0.0, 1 - distance / local_radius)
                angle = math.atan2(y - peak[1], x - peak[0])
                gullies = 1 - 0.1 * (0.5 + 0.5 * math.sin(angle * 9 + gully_phase)) * (1 - shape)
                bumps = 1 + roughness * (noise_random.random() - 0.5)
                z = top * min(1.0, shape * 1.04) ** 1.1 * gullies * bumps
                row.append(builder.bm.verts.new((float(x), float(y), COLLIERY_GROUND - 0.3 + z)))
            grid.append(row)
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                face = builder.bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
                face.material_index = builder.material_index(material_name)
                face.smooth = True
        return builder.finish(name, 'colliery')

    heap('spoil_heap_main', (-10.0, 165.0), (50.0, 185.0), 52.0, 32.0, 'spoil_heap')
    heap('spoil_heap_old', (48.0, 135.0), (75.0, 150.0), 28.0, 14.0, 'spoil_heap')
    hill_random = np.random.default_rng(4)
    for index, (cy, height, spread) in enumerate(((330.0, 55.0, 700.0), (420.0, 85.0, 900.0))):
        builder = MeshBuilder()
        xs = np.linspace(-spread / 2, spread / 2, 60)
        rows = []
        phase = hill_random.random() * 10
        for depth in (-60.0, 0.0, 60.0):
            row = []
            for x in xs:
                crest = height * (0.6 + 0.25 * math.sin(x / 90 + phase) + 0.15 * math.sin(x / 37 + phase * 2))
                z = COLLIERY_GROUND - 2 + (crest if depth == 0.0 else crest * 0.3)
                row.append(builder.bm.verts.new((x, cy + depth, z)))
            rows.append(row)
        for j in range(2):
            for i in range(len(xs) - 1):
                face = builder.bm.faces.new([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]])
                face.material_index = builder.material_index('moor')
                face.smooth = True
        builder.finish(f'moorland_hills_{index}', 'colliery')


def build_sky_dome():
    """A low dome over the whole set with the dusk sky picture on its inside."""
    builder = MeshBuilder()
    radius = 1200.0
    segments, rings = 48, 14
    centre = Vector((0, 40, -40))
    verts = []
    for r in range(rings + 1):
        elevation = math.radians(-8 + 98 * r / rings)
        row = []
        for s in range(segments + 1):
            azimuth = math.pi + 2 * math.pi * s / segments    # the picture's seam behind the camera
            row.append(builder.bm.verts.new(centre + Vector((radius * math.cos(elevation) * math.sin(azimuth),
                                                              radius * math.cos(elevation) * math.cos(azimuth),
                                                              radius * math.sin(elevation) * 0.55))))
        verts.append(row)
    index = builder.material_index('sky_dome_glow')
    for r in range(rings):
        for s in range(segments):
            face = builder.bm.faces.new([verts[r][s], verts[r + 1][s], verts[r + 1][s + 1], verts[r][s + 1]])
            face.material_index = index
            face.smooth = True
            for loop in face.loops:
                rr = r + (1 if loop.vert in (verts[r + 1][s], verts[r + 1][s + 1]) else 0)
                ss = s + (1 if loop.vert in (verts[r][s + 1], verts[r + 1][s + 1]) else 0)
                elevation = -8 + 98 * rr / rings
                # picture: v = 1 at the top (zenith), 0.5 at the horizon
                loop[builder.uv_layer].uv = (ss / segments * 3, 0.5 + 0.5 * max(-1.0, elevation / 90.0) if elevation >= 0 else 0.5 + elevation / 90.0)
            builder.explicit_uv_faces.add(face)
    dome = builder.finish('sky_dome', 'sky')
    dome.visible_shadow = False
    return dome


# ==================================================================================== camera & lights

def build_cameras():
    eye_z = road_height(0.0, CAMERA_Y) + CAMERA_EYE_HEIGHT
    rotation = Euler((math.radians(90 + CAMERA_PITCH_UP), 0.0, 0.0), 'XYZ')
    cameras = {}
    for name, x in (('main_camera', 0.0), ('side_camera', 2.0)):
        data = bpy.data.cameras.new(name)
        data.sensor_fit = 'VERTICAL'
        data.angle_y = math.radians(CAMERA_VERTICAL_FOV)
        data.clip_start, data.clip_end = CAMERA_NEAR, CAMERA_FAR
        camera = bpy.data.objects.new(name, data)
        camera.location = (x, CAMERA_Y, eye_z)
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = rotation.to_quaternion()
        collection('cameras').objects.link(camera)
        cameras[name] = camera
    scene.camera = cameras['main_camera']
    scene.render.resolution_x, scene.render.resolution_y = FRAME_WIDTH, FRAME_HEIGHT
    return cameras


def write_camera_json(camera):
    location = camera.location
    quaternion = camera.rotation_quaternion
    # three.js: the whole world is turned -90 degrees about x (Blender z-up -> y-up). A camera's own
    # axes mean the same in both (look down -z, +y up), so only the world turn applies:
    # q_three = q_world_turn @ q_blender (this matches the camera node the glTF exporter writes).
    world_turn = Quaternion((1, 0, 0), math.radians(-90))
    three_quaternion = world_turn @ quaternion
    data = {
        'about': 'Main camera of the pit village street set (street.glb). Blender space is z-up; '
                 'three.js space is y-up: positions convert as (x, y, z) -> (x, z, -y); the camera quaternion converts as '
                 'q_three = rotation(-90 degrees about x) * q_blender, because a camera looks down its own -z with +y up in both. '
                 '(For ordinary objects the glTF exporter instead writes (w, x, z, -y), since their vertices are converted too.) '
                 'The camera is also inside street.glb as the node "main_camera" (and "side_camera", 2 m to the right).',
        'frame': {'width': FRAME_WIDTH, 'height': FRAME_HEIGHT, 'aspect': FRAME_WIDTH / FRAME_HEIGHT},
        'vertical_fov_degrees': CAMERA_VERTICAL_FOV,
        'horizontal_fov_degrees': math.degrees(2 * math.atan(math.tan(math.radians(CAMERA_VERTICAL_FOV / 2)) * FRAME_WIDTH / FRAME_HEIGHT)),
        'near': CAMERA_NEAR,
        'far': CAMERA_FAR,
        'blender': {
            'location': [round(v, 5) for v in location],
            'rotation_quaternion_wxyz': [round(v, 6) for v in quaternion],
            'rotation_euler_xyz_degrees': [round(math.degrees(v), 4) for v in quaternion.to_euler('XYZ')],
        },
        'threejs': {
            'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
            'quaternion_xyzw': [round(three_quaternion.x, 6), round(three_quaternion.y, 6), round(three_quaternion.z, 6), round(three_quaternion.w, 6)],
            'rotation_euler_xyz_degrees': [round(math.degrees(v), 4) for v in three_quaternion.to_euler('XYZ')],
            'fov': CAMERA_VERTICAL_FOV,
        },
        'set_notes': {
            'street_slope_degrees': 4.0,
            'street_runs_along': 'Blender +y (three.js -z), uphill',
            'street_half_width': STREET_HALF_WIDTH,
            'house_front_x': HOUSE_FRONT_X,
            'ground_height_formula': 'z = min(y, 76) * tan(4 deg) (channel line); pavement top = that + 0.13; road crown + 0.08',
            'winding_wheels': 'nodes winding_wheel_left and winding_wheel_right, each with its origin on its own axle and no rotation; '
                              'the axles run along Blender y, which is three.js -z, so turn them with wheel.rotation.z in three.js '
                              '(rotation_euler y in Blender). The wheels face the camera; ropes are a separate static object (winding_ropes).',
            'markers': 'empties: lamp_0..lamp_4 (lamp heads), <row>_cottage_NN_doorway, <row>_cottage_NN_chimney_top, '
                       'chimney_smoke_top (colliery chimney), wheel_left_axle, wheel_right_axle, engine_house_door',
            'glowing_material_names': 'window_lit_glow_0..2 (lit cottage windows), engine_window_glow, lamp_glass_glow, sky_dome_glow',
        },
    }
    with open(CAMERA_JSON_PATH, 'w') as handle:
        json.dump(data, handle, indent=2)
    return data


def preview_lighting():
    world = bpy.data.worlds.new('dusk_world')
    world.use_nodes = True
    background = world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (0.05, 0.075, 0.1, 1)
    background.inputs['Strength'].default_value = 1.4
    scene.world = world
    # last of the daylight: a soft cool key from high behind the colliery, a little to the left
    sun = bpy.data.lights.new('dusk_skylight', 'SUN')
    sun.energy = 0.35
    sun.color = (0.62, 0.72, 0.9)
    sun.angle = math.radians(12)
    sun_object = bpy.data.objects.new('dusk_skylight', sun)
    sun_object.rotation_euler = (math.radians(-62), math.radians(-25), 0)
    collection('preview_lights').objects.link(sun_object)
    # a dim warm glow low behind the heap, from the sunken sun
    glow = bpy.data.lights.new('afterglow', 'SUN')
    glow.energy = 0.25
    glow.color = (1.0, 0.62, 0.36)
    glow_object = bpy.data.objects.new('afterglow', glow)
    glow_object.rotation_euler = (math.radians(-84), 0, math.radians(180))
    collection('preview_lights').objects.link(glow_object)
    # engine house lit windows spill
    x0, x1, y0, y1 = ENGINE_HOUSE
    for name, location in (('engine_house_light_front', (x0 + 2.5, y0 - 1.2, COLLIERY_GROUND + 4.0)),
                           ('engine_house_light_side', (x1 + 1.2, (y0 + y1) / 2, COLLIERY_GROUND + 4.0))):
        light = bpy.data.lights.new(name, 'POINT')
        light.energy = 400.0
        light.color = (1.0, 0.66, 0.34)
        light_object = bpy.data.objects.new(name, light)
        light_object.location = location
        collection('preview_lights').objects.link(light_object)


def render_previews(cameras, folder):
    os.makedirs(folder, exist_ok=True)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = PREVIEW_SAMPLES
    try:
        scene.eevee.use_shadows = True
        scene.eevee.use_raytracing = False
    except AttributeError:
        pass
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.6
    for name, file_name in (('main_camera', 'preview.png'), ('side_camera', 'preview_side.png')):
        scene.camera = cameras[name]
        scene.render.filepath = os.path.join(folder, file_name)
        bpy.ops.render.render(write_still=True)
        print('rendered', scene.render.filepath)
    scene.camera = cameras['main_camera']
    scene.render.resolution_x, scene.render.resolution_y = FRAME_WIDTH, FRAME_HEIGHT


def count_triangles():
    graph = bpy.context.evaluated_depsgraph_get()
    total = 0
    per_collection = {}
    for part in scene.objects:
        if part.type != 'MESH':
            continue
        mesh = part.evaluated_get(graph).to_mesh()
        mesh.calc_loop_triangles()
        count = len(mesh.loop_triangles)
        part.evaluated_get(graph).to_mesh_clear()
        total += count
        name = part.users_collection[0].name if part.users_collection else 'none'
        per_collection[name] = per_collection.get(name, 0) + count
    return total, per_collection


# ==================================================================================== main

def main():
    make_materials()
    build_street()
    build_ground()
    lit = 0
    # right side: rubble sandstone; left side: dark red brick. 8 cottages, a back lane, 6 more.
    lit += place_cottage_row(1, -0.5, 8, 'cottage_stone', 'right_row_a')
    lit += place_cottage_row(1, -0.5 + 8 * COTTAGE_WIDTH + 4.0, 6, 'cottage_stone', 'right_row_b')
    lit += place_cottage_row(-1, -0.5, 8, 'cottage_brick', 'left_row_a')
    lit += place_cottage_row(-1, -0.5 + 8 * COTTAGE_WIDTH + 4.0, 6, 'cottage_brick', 'left_row_b')
    place_gas_lamps()
    build_headframe()
    build_heapstead()
    build_engine_house()
    build_second_winding_house()
    build_chimney()
    build_spoil_heap_and_hills()
    build_sky_dome()
    # hide the kits (their meshes are used by the placed copies)
    for kit_name in ('cottage_kit', 'lamp_kit'):
        kit = collection(kit_name)
        for part in list(kit.objects):
            kit.objects.unlink(part)
        bpy.data.collections.remove(kit)
    if 'cutters' in collections:
        bpy.data.collections.remove(collections['cutters'])
    cameras = build_cameras()
    preview_lighting()
    total, per_collection = count_triangles()
    print('TRIANGLES', total, per_collection, 'lit windows', lit)
    write_camera_json(cameras['main_camera'])
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    if PREVIEW_FOLDER:
        render_previews(cameras, PREVIEW_FOLDER)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    # the .glb: meshes, materials, textures, cameras and named empties; lights are left out (the
    # stage lights the set itself)
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB', export_yup=True, export_apply=True,
                              export_cameras=True, export_lights=False, export_extras=True,
                              export_image_format='AUTO', export_materials='EXPORT')
    print('wrote', BLEND_PATH, GLB_PATH, CAMERA_JSON_PATH)


main()
