# What this does: the shared tools for building the Works' two factories and the far town at true size in
# Blender by script (build_factories.py, build_far_town.py), and for lighting the factories' windows when
# a plate is drawn (an assemble script for a Works view imports this file and calls set_windows and
# set_doorway). Run inside Blender; it does nothing by itself.
#
# What it gives:
#   - settings read after "--" on the command line (option, flag) and the kit's folders
#   - a fresh, empty scene (with Blender's .blend1 backup copies turned off)
#   - materials wearing Poly Haven surfaces at their real size (a brick is a brick's size on every
#     wall), tinted; and the glass materials, each window type twice, lit and dark (pictures painted by
#     paint_works_pictures.py, kept outside the .blend files)
#   - MeshBuilder: boxes, beams, rods, turned shapes, flat outlines pushed out, and roof slopes, gathered
#     into one object with several materials; texture coordinates are given at the end from where each
#     face lies in the set, so surfaces line up across parts (the same idea as the pit village street's
#     builder in pit-village/build_street.py, which cannot be imported because it builds on import)
#   - one root empty per model, named groups under it, and the export of that root alone to .glb
#   - set_windows / set_doorway: light a factory's windows by thirds (steps 1, 2 and 3), or none, and its
#     loading doorway, by swapping each glass piece between its lit and dark material
#
# The Works' layout (metres): x across the lane (0 on the lane's centre line, No. 1 at minus x, No. 2 at
# plus x), y away from the lane (0 at the works wall's face on the lane side), z up (0 at the ground).
# Blender's z-up becomes three.js's y-up in the .glb: a point (x, y, z) here is (x, z, -y) in three.js.

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_FOLDER = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
PIT_VILLAGE_TEXTURES = os.path.join(KIT_FOLDER, 'assets', 'models', 'pit-village', 'textures')
CHAPTER_TEXTURES = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers', 'textures')
WORKS_FOLDER = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers', 'works')
WORKS_TEXTURES = os.path.join(WORKS_FOLDER, 'textures')

# the Poly Haven surfaces used (all CC0), with the size one picture covers in metres (Poly Haven's own
# measurements) and the folder they are kept in
SURFACES = {
    'castle_brick_02_red': (1.5, PIT_VILLAGE_TEXTURES),
    'red_brick': (1.4, PIT_VILLAGE_TEXTURES),
    'white_sandstone_bricks': (2.0, CHAPTER_TEXTURES),
    'large_red_bricks': (2.0, CHAPTER_TEXTURES),
    'large_sandstone_blocks': (3.0, PIT_VILLAGE_TEXTURES),
    'roof_slates_03': (3.0, PIT_VILLAGE_TEXTURES),
    'rusty_metal_02': (1.0, PIT_VILLAGE_TEXTURES),
    'grey_plaster_02': (1.0, PIT_VILLAGE_TEXTURES),
    'distressed_painted_planks': (1.6, PIT_VILLAGE_TEXTURES),
    'square_cobblestone': (2.0, PIT_VILLAGE_TEXTURES),
    'muddy_tracks': (2.25, PIT_VILLAGE_TEXTURES),
    'stone_brick_wall_001': (2.5, PIT_VILLAGE_TEXTURES),
}

# the glass pictures (paint_works_pictures.py): each holds four windows side by side
GLASS_TYPES = ('mill-window-narrow', 'mill-window-wide', 'north-light', 'lantern-light', 'doorway-inside')
GLASS_VARIANTS = {'doorway-inside': 1}          # every other type: 4 windows side by side
LIT_GLOW = 1.4                                  # how strongly lit glass glows: warm, not white (the pit village's
                                                # lit windows glow 4, but their pictures are much darker)


# ------------------------------------------------------------------------------------------ settings

def arguments():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def option(name, default=None):
    given = arguments()
    return given[given.index(name) + 1] if name in given else default


def flag(name):
    return name in arguments()


# ------------------------------------------------------------------------------------------- scene

