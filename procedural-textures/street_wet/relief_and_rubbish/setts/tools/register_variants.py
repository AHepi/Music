# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A tiny helper script for the study's picture runner (study/tools/b03_render_jobs.py). The runner runs it once inside Blender, after the round 2 wetness layer is on (that is
# what a job file's "after_apply" does). All it does is make the new road variant called "joints_layer" (joint_layer.py) known to the runner, so a job can say
# {"variant": "joints_layer", "args": {"darkness": 0.15, ...}}. It changes nothing in the street by itself.
import sys

SETTS_TOOLS = 'proc-work/street_wet/relief_and_rubbish/setts/tools'
if SETTS_TOOLS not in sys.path:
    sys.path.insert(0, SETTS_TOOLS)
sys.dont_write_bytecode = True
import joint_layer  # noqa: E402

joint_layer.register_variants(lv, aw)      # lv and aw are given to this script by the runner
print('REGISTERED variants:', sorted(lv.VARIANTS), flush=True)
