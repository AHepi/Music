# What this file does: carries out the save plan (plan.json, or another plan file named on the
# command line) in batches small enough for this computer's nearly full disk and for GitHub.
# For each batch it makes a fresh, tiny copy of the repository that holds no file contents
# (a "partial clone"), puts the batch's files into it (moving the big pictures and models,
# copying everything else), commits, pushes, and then deletes that copy, so the disk space comes
# back. A "moved" file is first linked into the copy (no extra space) and its original is deleted
# only after the push has succeeded, so a failed push never loses a file. It remembers which batches are done in a progress file, so it can be run again after a stop.
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_FILE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'plan.json')
LABEL = os.path.splitext(os.path.basename(PLAN_FILE))[0]
CLONE = os.path.join(HERE, 'clone')
URL = 'https://github.com/AHepi/Music'
BRANCH = 'ccr-e7298c9b-n19qkt'
BATCH_BYTES = 300 * 1024 * 1024
KEEP_FREE_BYTES = 700 * 1024 * 1024
TRAILER = ('\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
           'Claude-Session: https://claude.ai/code/session_01EvrRycp2XpFVXzJLwEfAgT\n')


def log(message):
    line = time.strftime('%H:%M:%S ') + message
    print(line, flush=True)
    with open(os.path.join(HERE, 'save_log.txt'), 'a') as handle:
        handle.write(line + '\n')


def run(args, cwd=None, check=True):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(' '.join(args[:4]) + ' failed: ' + result.stderr[-800:])
    return result


def git(*args, check=True):
    return run(['git', '-C', CLONE, *args], check=check)


def free_bytes():
    stats = os.statvfs('/')
    return stats.f_bavail * stats.f_frsize


def fresh_clone():
    shutil.rmtree(CLONE, ignore_errors=True)
    run(['git', 'clone', '-q', '--depth', '1', '--filter=blob:none', '--sparse', '--branch', BRANCH, URL, CLONE])
    git('config', 'user.name', 'Claude')
    git('config', 'user.email', 'noreply@anthropic.com')
    git('config', 'gc.auto', '0')


def push_with_retries():
    for wait in (0, 2, 4, 8, 16, 32):
        time.sleep(wait)
        result = git('push', '-q', 'origin', 'HEAD:' + BRANCH, check=False)
        if result.returncode == 0:
            return
        log('push failed, retrying: ' + result.stderr.strip()[-300:])
        if 'non-fast-forward' in result.stderr or 'fetch first' in result.stderr:
            git('fetch', '-q', '--depth', '1', 'origin', BRANCH)
            git('rebase', '-q', 'FETCH_HEAD')
    raise RuntimeError('push kept failing')


plan = json.load(open(PLAN_FILE))['plan']
plan.sort(key=lambda item: item['target'])
batches, current, current_bytes = [], [], 0
for item in plan:
    if current and current_bytes + item['size'] > BATCH_BYTES:
        batches.append(current)
        current, current_bytes = [], 0
    current.append(item)
    current_bytes += item['size']
if current:
    batches.append(current)

progress_file = os.path.join(HERE, f'progress-{LABEL}.json')
done = set(json.load(open(progress_file))) if os.path.exists(progress_file) else set()
log(f'{LABEL}: {len(batches)} batches, {len(done)} already done')

for number, batch in enumerate(batches, 1):
    if number in done:
        continue
    moved = sum(i['size'] for i in batch if i['action'] == 'move')
    copied = sum(i['size'] for i in batch if i['action'] == 'copy')
    need = moved + 2 * copied + KEEP_FREE_BYTES
    while free_bytes() < need:
        log(f'batch {number}: waiting for disk space ({free_bytes() // 1048576} MB free, need {need // 1048576} MB)')
        time.sleep(60)
    fresh_clone()
    targets = []
    for item in batch:
        source, target = item['source'], os.path.join(CLONE, item['target'])
        if not os.path.exists(source):
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if item['action'] == 'move':
            os.link(source, target)
        else:
            shutil.copy2(source, target)
        targets.append(item['target'])
    if not targets:
        done.add(number)
        continue
    list_file = os.path.join(HERE, f'batch-{LABEL}-{number}.txt')
    with open(list_file, 'w') as handle:
        handle.write('\n'.join(targets) + '\n')
    git('add', '--sparse', '--pathspec-from-file=' + list_file)
    folders = sorted({'/'.join(t.split('/')[2:4]) for t in targets if len(t.split('/')) > 4})
    summary = ', '.join(folders[:5]) + (' and more' if len(folders) > 5 else '')
    message = (f'Working files (log 35), {LABEL} batch {number} of {len(batches)}: {len(targets)} files '
               f'({(moved + copied) // 1048576} MB) from {summary}' + TRAILER)
    git('commit', '-q', '-m', message)
    push_with_retries()
    for item in batch:
        if item['action'] == 'move' and os.path.exists(item['source']):
            os.remove(item['source'])
    shutil.rmtree(CLONE, ignore_errors=True)
    done.add(number)
    json.dump(sorted(done), open(progress_file, 'w'))
    log(f'{LABEL} batch {number} of {len(batches)} pushed: {len(targets)} files, {(moved + copied) // 1048576} MB; '
        f'{free_bytes() // 1048576} MB free')

log(f'{LABEL}: ALL BATCHES DONE')
