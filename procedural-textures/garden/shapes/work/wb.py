# Workbench look-at pictures for quick local checks (in-memory only). render_views([(name, (cx,cy,cz), (tx,ty,tz), lens)], prefix, res)
import bpy, math, os
from mathutils import Vector
HIDE = ('Maple leaves', 'Maple inner mass', 'Pine pads', 'Bamboo leaves', 'Fallen leaves', 'Lily pads', 'Lotus blossoms', 'Astra / moss grouped bodies',
        'Astra / pebbles grouped bodies', 'Maple trunk', 'Maple branch', 'Maple branch.001', 'Maple branch.002', 'Pine trunk', 'Pine limb', 'Pine limb.001', 'Pine limb.002', 'Pine limb.003', 'Pine limb.004', 'Hills, far', 'Hills, middle', 'Hills, near', 'Dark plain', 'Bamboo stalks')
def render_views(views, prefix, res=(640, 427), hide=HIDE, ortho=None, flat=False):
    sc = bpy.context.scene
    saved = {}
    for n in hide:
        ob = bpy.data.objects.get(n)
        if ob: saved[n] = ob.hide_render; ob.hide_render = True
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'OBJECT' if not flat else 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = False
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    sc.world.use_nodes = False
    sc.world.color = (0.75, 0.82, 0.9)
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and not ob.hide_render:
            ob.color = (0.7, 0.7, 0.68, 1)
    # colour by role-ish for contrast
    def col(n, c):
        ob = bpy.data.objects.get(n)
        if ob: ob.color = c
    for ob in bpy.data.objects:
        n = ob.name
        if n.startswith(('Rock','Pond edge','Stepping','Gravel rock','Veranda step','Bridge pier','Water basin','Lantern base','Lantern post','Lantern gallery','Lantern firebox','Lantern cap','Shore','Basin','Gravel kerb')):
            ob.color = (0.62, 0.62, 0.58, 1)
        elif n.startswith('Astra / varied planks'): ob.color = (0.55, 0.38, 0.25, 1)
        elif 'Lantern window glow' in n: ob.color = (1, 0.5, 0.1, 1)
        elif n in ('Astra / Courtyard receiving ground',): ob.color = (0.3, 0.45, 0.25, 1)
        elif n == 'Raked gravel court': ob.color = (0.82, 0.8, 0.74, 1)
        elif n == 'Pond water': ob.color = (0.2, 0.45, 0.55, 1)
        elif 'cap' in n and 'wall' in n.lower(): ob.color = (0.15, 0.15, 0.17, 1)
        elif 'wall' in n.lower(): ob.color = (0.85, 0.8, 0.7, 1)
    cam = sc.camera
    cd = cam.data
    old = (cam.location.copy(), cam.rotation_euler.copy(), cd.lens, cd.type, cd.ortho_scale, cd.clip_start, cd.clip_end, cd.dof.use_dof)
    cd.dof.use_dof = False; cd.clip_start = 0.05; cd.clip_end = 400
    outs = []
    for name, loc, tgt, lens in views:
        if tgt is not None:
            cam.location = loc
            cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        if lens < 0:
            cd.type = 'ORTHO'; cd.ortho_scale = -lens
        else:
            cd.type = 'PERSP'; cd.lens = lens
        sc.render.filepath = f'{prefix}_{name}.png'
        bpy.ops.render.render(write_still=True)
        outs.append(sc.render.filepath)
    cam.location, cam.rotation_euler, cd.lens, cd.type, cd.ortho_scale, cd.clip_start, cd.clip_end, cd.dof.use_dof = old
    for n, v in saved.items(): bpy.data.objects[n].hide_render = v
    return outs
