# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GENERIC SCATTER ENGINE (Blender code, Geometry Nodes). It knows nothing about any place. Given
#     * a list of TARGET objects (the surfaces plants may stand on: roads and pavements, earth, gravel, or a tilted stone),
#     * MASK PICTURES (the kit's ground-plan pictures, looked up by world x and y; the engine reads them by NAME: weed_site, moss_site, keepclear, footfall, crown, rubbish_heap,
#       wall_dist, seam_dist, shade, dampness, existing_growth, has_ground, and two private strips: gutter_strip, wall_strip),
#     * a list of KINDS (each with a pool of piece variants, a share, a size range, a spacing and a liking for damp, light, wall feet and seams),
# it builds ONE node group that stands pieces on the targets:
#     1. all targets are joined (instances realised) and a Poisson-disk set of candidate points is laid on the faces within the pieces distance of the camera, for every kind (no two
#        of a kind closer than its spacing; the points of a face do not depend on the other faces, so a plant stands in the same place whichever camera draws the picture),
#     2. every point is KEPT or DROPPED by a probability made from the masks: site (weed_site or moss_site, plus a wall-foot and a gutter-side strip for weeds) x the kind's liking
#        x the HARD gates (keepclear, footfall, crown: exactly zero inside the zones) x the rubbish rule (full density below rubbish_thin_max, linearly less up to rubbish_heap_min,
#        none above; moss stops between its own two numbers) x existing growth (so the add-on's own moss is not doubled) x the distance fade of the picture's camera; and pieces are
#        also dropped where they would stand within a clearance of the real 3D pieces of another object (the earlier rubbish layer's litter),
#     3. what is left becomes instances picked at random from the kind's variants, leaning with a random tilt, turned (free, or along an axis for moss strings), scaled by a random
#        size, by the piece_size dial and by a widening that grows with distance (a piece is never narrower than min_dots plate dots, never more than inflate_limit times bigger),
#     4. a ceiling `max_pieces` cuts what is left; `realise` turns the instances into plain meshes.
# The camera is the scene's ACTIVE camera (the runner sets it for every picture); a calibration can pin it with the cam_override dials. The probability of a kind is linear in its
# GAINS (one per population: background, wall foot, gutter side, moss, toadflax), which apply_growth.py sets by counting (calibration), so the dials weed_cover, gutter_tuft_share,
# wall_foot_share and cushion_cover mean what they say.
# HOW IT IS BUILT: one small node group, WKG kind, does everything for ONE kind (candidate points, keep or drop, instances); the main tree makes the shared fields (the mask look-ups,
# the gates, the rubbish rule, the distance fade) once and puts one WKG kind node per kind (a big node tree takes seconds to build one node at a time; small ones are fast).
# All numbers live in Value nodes named dial_<name> in the main tree (set_dial moves them); amount 0 gives probability exactly 0 for every kind, so zero pieces.
import math

import bpy

from apply import nodes as nodes_module

TREE_NAME = 'WKG scatter'
KIND_TREE_NAME = 'WKG kind'
HOST_NAME = 'WKG scatter host'

# (name, default): every number the main tree reads. Python sets them; the look's dials arrive through apply_growth.py.
DIAL_DEFAULTS = dict(
    seed=0.0, amount=1.0, weeds_amount=1.0, cushions_amount=1.0, scale_total=1.0,
    distance=18.0, distance_fade=5.0, piece_size=1.0, min_spacing=0.15, inflate_limit=3.0, tilt_random=0.5, colour_gain=1.0,
    g_bg=1.0, g_wall=1.0, g_gut=1.0, g_moss=1.0, g_toad=0.0,
    rubbish_thin_max=0.45, rubbish_heap_min=0.75, moss_smother_from=0.30, moss_smother_to=0.60, existing_avoid=0.8, avoid_m=0.05,
    keep_soft=0.40, foot_from=0.35, foot_to=0.60, crown_from=0.30, crown_to=0.60,
    dot_angle=0.000266, painter_widen=1.111, wall_reach_m=1.275, seam_reach_m=0.5,
    cam_override_on=0.0, cam_x=0.0, cam_y=0.0, cam_z=1.8, cam_fx=0.0, cam_fy=1.0, cam_fz=0.0, cull_cos=-1.0,
    max_pieces=2500.0, realise=0.0, mask_only_kind=-1.0, select_margin=6.0, cand_density_scale=1.0, water_z=-1000.0, min_dots_scale=1.0,
)

