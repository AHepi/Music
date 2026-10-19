# What this does: finds out why a flat ground panel with the normal map came out pure black in the first swatch test.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bpy
import mine_common as mc
mc.clear_scene(); mc.preview_stage()
for light in list(bpy.data.objects):
    if light.type == 'LIGHT': bpy.data.objects.remove(light)
mc.set_sun(35, 90, strength=4.5, colour=(1.0, 0.9, 0.78))
def panel(name, surface, x0, lift, strength=None, **kw):
    material = mc.surface_material(surface, variation=0.0, splash=0.0, normal_strength=strength, **kw)
    b = mc.MeshBuilder(name, [material]); z = lift
    b.add_polygon([(x0, -3, z), (x0 + 3.4, -3, z), (x0 + 3.4, 0.4, z), (x0, 0.4, z)], slot=0)
    return b.finish('Test')
panel('a: normal map, lifted 2 cm', 'mud', -5.4, 0.02)
panel('b: normal map, strength 0', 'mud', -1.7, 0.02, strength=0.0)
panel('c: gravel normal map lifted', 'gravel', 2.0, 0.02)
mc.render_preview('out/black_ground_test.png', (0, -9, 2.4), (0, -1.2, 0), lens=30, size=(1400, 600), samples=24)
