# What this does: the FIRST DRAFT of the WETNESS layer, a Blender shader node group that can sit between ANY material's dry look (colour, roughness,
# relief height, normal) and its Principled BSDF, and turns it into the wet look: darker and more colourful, smoother, more reflective, a thin clear
# water film, puddles in the low spots (flat, mirror-like, the relief flattened), a wet band along the foot of walls, rain streaks on walls, and the
# tops of the stones (the high parts of the relief) staying drier. It is a test draft, built for the study "09 Research - wet surfaces for the
# street set.md"; the real build is described there. It uses only nodes that Cycles and EEVEE both run (no Voronoi, no AO node, no bake).
# Use (inside Blender):  import wetness_group as wg ;  tree = wg.build_wetness_group() ;  wg.add_wetness_to_material(material, ...)
#
# INPUTS (all can be left at their defaults except the dry look that you plug in):
#   Colour, Roughness, Height (0..1, 0.5 = flat), Normal      the dry look of the material you are putting the layer on
#   Wetness (0..1)        how wet everything is (0 = bone dry, 1 = soaked)
#   Puddles (0..1)        how much standing water (0 = none, 1 = a lot)
#   Porosity (0..1)       how much the surface soaks water up and darkens (stone 0.5 to 0.7, brick 0.7, slate 0.3, painted wood 0.2)
#   Wet Roughness         the roughness a soaked rough surface gets (0.3), Puddle Roughness the roughness of standing water (0.03)
#   Lowness (0..1)        how low the spot is, supplied by the caller (for the road: 1 beside the gutter, 0 on the crown); 0.5 = no opinion
#   Dry Tops (0..1)       how much the high parts of the relief stay drier than the joints and dips
#   Ground Slope, Ground Offset   the ground's rise per metre along +y (the street: tan 4 degrees = 0.0699) and the height of this surface's
#                         ground above the road channel (pavement 0.13); used to measure "height above the ground" for the wet band on walls
#   Wall Band             how high (metres) the wet band at the foot of a wall reaches
#   Streaks (0..1)       how strong the rain streaks on walls are
#   Wall Wetness (0..1)  how wet the whole face of a wall is (driven rain), on top of the band at its foot and the streaks
#   Water Level (0..1)   how high the standing water reaches on the Height scale (0.65: fills the joints and dips, the tops stay out)
#   Seed                  any number; changes where the puddles and streaks fall
#   Colour Effect, Roughness Effect, Specular Effect, Coat Effect, Normal Effect (0..1 each, default 1)   how much of each part of the wet look is used; 0 gives the dry
#                         value back (for switching a part off and for tests)
# OUTPUTS: Colour, Roughness, Specular IOR Level (0.5 = normal), Coat Weight, Coat Roughness (Coat IOR is set outside to 1.33, water),
#   Normal, Height, Wet Mask, Puddle Mask, Streak Mask (the last three are for checking and for baking maps).
import bpy

TREE_NAME = 'WETNESS'


