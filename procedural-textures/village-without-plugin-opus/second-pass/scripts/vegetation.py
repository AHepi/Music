"""Vegetation library (plants, trees, rocks) and scattering with geometry nodes."""
import bpy
import numpy as np
import math
from mathutils import Vector, kdtree
import common as C
from common import NB, new_material, smoothstep, fbm
import plants as PL
import trees as TR
import layout as L
from materials import hexc, srgb

LIB = "Library"


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
def mat_plant(name="plant", trans=0.32, rough=0.5, hue_var=0.035, val_var=0.25, sat=1.0, patches=0.0, gain=1.0):
    m = new_material(name)
    nb = NB(m.node_tree)
    col = nb.attr('col', 'Color')
    rnd = nb.objinfo('Random')
    h = nb.math('ADD', 0.5, nb.math('MULTIPLY', nb.math('SUBTRACT', rnd, 0.5), hue_var * 2))
    v = nb.math('MULTIPLY', nb.math('ADD', 1.0 - val_var * 0.5, nb.math('MULTIPLY', rnd, val_var)), gain)
    base = nb.hsv(col, h=h, s=sat, v=v)
    if patches > 0:
        # large patches of drier / lusher grass across the meadow, keyed to the instance position
        loc = nb.objinfo('Location')
        pn = nb.noise(loc, scale=0.07, detail=3, rough=0.55)
        pn2 = nb.noise(loc, scale=0.25, detail=2)
        dry = nb.maprange(nb.math('ADD', pn, nb.math('MULTIPLY', pn2, 0.3)), 0.5, 0.72, 0.0, patches)
        base = nb.mix(dry, base, nb.hsv(base, h=0.46, s=0.75, v=1.25))
        lush = nb.maprange(pn, 0.25, 0.42, patches * 0.6, 0.0)
        base = nb.mix(lush, base, nb.hsv(base, h=0.52, s=1.15, v=0.8))
    bsdf = nb.principled(Base_Color=base, Roughness=rough)
    nb.set(bsdf, 'Specular IOR Level', 0.42)
    tr = nb.node('ShaderNodeBsdfTranslucent')
    nb.set(tr, 'Color', nb.hsv(base, s=1.15, v=1.25))
    mix = nb.node('ShaderNodeMixShader')
    nb.set(mix, 'Fac', trans)
    nb.links.new(bsdf.outputs[0], mix.inputs[1])
    nb.links.new(tr.outputs[0], mix.inputs[2])
    nb.output(mix)
    return m


