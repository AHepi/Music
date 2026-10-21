# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It holds the RUBBISH LAYER for the pit village street (Blender code; it runs only inside Blender). Two parts that share ONE mask:
#
#   1. a MUCK LAYER ("RUBBISH", a Blender node group like WETNESS and JOINTS). It sits after the other two layers on the ground materials:
#          dry look -> WETNESS (water) -> JOINTS (joints between the setts, road only) -> RUBBISH (this file) -> the ground's surface
#      and paints the rubbish itself onto the ground: coal dust, cinders, ash, mud, wet straw, sodden paper scraps and dead leaves, each as colour, roughness and a little relief,
#      and wet where the street is wet (it reads the wetness layer's Wet Mask and Puddle Mask).
#   2. a SCATTER (optional, plate only): a few small separate 3D pieces (cinder and coal lumps, ash heaps, paper scraps, leaves, straw, a broken pot, a stick) laid on the ground
#      by Geometry Nodes where the same mask says there is rubbish.
#
# THE MASK ("where rubbish gathers"), built from five places plus noise:
#   gutter            the channel stones, the kerb, the foot of the kerb and the outer strip of the road (never the middle of the road: see Crown Clear)
#   wall foot         the ground along the foot of the house walls and steps (found from the real geometry: places pictures, see make_places_pictures.py)
#   corners and doorsteps   the foot of each front step, the foot of each rain pipe and lamp post, and inside corners (a step and its wall, a bin and the wall)
#   around props      the ground round the fire drum, sacks, handcart, dustbins, pails, barrel, ladder ... (only the lockout shot file has props)
#   patches           smooth random patches (and a slow change from house to house) break every strip up so that nothing is a clean stripe
# Each place has its own dial, so the person can test "only the gutter", "no rubbish round the props" and so on.
#
# THE CONTROLS of the group RUBBISH (all numbers; defaults in DIALS below; the same names work in apply_rubbish_to_set.py with underscores):
#   Rubbish Amount       0..2   the master dial. 0 = nothing at all = the ground exactly as before. 1 = normal. 2 = heavy.
#   Gutter               0..2   how much rubbish gathers in the gutter, on the kerb and on the road's outer strip.
#   Wall Foot            0..2   how much along the foot of the house walls.
#   Corners And Doorsteps 0..2  how much at the foot of the front steps, rain pipes, lamp posts and in inside corners.
#   Around Props         0..2   how much round the props (lockout shot only).
#   Seed                 any    moves the patches (the same seed gives the same street every time).
#   Patchiness           0..1   0 = a smooth even strip, 1 = broken into separate heaps with bare gaps.
#   Gutter Width         m      how far the gutter's rubbish reaches from the channel onto the road (0.45 m); it never gets nearer the middle than Crown Clear allows.
#   Wall Foot Width      m      how far from the wall the wall foot's rubbish reaches (0.75 m), strongest at the wall.
#   Props Width          m      how far from a prop its rubbish reaches (0.8 m).
#   Crown Clear          0..1   1 = no gutter rubbish inside 1.3 m of the street's middle line (the crown of the road stays clean); 0 = no limit.
#   Dust And Cinders, Ash, Mud, Straw, Paper, Leaves   0..2 each: how much of that KIND of rubbish. 0 switches the kind off, 2 doubles it.
#   Dust Darkness        0..1   how dark the coal dust film is (0.75).
#   Grit Size            0.5..2 the size of cinder grit (1 = about 1.8 cm cells, cinders 0.5 to 1.2 cm across).
#   Relief               0..2   how much the cinders, straw, paper and leaves stand up from the ground (the light and shadow on them); 0 = flat paint.
#   Wet Look             0..1   how much the muck follows the street's wetness (1 = wet cinders are dark and shiny, wet paper is dark and limp; 0 = always dry colours).
# Inputs wired by the caller (not dials): Colour, Roughness, Specular IOR Level, Coat Weight, Normal (what the layer before gave) and Wet Mask, Puddle Mask (from WETNESS).
# Outputs: the five surface values, and the masks for checking: Rubbish Mask (all places together), Gutter Part, Wall Part, Corner Part, Props Part, Mud Part.
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath('proc-work/street_wet')        # street_wet (the real one; this copy lives under painter_round_2/plate)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.dont_write_bytecode = True
import wetness_layer as wl  # noqa: E402

TREE_NAME = 'RUBBISH'
MAPS = os.path.join(RUBBISH, 'maps')
X0, X1, Y0, Y1 = -4.5, 4.5, -12.0, 72.0                 # what the places pictures cover (make_places_pictures.py)
DIST_SCALE = 1.275                                        # a places picture value of 1.0 means this many metres
GUTTER_CENTRE, GUTTER_HALF = 2.35, 0.15                   # the channel stones lie between |x| 2.2 and 2.5
KERB_SIDE_REACH = 0.45                                    # how far the gutter's rubbish reaches over the kerb and onto the pavement
CROWN_FROM, CROWN_TO = 1.3, 1.8                           # Crown Clear: no gutter rubbish nearer the middle line than 1.3 m, full strength from 1.8 m

