# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A tiny "run this once after the wetness layer is on" script for the study's picture runner (a job file's "after_apply", see make_job_lists.py): it puts the JOINTS layer on the
# road with the chosen settings (apply_joints_to_set.apply) and also makes the test variants 'joints_layer' and 'joints_geometry' known, so that one job file can mix pictures
# with the layer ON for the whole run and pictures that name a variant. The runner gives this script the names lv (the variant toolbox) and aw (the wetness tools).
import sys

SETTS_TOOLS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/setts/tools'
if SETTS_TOOLS not in sys.path:
    sys.path.insert(0, SETTS_TOOLS)
sys.dont_write_bytecode = True
import apply_joints_to_set  # noqa: E402
import joint_layer  # noqa: E402

joint_layer.register_variants(lv, aw)      # lv and aw are given to this script by the runner
apply_joints_to_set.apply()
print('JOINTS layer is on; variants:', sorted(lv.VARIANTS), flush=True)
