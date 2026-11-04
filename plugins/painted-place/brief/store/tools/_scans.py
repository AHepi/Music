"""
What this file does: loads the store's scanned models (Poly Haven plants and branches in store/scans/, fetched by
scans/fetch_scans.py) for the tools that use them: each piece becomes a shape standing at the origin on its own foot,
and its material learns to read the numbers the tool writes on each copy (how dry, how wet), so a scanned clump of grass
goes straw-coloured on a dry crown and dark in the wet like the store's own. (A name starting with '_' keeps it out of
the store's list of tools.)

    import _scans
    held = _scans.shapes([('grass_medium_01', ['large', 'tall'])], collection, 'tussocks', size=1.0)   # None if no scan is here
"""

import json
import os

import bpy
import numpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
SCANS = os.path.join(os.path.dirname(TOOLS), 'scans')


def available(scan_id):
    path = os.path.join(SCANS, 'manifest.json')
    if not os.path.exists(path):
        return False
    manifest = json.load(open(path))
    return scan_id in manifest and os.path.exists(os.path.join(SCANS, scan_id, manifest[scan_id]['file']))


def _import(scan_id):
    """Every mesh of the scan, imported once (kept hidden, out of the scene), by name."""
    held = bpy.data.collections.get('scan • ' + scan_id)
    if held is not None:
        return {obj.name: obj for obj in held.objects if obj.type == 'MESH'}
    manifest = json.load(open(os.path.join(SCANS, 'manifest.json')))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SCANS, scan_id, manifest[scan_id]['file']))
    held = bpy.data.collections.new('scan • ' + scan_id)
    for obj in set(bpy.data.objects) - before:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        held.objects.link(obj)
    return {obj.name: obj for obj in held.objects if obj.type == 'MESH'}


def tinted(material):
    """A copy of a scanned material that reads, from each copy's point, how dry it is ('grass_dry': greens fade to
    straw) and how wet ('wetness': darker, with a sheen)."""
    name = material.name + ' • store'
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    copy = material.copy()
    copy.name = name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    principled = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if principled is None or not principled.inputs['Base Color'].links:
        return copy
    source = principled.inputs['Base Color'].links[0].from_socket
    shift = nodes.new('ShaderNodeHueSaturation')
    links.new(source, shift.inputs['Color'])

    def attribute(name):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_type = 'INSTANCER'
        node.attribute_name = name
        return node.outputs['Fac']

    def math(operation, a, b):
        node = nodes.new('ShaderNodeMath')
        node.operation = operation
        for socket, value in zip(node.inputs, (a, b)):
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, socket)
            else:
                socket.default_value = value
        return node.outputs[0]
    dry = attribute('grass_dry')                               # a copy without these numbers reads 0: green and dry
    wet = attribute('wetness')
    links.new(math('SUBTRACT', 0.5, math('MULTIPLY', dry, 0.05)), shift.inputs['Hue'])
    links.new(math('SUBTRACT', 1.0, math('MULTIPLY', dry, 0.5)), shift.inputs['Saturation'])
    links.new(math('SUBTRACT', math('ADD', 0.85, math('MULTIPLY', dry, 0.25)), math('MULTIPLY', wet, 0.3)), shift.inputs['Value'])
    links.new(shift.outputs['Color'], principled.inputs['Base Color'])
    links.new(math('MULTIPLY', wet, 0.5), principled.inputs['Coat Weight'])
    principled.inputs['Coat Roughness'].default_value = 0.15
    return copy


def shapes(sources, collection, name, size=1.0, along='z', turn_to_x=False):
    """A hidden collection of the pieces of the scans in `sources` ([(scan id, [words in the pieces' names]), ...]),
    each standing on its foot at the origin and scaled so its height (along='z') or its length (along='length') is
    `size` metres; None if none of the scans is in the store."""
    sources = [(scan_id, picks) for scan_id, picks in sources if available(scan_id)]
    if not sources:
        return None
    full = 'scan shapes • ' + name
    held = bpy.data.collections.get(full)
    if held is not None and len(held.objects):
        if held.name not in collection.children:
            collection.children.link(held)
        return held
    held = bpy.data.collections.new(full)
    collection.children.link(held)
    held.hide_render = True
    held.hide_viewport = True
    chosen = []
    for scan_id, picks in sources:
        pieces = _import(scan_id)
        chosen += [pieces[piece] for piece in sorted(pieces) if any(pick in piece for pick in picks)]
    for source in chosen:
        piece_name = source.name
        mesh = source.data.copy()
        points = numpy.zeros(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get('co', points)
        points = points.reshape(-1, 3) @ numpy.array(source.matrix_basis.to_3x3()).T
        if turn_to_x:                                          # lying along Y in the scan: turned to lie along X
            points = points[:, [1, 0, 2]] * numpy.array([1.0, -1.0, 1.0])
        low, high = points.min(axis=0), points.max(axis=0)
        points[:, 0] -= (low[0] + high[0]) / 2.0
        points[:, 1] -= (low[1] + high[1]) / 2.0
        points[:, 2] -= low[2]
        extent = (high[2] - low[2]) if along == 'z' else max(high[0] - low[0], high[1] - low[1])
        points *= size / max(extent, 1e-6)
        mesh.vertices.foreach_set('co', points.ravel())
        mesh.update()
        for index, material in enumerate(mesh.materials):
            if material is not None:
                mesh.materials[index] = tinted(material)
        held.objects.link(bpy.data.objects.new('%s shape %s' % (name, piece_name), mesh))
    return held if len(held.objects) else None
