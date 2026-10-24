import bpy
sc = bpy.context.scene
r = sc.render
print("DBG comp device", getattr(r, 'compositor_device', None), getattr(r, 'compositor_precision', None), flush=True)
r.resolution_x, r.resolution_y, r.resolution_percentage = 120, 80, 100
sc.cycles.samples = 1
sc.cycles.use_denoising = False
r.use_compositing = False
r.filepath = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-4k/opus_work/checks/dbg.jpg'
print("DBG render start", flush=True)
bpy.ops.render.render(write_still=True)
print("DBG render ok", flush=True)