MASK_DEFAULTS = dict(weed_site=0.0, moss_site=0.0, keepclear=0.0, footfall=0.0, crown=0.0, rubbish_heap=0.0, wall_dist=1.0, seam_dist=1.0, shade=0.5, dampness=0.3,
                     existing_growth=0.0, has_ground=1.0, gutter_strip=0.0, wall_strip=0.0, above_water=1.0, litter_dist=1.0)


def S(node, name, kind=None):
    for s in node.inputs:
        if s.name == name and (kind is None or s.type == kind) and s.enabled:
            return s
    for s in node.inputs:
        if s.name == name and (kind is None or s.type == kind):
            return s
    raise KeyError(f'{node.bl_idname}: no input {name} {kind}')


def O(node, name=None, kind=None):
    for s in node.outputs:
        if (name is None or s.name == name) and (kind is None or s.type == kind):
            return s
    raise KeyError(f'{node.bl_idname}: no output {name} {kind}')


class GNet(nodes_module.Net):
    """The kit's node helper plus the Geometry Nodes pieces the scatter needs."""

    def _place(self, node):                 # node positions do not matter here and each costs a tree update
        self.count += 1
        return node

    def gnode(self, idname, **props):
        node = self.new(idname)
        for key, value in props.items():
            setattr(node, key, value)
        return node

    def link(self, src, dst):
        self.tree.links.new(src, dst)

    def feed(self, node, name, value, kind=None):
        sock = S(node, name, kind)
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, sock)
        elif value is not None:
            sock.default_value = value
        return sock

    def position(self):
        return O(self.gnode('GeometryNodeInputPosition'), 'Position')

    def index(self):
        return O(self.gnode('GeometryNodeInputIndex'), 'Index')

    def compare(self, a, op, b):
        node = self.gnode('FunctionNodeCompare', data_type='FLOAT', operation=op)
        self.feed(node, 'A', a, 'VALUE')
        self.feed(node, 'B', b, 'VALUE')
        return O(node, 'Result')

    def bool_op(self, op, a, b=None):
        node = self.gnode('FunctionNodeBooleanMath', operation=op)
        self.link(a, node.inputs[0])
        if b is not None:
            self.link(b, node.inputs[1])
        return O(node, 'Boolean')

    def int_add(self, a, offset):
        node = self.gnode('FunctionNodeIntegerMath', operation='ADD')
        if isinstance(a, bpy.types.NodeSocket):
            self.link(a, node.inputs[0])
        else:
            node.inputs[0].default_value = int(a)
        node.inputs[1].default_value = int(offset)
        return node.outputs[0]

    def random_float(self, lo, hi, seed, ident=None):
        node = self.gnode('FunctionNodeRandomValue', data_type='FLOAT')
        self.feed(node, 'Min', lo, 'VALUE')
        self.feed(node, 'Max', hi, 'VALUE')
        self.feed(node, 'Seed', seed, 'INT')
        if ident is not None:
            self.feed(node, 'ID', ident, 'INT')
        return O(node, 'Value', 'VALUE')

    def random_int(self, lo, hi, seed, ident=None):
        node = self.gnode('FunctionNodeRandomValue', data_type='INT')
        self.feed(node, 'Min', lo, 'INT')
        self.feed(node, 'Max', hi, 'INT')
        self.feed(node, 'Seed', seed, 'INT')
        if ident is not None:
            self.feed(node, 'ID', ident, 'INT')
        return O(node, 'Value', 'INT')

    def to_int(self, value):
        node = self.gnode('FunctionNodeFloatToInt', rounding_mode='ROUND')
        self.link(value, node.inputs[0])
        return node.outputs[0]

    def store(self, geometry, name, value, data_type='FLOAT', domain='POINT'):
        node = self.gnode('GeometryNodeStoreNamedAttribute', data_type=data_type, domain=domain)
        self.link(geometry, S(node, 'Geometry'))
        S(node, 'Name').default_value = name
        self.link(value, S(node, 'Value'))
        return O(node, 'Geometry')

    def join(self, geometries):
        node = self.gnode('GeometryNodeJoinGeometry')
        for geo in geometries:
            self.link(geo, node.inputs[0])
        return O(node, 'Geometry')


