# What this does: shows, from straight above as a HEIGHT picture (white = high), what each classic modifier does to a simple shape, so the guide can say
# "this modifier does this to a height map". 12 small pictures, one per modifier (some show 2 or 3 settings side by side in one picture), plus a table of
# vertex counts and the time each took. Everything is measured in Blender 5.2.2 (CPU).
# Run: blender -b --disable-autoexec -t 2 --python t05_modifier_gallery.py        then   python3 -I ../../lib/make_strip.py out/t05_modifiers out/t05_modifiers_sheet.png --columns 4 --title "..."
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import gn_tools as gt  # noqa: E402
import bake_harness as bh  # noqa: E402

OUT = os.path.join(HERE, 'out', 't05_modifiers')
os.makedirs(OUT, exist_ok=True)
SIZE = 256
Z_LOW, Z_HIGH = -0.02, 0.14


def box_mesh(name, size=(0.2, 0.2, 0.08), cuts=0, base_z=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z = (v.co.z + 0.5) * size[2] + base_z
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def grid_mesh(name, segments=96, size=1.0):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segments, y_segments=segments, size=size / 2)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def add(name, mesh, location):
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def cell_displace():
    tex = bpy.data.textures.new('clouds', 'CLOUDS')
    tex.noise_scale = 0.22
    tex.noise_depth = 3
    obj = add('plane', grid_mesh('plane', 128), (0.5, 0.5, 0.0))
    m = obj.modifiers.new('displace', 'DISPLACE')
    m.texture, m.strength, m.mid_level, m.texture_coords = tex, 0.10, 0.5, 'LOCAL'
    return [obj], 'Displace: Clouds texture, strength 0.10'


def cell_subsurf():
    objs = []
    for i, level in enumerate((0, 2, 3)):
        obj = add(f'cube{level}', box_mesh(f'c{level}', (0.2, 0.2, 0.1)), (0.18 + i * 0.32, 0.5, 0.0))
        m = obj.modifiers.new('subsurf', 'SUBSURF')
        m.levels = m.render_levels = level
        objs.append(obj)
    return objs, 'Subdivision Surface: level 0, 2, 3'


def cell_bevel():
    objs = []
    for i, (width, segments) in enumerate(((0.0, 1), (0.02, 1), (0.04, 4))):
        obj = add(f'b{i}', box_mesh(f'b{i}', (0.2, 0.2, 0.1)), (0.18 + i * 0.32, 0.5, 0.0))
        m = obj.modifiers.new('bevel', 'BEVEL')
        m.width, m.segments, m.limit_method = max(width, 1e-5), segments, 'ANGLE'
        objs.append(obj)
    return objs, 'Bevel: width 0 / 0.02 (1 seg) / 0.04 (4 seg)'


def cell_boolean_cut():
    plate = add('plate', box_mesh('plate', (0.8, 0.8, 0.06), cuts=0), (0.5, 0.5, 0.0))
    objs = [plate]
    for x, y in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.07, depth=0.2, location=(x, y, 0.03))
        cutter = bpy.context.object
        cutter.display_type, cutter.hide_render = 'WIRE', True
        m = plate.modifiers.new('cut', 'BOOLEAN')
        m.operation, m.object, m.solver = 'DIFFERENCE', cutter, 'EXACT'
        objs.append(cutter)
    return [plate], 'Boolean: Difference (cut 4 holes with cylinders)'


def cell_boolean_union():
    plate = add('plate', box_mesh('plate', (0.8, 0.8, 0.03), cuts=0), (0.5, 0.5, 0.0))
    for x, y in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.06, location=(x, y, 0.03))
        ball = bpy.context.object
        ball.hide_render = True
        m = plate.modifiers.new('bolt', 'BOOLEAN')
        m.operation, m.object, m.solver = 'UNION', ball, 'EXACT'
    return [plate], 'Boolean: Union (add 4 domed bolts)'


def cell_remesh():
    objs = []
    for i, (mode, voxel) in enumerate((('VOXEL', 0.02), ('BLOCKS', 0.0))):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.12, location=(0.28 + i * 0.44, 0.5, 0.0))
        obj = bpy.context.object
        m = obj.modifiers.new('remesh', 'REMESH')
        m.mode = mode
        if mode == 'VOXEL':
            m.voxel_size = voxel
        else:
            m.octree_depth, m.scale = 5, 0.8
            m.use_remove_disconnected = False
        objs.append(obj)
    return objs, 'Remesh: Voxel 0.02 (rebuilds the surface evenly) / Blocks'


def cell_weld_array():
    obj = add('brick', box_mesh('brick', (0.18, 0.1, 0.06)), (0.15, 0.5, 0.0))
    m = obj.modifiers.new('array', 'ARRAY')
    m.count, m.use_relative_offset, m.relative_offset_displace = 5, True, (1.0, 0.0, 0.0)     # touching bricks: the shared faces are DOUBLE
    w = obj.modifiers.new('weld', 'WELD')
    w.merge_threshold = 0.001
    return [obj], 'Array (5, touching) + Weld: height picture is the same as Array alone; vertices are merged (see table)'


def cell_solidify():
    obj = add('sheet', grid_mesh('sheet', 40, 0.8), (0.5, 0.5, 0.08))
    d = obj.modifiers.new('bend', 'WAVE')
    d.height = 0.08
    bpy.context.scene.frame_set(8)
    s = obj.modifiers.new('solidify', 'SOLIDIFY')
    s.thickness, s.offset = 0.04, -1
    return [obj], 'Wave + Solidify: a rippled sheet given thickness (top picture hardly changes; the underside moves down)'


