# POND BUILDER: the checks (direction tests 18 to 23). Runs inside Blender, on the RunPod card or locally (no graphics card needed except where said).
# usage (the scene opened first for 'ownership' and 'scene'):
#   blender -b START.blend -P test_pond.py -- ownership  OUT.json
#   blender -b START.blend -P test_pond.py -- scene      OUT.json        (staged scene facts: counts, maps, UV hygiene, node checks)
#   blender -b --factory-startup -P test_pond.py -- direction OUT.json   (normal-map test light: NORMAL_DIRECTION line + per-map correlations)
#   blender -b --factory-startup -P test_pond.py -- analyze OUT.json IMAGE.png photo|veranda [more pairs ...]   (value range, saturation, detail energy, bands)
import bpy
import sys
import os
import json
import math
import hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OWN_OBJECTS = (['Pond water', 'Basin water', 'Life / pond bed', 'Life / pond pebbles', 'Lily pads', 'Lotus blossoms', 'Life / iris clumps', 'Life / lily stems',
                'Maple trunk', 'Maple inner mass', 'Maple leaves', 'Pine trunk', 'Pine pads', 'Bamboo stalks', 'Bamboo leaves', 'Bamboo fence', 'Basin bamboo spout',
                'Basin ladle']
               + ['Maple branch'] + ['Maple branch.%03d' % i for i in range(1, 17)] + ['Maple leaf source %d' % i for i in range(5)]
               + ['Pine limb'] + ['Pine limb.%03d' % i for i in range(1, 8)])
OWN_MATERIALS = ['Pond water', 'Life / pond bed', 'Life / iris blade', 'Life / lily stem', 'Lily pad', 'Lotus blossom', 'Maple leaves', 'Maple inner mass', 'Bark',
                 'GARDEN bark.pine', 'Pine needles', 'Bamboo stalk', 'Bamboo leaf colour', 'GARDEN ground.earth']


def is_mine_obj(o):
    return o.name in OWN_OBJECTS or o.get('g6p_new') == 1 or o.name.startswith('G6 pond')


def is_mine_mat(m):
    return m.name in OWN_MATERIALS or m.name.startswith('G6 pond')


# ------------------------------------------------------------------------------------------------ snapshots (ownership, test 23)
def hash_floats(a):
    a = np.round(np.asarray(a, dtype=np.float64) * 1e4).astype(np.int64)
    return hashlib.sha1(a.tobytes()).hexdigest()[:16]


def obj_snapshot(o):
    d = dict(type=o.type, loc=[round(v, 4) for v in o.location], rot=[round(v, 4) for v in o.rotation_euler], scale=[round(v, 4) for v in o.scale],
             collections=sorted(c.name for c in o.users_collection), lightgroup=getattr(o, 'lightgroup', ''), hide_render=o.hide_render,
             materials=[s.material.name if s.material else None for s in o.material_slots], modifiers=[m.name for m in o.modifiers])
    if o.type == 'MESH':
        me = o.data
        n = len(me.vertices)
        co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co)
        d['verts'] = n; d['faces'] = len(me.polygons); d['pos_hash'] = hash_floats(co)
        d['uv'] = [u.name for u in me.uv_layers]
    elif o.type == 'CURVE':
        d['splines'] = [[tuple(round(v, 4) for v in p.co[:3]) for p in s.points] for s in o.data.splines]
    return d


def mat_snapshot(m):
    if m.node_tree is None:
        return dict(nodes=0, links=0)
    nt = m.node_tree
    return dict(nodes=len(nt.nodes), links=len(nt.links), users=m.users)


def take_snapshot():
    return dict(objects={o.name: obj_snapshot(o) for o in bpy.data.objects}, materials={m.name: mat_snapshot(m) for m in bpy.data.materials},
                collections={c.name: sorted(x.name for x in c.objects) for c in bpy.data.collections},
                lights={o.name: (round(o.data.energy, 4), tuple(round(v, 4) for v in o.data.color)) for o in bpy.data.objects if o.type == 'LIGHT'},
                cameras={o.name: (round(o.data.lens, 3), [round(v, 4) for v in o.location]) for o in bpy.data.objects if o.type == 'CAMERA' and not o.name.startswith('G6 pond')})


