# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It builds the WETNESS LAYER: one Blender "node group" (a small packaged recipe made of node boxes) that can sit between ANY material's dry look and
# its Principled BSDF (Blender's all-purpose surface shader) and turns the dry look into the wet look after rain. It is used for the pit village
# street (see "09 Recipe - wetness layer and specular map for the street - how it is made.md" in the folder above for the full story).
#
# Example first: a dry cobbled road has colour 0.19 (grey-brown), roughness 0.9 (chalky), and nothing else. Put the layer on it, set Wetness 0.85
# and Puddles 0.5, and the road comes out darker and a little richer in colour, smooth (roughness 0.3, so lamp light streaks across it), shiny
# (a thin clear water film), with flat dark mirror puddles in the low spots near the gutters, while the raised tops of the stones stay a little drier.
# A wall comes out with a wet dark band along its foot and with rain streaks running down from the window sills and the eaves.
#
# Words: "roughness" = how blurry reflections are (0 mirror, 1 chalk). "specular" = how strongly a surface reflects light head-on (the "shine"), here the
# Principled BSDF's "Specular IOR Level" (0.5 is normal, 0.75 is a wet surface, 0 is no reflection). "coat" = a thin clear layer on top (like water
# on stone, or varnish); Principled calls it "Coat". "height" = a grey picture of how high each dot is (0.5 = flat, 1 = high). "mask" = a grey picture
# of where something happens (0 nowhere, 1 fully).
#
# HOW TO USE (inside Blender, in a script):
#     import wetness_layer as wl
#     group_tree = wl.build_wetness_group()            # makes (once) the node group called WETNESS
#     node = wl.add_wetness_to_material(material, wetness=0.85, puddles=0.5, rough_image=..., height_image=..., lowness=..., porosity=0.6)
# The second call puts the group between the material's colour/normal pictures and its Principled BSDF. For a material made of node groups (one of the
# texture recipes), plug the recipe's Colour, Roughness and Height outputs into the matching inputs of a WETNESS node yourself and plug the
# outputs of the layer into the Principled BSDF (the table below says which goes where).
#
# INPUTS (every one has a default; only the dry look has to be plugged in). "range" is what makes sense; "default" is what you get if you do nothing.
#   THE DRY LOOK (plug these in)
#     Colour      the dry colour picture
#     Roughness   the dry roughness (a number, or a roughness picture)
#     Height      the dry relief height, 0..1, 0.5 = flat (a height picture); it lets the layer keep the stone TOPS drier and let water gather in the JOINTS
#     Normal      the dry normal (the bumpy look from a normal map). Plain surface normal if you have none.
#   WHERE AM I (so the layer can tell ground from wall from roof, and measure height above the ground)
#     Use World Geometry   1 (default): the layer reads the object's world position and true surface direction itself.
#                          0: it uses the Position and Surface Up inputs instead. Use 0 for walls, to measure in the object's OWN coordinates (so every
#                          copy of a shared wall mesh gets the same wet pattern, which is what a baked map needs), and for flat texture tiles
#                          (plug the tile coordinate into Position and (0, 0, 1) into Surface Up).
#     Position, Surface Up   used only when Use World Geometry is 0
#   HOW WET
#     Wetness     0..1 (0.8): how wet everything is. 0 = bone dry: the layer gives the dry look back unchanged. 1 = soaked.
#     Puddles     0..1 (0.5): how much standing water. 0 = none. The dial is calibrated (see PUDDLE_CURVE below and the recipe note) so that on the
#                 street's road, as seen from the main camera, the share of road under water rises smoothly with the dial.
#     Seed        any number: moves where the puddles and streaks fall.
#   THE MATERIAL
#     Porosity          0..1 (0.6): how much the surface soaks water up and darkens. Brick 0.7, stone 0.6, slate 0.3, painted wood 0.2, metal 0.
#     Darkest           0..1 (0.45): how dark a fully porous, soaked surface gets, as a multiple of its dry colour. 0.45 means "a bit under half as bright";
#                       with porosity 0.6 and wetness 0.85 the colour ends up about 0.72 of dry (the target for stone and brick).
#     Wet Roughness     0..1 (0.3): the roughness of a soaked surface (0.3 for ground; about 0.45 for walls, or they look like glass).
#     Puddle Roughness  0..1 (0.08): the roughness of standing water (0.03 is a perfect mirror, which turns into a black hole wherever it reflects only dark
#                       houses; 0.08 is a little blurred and reads as water without going black; chosen by eye from three variants).
#     Specular Boost    0..0.5 (0.25): how far the shine rises when wet (Specular IOR Level goes from 0.5 to 0.5 + this).
#     Relief Flatten    0..1 (0.35): how far the normal map relief is smoothed away on wet ground (water fills the fine bumps; this is also the cure for
#                       sparkly "gritty" flagstones). Inside puddles the relief is flattened completely whatever this is.
#     Puddle Bias       -0.3..0.3 (0): moves the puddle threshold for ONE material: plus = fewer puddles (a pavement, which should hold less water than the
#                       road), minus = more.
#     Puddle Darkness   0..1 (0.9): the colour of the ground under standing water, as a multiple (1 = not darker). Kept high on purpose (see Puddle Roughness).
#   WHERE THE WATER GOES
#     Lowness     0..1 (0.5): how low this spot is, supplied by whoever puts the layer on (the road: 1 at the gutter, 0 on the crown). 0.5 = no opinion.
#     Dry Tops    0..1 (0.5): how much the high parts of the relief (stone tops) stay drier than the joints.
#     Water Level 0..1 (0.65): how high puddles reach on the Height scale (fills joints and dips, tops stay out). Sets the flat height inside puddles.
#     Ground Slope, Ground Offset: the ground rises Ground Slope metres per metre along +y (the street: tan 4 degrees = 0.0699); Ground Offset is the
#                       height of this surface's ground above the origin line. The layer measures "height above the ground" as
#                       z - y * Ground Slope - Ground Offset, to put the wet band at the foot of walls. (For a wall measured in its own coordinates:
#                       the street's cottages use +-0.0699 and -0.307, see apply_wetness_to_set.py.)
#     Wall Band   metres (0.45): how high the wet band at the foot of a wall reaches (its top edge wavers).
#     Wall Wetness 0..1 (0.35): how wet the whole face of a wall is (driven rain), on top of the band and the streaks.
#     Streaks     0..1 (0.5): how strong the general vertical rain streaks on walls are.
#     Drip Mask   0..1 (0): rain running down from a source the caller knows (window sills, eaves): made by the DRIP sub-group below.
#   SWITCHES (0..1 each, default 1): Colour Effect, Roughness Effect, Specular Effect, Coat Effect, Normal Effect. 0 gives that part's dry value back
#     (for tests and for switching one part of the wet look off).
#
# OUTPUTS (plug into the Principled BSDF as the table says)
#   Colour -> Base Color; Roughness -> Roughness; Specular IOR Level -> Specular IOR Level; Coat Weight -> Coat Weight; Coat Roughness -> Coat Roughness;
#   Normal -> Normal; (and set the Principled BSDF's Coat IOR to 1.33, the index of water). Height: the relief height after water has filled the puddles.
#   Wet Mask, Puddle Mask, Streak Mask, Puddle Depth: grey pictures for checking and for baking maps (Puddle Depth is the number the puddle threshold is
#   cut from; the calibration reads it).
#
# THE RECIPE INSIDE, IN ORDER (all tested; numbers are in the recipe note)
#   1. kind of surface from the surface direction: ground (faces up within about 20 degrees), wall (upright), roof (in between).
#   2. puddle depth = 50 % slow wobble across the ground + 25 % the caller's Lowness + 25 % the low parts of the relief. A soft threshold, moved by the
#      Puddles dial along a calibrated curve, turns depth into puddles. Ground only.
#   3. wet ground = Wetness (patchy), with the high parts of the relief drier (Dry Tops).
#   4. wet wall = the wet band at the foot (edge wavering), the general damp, and streaks (general ones, plus the Drip Mask).
#   5. wet roof = Wetness x 0.9. Standing water counts as soaked.
#   6. the wet look: colour x porosity darkening, a little more colour; roughness slid to Wet Roughness (puddles: Puddle Roughness); specular up;
#      coat up to 1 in puddles (0.3 x wet elsewhere); normal slid toward the plain surface direction (flat in puddles).
import math

