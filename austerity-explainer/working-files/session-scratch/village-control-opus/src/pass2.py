"""Pass 2 build steps (run inside the connected Blender, after opening village.blend from pass 1).

Order used for the delivered scene (each step can be re-run on its own):
    exec(open(SRC + '/run.py').read()); import pass2
    pass2.step_light()            # lower, warmer morning sun (25 deg, from a little east of south), hazier sky
    pass2.step_ground2()          # new dirt / puddle / stone materials; every road and yard rebuilt in place
    pass2.step_scatter2()         # stones, gravel, straw, leaves, twigs, dung, verge and crown grass on them
    pass2.step_village2()         # four more cottages, crofts, strip field, trodden ground, meadow variety, crops,
                                  # lone birches/beeches to oaks, new haystacks, household props for the new cottages
    pass2.step_buildings2()       # rebuilt buildings: framed gables, real window rooms, ledged shutters, irregular
                                  # shingles, no straw fuzz, no hidden stable light; lumpy thatch; roof moss
    pass2.step_cameras()          # pass-2 framings
    pass2.step_ground2(['main'], yards=False); pass2.step_scatter2()   # close-view patches follow the cameras
    pass2.step_compositor()       # mist-pass haze, set per shot
    import render_final; render_final.run()

After the computer restarted (05:28) the second half of this pass (pass2b.py) changed, in this order:
    pass2b.step_roads()      # worn wheel bands, grass crown + green mat seen from afar, deeper verge bites, broken
                             # clods, crumbled rut lips, pale dry / dark wet ruts, wet shine in separate dips, more grit,
                             # big mud-hole puddles (roads2.BIG_PUDDLES), denser flat weeds
    pass2b.step_stable()     # back-wall windows, more missing boards, limewashed stalls (real daylight inside)
    pass2b.step_haystacks()  # pointed caps, clumpy slumped bodies, weathered hay, one cut back, not three in a row
    pass2b.step_cameras()    # aerial aimed further south, 28 mm
    pass2b.step_cottage_a()  # ragged thatch eave; straw-coloured cut ends (buildmats)
    pass2b.step_trees()      # two stick-like trees at the forest edge removed
    pass2b.step_cottage_camera()   # clear blades near the cottage lens, f/2.8
    pass2b.step_stable_yard()      # prints where horses walk, darker yard puddles, water faces up
    render_final.run()       # with 4 diffuse bounces   (full list and order: pass2b.py)
"""
import bpy
import time
import importlib
import math
import numpy as np
import common as C
import layout as L
import terrain as T
import p2

ARCS_STABLE = [(14.0, 21.5, 5.2, 0.045), (3.5, 23.0, 4.6, 0.035)]

SUN_ELEV = 25.0
SUN_AZ = 280.0          # degrees counter-clockwise from +X: 280 = a little east of south (morning, low and warm)


def step_light():
    """Lower, warmer morning sun from the south-south-east; hazier sky (pass 1 was 'soft and flat, little mood')."""
    import scene_setup as SS
    importlib.reload(SS)
    SS.SUN_ELEV = SUN_ELEV
    SS.SUN_AZ = SUN_AZ
    w = SS.setup_world(strength=0.16, elev=SUN_ELEV, az=SUN_AZ, clouds=True, coverage=0.8)
    for n in w.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeTexSky':
            n.aerosol_density = 2.4
    SS.setup_sun(strength=4.8, angle_deg=1.0, color=(1.0, 0.83, 0.64), elev=SUN_ELEV, az=SUN_AZ)
    return dict(elev=SUN_ELEV, az=SUN_AZ)


# close-view patches on the main road: (camera, metres behind, metres ahead along the road)
PATCH_CAMS = (("CamRoadClose", 1.5, 11.0), ("CamRoad", 1.0, 16.0))


def road_patches():
    import roads2 as R2
    rc = L.RoadCurve("main")
    out = []
    for cam, back, ahead in PATCH_CAMS:
        ob = bpy.data.objects.get(cam)
        if ob is None:
            continue
        s0, dist = R2.s_of_point(rc, ob.location.x, ob.location.y)
        out.append(("patch_" + cam, s0 - back, s0 + ahead))
    return out


def step_ground2(names=None, yards=True):
    """New dirt / water / stone materials, then rebuild the road and yard meshes in place."""
    import materials2 as M2
    import roads2 as R2
    importlib.reload(M2)
    importlib.reload(R2)
    t0 = time.time()
    mats = M2.build()
    R2.disp_group()
    out = {}
    for name in (names or list(L.ROADS.keys())):
        patches = road_patches() if name == "main" else ()
        out[name] = R2.rebuild_road(name, mats["road"], mats["water"], patches=patches, patch_mat=mats["road_patch"])
        p2.log("road %s rebuilt %s" % (name, out[name]))
    if yards:
        for yd in L.YARDS:
            out["yard_%d" % yd["seed"]] = R2.build_yard2(yd, mats["road"], mats["water"], arcs=ARCS_STABLE if yd["seed"] == 901 else None)
    T._BVH.clear()
    out["seconds"] = round(time.time() - t0, 1)
    return out


