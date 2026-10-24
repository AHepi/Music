"""Pass 2 props: crofts and household clutter for the new cottages, new haystacks.

Judges on pass 1: "three hay mounds are smooth egg-shaped blobs", "the haystack is a smooth dome blob",
"the props are too small to read" from above.
"""
import bpy
import numpy as np
import math
from mathutils import Euler, Vector
import common as C
import layout as L
import terrain as T
import props as PR
import village_props as VP
from bparts import Parts, Strands, straw_colour
import terrain2 as T2


def clone_prop(src, name, x, y, rot, col=None, sink=0.0):
    """Linked copy of a placed prop (parent empty + children sharing their meshes)."""
    p = bpy.data.objects[src]
    col = col or p.users_collection[0]
    old = bpy.data.objects.get(name)
    if old is not None:
        for ch in list(old.children):
            bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(old, do_unlink=True)
    newp = p.copy()
    newp.name = name
    col.objects.link(newp)
    for ch in p.children:
        c2 = ch.copy()
        c2.name = name + "_" + ch.name.split("_")[-1]
        col.objects.link(c2)
        c2.parent = newp
        c2.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
    z = T.ground_z(x, y)
    newp.location = (x, y, z - sink)
    newp.rotation_euler = (0.0, 0.0, math.radians(rot))
    return newp


def new_cottage_props():
    col = C.get_collection("Props")
    out = []
    plan = {
        "cottage_n1": [("woodpile_b", 4.6, 0.3, 90.0), ("butt_a", -4.2, -2.9, 0.0), ("chopping_b", 5.2, -2.6, 25.0), ("crates_c", -2.2, -3.4, 0.0)],
        "cottage_n2": [("woodpile_b", -3.9, 0.4, 90.0), ("pots_d", 1.9, -2.6, 0.0), ("chopping_a", -3.6, -2.7, 60.0)],
        "cottage_n3": [("woodpile_a", -4.9, 0.4, 90.0), ("butt_b", -3.8, -2.7, 0.0), ("bench_b", 1.6, -2.9, 0.0), ("skeps_a", -1.5, 4.6, 180.0)],
        "cottage_n4": [("woodpile_b", 5.2, 0.4, 90.0), ("butt_a", -4.75, -3.05, 0.0), ("barrels_c", 3.0, -3.3, 0.0), ("chopping_b", 6.0, -2.4, 10.0)],
    }
    for bname, items in plan.items():
        b = T2.NEW_BUILDINGS[bname]
        for k, (src, lx, ly, r) in enumerate(items):
            if bpy.data.objects.get(src) is None:
                continue
            x, y = T2.bworld(b, lx, ly)
            out.append(clone_prop(src, "%s_%s_%d" % (bname, src, k), x, y, b["rot"] + r, col).name)
    return out


def gardens2(mats):
    col = C.get_collection("Props")
    pl = VP.Placer(col, mats)
    rng = np.random.RandomState(4343)
    for g in T2.GARDENS2:
        for nm in ("garden_soil_%d" % g["seed"], "garden_plants_%d" % g["seed"]):
            o = bpy.data.objects.get(nm)
            if o is not None:
                bpy.data.objects.remove(o, do_unlink=True)
        for o in list(bpy.data.objects):
            if o.name.startswith("wattle_garden_%d" % g["seed"]):
                bpy.data.objects.remove(o, do_unlink=True)
        VP.garden_patch(pl, g, rng)
    return len(T2.GARDENS2)