def mat_bark(kind):
    m = new_material("bark_" + kind)
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    sx, sy, sz = nb.sep(uv)
    rnd = nb.attr('rnd')
    if kind == 'birch':
        # white bark with dark horizontal lenticels, dark rough base
        lent_vec = nb.comb(nb.math('MULTIPLY', sx, 3.0), nb.math('MULTIPLY', sy, 40.0), 0)
        lent = nb.noise(lent_vec, scale=1.5, detail=3, rough=0.6)
        lentm = nb.maprange(lent, 0.62, 0.7, 0.0, 1.0)
        patches = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 1.5), nb.math('MULTIPLY', sy, 3.0), 0), scale=1.0, detail=4)
        white = nb.mix(nb.maprange(patches, 0.45, 0.65), hexc('d9d6cc'), hexc('b9b5aa'))
        base = nb.mix(lentm, white, hexc('2b2622'))
        geo_z = nb.sep(obj)[2]
        lowdark = nb.maprange(geo_z, 1.6, 0.2, 0.0, 1.0)
        lowdark = nb.math('MULTIPLY', lowdark, nb.maprange(nb.noise(obj, scale=3.0, detail=4), 0.3, 0.6, 0.6, 1.0))
        base = nb.mix(lowdark, base, hexc('3a342d'))
        h = nb.math('ADD', nb.math('MULTIPLY', lentm, -0.5), nb.math('MULTIPLY', lowdark, nb.noise(obj, scale=12.0)))
        bump = nb.bump(h, 0.4, 0.01)
        rough = 0.65
    elif kind == 'beech':
        n1 = nb.noise(nb.comb(sx, nb.math('MULTIPLY', sy, 0.6), 0), scale=3.0, detail=6, rough=0.6)
        base = nb.ramp(n1, [(0.3, hexc('5f5c55')), (0.55, hexc('7c786e')), (0.75, hexc('8e8b80'))])
        moss = nb.maprange(nb.noise(obj, scale=1.2, detail=4), 0.55, 0.7, 0.0, 0.8)
        base = nb.mix(moss, base, hexc('4d5a2a'))
        bump = nb.bump(nb.noise(nb.comb(sx, sy, 0), scale=25.0, detail=3), 0.15, 0.01)
        rough = 0.6
    elif kind == 'spruce':
        sc = nb.voronoi(nb.comb(nb.math('MULTIPLY', sx, 1.0), nb.math('MULTIPLY', sy, 0.7), 0), scale=18.0, feature='F1', which='Distance')
        scc = nb.voronoi(nb.comb(nb.math('MULTIPLY', sx, 1.0), nb.math('MULTIPLY', sy, 0.7), 0), scale=18.0, feature='F1', which='Color')
        base = nb.ramp(nb.noise(scc, scale=4, detail=0), [(0.3, hexc('4a3426')), (0.6, hexc('6b4d38')), (0.85, hexc('5a4a40'))])
        base = nb.mix(nb.maprange(sc, 0.25, 0.5), base, hexc('2f241c'))
        bump = nb.bump(sc, 0.5, 0.01)
        rough = 0.75
    else:  # oak
        fis_vec = nb.comb(nb.math('MULTIPLY', sx, 9.0), nb.math('MULTIPLY', sy, 1.6), 0)
        fis = nb.voronoi(fis_vec, scale=1.0, feature='DISTANCE_TO_EDGE', which='Distance')
        fism = nb.maprange(fis, 0.0, 0.12, 0.0, 1.0)
        ns = nb.noise(fis_vec, scale=2.0, detail=6, rough=0.6)
        base = nb.mix(nb.maprange(ns, 0.35, 0.65), hexc('3c352d'), hexc('5d554a'))
        base = nb.mix(nb.math('SUBTRACT', 1.0, fism), base, hexc('1d1915'))
        moss = nb.maprange(nb.noise(obj, scale=0.8, detail=4), 0.55, 0.68, 0.0, 0.75)
        geo_z = nb.sep(obj)[2]
        moss = nb.math('MULTIPLY', moss, nb.maprange(geo_z, 3.5, 0.3, 0.2, 1.0))
        base = nb.mix(moss, base, hexc('48552a'))
        bump = nb.bump(nb.math('ADD', fism, nb.math('MULTIPLY', ns, 0.3)), 0.9, 0.02)
        rough = 0.85
    base = nb.hsv(base, v=nb.math('ADD', 0.85, nb.math('MULTIPLY', rnd, 0.3)))
    bsdf = nb.principled(Base_Color=base, Roughness=rough, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.3)
    nb.output(bsdf)
    return m


def mat_rock(name="rock", val=1.0, dirt=0.7):
    m = new_material(name)
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    gen = nb.texcoord('Generated')
    rnd = nb.objinfo('Random')
    n1 = nb.noise(obj, scale=2.5, detail=6, rough=0.6)
    n2 = nb.noise(obj, scale=14.0, detail=4, rough=0.6)
    base = nb.ramp(n1, [(0.3, hexc('5e5b55')), (0.5, hexc('7a766c')), (0.7, hexc('8c8578'))])
    base = nb.hsv(base, h=nb.math('ADD', 0.47, nb.math('MULTIPLY', rnd, 0.06)), v=nb.math('MULTIPLY', nb.math('ADD', 0.75, nb.math('MULTIPLY', rnd, 0.4)), val))
    # lichen and moss on top
    nz = nb.sep(nb.geometry('Normal'))[2]
    top = nb.maprange(nz, 0.3, 0.9, 0.0, 1.0)
    lich = nb.maprange(nb.noise(obj, scale=6.0, detail=3), 0.55, 0.65, 0.0, 1.0)
    base = nb.mix(nb.math('MULTIPLY', lich, 0.6), base, hexc('a5a07a'))
    moss = nb.math('MULTIPLY', top, nb.maprange(nb.noise(obj, scale=1.5, detail=4), 0.45, 0.62, 0.0, 1.0))
    base = nb.mix(moss, base, hexc('3f4d1d'))
    # dirt at the bottom
    gz = nb.sep(gen)[2]
    base = nb.mix(nb.maprange(gz, 0.35 + 0.3 * (dirt - 0.7), 0.05, 0.0, dirt), base, hexc('3a2e22'))
    bump = nb.bump(nb.math('ADD', n2, nb.math('MULTIPLY', n1, 0.5)), 0.5, 0.02)
    bsdf = nb.principled(Base_Color=base, Roughness=0.82, Normal=bump)
    nb.output(bsdf)
    return m


