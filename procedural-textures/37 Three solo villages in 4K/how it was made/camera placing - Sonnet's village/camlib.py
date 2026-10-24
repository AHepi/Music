"""Shared: build camera objects from a JSON spec (ground-relative heights via ray cast on Terrain)."""
import bpy, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_BVH = {}
def terrain_bvh():
    if 'b' not in _BVH:
        dg = bpy.context.evaluated_depsgraph_get()
        ter = bpy.data.objects['Terrain'].evaluated_get(dg)
        me = ter.to_mesh()
        mw = ter.matrix_world
        verts = [mw @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        _BVH['b'] = BVHTree.FromPolygons(verts, polys)
        ter.to_mesh_clear()
    return _BVH['b']

def ground(x, y):
    hit = terrain_bvh().ray_cast(Vector((x, y, 300.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0

def resolve(p):
    """p = [x, y, z, 'agl'|'abs']"""
    x, y, z = p[0], p[1], p[2]
    mode = p[3] if len(p) > 3 else 'agl'
    return Vector((x, y, ground(x, y) + z if mode == 'agl' else z))

def make_camera(spec, coll):
    name = spec['name']
    loc = resolve(spec['loc']); tgt = resolve(spec['target'])
    cd = bpy.data.cameras.get(name)
    if cd is None:
        cd = bpy.data.cameras.new(name)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
        coll.objects.link(ob)
    ob.data = cd
    cd.lens = spec.get('lens', 30.0)
    cd.sensor_width = 36.0
    cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start = spec.get('clip_start', 0.05)
    cd.clip_end = 3000.0
    cd.shift_x = spec.get('shift_x', 0.0)
    cd.shift_y = spec.get('shift_y', 0.0)
    ob.location = loc
    d = tgt - loc
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if spec.get('fstop'):
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = spec['fstop']
        cd.dof.focus_distance = spec.get('focus', d.length)
    else:
        cd.dof.use_dof = False
    return ob, loc, tgt