def compare_snapshots(a, b):
    """Differences in everything that is NOT the pond builder's. Returns a dict of lists (empty lists = clean)."""
    out = dict(objects_changed=[], objects_removed=[], objects_added_not_mine=[], materials_changed=[], collections_changed=[], lights_changed=[], cameras_changed=[])
    for name, sa in a['objects'].items():
        if name in OWN_OBJECTS:
            continue
        sb = b['objects'].get(name)
        if sb is None:
            out['objects_removed'].append(name)
        elif sa != sb:
            # a collection list may differ only by the G6 pond collection (never for other people's objects)
            diff = [k for k in sa if sa[k] != sb.get(k)]
            out['objects_changed'].append((name, diff))
    for name in b['objects']:
        if name not in a['objects'] and not (name.startswith('G6 pond') or b['objects'][name].get('type') == 'CAMERA' and name.startswith('G6 pond')):
            out['objects_added_not_mine'].append(name)
    for name, sa in a['materials'].items():
        if name in OWN_MATERIALS:
            continue
        sb = b['materials'].get(name)
        if sb is None or (sa['nodes'], sa['links']) != (sb['nodes'], sb['links']):
            out['materials_changed'].append((name, sa, sb))
    for name, sa in a['collections'].items():
        sb = b['collections'].get(name)
        sa2 = [n for n in sa if n not in OWN_OBJECTS]
        sb2 = [n for n in (sb or []) if not n.startswith('G6 pond') and n not in OWN_OBJECTS]
        if sorted(sa2) != sorted(sb2):
            out['collections_changed'].append(name)
    if a['lights'] != b['lights']:
        out['lights_changed'] = [k for k in a['lights'] if a['lights'][k] != b['lights'].get(k)]
    if a['cameras'] != b['cameras']:
        out['cameras_changed'] = [k for k in a['cameras'] if a['cameras'][k] != b['cameras'].get(k)]
    return out


def mode_ownership(outpath):
    import stage_pond
    snap0 = take_snapshot()
    rep1 = stage_pond.apply({})
    snap1 = take_snapshot()
    f1 = '/tmp/_g6p_run1.blend'
    bpy.ops.wm.save_as_mainfile(filepath=f1, copy=True)
    rep2 = stage_pond.apply({})
    snap2 = take_snapshot()
    f2 = '/tmp/_g6p_run2.blend'
    bpy.ops.wm.save_as_mainfile(filepath=f2, copy=True)
    res = dict(
        others_after_first_run=compare_snapshots(snap0, snap1),
        others_after_second_run=compare_snapshots(snap0, snap2),
        objects_before=len(snap0['objects']), objects_after_1=len(snap1['objects']), objects_after_2=len(snap2['objects']),
        verts_total_1=sum(v.get('verts', 0) for v in snap1['objects'].values()), verts_total_2=sum(v.get('verts', 0) for v in snap2['objects'].values()),
        file_bytes_1=os.path.getsize(f1), file_bytes_2=os.path.getsize(f2),
        same_names_twice=sorted(snap1['objects']) == sorted(snap2['objects']),
        same_positions_twice=all(snap1['objects'][k].get('pos_hash') == snap2['objects'][k].get('pos_hash') for k in snap1['objects'] if k in snap2['objects']),
        created_first_run=rep1['created'], created_second_run=rep2['created'], new_materials=rep1['new_materials'],
        duplicate_names=[n for n in snap2['objects'] if n[-4:-3] == '.' and n[-3:].isdigit() and n.startswith('G6 pond')],
        owned_objects_changed=[k for k in OWN_OBJECTS if k in snap0['objects'] and (snap0['objects'][k].get('pos_hash') != snap1['objects'].get(k, {}).get('pos_hash') or snap0['objects'][k]['type'] != snap1['objects'].get(k, {}).get('type'))],
        tags_ok=all(bpy.data.objects[n].get('garden_owner') == 'pond' and bpy.data.objects[n].get('garden_role') for n in snap2['objects'] if n.startswith('G6 pond')),
        in_collection_ok=all('G6 pond' in [c.name for c in bpy.data.objects[n].users_collection] for n in snap2['objects'] if n.startswith('G6 pond')),
        names_kept=[n for n in OWN_OBJECTS if n in snap0['objects'] and n not in snap2['objects']],
        rim_receivers_kept=sorted(set(n for n in snap0['collections'].get('G4 rim receivers', [])) - set(snap2['collections'].get('G4 rim receivers', []))))
    for f in (f1, f2):
        try:
            os.remove(f)
        except OSError:
            pass
    json.dump(res, open(outpath, 'w'), indent=1, default=str)
    print('OWNERSHIP_DONE', json.dumps({k: res[k] for k in ('objects_before', 'objects_after_1', 'objects_after_2', 'file_bytes_1', 'file_bytes_2', 'same_names_twice', 'same_positions_twice')}))
    print('OTHERS_CHANGED_FIRST', json.dumps(res['others_after_first_run']))


