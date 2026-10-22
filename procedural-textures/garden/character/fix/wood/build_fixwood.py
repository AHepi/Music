# build_character.py - the INTEGRATION step of the garden character round (22 October).
# Plain words: opens the starting scene (garden_real_fixed.blend, never saved over), runs the four builders' stages one after another
# (wood, roof, ground, pond unless the job file says another order), and after EVERY stage compares a fingerprint of the whole scene with the
# one before it. That tells, in a report, whether each stage touched only what it owns (objects, materials, node groups, collections,
# light links, lights, cameras, world, compositor, render settings), whether any name the weathering kit and the earlier stages rely on has
# vanished, whether any new name ended in .001 (a duplicate), and how long each stage took. At the end it adds the extra close-up cameras,
# packs every picture into the file, saves garden_character.blend (on the store only), re-opens it and checks the normal maps again
# (test 20 on the combined scene) and that the saved file draws the same number of triangles.
# Run inside Blender, headless:  blender -b --disable-autoexec START.blend -P build_character.py -- JOB.json
# JOB.json: {"order": ["wood","roof","ground","pond"], "save": "/abs/garden_character.blend" | null, "report": "/abs/report.json", "cameras": true}
import bpy
import sys
import os
import json
import time
import re
import hashlib
import traceback
import importlib
import numpy as np

sys.dont_write_bytecode = True
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden'
CH = G + '/character'
for n in ('wood', 'roof', 'ground', 'pond', 'final'):
    d = CH + '/' + ('fix/wood' if n == 'wood' else n)       # FIX ROUND (wood): the fixed copy replaces the builder's original
    if d in sys.path:
        sys.path.remove(d)
    sys.path.append(d)

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
T0 = time.time()


def say(*a):
    print('[build]', *a, flush=True)


# ---------------------------------------------------------------------------------------------------------- ownership (direction doc, section 9)
def rx(*pats):
    return re.compile('|'.join('(?:%s)' % p for p in pats))


OWN_OBJ = {
    'wood': rx(r'^Astra / varied planks(\.\d{3})?$', r'^Astra / Planked run', r'^Bridge pier \d$', r'^Bridge stringers$', r'^Veranda step(, lower)?$',
               r'^Hall posts$', r'^Hall beams$', r'^Eave soffit$', r'^Roof carrying frame$', r'^Gravel timber edge$', r'^Shoji bars$', r'^Stone plinth$'),
    'roof': rx(r'^Hall roof$', r'^CT / Ceramic pan prototype$', r'^Hall plaster$', r'^Back wall, (left|right)( cap)?$', r'^Right wall behind hall( cap)?$',
               r'^Lantern (base|post|gallery|firebox|cap|finial)$', r'^Water basin$', r'^Basin (front|candle|bucket) stone$', r'^Basin drain pebbles$',
               r'^Rock \d$', r'^Pond edge stone \d+$', r'^Shore stones$'),
    'ground': rx(r'^Astra / Courtyard receiving ground$', r'^Courtyard ground source$', r'^Astra / moss grouped bodies$', r'^Astra / pebbles grouped bodies$',
                 r'^Life / moss at feet and damp edges$', r'^Life / pebble fringe$', r'^Life / tufts$', r'^Life / (moss|pebble|tuft) sources \d$',
                 r'^Life / shrubs$', r'^Fix / far hedge$', r'^Fallen leaves$', r'^Raked gravel court$', r'^Gravel kerb$', r'^Gravel rock \d$',
                 r'^Stepping stone \d$'),
    'final': rx(r'^$'),
    'pond': rx(r'^Pond water$', r'^Basin water$', r'^Life / pond bed$', r'^Life / pond pebbles$', r'^Lily pads$', r'^Lotus blossoms$',
               r'^Life / iris clumps$', r'^Life / lily stems$', r'^Maple (trunk|branch(\.\d{3})?|inner mass|leaf source \d|leaves)$',
               r'^Pine (trunk|limb(\.\d{3})?|pads)$', r'^Bamboo (stalks|leaves|fence)$', r'^Basin bamboo spout$', r'^Basin ladle$'),
}
STONE = r'^CT / Stone painterly surface'
OWN_MAT = {
    'wood': rx(r'^Astra / planks tone \d(\.\d{3})?$', r'^Dark timber$', r'^Beam timber$', r'^GARDEN timber\.post$', r'^Plinth stone$',
               STONE + r'\.(008|009|039|040|041|042)$'),
    'roof': rx(r'^CT / Ceramic painterly surface$', r'^CT / Ceramic ridge host-local surface$', r'^CT / Timber painterly surface$', r'^Plaster wall$',
               r'^GARDEN wall\.garden$', r'^Wall cap tile$', r'^GARDEN stone\.lantern$', STONE + r'\.(01\d|02\d|033|034|035|036|037|038)$'),
    'ground': rx(r'^Moss and earth$', r'^Raked gravel$', r'^Astra / moss tone \d$', r'^Astra / pebbles tone \d$', r'^Life / tuft$', r'^Life / shrub$',
                 r'^Fallen leaves$', STONE + r'$', STONE + r'\.(00[1-7]|030|031|032)$'),
    'final': rx(r'^G6 roof / '),
    'pond': rx(r'^Pond water$', r'^Life / pond bed$', r'^Life / iris blade$', r'^Life / lily stem$', r'^Lily pad$', r'^Lotus blossom$', r'^Maple leaves$',
               r'^Maple inner mass$', r'^Bark$', r'^GARDEN bark\.pine$', r'^Pine needles$', r'^Bamboo stalk$', r'^Bamboo leaf colour$', r'^GARDEN ground\.earth$'),
}
OWN_COLL_EXTRA = {'wood': rx(r'^Astra / Planked run'), 'roof': rx(r'^G4 (rim|roof) receivers$'), 'ground': rx(r'^$'), 'pond': rx(r'^G4 rim receivers$'), 'final': rx(r'^$')}


