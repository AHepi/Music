"""Stage 2: buildings, props, fences."""
import time
import numpy as np
import bpy
from common import *
import layout, materials, assemble

def ensure_mats():
    need = [n for n in ('Plaster', 'Bark', 'Leaf') if bpy.data.materials.get(n) is None]
    if need:
        materials.MATS.clear()
        materials.make_building_mats()
        materials.make_plant_mats()

def run(log):
    ensure_mats()
    assemble.ensure_layout()
    t0 = time.time()
    b = assemble.build_buildings(log)
    log.append('buildings %.1fs' % (time.time() - t0))
    p = assemble.build_props(log)
    log.append('props %d %.1fs' % (len(p), time.time() - t0))
    f = assemble.build_fences(log)
    log.append('fences %s %.1fs' % (f, time.time() - t0))
    return {'buildings': b, 'props': len(p), 'fences': f}
