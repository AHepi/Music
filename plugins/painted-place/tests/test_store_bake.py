"""
What this file does: checks the bake_to_pbr tool (decision 87: bake a detailed thing onto a simple low shape as PBR
pictures):
  - its TOOL description is complete;
  - the store's azalea, baked small: the tool gives back one low shape of 320 faces (32 x 10) with a UV map inside
    the picture, hugging the bush's outline (its box within a few centimetres of the bush's) with its foot on the
    ground; a material 'BAKED • ...' with its four pictures (colour, normal, roughness, height) at the size asked; the
    colour picture holds the flowers' pink and the leaves' dark green, the normal picture has relief in it, the
    projection found the bush almost everywhere; the height as real relief (Subdivision 'SIMPLE' and Displace by the
    height picture) unless relief=False; the faces the bush draws (its live copies counted) recorded;
  - the bush itself is left exactly as it was (its objects, modifiers and materials), and nothing of the bake is left
    behind (no scene, mesh, material or picture of its own work);
  - the pictures are written to the folder given, as PNG, or packed into the file when no folder is given;
  - a lumpy stone baked as a 'ball' gives a closed shape; a shape of yours is used as given; wrong values are refused.
    python3 tests/test_store_bake.py
"""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import store  # noqa: E402
import bake_to_pbr  # noqa: E402


def box(objects):
    low, high = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for v in mesh.vertices:
            p = obj.matrix_world @ v.co
            low = Vector(tuple(map(min, low, p)))
            high = Vector(tuple(map(max, high, p)))
        evaluated.to_mesh_clear()
    return low, high


def pixels(image):
    data = numpy.empty(image.size[0] * image.size[1] * image.channels, dtype=numpy.float32)
    image.pixels.foreach_get(data)
    return data.reshape(image.size[1], image.size[0], image.channels)


def test_description():
    for key in ('name', 'what', 'call', 'options', 'materials', 'source', 'trap'):
        check(bake_to_pbr.TOOL.get(key), 'bake_to_pbr TOOL has no %s' % key)
    check(bake_to_pbr.TOOL['name'] == 'bake_to_pbr', 'bake_to_pbr TOOL is named %r' % bake_to_pbr.TOOL['name'])
    for option in ('objects', 'shape', 'form', 'size', 'reach', 'depth', 'relief', 'relief_detail', 'lit_through', 'bits', 'folder'):
        check(any(option in key for key in bake_to_pbr.TOOL['options']), 'bake_to_pbr TOOL does not describe %s' % option)
    print('PASS bake_to_pbr: its TOOL description is complete')


