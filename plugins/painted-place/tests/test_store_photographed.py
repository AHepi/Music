"""
What this file does: checks the photographed materials of decision 80 (brief/store/materials/Photographed.md):
  - every material Photographed.md names comes in by name, the new ones with all four of their pictures (colour,
    roughness, height, normal) found on the shelf and used;
  - two pieces with different 'pp_piece' numbers draw differently, and a material with no 'pp_piece' on the mesh draws
    exactly as it did before (pixel for pixel the same as the material with its Pieces nodes taken out);
  - copies instanced on points that carry 'pp_piece' differ from each other;
  - a turned piece's normal picture is turned with it (its relief stays lit from the right side);
  - each atlas file's units lie inside the picture, have brick or block proportions, stand higher than the joints round
    them in the height picture, and are enough (40 or more in a brick set);
  - each atlas material reads the UV map 'pp_atlas' for all four pictures.
    python3 tests/test_store_photographed.py
"""
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import BRIEF, STORE, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
import store  # noqa: E402

MATERIALS = os.path.join(STORE, 'materials')
ATLAS = os.path.join(MATERIALS, 'atlas')
SHELF = os.path.join(BRIEF, 'surfaces')
NEW = ['SURFACE • dark_rock_02', 'SURFACE • worn_rock_natural_01', 'SURFACE • rough_plasterbrick_05',
       'SURFACE • sandstone_blocks_05', 'SURFACE • brick_wall_10',
       'BRICK • brick_wall_02', 'BRICK • brick_wall_10', 'ASHLAR • sandstone_blocks_05']
WORK = tempfile.mkdtemp(prefix='pp_photographed_')


def named_in_photographed():
    text = open(os.path.join(MATERIALS, 'Photographed.md')).read()
    table = text.split('## Which material for which job')[1].split('\n## ')[0]
    return sorted(set(re.findall(r'`((?:SURFACE|BRICK|ASHLAR) • [^`]+)`', table)))


def check_names_and_pictures():
    available = store.names('materials')
    named = named_in_photographed()
    check(len(named) >= 6, 'Photographed.md names only %d materials' % len(named))
    for name in sorted(set(named) | set(NEW)):
        check(name in available, '%s (named in Photographed.md) is not in the store' % name)
        material = store.material(name)
        check(material is not None and material.name == name, '%s did not come in by name' % name)
    for name in NEW:
        material = bpy.data.materials[name]
        used = {}
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image is not None and node.outputs['Color'].is_linked:
                used[node.image.name] = node.image
        roles = {role for role in ('_diff_', '_rough_', '_disp_', '_nor_gl_') if any(role in n for n in used)}
        check(len(roles) == 4, '%s uses only %s of its four pictures' % (name, sorted(roles)))
        for image in used.values():
            check(os.path.exists(bpy.path.abspath(image.filepath)), '%s: picture not found %s' % (name, image.filepath))
        check(material.get('store_what') and material.get('store_size_m'), '%s does not say what it is or its size' % name)
        check('Weather' in material.node_tree.nodes, '%s has no Weather dials' % name)
        check('Pieces' in material.node_tree.nodes, '%s has no Pieces node (pp_piece)' % name)
    print('PASS photographed materials: %d named in Photographed.md come in by name; the %d new ones use all four pictures'
          % (len(named), len(NEW)))


# ------------------------------------------------------------------------------------------------- drawing small

def small_scene():
    scene = fresh_scene()
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.cycles.seed = 1
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('test world')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.05, 0.05, 1)
    scene.world = world
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (0.25, 0.1, 0.0)
    scene.collection.objects.link(sun)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 1.6
    camera.location = (0.0, 0.0, 3.0)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = 160, 80
    scene.render.resolution_percentage = 100
    return scene


def draw(scene, name):
    path = os.path.join(WORK, name + '.png')
    scene.render.filepath = path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path)
    pixels = numpy.array(image.pixels[:], dtype=numpy.float64).reshape(image.size[1], image.size[0], 4)[:, :, :3]
    bpy.data.images.remove(image)
    return pixels