# ---------------------------------------------------------------------------------------------------------- fingerprints
SKIP = {'rna_type', 'location', 'width', 'height', 'dimensions', 'select', 'inputs', 'outputs', 'internal_links', 'parent', 'is_active_output',
        'bl_idname', 'bl_label', 'bl_description', 'bl_icon', 'bl_static_type', 'bl_width_default', 'bl_width_min', 'bl_width_max', 'bl_height_default',
        'bl_height_min', 'bl_height_max', 'show_options', 'show_preview', 'show_texture', 'is_evaluated', 'session_uid', 'users', 'use_fake_user',
        'is_runtime_data', 'tag', 'is_missing', 'original', 'name_full', 'id_type', 'preview', 'library', 'override_library', 'asset_data'}


def vsig(v):
    try:
        if isinstance(v, float):
            return round(v, 4)
        if isinstance(v, (int, bool, str)) or v is None:
            return v
        if isinstance(v, bpy.types.ID):
            return 'ID:' + v.name
        if hasattr(v, '__len__'):
            return tuple(vsig(x) for x in v)
        return str(v)
    except Exception:
        return '?'


def psig(r, skip=()):
    out = []
    for p in r.bl_rna.properties:
        pid = p.identifier
        if pid in SKIP or pid in skip:
            continue
        if p.type in ('BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'):
            try:
                v = getattr(r, pid)
            except Exception:
                continue
            if p.type == 'ENUM' and p.is_enum_flag:
                v = sorted(v)
            out.append((pid, vsig(v)))
        elif p.type == 'POINTER':
            try:
                v = getattr(r, pid)
            except Exception:
                continue
            if v is None:
                out.append((pid, None))
            elif isinstance(v, bpy.types.ID):
                out.append((pid, 'ID:' + v.name))
    return out


def idprops(idb):
    out = []
    try:
        for k in sorted(idb.keys()):
            v = idb[k]
            if isinstance(v, (int, float, str, bool)):
                out.append((k, vsig(v)))
            elif hasattr(v, 'to_dict'):
                out.append((k, str(v.to_dict())[:200]))
            elif hasattr(v, '__len__'):
                out.append((k, vsig(list(v))))
    except Exception:
        pass
    return out


def hsh(x):
    return hashlib.md5(repr(x).encode()).hexdigest()


