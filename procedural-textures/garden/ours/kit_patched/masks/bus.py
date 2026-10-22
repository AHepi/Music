# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE BUS: the one standard set of named masks every layer reads. For each material that carries kit layers it builds ONE node group, WK MASKS <material>, holding only the
# masks the layers on that material ask for (a layer asks by declaring an input 'M <Name>'; names.py lists them), and wires its outputs to the layers by name. A layer never
# knows which picture, frame or set a mask comes from:
#   * ground plan (GP): the picture is looked up by the dot's WORLD x and y (outside the picture the default is returned)
#   * wall sheet (WF): the picture is looked up by the dot's position in the object's OWN frame; the sheet is chosen by the object value wk_frame_id (an atlas holds the sheets);
#     the sheet counts only where the surface faces the frame (within about 25 degrees): frame_valid. Where it does not, the ground-plan version (or the default) is used
#   * texture space (TX): the material's own photo coordinates (tx_cavity, tx_joint, tx_cell) for the photo materials the set names
#   * height is special: GP gives z minus the ground height under the dot; a wall sheet gives the baked height above the ground at the wall foot
# A mask the pack has nothing for returns its default (names.py). Attribute reads: wk_frame_id (object value; written by seed.py/this module).
# attach(kit) loads a pack and registers the service that does the wiring whenever a layer goes into a material.
import json
import math
import os

import bpy

from apply import hook, nodes
from . import names as names_module, pack as pack_module, scale as scale_module

FRONT_COS_LO, FRONT_COS_HI = math.cos(math.radians(32.0)), math.cos(math.radians(20.0))
BUS_TAG = 'bus'


class MaskPack:
    def __init__(self, manifest):
        self.manifest = manifest
        self.dir = manifest['_dir']
        self._images = {}

    def image(self, picture):
        if picture in self._images:
            return self._images[picture]
        if picture.startswith('tx:'):
            entry = self.manifest['textures'][picture[3:]]
            path = os.path.normpath(os.path.join(self.dir, entry['file']))
        else:
            path = os.path.join(self.dir, self.manifest['pictures'][picture]['file'])
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = 'Non-Color'
        image.alpha_mode = 'CHANNEL_PACKED'
        self._images[picture] = image
        return image

    def entry(self, frame, name):
        return self.manifest['masks'].get(frame, {}).get(name)


def load_pack(kit_root, set_id, scene_id):
    return MaskPack(pack_module.load_manifest(kit_root, set_id, scene_id))


def attach(kit, kit_root=None, mask_pack=None):
    """Loads the scene's pack (unless given) and registers the wiring service on the kit. Returns the MaskPack."""
    from apply import KIT_ROOT
    kit.mask_pack = mask_pack or load_pack(kit_root or KIT_ROOT, kit.settings.id, kit.scene_id)
    kit.bus_needed = {}
    if service not in kit.services:
        kit.services.append(service)
    write_frame_ids(kit)
    return kit.mask_pack


def write_frame_ids(kit):
    ids = kit.mask_pack.manifest['frames'].get('frame_of_object', {})
    for obj in bpy.context.scene.objects:
        obj['wk_frame_id'] = float(ids.get(obj.name, 0))


def mask_inputs(node):
    """{socket name: mask name} for the bus inputs a layer node declares."""
    found = {}
    for socket in node.inputs:
        name = names_module.name_of_socket(socket.name)
        if name:
            found[socket.name] = name
    return found


def service(kit, chain, node, key):
    """Called by the kit after a layer node went into a chain: makes sure the material has a bus carrying what the layer asks for, a scale node, and wires both by name."""
    needed = kit.bus_needed.setdefault(chain.material_name, set())
    wanted = set(mask_inputs(node).values())
    if not wanted <= needed:
        needed |= wanted
        rebuild_bus(kit, chain)
    else:
        wire(kit, chain)
    ensure_scale(kit, chain)
    wire(kit, chain)


def ensure_scale(kit, chain):
    tree = chain.tree
    node = next((n for n in tree.nodes if n.get('wk') == 'scale'), None)
    if node is None:
        node = scale_module.add_scale_node(tree, kit.settings, (chain.principled.location.x - 700, chain.principled.location.y + 700))
    return node


def wire(kit, chain):
    """Links bus outputs and scale outputs to every kit layer input of the same name."""
    tree = chain.tree
    bus = next((n for n in tree.nodes if n.get('wk') == BUS_TAG), None)
    scale = next((n for n in tree.nodes if n.get('wk') == 'scale'), None)
    for stage in chain.stages:
        if stage.kind != 'kit':
            continue
        node = tree.nodes.get(stage.node_name)
        if node is None:
            continue
        for socket in node.inputs:
            if bus is not None and socket.name in bus.outputs and not socket.links:
                tree.links.new(bus.outputs[socket.name], socket)
            elif scale is not None and socket.name in scale.outputs and socket.name != 'Mask' and not socket.links:
                tree.links.new(scale.outputs[socket.name], socket)