def slab(name, x, piece=None, size=0.6):
    """A flat 0.6 m square slab whose own coordinates are the same wherever it stands; 'pp_piece' on its faces."""
    mesh = bpy.data.meshes.new(name)
    h = size / 2
    verts = [(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0), (-h, -h, 0.05), (h, -h, 0.05), (h, h, 0.05), (-h, h, 0.05)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(verts, [], faces)
    if piece is not None:
        attribute = mesh.attributes.new('pp_piece', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', [piece] * len(faces))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (x, 0.0, 0.0)
    obj['pp_ground'] = 0.0
    return obj


def without_pieces(material):
    """A copy of a SURFACE material with its Pieces nodes taken out: the material as it was before decision 80."""
    copy = material.copy()
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    projected = nodes['Picture size'].outputs['Vector']
    weather = nodes['Weather']
    for node in list(nodes):
        if node.type == 'TEX_IMAGE':
            links.new(projected, node.inputs['Vector'])
            if any(l.to_node.type == 'VECT_MATH' for l in node.outputs['Color'].links):
                links.new(node.outputs['Color'], weather.inputs['Color'])
    if 'Normal picture' in nodes:
        turned = nodes['Normal picture']
        for socket in ('Axis', 'Angle'):
            for link in list(turned.inputs[socket].links):
                links.remove(link)
        turned.inputs['Angle'].default_value = 0.0
    for node in list(nodes):
        if node.name == 'Pieces' or node.type == 'VECTOR_ROTATE' or (node.type == 'VECT_MATH' and not node.outputs[0].is_linked):
            nodes.remove(node)
    for node in list(nodes):
        if node.type == 'VECT_MATH' and not node.outputs[0].is_linked:
            nodes.remove(node)
    return copy


def halves(pixels):
    width = pixels.shape[1]
    return pixels[16:64, 8:width // 2 - 8], pixels[16:64, width // 2 + 8:width - 8]


def check_pieces():
    for name in ('SURFACE • dark_rock_02', 'SURFACE • worn_rock_natural_01'):
        scene = small_scene()
        material = store.material(name)
        left, right = slab('left', -0.4, 0.21), slab('right', 0.4, 0.67)
        for obj in (left, right):
            obj.data.materials.append(material)
        a, b = halves(draw(scene, 'different'))
        different = numpy.abs(a - b).mean()
        for obj, value in ((left, 0.43), (right, 0.43)):
            obj.data.attributes['pp_piece'].data.foreach_set('value', [value] * 6)
        a, b = halves(draw(scene, 'same'))
        same = numpy.abs(a - b).mean()
        check(different > 3.0 * same and different > 0.004,
              '%s: two pieces with different pp_piece differ by %.4f, two with the same by %.4f' % (name, different, same))
        # no pp_piece at all: exactly as the material without its Pieces nodes
        for obj in (left, right):
            obj.data.attributes.remove(obj.data.attributes['pp_piece'])
        with_nodes = draw(scene, 'absent')
        before = without_pieces(material)
        check(not any(n.name == 'Pieces' for n in before.node_tree.nodes), 'the copy still has its Pieces node')
        for obj in (left, right):
            obj.data.materials[0] = before
        as_before = draw(scene, 'before')
        changed = numpy.abs(with_nodes - as_before).max()
        check(changed == 0.0, '%s: with no pp_piece the picture changed (largest change %.6f)' % (name, changed))
        print('PASS %s: pieces with different pp_piece differ (%.4f against %.4f for equal ones); without pp_piece it draws '
              'pixel for pixel as before' % (name, different, same))


def check_instances():
    scene = small_scene()
    material = store.material('SURFACE • dark_rock_02')
    mesh = bpy.data.meshes.new('cube')
    s = 0.2
    verts = [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0), (-s, -s, 0.1), (s, -s, 0.1), (s, s, 0.1), (-s, s, 0.1)]
    mesh.from_pydata(verts, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mesh.materials.append(material)
    cube = bpy.data.objects.new('cube', mesh)
    scene.collection.objects.link(cube)
    cube.hide_render = True
    cube.location = (0.0, 0.0, -5.0)
    points = bpy.data.meshes.new('points')
    points.from_pydata([(-0.5, 0.0, 0.0), (0.0, 0.0, 0.0), (0.5, 0.0, 0.0)], [], [])
    numbers = points.attributes.new('pp_piece', 'FLOAT', 'POINT')
    carrier = bpy.data.objects.new('carrier', points)
    scene.collection.objects.link(carrier)
    tree = bpy.data.node_groups.new('copies', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g_in, g_out = tree.nodes.new('NodeGroupInput'), tree.nodes.new('NodeGroupOutput')
    info = tree.nodes.new('GeometryNodeObjectInfo')
    info.inputs['Object'].default_value = cube
    info.transform_space = 'ORIGINAL'
    on_points = tree.nodes.new('GeometryNodeInstanceOnPoints')
    tree.links.new(g_in.outputs[0], on_points.inputs['Points'])
    tree.links.new(info.outputs['Geometry'], on_points.inputs['Instance'])
    tree.links.new(on_points.outputs['Instances'], g_out.inputs[0])
    carrier.modifiers.new('copies', 'NODES').node_group = tree

    def crops(pixels):
        # the three copies' tops: 0.4 m wide, at x = -0.5, 0, 0.5 (100 pixels per metre across 1.6 m)
        return [pixels[28:52, c - 12:c + 12] for c in (30, 80, 130)]

    def alike(a, b):
        # how alike two crops' patterns are: 1 the same pattern, about 0 unrelated ones
        a, b = a.mean(axis=2) - a.mean(), b.mean(axis=2) - b.mean()
        return float((a * b).sum() / max(numpy.sqrt((a * a).sum() * (b * b).sum()), 1e-12))

    scene.cycles.samples = 32
    numbers.data.foreach_set('value', [0.5, 0.5, 0.5])
    equal = crops(draw(scene, 'copies equal'))
    numbers.data.foreach_set('value', [0.12, 0.47, 0.83])
    carrier.data.update()
    varied = crops(draw(scene, 'copies varied'))
    same = min(alike(equal[0], equal[1]), alike(equal[1], equal[2]))
    differ = max(alike(varied[0], varied[1]), alike(varied[1], varied[2]), alike(varied[0], varied[2]))
    check(same > 0.6, 'three copies with the same pp_piece should look alike, but are only %.2f alike' % same)
    check(differ < 0.5 * same, 'instanced copies with different pp_piece are still %.2f alike (equal ones %.2f)' % (differ, same))
    print('PASS instanced copies: three copies of one cube on points with pp_piece each show their own part (at most %.2f '
          'alike; with equal numbers %.2f alike)' % (differ, same))


def check_relief():
    """A turned piece's normal picture is turned back with it: under a low light from one side, the shading the normal
    picture alone gives agrees with the shading the height picture alone gives (the bump, worked out on the turned
    picture itself). Were the normal picture not turned back, the two would disagree on most turned pieces."""
    from scipy import ndimage
    scene = small_scene()
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    sun = bpy.data.objects['sun']
    sun.rotation_euler = (1.22, 0.0, 1.571)                       # 20 degrees above the ground, from +X
    scene.camera.data.ortho_scale = 0.5
    scene.render.resolution_x = scene.render.resolution_y = 128
    scene.cycles.samples = 16
    material = store.material('SURFACE • worn_rock_natural_01').copy()
    nodes = material.node_tree.nodes
    nodes['Weather'].inputs['Grime'].default_value = 0.0
    piece = slab('relief', 0.0, 0.0)
    piece.data.materials.append(material)

    def shading(pixels):
        grey = pixels.mean(axis=2)
        return grey / numpy.maximum(ndimage.uniform_filter(grey, 15), 1e-6) - 1.0

    agreements = []
    for number in (0.13, 0.37, 0.61, 0.88):
        piece.data.attributes['pp_piece'].data.foreach_set('value', [number] * 6)
        piece.data.update()
        nodes['Weather'].inputs['Bump'].default_value, nodes['Normal picture'].inputs['Strength'].default_value = 0.0, 1.0
        a = shading(draw(scene, 'relief normal'))
        nodes['Weather'].inputs['Bump'].default_value, nodes['Normal picture'].inputs['Strength'].default_value = 1.5, 0.0
        b = shading(draw(scene, 'relief height'))
        agreements.append(float((a * b).sum() / numpy.sqrt((a * a).sum() * (b * b).sum())))
    check(min(agreements) > 0.5, 'a turned piece\'s normal picture disagrees with its height picture: %s'
          % ', '.join('%.2f' % x for x in agreements))
    print('PASS turned pieces keep their relief lit the right way: normal and height pictures agree %s'
          % ', '.join('%.2f' % x for x in agreements))


def check_atlas_relief():
    """An atlas unit mapped through pp_atlas, straight and turned half round: its normal picture's shading agrees with
    its height picture's shading both ways (the normal picture follows the UV map's own directions)."""
    from scipy import ndimage
    scene = small_scene()
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    bpy.data.objects['sun'].rotation_euler = (1.22, 0.0, 1.571)
    scene.camera.data.ortho_scale = 0.5
    scene.render.resolution_x = scene.render.resolution_y = 128
    scene.cycles.samples = 16
    material = store.material('ASHLAR • sandstone_blocks_05').copy()
    nodes = material.node_tree.nodes
    nodes['Weather'].inputs['Grime'].default_value = 0.0
    atlas = json.load(open(os.path.join(ATLAS, 'sandstone_blocks_05.json')))
    u0, v0, u1, v1 = max(atlas['units'], key=lambda u: (u[2] - u[0]) * (u[3] - u[1]))
    mesh = bpy.data.meshes.new('unit')
    mesh.from_pydata([(-0.24, -0.24, 0), (0.24, -0.24, 0), (0.24, 0.24, 0), (-0.24, 0.24, 0)], [], [(0, 1, 2, 3)])
    layer = mesh.uv_layers.new(name='pp_atlas')
    obj = bpy.data.objects.new('unit', mesh)
    scene.collection.objects.link(obj)
    mesh.materials.append(material)

    def shading(pixels):
        grey = pixels.mean(axis=2)
        return grey / numpy.maximum(ndimage.uniform_filter(grey, 15), 1e-6) - 1.0

    agreements = []
    for corners in ([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], [(u1, v1), (u0, v1), (u0, v0), (u1, v0)]):
        for loop, corner in zip(layer.data, corners):
            loop.uv = corner
        mesh.update()
        relief = next(n for n in nodes if n.type == 'NORMAL_MAP')
        nodes['Weather'].inputs['Bump'].default_value, relief.inputs['Strength'].default_value = 0.0, 1.0
        a = shading(draw(scene, 'atlas normal'))
        nodes['Weather'].inputs['Bump'].default_value, relief.inputs['Strength'].default_value = 1.5, 0.0
        b = shading(draw(scene, 'atlas height'))
        agreements.append(float((a * b).sum() / numpy.sqrt((a * a).sum() * (b * b).sum())))
    check(min(agreements) > 0.5, 'an atlas unit\'s normal picture disagrees with its height picture: %s'
          % ', '.join('%.2f' % x for x in agreements))
    print('PASS an atlas unit keeps its relief lit the right way, straight and turned half round: %s'
          % ', '.join('%.2f' % x for x in agreements))


# ------------------------------------------------------------------------------------------------- atlases

def check_atlases():
    from PIL import Image
    files = sorted(f for f in os.listdir(ATLAS) if f.endswith('.json'))
    check(len(files) >= 3, 'only %d atlas files in %s' % (len(files), ATLAS))
    manifest = json.load(open(os.path.join(SHELF, 'manifest.json')))
    bricks = 0
    for file_name in files:
        atlas = json.load(open(os.path.join(ATLAS, file_name)))
        for key in ('material', 'set', 'picture_size_m', 'units'):
            check(key in atlas, '%s has no %r' % (file_name, key))
        name, set_id = atlas['material'], atlas['set']
        check(name.startswith(('BRICK • ', 'ASHLAR • ')), '%s: material %r is not BRICK or ASHLAR' % (file_name, name))
        check(set_id in manifest and atlas['picture_size_m'] == manifest[set_id]['size_m'], '%s: set or size wrong' % file_name)
        units = numpy.array(atlas['units'], dtype=float)
        brick = name.startswith('BRICK')
        check(len(units) >= (40 if brick else 12), '%s: only %d units' % (file_name, len(units)))
        if 'kinds' in atlas:
            check(len(atlas['kinds']) == len(units) and set(atlas['kinds']) <= {'stretcher', 'header'}, '%s: kinds wrong' % file_name)
        check(units.min() >= 0.0 and units.max() <= 1.0, '%s: a unit lies outside the picture' % file_name)
        check(bool((units[:, 2] > units[:, 0]).all() and (units[:, 3] > units[:, 1]).all()), '%s: a unit is turned inside out' % file_name)
        width = (units[:, 2] - units[:, 0]) * atlas['picture_size_m'][0]
        height = (units[:, 3] - units[:, 1]) * atlas['picture_size_m'][1]
        ratio = width / height
        if brick:
            check(bool(((height > 0.035) & (height < 0.1)).all()), '%s: brick faces %.3f to %.3f m high' % (file_name, height.min(), height.max()))
            check(bool(((width > 0.07) & (width < 0.35)).all()), '%s: brick faces %.3f to %.3f m long' % (file_name, width.min(), width.max()))
            check(bool(((ratio > 1.1) & (ratio < 6.0)).all()), '%s: brick faces %.1f to %.1f times as long as high' % (file_name, ratio.min(), ratio.max()))
            bricks += 1
        else:
            check(bool(((height > 0.12) & (height < 0.7)).all()), '%s: block faces %.3f to %.3f m high' % (file_name, height.min(), height.max()))
            check(bool(((ratio > 0.4) & (ratio < 5.0)).all()), '%s: block faces %.1f to %.1f times as long as high' % (file_name, ratio.min(), ratio.max()))
        # each unit stands higher than the joints round it in the height picture (it is not on mortar)
        entry = manifest[set_id]
        picture = Image.open(os.path.join(SHELF, set_id, entry['maps']['disp'])).convert('F').resize((1024, 1024))
        heights = numpy.asarray(picture, dtype=numpy.float64) / 255.0
        low = 0
        for u0, v0, u1, v1 in units:
            c0, c1 = int(round(u0 * 1024)), int(round(u1 * 1024))
            r0, r1 = int(round((1 - v1) * 1024)), int(round((1 - v0) * 1024))
            inside = heights[r0:r1, c0:c1].mean()
            big = heights[max(r0 - 7, 0):r1 + 7, max(c0 - 7, 0):c1 + 7]
            middle = heights[max(r0 - 2, 0):r1 + 2, max(c0 - 2, 0):c1 + 2]
            ring = (big.sum() - middle.sum()) / max(big.size - middle.size, 1)
            low += inside <= ring - 0.002
        check(low == 0, '%s: %d units lie no higher than the joints round them' % (file_name, low))
        # the material reads pp_atlas for all four pictures
        material = store.material(name)
        nodes = material.node_tree.nodes
        uv_maps = [n for n in nodes if n.type == 'UVMAP']
        check(uv_maps and all(n.uv_map == 'pp_atlas' for n in uv_maps), '%s does not read the UV map pp_atlas' % name)
        pictures = [n for n in nodes if n.type == 'TEX_IMAGE']
        check(len(pictures) == 4 and all(p.inputs['Vector'].is_linked and p.inputs['Vector'].links[0].from_node.type == 'UVMAP'
                                         for p in pictures), '%s: its four pictures do not all read pp_atlas' % name)
        normal_maps = [n for n in nodes if n.type == 'NORMAL_MAP']
        check(normal_maps and normal_maps[0].uv_map == 'pp_atlas', '%s: its normal picture is not turned by pp_atlas' % name)
        check(material.get('store_atlas') == 'atlas/' + file_name, '%s does not name its atlas file' % name)
        print('PASS atlas %s: %d units inside the picture, %.2f to %.2f m long and %.2f to %.2f m high, each standing above '
              'its joints; %s reads pp_atlas' % (set_id, len(units), width.min(), width.max(), height.min(), height.max(), name))
    check(bricks >= 2, 'only %d brick atlases' % bricks)


def main():
    fresh_scene()
    check_names_and_pictures()
    check_atlases()
    check_pieces()
    check_instances()
    check_relief()
    check_atlas_relief()
    print('PASS test_store_photographed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as error:
        print('FAIL', error)
        sys.exit(1)