def empty_scene():
    """A new empty scene in metres, with no .blend1 backup copies when saving."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    MATERIALS.clear()
    IMAGES.clear()
    return scene


def collection(name):
    """A collection under the scene's own (made the first time it is asked for)."""
    found = bpy.data.collections.get(name)
    if found is None:
        found = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(found)
    return found


def empty(name, location=(0, 0, 0), parent=None, collection_name='markers', size=0.5):
    """A named empty: a root, a group, or a spot the film can find (a chimney's top for smoke)."""
    made = bpy.data.objects.new(name, None)
    made.location = location
    made.empty_display_size = size
    collection(collection_name).objects.link(made)
    if parent is not None:
        made.parent = parent
    return made


# --------------------------------------------------------------------------------------- materials

MATERIALS = {}
IMAGES = {}


def load_image(path, colour_data=True):
    key = (path, colour_data)
    if key not in IMAGES:
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = 'sRGB' if colour_data else 'Non-Color'
        IMAGES[key] = image
    return IMAGES[key]


def surface_material(name, surface, tint=(1, 1, 1), roughness=0.85, metallic=0.0, normal_strength=1.0, tile_metres=None, glow=None):
    """A material wearing a Poly Haven surface at its real size, its colour multiplied by tint
    (written to the .glb as the base colour factor). tile_metres overrides the surface's own size.
    glow (colour, strength): the surface also gives off a little light of its own, its picture times that
    colour, as if lit by a glow the scene's lights don't carry (No. 2's chimneys, lit warm on the side
    toward its own blazing yard); written to the .glb as an emissive picture."""
    if name in MATERIALS:
        return MATERIALS[name]
    size, folder = SURFACES[surface]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    colour = nodes.new('ShaderNodeTexImage')
    colour.image = load_image(os.path.join(folder, f'{surface}_colour.jpg'))
    colour.location = (-700, 300)
    multiply = nodes.new('ShaderNodeMix')
    multiply.data_type = 'RGBA'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs['Factor'].default_value = 1.0
    multiply.inputs[7].default_value = (*tint, 1)
    multiply.location = (-350, 300)
    links.new(colour.outputs['Color'], multiply.inputs[6])
    links.new(multiply.outputs[2], shader.inputs['Base Color'])
    if glow is not None:
        glow_colour, glow_strength = glow
        lit_by = nodes.new('ShaderNodeMix')
        lit_by.data_type = 'RGBA'
        lit_by.blend_type = 'MULTIPLY'
        lit_by.inputs['Factor'].default_value = 1.0
        lit_by.inputs[7].default_value = (*glow_colour, 1)
        lit_by.location = (-350, 0)
        links.new(colour.outputs['Color'], lit_by.inputs[6])
        links.new(lit_by.outputs[2], shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value = glow_strength
    normal_picture = nodes.new('ShaderNodeTexImage')
    normal_picture.image = load_image(os.path.join(folder, f'{surface}_normal.jpg'), colour_data=False)
    normal_picture.location = (-700, -100)
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.inputs['Strength'].default_value = normal_strength
    normal_map.location = (-350, -100)
    links.new(normal_picture.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    material['tile_metres'] = tile_metres or size
    MATERIALS[name] = material
    return material


def plain_material(name, colour, roughness=0.8, metallic=0.0):
    """A material of one plain colour (used only where no surface would show, such as a flue's
    dark mouth)."""
    if name in MATERIALS:
        return MATERIALS[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    material['tile_metres'] = 1.0
    MATERIALS[name] = material
    return material


def glass_material(prefix, glass_type, state):
    """A factory's glass of one type, lit or dark: '<prefix>-<type>-lit' glows with the lit picture,
    '<prefix>-<type>-dark' shows the dusk sky in dark glass. Built from the picture files if it is not
    in the scene already, so it also works on a factory imported from its .glb."""
    name = f'{prefix}-{glass_type}-{state}'
    if name in MATERIALS:
        return MATERIALS[name]
    existing = bpy.data.materials.get(name)
    if existing is not None:
        MATERIALS[name] = existing
        return existing
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    picture = nodes.new('ShaderNodeTexImage')
    picture.image = load_image(os.path.join(WORKS_TEXTURES, f'{glass_type}-{state}.jpg'))
    picture.location = (-500, 200)
    links.new(picture.outputs['Color'], shader.inputs['Base Color'])
    if state == 'lit':
        links.new(picture.outputs['Color'], shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value = LIT_GLOW
        shader.inputs['Roughness'].default_value = 0.4
    else:
        # dull enough that a lamp nearby does not turn a dark window into a bright one: the dusk sky
        # it reflects is painted into the picture
        shader.inputs['Roughness'].default_value = 0.45
        shader.inputs['Specular IOR Level'].default_value = 0.25
    material['tile_metres'] = 0.0      # laid once over each piece by its own coordinates
    material['works_glass'] = glass_type
    material['works_state'] = state
    MATERIALS[name] = material
    return material


# ----------------------------------------------------------------------------------- mesh building

class MeshBuilder:
    """Collects parts into one mesh with several materials. Every point is given in the set's own
    coordinates. Texture coordinates are given at the end, face by face, from where the face lies and
    which way it faces, divided by the material's real size (true scale), unless a part gave its own."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv_layer = self.bm.loops.layers.uv.new('UVMap')
        self.materials = []
        self.explicit_uv_faces = set()
        self.smooth_faces = set()

    def material_index(self, material):
        if material not in self.materials:
            self.materials.append(material)
        return self.materials.index(material)

    def _tag(self, faces, material, smooth=False):
        index = self.material_index(material)
        for face in faces:
            face.material_index = index
            if smooth:
                self.smooth_faces.add(face)
        return faces

    def box(self, minimum, maximum, material, matrix=None):
        """A box from corner minimum to corner maximum (then moved by matrix)."""
        (x0, y0, z0), (x1, y1, z1) = minimum, maximum
        corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if matrix is not None:
            corners = [tuple(matrix @ Vector(corner)) for corner in corners]
        verts = [self.bm.verts.new(corner) for corner in corners]
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return self._tag([self.bm.faces.new([verts[i] for i in quad]) for quad in quads], material)

    def centred_box(self, centre, size, material, matrix=None):
        half = Vector(size) / 2
        return self.box(tuple(Vector(centre) - half), tuple(Vector(centre) + half), material, matrix)

    def beam(self, start, end, width, depth, material, up=(0, 0, 1)):
        """A straight member of rectangular section from start to end (girders, braces, legs)."""
        start, end = Vector(start), Vector(end)
        axis = (end - start).normalized()
        up = Vector(up)
        if abs(axis.dot(up)) > 0.95:
            up = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
        side = axis.cross(up).normalized()
        real_up = side.cross(axis).normalized()
        matrix = Matrix.Translation(start) @ Matrix((side, real_up, axis)).transposed().to_4x4()
        return self.box((-width / 2, -depth / 2, 0), (width / 2, depth / 2, (end - start).length), material, matrix)

    def rod(self, start, end, radius, material, sides=8, end_radius=None):
        """A round bar or pipe from start to end."""
        start, end = Vector(start), Vector(end)
        axis = (end - start).normalized()
        helper = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
        side = axis.cross(helper).normalized()
        other = axis.cross(side).normalized()
        rings = []
        for point, ring_radius in ((start, radius), (end, radius if end_radius is None else end_radius)):
            rings.append([self.bm.verts.new(point + (side * math.cos(2 * math.pi * i / sides) + other * math.sin(2 * math.pi * i / sides)) * ring_radius)
                          for i in range(sides)])
        faces = [self.bm.faces.new([rings[0][i], rings[0][(i + 1) % sides], rings[1][(i + 1) % sides], rings[1][i]]) for i in range(sides)]
        self._tag(faces, material, smooth=True)
        self._tag([self.bm.faces.new(list(reversed(rings[0]))), self.bm.faces.new(rings[1])], material)
        return faces

    def lathe(self, profile, material, centre=(0, 0, 0), sides=24, smooth=True, square=False):
        """A turned shape: profile [(radius, height), ...] from bottom to top spun round an upright
        axis through centre. square=True makes it four-sided instead (a square stack: radius is half
        the side)."""
        centre = Vector(centre)
        count = 4 if square else sides
        rings = []
        for radius, height in profile:
            ring = []
            for i in range(count):
                angle = 2 * math.pi * i / count + (math.pi / 4 if square else 0)
                scale = math.sqrt(2) if square else 1.0
                ring.append(self.bm.verts.new(centre + Vector((math.cos(angle) * radius * scale, math.sin(angle) * radius * scale, height))))
            rings.append(ring)
        faces = []
        for k in range(len(rings) - 1):
            for i in range(count):
                j = (i + 1) % count
                faces.append(self.bm.faces.new([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]))
        self._tag(faces, material, smooth=smooth and not square)
        caps = []
        if profile[0][0] > 0.0001:
            caps.append(self.bm.faces.new(list(reversed(rings[0]))))
        if profile[-1][0] > 0.0001:
            caps.append(self.bm.faces.new(rings[-1]))
        self._tag(caps, material)
        return faces

    def prism(self, outline, push_from, push_to, material, axis='y'):
        """A flat outline pushed from push_from to push_to along an axis. axis 'y': outline in (x, z), like
        a gable seen from the front; 'x': outline in (y, z); 'z': outline in (x, y), like a floor plan."""
        def point(first, second, pushed):
            return (first, pushed, second) if axis == 'y' else (pushed, first, second) if axis == 'x' else (first, second, pushed)
        near = [self.bm.verts.new(point(first, second, push_from)) for first, second in outline]
        far = [self.bm.verts.new(point(first, second, push_to)) for first, second in outline]
        faces = [self.bm.faces.new(near), self.bm.faces.new(list(reversed(far)))]
        for i in range(len(outline)):
            j = (i + 1) % len(outline)
            faces.append(self.bm.faces.new([near[i], near[j], far[j], far[i]]))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return self._tag(faces, material)

    def roof_slope(self, low_start, low_end, high_end, high_start, material, thickness=0.12):
        """A roof slope as a slab: its top face has the corners low_start -> low_end along the eaves and
        high_end -> high_start along the ridge. The covering's courses run along the eaves: the picture's
        across-direction follows the eaves, its up-direction runs up the slope (real size)."""
        corners = [Vector(corner) for corner in (low_start, low_end, high_end, high_start)]
        normal = (corners[1] - corners[0]).cross(corners[3] - corners[0]).normalized()
        if normal.z < 0:
            normal = -normal
        top = [self.bm.verts.new(corner) for corner in corners]
        bottom = [self.bm.verts.new(corner - normal * thickness) for corner in corners]
        tile = material.get('tile_metres', 1.0) or 1.0
        along = (corners[1] - corners[0]).normalized()
        up_slope = (corners[3] - corners[0])
        up_slope = (up_slope - along * up_slope.dot(along)).normalized()
        top_face = self.bm.faces.new(top)
        for loop in top_face.loops:
            offset = loop.vert.co - corners[0]
            loop[self.uv_layer].uv = ((offset.dot(along) + corners[0].x + corners[0].y) / tile, offset.dot(up_slope) / tile)
        self.explicit_uv_faces.add(top_face)
        faces = [top_face, self.bm.faces.new(list(reversed(bottom)))]
        for i in range(4):
            j = (i + 1) % 4
            faces.append(self.bm.faces.new([top[i], bottom[i], bottom[j], top[j]]))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        if top_face.normal.z < 0:
            top_face.normal_flip()
        return self._tag(faces, material)

    def quad(self, corners, material, uvs=None):
        """One flat four-cornered face; uvs: picture coordinates for its corners."""
        face = self.bm.faces.new([self.bm.verts.new(corner) for corner in corners])
        if uvs is not None:
            for loop, uv in zip(face.loops, uvs):
                loop[self.uv_layer].uv = uv
            self.explicit_uv_faces.add(face)
        return self._tag([face], material)

    def finish(self, name, parent=None, collection_name='parts', origin=(0, 0, 0)):
        """Make the object. origin: where the object's own centre goes (a door leaf's hinge); the
        points stay where they were given in the set."""
        origin = Vector(origin)
        # every face's facing, worked out now: bmesh leaves a new face's facing at zero until asked, and a face with
        # no facing took the ground's mapping (across x, up y), so an upright wall's picture ran in one direction
        # only and came out as fine stripes (the gate piers' "curtains", round 3 of log 34)
        self.bm.normal_update()
        for face in self.bm.faces:
            if face in self.explicit_uv_faces:
                continue
            material = self.materials[face.material_index]
            tile = material.get('tile_metres', 1.0) or 1.0
            normal = face.normal
            facing_x, facing_y, facing_z = abs(normal.x), abs(normal.y), abs(normal.z)
            for loop in face.loops:
                point = loop.vert.co
                if facing_z >= facing_x and facing_z >= facing_y:
                    across, up = point.x, point.y
                elif facing_x >= facing_y:
                    across, up = point.y, point.z
                else:
                    across, up = point.x, point.z
                loop[self.uv_layer].uv = (across / tile, up / tile)
        for face in self.bm.faces:
            face.smooth = face in self.smooth_faces
        if origin.length:
            bmesh.ops.translate(self.bm, verts=self.bm.verts, vec=-origin)
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for material in self.materials:
            mesh.materials.append(material)
        part = bpy.data.objects.new(name, mesh)
        part.location = origin
        collection(collection_name).objects.link(part)
        if parent is not None:
            part.parent = parent
        return part


def glass_piece(name, corners, prefix, glass_type, state, variant, step, parent, extra=None):
    """One pane of glass as its own object (a window, a north light panel): corners in order bottom
    left, bottom right, top right, top left as seen from outside. It wears one of the four windows in
    its type's picture (variant), and remembers its factory, type and lighting step (1, 2 or 3; 0 for
    the loading doorway) so set_windows can light it."""
    variants = GLASS_VARIANTS.get(glass_type, 4)
    left_edge, right_edge = variant / variants, (variant + 1) / variants
    builder = MeshBuilder()
    builder.quad(corners, glass_material(prefix, glass_type, state), uvs=[(left_edge, 0), (right_edge, 0), (right_edge, 1), (left_edge, 1)])
    centre = sum((Vector(corner) for corner in corners), Vector()) / 4
    piece = builder.finish(name, parent=parent, collection_name='glass', origin=centre)
    piece['works_factory'] = prefix
    piece['works_glass'] = glass_type
    piece['window_step'] = step
    for key, value in (extra or {}).items():
        piece[key] = value
    return piece


# ---------------------------------------------------------------------------------------- lighting

def glass_pieces(prefix):
    return [part for part in bpy.data.objects if part.type == 'MESH' and part.get('works_factory') == prefix and part.get('works_glass')]


def set_windows(prefix, steps_lit):
    """Light a factory's windows and roof glazing by thirds: steps_lit is a set of steps from 1, 2 and 3
    (all three: every window lit; {1}: a third; empty: all dark). prefix: 'no-1' or 'no-2'.
    Returns how many pieces are lit."""
    lit = 0
    for piece in glass_pieces(prefix):
        step = int(piece.get('window_step', 0))
        if step == 0:
            continue
        state = 'lit' if step in steps_lit else 'dark'
        piece.data.materials[0] = glass_material(prefix, piece['works_glass'], state)
        lit += state == 'lit'
    return lit


def set_doorway(prefix, lit):
    """Light (True) or darken (False) the inside of a factory's loading doorway."""
    for piece in glass_pieces(prefix):
        if int(piece.get('window_step', 0)) == 0:
            piece.data.materials[0] = glass_material(prefix, piece['works_glass'], 'lit' if lit else 'dark')


# ------------------------------------------------------------------------------------------ saving

def stop_if_files_exist(paths, replace):
    """Never write over files that are already there unless asked to (--replace)."""
    existing = [path for path in paths if os.path.exists(path)]
    if existing and not replace:
        print('stopped, these files are already there:', ', '.join(existing))
        print('  choose another folder (--out) or add --replace to write over them')
        sys.exit(1)


def descendants(root):
    found = [root]
    for child in root.children:
        found += descendants(child)
    return found


def export_glb(root, path):
    """Write the root and everything under it (no cameras or lights) as one .glb; custom properties
    (window steps and the like) travel as glTF extras."""
    bpy.ops.object.select_all(action='DESELECT')
    for part in descendants(root):
        part.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True, export_apply=True,
                              use_selection=True, export_cameras=False, export_lights=False,
                              export_extras=True, export_image_format='AUTO', export_materials='EXPORT')
    print('wrote', path, f'{os.path.getsize(path) / 1e6:.1f} MB')


def save_blend(path):
    """Save the scene with its pictures referred to by relative paths (kept outside the file)."""
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    print('wrote', path, f'{os.path.getsize(path) / 1e6:.1f} MB')


LAYOUT_NOTE = ('Works layout, metres: x across the lane (0 on its centre line, No. 1 at minus x, No. 2 at plus x); '
               'y away from the lane (0 at the works wall\'s face on the lane side); z up from the ground. Place the root '
               'at the wall\'s face on the lane\'s centre line (for a lane built with --length L, at y = L). In three.js a '
               'point (x, y, z) is (x, z, -y).')


def record(folder, entry):
    """Write (or replace) one model's entry in the folder's index.json, which an assemble script reads:
    the file, its root, its size and parts as measured from the built model, its glass, its markers."""
    import json
    path = os.path.join(folder, 'index.json')
    entries = []
    if os.path.exists(path):
        with open(path) as f:
            entries = json.load(f)['models']
    entries = [e for e in entries if e['file'] != entry['file']] + [entry]
    entries.sort(key=lambda e: e['file'])
    with open(path, 'w') as f:
        json.dump({'about': LAYOUT_NOTE, 'models': entries}, f, indent=1)
    print('recorded in', path)


def describe(root, path, description, facts):
    """An index entry for a model: measured size, triangles, file size, markers and glass groups."""
    bpy.context.view_layer.update()
    parts = descendants(root)
    low, high = bounds(parts)
    glass = [part for part in parts if part.type == 'MESH' and part.get('works_glass')]
    steps = {}
    for piece in glass:
        steps[f"step {int(piece['window_step'])}" if int(piece['window_step']) else 'doorway'] = steps.get(
            f"step {int(piece['window_step'])}" if int(piece['window_step']) else 'doorway', 0) + 1
    surfaces = sorted({node.image.name.rsplit('_', 1)[0] for part in parts if part.type == 'MESH' for material in part.data.materials
                       for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image and '_' in node.image.name})
    return {
        'file': os.path.basename(path),
        'blend': os.path.basename(path).replace('.glb', '.blend'),
        'root': root.name,
        'description': description,
        'size_metres': {'from': [round(value, 2) for value in low], 'to': [round(value, 2) for value in high],
                        'width_x': round(high.x - low.x, 2), 'depth_y': round(high.y - low.y, 2), 'height_z': round(high.z - low.z, 2)},
        'facts': facts,
        'objects': len(parts),
        'triangles': count_triangles(parts),
        'glb_megabytes': round(os.path.getsize(path) / 1e6, 1),
        'markers': sorted(part.name for part in parts if part.type == 'EMPTY' and not part.children),
        'glass_pieces': steps,
        'glass_materials': sorted({material.name for piece in glass for material in piece.data.materials}),
        'lettering': 'none (no signs, no lettering, no figures)',
        'surfaces': surfaces,
        'licence': 'Poly Haven surfaces (CC0); glass pictures painted by paint_works_pictures.py; built by script',
    }


def count_triangles(objects):
    graph = bpy.context.evaluated_depsgraph_get()
    total = 0
    for part in objects:
        if part.type != 'MESH':
            continue
        mesh = part.evaluated_get(graph).to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        part.evaluated_get(graph).to_mesh_clear()
    return total


def bounds(objects):
    """The box round the given objects' points in the set: (minimum, maximum)."""
    low, high = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for part in objects:
        if part.type != 'MESH':
            continue
        for vertex in part.data.vertices:
            point = part.matrix_world @ vertex.co
            low = Vector(map(min, low, point))
            high = Vector(map(max, high, point))
    return low, high
