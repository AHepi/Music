# How to render on the rented machine (for helpers)

A rented RunPod machine with an NVIDIA RTX 4090 graphics card runs Blender 5.2.2 at /workspace/blender/blender. EEVEE (the film's plate renderer) uses the
card there: the first picture of a scene takes about 20-25 s (warm-up), each further picture in the same Blender run about 1 s (here on the shared 4-core
machine: 1.5-4 minutes). Cycles CANNOT use the card on this machine (CUDA fails on this host), but it has 25 processor cores (about 10 times this machine's 2 threads).

Tool: python3 -I /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client.py
  status                                  machine state, card, running jobs
  upload LOCAL_FOLDER_OR_FILE              copies to the SAME absolute path on the machine (folders go as one bundle: fast). Upload every script or file you changed before using it there.
  run "SHELL COMMAND" --cwd FOLDER         starts a job, prints its id (for Blender: /workspace/blender/blender -b --disable-autoexec FILE.blend --python SCRIPT -- ARGS; no xvfb-run, no -t)
  wait JOB_ID --limit 560                  waits up to 9.3 minutes and prints the state, return code and end of the log (call again if still running)
  job JOB_ID                               state now
  download REMOTE_FOLDER_OR_FILE --local LOCAL_PATH   brings results back (pictures to look at, numbers)

Already on the machine (same paths as here): proc-work/street_wet/set_copy, tools, maps; the film project's assets/models/pit-village and paper-film/blender/pit-village
(read-only copies; never change the real film project). Anything else must be uploaded first.

Rules: one Blender job at a time per helper; render in batches (many pictures in one Blender run, so the warm-up is paid once); keep measuring, sheets and
looking on this machine; never print, copy or move anything in ~/.runpod (the account key and token live there); do NOT stop the machine (the coordinator
does that). The machine costs about US$0.34 an hour while it runs. If the machine does not answer for 5 minutes, render here instead and say so.