def node_sig(n):
    s = [n.bl_idname, n.name, psig(n), idprops(n)]
    ins = []
    for i in n.inputs:
        if i.is_linked:
            ins.append((i.identifier, 'L'))
        elif hasattr(i, 'default_value'):
            ins.append((i.identifier, vsig(i.default_value)))
    s.append(ins)
    if hasattr(n, 'color_ramp') and n.color_ramp is not None:
        s.append([(round(e.position, 4), vsig(e.color)) for e in n.color_ramp.elements])
    if hasattr(n, 'image') and n.image is not None:
        s.append(n.image.name)
    return s


def tree_sig(nt):
    if nt is None:
        return None
    nodes = sorted(nt.nodes, key=lambda n: n.name)
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links)
    return hsh(([node_sig(n) for n in nodes], links, len(nt.nodes), len(nt.links)))


def mesh_sig(me):
    n = len(me.vertices)
    a = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', a)
    h = hashlib.md5(np.round(a, 4).tobytes())
    uvs = []
    try:
        for uv in me.uv_layers:
            uvs.append(uv.name)
            try:
                b = np.empty(len(uv.data) * 2, np.float32)
                uv.data.foreach_get('uv', b)
                h.update(np.round(b, 4).tobytes())
            except Exception:
                pass
    except Exception:
        pass
    h.update(repr((len(me.polygons), len(me.edges), uvs, [m.name if m else None for m in me.materials])).encode())
    return h.hexdigest()


def obj_sig(o):
    d = [o.type, o.data.name if o.data is not None else None, tuple(round(x, 4) for r in o.matrix_world for x in r),
         o.parent.name if o.parent else None, tuple(sorted(c.name for c in o.users_collection)),
         psig(o), o.hide_get() if o.name in bpy.context.view_layer.objects else None,
         [(s.material.name if s.material else None, s.link) for s in o.material_slots], idprops(o), o.lightgroup]
    mods = []
    for m in o.modifiers:
        inp = []
        try:
            for k in m.keys():
                inp.append((k, vsig(m[k])))
        except Exception:
            pass
        mods.append((m.name, m.type, psig(m), inp))
    d.append(mods)
    if o.type == 'MESH':
        d.append(mesh_sig(o.data))
    elif o.type in ('CURVE', 'SURFACE'):
        pts = []
        for sp in o.data.splines:
            pts.extend([tuple(round(c, 4) for c in p.co) for p in sp.bezier_points] + [tuple(round(c, 4) for c in p.co) for p in sp.points])
        d.append(hsh(pts))
    elif o.type in ('LIGHT', 'CAMERA'):
        d.append(psig(o.data))
    try:
        ll = o.light_linking
        d.append((ll.receiver_collection.name if ll.receiver_collection else None, ll.blocker_collection.name if ll.blocker_collection else None))
    except Exception:
        pass
    return hsh(d)


def frozen_sig():
    sc = bpy.context.scene
    d = {}
    d['render'] = psig(sc.render)
    d['cycles'] = psig(sc.cycles)
    d['view'] = psig(sc.view_settings)
    d['seq'] = psig(sc.display_settings)
    d['vl'] = [(vl.name, [g.name for g in vl.lightgroups], psig(vl)) for vl in sc.view_layers]
    d['world'] = (sc.world.name, tree_sig(sc.world.node_tree), psig(sc.world)) if sc.world else None
    comp = getattr(sc, 'compositing_node_group', None) or getattr(sc, 'node_tree', None)
    d['comp'] = tree_sig(comp) if comp is not None else None
    d['camera'] = sc.camera.name if sc.camera else None
    return hsh(d)


