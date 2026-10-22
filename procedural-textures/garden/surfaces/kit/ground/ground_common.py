# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# What the four ground layers (dirt, groundcracks, groundmoss, iron) share. No place is named here and no size of any place: everything that belongs to one set is read from
# the set's "ground" section (settings key `ground`, or the sidecar file ground/ground_sets/<set id>.json until the integrator moves it into the set file) and from the look.
#   * GroundLayer: a layer node group with the kit's standard sockets plus `Distance` and `Cos View` (the scale helper hands them over by name) and a debug selector
#     (the dial show_part) that picks one named part of the layer for the Mask output.
#   * Small node helpers (noise on world position with a seed, white-noise random numbers per cell, a look-up ramp, brightness of a colour, a mark width in plate dots).
#   * The per-object values the layers read: per-role multipliers of dials (the set's ground.role_dials) and "rings" (where standing objects of some roles stand, so a
#     ring can be painted on the ground round them). They are written as custom properties on objects (never on meshes or material slots), by a kit service that runs
#     every time one of the ground layers goes into a material (so they come back after kit.remove()).
# The four rules of the slate moss layer hold for all of them: own seed (the Seed dial and the object's wk_seed), amount 0 means exactly nothing (every effect factor contains the
# amount; nothing can be NaN), no peeking at other layers (only the bus masks and the incoming bundle are read), and independence is proved by the isolation self-test.
import json
import math
import os

import bpy

from apply import dials, layer_template, nodes
from apply.layer_template import BUNDLE_SOCKETS, SCALE_SOCKETS, WET_SOCKETS, LayerBase, mask_default, socket_name
from masks import names as mask_names, scale as scale_module

from . import dials_ground
from .ground_names import *  # noqa: F401,F403  (the plain tables: keys, elements, part numbers, role dials, the set's ground section)
from .ground_names import GROUND_DIR, SECTION_DIR, LOOK_DIR, LAYER_KEYS, ELEMENTS, PART_NUMBERS, ROLE_DIALS, RING_SLOTS, ground_section, look_extras  # noqa: F401

# ------------------------------------------------------------------------------------------------------------------------------ colours
def srgb_to_linear(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 5.5e-2) / 1.055) ** 2.4


def lin(r, g, b):
    """A colour written as plate sRGB 0..255 (the plan's Appendix A) turned into the linear colour a node wants."""
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


def chroma(r, g, b):
    """The colour's direction with brightness 1 (red, green, blue shares divided by its luma): multiply by a brightness to get a colour of that tint at that brightness."""
    rl, gl, bl, _ = lin(r, g, b)
    y = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    return (rl / y, gl / y, bl / y, 1.0)


def _object_extent(obj):
    from mathutils import Vector
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    return 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * max(max(xs) - min(xs), max(ys) - min(ys))


def write_object_props(kit, layers=None):
    """Writes the per-role dial multipliers and the rings as custom properties. Returns how many objects got values."""
    section = ground_section(kit.settings)
    table = section.get('role_dials', {})
    rings = section.get('rings', {})
    count = 0
    keys = tx_keys(kit)
    for obj in bpy.context.scene.objects:
        index = 0
        if obj.type == 'MESH' and keys:
            for slot in obj.material_slots:
                if slot.material is not None:
                    hit = next((i for i, k in enumerate(keys, 1) if slot.material.name.startswith(k)), 0)
                    if hit:
                        index = hit
                        break
        if index or 'wk_tx_index' in obj.keys():
            obj['wk_tx_index'] = float(index)
    for key in (layers or LAYER_KEYS):
        wanted = set(kit.layer_role_names(key)) if key in kit.registry else set()
        if not wanted:
            continue
        per_role = table.get(key, {})
        ring_roles = set(kit.settings.expand_roles(rings.get('roles', []))) if rings and key == rings.get('layer', 'dirt') else set()
        ring_objects = [bpy.data.objects[n] for n in kit.role_map.objects_of(sorted(ring_roles))][:RING_SLOTS] if ring_roles else []
        for obj in bpy.context.scene.objects:
            role = kit.role_map.primary.get(obj.name)
            if role not in wanted:
                continue
            for dial in ROLE_DIALS.get(key, []):
                obj[dials.object_attribute_name(key, dial)] = float(per_role.get(role, {}).get(dial, 1.0))
            if key == rings.get('layer', 'dirt') and ring_roles:
                for slot in range(RING_SLOTS):
                    if slot < len(ring_objects):
                        x, y, r = _object_extent(ring_objects[slot])
                    else:
                        x, y, r = 0.0, 0.0, 0.0
                    obj[f'wk_{key}_ring{slot}_x'], obj[f'wk_{key}_ring{slot}_y'], obj[f'wk_{key}_ring{slot}_r'] = x, y, r
            count += 1
    return count