# ------------------------------------------------------------------------------------------------ scene facts after the stage (tests 18, 19, 20, 22)
def uv_report(ob):
    me = ob.data
    if me.type != 'MESH' if hasattr(me, 'type') else False:
        return None
    out = {}
    for lay in me.uv_layers:
        n = len(lay.data)
        uv = np.empty(n * 2, np.float32); lay.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        tri = uv.reshape(-1, 3, 2) if n % 3 == 0 else None
        neg = pos = 0
        if tri is not None:
            a = (tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])
            neg, pos = int((a < -1e-12).sum()), int((a > 1e-12).sum())
        out[lay.name] = dict(u_range=[round(float(uv[:, 0].min()), 3), round(float(uv[:, 0].max()), 3)], v_range=[round(float(uv[:, 1].min()), 3), round(float(uv[:, 1].max()), 3)],
                             negative_area_tris=neg, positive_area_tris=pos)
    return out


def nodes_check(mat):
    """Normal Map nodes of a material: space, uv layer exists on every object that uses it, Non-Color image of at least 1024, reaches the Principled Normal."""
    res = []
    if mat.node_tree is None:
        return res
    nt = mat.node_tree
    bsdf = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    users = [o for o in bpy.data.objects if o.type == 'MESH' and mat.name in [s.material.name for s in o.material_slots if s.material]]

    def upstream_reaches(node, target_nodes, seen=None):
        seen = seen or set()
        if node.name in seen:
            return False
        seen.add(node.name)
        for out in node.outputs:
            for l in out.links:
                if l.to_node in target_nodes and l.to_socket.name == 'Normal':
                    return True
                if l.to_node.bl_idname in ('ShaderNodeBump', 'ShaderNodeVectorMath', 'ShaderNodeGroup') and upstream_reaches(l.to_node, target_nodes, seen):
                    return True
        return False
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeNormalMap':
            img = None
            src = n.inputs['Color'].links[0].from_node if n.inputs['Color'].is_linked else None
            if src is not None and src.bl_idname == 'ShaderNodeTexImage':
                img = src.image
            res.append(dict(node=n.name, space=n.space, uv_map=n.uv_map, strength=round(n.inputs['Strength'].default_value, 3),
                            image=img.name if img else None, image_colorspace=img.colorspace_settings.name if img else None,
                            image_size=list(img.size) if img else None, reaches_principled_normal=upstream_reaches(n, bsdf),
                            uv_exists_on_all_users=all(n.uv_map in [u.name for u in o.data.uv_layers] for o in users) if users else None, users=len(users)))
    bumps = [dict(node=n.name, strength=round(n.inputs['Strength'].default_value, 3), fed_by_normal_map=bool(n.inputs['Normal'].is_linked and n.inputs['Normal'].links[0].from_node.bl_idname == 'ShaderNodeNormalMap'))
             for n in nt.nodes if n.bl_idname == 'ShaderNodeBump']
    return dict(normal_maps=res, bumps=bumps)


