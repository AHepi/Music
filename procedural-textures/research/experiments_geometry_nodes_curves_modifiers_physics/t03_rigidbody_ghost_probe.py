# What this does: tests in Blender 5.2.2 whether Rigid Body physics can be driven step by step from Python (scene.frame_set) and whether
# moving a kinematic "ghost" object from Python on every step resets the simulation. A ghost = a copy of a rock that is moved to follow the real rock,
# shifted by one tile, so rocks near the tile edge feel the rocks on the other side (a way to make a physics pile wrap).
import bpy, sys, os, time
import numpy as np
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0)); floor = bpy.context.object; floor.scale = (10, 10, 0.1); floor.location.z = -0.05
bpy.ops.rigidbody.object_add(type='PASSIVE')
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 1.0)); rock = bpy.context.object
bpy.ops.rigidbody.object_add(type='ACTIVE')
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(3, 0, 1.0)); ghost = bpy.context.object
bpy.ops.rigidbody.object_add(type='PASSIVE'); ghost.rigid_body.kinematic = True
scene.rigidbody_world.point_cache.frame_start = 1; scene.rigidbody_world.point_cache.frame_end = 200
scene.frame_start, scene.frame_end = 1, 200
def run(update_ghost):
    scene.frame_set(1)
    rock.location = (0, 0, 1.0); rock.rotation_euler = (0, 0, 0)
    zs = []
    t = time.time()
    for f in range(2, 60):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        zs.append(rock.matrix_world.translation.z)
        if update_ghost:
            ghost.matrix_world = rock.matrix_world.copy()
            ghost.matrix_world.translation.x += 3.0
    return zs, time.time() - t
mode = sys.argv[sys.argv.index('--') + 1]
zs, secs = run(mode == 'ghost')
print(mode, ': z at frames 2,10,20,40,59', [round(zs[i], 3) for i in (0, 8, 18, 38, 57)], 'seconds', round(secs, 3))
print('free fall expectation at frame 10 (fps 24):', round(1.0 - 0.5 * 9.81 * (9 / 24) ** 2, 3))