# short name, socket name, default, minimum, maximum, what it does
DIALS = [
    ('amount', 'Rubbish Amount', 1.4, 0.0, 2.0, 'Master dial: 0 = no rubbish at all, 1 = round 1 normal, 1.4 = the round 2 plate default (the checker found the street shots too thin at 1), 2 = heavy'),
    ('gutter', 'Gutter', 1.0, 0.0, 2.0, 'Rubbish in the gutter, on the kerb and on the outer strip of the road'),
    ('wall_foot', 'Wall Foot', 1.0, 0.0, 2.0, 'Rubbish along the foot of the house walls'),
    ('corners', 'Corners And Doorsteps', 1.0, 0.0, 2.0, 'Rubbish at the foot of the front steps, rain pipes, lamp posts and in inside corners'),
    ('props', 'Around Props', 1.0, 0.0, 2.0, 'Rubbish round the props: drum, sacks, cart, bins, pails (lockout shot only)'),
    ('seed', 'Seed', 0.0, -1000.0, 1000.0, 'Moves the patches; the same seed gives the same street'),
    ('patchiness', 'Patchiness', 0.7, 0.0, 1.0, '0 = smooth even strips, 1 = separate heaps with bare gaps (0.55 in round 1; 0.7 for the round 2 plate so that the heaps gather)'),
    ('gutter_width', 'Gutter Width', 0.45, 0.05, 1.5, 'Metres the gutter rubbish reaches onto the road'),
    ('wall_width', 'Wall Foot Width', 0.6, 0.1, 2.0, 'Metres the wall foot rubbish reaches from the wall (0.75 in round 1; 0.6 for the round 2 plate so that the heaps hug the wall and the steps)'),
    ('props_width', 'Props Width', 0.8, 0.1, 1.5, 'Metres the rubbish reaches from a prop'),
    ('crown_clear', 'Crown Clear', 1.0, 0.0, 1.0, '1 = never on the crown of the road (nothing within 1.3 m of the middle line)'),
    ('dust', 'Dust And Cinders', 1.0, 0.0, 2.0, 'Coal dust film, cinders and grit'),
    ('ash', 'Ash', 1.0, 0.0, 2.0, 'Pale ash (strongest at doorsteps and round the drum)'),
    ('mud', 'Mud', 1.0, 0.0, 2.0, 'Brown mud (strongest at the gutter bottom and the foot of rain pipes)'),
    ('straw', 'Straw', 1.0, 0.0, 2.0, 'Wet straw strokes'),
    ('paper', 'Paper', 1.0, 0.0, 2.0, 'Sodden paper scraps (plain grey-brown, no print)'),
    ('leaves', 'Leaves', 1.0, 0.0, 2.0, 'Dead leaves, a few green'),
    ('dust_darkness', 'Dust Darkness', 0.75, 0.0, 1.0, 'How dark the coal dust film is'),
    ('grit_size', 'Grit Size', 1.0, 0.5, 2.0, 'Size of the cinder grit (1 = about 1.8 cm cells)'),
    ('relief', 'Relief', 1.0, 0.0, 2.0, 'How much the pieces stand up from the ground in the light (0 = flat paint)'),
    ('wet_look', 'Wet Look', 1.0, 0.0, 1.0, 'How much the muck follows the street wetness (0 = always dry colours)'),
]
DEFAULTS = {key: default for key, _, default, _, _, _ in DIALS}
DIAL_SOCKETS = {key: name for key, name, _, _, _, _ in DIALS}
PLACE_PICTURES = {'street': ('places_street_a.png', 'places_street_b.png'), 'lockout': ('places_lockout_a.png', 'places_lockout_b.png')}

# the colours of the kinds of rubbish (linear light, as Blender wants them): dry, then wet. Chosen by eye for a 1926 colliery village: coal dust, cinder, ash, mud, straw, paper, leaf.
COLOURS = dict(
    dust=((0.050, 0.046, 0.043), (0.014, 0.013, 0.013)),
    cinder=((0.030, 0.028, 0.027), (0.011, 0.010, 0.010)),
    clinker=((0.115, 0.082, 0.060), (0.045, 0.030, 0.022)),
    ash=((0.215, 0.205, 0.195), (0.040, 0.039, 0.039)),
    mud=((0.085, 0.062, 0.043), (0.030, 0.021, 0.014)),
    straw=((0.36, 0.265, 0.105), (0.145, 0.098, 0.040)),
    paper=((0.34, 0.305, 0.255), (0.115, 0.100, 0.082)),
    leaf_brown=((0.105, 0.052, 0.020), (0.040, 0.020, 0.008)),
    leaf_orange=((0.17, 0.080, 0.022), (0.062, 0.030, 0.010)),
    leaf_green=((0.040, 0.058, 0.013), (0.016, 0.024, 0.006)),
)
# the roughness of each kind: dry, wet
ROUGHNESS = dict(dust=(0.97, 0.55), cinder=(0.92, 0.62), ash=(0.97, 0.50), mud=(0.90, 0.22), straw=(0.88, 0.72), paper=(0.80, 0.35), leaf=(0.80, 0.40))