# ---------------------------------------------------------------------------------------------------------------------------------------------- the kind group
# (name, socket type, default): the inputs of WKG kind. The mask-made numbers (Select, Site, Damp, Light, Wall Near, Seam Near, Dist, Avoid) arrive as FIELDS (one number per point).
KIND_INPUTS = [
    ('Mesh', 'NodeSocketGeometry', None), ('Pieces', 'NodeSocketCollection', None),
    ('Select', 'NodeSocketFloat', 1.0), ('Site', 'NodeSocketFloat', 0.0), ('Damp', 'NodeSocketFloat', 0.3), ('Light', 'NodeSocketFloat', 0.5), ('Wall Near', 'NodeSocketFloat', 0.0),
    ('Seam Near', 'NodeSocketFloat', 0.0), ('Dist', 'NodeSocketFloat', 0.0), ('Avoid', 'NodeSocketFloat', 0.0),
    ('Pref Base', 'NodeSocketFloat', 0.4), ('Pref Damp', 'NodeSocketFloat', 0.0), ('Pref Light', 'NodeSocketFloat', 0.0), ('Pref Wall', 'NodeSocketFloat', 0.0), ('Pref Seam', 'NodeSocketFloat', 0.0),
    ('Share', 'NodeSocketFloat', 1.0), ('Keep Kind', 'NodeSocketFloat', 1.0), ('Scale Total', 'NodeSocketFloat', 1.0),
    ('Spacing', 'NodeSocketFloat', 0.8), ('Density Max', 'NodeSocketFloat', 8.0), ('Upright', 'NodeSocketFloat', 0.5), ('Align Normal', 'NodeSocketFloat', 0.0),
    ('Scale Min', 'NodeSocketFloat', 0.8), ('Scale Max', 'NodeSocketFloat', 1.2), ('Min Dots', 'NodeSocketFloat', 6.0), ('Width M', 'NodeSocketFloat', 0.08),
    ('Kind Id', 'NodeSocketInt', 0), ('Yaw Base', 'NodeSocketFloat', 0.0), ('Yaw Axis', 'NodeSocketFloat', 0.0), ('Variants', 'NodeSocketInt', 1),
    ('Seed', 'NodeSocketInt', 0), ('Min Spacing', 'NodeSocketFloat', 0.15), ('Tilt Random', 'NodeSocketFloat', 0.5), ('Piece Size', 'NodeSocketFloat', 1.0),
    ('Inflate Limit', 'NodeSocketFloat', 3.0), ('Dot Angle', 'NodeSocketFloat', 0.000266), ('Painter Widen', 'NodeSocketFloat', 1.111), ('Cand Scale', 'NodeSocketFloat', 1.0),
]


