import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
world=bpy.data.worlds.new('w'); scene.world=world; world.use_nodes=True
nt=world.node_tree
print([ (n.name,n.type) for n in nt.nodes])
bg=nt.nodes.get('Background'); print(bg)
bg.inputs['Color'].default_value=(1,0.2,0.1,1)
scene.render.engine='CYCLES'; scene.cycles.samples=1; scene.render.resolution_x=16; scene.render.resolution_y=16
scene.view_settings.view_transform='Raw'
cam_data=bpy.data.cameras.new('c'); cam=bpy.data.objects.new('c',cam_data); scene.collection.objects.link(cam); scene.camera=cam
scene.render.filepath='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village_scratch/dbg.png'
bpy.ops.render.render(write_still=True)
r=bpy.data.images.load(scene.render.filepath); px=np.array(r.pixels[:]).reshape(16,16,4); print('PX',px[8,8])
