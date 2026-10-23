"""What this does: the two ways the variations tool talks to a rented card, behind one small set of calls (upload, submit, wait, download), so the runner does not care which one is used.
  ClientCard    the plugin's own client (place_kit/render/client.py: RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID in the environment or in the file named by RENDER_SETTINGS_FILE). It knows what every
                small job billed, so the card-time ledger is exact.
  CommandCard   any command-line client that offers the actions the older clients offer: `upload LOCAL --remote PATH`, `run "COMMAND" --cwd FOLDER --timeout SECONDS` (prints a job id),
                `job ID` and `download REMOTE --local PATH` (JSON or plain lines: see the notes on each call). Name it with --card-client "python3 -I /path/render_client_serverless.py".
                It cannot say what an upload billed, so those steps are counted from the wall clock (marked as an estimate in the ledger); the jobs themselves report their billed seconds.
Both end a wait the same way the rest of the kit does: a job that waits in line for place_render.jobs_waiting_stop_minutes while the card shows idle (ClientCard) or at all (CommandCard,
which cannot ask) STOPS the batch with a plain sentence; nothing is cancelled, purged or changed. They never print or store a key or an endpoint id.
A FakeCard for the tests lives in the test file, not here. Plain Python (standard library only); no Blender needed.

A concrete example: backend = ClientCard(Client(WebTransport(settings)), settings); backend.submit('echo hi', '/workspace', 60) returns a job id; backend.wait(id, 600) returns
{'id', 'runpod_status', 'return_code', 'seconds', 'wake_up_ms', 'billed_work_ms', 'log_tail'}.
"""
import json
import os
import shlex
import subprocess
import time

from .. import house_numbers as numbers
from ..render import client as client_module


class CardProblem(Exception):
    """The card client cannot be used or a call failed (exit 1 for a failed call; exit 2 for a missing setting)."""


class ClientCard:
    kind = 'the plugin client'

    def __init__(self, client, settings):
        self.client, self.settings = client, settings
        self.store_folder, self.remote_blender = settings.store_folder, settings.remote_blender

    def upload(self, local, remote):
        uploads = self.store_folder + '/place-jobs/uploads'
        if os.path.isdir(local):
            return self.client.upload_folder(local, remote, uploads)
        return self.client.upload_file(local, remote)

    def have_file(self, remote_path):
        try:
            return self.client.do({'op': 'info', 'path': remote_path}).get('size', 0) > 0
        except client_module.RentFailed:
            return False

    def submit(self, command, cwd, timeout):
        return self.client.submit({'op': 'run', 'command': command, 'cwd': cwd, 'timeout': timeout})

    def wait(self, job_id, limit):
        return client_module.job_summary(self.client.wait_for(job_id, limit))

    def download(self, remote, local):
        info = self.client.do({'op': 'info', 'path': remote})
        if info.get('size') is None:
            raise CardProblem(f'{remote} is not on the store')
        self.client.download_file(remote, local, info['size'])
        return local

    def small_jobs(self):
        return list(self.client.small_jobs)

    def wall_seconds(self):
        return None


class CommandCard:
    kind = 'a command-line client'

    def __init__(self, argv_prefix, store_folder='/workspace', remote_blender=None, poll_seconds=5.0):
        self.argv = list(argv_prefix)
        self.store_folder = store_folder.rstrip('/') or '/'
        self.remote_blender = remote_blender or self.store_folder + '/blender/blender'
        self.poll_seconds = poll_seconds
        self.seconds_used = 0.0

    @classmethod
    def from_text(cls, text, **options):
        argv = shlex.split(text or '')
        if not argv:
            raise CardProblem('--card-client needs the command that starts the client, for example: --card-client "python3 -I /path/to/render_client_serverless.py"')
        return cls(argv, **options)

    def _call(self, args, timeout=900):
        started = time.time()
        try:
            run = subprocess.run(self.argv + args, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as problem:
            raise CardProblem(f'the card client could not be run: {problem}')
        finally:
            if args[0] in ('upload', 'download'):          # only these keep a worker busy (the older client does each in small jobs); `run` and `job` only ask the service
                self.seconds_used += time.time() - started
        if run.returncode != 0:
            tail = (run.stderr or run.stdout or '').strip().splitlines()[-3:]
            raise CardProblem(f'the card client failed on "{args[0]}": ' + ' | '.join(tail)[:400])
        return run.stdout

    def upload(self, local, remote):
        return self._call(['upload', local, '--remote', remote]).strip().splitlines()[-1:] or ['uploaded']

    def have_file(self, remote_path):
        return False                  # this client has no cheap way to ask: the kit is uploaded again

    def submit(self, command, cwd, timeout):
        output = self._call(['run', command, '--cwd', cwd, '--timeout', str(int(timeout))]).strip().splitlines()
        if not output:
            raise CardProblem('the card client printed no job id for the job it was asked to run')
        return output[-1].strip()

    def wait(self, job_id, limit):
        started = time.time()
        queued_since = None
        stop_after = numbers.value('place_render.jobs_waiting_stop_minutes') * 60
        while True:
            text = self._call(['job', job_id], timeout=120)
            try:
                summary = json.loads(text[text.index('{'):])
            except ValueError:
                raise CardProblem(f'the card client answered "job {job_id}" with something that is not JSON: {text[:200]}')
            status = summary.get('runpod_status')
            if summary.get('state') == 'finished' or status in client_module.DONE:
                return summary
            now = time.time()
            if status == 'IN_QUEUE':
                queued_since = now if queued_since is None else queued_since
                if now - queued_since >= stop_after:
                    raise client_module.RentStuck(f'stopped: job {job_id} has waited {int((now - queued_since) // 60)} minutes in line. This client cannot ask whether the workers show idle, so it stops '
                                                  'at the same time limit as the plugin client does. Nothing was cancelled or changed; tell the account owner.')
            else:
                queued_since = None
            if now - started > limit:
                return summary
            time.sleep(self.poll_seconds)

    def download(self, remote, local):
        os.makedirs(os.path.dirname(os.path.abspath(local)) or '.', exist_ok=True)
        self._call(['download', remote, '--local', local])
        if not os.path.exists(local):
            raise CardProblem(f'the card client said it downloaded {remote} but {local} is not there')
        return local

    def small_jobs(self):
        return []

    def wall_seconds(self):
        return self.seconds_used
