"""Forest placement: trees and bushes as instanced point clouds (one point object per variant)."""
import bpy
import numpy as np
import math
import common as C
from common import NB, smoothstep, fbm
import layout as L
import terrain as T


def instance_group():
    name = "GN_instance_points"
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Object', in_out='INPUT', socket_type='NodeSocketObject')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nb = NB(ng)
    gin = nb.node('NodeGroupInput')
    gout = nb.node('NodeGroupOutput')
    oi = nb.node('GeometryNodeObjectInfo', transform_space='ORIGINAL')
    nb.links.new(gin.outputs[1], oi.inputs['Object'])
    oi.inputs['As Instance'].default_value = True
    m2p = nb.node('GeometryNodeMeshToPoints')
    nb.links.new(gin.outputs[0], m2p.inputs['Mesh'])
    def named(n):
        a = nb.node('GeometryNodeInputNamedAttribute', data_type='FLOAT')
        a.inputs['Name'].default_value = n
        return nb.out(a, 'Attribute')
    eul = nb.node('ShaderNodeCombineXYZ')
    nb.set(eul, 'X', named('rx'))
    nb.set(eul, 'Y', named('ry'))
    nb.set(eul, 'Z', named('rz'))
    e2r = nb.node('FunctionNodeEulerToRotation')
    nb.links.new(nb.out(eul), e2r.inputs['Euler'])
    iop = nb.node('GeometryNodeInstanceOnPoints')
    nb.links.new(nb.out(m2p), iop.inputs['Points'])
    nb.links.new(nb.out(oi, 'Geometry'), iop.inputs['Instance'])
    nb.links.new(nb.out(e2r), iop.inputs['Rotation'])
    nb.set(iop, 'Scale', named('scale'))
    nb.links.new(nb.out(iop), gout.inputs[0])
    return ng


def make_points_object(name, pts, scales, rots, col, src_obj, tilt=0.03, rng=None):
    rng = rng or np.random.RandomState(len(name))
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 3)
    me = bpy.data.meshes.get(name + "_pts")
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name + "_pts")
    me.vertices.add(len(pts))
    me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
    me.update()
    n = len(pts)
    for an, vals in (("scale", scales), ("rz", rots), ("rx", rng.normal(0, tilt, n)), ("ry", rng.normal(0, tilt, n))):
        a = me.attributes.new(an, 'FLOAT', 'POINT')
        a.data.foreach_set("value", np.asarray(vals, dtype=np.float32))
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    mod = ob.modifiers.new("inst", 'NODES')
    mod.node_group = instance_group()
    C.set_mod_input(mod, "Object", src_obj)
    return ob


def road_clearance(x, y):
    """Signed distance from road edges (m, + outside) for arrays x, y (coarse, centre-line based)."""
    d = np.full(x.shape, 99.0)
    for name, rc in L.road_curves().items():
        ss = np.arange(0, rc.length, 0.5)
        cx, cy, _, _ = rc.at(ss)
        el, er = rc.edges(ss)
        E = np.maximum(el, er)
        # brute force in chunks
        P = np.stack([x, y], 1)
        for k0 in range(0, len(P), 20000):
            Pc = P[k0:k0 + 20000]
            dx = Pc[:, 0:1] - cx[None, :]
            dy = Pc[:, 1:2] - cy[None, :]
            dist = np.sqrt(dx * dx + dy * dy) - E[None, :]
            d[k0:k0 + 20000] = np.minimum(d[k0:k0 + 20000], dist.min(1))
    for yd in L.YARDS:
        t, _, _ = T.yard_signed_dist(yd, x, y)
        d = np.minimum(d, t)
    return d


def building_clearance(x, y):
    d = np.full(x.shape, 99.0)
    for bname, b in L.BUILDINGS.items():
        c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
        lx = (x - b["x"]) * c + (y - b["y"]) * s
        ly = -(x - b["x"]) * s + (y - b["y"]) * c
        dx = np.maximum(np.abs(lx) - b["w"] / 2, 0)
        dy = np.maximum(np.abs(ly) - b["d"] / 2, 0)
        d = np.minimum(d, np.sqrt(dx * dx + dy * dy))
    # paddock east of the stable and haystack area kept open
    for (x0, x1, y0, y1) in L.OPEN_AREAS:
        inside = (x > x0) & (x < x1) & (y > y0) & (y < y1)
        d = np.where(inside, 0.0, d)
    return d


def jitter_grid(rng, cell, lo=-178, hi=178):
    xs = np.arange(lo, hi, cell)
    X, Y = np.meshgrid(xs, xs)
    X = X.ravel() + rng.uniform(0, cell, X.size)
    Y = Y.ravel() + rng.uniform(0, cell, Y.size)
    return X, Y


