# Critic (look lens) test wrapper: runs the normal assembler WITHOUT rendering, then applies the tweak snippet named in the
# environment variable CRITIC_TWEAK (a python file), then renders. Read-only for the project: it only writes critic_look_* files.
import os
import sys
import runpy

HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
argv_tail = sys.argv[sys.argv.index('--') + 1:]
if '--no-render' not in argv_tail:
    sys.argv = sys.argv + ['--no-render']
namespace = runpy.run_path(os.path.join(HERE, 'assemble_mine.py'), run_name='assembler_run')
import bpy  # noqa: E402

tweak = os.environ.get('CRITIC_TWEAK')
if tweak:
    exec(open(tweak).read(), {'bpy': bpy, 'mc': namespace['mc'], 'namespace': namespace})
scene = bpy.context.scene
import time  # noqa: E402
t0 = time.time()
bpy.ops.render.render(write_still=True)
print('[critic] render seconds', round(time.time() - t0, 1), scene.render.filepath, flush=True)