class Net:
    """Tiny helper: makes nodes in one group and chains them. Every helper returns an output socket, so results can be passed on as the next input."""

    def __init__(self, tree):
        self.tree = tree
        self.count = 0

    def _place(self, node):
        node.location = ((self.count % 12) * 200, -(self.count // 12) * 180)
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
        return node.outputs[0] if operation not in ('LENGTH', 'DOT_PRODUCT') else node.outputs['Value']

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


def build_wetness_group():
    existing = bpy.data.node_groups.get(TREE_NAME)
    if existing:
        return existing
    tree = bpy.data.node_groups.new(TREE_NAME, 'ShaderNodeTree')
    inputs = [
        ('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.85), ('Height', 'NodeSocketFloat', 0.5),
        ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)),
        ('Wetness', 'NodeSocketFloat', 0.8), ('Puddles', 'NodeSocketFloat', 0.5), ('Porosity', 'NodeSocketFloat', 0.6),
        ('Wet Roughness', 'NodeSocketFloat', 0.3), ('Puddle Roughness', 'NodeSocketFloat', 0.03),
        ('Lowness', 'NodeSocketFloat', 0.5), ('Dry Tops', 'NodeSocketFloat', 0.5),
        ('Ground Slope', 'NodeSocketFloat', 0.0699), ('Ground Offset', 'NodeSocketFloat', 0.0), ('Wall Band', 'NodeSocketFloat', 0.45),
        ('Streaks', 'NodeSocketFloat', 0.5), ('Wall Wetness', 'NodeSocketFloat', 0.45), ('Water Level', 'NodeSocketFloat', 0.65), ('Seed', 'NodeSocketFloat', 0.0),
        ('Colour Effect', 'NodeSocketFloat', 1.0), ('Roughness Effect', 'NodeSocketFloat', 1.0), ('Specular Effect', 'NodeSocketFloat', 1.0),
        ('Coat Effect', 'NodeSocketFloat', 1.0), ('Normal Effect', 'NodeSocketFloat', 1.0)]
    outputs = [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'),
               ('Coat Weight', 'NodeSocketFloat'), ('Coat Roughness', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'),
               ('Height', 'NodeSocketFloat'), ('Wet Mask', 'NodeSocketFloat'), ('Puddle Mask', 'NodeSocketFloat'), ('Streak Mask', 'NodeSocketFloat')]
    for name, kind, default in inputs:
        socket = tree.interface.new_socket(name, in_out='INPUT', socket_type=kind)
        socket.default_value = default
    for name, kind in outputs:
        tree.interface.new_socket(name, in_out='OUTPUT', socket_type=kind)
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (2600, 0)
    g = lambda name: group_in.outputs[name]   # noqa: E731
    n = Net(tree)

    # ---- where am I, and what am I facing
    geometry = n.geometry()
    position, normal_world = geometry.outputs['Position'], geometry.outputs['Normal']
    px, py, pz = n.separate(position)
    nx, ny, nz = n.separate(normal_world)
    ground_like = n.map_range(nz, 0.93, 0.99, 0.0, 1.0, smooth=True)                      # facing up, within about 20 degrees of flat
    wall_like = n.math('SUBTRACT', 1.0, n.map_range(n.math('ABSOLUTE', nz), 0.15, 0.5, 0.0, 1.0, smooth=True))   # standing upright
    roof_like = n.math('MAXIMUM', 0.0, n.math('SUBTRACT', n.math('SUBTRACT', 1.0, ground_like), wall_like))    # in between: a roof slope
    seed_shift = n.math('MULTIPLY', g('Seed'), 17.31)

    # ---- the low spots: a slow wobble over the ground (long along the street), the caller's Lowness, and the dry relief's own low parts
    dip_vector = n.combine(n.math('MULTIPLY', px, 0.55), n.math('ADD', n.math('MULTIPLY', py, 0.32), seed_shift), 0.0)
    dips = n.map_range(n.noise(dip_vector, scale=1.0, detail=3.0, roughness=0.55), 0.33, 0.67, 0.0, 1.0)           # slow wobble, stretched to use the whole 0..1
    low_relief = n.map_range(n.math('SUBTRACT', 1.0, g('Height')), 0.2, 0.8, 0.0, 1.0)
    depth = n.math('ADD', n.math('ADD', n.math('MULTIPLY', dips, 0.5), n.math('MULTIPLY', g('Lowness'), 0.25)), n.math('MULTIPLY', low_relief, 0.25))
    threshold = n.math('SUBTRACT', 0.97, n.math('MULTIPLY', g('Puddles'), 0.7))
    puddle_raw = n.map_range(depth, threshold, n.math('ADD', threshold, 0.06), 0.0, 1.0, smooth=True)
    puddle = n.math('MULTIPLY', n.math('MULTIPLY', puddle_raw, ground_like), n.map_range(g('Puddles'), 0.0, 0.05, 0.0, 1.0))

    # ---- the film of wet over the ground: patchy, and the high parts of the relief stay drier
    patch_vector = n.combine(n.math('MULTIPLY', px, 2.3), n.math('ADD', n.math('MULTIPLY', py, 2.3), seed_shift), n.math('MULTIPLY', pz, 2.3))
    patchy = n.noise(patch_vector, scale=1.0, detail=4.0, roughness=0.6)
    wet_ground_base = n.math('MULTIPLY', g('Wetness'), n.map_range(patchy, 0.25, 0.7, 0.75, 1.0))
    tops = n.map_range(g('Height'), 0.55, 0.85, 0.0, 1.0, smooth=True)
    dry_tops = n.math('MULTIPLY', n.math('MULTIPLY', tops, g('Dry Tops')), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', g('Wetness'), 0.45)))
    wet_ground = n.math('MULTIPLY', wet_ground_base, n.math('SUBTRACT', 1.0, dry_tops))

    # ---- walls: a wet band at the foot (its top edge wavering) and long rain streaks hanging down
    above_ground = n.math('SUBTRACT', n.math('SUBTRACT', pz, n.math('MULTIPLY', py, g('Ground Slope'))), g('Ground Offset'))
    edge_vector = n.combine(n.math('MULTIPLY', px, 1.3), n.math('ADD', n.math('MULTIPLY', py, 1.3), seed_shift), 0.0)
    edge_wobble = n.map_range(n.noise(edge_vector, scale=1.0, detail=3.0), 0.3, 0.7, 0.6, 1.5)
    band_top = n.math('MULTIPLY', g('Wall Band'), edge_wobble)
    band = n.math('SUBTRACT', 1.0, n.map_range(above_ground, n.math('MULTIPLY', band_top, 0.15), band_top, 0.0, 1.0, smooth=True))
    streak_vector = n.combine(n.math('MULTIPLY', px, 9.0), n.math('ADD', n.math('MULTIPLY', py, 9.0), seed_shift), n.math('MULTIPLY', pz, 0.7))
    streak_noise = n.noise(streak_vector, scale=1.0, detail=2.0, roughness=0.5)
    streak = n.math('MULTIPLY', n.map_range(streak_noise, 0.52, 0.72, 0.0, 1.0, smooth=True), n.math('MULTIPLY', g('Streaks'), wall_like))
    wall_general = n.math('MULTIPLY', g('Wall Wetness'), n.map_range(patchy, 0.3, 0.7, 0.6, 1.0))
    wet_wall = n.math('MAXIMUM', n.math('MAXIMUM', n.math('MULTIPLY', band, 0.95), n.math('MULTIPLY', streak, 0.7)), wall_general)

    # ---- all together: ground, wall and roof each wet in their own way; standing water counts as soaked
    wet_roof = n.math('MULTIPLY', g('Wetness'), 0.9)
    wet_by_kind = n.math('ADD', n.math('ADD', n.math('MULTIPLY', ground_like, wet_ground), n.math('MULTIPLY', wall_like, n.math('MULTIPLY', wet_wall, g('Wetness')))),
                         n.math('MULTIPLY', roof_like, wet_roof))
    wet = n.math('MAXIMUM', n.math('MINIMUM', wet_by_kind, 1.0), puddle)

    # ---- the wet look
    soak = n.mix(g('Porosity'), 1.0, 0.2)                          # Lagarde: the diffuse colour is multiplied by 1 (no pores) .. 0.2 (all pores) when soaked
    darken = n.mix(wet, 1.0, soak)
    multiplied = tree.nodes.new('ShaderNodeMix')
    multiplied.data_type = 'RGBA'
    multiplied.blend_type = 'MULTIPLY'
    multiplied.inputs[0].default_value = 1.0
    tree.links.new(g('Colour'), multiplied.inputs[6])
    tree.links.new(n.combine(darken, darken, darken), multiplied.inputs[7])
    saturated = tree.nodes.new('ShaderNodeHueSaturation')
    saturated.inputs['Saturation'].default_value = 1.0
    tree.links.new(n.math('ADD', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', wet, g('Porosity')), 0.3)), saturated.inputs['Saturation'])
    tree.links.new(multiplied.outputs[2], saturated.inputs['Color'])
    water_dark = n.mix(puddle, 1.0, 0.8)                           # standing water over it is a little darker again
    final = tree.nodes.new('ShaderNodeMix')
    final.data_type = 'RGBA'
    final.blend_type = 'MULTIPLY'
    final.inputs[0].default_value = 1.0
    tree.links.new(saturated.outputs['Color'], final.inputs[6])
    tree.links.new(n.combine(water_dark, water_dark, water_dark), final.inputs[7])

    smoothness = n.map_range(wet, 0.0, 0.7, 0.0, 1.0, smooth=True)
    rough_film = n.mix(smoothness, g('Roughness'), n.math('MINIMUM', g('Roughness'), g('Wet Roughness')))
    rough_out = n.mix(g('Roughness Effect'), g('Roughness'), n.mix(puddle, rough_film, g('Puddle Roughness')))
    specular_out = n.mix(g('Specular Effect'), 0.5, n.math('ADD', 0.5, n.math('MULTIPLY', wet, 0.25)))
    coat_weight = n.math('MULTIPLY', n.math('MINIMUM', n.math('ADD', n.math('MULTIPLY', wet, 0.3), puddle), 1.0), g('Coat Effect'))
    coat_roughness = n.mix(puddle, 0.2, 0.03)
    flatten = n.math('MAXIMUM', puddle, n.math('MULTIPLY', wet, 0.2))
    normal_out = n.vector_math('NORMALIZE', n.mix_vector(n.math('MULTIPLY', flatten, g('Normal Effect')), g('Normal'), normal_world))
    height_out = n.mix(puddle, g('Height'), n.math('MAXIMUM', g('Height'), g('Water Level')))
    colour_out = n.mix_colour(g('Colour Effect'), g('Colour'), final.outputs[2])
    for name, socket in (('Roughness', rough_out), ('Specular IOR Level', specular_out), ('Coat Weight', coat_weight), ('Coat Roughness', coat_roughness),
                         ('Normal', normal_out), ('Height', height_out), ('Wet Mask', wet), ('Puddle Mask', puddle), ('Streak Mask', streak), ('Colour', colour_out)):
        tree.links.new(socket, group_out.inputs[name])
    return tree


def add_wetness_to_material(material, state, rough_image=None, height_image=None, lowness=None, ground_offset=0.0, porosity=0.6, seed=0.0,
                            wet_roughness=0.3, wall_band=0.45, streaks=0.5, dry_tops=0.5, debug_output=None):
    """Puts the WETNESS group between a photo-textured material's (colour, normal) and its Principled BSDF.
    state: dict with 'wetness' and 'puddles'. rough_image / height_image: optional images (Non-Color) laid with the same coordinates as the colour.
    lowness: optional output socket (in this material's tree) that says how low the spot is. debug_output: 'Wet Mask', 'Puddle Mask' or 'Streak Mask'
    shows that mask as plain light instead of the material (a checking view)."""
    tree = material.node_tree
    principled = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    output = next(node for node in tree.nodes if node.type == 'OUTPUT_MATERIAL')
    colour_link = next(link for link in tree.links if link.to_socket == principled.inputs['Base Color'])
    normal_link = next((link for link in tree.links if link.to_socket == principled.inputs['Normal']), None)
    group_node = tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = build_wetness_group()
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
    group_node.inputs['Wetness'].default_value = state['wetness']
    group_node.inputs['Puddles'].default_value = state['puddles']
    group_node.inputs['Porosity'].default_value = porosity
    group_node.inputs['Seed'].default_value = seed
    group_node.inputs['Ground Offset'].default_value = ground_offset
    group_node.inputs['Wet Roughness'].default_value = wet_roughness
    group_node.inputs['Wall Band'].default_value = wall_band
    group_node.inputs['Streaks'].default_value = streaks
    group_node.inputs['Dry Tops'].default_value = dry_tops
    for name, socket in (('Colour', 'Base Color'), ('Roughness', 'Roughness'), ('Specular IOR Level', 'Specular IOR Level'), ('Coat Weight', 'Coat Weight'),
                         ('Coat Roughness', 'Coat Roughness'), ('Normal', 'Normal')):
        tree.links.new(group_node.outputs[name], principled.inputs[socket])
    principled.inputs['Coat IOR'].default_value = 1.33
    if debug_output:
        emission = tree.nodes.new('ShaderNodeEmission')
        combine = tree.nodes.new('ShaderNodeCombineColor')
        for channel in ('Red', 'Green', 'Blue'):
            tree.links.new(group_node.outputs[debug_output], combine.inputs[channel])
        tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return group_node
