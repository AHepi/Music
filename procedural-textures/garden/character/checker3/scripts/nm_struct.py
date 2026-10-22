# Fresh-eyes check of every normal map in the combined scene (checker's own code).
# blender -b garden_character.blend --python nm_struct.py -- OUT.json
import bpy, sys, json, numpy as np
OUT = sys.argv[-1]
R = {}

def walk_back(node, sock_name, depth=0, seen=None):
    """follow the link into node.inputs[sock_name] backwards to the first Image Texture node (through reroutes, math, mix, hue ...)"""
    if depth > 8: return None
    s = node.inputs.get(sock_name) if isinstance(sock_name, str) else node.inputs[sock_name]
    if s is None or not s.is_linked: return None
    n = s.links[0].from_node
    if n.bl_idname == 'ShaderNodeTexImage': return n
    for i in n.inputs:
        if i.is_linked:
            r = walk_back(n, i.name if i.name in n.inputs.keys() else 0, depth + 1)
            if r is not None: return r
    return None

def forward_reach(tree, start_sock, depth=0):
    """does start_sock reach the 'Normal' input of a Principled BSDF? returns path of node types"""
    if depth > 10: return None
    for l in start_sock.links:
        n = l.to_node
        if n.bl_idname == 'ShaderNodeBsdfPrincipled' and l.to_socket.name == 'Normal':
            return [n.bl_idname]
        if n.bl_idname in ('ShaderNodeBsdfPrincipled',):
            continue
        # pass through any node that has a 'Normal' output (Bump, Normal Map, Mix of vectors, group in, reroute)
        for o in n.outputs:
            if o.is_linked and o.name in ('Normal', 'Vector', 'Color', 'Result', 'Value', 'Fac') or (n.bl_idname == 'NodeReroute' and o.is_linked):
                r = forward_reach(tree, o, depth + 1)
                if r: return [n.bl_idname] + r
    return None

def trees_of(mat):
    out = [(mat.name, mat.node_tree)]
    stack = [(mat.name, mat.node_tree)]
    seen = {mat.node_tree.name}
    while stack:
        nm, t = stack.pop()
        for n in t.nodes:
            if n.bl_idname == 'ShaderNodeGroup' and n.node_tree and n.node_tree.name not in seen:
                seen.add(n.node_tree.name)
                out.append((nm + ' > ' + n.node_tree.name, n.node_tree)); stack.append((nm + ' > ' + n.node_tree.name, n.node_tree))
    return out

# image statistics
imgstats = {}
def img_stats(im):
    if im.name in imgstats: return imgstats[im.name]
    w, h = im.size
    n = w * h * im.channels
    px = np.empty(n, dtype=np.float32); im.pixels.foreach_get(px)
    px = px.reshape(h, w, im.channels)
    st = {'size': [w, h], 'cs': im.colorspace_settings.name, 'mean_rgb': [round(float(px[..., c].mean()), 3) for c in range(3)], 'packed': im.packed_file is not None, 'is_float': im.is_float, 'alpha_mode': im.alpha_mode}
    imgstats[im.name] = st
    return st

# which materials are used by which mesh objects
mat_users = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.data is None: continue
    for s in ob.material_slots:
        if s.material:
            mat_users.setdefault(s.material.name, []).append(ob)
# materials used by geometry-nodes Set Material nodes
gn_mats = {}
for ng in bpy.data.node_groups:
    for n in ng.nodes:
        if n.bl_idname == 'GeometryNodeSetMaterial':
            m = n.inputs['Material'].default_value
            if m: gn_mats.setdefault(m.name, set()).add(ng.name)
        if n.bl_idname == 'GeometryNodeInputMaterial' and n.material:
            gn_mats.setdefault(n.material.name, set()).add(ng.name)

rows = []
for mat in bpy.data.materials:
    if not mat.use_nodes or mat.node_tree is None: continue
    info = {'material': mat.name, 'normal_maps': [], 'bumps': [], 'users': len(mat_users.get(mat.name, [])), 'via_geometry_nodes': sorted(gn_mats.get(mat.name, []))[:3]}
    for tname, t in trees_of(mat):
        for n in t.nodes:
            if n.bl_idname == 'ShaderNodeNormalMap':
                col = n.inputs['Color']
                src = walk_back(n, 'Color')
                reach = forward_reach(t, n.outputs['Normal'])
                entry = {'tree': tname, 'node': n.name, 'space': n.space, 'uv_map': n.uv_map, 'strength': round(float(n.inputs['Strength'].default_value), 3), 'strength_linked': n.inputs['Strength'].is_linked,
                         'image': src.image.name if (src and src.image) else None, 'tex_extension': src.extension if src else None, 'reaches_principled_normal': reach, 'color_linked': col.is_linked}
                if src and src.image:
                    entry['img'] = img_stats(src.image)
                    entry['tex_colorspace_node'] = src.image.colorspace_settings.name
                # UV layers on users
                miss = []
                for ob in mat_users.get(mat.name, []):
                    names = [u.name for u in ob.data.uv_layers]
                    if n.uv_map:
                        if n.uv_map not in names: miss.append(ob.name)
                    else:
                        if not names: miss.append(ob.name)
                entry['users_missing_uv_layer'] = miss[:6]
                entry['n_users_missing_uv_layer'] = len(miss)
                info['normal_maps'].append(entry)
            elif n.bl_idname == 'ShaderNodeBump':
                nrm_linked = n.inputs['Normal'].is_linked
                fed = bool(nrm_linked and n.inputs['Normal'].links[0].from_node.bl_idname == 'ShaderNodeNormalMap')
                info['bumps'].append({'tree': tname, 'strength': round(float(n.inputs['Strength'].default_value), 3), 'fed_by_normal_map': fed, 'strength_linked': n.inputs['Strength'].is_linked})
    rows.append(info)