# ----------------------------------------------------------------------------
# Library objects
# ----------------------------------------------------------------------------
def lib_collection(name):
    root = C.get_collection(LIB)
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        root.children.link(col)
    return col


def exclude_library():
    vl = bpy.context.view_layer
    for lc in vl.layer_collection.children:
        if lc.name == LIB:
            lc.exclude = True


def geo_to_object(name, geo, col, mats):
    v, f, c, mi = geo.arrays()
    me = C.mesh_from_arrays(name, v, f, point_attrs={"col": c}, mat_index=mi, materials=mats)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def tree_to_object(name, tg, col, bark_mat, leaf_mat):
    bme = tg.bark.build(name + "_bark_tmp", materials=[bark_mat], smooth=True)
    # merge leaves into the same mesh as a second material slot
    lv = np.array(tg.lv) if tg.lv else np.zeros((0, 3))
    nb_ = len(bme.vertices)
    bv = np.zeros(nb_ * 3)
    bme.vertices.foreach_get("co", bv)
    bv = bv.reshape(-1, 3)
    bfaces = [list(p.vertices) for p in bme.polygons]
    buv = np.zeros(len(bme.loops) * 2)
    bme.uv_layers[0].data.foreach_get("uv", buv)
    buv = buv.reshape(-1, 2)
    brnd = np.zeros(len(bme.polygons))
    bme.attributes["rnd"].data.foreach_get("value", brnd)
    bpy.data.meshes.remove(bme)
    allv = np.concatenate([bv, lv]) if len(lv) else bv
    allf = bfaces + [[i + nb_ for i in f] for f in tg.lf]
    nlo_leaf = sum(len(f) for f in tg.lf)
    loop_uv = np.concatenate([buv, np.zeros((nlo_leaf, 2))]) if nlo_leaf else buv
    cols = np.concatenate([np.tile([0.2, 0.15, 0.1, 1.0], (nb_, 1)), np.array([tuple(c) + (1.0,) for c in tg.lc])]) if len(lv) else np.tile([0.2, 0.15, 0.1, 1.0], (nb_, 1))
    mi = np.concatenate([np.zeros(len(bfaces), dtype=np.int32), np.ones(len(tg.lf), dtype=np.int32)])
    frnd = np.concatenate([brnd, np.zeros(len(tg.lf))])
    me = C.mesh_from_arrays(name, allv, allf, loop_uv=loop_uv, point_attrs={"col": cols}, face_attrs={"rnd": frnd}, mat_index=mi, materials=[bark_mat, leaf_mat])
    # smooth bark, flat leaves are fine smooth too
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def build_library():
    """Create all vegetation library objects (hidden) and return a summary."""
    mats = {
        "grass": mat_plant("grass_blades", trans=0.35, rough=0.45, hue_var=0.03, val_var=0.35, patches=0.8),
        "herb": mat_plant("herbs", trans=0.3, rough=0.5, hue_var=0.02, val_var=0.25),
        "flower": mat_plant("flowers", trans=0.25, rough=0.5, hue_var=0.01, val_var=0.15),
        "leaf": mat_plant("tree_leaves", trans=0.38, rough=0.55, hue_var=0.035, val_var=0.3, gain=1.45),
        "needle": mat_plant("needles", trans=0.2, rough=0.45, hue_var=0.02, val_var=0.25, gain=1.3),
        "rock": mat_rock(),
        "pebble": mat_rock("pebble_stone", val=0.62, dirt=0.85),
        "organic": mat_plant("organic", trans=0.0, rough=0.5, hue_var=0.01, val_var=0.3),
    }
    for k in ("oak", "beech", "birch", "spruce"):
        mats["bark_" + k] = mat_bark(k)
    summary = {}
    # ---- grass families
    specs = {
        "lib_grass_short": [dict(n=65, h=(0.10, 0.24), r=0.08, dry=0.1), dict(n=80, h=(0.08, 0.22), r=0.1, dry=0.15),
                            dict(n=55, h=(0.12, 0.28), r=0.07, dry=0.06), dict(n=70, h=(0.1, 0.26), r=0.11, dry=0.18)],
        "lib_grass_tall": [dict(n=75, h=(0.25, 0.6), r=0.1, dry=0.22, seed=3), dict(n=60, h=(0.3, 0.65), r=0.09, dry=0.32, seed=4),
                           dict(n=80, h=(0.2, 0.55), r=0.12, dry=0.18, seed=2), dict(n=55, h=(0.35, 0.75), r=0.08, dry=0.38, seed=5)],
        "lib_grass_dry": [dict(n=50, h=(0.18, 0.4), r=0.08, dry=0.7, seed=2), dict(n=40, h=(0.2, 0.45), r=0.09, dry=0.85, seed=1)],
        "lib_grass_road": [dict(n=22, h=(0.05, 0.14), r=0.05, dry=0.25), dict(n=30, h=(0.06, 0.16), r=0.06, dry=0.35),
                           dict(n=16, h=(0.04, 0.1), r=0.04, dry=0.2)],
    }
    for cname, lst in specs.items():
        col = lib_collection(cname)
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for i, sp in enumerate(lst):
            rng = np.random.RandomState(1000 + i * 17 + len(cname))
            geo = PL.grass_clump(rng, sp["n"], sp["h"], sp["r"], dry=sp["dry"], seedheads=sp.get("seed", 0))
            geo_to_object(f"{cname}_{i}", geo, col, [mats["grass"]])
        summary[cname] = len(lst)
    # ---- weeds / herbs
    col = lib_collection("lib_weeds")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(3):
        geo_to_object(f"plantain_{i}", PL.plantain(np.random.RandomState(200 + i)), col, [mats["herb"]])
    for i in range(3):
        geo_to_object(f"dandelion_{i}", PL.dandelion(np.random.RandomState(300 + i), flowers=(i != 2)), col, [mats["herb"]])
    for i in range(2):
        geo_to_object(f"clover_{i}", PL.clover_patch(np.random.RandomState(400 + i), flowers=2 + i), col, [mats["herb"]])
    summary["weeds"] = len(col.objects)
    col = lib_collection("lib_flowers")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i, kind in enumerate(["yarrow", "buttercup", "knapweed", "campion", "yarrow", "buttercup"]):
        geo_to_object(f"flower_{kind}_{i}", PL.wildflower(np.random.RandomState(500 + i), kind), col, [mats["flower"]])
    summary["flowers"] = len(col.objects)
    col = lib_collection("lib_nettles")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(3):
        geo_to_object(f"nettle_{i}", PL.nettle(np.random.RandomState(600 + i)), col, [mats["herb"]])
    col = lib_collection("lib_ferns")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(4):
        geo_to_object(f"fern_{i}", PL.fern(np.random.RandomState(700 + i), size=rng.uniform(0.8, 1.2) if False else 0.8 + 0.15 * i), col, [mats["herb"]])
    # ---- rocks
    col = lib_collection("lib_rocks")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(6):
        rng = np.random.RandomState(800 + i)
        v, f = PL.rock(rng, 1.0, flat=rng.uniform(0.45, 0.8), sub=3)
        me = C.mesh_from_arrays(f"rock_{i}", v, f, smooth=True, materials=[mats["rock"]])
        ob = bpy.data.objects.new(f"rock_{i}", me)
        col.objects.link(ob)
    col = lib_collection("lib_pebbles")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(6):
        rng = np.random.RandomState(850 + i)
        v, f = PL.rock(rng, 1.0, flat=rng.uniform(0.4, 0.7), sub=2)
        me = C.mesh_from_arrays(f"pebble_{i}", v, f, smooth=True, materials=[mats["pebble"]])
        ob = bpy.data.objects.new(f"pebble_{i}", me)
        col.objects.link(ob)
    col = lib_collection("lib_gravel")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(5):
        rng = np.random.RandomState(870 + i)
        v, f = PL.rock(rng, 1.0, flat=rng.uniform(0.5, 0.8), sub=1)
        me = C.mesh_from_arrays(f"gravel_{i}", v, f, smooth=True, materials=[mats["pebble"]])
        ob = bpy.data.objects.new(f"gravel_{i}", me)
        col.objects.link(ob)
    col = lib_collection("lib_debris")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(5):
        geo_to_object(f"twig_{i}", PL.twig(np.random.RandomState(880 + i)), col, [mats["organic"]])
    col = lib_collection("lib_dung")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for i in range(3):
        geo_to_object(f"dung_{i}", PL.dung(np.random.RandomState(890 + i)), col, [mats["organic"]])
    summary["rocks"] = 12
    exclude_library()
    return mats, summary


