import bpy, sys, json, os, math
import numpy as np
sys.dont_write_bytecode = True
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/ground/previews/insp1'
os.makedirs(OUT, exist_ok=True)
dg = bpy.context.evaluated_depsgraph_get()
def info(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        print('NOOBJ', name); return
    me = ob.data
    print('OBJ', name, 'type', ob.type, 'verts', len(me.vertices), 'mods', [(m.name, m.type, getattr(m.node_group,'name',None)) for m in ob.modifiers], 'mats', [s.material.name if s.material else None for s in ob.material_slots], 'hide_render', ob.hide_render)
    print('  attrs', [(a.name, a.domain, a.data_type) for a in me.attributes])
    if 'lived_scale' in me.attributes:
        a = np.zeros(len(me.vertices)*3, np.float32); me.attributes['lived_scale'].data.foreach_get('vector', a); a = a.reshape(-1,3)
        print('  lived_scale x min/mean/max', a[:,0].min(), a[:,0].mean(), a[:,0].max(), 'pct', np.percentile(a[:,0], [5,25,50,75,95]), 'z pct', np.percentile(a[:,2], [5,50,95]))
    ev = ob.evaluated_get(dg)
    print('  evaluated: verts', len(ev.to_mesh().vertices))
    ev.to_mesh_clear()
for n in ['Life / moss at feet and damp edges', 'Astra / moss grouped bodies', 'G6 ground / moss collars', 'Life / pebble fringe', 'Astra / pebbles grouped bodies', 'Life / tufts', 'Fallen leaves']:
    info(n)
ob = bpy.data.objects['Life / moss at feet and damp edges']
for m in ob.modifiers:
    if m.type == 'NODES' and m.node_group:
        print('GROUP', m.node_group.name)
        try:
            for k in m.keys(): print('  modkey', k, m[k])
        except Exception: pass
        for n in m.node_group.nodes:
            ins = []
            for i in n.inputs:
                if hasattr(i, 'default_value') and not i.is_linked:
                    try:
                        v = i.default_value
                        v = tuple(v) if hasattr(v, '__len__') and not isinstance(v, str) else v
                        ins.append((i.name, v if not isinstance(v, float) else round(v, 3)))
                    except Exception: pass
            print('  node', n.bl_idname.replace('GeometryNode',''), '|', n.name, '|', ins[:8])
        for l in m.node_group.links:
            print('  link', l.from_node.name, l.from_socket.name, '->', l.to_node.name, l.to_socket.name)
# hierarchy of grouped bodies: islands
gb = bpy.data.objects['Astra / moss grouped bodies']
me = gb.data
n = len(me.vertices)
parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
for e in me.edges:
    x, y = find(e.vertices[0]), find(e.vertices[1])
    if x != y: parent[x] = y
roots = {}
co = np.zeros(n*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
for i in range(n): roots.setdefault(find(i), []).append(i)
print('GROUPED islands', len(roots))
sizes = []
for r, idx in roots.items():
    p = co[idx]; sizes.append(tuple(np.round(p.max(0)-p.min(0), 2)))
import collections
print('island dims sample', sizes[:12])
print('island xy extents percentiles', np.percentile([s[0] for s in sizes],[5,50,95]), np.percentile([s[2] for s in sizes],[5,50,95]))
# renders hiding objects
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.camera = bpy.data.objects['veranda']
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 80
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print('gpu setup', e)
def render(tag, hide):
    for h in hide:
        o = bpy.data.objects.get(h)
        if o: o.hide_render = True
    sc.render.filepath = os.path.join(OUT, tag + '.jpg')
    bpy.ops.render.render(write_still=True)
    for h in hide:
        o = bpy.data.objects.get(h)
        if o: o.hide_render = False
render('all', [])
render('no_lived', ['Life / moss at feet and damp edges'])
render('no_grouped', ['Astra / moss grouped bodies'])
render('no_collars', ['G6 ground / moss collars'])
print('INSPECT_DONE')
