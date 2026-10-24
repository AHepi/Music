"""Pass 2, second half (after the computer restarted at about 05:28): fixes made after re-checking every view.

Run inside the connected Blender with village.blend open, in this order (each step can be re-run on its own):
    exec(open(SRC + '/run.py').read()); import pass2b
    pass2b.step_roads()            # worn wheel bands, fuller grass crown and verge, big mud-hole puddles, broken clods,
                                   # crumbled rut lips, pale dry / dark wet ruts, wet shine in separate dips, more grit,
                                   # a grass-and-moss ground colour that fades in with distance (roads2/materials2/scatter2)
    pass2b.step_stable()           # back-wall windows, more missing boards, limewashed stalls
    pass2b.step_haystacks()        # pointed caps, clumpy slumped bodies, weathered hay, varied sizes and placing
    pass2b.step_cameras()          # aerial aimed further south, 28 mm
    pass2b.step_cottage_a()        # ragged thatch eave (bparts); straw-coloured cut ends (buildmats)
    pass2b.step_trees()            # two stick-like trees at the forest edge removed
    pass2b.step_cottage_camera()   # no tall blades within 1.5 m of the cottage lens; f/2.8 focused on the wall
    pass2b.step_stable_yard()      # hoof prints where horses walk; darker yard puddle water; water faces up
    import render_final; render_final.run()     # 4 diffuse bounces
Every step writes to pass2_log.txt (p2.log) so progress can be watched from outside Blender.
"""
import bpy
import time
import importlib
import traceback
import p2


def _run(label, fn, *a, **kw):
    t0 = time.time()
    try:
        out = fn(*a, **kw)
        p2.log("%s done in %.0f s %s" % (label, time.time() - t0, out if out is not None else ""))
        return out
    except Exception:
        p2.log("%s FAILED %s" % (label, traceback.format_exc()))
        raise


def step_roads():
    import pass2
    importlib.reload(pass2)

    def go():
        res = pass2.step_ground2()
        sc = pass2.step_scatter2()
        return dict(puddles={k: v for k, v in res.items() if k.startswith("yard") or k == "seconds"}, scatter=sc.get("n"))
    return _run("roads2b", go)


def tests(cams, tag, pct=50, spp=24):
    for cam in cams:
        p2.test_render(cam, name="%s_%s" % (tag, cam), pct=pct, spp=spp)
    p2.log("BATCH %s DONE" % tag)


def step_stable():
    """Stable rebuilt with a small window high in the back wall of each stall and more missing boards: real daylight
    into the empty stalls (the pass-1 hidden fill light is gone, and pass 2a left the stalls black)."""
    import pass2
    importlib.reload(pass2)
    return _run("stable2b", lambda: pass2.step_buildings2(names=("stable",)))


def step_haystacks():
    """Haystacks with a pointed cap, a slumped clumpy body and weathered grey-brown forkfuls of hay."""
    import props2 as P2
    import buildmats as BM
    import terrain as T
    importlib.reload(P2)

    def go():
        mats = BM.build_all()
        mats["herb_mat"] = bpy.data.materials["herbs"]
        T._BVH.clear()
        return P2.rebuild_haystacks(mats)
    return _run("haystacks2b", go)


def step_cameras():
    """Aerial aimed a little further south so the stone cottage and its croft at the bottom are not cut by the frame."""
    import pass2
    importlib.reload(pass2)
    shots = dict(pass2.SHOTS2)
    shots["CamAerial"] = dict(eye=(-48.0, -70.0), eye_h=70.0, tgt=(-4.0, -2.0), tgt_h=0.0, lens=28.0, abs_eye=True)
    pass2.SHOTS2.update(shots)
    return _run("cameras2b", lambda: pass2.step_cameras({"CamAerial": shots["CamAerial"]}))


def step_cottage_a():
    """Cottage A rebuilt: the thatch eave's lower edge wavers and its thickness varies (not machine-straight)."""
    import pass2
    importlib.reload(pass2)
    return _run("cottage_a2b", lambda: pass2.step_buildings2(names=("cottage_a",)))


def step_trees():
    """Remove a thin, sparse beech and oak at the forest edge above the paddock and the stable: from the air their
    sunlit trunks read as sticks standing alone (the judges' 'stick props that look pasted on')."""
    import terrain2 as T2
    importlib.reload(T2)
    return _run("trees2b", lambda: T2.clear_trees_near([(33.1, 46.5, 1.2), (9.5, 42.5, 1.2)], None))


def step_cottage_camera():
    """Cottage view: the photographer stands on trodden grass (no tall blades within 1.5 m of the lens - up close they
    rendered as sharp flat pale strips like sticks), and the lens is focused on the front wall at f/2.8, so what grass
    is near is soft as in a photograph."""
    import numpy as np
    from common import smoothstep

    def go():
        cam = bpy.data.objects["CamCottage"]
        cx, cy = cam.location.x, cam.location.y
        ter = bpy.data.objects["terrain"]
        me = ter.data
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ter.matrix_world)
        w = co @ M[:3, :3].T + M[:3, 3]
        keep = smoothstep(1.1, 1.8, np.hypot(w[:, 0] - cx, w[:, 1] - cy))
        changed = 0
        for nm in ("d_tall", "d_dry", "d_weeds", "d_flowers", "d_nettles"):
            if nm not in me.attributes:
                continue
            a = np.zeros(n)
            me.attributes[nm].data.foreach_get("value", a)
            me.attributes[nm].data.foreach_set("value", (a * keep).astype(np.float32))
            changed += 1
        me.update()
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = 10.8
        cam.data.dof.aperture_fstop = 2.8
        return dict(attrs=changed, cleared=int((keep < 0.5).sum()))
    return _run("cottage_cam2b", go)


def step_stable_yard():
    """Stable yard rebuilt with the hoof prints concentrated where horses walk and stand (pass 2a sprinkled them
    evenly over the whole yard, like dots), then the road and yard scatter layers again."""
    import roads2 as R2
    import scatter2 as S2
    import layout as L
    import terrain as T
    import pass2
    importlib.reload(R2)
    importlib.reload(S2)

    import materials2 as M2
    importlib.reload(M2)

    def go():
        yd = [y for y in L.YARDS if y["seed"] == 901][0]
        # the yard's shallow puddles in a darker water, so they read as dark water holding reflections and not as
        # flat brown patches next to the sky-sheened wet mud
        wy = M2.mat_water2("puddle_water_yard", shallow_hex='2b2219', deep_hex='18120c', depth_full=0.02)
        r = R2.build_yard2(yd, bpy.data.materials["road_dirt"], wy, arcs=pass2.ARCS_STABLE)
        T._BVH.clear()
        S2.road_scatter_all()
        return r
    return _run("stable_yard2b", go)
