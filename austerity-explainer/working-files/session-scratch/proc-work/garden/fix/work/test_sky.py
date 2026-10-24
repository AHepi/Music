import bpy, sys, os, math, time
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/fix/stage')
import stage_light
t=time.time()
look = sys.argv[sys.argv.index('--')+1]
out = sys.argv[sys.argv.index('--')+2]
stage_light.build_world(look, 'golden', 7)
print('world built', time.time()-t)
sc = bpy.context.scene
for ob in bpy.data.objects:
    if ob.type in ('MESH','CURVE'):
        ob.hide_render = True
sc.camera = bpy.data.objects['veranda']
sc.render.engine='CYCLES'
sc.cycles.device='CPU'
sc.cycles.samples=6
sc.cycles.use_denoising=False
sc.render.resolution_x=900; sc.render.resolution_y=600; sc.render.resolution_percentage=100
sc.render.use_compositing=False
sc.render.filepath = out
sc.render.image_settings.file_format='PNG'
bpy.ops.render.render(write_still=True)
print('rendered', time.time()-t)
