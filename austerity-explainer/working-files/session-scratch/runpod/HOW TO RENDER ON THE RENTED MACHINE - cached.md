# How to render on the rented machine - cached, on demand (for helpers, updated 21 October 04:45 UTC)

Use: python3 -I /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py ACTION ...
Actions: status, upload LOCAL [--remote PATH], run "COMMAND" [--cwd FOLDER] (prints a job id), job ID, wait ID [--limit SECONDS], download REMOTE [--local PATH].
A file keeps the same absolute path on the machine unless --remote is given. Folders are sent as one bundle.

## What happens when you call it
Every call first makes sure a machine is running. If one is, it is reused at once. If none is, the client starts one, trying in this order:
1. the store used last (normally Romania, EU-RO-1), with its cards in this order: RTX 4090, RTX PRO 4500, RTX 5090, RTX PRO 4000, L4, RTX 2000 Ada, RTX PRO 6000;
2. the other store (Iceland, EUR-IS-1), cards: RTX 4090, RTX PRO 6000, RTX 5090, RTX 4000 Ada, RTX PRO 4500, L4, RTX 2000 Ada;
3. any community card without a store: RTX A5000, RTX A4000, RTX 4000 Ada, RTX 3090, RTX A4500, RTX 4090, RTX A6000.
   Blender then installs itself from mirror sites (checked against the official checksum) and the base folders below are sent once (about 2-3 minutes in all).
All three steps are tried three times, 20 seconds apart. If nothing is free it stops with "NO CARD FREE": then render on this machine as before and say so.
Proven times: Romania store ready in 25 s; Iceland store ready in about 80 s; community card ready in about 160 s including Blender and the base folders.

A "store" is a permanent RunPod disk in one data centre. Blender and every file uploaded to it stay there between machines, so later starts are quick.
Files uploaded to a community machine (step 3) are lost when that machine ends.

## On the machine
* Blender: /workspace/blender/blender -b --disable-autoexec ... (no xvfb-run, no -t). EEVEE uses the card (log line "GPU BACKEND OPENGL | NVIDIA ...").
  Cycles uses the card (OptiX) on the stores; on some community hosts the card refuses Cycles and it runs on the processor cores instead.
* Already there (base folders): proc-work/street_wet/set_copy, tools, maps; the film project's assets/models/pit-village and paper-film/blender/pit-village
  (read-only copies; never write back into the film project).
* Typical speed on an RTX 4090: a 540 x 960 street picture 0.4-6 s after a 20 s warm-up; the full-size 1536 x 2730 street picture 2.4 s.

## Rules
* Upload every changed script or file before using it there. Render in batches (one run command that draws many pictures), not one call per picture.
* The machine ends itself after 30 minutes without a request; you do not stop or end machines yourself.
* Never print, copy or move anything in ~/.runpod, and never put ids or keys into notes, prompts or the repository.
* If a call fails with "no answer from the machine", run status once (it starts a fresh machine if the old one ended) and try again.
