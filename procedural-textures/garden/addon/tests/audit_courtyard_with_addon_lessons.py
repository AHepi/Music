# What this does: opens the saved courtyard (read-only, nothing saved, nothing rendered) and runs the checks the
# add-on's own advice asks for: its own landscape audit through the real camera, closed-shape winding per piece,
# which objects use per-object material overrides, unused material slots, and stone/pier/bridge ground contact.
import sys, importlib.util, math, json
sys.dont_write_bytecode = True
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
FOLDER = 'scratchpad/astra-upload-021'
BLEND = 'scratchpad/astra-work/out/courtyard_final.blend'
name = 'astra_painted_workbench'
spec = importlib.util.spec_from_file_location(name, FOLDER + '/__init__.py', submodule_search_locations=[FOLDER])
mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
import astra_painted_workbench.runtime.api as api
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
print('objects', len(bpy.data.objects), 'meshes', len(bpy.data.meshes), 'camera', scene.camera.name, scene.render.resolution_x, scene.render.resolution_y)
# 1. the add-on's own landscape audit with the photo camera
root = next(o for o in bpy.data.objects if o.get('astra_kind') == 'landscape')
rep = api.audit_landscape(root, scene.camera, scene)
print('LANDSCAPE counts', rep['counts'], 'relief_peak', round(rep['relief_peak'], 3))
print('LANDSCAPE protection', {k: rep['protection'][k] for k in ('frozen_polygons', 'total_polygons', 'conservatively_suppressed_vertices')})
print('LANDSCAPE rejections', json.dumps(rep['rejections']))
print('LANDSCAPE checks', rep['checks'])
print('LANDSCAPE projection', json.dumps(rep.get('projection_estimates')))
for w in rep['warnings']: print('LANDSCAPE warning:', w[:200])
# 2. winding per closed component, hand-made meshes and add-on meshes
dg = bpy.context.evaluated_depsgraph_get()
def component_report(ob):
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear()
    bm.verts.ensure_lookup_table(); seen = set(); neg = pos = open_c = 0; comps = 0
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); verts = []; 
        while stack:
            a = stack.pop(); verts.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen: seen.add(b.index); stack.append(b)
        comps += 1
        faces = {f for a in verts for f in a.link_faces}
        closed = all(len(e.link_faces) == 2 for a in verts for e in a.link_edges)
        if not closed: open_c += 1; continue
        vol = 0.0
        for f in faces:
            vs = [l.vert.co for l in f.loops]
            for i in range(1, len(vs) - 1): vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
        if vol < 0: neg += 1
        else: pos += 1
    bm.free(); return comps, pos, neg, open_c
print('WINDING (closed components: positive/negative volume; open = not closed)')
bad = []
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != 'MESH' or ob.hide_render: continue
    if len(ob.data.polygons) > 120000: print('  skip big', ob.name); continue
    comps, pos, neg, op = component_report(ob)
    if neg: bad.append((ob.name, comps, pos, neg, op))
print('  objects with inward closed components:', bad)
# 3. per-object material overrides and unused slots
over = [(o.name, [s.material.name if s.material else None for s in o.material_slots if s.link == 'OBJECT']) for o in bpy.data.objects if o.type == 'MESH' and any(s.link == 'OBJECT' for s in o.material_slots)]
print('OBJECT-linked material slots:', over[:10], len(over))
unused = []
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    used = {p.material_index for p in o.data.polygons}
    empty = [i for i in range(len(o.material_slots)) if i not in used]
    if empty and len(o.material_slots) > 1: unused.append((o.name, len(o.material_slots), len(empty)))
print('objects with unused material slots:', unused[:12])
# 4. ground contact for stones, piers, lantern parts (lowest points vs ground, plus corner/edge sampling)
ground = bpy.data.objects['Astra / Courtyard receiving ground']
ev = ground.evaluated_get(dg); gme = ev.to_mesh(); gme.calc_loop_triangles()
gv = [ground.matrix_world @ v.co for v in gme.vertices]
bvh = BVHTree.FromPolygons(gv, [t.vertices[:] for t in gme.loop_triangles])
ev.to_mesh_clear()
def ground_z(x, y):
    h = bvh.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)))
    return h[0].z if h[0] is not None else None
rows = []
for ob in bpy.data.objects:
    if not (ob.name.startswith(('Stepping stone', 'Pond edge stone', 'Rock ', 'Gravel rock', 'Bridge pier', 'Lantern base', 'Water basin', 'Veranda step'))): continue
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    pts = [ob.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + 0.01]
    gaps = []
    for p in low:
        gz = ground_z(p.x, p.y)
        if gz is not None: gaps.append(p.z - gz)
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    xs = [p.x for p in pts]; ys = [p.y for p in pts]
    samples = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys)), (cx, cy)]
    around = [ground_z(x, y) for x, y in samples]
    rows.append((ob.name, round(zmin, 3), round(min(gaps), 3) if gaps else None, round(max(gaps), 3) if gaps else None, round(min(g for g in around if g is not None), 3), round(max(g for g in around if g is not None), 3)))
print('CONTACT (name, lowest z, gap of lowest points to ground min/max, ground z range under footprint corners+centre)')
floaters = [r for r in rows if r[2] is not None and r[2] > 0.02]
buried = [r for r in rows if r[3] is not None and r[3] < -0.30]
for r in rows[:6]: print('  ', r)
print('  count', len(rows), 'lowest points more than 2 cm above ground:', [(r[0], r[2]) for r in floaters][:12])
print('  lowest points deeper than 30 cm below ground:', [(r[0], r[3]) for r in buried][:12])
# bridge: plank runs vs piers
runs = [o for o in bpy.data.objects if o.name.startswith('Astra / varied planks') and o.parent and o.parent.get('astra_kind') == 'planks']
print('plank objects', len(runs))
