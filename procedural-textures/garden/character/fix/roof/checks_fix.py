"""Own checks of the roof builder (direction tests 20 to 23 and parts of 14 to 16). Run:
   blender -b START.blend --python checks_roof.py -- OUT.json [small]
Plain words: opens the starting scene, remembers what every object and material looked like, runs stage_roof.apply twice, and
reports (a) what changed outside the roof builder's own list (must be nothing), (b) object/material counts after the 1st and 2nd run
(idempotence), (c) normal-map hygiene of every changed material (Normal Map node, Tangent, uv_map exists, Non-Color image >= 1024,
mean blue >= 0.85, mean red/green 0.5 +- 0.03, no strong old bump), (d) UV hygiene (UV layers, range, flipped islands),
(e) counts for tiles, walls, stones, lantern."""
import sys, os, json, hashlib, time
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof'
sys.path.insert(0, HERE)
import bpy, numpy as np
import stage_roof
from r_common import PFX

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
small = len(argv) > 1 and argv[1] == 'small'
sizes = {'glaze': 256, 'plaster': 256, 'stone': 256, 'moss': 256} if small else None


def obj_sig(o):
    if o.type != 'MESH':
        return (o.type, tuple(round(x, 4) for x in o.location))
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get('co', co)
    h = hashlib.md5(np.round(co, 5).tobytes()).hexdigest()[:12]
    return (len(me.vertices), len(me.polygons), h, tuple(m.name if m else None for m in me.materials), tuple(round(x, 4) for x in o.location),
            tuple(sorted(c.name for c in o.users_collection)))


def mat_sig(m):
    if not m.use_nodes or m.node_tree is None:
        return None
    nt = m.node_tree
    return (len(nt.nodes), len(nt.links))


def snap():
    return ({o.name: obj_sig(o) for o in bpy.data.objects}, {m.name: mat_sig(m) for m in bpy.data.materials},
            {g.name: (len(g.nodes), len(g.links)) for g in bpy.data.node_groups},
            {l.name: (round(l.energy, 3), tuple(round(c, 3) for c in l.color)) for l in bpy.data.lights})

s0 = snap()
# lantern glow reference (colour and strength of 'Lantern flame')
def glow():
    m = bpy.data.materials['Lantern flame']
    res = []
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeEmission':
            res.append((tuple(round(x, 4) for x in n.inputs['Color'].default_value), round(n.inputs['Strength'].default_value, 4)))
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            res.append((tuple(round(x, 4) for x in n.inputs['Emission Color'].default_value), round(n.inputs['Emission Strength'].default_value, 4)))
    return res
glow0 = glow()
t = time.time()
rep1 = stage_roof.apply({'map_sizes': sizes} if sizes else {})
s1 = snap()
t1 = time.time() - t
rep2 = stage_roof.apply({'map_sizes': sizes} if sizes else {})
s2 = snap()
glow1 = glow()

own = set(stage_roof.OWN_OBJECTS)
changed_foreign = []
for name, sig in s1[0].items():
    if name.startswith('G6 roof'):
        continue
    if name not in s0[0]:
        changed_foreign.append(('NEW', name))
    elif sig != s0[0][name] and name not in own:
        changed_foreign.append(('CHANGED', name))
for name in s0[0]:
    if name not in s1[0]:
        changed_foreign.append(('DELETED', name))
changed_own = sorted(n for n in own if n in s1[0] and s1[0][n] != s0[0][n])
unchanged_own = sorted(n for n in own if n in s1[0] and s1[0][n] == s0[0][n])
mat_changed_foreign = [n for n, v in s1[1].items() if not n.startswith('G6 roof') and n in s0[1] and v != s0[1][n]]
mat_new_foreign = [n for n in s1[1] if not n.startswith('G6 roof') and n not in s0[1]]
mat_deleted = [n for n in s0[1] if n not in s1[1]]
ng_changed = [n for n, v in s1[2].items() if not n.startswith('G6 roof') and n in s0[2] and v != s0[2][n]]
ng_new = [n for n in s1[2] if not n.startswith('G6 roof') and n not in s0[2]]
lights_changed = [n for n, v in s1[3].items() if v != s0[3].get(n)]
idem = {'objects_run1': len(s1[0]), 'objects_run2': len(s2[0]), 'materials_run1': len(s1[1]), 'materials_run2': len(s2[1]),
        'node_groups_run1': len(s1[2]), 'node_groups_run2': len(s2[2]),
        'same_names': sorted(s1[0]) == sorted(s2[0]) and sorted(s1[1]) == sorted(s2[1]),
        'same_signatures': all(s1[0][k] == s2[0].get(k) for k in s1[0]), 'images_run2': len([i for i in bpy.data.images if i.name.startswith(PFX)])}

