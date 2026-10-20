# What this does: small helpers for the real-geometry experiments in this folder (scatter stones, slate rows, rivets): build a Geometry Nodes
# group from Python in a few lines, make an overhead 1 x 1 scene, and "photograph" the geometry from straight above once as colour and once as height.
# It reuses the project's lib/bake_harness.py scene and render helpers and changes nothing in lib/.
# Use (inside Blender):  import geo_helpers as gh
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.abspath(os.path.join(HERE, '..', '..', 'lib'))
sys.path.insert(0, LIB)
sys.path.insert(0, HERE)
import bake_harness as bh  # noqa: E402
import builder as bd  # noqa: E402


class GeoBuilder:
    """Add Geometry Nodes nodes and get their outputs back (same idea as builder.Builder, for geometry trees)."""

    def __init__(self, name, inputs=None):
        self.tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        self.tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        self.tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        self.input = self.tree.nodes.new('NodeGroupInput')
        self.output = self.tree.nodes.new('NodeGroupOutput')
        self.count = 0

    def node(self, kind, **settings):
        node = self.tree.nodes.new(kind)
        self.count += 1
        node.location = ((self.count % 12) * 230, -(self.count // 12) * 280)
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    def put(self, node, key, value):
        if value is None:
            return
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, node.inputs[key])
        else:
            node.inputs[key].default_value = value

    def make(self, kind, outputs, settings=None, **inputs):
        node = self.node(kind, **(settings or {}))
        for key, value in inputs.items():
            self.put(node, key.replace('__', ' '), value)
        return node.outputs[outputs] if isinstance(outputs, (str, int)) else node

    def math(self, operation, a=None, b=None, c=None):
        node = self.node('ShaderNodeMath', operation=operation)
        for index, value in enumerate((a, b, c)):
            self.put(node, index, value)
        return node.outputs[0]

    def vec_math(self, operation, a=None, b=None, scale=None):
        node = self.node('ShaderNodeVectorMath', operation=operation)
        self.put(node, 0, a)
        self.put(node, 1, b)
        if scale is not None:
            self.put(node, 'Scale', scale)
        return node.outputs[0]

    def combine(self, x=0.0, y=0.0, z=0.0):
        node = self.node('ShaderNodeCombineXYZ')
        self.put(node, 'X', x)
        self.put(node, 'Y', y)
        self.put(node, 'Z', z)
        return node.outputs[0]

    def random_float(self, low, high, seed=0, id_value=None):
        node = self.node('FunctionNodeRandomValue', data_type='FLOAT')
        self.put(node, 'Min', low)
        self.put(node, 'Max', high)
        self.put(node, 'Seed', seed)
        if id_value is not None:
            self.put(node, 'ID', id_value)
        return node.outputs['Value']

    def random_vector(self, low, high, seed=0, id_value=None):
        node = self.node('FunctionNodeRandomValue', data_type='FLOAT_VECTOR')
        self.put(node, 'Min', low)
        self.put(node, 'Max', high)
        self.put(node, 'Seed', seed)
        if id_value is not None:
            self.put(node, 'ID', id_value)
        return node.outputs['Value']

    def finish(self, geometry):
        self.tree.links.new(geometry, self.output.inputs['Geometry'])
        return self.tree


def add_object_with_tree(name, tree, base_mesh=None):
    if base_mesh is None:
        base_mesh = bpy.data.meshes.new(name + ' base')
        base_mesh.from_pydata([(0.5, 0.5, 0.0)], [], [])
    obj = bpy.data.objects.new(name, base_mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new('recipe', 'NODES')
    modifier.node_group = tree
    return obj, modifier


def new_overhead_scene(size):
    """The project's overhead scene (camera over x 0..1, y 0..1, straight down) without its flat square."""
    scene, tile = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile)
    return scene


def emission_material(name, colour_socket_builder):
    """A material that shows what colour_socket_builder(tree, nodes) returns as plain light. Returns the material."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emit = tree.nodes.new('ShaderNodeEmission')
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    socket = colour_socket_builder(tree)
    tree.links.new(socket, emit.inputs['Color'])
    return material


def height_material(z_low, z_high):
    """Emission = (z - z_low) / (z_high - z_low) from the world position, so a render is a height picture."""
    def build(tree):
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        split = tree.nodes.new('ShaderNodeSeparateXYZ')
        tree.links.new(geometry.outputs['Position'], split.inputs[0])
        mapper = tree.nodes.new('ShaderNodeMapRange')
        mapper.inputs[1].default_value = z_low
        mapper.inputs[2].default_value = z_high
        tree.links.new(split.outputs['Z'], mapper.inputs[0])
        grey = tree.nodes.new('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            tree.links.new(mapper.outputs[0], grey.inputs[socket])
        return grey.outputs[0]
    return emission_material('height z %.3f..%.3f' % (z_low, z_high), build)


def object_random_colour_material(stops, name='random colour'):
    """Emission colour = a Color Ramp (stops: list of (position, '#hex')) read with Object Info > Random (one random number per object or per instance)."""
    def build(tree):
        info = tree.nodes.new('ShaderNodeObjectInfo')
        ramp = tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        while len(ramp.color_ramp.elements) > 1:
            ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
        ramp.color_ramp.elements[0].position = stops[0][0]
        ramp.color_ramp.elements[0].color = bd.as_colour(stops[0][1])
        for position, colour in stops[1:]:
            element = ramp.color_ramp.elements.new(position)
            element.color = bd.as_colour(colour)
        tree.links.new(info.outputs['Random'], ramp.inputs['Fac'])
        return ramp.outputs['Color']
    return emission_material(name, build)


def random_grey_material():
    """Emission grey = Object Info > Random (to count how many different values come out)."""
    def build(tree):
        info = tree.nodes.new('ShaderNodeObjectInfo')
        grey = tree.nodes.new('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            tree.links.new(info.outputs['Random'], grey.inputs[socket])
        return grey.outputs[0]
    return emission_material('random grey', build)


def render_picture(scene, path, sixteen_bit=False, linear=False):
    bh.render_to(scene, path, linear, sixteen_bit)


def set_material(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def constant_colour_material(name, rgba):
    """Emission of one fixed colour (linear rgba)."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emit = tree.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = rgba
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return material


def use_material(set_material_output, material):
    """Change the material of a Set Material node (pass its output socket): instanced meshes carry NO material of their own in Blender 5.2 (tested:
    without a Set Material node the instances render black whatever the object's material slot holds)."""
    set_material_output.node.inputs['Material'].default_value = material


instancer_random_colour_material = object_random_colour_material     # Object Info > Random is unique per instance (tested: 196 values for 196 cubes)
