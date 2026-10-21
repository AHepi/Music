# RunPod set-up for rendering - findings (21 October, about 00:30)

What this file is: what was checked about moving the Blender rendering to a rented RunPod graphics-card machine, and the plan. Nothing was rented.

## Checked from this cloud session
* The official RunPod skills (`npx skills add runpod/runpod-plugins-official`) were installed into a scratch folder; the same skills were already loaded here as a plugin.
* No RunPod key is set (no RUNPOD_API_KEY, no ~/.runpod), runpodctl and flash are not installed (the installer site answers, so they can be installed).
* api.runpod.io and console.runpod.io answer over HTTPS from here.
* A direct SSH connection (port 22 to ssh.runpod.io) is blocked from here; a raw connection on port 443 to a public address works.
  So the machine would be driven through RunPod's HTTPS pod address (https://<pod-id>-<port>.proxy.runpod.net, at most 100 s per request): a small job
  server on the pod (upload scene files in pieces, start a render, ask for the status, download the pictures). runpodctl send/receive not tested.

## Recommended machine
* An RTX-class card with graphics (EEVEE needs OpenGL/EGL on the card): RTX 4090 (24 GB) first choice, RTX A5000 / A4000 / L4 cheaper; not A100/H100
  (no graphics engine; EEVEE may not run or runs slowly). Host CUDA 12.8 or newer, 16+ GB system memory (the full-size plate used about 7 GB), 50 GB disk.
* Set NVIDIA_DRIVER_CAPABILITIES=all when creating the pod so the container can use the card for graphics (EGL), install the Blender 5.2.2 Linux download
  and its graphics libraries, and prove EEVEE uses the card with one small render before moving any work. Risk: if EGL does not work in the container,
  EEVEE falls back to the slow software mode (then only Cycles benefits).
* Price: read the live price with the key before renting; stop the pod when idle; count it against the person's US$20 budget.

## What the person has to do
* Create a RunPod API key that may create and stop pods, and add it in this cloud environment's settings (environment menu in the session title bar,
  Edit, Network secrets / API credentials, or an environment variable) under the name RUNPOD_API_KEY. A NEW session picks it up.
* Before starting that new session, the working files must be in the repository (the big scene copies and renders in the scratch folder are not).

## What was built and tested (21 October, 02:08-03:30 UTC)
* **First machine (still running for the setts-and-rubbish job):** RTX 4090, community cloud, US$0.34 an hour, no permanent storage. EEVEE uses the card (street picture
  about 0.6 s after a 20 s warm-up); Blender's exact renderer (Cycles) could NOT use the card there (CUDA fails on that host) and runs on its 25 processor cores.
  Controlled through a small job server (render_job_server.py) at the machine's HTTPS address with a secret code; files go in one bundle (21 MB in 8 s).
  Two traps found: RunPod's address refuses Python's default identity (fixed by naming the client), and many small files are slow (fixed by bundles).
* **Cached on-demand set-up (for all later work), as the person asked: "rent per second and cache the config":**
  - a saved private template "blender-render-cached" (image, start-up, job server, port; ids in ~/.runpod/cached_machine.json, never in the repository);
  - a permanent 30 GB network volume "blender-render-cache" in EU-RO-1 (Romania) holding Blender 5.2.2 and every uploaded file (about US$2 a month, about 7 cents a day);
  - the client render_client_cached.py starts a machine from the template on the volume when one is needed (card order: RTX 4000 Ada about US$0.28 an hour,
    then RTX 4090 about US$0.89 an hour, L4, RTX 5090; network volumes need RunPod's secure cloud, which costs more per hour than community), and the job server
    ends its own machine after 15 minutes without a request (using the machine's own key), so the account pays per second while work is done;
  - on the store the paths /tmp/claude-0 and /home/user point into the volume, so files keep the same absolute paths as here.
  Tested: ready 25 s after asking (Blender already on the store); EEVEE and Cycles (OptiX) both use the RTX 4090 there; street pictures at 540 x 960 in 0.4-6 s,
  the full-size 1536 x 2730 street picture in 2.4 s (about 20 minutes on the shared 4-core machine here). Two set-up mistakes of mine cost two broken starts
  (the job server started before its file was written; a text replacement hit two places): both fixed in the template.

## The finished workflow (21 October, 03:40-04:45 UTC), after "Don't worry about runpod budget. Just find a workflow that works"
Problem found: a RunPod store sits in one data centre, and sometimes that data centre has no free card. So the client now has three routes, tried in order:
1. **Romania store** (EU-RO-1): the store used last goes first. Cards in order of how often they were free: RTX 4090, RTX PRO 4500, RTX 5090, RTX PRO 4000, L4,
   RTX 2000 Ada, RTX PRO 6000. Tested: ready 25 s after asking; an RTX 2000 Ada (the cheapest card) drew the wet street in 6.6 s.
2. **Iceland store** (EUR-IS-1): a second 30 GB store with its own copy of Blender and the base folders. Tested: ready in about 80 s the first time
   (Blender came from a mirror site), base folders sent once and kept; wet street drawn in 8.4 s on an RTX 4090.
3. **Community card, no store**: RTX A5000, A4000, 4000 Ada, 3090, A4500, 4090, A6000. Blender installs itself from mirror sites (the official Blender site
   refused some RunPod hosts and was very slow from Iceland, about 9 KB a second), checked against the official checksum; the base folders are sent once.
   Tested with both stores switched off: ready in 157 s on an RTX A5000 including Blender and the base folders; today 12.2 s, wet 4.7 s; 181 s in all.
Each route is tried three times, 20 s apart; if no card is free anywhere the helper is told to render here instead. Machines now end themselves after
**30 minutes** without a request (was 15), so short pauses between helper steps do not cost a fresh start.

Traps found and fixed in this round: a missing setting after an edit (the piece size); base folders were only sent by the call that created the machine
(now tracked per store); the community route failed when the official Blender download was refused (now mirror sites in turn, with a speed limit so a slow
site is dropped after 15 s); many community starts failed with "no instances available" (now three passes).

Not tested: a store's data centre with no card at all for a long time (the client would fall to Iceland, then community, which was proven); Cycles on the
community A5000 card (only EEVEE was drawn there); two helpers asking for a machine at the same moment (a lock file makes the second wait for the first).