def build_forest():
    col = C.get_collection("Forest")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    rng = np.random.RandomState(2024)
    lib_b = [o for o in bpy.data.collections["lib_trees_broad"].objects]
    lib_c = [o for o in bpy.data.collections["lib_trees_conifer"].objects]
    lib_h = [o for o in bpy.data.collections["lib_bushes"].objects]
    lib_s = [o for o in bpy.data.collections["lib_snags"].objects]
    oaks = [o for o in lib_b if "oak" in o.name]
    beeches = [o for o in lib_b if "beech" in o.name]
    birches = [o for o in lib_b if "birch" in o.name]
    spruces_big = [o for o in lib_c if o.name.split("_")[-1] in ("51", "52", "53")]
    spruce_small = [o for o in lib_c if o.name.endswith("54")]
    placements = {o.name: [] for o in lib_b + lib_c + lib_h + lib_s}

    # ---- canopy trees
    X, Y = jitter_grid(rng, 4.6)
    forest = L.forest_mask(X, Y)
    keep = forest > 0.25
    X, Y, forest = X[keep], Y[keep], forest[keep]
    rcl = road_clearance(X, Y)
    bcl = building_clearance(X, Y)
    p = smoothstep(0.3, 0.8, forest) * 0.92
    ok = (rng.uniform(size=len(X)) < p) & (rcl > 1.2) & (bcl > 6.0)
    X, Y, forest, rcl = X[ok], Y[ok], forest[ok], rcl[ok]
    conif = smoothstep(-0.25, 0.35, fbm(X / 70.0, Y / 70.0, 2, 301))
    edge = 1 - smoothstep(0.55, 0.95, forest)
    for i in range(len(X)):
        u = rng.uniform()
        if u < conif[i] * (1 - 0.5 * edge[i]):
            src = spruces_big[rng.randint(len(spruces_big))]
            sc = rng.uniform(0.8, 1.2)
        else:
            if edge[i] > 0.3 and rng.uniform() < 0.35:
                src = birches[rng.randint(len(birches))]
            elif rng.uniform() < 0.5:
                src = oaks[rng.randint(len(oaks))]
            else:
                src = beeches[rng.randint(len(beeches))]
            sc = rng.uniform(0.8, 1.2)
        if rng.uniform() < 0.012:
            src = lib_s[0]
            sc = rng.uniform(0.8, 1.1)
        placements[src.name].append((X[i], Y[i], sc))

    # ---- understory: hazel bushes and young spruce, dense along the clearing edge and forest roads
    X, Y = jitter_grid(rng, 3.2)
    forest = L.forest_mask(X, Y)
    keep = forest > 0.12
    X, Y, forest = X[keep], Y[keep], forest[keep]
    rcl = road_clearance(X, Y)
    bcl = building_clearance(X, Y)
    edge_band = smoothstep(0.12, 0.4, forest) * (1 - smoothstep(0.75, 1.0, forest))
    roadband = smoothstep(0.6, 1.5, rcl) * (1 - smoothstep(3.0, 6.0, rcl))
    p = 0.55 * edge_band + 0.35 * roadband * (forest > 0.5) + 0.06
    ok = (rng.uniform(size=len(X)) < p) & (rcl > 0.6) & (bcl > 4.0)
    for x, y in zip(X[ok], Y[ok]):
        if rng.uniform() < 0.68:
            src = lib_h[rng.randint(len(lib_h))]
            sc = rng.uniform(0.7, 1.3)
        else:
            src = spruce_small[0]
            sc = rng.uniform(0.12, 0.45)
        placements[src.name].append((x, y, sc))

    # ---- a few trees inside the village
    village_trees = [
        (oaks[0], -2.5, 13.0, 1.15),    # old oak on the green by the well
        (birches[0], 31.0, -6.5, 0.9),  # birch beside cottage C
        (beeches[0], 9.5, 42.5, 0.95),  # beech behind the stable
        (birches[1], -33.0, 13.0, 0.8),
        (oaks[1], -46.0, -6.0, 1.0),
        (lib_h[0], -18.5, 9.5, 0.9),     # hazel at cottage A's corner
        (lib_h[1], 15.5, 36.5, 1.0),     # hazel behind the stable
        (lib_h[2], -15.5, 32.0, 0.9),
    ]
    for src, x, y, sc in village_trees:
        placements[src.name].append((x, y, sc))
    counts = {}
    for nm, lst in placements.items():
        if not lst:
            continue
        arr = np.array(lst)
        z = L.height(arr[:, 0], arr[:, 1]) - 0.08
        pts = np.stack([arr[:, 0], arr[:, 1], z], 1)
        rots = rng.uniform(0, 2 * math.pi, len(arr))
        src = bpy.data.objects[nm]
        make_points_object("forest_" + nm, pts, arr[:, 2], rots, col, src, tilt=0.025 if "spruce" in nm else 0.04, rng=rng)
        counts[nm] = len(arr)
    return counts