# ----------------------------------------------------------------------------
# haystacks
# ----------------------------------------------------------------------------
def haystack2(P, st, H=3.2, R=1.7, lean=0.04, cut=0.0, seed=0):
    """Rick of loose hay round a pole: a straight-sided, bulging body, an overhanging shoulder and a combed,
    weathered cap; lumpy tufts all over, a used side cut back flat (cut>0), ropes over the top weighted with stones,
    loose hay trodden round the foot."""
    rng = np.random.RandomState(seed)
    nz, na = 64, 112
    verts = []
    zs = np.linspace(0, 1, nz + 1)
    ang = np.linspace(0, 2 * math.pi, na, endpoint=False)
    shoulder = rng.uniform(0.44, 0.52)
    # pass 2b: a straighter, pointed cap and a slumped, clumpy body (pass 2a still read as smooth eggs from above)
    for i, t in enumerate(zs):
        if t < shoulder:
            u = t / shoulder
            prof = R * (0.84 + 0.16 * math.sin(u * math.pi * 0.85)) * (1.0 + 0.05 * u)
        else:
            u = (t - shoulder) / (1 - shoulder)
            prof = R * 1.07 * (1 - u) ** 0.88 * (1.0 + 0.1 * math.sin(u * math.pi))
        for j, a in enumerate(ang):
            ca, sa = math.cos(a), math.sin(a)
            n1 = float(C.fbm(ca * 1.2 + t * 1.6, sa * 1.2 + seed * 0.37, 3, seed + 11))
            n2 = float(C.fbm(ca * 4.0 + t * 6.5, sa * 4.0 - seed * 0.11, 3, seed + 12))
            n3 = float(C.perlin(ca * 13.0 + t * 26.0, sa * 13.0, seed + 13))
            body = min(1.0, prof / R)
            rr = prof * (1 + 0.1 * n1) + (0.13 * n2 + 0.04 * n3) * (0.35 + 0.65 * body) if t < 0.995 else 0.0
            x = rr * ca
            y = rr * sa
            if cut > 0 and x > R * (1 - cut) and t < shoulder + 0.05:
                x = R * (1 - cut) + 0.04 * n2
            verts.append((x + lean * H * t * t, y, H * t))
    faces = []
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            faces.append([i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j])
    P.add("straw", np.array(verts), faces, None)   # "straw" key: smooth-shaded; its material is swapped for hay_rick
    # pole through the top
    P.cyl("fresh", (0, 0, -0.2), (lean * H * 0.9, 0, H + 0.55), 0.055, 0.03, sides=8)
    # ropes over the cap, weighted with stones
    for k in range(4):
        a = k * math.pi / 4 + rng.uniform(-0.15, 0.15)
        pts = []
        for s in np.linspace(-1, 1, 15):
            t = shoulder + (1 - shoulder) * (1 - abs(s)) * 0.98
            u = (t - shoulder) / (1 - shoulder)
            prof = R * 1.07 * (1 - u) ** 0.88 * (1.0 + 0.1 * math.sin(u * math.pi)) + 0.06
            sg = 1 if s >= 0 else -1
            pts.append((sg * prof * math.cos(a) + lean * H * t * t, sg * prof * math.sin(a), H * t + 0.015))
        # hanging ends
        for sg in (-1, 1):
            base = np.array([sg * R * 1.1 * math.cos(a), sg * R * 1.1 * math.sin(a), H * shoulder])
            end = base + np.array([sg * 0.05 * math.cos(a), sg * 0.05 * math.sin(a), -rng.uniform(0.5, 0.9)])
            P.tube("rope", [tuple(base), tuple(end)], [0.012, 0.012], sides=5)
            v, f = __import__('plants').rock(rng, rng.uniform(0.09, 0.13), flat=0.7, sub=2)
            P.add("stone", v + end - np.array([0, 0, 0.08]), f, None)
        P.tube("rope", pts, [0.012] * len(pts), sides=5)
    # strands sticking out of the body and the shoulder, short and clumped
    for k in range(2600):
        t = rng.uniform(0.02, shoulder + 0.25)
        a = rng.uniform(0, 2 * math.pi)
        if t < shoulder:
            prof = R * (0.84 + 0.16 * math.sin(t / shoulder * math.pi * 0.85))
        else:
            u = (t - shoulder) / (1 - shoulder)
            prof = R * 1.07 * (1 - u) ** 0.88 * (1.0 + 0.1 * math.sin(u * math.pi))
        out = np.array([math.cos(a), math.sin(a), 0.0])
        p = np.array([prof * math.cos(a) + lean * H * t * t, prof * math.sin(a), H * t])
        d = np.array([0, 0, -1.0]) * rng.uniform(0.3, 1.0) + out * rng.uniform(0.3, 0.9) + rng.normal(0, 0.35, 3)
        st.add(p - out * 0.02, d, rng.uniform(0.06, 0.2), rng.uniform(0.003, 0.005), straw_colour(rng, 0.45), segs=2)
    # loose hay trodden round the foot
    for k in range(900):
        a = rng.uniform(0, 2 * math.pi)
        r = R * 0.95 + rng.uniform(0.0, 1.0) ** 2 * 1.2
        p = np.array([r * math.cos(a), r * math.sin(a), 0.015])
        b = rng.uniform(0, 2 * math.pi)
        st.add(p, (math.cos(b), math.sin(b), 0.05), rng.uniform(0.1, 0.3), rng.uniform(0.003, 0.006), straw_colour(rng, 0.55), segs=1)


