"""Pass-2 helpers: logging, quick test renders, saving."""
import bpy
import os
import time

WORK = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control-opus"
TEST = WORK + "/test_pass2"
LOG = WORK + "/pass2_log.txt"
BLEND = WORK + "/village.blend"

EXPOSURE = {"CamAerial": 0.55, "CamRoad": 0.45, "CamStable": 0.45, "CamCottage": 0.45, "CamRoadClose": 0.45}


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + str(msg) + "\n")


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    log("saved " + BLEND)
    return BLEND


def test_render(cam, name=None, pct=25, spp=24, border=None, exposure=None, denoise=True):
    """Quick low-resolution check render of one camera. border=(xmin, xmax, ymin, ymax) in 0..1 crops."""
    os.makedirs(TEST, exist_ok=True)
    sc = bpy.context.scene
    try:
        import pass2
        pass2.set_shot(cam)
    except Exception as e:
        log("set_shot failed: %s" % e)
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 800
    sc.render.resolution_percentage = pct
    sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = denoise
    if exposure is not None:
        sc.view_settings.exposure = exposure
    if border:
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = border
    else:
        sc.render.use_border = False
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 90
    out = os.path.join(TEST, (name or cam) + ".jpg")
    sc.render.filepath = out
    t = time.time()
    log("test start %s pct=%d spp=%d" % (cam, pct, spp))
    bpy.ops.render.render(write_still=True)
    sc.render.use_border = False
    dt = time.time() - t
    log("test done %s in %.0f s -> %s" % (cam, dt, out))
    return dict(out=out, seconds=round(dt, 1))