def snapshot():
    bpy.context.view_layer.update()      # new objects keep a stale matrix_world until the view layer is updated
    s = {'objects': {}, 'materials': {}, 'groups': {}, 'collections': {}, 'images': sorted(i.name for i in bpy.data.images),
         'meshes': sorted(m.name for m in bpy.data.meshes), 'cameras': sorted(c.name for c in bpy.data.cameras)}
    for o in bpy.data.objects:
        s['objects'][o.name] = obj_sig(o)
    for m in bpy.data.materials:
        s['materials'][m.name] = hsh((tree_sig(m.node_tree), psig(m), idprops(m)))
    for g in bpy.data.node_groups:
        s['groups'][g.name] = hsh((tree_sig(g), idprops(g)))
    for c in bpy.data.collections:
        s['collections'][c.name] = hsh((sorted(o.name for o in c.objects), sorted(ch.name for ch in c.children), psig(c)))
    s['coll_members'] = {c.name: sorted(o.name for o in c.objects) for c in bpy.data.collections}
    s['frozen'] = frozen_sig()
    s['lightlinks'] = {o.name: (o.light_linking.receiver_collection.name if o.light_linking.receiver_collection else None,
                               o.light_linking.blocker_collection.name if o.light_linking.blocker_collection else None)
                       for o in bpy.data.objects if o.type == 'LIGHT'}
    s['wk_nodes'] = sum(1 for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.get('wk') is not None)
    s['wk_scale_nodes'] = sum(1 for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.get('wk') == 'scale')
    s['counts'] = dict(objects=len(bpy.data.objects), materials=len(bpy.data.materials), groups=len(bpy.data.node_groups), meshes=len(bpy.data.meshes),
                       images=len(bpy.data.images), collections=len(bpy.data.collections))
    return s


def dif(a, b):
    return ([k for k in b if k not in a], [k for k in a if k not in b], [k for k in a if k in b and a[k] != b[k]])


def count_tris():
    dg = bpy.context.evaluated_depsgraph_get()
    cache = {}
    total = inst_n = 0
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type != 'MESH' or ob.hide_render:
            continue
        me = ob.data
        key = (me.name, len(me.polygons))
        if key not in cache:
            cache[key] = sum(max(len(p.vertices) - 2, 0) for p in me.polygons) if len(me.polygons) < 200000 else len(me.loop_triangles)
        total += cache[key]
        inst_n += 1
    return total, inst_n


