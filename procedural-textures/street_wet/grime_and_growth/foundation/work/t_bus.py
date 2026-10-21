import sys, json, os, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy, numpy as np
from apply import kit as wk, layer_template
from masks import bus, debug, names
out = 'bus_out'; os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
def draw(name, W=135, H=240, S=1):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    scene.eevee.taa_render_samples = S
    p = os.path.join(out, name + '.png'); scene.render.filepath = p
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., :3]
    bpy.data.images.remove(img)
    return a
k = wk.Kit.load('pit_village_street')
bus.attach(k)
k.prepare()
k.register_layer('t_a', lambda key: layer_template.build_template(key), slot='A', roles='all')
k.apply(layers=['t_a'])
print('VERIFY', k.verify())
t = k.chains['street_setts'].tree
print('NODES', [n.name for n in t.nodes if n.get('wk')])
print('BUS OUT', [o.name for o in t.nodes['WK MASKS'].outputs])
t2 = k.chains['cottage_stone_door_left'].tree if 'cottage_stone_door_left' in k.chains else k.chains['cottage_stone'].tree
print('WALL BUS OUT', [o.name for o in t2.nodes['WK MASKS'].outputs])
def link_src(mat='street_setts'):
    t = bpy.data.materials[mat].node_tree
    o = [n for n in t.nodes if n.type=='OUTPUT_MATERIAL'][0]
    l = o.inputs['Surface'].links
    return (l[0].from_node.name if l else None)
for m in ('height', 'shade', 'height', 'moss_site'):
    undo = debug.show_mask(k, m)
    print('SHOWN', m, link_src())
    a = draw('mask2_' + m)
    print('MASK', m, round(float(a.mean()),4), round(float(a.max()),4))
    undo()
    print('UNDONE', link_src())