def tx_keys(kit):
    """The photo materials of the set's ground that have a texture-space picture in the pack (tx_cavity, tx_joint, tx_cell), in a fixed order. The bus (masks/bus.py) gives
    these three masks only to the one material whose key is the pack's single manifest entry, so for setts and flags they read their defaults; the ground layers
    therefore read the pictures themselves (GroundLayer.tx) and pick the right one by an object value, wk_tx_index (1 = the first key here, 0 = no picture)."""
    pack = getattr(kit, 'mask_pack', None)
    if pack is None:
        return []
    textures = pack.manifest.get('textures', {})
    ground_roles = kit.settings.expand_roles(kit.settings.geometry.get('ground', {}).get('roles', []))
    names = kit.role_map.materials_of(ground_roles) if ground_roles else []
    return [key for key in sorted(textures) if any(name.startswith(key) for name in names)]


def make_tx_repeat(chain):
    """The bus looks the texture-space pictures (tx_cavity, tx_joint, tx_cell) up with the edge pixel stretched past the first tile (EXTEND); the photo, and so the picture,
    repeats every tile (2 or 3 m), so they must repeat too or every tile after the first shows smeared edge pixels. Done here, in the material's own copy of the bus group,
    because the bus (masks/bus.py) belongs to the foundation: REQUESTS.md asks for the one-word fix there. Returns how many picture nodes were changed."""
    changed = 0
    for node in chain.tree.nodes:
        if node.get('wk') == 'bus' and node.node_tree is not None:
            for inner in node.node_tree.nodes:
                if inner.type == 'TEX_IMAGE' and inner.image is not None and os.path.basename(inner.image.filepath).startswith('tx_') and inner.extension != 'REPEAT':
                    inner.extension = 'REPEAT'
                    changed += 1
    return changed


def _service(kit, chain, node, key):
    """Runs when a layer goes into a material: makes the texture-space pictures of the bus repeat, and (for the ground layers) makes sure the per-object values exist (kit.remove()
    clears every wk_ value)."""
    make_tx_repeat(chain)
    if key not in LAYER_KEYS:
        return
    first = ROLE_DIALS[key][0]
    attribute = dials.object_attribute_name(key, first)
    wanted = set(kit.layer_role_names(key))
    probe = next((o for o in bpy.context.scene.objects if kit.role_map.primary.get(o.name) in wanted), None)
    if probe is not None and attribute not in probe.keys():
        write_object_props(kit, [key])
    # the material gets the variant of the group that carries only what its objects can use (less to compile)
    elements = elements_for_material(kit, key, chain.material_name)
    if elements is not None and node.node_tree is not None and not node.node_tree.name.endswith(f'[{",".join(elements)}]'):
        node.node_tree = variant_tree(kit, key, elements)


def elements_for_material(kit, key, material_name):
    """The elements of a layer that the objects using a material can ever have: an element stays unless every role of those objects gives all its role dials a multiplier of 0
    (the set's ground.role_dials; a role the set does not mention keeps everything). Returns a sorted tuple, or None (= all elements) when the set has no role table for the layer."""
    section = ground_section(kit.settings)
    per_role = section.get('role_dials', {}).get(key)
    if not per_role:
        return None
    roles = set()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and any(s.material is not None and s.material.name == material_name for s in obj.material_slots):
            role = kit.role_map.primary.get(obj.name)
            if role in set(kit.layer_role_names(key)):
                roles.add(role)
    if not roles:
        return None
    keep = []
    rings_exist = bool(kit.role_map.objects_of(sorted(kit.settings.expand_roles(section.get('rings', {}).get('roles', []))))) if section.get('rings') else False
    for element, dial_names in ELEMENTS[key].items():
        if key == 'dirt' and element == 'drum' and not rings_exist:
            continue                                  # no standing object in this scene needs a ring on the ground
        if any(per_role.get(role) is None or any(float(per_role[role].get(d, 1.0)) > 0.0 for d in dial_names) for role in roles):
            keep.append(element)
    return tuple(sorted(keep))


