# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE REMOTE RUNNER: draws a batch of pictures on the rented graphics machine, through the ONE allowed client (runpod/render_client_cached.py; never the old render_client.py,
# never anything in ~/.runpod). Steps:
#   sync(paths)        sends only the files that changed since the last send (one tar, same absolute paths on the machine). A small marker file on the machine tells whether the
#                      earlier send is still there (a fresh machine forgets), and if not everything is sent again.
#   run_batch(...)     clears the remote output folder (the stale-picture trap: the runner skips pictures that exist), starts ONE Blender run that draws the whole job list, waits,
#                      packs the JPG, JSON (and any kept PNG) into one tar, brings it back, unpacks it here, and deletes the remote PNGs.
# Rules kept: states start with 'today' (the runner sorts them), one run per batch, no machine is stopped or ended, nothing is read from ~/.runpod.
# If a call says "no answer from the machine" run status() once and try again; "NO CARD FREE" means draw here and say so (the error is passed on).
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time

from . import KIT_ROOT

CLIENT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py'
BLENDER_REMOTE = '/workspace/blender/blender'
MARKER = os.path.join(KIT_ROOT, '.wk_synced_marker')
STATE_FILE = os.path.join(KIT_ROOT, 'harness', '.remote_state.json')
SKIP_DIRS = {'__pycache__', '.git', '_raw'}
SKIP_SUFFIX = ('.pyc', '.blend1')


def _client(*args, timeout=900, check=True):
    cmd = ['python3', '-I', CLIENT] + [str(a) for a in args]
    last = None
    for attempt in range(3):
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0:
            return proc.stdout
        last = proc
        if 'no answer from the machine' in (proc.stderr + proc.stdout):
            time.sleep(10)
            continue
        break
    if check:
        raise RuntimeError(f'client {args[0]} failed: {(last.stderr or last.stdout)[-800:]}')
    return (last.stdout or '') + (last.stderr or '')


def status():
    return _client('status')


def _json_after(text):
    """The client prints a JSON block (wait/job); returns it as a dict."""
    start = text.find('{')
    return json.loads(text[start:]) if start >= 0 else {}


def run_remote(command, cwd=None, limit=1700, poll_limit=570):
    """Runs a shell command on the machine and waits. Returns (return_code, log tail)."""
    args = ['run', command] + (['--cwd', cwd] if cwd else [])
    job_id = _client(*args).strip().splitlines()[-1].strip()
    started = time.time()
    while True:
        out = _client('wait', job_id, '--limit', poll_limit, timeout=poll_limit + 120)
        info = _json_after(out)
        if info.get('state') != 'running':
            return info.get('return_code'), info.get('log_tail', '')
        if time.time() - started > limit:
            return None, 'still running after the time limit: ' + info.get('log_tail', '')


def collect_files(roots):
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(os.path.abspath(root))
            continue
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in names:
                if name.endswith(SKIP_SUFFIX) or name.startswith('.remote_state'):
                    continue
                files.append(os.path.join(base, name))
    return sorted(set(files))


def _sha(path):
    h = hashlib.sha1()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def machine_has_marker():
    code, log = run_remote(f'test -f "{MARKER}" && echo WK_SYNC_YES || echo WK_SYNC_NO', limit=120)
    return 'WK_SYNC_YES' in (log or '')


def sync(roots, force=False):
    """Sends changed files. Returns (files sent, bytes)."""
    state = {}
    if os.path.exists(STATE_FILE) and not force:
        state = json.load(open(STATE_FILE))
        if state and not machine_has_marker():
            state = {}
    files = collect_files(roots)
    changed = []
    now = {}
    for path in files:
        digest = _sha(path)
        now[path] = digest
        if state.get(path) != digest:
            changed.append(path)
    if not changed:
        return 0, 0
    tar_path = tempfile.NamedTemporaryFile(suffix='.tar', delete=False).name
    with tarfile.open(tar_path, 'w') as archive:
        for path in changed:
            archive.add(path, arcname=path.lstrip('/'))
    size = os.path.getsize(tar_path)
    remote_tar = f'/workspace/uploads/wk_sync_{int(time.time())}.tar'
    _client('upload', tar_path, '--remote', remote_tar, timeout=1800)
    os.remove(tar_path)
    code, log = run_remote(f'tar -xf "{remote_tar}" -C / && rm "{remote_tar}" && touch "{MARKER}"', limit=600)
    if code != 0:
        raise RuntimeError('unpacking the sent files failed: ' + str(log)[-500:])
    state.update(now)
    json.dump(state, open(STATE_FILE, 'w'))
    return len(changed), size