# ------------------------------------------------------------------------------------------------------------------------------- a builder that works in a shader tree or a geometry tree
class Builder(wl.Net):
    """wl.Net plus a few more helpers. kind = 'shader' (a material node group) or 'geometry' (a Geometry Nodes group): the Math, Map Range, Mix, Noise and Vector nodes are the
    same in both, only the picture look-up and the colour splitter differ."""

    def __init__(self, tree, kind):
        super().__init__(tree)
        self.kind = kind

    def smooth(self, value, lo, hi):
        return self.map_range(value, lo, hi, 0.0, 1.0, smooth=True)

    def lin(self, value, lo, hi):
        return self.map_range(value, lo, hi, 0.0, 1.0)

    def add(self, a, b):
        return self.math('ADD', a, b)

    def sub(self, a, b):
        return self.math('SUBTRACT', a, b)

    def mul(self, a, b):
        return self.math('MULTIPLY', a, b)

    def clamp01(self, a):
        return self.math('ADD', a, 0.0, clamp=True)

    def maximum(self, a, b):
        return self.math('MAXIMUM', a, b)

    def power(self, a, b):
        return self.math('POWER', self.math('MAXIMUM', a, 0.0), b)

    def lerp(self, fac, a, b):
        return self.mix(fac, a, b)

    def one_minus(self, a):
        return self.math('SUBTRACT', 1.0, a)

    def sep_colour(self, colour):
        node = self._place(self.tree.nodes.new('ShaderNodeSeparateColor' if self.kind == 'shader' else 'FunctionNodeSeparateColor'))
        self.tree.links.new(colour, node.inputs['Color'])
        return node.outputs['Red'], node.outputs['Green'], node.outputs['Blue']

    def picture(self, vector, name, label):
        """Looks up a places picture by the (u, v, 0) vector; returns (red, green, blue). The picture itself is put in by set_places()."""
        if self.kind == 'shader':
            node = self._place(self.tree.nodes.new('ShaderNodeTexImage'))
            node.interpolation, node.extension = 'Linear', 'EXTEND'
            node.name, node.label = name, label
            self.tree.links.new(vector, node.inputs['Vector'])
        else:
            node = self._place(self.tree.nodes.new('GeometryNodeImageTexture'))
            node.interpolation, node.extension = 'Linear', 'EXTEND'
            node.name, node.label = name, label
            self.tree.links.new(vector, node.inputs['Vector'])
        return self.sep_colour(node.outputs['Color'])

    def voronoi(self, vector, scale, randomness=1.0):
        """Cells: returns (distance to the cell's middle in cell widths, three random numbers 0..1 that are the same all over one cell)."""
        node = self._place(self.tree.nodes.new('ShaderNodeTexVoronoi'))
        node.voronoi_dimensions = '3D'
        node.feature = 'F1'
        node.distance = 'EUCLIDEAN'
        self.tree.links.new(vector, node.inputs['Vector'])
        self._feed(node, node.inputs.find('Scale'), scale)
        node.inputs['Randomness'].default_value = randomness
        r, g, b = self.sep_colour(node.outputs['Color'])
        return node.outputs['Distance'], r, g, b

    def voronoi_edge(self, vector, scale, randomness=1.0):
        """The same cells as voronoi() (same vector, scale and randomness), but gives the distance to the nearest cell WALL (0 at a wall, about 0.3 to 0.5 in the middle): cells become angular lumps."""
        node = self._place(self.tree.nodes.new('ShaderNodeTexVoronoi'))
        node.voronoi_dimensions = '3D'
        node.feature = 'DISTANCE_TO_EDGE'
        self.tree.links.new(vector, node.inputs['Vector'])
        self._feed(node, node.inputs.find('Scale'), scale)
        node.inputs['Randomness'].default_value = randomness
        return node.outputs['Distance']

    def noise_at(self, x, y, z, scale, detail=3.0, rough=0.5):
        return self.noise(self.combine(x, y, z), scale=scale, detail=detail, roughness=rough)

    def colour(self, rgb):
        node = self._place(self.tree.nodes.new('ShaderNodeRGB'))
        node.outputs[0].default_value = (*rgb, 1.0)
        return node.outputs[0]