def material_frame_ids(kit, chain, manifest):
    """The sheet ids used by the objects that carry this material."""
    frame_of = manifest['frames'].get('frame_of_object', {})
    ids = set()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and any(s.material is not None and s.material.name == chain.material_name for s in obj.material_slots):
            if obj.name in frame_of:
                ids.add(int(frame_of[obj.name]))
    return sorted(ids)


def texture_key(manifest, material_name):
    best = None
    for key in manifest.get('textures', {}):
        if material_name.startswith(key) and (best is None or len(key) > len(best)):
            best = key
    return best


def rebuild_bus(kit, chain):
    tree = chain.tree
    for old in [n for n in tree.nodes if n.get('wk') == BUS_TAG]:
        group = old.node_tree
        tree.nodes.remove(old)
        if group is not None and group.users == 0:
            bpy.data.node_groups.remove(group)
    needed = sorted(kit.bus_needed.get(chain.material_name, []))
    group = build_bus_group(kit, chain, needed)
    node = tree.nodes.new('ShaderNodeGroup')
    node.node_tree = group
    node.name = 'WK MASKS'
    node.label = 'WK MASKS'
    node['wk'] = BUS_TAG
    node.location = (chain.principled.location.x - 700, chain.principled.location.y + 300)
    wire(kit, chain)
    return node


