"""wood_jobs.py - hooks the render job calls after the stage ('post': NAME in the JOBS json). They only change the test scene that is drawn, never the starting file."""
import bpy
import numpy as np
from mathutils import Vector
import wood_mats as wm

BRIDGE_OBJECTS = (['Astra / varied planks.%03d' % i for i in range(3, 8)] + ['Bridge stringers'] + ['Bridge pier %d' % i for i in range(4)] +
                  ['G6 wood / bridge bearers', 'G6 wood / bridge posts', 'G6 wood / bridge footings', 'G6 wood / bridge pegs', 'G6 wood / bridge cramps'])


def _flat(name, hexs, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = wm.lin(hexs)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.0
    return m


def diagram(v, outdir):
    """parts diagram: only the bridge, each part type in its own colour, plan and side view (cameras 'G6 wood cam 10' plan, '... 11' side)"""
    sc = bpy.context.scene
    keep = set(BRIDGE_OBJECTS)
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META', 'POINTCLOUD', 'CURVES', 'VOLUME') and o.name not in keep:
            o.hide_render = True
        if o.type == 'LIGHT':
            o.hide_render = True
    col = dict(planks='#d8c3a0', rails='#4b8fc9', bearers='#d9584a', posts='#e3a636', footings='#7f8c99', sills='#9a9a9a', pegs='#f4f4f4', cramps='#1c1c1c')
    mat = {k: _flat('diag ' + k, h) for k, h in col.items()}
    names = {'planks': ['Astra / varied planks.%03d' % i for i in range(3, 8)], 'rails': ['Bridge stringers'], 'bearers': ['G6 wood / bridge bearers'],
             'posts': ['G6 wood / bridge posts'], 'footings': ['G6 wood / bridge footings', 'Bridge pier 1', 'Bridge pier 2'], 'sills': ['Bridge pier 0', 'Bridge pier 3'],
             'pegs': ['G6 wood / bridge pegs'], 'cramps': ['G6 wood / bridge cramps']}
    for k, lst in names.items():
        for n in lst:
            o = bpy.data.objects.get(n)
            if o is None:
                continue
            o.data.materials.clear()
            o.data.materials.append(mat[k])
            if k == 'pegs':
                o.data.materials.append(mat[k])
            for p in o.data.polygons:
                p.material_index = 0
    # water plane (translucent) so the footings read as standing in the pond
    me = bpy.data.meshes.new('diag water')
    me.from_pydata([(-8, -6, -0.12), (3, -6, -0.12), (3, 5, -0.12), (-8, 5, -0.12)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new('diag water', me)
    sc.collection.objects.link(ob)
    wmat = bpy.data.materials.new('diag water')
    wmat.use_nodes = True
    nt = wmat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = wm.lin('#6fa8c8')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.30
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    me.materials.append(wmat)
    # ground plane under the pond (light grey) for the side view only: skip; world light
    w = sc.world or bpy.data.worlds.new('diag world')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.93, 0.92, 0.89, 1.0)
        bg.inputs['Strength'].default_value = 1.0
        for l in list(w.node_tree.links):
            if l.to_node == bg and l.to_socket.name == 'Color':
                w.node_tree.links.remove(l)
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sun_d = bpy.data.lights.new('diag sun', 'SUN'); sun_d.energy = 2.2
    sun = bpy.data.objects.new('diag sun', sun_d); sc.collection.objects.link(sun)
    sun.rotation_euler = Vector((0.4, -0.3, -0.85)).to_track_quat('-Z', 'Y').to_euler() if False else (0.9, 0.2, 0.6)
    # cameras
    def ortho(name, loc, rot, scale):
        cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = scale
        co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co); co.location = loc; co.rotation_euler = rot
    ortho('G6 wood cam 10', (-3.3, 0.45, 6.0), (0, 0, 0), 7.2)
    ortho('G6 wood cam 11', (-3.2, -8.0, 0.05), (1.5708, 0, 0), 7.2)


def debug_mask(v, outdir):
    """moss (red), mould (green) and walking-line wear (blue) as emission on every plank material; only planks are drawn; transparent background"""
    sc = bpy.context.scene
    keep = set(['Astra / varied planks.%03d' % i for i in range(3, 8)])
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META', 'POINTCLOUD', 'CURVES', 'VOLUME') and o.name not in keep:
            o.hide_render = True
    for m in bpy.data.materials:
        if m.name.startswith('G6 wood / ') and m.node_tree:
            for n in m.node_tree.nodes:
                if n.label == 'G6 debug':
                    n.outputs[0].default_value = 1.0
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.file_format = 'PNG'


def dark_mask_off(v, outdir):
    pass


def silhouette(v, outdir):
    """only the bridge planks, white on transparent: the plan outline of the deck seen from the picture camera"""
    sc = bpy.context.scene
    keep = set(['Astra / varied planks.%03d' % i for i in range(3, 8)])
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META', 'POINTCLOUD', 'CURVES', 'VOLUME') and o.name not in keep:
            o.hide_render = True
        if o.type == 'LIGHT':
            o.hide_render = True
    for o in keep:
        ob = bpy.data.objects[o]
        ob.data.materials.clear()
        m = bpy.data.materials.new('sil')
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        ob.data.materials.append(m)
        for p in ob.data.polygons:
            p.material_index = 0
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.color_mode = 'RGBA'


def step_dials(v, outdir):
    """test hook: set weathering-kit dials on the two veranda step materials. v['dials'] = {'WK WALL CRACKS': {'Crack Amount': 0.1}, ...}"""
    cfg = v.get('dials', {})
    for mn in ('CT / Stone painterly surface.008', 'CT / Stone painterly surface.009'):
        m = bpy.data.materials[mn]
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeGroup' and n.node_tree is not None:
                for gname, d in cfg.items():
                    if n.node_tree.name.startswith(gname):
                        for k, val in d.items():
                            if k in n.inputs and not n.inputs[k].is_linked:
                                n.inputs[k].default_value = val