# ------------------------------------------------------------------------------------------------------------------------------- the mask (the same nodes in the shader and in the scatter)
def build_terms(b, dial, position):
    """Makes the rubbish mask's nodes in the builder's tree. dial(name) gives the socket of a dial by its short name. position = the world position vector socket.
    Returns a dict of sockets, all 0..1 unless said: mask (all places together, times Rubbish Amount), gutter, wall, corner (catch points + corners), props, core (the gutter bottom),
    door, feet (rain pipe and lamp post feet), corner_only, d_wall and d_prop (distances in metres), house (0.6..1.35), px, py, pz, inside_picture."""
    px, py, pz = b.separate(position)
    ax = b.math('ABSOLUTE', px)
    seed = b.mul(dial('seed'), 17.31)
    patchy = dial('patchiness')

    def broken(noise_value, lo=0.33, hi=0.66, floor=0.12):
        """a patch factor: 1 everywhere when Patchiness is 0; otherwise the noise (shaped to 0..1) with a small floor, so that heaps and bare gaps alternate"""
        shaped = b.lin(noise_value, lo, hi)
        return b.lerp(patchy, 1.0, b.add(floor, b.mul(shaped, 1.0 - floor + 0.1)))
    # a slow change from house to house (0.6 to 1.35 times)
    house_noise = b.noise_at(b.add(b.mul(py, 0.11), seed), 4.2, 0.0, 1.0, detail=1.0)
    house = b.map_range(house_noise, 0.3, 0.7, 0.6, 1.35)
    # ---- the places pictures: u across the street, v along it
    u = b.math('DIVIDE', b.sub(px, X0), X1 - X0)
    v = b.math('DIVIDE', b.sub(py, Y0), Y1 - Y0)
    inside = b.mul(b.mul(b.lin(u, 0.0, 0.01), b.lin(u, 1.0, 0.99)), b.mul(b.lin(v, 0.0, 0.004), b.lin(v, 1.0, 0.996)))
    vector = b.combine(u, v, 0.0)
    a_red, a_green, a_blue = b.picture(vector, 'places_a', 'places picture A')
    b_red, b_green, b_blue = b.picture(vector, 'places_b', 'places picture B')
    d_wall = b.mul(a_red, DIST_SCALE)
    d_prop = b.mul(a_green, DIST_SCALE)
    # ---- the gutter: full strength on the channel stones, falling away over Gutter Width on the road side and over 0.45 m over the kerb and onto the pavement
    across = b.math('ABSOLUTE', b.sub(ax, GUTTER_CENTRE))
    outside = b.maximum(b.sub(across, GUTTER_HALF), 0.0)
    reach = b.mix(b.math('LESS_THAN', ax, GUTTER_CENTRE), KERB_SIDE_REACH, dial('gutter_width'))
    gutter_shape = b.one_minus(b.smooth(outside, 0.0, reach))
    # the crown stays clean: nothing nearer the middle line than CROWN_FROM (full strength from CROWN_TO), as far as Crown Clear says
    crown = b.lerp(dial('crown_clear'), 1.0, b.smooth(ax, CROWN_FROM, CROWN_TO))
    # the kerb stone's top is a raised stone: less rubbish stays on it than at its foot
    kerb_top = b.mul(b.smooth(ax, 2.48, 2.52), b.one_minus(b.smooth(ax, 2.66, 2.72)))
    gutter_shape = b.mul(gutter_shape, b.sub(1.0, b.mul(kerb_top, 0.45)))
    core = b.one_minus(b.smooth(b.math('ABSOLUTE', b.sub(ax, GUTTER_CENTRE - 0.02)), 0.05, 0.22))      # the very bottom of the channel (mud collects here)
    gutter_streaks = broken(b.noise_at(b.add(b.mul(px, 2.6), seed), b.add(b.mul(py, 0.34), b.mul(seed, 0.37)), 1.7, 1.0, detail=3.0, rough=0.55))
    gutter = b.mul(b.mul(b.mul(dial('gutter'), gutter_shape), b.mul(crown, house)), gutter_streaks)
    # ---- the foot of the walls, from the real geometry
    wall_shape = b.power(b.one_minus(b.smooth(d_wall, 0.0, dial('wall_width'))), 1.5)
    wall_drifts = broken(b.noise_at(b.mul(px, 2.0), b.add(b.mul(py, 0.8), seed), b.add(3.3, b.mul(seed, 0.21)), 1.0, detail=3.0, rough=0.55))
    wall = b.mul(b.mul(b.mul(dial('wall_foot'), wall_shape), b.mul(house, wall_drifts)), inside)
    # ---- doorsteps, rain pipe and lamp post feet, inside corners
    door, feet, corner_only = b_green, b_blue, b_red
    catch_shape = b.maximum(b.maximum(door, feet), b.mul(corner_only, 0.9))
    catch_patches = broken(b.noise_at(b.mul(px, 3.1), b.add(b.mul(py, 3.1), seed), 9.0, 1.0, detail=2.0, rough=0.5), floor=0.35)
    catch_gate = b.mul(b.mul(dial('corners'), catch_patches), inside)
    corner = b.mul(catch_shape, catch_gate)
    door_t, feet_t, corner_t = b.mul(door, catch_gate), b.mul(feet, catch_gate), b.mul(b.mul(corner_only, 0.9), catch_gate)
    # ---- round the props
    prop_shape = b.power(b.one_minus(b.smooth(d_prop, 0.0, dial('props_width'))), 1.3)
    prop_patches = broken(b.noise_at(b.mul(px, 1.9), b.add(b.mul(py, 1.9), seed), 17.0, 1.0, detail=3.0, rough=0.55), floor=0.3)
    props = b.mul(b.mul(dial('props'), prop_shape), b.mul(prop_patches, inside))
    # a prop's own footprint is hidden: keep it from showing as a ring of rubbish INSIDE the prop (distance almost 0 = touching)
    combined = b.one_minus(b.mul(b.mul(b.one_minus(b.clamp01(gutter)), b.one_minus(b.clamp01(wall))), b.mul(b.one_minus(b.clamp01(corner)), b.one_minus(b.clamp01(props)))))
    amount = dial('amount')
    mask = b.clamp01(b.mul(combined, amount))
    scaled = lambda term: b.clamp01(b.mul(term, amount))      # noqa: E731
    return dict(mask=mask, gutter=scaled(gutter), wall=scaled(wall), corner=scaled(corner), props=scaled(props), core=core, door=scaled(door_t), feet=scaled(feet_t),
                corner_only=scaled(corner_t), d_wall=d_wall, d_prop=d_prop, house=house, px=px, py=py, pz=pz, inside=inside, seed=seed, amount=amount)


