# What this does: tests the skill's own fix for "closed parts with normals pointing inward" (bmesh.ops.recalc_face_normals) on the four flagged objects, IN MEMORY ONLY (nothing is saved),
# then runs the delivery gate again (render profile, 1 mm) and prints how many inside-out and total errors remain, before and after.
import sys, json
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bmesh, bx_audit
names = [o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get() and not o.name.startswith(('sky_dome', 'moorland_hills'))]
def gate():
    r = bx_audit.deliverable(names, profile='render', eps=0.001, tol=0.05, gap=0.5)
    inward = [e for e in r['errors'] if 'pointing inward' in e]
    return len(r['errors']), len(inward), inward
b = gate(); print('BEFORE errors', b[0], 'inside-out messages', b[1])
for n in ('headframe_lattice', 'winding_wheel_left', 'winding_wheel_right', 'engine_house_trim'):
    o = bpy.data.objects[n]
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free(); o.data.update()
a = gate(); print('AFTER  errors', a[0], 'inside-out messages', a[1], a[2])