# ---------------------------------------------------------------------------------------------------------- stages
STAGES = {'wood': 'stage_wood', 'roof': 'stage_roof', 'ground': 'stage_ground', 'pond': 'stage_pond', 'final': 'stage_final'}
START = bpy.data.filepath
report = {'start_scene': START, 'order': job['order'], 'blender': bpy.app.version_string, 'stages': {}, 'warnings': []}
base = snapshot()
report['start_counts'] = base['counts']
report['start_tris'] = count_tris()
say('start scene', base['counts'], 'tris/instances', report['start_tris'], '%.1fs' % (time.time() - T0))
prev = base
for name in job['order']:
    t = time.time()
    rec = {'violations': [], 'warnings': []}
    try:
        mod = importlib.import_module(STAGES[name])
        importlib.reload(mod)
        rep = mod.apply(dict(job.get('options', {}).get(name, {})))
        rec['stage_returned'] = 'dict with %d keys' % len(rep) if isinstance(rep, dict) else str(type(rep))
        if isinstance(rep, dict):
            for k in ('created', 'changed', 'deleted'):
                if k in rep:
                    try:
                        rec['stage_' + k] = len(rep[k])
                    except Exception:
                        pass
    except Exception:
        rec['error'] = traceback.format_exc()[-1800:]
        say('STAGE ERROR', name, rec['error'])
    rec['seconds'] = round(time.time() - t, 1)
    cur = snapshot()
    ao, ro, co = dif(prev['objects'], cur['objects'])
    am, rm, cm = dif(prev['materials'], cur['materials'])
    ag, rg, cg = dif(prev['groups'], cur['groups'])
    ac, rc, cc = dif(prev['collections'], cur['collections'])
    rec['objects'] = dict(added=len(ao), removed=ro, changed=len(co))
    rec['materials'] = dict(added=len(am), removed=rm, changed=len(cm))
    rec['groups'] = dict(added=ag, removed=rg, changed=cg)
    rec['changed_objects'] = sorted(co)
    rec['changed_materials'] = sorted(cm)
    rec['added_objects'] = sorted(ao)
    rec['added_materials'] = sorted(am)
    own_o, own_m = OWN_OBJ[name], OWN_MAT[name]
    v = rec['violations']
    for n in ro:
        v.append(['object removed', n])
    for n in co:
        if not own_o.match(n):
            v.append(['foreign object changed', n])
    for n in ao:
        ob = bpy.data.objects[n]
        if ob.get('garden_owner') != name:
            v.append(['new object not labelled garden_owner=%s' % name, n, ob.get('garden_owner')])
        if not ob.get('garden_role'):
            rec['warnings'].append(['new object without garden_role', n])
        if not any(c.name == 'G6 ' + name for c in ob.users_collection):
            rec['warnings'].append(['new object not in collection G6 %s' % name, n, [c.name for c in ob.users_collection]])
    for n in rm:
        v.append(['material removed', n])
    for n in cm:
        if not own_m.match(n):
            v.append(['foreign material changed', n])
    for n in am:
        if not n.startswith('G6 %s / ' % name):
            rec['warnings'].append(['new material not named G6 %s / ...' % name, n])
    for n in rg:
        v.append(['node group removed', n])
    for n in cg:
        v.append(['existing node group changed (must be copied instead)', n])
    for n in ag:
        if not n.startswith('G6 ') and not n.startswith('G6') and ('G6' not in n):
            rec['warnings'].append(['new node group not named G6 ...', n])
    for n in rc:
        v.append(['collection removed', n])
    for n in cc:
        added_members = [m for m in cur['coll_members'][n] if m not in prev['coll_members'].get(n, [])]
        removed_members = [m for m in prev['coll_members'].get(n, []) if m not in cur['coll_members'][n]]
        if removed_members:
            rec['warnings'].append(['collection lost members', n, removed_members[:6]])
        if OWN_COLL_EXTRA[name].match(n) or n == 'G6 ' + name:
            continue
        if all((bpy.data.objects[m].get('garden_owner') == name) for m in added_members if m in bpy.data.objects) and not removed_members:
            continue
        v.append(['foreign collection changed', n, added_members[:6]])
    for n in ac:
        if n != 'G6 ' + name:
            rec['warnings'].append(['new collection', n])
    if cur['frozen'] != prev['frozen']:
        v.append(['render settings / world / compositor / view layer changed', ''])
    if cur['lightlinks'] != prev['lightlinks']:
        v.append(['light linking changed', ''])
    if cur['wk_nodes'] < prev['wk_nodes']:
        v.append(['weathering kit nodes lost', '%d -> %d' % (prev['wk_nodes'], cur['wk_nodes'])])
    rec['wk_nodes'] = (prev['wk_nodes'], cur['wk_nodes'])
    rec['counts'] = cur['counts']
    report['stages'][name] = rec
    say(name, 'done in', rec['seconds'], 's', 'objects +%d ~%d' % (len(ao), len(co)), 'materials +%d ~%d' % (len(am), len(cm)), 'violations', len(v),
        'error' if 'error' in rec else '')
    prev = cur

# ---------------------------------------------------------------------------------------------------------- whole-scene checks
final = prev
ao, ro, co = dif(base['objects'], final['objects'])
am, rm, cm = dif(base['materials'], final['materials'])
ag, rg, cg = dif(base['groups'], final['groups'])
ac, rc, cc = dif(base['collections'], final['collections'])
glob = {}
glob['names_that_vanished'] = dict(objects=ro, materials=rm, node_groups=rg, collections=rc, images=[i for i in base['images'] if i not in final['images']])
suf = re.compile(r'\.\d{3}$')


def autodup(names, existing):
    """names ending in .001 whose stem also exists = what Blender adds when two things get the same name (a real duplicate)"""
    return [n for n in names if suf.search(n) and suf.sub('', n) in existing]


glob['new_names_ending_in_dot_number'] = dict(
    objects=[n for n in ao if suf.search(n)], materials=[n for n in am if suf.search(n)], node_groups=[n for n in ag if suf.search(n)],
    collections=[n for n in ac if suf.search(n)], meshes=[n for n in final['meshes'] if n not in base['meshes'] and suf.search(n)],
    images=[n for n in final['images'] if n not in base['images'] and suf.search(n)])
glob['likely_blender_auto_duplicates'] = dict(
    objects=autodup(ao, set(final['objects'])), materials=autodup(am, set(final['materials'])), node_groups=autodup(ag, set(final['groups'])),
    collections=autodup(ac, set(final['collections'])), meshes=autodup([n for n in final['meshes'] if n not in base['meshes']], set(final['meshes'])),
    images=autodup([n for n in final['images'] if n not in base['images']], set(final['images'])))
