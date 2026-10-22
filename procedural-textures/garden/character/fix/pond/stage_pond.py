# POND FIX ROUND (22 October, owner 'pond'): the fixed stage. Same name and apply(options) as the builder's; changes are in g6p_water.py (pond reads at 1200 px: bigger greener notched
# lily pads, bigger flowers, clearer shelf with brighter pebbles, larger ripple rings, floating red leaves in the visible water), g6p_trees.py (maple lifted toward the previous final's
# colour with softer pads and a window to two branches; pine with a shorter fringe of broad brush-stroke clumps and plated bark that reads) and g6p_maps.py (ripple map, pine plate shade).
# POND BUILDER (22 October character round): the stage. apply(options) works on the open starting scene (garden_real_fixed.blend) and touches only
# what the pond builder owns (see report.md). Idempotent: it first removes what an earlier run made (objects tagged g6p_new) and rebuilds the
# owned objects from fixed seeds, so running twice gives the same result.
# options: steps (list of 'water','bed','rims','plants','maple','pine'; default all), seed (int, 31), plus tuning keys used in g6p_water / g6p_trees.
# Dials added or changed in the fix round (all with the defaults used for the finals):
#   water/plants: pad_radius_scale 1.12, pad_clusters, flower_pads, bud_pads, flower_scale, flower_emit 0.14, pad_emit 0.12, pebble_emit 0.06, murk_from 0.24, murk_to 0.40,
#                 murk_share 0.50, float_leaf_spots, float_leaf_scale, iris_flower_scale 1.45
#   maple: maple_windows True, maple_window_branches [3, 4], maple_window_radius 0.11, maple_window_from 0.45, maple_thick_scale 0.82, maple_tone_mean 1.13, maple_tone_sd 0.14,
#          maple_hue_noise 0.09, maple_hue_freq 1.7, maple_fringe 0.07, maple_bump 1.0, maple_emit 0.06, maple_old_hue_blend 1.0, maple_old_nn True, maple_old_noise 0.02,
#          maple_old_tone_blend 0, maple_old_normal_blend 0, maple_sun_bias 0, maple_wr_scale 1.0, maple_tail_drop 0.30, bark_lift (1.15, 0.98, 0.90), bark_emit 0.07
#   pine: pine_needle_tris 52000, pine_K 4, pine_width 0.018, pine_len 1.0, pine_rim_len 1.12, pine_rnd 0.5, pine_tip_light 1.3, pine_plates 0.075, pine_plates_gain 1.45
# Data files next to the stage: maps/ (six pictures made by g6p_maps.py, and maple_old_crown.npz = positions and colour positions of the previous final's maple leaves).
import bpy
import sys
import os
import json
import time
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import g6p_common as C            # noqa: E402
import g6p_water as W             # noqa: E402
for _m in (C, W):
    importlib.reload(_m)
try:
    import g6p_trees as T         # noqa: E402
    importlib.reload(T)
except ImportError:
    T = None

ALL_STEPS = ['water', 'bed', 'rims', 'plants', 'maple', 'pine']


class Ctx:
    pass


def apply(options=None):
    t0 = time.time()
    opts = dict(options or {})
    C.REP.__init__()
    ctx = Ctx()
    ctx.opts = opts
    ctx.seed = int(opts.get('seed', 31))
    steps = opts.get('steps') or ALL_STEPS
    before_o, before_m = C.snapshot_names()
    gone = C.remove_previous()
    if gone:
        C.say('re-run: removed %d objects an earlier run made' % len(gone))
        C.REP.deleted.extend(gone)
    C.collection()
    ctx.ground = C.Ground()
    ctx.leaf_mat = W.leaf_material()
    if 'water' in steps:
        W.step_water(ctx)
    if 'bed' in steps:
        W.step_bed(ctx)
    elif 'plants' in steps:
        raise RuntimeError("step 'plants' needs 'bed' (it reads the bed height)")
    if 'rims' in steps:
        W.step_rims(ctx)
    if 'plants' in steps:
        W.step_plants(ctx)
    if 'maple' in steps and T is not None:
        T.step_maple(ctx)
    if 'pine' in steps and T is not None:
        T.step_pine(ctx)
    if opts.get('cameras', True):
        for (nm, loc, tgt, lens) in C.G6_CAMERAS:
            C.make_camera(nm, loc, tgt, lens)
    after_o, after_m = C.snapshot_names()
    rep = dict(created=sorted(set(after_o) - set(before_o)), removed=sorted(set(before_o) - set(after_o)), new_materials=sorted(set(after_m) - set(before_m)),
               numbers=C.REP.numbers, notes=C.REP.notes, seconds=round(time.time() - t0, 1), changed=C.REP.changed)
    print('POND_STAGE_DONE', json.dumps({k: (v if k != 'notes' else len(v)) for k, v in rep.items() if k in ('seconds',)}), flush=True)
    return rep
