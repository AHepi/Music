# Batched rounds and card time (one sweep, then look; about 10 different versions in one batch)

What this is: the rule for trying things on a place you are building, and the two tools that keep it: `explainer-film-place variations`
(a batch of about 10 measurably different versions of one change, drawn small and quick on up to 3 rented cards at once, on ONE
labelled sheet) and `explainer-film-place card-time` (the ledger of every card second and each helper's allowance). Every number says
what kind it is: **measured**, **judged** or **invented**.

## 1. A concrete example first: what went wrong in the garden

In the Japanese garden job the helpers spent US$10.89 of rented-card time (from the job's own report). The finished pictures cost about
5 cents. The rest went on trying things ONE small change at a time: the whole scene was rebuilt for every small test, test pictures were
drawn at full size and full quality, one tree was tried in about 25 versions one after another, and nothing limited anyone's card time.

The same work as a batch: write every change you plan; make them all in one sweep; then, for the tree, write about 10 versions whose
settings are far apart (branch count, lean, leaf amount), send them in ONE batch (3 cards at once, 600 x 400 pictures), look at ONE
sheet, pick the best one or combine two, and draw at most ONE more batch around the pick. That is 2 looks instead of 25. The person's
own words for it: "Do one full sweep of changes, then look. Instead of one small change, then check. Maybe even batch according to
variations. So maybe 10 variations that are measurably different for each asset change."

## 2. The rule (every helper, every place, every set, every prop)

1. **Plan every change first, make them all in one sweep, then look once.** Not: change one thing, look, change the next.
2. **Build the scene once and save it.** A batch starts from the saved, finished scene. Never rebuild the scene to try one setting.
3. **For each change to a thing, draw about 10 measurably different versions in ONE batch.** Spread over the cards (up to 3 jobs at
   the same time). Look at the one sheet. Pick one or combine two or three. At most ONE more batch for that change (the tool counts
   batches and refuses a third).
4. **Small quick pictures until the end:** 600 x 400, EEVEE or low-sample Cycles by the renderer rule (the tool does this for you).
5. **Full-size pictures are drawn ONCE, at the very end,** from the last audited file (`render --finals`, in views that say
   `"kinds": ["final"]`).
6. **Stay inside your card-time allowance and report the card seconds you used** (builder 10 minutes, fixer 5, integrator 10, renderer 10,
   checker 3, planner 0: judged). The tool refuses past it.

## 3. Doing it, step by step (example: moss on the canal lock's brick wall and timber gate)

1. Finish and save the scene (`finish --save-as lock-finished.blend`; the pass and the audit come first, see `the-required-steps.md`).
2. Make the file of variations. Either let the tool spread the settings for you, so ten versions are far apart by construction:
   ```
   explainer-film-place variations make --keys amount.moss_and_algae dials.moss_and_algae.cover dials.moss_and_algae.clump_size_metres \
     --count 10 --change "moss on the lock walls and gate" --scene lock-finished.blend --settings place-settings.json \
     --cameras "Camera A" "Camera B" --out moss-variations.json
   ```
   or write the file by hand (section 5). `explainer-film-place variations keys` lists every setting a variation may change, with its range.
3. Look at the plan; it draws nothing and costs nothing: `explainer-film-place variations plan moss-variations.json --helper YOUR-NAME --role builder`.
   It says which variations are too close to each other and are dropped BEFORE drawing, how they are split into jobs, and the card seconds
   it expects (an estimate, not a bill).
4. Draw the batch: `explainer-film-place variations run moss-variations.json --where rented --helper YOUR-NAME --role builder`.
   (`--where local` draws here, one job after another: for tiny scenes and tests only; this computer is slow.)
5. Look at the sheet with the Read tool (the path is printed; it is one JPG under 400 KB). Pick one version, or combine two or three.
6. If you are not sure, ONE more batch around the pick(s): `explainer-film-place variations refine moss-variations-run/variations-result.json --pick NAME NAME`,
   then `plan` and `run` the new file. The rule allows no third batch.
7. Put the pick into the real stage file or settings (a number in `place-settings.json`, or the script hook's numbers in the stage file),
   run the pass once more, audit last. Full-size pictures only now, once.

### A free scout first, when you do not know which settings show

A concrete case from the real proof (canal lock, 23 October 2026): the first batch of 10 moss versions drew 10 versions whose settings were far apart, but 5 of the 10 pictures came out nearly the same as the saved scene (moss hardly shows
from those two cameras at 600 x 400), so half of the batch told nothing. A scout would have said so for free: write ONE extreme version of each change you might try (every dial at its high end, and `master` 0 for no wear at all), and draw it
here, tiny, one job: `explainer-film-place variations run scout.json --where local --size 300x200 --samples 8 --jobs 1 --change "scout"` (7 versions through 2 cameras took 36 seconds on this computer, and no card seconds). The sheet shows which changes
move the picture (a colour shift of about 2 or more, or a detail change) in YOUR cameras. Then spend the card batch on a change that shows. In a scout of that kind on the same lock (extremes drawn at 300 x 200), grime moved the colour most (a shift of 2.7), then wetness (1.7), weathering (1.5), edge wear (1.2) and cracks (a shift of only 0.6, but the cracks themselves are plain to see and the detail measure rose 0.4); dirt hardly moved it (0.8). Moss was not in that scout.

## 4. What the tool does for you (so you do not have to)

- **Checks BEFORE drawing that the versions differ.** A version is dropped when no setting of it is at least `place_variations.settings_difference_min_share`
  (8 percent: invented) of that setting's range away from the saved scene or from an earlier version. The sentence says which one and why.
  Example: moss amount 0.50 and 0.55 are 5 percent apart, so the second is dropped; 0.50 and 0.90 are 40 percent apart.
- **Splits the versions** over up to `place_render.workers_max` (3) card jobs, at least `place_variations.min_variations_per_job` (3) in each, so one
  wake-up of a card (20 to 25 seconds: measured) is shared. The saved scene is drawn too, as the baseline, in the job that has the fewest.
- **Each job opens the scene once.** For each version it applies the settings, draws the small pictures through every camera, then puts the
  values back and checks them with a fingerprint; a version with a script hook, or one whose reset did not come back exact, makes the job reopen
  the scene instead, so one version can never leak into the next. The scene is never saved. `--check-reset` draws the baseline again at the
  end of its job to prove it (one more small picture).
- **Checks AFTER drawing that the pictures differ.** Every pair of pictures is compared pixel by pixel; a pair that came out nearly the same through
  EVERY camera is flagged ("nearly the same as #3"), and a version nearly the same as the baseline is flagged "does not show in these cameras"
  (its settings may be right, but the change cannot be seen from where the cameras are, or it changes nothing in this scene).
- **Makes ONE contact sheet.** The baseline first, then every version: its name, its settings in plain words and its measures, and at the bottom the
  card seconds. The measures are made here from the small pictures after they come back (they cost no card seconds), against the baseline:
  - `range`: the 5th and 95th percentile of brightness and their gap (a flat picture has a small gap);
  - `detail`: fine contrast, and in brackets how far it moved from the baseline;
  - `colour shift`: how far the average colour moved from the baseline, in Lab units (0 = the same; about 2 is the least a person sees);
  - `sat`: the change in colourfulness;
  - `squint`: how well the big shapes and the light hold, 1.0 = the same as the baseline (the house target `place_measures.squint_target` is 0.92:
    a version under it changed the big shapes or the light a lot).
  These are measured. Whether a version looks right is judged: you decide, by looking.

## 5. A variations file by hand (settings, or a script hook for anything else)

```
{ "change": "the maple tree",
  "scene": "lock-finished.blend", "settings": "place-settings.json", "cameras": ["Camera A"],
  "variations": [
    { "name": "moss-light", "set": { "amount.moss_and_algae": 0.3 } },
    { "name": "moss-thick-damp", "set": { "amount.moss_and_algae": 1.0, "dials.moss_and_algae.cover": 0.9, "state": "damp" } },
    { "name": "lean-8", "script": "hooks/lean.py", "args": { "lean_degrees": 8 }, "ranges": { "lean_degrees": [0, 20] } } ] }
```
- `set` takes the dials of the wear layers (`amount.<layer>`, `dials.<layer>.<dial>`), `master`, `state` and `look`.
- A shape (a tree's branches, the number of boards, a new prop) goes in a small script hook: a Python file with `apply(variation)` that runs inside
  Blender on the freshly opened scene; its numbers go in `args`, with their range in `ranges` so the tool can tell whether two are far enough apart.
- Names: 1 to 40 characters, lower-case letters, digits, `-` and `_`. `baseline` is reserved.
- About 10 versions (`place_variations.batch_size`; at least 3 and at most 16). Fewer than 3 is not a batch: draw one picture. More than 16 is
  wandering, and the tool refuses it unless you write a reason.

## 6. Card time: the ledger and the allowance

Every job sent to a rented card is written into one ledger file (one line for each job: who, what, work seconds, wake-up seconds, the idle tail of about
5 seconds). **Card seconds = work + wake-up + idle tail**, counted cautiously so a number is never too small. The price shown (about US$0.0003 a second on a
4090) is an estimate from the hourly price of the day, never a bill.

- Say who you are on every command that can use a card: `--helper NAME --role builder|fixer|integrator|renderer|checker|planner`
  (or the environment `PLACE_HELPER`, `PLACE_HELPER_ROLE`, and `PLACE_CARD_LEDGER` for the file). Use the ledger file you were given: all helpers of one run use the same one.
- `explainer-film-place card-time show` prints the ledger and what each helper has left. `card-time check --estimate-seconds 200` says whether a step would fit.
- The tool WARNS at 80 percent of your allowance, REFUSES a step that would pass it (nothing is sent), and refuses a third batch for one change.
- Over the allowance only with `--over-allowance "a reason of at least 15 letters"`: the reason is written into the ledger and the person reads it, and even then
  nothing may pass the allowance by more than half again. Past that, stop and tell the person.
- The whole job has a total too (`place_card_time.team_total_minutes`, 60 minutes: judged); only the person raises it (`card-time start --team-minutes N`).
- A job that waits in line more than 5 minutes while workers show idle STOPS the batch with a plain sentence. Never purge the queue and never change the endpoint.
- Never put a key, an endpoint id or any personal detail into a file. The clients read the person's settings when they run.

## 7. When NOT to use a batch

- One setting, one number: draw one small picture (or none: read the audit).
- A FAIL line of the audit or the construction check: fix it; the checks are the look.
- A pure check of structure (is the plank carried?): no picture at all.

## 8. What to report

The number of batches, the variations asked, dropped before drawing and flagged after drawing, the card seconds used (from the ledger), which version you picked and
why (measured or judged), and what you did NOT test.