import bpy

TREE_NAME = 'WETNESS'
DRIP_TREE_NAME = 'WETNESS DRIP'
# the puddle dial: threshold = PUDDLE_THRESHOLD_TOP - PUDDLE_THRESHOLD_RANGE * (Puddles ** PUDDLE_CURVE); calibrated by tools/02_puddle_sweep.py
PUDDLE_THRESHOLD_TOP = 0.79
PUDDLE_THRESHOLD_RANGE = 0.39
PUDDLE_CURVE = 0.80


class Net:
    """Tiny helper: makes nodes in one group and chains them. Every helper returns an output socket, so a result can be passed on as the next input."""

    def __init__(self, tree):
        self.tree = tree
        self.count = 0

    def _place(self, node):
        node.location = ((self.count % 14) * 200, -(self.count // 14) * 180)
        self.count += 1
        return node

    def _feed(self, node, index, value):
        if value is None:
            return
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, node.inputs[index])
        else:
            node.inputs[index].default_value = value

    def math(self, operation, a, b=None, c=None, clamp=False):
        node = self._place(self.tree.nodes.new('ShaderNodeMath'))
        node.operation = operation
        node.use_clamp = clamp
        for index, value in enumerate((a, b, c)):
            self._feed(node, index, value)
        return node.outputs[0]

    def map_range(self, value, from_min, from_max, to_min=0.0, to_max=1.0, smooth=False, clamp=True):
        node = self._place(self.tree.nodes.new('ShaderNodeMapRange'))
        node.data_type = 'FLOAT'
        node.interpolation_type = 'SMOOTHSTEP' if smooth else 'LINEAR'
        node.clamp = clamp
        for index, item in enumerate((value, from_min, from_max, to_min, to_max)):
            self._feed(node, index, item)
        return node.outputs[0]

    def mix(self, fac, a, b):
        node = self._place(self.tree.nodes.new('ShaderNodeMix'))
        node.data_type = 'FLOAT'
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 2, a)
        self._feed(node, 3, b)
        return node.outputs[0]

    def mix_colour(self, fac, a, b, blend='MIX'):
        node = self._place(self.tree.nodes.new('ShaderNodeMix'))
        node.data_type = 'RGBA'
        node.blend_type = blend
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 6, a)
        self._feed(node, 7, b)
        return node.outputs[2]

    def mix_vector(self, fac, a, b):
        node = self._place(self.tree.nodes.new('ShaderNodeMix'))
        node.data_type = 'VECTOR'
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 4, a)
        self._feed(node, 5, b)
        return node.outputs[1]

    def vector_math(self, operation, a, b=None):
        node = self._place(self.tree.nodes.new('ShaderNodeVectorMath'))
        node.operation = operation
        self._feed(node, 0, a)
        self._feed(node, 1, b)
        return node.outputs[0]

    def combine(self, x, y, z):
        node = self._place(self.tree.nodes.new('ShaderNodeCombineXYZ'))
        self._feed(node, 0, x)
        self._feed(node, 1, y)
        self._feed(node, 2, z)
        return node.outputs[0]

    def separate(self, vector):
        node = self._place(self.tree.nodes.new('ShaderNodeSeparateXYZ'))
        self.tree.links.new(vector, node.inputs[0])
        return node.outputs[0], node.outputs[1], node.outputs[2]

    def noise(self, vector, scale=1.0, detail=3.0, roughness=0.5):
        node = self._place(self.tree.nodes.new('ShaderNodeTexNoise'))
        node.noise_dimensions = '3D'
        node.noise_type = 'FBM'
        node.normalize = True
        self.tree.links.new(vector, node.inputs['Vector'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        return node.outputs['Fac']

    def geometry(self):
        return self._place(self.tree.nodes.new('ShaderNodeNewGeometry'))


def _add_sockets(tree, inputs, outputs):
    for name, kind, default in inputs:
        socket = tree.interface.new_socket(name, in_out='INPUT', socket_type=kind)
        socket.default_value = default
        if kind == 'NodeSocketVector' and name in ('Normal', 'Position', 'Surface Up'):
            socket.hide_value = True
    for name, kind in outputs:
        tree.interface.new_socket(name, in_out='OUTPUT', socket_type=kind)


def build_drip_group():
    """WETNESS DRIP: a rain streak that hangs down from one source (a window sill, the eaves) on a wall measured in the wall's own coordinates.
    Inputs: Position (x, y, z of the wall dot), Centre (where along the wall the source is), Half Width, Top (height of the source), Length (how far
    the streak runs down), Seed. Output: Mask 0..1. Several of them chained with Maximum make the Drip Mask of a wall."""
    existing = bpy.data.node_groups.get(DRIP_TREE_NAME)
    if existing:
        return existing
    tree = bpy.data.node_groups.new(DRIP_TREE_NAME, 'ShaderNodeTree')
    _add_sockets(tree, [('Position', 'NodeSocketVector', (0.0, 0.0, 0.0)), ('Centre', 'NodeSocketFloat', 0.0), ('Half Width', 'NodeSocketFloat', 0.5),
                        ('Top', 'NodeSocketFloat', 1.0), ('Length', 'NodeSocketFloat', 1.0), ('Seed', 'NodeSocketFloat', 0.0)],
                 [('Mask', 'NodeSocketFloat')])
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (3200, 0)
    g = lambda name: group_in.outputs[name]   # noqa: E731
    n = Net(tree)
    _, y, z = n.separate(g('Position'))
    seed_shift = n.math('MULTIPLY', g('Seed'), 11.7)
    across = n.math('DIVIDE', n.math('ABSOLUTE', n.math('SUBTRACT', y, g('Centre'))), n.math('MAXIMUM', g('Half Width'), 0.05))
    # long vertical lines: noise squeezed across the wall and stretched down it; and a slow wobble that makes the sides ragged
    lines = n.noise(n.combine(n.math('ADD', n.math('MULTIPLY', y, 16.0), seed_shift), 3.1, n.math('MULTIPLY', z, 0.8)), scale=1.0, detail=2.0, roughness=0.5)
    wobble = n.noise(n.combine(n.math('ADD', n.math('MULTIPLY', y, 5.0), seed_shift), 7.7, n.math('MULTIPLY', z, 0.5)), scale=1.0, detail=2.0, roughness=0.5)
    edge = n.math('ADD', 0.95, n.math('MULTIPLY', n.math('SUBTRACT', wobble, 0.5), 0.9))
    inside = n.math('SUBTRACT', 1.0, n.map_range(across, n.math('SUBTRACT', edge, 0.3), n.math('ADD', edge, 0.15), 0.0, 1.0, smooth=True))
    below = n.math('SUBTRACT', g('Top'), z)                                  # metres below the source (negative above it)
    fade = n.math('POWER', n.math('SUBTRACT', 1.0, n.map_range(below, 0.0, g('Length'), 0.0, 1.0)), 1.6)
    start = n.map_range(below, -0.02, 0.06, 0.0, 1.0, smooth=True)           # nothing above the source
    stripes = n.map_range(lines, 0.42, 0.62, 0.0, 1.0, smooth=True)
    strength = n.mix(stripes, 0.3, 1.0)
    mask = n.math('MULTIPLY', n.math('MULTIPLY', inside, fade), n.math('MULTIPLY', start, strength))
    tree.links.new(mask, group_out.inputs['Mask'])
    return tree


def build_wetness_group():
    existing = bpy.data.node_groups.get(TREE_NAME)
    if existing:
        return existing
    tree = bpy.data.node_groups.new(TREE_NAME, 'ShaderNodeTree')
    inputs = [
        ('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.85), ('Height', 'NodeSocketFloat', 0.5),
        ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)),
        ('Use World Geometry', 'NodeSocketFloat', 1.0), ('Position', 'NodeSocketVector', (0.0, 0.0, 0.0)), ('Surface Up', 'NodeSocketVector', (0.0, 0.0, 1.0)),
        ('Wetness', 'NodeSocketFloat', 0.8), ('Puddles', 'NodeSocketFloat', 0.5), ('Seed', 'NodeSocketFloat', 0.0),
        ('Porosity', 'NodeSocketFloat', 0.6), ('Darkest', 'NodeSocketFloat', 0.45), ('Wet Roughness', 'NodeSocketFloat', 0.3),
        ('Puddle Roughness', 'NodeSocketFloat', 0.08), ('Specular Boost', 'NodeSocketFloat', 0.25), ('Relief Flatten', 'NodeSocketFloat', 0.35),
        ('Puddle Darkness', 'NodeSocketFloat', 0.9), ('Puddle Bias', 'NodeSocketFloat', 0.0),
        ('Lowness', 'NodeSocketFloat', 0.5), ('Dry Tops', 'NodeSocketFloat', 0.5), ('Water Level', 'NodeSocketFloat', 0.65),
        ('Ground Slope', 'NodeSocketFloat', 0.0699), ('Ground Offset', 'NodeSocketFloat', 0.0), ('Wall Band', 'NodeSocketFloat', 0.45),
        ('Wall Wetness', 'NodeSocketFloat', 0.35), ('Streaks', 'NodeSocketFloat', 0.5), ('Drip Mask', 'NodeSocketFloat', 0.0),
        ('Colour Effect', 'NodeSocketFloat', 1.0), ('Roughness Effect', 'NodeSocketFloat', 1.0), ('Specular Effect', 'NodeSocketFloat', 1.0),
        ('Coat Effect', 'NodeSocketFloat', 1.0), ('Normal Effect', 'NodeSocketFloat', 1.0)]
    outputs = [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'),
               ('Coat Weight', 'NodeSocketFloat'), ('Coat Roughness', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'),
               ('Height', 'NodeSocketFloat'), ('Wet Mask', 'NodeSocketFloat'), ('Puddle Mask', 'NodeSocketFloat'), ('Streak Mask', 'NodeSocketFloat'),
               ('Puddle Depth', 'NodeSocketFloat')]
    _add_sockets(tree, inputs, outputs)
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (3000, 0)
    g = lambda name: group_in.outputs[name]   # noqa: E731
    n = Net(tree)

    # ---- where am I, and what am I facing
    geometry = n.geometry()
    position = n.mix_vector(g('Use World Geometry'), g('Position'), geometry.outputs['Position'])
    up_vector = n.mix_vector(g('Use World Geometry'), g('Surface Up'), geometry.outputs['Normal'])
    px, py, pz = n.separate(position)
    _, _, nz = n.separate(up_vector)
    ground_like = n.map_range(nz, 0.93, 0.99, 0.0, 1.0, smooth=True)                      # facing up, within about 20 degrees of flat
    wall_like = n.math('SUBTRACT', 1.0, n.map_range(n.math('ABSOLUTE', nz), 0.15, 0.5, 0.0, 1.0, smooth=True))   # standing upright
    roof_like = n.math('MAXIMUM', 0.0, n.math('SUBTRACT', n.math('SUBTRACT', 1.0, ground_like), wall_like))      # in between: a roof slope
    seed_shift = n.math('MULTIPLY', g('Seed'), 17.31)

    # ---- the low spots: a slow wobble over the ground (long along the street), the caller's Lowness, and the dry relief's own low parts
    dip_vector = n.combine(n.math('MULTIPLY', px, 0.55), n.math('ADD', n.math('MULTIPLY', py, 0.32), seed_shift), 0.0)
    dips = n.map_range(n.noise(dip_vector, scale=1.0, detail=3.0, roughness=0.55), 0.33, 0.67, 0.0, 1.0)
    low_relief = n.map_range(n.math('SUBTRACT', 1.0, g('Height')), 0.2, 0.8, 0.0, 1.0)
    depth = n.math('ADD', n.math('ADD', n.math('MULTIPLY', dips, 0.5), n.math('MULTIPLY', g('Lowness'), 0.25)), n.math('MULTIPLY', low_relief, 0.25))
    dial = n.math('POWER', n.math('MAXIMUM', g('Puddles'), 0.0001), PUDDLE_CURVE)
    threshold = n.math('ADD', n.math('SUBTRACT', PUDDLE_THRESHOLD_TOP, n.math('MULTIPLY', dial, PUDDLE_THRESHOLD_RANGE)), g('Puddle Bias'))
    puddle_raw = n.map_range(depth, threshold, n.math('ADD', threshold, 0.06), 0.0, 1.0, smooth=True)
    puddle = n.math('MULTIPLY', n.math('MULTIPLY', puddle_raw, ground_like), n.map_range(g('Puddles'), 0.0, 0.05, 0.0, 1.0))

    # ---- the film of wet over the ground: patchy, and the high parts of the relief stay drier
    patch_vector = n.combine(n.math('MULTIPLY', px, 2.3), n.math('ADD', n.math('MULTIPLY', py, 2.3), seed_shift), n.math('MULTIPLY', pz, 2.3))
    patchy = n.noise(patch_vector, scale=1.0, detail=4.0, roughness=0.6)
    wet_ground_base = n.math('MULTIPLY', g('Wetness'), n.map_range(patchy, 0.25, 0.7, 0.75, 1.0))
    tops = n.map_range(g('Height'), 0.55, 0.85, 0.0, 1.0, smooth=True)
    dry_tops = n.math('MULTIPLY', n.math('MULTIPLY', tops, g('Dry Tops')), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', g('Wetness'), 0.45)))
    wet_ground = n.math('MULTIPLY', wet_ground_base, n.math('SUBTRACT', 1.0, dry_tops))

    # ---- walls: a wet band at the foot (its top edge wavering), rain streaks hanging down (general ones and the caller's Drip Mask), general damp
    above_ground = n.math('SUBTRACT', n.math('SUBTRACT', pz, n.math('MULTIPLY', py, g('Ground Slope'))), g('Ground Offset'))
    edge_vector = n.combine(n.math('MULTIPLY', px, 1.3), n.math('ADD', n.math('MULTIPLY', py, 1.3), seed_shift), 0.0)
    edge_wobble = n.map_range(n.noise(edge_vector, scale=1.0, detail=3.0), 0.3, 0.7, 0.6, 1.5)
    band_top = n.math('MULTIPLY', g('Wall Band'), edge_wobble)
    band = n.math('SUBTRACT', 1.0, n.map_range(above_ground, n.math('MULTIPLY', band_top, 0.15), band_top, 0.0, 1.0, smooth=True))
    streak_vector = n.combine(n.math('MULTIPLY', px, 9.0), n.math('ADD', n.math('MULTIPLY', py, 9.0), seed_shift), n.math('MULTIPLY', pz, 0.7))
    streak_noise = n.noise(streak_vector, scale=1.0, detail=2.0, roughness=0.5)
    general_streak = n.math('MULTIPLY', n.map_range(streak_noise, 0.52, 0.72, 0.0, 1.0, smooth=True), g('Streaks'))
    streak = n.math('MULTIPLY', n.math('MAXIMUM', general_streak, g('Drip Mask')), wall_like)
    wall_general = n.math('MULTIPLY', g('Wall Wetness'), n.map_range(patchy, 0.3, 0.7, 0.6, 1.0))
    wet_wall = n.math('MAXIMUM', n.math('MAXIMUM', n.math('MULTIPLY', band, 0.95), n.math('MULTIPLY', streak, 0.7)), wall_general)

    # ---- all together: ground, wall and roof each wet in their own way; standing water counts as soaked
    wet_roof = n.math('MULTIPLY', g('Wetness'), 0.9)
    wet_by_kind = n.math('ADD', n.math('ADD', n.math('MULTIPLY', ground_like, wet_ground), n.math('MULTIPLY', wall_like, n.math('MULTIPLY', wet_wall, g('Wetness')))),
                         n.math('MULTIPLY', roof_like, wet_roof))
    wet = n.math('MAXIMUM', n.math('MINIMUM', wet_by_kind, 1.0), puddle)

    # ---- the wet look
    soak = n.mix(g('Porosity'), 1.0, g('Darkest'))                  # a porous surface soaked right through is as dark as 'Darkest' times its dry colour
    darken = n.mix(wet, 1.0, soak)
    multiplied = tree.nodes.new('ShaderNodeMix')
    multiplied.data_type = 'RGBA'
    multiplied.blend_type = 'MULTIPLY'
    multiplied.inputs[0].default_value = 1.0
    tree.links.new(g('Colour'), multiplied.inputs[6])
    tree.links.new(n.combine(darken, darken, darken), multiplied.inputs[7])
    saturated = tree.nodes.new('ShaderNodeHueSaturation')
    tree.links.new(n.math('ADD', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', wet, g('Porosity')), 0.3)), saturated.inputs['Saturation'])
    tree.links.new(multiplied.outputs[2], saturated.inputs['Color'])
    water_dark = n.mix(puddle, 1.0, g('Puddle Darkness'))           # the ground under standing water is a little darker again
    final = tree.nodes.new('ShaderNodeMix')
    final.data_type = 'RGBA'
    final.blend_type = 'MULTIPLY'
    final.inputs[0].default_value = 1.0
    tree.links.new(saturated.outputs['Color'], final.inputs[6])
    tree.links.new(n.combine(water_dark, water_dark, water_dark), final.inputs[7])

    smoothness = n.map_range(wet, 0.0, 0.7, 0.0, 1.0, smooth=True)
    rough_film = n.mix(smoothness, g('Roughness'), n.math('MINIMUM', g('Roughness'), g('Wet Roughness')))
    rough_out = n.mix(g('Roughness Effect'), g('Roughness'), n.mix(puddle, rough_film, g('Puddle Roughness')))
    specular_out = n.mix(g('Specular Effect'), 0.5, n.math('ADD', 0.5, n.math('MULTIPLY', wet, g('Specular Boost'))))
    coat_weight = n.math('MULTIPLY', n.math('MINIMUM', n.math('ADD', n.math('MULTIPLY', wet, 0.3), puddle), 1.0), g('Coat Effect'))
    coat_roughness = n.mix(puddle, 0.2, g('Puddle Roughness'))
    flatten = n.math('MAXIMUM', puddle, n.math('MULTIPLY', wet, g('Relief Flatten')))
    normal_out = n.vector_math('NORMALIZE', n.mix_vector(n.math('MULTIPLY', flatten, g('Normal Effect')), g('Normal'), geometry.outputs['Normal']))
    height_out = n.mix(puddle, g('Height'), n.math('MAXIMUM', g('Height'), g('Water Level')))
    colour_out = n.mix_colour(g('Colour Effect'), g('Colour'), final.outputs[2])
    for name, socket in (('Roughness', rough_out), ('Specular IOR Level', specular_out), ('Coat Weight', coat_weight), ('Coat Roughness', coat_roughness),
                         ('Normal', normal_out), ('Height', height_out), ('Wet Mask', wet), ('Puddle Mask', puddle), ('Streak Mask', streak), ('Colour', colour_out),
                         ('Puddle Depth', depth)):
        tree.links.new(socket, group_out.inputs[name])
    return tree


def add_wetness_to_material(material, wetness=0.85, puddles=0.5, rough_image=None, height_image=None, lowness=None, ground_offset=0.0, ground_slope=0.0699,
                            porosity=0.6, seed=0.0, wet_roughness=0.3, wall_band=0.45, wall_wetness=0.35, streaks=0.5, dry_tops=0.5, relief_flatten=0.35,
                            puddle_darkness=0.9, puddle_roughness=0.08, darkest=0.45, specular_boost=0.25, puddle_bias=0.0, position=None, drip=None, debug_output=None):
    """Puts the WETNESS group between a photo-textured material's (colour, normal) and its Principled BSDF and returns the group node.
    rough_image / height_image: optional images (Non-Color), laid with the same coordinates as the colour picture (a roughness picture and a height
    picture from the same Poly Haven set). lowness: optional output socket in this material's tree that says how low the spot is. position: optional
    socket (for example Texture Coordinate 'Object') to measure in instead of the world; with it Use World Geometry is switched off and the surface
    direction is the true normal. drip: optional socket giving the Drip Mask. debug_output: 'Wet Mask', 'Puddle Mask', 'Streak Mask' or 'Puddle Depth'
    shows that mask as plain light instead of the material (a checking view)."""
    tree = material.node_tree
    principled = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    colour_link = next(link for link in tree.links if link.to_socket == principled.inputs['Base Color'])
    normal_link = next((link for link in tree.links if link.to_socket == principled.inputs['Normal']), None)
    group_node = tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = build_wetness_group()
    group_node.name = 'WETNESS'
    group_node.location = (principled.location.x - 350, principled.location.y)
    tree.links.new(colour_link.from_socket, group_node.inputs['Colour'])
    if rough_image is not None:
        rough_node = tree.nodes.new('ShaderNodeTexImage')
        rough_node.image = rough_image
        rough_image.colorspace_settings.name = 'Non-Color'
        tree.links.new(rough_node.outputs['Color'], group_node.inputs['Roughness'])
    else:
        group_node.inputs['Roughness'].default_value = principled.inputs['Roughness'].default_value
    if height_image is not None:
        height_node = tree.nodes.new('ShaderNodeTexImage')
        height_node.image = height_image
        height_image.colorspace_settings.name = 'Non-Color'
        tree.links.new(height_node.outputs['Color'], group_node.inputs['Height'])
    if normal_link is not None:
        tree.links.new(normal_link.from_socket, group_node.inputs['Normal'])
    else:
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        tree.links.new(geometry.outputs['Normal'], group_node.inputs['Normal'])
    if lowness is not None:
        tree.links.new(lowness, group_node.inputs['Lowness'])
    if position is not None:
        group_node.inputs['Use World Geometry'].default_value = 0.0
        tree.links.new(position, group_node.inputs['Position'])
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        tree.links.new(geometry.outputs['Normal'], group_node.inputs['Surface Up'])
    if drip is not None:
        tree.links.new(drip, group_node.inputs['Drip Mask'])
    values = {'Wetness': wetness, 'Puddles': puddles, 'Porosity': porosity, 'Seed': seed, 'Ground Offset': ground_offset, 'Ground Slope': ground_slope,
              'Wet Roughness': wet_roughness, 'Wall Band': wall_band, 'Wall Wetness': wall_wetness, 'Streaks': streaks, 'Dry Tops': dry_tops,
              'Relief Flatten': relief_flatten, 'Puddle Darkness': puddle_darkness, 'Puddle Roughness': puddle_roughness, 'Darkest': darkest,
              'Specular Boost': specular_boost, 'Puddle Bias': puddle_bias}
    for name, value in values.items():
        group_node.inputs[name].default_value = value
    for name, socket in (('Colour', 'Base Color'), ('Roughness', 'Roughness'), ('Specular IOR Level', 'Specular IOR Level'), ('Coat Weight', 'Coat Weight'),
                         ('Coat Roughness', 'Coat Roughness'), ('Normal', 'Normal')):
        tree.links.new(group_node.outputs[name], principled.inputs[socket])
    principled.inputs['Coat IOR'].default_value = 1.33
    if debug_output:
        show_mask(material, group_node, debug_output)
    return group_node


def show_mask(material, group_node, output_name):
    """Checking view: the named output of a WETNESS node shown as plain light (grey) instead of the material."""
    tree = material.node_tree
    output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
    emission = tree.nodes.new('ShaderNodeEmission')
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(group_node.outputs[output_name], combine.inputs[channel])
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])


def drip_chain(tree, position_socket, sources, seed=0.0):
    """Builds, inside a material's tree, one WETNESS DRIP node per source and joins them with Maximum. sources: a list of
    (centre, half_width, top, length). Returns the output socket (the Drip Mask) for add_wetness_to_material(drip=...)."""
    group = build_drip_group()
    result = None
    for index, (centre, half_width, top, length) in enumerate(sources):
        node = tree.nodes.new('ShaderNodeGroup')
        node.node_tree = group
        node.label = f'drip {index}'
        tree.links.new(position_socket, node.inputs['Position'])
        for name, value in (('Centre', centre), ('Half Width', half_width), ('Top', top), ('Length', length), ('Seed', seed + index * 1.9)):
            node.inputs[name].default_value = value
        if result is None:
            result = node.outputs['Mask']
        else:
            maximum = tree.nodes.new('ShaderNodeMath')
            maximum.operation = 'MAXIMUM'
            tree.links.new(result, maximum.inputs[0])
            tree.links.new(node.outputs['Mask'], maximum.inputs[1])
            result = maximum.outputs[0]
    return result
