"""What this does: puts the wear layers into a material, in their FIXED ORDER, wired from the material's own surface. Every time it is called it first takes away what an earlier
call added (hook.restore_base), then rebuilds the whole chain from the list, so applying twice and then removing gives the same node counts and the same picture as before (a chain
that remembers its wires cuts other layers out when one is removed; this one never remembers wires). The order, measured on an earlier outdoor test: dirt, grime, weathering, rust (iron), then
wetness (so water sits on the dirt), then cracks and chips and edge wear (they stay dull when wet), then moss, then rubbish last. Each layer gets the six bundle values from the one
before it (the first from the material's own wires), its masks by name from the material's Plan node, and its dial numbers; the last layer's outputs go into the Principled plugs.
A material that glows (a lit window, a lantern) or has no Principled box is skipped and the reason is returned. It needs Blender (bpy).
A concrete example: insert_layers(material, ['dirt', 'wetness'], {'dirt': {...}, 'wetness': {...}}, plan_masks) gives a material whose Base Color comes from PK Wetness, fed by PK Dirt,
fed by the surface's own colour.
"""
import importlib

import bpy

from .. import names
from . import dials as dials_module, hook, layer_base, plan_group

BUILDERS = {'dirt': 'dirt', 'grime': 'grime', 'weathering': 'weathering', 'rust': 'rust', 'wetness': 'wetness', 'cracks_and_chips': 'cracks_and_chips', 'edge_wear': 'edge_wear',
            'moss_and_algae': 'moss_and_algae', 'rubbish': 'rubbish'}


def layer_tree(key):
    """The layer's node group (built the first time; reused after, unless it is from an older version of the kit and nobody uses it)."""
    existing = bpy.data.node_groups.get(names.layer_group_name(key))
    if existing is not None and existing.get('pk_version') == layer_base.GROUP_VERSION:
        return existing
    module = importlib.import_module(f'{__package__}.layers.{BUILDERS[key]}')
    return getattr(module, f'build_{key}')()


SEAM_TAG = 'seam'


def add_seam_blend(material, plan_node, colour_socket):
    """For a GROUND material: mixes the colour toward the other ground surface near their seam (the Plan node's Seam Blend and Seam R, G, B), broken up by a noise of
    about 40 cm, so two ground surfaces meet in a ragged, soft band instead of a ruled line (a straight edge between grass and earth once read as a brown rectangle
    laid on the meadow). Far from any seam the blend is 0 and the colour is exactly as it was. Returns the new colour socket."""
    from .nodes import Net
    tree = material.node_tree
    before = set(node.name for node in tree.nodes)
    net = Net(tree)
    position = net.geometry().outputs['Position']
    ragged = net.noise(net.scale_vector(position, 2.5), scale=1.0, detail=3.0)
    factor = net.clamp01(net.math('MULTIPLY', plan_node.outputs['Seam Blend'], net.map_range(ragged, 0.3, 0.7, 0.4, 1.6)))
    other = net.comb_rgb(plan_node.outputs['Seam R'], plan_node.outputs['Seam G'], plan_node.outputs['Seam B'])
    result = net.mix_colour(factor, colour_socket, other)
    for node in tree.nodes:
        if node.name not in before:
            hook.tag(node, SEAM_TAG)
    return result


def insert_layers(material, layer_keys, dials_by_layer, plan_masks, master=1.0, layer_masters=None, dot_metres=None, seam_blend=False):
    """Rebuilds the material's chain with these layers (those in names.LAYER_ORDER, in that order). seam_blend=True (ground materials) also blends the colour into the
    neighbouring ground surface near their seam (add_seam_blend). Returns (layers inserted, reason skipped or None)."""
    reason, principled = hook.classify(material)
    if reason != 'ok':
        return [], reason
    hook.restore_base(material)
    record = hook.remember_base(material, principled)
    tree = material.node_tree
    ordered = [key for key in names.LAYER_ORDER if key in layer_keys]
    if not ordered:
        return [], None
    origin = hook.Origin(material, record)
    plan_node = tree.nodes.new('ShaderNodeGroup')
    plan_node.node_tree = bpy.data.node_groups.get(names.PLAN_GROUP) or plan_group.build_plan_group()
    plan_node.name = plan_node.label = 'PK Plan'
    hook.tag(plan_node, 'plan')
    plan_node.location = (principled.location.x - 700, principled.location.y + 700)
    if plan_masks is not None:
        plan_group.set_bounds(plan_node, plan_masks)
    current = {port: origin.socket(port) for port in hook.BUNDLE}
    layer_masters = layer_masters or {}
    for position, key in enumerate(ordered):
        node = tree.nodes.new('ShaderNodeGroup')
        node.node_tree = layer_tree(key)
        node.name = f'PK {key}'
        node.label = f'PK {key}'
        hook.tag(node, key)
        node.location = (principled.location.x - 500 - 220 * (len(ordered) - position), principled.location.y + 300)
        for port in hook.BUNDLE:
            tree.links.new(current[port], node.inputs[port])
        for socket in node.inputs:
            if socket.name.startswith('M ') and socket.name[2:] in plan_node.outputs:
                tree.links.new(plan_node.outputs[socket.name[2:]], socket)
        values = dict(dials_by_layer.get(key, {}))
        for dial, value in values.items():
            socket = node.inputs.get(dials_module.socket_name(dial))
            if socket is not None and dial not in ('amount', 'seed'):
                socket.default_value = float(value)
        node.inputs['Seed'].default_value = float(values.get('seed', 0.0))
        node.inputs['Amount'].default_value = float(master) * float(layer_masters.get(key, 1.0)) * float(values.get('amount', 1.0))
        if dot_metres is not None:
            node.inputs['Dot Metres'].default_value = float(dot_metres)
        current = {port: node.outputs[port] for port in hook.BUNDLE}
    if seam_blend and 'Seam Blend' in plan_node.outputs:
        current['Colour'] = add_seam_blend(material, plan_node, current['Colour'])
    for port in hook.BUNDLE:
        socket = principled.inputs[hook.PLUG[port]]
        for link in list(socket.links):
            tree.links.remove(link)
        tree.links.new(current[port], socket)
    return ordered, None


def layer_nodes(material, key=None):
    """The wear layer group nodes in a material (all, or one layer's)."""
    if material.node_tree is None:
        return []
    return [n for n in hook.kit_nodes(material.node_tree) if n.get(hook.TAG) in names.LAYER_ORDER and (key is None or n[hook.TAG] == key)]


def chain_keys(material):
    """The layers in the material's chain, in the order they are wired (read back from the nodes)."""
    return [n[hook.TAG] for n in sorted(layer_nodes(material), key=lambda node: names.LAYER_ORDER.index(node[hook.TAG]))]
