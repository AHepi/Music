"""Stage 1: roads, puddles, terrain mesh."""
import math, time
import numpy as np
import bpy
from common import *
import layout, terrain

def setup_layout():
    R = layout.make_roads()
    layout.make_buildings()
    R1, R2, R3 = R['R1'], R['R2'], R['R3']
    sE = R1.s_at_x(-58)
    sR = R1.s_at_x(-40)
    R1.puddles = [(sE + 7.0, +1, 3.0, 0.07), (sE + 13.5, -1, 2.4, 0.065), (sR + 0.9, -1, 2.8, 0.07), (sR + 4.6, +1, 2.2, 0.06),
                  (R1.s_at_x(-24), -1, 2.6, 0.065), (R1.s_at_x(-8), +1, 3.0, 0.07), (R1.s_at_x(14), -1, 2.6, 0.065),
                  (R1.s_at_x(30), +1, 2.8, 0.07), (R1.s_at_x(52), -1, 2.4, 0.06), (R1.s_at_x(-75), +1, 2.6, 0.065)]
    R2.puddles = [(10.0, -1, 2.5, 0.065), (24.0, +1, 2.2, 0.06)]
    R3.puddles = [(14.0, +1, 2.0, 0.06)]
    for r in R.values():
        r.flatten_for_puddles()
    layout.POINTS_HINT['sR'] = sR
    layout.build_hoof()
    layout.POINTS = dict(sE=sE, sR=sR)
    zones = []
    for ds in (3.5, 6.5, 9.5, 12.5, 15.5):
        x, y, tx, ty = R1.point(sE + ds)
        zones.append((x, y, 3.2, 0.0625))
    for ds in (-2.0, 0.5, 3.0, 5.5):
        x, y, tx, ty = R1.point(sR + ds)
        zones.append((x, y, 3.0, 0.03125))
    zones.append((14.0, 32.5, 6.5, 0.0625))
    for r in R.values():
        for (s0, side, Lp, ex) in r.puddles:
            x, y, tx, ty = r.point(s0)
            zones.append((x, y, 2.4, 0.0625))
    return zones

def run_terrain(log):
    zones = setup_layout()
    me = terrain.build_mesh(zones, log=log)
    log.append('mesh built: %d verts %d faces' % (len(me.vertices), len(me.polygons)))
    out = terrain.shape_mesh(me, log=log)
    coll = get_coll('Terrain')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    ob = add_obj('Terrain', me, coll)
    pm, infos = terrain.build_puddles(me)
    log.append('puddles %s' % (infos,))
    pme = pm.build('Puddles')
    pob = add_obj('Puddles', pme, coll)
    return {'verts': len(me.vertices), 'faces': len(me.polygons), 'puddles': infos}
