# What this does: photographs mud and gravel with real displacement at the lowered relief heights, from low and oblique, at
# two sun heights, to see ruts, puddles and stones standing out as real bumps.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bpy
import mine_common as mc
mc.clear_scene(); mc.preview_stage()
for light in list(bpy.data.objects):
    if light.type == 'LIGHT': bpy.data.objects.remove(light)
mc.set_sun(14, 90, strength=5.0, colour=(1.0, 0.8, 0.6))
def panel(name, surface, x0):
    material = mc.surface_material(surface, true_displacement=True, variation=0.0, splash=0.0)
    b = mc.MeshBuilder(name, [material])
    b.add_polygon([(x0, -3, 0.05), (x0 + 3.4, -3, 0.05), (x0 + 3.4, 0.4, 0.05), (x0, 0.4, 0.05)], slot=0)
    obj = b.finish('Test'); mc.use_real_displacement(obj, 1.0)
panel('mud', 'mud', -3.8); panel('gravel', 'gravel', 0.4)
mc.render_preview('out/ground_displacement_test.png', (0, -6.0, 1.3), (0, -1.2, 0), lens=32, size=(1400, 600), samples=48)
