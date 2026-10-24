"""Final renders: run inside a background Blender that has village.blend open."""
import bpy
import time
import os

WORK = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control-opus"
OUT = WORK + "/pictures"
LOG = WORK + "/render_log.txt"

SHOTS = [
    ("CamAerial", "01_village_from_above.jpg", 0.55, 128),
    ("CamRoad", "02_road_at_eye_height.jpg", 0.45, 128),
    ("CamStable", "03_stable_close.jpg", 0.45, 128),
    ("CamCottage", "04_cottage_close.jpg", 0.45, 128),
    ("CamRoadClose", "05_road_surface_closeup.jpg", 0.45, 160),
]


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def run(only=None, pct=100):
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 800
    sc.render.resolution_percentage = pct
    sc.render.use_persistent_data = True
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.adaptive_min_samples = 32
    sc.cycles.use_denoising = True
    sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    sc.cycles.denoising_prefilter = 'ACCURATE'
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 94
    sc.render.film_transparent = False
    for cam, fname, exposure, spp in SHOTS:
        if only and cam not in only:
            continue
        t = time.time()
        sc.camera = bpy.data.objects[cam]
        sc.view_settings.exposure = exposure
        sc.cycles.samples = spp
        sc.render.filepath = os.path.join(OUT, fname)
        log("start %s (%d spp)" % (cam, spp))
        bpy.ops.render.render(write_still=True)
        log("done %s in %.0f s -> %s" % (cam, time.time() - t, fname))
    log("ALL DONE")
