"""Pass 2: the clearing as a working village, not a lawn.

Judges on pass 1 (from above): "an even dark-green lawn that looks mown, like a golf course, with no gardens,
fields, woodpiles or bare yards"; "the houses are tiny, spotless and few for the size of the clearing";
"uncut grass runs right up to the walls with no trodden ground at the door".
This module adds:
- four more cottages (instances of the pass-1 cottages, turned to face the roads) so the village has nine buildings;
- crofts (fenced vegetable plots) behind houses, a strip field (ridge and furrow) with barley, oats and plough;
- trodden ground: worn paths from every door to the road, bare earth at doors, along walls (drip line), at the well,
  the stable yard, the paddock gate and the field gate;
- grazed short turf in the paddock and on the green, tall hay grass and flowers elsewhere, in big patches;
- the terrain shader shows bare trodden soil, plough furrows and the field strips.
"""
import bpy
import numpy as np
import math
from mathutils import Vector, Euler
import common as C
from common import NB, smoothstep, fbm, perlin
import layout as L
import terrain as T
import vegetation as V
from materials import hexc

# new cottages: instances of pass-1 cottages (src) turned to face the roads
NEW_BUILDINGS = {
    "cottage_n1": dict(src="cottage_c", x=38.5, y=-2.5, rot=196.0, w=7.8, d=5.2, door=(0.2, -2.5)),
    "cottage_n2": dict(src="cottage_d", x=-3.0, y=-15.5, rot=171.0, w=5.6, d=4.4, door=(1.0, -2.0)),
    "cottage_n3": dict(src="cottage_b", x=-34.0, y=24.0, rot=-28.0, w=7.2, d=5.0, door=(0.0, -2.25)),
    "cottage_n4": dict(src="cottage_a", x=27.0, y=14.5, rot=12.0, w=8.6, d=5.4, door=(0.52, -2.6)),
}
DOORS = {
    "cottage_a": (0.52, -2.6), "cottage_b": (0.0, -2.25), "cottage_c": (0.2, -2.5), "cottage_d": (1.0, -2.0),
}

# crofts: fenced vegetable plots behind the houses (centre x, y, size w x d, rotation)
GARDENS2 = [
    dict(x=38.0, y=-9.0, w=6.5, d=4.0, rot=196.0, seed=961),
    dict(x=-2.4, y=-21.0, w=5.5, d=3.6, rot=171.0, seed=962),
    dict(x=23.4, y=-18.6, w=6.5, d=4.2, rot=184.0, seed=963),
    dict(x=-38.6, y=-27.6, w=5.2, d=3.8, rot=156.0, seed=964),
    dict(x=-36.6, y=29.4, w=5.6, d=3.8, rot=-28.0, seed=965),
]

# strip field (ridge and furrow): centre, size along / across the strips, rotation (deg) of the strip direction
FIELD = dict(x=15.0, y=-27.0, length=13.0, width=27.0, rot=8.0, strips=6, ridge=0.22)
STRIP_KIND = ["barley", "plough", "oats", "barley", "stubble", "oats"]


def bworld(b, lx, ly):
    c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
    return b["x"] + lx * c - ly * s, b["y"] + lx * s + ly * c


def all_buildings():
    out = dict(L.BUILDINGS)
    out.update(NEW_BUILDINGS)
    return out


def door_points():
    pts = []
    for name, b in L.BUILDINGS.items():
        if name in DOORS:
            pts.append(bworld(b, DOORS[name][0], DOORS[name][1] - 0.4))
    for name, b in NEW_BUILDINGS.items():
        pts.append(bworld(b, b["door"][0], b["door"][1] - 0.4))
    return pts


