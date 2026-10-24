import bpy, sys, math
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_geometry_nodes_curves_modifiers_physics')
import gn_tools as gt, t05_modifier_gallery as t5, numpy as np
gt.new_scene(64)
obj = t5.add('w', t5.grid_mesh('w', 64), (0.5, 0.5, 0.05))
m = obj.modifiers.new('wave', 'WAVE')
for attr in ('height','width','narrowness','speed','time_offset','lifetime','damping_time','falloff_radius','start_position_x','start_position_y','use_x','use_y','use_cyclic','use_normal'):
    print(attr, getattr(m, attr))
for frame in (1, 10, 30, 60):
    bpy.context.scene.frame_set(frame)
    p = gt.evaluated_vertices(obj); print(frame, p[:,2].min(), p[:,2].max())
m.height=0.06
for frame in (10, 30):
    bpy.context.scene.frame_set(frame)
    p = gt.evaluated_vertices(obj); print('height .06 only', frame, p[:,2].min(), p[:,2].max())
m.width=0.12; m.narrowness=1.5
for frame in (10, 30):
    bpy.context.scene.frame_set(frame)
    p = gt.evaluated_vertices(obj); print('+ width .12 narrowness 1.5', frame, p[:,2].min(), p[:,2].max())
