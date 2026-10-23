"""Stage 3: tree library, forest, undergrowth, grass."""
import time, math
import numpy as np
import bpy
from common import *
import layout, forest, assemble

def run_forest(log):
    assemble.ensure_layout()
    t0 = time.time()
    forest.build_library(log)
    log.append('library %.1fs' % (time.time() - t0))
    r1 = forest.place_trees(log)
    log.append('trees placed %.1fs' % (time.time() - t0))
    r2 = forest.place_undergrowth(log)
    log.append('undergrowth %.1fs' % (time.time() - t0))
    return {'trees': r1, 'under': r2}

def grass_zones():
    R1 = layout.ROADS['R1']
    sE = layout.POINTS['sE']; sR = layout.POINTS['sR']
    zones = []
    for ds in (6, 18, 30, 42):
        x, y, tx, ty = R1.point(sE + ds)
        zones.append((x, y, 11.0, 1.0))
    x, y, tx, ty = R1.point(sR + 2)
    zones.append((x, y, 7.0, 1.3))
    B = {b['name']: b for b in layout.BUILDINGS}
    c1 = B['Cottage1']
    zones.append((c1['x'], c1['y'] - 4.0, 13.0, 1.0))
    st = B['Stable']
    zones.append((st['x'], st['y'] - 9.0, 15.0, 1.0))
    zones.append((10.0, 3.0, 11.0, 0.9))
    zones.append((B['Cottage3']['x'], B['Cottage3']['y'] - 3.0, 11.0, 0.8))
    zones.append((B['Cottage2']['x'], B['Cottage2']['y'] + 3.0, 10.0, 0.8))
    return zones

def run_grass(log):
    assemble.ensure_layout()
    return forest.scatter_grass(log, zones=grass_zones())


def run_flowers(log):
    assemble.ensure_layout()
    return forest.scatter_flowers(log, zones=grass_zones())
