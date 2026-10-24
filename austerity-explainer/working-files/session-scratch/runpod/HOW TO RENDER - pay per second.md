# How to render on RunPod, paying per second (for helpers, from 21 October 21:30 UTC)

What this file is: the way to draw Blender pictures on rented RunPod graphics cards so the person pays only for the seconds a card is
actually working. It replaces the older always-on machine route (`HOW TO RENDER ON THE RENTED MACHINE - cached.md`), which keeps a
machine running, and billing, for 30 minutes after the last job.

Use: `python3 -I /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_serverless.py ACTION ...`
Actions (the same as the older client): `status`, `upload LOCAL [--remote PATH]`, `run "COMMAND" [--cwd FOLDER] [--timeout SECONDS]` (prints a
job id), `job ID`, `wait ID [--limit SECONDS]`, `download REMOTE [--local PATH]`.

## How it works
* A "serverless endpoint" on the person's RunPod account: a worker machine (a card) starts only when a job is waiting, does the job, and
  stops about 5 seconds after its last job. Billing runs per second while a worker is up, so there is no cost while nothing is drawn.
* Wake-up: about 20-25 s when no worker is warm; under 1 s when one is (a job sent within a few seconds of the last one).
* Cards: RTX 4090 first, then RTX 5090, then 24 GB cards (A5000, L4, 3090), all in the Romania data centre where the store is.
  Price on a 4090: US$1.10 an hour, about 0.03 US cents a second. At most 3 workers at once, so up to 3 jobs run side by side.
* Every worker mounts the permanent store. The same absolute paths as in this session work there: `/tmp/claude-0/...`, `/home/user/...`
  and `/workspace/...` all point into the store. Already on the store: Blender 5.2.2 (`/workspace/blender/blender`), the street copy
  (`proc-work/street_wet/set_copy`, `tools`, `maps`) and the film project's pit-village models. Anything else: upload it first.
* Each job may run at most about 55 minutes (`--timeout`, default 3300 s). Split longer work into several jobs.

## Proven (21 October)
* EEVEE uses the card: the wet street at 540 x 960, "today" 15.8 s (with warm-up) and "wet" 5.8 s; 31.6 s billed for the whole job.
* Cycles uses the card through OptiX: 540 x 960, 128 samples with denoising, 5.2 s.

## Rules
* Batch: one `run` command that draws many pictures costs one wake-up; many tiny jobs cost many.
* Blender there: `/workspace/blender/blender -b --disable-autoexec ...`. No `xvfb-run` and no `-t` needed.
* Upload every changed script or file before using it there (folders go as one bundle). Download results with `download`.
* Jobs are independent machines: do not rely on files in `/tmp` of the worker; write outputs into the store (any path under
  `/tmp/claude-0/...` is in the store).
* The person's renderer rule: Cycles where lamps, windows, lanterns or fires are lit; EEVEE when they are off.
* Never print, copy or move anything in `~/.runpod`; never put ids or keys in notes, prompts or the repository.
* If the endpoint fails (for example RunPod's own systems are down), say so; the older always-on route still exists as a fallback, but
  it bills while idle, so use it only when told.

## Switched off (22 October 15:27)
* The endpoint is switched fully off: most workers 0, so no job can start and nothing can bill. Jobs sent now wait in line forever.
* Only the main session switches it back on, with `runpod/diagnose/set_most_workers.py 3` (it reads ~/.runpod; helpers never run it). Before a
  long job, the main session also checks the account balance: with too little money, workers sit idle and jobs wait (this happened on 22 October,
  07:31 to 08:30).
* If your jobs wait in line for more than 5 minutes while the workers show idle, stop sending jobs and report it; never purge the queue or change
  the endpoint yourself.
