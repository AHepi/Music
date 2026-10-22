# Rendering on rented cards (cheap Cycles, paid by the second)

What this is: why and how to draw a place's pictures on a rented graphics card instead of a slow computer, with the
film owner's rule for which renderer to use. It holds no key, no id and no address: the person's own settings are read at
run time and never written anywhere. Every number says what kind it is: **measured**, **judged** or **invented**.

## 1. The rule: which renderer

The film owner's rule, in plain words: Cycles looks much better, and it can be expensive, but it is worth it for scenes
where the lights are on (lamps, lit windows, lanterns, fires). When the lights are off, EEVEE is fine.

So: **Cycles where any lamp, lit window, lantern or fire is on; EEVEE otherwise.** `explainer-film-place renderer-for`
applies the rule and prints the reasons (a lamp other than the sun with energy, an emissive material that is lit, an
object with the glow role). `explainer-film-place render` uses it. If the scene is lit and no rented card is set up,
do not quietly fall back to EEVEE: say so, and draw only tiny Cycles previews here, or ask the person to set up a card.
The Scenario skills default to EEVEE for finals; the film owner's rule wins.

## 2. Why a rented card

- A shared computer without a graphics card is slow: on the one this plugin was made on, a small EEVEE picture of a
  heavily hooked scene took over 3 minutes (measured), and Cycles took 35 to 90 s a frame on 4 processor cores (measured).
- A rented card draws a 2400 x 1600 final in about 40 s (measured: 44.3 s and 39.7 s on an RTX 4090); previews at
  1200 x 800 and 96 samples take 6 to 10 s (measured).

## 3. How it works

A "serverless endpoint" on the person's own rented-card account: a worker (a card) starts only when a job is waiting,
does the job, and stops about 5 s after its last job. Billing runs per second while a worker is up, so nothing bills
while nothing is drawn. A cold worker wakes in 20 to 22 s; a warm one answers in under 1 s (measured). Several workers
may run at once, so several jobs can run side by side. A 4090 costs about US$1.10 an hour (measured, read 22 October
2026; read the live price before you rely on it). A bill once came out about 2.5 times the seconds of work and was not
explained, so never promise a cost from seconds alone.

## 4. The one-time set-up (the PERSON does this, in the provider's web pages)

1. An account, and a key that is allowed to create endpoints.
2. One network store (about 30 GB) in one data centre, holding Blender 5.2.2 and the uploaded files.
3. One endpoint on a plain Ubuntu image, with the start command from `place-kit/place_kit/render/worker/start.sh`;
   workers up to 3 (judged); idle timeout 5 s; job timeout about 1 hour; cards RTX 4090, then 5090, then 24 GB cards;
   the store mounted.
4. Run `copy_libraries.sh` (in the same folder) once on a machine that has the store, so Blender can draw there.

Warning: the job taker runs any shell command it is sent, so the key is the only lock. The plugin never exposes the
endpoint, and an agent may run `rent run` only with a job file, never a free-form command.

## 5. Settings at run time (never written down)

The client reads `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` (and `RENDER_STORE_FOLDER`, default
`explainer-film-places`) from the environment, or from the JSON file named by `RENDER_SETTINGS_FILE`
(`{"api_key": ..., "endpoint_id": ..., "store_folder": ...}`), which the person keeps OUTSIDE any repository. The client
never prints, logs or stores them, and refuses a settings file inside a git repository. Never write them into a note, a
prompt, a log or the repository. `explainer-film-setup` says whether they are set, never their values.

## 6. Daily use

- `explainer-film-place rent status | upload | run | job | wait | download | balance` and
  `explainer-film-place render --job JOB.json` (the job file format is in `place-kit/README.md`).
- Batch: one `run` that draws many pictures costs one wake-up; many tiny jobs cost many.
- Each job at most about 55 minutes (measured limit); split longer work. A folder goes up as one bundle.
- Write outputs into the store. Clear the remote output folder before a run (a stale picture once came back as a black road).
- Download only small JPG previews (under 400 KB) and JSON. Keep .blend, EXR and big PNG on the store: a local disk fills quickly.
- The client sends a name that says what it is (generic) and nothing about the person.

## 7. Before a long job

1. Check the balance (`rent balance`; it may say "unknown" when the provider cannot be asked). A nearly empty balance
   stalls every job while the workers show idle and the jobs wait.
2. Prove the card with one tiny Cycles picture (`cycles_check.py` in the worker folder: it must say OptiX).
3. If jobs wait more than 5 minutes while workers show idle, STOP and tell the person. Never purge the queue and never
   change the endpoint.
4. If `rent status` shows that no worker can start, say so; use the local fallback only for tiny previews.

## 8. Settings that matter

- Cycles: OptiX denoise, adaptive threshold 0.01, light tree on (judged). Previews 1200 x 800 at 96 samples, close-ups
  1600 x 1067, finals 2400 x 1600 at 512 (judged).
- EEVEE (when lights are off): shadow rays 4, shadow steps 16, 32 to 48 samples (measured). White speckle on wet ground
  was EEVEE's soft shadows, not the material. A render log with "Shadow buffer full" or "Could not allocate shadow atlas"
  means the picture cannot be judged.
- Save next to every picture: engine, device, samples, seed, view transform, exposure, size, camera, seconds, Blender
  version and the SHA-256 of the scene file. `render` writes this log for you.