def build_trees(mats):
    """Tree variants into lib_trees_broad / lib_trees_conifer / lib_bushes."""
    out = {}
    plan = {
        "lib_trees_broad": [("oak", 11), ("oak", 12), ("oak", 13), ("beech", 21), ("beech", 22), ("birch", 31), ("birch", 32)],
        "lib_bushes": [("hazel", 41), ("hazel", 42), ("hazel", 43)],
    }
    for cname, lst in plan.items():
        col = lib_collection(cname)
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for kind, seed in lst:
            tg, info = TR.broadleaf(kind, seed)
            ob = tree_to_object(f"tree_{kind}_{seed}", tg, col, mats[info["bark"]], mats["leaf"])
            out[ob.name] = dict(verts=len(ob.data.vertices), height=round(info["height"], 1), crown=round(info["crown"], 1))
    col = lib_collection("lib_trees_conifer")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for seed, h in ((51, 22.0), (52, 18.0), (53, 25.0), (54, 15.0)):
        tg, info = TR.spruce(seed, height=h, low_branch=1.0 if seed != 53 else 3.0, dead_lower=0.0 if seed != 53 else 0.15)
        ob = tree_to_object(f"tree_spruce_{seed}", tg, col, mats["bark_spruce"], mats["needle"])
        out[ob.name] = dict(verts=len(ob.data.vertices), height=round(info["height"], 1))
    # a dead snag for the forest edge
    col = lib_collection("lib_snags")
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    tg, info = TR.broadleaf("oak", 99, leaves=False, scale=0.8)
    ob = tree_to_object("tree_snag_99", tg, col, mats["bark_oak"], mats["leaf"])
    out[ob.name] = dict(verts=len(ob.data.vertices))
    exclude_library()
    return out


