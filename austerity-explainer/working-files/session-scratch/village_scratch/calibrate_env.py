# Finds out how Blender maps directions to the picture of an environment texture (which way is u, which way is v).
import bpy, numpy as np, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
W,H=256,128
img = bpy.data.images.new('calib', W, H, alpha=False, float_buffer=True)
img.colorspace_settings.name='Non-Color'
arr = np.zeros((H,W,4),dtype=np.float32)
u = (np.arange(W)+0.5)/W
v = (np.arange(H)+0.5)/H
arr[...,0]=u[None,:]
arr[...,1]=v[:,None]
arr[...,2]=0.0
arr[...,3]=1.0
img.pixels.foreach_set(arr.ravel())
print('IMGCHK', img.pixels[0], img.pixels[1], img.pixels[(5*W+100)*4], img.size[:], img.is_float)
scene=bpy.context.scene
world=bpy.data.worlds.new('w'); scene.world=world; world.use_nodes=True
nt=world.node_tree
for n in list(nt.nodes):
    if n.type!='OUTPUT_WORLD': nt.nodes.remove(n)
out=[n for n in nt.nodes if n.type=='OUTPUT_WORLD'][0]
env=nt.nodes.new('ShaderNodeTexEnvironment'); env.image=img; env.interpolation='Linear'
bg=nt.nodes.new('ShaderNodeBackground')
nt.links.new(env.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
scene.render.engine='CYCLES'; scene.cycles.samples=1; scene.cycles.device='CPU'
scene.render.resolution_x=16; scene.render.resolution_y=16
scene.view_settings.view_transform='Raw'
scene.cycles.use_denoising=False
cam_data=bpy.data.cameras.new('c'); cam=bpy.data.objects.new('c',cam_data); scene.collection.objects.link(cam); scene.camera=cam
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_depth='16'
for name,d in [('+X',(1,0,0)),('+Y',(0,1,0)),('-X',(-1,0,0)),('-Y',(0,-1,0)),('+Z up45',(1,0,1)),('-Z down45',(1,0,-1))]:
    d=Vector(d)
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village_scratch/cal_%s.png'%name.replace('+','p').replace('-','m').replace(' ','_')
    bpy.ops.render.render(write_still=True)
    r=bpy.data.images.load(scene.render.filepath)
    r.colorspace_settings.name='Non-Color'
    px=np.array(r.pixels[:]).reshape(16,16,4)
    c=px[8,8]; 
    print('DIR',name,'u=%.3f v=%.3f'%(c[0],c[1]))
