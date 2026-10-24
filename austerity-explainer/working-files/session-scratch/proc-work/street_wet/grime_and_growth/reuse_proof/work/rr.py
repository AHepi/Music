# Remote runner of the reuse proof: sends what changed (kit code, the courtyard's settings, looks, pack, my scripts), runs one Blender job on the rented machine, brings the pictures back.
# Uses ONLY runpod/render_client_cached.py. Never touches ~/.runpod. Never stops a machine.
import json, os, subprocess, sys, tarfile, tempfile, time
sys.dont_write_bytecode = True
CLIENT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py'
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BLENDER = '/workspace/blender/blender'
SCENE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work/out/courtyard_final.blend'
STATE = os.path.join(HERE, '.sent.json')


def client(*args, timeout=900):
    for attempt in range(3):
        p = subprocess.run(['python3', '-I', CLIENT] + [str(a) for a in args], capture_output=True, text=True, timeout=timeout)
        if p.returncode == 0:
            return p.stdout
        if 'no answer from the machine' in p.stderr + p.stdout:
            time.sleep(10)
            continue
        break
    raise RuntimeError('client failed: ' + (p.stderr or p.stdout)[-600:])


def run(command, limit=1500):
    job = client('run', command).strip().splitlines()[-1].strip()
    started = time.time()
    while True:
        out = client('wait', job, '--limit', 500, timeout=700)
        info = json.loads(out[out.find('{'):])
        if info.get('state') != 'running':
            return info.get('return_code'), info.get('log_tail', '')
        if time.time() - started > limit:
            return None, 'still running: ' + info.get('log_tail', '')


def kit_files():
    files = []
    for base, dirs, names in os.walk(KIT):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'baseline', 'legacy_pinned', 'legacy_round2', 'packs', 'textures')]
        for n in names:
            if n.endswith(('.py', '.json')) and 'integrate/' not in os.path.join(base, n):
                files.append(os.path.join(base, n))
    files.append(os.path.join(KIT, 'masks/packs/japanese_courtyard/courtyard'))
    return files


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for base, dirs, names in os.walk(p):
                for n in names:
                    out.append(os.path.join(base, n))
        else:
            out.append(p)
    return sorted(set(out))


def sha(p):
    import hashlib
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def sync(extra=()):
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    files = expand(kit_files() + list(extra))
    now, changed = {}, []
    for f in files:
        now[f] = sha(f)
        if state.get(f) != now[f]:
            changed.append(f)
    if not changed:
        return 0
    tar = tempfile.NamedTemporaryFile(suffix='.tar', delete=False).name
    with tarfile.open(tar, 'w') as a:
        for f in changed:
            a.add(f, arcname=f.lstrip('/'))
    remote = f'/workspace/uploads/reuse_{int(time.time())}.tar'
    client('upload', tar, '--remote', remote, timeout=1200)
    os.remove(tar)
    code, log = run(f'tar -xf "{remote}" -C / && rm "{remote}" && echo SYNC_OK', limit=300)
    if 'SYNC_OK' not in (log or ''):
        raise RuntimeError('unpack failed ' + str(log)[-300:])
    state.update(now)
    json.dump(state, open(STATE, 'w'))
    return len(changed)


def render(cfg_path, local_out):
    cfg = json.load(open(cfg_path))
    remote_out = cfg['out']
    sent = sync(extra=[cfg_path, os.path.join(HERE, 'reuse_render.py')])
    t = time.time()
    run(f'rm -rf "{remote_out}" && mkdir -p "{remote_out}"', limit=120)
    code, tail = run(f'"{BLENDER}" -b --disable-autoexec "{SCENE}" --python "{HERE}/reuse_render.py" -- "{cfg_path}" > "{remote_out}/run.log" 2>&1', limit=1500)
    tar_remote = remote_out.rstrip('/') + '.tar'
    run(f'cd "{remote_out}" && tar -cf "{tar_remote}" . && ls | wc -l', limit=300)
    local_tar = os.path.join(tempfile.gettempdir(), os.path.basename(tar_remote))
    client('download', tar_remote, '--local', local_tar, timeout=1200)
    os.makedirs(local_out, exist_ok=True)
    with tarfile.open(local_tar) as a:
        a.extractall(local_out)
    os.remove(local_tar)
    run(f'rm -f "{tar_remote}"', limit=120)
    return dict(seconds=round(time.time() - t, 1), sent_files=sent, return_code=code)


if __name__ == '__main__':
    cfg_path = sys.argv[1]
    cfg = json.load(open(cfg_path))
    print(render(cfg_path, cfg['out']))
