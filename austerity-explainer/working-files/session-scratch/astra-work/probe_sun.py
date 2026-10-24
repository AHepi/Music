# What this does: prints the direction of the sun in the Sky Texture node for a few rotation angles (read only).
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
w = bpy.data.worlds.new('w'); w.use_nodes = True
n = w.node_tree.nodes.new('ShaderNodeTexSky'); n.sky_type = 'MULTIPLE_SCATTERING'; n.sun_elevation = math.radians(9)
for deg in (0, 90, 180, 270):
    n.sun_rotation = math.radians(deg)
    print('SUN', deg, tuple(round(v, 2) for v in n.sun_direction))
