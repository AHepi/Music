# What this does (plain words): STUDY ONLY, saves nothing in the scene. Draws the courtyard from the photo's camera with every material replaced by a flat family colour (no light), so the families
# of surface that the kit would treat show up as clear colour patches. Uses the same family-by-material table as c6_hook_test.py.
# Run: blender -b --disable-autoexec FILE --python c7_family_map.py -- OUT.png [WIDTH]
import os, sys
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]; W = int(args[1]) if len(args) > 1 else 1200
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'c6_hook_test.py')).read().split('# ---------------------------------------------------------------- the do-nothing group')[0]
sys.argv = [sys.argv[0], '--', 'x']
exec(compile(src, 'c6_family_part', 'exec'))             # gives mat_fam: material name -> family
COL = {'ground and earth': (0.30, 0.55, 0.18), 'moss and pebbles (add-on)': (0.62, 0.88, 0.32), 'raked gravel': (0.88, 0.78, 0.48), 'water': (0.15, 0.40, 0.85),
       'wood (planks, posts, beams, roof deck)': (0.80, 0.40, 0.10), 'plaster': (0.97, 0.97, 0.88), 'wall cap tiles': (0.10, 0.10, 0.55), 'roof tiles': (0.45, 0.25, 0.70),
       'stone (add-on stones)': (0.62, 0.62, 0.66), 'plain stone (plinth)': (0.32, 0.34, 0.45), 'bamboo': (0.85, 0.92, 0.15), 'bark': (0.45, 0.22, 0.08),
       'leaves and needles': (0.05, 0.28, 0.07), 'glow and backdrop': (0.22, 0.22, 0.26)}
for m in bpy.data.materials:
    f = mat_fam.get(m.name, 'unused')
    if f not in COL or m.users == 0: continue
    if not m.use_nodes: m.use_nodes = True
    t = m.node_tree; t.nodes.clear()
    e = t.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*COL[f], 1.0); e.inputs['Strength'].default_value = 1.0
    o = t.nodes.new('ShaderNodeOutputMaterial'); t.links.new(e.outputs['Emission'], o.inputs['Surface'])
sc = bpy.context.scene
sc.world.node_tree.nodes.clear(); bg = sc.world.node_tree.nodes.new('ShaderNodeBackground'); bg.inputs['Color'].default_value = (0, 0, 0, 1); wo = sc.world.node_tree.nodes.new('ShaderNodeOutputWorld')
sc.world.node_tree.links.new(bg.outputs['Background'], wo.inputs['Surface'])
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False; sc.cycles.device = 'CPU'
sc.render.resolution_x = W; sc.render.resolution_y = int(W * 2 / 3); sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
