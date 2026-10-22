import bpy, json, sys, numpy as np
out = {'materials': {}, 'images': {}}
FLIPPERS = {'INVERT', 'MATH', 'VECT_MATH', 'SEPARATE_COLOR', 'COMBINE_COLOR', 'SEPARATE_XYZ', 'COMBINE_XYZ', 'MAP_RANGE', 'CURVE_RGB', 'GAMMA', 'HUE_SAT', 'BRIGHTCONTRAST', 'MIX', 'MIX_RGB'}

def links_from(nt, node, sock):
    return [l for l in nt.links if l.from_node == node and l.from_socket == sock and not l.is_muted]

def reach(nt, node, sock, stack, seen, trail, hits):
    for l in links_from(nt, node, sock):
        to, ts = l.to_node, l.to_socket
        key = (nt.name, to.name, ts.identifier, len(stack))
        if key in seen: continue
        seen.add(key)
        t2 = trail + [to.type + (':' + to.operation if hasattr(to, 'operation') else '')]
        if to.type == 'GROUP' and to.node_tree is not None:
            sub = to.node_tree
            for gi in [n for n in sub.nodes if n.type == 'GROUP_INPUT']:
                for o in gi.outputs:
                    if o.identifier == ts.identifier:
                        reach(sub, gi, o, stack + [(nt, to)], seen, t2 + ['[' + sub.name + ']'], hits)
        elif to.type == 'GROUP_OUTPUT':
            if stack:
                onode_nt, gnode = stack[-1]
                for o in gnode.outputs:
                    if o.identifier == ts.identifier:
                        reach(onode_nt, gnode, o, stack[:-1], seen, t2, hits)
        elif to.type == 'BSDF_PRINCIPLED':
            if ts.name == 'Normal':
                hits.append(t2)
        else:
            for o in to.outputs:
                reach(nt, to, o, stack, seen, t2, hits)

def walk(nt, matname, depth, res):
    for n in nt.nodes:
        if n.type == 'NORMAL_MAP':
            # image feeding Color
            src = None
            sock = n.inputs['Color']
            img = None
            for l in nt.links:
                if l.to_node == n and l.to_socket == sock:
                    cur = l.from_node
                    for _ in range(5):
                        if cur.type == 'TEX_IMAGE':
                            img = cur.image; src = cur; break
                        # go back through first linked input
                        nxt = None
                        for l2 in nt.links:
                            if l2.to_node == cur:
                                nxt = l2.from_node; break
                        if nxt is None: break
                        cur = nxt
            hits = []
            reach(nt, n, n.outputs['Normal'], [], set(), ['NORMAL_MAP'], hits)
            strength = n.inputs['Strength'].default_value
            res.append({'node': n.name, 'in_group': nt.name if depth else None, 'space': n.space, 'uv_map': n.uv_map, 'strength': round(float(strength), 3), 'strength_linked': n.inputs['Strength'].is_linked,
                        'image': img.name if img else None, 'image_cs': img.colorspace_settings.name if img else None, 'image_size': list(img.size) if img else None,
                        'tex_interp': src.interpolation if src else None, 'tex_ext': src.extension if src else None,
                        'reaches_principled_normal': len(hits) > 0, 'paths': [' > '.join(h) for h in hits[:3]]})
        if n.type == 'GROUP' and n.node_tree is not None and depth < 4:
            walk(n.node_tree, matname, depth + 1, res)

obj_users = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    for s in ob.material_slots:
        if s.material:
            obj_users.setdefault(s.material.name, []).append(ob.name)
# materials set by geometry nodes
gn_mat = {}
for ng in bpy.data.node_groups:
    if ng.bl_idname != 'GeometryNodeTree': continue
    for n in ng.nodes:
        if n.type == 'SET_MATERIAL':
            m = n.inputs['Material'].default_value
            if m: gn_mat.setdefault(m.name, set()).add(ng.name)
gn_users = {}
for ob in bpy.data.objects:
    for m in ob.modifiers:
        if m.type == 'NODES' and m.node_group:
            for mn, groups in gn_mat.items():
                if m.node_group.name in groups: gn_users.setdefault(mn, []).append(ob.name)
total = 0
n_with = 0
for m in bpy.data.materials:
    if not m.use_nodes or m.node_tree is None: continue
    res = []
    walk(m.node_tree, m.name, 0, res)
    if not res: continue
    n_with += 1
    total += len(res)
    users = obj_users.get(m.name, [])
    # uv check
    uvbad = []
    for r in res:
        if r['uv_map']:
            for u in users:
                ob = bpy.data.objects[u]
                if r['uv_map'] not in [x.name for x in ob.data.uv_layers]:
                    uvbad.append((u, r['uv_map']))
    # bump leftovers
    bumps = []
    def find_bumps(nt, d=0):
        for n in nt.nodes:
            if n.type == 'BUMP':
                fed = any(l.to_node == n and l.to_socket.name == 'Normal' for l in nt.links)
                bumps.append({'strength': round(float(n.inputs['Strength'].default_value), 3), 'normal_input_linked': fed, 'in': nt.name})
            if n.type == 'GROUP' and n.node_tree is not None and d < 3: find_bumps(n.node_tree, d + 1)
    find_bumps(m.node_tree)
    nimg = len([n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'])
    out['materials'][m.name] = {'normal_maps': res, 'users': users, 'n_users': len(users), 'gn_users': gn_users.get(m.name, []), 'uv_missing': uvbad, 'bumps': bumps, 'n_image_nodes_top': nimg}
out['n_materials_with_normal_map'] = n_with
out['n_normal_map_nodes'] = total
# images
used = set()
for mn, d in out['materials'].items():
    for r in d['normal_maps']:
        if r['image']: used.add(r['image'])
for name in sorted(used):
    img = bpy.data.images[name]
    w, h = img.size
    px = np.empty(w * h * img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)
    out['images'][name] = {'size': [w, h], 'cs': img.colorspace_settings.name, 'packed': img.packed_file is not None, 'mean_rgb': [round(float(px[..., i].mean()), 4) for i in range(3)], 'float': img.is_float,
                           'min_rgb': [round(float(px[..., i].min()), 3) for i in range(3)], 'users_mats': [mn for mn, d in out['materials'].items() if any(r['image'] == name for r in d['normal_maps'])][:6]}
json.dump(out, open(sys.argv[-1], 'w'), indent=1)
print('NMSTRUCT', n_with, total, len(used))