def test_azalea():
    fresh_scene()
    bush = store.add_part('azalea')
    bpy.context.view_layer.update()
    parts = [o for o in bush.children_recursive if o.type == 'MESH']
    before = {o.name: ([m.name for m in o.modifiers], [m.name for m in o.data.materials]) for o in parts}
    leaves_material = bpy.data.materials['PART • azalea: leaves']
    scenes, meshes, materials = len(bpy.data.scenes), set(bpy.data.meshes.keys()), set(bpy.data.materials.keys())
    images = set(bpy.data.images.keys())
    folder = tempfile.mkdtemp(prefix='test_bake_')
    shape = bake_to_pbr.bake(bush, size=256, folder=folder, lit_through=0.3)
    check(shape.type == 'MESH' and shape.name == bush.name + ' • baked', 'the baked shape is %s %r' % (shape.type, shape.name))
    check(shape.name in bpy.context.scene.collection.objects, 'the baked shape is not in the scene')
    check(len(shape.data.polygons) == 320, 'the baked shape has %d faces, not 320' % len(shape.data.polygons))
    uv = shape.data.uv_layers.get('UVMap')
    check(uv is not None, 'the baked shape has no UV map')
    spots = numpy.empty(len(uv.data) * 2, dtype=numpy.float32)
    uv.data.foreach_get('uv', spots)
    check(spots.min() >= 0.0 and spots.max() <= 1.0, 'the UV map leaves the picture (%.3f to %.3f)' % (spots.min(), spots.max()))
    # it hugs the bush
    bush_low, bush_high = box(parts)
    flat = [m for m in shape.modifiers]
    for m in flat:
        m.show_viewport = False
    shape_low, shape_high = box([shape])
    for m in flat:
        m.show_viewport = True
    check(abs(shape_low.z - bush_low.z) < 0.002, 'the baked shape\'s foot is at %.3f, the bush\'s at %.3f' % (shape_low.z, bush_low.z))
    for axis in range(3):
        check(abs(shape_high[axis] - bush_high[axis]) < 0.06 and (axis == 2 or abs(shape_low[axis] - bush_low[axis]) < 0.06),
              'the baked shape does not hug the bush along %s: %s..%s against %s..%s' % ('xyz'[axis], tuple(shape_low), tuple(shape_high),
                                                                                       tuple(bush_low), tuple(bush_high)))
    # its material and pictures
    material = shape.data.materials[0]
    check(material.name == 'BAKED • ' + shape.name, 'the baked material is %r' % material.name)
    nodes = material.node_tree.nodes
    for label in ('Colour picture', 'Normal picture', 'Roughness picture', 'Height picture'):
        check(label in nodes and nodes[label].image is not None, 'the baked material has no %s' % label)
        check(tuple(nodes[label].image.size) == (256, 256), '%s is %s, not 256 x 256' % (label, tuple(nodes[label].image.size)))
    for key in ('colour', 'normal', 'roughness', 'height'):
        path = os.path.join(folder, '%s - baked - %s.png' % (bush.name, key))
        check(os.path.exists(path) and os.path.getsize(path) > 1000, 'the %s picture was not written to the folder' % key)
    colour = pixels(nodes['Colour picture'].image)
    found = colour[..., 3] > 0.5
    pink = found & (colour[..., 0] > 2.0 * colour[..., 1]) & (colour[..., 0] > 0.3)
    green = found & (colour[..., 1] > colour[..., 0]) & (colour[..., 1] < 0.45)
    check(0.1 < pink.sum() / found.sum() < 0.75, 'the colour picture is %.0f%% flower pink' % (100 * pink.sum() / found.sum()))
    check(green.sum() / found.sum() > 0.1, 'the colour picture is only %.0f%% leaf green' % (100 * green.sum() / found.sum()))
    normal = pixels(nodes['Normal picture'].image)
    check(normal[found][:, 0].std() > 0.05 and normal[found][:, 1].std() > 0.05, 'the normal picture is flat')
    check(shape['baked_found'] > 0.9, 'the projection found the bush on only %.0f%% of the shape' % (100 * shape['baked_found']))
    check(-0.25 <= shape['baked_height_low'] < 0.0 < shape['baked_height_high'] <= 0.06,
          'the height runs %.3f to %.3f m' % (shape['baked_height_low'], shape['baked_height_high']))
    check(shape['baked_from_faces'] > 100000, 'the bush drew only %d faces' % shape['baked_from_faces'])
    check('Lit through mix' in nodes and abs(nodes['Lit through mix'].inputs['Fac'].default_value - 0.3) < 1e-6, 'lit_through was not taken')
    # the relief
    kinds = [(m.type, getattr(m, 'subdivision_type', None)) for m in shape.modifiers]
    check(kinds == [('SUBSURF', 'SIMPLE'), ('DISPLACE', None)], 'the relief modifiers are %s' % kinds)
    lift = shape.modifiers[1]
    check(lift.texture is not None and lift.texture.image == nodes['Height picture'].image and lift.texture_coords == 'UV',
          'the Displace does not use the height picture by the UV map')
    check(abs(lift.strength - (shape['baked_height_high'] - shape['baked_height_low'])) < 1e-5, 'the Displace strength is not the height range')
    # the bush as it was; nothing of the bake left behind
    after = {o.name: ([m.name for m in o.modifiers], [m.name for m in o.data.materials]) for o in parts}
    check(before == after, 'the bush was changed: %s against %s' % (after, before))
    check(any(n.type == 'ATTRIBUTE' and n.attribute_type == 'INSTANCER' for n in leaves_material.node_tree.nodes),
          "the leaves' own material was changed")
    check(all(not o.hide_render for o in parts), 'the bush was hidden')
    check(len(bpy.data.scenes) == scenes, 'the bake left a scene behind')
    left = [m for m in set(bpy.data.meshes.keys()) - meshes if m != shape.data.name]
    check(not left, 'the bake left meshes behind: %s' % left)
    left = [m for m in set(bpy.data.materials.keys()) - materials if m != material.name]
    check(not left, 'the bake left materials behind: %s' % left)
    left = [i for i in set(bpy.data.images.keys()) - images if not i.startswith('BAKED • ')]
    check(not left, 'the bake left pictures behind: %s' % left)
    print('PASS bake_to_pbr on the azalea (256 pictures): one shape of 320 faces hugging the bush (from %d faces), foot on the ground, '
          'UV map inside the picture, four pictures written (%.0f%% flower pink, the rest leaf green), relief by the height '
          '(%.3f to %.3f m), found %.0f%%; the bush unchanged and nothing left behind (%.1f s)'
          % (shape['baked_from_faces'], 100 * pink.sum() / found.sum(), shape['baked_height_low'], shape['baked_height_high'],
             100 * shape['baked_found'], shape['baked_seconds']))


