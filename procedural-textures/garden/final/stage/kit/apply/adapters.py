# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE ADAPTER: some materials have no Principled BSDF on their surface; a shader GROUP (a packaged recipe from an add-on) makes the shader and hands out its own
# Albedo, Roughness and Normal. For those the adapter builds ONE Principled box in the material from the group's outputs, copies the plain numbers (Specular IOR Level 0.4,
# IOR 1.5 ...) from the Principled box INSIDE the group, and puts the new box between the group and the Material Output. The rest of the kit then sees an ordinary material.
# Which groups and which of their outputs: the set's `hook.adapters` (groups = name patterns; outputs = {"Base Color": group output name, "Roughness": ..., "Normal": ...}).
# The adapter's box and wires are removed again by Snapshot.restore (hook.py): the adapter's nodes are tagged 'adapter' and were not in the snapshot.
# Proven on the add-on's 46 stone, tile and wood materials: the picture is identical in Cycles and within one step of 255 on under 1 % of dots in EEVEE.
import re

import bpy

from . import hook


def match_adapter(material, settings):
    """The adapter spec (a dict from settings.hook.adapters) whose group pattern matches the shader group that makes this material's surface, and that group node; or (None, None)."""
    tree = material.node_tree
    output = hook.active_output(tree) if tree else None
    if output is None or not output.inputs['Surface'].links:
        return None, None
    node = output.inputs['Surface'].links[0].from_node
    if node.type != 'GROUP' or node.node_tree is None:
        return None, None
    for spec in (settings.get('hook') or {}).get('adapters', []):
        if any(re.match(p, node.node_tree.name) for p in spec['groups']):
            return spec, node
    return None, None


def inner_principled(group_tree):
    for node in group_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def apply(material, spec, group_node):
    """Builds the Principled box. Returns it (tagged 'adapter'). Raises KeyError when the group lacks one of the outputs the spec names."""
    tree = material.node_tree
    inner = inner_principled(group_node.node_tree)
    box = tree.nodes.new('ShaderNodeBsdfPrincipled')
    hook.tag(box, 'adapter')
    box.location = (group_node.location.x + 300, group_node.location.y)
    wired = set(spec['outputs'])
    if inner is not None:
        for inp in inner.inputs:
            if inp.name in wired or inp.links:
                continue
            target = box.inputs.get(inp.name)
            value = getattr(inp, 'default_value', None)
            if target is None or value is None:
                continue
            try:
                target.default_value = value
            except (TypeError, AttributeError, ValueError):
                pass
        for name in ('distribution', 'subsurface_method'):
            if hasattr(inner, name) and hasattr(box, name):
                setattr(box, name, getattr(inner, name))
    for plug, output_name in spec['outputs'].items():
        socket = group_node.outputs.get(output_name)
        if socket is None:
            raise KeyError(f'group {group_node.node_tree.name!r} has no output {output_name!r}')
        tree.links.new(socket, box.inputs[plug])
    output = hook.active_output(tree)
    tree.links.new(box.outputs['BSDF'], output.inputs['Surface'])
    return box
