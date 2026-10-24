import sys, json
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import bpy, street_weathering as sw, apply_weathering as aw
w = sw.apply(state='wet', masters={'walls': 0.5, 'growth': 0})
print('ACTIVE', sorted(w.kit.active), 'soot amount node value', [n.inputs['Amount'].default_value for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type=='GROUP' and n.name=='WK soot'][:1])
sw.set_master('earlier', 0)
print('state after earlier 0', w.state)
sw.set_master('all', 0.2); sw.set_master('soot', 0)
sw.remove(); print('removed', aw.current() is None)
w2 = sw.apply(state='dry'); sw.remove(); print('second cycle ok')