def cell_array():
    obj = add('brick', box_mesh('brick', (0.2, 0.08, 0.06)), (0.12, 0.2, 0.0))
    m = obj.modifiers.new('array', 'ARRAY')
    m.count, m.use_relative_offset, m.relative_offset_displace = 4, True, (1.12, 0.0, 0.0)
    m.use_constant_offset, m.constant_offset_displace = True, (0.0, 0.0, 0.0)
    obj2 = add('brick2', box_mesh('brick2', (0.2, 0.08, 0.06)), (0.12, 0.62, 0.0))
    m2 = obj2.modifiers.new('array', 'ARRAY')
    m2.count, m2.use_relative_offset, m2.relative_offset_displace = 4, True, (1.12, 0.0, 0.0)
    m2.use_constant_offset, m2.constant_offset_displace = True, (0.0, 0.0, 0.015)      # each next brick 0.015 higher: a staircase
    return [obj, obj2], 'Array: relative offset 1.12 (gaps) / + constant offset in z'


def cell_wave():
    obj = add('water', grid_mesh('water', 128), (0.5, 0.5, 0.05))
    m = obj.modifiers.new('wave', 'WAVE')
    m.height = 0.12        # width, narrowness, speed etc. stay at their defaults (width 1.5, narrowness 1.5): a ring spreading from the middle
    bpy.context.scene.frame_set(8)      # the Wave modifier moves with the scene clock
    return [obj], 'Wave: height 0.12 at frame 8 (a ring spreading from the middle; other settings default)'


def cell_cast():
    objs = []
    for i, factor in enumerate((0.0, 0.5, 1.0)):
        obj = add(f'cast{i}', box_mesh(f'cast{i}', (0.2, 0.2, 0.2), cuts=6), (0.18 + i * 0.32, 0.5, 0.0))
        m = obj.modifiers.new('cast', 'CAST')
        m.cast_type, m.factor, m.radius = 'SPHERE', factor, 0.0
        objs.append(obj)
    return objs, 'Cast (sphere): factor 0 / 0.5 / 1.0 - a block becomes a pebble'


def cell_simple_deform():
    objs = []
    for i, (method, angle) in enumerate((('BEND', 70), ('TWIST', 80), ('TAPER', 0))):
        obj = add(f'sd{i}', box_mesh(f'sd{i}', (0.5, 0.08, 0.05), cuts=10), (0.5, 0.17 + i * 0.3, 0.0))
        m = obj.modifiers.new('deform', 'SIMPLE_DEFORM')
        m.deform_method = method
        m.deform_axis = 'Z' if method == 'BEND' else 'X'
        if method == 'TAPER':
            m.factor = 0.8
        else:
            m.angle = math.radians(angle)
        objs.append(obj)
    return objs, 'Simple Deform: Bend 70 / Twist 80 / Taper (a plank)'


SHORT = ['Displace (Clouds)', 'Subdivision 0 / 2 / 3', 'Bevel 0 / 1 / 4 seg', 'Boolean: Difference', 'Boolean: Union', 'Remesh: Voxel / Blocks', 'Array + Weld', 'Wave + Solidify', 'Array offsets', 'Wave', 'Cast 0 / .5 / 1', 'Simple Deform']
CELLS = [cell_displace, cell_subsurf, cell_bevel, cell_boolean_cut, cell_boolean_union, cell_remesh, cell_weld_array, cell_solidify, cell_array, cell_wave, cell_cast, cell_simple_deform]


def main():
    results = []
    files, labels = [], []
    material = None
    for index, build in enumerate(CELLS):
        scene = gt.new_scene(SIZE)
        started = time.time()
        objs, label = build()
        bpy.context.view_layer.update()
        count = 0
        for obj in objs:
            count += len(gt.evaluated_vertices(obj))
        eval_time = time.time() - started
        material = gt.height_material(Z_LOW, Z_HIGH)
        for obj in objs:
            obj.data.materials.clear()
            obj.data.materials.append(material)
        path = os.path.join(OUT, f'tile_{index:02d}.png')
        t0 = time.time()
        gt.render_with(scene, [o for o in objs], material, path, True, False)
        results.append({'cell': build.__name__, 'label': label, 'vertices_after_modifiers': count, 'evaluate_seconds': round(eval_time, 3), 'render_seconds': round(time.time() - t0, 2)})
        files.append(os.path.basename(path))
        labels.append(SHORT[index])
        # vertices BEFORE the modifier(s) for the Weld/Array row
    # weld numbers: the same Array with and without Weld
    scene = gt.new_scene(64)
    brick = add('b', box_mesh('b', (0.18, 0.1, 0.06)), (0.15, 0.5, 0.0))
    a = brick.modifiers.new('array', 'ARRAY')
    a.count, a.use_relative_offset, a.relative_offset_displace = 5, True, (1.0, 0.0, 0.0)
    without = len(gt.evaluated_vertices(brick))
    w = brick.modifiers.new('weld', 'WELD')
    w.merge_threshold = 0.001
    with_weld = len(gt.evaluated_vertices(brick))
    results.append({'weld_check': {'vertices_array_only': without, 'vertices_array_then_weld': with_weld}})
    # solidify numbers
    scene = gt.new_scene(64)
    sheet = add('s', grid_mesh('s', 20, 0.8), (0.5, 0.5, 0.08))
    before = gt.evaluated_vertices(sheet)
    sol = sheet.modifiers.new('solidify', 'SOLIDIFY')
    sol.thickness, sol.offset = 0.04, -1
    after = gt.evaluated_vertices(sheet)
    results.append({'solidify_check': {'vertices_before': len(before), 'vertices_after': len(after), 'z_range_before': [float(before[:, 2].min()), float(before[:, 2].max())],
                                       'z_range_after': [float(after[:, 2].min()), float(after[:, 2].max())]}})
    with open(os.path.join(OUT, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels}, handle)
    with open(os.path.join(OUT, 'results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