def stone(name, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.3, location=(0.0, 0.0, 0.25))
    obj = bpy.context.object
    obj.name = name
    rng = numpy.random.default_rng(seed)
    for v in obj.data.vertices:
        v.co *= 1.0 + 0.12 * math.sin(7 * v.co.x + rng.random()) * math.cos(5 * v.co.y)
    material = bpy.data.materials.new('test stone')
    material.use_nodes = True
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.2, 0.18, 0.15, 1.0)
    obj.data.materials.append(material)
    return obj


def test_ball_and_given():
    fresh_scene()
    rock = stone('rock', 2)
    ball = bake_to_pbr.bake(rock, form='ball', size=128, segments=16, rings=8, relief=False)
    check(len(ball.data.polygons) == 16 * 7 + 2 * 16, 'the ball has %d faces' % len(ball.data.polygons))
    edges = {}
    for face in ball.data.polygons:
        for key in face.edge_keys:
            edges[key] = edges.get(key, 0) + 1
    check(all(n == 2 for n in edges.values()), 'the ball is not closed')
    check(not ball.modifiers, 'relief=False still added modifiers')
    image = ball.data.materials[0].node_tree.nodes['Colour picture'].image
    check(image.packed_file is not None, 'without a folder the pictures are not packed into the file')
    # a shape of your own, with a UV map, is used as it is
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.42, location=(0.0, 0.0, 0.25))
    mine = bpy.context.object
    mine.name = 'my shape'
    faces = len(mine.data.polygons)
    used = bake_to_pbr.bake(rock, shape=mine, size=128, relief=False)
    check(used is mine and len(mine.data.polygons) == faces, 'the given shape was not used as it was')
    check(mine.data.materials[0].name.startswith('BAKED • '), 'the given shape did not get the baked material')
    # wrong values
    for options, word in (({'form': 'cube'}, 'form'), ({'size': 10}, 'size'), ({'segments': 3}, 'segments'), ({'bits': 12}, 'bits')):
        try:
            bake_to_pbr.bake(rock, **options)
        except ValueError as problem:
            check(word in str(problem), 'the refusal of %s does not say why: %s' % (options, problem))
        else:
            check(False, 'bake_to_pbr took %s' % options)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3, 0, 0.5))
    plain = bpy.context.object
    plain.data.uv_layers.remove(plain.data.uv_layers[0])
    try:
        bake_to_pbr.bake(rock, shape=plain, size=64)
    except ValueError as problem:
        check('UV map' in str(problem), 'a shape without a UV map is refused without saying so: %s' % problem)
    else:
        check(False, 'a shape without a UV map was taken')
    print('PASS bake_to_pbr: a stone baked as a ball is closed (%d faces), pictures packed without a folder; a shape of '
          'yours is used as it is; wrong form, size, segments, bits and a shape without a UV map refused' % len(ball.data.polygons))


def main():
    check('bake_to_pbr' in store.names('tools'), 'the store has no tool bake_to_pbr')
    test_description()
    test_azalea()
    test_ball_and_given()
    print('PASS test_store_bake')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as problem:
        print('FAIL', problem)
        sys.exit(1)
