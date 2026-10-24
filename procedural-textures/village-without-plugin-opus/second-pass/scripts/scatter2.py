"""Pass 2: what lies on the roads and yards.

Pass 1 scattered pebbles "evenly, like polka dots, round green-grey" and had almost no organic debris.
Here every layer is clumped (masks made from noise), sizes follow a power law (many small, few large),
stones are partly sunk and tilted, and there is straw, fallen leaves, twigs and dung where they belong.
"""
import bpy
import numpy as np
import math
import common as C
from common import NB, new_material, smoothstep, fbm
import plants as PL
from materials import hexc
import vegetation as V

ROAD_GROUND_PREFIX = ("road_", "yard_")


def ground_objects():
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(ROAD_GROUND_PREFIX) and not o.name.endswith("_water")]


# ----------------------------------------------------------------------------
# library: straw bits and fallen leaves
# ----------------------------------------------------------------------------
def mat_straw_bits():
    m = new_material("straw_bits")
    nb = NB(m.node_tree)
    rnd = nb.objinfo('Random')
    col = nb.ramp(rnd, [(0.0, hexc('a38c58')), (0.3, hexc('8c7c5c')), (0.55, hexc('b9a066')), (0.75, hexc('6e6656')), (1.0, hexc('9a8456'))])
    uv = nb.texcoord('UV')
    st = nb.noise(nb.comb(nb.math('MULTIPLY', nb.sep(uv)[0], 3.0), nb.math('MULTIPLY', nb.sep(uv)[1], 60.0), 0.0), scale=1.0, detail=2)
    col = nb.hsv(col, v=nb.maprange(st, 0.3, 0.7, 0.8, 1.15))
    bsdf = nb.principled(Base_Color=col, Roughness=0.6)
    nb.set(bsdf, 'Specular IOR Level', 0.35)
    tr = nb.node('ShaderNodeBsdfTranslucent')
    nb.set(tr, 'Color', col)
    mix = nb.node('ShaderNodeMixShader')
    nb.set(mix, 'Fac', 0.15)
    nb.links.new(bsdf.outputs[0], mix.inputs[1])
    nb.links.new(tr.outputs[0], mix.inputs[2])
    nb.output(mix)
    return m


