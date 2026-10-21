# What this does: runs the skill's delivery gate (bx_audit.deliverable) on the street copy with choices the command line of the skill does not offer:
#   which objects to leave out (by name start) and the three tolerances (metres). Writes a JSON report. Changes and saves nothing in the .blend.
# Run: blender -b --disable-autoexec --factory-startup STREET.blend -P run_gate.py -- OUT.json PROFILE EXCLUDE_PREFIXES(comma, or -) EPS TOL GAP   (EPS TOL GAP: a number in metres, or - for the skill's own default)
import sys, json, time
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bx_audit
a = sys.argv[sys.argv.index('--') + 1:]
out, profile = a[0], a[1]
excl = [] if a[2] == '-' else a[2].split(',')
num = lambda s: None if s == '-' else float(s)
eps, tol, gap = num(a[3]), num(a[4]), num(a[5])
objs = [o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get() and not any(o.name.startswith(p) for p in excl)]
t = time.time()
r = bx_audit.deliverable(objs, profile=profile, eps=eps, tol=tol, gap=gap)
r['seconds'] = round(time.time() - t, 1); r['objects_checked'] = len(objs); r['excluded_prefixes'] = excl
json.dump(r, open(out, 'w'), indent=1)
print('GATE', profile, 'pass', r['pass'], 'errors', len(r['errors']), 'warnings', len(r['warnings']), 'seconds', r['seconds'], 'eps/tol/gap', r['eps'], r['tol'], r['gap'])