# normal map hygiene
nm_report = []
mats_changed = [m for m in bpy.data.materials if m.name.startswith(PFX) and m.use_nodes]
bad = []
for m in mats_changed:
    nt = m.node_tree
    nms = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeNormalMap']
    if not nms:
        continue
    for nm in nms:
        info = {'material': m.name, 'space': nm.space, 'uv_map': nm.uv_map}
        src = nm.inputs['Color'].links[0].from_node if nm.inputs['Color'].links else None
        if src is None or src.bl_idname != 'ShaderNodeTexImage' or src.image is None:
            bad.append((m.name, 'no image')); continue
        img = src.image
        info['image'] = img.name
        info['size'] = tuple(img.size)
        info['colorspace'] = img.colorspace_settings.name
        px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        info['mean_rgb'] = [round(float(px[:, c].mean()), 3) for c in range(3)]
        okc = info['colorspace'] == 'Non-Color' and min(img.size) >= (256 if small else 1024) and info['mean_rgb'][2] >= 0.85 \
            and abs(info['mean_rgb'][0] - 0.5) <= 0.03 and abs(info['mean_rgb'][1] - 0.5) <= 0.03 and nm.space == 'TANGENT'
        info['ok'] = bool(okc)
        # reaches a Principled normal?
        def reaches(node, depth=0):
            for o in node.outputs:
                for l in o.links:
                    if l.to_node.bl_idname == 'ShaderNodeBsdfPrincipled' and l.to_socket.name == 'Normal':
                        return True
                    if l.to_node.bl_idname == 'ShaderNodeGroup' and depth < 3:
                        # through a kit group: the group's Normal output goes to the Principled normal
                        for l2 in [l2 for o2 in l.to_node.outputs if o2.name.startswith('Normal') for l2 in o2.links]:
                            if l2.to_node.bl_idname == 'ShaderNodeBsdfPrincipled' or l2.to_node.bl_idname == 'ShaderNodeGroup':
                                return True
                    if depth < 6 and reaches(l.to_node, depth + 1):
                        return True
            return False
        info['reaches_principled_normal'] = reaches(nm)
        # leftover bump strength
        for b in [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBump']:
            if b.inputs['Strength'].default_value > 0.3 and not (b.inputs['Normal'].links):
                info['old_bump_over_0.3'] = round(b.inputs['Strength'].default_value, 3)
        # uv layer exists on every object using it
        users = [o for o in bpy.data.objects if o.type == 'MESH' and any(s.material == m for s in o.material_slots)]
        info['users'] = len(users)
        info['uv_ok'] = all(nm.uv_map in [u.name for u in o.data.uv_layers] for o in users) if users else None
        nm_report.append(info)
rep_nm = {'count': len(nm_report), 'all_ok': all(i['ok'] and i.get('uv_ok') is not False and i['reaches_principled_normal'] for i in nm_report),
          'failing': [i for i in nm_report if not (i['ok'] and i.get('uv_ok') is not False and i['reaches_principled_normal'])][:10],
          'images': sorted(set((i['image'], i['size'][0], i['mean_rgb'][2]) for i in nm_report))}

# UV hygiene: range and mirrored islands on the objects that got a UV layer
uv_rep = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not (o.name in own or o.name.startswith('G6 roof')):
        continue
    me = o.data
    if not me.uv_layers:
        uv_rep.append((o.name, 'NO UV')); continue
    lay = me.uv_layers[0]
    n = len(lay.data)
    uv = np.empty(n * 2, np.float32)
    lay.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    # mirrored faces: signed UV area opposite to the sign of ... count faces with tiny or negative area
    neg = 0
    deg = 0
    for p in me.polygons[:20000]:
        pts = uv[list(p.loop_indices)]
        a = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
        if abs(a) < 1e-10:
            deg += 1
        elif a < 0:
            neg += 1
    uv_rep.append((o.name, int(len(me.polygons)), round(float(uv.min()), 2), round(float(uv.max()), 2), int(neg), int(deg)))

result = {'seconds_first_run': round(t1, 1), 'foreign_changes': changed_foreign, 'own_objects_changed': changed_own, 'own_objects_unchanged': unchanged_own,
          'materials_changed_outside_G6': mat_changed_foreign, 'materials_new_outside_G6': mat_new_foreign, 'materials_deleted': mat_deleted,
          'node_groups_changed': ng_changed, 'node_groups_new': ng_new, 'lights_changed': lights_changed,
          'idempotence': idem, 'normal_maps': rep_nm, 'uv': uv_rep, 'glow_before': glow0, 'glow_after': glow1,
          'report_run1': {k: v for k, v in rep1.items() if k not in ('new_objects', 'new_materials')},
          'new_objects': rep1['new_objects'], 'new_materials': rep1['new_materials'], 'removed_objects': rep1['removed_objects'],
          'objects_before': len(s0[0]), 'objects_after': len(s1[0]), 'materials_before': len(s0[1]), 'materials_after': len(s1[1])}
json.dump(result, open(out, 'w'), indent=1, default=str)
print('CHECKS_DONE', out, 'foreign', len(changed_foreign), 'idem', idem['same_names'], idem['same_signatures'], 'nm_ok', rep_nm['all_ok'])