def mat_dead_leaves():
    m = new_material("dead_leaves")
    nb = NB(m.node_tree)
    rnd = nb.objinfo('Random')
    obj = nb.texcoord('Object')
    col = nb.ramp(rnd, [(0.0, hexc('6b4222')), (0.18, hexc('8a5a26')), (0.36, hexc('a0782e')), (0.5, hexc('5a3d22')),
                        (0.64, hexc('7a6a30')), (0.8, hexc('94562a')), (0.92, hexc('4a3622'))], interp='CONSTANT')
    n = nb.noise(obj, scale=60.0, detail=3)
    col = nb.hsv(col, v=nb.maprange(n, 0.3, 0.7, 0.75, 1.15))
    spots = nb.maprange(nb.noise(obj, scale=25.0, detail=2), 0.6, 0.7, 0.0, 0.6)
    col = nb.mix(spots, col, hexc('3a2818'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.55)
    tr = nb.node('ShaderNodeBsdfTranslucent')
    nb.set(tr, 'Color', nb.hsv(col, v=0.8))
    mix = nb.node('ShaderNodeMixShader')
    nb.set(mix, 'Fac', 0.25)
    nb.links.new(bsdf.outputs[0], mix.inputs[1])
    nb.links.new(tr.outputs[0], mix.inputs[2])
    nb.output(mix)
    return m


def straw_bit_mesh(rng, name, mat):
    L = rng.uniform(0.04, 0.13)
    w = rng.uniform(0.0025, 0.0045)
    n = 5
    verts, faces, uvs = [], [], []
    bend = rng.normal(0, 0.25)
    lift = rng.uniform(0.0, 0.012)
    for i in range(n + 1):
        t = i / n
        x = (t - 0.5) * L
        y = bend * (t - 0.5) ** 2 * L
        z = lift * math.sin(t * math.pi) + 0.0015
        # flattened tube: two strips at an angle so it reads from any side
        verts.append((x, y - w / 2, z))
        verts.append((x, y + w / 2, z))
        verts.append((x, y, z + w * 0.6))
    for i in range(n):
        a = 3 * i
        b = 3 * (i + 1)
        faces.append([a, b, b + 2, a + 2])
        faces.append([a + 2, b + 2, b + 1, a + 1])
        uvs.append([(i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 0.5), (i / n, 0.5)])
        uvs.append([(i / n, 0.5), ((i + 1) / n, 0.5), ((i + 1) / n, 1), (i / n, 1)])
    loop_uv = np.array([uv for f in uvs for uv in f])
    me = C.mesh_from_arrays(name, np.array(verts), faces, loop_uv=loop_uv, smooth=True, materials=[mat])
    return me


def leaf_mesh(rng, name, mat):
    L = rng.uniform(0.035, 0.085)
    W = L * rng.uniform(0.45, 0.7)
    lobes = rng.uniform() < 0.5
    nu, nv = 7, 5
    verts, faces = [], []
    curl = rng.uniform(0.15, 0.6)
    twist = rng.normal(0, 0.3)
    for i in range(nu + 1):
        t = i / nu
        half = W * 0.5 * math.sin(math.pi * min(max(t, 0.02), 0.98)) ** 0.8
        if lobes:
            half *= 1.0 + 0.22 * math.sin(t * math.pi * 7)
        for j in range(nv + 1):
            v = j / nv * 2 - 1
            x = (t - 0.5) * L
            y = v * half
            z = curl * (abs(y) ** 2) / max(W, 1e-3) * 2.2 + twist * y * (t - 0.5) + 0.002
            z += 0.25 * L * (t - 0.5) ** 2 * rng.uniform(0.0, 1.0)
            verts.append((x, y, z))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append([a, a + nv + 1, a + nv + 2, a + 1])
    return C.mesh_from_arrays(name, np.array(verts), faces, smooth=True, materials=[mat])


def build_library():
    ms = mat_straw_bits()
    ml = mat_dead_leaves()
    out = {}
    for cname, maker, mat, n in (("lib_straw_bits", straw_bit_mesh, ms, 10), ("lib_leaves_fallen", leaf_mesh, ml, 10)):
        col = V.lib_collection(cname)
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for i in range(n):
            rng = np.random.RandomState(4000 + 31 * i + len(cname))
            me = maker(rng, "%s_%d" % (cname, i), mat)
            ob = bpy.data.objects.new(me.name, me)
            col.objects.link(ob)
        out[cname] = n
    # road stones: clean / muddy stone colours instead of the mossy meadow rock
    st = bpy.data.materials.get("road_stone")
    if st is not None:
        for cname in ("lib_pebbles", "lib_gravel"):
            for o in bpy.data.collections[cname].objects:
                o.data.materials.clear()
                o.data.materials.append(st)
    V.exclude_library()
    return out


# ----------------------------------------------------------------------------
# masks on the ground meshes
# ----------------------------------------------------------------------------
def _get(me, name, n):
    a = np.zeros(n)
    if name in me.attributes:
        me.attributes[name].data.foreach_get("value", a)
    return a


def debris_masks(ob):
    me = ob.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    x, y = co[:, 0], co[:, 1]
    hoof = _get(me, "hoof", n)
    edgef = _get(me, "edgef", n)
    wet = _get(me, "wet", n)
    rut = _get(me, "rut", n)
    pathf = _get(me, "pathf", n)
    shore = _get(me, "shore", n)
    yard = 1.0 if ob.name.startswith("yard_901") else 0.0
    cl1 = smoothstep(0.0, 0.5, fbm(x / 0.8, y / 0.8, 3, 501))
    cl2 = smoothstep(0.05, 0.5, fbm(x / 1.6, y / 1.6, 3, 502))
    cl3 = smoothstep(0.2, 0.55, fbm(x / 2.5, y / 2.5, 2, 503))
    dry = 1 - np.clip(np.maximum(wet, shore) * 1.4, 0, 1)
    straw = (0.15 + 0.85 * np.maximum(hoof, yard * 0.8)) * cl1 * (0.5 + 0.5 * dry)
    leaves = (0.15 + 0.85 * edgef) * cl2 * (0.6 + 0.4 * dry)
    dung = hoof * cl3 * dry * (1 - np.clip(rut * 2, 0, 1))
    twig = (0.25 + 0.75 * edgef) * cl2 * dry
    for nm, arr in (("strawm", straw), ("leafm", leaves), ("dungm", dung), ("twigm", twig)):
        if nm in me.attributes:
            me.attributes.remove(me.attributes[nm])
        a = me.attributes.new(nm, 'FLOAT', 'POINT')
        a.data.foreach_set("value", np.clip(arr, 0, 1).astype(np.float32))
    return dict(n=n, straw=float(straw.mean()), leaves=float(leaves.mean()), dung=float(dung.mean()))


# ----------------------------------------------------------------------------
# scatter node group with power-law sizes, sinking and tumbling
# ----------------------------------------------------------------------------
def scatter_group2(name, surface, collection, density_attr, density, seed, smin, smax, power=1.0, sink=0.0,
                   mode='tumble', tilt=0.35, zflat=1.0, lift=0.0):
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
    na = nb.node('GeometryNodeInputNamedAttribute', data_type='FLOAT')
    na.inputs['Name'].default_value = density_attr
    dens = nb.math('MULTIPLY', nb.math('MAXIMUM', nb.out(na, 'Attribute'), 0.0), density)
    dist = nb.node('GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM')
    nb.links.new(nb.out(oi, 'Geometry'), dist.inputs['Mesh'])
    nb.set(dist, 'Density', dens)
    nb.set(dist, 'Seed', seed)
    rs = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rs, 'Min', 0.0)
    nb.set(rs, 'Max', 1.0)
    nb.set(rs, 'Seed', seed + 3)
    sc = nb.math('ADD', smin, nb.math('MULTIPLY', nb.math('POWER', nb.out(rs), power), smax - smin))
    pts = nb.out(dist, 'Points')
    if sink != 0.0 or lift != 0.0:
        sp = nb.node('GeometryNodeSetPosition')
        nb.links.new(pts, sp.inputs['Geometry'])
        nb.links.new(nb.comb(0.0, 0.0, nb.math('SUBTRACT', lift, nb.math('MULTIPLY', sc, sink))), sp.inputs['Offset'])
        pts = nb.out(sp)
    ci = nb.node('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
    ci.inputs['Collection'].default_value = collection
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    ri = nb.node('FunctionNodeRandomValue', data_type='INT')
    nb.set(ri, 'Min', 0)
    nb.set(ri, 'Max', max(len(collection.objects) - 1, 0))
    nb.set(ri, 'Seed', seed + 1)
    rz = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rz, 'Min', 0.0)
    nb.set(rz, 'Max', 6.2831)
    nb.set(rz, 'Seed', seed + 2)
    if mode == 'tumble':
        rx = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
        nb.set(rx, 'Min', -tilt)
        nb.set(rx, 'Max', tilt)
        nb.set(rx, 'Seed', seed + 5)
        ry = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
        nb.set(ry, 'Min', -tilt)
        nb.set(ry, 'Max', tilt)
        nb.set(ry, 'Seed', seed + 6)
        eul = nb.comb(nb.out(rx), nb.out(ry), nb.out(rz))
        e2r = nb.node('FunctionNodeEulerToRotation')
        nb.links.new(eul, e2r.inputs['Euler'])
        rot = nb.out(e2r)
    else:
        eul = nb.comb(0.0, 0.0, nb.out(rz))
        e2r = nb.node('FunctionNodeEulerToRotation')
        nb.links.new(eul, e2r.inputs['Euler'])
        rr = nb.node('FunctionNodeRotateRotation', rotation_space='LOCAL')
        nb.links.new(nb.out(dist, 'Rotation'), rr.inputs['Rotation'])
        nb.links.new(nb.out(e2r), rr.inputs['Rotate By'])
        rot = nb.out(rr)
    iop = nb.node('GeometryNodeInstanceOnPoints')
    nb.links.new(pts, iop.inputs['Points'])
    nb.links.new(nb.out(ci), iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    nb.links.new(nb.out(ri), iop.inputs['Instance Index'])
    nb.links.new(rot, iop.inputs['Rotation'])
    nb.links.new(nb.comb(sc, sc, nb.math('MULTIPLY', sc, zflat)), iop.inputs['Scale'])
    nb.links.new(nb.out(iop), gout.inputs[0])
    return ng


def make_scatter2(name, surface, collection_name, density_attr, density, seed, smin, smax, **kw):
    col = C.get_collection("Vegetation")
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name + "_empty")
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ng = scatter_group2("GN_" + name, surface, bpy.data.collections[collection_name], density_attr, density, seed, smin, smax, **kw)
    mod = ob.modifiers.new("scatter", 'NODES')
    mod.node_group = ng
    return ob


