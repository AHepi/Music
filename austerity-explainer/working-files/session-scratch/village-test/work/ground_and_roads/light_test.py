import sys, bpy, numpy as np, os
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/ground_and_roads'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 4; scene.cycles.use_denoising = False
scene.render.resolution_x = 600; scene.render.resolution_y = 400
scene.render.film_transparent = True
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Backdrop'): o.hide_render = True
scene.camera = bpy.data.objects['View wide']
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
sun = bpy.data.objects['Sun'].data
bg = bpy.data.worlds['Sky'].node_tree.nodes['Math'] if 'Math' in bpy.data.worlds['Sky'].node_tree.nodes else None
def shot(tag):
    scene.render.filepath = f'{base}/lt_{tag}.png'
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(f'{base}/lt_{tag}.png'); w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)  # bottom-up
    px = px[::-1]
    band = px[110:150, :, :]   # near ring band at 600px wide
    m = band[..., 3] > 0.98
    lin = band[..., :3][m].mean(0) if m.sum() else None
    print(tag, 'linear mean', None if lin is None else lin.round(4), 'n', int(m.sum()), flush=True)
    bpy.data.images.remove(img)
shot('as_is')
e = sun.energy; sun.energy = 0.0; shot('no_sun'); sun.energy = e
w = bpy.data.worlds['Sky']
for n in w.node_tree.nodes:
    if n.type == 'BACKGROUND':
        s = n.inputs['Strength']; links = [l for l in w.node_tree.links if l.to_socket == s]
        for l in links: w.node_tree.links.remove(l)
        s.default_value = 0.0
shot('no_sky')
