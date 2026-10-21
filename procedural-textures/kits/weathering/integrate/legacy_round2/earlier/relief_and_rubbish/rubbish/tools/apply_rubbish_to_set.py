# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The ONE script that puts the rubbish on the street copy (or on the film's lockout shot file, opened read-only). Like the wetness layer and the JOINTS layer it is put on inside
# Blender each time a picture is drawn; the street file itself is never changed on disk, and nothing in the film project's own folder is touched.
# It puts the muck layer RUBBISH (rubbish_layer.py) after the other layers on the road, the pavement flags, the gutter stones and the kerb stones, and the scatter of small 3D
# pieces (rubbish_pieces.py) on the ground. One mask drives both.
#
# Use (inside Blender, with the street copy or the lockout shot file open):
#     import apply_wetness_to_set as aw
#     import apply_joints_to_set as aj
#     import apply_rubbish_to_set as ar
#     aw.apply(wetness=0.85, puddles=0.5)         # the water layer first
#     aj.apply()                                  # the joints between the setts (road only)
#     ar.apply(places='street')                   # the rubbish, normal strength. For the lockout shot file: ar.apply(places='lockout')
#     ar.apply(places='lockout', amount=1.5, gutter=1.2, props=0)     # heavier, more in the gutter, nothing round the props
#     ar.set_dials(wall_foot=0.5, seed=3)         # change a dial of what is already on
#     ar.set_state(0.85)                          # tell the pieces how wet the street is (paper goes dark, coal shiny); aw.set_state does not reach them
#     ar.pieces(False)                            # hide the separate 3D pieces (the painted muck stays)
#     undo = ar.show_mask('colours')              # checking view: the mask drawn on the ground, red = gutter, green = wall foot, blue = corners and doorsteps, yellow = props
#     undo()                                      # back to the normal look
#     ar.remove()                                 # everything off again
# The dials (short names with underscores; the long names are on the group's node): amount, gutter, wall_foot, corners, props, seed, patchiness, gutter_width, wall_width, props_width,
# crown_clear, dust, ash, mud, straw, paper, leaves, dust_darkness, grit_size, relief, wet_look; and for the pieces: pieces_density, pieces_distance, piece_size.
# What each does is at the top of rubbish_layer.py and rubbish_pieces.py and in the recipe note.
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
RUBBISH = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(RUBBISH, '..', '..'))        # street_wet
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402
import rubbish_layer as rl  # noqa: E402
import rubbish_pieces as rp  # noqa: E402

_STATE = {'nodes': {}, 'undos': {}, 'host': None, 'places': None}


def apply(places='street', pieces=True, **dials):
    """Puts the rubbish on. places = 'street' (the street copy) or 'lockout' (the lockout shot file, with its props). Calling it twice takes the first one off first."""
    remove()
    for name in rl.SHADER_MATERIALS:
        wetness_node = aw.APPLIED[name][0]
        node, undo = rl.add_rubbish_to_material(bpy.data.materials[name], wetness_node, **{k: v for k, v in dials.items() if k in rl.DIAL_SOCKETS})
        _STATE['nodes'][name], _STATE['undos'][name] = node, undo
    rl.build_rubbish_group()
    if pieces:
        _STATE['host'] = rp.add_scatter(bpy.context.scene)
    rl.set_places(places)
    _STATE['places'] = places
    set_dials(**dials)
    return _STATE['nodes']['street_setts']


def set_dials(**dials):
    """Changes dials of the rubbish that is already on (by short name). Both the painted layer and the scatter follow."""
    for key, value in dials.items():
        if key in rl.DIAL_SOCKETS:
            for node in _STATE['nodes'].values():
                node.inputs[rl.DIAL_SOCKETS[key]].default_value = value
        elif key not in rp.PIECE_SOCKETS:
            raise KeyError(f'unknown rubbish dial {key!r}')
    rp.set_scatter_dials(**dials)


def set_state(wetness):
    """How wet the separate pieces look (0 to 1)."""
    rp.set_wetness(wetness)


def set_view_point(location):
    """Tells the pieces where the camera is, for the size cap near it (round 2 plate). The picture runner calls it before every picture."""
    rp.set_view_point(location)


def pieces(visible):
    host = _STATE.get('host')
    if host is not None:
        host.hide_render = not visible
        host.hide_viewport = not visible


def piece_count():
    host = _STATE.get('host')
    return rp.count_pieces(host) if host is not None else 0


def show_mask(mode='colours', raw=True):
    """Checking view, not a look: the ground materials show the mask as plain light. mode 'total' (grey) or 'colours' (red gutter, green wall foot, blue corners and doorsteps,
    yellow props). With raw=True (the default) the scene's normal colour look is switched off (raw numbers, for measuring); raw=False keeps the film's own look so that the rest of the street can be seen. Returns an undo function."""
    scene = bpy.context.scene
    saved = []
    for name in rl.SHADER_MATERIALS:
        tree = bpy.data.materials[name].node_tree
        node = _STATE['nodes'][name]
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        link = next(l for l in tree.links if l.to_socket == output.inputs['Surface'])
        old_from = link.from_socket                     # keep the socket now: the link object is gone once the emission is plugged in
        emission = tree.nodes.new('ShaderNodeEmission')
        combine = tree.nodes.new('ShaderNodeCombineColor')
        if mode == 'total':
            for channel in ('Red', 'Green', 'Blue'):
                tree.links.new(node.outputs['Rubbish Mask'], combine.inputs[channel])
        else:
            def maximum(a, b, scale=1.0):
                m = tree.nodes.new('ShaderNodeMath')
                m.operation = 'MAXIMUM'
                tree.links.new(a, m.inputs[0])
                if isinstance(b, bpy.types.NodeSocket):
                    tree.links.new(b, m.inputs[1])
                return m.outputs[0]

            def scaled(a, k):
                m = tree.nodes.new('ShaderNodeMath')
                m.operation = 'MULTIPLY'
                tree.links.new(a, m.inputs[0])
                m.inputs[1].default_value = k
                return m.outputs[0]
            tree.links.new(maximum(node.outputs['Gutter Part'], scaled(node.outputs['Props Part'], 1.0)), combine.inputs['Red'])
            tree.links.new(maximum(node.outputs['Wall Part'], scaled(node.outputs['Props Part'], 0.75)), combine.inputs['Green'])
            tree.links.new(node.outputs['Corner Part'], combine.inputs['Blue'])
        tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        saved.append((tree, old_from, output, emission, combine))
    keep = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma)
    if raw:
        scene.view_settings.view_transform = 'Raw'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0

    def undo():
        for tree, old_from, output, emission, combine in saved:
            tree.links.new(old_from, output.inputs['Surface'])
            tree.nodes.remove(emission)
            tree.nodes.remove(combine)
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = keep
    return undo


def remove():
    for name, undo in list(_STATE['undos'].items()):
        undo()
    _STATE['undos'].clear()
    _STATE['nodes'].clear()
    host = _STATE.get('host')
    if host is not None:
        bpy.data.objects.remove(host)
        _STATE['host'] = None
    view = bpy.data.objects.get(rp.VIEW_POINT_NAME)
    if view is not None:
        bpy.data.objects.remove(view)
