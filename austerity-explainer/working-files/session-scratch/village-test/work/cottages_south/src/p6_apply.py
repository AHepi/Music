

# ------------------------------------------------------------------ the stage
DEFAULTS = dict(seed=31, thatch_lump=1.3, thatch_roll=1.5, sag=1.0, chip=1.5, cob_lump=1.2, daub_tone=0.15, daub_value=1.08, thatch_tone=0.6, cob_tone=0.4, lean=1.0, daub_hex='#9C4F36',
                thatch_hex='#B8985A', cob_hex='#B9A683', shingle_hex='#A9A8A2', shingle_mix=1.2, cottages='CD')
ROUGHNESS = {'timber.beam': (0.72, 0.95), 'timber.post': (0.72, 0.95), 'timber.door': (0.7, 0.92), 'timber.shutter': (0.7, 0.92), 'timber.generic': (0.75, 0.95), 'stone.footing': (0.8, 0.97),
             'stone.step': (0.7, 0.92), 'floor.earth': (0.9, 1.0), 'iron.fitting': (0.45, 0.75), 'wall.timber_frame': (0.85, 0.98), 'wall.cob': (0.88, 1.0), 'roof.thatch': (0.9, 1.0),
             'roof.shingle': (0.7, 0.92)}


def apply(options=None):
    """Builds cottage C and cottage D on the frozen ground. Safe to run twice (it forgets what an earlier run made first). Returns a dict of facts."""
    o = dict(DEFAULTS)
    o.update(options or {})
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    parts = Parts()
    facts = {}
    if 'C' in o['cottages']:
        facts['C'] = build_C(parts, o)
    if 'D' in o['cottages'] and 'build_D' in globals():
        facts['D'] = build_D(parts, o)
    mats = {}
    made, tris = 0, 0
    for key in parts.order:
        d = parts.d[key]
        if d['acc'].empty():
            continue
        mesh = d['acc'].make(d['name'])
        role = d['role']
        if role not in mats:
            lo, hi = ROUGHNESS.get(role, (0.75, 0.95))
            mats[role] = make_material('Cottage S ' + role, lo, hi, displace=0.05 if role == 'roof.thatch' else None)
        mesh.materials.append(mats[role])
        obj = pk.new_part_object(OWNER, role, d['name'], mesh)
        if d['seat'] is not None and d['seat'] is not False:
            pk.seat_on_ground(obj, sink=float(d['seat']))
        made += 1
        tris += sum(len(p.vertices) - 2 for p in mesh.polygons)
    bpy.context.view_layer.update()
    facts['objects'] = made
    facts['triangles'] = tris
    print(f'cottages_south: {made} objects made, {tris} triangles, 0 changed, 0 deleted outside the part')
    return facts
