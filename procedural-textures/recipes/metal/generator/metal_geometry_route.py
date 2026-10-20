# What this does (plain words): the REAL-GEOMETRY route for the metal plate. Instead of painting flat shapes, it builds real raised parts in Blender from the same
# description and photographs them from straight above:
#   * every strap and brace is a real bar: one "Curve Line" along its centre, swept with a rectangle profile by "Curve to Mesh" (a Geometry Nodes group,
#     one copy of the group per bar, each with its own start, end, width and height typed into the modifier);
#   * every rivet is a real 8-sided cone: the rivet positions are a cloud of points, and "Instance on Points" puts one cone on each point;
#   * the plate is a flat square. Everything is also repeated one tile over, so the tile wraps.
# Pictures written: height_geometry.png (16-bit: the true height of the surface) and normal_geometry.png (the true surface normal, OpenGL convention).
# It does NOT make the colour (the painted route does that); it is used to compare "height from colour" with "height from real geometry", and to mix them.
# Use (command line):  blender -b --disable-autoexec -t 2 --python metal_geometry_route.py -- DESCRIPTION.json OUT_FOLDER [--size 1254] [--strap-height 0.012] [--rivet-height 0.02]
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))
import bake_harness as bh  # noqa: E402
import gn_tools as gt  # noqa: E402


def make_bar_group():
    """Geometry Nodes group 'Metal bar': inputs Start (vector), End (vector), Width (across, in tile units), Height. One Curve Line, swept with a rectangular profile."""
    tree, g = gt.make_geometry_group('Metal bar', [
        ('Start', 'NodeSocketVector', (0, 0, 0)), ('End', 'NodeSocketVector', (1, 0, 0)), ('Width', 'NodeSocketFloat', 0.1), ('Height', 'NodeSocketFloat', 0.012)])
    g.node('GeometryNodeCurvePrimitiveLine', 'line', {'Start': ('in', 'Start'), 'End': ('in', 'End')})
    # the bar's cross-section: a plain rectangle (Width across, Height up), so the walls are steep like a real strap
    g.node('GeometryNodeCurvePrimitiveQuadrilateral', 'profile', {'Width': ('in', 'Width'), 'Height': ('in', 'Height')}, mode='RECTANGLE')
    g.node('GeometryNodeCurveToMesh', 'sweep', {'Curve': ('line', 'Curve'), 'Profile Curve': ('profile', 'Curve'), 'Fill Caps': True})
    # lift so that the bar stands on the plate (its profile is centred on the curve): move up by half the height
    g.node('ShaderNodeCombineXYZ', 'lift xyz', {'X': 0.0, 'Y': 0.0})
    g.node('ShaderNodeMath', 'half height', {0: ('in', 'Height'), 1: 0.5}, operation='MULTIPLY')
    g.link('half height', 0, 'lift xyz', 'Z')
    g.node('GeometryNodeTransform', 'lift', {'Geometry': ('sweep', 'Mesh'), 'Translation': ('lift xyz', 'Vector')})
    gt.finish_with_material_slot(g, 'lift')
    return tree


def make_rivet_group():
    """Geometry Nodes group 'Metal rivets': every point of the object gets a cone (8 sides) on it. Inputs: Radius, Height."""
    tree, g = gt.make_geometry_group('Metal rivets', [('Geometry', 'NodeSocketGeometry', None), ('Radius', 'NodeSocketFloat', 0.016), ('Height', 'NodeSocketFloat', 0.02)])
    g.node('GeometryNodeMeshCone', 'cone', {'Vertices': 8, 'Radius Top': 0.0, 'Radius Bottom': ('in', 'Radius'), 'Depth': ('in', 'Height')}, fill_type='NGON')
    g.node('ShaderNodeMath', 'half height', {0: ('in', 'Height'), 1: 0.5}, operation='MULTIPLY')
    g.node('ShaderNodeCombineXYZ', 'lift xyz', {'X': 0.0, 'Y': 0.0})
    g.link('half height', 0, 'lift xyz', 'Z')
    g.node('GeometryNodeTransform', 'lift cone', {'Geometry': ('cone', 'Mesh'), 'Translation': ('lift xyz', 'Vector')})
    g.node('GeometryNodeInstanceOnPoints', 'instance', {'Points': ('in', 'Geometry'), 'Instance': ('lift cone', 'Geometry')})
    g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('instance', 'Instances')})
    gt.finish_with_material_slot(g, 'realize')
    return tree


