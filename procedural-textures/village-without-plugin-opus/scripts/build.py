"""Build steps for the forest village. Each step can be re-run on its own."""
import bpy
import time
import common as C
import layout as L
import materials as M
import terrain as T

BLEND = C.WORK + "/village.blend"
ARCS_STABLE = [(14.0, 21.5, 5.2, 0.045), (3.5, 23.0, 4.6, 0.035)]


def purge_orphans():
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.node_groups, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def step_ground():
    t0 = time.time()
    gcol = C.get_collection("Ground")
    C.clear_collection("Ground")
    purge_orphans()
    mats = M.build_ground_materials()
    ter = T.build_terrain(gcol, [mats['terrain']])
    infos = {}
    for name in L.ROADS:
        ob, wobs, info = T.build_road(name, gcol, [mats['road']], mats['water'])
        infos[name] = info
    for yd in L.YARDS:
        T.build_yard(yd, gcol, [mats['road']], mats['water'], arcs=ARCS_STABLE if yd['seed'] == 901 else None)
    T._BVH.clear()
    return dict(seconds=time.time() - t0, terrain_verts=len(ter.data.vertices), roads=infos)


def save(path=None):
    path = path or BLEND
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    return path


def step_vegetation_lib():
    import vegetation as V
    t0 = time.time()
    mats, summary = V.build_library()
    summary["seconds"] = time.time() - t0
    return summary


def step_trees():
    import vegetation as V
    t0 = time.time()
    mats = {m.name: m for m in bpy.data.materials}
    m2 = {"leaf": mats["tree_leaves"], "needle": mats["needles"]}
    for k in ("oak", "beech", "birch", "spruce"):
        m2["bark_" + k] = mats["bark_" + k]
    out = V.build_trees(m2)
    out["seconds"] = time.time() - t0
    return out


def step_scatter_ground():
    import vegetation as V
    t0 = time.time()
    stats = V.scatter_ground()
    stats["seconds"] = time.time() - t0
    return stats


def step_forest():
    import forest as F
    t0 = time.time()
    counts = F.build_forest()
    counts["seconds"] = time.time() - t0
    return counts


def step_building(name):
    import buildmats as BM
    import buildings as B
    t0 = time.time()
    mats = BM.build_all()
    col = C.get_collection("Buildings")
    sub = bpy.data.collections.get("B_" + name)
    if sub is None:
        sub = bpy.data.collections.new("B_" + name)
        col.children.link(sub)
    for o in list(sub.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    fn = getattr(B, name)
    parent, info = fn(sub, mats)
    info["seconds"] = time.time() - t0
    info["objects"] = len(sub.objects)
    info["faces"] = sum(len(o.data.polygons) for o in sub.objects if o.type == 'MESH')
    return info


def step_props():
    import buildmats as BM
    import village_props as VP
    t0 = time.time()
    mats = BM.build_all()
    mats["herb_mat"] = bpy.data.materials["herbs"]
    col = C.get_collection("Props")
    for o in list(col.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    T._BVH.clear()
    out = VP.build_props(col, mats)
    out["seconds"] = time.time() - t0
    out["objects"] = len(col.objects)
    return out
