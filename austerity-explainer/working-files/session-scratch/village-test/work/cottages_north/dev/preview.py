import sys, math, bpy, time
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
outdir=args[0]; shots=args[1:]   # names like A_front
sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.samples=24
sc.cycles.use_denoising=False
sc.cycles.device='CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 427, 100
sc.render.image_settings.file_format='JPEG'; sc.render.image_settings.quality=80
sc.render.threads_mode='FIXED'; sc.render.threads=2
cams={ 'A_front':((-40,-2.0,3.2),(-32,10,1.9),32), 'A_back':((-24,19,5),(-32,10,2.2),32), 'A_west':((-46,13,2.6),(-37,9.8,1.8),35),
       'B_front':((-12,-1.5,3.0),(-6,9.5,2.2),32), 'B_east':((3,6,3.2),(-3.5,9.7,3.0),36), 'B_back':((-1,19,5),(-6,9.5,2.5),32),
       'A_close':((-33.5,3.6,1.8),(-33.2,7.6,1.4),40), 'B_close':((-6.5,3.2,1.7),(-6.0,7.2,1.3),40), 'roof_A':((-44,6.5,7.5),(-32,10,3.8),32), 'roof_B':((-12,3.5,7.0),(-6,9.5,4.0),32)}
for name in shots:
    loc,tgt,lens=cams[name]
    cam=bpy.data.cameras.new('Place cottages_north cam tmp'); cam.lens=lens; cam.clip_end=3000
    co=bpy.data.objects.new('Place cottages_north cam tmp', cam); sc.collection.objects.link(co)
    co.location=loc
    d=Vector(tgt)-Vector(loc); co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.camera=co
    sc.render.filepath=f'{outdir}/{name}.jpg'
    t=time.time(); bpy.ops.render.render(write_still=True); print('RENDERED',name,round(time.time()-t,1))
    bpy.data.objects.remove(co); bpy.data.cameras.remove(cam)