def mat_hay():
    """Hay rick: weathered grey-brown outside (rain-bleached on the cap), golden where cut, damp and dark at the foot."""
    from common import NB, new_material
    from materials import hexc
    m = new_material("hay_rick")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    gen = nb.texcoord('Generated')
    nrm = nb.geometry('Normal')
    n1 = nb.noise(nb.mapping(obj, scale=(1.0, 1.0, 0.35)), scale=22.0, detail=6, rough=0.65, distortion=0.9)
    n2 = nb.noise(obj, scale=2.5, detail=4)
    n3 = nb.noise(obj, scale=90.0, detail=3, distortion=1.5)
    hay = nb.ramp(n1, [(0.25, hexc('54442a')), (0.5, hexc('7a633b')), (0.72, hexc('8f7546')), (0.9, hexc('a48955'))])
    hay = nb.mix(nb.maprange(n3, 0.55, 0.75, 0.0, 0.5), hay, hexc('3a2f1e'))
    gz = nb.sep(gen)[2]
    nz = nb.sep(nrm)[2]
    # pass 2b: forkfuls of hay - clumps a hand or two across with dark gaps between them, so the stack has a
    # broken, fibrous surface even from the air
    clv = nb.voronoi(nb.mapping(obj, scale=(1.0, 1.0, 1.6)), scale=6.5, feature='DISTANCE_TO_EDGE', which='Distance')
    gaps = nb.maprange(clv, 0.0, 0.09, 1.0, 0.0)
    clc = nb.voronoi(nb.mapping(obj, scale=(1.0, 1.0, 1.6)), scale=6.5, feature='F1', which='Color')
    clr = nb.sep(clc)[0]
    hay = nb.hsv(hay, v=nb.maprange(clr, 0.0, 1.0, 0.72, 1.12))
    # rain-bleached grey-brown on the upper surfaces (old hay goes grey and dark, not pale)
    weather = nb.math('MULTIPLY', nb.maprange(nz, 0.1, 0.8, 0.0, 0.65), nb.maprange(n2, 0.3, 0.7, 0.5, 1.0))
    hay = nb.mix(weather, hay, nb.mix(nb.maprange(nb.math('ADD', nb.math('MULTIPLY', n1, 0.6), nb.math('MULTIPLY', clr, 0.4)), 0.3, 0.7), hexc('41372a'), hexc('64553f')))
    hay = nb.mix(nb.math('MULTIPLY', gaps, 0.8), hay, hexc('241d14'))
    # rain runs down the outside in dark streaks from the cap
    rstreak = nb.noise(nb.mapping(obj, scale=(9.0, 9.0, 0.45)), scale=2.2, detail=4, rough=0.6)
    rs = nb.math('MULTIPLY', nb.maprange(rstreak, 0.5, 0.7, 0.0, 0.75), nb.maprange(nz, -0.2, 0.5, 0.4, 1.0))
    hay = nb.mix(rs, hay, hexc('2f2a22'))
    # dark damp foot
    hay = nb.mix(nb.maprange(gz, 0.12, 0.0, 0.0, 0.75), hay, hexc('2e2618'))
    h = nb.math('ADD', nb.math('ADD', n1, nb.math('MULTIPLY', n3, 0.5)), nb.math('MULTIPLY', nb.math('SUBTRACT', clr, nb.math('MULTIPLY', gaps, 1.4)), 0.8))
    bsdf = nb.principled(Base_Color=hay, Roughness=0.88, Normal=nb.bump(h, 1.0, 0.03))
    nb.set(bsdf, 'Sheen Weight', 0.25)
    nb.output(bsdf)
    return m


def rebuild_haystacks(mats):
    col = C.get_collection("Props")
    mats = dict(mats)
    mats["straw"] = mat_hay()
    pl = VP.Placer(col, mats)
    for nm in ("haystack_1", "haystack_2", "haystack_3"):
        p = bpy.data.objects.get(nm)
        if p is not None:
            for ch in list(p.children):
                bpy.data.objects.remove(ch, do_unlink=True)
            bpy.data.objects.remove(p, do_unlink=True)
    # pass 2b: not three alike in a row - one big old rick, one half used (cut back), one small new one set apart
    pl.place("haystack_1", lambda P, st: haystack2(P, st, H=3.6, R=1.85, lean=0.05, seed=1), 20.0, 38.6, 30.0, strands=True, sink=0.05)
    pl.place("haystack_2", lambda P, st: haystack2(P, st, H=2.8, R=1.6, lean=-0.07, cut=0.42, seed=2), 25.2, 40.4, 205.0, strands=True, sink=0.05)
    pl.place("haystack_3", lambda P, st: haystack2(P, st, H=2.2, R=1.3, lean=0.08, seed=3), 29.8, 35.6, 160.0, strands=True, sink=0.05)
    return 3