def mode_scene(outpath):
    import stage_pond
    rep = stage_pond.apply({})
    res = dict(stage_numbers=rep['numbers'], created=rep['created'], seconds=rep['seconds'])
    # materials changed: normal map nodes
    mats = {}
    for name in ('Pond water', 'G6 pond / silt', 'G6 pond / pebble', 'Bark', 'GARDEN bark.pine'):
        m = bpy.data.materials.get(name)
        if m:
            mats[name] = nodes_check(m)
    res['materials'] = mats
    # image statistics for the normal maps
    imgs = {}
    for f in sorted(os.listdir(os.path.join(HERE, 'maps'))):
        if f.endswith('_normal.png'):
            im = bpy.data.images.load(os.path.join(HERE, 'maps', f))
            im.colorspace_settings.name = 'Non-Color'
            w, h = im.size
            a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
            imgs[f] = dict(size=[w, h], mean_rgb=[round(float(a[..., k].mean()), 4) for k in range(3)])
            bpy.data.images.remove(im)
    res['normal_map_images'] = imgs
    # UV hygiene per object
    uvs = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o.name in ('Pond water', 'Basin water', 'Life / pond bed', 'Life / pond pebbles', 'Maple trunk', 'Pine trunk', 'Maple branch', 'Pine limb', 'G6 pond / bed stones')):
            uvs[o.name] = uv_report(o)
    res['uv'] = uvs
    # water: depth attribute, edge versus middle by construction
    pw = bpy.data.objects['Pond water']
    d = np.array([a.value for a in pw.data.attributes['depth'].data])
    res['water_depth_attr'] = dict(min=float(d.min()), max=float(d.max()), verts_clear_lt_0_1=int((d < 0.1).sum()), verts_deep_gt_0_3=int((d > 0.3).sum()))
    # ripple spots: count the ripple map's separate ring patterns (connected blobs of non-flat normal)
    img = bpy.data.images.load(os.path.join(HERE, 'maps', 'ripple_normal.png')); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    mag = np.hypot(a[..., 0] - 0.5, a[..., 1] - 0.5)
    mask = (mag > 0.004)
    lab = np.zeros(mask.shape, np.int32)
    k = 0
    for y0 in range(0, h, 8):          # a coarse flood fill on an 8-pixel grid
        pass
    from collections import deque
    small = mask[::8, ::8]
    seen = np.zeros(small.shape, bool)
    comps = 0
    for y in range(small.shape[0]):
        for x in range(small.shape[1]):
            if small[y, x] and not seen[y, x]:
                comps += 1
                q = deque([(y, x)]); seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    for dy in range(-6, 7):
                        for dx in range(-6, 7):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < small.shape[0] and 0 <= nx < small.shape[1] and small[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True; q.append((ny, nx))
    res['ripple_spots_in_map'] = comps
    import g6p_maps
    res['ripple_spots_defined'] = [(s[0], s[1], s[2], s[3], s[4]) for s in g6p_maps.RIPPLE_SPOTS]
    # counts for test 18 and 19
    cnt = lambda prefix: len([o for o in bpy.data.objects if o.name.startswith(prefix)])
    res['counts'] = dict(floating_leaves=cnt('G6 pond / floating leaf'), submerged_leaves=cnt('G6 pond / submerged leaf'), algae_rims=cnt('G6 pond / algae rim'),
                         lily_pad_faces=len(bpy.data.objects['Lily pads'].data.polygons), maple_branch_meshes=len([o for o in bpy.data.objects if o.name.startswith('Maple branch') and o.type == 'MESH']),
                         pine_limb_meshes=len([o for o in bpy.data.objects if o.name.startswith('Pine limb') and o.type == 'MESH']),
                         curves_left=[o.name for o in bpy.data.objects if o.type == 'CURVE' and o.name.startswith(('Maple', 'Pine'))],
                         maple_leaf_points=len(bpy.data.objects['Maple leaves'].data.vertices), pine_triangles=len(bpy.data.objects['Pine pads'].data.polygons))
    # which stones touch water (algae rim present)
    res['algae_rim_stones'] = sorted(o['g6p_stone'] for o in bpy.data.objects if o.name.startswith('G6 pond / algae rim'))
    # leaf colour distribution before / after (ramp position histogram)
    ml = bpy.data.objects['Maple leaves'].data
    hue = np.array([a.value for a in ml.attributes['leaf_hue'].data])
    res['maple_hue_hist_after'] = np.histogram(hue, bins=10, range=(0, 1))[0].tolist()
    res['maple_hue_mean_std_after'] = [round(float(hue.mean()), 4), round(float(hue.std()), 4)]
    old = np.load(os.path.join(HERE, 'work', 'old_maple.npz')) if os.path.exists(os.path.join(HERE, 'work', 'old_maple.npz')) else None
    if old is not None:
        res['maple_hue_hist_before'] = np.histogram(old['hue'], bins=10, range=(0, 1))[0].tolist()
        res['maple_hue_mean_std_before'] = [round(float(old['hue'].mean()), 4), round(float(old['hue'].std()), 4)]
        res['maple_leaves_before'] = int(len(old['hue']))
        res['maple_leaf_scale_mean_before_after'] = [round(float(old['scale'][:, 0].mean()), 5), None]
    sc = np.array([a.vector[:] for a in ml.attributes['leaf_scale'].data])
    res['maple_leaf_scale_mean_after'] = round(float(sc[:, 0].mean()), 5)
    json.dump(res, open(outpath, 'w'), indent=1, default=str)
    print('SCENE_TEST_DONE', outpath)


# ------------------------------------------------------------------------------------------------ the normal-map test light (tests 21)
def render_plane(png_path, uv_name, strength, tag, size, az_deg, out_png, samples=32, scale=(1, 1, 1)):
    import normal_tools as nt
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
    sc.world = bpy.data.worlds.new('W'); sc.world.color = (0, 0, 0)
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    plane = bpy.context.active_object
    cam_d = bpy.data.cameras.new('C'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 2.0
    cam = bpy.data.objects.new('C', cam_d); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, 0, 5)
    sun_d = bpy.data.lights.new('S', 'SUN'); sun_d.energy = 4.0
    sun = bpy.data.objects.new('S', sun_d); sc.collection.objects.link(sun)
    from mathutils import Vector
    el = math.radians(30.0)
    direction = Vector((-math.cos(math.radians(az_deg)) * math.cos(el), -math.sin(math.radians(az_deg)) * math.cos(el), -math.sin(el)))
    sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    m = bpy.data.materials.new('m'); m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1); bs.inputs['Roughness'].default_value = 1.0
    plane.data.materials.append(m)
    plane.data.uv_layers.active.name = uv_name
    img = bpy.data.images.load(png_path)
    img.colorspace_settings.name = 'Non-Color'
    nt.add_normal_map_nodes(m, img, uv_name, strength, scale)
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    a = bpy.data.images.load(out_png)
    px = np.array(a.pixels[:], dtype=np.float32).reshape(size, size, 4)[..., :3].mean(axis=2)[::-1]      # rows from the TOP
    return px


