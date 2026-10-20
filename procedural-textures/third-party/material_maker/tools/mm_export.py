# Plain note: runs Material Maker 1.7 in the background (virtual screen + software Vulkan "lavapipe", no graphics card needed) to turn
# one graph file (.ptex) into picture files (albedo, normal, height, roughness ...) in an output folder. Two quirks found by testing:
#  (1) Material Maker 1.7 does not quit by itself after a command-line export, so this script waits until the expected files exist
#      and have stopped changing, then stops the program;
#  (2) it crashes at start-up about one run in five (before drawing anything), so this script starts it again (up to --tries times).
# The program cannot reach the internet (the proxy setting is removed in run_mm.sh).
# Usage: python3 -I mm_export.py GRAPH.ptex OUTPUT_FOLDER [--target Blender] [--wait 6] [--timeout 600] [--any]
# Result: prints one line of JSON (files written, seconds taken, how many tries); exit code 0 if the files appeared.
import os, sys, time, signal, subprocess, json, argparse, glob

HERE = 'proc-work/third-party/material_maker'
RUNNER = HERE + '/run_mm.sh'

# which Material-node input port gives which file in the "Blender" export (read from nodes/material.mmg)
BLENDER_PORT_FILE = {0: '_albedo.png', 1: '_metal.exr', 2: '_rough.exr', 3: '_emission.png', 4: '_normal.png', 5: '_occlusion.exr', 6: '_displace.exr', 8: '_sss.exr'}


def expected_files(ptex_path, out_dir):
    data = json.load(open(ptex_path))
    stem = os.path.splitext(os.path.basename(ptex_path))[0]
    names = {n['name'] for n in data['nodes'] if n['type'] == 'material'}
    ports = sorted({c['to_port'] for c in data['connections'] if c['to'] in names})
    return [os.path.join(out_dir, stem + BLENDER_PORT_FILE[p]) for p in ports if p in BLENDER_PORT_FILE]


def stop(proc):
    if proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        time.sleep(1.0)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


def one_try(a, want, log_path):
    log = open(log_path, 'w')
    proc = subprocess.Popen([RUNNER, '--verbose', '--export-material', '--target', a.target, '-o', a.out, a.ptex],
                            stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    ok = False
    while time.time() - t0 < a.timeout:
        if proc.poll() is not None:
            break  # the program ended by itself (crash, or a clean exit)
        if want:
            have = [f for f in want if os.path.exists(f)]
            if len(have) == len(want) and time.time() - max(os.path.getmtime(f) for f in have) > a.wait:
                ok = True
                break
        else:
            outs = [f for f in glob.glob(os.path.join(a.out, '*')) if not f.endswith('.log')]
            if outs and time.time() - t0 > 12 and time.time() - max(os.path.getmtime(f) for f in outs) > a.wait + 4:
                ok = True
                break
        time.sleep(0.5)
    ended_by_itself = proc.poll() is not None
    stop(proc)
    if want:
        ok = ok or all(os.path.exists(f) for f in want)
    else:
        ok = ok or bool([f for f in glob.glob(os.path.join(a.out, '*')) if not f.endswith('.log')])
    return ok, ended_by_itself, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ptex')
    ap.add_argument('out')
    ap.add_argument('--target', default='Blender')
    ap.add_argument('--wait', type=float, default=6.0, help='seconds the files must stay unchanged before the program is stopped')
    ap.add_argument('--timeout', type=float, default=600.0)
    ap.add_argument('--tries', type=int, default=4)
    ap.add_argument('--any', action='store_true', help='do not expect particular file names (other targets than Blender)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    want = expected_files(a.ptex, a.out) if (a.target == 'Blender' and not a.any) else []
    t_all = time.time()
    for attempt in range(1, a.tries + 1):
        ok, ended, secs = one_try(a, want, os.path.join(a.out, 'mm_stdout.log'))
        if ok:
            break
    files = sorted(f for f in os.listdir(a.out) if not f.endswith('.log'))
    print(json.dumps({'seconds': round(time.time() - t_all, 1), 'tries': attempt, 'ok': ok, 'files': files}))
    sys.exit(0 if ok else 1)


main()
