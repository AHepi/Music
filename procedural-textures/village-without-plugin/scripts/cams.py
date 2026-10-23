"""Final camera set (planned positions are also used to keep trees out of the frame)."""
import math
import numpy as np
import bpy
from common import *
import layout, scene_setup, assemble

def ground(x, y):
    return assemble.gz(x, y)

def plan():
    assemble.ensure_layout()
    R1 = layout.ROADS['R1']
    sE = layout.POINTS['sE']; sR = layout.POINTS['sR']
    B = {b['name']: b for b in layout.BUILDINGS}
    P = {}
    P['Cam_Aerial'] = dict(loc=(6, -106, 82), target=(14, 4, 0), lens=35)
    x, y, tx, ty = R1.point(sE); nx, ny = -ty, tx
    cx, cy = x + nx * 0.15, y + ny * 0.15
    x2, y2, _, _ = R1.point(sE + 45)
    P['Cam_Eye'] = dict(loc=(cx, cy, ground(cx, cy) + 1.65), target=(x2, y2, ground(x2, y2) + 1.55), lens=28)
    st = B['Stable']
    cam_st = (st['x'] - 11.5, st['y'] - 14.0)
    P['Cam_Stable'] = dict(loc=(cam_st[0], cam_st[1], ground(*cam_st) + 1.65), target=(st['x'] - 0.5, st['y'] - 2.0, st['pad_z'] + 1.6), lens=32)
    c1 = B['Cottage1']
    cam_c = assemble.l2w(c1, -5.0, -10.4)
    tg = assemble.l2w(c1, -0.3, -2.3)
    P['Cam_Cottage'] = dict(loc=(cam_c[0], cam_c[1], ground(*cam_c) + 1.7), target=(tg[0], tg[1], c1['pad_z'] + 2.2), lens=30)
    x, y, tx, ty = R1.point(sR - 2.8); nx, ny = -ty, tx
    cx, cy = x + nx * 0.1, y + ny * 0.1
    x2, y2, _, _ = R1.point(sR + 1.2)
    P['Cam_Road'] = dict(loc=(cx, cy, ground(cx, cy) + 0.95), target=(x2, y2, ground(x2, y2)), lens=40, fstop=4.0)
    return P

def make_all():
    P = plan()
    out = []
    for nm, d in P.items():
        scene_setup.make_camera(nm, d['loc'], d['target'], lens=d['lens'], fstop=d.get('fstop'))
        out.append(nm)
    return out
