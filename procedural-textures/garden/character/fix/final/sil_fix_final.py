"""sil_fix_final.py - silhouette masks (alpha PNG) of object groups at the hero and veranda cameras, on a card, inside Blender.
   blender -b --disable-autoexec SCENE.blend -P sil_fix_final.py -- JOB.json
JOB.json = {"outdir": "...", "prefix": "before_"|"after_", "size": "1200x800", "cameras": {"hero": "photo", "veranda": "veranda"},
            "groups": {"bridge": ["Astra / varied planks", ...], ...}}
All meshes and curves whose name does not start with one of the group's prefixes become holdouts; film is transparent; Cycles 4 samples, no denoise."""
import bpy, sys, os, json
sys.dont_write_bytecode = True
FS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final/stage'
sys.path.insert(0, FS)
import render_job   # noqa
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
sc = bpy.context.scene
w, h = [int(v) for v in job.get('size', '1200x800').split('x')]
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.samples = 4; cy.use_denoising = False; cy.use_adaptive_sampling = False; cy.seed = 7
render_job.pick_device(sc, False)
sc.render.film_transparent = True
ims = sc.render.image_settings
ims.media_type = 'IMAGE'; ims.file_format = 'PNG'; ims.color_mode = 'RGBA'; ims.color_depth = '8'; ims.color_management = 'FOLLOW_SCENE'
os.makedirs(job['outdir'], exist_ok=True)
counts = {}
for gname, prefs in job['groups'].items():
    prefs = tuple(prefs)
    held = []
    n_keep = 0
    for ob in bpy.data.objects:
        if ob.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT'):
            if ob.name.startswith(prefs):
                n_keep += 1
            else:
                held.append((ob, ob.is_holdout)); ob.is_holdout = True
    counts[gname] = n_keep
    for cname, camname in job['cameras'].items():
        sc.camera = bpy.data.objects[camname]
        path = os.path.join(job['outdir'], '%s%s_%s.png' % (job.get('prefix', ''), gname, cname))
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
    for ob, o in held:
        ob.is_holdout = o
print('SIL_DONE', json.dumps(counts), flush=True)
