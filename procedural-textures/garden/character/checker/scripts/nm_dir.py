import bpy, json, sys, os, numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
for p in (G + '/roof', G + '/pond', G + '/direction/shared', G + '/wood', G + '/ground'):
    sys.path.insert(0, p)
R = {'images': {}, 'mapping_chain': {}}
def decode(img):
    w, h = img.size
    px = np.empty(w * h * img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)[::-1]     # rows from the TOP
    n = px[..., :3] * 2 - 1
    nz = np.maximum(n[..., 2], 1e-3)
    return -n[..., 0] / nz, n[..., 1] / nz        # gx (per px, +x), grow (per row down)
def known_heights():
    K = {}
    wm = G + '/checker/known/wood/'
    for nm, f in (('plank_top_normal.png', '_h_plank_top.npy'), ('end_grain_normal.png', '_h_end_grain.npy'), ('footing_stone_normal.png', '_h_footing_stone.npy'), ('post_timber_normal.png', '_h_post_timber.npy')):
        try: K[nm] = np.load(wm + f).astype(np.float32)
        except Exception as e: K[nm] = 'ERR ' + str(e)[:80]
    gm = G + '/checker/known/ground/'
    for nm, f in (('G6 ground_normal', 'ground_height.png'), ('G6 moss_normal', 'moss_height.png'), ('G6 pebble_normal', 'pebble_height.png'), ('G6 stone_normal', 'stone_height.png')):
        try:
            im = bpy.data.images.load(gm + f); im.colorspace_settings.name = 'Non-Color'
            w, h = im.size; a = np.empty(w * h * im.channels, dtype=np.float32); im.pixels.foreach_get(a)
            K[nm] = a.reshape(h, w, im.channels)[::-1][..., 0].copy(); bpy.data.images.remove(im)
        except Exception as e: K[nm] = 'ERR ' + str(e)[:80]
    try:
        import r_maps
        K['G6 roof / glaze normal'] = r_maps.glaze_height(1024, 11)
        K['G6 roof / plaster normal'] = r_maps.plaster_height(2048, 21)
        K['G6 roof / stone normal'] = r_maps.stone_height(1024, 31)
        K['G6 roof / moss normal'] = r_maps.moss_height(1024, 41)
    except Exception as e:
        K['roof'] = 'ERR ' + str(e)[:200]
    try:
        import g6p_maps as gp
        h, px = gp.swell_height(2048); K['swell_normal.png'] = h
        h, a, b = gp.ripple_height(2048); K['ripple_normal.png'] = h
        s = gp.load_scan('clean_pebbles_disp_1k.jpg'); K['pebble_normal.png'] = gp.stretch01(gp.gauss_blur(s, 5.0))
        s = gp.load_scan('trident_maple_bark_disp_1k.jpg'); K['maple_bark_normal.png'] = gp.stretch01(gp.gauss_blur(s, 2.2))
        s = gp.load_scan('pine_bark_disp_1k.jpg'); K['pine_bark_normal.png'] = gp.stretch01(gp.gauss_blur(s, 2.6))
    except Exception as e:
        K['pond'] = 'ERR ' + str(e)[:200]
    return K
K = known_heights()
for k, v in K.items():
    if isinstance(v, str): R['images'][k] = {'known_height': v}
def corr(a, b):
    a = a.ravel() - a.mean(); b = b.ravel() - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else float('nan')
for img in bpy.data.images:
    if img.name not in K or isinstance(K[img.name], str): continue
    gx, gr = decode(img)
    h = np.asarray(K[img.name], dtype=np.float32)
    if h.ndim == 3: h = h[..., :3].mean(axis=2)
    if h.shape != gx.shape:
        R['images'][img.name] = {'shape_mismatch': [list(h.shape), list(gx.shape)]}
        continue
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dr = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    R['images'][img.name] = {'corr_gx_vs_dh/dx': round(corr(gx, dx), 3), 'corr_grow_vs_dh/drow(down)': round(corr(gr, dr), 3),
                             'implied_flipped_green_corr': round(corr(-gr, dr), 3)}
# mapping chain per material: rotation / negative scale / box projection
def chain(nt, node, depth=0):
    # follow Vector input back
    out = []
    cur = node
    for _ in range(6):
        l = [x for x in nt.links if x.to_node == cur and x.to_socket.name == 'Vector']
        if not l: break
        cur = l[0].from_node
        if cur.type == 'MAPPING':
            out.append({'type': 'MAPPING', 'loc': [round(v, 3) for v in cur.inputs['Location'].default_value], 'rot': [round(v, 3) for v in cur.inputs['Rotation'].default_value], 'scale': [round(v, 3) for v in cur.inputs['Scale'].default_value], 'vec_type': cur.vector_type})
        elif cur.type == 'UVMAP':
            out.append({'type': 'UVMAP', 'uv_map': cur.uv_map})
        else:
            out.append({'type': cur.type})
    return out
bad = []
for m in bpy.data.materials:
    if not m.use_nodes or not m.node_tree: continue
    def walk(nt, d=0):
        for n in nt.nodes:
            if n.type == 'NORMAL_MAP':
                for l in nt.links:
                    if l.to_node == n and l.to_socket.name == 'Color' and l.from_node.type == 'TEX_IMAGE':
                        tex = l.from_node
                        c = chain(nt, tex)
                        info = {'img': tex.image.name if tex.image else None, 'projection': tex.projection, 'chain': c, 'nm_uv': n.uv_map}
                        R['mapping_chain'].setdefault(m.name, []).append(info)
                        for e in c:
                            if e['type'] == 'MAPPING':
                                if any(abs(v) > 1e-6 for v in e['rot']) or any(v < 0 for v in e['scale']):
                                    bad.append((m.name, 'mapping rotates or mirrors', e))
                        if tex.projection != 'FLAT': bad.append((m.name, 'projection', tex.projection))
                        # uv mismatch between UV Map node and Normal Map node
                        for e in c:
                            if e['type'] == 'UVMAP' and e['uv_map'] != n.uv_map: bad.append((m.name, 'tex uv != normalmap uv', (e['uv_map'], n.uv_map)))
                        if not any(e['type'] == 'UVMAP' for e in c): bad.append((m.name, 'texture not driven by UVMap node', [e['type'] for e in c]))
            if n.type == 'GROUP' and n.node_tree and d < 3: walk(n.node_tree, d + 1)
    walk(m.node_tree)
R['mapping_problems'] = bad
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('NMDIR done', len(R['images']), len(bad))
