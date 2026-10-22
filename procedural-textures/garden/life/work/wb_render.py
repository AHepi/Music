# Workbench quick look. Args: out.png [res_x] [camera: Camera|<custom x,y,z,tx,ty,tz,lens>] [engine WORKBENCH|BLENDER_EEVEE]
import bpy, sys, math
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]
out=argv[0]; rx=int(argv[1]) if len(argv)>1 else 640
sc=bpy.context.scene
cam=sc.camera
if len(argv)>2 and argv[2]!='Camera':
    x,y,z,tx,ty,tz,lens=[float(v) for v in argv[2].split(',')]
    cd=bpy.data.cameras.new('tmpcam'); cd.lens=lens; cd.sensor_width=36
    co=bpy.data.objects.new('tmpcam',cd); sc.collection.objects.link(co); co.location=(x,y,z)
    co.rotation_euler=(Vector((tx,ty,tz))-co.location).to_track_quat('-Z','Y').to_euler(); sc.camera=co
sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=rx; sc.render.resolution_y=int(rx*2/3); sc.render.resolution_percentage=100
sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'; sh.show_shadows=True; sh.show_cavity=False
sc.display.render_aa='OFF'
sc.render.image_settings.file_format='PNG'
sc.render.filepath=out
sc.view_settings.view_transform='Standard'
bpy.ops.render.render(write_still=True)
print('WB DONE')
