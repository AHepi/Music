# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CHECKING VIEWS. show_mask(kit, name) draws one bus mask as plain grey light on every material the kit has hooked (so any camera shows where the mask is); the undo function it
# returns puts every material back exactly. plan(kit, name, ...) makes an orthographic camera straight above the ground bounds so a mask can be seen as a map.
# These change materials only while a view is shown; nothing here belongs to a look.
import bpy

from apply import hook, nodes
from . import bus as bus_module, names as names_module


VIEW_DIVISOR = {'height': 8.0, 'ground_height': 8.0}      # metres masks are shown as metres / 8 so a plain-light picture does not clip at 1.0


def _emit(tree, output, socket_r, socket_g, socket_b):
    link = output.inputs['Surface'].links[0] if output.inputs['Surface'].links else None
    old_from = link.from_socket if link else None
    emission = tree.nodes.new('ShaderNodeEmission')
    combine = tree.nodes.new('ShaderNodeCombineColor')
    hook.tag(emission, 'debug')
    hook.tag(combine, 'debug')
    for channel, socket in (('Red', socket_r), ('Green', socket_g), ('Blue', socket_b)):
        if socket is not None:
            tree.links.new(socket, combine.inputs[channel])
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return (tree, old_from, output, emission, combine)


def _undo(saved):
    for tree, old_from, output, emission, combine in saved:
        if old_from is not None:
            tree.links.new(old_from, output.inputs['Surface'])
        tree.nodes.remove(emission)
        tree.nodes.remove(combine)
        for node in [n for n in tree.nodes if n.get('wk') == 'debug']:
            tree.nodes.remove(node)


def _blackout(kit, handled):
    """Black plain light on every material the view did not handle (skipped, never-listed, glowing materials), so a mask view shows only what the mask says."""
    saved = []
    for material in bpy.data.materials:
        if material.node_tree is None or material.name in handled:
            continue
        output = hook.active_output(material.node_tree)
        if output is None:
            continue
        saved.append(_emit(material.node_tree, output, None, None, None))
    return saved


def show_layer(kit, key):
    """Each layer node's own 'Mask' output as grey light on its materials; materials without the layer go black."""
    saved = []
    for name in kit.hookable():
        chain = kit.chain_for(name)
        if chain is None:
            continue
        tree = chain.tree
        output = hook.active_output(tree)
        node = chain.node(key)
        socket = node.outputs['Mask'] if node is not None else None
        saved.append(_emit(tree, output, socket, socket, socket))
    saved += _blackout(kit, set(kit.hookable()) - set(kit.skipped))
    return lambda: _undo(saved)


def show_stage(kit, stage_key, output_name, channels='R'):
    """An output of an earlier layer's node (for example the water layer's Puddle Mask, the rubbish layer's Rubbish Mask) as light on every material that has that stage;
    everything else black. channels 'R' puts it in red only (the measures read red), 'RGB' in all three."""
    saved = []
    for name in kit.hookable():
        chain = kit.chain_for(name)
        if chain is None:
            continue
        tree = chain.tree
        output = hook.active_output(tree)
        node = chain.node(stage_key)
        socket = node.outputs[output_name] if node is not None and output_name in node.outputs else None
        saved.append(_emit(tree, output, socket, socket if channels == 'RGB' else None, socket if channels == 'RGB' else None))
    saved += _blackout(kit, set(kit.hookable()) - set(kit.skipped))
    return lambda: _undo(saved)


def show_puddles(kit):
    """The water layer's Puddle Mask as red on every material that has the water layer; everything else black (the earlier checking view)."""
    saved = []
    for name in kit.hookable():
        chain = kit.chain_for(name)
        if chain is None:
            continue
        tree = chain.tree
        output = hook.active_output(tree)
        node = chain.node('wetness')
        socket = node.outputs['Puddle Mask'] if node is not None else None
        saved.append(_emit(tree, output, socket, None, None))
    saved += _blackout(kit, set(kit.hookable()) - set(kit.skipped))
    return lambda: _undo(saved)


def show_mask(kit, name, materials=None, raw=True):
    """Replaces the surface of every hookable material by Emission of the named mask (grey), or of up to three masks given as a list (R, G, B). Returns undo()."""
    if isinstance(name, (list, tuple)):
        names = list(name)
    else:
        names = [name]
    scene = bpy.context.scene
    saved = []
    keep_view = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma)
    if raw:
        scene.view_settings.view_transform = 'Raw'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
    for material_name in (materials or kit.hookable()):
        if material_name in kit.skipped:
            continue
        chain = kit.chain_for(material_name)
        if chain is None:
            continue
        tree = chain.tree
        output = hook.active_output(tree)
        needed = kit.bus_needed.setdefault(material_name, set())
        if not set(names) <= needed:
            needed |= set(names)
            bus_module.rebuild_bus(kit, chain)
        bus = next(n for n in tree.nodes if n.get('wk') == bus_module.BUS_TAG)
        sockets = []
        for n_ in names:
            sock = bus.outputs[names_module.mask_socket(n_)]
            if n_ in VIEW_DIVISOR:
                div = tree.nodes.new('ShaderNodeMath')
                div.operation = 'DIVIDE'
                hook.tag(div, 'debug')
                div.inputs[1].default_value = VIEW_DIVISOR[n_]
                tree.links.new(sock, div.inputs[0])
                sock = div.outputs[0]
            sockets.append(sock)
        if len(sockets) == 1:
            sockets = sockets * 3
        while len(sockets) < 3:
            sockets.append(None)
        saved.append(_emit(tree, output, sockets[0], sockets[1], sockets[2]))

    def undo():
        _undo(saved)
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = keep_view
    return undo


def plan_camera(settings, margin=0.0):
    """An orthographic camera straight above the ground bounds (the whole picture area, long side vertical). Returns the camera object (linked to the scene)."""
    b = settings.geometry['ground']['bounds']
    cx, cy = 0.5 * (b['x'][0] + b['x'][1]), 0.5 * (b['y'][0] + b['y'][1])
    height = (b['y'][1] - b['y'][0]) + margin
    data = bpy.data.cameras.new('wk_plan_camera')
    data.type = 'ORTHO'
    data.sensor_fit = 'VERTICAL'
    data.ortho_scale = height
    data.clip_start, data.clip_end = 1.0, 800.0
    obj = bpy.data.objects.new('wk_plan_camera', data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (cx, cy, 200.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    return obj