def blur_np(a, sigma):
    if sigma <= 0:
        return a
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a, r, mode='reflect')
    t = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))[r:-r] if False else None
    out = np.zeros_like(a)
    tmp = np.zeros((p.shape[0], a.shape[1]), np.float32)
    for i in range(2 * r + 1):
        tmp += k[i] * p[:, i:i + a.shape[1]]
    for i in range(2 * r + 1):
        out += k[i] * tmp[i:i + a.shape[0], :]
    return out


def mode_direction(outpath):
    import normal_tools as nt
    import g6p_maps as gm
    res = {}
    chk = nt.check_direction(out_dir='/tmp/_g6p_nrm', verbose=False)
    res['NORMAL_DIRECTION'] = chk['line']
    print(chk['line'])
    N = 512
    # heights (0..1 or metres): rows from the top; use the same functions the maps were made from
    sw_h, px = gm.swell_height(2048)
    rp_h, _, _ = gm.ripple_height(2048)
    pb = gm.stretch01(gm.gauss_blur(gm.load_scan('clean_pebbles_disp_1k.jpg'), 5.0))
    mb = gm.stretch01(gm.gauss_blur(gm.load_scan('trident_maple_bark_disp_1k.jpg'), 2.2))
    pn = gm.stretch01(gm.gauss_blur(gm.load_scan('pine_bark_disp_1k.jpg'), 2.6))
    cases = [('swell', 'swell_normal.png', sw_h, 0.6 * 8), ('ripple', 'ripple_normal.png', rp_h, 1.0 * 3), ('pebble', 'pebble_normal.png', pb, 0.7),
             ('maple_bark', 'maple_bark_normal.png', mb, 0.9), ('pine_bark', 'pine_bark_normal.png', pn, 0.9)]
    for name, fn, h, strength in cases:
        n_h = h.shape[0]
        f = n_h // N
        hs = h.reshape(N, f, N, f).mean(axis=(1, 3))               # block average to the render grid
        dx = (np.roll(hs, -1, axis=1) - np.roll(hs, 1, axis=1)) * 0.5      # per column, to the right (+U / +X)
        dr = (np.roll(hs, -1, axis=0) - np.roll(hs, 1, axis=0)) * 0.5      # per row, downward (-V)
        exp_x = -dx                                                          # sun from +X lights faces whose slope falls to +X: -dh/dx
        exp_y = +dr                                                          # sun from +Y (top of the picture): -dh/dy_up = +dh/drow
        r = {}
        for az, exp, tag in ((0.0, exp_x, '+X'), (90.0, exp_y, '+Y')):
            lum = render_plane(os.path.join(HERE, 'maps', fn), 'UVMap', strength, name, N, az, '/tmp/_g6p_nrm/%s_%s.png' % (name, tag.replace('+', '')))
            sg = 0 if name == 'swell' else 6            # the swell is all broad shapes: no high-pass for it
            hp = lum - (blur_np(lum, sg) if sg else lum.mean())
            ep = exp - (blur_np(exp, sg) if sg else exp.mean())
            c = float(np.corrcoef(hp.ravel(), ep.ravel())[0, 1])
            r[tag] = round(c, 3)
        r['PASS'] = bool(r['+X'] >= 0.25 and r['+Y'] >= 0.25)
        res[name] = r
        print('NORMAL_CORRELATION', name, json.dumps(r), flush=True)
    # ripple rings: for every spot, inside its ring area, the render must be brighter where the slope faces the sun (sun from +X)
    lum = render_plane(os.path.join(HERE, 'maps', 'ripple_normal.png'), 'UVMap', 3.0, 'ripple', N, 0.0, '/tmp/_g6p_nrm/ring_X.png')
    hs = rp_h.reshape(N, 2048 // N, N, 2048 // N).mean(axis=(1, 3))
    exp = -((np.roll(hs, -1, axis=1) - np.roll(hs, 1, axis=1)) * 0.5)
    x0, y0, x1, y1 = gm.POND_BBOX
    rings = []
    for (cx, cy, nr, lam, story) in gm.RIPPLE_SPOTS:
        u = (cx - x0) / (x1 - x0) * N; v = (y1 - cy) / (y1 - y0) * N
        yy, xx = np.mgrid[0:N, 0:N]
        dxm = (xx - u) / N * (x1 - x0); dym = (v - yy) / N * (y1 - y0)
        rr = np.hypot(dxm, dym)
        area = (rr > lam * 0.8) & (rr < lam * (nr + 0.5))
        hp = (lum - blur_np(lum, 6))[area]; ep = (exp - blur_np(exp, 6))[area]
        rings.append(dict(spot=story, rings=nr, spacing_cm=round(lam * 100, 1), corr_lit_side=round(float(np.corrcoef(hp, ep)[0, 1]), 3)))
    res['ripple_rings_sun_side'] = rings
    # annulus correlation per spot
    json.dump(res, open(outpath, 'w'), indent=1)
    print('DIRECTION_DONE', outpath)


# ------------------------------------------------------------------------------------------------ picture analysis (value range, detail energy, bands)
def load_rgb(path):
    im = bpy.data.images.load(path)
    im.colorspace_settings.name = 'Non-Color'
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3][::-1]
    bpy.data.images.remove(im)
    return a


