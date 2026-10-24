# Critic (look lens) test wrapper v2: optional CRITIC_PRE snippet (patch module constants BEFORE the build), the normal
# assembler WITHOUT rendering, optional CRITIC_TWEAK snippet (edit the built scene), then render.
# Read-only for the project: it only writes critic_look_* files.
import os
import sys
import runpy

HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, os.path.join(HERE, 'lib'))
sys.path.insert(0, os.path.join(HERE, 'modules'))
import bpy  # noqa: E402

argv_tail = sys.argv[sys.argv.index('--') + 1:]
if '--no-render' not in argv_tail:
    sys.argv = sys.argv + ['--no-render']
pre = os.environ.get('CRITIC_PRE')
if pre:
    exec(open(pre).read(), {'bpy': bpy, 'HERE': HERE})
namespace = runpy.run_path(os.path.join(HERE, 'assemble_mine.py'), run_name='assembler_run')
tweak = os.environ.get('CRITIC_TWEAK')
if tweak:
    exec(open(tweak).read(), {'bpy': bpy, 'mc': namespace['mc'], 'namespace': namespace})
scene = bpy.context.scene
import time  # noqa: E402
t0 = time.time()
bpy.ops.render.render(write_still=True)
print('[critic] render seconds', round(time.time() - t0, 1), scene.render.filepath, flush=True)