# ------------------------------------------------------------------------------------------------------------------------------- the group
def build_bus_group(kit, chain, mask_list):
    mp = kit.mask_pack
    manifest = mp.manifest
    group_name = f'WK MASKS {chain.material_name}'
    existing = bpy.data.node_groups.get(group_name)
    if existing is not None and existing.users == 0:
        bpy.data.node_groups.remove(existing)
    outputs = [(names_module.mask_socket(m), 'NodeSocketFloat') for m in mask_list]
    tree, gin, gout = nodes.new_group(group_name, [], outputs)
    n = nodes.Net(tree)
    geometry = n.geometry()
    px, py, pz = n.separate(geometry.outputs['Position'])
    ground = manifest['ground']
    ux = n.math('DIVIDE', n.math('SUBTRACT', px, ground['x'][0]), ground['x'][1] - ground['x'][0])
    vy = n.math('DIVIDE', n.math('SUBTRACT', py, ground['y'][0]), ground['y'][1] - ground['y'][0])
    inside = n.math('MULTIPLY', n.math('MULTIPLY', n.math('GREATER_THAN', ux, 0.0), n.math('LESS_THAN', ux, 1.0)),
                    n.math('MULTIPLY', n.math('GREATER_THAN', vy, 0.0), n.math('LESS_THAN', vy, 1.0)))
    gp_uv = n.combine(ux, vy, 0.0)
    cache = {}

    def sample(picture, vector):
        key = (picture, id(vector.node), vector.name) if vector is not None else (picture, None)
        if key not in cache:
            node = n.new('ShaderNodeTexImage')
            node.image = mp.image(picture)
            node.interpolation = 'Linear'
            node.extension = 'EXTEND'
            if vector is not None:
                tree.links.new(vector, node.inputs['Vector'])
            sep = n.new('ShaderNodeSeparateColor')
            tree.links.new(node.outputs['Color'], sep.inputs['Color'])
            cache[key] = dict(R=sep.outputs['Red'], G=sep.outputs['Green'], B=sep.outputs['Blue'], A=node.outputs['Alpha'])
        return cache[key]

    def channel(entry, vector):
        return sample(entry['picture'], vector)[entry['channel']]

    # ---- the ground plan
    z_lo, z_hi = ground.get('z_range', [-2.0, 6.0])

    def gp_value(name):
        entry = mp.entry('GP', name)
        if entry is None:
            return None
        if name == 'ground_height':
            raw = channel(entry, gp_uv)
            has = sample('gp_height', gp_uv)['G']
            return n.math('MULTIPLY', n.math('ADD', n.math('MULTIPLY', raw, z_hi - z_lo), z_lo), has), has
        return n.mix(inside, names_module.default_of(name), channel(entry, gp_uv))

    # ---- wall sheets (only built if a mask asks for them and the material's objects have sheets)
    frame_ids = material_frame_ids(kit, chain, manifest) if any(mp.entry('WF', m) or m in ('height', 'frame_valid') for m in mask_list) else []
    sheets = {s['id']: s for s in manifest['frames']['sheets']} if frame_ids else {}
    wf = {}
    if frame_ids:
        frame_id = n.attr('wk_frame_id')
        coord = n.new('ShaderNodeTexCoord')
        cx, cy, cz = n.separate(coord.outputs['Object'])
        transform = n.new('ShaderNodeVectorTransform')
        transform.vector_type = 'NORMAL'
        transform.convert_from = 'WORLD'
        transform.convert_to = 'OBJECT'
        tree.links.new(geometry.outputs['Normal'], transform.inputs['Vector'])
        nx, ny, nz = n.separate(n.vector_math('NORMALIZE', transform.outputs['Vector']))
        axes = [cx, cy, cz]
        naxes = [nx, ny, nz]
        sel, valid, unorm, vnorm = {}, {}, {}, {}
        for fid in frame_ids:
            s = sheets[fid]
            sel[fid] = n.math('MAXIMUM', n.one_minus(n.math('ABSOLUTE', n.math('SUBTRACT', frame_id, float(fid)))), 0.0)
            u_local = n.math('DIVIDE', n.math('SUBTRACT', axes[s['u_axis']], s['u_range'][0]), s['u_range'][1] - s['u_range'][0])
            v_local = n.math('DIVIDE', n.math('SUBTRACT', cz, s['v_range'][0]), s['v_range'][1] - s['v_range'][0])
            gate = n.math('MULTIPLY', n.math('MULTIPLY', n.math('GREATER_THAN', u_local, 0.0), n.math('LESS_THAN', u_local, 1.0)),
                          n.math('MULTIPLY', n.math('GREATER_THAN', v_local, 0.0), n.math('LESS_THAN', v_local, 1.0)))
            facing = n.math('MULTIPLY', naxes[s['front_axis']], float(s['front_sign']))
            valid[fid] = n.math('MULTIPLY', n.smoothstep(facing, FRONT_COS_LO, FRONT_COS_HI), gate)
            unorm[fid] = n.clamp01(u_local)
            vnorm[fid] = n.clamp01(v_local)
        frame_valid = None
        for fid in frame_ids:
            term = n.math('MULTIPLY', sel[fid], valid[fid])
            frame_valid = term if frame_valid is None else n.math('ADD', frame_valid, term)
        wf['valid'] = n.clamp01(frame_valid)
        atlas_uv = {}

        def atlas_vector(atlas):
            if atlas in atlas_uv:
                return atlas_uv[atlas]
            info = manifest['frames']['atlases'][atlas]
            aw, ah = info['size']
            us = vs = None
            for fid in frame_ids:
                rect = info['rects'][str(fid)]
                u_at = n.math('DIVIDE', n.math('ADD', n.math('MULTIPLY', unorm[fid], float(rect['w'])), float(rect['x'])), float(aw))
                v_at = n.math('DIVIDE', n.math('ADD', n.math('MULTIPLY', vnorm[fid], float(rect['h'])), float(rect['y'])), float(ah))
                u_at, v_at = n.math('MULTIPLY', u_at, sel[fid]), n.math('MULTIPLY', v_at, sel[fid])
                us = u_at if us is None else n.math('ADD', us, u_at)
                vs = v_at if vs is None else n.math('ADD', vs, v_at)
            atlas_uv[atlas] = n.combine(us, vs, 0.0)
            return atlas_uv[atlas]

        def wf_value(name):
            entry = mp.entry('WF', name)
            if entry is None:
                return None
            return channel(entry, atlas_vector(entry['picture']))
        wf['value'] = wf_value
        wf['atlas_vector'] = atlas_vector

    # ---- texture space
    tx_key = texture_key(manifest, chain.material_name)

    def tx_value(name):
        entry = mp.entry('TX', name)
        if entry is None or tx_key is None or entry['picture'] != 'tx:' + tx_key:
            return None
        return channel(entry, None)

    # ---- assemble every requested name
    results = {}
    ground_z = None
    for name in mask_list:
        out = None
        if name == 'ground_height':
            got = gp_value('ground_height')
            out = got[0] if got else 0.0
        elif name == 'height':
            got = gp_value('ground_height')
            gp_h = n.math('MULTIPLY', n.math('SUBTRACT', pz, got[0]), got[1]) if got else 0.0
            if wf:
                entry = mp.entry('WF', 'height')
                baked = n.math('ADD', n.math('MULTIPLY', channel(entry, wf['atlas_vector'](entry['picture'])), pack_module.HEIGHT_RANGE[1] - pack_module.HEIGHT_RANGE[0]), pack_module.HEIGHT_RANGE[0]) if entry else None
                out = n.mix(wf['valid'], gp_h, baked) if baked is not None else gp_h
            else:
                out = gp_h
        elif name == 'frame_valid':
            out = wf['valid'] if wf else 0.0
        elif name.startswith('tx_'):
            v = tx_value(name)
            out = v if v is not None else names_module.default_of(name)
        else:
            gp = gp_value(name)
            wfv = wf['value'](name) if wf else None
            default = names_module.default_of(name)
            if gp is not None and wfv is not None:
                out = n.mix(wf['valid'], gp, wfv)
            elif wfv is not None:
                out = n.mix(wf['valid'], default, wfv)
            elif gp is not None:
                out = gp
            else:
                out = default
        results[name] = out
    for name in mask_list:
        socket = gout.inputs[names_module.mask_socket(name)]
        value = results[name]
        if isinstance(value, bpy.types.NodeSocket):
            tree.links.new(value, socket)
        else:
            socket.default_value = float(value)
    return tree


def available(kit):
    """The bus names the loaded pack can supply (by frame)."""
    masks = kit.mask_pack.manifest['masks']
    return {frame: sorted(entries) for frame, entries in masks.items()}