def clear_road_scatter():
    n = 0
    for o in list(bpy.data.objects):
        if o.name.startswith(("sc_r", "sc2_")):
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
            n += 1
    for ng in list(bpy.data.node_groups):
        if ng.name.startswith(("GN_sc_r", "GN_sc2_")) and ng.users == 0:
            bpy.data.node_groups.remove(ng)
    return n


def road_scatter_all():
    """(Re)create every scatter layer on every road, patch and yard mesh."""
    removed = clear_road_scatter()
    stats = {}
    for k, ob in enumerate(ground_objects()):
        rn = ob.name
        stats[rn] = debris_masks(ob)
        s = 100 + 37 * k
        stable = rn.startswith("yard_901")
        rut_road = rn.startswith(("road_main", "road_lane", "road_patch")) or stable
        # grass and weeds: verge and the grassy middle strip
        # pass 2b: more of it, more varied in size, and many more flat weeds (plantain, clover, dandelion
        # rosettes) so the crown and the verge read as trodden growth, not as spiky tufts planted in rows
        V.make_scatter("sc_rgrass_" + rn, ob, "lib_grass_road", "gmask", 60.0, s + 1, (0.5, 1.7))
        V.make_scatter("sc_rgrass2_" + rn, ob, "lib_grass_short", "gmask", 26.0, s + 2, (0.45, 1.0), density_power=1.6)
        V.make_scatter("sc_rweeds_" + rn, ob, "lib_weeds", "gmask", 6.5, s + 3, (0.4, 1.05), align_normal=True)
        # stones: many small, a few big, partly sunk and tilted
        # pass 2b: more grit (pass 2a had almost none left), still clumped by pebm and partly sunk
        make_scatter2("sc2_stone_" + rn, ob, "lib_pebbles", "pebm", 20.0, s + 4, 0.006, 0.065, power=2.6, sink=0.4, tilt=0.5, zflat=0.8)
        make_scatter2("sc2_gravel_" + rn, ob, "lib_gravel", "pebm", 150.0, s + 5, 0.003, 0.013, power=2.2, sink=0.35, tilt=0.6)
        # organic debris
        make_scatter2("sc2_straw_" + rn, ob, "lib_straw_bits", "strawm", 60.0 if stable else 30.0, s + 6, 0.7, 1.3, mode='align', lift=0.001)
        make_scatter2("sc2_leaf_" + rn, ob, "lib_leaves_fallen", "leafm", 7.0, s + 7, 0.7, 1.3, mode='align', lift=0.001)
        make_scatter2("sc2_twig_" + rn, ob, "lib_debris", "twigm", 1.2, s + 8, 0.5, 1.2, mode='align', lift=0.003)
        if rut_road:
            make_scatter2("sc2_dung_" + rn, ob, "lib_dung", "dungm", 0.35 if stable else 0.12, s + 9, 0.8, 1.25, mode='align', sink=0.012)
    return dict(removed=removed, stats=stats)
