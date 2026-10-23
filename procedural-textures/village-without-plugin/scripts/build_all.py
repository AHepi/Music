"""Master build: every stage, re-runnable. Use run_async('all', build_all.run, log, stages)."""
import time
import numpy as np
import bpy
from common import *
import layout, terrain, stage1, stage2, stage3, materials, assemble, forest, cams, scene_setup

HAZE = 0.0
CLOUDS = 0.35
HAZE_BOX = 0.0035
ALL = ('clear', 'mats', 'terrain', 'stage2', 'forest', 'grass', 'flowers', 'debris', 'finish')

def run(log, stages=ALL, sun_az=222.0, sun_el=31.0):
    t0 = time.time()
    res = {}
    if 'clear' in stages:
        clear_scene()
        materials.MATS.clear()
        log.append('cleared %.1fs' % (time.time() - t0))
    if 'mats' in stages:
        materials.make_building_mats(); materials.make_plant_mats()
        materials.ground(); materials.water()
        log.append('materials %.1fs' % (time.time() - t0))
    if 'terrain' in stages:
        res['terrain'] = stage1.run_terrain(log)
        g = bpy.data.materials['Ground']; w = bpy.data.materials['PuddleWater']
        terr = bpy.data.objects['Terrain']; terr.data.materials.clear(); terr.data.materials.append(g)
        pud = bpy.data.objects['Puddles']; pud.data.materials.clear(); pud.data.materials.append(w)
        log.append('terrain %.1fs' % (time.time() - t0))
    else:
        assemble.ensure_layout()
    if 'stage2' in stages:
        res['stage2'] = stage2.run(log)
        log.append('stage2 %.1fs' % (time.time() - t0))
    forest.SUN_AZ = sun_az
    if 'forest' in stages:
        res['forest'] = stage3.run_forest(log)
        log.append('forest %.1fs' % (time.time() - t0))
    if 'grass' in stages:
        res['grass'] = stage3.run_grass(log)
        log.append('grass %.1fs' % (time.time() - t0))
    if 'flowers' in stages:
        res['flowers'] = stage3.run_flowers(log)
        log.append('flowers %.1fs' % (time.time() - t0))
    if 'debris' in stages:
        res['debris'] = forest.scatter_road_debris(log)
        log.append('debris %.1fs' % (time.time() - t0))
    if 'finish' in stages:
        res['cams'] = cams.make_all()
        stb = [x for x in layout.BUILDINGS if x['name'] == 'Stable'][0]
        res['lights'] = scene_setup.add_stable_lights(stb, assemble.l2w)
        res['world'] = scene_setup.setup_world(sun_az=sun_az, sun_el=sun_el, haze=HAZE, clouds=CLOUDS)
        scene_setup.add_haze_box(HAZE_BOX)
        scene_setup.setup_render(1200, 800, 128, exposure=-2.4)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        log.append('saved %.1fs' % (time.time() - t0))
    return res
