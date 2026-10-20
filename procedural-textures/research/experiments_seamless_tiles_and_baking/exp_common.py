# What this does: small shared helpers for the seamless-tile and baking experiments in this folder. It sits on top of the
# project's own lib/ (bake_harness.py and recipe_tools.py), so every experiment photographs a flat 1 x 1 square from straight above
# the same way the real bakes do. Nothing in here changes lib/.
# Use (inside Blender):  import exp_common as ec
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
LIB = os.path.join(PROC, 'lib')
sys.path.insert(0, LIB)
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402

OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)


def pattern_group(name, build):
    """A node group with input Vector and one output Height. build(writer) adds nodes to the writer and returns
    (node_name, output_socket) to send to Height."""
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    node_name, socket = build(w)
    w.link(node_name, socket, 'out', 'Height')
    return tree


def render_patterns(patterns, out_folder, size=512, sixteen=True):
    """patterns: dict name -> build function (see pattern_group). Writes one PNG per pattern (the Height output as linear grey)."""
    os.makedirs(out_folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(size)
    paths = {}
    for name, build in patterns.items():
        group = pattern_group('pat ' + name, build)
        material = bh.show_channel_material(group, 'Height')
        tile.data.materials.clear()
        tile.data.materials.append(material)
        path = os.path.join(out_folder, name + '.png')
        bh.render_to(scene, path, True, sixteen)
        paths[name] = path
    return paths


def shifted_group(inner, offset, name):
    """A group that adds `offset` (x, y, z) to the Vector before sending it into `inner`, and passes the Height output through.
    Used for the exact tiling test: a pattern that tiles must look the same when its coordinates are moved by one whole tile."""
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    w.vector_math('shift', 'ADD', x=1)
    w.nodes['shift'].inputs[1].default_value = offset
    w.link('in', 'Vector', 'shift', 0)
    w.add('ShaderNodeGroup', 'inner', x=2)
    w.nodes['inner'].node_tree = inner
    w.link('shift', 0, 'inner', 'Vector')
    w.link('inner', 'Height', 'out', 'Height')
    return tree


def render_patterns_shifted(patterns, out_folder, offsets, size=512, sixteen=True):
    """Like render_patterns, but also renders every pattern with its coordinates moved by each offset in `offsets`
    (a dict label -> (x, y, z)). Files are NAME__label.png (and NAME__base.png)."""
    os.makedirs(out_folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(size)
    for name, build in patterns.items():
        inner = pattern_group('pat ' + name, build)
        versions = {'base': inner}
        for label, offset in offsets.items():
            versions[label] = shifted_group(inner, offset, f'shift {label} {name}')
        for label, group in versions.items():
            material = bh.show_channel_material(group, 'Height')
            tile.data.materials.clear()
            tile.data.materials.append(material)
            bh.render_to(scene, os.path.join(out_folder, f'{name}__{label}.png'), True, sixteen)


def sep_uv(w, prefix=''):
    """Adds Separate XYZ on the group's Vector input; returns the node name whose X and Y outputs are u and v."""
    name = prefix + 'uv'
    w.add('ShaderNodeSeparateXYZ', name, x=-3)
    w.link('in', 'Vector', name, 'Vector')
    return name


def write_json(data, name):
    with open(os.path.join(OUT, name), 'w') as handle:
        json.dump(data, handle, indent=1, default=float)