glob['new_objects_by_owner'] = {}
for n in ao:
    glob['new_objects_by_owner'].setdefault(str(bpy.data.objects[n].get('garden_owner')), []).append(n)
glob['new_objects_by_owner'] = {k: len(v) for k, v in glob['new_objects_by_owner'].items()}
glob['objects_changed_by_two_stages'] = []
seen = {}
for st, rec in report['stages'].items():
    for n in rec['changed_objects']:
        if n in seen:
            glob['objects_changed_by_two_stages'].append([n, seen[n], st])
        seen[n] = st
glob['materials_changed_by_two_stages'] = []
seenm = {}
for st, rec in report['stages'].items():
    for n in rec['changed_materials']:
        if n in seenm:
            glob['materials_changed_by_two_stages'].append([n, seenm[n], st])
        seenm[n] = st
glob['frozen_unchanged_all_stages'] = (final['frozen'] == base['frozen'])
glob['lightlinks_unchanged'] = (final['lightlinks'] == base['lightlinks'])
glob['wk_nodes'] = (base['wk_nodes'], final['wk_nodes'])
glob['wk_scale_nodes_dot_angle'] = (base['wk_scale_nodes'], final['wk_scale_nodes'])
glob['G4_rim_receivers_added'] = [m for m in final['coll_members'].get('G4 rim receivers', []) if m not in base['coll_members'].get('G4 rim receivers', [])]
glob['G4_roof_receivers_added'] = [m for m in final['coll_members'].get('G4 roof receivers', []) if m not in base['coll_members'].get('G4 roof receivers', [])]
glob['counts_start'] = base['counts']
glob['counts_end'] = final['counts']
report['global'] = glob

# extra close-up cameras (owner: the integration step)
CAMS = job.get('extra_cameras') or {}
if CAMS:
    from mathutils import Vector
    coll = bpy.data.collections.get('G6 final')
    if coll is None:
        coll = bpy.data.collections.new('G6 final')
        bpy.context.scene.collection.children.link(coll)
    coll['garden_owner'] = 'final'
    for nm, (loc, tgt, lens) in CAMS.items():
        cd = bpy.data.cameras.new('G6 final cam ' + nm)
        cd.lens = lens
        cd.clip_start = 0.05
        co = bpy.data.objects.new('G6 final cam ' + nm, cd)
        co['garden_owner'] = 'final'
        co['garden_role'] = 'camera'
        co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(co)
    say('extra cameras', list(CAMS))

report['tris_after_stages'] = count_tris()
say('after stages: tris/instances', report['tris_after_stages'], '%.1fs' % (time.time() - T0))

