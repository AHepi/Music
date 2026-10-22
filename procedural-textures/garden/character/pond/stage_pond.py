# POND BUILDER (22 October character round): the stage. apply(options) works on the open starting scene (garden_real_fixed.blend) and touches only
# what the pond builder owns (see report.md). Idempotent: it first removes what an earlier run made (objects tagged g6p_new) and rebuilds the
# owned objects from fixed seeds, so running twice gives the same result.
# options: steps (list of 'water','bed','rims','plants','maple','pine'; default all), seed (int, 31), plus tuning keys used in g6p_water / g6p_trees.
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
