"""GROUND builder: a small generic geometry-nodes instancer ('G6 ground / <name> instancer') and the point meshes that feed it.
Points carry INT g6_pick (which source), FLOAT g6_scale, FLOAT g6_rot (turn about z); the node group reads them and instances the hidden sources.
No placement logic lives in the nodes: positions are chosen by the stage (ray casts against the real scene), so a re-run on a changed scene follows it.
"""
import bpy
import numpy as np
from g6_common import PFX, tag, get_collection


def make_points_mesh(name, xyz, attrs):
    me = bpy.data.meshes.new(name)
    xyz = np.asarray(xyz, dtype=np.float32).reshape(-1, 3)
    me.vertices.add(len(xyz))
    me.vertices.foreach_set('co', xyz.ravel())
    for an, (dt, arr) in attrs.items():
        a = me.attributes.new(an, dt, 'POINT')
        a.data.foreach_set('value', np.asarray(arr, dtype=np.float32 if dt == 'FLOAT' else np.int32))
    me.update()
    return me


def build_instancer_group(name, sources, tilt_attr=None):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    nd, lk = ng.nodes, ng.links
    gi = nd.new('NodeGroupInput'); gi.location = (-900, 0)
    go = nd.new('NodeGroupOutput'); go.location = (700, 0)

    def named(attr, dtype, y):
        n = nd.new('GeometryNodeInputNamedAttribute')
        n.data_type = dtype
        n.inputs['Name'].default_value = attr
        n.location = (-700, y)
        return n
    pick = named('g6_pick', 'INT', -150)
    scl = named('g6_scale', 'FLOAT', -300)
    rot = named('g6_rot', 'FLOAT', -450)
    comb = nd.new('ShaderNodeCombineXYZ'); comb.location = (-480, -450)
    lk.new(rot.outputs['Attribute'], comb.inputs['Z'])
    g2i = nd.new('GeometryNodeGeometryToInstance'); g2i.location = (-200, -650)
    # NOTE (found 22 October): the multi-input socket of Geometry to Instance evaluates its links in REVERSE order of creation, so the links are
    # made last source first; then instance index k is sources[k] (checked by counting the realised triangles against the picks).
    for i, so in reversed(list(enumerate(sources))):
        oi = nd.new('GeometryNodeObjectInfo'); oi.location = (-700, -650 - 120 * i)
        oi.transform_space = 'ORIGINAL'
        oi.inputs['Object'].default_value = so
        oi.inputs['As Instance'].default_value = False
        lk.new(oi.outputs['Geometry'], g2i.inputs['Geometry'])
    iop = nd.new('GeometryNodeInstanceOnPoints'); iop.location = (300, 0)
    iop.inputs['Pick Instance'].default_value = True
    lk.new(gi.outputs[0], iop.inputs['Points'])
    lk.new(g2i.outputs['Instances'], iop.inputs['Instance'])
    lk.new(pick.outputs['Attribute'], iop.inputs['Instance Index'])
    lk.new(comb.outputs['Vector'], iop.inputs['Rotation'])
    lk.new(scl.outputs['Attribute'], iop.inputs['Scale'])
    lk.new(iop.outputs['Instances'], go.inputs[0])
    return ng
