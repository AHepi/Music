import bpy, json, sys
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/'
def snap():
    out = {}
    for c in ('G4 rim receivers', 'G4 roof receivers'):
        col = bpy.data.collections.get(c)
        out[c] = sorted(o.name for o in col.all_objects) if col else None
    ll = {}
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT':
            try:
                ll[ob.name] = {'recv': ob.light_linking.receiver_collection.name if ob.light_linking.receiver_collection else None, 'type': ob.light_linking.receiver_type if hasattr(ob.light_linking, 'receiver_type') else None, 'energy': round(ob.data.energy, 2)}
            except Exception as e: ll[ob.name] = str(e)
    out['lights'] = ll
    return out
bpy.ops.wm.open_mainfile(filepath=G + 'direction/start/garden_real_fixed.blend'); A = snap()
bpy.ops.wm.open_mainfile(filepath=G + 'final/garden_character.blend'); B = snap()
R = {'lights_same': A['lights'] == B['lights'], 'lights': B['lights']}
for c in ('G4 rim receivers', 'G4 roof receivers'):
    R[c] = {'before': len(A[c]), 'after': len(B[c]), 'added': sorted(set(B[c]) - set(A[c])), 'removed': sorted(set(A[c]) - set(B[c]))}
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('RIM', {c: (R[c]['before'], R[c]['after'], len(R[c]['removed'])) for c in ('G4 rim receivers', 'G4 roof receivers')}, R['lights_same'])
