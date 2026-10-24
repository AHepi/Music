"""Final renders (pass 2): run inside the connected Blender that has village.blend open.

    import render_final; render_final.run()            # all five
    import render_final; render_final.run(["CamRoad"])  # one
Each shot sets its own exposure, haze and close-road patch subdivision (pass2.set_shot), renders at 1200 x 800 and
writes a JPG into pictures/. Progress goes to render_log.txt so it can be watched from outside Blender.
"""
import bpy
import time
import os
import importlib

WORK = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control-opus"
OUT = WORK + "/pictures"
LOG = WORK + "/render_log.txt"

SHOTS = [
    ("CamAerial", "01_village_from_above.jpg", 160),
    ("CamRoad", "02_road_at_eye_height.jpg", 160),
    ("CamStable", "03_stable_close.jpg", 160),
    ("CamCottage", "04_cottage_close.jpg", 160),
    ("CamRoadClose", "05_road_surface_closeup.jpg", 192),
]


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def run(only=None, pct=100):
    import pass2
    importlib.reload(pass2)
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 800
    sc.render.resolution_percentage = pct
    sc.render.use_border = False
    sc.render.use_persistent_data = False
    sc.cycles.diffuse_bounces = 4          # pass 2b: one more bounce so daylight carries into the stalls and doorways
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.adaptive_min_samples = 48
    sc.cycles.use_denoising = True
    sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    sc.cycles.denoising_prefilter = 'ACCURATE'
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 94
    sc.render.film_transparent = False
    for cam, fname, spp in SHOTS:
        if only and cam not in only:
            continue
        t = time.time()
        pass2.set_shot(cam)
        sc.cycles.samples = spp
        sc.render.filepath = os.path.join(OUT, fname)
        log("start %s (%d spp)" % (cam, spp))
        bpy.ops.render.render(write_still=True)
        log("done %s in %.0f s -> %s" % (cam, time.time() - t, fname))
    log("ALL DONE")
