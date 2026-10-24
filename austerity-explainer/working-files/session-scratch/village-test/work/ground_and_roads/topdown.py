import sys, time, os, bpy, math
from mathutils import Vector
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
args = sys.argv[sys.argv.index('--') + 1:]
tag = args[0]; x0, y0, x1, y1 = [float(v) for v in args[1:5]]; px = int(args[5]); mode = args[6] if len(args) > 6 else 'label'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 1; scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'Standard'
w = x1 - x0; h = y1 - y0
scene.render.resolution_x = px; scene.render.resolution_y = int(px * h / w); scene.render.resolution_percentage = 100
cam = bpy.data.objects.new('dbg', bpy.data.cameras.new('dbg')); scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = w; cam.data.clip_end = 5000
cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, 200); cam.rotation_euler = (0, 0, 0)
scene.camera = cam
# material override: flat colour per object (random), or height shading
mat = bpy.data.materials.new('dbgmat'); mat.use_nodes = True
t = mat.node_tree; t.nodes.clear()
out = t.nodes.new('ShaderNodeOutputMaterial'); em = t.nodes.new('ShaderNodeEmission')
if mode == 'label':
    oi = t.nodes.new('ShaderNodeObjectInfo');

    ramp = t.nodes.new('ShaderNodeValToRGB'); 
    t.links.new(oi.outputs['Random'], ramp.inputs['Fac'])
    ramp.color_ramp.interpolation = 'CONSTANT'
    cols = [(1,0,0,1),(0,1,0,1),(0,0,1,1),(1,1,0,1),(1,0,1,1),(0,1,1,1),(1,0.5,0,1),(0.4,0.4,0.4,1)]
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = cols[0]
    els[1].position = 1/8.0; els[1].color = cols[1]
    for i in range(2, 8):
        e = els.new(i/8.0); e.color = cols[i]
    t.links.new(ramp.outputs['Color'], em.inputs['Color'])
else:   # height: z from -0.8 to 0.8 as grey
    geo = t.nodes.new('ShaderNodeNewGeometry'); sep = t.nodes.new('ShaderNodeSeparateXYZ'); mr = t.nodes.new('ShaderNodeMapRange')
    t.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    mr.inputs['From Min'].default_value = float(args[7]) if len(args) > 7 else -0.8; mr.inputs['From Max'].default_value = float(args[8]) if len(args) > 8 else 0.8
    t.links.new(sep.outputs['Z'], mr.inputs['Value'])
    t.links.new(mr.outputs['Result'], em.inputs['Color'])
t.links.new(em.outputs['Emission'], out.inputs['Surface'])
scene.view_layers[0].material_override = mat
# hide the backdrop
for o in bpy.data.objects:
    if o.name.startswith('Backdrop'): o.hide_render = True
if bpy.data.worlds.get('Sky'):
    bpy.data.worlds['Sky'].node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = f'{base}/pictures/top_{tag}.png'
bpy.ops.render.render(write_still=True)
print('done', tag, flush=True)