# ------------------------------------------------------------------------------------------------------------------------------- the muck layer (shader group)
def build_rubbish_group():
    existing = bpy.data.node_groups.get(TREE_NAME)
    if existing:
        return existing
    tree = bpy.data.node_groups.new(TREE_NAME, 'ShaderNodeTree')
    for name, kind, default in (('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.85), ('Specular IOR Level', 'NodeSocketFloat', 0.5),
                                ('Coat Weight', 'NodeSocketFloat', 0.0), ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)), ('Wet Mask', 'NodeSocketFloat', 0.0),
                                ('Puddle Mask', 'NodeSocketFloat', 0.0)):
        socket = tree.interface.new_socket(name, in_out='INPUT', socket_type=kind)
        socket.default_value = default
        if name == 'Normal':
            socket.hide_value = True
    for key, name, default, lo, hi, text in DIALS:
        socket = tree.interface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat')
        socket.default_value, socket.min_value, socket.max_value, socket.description = default, lo, hi, text
    for name, kind in (('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'), ('Coat Weight', 'NodeSocketFloat'),
                       ('Normal', 'NodeSocketVector'), ('Rubbish Mask', 'NodeSocketFloat'), ('Gutter Part', 'NodeSocketFloat'), ('Wall Part', 'NodeSocketFloat'),
                       ('Corner Part', 'NodeSocketFloat'), ('Props Part', 'NodeSocketFloat'), ('Mud Part', 'NodeSocketFloat')):
        tree.interface.new_socket(name, in_out='OUTPUT', socket_type=kind)
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (4000, 0)
    b = Builder(tree, 'shader')
    dial = lambda key: group_in.outputs[DIAL_SOCKETS[key]]   # noqa: E731
    geometry = b.geometry()
    t = build_terms(b, dial, geometry.outputs['Position'])
    px, py, pz, seed = t['px'], t['py'], t['pz'], t['seed']
    wet = b.mul(group_in.outputs['Wet Mask'], dial('wet_look'))
    puddle = group_in.outputs['Puddle Mask']
    cover = b.sub(1.0, b.mul(puddle, 0.8))                   # standing water covers the dulling and the relief of the muck (the colour stays: you see it through the water)
    mask = t['mask']
    # rubbish lies on surfaces that face up: it does not stick to the upright face of a kerb stone or a step (full from 0.93 of "straight up" down to nothing at 0.75)
    _, _, normal_z = b.separate(geometry.outputs['Normal'])
    up = b.smooth(normal_z, 0.75, 0.93)
    kind_colour = lambda name: b.mix_colour(wet, b.colour(COLOURS[name][0]), b.colour(COLOURS[name][1]))      # noqa: E731
    kind_rough = lambda name: b.mix(wet, ROUGHNESS[name][0], ROUGHNESS[name][1])                              # noqa: E731
    # ---- coal dust film: a soft dark film over the stone wherever the mask is, mottled
    mottle = b.lin(b.noise_at(b.mul(px, 7.0), b.mul(py, 7.0), b.mul(pz, 7.0), 1.0, detail=4.0, rough=0.6), 0.3, 0.7)
    film = b.clamp01(b.mul(b.mul(b.mul(b.power(mask, 0.85), b.add(0.55, b.mul(mottle, 0.7))), dial('dust')), dial('dust_darkness')))
    # ---- cinders: angular lumps. The ground is cut into random polygon cells (about 1.8 cm across at Grit Size 1, and a second set of 4 cm cells for bigger lumps); a cell holds a lump when the
    # local rubbish is stronger than the cell's own random number; each lump is the cell shrunk by a small gap with a ragged edge, so it looks like broken cinder, not a round dot
    pos = geometry.outputs['Position']
    ragged_cinder = b.mul(b.sub(b.noise_at(b.mul(px, 160.0), b.mul(py, 160.0), b.mul(pz, 160.0), 1.0, detail=2.0), 0.5), 0.16)

    def lumps(scale, cover, edge_soft):
        d_edge = b.voronoi_edge(pos, scale)
        _, rr, rg, rb = b.voronoi(pos, scale)
        pick = b.clamp01(b.mul(b.sub(cover, rg), 7.0))
        gap = b.add(0.03, b.mul(rb, 0.07))
        body = b.smooth(b.add(d_edge, ragged_cinder), gap, b.add(gap, 0.04))
        dome = b.smooth(b.add(d_edge, ragged_cinder), gap, b.add(gap, edge_soft))
        return b.mul(pick, body), b.mul(b.mul(pick, dome), b.add(0.4, b.mul(rr, 0.6))), rr, rb
    cluster = b.power(b.lin(b.noise_at(b.mul(px, 2.4), b.add(b.mul(py, 2.4), seed), b.mul(pz, 2.4), 1.0, detail=3.0), 0.32, 0.68), 1.4)
    cinder_cover = b.mul(b.mul(mask, b.add(0.08, b.mul(cluster, 0.85))), b.mul(dial('dust'), 0.9))
    grit_scale = b.math('DIVIDE', 55.0, dial('grit_size'))
    cinder_a, cinder_height, cr, cb = lumps(grit_scale, cinder_cover, 0.22)
    big_a, big_height, br_, bb_ = lumps(b.math('DIVIDE', 24.0, dial('grit_size')), b.mul(cinder_cover, 0.30), 0.30)
    # a lump is dark grey cinder, brown clinker or (a few) pale ash grit, chosen by the cell's random number; the big lumps are black coal or clinker
    clinker_pick = b.smooth(cr, 0.58, 0.66)
    ash_grit_pick = b.smooth(cr, 0.90, 0.95)
    cinder_colour = b.mix_colour(ash_grit_pick, b.mix_colour(clinker_pick, kind_colour('cinder'), kind_colour('clinker')), kind_colour('ash'))
    big_colour = b.mix_colour(b.smooth(br_, 0.55, 0.65), kind_colour('cinder'), kind_colour('clinker'))
    # fine grit, 3 to 6 mm: dark specks (cheap noise) that make the film gritty
    grit_noise = b.noise_at(b.mul(px, 210.0), b.mul(py, 210.0), b.mul(pz, 210.0), 1.0, detail=1.0, rough=0.5)
    grit_a = b.mul(b.smooth(grit_noise, b.sub(0.66, b.mul(b.power(mask, 0.8), 0.07)), b.sub(0.70, b.mul(b.power(mask, 0.8), 0.07))), b.mul(b.power(mask, 0.8), b.mul(dial('dust'), 0.9)))
    # ---- mud: brown paste at the gutter bottom and the foot of rain pipes and lamp posts (and a little along the wall foot); ragged edges
    mud_weight = b.clamp01(b.mul(b.add(b.add(b.mul(t['core'], b.mul(1.2, b.clamp01(b.mul(t['gutter'], 1.6)))), b.mul(t['feet'], 0.85)), b.mul(t['wall'], 0.3)), dial('mud')))
    mud_noise = b.noise_at(b.mul(px, 3.5), b.add(b.mul(py, 3.5), seed), b.mul(pz, 3.5), 1.0, detail=4.0, rough=0.6)
    mud_a = b.mul(b.smooth(b.add(b.mul(mud_noise, 0.6), b.mul(mud_weight, 0.9)), 0.55, 0.75), b.lin(mud_weight, 0.02, 0.10))
    # ---- ash: soft pale patches round the doorsteps and the drum (and a little elsewhere)
    ash_weight = b.clamp01(b.mul(b.maximum(b.maximum(b.mul(t['props'], 0.95), b.mul(t['door'], 0.8)), b.mul(t['wall'], 0.22)), dial('ash')))
    ash_noise = b.noise_at(b.mul(px, 4.6), b.add(b.mul(py, 4.6), seed), b.mul(pz, 4.6), 1.0, detail=4.0, rough=0.6)
    ash_a = b.mul(b.smooth(b.add(b.mul(ash_noise, 0.55), b.mul(ash_weight, 0.85)), 0.5, 0.72), b.lin(ash_weight, 0.02, 0.10))
    # ---- wet straw: thin strokes 6 mm wide and 5 to 15 cm long, in two directions (mostly along the street), at the kerb foot and the wall foot
    def strokes(angle, shift, thin, long_):
        c, s = math.cos(angle), math.sin(angle)
        xr = b.add(b.mul(px, c), b.mul(py, -s))
        yr = b.add(b.mul(px, s), b.mul(py, c))
        return b.noise_at(b.add(b.mul(xr, thin), shift), b.mul(yr, long_), 0.0, 1.0, detail=1.0, rough=0.5)
    straw_weight = b.clamp01(b.mul(b.add(b.mul(t['gutter'], 0.9), b.mul(t['wall'], 0.8)), b.mul(dial('straw'), 0.6)))
    straw_cut = b.sub(0.735, b.mul(straw_weight, 0.12))             # a stroke is where the stretched noise is above this
    straw_a = b.maximum(b.smooth(strokes(0.10, seed, 130.0, 10.0), straw_cut, b.add(straw_cut, 0.045)), b.smooth(strokes(1.05, b.add(seed, 5.0), 130.0, 10.0), straw_cut, b.add(straw_cut, 0.045)))
    straw_a = b.mul(straw_a, b.lin(straw_weight, 0.03, 0.12))
    # ---- sodden paper: flat grey-beige scraps 5 to 10 cm, ragged edges; plain (no print)
    paper_weight = b.clamp01(b.mul(b.add(b.add(b.mul(t['wall'], 0.7), b.mul(t['gutter'], 0.5)), b.mul(t['corner'], 0.9)), b.mul(dial('paper'), 0.5)))
    pd, pr, pg, pb = b.voronoi(pos, 6.5)
    paper_pick = b.clamp01(b.mul(b.sub(paper_weight, pg), 8.0))
    paper_size = b.add(0.17, b.mul(pb, 0.17))
    ragged = b.mul(b.sub(b.noise_at(b.mul(px, 55.0), b.mul(py, 55.0), b.mul(pz, 55.0), 1.0, detail=2.0), 0.5), 0.22)
    paper_a = b.mul(paper_pick, b.one_minus(b.smooth(b.add(pd, ragged), b.mul(paper_size, 0.85), paper_size)))
    crumple = b.add(0.82, b.mul(b.noise_at(b.mul(px, 45.0), b.mul(py, 45.0), b.mul(pz, 45.0), 1.0, detail=3.0, rough=0.6), 0.36))
    # ---- dead leaves: oval, 4 to 6 cm, brown, some orange-brown, a few green; mostly at rain pipe feet and in corners
    leaf_weight = b.clamp01(b.mul(b.add(b.add(b.mul(t['feet'], 0.9), b.mul(t['corner_only'], 0.5)), b.mul(t['wall'], 0.28)), b.mul(dial('leaves'), 0.7)))
    stretched = b.combine(b.mul(px, 1.0), b.mul(py, 0.55), b.mul(pz, 1.0))
    ld, lr, lg, lb = b.voronoi(stretched, 17.0)
    leaf_pick = b.clamp01(b.mul(b.sub(leaf_weight, lg), 8.0))
    leaf_size = b.add(0.30, b.mul(lb, 0.22))
    leaf_a = b.mul(leaf_pick, b.one_minus(b.smooth(ld, b.mul(leaf_size, 0.8), leaf_size)))
    leaf_colour = b.mix_colour(b.smooth(lr, 0.80, 0.86), b.mix_colour(b.smooth(lr, 0.40, 0.50), kind_colour('leaf_brown'), kind_colour('leaf_orange')), kind_colour('leaf_green'))
    # ---- only on surfaces that face up
    film, mud_a, ash_a = b.mul(film, up), b.mul(mud_a, up), b.mul(ash_a, up)
    cinder_a, big_a, grit_a, straw_a, paper_a, leaf_a = b.mul(cinder_a, up), b.mul(big_a, up), b.mul(grit_a, up), b.mul(straw_a, up), b.mul(paper_a, up), b.mul(leaf_a, up)
    cinder_height, big_height = b.mul(cinder_height, up), b.mul(big_height, up)
    # ---- put them on, bottom to top: dust film, mud, ash, cinders, grit, straw, paper, leaves
    base = group_in.outputs['Colour']
    c = b.mix_colour(film, base, kind_colour('dust'))
    c = b.mix_colour(b.mul(mud_a, 0.95), c, kind_colour('mud'))
    c = b.mix_colour(b.mul(ash_a, 0.92), c, kind_colour('ash'))
    c = b.mix_colour(b.mul(cinder_a, 0.97), c, cinder_colour)
    c = b.mix_colour(b.mul(big_a, 0.97), c, big_colour)
    c = b.mix_colour(b.mul(grit_a, 0.9), c, kind_colour('cinder'))
    c = b.mix_colour(b.mul(straw_a, 0.95), c, kind_colour('straw'))
    paper_c = b.mix_colour(b.sub(1.0, crumple), kind_colour('paper'), b.colour((0.0, 0.0, 0.0)))
    c = b.mix_colour(b.mul(paper_a, 0.96), c, paper_c)
    c = b.mix_colour(b.mul(leaf_a, 0.96), c, leaf_colour)
    # ---- roughness, shine and relief
    total = b.one_minus(b.mul(b.mul(b.mul(b.one_minus(film), b.one_minus(mud_a)), b.mul(b.mul(b.one_minus(ash_a), b.one_minus(cinder_a)), b.one_minus(big_a))), b.mul(b.one_minus(straw_a), b.mul(b.one_minus(paper_a), b.one_minus(leaf_a)))))
    rough = b.mix(b.mul(film, cover), group_in.outputs['Roughness'], kind_rough('dust'))
    rough = b.mix(b.mul(b.mul(mud_a, cover), 0.95), rough, kind_rough('mud'))
    rough = b.mix(b.mul(b.mul(ash_a, cover), 0.9), rough, kind_rough('ash'))
    rough = b.mix(b.mul(b.mul(b.maximum(b.maximum(cinder_a, big_a), grit_a), cover), 0.95), rough, kind_rough('cinder'))
    rough = b.mix(b.mul(b.mul(b.maximum(straw_a, paper_a), cover), 0.9), rough, b.mix(b.smooth(paper_a, 0.0, 0.5), kind_rough('straw'), kind_rough('paper')))
    rough = b.mix(b.mul(b.mul(leaf_a, cover), 0.9), rough, kind_rough('leaf'))
    dulling = b.mul(b.clamp01(b.add(b.add(b.mul(film, 0.8), b.mul(ash_a, 0.9)), b.add(b.mul(cinder_a, 0.7), b.mul(straw_a, 0.6)))), cover)
    spec = b.mul(group_in.outputs['Specular IOR Level'], b.sub(1.0, b.mul(dulling, 0.55)))
    coat = b.mul(group_in.outputs['Coat Weight'], b.sub(1.0, b.mul(dulling, 0.85)))
    coat = b.maximum(coat, b.mul(b.mul(mud_a, wet), 0.45))                              # wet mud has a film of water on it
    height = b.add(b.add(b.add(b.mul(cinder_height, 1.0), b.mul(big_height, 1.3)), b.mul(grit_a, 0.25)), b.add(b.add(b.mul(straw_a, 0.18), b.mul(paper_a, 0.22)), b.add(b.mul(leaf_a, 0.5), b.mul(ash_a, 0.12))))
    height = b.sub(height, b.mul(mud_a, 0.2))
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.012
    tree.links.new(b.mul(b.mul(dial('relief'), 1.0), cover), bump.inputs['Strength'])
    tree.links.new(height, bump.inputs['Height'])
    tree.links.new(group_in.outputs['Normal'], bump.inputs['Normal'])
    for name, socket in (('Colour', c), ('Roughness', rough), ('Specular IOR Level', spec), ('Coat Weight', coat), ('Normal', bump.outputs['Normal']),
                         ('Rubbish Mask', mask), ('Gutter Part', t['gutter']), ('Wall Part', t['wall']), ('Corner Part', t['corner']), ('Props Part', t['props']), ('Mud Part', mud_weight)):
        tree.links.new(socket, group_out.inputs[name])
    return tree


