"""Pass 2 building extras: lumpy thatch geometry, moss cushions on the stable roof.

Judges on pass 1: thatch "a smoothly streaked, brushed texture with a sausage-like eave", "motion-blurred fur";
stable roof "very evenly tiled with flat moss patches", "blotchy flat spotting".
"""
import bpy
import numpy as np
import math
import common as C
from common import NB, new_material
from materials import hexc
import vegetation as V


def _named(nb, name, dtype='FLOAT'):
    n = nb.node('GeometryNodeInputNamedAttribute', data_type=dtype)
    n.inputs['Name'].default_value = name
    return nb.out(n, 'Attribute')


def thatch_relief_group():
    """Subdivide the thatch slab and push the top surface out along its normal by straw bundles (the same
    UV-space cells as the thatch shader), broad lumps and a fine bristle; the cut eave faces stay put."""
    name = "GN_thatch_relief"
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    lv = ng.interface.new_socket('Level', in_out='INPUT', socket_type='NodeSocketInt')
    lv.default_value = 3
    sc = ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    sc.default_value = 0.035
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nb = NB(ng)
    gin = nb.node('NodeGroupInput')
    gout = nb.node('NodeGroupOutput')
    sub = nb.node('GeometryNodeSubdivideMesh')
    nb.links.new(gin.outputs[0], sub.inputs['Mesh'])
    nb.links.new(gin.outputs[1], sub.inputs['Level'])
    uv = _named(nb, 'UVMap', 'FLOAT_VECTOR')
    eave = _named(nb, 'eave')
    sx, sy, _ = nb.sep(uv)
    bvec = nb.comb(nb.math('MULTIPLY', sx, 8.0), nb.math('MULTIPLY', sy, 2.4), 0.0)
    bvor = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1')
    nb.set(bvor, 'Vector', bvec)
    nb.set(bvor, 'Scale', 1.0)
    bpos = nb.out(bvor, 'Position')
    bund = nb.out(bvor, 'Color')
    by = nb.math('SUBTRACT', nb.sep(bvec)[1], nb.sep(bpos)[1])
    bh = nb.maprange(by, 0.45, -0.45, 0.0, 1.0)
    bund_d = nb.voronoi(bvec, scale=1.0, feature='DISTANCE_TO_EDGE', which='Distance', dims='2D')
    gaps = nb.maprange(bund_d, 0.0, 0.07, 1.0, 0.0)
    brnd = nb.noise(bund, scale=3.0, detail=0)
    lumps = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 1.6), nb.math('MULTIPLY', sy, 0.9), 0.0), scale=1.0, detail=4, rough=0.6)
    off = nb.vmath('MULTIPLY', bund, (5.0, 5.0, 5.0))
    svec = nb.vmath('ADD', nb.comb(nb.math('MULTIPLY', sx, 110.0), nb.math('MULTIPLY', sy, 11.0), 0.0), off)
    strands = nb.noise(svec, scale=1.0, detail=3, rough=0.6, distortion=0.4)
    h = nb.math('MULTIPLY', bh, nb.math('ADD', 0.6, nb.math('MULTIPLY', brnd, 0.8)))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', gaps, 0.5))
    h = nb.math('ADD', h, nb.math('MULTIPLY', nb.math('SUBTRACT', lumps, 0.5), 1.4))
    h = nb.math('ADD', h, nb.math('MULTIPLY', strands, 0.15))
    mask = nb.math('SUBTRACT', 1.0, nb.math('MINIMUM', nb.math('MULTIPLY', eave, 2.0), 1.0))
    nrm = nb.out(nb.node('GeometryNodeInputNormal'))
    d = nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('SUBTRACT', h, 0.35), mask), gin.outputs[2])
    sp = nb.node('GeometryNodeSetPosition')
    nb.links.new(nb.out(sub), sp.inputs['Geometry'])
    nb.links.new(nb.vmath('MULTIPLY', nrm, nb.comb(d, d, d)), sp.inputs['Offset'])
    nb.links.new(nb.out(sp), gout.inputs[0])
    return ng


def apply_thatch_relief(levels=None):
    levels = levels or {"cottage_a_thatch": 3, "cottage_b_thatch": 2, "cottage_d_thatch": 2}
    ng = thatch_relief_group()
    out = {}
    for nm, lvl in levels.items():
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        for m in list(ob.modifiers):
            if m.type == 'NODES' and m.name == "relief":
                ob.modifiers.remove(m)
        mod = ob.modifiers.new("relief", 'NODES')
        mod.node_group = ng
        C.set_mod_input(mod, "Level", lvl)
        out[nm] = lvl
    return out