def analyze(path, cam):
    a = load_rgb(path)
    H, W = a.shape[:2]
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    out = dict(path=os.path.basename(path), size=[W, H], lum_percentiles={str(p): round(float(np.percentile(lum, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)},
               mean_saturation=round(float(sat.mean()), 4), turquoise_fraction=round(float(((hue >= 160) & (hue <= 210) & (sat > 0.35)).mean()), 5),
               sat_over_070_fraction=round(float((sat > 0.70).mean()), 5))
    boxes = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
             "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}
    if cam == 'photo' and (W, H) == (2400, 1600):
        g = np.floor(lum * 255).astype(np.float32)
        bl = blur_np(g, 2.0)
        hf = np.abs(g - np.round(bl))
        out['detail_energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 3) for k, (x0, y0, x1, y1) in boxes.items()}
        x0, y0, x1, y1 = boxes['maple']
        out['maple_box_mean_saturation'] = round(float(sat[y0:y1, x0:x1].mean()), 4)
        out['maple_box_mean_rgb'] = [round(float(v), 4) for v in a[y0:y1, x0:x1].reshape(-1, 3).mean(0)]
    # water bands
    sp = os.path.join(HERE, 'work', 'water_samples.json')
    if os.path.exists(sp):
        s = np.array(json.load(open(sp))[cam])
        sx, sy = W / 2400.0, H / 1600.0
        bands = {}
        for lo, hi, name in ((0, 0.04, 'rim'), (0.04, 0.10, 'edge'), (0.10, 0.20, 'mid-edge'), (0.20, 0.30, 'slope'), (0.30, 0.5, 'middle')):
            m = (s[:, 2] >= lo) & (s[:, 2] < hi)
            if not m.any():
                continue
            L, Cc = [], []
            w_ = max(2, int(4 * sx))
            for x, y, dd, px_, py_ in s[m]:
                px_, py_ = int(px_ * sx), int(py_ * sy)
                L.append(lum[py_ - w_:py_ + w_ + 1, px_ - w_:px_ + w_ + 1].mean()); Cc.append(a[py_ - w_:py_ + w_ + 1, px_ - w_:px_ + w_ + 1].reshape(-1, 3).mean(0))
            L = np.array(L); Cc = np.array(Cc).mean(0)
            mxv, mnv = Cc.max(), Cc.min()
            bands[name] = dict(n=int(m.sum()), lum=round(float(L.mean()), 4), std=round(float(L.std()), 4), rgb=[round(float(v), 3) for v in Cc], sat=round(float((mxv - mnv) / max(mxv, 1e-4)), 3))
        out['water_bands'] = bands
    return out


def mode_analyze(outpath, pairs):
    res = {}
    for i in range(0, len(pairs), 2):
        res[os.path.basename(pairs[i])] = analyze(pairs[i], pairs[i + 1])
        print('ANALYZE', os.path.basename(pairs[i]), json.dumps(res[os.path.basename(pairs[i])]), flush=True)
    json.dump(res, open(outpath, 'w'), indent=1)


def alpha_of(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3] > 0.5
    bpy.data.images.remove(im)
    return a


def mode_masks(outpath, folder):
    """Silhouette numbers from the mask pictures in `folder`: before__m_X.png against A__m_X.png (area ratio, overlap) and the per-branch visible pixel counts (A__b_*)."""
    res = dict(silhouettes={}, branches_hero={}, branches_veranda={})
    for f in sorted(os.listdir(folder)):
        if f.startswith('before__m_') and f.endswith('.png'):
            key = f[len('before__m_'):-4]
            g = os.path.join(folder, 'A__m_' + key + '.png')
            if os.path.exists(g):
                a, b = alpha_of(os.path.join(folder, f)), alpha_of(g)
                inter = int((a & b).sum()); uni = int((a | b).sum())
                res['silhouettes'][key] = dict(area_before=round(float(a.mean()), 5), area_after=round(float(b.mean()), 5), area_ratio=round(float(b.sum() / max(1, a.sum())), 3),
                                               iou=round(inter / max(1, uni), 3), inter_over_before=round(inter / max(1, int(a.sum())), 3))
        if f.startswith('A__b_') and f.endswith('.png'):
            parts = f[len('A__b_'):-4].split('_', 1)
            cam, name = parts[0], parts[1]
            res['branches_hero' if cam == 'h' else 'branches_veranda'][name] = int(alpha_of(os.path.join(folder, f)).sum())
    for k in ('branches_hero', 'branches_veranda'):
        res[k + '_count_over_120px'] = sum(1 for n, v in res[k].items() if v >= 120 and n not in ('trunk', 'leaves'))
    json.dump(res, open(outpath, 'w'), indent=1)
    print('MASKS', json.dumps(res['silhouettes']), res['branches_hero_count_over_120px'], res['branches_veranda_count_over_120px'])


def mode_jpg(args):
    """jpg SRC.png DST.jpg WIDTH QUALITY : make a small JPEG preview (kept under 400 KB by lowering quality when needed)."""
    src, dst, width, quality = args[0], args[1], int(args[2]), int(args[3])
    im = bpy.data.images.load(src)
    w, h = im.size
    im.colorspace_settings.name = 'sRGB'
    if width < w:
        im.scale(width, int(round(h * width / w)))
    sc = bpy.context.scene
    ims = sc.render.image_settings
    ims.file_format = 'JPEG'; ims.quality = quality; ims.color_mode = 'RGB'
    ims.color_management = 'OVERRIDE'
    ims.view_settings.view_transform = 'Standard'
    ims.display_settings.display_device = 'sRGB'
    im.save_render(filepath=dst, scene=sc)
    print('JPG', dst, os.path.getsize(dst))


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    mode = argv[0]
    if mode == 'ownership':
        mode_ownership(argv[1])
    elif mode == 'scene':
        mode_scene(argv[1])
    elif mode == 'direction':
        mode_direction(argv[1])
    elif mode == 'analyze':
        mode_analyze(argv[1], argv[2:])
    elif mode == 'jpg':
        mode_jpg(argv[1:])
    elif mode == 'masks':
        mode_masks(argv[1], argv[2])