# ----------------------------------------------------------------------------
# Scattering
# ----------------------------------------------------------------------------
def scatter_group(name, surface, collection, density_attr, density, seed, scale=(0.8, 1.2),
                  align_normal=False, sink=0.0, mask_attr2=None, density_power=1.0):
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
    na.inputs['Name'].default_value = density_attr or "pathf"
    dens = nb.out(na, 'Attribute') if density_attr else 1.0
    if density_power != 1.0:
        dens = nb.math('POWER', nb.math('MAXIMUM', dens, 0.0), density_power)
    if mask_attr2:
        na2 = nb.node('GeometryNodeInputNamedAttribute', data_type='FLOAT')
        na2.inputs['Name'].default_value = mask_attr2
        dens = nb.math('MULTIPLY', dens, nb.out(na2, 'Attribute'))
    dens = nb.math('MULTIPLY', dens, density) if density_attr else density
    dist = nb.node('GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM')
    nb.links.new(nb.out(oi, 'Geometry'), dist.inputs['Mesh'])
    nb.set(dist, 'Density', dens)
    nb.set(dist, 'Seed', seed)
    ci = nb.node('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
    ci.inputs['Collection'].default_value = collection
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    nobj = len(collection.objects)
    ri = nb.node('FunctionNodeRandomValue', data_type='INT')
    nb.set(ri, 'Min', 0)
    nb.set(ri, 'Max', max(nobj - 1, 0))
    nb.set(ri, 'Seed', seed + 1)
    rz = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rz, 'Min', 0.0)
    nb.set(rz, 'Max', 6.2831)
    nb.set(rz, 'Seed', seed + 2)
    eul = nb.node('ShaderNodeCombineXYZ')
    nb.set(eul, 'Z', nb.out(rz))
    e2r = nb.node('FunctionNodeEulerToRotation')
    nb.links.new(nb.out(eul), e2r.inputs['Euler'])
    if align_normal:
        rr = nb.node('FunctionNodeRotateRotation', rotation_space='LOCAL')
        nb.links.new(nb.out(dist, 'Rotation'), rr.inputs['Rotation'])
        nb.links.new(nb.out(e2r), rr.inputs['Rotate By'])
        rot = nb.out(rr)
    else:
        rot = nb.out(e2r)
    rs = nb.node('FunctionNodeRandomValue', data_type='FLOAT')
    nb.set(rs, 'Min', scale[0])
    nb.set(rs, 'Max', scale[1])
    nb.set(rs, 'Seed', seed + 3)
    iop = nb.node('GeometryNodeInstanceOnPoints')
    nb.links.new(nb.out(dist, 'Points'), iop.inputs['Points'])
    nb.links.new(nb.out(ci), iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    nb.links.new(nb.out(ri), iop.inputs['Instance Index'])
    nb.links.new(rot, iop.inputs['Rotation'])
    nb.links.new(nb.out(rs), iop.inputs['Scale'])
    geo_out = nb.out(iop)
    if sink != 0.0:
        tr = nb.node('GeometryNodeTranslateInstances')
        nb.links.new(geo_out, tr.inputs['Instances'])
        tr.inputs['Translation'].default_value = (0, 0, -sink)
        tr.inputs['Local Space'].default_value = True
        geo_out = nb.out(tr)
    nb.links.new(geo_out, gout.inputs[0])
    return ng


def make_scatter(name, surface, collection_name, density_attr, density, seed, scale=(0.8, 1.2), align_normal=False, sink=0.0, mask_attr2=None, density_power=1.0, parent_col="Vegetation"):
    col = C.get_collection(parent_col)
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name + "_empty")
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ng = scatter_group("GN_" + name, surface, bpy.data.collections[collection_name], density_attr, density, seed, scale, align_normal, sink, mask_attr2, density_power)
    mod = ob.modifiers.new("scatter", 'NODES')
    mod.node_group = ng
    return ob


