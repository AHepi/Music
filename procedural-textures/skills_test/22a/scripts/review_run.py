# What this does (plain words): makes the "review contact sheets" of the skill scenario-blender-expert (bx_review.py) for the street copy. It draws with Blender's plain fast
# Workbench renderer (not the film's EEVEE) and changes and saves nothing in the .blend.
# Four jobs, chosen by the word after "--" and the output folder:
#   stock    = the skill's own review() exactly as it ships: several fixed views of the street objects, rows = looks (silhouette / clay / wire ...).
#   focus    = the same review() but zoomed on the first stretch of street with the skill's "focus" option, plus the "normals" look that shows flipped faces.
#   camera   = NOT in the skill: review() can only use its own fixed views, so this uses the skill's own helper functions to draw the same looks from the film's main camera.
#   cull     = the skill's tip for inside-out parts: the parts the audit called inside-out, drawn with back faces visible and then hidden (back-face culling), like a game engine does.
# Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec --factory-startup --python-exit-code 1 STREET.blend -P review_run.py -- JOB OUT_FOLDER
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy  # noqa: E402
import bx_review  # noqa: E402

job, out = sys.argv[sys.argv.index('--') + 1:][:2]
scene0 = bpy.context.scene
meshes = [o for o in scene0.objects if o.type == 'MESH']
street = [o for o in meshes if not o.name.startswith(('sky_dome', 'moorland_hills', 'ground', 'spoil_heap'))]
started = time.time()


def camera_sheet(objs, out_dir, modes, width, height):
    """The skill's own steps (temporary scene, look set-up, wire copies, tiling) but with the scene's main camera instead of the skill's fixed views."""
    os.makedirs(out_dir, exist_ok=True)
    sc, cam, world = bx_review._setup_scene(objs, 100)
    sc.render.resolution_x, sc.render.resolution_y = width, height
    src = scene0.camera
    for name in ('type', 'lens', 'sensor_fit', 'sensor_width', 'sensor_height', 'shift_x', 'shift_y', 'clip_start', 'clip_end'):
        setattr(cam.data, name, getattr(src.data, name))
    cam.matrix_world = src.matrix_world.copy()
    wires = bx_review._make_wires(sc, objs) if 'wire' in modes else []
    paths, labels = [], []
    try:
        for mode in modes:
            bx_review._set_mode(sc, world, mode, objs, wires)
            p = os.path.join(out_dir, f'{mode}_main_camera.png')
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True, scene=sc.name)
            paths.append(p)
            labels.append(f'{mode} / main_camera')
        sheet = bx_review._tile(paths, 1, len(modes), os.path.join(out_dir, 'main_camera_sheet.png'), labels)
    finally:
        for w in wires:
            bpy.data.objects.remove(w)
        bx_review._cleanup(sc, cam, world)
    return sheet


if job == 'stock':
    # the skill's defaults: views front/right/threequarter/back, looks silhouette/clay/wire, res 800 here cut to 400 as the skill advises for a 1600 px sheet
    print('SHEET', bx_review.review(street, out, res=400))
elif job == 'focus':
    print('SHEET', bx_review.review(street, out, views=('front', 'threequarter', 'right', 'low'), modes=('silhouette', 'matcap', 'normals', 'wire'), res=400, focus=((0.0, 16.0, 4.0), 14.0)))
elif job == 'camera':
    print('SHEET', camera_sheet([o for o in meshes if o.name != 'sky_dome'], out, ('silhouette', 'matcap', 'normals', 'wire'), 540, 960))
elif job in ('cull_off', 'cull_on'):
    original = bx_review._setup_scene

    def patched(objs, res):
        sc, cam, world = original(objs, res)
        sc.display.shading.show_backface_culling = (job == 'cull_on')
        return sc, cam, world
    bx_review._setup_scene = patched
    names = ('headframe_lattice', 'winding_wheel_left', 'winding_wheel_right', 'engine_house_trim')
    objs = [bpy.data.objects[n] for n in names]
    print('SHEET', bx_review.review(objs, out, views=('front', 'threequarter'), modes=('matcap', 'normals'), res=500, focus=((0.0, 86.0, 13.0), 13.0)))
print('REVIEW_DONE', job, 'seconds', round(time.time() - started, 1), flush=True)