def step_scatter2():
    """Straw bits / fallen leaves library, road stones re-coloured, then every road, patch and yard scatter layer."""
    import scatter2 as S2
    importlib.reload(S2)
    t0 = time.time()
    lib = S2.build_library()
    out = S2.road_scatter_all()
    out["lib"] = lib
    out["seconds"] = round(time.time() - t0, 1)
    p2.log("scatter2 done in %.0f s" % out["seconds"])
    return dict(lib=lib, removed=out["removed"], seconds=out["seconds"], n=len(out["stats"]))


def step_village2():
    """New cottages, crofts, field, trodden ground, meadow variety, crops; trees cleared where needed."""
    import terrain2 as T2
    import props2 as P2
    import buildmats as BM
    importlib.reload(T2)
    importlib.reload(P2)
    t0 = time.time()
    out = {}
    out["clones"] = T2.clone_buildings()
    pts = []
    for name, b in T2.NEW_BUILDINGS.items():
        pts.append((b["x"], b["y"], max(b["w"], b["d"]) / 2 + 4.5))
    for g in T2.GARDENS2:
        pts.append((g["x"], g["y"], max(g["w"], g["d"]) / 2 + 2.0))
    f = T2.FIELD
    for u in np.linspace(-0.5, 0.5, 7):
        for v in np.linspace(-0.5, 0.5, 4):
            lx, ly = u * f["width"], v * f["length"]
            c, s = math.cos(math.radians(f["rot"])), math.sin(math.radians(f["rot"]))
            pts.append((f["x"] + lx * c - ly * s, f["y"] + lx * s + ly * c, 4.0))
    # the conifer in front of cottage B as seen from the aerial camera
    bx, by = L.BUILDINGS["cottage_b"]["x"], L.BUILDINGS["cottage_b"]["y"]
    cam = bpy.data.objects["CamAerial"].location
    for t in np.linspace(0.08, 0.35, 8):
        pts.append((bx + (cam.x - bx) * t, by + (cam.y - by) * t, 5.0))
    out["trees_removed"] = T2.clear_trees_near(pts, None)
    out["birches_moved"] = T2.birches_to_broadleaf(0.95)
    out["lone_trees_moved"] = T2.lone_trees_to_oaks()
    out["field"] = T2.apply_field()
    out["masks"] = T2.masks2()
    T2.mat_terrain2()
    out["crops"] = T2.build_crop_library()
    T2.scatter_terrain2()
    mats = BM.build_all()
    mats["herb_mat"] = bpy.data.materials["herbs"]
    T._BVH.clear()
    out["gardens"] = P2.gardens2(mats)
    out["props"] = P2.new_cottage_props()
    out["haystacks"] = P2.rebuild_haystacks(mats)
    out["seconds"] = round(time.time() - t0, 1)
    p2.log("village2 done in %.0f s" % out["seconds"])
    return out


def step_buildings2(names=("cottage_a", "cottage_b", "cottage_c", "cottage_d", "stable")):
    """Rebuild the five buildings with the pass-2 parts and materials, then thatch relief and roof moss."""
    import bparts
    import buildmats
    import buildings
    import build
    import buildings2 as B2
    for m in (bparts, buildmats, buildings, build, B2):
        importlib.reload(m)
    t0 = time.time()
    out = {}
    for nm in names:
        info = build.step_building(nm)
        out[nm] = dict(objects=info.get("objects"), faces=info.get("faces"), s=round(info.get("seconds", 0), 1))
        p2.log("building %s rebuilt %s" % (nm, out[nm]))
    lt = bpy.data.objects.get("stable_fill")
    if lt is not None:
        bpy.data.objects.remove(lt, do_unlink=True)
    out["thatch"] = B2.apply_thatch_relief()
    out["moss"] = B2.roof_moss()
    out["seconds"] = round(time.time() - t0, 1)
    p2.log("buildings2 done in %.0f s" % out["seconds"])
    return out


