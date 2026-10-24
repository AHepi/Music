import bpy, math
from mathutils import Vector
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s=bpy.context.scene
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=24
s.render.resolution_x=1080; s.render.resolution_y=1920; s.render.resolution_percentage=40
bpy.ops.import_scene.gltf(filepath='/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/town.glb')
w=bpy.data.worlds.new('w'); s.world=w; w.use_nodes=True
w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.02,0.025,0.035,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=1.0
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera=cam
cam.data.lens=50
cam.location=(-1.0,-12,2.2)
d=Vector((0,6,0.8))-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); s.collection.objects.link(sun)
sun.data.energy=3.5; sun.data.color=(1.0,0.82,0.62); sun.data.angle=math.radians(4)
sun.rotation_euler=(math.radians(55),0,math.radians(-35))
fill=bpy.data.objects.new('fill',bpy.data.lights.new('fill','AREA')); s.collection.objects.link(fill)
fill.data.energy=60; fill.data.size=4; fill.data.color=(0.6,0.7,1.0); fill.location=(3,-3,3); fill.rotation_euler=(math.radians(50),0,math.radians(45))
result={'objects':len(s.objects)}
