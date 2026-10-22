import bpy, numpy as np, sys
sys.dont_write_bytecode=True
sc = bpy.context.scene
N=16
img = bpy.data.images.new('t', N, N, alpha=False, float_buffer=True)
vals = np.array([0.0, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8], dtype=np.float32)
px = np.zeros((N,N,4),dtype=np.float32); px[:,:,0]=vals[None,:]; px[:,:,1]=vals[None,:]; px[:,:,2]=vals[None,:]; px[:,:,3]=1
img.pixels.foreach_set(px.ravel())
img.update()
img.filepath_raw='proc-work/garden/fix/work/toe_in.exr'
img.file_format='OPEN_EXR'
img.save()
bpy.data.images.remove(img)
img = bpy.data.images.load('proc-work/garden/fix/work/toe_in.exr')
print('in size', img.size, list(img.pixels[:8]))
sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.device='CPU'
sc.render.resolution_x=N; sc.render.resolution_y=N; sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
try: sc.render.compositor_device='CPU'
except Exception as e: print(e)
tree = bpy.data.node_groups.new('t','CompositorNodeTree')
tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
feed = tree.nodes.new('CompositorNodeImage'); feed.image=img
out = tree.nodes.new('NodeGroupOutput')
sock = feed.outputs['Image']
def add_toe(tree, sock, T, L0, tint):
    bw = tree.nodes.new('CompositorNodeRGBToBW'); tree.links.new(bw.inputs['Image'], sock)
    den = tree.nodes.new('ShaderNodeMath'); den.operation='ADD'; den.inputs[1].default_value=T
    tree.links.new(bw.outputs['Val'], den.inputs[0])
    wt = tree.nodes.new('ShaderNodeMath'); wt.operation='DIVIDE'; wt.inputs[0].default_value=T
    tree.links.new(den.outputs[0], wt.inputs[1])
    sc_ = tree.nodes.new('ShaderNodeMix'); sc_.data_type='RGBA'; sc_.blend_type='MULTIPLY'; sc_.inputs['Factor'].default_value=1.0
    tree.links.new(wt.outputs[0], sc_.inputs[6]); sc_.inputs[7].default_value=(tint[0]*L0, tint[1]*L0, tint[2]*L0, 1.0)
    ad = tree.nodes.new('ShaderNodeMix'); ad.data_type='RGBA'; ad.blend_type='ADD'; ad.inputs['Factor'].default_value=1.0
    tree.links.new(sock, ad.inputs[6]); tree.links.new(sc_.outputs[2], ad.inputs[7])
    return ad.outputs[2]
import os
if os.environ.get("TOE","1")=="1": sock = add_toe(tree, sock, 0.02, 0.006, (0.8, 1.0, 1.0))
tree.links.new(out.inputs[0], sock)
sc.compositing_node_group = tree
sc.render.use_compositing=True
sc.render.image_settings.media_type='IMAGE'
sc.render.image_settings.file_format='OPEN_EXR'
sc.render.image_settings.color_depth='32'
sc.render.filepath='proc-work/garden/fix/work/toe_test.exr'
bpy.ops.render.render(write_still=True)
r = bpy.data.images.load(sc.render.filepath)
r.reload(); _=r.pixels[0]; a = np.array(list(r.pixels)).reshape(N,N,4)[N//2]
for v,o in zip(vals, a): print(v, '->', o[:3].round(5))
print('result image size', r.size, 'channels', r.channels, 'is_float', r.is_float, 'sum', sum(r.pixels[:]))
print('scene cam', sc.camera, 'objects', [o.name for o in bpy.data.objects])
print('use_compositing', sc.render.use_compositing, 'group', sc.compositing_node_group)