def add_point_attr(ob, name, values):
    me = ob.data
    if name in me.attributes:
        me.attributes.remove(me.attributes[name])
    a = me.attributes.new(name, 'FLOAT', 'POINT')
    a.data.foreach_set("value", np.asarray(values, dtype=np.float32))


def terrain_masks():
    """Extra density masks on the terrain for the scatter layers."""
    ter = bpy.data.objects["terrain"]
    me = ter.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    x, y = co[:, 0], co[:, 1]

    def attr(name):
        a = np.zeros(n)
        me.attributes[name].data.foreach_get("value", a)
        return a
    grass = attr("grass")
    forest = attr("forest")
    edge_t = attr("edge_t")
    built = attr("built")
    rv = np.sqrt((x - L.VILLAGE_C[0]) ** 2 + (y - L.VILLAGE_C[1]) ** 2)
    meadow = grass * (1 - smoothstep(0.35, 0.8, forest))
    patch = smoothstep(-0.25, 0.45, fbm(x / 7.0, y / 7.0, 3, 81))
    patch2 = smoothstep(-0.2, 0.5, fbm(x / 4.0, y / 4.0, 2, 82))
    # building proximity (weeds, nettles, tall grass along walls)
    near_b = np.zeros(n)
    for bname, b in L.BUILDINGS.items():
        c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
        lx = (x - b["x"]) * c + (y - b["y"]) * s
        ly = -(x - b["x"]) * s + (y - b["y"]) * c
        dx = np.maximum(np.abs(lx) - b["w"] / 2, 0)
        dy = np.maximum(np.abs(ly) - b["d"] / 2, 0)
        d = np.sqrt(dx * dx + dy * dy)
        inside = (np.abs(lx) < b["w"] / 2) & (np.abs(ly) < b["d"] / 2)
        near_b = np.maximum(near_b, np.where(inside, 0, 1 - smoothstep(0.2, 1.6, d)))
    roadside = smoothstep(0.0, 0.3, edge_t) * (1 - smoothstep(0.8, 2.6, edge_t))
    ragged = 0.5 + 0.5 * fbm(x / 1.3, y / 1.3, 3, 87)
    edge_ramp = smoothstep(0.05, 0.25 + 1.1 * ragged, edge_t)
    verge = smoothstep(-0.1, 0.15, edge_t) * (1 - smoothstep(0.5, 1.4 + ragged, edge_t)) * (1 - built)
    fringe = smoothstep(0.15, 0.5, forest) * (1 - smoothstep(0.6, 0.95, forest))   # the clearing's edge
    deep = smoothstep(0.5, 1.0, forest) * (1 - smoothstep(55.0, 110.0, rv))
    m = {
        "d_short": meadow * (0.55 + 0.45 * (1 - patch)) * edge_ramp,
        "d_tall": meadow * (0.15 + 0.85 * patch) * (1 - 0.8 * roadside) * edge_ramp + 0.6 * grass * fringe,
        "d_verge": verge * (1 - forest),
        "d_dry": meadow * patch2 * 0.6 + 0.5 * roadside * grass,
        "d_weeds": grass * (0.25 + 0.75 * roadside) * (1 - forest),
        "d_flowers": meadow * smoothstep(-0.1, 0.5, fbm(x / 11.0, y / 11.0, 2, 83)) * (1 - roadside * 0.7),
        "d_nettles": near_b * (1 - built) * smoothstep(0.3, 0.9, edge_t) * smoothstep(-0.2, 0.4, fbm(x / 3.0, y / 3.0, 2, 84)),
        "d_ferns": smoothstep(0.35, 0.9, forest) * (1 - smoothstep(60.0, 120.0, rv)) * smoothstep(1.0, 3.0, edge_t) * smoothstep(-0.3, 0.3, fbm(x / 6.0, y / 6.0, 2, 85)),
        "d_rocks": (smoothstep(0.2, 0.8, forest) * 0.6 + roadside * 0.4) * smoothstep(0.35, 0.6, fbm(x / 9.0, y / 9.0, 2, 86)) * (1 - built),
        "d_forestgrass": fringe * smoothstep(0.5, 2.0, edge_t) + deep * 0.08 * smoothstep(0.5, 2.0, edge_t),
    }
    for k, v in m.items():
        add_point_attr(ter, k, np.clip(v, 0, 1))
    return {k: float(np.mean(v)) for k, v in m.items()}