def build_kind_group():
    """The node group that does everything for one kind (candidate points, keep or drop, instances)."""
    old = bpy.data.node_groups.get(KIND_TREE_NAME)
    if old is not None:
        bpy.data.node_groups.remove(old)
    tree = bpy.data.node_groups.new(KIND_TREE_NAME, 'GeometryNodeTree')
    for name, kind, default in KIND_INPUTS:
        sock = tree.interface.new_socket(name, in_out='INPUT', socket_type=kind)
        if default is not None:
            sock.default_value = default
    tree.interface.new_socket('Instances', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n = GNet(tree)
    gin = tree.nodes.new('NodeGroupInput')
    gout = tree.nodes.new('NodeGroupOutput')
    g = lambda name: O(gin, name)   # noqa: E731
    mm = lambda a, b: n.math('MULTIPLY', a, b)   # noqa: E731
    # the kind's liking of this spot, and the probability of keeping a candidate point there
    likes = n.math('ADD', n.math('ADD', n.math('ADD', g('Pref Base'), mm(g('Pref Damp'), g('Damp'))), n.math('ADD', mm(g('Pref Light'), g('Light')), mm(g('Pref Wall'), g('Wall Near')))),
                   mm(g('Pref Seam'), g('Seam Near')))
    prob = mm(mm(mm(g('Site'), likes), mm(g('Share'), g('Keep Kind'))), g('Scale Total'))
    # candidate points: Poisson disk on the selected faces
    dist_node = n.gnode('GeometryNodeDistributePointsOnFaces', distribute_method='POISSON')
    n.link(g('Mesh'), S(dist_node, 'Mesh'))
    n.link(n.compare(g('Select'), 'GREATER_THAN', 0.5), S(dist_node, 'Selection'))
    n.link(n.math('MAXIMUM', mm(g('Min Spacing'), g('Spacing')), 0.02), S(dist_node, 'Distance Min'))
    n.link(mm(g('Density Max'), g('Cand Scale')), S(dist_node, 'Density Max'))
    n.link(n.int_add(g('Seed'), 5), S(dist_node, 'Seed'))
    points = O(dist_node, 'Points')
    normal = O(dist_node, 'Normal')
    idx = n.index()
    rand = n.random_float(0.0, 1.0, n.int_add(g('Seed'), 101), ident=idx)
    drop = n.bool_op('OR', n.compare(rand, 'GREATER_EQUAL', prob), n.compare(g('Avoid'), 'GREATER_THAN', 0.5))
    tint = n.random_float(0.0, 1.0, n.int_add(g('Seed'), 211), ident=idx)
    stored = n.store(points, 'tint', tint)
    stored = n.store(stored, 'damp', g('Damp'))
    stored = n.store(stored, 'kind', g('Kind Id'), data_type='INT')
    dele = n.gnode('GeometryNodeDeleteGeometry', domain='POINT')
    n.link(stored, S(dele, 'Geometry'))
    n.link(drop, S(dele, 'Selection'))
    kept = O(dele, 'Geometry')
    # instances picked from the kind's pieces
    info = n.gnode('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
    n.link(g('Pieces'), S(info, 'Collection'))
    S(info, 'Separate Children').default_value = True
    S(info, 'Reset Children').default_value = True
    inst = n.gnode('GeometryNodeInstanceOnPoints')
    n.link(kept, S(inst, 'Points'))
    n.link(O(info, 'Instances'), S(inst, 'Instance'))
    S(inst, 'Pick Instance').default_value = True
    n.link(n.random_int(0, n.int_add(g('Variants'), -1), n.int_add(g('Seed'), 307), ident=idx), S(inst, 'Instance Index'))
    # rotation: stand along the surface normal blended with world up, turned about it, tilted a little
    up_weight = n.math('MAXIMUM', 0.0, n.math('SUBTRACT', g('Upright'), g('Align Normal')))
    axis_vec = n.vector_math('NORMALIZE', n.mix_vector(up_weight, normal, (0.0, 0.0, 1.0)))
    align = n.gnode('FunctionNodeAlignRotationToVector', axis='Z')
    n.link(axis_vec, S(align, 'Vector'))
    free_yaw = n.random_float(0.0, 2.0 * math.pi, n.int_add(g('Seed'), 409), ident=idx)
    flip = n.random_float(0.0, 1.0, n.int_add(g('Seed'), 401), ident=idx)
    axis_yaw = n.math('ADD', g('Yaw Base'), n.math('ADD', mm(n.math('GREATER_THAN', flip, 0.5), math.pi), mm(n.math('SUBTRACT', flip, 0.5), 0.5)))
    yaw = n.mix(g('Yaw Axis'), free_yaw, axis_yaw)
    tilt_x = mm(n.random_float(-1.0, 1.0, n.int_add(g('Seed'), 419), ident=idx), mm(g('Tilt Random'), 0.35))
    tilt_y = mm(n.random_float(-1.0, 1.0, n.int_add(g('Seed'), 431), ident=idx), mm(g('Tilt Random'), 0.35))
    euler = n.gnode('FunctionNodeEulerToRotation')
    n.link(n.combine(tilt_x, tilt_y, yaw), euler.inputs[0])
    rotate = n.gnode('FunctionNodeRotateRotation', rotation_space='LOCAL')
    n.link(O(align, 'Rotation'), S(rotate, 'Rotation'))
    n.link(O(euler, 'Rotation'), S(rotate, 'Rotate By'))
    n.link(O(rotate, 'Rotation'), S(inst, 'Rotation'))
    # scale: random size x piece_size x the widening that keeps the plant min_dots plate dots wide at its distance (never more than inflate_limit times)
    size = n.random_float(g('Scale Min'), g('Scale Max'), n.int_add(g('Seed'), 503), ident=idx)
    dot = mm(mm(g('Dist'), g('Dot Angle')), g('Painter Widen'))
    widen = n.math('MINIMUM', n.math('MAXIMUM', n.math('DIVIDE', mm(dot, g('Min Dots')), n.math('MAXIMUM', g('Width M'), 0.001)), 1.0), g('Inflate Limit'))
    n.link(mm(mm(size, g('Piece Size')), widen), S(inst, 'Scale'))
    n.link(O(inst, 'Instances'), gout.inputs[0])
    return tree


# ---------------------------------------------------------------------------------------------------------------------------------------------- the engine
class Engine:
    """Builds the scatter tree for a list of kinds on a list of target objects."""

    def __init__(self, name=TREE_NAME):
        self.name = name
        self.tree = None
        self.kind_index = {}
        self.options = {}
        self.probes = {}
        self.fields = {}

    def build(self, kinds, targets, masks, bounds, options=None):
        """kinds: [dict(name, group 'weed'|'moss', collection, variants, scale (lo, hi), min_dots, width_m, upright, spacing, density_max, yaw ('free'|'axis'), prefer {base, damp,
        light, wall, seam}, pop ('weed'|'moss'|'toad'), share_dial (name of the Value node holding its share))];  targets: [objects];
        masks: {mask name: (image, 'R'|'G'|'B'|'A')} (names missing here read MASK_DEFAULTS);  bounds: dict(x=[x0,x1], y=[y0,y1]);
        options: dict(avoid=[objects whose pieces are kept clear], yaw_axis 'x'|'y'|None, align_normal 0..1 added to every kind's upright, realise_targets True)."""
        options = options or {}
        self.options = options
        old = bpy.data.node_groups.get(self.name)
        if old is not None:
            bpy.data.node_groups.remove(old)
        kind_tree = build_kind_group()
        tree = bpy.data.node_groups.new(self.name, 'GeometryNodeTree')
        tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        self.tree = tree
        self.kind_tree = kind_tree
        self.probes, self.fields, self.kind_index = {}, {}, {}
        n = GNet(tree)
        group_out = tree.nodes.new('NodeGroupOutput')
        self.group_out = group_out
        # ---- the dials: one Value node each
        dials = {}
        dial_names = list(DIAL_DEFAULTS) + sorted({k['share_dial'] for k in kinds if k.get('share_dial')})
        for key in dial_names:
            node = tree.nodes.new('ShaderNodeValue')
            node.name, node.label = 'dial_' + key, key
            node.outputs[0].default_value = DIAL_DEFAULTS.get(key, 0.0)
            dials[key] = node.outputs[0]
        d = lambda key: dials[key]   # noqa: E731
        self.dial_names = dial_names
        mm = lambda a, b: n.math('MULTIPLY', a, b)   # noqa: E731
        # ---- the targets, joined (instances realised: a roof of instanced tiles is a surface too)
        join_t = n.gnode('GeometryNodeJoinGeometry')
        for obj in targets:
            info = n.gnode('GeometryNodeObjectInfo', transform_space='RELATIVE')
            S(info, 'Object').default_value = obj
            S(info, 'As Instance').default_value = False
            n.link(O(info, 'Geometry'), join_t.inputs[0])
        target_geo = O(join_t, 'Geometry')
        if options.get('realise_targets', True):
            real_t = n.gnode('GeometryNodeRealizeInstances')
            n.link(target_geo, S(real_t, 'Geometry'))
            target_geo = O(real_t, 'Geometry')
        # ---- the camera: the scene's active camera, or the pinned override
        active = n.gnode('GeometryNodeInputActiveCamera')
        cam_info = n.gnode('GeometryNodeObjectInfo', transform_space='ORIGINAL')
        n.link(O(active, 'Active Camera'), S(cam_info, 'Object'))
        override = n.combine(d('cam_x'), d('cam_y'), d('cam_z'))
        cam_pos = n.mix_vector(d('cam_override_on'), O(cam_info, 'Location'), override)
        rot_vec = n.gnode('FunctionNodeRotateVector')
        S(rot_vec, 'Vector').default_value = (0.0, 0.0, -1.0)
        n.link(O(cam_info, 'Rotation'), S(rot_vec, 'Rotation'))
        cam_fwd = n.vector_math('NORMALIZE', n.mix_vector(d('cam_override_on'), O(rot_vec, 'Vector'), n.combine(d('cam_fx'), d('cam_fy'), d('cam_fz'))))
        # ---- the masks, looked up by world x and y (Closest: a dot's own value, so a zone is exactly the picture's zone)
        px, py, pz = n.separate(n.position())
        x0, x1 = bounds['x']
        y0, y1 = bounds['y']
        uv = n.combine(n.math('DIVIDE', n.math('SUBTRACT', px, x0), x1 - x0), n.math('DIVIDE', n.math('SUBTRACT', py, y0), y1 - y0), 0.0)
        samplers = {}

        def picture(image):
            if image.name in samplers:
                return samplers[image.name]
            node = n.gnode('GeometryNodeImageTexture', interpolation='Closest', extension='CLIP')
            S(node, 'Image').default_value = image
            n.link(uv, S(node, 'Vector'))
            sep = n.gnode('FunctionNodeSeparateColor')
            n.link(O(node, 'Color'), sep.inputs[0])
            samplers[image.name] = (O(sep, 'Red'), O(sep, 'Green'), O(sep, 'Blue'), O(sep, 'Alpha'))
            return samplers[image.name]

        def mask(name):
            if name in masks and masks[name] is not None:
                image, channel = masks[name]
                return picture(image)['RGBA'.index(channel)]
            return MASK_DEFAULTS[name]

        W, M, K, F, C, H = (mask(k) for k in ('weed_site', 'moss_site', 'keepclear', 'footfall', 'crown', 'rubbish_heap'))
        WD, SD, SH, DP, EG, HG = (mask(k) for k in ('wall_dist', 'seam_dist', 'shade', 'dampness', 'existing_growth', 'has_ground'))
        WS, GS = mask('wall_strip'), mask('gutter_strip')
        AW = mask('above_water')
        LD = mask('litter_dist')

        def one_minus_smooth(v, e0, e1):
            return n.one_minus(n.map_range(v, e0, e1, 0.0, 1.0, smooth=True))

        # hard gates: exactly zero inside the zones (keepclear from keep_soft up, footfall from foot_to up, crown from crown_to up) and where there is no ground
        has = n.math('GREATER_THAN', HG, 0.5) if not isinstance(HG, float) else HG
        gate = mm(mm(mm(has, one_minus_smooth(K, 0.0, d('keep_soft'))), one_minus_smooth(F, d('foot_from'), d('foot_to'))), one_minus_smooth(C, d('crown_from'), d('crown_to')))
        if not isinstance(AW, float):                                           # nothing grows under water (a set with water gives above_water 0 at and below its level)
            gate = mm(gate, n.map_range(AW, 0.03, 0.12, 0.0, 1.0, smooth=True))
        gate = mm(gate, n.compare(pz, 'GREATER_THAN', n.math('ADD', d('water_z'), 0.04)))   # and a plant on the flank of a stone is not made below the water level either
        heap_w = n.clamp01(n.math('DIVIDE', n.math('SUBTRACT', d('rubbish_heap_min'), H), n.math('MAXIMUM', n.math('SUBTRACT', d('rubbish_heap_min'), d('rubbish_thin_max')), 0.01)))
        heap_m = n.clamp01(n.math('DIVIDE', n.math('SUBTRACT', d('moss_smother_to'), H), n.math('MAXIMUM', n.math('SUBTRACT', d('moss_smother_to'), d('moss_smother_from')), 0.01)))
        existing = n.one_minus(mm(d('existing_avoid'), EG))
        wall_m = mm(WD, d('wall_reach_m'))
        seam_m = mm(SD, d('seam_reach_m'))
        wall_near = n.one_minus(n.map_range(wall_m, 0.05, 0.5, 0.0, 1.0, smooth=True))
        seam_near = n.one_minus(n.map_range(seam_m, 0.03, 0.30, 0.0, 1.0, smooth=True))
        light = n.one_minus(SH)
        dist = n.vector_math('DISTANCE', n.position(), cam_pos)
        fade_d = n.one_minus(n.map_range(dist, n.math('SUBTRACT', d('distance'), n.math('MAXIMUM', d('distance_fade'), 0.01)), d('distance'), 0.0, 1.0, smooth=True))
        cos_angle = n.vector_math('DOT_PRODUCT', n.vector_math('NORMALIZE', n.vector_math('SUBTRACT', n.position(), cam_pos)), cam_fwd)
        in_cone = n.math('GREATER_THAN', cos_angle, d('cull_cos'))              # inside the cone round the camera's axis (plants behind or far beside the picture are not made)
        site_base = mm(mm(gate, fade_d), in_cone)
        amount_w = mm(d('weeds_amount'), d('amount'))
        amount_m = mm(d('cushions_amount'), d('amount'))
        # three populations that do not overlap: the wall-foot strip and the gutter-side strip have their own gain; the background (everything else the habitat field allows) leaves them out
        outside = mm(n.one_minus(n.math('MINIMUM', WS, 1.0)), n.one_minus(n.math('MINIMUM', GS, 1.0)))
        weed_site = mm(mm(n.math('ADD', n.math('ADD', mm(mm(W, outside), d('g_bg')), mm(WS, d('g_wall'))), mm(GS, d('g_gut'))), mm(site_base, heap_w)), amount_w)
        moss_site = mm(mm(mm(M, d('g_moss')), mm(site_base, heap_m)), mm(mm(existing, amount_m), n.math('ADD', 0.45, mm(0.55, n.math('MAXIMUM', wall_near, seam_near)))))
        toad_site = mm(mm(mm(W, d('g_toad')), mm(site_base, heap_w)), amount_w)
        self.fields = dict(gate=gate, heap_w=heap_w, fade_d=fade_d, W=W, WS=WS, GS=GS, K=K, F=F, C=C, H=H, HG=HG, dist=dist, weed_site=weed_site, moss_site=moss_site, toad_site=toad_site)
        # only the faces within the pieces distance (plus a margin that covers the biggest target face) of the camera get candidate points
        near_face = mm(n.compare(n.vector_math('DISTANCE', n.position(), cam_pos), 'LESS_THAN', n.math('ADD', d('distance'), n.math('ADD', d('distance_fade'), d('select_margin')))),
                       n.math('GREATER_THAN', cos_angle, n.math('SUBTRACT', d('cull_cos'), 0.12)))
        # the litter the plants keep clear of: the baked distance picture if the pack has one (litter_dist), else the real distance to the faces of those objects' pieces
        avoid_field = 0.0
        avoid = options.get('avoid') or []
        if not isinstance(LD, float):
            # the baked picture of the distance to the nearest litter piece (masks/stamp_pack.py --litter; metres / litter_max_m): the same question as the Proximity node below, answered
            # by one look-up instead of a search over tens of thousands of pieces on every picture
            avoid_field = n.compare(n.math('MULTIPLY', LD, float(options.get('litter_max_m', 0.25))), 'LESS_THAN', d('avoid_m'))
        elif avoid:
            join_a = n.gnode('GeometryNodeJoinGeometry')
            for obj in avoid:
                info = n.gnode('GeometryNodeObjectInfo', transform_space='RELATIVE')
                S(info, 'Object').default_value = obj
                S(info, 'As Instance').default_value = False
                n.link(O(info, 'Geometry'), join_a.inputs[0])
            real_a = n.gnode('GeometryNodeRealizeInstances')
            n.link(O(join_a, 'Geometry'), S(real_a, 'Geometry'))
            # the clearance is measured on the ground plan (x and y only: a plant at the foot of a kerb is also kept away from litter lying on the kerb's top)
            ax, ay, az = n.separate(n.position())
            flat = n.gnode('GeometryNodeSetPosition')
            n.link(O(real_a, 'Geometry'), S(flat, 'Geometry'))
            n.link(n.combine(ax, ay, 0.0), S(flat, 'Position'))
            prox = n.gnode('GeometryNodeProximity', target_element='FACES')
            n.link(O(flat, 'Geometry'), S(prox, 'Geometry'))
            n.link(n.combine(px, py, 0.0), S(prox, 'Sample Position'))
            avoid_field = n.compare(O(prox, 'Distance'), 'LESS_THAN', d('avoid_m'))
        seed_i = n.to_int(d('seed'))
        outputs = []
        for k, kind in enumerate(kinds):
            self.kind_index[kind['name']] = k
            pref = kind['prefer']
            norm = max(1e-6, pref['base'] + pref['damp'] + pref['light'] + pref['wall'] + pref['seam'])
            site = {'moss': moss_site, 'toad': toad_site}.get(kind['pop'], weed_site)
            node = n.gnode('GeometryNodeGroup')
            node.node_tree = kind_tree

            def put(name, value, node=node):
                sock = node.inputs[name]
                if isinstance(value, bpy.types.NodeSocket):
                    n.link(value, sock)
                else:
                    sock.default_value = value

            put('Mesh', target_geo)
            node.inputs['Pieces'].default_value = kind['collection']
            put('Select', near_face)
            put('Site', site)
            put('Damp', DP)
            put('Light', light)
            put('Wall Near', wall_near)
            put('Seam Near', seam_near)
            put('Dist', dist)
            put('Avoid', avoid_field)
            for key in ('base', 'damp', 'light', 'wall', 'seam'):
                put('Pref ' + key.title(), pref[key] / norm)
            put('Share', d(kind['share_dial']) if kind.get('share_dial') else 1.0)
            put('Keep Kind', n.math('MAXIMUM', n.math('LESS_THAN', d('mask_only_kind'), 0.0), n.math('LESS_THAN', n.math('ABSOLUTE', n.math('SUBTRACT', d('mask_only_kind'), float(k))), 0.5)))
            put('Scale Total', d('scale_total'))
            put('Spacing', kind['spacing'] / 0.15)
            put('Density Max', kind['density_max'])
            put('Upright', min(1.0, kind['upright']))
            put('Align Normal', float(options.get('align_normal', 0.0)))
            put('Scale Min', kind['scale'][0])
            put('Scale Max', kind['scale'][1])
            put('Min Dots', n.math('MULTIPLY', d('min_dots_scale'), kind['min_dots']))
            put('Width M', kind['width_m'])
            node.inputs['Kind Id'].default_value = k
            node.inputs['Yaw Base'].default_value = (math.pi / 2.0) if options.get('yaw_axis') == 'y' else 0.0
            node.inputs['Yaw Axis'].default_value = 1.0 if (kind.get('yaw') == 'axis' and options.get('yaw_axis')) else 0.0
            node.inputs['Variants'].default_value = int(kind['variants'])
            n.link(n.int_add(seed_i, 17 * k + 1), node.inputs['Seed'])
            put('Min Spacing', d('min_spacing'))
            put('Tilt Random', d('tilt_random'))
            put('Piece Size', d('piece_size'))
            put('Inflate Limit', d('inflate_limit'))
            put('Dot Angle', d('dot_angle'))
            put('Painter Widen', d('painter_widen'))
            put('Cand Scale', d('cand_density_scale'))
            outputs.append(O(node, 'Instances'))
            self.fields[f'site_{k}'] = site
        joined = n.join(outputs)
        self.probes['joined'] = joined
        # the ceiling (a backstop: the calibration keeps the count under it) and the option to turn instances into meshes
        ceiling = n.gnode('GeometryNodeDeleteGeometry', domain='INSTANCE')
        n.link(joined, S(ceiling, 'Geometry'))
        n.link(n.compare(n.index(), 'GREATER_EQUAL', d('max_pieces')), S(ceiling, 'Selection'))
        capped = O(ceiling, 'Geometry')
        realise = n.gnode('GeometryNodeRealizeInstances')
        n.link(capped, S(realise, 'Geometry'))
        switch = n.gnode('GeometryNodeSwitch', input_type='GEOMETRY')
        n.link(n.math('GREATER_THAN', d('realise'), 0.5), S(switch, 'Switch'))
        n.link(capped, S(switch, 'False'))
        n.link(O(realise, 'Geometry'), S(switch, 'True'))
        n.link(O(switch, 'Output'), group_out.inputs[0])
        return tree

    # ---------------------------------------------------------------- debugging
    def probe(self, host, stage='joined'):
        """Debug: the number of points or instances at a named stage of the tree; the tree is put back as it was."""
        socket = self.probes[stage]
        links = self.tree.links
        old = [l.from_socket for l in self.group_out.inputs[0].links]
        links.new(socket, self.group_out.inputs[0])
        try:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()
            geo = host.evaluated_get(depsgraph).evaluated_geometry()
            ipc = geo.instances_pointcloud()
            pc = geo.pointcloud
            return dict(instances=None if ipc is None else len(ipc.points), points=None if pc is None else len(pc.points))
        finally:
            for src in old:
                links.new(src, self.group_out.inputs[0])

    # ---------------------------------------------------------------- the host object
    def add_host(self, scene):
        host = bpy.data.objects.get(HOST_NAME)
        if host is None:
            mesh = bpy.data.meshes.new(HOST_NAME)
            host = bpy.data.objects.new(HOST_NAME, mesh)
            scene.collection.objects.link(host)
        modifier = host.modifiers.get('WKG scatter')
        if modifier is None:
            modifier = host.modifiers.new('WKG scatter', 'NODES')
        modifier.node_group = self.tree
        host.hide_select = True
        return host

    def set_dial(self, name, value):
        node = self.tree.nodes.get('dial_' + name) if self.tree else None
        if node is None:
            raise KeyError(f'the scatter has no dial {name!r}')
        node.outputs[0].default_value = float(value)

    def set_dials(self, **values):
        for name, value in values.items():
            self.set_dial(name, value)

    def get_dial(self, name):
        return float(self.tree.nodes['dial_' + name].outputs[0].default_value)


def evaluated_instances(host, kinds=None):
    """The host's evaluated instances: (matrices as a numpy array (n, 4, 4), kind ids (n,), {attribute: values}). Reads the evaluated geometry set (no depsgraph instance walk)."""
    import numpy as np
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = host.evaluated_get(depsgraph)
    geo = evaluated.evaluated_geometry()
    ipc = geo.instances_pointcloud()
    if ipc is None or len(ipc.points) == 0:
        return np.zeros((0, 4, 4), np.float32), np.zeros(0, np.int32), {}
    count = len(ipc.points)
    mats = np.zeros(count * 16, np.float32)
    ipc.attributes['instance_transform'].data.foreach_get('value', mats)
    extra = {}
    for name, dtype in (('kind', np.int32), ('tint', np.float32), ('damp', np.float32)):
        if name in ipc.attributes:
            arr = np.zeros(count, dtype)
            ipc.attributes[name].data.foreach_get('value', arr)
            extra[name] = arr
    return mats.reshape(count, 4, 4), extra.get('kind', np.zeros(count, np.int32)), extra