# ---------------------------------------------------------------------------------------------------------- pack and save
if job.get('save'):
    packed = []
    for im in list(bpy.data.images):
        if im.type in ('RENDER_RESULT', 'COMPOSITING') or im.name in ('Render Result', 'Viewer Node'):
            continue
        if im.packed_file is None and im.users > 0 and (im.source in ('FILE', 'GENERATED')):
            try:
                if im.source == 'FILE' and not os.path.exists(bpy.path.abspath(im.filepath)) and not im.is_dirty:
                    report['warnings'].append(['image file missing, not packed', im.name, im.filepath])
                    continue
                im.pack()
                packed.append(im.name)
            except Exception as e:
                report['warnings'].append(['could not pack image', im.name, str(e)[:120]])
    report['packed_images'] = len(packed)
    bpy.context.preferences.filepaths.save_version = 0
    os.makedirs(os.path.dirname(job['save']), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=job['save'], compress=True)
    report['saved'] = dict(path=job['save'], bytes=os.path.getsize(job['save']))
    say('saved', report['saved'], '%.1fs' % (time.time() - T0))
    # re-open and check test 20 (normal maps) and triangle count on the combined scene
    bpy.ops.wm.open_mainfile(filepath=job['save'])
    t20 = {'materials': {}, 'violations': [], 'images': {}}
    users = {}
    for o in bpy.data.objects:
        for s in o.material_slots:
            if s.material:
                users.setdefault(s.material.name, []).append(o)
    img_stats = {}

    def image_stat(im):
        if im.name in img_stats:
            return img_stats[im.name]
        w, h = im.size
        st = {'size': [w, h], 'colorspace': im.colorspace_settings.name, 'packed': im.packed_file is not None}
        try:
            a = np.empty(w * h * 4, np.float32)
            im.pixels.foreach_get(a)
            a = a.reshape(-1, 4)[::7]
            st['mean_rgb'] = [round(float(a[:, i].mean()), 3) for i in range(3)]
        except Exception as e:
            st['mean_rgb'] = None
        img_stats[im.name] = st
        return st

    for m in bpy.data.materials:
        if m.node_tree is None:
            continue
        nms = [n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeNormalMap']
        if not nms:
            continue
        entry = {'normal_map_nodes': len(nms), 'users': len(users.get(m.name, [])), 'images': [], 'strength': []}
        for nm in nms:
            entry['strength'].append(round(nm.inputs['Strength'].default_value, 3))
            if nm.space != 'TANGENT':
                t20['violations'].append([m.name, 'space not tangent', nm.space])
            lk = [l for l in m.node_tree.links if l.to_node == nm and l.to_socket.identifier == 'Color']
            src = lk[0].from_node if lk else None
            if src is None or src.bl_idname != 'ShaderNodeTexImage' or src.image is None:
                t20['violations'].append([m.name, 'normal map colour not from an image texture', nm.name])
                continue
            st = image_stat(src.image)
            entry['images'].append(src.image.name)
            if st['colorspace'] != 'Non-Color':
                t20['violations'].append([m.name, 'image not Non-Color', src.image.name, st['colorspace']])
            if max(st['size']) < 1024:
                t20['violations'].append([m.name, 'image smaller than 1024', src.image.name, st['size']])
            mr = st.get('mean_rgb')
            if mr is None or mr[2] < 0.85 or abs(mr[0] - 0.5) > 0.03 or abs(mr[1] - 0.5) > 0.03:
                t20['violations'].append([m.name, 'image colour means off', src.image.name, mr])
            if nm.uv_map:
                bad = [o.name for o in users.get(m.name, []) if o.type == 'MESH' and nm.uv_map not in [u.name for u in o.data.uv_layers]]
                if bad:
                    t20['violations'].append([m.name, 'uv map %s missing on' % nm.uv_map, bad[:5]])
            # does the Normal output reach a Principled BSDF Normal input?
            reach, todo, seen_nodes = False, [nm], set()
            while todo and not reach:
                cur_n = todo.pop()
                if cur_n.name in seen_nodes:
                    continue
                seen_nodes.add(cur_n.name)
                for l in m.node_tree.links:
                    if l.from_node == cur_n:
                        if l.to_node.bl_idname == 'ShaderNodeBsdfPrincipled' and l.to_socket.identifier == 'Normal':
                            reach = True
                            break
                        todo.append(l.to_node)
            if not reach:
                t20['violations'].append([m.name, 'normal map does not reach a Principled BSDF', nm.name])
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeBump' and n.inputs['Strength'].default_value > 0.3001 and not n.inputs['Normal'].is_linked and not n.inputs['Strength'].is_linked:
                t20['violations'].append([m.name, 'old Bump above 0.3 and not fed by the normal map', n.name, round(n.inputs['Strength'].default_value, 3)])
        t20['materials'][m.name] = entry
    t20['images'] = img_stats
    report['test20_combined'] = {'normal_map_materials': len(t20['materials']), 'violations': t20['violations'], 'detail': t20['materials'], 'images': t20['images']}
    report['reopen_counts'] = dict(objects=len(bpy.data.objects), materials=len(bpy.data.materials), images=len(bpy.data.images))
    report['tris_after_reopen'] = count_tris()
    say('reopened: tris/instances', report['tris_after_reopen'], 'test 20 violations', len(t20['violations']))

report['seconds_total'] = round(time.time() - T0, 1)
os.makedirs(os.path.dirname(job['report']), exist_ok=True)
json.dump(report, open(job['report'], 'w'), indent=1, default=str)
tot_v = sum(len(r['violations']) for r in report['stages'].values())
say('BUILD_DONE', json.dumps({'seconds': report['seconds_total'], 'violations': tot_v, 'errors': [k for k, r in report['stages'].items() if 'error' in r]}))
