# What this does: puts each uploaded surface (brick, slate, wood, metal on upright panels; mud and gravel on the ground) on
# test pieces and photographs them with low raking light. Run it once with "normalmap" and once with "displaced" in the
# output name to compare the normal map alone against real surface displacement, which shows whether the maps point the right way.
# Use: blender -b --python test_swatches.py -- OUTPUT_PREFIX   (prefix containing the word "displaced" turns real displacement on)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bpy
import mine_common as mc

prefix = sys.argv[sys.argv.index('--') + 1]
displaced = 'displaced' in prefix
mc.clear_scene()
mc.preview_stage()
for light in list(bpy.data.objects):
    if light.type == 'LIGHT': bpy.data.objects.remove(light)
mc.set_sun(20, 90, strength=4.5, colour=(1.0, 0.9, 0.78))   # light comes from the left (-X), low

def panel(name, surface, corners):
    material = mc.surface_material(surface, true_displacement=displaced, variation=0.0, splash=0.0)
    builder = mc.MeshBuilder(name, [material])
    builder.add_polygon(corners, slot=0)
    obj = builder.finish('Test')
    if displaced:
        mc.use_real_displacement(obj, 1.0)

# upright panels facing the camera at -Y ... polygon winding below faces -Y (counter-clockwise seen from -Y)
for i, surface in enumerate(['brick', 'slate', 'wood', 'metal']):
    x0 = -5.2 + i * 2.6
    panel(surface, surface, [(x0, 5, 0.1), (x0, 5, 2.5), (x0 + 2.4, 5, 2.5), (x0 + 2.4, 5, 0.1)][::-1] if False else [(x0, 5, 0.1), (x0 + 2.4, 5, 0.1), (x0 + 2.4, 5, 2.5), (x0, 5, 2.5)])
# ground pieces: mud and gravel, 3.5 m squares seen from low and oblique
panel('mud', 'mud', [(-3.8, -3, 0), (-0.2, -3, 0), (-0.2, 0.6, 0), (-3.8, 0.6, 0)])
panel('gravel', 'gravel', [(0.2, -3, 0), (3.8, -3, 0), (3.8, 0.6, 0), (0.2, 0.6, 0)])
cam = mc.render_preview(prefix + '_ground.png', (0, -7.5, 1.6), (0, -1.0, 0.0), lens=32, size=(1400, 700), samples=64)
# turn the camera to the upright panels
for ob in list(bpy.data.objects):
    if ob.type == 'CAMERA': bpy.data.objects.remove(ob)
# move the sun to rake across the upright panels too (it already comes from -X)
mc.render_preview(prefix + '_walls.png', (0, -3.0, 1.4), (0, 5, 1.3), lens=24, size=(1600, 560), samples=64)
