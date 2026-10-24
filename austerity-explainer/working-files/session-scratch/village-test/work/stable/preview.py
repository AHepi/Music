import sys, math, bpy, time
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
outdir=args[0]; shots=args[1:]
sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.samples=12
sc.cycles.use_denoising=False
sc.cycles.device='CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 600, 400, 100
sc.render.image_settings.file_format='JPEG'; sc.render.image_settings.quality=80
sc.render.threads_mode='FIXED'; sc.render.threads=2
import os
if os.environ.get('NOROOF'):
    for o in bpy.data.objects:
        if o.get('place_owner')=='stable' and any(k in o.name for k in ('shingles','rafters','purlin','ridge piece','queen','cladding')):
            o.hide_render=True
cams={ 'close':('View stable_close',None,None,None),
       'south':((24,24,2.2),(24,39,1.8),30),
       'west_in':((18.0,33,3.0),(24,39,1.6),32),
       'ne':((34,46,6),(24,39,2.4),34),
       'inside':((24,36.9,1.7),(24,40.8,1.5),22),
       'inside2':((20.0,37.0,1.7),(24.5,41.6,1.3),24),
       'roof':((24,30,8.5),(24,39,4),32),
       'yard':((33,31,1.8),(28,35,0.5),30),
       'top':((24,33,12),(24,39.5,0.5),34),'stalls':((24,37.0,3.2),(24,41,0.8),30),'stalls2':((19.8,37.2,2.6),(26,41.4,1.2),24),'doors':((24,31.5,1.7),(24,36,1.3),30)}
for name in shots:
    spec=cams[name]
    if isinstance(spec[0],str):
        sc.camera=bpy.data.objects[spec[0]]
    else:
        loc,tgt,lens=spec
        cam=bpy.data.cameras.new('Place stable cam tmp'); cam.lens=lens; cam.clip_end=3000
        co=bpy.data.objects.new('Place stable cam tmp', cam); sc.collection.objects.link(co)
        co.location=loc
        d=Vector(tgt)-Vector(loc)
        co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
        sc.camera=co
    sc.render.filepath=f'{outdir}/{name}.jpg'
    t=time.time(); bpy.ops.render.render(write_still=True); print('RENDER',name,round(time.time()-t,1),'s')
