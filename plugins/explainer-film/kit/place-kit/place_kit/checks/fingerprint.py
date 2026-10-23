"""What this does: takes a FINGERPRINT of a whole Blender scene: a compact record of every object (its matrix, a hash of its mesh with UVs, its material slots, its modifiers, its collections,
its owner and role), every material and node group (a hash of its nodes and links), the collections, and the state that must stay frozen while parts are built side by side (render settings,
the camera, the world, the lights). Two fingerprints can be compared to see exactly what a builder's stage changed (ownership.py does that against who owns what). Needs Blender (bpy) and numpy.
A concrete example: fingerprint_scene()['objects']['plank 3']['mesh'] is a short hash; after a stage moves one vertex of that plank only that hash changes.
"""
import hashlib
import json

import numpy as np

import bpy

from .. import names


def _hash(data):
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]


def mesh_hash(mesh):
    """A hash of a mesh's points (to 0.01 mm), its faces and its UV layers."""
    count = len(mesh.vertices)
    digest = hashlib.md5()
    if count:
        coords = np.empty(count * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', coords)
        digest.update(np.round(coords, 5).tobytes())
    loops = len(mesh.loops)
    if loops:
        indices = np.empty(loops, dtype=np.int64)
        mesh.loops.foreach_get('vertex_index', indices)
        digest.update(indices.tobytes())
    for layer in mesh.uv_layers:
        uv = np.empty(loops * 2, dtype=np.float32)
        layer.uv.foreach_get('vector', uv)
        digest.update(layer.name.encode() + np.round(uv, 4).tobytes())
    return digest.hexdigest()[:12]


def node_tree_hash(tree):
    """A hash of a node tree: its nodes (kind, name, plain input numbers) and links."""
    nodes = []
    for node in sorted(tree.nodes, key=lambda n: n.name):
        values = []
        for socket in node.inputs:
            value = getattr(socket, 'default_value', None)
            if value is None:
                continue
            try:
                values.append([socket.identifier, [round(float(v), 5) for v in value]])
            except TypeError:
                try:
                    values.append([socket.identifier, round(float(value), 5)])
                except (TypeError, ValueError):
                    pass
        nodes.append([node.bl_idname, node.name, values, node.node_tree.name if getattr(node, 'node_tree', None) else None, getattr(getattr(node, 'image', None), 'name', None)])
    links = sorted([l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier] for l in tree.links)
    return _hash([nodes, links])


def fingerprint_scene():
    """{objects, materials, node_groups, collections, frozen} (see the note at the top)."""
    scene = bpy.context.scene
    bpy.context.view_layer.update()                    # a new or moved object keeps its old world matrix until the scene is updated
    objects = {}
    for obj in bpy.data.objects:
        entry = {'type': obj.type, 'matrix': [round(v, 5) for row in obj.matrix_world for v in row], 'collections': sorted(c.name for c in obj.users_collection),
                 'owner': obj.get(names.OWNER), 'role': obj.get(names.ROLE), 'made': bool(obj.get(names.MADE)), 'modifiers': [[m.name, m.type] for m in obj.modifiers],
                 'slots': [s.material.name if s.material else None for s in obj.material_slots], 'hidden': bool(obj.hide_render)}
        if obj.type == 'MESH':
            entry['mesh'] = mesh_hash(obj.data)
        if obj.type == 'LIGHT':
            entry['light'] = [obj.data.type, round(obj.data.energy, 4), [round(c, 4) for c in obj.data.color]]
        objects[obj.name] = entry
    materials = {m.name: node_tree_hash(m.node_tree) if m.node_tree else None for m in bpy.data.materials}
    groups = {g.name: node_tree_hash(g) for g in bpy.data.node_groups}
    collections = {c.name: sorted([o.name for o in c.objects] + [child.name for child in c.children]) for c in bpy.data.collections}
    camera = scene.camera
    frozen = {'render': {'engine': scene.render.engine, 'resolution': [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage]},
              'cycles': {'device': getattr(scene.cycles, 'device', None), 'samples': getattr(scene.cycles, 'samples', None)},
              'view': {'transform': scene.view_settings.view_transform, 'exposure': round(scene.view_settings.exposure, 4)},
              'camera': {'name': camera.name, 'matrix': [round(v, 5) for row in camera.matrix_world for v in row], 'lens': round(camera.data.lens, 4)} if camera is not None else None,
              'world': {'name': scene.world.name, 'hash': node_tree_hash(scene.world.node_tree) if scene.world and scene.world.node_tree else None} if scene.world else None,
              'lights': sorted([o.name for o in bpy.data.objects if o.type == 'LIGHT'])}
    return {'objects': objects, 'materials': materials, 'node_groups': groups, 'collections': collections, 'frozen': frozen}