def _image(path, colour_space='Non-Color'):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colour_space
    return image


def set_places(kind):
    """Lays the places pictures of 'street' (the street copy) or 'lockout' (the lockout shot file, with its props) into the muck layer and the scatter."""
    a_name, b_name = PLACE_PICTURES[kind]
    a_image, b_image = _image(os.path.join(MAPS, a_name)), _image(os.path.join(MAPS, b_name))
    group = bpy.data.node_groups.get(TREE_NAME)
    trees = [group] if group else []
    scatter = bpy.data.node_groups.get(SCATTER_TREE_NAME)
    if scatter:
        trees.append(scatter)
    for tree in trees:
        for node in tree.nodes:
            if node.name == 'places_a':
                if node.bl_idname == 'ShaderNodeTexImage':
                    node.image = a_image
                else:
                    node.inputs['Image'].default_value = a_image
            elif node.name == 'places_b':
                if node.bl_idname == 'ShaderNodeTexImage':
                    node.image = b_image
                else:
                    node.inputs['Image'].default_value = b_image


SCATTER_TREE_NAME = 'RUBBISH PIECES'
SHADER_MATERIALS = ('street_setts', 'pavement_flags', 'channel_stones', 'kerb_stone')


def add_rubbish_to_material(material, wetness_node, **dials):
    """Puts the RUBBISH group between whatever feeds the material's Principled BSDF now (the wetness layer, or JOINTS after it) and the Principled BSDF. Returns (group_node, undo)."""
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    names = ('Base Color', 'Roughness', 'Specular IOR Level', 'Coat Weight', 'Normal')
    old = {}
    for name in names:
        link = next(l for l in tree.links if l.to_socket == principled.inputs[name])
        old[name] = (link.from_socket, link.to_socket)
    node = tree.nodes.new('ShaderNodeGroup')
    node.node_tree = build_rubbish_group()
    node.name = 'RUBBISH'
    node.location = (principled.location.x - 150, principled.location.y - 1100)
    for group_name, key in (('Colour', 'Base Color'), ('Roughness', 'Roughness'), ('Specular IOR Level', 'Specular IOR Level'), ('Coat Weight', 'Coat Weight'), ('Normal', 'Normal')):
        tree.links.new(old[key][0], node.inputs[group_name])
        tree.links.new(node.outputs[group_name], principled.inputs[key])
    tree.links.new(wetness_node.outputs['Wet Mask'], node.inputs['Wet Mask'])
    tree.links.new(wetness_node.outputs['Puddle Mask'], node.inputs['Puddle Mask'])
    values = dict(DEFAULTS)
    values.update(dials)
    for key, socket_name in DIAL_SOCKETS.items():
        node.inputs[socket_name].default_value = values[key]

    def undo():
        tree.nodes.remove(node)
        for key, (source, target) in old.items():
            tree.links.new(source, target)
    return node, undo
