"""Negative test: a 'lazy' scene. Takes the plain built scene (no materials at all) and does ONLY what the audit's four FAIL lines asked for:
bevel modifiers on the plain boxes, then (outside this script) the damage and roads verbs. No surfaces, no wear, no plants."""
import sys, bpy
out = sys.argv[sys.argv.index('--') + 1]
for o in bpy.data.objects:
    if o.type == 'MESH' and not any(m.type == 'BEVEL' for m in o.modifiers) and (o.get('place_role') or '').split('.')[0] in ('wall','timber','stone','floor','iron','prop'):
        m = o.modifiers.new('MyBevel', 'BEVEL'); m.width = 0.01
bpy.ops.wm.save_as_mainfile(filepath=out)
