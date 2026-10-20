# What this does: measures how long it takes to cut N round holes (rivet holes, bolt holes) in a plate with Boolean in Blender 5.2.2 (CPU, 1 thread here), four ways:
#   a) N separate Boolean modifiers, Exact solver, one per cutter          (the "obvious" way)
#   b) ONE Boolean modifier with ONE cutter object that already contains all N cylinders, Exact solver
#   c) the same one-cutter version with the Float (fast) solver
#   e) the one-cutter version with the Manifold solver
#   d) the Geometry Nodes "Mesh Boolean" node (solver Float, its default) with all cylinders joined into one mesh
# Run: blender -b --disable-autoexec -t 1 --python t08_boolean_speed.py
import json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh, numpy as np
import gn_tools as gt
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

def plate():
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x *= 0.9; v.co.y *= 0.9; v.co.z = (v.co.z + 0.5) * 0.04
    mesh = bpy.data.meshes.new('plate'); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new('plate', mesh); obj.location = (0.5, 0.5, 0); bpy.context.scene.collection.objects.link(obj); return obj

def cutters_mesh(n):
    bm = bmesh.new()
    side = int(math.ceil(math.sqrt(n)))
    k = 0
    for i in range(side):
        for j in range(side):
            if k >= n: break
            bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.012, radius2=0.012, depth=0.2, matrix=__import__('mathutils').Matrix.Translation((((i + 0.5) / side - 0.5) * 0.8, ((j + 0.5) / side - 0.5) * 0.8, 0.02)))
            k += 1
    mesh = bpy.data.meshes.new('cutters'); bm.to_mesh(mesh); bm.free(); return mesh

def timed(fn):
    t = time.time(); fn(); return round(time.time() - t, 3)

results = {}
for n in (4, 16, 64, 144):
    row = {}
    # a) N modifiers
    gt.new_scene(32)
    p = plate()
    mesh = cutters_mesh(n)
    # build N separate cutter objects from the same shapes
    per = []
    side = int(math.ceil(math.sqrt(n))); k = 0
    for i in range(side):
        for j in range(side):
            if k >= n: break
            bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.012, radius2=0.012, depth=0.2)
            m = bpy.data.meshes.new('c'); bm.to_mesh(m); bm.free()
            c = bpy.data.objects.new('c', m); c.location = (0.5 + ((i + 0.5) / side - 0.5) * 0.8, 0.5 + ((j + 0.5) / side - 0.5) * 0.8, 0.02); bpy.context.scene.collection.objects.link(c); c.hide_render = True
            mod = p.modifiers.new('cut', 'BOOLEAN'); mod.operation, mod.object, mod.solver = 'DIFFERENCE', c, 'EXACT'
            k += 1
    row['a_N_modifiers_exact_s'] = timed(lambda: gt.evaluated_vertices(p))
    # b) one cutter with all cylinders
    gt.new_scene(32); p = plate()
    c = bpy.data.objects.new('cutter', cutters_mesh(n)); c.location = (0.5, 0.5, 0); bpy.context.scene.collection.objects.link(c); c.hide_render = True
    mod = p.modifiers.new('cut', 'BOOLEAN'); mod.operation, mod.object, mod.solver = 'DIFFERENCE', c, 'EXACT'
    row['b_one_cutter_exact_s'] = timed(lambda: gt.evaluated_vertices(p))
    row['vertices_after'] = int(len(gt.evaluated_vertices(p)))
    mod.solver = 'FLOAT' if 'FLOAT' in [i.identifier for i in mod.bl_rna.properties['solver'].enum_items] else 'FAST'
    row['c_one_cutter_float_s'] = timed(lambda: gt.evaluated_vertices(p)); row['c_solver_used'] = mod.solver
    row['c_vertices_after'] = int(len(gt.evaluated_vertices(p)))
    mod.solver = 'MANIFOLD'
    row['e_one_cutter_manifold_s'] = timed(lambda: gt.evaluated_vertices(p)); row['e_vertices_after'] = int(len(gt.evaluated_vertices(p)))
    # d) GN Mesh Boolean
    gt.new_scene(32)
    tree, g = gt.make_geometry_group('bool', [('Geometry', 'NodeSocketGeometry', None)])
    g.node('GeometryNodeObjectInfo', 'plate info'); 
    p = plate()
    c = bpy.data.objects.new('cutter', cutters_mesh(n)); c.location = (0.5, 0.5, 0); bpy.context.scene.collection.objects.link(c); c.hide_render = True
    g.node('GeometryNodeObjectInfo', 'cut info', {'Object': c}, transform_space='RELATIVE')
    g.node('GeometryNodeMeshBoolean', 'boolean', {'Mesh 1': ('in', 'Geometry'), 'Mesh 2': ('cut info', 'Geometry')}, operation='DIFFERENCE', solver='FLOAT')   # the node's default solver is Float; Exact and Manifold also exist
    g.link('boolean', 'Mesh', 'out', 'Geometry')
    mod = p.modifiers.new('gn', 'NODES'); mod.node_group = tree
    row['d_geometry_nodes_mesh_boolean_s'] = timed(lambda: gt.evaluated_vertices(p))
    row['d_vertices_after'] = int(len(gt.evaluated_vertices(p)))
    results[str(n)] = row
    print(n, row)
json.dump(results, open(os.path.join(OUT, 't08_boolean_speed.json'), 'w'), indent=1)