def run_batch(blend, jobs_files, remote_out, local_out, runner_script=None, extra_roots=(), timeout=3000, keep_log=True):
    """Draws a whole batch of pictures remotely. blend: absolute path of the scene file (same path on the machine). jobs_files: list of local job JSON paths (sent too).
    Returns dict(seconds_total, return_code, log_tail, files)."""
    runner_script = runner_script or os.path.join(KIT_ROOT, 'harness', 'runner.py')
    roots = [KIT_ROOT] + list(extra_roots) + [os.path.abspath(j) for j in jobs_files]
    sent, size = sync(roots)
    started = time.time()
    os.makedirs(local_out, exist_ok=True)
    remote_logs = []
    code_total = 0
    # the stale-picture trap: the remote folder is cleared before a run
    run_remote(f'rm -rf "{remote_out}" && mkdir -p "{remote_out}"', limit=120)
    for jobs_file in jobs_files:
        log = os.path.join(remote_out, os.path.basename(jobs_file) + '.log')
        cmd = f'"{BLENDER_REMOTE}" -b --disable-autoexec "{blend}" --python "{runner_script}" -- "{os.path.abspath(jobs_file)}" "{remote_out}" > "{log}" 2>&1'
        code, tail = run_remote(cmd, limit=timeout)
        code_total = code if code not in (0, None) else code_total
    # one tar of the small files, then delete the remote PNGs that are not kept
    tar_remote = remote_out.rstrip('/') + '.tar'
    code, log = run_remote(f'cd "{remote_out}" && tar -cf "{tar_remote}" --exclude="*.log" . && ls | wc -l', limit=300)
    local_tar = os.path.join(tempfile.gettempdir(), os.path.basename(tar_remote))
    _client('download', tar_remote, '--local', local_tar, timeout=1800)
    with tarfile.open(local_tar) as archive:
        archive.extractall(local_out)
    os.remove(local_tar)
    run_remote(f'rm -f "{tar_remote}" "{remote_out}"/*.png', limit=120)
    files = sorted(os.listdir(local_out))
    return dict(seconds_total=round(time.time() - started, 1), return_code=code_total, files=len(files), sent_files=sent, sent_bytes=size)


def run_script(blend, script, script_args, remote_out, local_out, extra_roots=(), timeout=3000, fetch=True):
    """Runs any Blender script of the kit remotely (the self-tests, the plan pictures ...): sends changed files, clears remote_out, runs
    blender -b BLEND --python SCRIPT -- ARGS, brings remote_out back as one tar. script_args may name remote_out as '{out}'."""
    roots = [KIT_ROOT] + list(extra_roots)
    sent, size = sync(roots)
    started = time.time()
    os.makedirs(local_out, exist_ok=True)
    run_remote(f'rm -rf "{remote_out}" && mkdir -p "{remote_out}"', limit=120)
    args = ' '.join('"%s"' % a.replace('{out}', remote_out) for a in script_args)
    log = os.path.join(remote_out, 'run.log')
    code, tail = run_remote(f'"{BLENDER_REMOTE}" -b --disable-autoexec "{blend}" --python "{script}" -- {args} > "{log}" 2>&1', limit=timeout)
    result = dict(seconds_total=round(time.time() - started, 1), return_code=code, sent_files=sent, sent_bytes=size)
    if fetch:
        tar_remote = remote_out.rstrip('/') + '.tar'
        run_remote(f'cd "{remote_out}" && tar -cf "{tar_remote}" . && ls | wc -l', limit=300)
        local_tar = os.path.join(tempfile.gettempdir(), os.path.basename(tar_remote))
        _client('download', tar_remote, '--local', local_tar, timeout=1800)
        with tarfile.open(local_tar) as archive:
            archive.extractall(local_out)
        os.remove(local_tar)
        run_remote(f'rm -f "{tar_remote}" "{remote_out}"/*.png', limit=120)
    return result
