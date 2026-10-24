# What this does: a small job server that runs on the rented RunPod graphics machine. The cloud session cannot open a terminal (SSH) to the machine,
# so it talks to this server over RunPod's HTTPS address instead: it uploads files in pieces, starts commands (Blender renders) in the background,
# asks how they are doing, and downloads the results in pieces. Every request must carry the secret token from the SERVER_TOKEN environment variable.
# Requests are kept short because RunPod's HTTPS address cuts any request off after 100 seconds.
# Cached version: the machine's files live on a permanent RunPod network volume mounted at /workspace (Blender, uploads, results survive), the paths
# /tmp/claude-0 and /home/user point into it, and the server ends its own machine after IDLE_SECONDS with no request and no running job.
import base64
import hashlib
import json
import os
import subprocess
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SERVER_TOKEN = os.environ['SERVER_TOKEN']
JOB_FOLDER = '/workspace/jobs'
os.makedirs(JOB_FOLDER, exist_ok=True)
jobs = {}
jobs_lock = threading.Lock()
last_request_time = time.time()
IDLE_SECONDS = int(os.environ.get('IDLE_SECONDS', '900'))


def end_machine_when_idle():
    while True:
        time.sleep(30)
        with jobs_lock:
            busy = any(job['state'] == 'running' for job in jobs.values())
        if busy or time.time() - last_request_time < IDLE_SECONDS:
            continue
        for action in ('terminate', 'stop'):
            request = urllib.request.Request(f"https://api.runpod.io/v2/pods/{os.environ['RUNPOD_POD_ID']}/action", method='POST',
                                             data=json.dumps({'action': action}).encode(),
                                             headers={'Authorization': 'Bearer ' + os.environ['RUNPOD_API_KEY'], 'Content-Type': 'application/json',
                                                      'User-Agent': 'render-job-server/1.0'})
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    open('/workspace/idle.log', 'a').write(f'{time.ctime()} idle for {IDLE_SECONDS} s: {action} -> {response.status}\n')
                    break
            except Exception as problem:
                open('/workspace/idle.log', 'a').write(f'{time.ctime()} {action} failed: {problem}\n')
        time.sleep(300)


def run_job(job_id, command, working_folder, environment):
    log_path = os.path.join(JOB_FOLDER, job_id + '.log')
    started = time.time()
    with open(log_path, 'wb') as log_file:
        process = subprocess.Popen(command, cwd=working_folder or '/workspace', stdout=log_file, stderr=subprocess.STDOUT,
                                   shell=isinstance(command, str), env={**os.environ, **(environment or {})})
        with jobs_lock:
            jobs[job_id]['pid'] = process.pid
        return_code = process.wait()
    with jobs_lock:
        jobs[job_id].update(state='finished', return_code=return_code, seconds=round(time.time() - started, 1))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, content_type='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def allowed(self):
        global last_request_time
        if self.headers.get('X-Token') != SERVER_TOKEN:
            self.reply(403, {'error': 'wrong or missing token'})
            return False
        last_request_time = time.time()
        return True

    def do_GET(self):
        if not self.allowed():
            return
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == '/status':
            gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader'],
                                 capture_output=True, text=True).stdout.strip()
            disk = subprocess.run(['df', '-h', '/workspace'], capture_output=True, text=True).stdout.strip().splitlines()[-1]
            with jobs_lock:
                running = [job_id for job_id, job in jobs.items() if job['state'] == 'running']
            self.reply(200, {'gpu': gpu, 'disk': disk, 'running_jobs': running,
                             'blender_ready': os.path.exists('/tmp/setup_done') and os.path.exists('/workspace/blender/blender'), 'idle_seconds': IDLE_SECONDS, 'time': time.time()})
        elif url.path.startswith('/jobs/'):
            job_id = url.path.split('/')[-1]
            with jobs_lock:
                job = dict(jobs.get(job_id, {}))
            if not job:
                return self.reply(404, {'error': 'no such job'})
            tail_bytes = int(query.get('tail', ['4000'])[0])
            log_path = os.path.join(JOB_FOLDER, job_id + '.log')
            log_tail = b''
            if os.path.exists(log_path):
                with open(log_path, 'rb') as log_file:
                    log_file.seek(max(0, os.path.getsize(log_path) - tail_bytes))
                    log_tail = log_file.read()
            job['log_tail'] = log_tail.decode(errors='replace')
            self.reply(200, job)
        elif url.path == '/file':
            path = query['path'][0]
            offset = int(query.get('offset', ['0'])[0])
            length = int(query.get('length', [str(32 * 1024 * 1024)])[0])
            if not os.path.isfile(path):
                return self.reply(404, {'error': 'no such file'})
            with open(path, 'rb') as file:
                file.seek(offset)
                self.reply(200, file.read(length), 'application/octet-stream')
        elif url.path == '/info':
            path = query['path'][0]
            if os.path.isdir(path):
                entries = []
                for root, dirs, files in os.walk(path):
                    for name in files:
                        full = os.path.join(root, name)
                        entries.append([full, os.path.getsize(full)])
                return self.reply(200, {'folder': True, 'files': entries[:20000]})
            if not os.path.isfile(path):
                return self.reply(404, {'error': 'no such file'})
            digest = hashlib.sha256()
            with open(path, 'rb') as file:
                for block in iter(lambda: file.read(1 << 20), b''):
                    digest.update(block)
            self.reply(200, {'folder': False, 'size': os.path.getsize(path), 'sha256': digest.hexdigest()})
        else:
            self.reply(404, {'error': 'unknown address'})

    def do_POST(self):
        if not self.allowed():
            return
        url = urlparse(self.path)
        query = parse_qs(url.query)
        body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        if url.path == '/file':
            path = query['path'][0]
            offset = int(query.get('offset', ['0'])[0])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = 'r+b' if offset and os.path.exists(path) else 'wb'
            with open(path, mode) as file:
                file.seek(offset)
                file.write(body)
            self.reply(200, {'written': len(body), 'size': os.path.getsize(path)})
        elif url.path == '/run':
            request = json.loads(body)
            job_id = uuid.uuid4().hex[:12]
            with jobs_lock:
                jobs[job_id] = {'id': job_id, 'state': 'running', 'command': request['command'], 'started': time.time()}
            threading.Thread(target=run_job, args=(job_id, request['command'], request.get('cwd'), request.get('env')), daemon=True).start()
            self.reply(200, {'id': job_id})
        else:
            self.reply(404, {'error': 'unknown address'})


if __name__ == '__main__':
    threading.Thread(target=end_machine_when_idle, daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