# paths worn into the grass (polylines, world xy). Pass-1 road meshes already serve doors A, B, C, D and the well.
def worn_paths():
    nb = NEW_BUILDINGS
    p = []
    d1 = bworld(nb["cottage_n1"], 0.2, -3.2)
    p.append([d1, (d1[0] - 0.5, d1[1] + 3.5), (d1[0] - 1.0, d1[1] + 7.2)])
    d2 = bworld(nb["cottage_n2"], 1.0, -2.6)
    p.append([d2, (d2[0] - 0.4, d2[1] + 4.5), (d2[0] - 1.5, d2[1] + 9.5), (d2[0] - 2.0, d2[1] + 12.3)])
    d3 = bworld(nb["cottage_n3"], 0.0, -2.9)
    p.append([d3, (-30.0, 18.0), (-26.0, 13.5), (-24.6, 9.0), (-23.6, 2.6)])
    d4 = bworld(nb["cottage_n4"], 0.52, -3.2)
    p.append([d4, (d4[0] + 0.5, d4[1] - 4.0), (d4[0] + 1.0, d4[1] - 8.0), (d4[0] + 0.6, d4[1] - 10.6)])
    # cottage A to cottage D across the green, past the well
    p.append([(-22.5, 2.2), (-15.0, 6.0), (-8.6, 8.4), (-8.4, 14.0), (-8.6, 20.0), (-8.9, 25.6)])
    # stable yard to the paddock gate and round the haystacks
    p.append([(14.5, 24.5), (17.0, 24.6), (19.5, 25.4), (20.5, 30.0), (21.5, 36.0)])
    # from the road down to the field
    p.append([(8.0, -3.6), (9.5, -9.0), (11.5, -15.0), (13.0, -20.5)])
    # behind cottage A to its garden and woodpile
    p.append([(-20.0, 4.5), (-19.5, 8.5), (-21.5, 10.5)])
    # round the back of cottage C to its croft
    p.append([(26.5, -10.0), (27.0, -14.0), (25.5, -16.4)])
    return p


def seg_dist(P, poly):
    poly = np.asarray(poly, dtype=np.float64)
    d, s = T._seg_dist(P, poly)
    return d, s