# ----------------------------------------------------------------------------
# moss cushions on the shingle roof
# ----------------------------------------------------------------------------
def mat_moss():
    m = new_material("moss_cushion")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    rnd = nb.objinfo('Random')
    n = nb.noise(obj, scale=60.0, detail=4, rough=0.7)
    col = nb.ramp(rnd, [(0.0, hexc('3a4718')), (0.35, hexc('4f5f1e')), (0.65, hexc('66702a')), (0.85, hexc('7a7a3a')), (1.0, hexc('45501f'))])
    col = nb.hsv(col, v=nb.maprange(n, 0.3, 0.7, 0.7, 1.2))
    gz = nb.sep(nb.texcoord('Generated'))[2]
    col = nb.mix(nb.maprange(gz, 0.4, 0.0, 0.0, 0.6), col, hexc('2a2f14'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.8, Normal=nb.bump(n, 0.8, 0.004))
    nb.set(bsdf, 'Sheen Weight', 0.6)
    nb.set(bsdf, 'Sheen Tint', (0.85, 0.95, 0.6, 1.0))
    tr = nb.node('ShaderNodeBsdfTranslucent')
    nb.set(tr, 'Color', nb.hsv(col, v=0.8))
    mix = nb.node('ShaderNodeMixShader')
    nb.set(mix, 'Fac', 0.15)
    nb.links.new(bsdf.outputs[0], mix.inputs[1])
    nb.links.new(tr.outputs[0], mix.inputs[2])
    nb.output(mix)
    return m


def build_moss_library():
    import plants as PL
    mat = mat_moss()
    col = V.lib_collection("lib_moss")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(6):
        rng = np.random.RandomState(6100 + i)
        v, f = PL.rock(rng, 1.0, flat=rng.uniform(0.3, 0.45), sub=3)
        v = v.copy()
        v[:, 2] = np.clip(v[:, 2], -0.05, None)
        # lumpy, cushion-like
        v *= (1.0 + 0.12 * np.sin(v[:, :1] * 9.0 + i) * np.cos(v[:, 1:2] * 7.0))
        me = C.mesh_from_arrays("moss_%d" % i, v, f, smooth=True, materials=[mat])
        ob = bpy.data.objects.new(me.name, me)
        col.objects.link(ob)
    V.exclude_library()
    return 6


def moss_group(surface, density=60.0, seed=7):
    name = "GN_roof_moss"
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nb = NB(ng)
    gin = nb.node('NodeGroupInput')
    gout = nb.node('NodeGroupOutput')
    oi = nb.node('GeometryNodeObjectInfo', transform_space='RELATIVE')
    oi.inputs['Object'].default_value = surface
    pos = nb.out(nb.node('GeometryNodeInputPosition'))
    nrm = nb.out(nb.node('GeometryNodeInputNormal'))
    clump = nb.maprange(nb.noise(pos, scale=0.9, detail=4, rough=0.6), 0.5, 0.66, 0.0, 1.0)
    fine = nb.maprange(nb.noise(pos, scale=6.0, detail=2), 0.4, 0.7, 0.2, 1.0)
    up = nb.maprange(nb.sep(nrm)[2], 0.35, 0.75, 0.0, 1.0)
    # more moss low on the roof, near the eaves where the shingles stay wet
    low = nb.maprange(nb.sep(pos)[2], 4.6, 3.0, 0.3, 1.0)
    dens = nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('MULTIPLY', clump, fine), nb.math('MULTIPLY', up, low)), density)
    dist = nb.node('GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM')
    nb.links.new(nb.out(oi, 'Geometry'), dist.inputs['Mesh'])
    nb.set(dist, 'Density', dens)
    nb.set(dist, 'Seed', seed)
    rs = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rs, 'Min', 0.0)
    nb.set(rs, 'Max', 1.0)
    nb.set(rs, 'Seed', seed + 3)
    s = nb.math('ADD', 0.012, nb.math('MULTIPLY', nb.math('POWER', nb.out(rs), 2.2), 0.07))
    rz = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rz, 'Min', 0.0)
    nb.set(rz, 'Max', 6.2831)
    nb.set(rz, 'Seed', seed + 2)
    e2r = nb.node('FunctionNodeEulerToRotation')
    nb.links.new(nb.comb(0.0, 0.0, nb.out(rz)), e2r.inputs['Euler'])
    rr = nb.node('FunctionNodeRotateRotation', rotation_space='LOCAL')
    nb.links.new(nb.out(dist, 'Rotation'), rr.inputs['Rotation'])
    nb.links.new(nb.out(e2r), rr.inputs['Rotate By'])
    ci = nb.node('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
    ci.inputs['Collection'].default_value = bpy.data.collections["lib_moss"]
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    ri = nb.node('FunctionNodeRandomValue', data_type='INT')
    nb.set(ri, 'Min', 0)
    nb.set(ri, 'Max', 5)
    nb.set(ri, 'Seed', seed + 1)
    iop = nb.node('GeometryNodeInstanceOnPoints')
    nb.links.new(nb.out(dist, 'Points'), iop.inputs['Points'])
    nb.links.new(nb.out(ci), iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    nb.links.new(nb.out(ri), iop.inputs['Instance Index'])
    nb.links.new(nb.out(rr), iop.inputs['Rotation'])
    nb.links.new(nb.comb(s, s, nb.math('MULTIPLY', s, 0.8)), iop.inputs['Scale'])
    nb.links.new(nb.out(iop), gout.inputs[0])
    return ng


def roof_moss():
    build_moss_library()
    surf = bpy.data.objects.get("stable_shingle")
    if surf is None:
        return 0
    col = bpy.data.collections["B_stable"]
    ob = bpy.data.objects.get("stable_roof_moss")
    if ob is None:
        me = bpy.data.meshes.new("stable_roof_moss_empty")
        ob = bpy.data.objects.new("stable_roof_moss", me)
        col.objects.link(ob)
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    mod = ob.modifiers.new("moss", 'NODES')
    mod.node_group = moss_group(surf)
    # the scatter reads the roof in its own (parent-relative) space, so follow the stable's parent
    ob.parent = surf.parent
    ob.matrix_parent_inverse = surf.matrix_parent_inverse.copy()
    return 1
