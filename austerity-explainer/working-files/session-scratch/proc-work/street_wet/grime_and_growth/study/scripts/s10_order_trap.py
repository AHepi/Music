# What this does (plain words): STUDY ONLY, saves nothing. Tests two suspected traps of the earlier apply scripts, in memory:
#  1. order: put on wetness, joints, rubbish, then take the JOINTS layer off first (the wrong order). Does it break?
#  2. wetness applied twice, or the state 'today' after a layer is on.
import sys, traceback
import bpy
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
sys.path[:0] = [base + 'tools', base + 'relief_and_rubbish/setts/tools', base + 'relief_and_rubbish/rubbish/tools']
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw
import apply_joints_to_set as aj
import apply_rubbish_to_set as ar
aw.apply(wetness=0.85, puddles=0.5)
aj.apply()
ar.apply(places='street', pieces=False)
print('ALL THREE ON')
try:
    aj.remove()          # wrong order: JOINTS is under RUBBISH
    print('TRAP1: removing JOINTS first did not raise')
    _t = bpy.data.materials['street_setts'].node_tree
    _p = next(n for n in _t.nodes if n.type == 'BSDF_PRINCIPLED')
    print('TRAP1 CHAIN after wrong-order removal: Principled Base Color is fed by', _p.inputs['Base Color'].links[0].from_node.name, '| RUBBISH node outputs linked:', any(o.is_linked for o in ar._STATE['nodes']['street_setts'].outputs), '| RUBBISH Colour input linked:', ar._STATE['nodes']['street_setts'].inputs['Colour'].is_linked)
    # does RUBBISH still have a valid input?
    tree = bpy.data.materials['street_setts'].node_tree
    node = ar._STATE['nodes']['street_setts']
    print('rubbish colour input linked:', node.inputs['Colour'].is_linked, 'from', node.inputs['Colour'].links[0].from_node.name if node.inputs['Colour'].is_linked else None)
except Exception:
    print('TRAP1: removing JOINTS first RAISED:')
    traceback.print_exc()
try:
    ar.remove()
    print('rubbish.remove after wrong order: ok')
except Exception:
    print('TRAP1b: rubbish.remove after that RAISED:')
    traceback.print_exc()
tree = bpy.data.materials['street_setts'].node_tree
p = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
for name in ('Base Color', 'Roughness', 'Normal'):
    s = p.inputs[name]
    print('AFTER BOTH REMOVED', name, 'linked' if s.is_linked else 'NOT LINKED', (s.links[0].from_node.name) if s.is_linked else '')
print('NODES LEFT', sorted({n.name for n in tree.nodes if n.type == 'GROUP'}))