# ----------------------------------------------------------------------------
# cottages
# ----------------------------------------------------------------------------
def site_z(b):
    c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
    hw, hd = b["w"] / 2, b["d"] / 2
    zs = [float(L.height(b["x"] + c * lx - s * ly, b["y"] + s * lx + c * ly)) for lx, ly in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
    return float(np.mean(zs)) + 0.03


def clone_buildings():
    col = C.get_collection("Buildings")
    out = {}
    for name, b in NEW_BUILDINGS.items():
        src_col = bpy.data.collections["B_" + b["src"]]
        parent = bpy.data.objects[b["src"]]
        src_col.instance_offset = parent.location
        ob = bpy.data.objects.get(name)
        if ob is None:
            ob = bpy.data.objects.new(name, None)
            col.objects.link(ob)
        ob.instance_type = 'COLLECTION'
        ob.instance_collection = src_col
        ob.location = (b["x"], b["y"], site_z(b))
        ob.rotation_euler = (0.0, 0.0, math.radians(b["rot"] - L.BUILDINGS[b["src"]]["rot"]))
        out[name] = [round(v, 2) for v in ob.location]
    return out


def clear_trees_near(points_xy, radius):
    """Remove forest instances closer than radius to any of the given points (list of (x, y, r))."""
    removed = 0
    for ob in bpy.data.collections["Forest"].objects:
        me = ob.data
        n = len(me.vertices)
        if n == 0:
            continue
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        kill = np.zeros(n, bool)
        for (x, y, r) in points_xy:
            kill |= np.hypot(co[:, 0] - x, co[:, 1] - y) < r
        if kill.any():
            keep = ~kill
            attrs = {}
            for a in me.attributes:
                if a.domain == 'POINT' and a.data_type == 'FLOAT' and not a.name.startswith('.'):
                    v = np.zeros(n)
                    a.data.foreach_get("value", v)
                    attrs[a.name] = v[keep]
            new = bpy.data.meshes.new(me.name)
            new.vertices.add(int(keep.sum()))
            new.vertices.foreach_set("co", co[keep].astype(np.float32).ravel())
            for k, v in attrs.items():
                at = new.attributes.new(k, 'FLOAT', 'POINT')
                at.data.foreach_set("value", v.astype(np.float32))
            new.update()
            ob.data = new
            bpy.data.meshes.remove(me)
            removed += int(kill.sum())
    return removed


def lone_trees_to_oaks(max_beech=0.8, max_birch=0.99):
    """Second clean-up after looking at the aerial: lone beeches in the clearing (pale trunk, crown high up) and the
    remaining edge birches read as sticks from above; give them to the oak point clouds."""
    fol = bpy.data.collections["Forest"]
    oaks = [o for o in fol.objects if "oak" in o.name]
    rng = np.random.RandomState(5)
    moved = 0

    def get(me):
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        names = [a.name for a in me.attributes if a.domain == 'POINT' and a.data_type == 'FLOAT' and not a.name.startswith('.')]
        vals = {}
        for a in names:
            v = np.zeros(n)
            me.attributes[a].data.foreach_get("value", v)
            vals[a] = v
        return co, vals

    def put(ob, co, vals):
        old = ob.data
        new = bpy.data.meshes.new(old.name)
        new.vertices.add(len(co))
        new.vertices.foreach_set("co", co.astype(np.float32).ravel())
        for a, v in vals.items():
            at = new.attributes.new(a, 'FLOAT', 'POINT')
            at.data.foreach_set("value", v.astype(np.float32))
        new.update()
        ob.data = new
        bpy.data.meshes.remove(old)
    for ob in [o for o in fol.objects if ("beech" in o.name or "birch" in o.name)]:
        co, vals = get(ob.data)
        fm = L.forest_mask(co[:, 0], co[:, 1])
        sel = fm < (max_beech if "beech" in ob.name else max_birch)
        if not sel.any():
            continue
        for i in np.where(sel)[0]:
            tgt = oaks[rng.randint(len(oaks))]
            tco, tvals = get(tgt.data)
            tco = np.concatenate([tco, co[i:i + 1]])
            for a in tvals:
                tvals[a] = np.concatenate([tvals[a], [vals[a][i] if a in vals else 1.0]])
            put(tgt, tco, tvals)
            moved += 1
        keep = ~sel
        put(ob, co[keep], {a: v[keep] for a, v in vals.items()})
    return moved


def birches_to_broadleaf(max_forest=0.75):
    """Move birch instances that stand in or at the edge of the clearing to the oak / beech point clouds
    (the lone birches read as 'thin, sparse, planted saplings, stick props' from above)."""
    fol = bpy.data.collections["Forest"]
    b_obs = [o for o in fol.objects if "birch" in o.name]
    targets = [o for o in fol.objects if ("oak" in o.name or "beech" in o.name) and "snag" not in o.name]
    moved = 0
    rng = np.random.RandomState(77)
    for ob in b_obs:
        me = ob.data
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        fm = L.forest_mask(co[:, 0], co[:, 1])
        sel = fm < max_forest
        if not sel.any():
            continue
        names = [a.name for a in me.attributes if a.domain == 'POINT' and a.data_type == 'FLOAT' and not a.name.startswith('.')]
        vals = {}
        for a in names:
            v = np.zeros(n)
            me.attributes[a].data.foreach_get("value", v)
            vals[a] = v
        # append the selected points to random broadleaf clouds
        for i in np.where(sel)[0]:
            tgt = targets[rng.randint(len(targets))]
            tm = tgt.data
            m = len(tm.vertices)
            tco = np.zeros(m * 3)
            tm.vertices.foreach_get("co", tco)
            tvals = {}
            for a in names:
                v = np.zeros(m)
                if a in tm.attributes:
                    tm.attributes[a].data.foreach_get("value", v)
                tvals[a] = v
            new = bpy.data.meshes.new(tm.name)
            new.vertices.add(m + 1)
            allco = np.concatenate([tco.reshape(-1, 3), co[i:i + 1]])
            new.vertices.foreach_set("co", allco.astype(np.float32).ravel())
            for a in names:
                at = new.attributes.new(a, 'FLOAT', 'POINT')
                vv = np.concatenate([tvals[a], [vals[a][i] * (1.15 if a == "scale" else 1.0)]])
                at.data.foreach_set("value", vv.astype(np.float32))
            new.update()
            tgt.data = new
            bpy.data.meshes.remove(tm)
            moved += 1
        keep = ~sel
        new = bpy.data.meshes.new(me.name)
        new.vertices.add(int(keep.sum()))
        new.vertices.foreach_set("co", co[keep].astype(np.float32).ravel())
        for a in names:
            at = new.attributes.new(a, 'FLOAT', 'POINT')
            at.data.foreach_set("value", vals[a][keep].astype(np.float32))
        new.update()
        ob.data = new
        bpy.data.meshes.remove(me)
    return moved


# ----------------------------------------------------------------------------
# field: ridge and furrow worked into the terrain
# ----------------------------------------------------------------------------
def field_local(x, y):
    f = FIELD
    c, s = math.cos(math.radians(f["rot"])), math.sin(math.radians(f["rot"]))
    lx = (x - f["x"]) * c + (y - f["y"]) * s       # across the strips
    ly = -(x - f["x"]) * s + (y - f["y"]) * c      # along the strips
    return lx, ly


def field_masks(x, y):
    f = FIELD
    lx, ly = field_local(x, y)
    # slightly reversed-S strips, ragged ends
    bend = 0.9 * np.sin(ly / f["length"] * math.pi)
    lxb = lx + bend
    w = f["width"] / f["strips"]
    inside = (1 - smoothstep(f["width"] / 2 - 0.6, f["width"] / 2 + 0.2, np.abs(lxb))) * \
             (1 - smoothstep(f["length"] / 2 - 0.8 + 0.6 * fbm(x / 3.0, y / 3.0, 2, 991), f["length"] / 2 + 0.4, np.abs(ly)))
    k = np.clip(np.floor((lxb + f["width"] / 2) / w), 0, f["strips"] - 1)
    ph = (lxb + f["width"] / 2) / w - k              # 0..1 across one strip
    ridge = f["ridge"] * np.cos((ph - 0.5) * math.pi) ** 2 - f["ridge"] * 0.5
    return inside, k, ph, ridge, ly


def apply_field():
    """Raise ridges / lower furrows inside the field on the terrain mesh and store 'field' and 'strip'."""
    ter = bpy.data.objects["terrain"]
    me = ter.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if "field_dz" in me.attributes:
        old = np.zeros(n)
        me.attributes["field_dz"].data.foreach_get("value", old)
        co[:, 2] -= old
    inside, k, ph, ridge, ly = field_masks(co[:, 0], co[:, 1])
    dz = ridge * inside
    co[:, 2] += dz
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.update()
    for nm, arr in (("field_dz", dz), ("field", inside), ("strip", (k + 0.5) / FIELD["strips"]), ("furrow", np.abs(ph - 0.5) * 2)):
        if nm in me.attributes:
            me.attributes.remove(me.attributes[nm])
        a = me.attributes.new(nm, 'FLOAT', 'POINT')
        a.data.foreach_set("value", np.asarray(arr, dtype=np.float32))
    T._BVH.clear()
    return dict(field_verts=int((inside > 0.5).sum()))


# ----------------------------------------------------------------------------
# masks for scattering and shading
# ----------------------------------------------------------------------------
def _attr(me, name, n):
    a = np.zeros(n)
    if name in me.attributes:
        me.attributes[name].data.foreach_get("value", a)
    return a


def _set(me, name, arr):
    if name in me.attributes:
        me.attributes.remove(me.attributes[name])
    a = me.attributes.new(name, 'FLOAT', 'POINT')
    a.data.foreach_set("value", np.clip(np.asarray(arr), 0, 1).astype(np.float32))


def rect_dist(x, y, b, pad=0.0):
    c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
    lx = (x - b["x"]) * c + (y - b["y"]) * s
    ly = -(x - b["x"]) * s + (y - b["y"]) * c
    dx = np.maximum(np.abs(lx) - b["w"] / 2 - pad, 0)
    dy = np.maximum(np.abs(ly) - b["d"] / 2 - pad, 0)
    inside = (np.abs(lx) < b["w"] / 2 + pad) & (np.abs(ly) < b["d"] / 2 + pad)
    return np.sqrt(dx * dx + dy * dy), inside, lx, ly


def masks2():
    ter = bpy.data.objects["terrain"]
    me = ter.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    x, y = co[:, 0], co[:, 1]
    forest = _attr(me, "forest", n)
    edge_t = _attr(me, "edge_t", n)
    grass0 = _attr(me, "grass", n)
    field = _attr(me, "field", n)
    strip = _attr(me, "strip", n)
    rv = np.hypot(x - L.VILLAGE_C[0], y - L.VILLAGE_C[1])
    # buildings, old and new, and the crofts
    built = np.zeros(n)
    near_b = np.zeros(n)
    trampled = np.zeros(n)
    drip = np.zeros(n)
    for name, b in all_buildings().items():
        d, inside, lx, ly = rect_dist(x, y, b, 0.15)
        built = np.maximum(built, inside.astype(float))
        near_b = np.maximum(near_b, np.where(inside, 0, 1 - smoothstep(0.2, 1.6, d)))
        # drip line under the eaves (bare, gravelly) and a trodden band all round the walls
        drip = np.maximum(drip, np.exp(-((d - 0.55) / 0.22) ** 2) * (~inside))
        rag = 0.5 + 0.5 * fbm(x / 1.1, y / 1.1, 2, 931)
        trampled = np.maximum(trampled, (1 - smoothstep(0.3, 1.0 + 1.2 * rag, d)) * 0.75 * (~inside))
        # the front yard: a worn, grazed apron of 4 m in front of the house (not for the stable: it has its yard)
        if name != "stable":
            fy = -ly - b["d"] / 2
            front = smoothstep(-0.2, 0.4, fy) * (1 - smoothstep(2.5 + 1.5 * rag, 4.5 + 1.5 * rag, fy)) * (1 - smoothstep(b["w"] / 2 - 0.5, b["w"] / 2 + 1.5, np.abs(lx)))
            trampled = np.maximum(trampled, front * (0.5 + 0.4 * rag) * (~inside))
    for g in L.GARDENS + GARDENS2:
        b = dict(x=g["x"], y=g["y"], w=g["w"] + 0.8, d=g["d"] + 0.8, rot=g["rot"])
        d, inside, _, _ = rect_dist(x, y, b, 0.1)
        built = np.maximum(built, inside.astype(float))
        trampled = np.maximum(trampled, (1 - smoothstep(0.0, 0.9, d)) * 0.5 * (~inside))
    # doors: bare earth fans
    for (dx_, dy_) in door_points():
        dd = np.hypot(x - dx_, y - dy_)
        rag = 0.6 + 0.4 * fbm(x / 0.8, y / 0.8, 2, 932)
        trampled = np.maximum(trampled, 1 - smoothstep(0.8 * rag, 3.0 * rag, dd))
    # worn paths
    ragp = 0.5 + 0.5 * fbm(x / 0.9, y / 0.9, 3, 933)
    for poly in worn_paths():
        poly = np.asarray(poly, float)
        bb = (x > poly[:, 0].min() - 3) & (x < poly[:, 0].max() + 3) & (y > poly[:, 1].min() - 3) & (y < poly[:, 1].max() + 3)
        if not bb.any():
            continue
        dpath, _ = seg_dist(np.stack([x[bb], y[bb]], 1), poly)
        w = 0.32 + 0.18 * ragp[bb]
        t = (1 - smoothstep(w * 0.6, w * 1.9, dpath)) * (0.7 + 0.3 * ragp[bb])
        trampled[bb] = np.maximum(trampled[bb], t)
    # well, stable surroundings, paddock gate, haystacks
    for (cx, cy, r) in ((-6.8, 7.8, 3.6), (8.5, 24.0, 10.5), (19.0, 25.5, 3.0), (20.0, 38.6, 2.8), (25.4, 39.8, 2.5), (29.3, 37.2, 2.4), (12.5, -20.0, 2.5)):
        dd = np.hypot(x - cx, y - cy)
        rag = 0.6 + 0.4 * fbm(x / 1.2, y / 1.2, 2, 934)
        trampled = np.maximum(trampled, (1 - smoothstep(r * 0.55 * rag, r * rag, dd)) * 0.85)
    trampled = trampled * (1 - built) * (1 - smoothstep(0.3, 0.7, forest))
    drip = drip * (1 - built)
    # grazing: the paddock and the green are short turf with bare patches
    paddock = ((x > 15.5) & (x < 32.5) & (y > 23.5) & (y < 42.5)).astype(float)
    green = 1 - smoothstep(6.0, 11.0, np.hypot(x - (-5.0), y - 10.0))
    grazed = np.maximum(paddock, green * 0.85)
    grazed = np.maximum(grazed, (1 - smoothstep(4.0, 9.0, np.hypot(x - 0.0, y - (-12.0)))) * 0.6)
    # hay meadow / short pasture in big patches
    big = smoothstep(-0.2, 0.3, fbm(x / 16.0, y / 16.0, 3, 935))
    hay = big * (1 - grazed)
    meadow = grass0 * (1 - smoothstep(0.35, 0.8, forest)) * (1 - built) * (1 - field)
    patch = smoothstep(-0.25, 0.45, fbm(x / 7.0, y / 7.0, 3, 81))
    patch2 = smoothstep(-0.2, 0.5, fbm(x / 4.0, y / 4.0, 2, 82))
    ragged = 0.5 + 0.5 * fbm(x / 1.3, y / 1.3, 3, 87)
    edge_ramp = smoothstep(0.05, 0.25 + 1.1 * ragged, edge_t)
    roadside = smoothstep(0.0, 0.3, edge_t) * (1 - smoothstep(0.8, 2.6, edge_t))
    verge = smoothstep(-0.1, 0.15, edge_t) * (1 - smoothstep(0.5, 1.4 + ragged, edge_t)) * (1 - built)
    fringe = smoothstep(0.15, 0.5, forest) * (1 - smoothstep(0.6, 0.95, forest))
    deep = smoothstep(0.5, 1.0, forest) * (1 - smoothstep(55.0, 110.0, rv))
    bare = smoothstep(0.35, 0.8, trampled)
    tall_ok = (1 - bare) * (1 - smoothstep(0.1, 0.5, trampled))
    short_k = (1 - 0.85 * bare)
    m = {
        "d_short": meadow * (0.45 + 0.55 * (1 - patch)) * edge_ramp * short_k * (1 + 0.6 * grazed) * (1 - 0.5 * hay) + 0.5 * grazed * meadow * short_k,
        "d_tall": (meadow * (0.1 + 0.9 * patch) * (1 - 0.8 * roadside) * edge_ramp * (0.25 + 0.75 * hay) + 0.6 * grass0 * fringe) * tall_ok * (1 - 0.92 * grazed),
        "d_verge": verge * (1 - forest) * (1 - 0.7 * bare),
        "d_dry": (meadow * (0.25 + 0.75 * patch2) * 0.8 * (0.2 + 0.8 * hay) + 0.5 * roadside * grass0) * (1 - 0.85 * grazed) * tall_ok,
        "d_weeds": grass0 * (0.25 + 0.75 * roadside) * (1 - forest) * (1 - built) * (1 - 0.6 * bare) + 0.6 * drip + 0.5 * grazed * meadow * patch2,
        "d_flowers": meadow * smoothstep(-0.1, 0.5, fbm(x / 11.0, y / 11.0, 2, 83)) * (1 - roadside * 0.7) * (0.3 + 0.7 * hay) * tall_ok,
        "d_nettles": near_b * (1 - built) * smoothstep(0.3, 0.9, edge_t) * smoothstep(-0.2, 0.4, fbm(x / 3.0, y / 3.0, 2, 84)) * (1 - bare) * (1 - drip),
        "d_ferns": smoothstep(0.35, 0.9, forest) * (1 - smoothstep(60.0, 120.0, rv)) * smoothstep(1.0, 3.0, edge_t) * smoothstep(-0.3, 0.3, fbm(x / 6.0, y / 6.0, 2, 85)),
        "d_rocks": (smoothstep(0.2, 0.8, forest) * 0.6 + roadside * 0.4) * smoothstep(0.35, 0.6, fbm(x / 9.0, y / 9.0, 2, 86)) * (1 - built) * (1 - field),
        "d_forestgrass": fringe * smoothstep(0.5, 2.0, edge_t) + deep * 0.08 * smoothstep(0.5, 2.0, edge_t),
        "d_trodden": bare * (0.25 + 0.75 * smoothstep(-0.1, 0.4, fbm(x / 0.7, y / 0.7, 2, 936))),
    }
    # field crops by strip
    kinds = {kd: np.zeros(n) for kd in ("barley", "oats", "stubble", "plough")}
    sidx = np.clip(np.floor(strip * FIELD["strips"]), 0, FIELD["strips"] - 1).astype(int)
    for i, kd in enumerate(STRIP_KIND):
        kinds[kd] = np.maximum(kinds[kd], (sidx == i) * field)
    m["d_barley"] = kinds["barley"] * (1 - 0.3 * smoothstep(0.2, 0.6, fbm(x / 2.0, y / 2.0, 2, 937)))
    m["d_oats"] = kinds["oats"] * (1 - 0.3 * smoothstep(0.2, 0.6, fbm(x / 2.0, y / 2.0, 2, 938)))
    m["d_stubble"] = kinds["stubble"]
    for k, v in m.items():
        _set(me, k, v)
    _set(me, "trampled", trampled)
    _set(me, "drip", drip)
    _set(me, "built2", built)
    _set(me, "grazed", grazed)
    _set(me, "plough", kinds["plough"])
    _set(me, "fieldcrop", kinds["barley"] + kinds["oats"] + kinds["stubble"])
    return {k: round(float(np.mean(v)), 4) for k, v in m.items()}


# ----------------------------------------------------------------------------
# terrain shader: bare trodden soil, drip-line gravel, plough furrows, field strips
# ----------------------------------------------------------------------------
def mat_terrain2():
    m = C.new_material("terrain_ground")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    forest = nb.attr('forest')
    roadedge = nb.attr('roadedge')
    mvar = nb.attr('mvar')
    trampled = nb.attr('trampled')
    drip = nb.attr('drip')
    plough = nb.attr('plough')
    crop = nb.attr('fieldcrop')
    furrow = nb.attr('furrow')
    grazed = nb.attr('grazed')
    n1 = nb.noise(obj, scale=0.12, detail=4, rough=0.6)
    n2 = nb.noise(obj, scale=1.3, detail=5, rough=0.6)
    n3 = nb.noise(obj, scale=9.0, detail=3, rough=0.6)
    meadow = nb.ramp(n2, [(0.3, hexc('2f3518')), (0.5, hexc('4a4a22')), (0.7, hexc('5d5232'))])
    meadow = nb.mix(nb.maprange(mvar, 0.2, 0.8, 0.0, 0.5), meadow, hexc('3e4a1c'))
    # thatch of dead grass under the living grass
    dead = nb.maprange(nb.noise(obj, scale=3.5, detail=4), 0.45, 0.7, 0.0, 0.5)
    meadow = nb.mix(dead, meadow, hexc('6b6040'))
    leaf = nb.voronoi(obj, scale=22.0, feature='F1', which='Color')
    leafc = nb.ramp(nb.noise(leaf, scale=2.0, detail=0), [(0.25, hexc('4a2e17')), (0.45, hexc('6e4a26')), (0.62, hexc('8a5c2a')), (0.8, hexc('3a2a1a'))])
    litter = nb.mix(nb.maprange(n3, 0.3, 0.7, 0.0, 0.6), leafc, hexc('2c2216'))
    moss = nb.maprange(n1, 0.55, 0.7, 0.0, 0.7)
    litter = nb.mix(moss, litter, hexc('3d4a1a'))
    base = nb.mix(nb.maprange(forest, 0.15, 0.85), meadow, litter)
    # damp trodden soil: near roads, doors, paths, the well, yards
    soil = nb.ramp(n2, [(0.3, hexc('3e3124')), (0.55, hexc('55432f')), (0.8, hexc('66523a'))])
    soil = nb.mix(nb.maprange(n3, 0.4, 0.7, 0.0, 0.4), soil, hexc('2c241a'))
    bare = nb.math('MINIMUM', nb.math('ADD', nb.math('MULTIPLY', nb.math('POWER', roadedge, 1.4), 0.75), nb.maprange(trampled, 0.15, 0.85, 0.0, 0.95)), 1.0)
    rag = nb.maprange(nb.noise(obj, scale=2.0, detail=5, rough=0.65), 0.3, 0.7, -0.25, 0.25)
    bare = nb.math('MINIMUM', nb.math('MAXIMUM', nb.math('ADD', bare, nb.math('MULTIPLY', rag, bare)), 0.0), 1.0)
    base = nb.mix(bare, base, soil)
    # drip line: washed gravel and dark wet soil under the eaves
    grav = nb.voronoi(obj, scale=60.0, feature='F1', which='Color')
    gravc = nb.ramp(nb.noise(grav, scale=3.0, detail=0), [(0.3, hexc('5b564c')), (0.6, hexc('7a7262')), (0.85, hexc('3e3a33'))])
    base = nb.mix(nb.math('MULTIPLY', drip, 0.8), base, nb.mix(nb.maprange(nb.noise(obj, scale=20.0), 0.4, 0.6), hexc('2e261d'), gravc))
    # grazed turf: greener, a few bare scuffs
    scuff = nb.math('MULTIPLY', grazed, nb.maprange(nb.noise(obj, scale=0.7, detail=3), 0.6, 0.68, 0.0, 0.8))
    base = nb.mix(scuff, base, soil)
    # field: ploughed strips show furrows of turned clods; crop strips show soil between the plants
    clods = nb.voronoi(obj, scale=9.0, feature='SMOOTH_F1', which='Distance', smooth=0.3)
    pl_col = nb.ramp(nb.maprange(clods, 0.0, 0.6), [(0.0, hexc('6b5440')), (0.5, hexc('4b3b2b')), (1.0, hexc('2e241a'))])
    pl_col = nb.mix(nb.maprange(furrow, 0.6, 1.0, 0.0, 0.5), pl_col, hexc('2a2118'))
    base = nb.mix(plough, base, pl_col)
    base = nb.mix(nb.math('MULTIPLY', crop, 0.85), base, nb.mix(nb.maprange(n3, 0.3, 0.7), hexc('4a3c2c'), hexc('5d4a34')))
    h = nb.math('ADD', nb.math('MULTIPLY', n3, 0.5), nb.math('MULTIPLY', nb.voronoi(obj, scale=22.0, feature='DISTANCE_TO_EDGE'), 0.6))
    h = nb.math('ADD', h, nb.math('MULTIPLY', nb.maprange(clods, 0.0, 0.6, 1.0, 0.0), nb.math('MULTIPLY', plough, 1.5)))
    bump = nb.bump(h, strength=0.4, distance=0.02)
    rough = nb.mix(bare, 0.9, 0.8, dtype='FLOAT')
    bsdf = nb.principled(Base_Color=base, Roughness=rough, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.35)
    nb.output(bsdf)
    return m


# ----------------------------------------------------------------------------
# crops
# ----------------------------------------------------------------------------
def build_crop_library():
    import plants as PL
    from plants import lin
    mats = bpy.data.materials
    gm = mats["grass_blades"]
    out = {}
    specs = {
        "lib_barley": dict(n=34, h=(0.5, 0.72), r=0.07, green=(lin((0.30, 0.30, 0.10)), lin((0.72, 0.62, 0.32))), dry=0.55, seed=10, lean=0.25),
        "lib_oats": dict(n=30, h=(0.45, 0.65), r=0.07, green=(lin((0.12, 0.2, 0.05)), lin((0.42, 0.5, 0.2))), dry=0.12, seed=8, lean=0.3),
        "lib_stubble": dict(n=40, h=(0.06, 0.12), r=0.08, green=(lin((0.4, 0.36, 0.2)), lin((0.72, 0.64, 0.4))), dry=0.85, seed=0, lean=0.15),
    }
    for cname, sp in specs.items():
        col = V.lib_collection(cname)
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for i in range(4):
            rng = np.random.RandomState(5100 + 13 * i + len(cname))
            geo = PL.grass_clump(rng, sp["n"], sp["h"], sp["r"], dry=sp["dry"], green=sp["green"], seedheads=sp["seed"], lean_max=sp["lean"])
            V.geo_to_object("%s_%d" % (cname, i), geo, col, [gm])
        out[cname] = 4
    V.exclude_library()
    return out


def scatter_terrain2():
    ter = bpy.data.objects["terrain"]
    V.make_scatter("sc_grass_short", ter, "lib_grass_short", "d_short", 40.0, 11, (0.75, 1.35))
    V.make_scatter("sc_grass_tall", ter, "lib_grass_tall", "d_tall", 20.0, 21, (0.7, 1.35))
    V.make_scatter("sc_grass_dry", ter, "lib_grass_dry", "d_dry", 14.0, 31, (0.7, 1.3))
    V.make_scatter("sc_verge", ter, "lib_grass_road", "d_verge", 30.0, 33, (0.8, 1.7))
    V.make_scatter("sc_weeds", ter, "lib_weeds", "d_weeds", 1.8, 41, (0.7, 1.3), align_normal=True)
    V.make_scatter("sc_flowers", ter, "lib_flowers", "d_flowers", 1.4, 51, (0.8, 1.2))
    V.make_scatter("sc_nettles", ter, "lib_nettles", "d_nettles", 2.0, 61, (0.7, 1.2))
    V.make_scatter("sc_trodden", ter, "lib_grass_road", "d_trodden", 6.0, 63, (0.6, 1.1))
    V.make_scatter("sc_barley", ter, "lib_barley", "d_barley", 70.0, 65, (0.85, 1.15))
    V.make_scatter("sc_oats", ter, "lib_oats", "d_oats", 70.0, 66, (0.85, 1.15))
    V.make_scatter("sc_stubble", ter, "lib_stubble", "d_stubble", 45.0, 67, (0.8, 1.2))
    return True
