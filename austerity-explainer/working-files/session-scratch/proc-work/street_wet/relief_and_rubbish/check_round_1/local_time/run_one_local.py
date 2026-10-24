# What this file does (plain words): runs ONE Blender job here (xvfb, 2 threads, like the earlier helpers) and prints the wall-clock seconds and the biggest memory the run used. Use: python3 -I run_one_local.py JOB_FILE OUT_FOLDER
import resource, subprocess, sys, time
S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet'
T = S + '/relief_and_rubbish/rubbish/tools/rubbish_runner.py'
LOCKOUT = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend'
job, out = sys.argv[1], sys.argv[2]
cmd = ['xvfb-run', '-a', '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', LOCKOUT, '--python', T, '--', job, out]
t = time.time()
with open(out + '/log_local.txt', 'w') as log:
    rc = subprocess.run(cmd, cwd=S, stdout=log, stderr=subprocess.STDOUT).returncode
print('return code', rc, 'wall seconds', round(time.time() - t), 'peak memory MB', round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024))
