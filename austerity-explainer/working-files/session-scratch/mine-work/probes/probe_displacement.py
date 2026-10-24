# What this does: asks Blender 5.2.2 which switches exist for true surface displacement (adaptive subdivision, material displacement method).
import bpy
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
names = [p for p in dir(cy) if not p.startswith('_')]
print('cycles scene settings with these words:', [p for p in names if any(w in p for w in ('dic', 'adaptive', 'subdiv', 'feature', 'device', 'denois'))])
try: print('feature_set =', cy.feature_set)
except Exception as e: print('no feature_set:', e)
bpy.ops.mesh.primitive_plane_add(size=2)
ob = bpy.context.object
print('object.cycles settings:', [p for p in dir(ob.cycles) if not p.startswith('_') and 'bl_' not in p and 'rna' not in p][:40])
mat = bpy.data.materials.new('m')
print('material settings with displ:', [p for p in dir(mat) if 'displ' in p.lower()])
print('material.cycles settings:', [p for p in dir(mat.cycles) if not p.startswith('_') and 'rna' not in p][:30])
md = ob.modifiers.new('s', 'SUBSURF')
print('subsurf modifier settings:', [p for p in dir(md) if not p.startswith('_') and 'rna' not in p])