def scatter_ground():
    ter = bpy.data.objects["terrain"]
    stats = terrain_masks()
    make_scatter("sc_grass_short", ter, "lib_grass_short", "d_short", 40.0, 11, (0.75, 1.35))
    make_scatter("sc_grass_tall", ter, "lib_grass_tall", "d_tall", 20.0, 21, (0.7, 1.35))
    make_scatter("sc_grass_dry", ter, "lib_grass_dry", "d_dry", 9.0, 31, (0.7, 1.25))
    make_scatter("sc_verge", ter, "lib_grass_road", "d_verge", 22.0, 33, (0.8, 1.6))
    make_scatter("sc_weeds", ter, "lib_weeds", "d_weeds", 1.6, 41, (0.7, 1.3), align_normal=True)
    make_scatter("sc_flowers", ter, "lib_flowers", "d_flowers", 1.1, 51, (0.8, 1.2))
    make_scatter("sc_nettles", ter, "lib_nettles", "d_nettles", 2.0, 61, (0.7, 1.2))
    make_scatter("sc_ferns", ter, "lib_ferns", "d_ferns", 0.45, 71, (0.7, 1.4))
    make_scatter("sc_rocks", ter, "lib_rocks", "d_rocks", 0.02, 81, (0.15, 0.55), align_normal=True, sink=0.06)
    make_scatter("sc_forestgrass", ter, "lib_grass_tall", "d_forestgrass", 6.0, 91, (0.6, 1.1))
    # on the roads: tufts in the centre strip and edges, pebbles
    for rn in [o.name for o in bpy.data.objects if o.name.startswith(("road_", "yard_")) and o.type == 'MESH']:
        rob = bpy.data.objects[rn]
        make_scatter("sc_rgrass_" + rn, rob, "lib_grass_road", "gmask", 18.0, 101 + len(rn), (0.7, 1.4))
        make_scatter("sc_rweeds_" + rn, rob, "lib_weeds", "gmask", 1.2, 131 + len(rn), (0.5, 0.9), align_normal=True)
        make_scatter("sc_rpebble_" + rn, rob, "lib_pebbles", "pebm", 4.5, 161 + len(rn), (0.01, 0.05), align_normal=True, sink=0.008, density_power=1.6)
        make_scatter("sc_rgravel_" + rn, rob, "lib_gravel", "pebm", 45.0, 171 + len(rn), (0.004, 0.012), align_normal=True, sink=0.002)
        make_scatter("sc_rtwig_" + rn, rob, "lib_debris", "edgef", 0.7, 181 + len(rn), (0.6, 1.2), align_normal=True, sink=0.004)
        if rn.startswith("road_main") or rn.startswith("road_lane") or rn.startswith("yard_901"):
            make_scatter("sc_rdung_" + rn, rob, "lib_dung", "hoof", 0.02, 191 + len(rn), (0.8, 1.2), align_normal=True, sink=0.01)
    return stats
