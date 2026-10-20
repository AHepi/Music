# What this does: small helpers (for the geometry-nodes experiments in this folder) that make it short to build a Geometry Nodes
# node group from a Python file, and to "photograph" real geometry from straight above as height, colour and normal pictures.
# It sits on top of the project's lib/ (bake_harness.py and recipe_tools.py) and changes nothing in lib/.
#
# Two parts:
#   1. GeoWriter: like lib/recipe_tools.NodeWriter, but a socket value can be a plain number (sets the default) or a
#      pair (node_name, socket_name) (makes a link). Example:
#          g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Vertices X': 4})
#          g.node('ShaderNodeMath', 'half', {0: ('grid', 'Mesh'), 1: 0.5}, operation='MULTIPLY')
#   2. photograph_geometry(): puts a finished object under the 1 x 1 overhead camera and writes height.png (16-bit),
#      colour.png, normal.png (from the height, as in lib/) and normal_geometry.png (the true surface normal of the geometry).
# Use (inside Blender):  import gn_tools as gt
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
LIB = os.path.join(PROC, 'lib')
sys.path.insert(0, LIB)
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402


# ----------------------------------------------------------------------------------------------------- node writing
class GeoWriter(rt.NodeWriter):
    """NodeWriter with one extra trick: `node()` takes a dict of input values where each value is a number/tuple (set the socket's
    default) or a ('node_name', 'socket_name') pair (link from that node's output)."""

    def node(self, kind, name, inputs=None, **settings):
        node = self.add(kind, name, **settings)
        for key, value in (inputs or {}).items():
            self.feed(name, key, value)
        return node

    def feed(self, name, socket, value):
        node = self.nodes[name]
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], (str, int)):
            self.link(value[0], value[1], name, socket)
        else:
            node.inputs[socket].default_value = value

    def group(self, name, tree, inputs=None):
        """A node that runs another node group (set the group FIRST, then the inputs exist)."""
        node = self.add('GeometryNodeGroup' if tree.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup', name)
        node.node_tree = tree
        for key, value in (inputs or {}).items():
            self.feed(name, key, value)
        return node

    def math(self, name, operation, a=None, b=None, c=None, clamp=False, x=None, y=0):
        node = self.add('ShaderNodeMath', name, x=x, y=y, operation=operation, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            if value is not None:
                self.feed(name, index, value)
        return node

    def vmath(self, name, operation, a=None, b=None, c=None, x=None, y=0):
        node = self.add('ShaderNodeVectorMath', name, x=x, y=y, operation=operation)
        for index, value in enumerate((a, b, c)):
            if value is not None:
                self.feed(name, index, value)
        return node

    def out(self, node_name, socket=0):
        """Shorthand for a link source: g.out('grid', 'Mesh') -> ('grid', 'Mesh')."""
        return (node_name, socket)


def make_geometry_group(name, inputs, outputs=None):
    """A new Geometry Nodes group. inputs: list of (name, socket_type, default[, minimum, maximum]) with socket_type such as
    'NodeSocketGeometry', 'NodeSocketFloat', 'NodeSocketInt', 'NodeSocketVector', 'NodeSocketColor'. outputs: list of (name, socket_type);
    default one output 'Geometry'. Returns (tree, writer); the writer knows 'in' (Group Input) and 'out' (Group Output)."""
    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    for spec in inputs:
        socket_name, socket_type, default = spec[:3]
        socket = tree.interface.new_socket(socket_name, in_out='INPUT', socket_type=socket_type)
        if default is not None and socket_type != 'NodeSocketGeometry':
            socket.default_value = default
        if len(spec) >= 5:
            socket.min_value, socket.max_value = spec[3], spec[4]
    for socket_name, socket_type in (outputs or [('Geometry', 'NodeSocketGeometry')]):
        tree.interface.new_socket(socket_name, in_out='OUTPUT', socket_type=socket_type)
    writer = GeoWriter(tree)
    writer.nodes['in'] = tree.nodes.new('NodeGroupInput')
    writer.nodes['in'].location = (-1200, 0)
    writer.nodes['out'] = tree.nodes.new('NodeGroupOutput')
    writer.nodes['out'].location = (3200, 0)
    return tree, writer


def modifier_inputs(modifier, **named_values):
    """Set a Geometry Nodes modifier's exposed inputs by their NAMES (underscores stand for spaces): modifier_inputs(m, Seed=3).
    Blender 5.x CHANGE (tested): the old way  modifier['Socket_2'] = value  now fails with "this type doesn't support IDProperties";
    each input is an object  modifier.properties.inputs.Socket_1  (named by the socket identifier) and its number is  .value  (it also has .attribute_name)."""
    tree = modifier.node_group
    lookup = {item.name: item.identifier for item in tree.interface.items_tree if item.item_type == 'SOCKET' and item.in_out == 'INPUT'}
    for key, value in named_values.items():
        getattr(modifier.properties.inputs, lookup[key.replace('_', ' ')]).value = value
    modifier.id_data.update_tag()      # without this, headless Blender kept showing the OLD result (tested: change of 0.0 until the tag was added)


def add_geometry_object(name, tree, base_mesh=None):
    """A new mesh object (default: a single point, because many recipes make all their geometry from nothing) with the group on it."""
    if base_mesh is None:
        base_mesh = bpy.data.meshes.new(name + ' base')
        base_mesh.from_pydata([(0.5, 0.5, 0.0)], [], [])
    obj = bpy.data.objects.new(name, base_mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new('recipe', 'NODES')
    modifier.node_group = tree
    return obj, modifier


# ----------------------------------------------------------------------------------------------------- scene and measuring
def new_scene(size):
    """lib's overhead scene (1 x 1 camera over x 0..1, y 0..1), but without its flat square, so we can put our own geometry in."""
    scene, tile = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile)
    return scene


def evaluated_vertices(obj):
    """Vertex positions (n x 3, world space) of the object after its modifiers have run."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    count = len(mesh.vertices)
    points = np.empty(count * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', points)
    points = points.reshape(count, 3)
    matrix = np.array(obj.matrix_world)
    world = points @ matrix[:3, :3].T + matrix[:3, 3]
    evaluated.to_mesh_clear()
    return world


def evaluated_attribute(obj, name):
    """The values of a named attribute (any domain) on the evaluated mesh, as a numpy array (one row per element)."""
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    attribute = mesh.attributes[name]
    count = len(attribute.data)
    if attribute.data_type in ('FLOAT', 'INT', 'BOOLEAN', 'INT8'):
        values = np.empty(count, dtype=np.float64 if attribute.data_type == 'FLOAT' else np.int64)
        values = np.zeros(count, dtype=np.float32 if attribute.data_type == 'FLOAT' else (np.bool_ if attribute.data_type == 'BOOLEAN' else np.int32))
        attribute.data.foreach_get('value', values)
    elif attribute.data_type in ('FLOAT_VECTOR',):
        values = np.zeros(count * 3, dtype=np.float32)
        attribute.data.foreach_get('vector', values)
        values = values.reshape(count, 3)
    else:
        values = np.zeros(count * 4, dtype=np.float32)
        attribute.data.foreach_get('color', values)
        values = values.reshape(count, 4)
    evaluated.to_mesh_clear()
    return values


def z_range(obj):
    points = evaluated_vertices(obj)
    return float(points[:, 2].min()), float(points[:, 2].max()), len(points)


# ----------------------------------------------------------------------------------------------------- materials
def _emission_material(name, builder):
    material = bpy.data.materials.new(name)
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeEmission', 'emit', x=5, Strength=1.0)
    w.add('ShaderNodeOutputMaterial', 'output', x=6)
    w.link('emit', 'Emission', 'output', 'Surface')
    builder(w)
    return material


def height_material(z_low, z_high, route='position'):
    """Emission of height: 0 at z_low, 1 at z_high. route 'position' = the Z of the surface point (Geometry > Position);
    route 'camera' = the Camera Data node's View Z Depth (distance from the camera plane; camera is 5 above the tile)."""
    def build(w):
        if route == 'position':
            w.add('ShaderNodeNewGeometry', 'geo', x=0)
            w.add('ShaderNodeSeparateXYZ', 'split', x=1)
            w.link('geo', 'Position', 'split', 'Vector')
            w.add('ShaderNodeMapRange', 'norm', x=2, clamp=True, From__Min=z_low, From__Max=z_high, To__Min=0.0, To__Max=1.0)
            w.link('split', 'Z', 'norm', 'Value')
        else:
            w.add('ShaderNodeCameraData', 'cam', x=0)
            w.add('ShaderNodeMapRange', 'norm', x=2, clamp=True, From__Min=5.0 - z_low, From__Max=5.0 - z_high, To__Min=0.0, To__Max=1.0)
            w.link('cam', 'View Z Depth', 'norm', 'Value')
        w.add('ShaderNodeCombineColor', 'grey', x=3)
        for socket in ('Red', 'Green', 'Blue'):
            w.link('norm', 'Result', 'grey', socket)
        w.link('grey', 'Color', 'emit', 'Color')
    return _emission_material('show height ' + route, build)


def colour_material(attribute='piece_colour', ambient_occlusion=0.0, occlusion_distance=0.03, object_colour=False, edge_wear=0.0, edge_colour=(0.45, 0.42, 0.38, 1.0),
                    pointiness_range=(0.5, 0.62)):
    """Emission of a colour stored on the geometry (Attribute node), optionally changed by the shape of the geometry:
      ambient_occlusion 0..1 - darkens crevices (Ambient Occlusion node; needs real geometry; this is what gives the dark outlines)
      edge_wear 0..1         - lightens sharp convex edges to edge_colour (Geometry > Pointiness; the "worn paint / bare metal" trick; Cycles only)
    object_colour=True reads the Object's own colour (Object Info > Color) instead of the attribute, for rocks that are separate objects."""
    def build(w):
        w.add('ShaderNodeObjectInfo' if object_colour else 'ShaderNodeAttribute', 'attr', x=0, **({} if object_colour else {'attribute_name': attribute}))
        last = ('attr', 'Color')
        if edge_wear > 0:
            w.add('ShaderNodeNewGeometry', 'geo', x=0)
            w.add('ShaderNodeMapRange', 'wear mask', x=1, clamp=True, From__Min=pointiness_range[0], From__Max=pointiness_range[1], To__Min=0.0, To__Max=edge_wear)
            w.link('geo', 'Pointiness', 'wear mask', 'Value')
            w.add('ShaderNodeMix', 'worn', x=2, data_type='RGBA')
            w.link('wear mask', 'Result', 'worn', 'Factor')
            w.link(last[0], last[1], 'worn', 'A')
            w.nodes['worn'].inputs['B'].default_value = edge_colour
            last = ('worn', 'Result')
        if ambient_occlusion > 0:
            w.add('ShaderNodeAmbientOcclusion', 'ao', x=3, samples=16, inside=False, only_local=False, Distance=occlusion_distance)
            w.add('ShaderNodeMix', 'dark', x=4, data_type='RGBA', blend_type='MULTIPLY', Factor=ambient_occlusion)
            w.link(last[0], last[1], 'dark', 'A')
            w.link('ao', 'AO', 'dark', 'B')
            last = ('dark', 'Result')
        w.link(last[0], last[1], 'emit', 'Color')
    return _emission_material('show colour', build)


def normal_material():
    """Emission of the true surface normal, in the OpenGL map convention (x right, y up the picture, z out of the picture), 0..1."""
    def build(w):
        w.add('ShaderNodeNewGeometry', 'geo', x=0)
        w.add('ShaderNodeVectorMath', 'half', x=1, operation='MULTIPLY_ADD')
        w.nodes['half'].inputs[1].default_value = (0.5, 0.5, 0.5)
        w.nodes['half'].inputs[2].default_value = (0.5, 0.5, 0.5)
        w.link('geo', 'Normal', 'half', 0)
        w.link('half', 0, 'emit', 'Color')
    return _emission_material('show normal', build)


def finish_with_material_slot(g, source_node, source_socket='Geometry'):
    """Last node of a recipe: Set Material, named 'show material'. WHY: a material put on the object's own slot does NOT reach geometry that a
    Geometry Nodes group has built (tested in Blender 5.2.2: the evaluated mesh has an empty material slot and the picture comes out black),
    so the material has to be set INSIDE the node group. photograph_geometry() swaps the material of this node for each picture."""
    g.node('GeometryNodeSetMaterial', 'show material', {'Geometry': (source_node, source_socket)})
    g.link('show material', 'Geometry', 'out', 'Geometry')


def render_with(scene, objs, material, path, linear_data, sixteen_bit=False, samples=4):
    """Put `material` on every object in objs (one object or a list), then render. Objects made by a Geometry Nodes group that ends with
    finish_with_material_slot() get the material through that node; plain mesh objects get it on their own slot."""
    for obj in (objs if isinstance(objs, (list, tuple)) else [objs]):
        node_group_object = False
        for modifier in obj.modifiers:
            if modifier.type == 'NODES' and modifier.node_group and 'show material' in modifier.node_group.nodes:
                modifier.node_group.nodes['show material'].inputs['Material'].default_value = material
                node_group_object = True
        if not node_group_object:
            obj.data.materials.clear()
            obj.data.materials.append(material)
    scene.cycles.samples = samples
    bh.render_to(scene, path, linear_data, sixteen_bit)


# ----------------------------------------------------------------------------------------------------- the whole photograph
def photograph_geometry(obj, out_folder, size=1254, normal_reference=None, ambient_occlusion=0.0, occlusion_distance=0.03,
                        z_low=None, z_high=None, attribute='piece_colour', object_colour=False, colour_samples=4, edge_wear=0.0, edge_colour=(0.45, 0.42, 0.38, 1.0),
                        extra_objects_for_range=(), with_geometry_normal=True, quiet=False, z_percentiles=None):
    """Writes colour.png, height.png (16 bit), normal.png (Sobel from the height, strength fitted to the named reference like lib/),
    normal_geometry.png (true normals) and photo.json (timings, height range). obj must already be in the current scene (new_scene)."""
    os.makedirs(out_folder, exist_ok=True)
    scene = bpy.context.scene
    timings = {}
    started = time.time()
    if z_low is None or z_high is None:
        lows, highs, counts = [], [], 0
        for item in ((obj if isinstance(obj, (list, tuple)) else [obj]) + list(extra_objects_for_range)):
            low, high, count = z_range(item)
            lows.append(low)
            highs.append(high)
            counts += count
        z_low, z_high = min(lows), max(highs)
        if z_percentiles:     # ignore a few stray high/low points (e.g. one stone still in the air): use these percentiles of all vertex heights instead
            allz = np.concatenate([evaluated_vertices(item)[:, 2] for item in ((obj if isinstance(obj, (list, tuple)) else [obj]) + list(extra_objects_for_range))])
            z_low, z_high = float(np.percentile(allz, z_percentiles[0])), float(np.percentile(allz, z_percentiles[1]))
        timings['vertices'] = counts
    timings['evaluate_geometry_s'] = round(time.time() - started, 2)
    started = time.time()
    render_with(scene, obj, height_material(z_low, z_high), os.path.join(out_folder, 'height.png'), True, True)
    timings['height_render_s'] = round(time.time() - started, 2)
    started = time.time()
    render_with(scene, obj, colour_material(attribute, ambient_occlusion, occlusion_distance, object_colour, edge_wear, edge_colour),
                os.path.join(out_folder, 'colour.png'), False, False, samples=colour_samples)
    timings['colour_render_s'] = round(time.time() - started, 2)
    if with_geometry_normal:
        started = time.time()
        render_with(scene, obj, normal_material(), os.path.join(out_folder, 'normal_geometry.png'), True, False, samples=8)
        timings['normal_render_s'] = round(time.time() - started, 2)
    height = bh.load_png_as_array(os.path.join(out_folder, 'height.png'))[..., 0]
    strength = bh.fit_sobel_strength(height, bh.reference_normal_slope_spread(normal_reference)) if normal_reference else 8.0
    bh.save_array_png(bh.sobel_normal(height, strength) * 0.5 + 0.5, os.path.join(out_folder, 'normal.png'))
    info = {'size': size, 'z_low': z_low, 'z_high': z_high, 'sobel_strength': strength, **timings}
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    if not quiet:
        print('[photo]', json.dumps(info))
    return info


def float_rng(seed):
    return np.random.default_rng(seed)


# ----------------------------------------------------------------------------------------------------- seamless noise inside Geometry Nodes
def tileable_noise_geo_group(name='Tileable noise (geometry)'):
    """Noise that repeats exactly every 1.0 in x and in y, for use on geometry that has to wrap (Blender's plain Noise node does NOT repeat).
    Same trick as lib/recipe_tools.tileable_noise_group: sample a 4-dimensional noise on a donut so the left edge continues into the right edge.
    Inputs: Position (vector; only x and y are used), Scale (features per tile), Detail, Roughness, Distortion, Seed (changes the pattern; any number).
    Output: Fac (0..1, centred on 0.5 like Blender's noise - so stretch it with Map Range before using it)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = make_geometry_group(name, [('Position', 'NodeSocketVector', (0, 0, 0)), ('Scale', 'NodeSocketFloat', 4.0), ('Detail', 'NodeSocketFloat', 4.0),
                                        ('Roughness', 'NodeSocketFloat', 0.5), ('Distortion', 'NodeSocketFloat', 0.0), ('Seed', 'NodeSocketFloat', 0.0)],
                                  [('Fac', 'NodeSocketFloat')])
    tau = 2 * math.pi
    g.node('ShaderNodeSeparateXYZ', 'split', {'Vector': ('in', 'Position')})
    g.math('turns u', 'MULTIPLY', ('split', 'X'), tau)
    g.math('turns v', 'MULTIPLY', ('split', 'Y'), tau)
    g.math('cos u', 'COSINE', ('turns u', 0))
    g.math('sin u', 'SINE', ('turns u', 0))
    g.math('cos v', 'COSINE', ('turns v', 0))
    g.math('sin v', 'SINE', ('turns v', 0))
    g.math('radius', 'DIVIDE', ('in', 'Scale'), tau)
    g.node('ShaderNodeCombineXYZ', 'donut', {'X': ('cos u', 0), 'Y': ('sin u', 0), 'Z': ('cos v', 0)})
    g.vmath('donut scaled', 'SCALE', ('donut', 'Vector'))
    g.link('radius', 0, 'donut scaled', 'Scale')
    g.math('w scaled', 'MULTIPLY', ('sin v', 0), ('radius', 0))
    g.math('w seeded', 'ADD', ('w scaled', 0), ('in', 'Seed'))
    g.node('ShaderNodeTexNoise', 'noise', {'Vector': ('donut scaled', 0), 'W': ('w seeded', 0), 'Scale': 1.0, 'Detail': ('in', 'Detail'),
                                           'Roughness': ('in', 'Roughness'), 'Distortion': ('in', 'Distortion')},
           noise_dimensions='4D', noise_type='FBM', normalize=True)
    g.link('noise', 'Fac', 'out', 'Fac')
    return tree


# ----------------------------------------------------------------------------------------------------- colours
def srgb(r, g, b):
    """Colour typed the way a painter reads it (0-255 sRGB) -> the linear RGBA a node wants."""
    f = lambda c: ((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92
    return (f(r), f(g), f(b), 1.0)


def make_ramp(g, name, stops, inputs=None, interpolation='LINEAR'):
    """A Color Ramp node (works in shader AND geometry node trees) from [(position 0..1, (r, g, b) as 0-255 sRGB), ...]."""
    node = g.node('ShaderNodeValToRGB', name, inputs or {})
    node.color_ramp.interpolation = interpolation      # 'CONSTANT' = hard bands (each stop's colour holds until the next stop)
    elements = node.color_ramp.elements
    while len(elements) > 1:
        elements.remove(elements[-1])
    elements[0].position, elements[0].color = stops[0][0], srgb(*stops[0][1])
    for position, rgb in stops[1:]:
        element = elements.new(position)
        element.color = srgb(*rgb)
    return node


def tileable_noise_stretched_group(name='Tileable noise stretched (geometry)'):
    """Like tileable_noise_geo_group but with separate feature counts along x and y, so the noise can be stretched into streaks (wood fibres, rust drips)
    and still repeat exactly every 1.0. Inputs: Position, Scale X (features per tile along x), Scale Y (features per tile along y), Detail, Roughness, Seed.
    The trick: the x circle and the y circle of the donut get different radii (radius = features / 2 pi)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = make_geometry_group(name, [('Position', 'NodeSocketVector', (0, 0, 0)), ('Scale X', 'NodeSocketFloat', 3.0), ('Scale Y', 'NodeSocketFloat', 30.0),
                                        ('Detail', 'NodeSocketFloat', 4.0), ('Roughness', 'NodeSocketFloat', 0.5), ('Seed', 'NodeSocketFloat', 0.0)], [('Fac', 'NodeSocketFloat')])
    tau = 2 * math.pi
    g.node('ShaderNodeSeparateXYZ', 'split', {'Vector': ('in', 'Position')})
    g.math('turns u', 'MULTIPLY', ('split', 'X'), tau)
    g.math('turns v', 'MULTIPLY', ('split', 'Y'), tau)
    g.math('cos u', 'COSINE', ('turns u', 0))
    g.math('sin u', 'SINE', ('turns u', 0))
    g.math('cos v', 'COSINE', ('turns v', 0))
    g.math('sin v', 'SINE', ('turns v', 0))
    g.math('radius x', 'DIVIDE', ('in', 'Scale X'), tau)
    g.math('radius y', 'DIVIDE', ('in', 'Scale Y'), tau)
    g.math('x1', 'MULTIPLY', ('cos u', 0), ('radius x', 0))
    g.math('x2', 'MULTIPLY', ('sin u', 0), ('radius x', 0))
    g.math('x3', 'MULTIPLY', ('cos v', 0), ('radius y', 0))
    g.math('w1', 'MULTIPLY', ('sin v', 0), ('radius y', 0))
    g.math('w2', 'ADD', ('w1', 0), ('in', 'Seed'))
    g.node('ShaderNodeCombineXYZ', 'donut', {'X': ('x1', 0), 'Y': ('x2', 0), 'Z': ('x3', 0)})
    g.node('ShaderNodeTexNoise', 'noise', {'Vector': ('donut', 'Vector'), 'W': ('w2', 0), 'Scale': 1.0, 'Detail': ('in', 'Detail'), 'Roughness': ('in', 'Roughness')},
           noise_dimensions='4D', noise_type='FBM', normalize=True)
    g.link('noise', 'Fac', 'out', 'Fac')
    return tree
