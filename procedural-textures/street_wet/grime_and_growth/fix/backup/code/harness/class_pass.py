# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE CLASS PASS: draws every object in a flat number that says what ROLE it has (the object value wk_role_id / 64, raw), so any measure can cut a picture into surfaces
# (walls, trims, road, pavement, iron, roofs ...) without guessing from colour. Objects with no role are 0 (sky, glass, glow). Used with a material override, 1 sample, no
# smoothing, so every dot holds exactly one object's number: read the picture and multiply by 64.
import json

import bpy

from apply import nodes

OVERRIDE_NAME = 'wk_class_override'
DEPTH_NAME = 'wk_depth_override'
DEPTH_RANGE_M = 128.0     # a depth picture holds distance / 128 m (16 bit: 2 mm steps)


def make_material():
    material = bpy.data.materials.get(OVERRIDE_NAME)
    if material is not None:
        return material
    material = bpy.data.materials.new(OVERRIDE_NAME)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    n = nodes.Net(tree)
    value = n.math('DIVIDE', n.attr('wk_role_id'), 64.0)
    emission = n.new('ShaderNodeEmission')
    tree.links.new(n.comb_rgb(value, value, value), emission.inputs['Color'])
    output = n.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def make_depth_material():
    """Flat distance from the camera (metres / 128), raw, for the distance bands of the mush measure. Used as a material override like the class pass."""
    material = bpy.data.materials.get(DEPTH_NAME)
    if material is not None:
        return material
    material = bpy.data.materials.new(DEPTH_NAME)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    n = nodes.Net(tree)
    camera = n.new('ShaderNodeCameraData')
    value = n.math('DIVIDE', camera.outputs['View Distance'], DEPTH_RANGE_M)
    emission = n.new('ShaderNodeEmission')
    tree.links.new(n.comb_rgb(value, value, value), emission.inputs['Color'])
    output = n.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def role_table(settings):
    """{role: id} exactly as seed.py numbers them (the place in the set's role list, from 1)."""
    return {role: index + 1 for index, role in enumerate(settings.roles)}


def classes_for(settings, groups):
    """Surface classes for the measures: {class name: [role ids]} from settings.test_set.classes if present, else one class per role family (the part before the dot)."""
    table = role_table(settings)
    given = (settings.get('test_set') or {}).get('classes')
    if given:
        return {name: [table[r] for role in roles for r in settings.expand_roles([role])] for name, roles in given.items()}
    families = {}
    for role, rid in table.items():
        families.setdefault(role.split('.')[0], []).append(rid)
    return families