def variant_tree(kit, key, elements):
    """The node group of a layer with only the given elements (built once per element set)."""
    import importlib
    cache = kit.__dict__.setdefault('_wk_ground_variants', {})
    token = (key, tuple(elements))
    tree = cache.get(token)
    if tree is None or tree.name not in bpy.data.node_groups:
        module = importlib.import_module({'dirt': 'ground.dirt', 'groundcracks': 'ground.groundcracks', 'groundmoss': 'ground.groundmoss', 'iron': 'ground.iron'}[key])
        tree = module.build(key, kit, set(elements))
        cache[token] = tree
    return tree


def install_service(kit):
    if _service not in kit.services:
        kit.services.append(_service)


# ------------------------------------------------------------------------------------------------------------------------------ the layer
class GroundLayer(LayerBase):
    """A LayerBase with the helpers the ground layers share. See layer_template.py for the sockets."""

    def __init__(self, key, group_name, masks=(), wet_normal=True, elements=None):
        dials_ground.ensure()
        self.elements = None if elements is None else set(elements)
        if self.elements is not None:
            group_name = f'{group_name} [{",".join(sorted(self.elements))}]'
        table = dials.TABLE.layers[key]
        self.key = key
        self.dial_names = table.names()
        inputs = [s for s in BUNDLE_SOCKETS if wet_normal or s[0] != 'Wet Normal']
        for mask in masks:
            inputs.append((mask_names.mask_socket(mask), 'NodeSocketFloat', mask_default(mask)))
        inputs += WET_SOCKETS + SCALE_SOCKETS + [('Distance', 'NodeSocketFloat', 10.0), ('Cos View', 'NodeSocketFloat', 1.0)]
        for dial in self.dial_names:
            inputs.append((socket_name(dial), 'NodeSocketFloat', float(table.row(dial)['default'])))
        outputs = [(s[0], s[1]) for s in BUNDLE_SOCKETS if wet_normal or s[0] != 'Wet Normal'] + [('Mask', 'NodeSocketFloat')]
        self.tree, self.gin, self.gout = nodes.new_group(group_name, inputs, outputs)
        self.n = nodes.Net(self.tree)
        self._pos = None
        self._seedw = None
        self._wn = {}
        self._mark = None
        self.parts = []
        self.tonal = set()
        role_amount = self.n.attr(dials.object_attribute_name(key, 'amount'))
        self.amount = self.n.math('MULTIPLY', self.n.math('MAXIMUM', self.g('Amount'), 0.0), role_amount)

    # ---- small things
    def has(self, element):
        """True when this variant of the group carries the element (all of them when no variant was asked for)."""
        return self.elements is None or element in self.elements

    def d(self, dial):
        return self.dial(dial)

    def role(self, dial):
        """The per-object multiplier of a dial (an Attribute node; 0 if the object has no value)."""
        return self.n.attr(dials.object_attribute_name(self.key, dial))

    def eff(self, dial):
        """The dial times the role's multiplier times the layer amount: the strength of one element; exactly 0 when the amount is 0."""
        return self.n.math('MULTIPLY', self.n.math('MULTIPLY', self.dial(dial), self.role(dial)), self.amount)

    def pos(self):
        if self._pos is None:
            geometry = self.n.geometry()
            vec = geometry.outputs['Position']
            self._pos = (vec,) + self.n.separate(vec)
        return self._pos

    def seedw(self):
        """A number that differs per object and per Seed dial (the noise's fourth coordinate)."""
        if self._seedw is None:
            n = self.n
            self._seedw = n.math('ADD', n.math('MULTIPLY', n.attr('wk_seed'), 37.0), n.math('MULTIPLY', self.dial('seed'), 11.3))
        return self._seedw

    def seeded(self, vector):
        """A position moved by this object's seed and the Seed dial (so the noise differs per object and per seed); the same vector gives the same node."""
        key = ('seeded', id(vector.node), vector.name)
        if key not in self._wn:
            n = self.n
            sw = self.seedw()
            shift = n.combine(n.math('MULTIPLY', sw, 0.131), n.math('MULTIPLY', sw, 0.0713), n.math('MULTIPLY', sw, 0.1019))
            self._wn[key] = n.vector_math('ADD', vector, shift)
        return self._wn[key]

    def noise(self, scale_m, detail=2.0, rough=0.55, w=0.0, vector=None, scale_socket=None):
        """Noise on world position (0..1, mostly 0.3 to 0.7): features about scale_m metres across; different per object and seed. 3D noise (the 4D one costs EEVEE much more
        to compile): the call's own number w moves the pattern by a fixed offset so two calls never repeat each other."""
        n = self.n
        node = n.new('ShaderNodeTexNoise')
        node.noise_dimensions = '3D'
        node.noise_type = 'FBM'
        node.normalize = True
        base = self.seeded(vector if vector is not None else self.pos()[0])
        self.tree.links.new(n.vector_math('ADD', base, (w * 7.13 + 1.3, w * 3.71 + 2.9, w * 5.37 + 0.7)), node.inputs['Vector'])
        if scale_socket is not None:
            self.tree.links.new(scale_socket, node.inputs['Scale'])
        else:
            node.inputs['Scale'].default_value = 1.0 / max(scale_m, 1e-4)
        if isinstance(detail, bpy.types.NodeSocket):
            self.tree.links.new(detail, node.inputs['Detail'])
        else:
            node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = rough
        return node.outputs['Fac']

    NOISE_SD = {0: 11.4e-2, 1: 8.5e-2, 2: 7.4e-2, 3: 6.7e-2, 4: 6.3e-2}

    def thr(self, share, detail=1):
        """The noise value above which `share` of a noise field lies (measured: the 4D normalized FBM noise has mean 0.5 and a standard deviation that depends on its detail
        (about a tenth, falling with the detail)), so a dial that says 'covers 10 percent' covers about 10 percent."""
        n = self.n
        table = ((0.02, 2.05), (0.05, 1.645), (0.1, 1.28), (0.2, 0.84), (0.3, 0.52), (0.4, 0.25), (0.5, 0.0), (0.7, -0.52), (0.9, -1.28))
        if not isinstance(share, bpy.types.NodeSocket):                       # a plain number: worked out here, no nodes
            c = min(max(float(share), 0.02), 0.9)
            for (a0, z0), (a1, z1) in zip(table, table[1:]):
                if a0 <= c <= a1:
                    return 0.5 + self.NOISE_SD[int(detail)] * (z0 + (z1 - z0) * (c - a0) / (a1 - a0))
        z = self.ramp(n.math('MAXIMUM', n.math('MINIMUM', share, 0.9), 0.02), [(a, (b + 3.0) / 6.0) for a, b in ((0.02, 2.05), (0.05, 1.645), (0.1, 1.28), (0.2, 0.84), (0.3, 0.52), (0.4, 0.25), (0.5, 0.0), (0.7, -0.52), (0.9, -1.28))])
        # the ramp stores values in 0..1 (a colour); so z is stored as (z + 3) / 6 and unpacked here
        return n.math('ADD', 0.5, n.math('MULTIPLY', n.math('SUBTRACT', n.math('MULTIPLY', z, 6.0), 3.0), self.NOISE_SD[int(detail)]))

    def shift(self, x, delta):
        """x plus a number, for x a socket or a plain number (thr() gives either)."""
        if isinstance(x, bpy.types.NodeSocket):
            return self.n.math('ADD', x, float(delta))
        return float(x) + float(delta)

    def white(self, value, k=0.0):
        """Random numbers (0..1) from a number: returns [v, r, g, b], four independent ones, the same for the same input on every card (an integer hash)."""
        n = self.n
        key = (id(value.node), value.name, k)
        if key in self._wn:
            return self._wn[key]
        node = n.new('ShaderNodeTexWhiteNoise')
        node.noise_dimensions = '1D'
        self.tree.links.new(n.math('ADD', value, float(k)), node.inputs['W'])
        r, g, b = n.sep_rgb(node.outputs['Color'])
        self._wn[key] = [node.outputs['Value'], r, g, b]
        return self._wn[key]

    def cell_id(self, cell_mask):
        """tx_cell (0..1, a number per flag or sett, 8-bit) turned into a whole number (so the same flag always gives the same random numbers)."""
        n = self.n
        return n.math('ROUND', n.math('MULTIPLY', cell_mask, 255.0))

    def ramp(self, x, stops, channel='R'):
        """A look-up curve: stops = [(position, value), ...] -> a number (a Color Ramp used as a table, Linear)."""
        node = self.n.new('ShaderNodeValToRGB')
        ramp = node.color_ramp
        ramp.interpolation = 'LINEAR'
        while len(ramp.elements) > 2:
            ramp.elements.remove(ramp.elements[-1])
        for i, (pos, val) in enumerate(stops):
            element = ramp.elements[i] if i < len(ramp.elements) else ramp.elements.new(pos)
            element.position = pos
            element.color = (val, val, val, 1.0)
        self.tree.links.new(x, node.inputs['Fac'])
        r, g, b = self.n.sep_rgb(node.outputs['Color'])
        return r

    def tx(self, kit):
        """The texture-space masks of the photo materials, read from the pack's pictures here (see tx_keys): {'cavity', 'joint', 'cell', 'has'} as sockets (or plain numbers when
        there is no picture). The picture repeats with the photo (REPEAT) and is looked up in the object's own UV, like the photo; wk_tx_index says which picture this object has."""
        n = self.n
        keys = tx_keys(kit) if kit is not None else []
        if not keys:
            return dict(cavity=0.0, joint=0.0, cell=0.5, has=0.0)
        index = n.attr('wk_tx_index')
        cav = jnt = cel = has = None
        for i, key in enumerate(keys, 1):
            node = n.new('ShaderNodeTexImage')
            node.image = kit.mask_pack.image('tx:' + key)
            node.interpolation = 'Linear'
            node.extension = 'REPEAT'
            r, g, b = n.sep_rgb(node.outputs['Color'])
            w = n.math('MAXIMUM', n.one_minus(n.math('ABSOLUTE', n.math('SUBTRACT', index, float(i)))), 0.0)
            terms = [n.math('MULTIPLY', r, w), n.math('MULTIPLY', g, w), n.math('MULTIPLY', b, w), w]
            cav, jnt, cel, has = [t if acc is None else n.math('ADD', acc, t) for acc, t in zip((cav, jnt, cel, has), terms)]
        cell = n.math('ADD', cel, n.math('MULTIPLY', n.one_minus(n.clamp01(has)), 0.5))
        return dict(cavity=cav, joint=jnt, cell=cell, has=n.clamp01(has))

    def luma(self, colour):
        node = self.n.new('ShaderNodeRGBToBW')
        self.tree.links.new(colour, node.inputs['Color'])
        return node.outputs['Val']

    def colour_mul(self, colour, rgb):
        """colour x (r, g, b) per channel."""
        node = self.n.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        node.blend_type = 'MULTIPLY'
        node.clamp_factor = True
        node.inputs[0].default_value = 1.0
        self.tree.links.new(colour, node.inputs[6])
        if isinstance(rgb, bpy.types.NodeSocket):
            self.tree.links.new(rgb, node.inputs[7])
        else:
            node.inputs[7].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        return node.outputs[2]

    def colour_scale(self, colour, s):
        """colour x a number."""
        r, g, b = self.n.sep_rgb(colour)
        return self.n.comb_rgb(self.n.math('MULTIPLY', r, s), self.n.math('MULTIPLY', g, s), self.n.math('MULTIPLY', b, s))

    def colour_of_luma(self, tint, luma):
        """A colour of the given tint (a chroma triple, see chroma()) at the given brightness (a socket or number)."""
        return self.n.comb_rgb(self.n.math('MULTIPLY', luma, tint[0]), self.n.math('MULTIPLY', luma, tint[1]), self.n.math('MULTIPLY', luma, tint[2]))

    def mark_width(self, real_width, min_dots, dot_socket):
        """(drawn width in metres, fade 1..0) of a mark: never thinner than min_dots plate dots, never drawn more than Inflate Limit times its real width."""
        if self._mark is None:
            self._mark = scale_module.build_mark_width_group()
        node = self.n.new('ShaderNodeGroup')
        node.node_tree = self._mark
        for name, value in (('Real Width', real_width), ('Min Dots', min_dots), ('Dot Size', dot_socket), ('Inflate Limit', self.dial('inflate_limit'))):
            if isinstance(value, bpy.types.NodeSocket):
                self.tree.links.new(value, node.inputs[name])
            else:
                node.inputs[name].default_value = float(value)
        return node.outputs['Width'], node.outputs['Fade']

    def gate_free(self):
        """1 on open ground, 0 where people walk: footfall 0.6 or more, crown 0.7 or more, keepclear 0.5 or more give exactly 0 (the habitat rule of P6)."""
        n = self.n
        free_foot = n.one_minus(n.smoothstep(self.g('M Footfall'), 0.35, 0.6))
        free_crown = n.one_minus(n.smoothstep(self.g('M Crown'), 0.3, 0.7))
        free_keep = n.one_minus(n.smoothstep(self.g('M Keepclear'), 0.15, 0.5))
        return n.math('MULTIPLY', n.math('MULTIPLY', free_foot, free_crown), free_keep)

    def near_fade(self, start_dial, width_m=6.0):
        """1 near the camera, 0 beyond the distance named by a dial (metres), over width_m."""
        n = self.n
        far = self.dial(start_dial)
        return n.one_minus(n.map_range(self.g('Distance'), n.math('MAXIMUM', n.math('SUBTRACT', far, width_m), 0.0), far, 0.0, 1.0, smooth=True))

    def add_part(self, mask, name, tonal=False):
        """Registers one named part for the show_part selector (part numbers are 1, 2, 3 ... in the order added). A TONAL part (a broad soft film or polish that changes tone
        but replaces no joint or stone detail) is shown by its number but is left out of the whole Mask (the measures count the whole as the kit's own marks)."""
        number = PART_NUMBERS[self.key][name]
        self.parts.append((number, mask))
        if tonal:
            self.tonal.add(number)
        return number

    def finish_parts(self, whole=None, **outputs):
        """Links the outputs; the Mask output is the whole (the largest part) when show_part is 0, else the part with that number."""
        n = self.n
        sel = self.dial('show_part')
        out = None
        biggest = None
        only_tonal = bool(self.parts) and all(index in self.tonal for index, _ in self.parts)       # a material that carries only tonal elements: they are its whole Mask
        for index, mask in self.parts:
            if only_tonal or index not in self.tonal:
                biggest = mask if biggest is None else n.math('MAXIMUM', biggest, mask)
            hit = n.math('LESS_THAN', n.math('ABSOLUTE', n.math('SUBTRACT', sel, float(index))), 0.5)
            term = n.math('MULTIPLY', hit, mask)
            out = term if out is None else n.math('ADD', out, term)
        if biggest is None:
            return self.finish(mask=whole, **outputs)
        whole = whole if whole is not None else biggest
        none_selected = n.math('LESS_THAN', sel, 0.5)
        out = n.math('ADD', n.math('MULTIPLY', none_selected, whole), out)
        return self.finish(mask=n.clamp01(out), **outputs)


def bump_normal(layer, height, strength, distance_m, normal):
    """The incoming normal changed by a height (a number per dot, metres up) through a Bump node. strength 0 gives the normal back unchanged (the caller multiplies the amount in)."""
    n = layer.n
    node = n.new('ShaderNodeBump')
    layer.tree.links.new(height, node.inputs['Height'])
    layer.tree.links.new(normal, node.inputs['Normal'])
    if isinstance(strength, bpy.types.NodeSocket):
        layer.tree.links.new(strength, node.inputs['Strength'])
    else:
        node.inputs['Strength'].default_value = strength
    if isinstance(distance_m, bpy.types.NodeSocket):
        layer.tree.links.new(distance_m, node.inputs['Distance'])
    else:
        node.inputs['Distance'].default_value = distance_m
    return node.outputs['Normal']
