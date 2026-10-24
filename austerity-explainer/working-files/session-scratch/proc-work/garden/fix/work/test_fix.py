# What this does (plain words): checks that the fix stage (1) only touches what it says it touches and (2) gives the same scene when run twice.
import bpy, sys, hashlib, json
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/fix/stage')
import stage_fix
look = sys.argv[sys.argv.index('--')+1]

def fp():
    out = {'objects': {}, 'materials': {}, 'lights': {}, 'world': None}
    for ob in bpy.data.objects:
        d = {'mw': tuple(round(x,4) for r in ob.matrix_world for x in r), 'vis': (ob.hide_render, ob.visible_camera, ob.visible_diffuse, ob.visible_glossy),
             'slots': tuple(s.material.name if s.material else None for s in ob.material_slots), 'coll': tuple(sorted(c.name for c in ob.users_collection))}
        if ob.type == 'MESH':
            me = ob.data; n = len(me.vertices); co = np.empty(n*3, np.float32); me.vertices.foreach_get('co', co)
            d['geo'] = (n, len(me.polygons), hashlib.md5(np.round(co,4).tobytes()).hexdigest()[:10])
            cols = me.color_attributes.get('Col')
            if cols is not None:
                c = np.empty(len(cols.data)*4, np.float32); cols.data.foreach_get('color', c); d['col'] = hashlib.md5(np.round(c,4).tobytes()).hexdigest()[:10]
            for a in me.attributes:
                if a.name in ('leaf_scale','lived_scale','lived_rotation','leaf_rank'):
                    v = np.empty(len(a.data)*(3 if a.data_type=='FLOAT_VECTOR' else 1), np.float32); a.data.foreach_get('vector' if a.data_type=='FLOAT_VECTOR' else 'value', v)
                    d[a.name] = hashlib.md5(np.round(v,4).tobytes()).hexdigest()[:10]
        out['objects'][ob.name] = d
    for m in bpy.data.materials:
        if m.node_tree:
            vals = []
            for n in m.node_tree.nodes:
                for s in n.inputs:
                    if hasattr(s, 'default_value'):
                        try: v = tuple(round(x,4) for x in s.default_value)
                        except TypeError:
                            try: v = round(float(s.default_value),4)
                            except Exception: v = None
                        vals.append((n.name, s.identifier, v))
            out['materials'][m.name] = (len(m.node_tree.nodes), len(m.node_tree.links), hashlib.md5(repr(vals).encode()).hexdigest()[:10])
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT': out['lights'][ob.name] = (ob.data.energy, tuple(ob.data.color))
    w = bpy.context.scene.world
    out['world'] = (len(w.node_tree.nodes), len(w.node_tree.links)) if w and w.node_tree else None
    out['cam'] = tuple(round(x,4) for r in bpy.context.scene.camera.matrix_world for x in r)
    return out

def diff(a, b):
    res = {'objects_added': sorted(set(b['objects'])-set(a['objects'])), 'objects_removed': sorted(set(a['objects'])-set(b['objects'])), 'objects_changed': {}, 'materials_changed': [], 'materials_added': sorted(set(b['materials'])-set(a['materials'])), 'lights_changed': [k for k in a['lights'] if a['lights'][k]!=b['lights'].get(k)], 'world_changed': a['world']!=b['world'], 'camera_moved': a['cam']!=b['cam']}
    for k in a['objects']:
        if k in b['objects'] and a['objects'][k] != b['objects'][k]:
            res['objects_changed'][k] = sorted(x for x in a['objects'][k] if a['objects'][k].get(x) != b['objects'][k].get(x))
    for k in a['materials']:
        if k in b['materials'] and a['materials'][k] != b['materials'][k]: res['materials_changed'].append(k)
    return res

f0 = fp()
stage_fix.apply({'look': look})
f1 = fp()
stage_fix.apply({'look': look})
f2 = fp()
d1 = diff(f0, f1); d2 = diff(f1, f2)
print('DIFF_FIRST', json.dumps({k: (v if k!='materials_changed' else f'{len(v)} materials: '+', '.join(v[:60])) for k,v in d1.items()}, indent=1))
print('DIFF_SECOND_RUN (should be empty except the rebuilt hedge/ground/sky/pond/toe)', json.dumps({k: (v if k!='materials_changed' else f'{len(v)} materials: '+', '.join(v[:20])) for k,v in d2.items()}, indent=1))