R['materials_total'] = len(bpy.data.materials)
with_nm = [r for r in rows if r['normal_maps']]
R['materials_with_normal_map'] = len(with_nm)
R['materials_with_normal_map_names'] = [r['material'] for r in with_nm]
# problems
prob = []
for r in with_nm:
    for e in r['normal_maps']:
        p = []
        if e['space'] != 'TANGENT': p.append('space ' + e['space'])
        if not e['image']: p.append('no image behind the Color input')
        else:
            im = e['img']
            if im['cs'] != 'Non-Color': p.append('image colour space ' + im['cs'])
            if min(im['size']) < 1024: p.append('image smaller than 1024: %s' % im['size'])
            if im['mean_rgb'][2] < 0.85: p.append('mean blue %.3f' % im['mean_rgb'][2])
            if abs(im['mean_rgb'][0] - 0.5) > 0.03 or abs(im['mean_rgb'][1] - 0.5) > 0.03: p.append('mean r,g %s' % im['mean_rgb'][:2])
        if not e['reaches_principled_normal']: p.append('does not reach a Principled Normal (checked forward through nodes)')
        if e['n_users_missing_uv_layer']: p.append('uv layer "%s" missing on %d user objects, e.g. %s' % (e['uv_map'], e['n_users_missing_uv_layer'], e['users_missing_uv_layer'][:3]))
        if e['strength_linked']: p.append('strength linked')
        if not e['users_missing_uv_layer'] and r['users'] == 0 and not r['via_geometry_nodes']: p.append('material has no mesh user')
        if p: prob.append({'material': r['material'], 'node': e['node'], 'problems': p})
R['problems'] = prob
R['bump_leftovers_over_0.3_not_fed'] = [{'material': r['material'], 'bumps': [b for b in r['bumps'] if b['strength'] > 0.3 and not b['fed_by_normal_map']]} for r in rows if any(b['strength'] > 0.3 and not b['fed_by_normal_map'] for b in r['bumps'])][:60]
R['n_bump_leftover_materials'] = len(R['bump_leftovers_over_0.3_not_fed'])
# images used by normal maps
R['images_used'] = {}
for r in with_nm:
    for e in r['normal_maps']:
        if e['image']:
            R['images_used'].setdefault(e['image'], {'stats': e['img'], 'materials': [], 'uv_maps': set(), 'strengths': set(), 'spaces': set()})
            d = R['images_used'][e['image']]
            d['materials'].append(r['material']); d['uv_maps'].add(e['uv_map']); d['strengths'].add(e['strength']); d['spaces'].add(e['space'])
for k, d in R['images_used'].items():
    d['n_materials'] = len(d['materials']); d['materials'] = d['materials'][:5]; d['uv_maps'] = sorted(d['uv_maps']); d['strengths'] = sorted(d['strengths']); d['spaces'] = sorted(d['spaces'])
R['n_images_used'] = len(R['images_used'])
R['rows'] = [{k: v for k, v in r.items() if k != 'normal_maps'} | {'nm': [{kk: vv for kk, vv in e.items() if kk not in ('img',)} for e in r['normal_maps']]} for r in with_nm]
# objects with no UV layer at all that use a normal-mapped material
nouv = []
nm_names = set(R['materials_with_normal_map_names'])
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if any(s.material and s.material.name in nm_names for s in ob.material_slots):
        if not ob.data.uv_layers: nouv.append(ob.name)
R['mesh_objects_with_normal_mapped_material_but_no_uv'] = nouv
# image-level duplicates and sizes in the blend
R['images_in_blend'] = len(bpy.data.images)
json.dump(R, open(OUT, 'w'), indent=1, default=lambda o: sorted(o) if isinstance(o, set) else float(o))
print('NM STRUCT DONE', R['materials_with_normal_map'], 'of', len(rows), 'problems', len(prob))
