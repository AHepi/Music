# usage: blender -b courtyard_final.blend -P check_diff.py -- LOOK OUT.json [steps]
# Opens the starting scene, takes an inventory, runs stage_shapes.apply(look), takes the inventory again and lists what changed.
import sys, os, json, re, time, hashlib
sys.dont_write_bytecode = True
HERE = 'proc-work/garden/shapes'
sys.path.insert(0, HERE)
import bpy, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
look, outjson = a[0], a[1]
steps = a[2].split(',') if len(a) > 2 else None
import stage_shapes

def inv():
    dg = bpy.context.evaluated_depsgraph_get()
    d = {'objects': {}, 'materials': {}, 'collections': sorted(c.name for c in bpy.data.collections), 'meshes': len(bpy.data.meshes), 'lights': {}, 'world': {}, 'render': {}}
    for ob in bpy.data.objects:
        o = {'type': ob.type, 'cols': sorted(c.name for c in ob.users_collection), 'parent': ob.parent.name if ob.parent else None,
             'mw': [round(x, 5) for row in ob.matrix_world for x in row], 'mods': [(m.name, m.type) for m in ob.modifiers],
             'mats': [s.material.name if s.material else None for s in ob.material_slots], 'hide': (ob.hide_render, ob.hide_viewport),
             'owner': ob.get('garden_owner'), 'role': ob.get('garden_role')}
        if ob.type == 'MESH':
            me = ob.data
            co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', co)
            o['verts'] = len(me.vertices); o['faces'] = len(me.polygons)
            o['geo'] = hashlib.md5(np.round(co, 5).tobytes()).hexdigest()[:12]
            o['smooth'] = int(sum(p.use_smooth for p in me.polygons))
        elif ob.type == 'CURVE':
            ev = ob.evaluated_get(dg); me = ev.to_mesh(); co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', co)
            o['geo'] = hashlib.md5(np.round(co, 5).tobytes()).hexdigest()[:12]; ev.to_mesh_clear()
        elif ob.type == 'LIGHT':
            L = ob.data; o['light'] = (L.type, round(L.energy, 4), [round(c, 4) for c in L.color])
        d['objects'][ob.name] = o
    for m in bpy.data.materials:
        t = m.node_tree
        d['materials'][m.name] = {'nodes': len(t.nodes) if t else 0, 'links': len(t.links) if t else 0, 'users': m.users,
                                  'bc': [round(x, 4) for x in m.diffuse_color]}
        if t:
            vals = []
            for n in t.nodes:
                for i in n.inputs:
                    if hasattr(i, 'default_value') and not i.is_linked:
                        try: vals.append(round(float(i.default_value), 4))
                        except Exception:
                            try: vals.append(tuple(round(float(x), 4) for x in i.default_value))
                            except Exception: pass
            d['materials'][m.name]['vals'] = hashlib.md5(repr(vals).encode()).hexdigest()[:10]
    sc = bpy.context.scene; w = sc.world
    d['world'] = {'name': w.name if w else None, 'nodes': len(w.node_tree.nodes) if w and w.node_tree else 0}
    d['render'] = {'engine': sc.render.engine, 'res': (sc.render.resolution_x, sc.render.resolution_y), 'cam': sc.camera.name if sc.camera else None,
                   'samples': getattr(sc.cycles, 'samples', None), 'vt': sc.view_settings.view_transform, 'look': sc.view_settings.look, 'exposure': sc.view_settings.exposure}
    return d

OWN = [r'^Astra / varied planks', r'^Astra / Planked run controls', r'^Bridge pier \d', r'^Veranda step', r'^Stone plinth$', r'^Hall posts$', r'^Hall beams$', r'^Hall plaster$',
       r'^Eave soffit$', r'^Hall roof$', r'^Back wall, (left|right)( cap)?$', r'^Right wall behind hall( cap)?$', r'^Rock \d+$', r'^Gravel rock \d+$', r'^Pond edge stone \d+$',
       r'^Stepping stone \d+$', r'^Lantern (base|post|gallery|firebox|cap|finial|window glow)$', r'^Water basin$', r'^Basin water$', r'^Raked gravel court$', r'^Shoji bars$', r'^Shoji paper$']
def owned(n): return any(re.match(p, n) for p in OWN)

