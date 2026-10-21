# What this does (plain words): STUDY ONLY, saves nothing (it draws two small pictures into the study's out folder). It tests the way a NEW layer could hook into ANY material: for every material
# that has a Principled BSDF, take whatever feeds Base Color, Roughness, Specular IOR Level, Coat Weight and Normal (a link, OR a plain number or colour that has no link at all, which the
# earlier layers' code cannot handle), put a do-nothing group between that source and the Principled BSDF, and wire it through. Then it draws the street twice, with and without the do-nothing
# group, and counts how many dots differ. Same method as the earlier layers' "Amount 0 = exactly the picture without the layer" self-test.
# Run: blender -b --disable-autoexec FILE --python s9_splice_test.py -- OUT_FOLDER [camera]
import json, os, sys
import bpy
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
out_folder = args[0]
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
SOCKETS = (('Base Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'), ('Coat Weight', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'))


def passthrough_group():
    g = bpy.data.node_groups.get('STUDY PASSTHROUGH')
    if g:
        return g
    g = bpy.data.node_groups.new('STUDY PASSTHROUGH', 'ShaderNodeTree')
    for name, kind in SOCKETS:
        g.interface.new_socket(name=name, in_out='INPUT', socket_type=kind)
        g.interface.new_socket(name=name, in_out='OUTPUT', socket_type=kind)
    gi, go = g.nodes.new('NodeGroupInput'), g.nodes.new('NodeGroupOutput')
    for name, _ in SOCKETS:
        g.links.new(gi.outputs[name], go.inputs[name])
    return g


def source_of(tree, socket):
    """A socket that carries what feeds `socket`: the linked source, or a new Value / RGB node holding its constant (Normal with no link: the surface's own normal)."""
    if socket.is_linked:
        return socket.links[0].from_socket
    if socket.name == 'Normal':
        geo = tree.nodes.new('ShaderNodeNewGeometry')
        return geo.outputs['Normal']
    if socket.type == 'RGBA':
        n = tree.nodes.new('ShaderNodeRGB')
        n.outputs[0].default_value = socket.default_value
        return n.outputs[0]
    n = tree.nodes.new('ShaderNodeValue')
    n.outputs[0].default_value = socket.default_value
    return n.outputs[0]


stats = dict(hooked=0, skipped_no_principled=0, constants_created=0, errors=[])
skipped = []
for mat in bpy.data.materials:
    if mat.users == 0 or not mat.use_nodes or mat.node_tree is None:
        continue
    tree = mat.node_tree
    out = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    # the BSDF that feeds the output directly: only then is it a plain surface we can hook
    p = None
    if out and out.inputs['Surface'].is_linked and out.inputs['Surface'].links[0].from_node.type == 'BSDF_PRINCIPLED':
        p = out.inputs['Surface'].links[0].from_node
    if p is None:
        stats['skipped_no_principled'] += 1
        skipped.append(mat.name)
        continue
    try:
        node = tree.nodes.new('ShaderNodeGroup')
        node.node_tree = passthrough_group()
        for name, _ in SOCKETS:
            wired_before = p.inputs[name].is_linked
            src = source_of(tree, p.inputs[name])
            stats['constants_created'] += (not wired_before)
            tree.links.new(src, node.inputs[name])
            tree.links.new(node.outputs[name], p.inputs[name])
        stats['hooked'] += 1
    except Exception as exc:                                    # noqa: BLE001
        stats['errors'].append((mat.name, repr(exc)))
stats['skipped'] = skipped
json.dump(stats, open(os.path.join(out_folder, 'splice_stats.json'), 'w'), indent=1)
print('SPLICE', json.dumps({k: v for k, v in stats.items() if k != 'skipped'}))