# pass-2 framings (same subjects and roughly the same viewpoints as pass 1)
SHOTS2 = {
    # whole village from the south-west, as before
    # (pass 2b: aimed a little further south and 1 mm wider so the stone cottage's croft is not cut at the bottom)
    "CamAerial": dict(eye=(-48.0, -70.0), eye_h=70.0, tgt=(-4.0, -2.0), tgt_h=0.0, lens=28.0, abs_eye=True),
    # a little further back and turned left so cottage A sits whole in the left third; the fence leads in
    "CamRoad": dict(eye=(-44.0, -13.3), eye_h=1.62, tgt=(-14.0, 1.0), tgt_h=1.9, lens=26.0),
    # three-quarter view from the south-west: front and west gable, the whole roof, cart and trough in the yard
    "CamStable": dict(eye=(-3.0, 22.0), eye_h=1.62, tgt=(8.5, 30.0), tgt_h=2.1, lens=24.0),
    # further back: the whole roof and chimney, the barrel and bench whole, trodden ground at the door
    # (pass 2b: focused on the front wall at f/2.8, so grass near the lens is soft as in a photograph instead of
    # sharp flat strips that read as sticks; see pass2b.step_cottage_camera)
    "CamCottage": dict(eye=(-33.5, -5.6), eye_h=1.6, tgt=(-24.0, 5.0), tgt_h=2.9, lens=26.0, dof=(10.8, 2.8)),
    # unchanged road close-up
    "CamRoadClose": dict(eye=(-4.9, -5.55), eye_h=0.95, tgt=(-1.6, -4.85), tgt_h=0.0, lens=30.0, dof=(3.2, 5.6)),
}


def step_cameras(shots=None):
    import scene_setup as SS
    importlib.reload(SS)
    T._BVH.clear()
    return SS.make_cameras(shots or SHOTS2)


# per-shot haze (aerial perspective from the mist pass) and exposure
HAZE = {"CamAerial": 0.16, "CamRoad": 0.2, "CamStable": 0.12, "CamCottage": 0.12, "CamRoadClose": 0.08}
EXPOSURE = {"CamAerial": 0.6, "CamRoad": 0.55, "CamStable": 0.5, "CamCottage": 0.5, "CamRoadClose": 0.5}
HAZE_COLOUR = (0.36, 0.38, 0.42, 1.0)


def step_compositor():
    """Mist pass -> a little aerial haze over distant things (not the sky), so the far tree line is not a flat
    dark wall; strength set per shot by set_shot()."""
    sc = bpy.context.scene
    vl = sc.view_layers[0]
    vl.use_pass_mist = True
    ms = sc.world.mist_settings
    ms.start = 15.0
    ms.depth = 420.0
    ms.falloff = 'LINEAR'
    ng = bpy.data.node_groups.get("Comp_pass2")
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new("Comp_pass2", 'CompositorNodeTree')
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    N = ng.nodes
    rl = N.new('CompositorNodeRLayers')
    rl.scene = sc
    out = N.new('NodeGroupOutput')
    mist = rl.outputs.get('Mist')
    notsky = N.new('ShaderNodeMath')
    notsky.operation = 'LESS_THAN'
    notsky.inputs[1].default_value = 0.999
    ng.links.new(mist, notsky.inputs[0])
    amt = N.new('ShaderNodeMath')
    amt.operation = 'MULTIPLY'
    ng.links.new(mist, amt.inputs[0])
    ng.links.new(notsky.outputs[0], amt.inputs[1])
    strength = N.new('ShaderNodeMath')
    strength.name = "haze_strength"
    strength.operation = 'MULTIPLY'
    strength.inputs[1].default_value = 0.2
    ng.links.new(amt.outputs[0], strength.inputs[0])
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    mix.name = "haze_mix"
    ng.links.new(strength.outputs[0], mix.inputs['Factor'])
    ng.links.new(rl.outputs['Image'], mix.inputs[6])
    mix.inputs[7].default_value = HAZE_COLOUR
    ng.links.new(mix.outputs[2], out.inputs[0])
    sc.compositing_node_group = ng
    sc.render.use_compositing = True
    return dict(mist=mist is not None)


def set_shot(cam):
    """Camera, exposure, haze strength and which close-view road patch is subdivided for this shot."""
    sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam]
    sc.view_settings.exposure = EXPOSURE.get(cam, 0.5)
    ng = sc.compositing_node_group
    if ng is not None and "haze_strength" in ng.nodes:
        ng.nodes["haze_strength"].inputs[1].default_value = HAZE.get(cam, 0.15)
    for pc, lvl in (("road_patch_CamRoadClose", 2 if cam == "CamRoadClose" else 0), ("road_patch_CamRoad", 2 if cam == "CamRoad" else 0)):
        ob = bpy.data.objects.get(pc)
        if ob is not None and "relief" in ob.modifiers:
            C.set_mod_input(ob.modifiers["relief"], "Level", lvl)
    return cam