before = inv()
t = time.time()
opts = {'look': look}
if steps: opts['steps'] = steps
rep = stage_shapes.apply(opts)
secs = time.time() - t
bpy.context.view_layer.update()
after = inv()
bo, ao = before['objects'], after['objects']
created = sorted(set(ao) - set(bo)); deleted = sorted(set(bo) - set(ao))
changed = []
for n in sorted(set(bo) & set(ao)):
    x, y = bo[n], ao[n]
    diffs = [k for k in ('type', 'cols', 'parent', 'mw', 'mods', 'mats', 'hide', 'verts', 'faces', 'geo', 'smooth', 'light') if x.get(k) != y.get(k)]
    if diffs: changed.append((n, diffs))
foreign = [(n, d) for n, d in changed if not owned(n)]
matdiff = {'added': sorted(set(after['materials']) - set(before['materials'])), 'removed': sorted(set(before['materials']) - set(after['materials'])),
           'changed': sorted(n for n in set(before['materials']) & set(after['materials']) if {k: v for k, v in before['materials'][n].items() if k != 'users'} != {k: v for k, v in after['materials'][n].items() if k != 'users'})}
own_changed = set(rep['changed']); ind_changed = set(n for n, _ in changed)
res = {'stage_report_matches_independent_diff': (own_changed == ind_changed, sorted(own_changed ^ ind_changed)), 'look': look, 'seconds': round(secs, 1), 'created': created, 'deleted': deleted, 'changed': changed, 'foreign_changes': foreign, 'materials': matdiff,
       'collections_added': sorted(set(after['collections']) - set(before['collections'])), 'world_same': before['world'] == after['world'], 'render_same': before['render'] == after['render'],
       'n_objects': (len(bo), len(ao)), 'material_slots_lost': [n for n in sorted(set(bo) & set(ao)) if bo[n]['mats'] and not ao[n]['mats']],
       'material_slots_changed_on_existing': [(n, bo[n]['mats'], ao[n]['mats']) for n in sorted(set(bo) & set(ao)) if bo[n]['mats'] != ao[n]['mats']],
       'new_untagged': [n for n in created if not ao[n].get('owner') or not ao[n].get('role')]}
res['names_before'] = sorted(bo)
res['names_after'] = sorted(ao)
res['materials_before'] = sorted(before['materials'])
res['materials_after'] = sorted(after['materials'])
json.dump(res, open(outjson, 'w'), indent=1, default=str)
with open(outjson.replace('.json', '_names.txt'), 'w') as fh:
    fh.write(f'LOOK {look}\nOBJECTS BEFORE ({len(bo)})\n' + '\n'.join(f"  {n}  [{bo[n]['type']}]  materials: {bo[n]['mats']}" for n in sorted(bo)) + '\n')
    fh.write(f'\nOBJECTS AFTER ({len(ao)})\n' + '\n'.join(f"  {n}  [{ao[n]['type']}]  materials: {ao[n]['mats']}" + ('  NEW' if n in created else '') + ('  CHANGED' if n in dict(changed) else '') for n in sorted(ao)) + '\n')
    fh.write(f"\nMATERIALS BEFORE ({len(before['materials'])})\n  " + '\n  '.join(sorted(before['materials'])) + f"\n\nMATERIALS AFTER ({len(after['materials'])})\n  " + '\n  '.join(f"{m}{'  NEW' if m in matdiff['added'] else ''}" for m in sorted(after['materials'])) + '\n')
print('DIFF look', look, 'seconds', res['seconds'])
print('  objects', res['n_objects'], 'created', len(created), 'deleted', len(deleted), 'changed', len(changed))
print('  created:', created)
print('  deleted:', deleted)
print('  changed (name, what):'); [print('    ', n, d) for n, d in changed]
print('  FOREIGN changes (not in my ownership list):', foreign)
print('  materials added/removed/changed:', matdiff)
print('  stage own report = independent diff?', res['stage_report_matches_independent_diff'])
print('  existing objects whose material slots changed:', res['material_slots_changed_on_existing'])
print('  objects that lost all materials:', res['material_slots_lost'])
print('  new objects without garden_owner/garden_role:', res['new_untagged'])
print('  collections added:', res['collections_added'], ' world same:', res['world_same'], ' render settings same:', res['render_same'])
if len(sys.argv) and '--save' in sys.argv:
    pass