def build_scene(description, size, strap_height, rivet_height, strap_top_z=None):
    tile = float(description.get('tile', 1254.0))
    scene = gt.new_scene(size)
    scene = bpy.context.scene
    objects = []
    # the plate
    mesh = bpy.data.meshes.new('plate')
    mesh.from_pydata([(-0.1, -0.1, 0), (1.1, -0.1, 0), (1.1, 1.1, 0), (-0.1, 1.1, 0)], [], [(0, 1, 2, 3)])
    plate = bpy.data.objects.new('plate', mesh)
    scene.collection.objects.link(plate)
    objects.append(plate)
    bar_tree = make_bar_group()
    rivet_tree = make_rivet_group()
    bars = [b for b in description['bands'] if b.get('name', '') not in ('S1', 'S2', 'S3', 'S')]
    n_bars = 0
    for band in bars:
        a = math.radians(band['angle'])
        d = np.array([math.cos(a), math.sin(a)])
        centre = np.array(band['centre'], float) + 0.5
        half_length = band['length'] / 2.0
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                c = centre + np.array([ox * tile, oy * tile])
                start, end = c - d * half_length, c + d * half_length
                lo, hi = np.minimum(start, end), np.maximum(start, end)
                if hi[0] < -band['half'] or lo[0] > tile + band['half'] or hi[1] < -band['half'] or lo[1] > tile + band['half']:
                    continue
                # tile units: x to the right, y UP the picture (so the picture's y runs the other way)
                base = bpy.data.meshes.new('bar point')
                base.from_pydata([(0, 0, 0)], [], [])
                obj = bpy.data.objects.new('bar', base)
                scene.collection.objects.link(obj)
                modifier = obj.modifiers.new('bar', 'NODES')
                modifier.node_group = bar_tree
                gt.modifier_inputs(modifier, Start=(start[0] / tile, 1.0 - start[1] / tile, 0.0), End=(end[0] / tile, 1.0 - end[1] / tile, 0.0),
                                   Width=2 * band['half'] / tile, Height=strap_height)
                objects.append(obj)
                n_bars += 1
    # rivets: a cloud of points (every rivet and its wrap copies), one cone per point
    points = []
    for x, y in description.get('rivets', []):
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                px, py = x + 0.5 + ox * tile, y + 0.5 + oy * tile
                if -40 < px < tile + 40 and -40 < py < tile + 40:
                    points.append((px / tile, 1.0 - py / tile, strap_height))
    cloud = bpy.data.meshes.new('rivet points')
    cloud.from_pydata(points, [], [])
    rivet_object = bpy.data.objects.new('rivets', cloud)
    scene.collection.objects.link(rivet_object)
    modifier = rivet_object.modifiers.new('rivets', 'NODES')
    modifier.node_group = rivet_tree
    gt.modifier_inputs(modifier, Radius=description.get('rivet', {}).get('radius', 19.5) / tile, Height=rivet_height)
    objects.append(rivet_object)
    return scene, objects, n_bars, len(points)


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    description = json.load(open(arguments[0]))
    out_folder = arguments[1]
    size = int(option('--size', 1254))
    strap_height = float(option('--strap-height', 0.012))
    rivet_height = float(option('--rivet-height', 0.02))
    os.makedirs(out_folder, exist_ok=True)
    started = time.time()
    scene, objects, n_bars, n_rivets = build_scene(description, size, strap_height, rivet_height)
    built = time.time() - started
    top = strap_height + rivet_height
    bpy.context.scene.camera.location = (0.5, 0.5, 3.0)
    bpy.context.scene.camera.data.clip_start = 0.5
    bpy.context.scene.camera.data.clip_end = 6.0
    t = time.time()
    # height: 0 at the plate, 1 at the top of a rivet
    gt.render_with(scene, objects, gt.height_material(0.0, top), os.path.join(out_folder, 'height_geometry.png'), True, True, samples=1)
    height_seconds = time.time() - t
    t = time.time()
    gt.render_with(scene, objects, gt.normal_material(), os.path.join(out_folder, 'normal_geometry.png'), True, False, samples=1)
    normal_seconds = time.time() - t
    info = {'size': size, 'bars': n_bars, 'rivet_points': n_rivets, 'strap_height': strap_height, 'rivet_height': rivet_height, 'top': top,
            'build_seconds': round(built, 2), 'height_render_seconds': round(height_seconds, 2), 'normal_render_seconds': round(normal_seconds, 2), 'seconds': round(time.time() - started, 2)}
    json.dump(info, open(os.path.join(out_folder, 'geometry_route.json'), 'w'), indent=1)
    print('[geometry route]', json.dumps(info))


if __name__ == '__main__':
    main()
