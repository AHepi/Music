# Local quick look: apply stage, hide heavy leaf/moss objects, Cycles CPU small. args: look out.png camera width samples [apply opts json]
import bpy, sys, json, time, math
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/garden/light')
import stage_light
a = sys.argv[sys.argv.index('--')+1:]
look, out, camname, width, samples = a[0], a[1], a[2], int(a[3]), int(a[4])
opts = {'look': look}
if len(a) > 5: opts.update(json.loads(a[5]))
if look != 'none': stage_light.apply(opts)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name in ('Maple leaves', 'Pine pads', 'Bamboo leaves', 'Fallen leaves') : o.hide_render = True
cam = bpy.data.objects.get(camname) or bpy.data.objects.get('Camera'); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = False
sc.render.resolution_x = width; sc.render.resolution_y = int(width * 2 / 3); sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print('RENDER_SECONDS', round(time.time() - t, 1))
