"""Small rig for previewing one asset on a plain ground, away from the main village (placed at 200,200)."""
import math
import numpy as np
import bpy
from common import *
import scene_setup

OX, OY = 200.0, 200.0

def prep(sun_az=215, sun_el=30, exposure=-2.6):
    coll = get_coll('Test')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for nm in ('Terrain', 'Puddles'):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
    gmb = MB(); gmb.quads_hard(np.array([[[-40, -40, 0], [40, -40, 0], [40, 40, 0], [-40, 40, 0]]]), mat=0)
    gm = MatB('tmp_ground'); gm.finish(gm.principled((0.04, 0.065, 0.02), 0.95))
    gme = gmb.build('tmpground', [gm.m])
    add_obj('tmpground', gme, coll, loc=(OX, OY, 0))
    scene_setup.setup_world(sun_az=sun_az, sun_el=sun_el)
    return coll

def place(name, me, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    coll = get_coll('Test')
    return add_obj(name, me, coll, loc=(OX + loc[0], OY + loc[1], loc[2]), rot=rot, scale=scale)

def shots(jobname, specs, exposure=-2.6, w=640, h=427, samples=24):
    """specs: list of (file, cam_pos(rel), target(rel), lens)"""
    coll = get_coll('Test')
    out = []
    for i, (fn, cp, tg, lens) in enumerate(specs):
        cname = 'TCam%d' % i
        scene_setup.make_camera(cname, (OX + cp[0], OY + cp[1], cp[2]), (OX + tg[0], OY + tg[1], tg[2]), lens=lens, coll=coll)
        out.append(dict(cam=cname, path=PREV + '/' + fn, w=w, h=h, samples=samples, exposure=exposure))
    return render_many(jobname, out)
