# Batched rounds and card time (one sweep, then look; about 10 different variations in one batch)

What this is: the rule for trying things on a place you are building, and the two tools that keep it: `explainer-film-place variations`
(a batch of about 10 measurably different variations of one change, drawn small and quick on up to 3 rented cards at once, on ONE
labelled sheet) and `explainer-film-place card-time` (the ledger of every card second and each helper's allowance). A **variation** is
one way the change could look: the saved scene with some settings changed. Every number says what kind it is: **measured**, **judged**
or **invented**.

## 1. A concrete example first: what went wrong in the garden

In the Japanese garden job the helpers spent US$10.89 of rented-card time (from the job's own report). The finished pictures cost about
5 cents. The rest went on trying things ONE small change at a time: the whole scene was rebuilt for every small test, test pictures were
drawn at full size and full quality, one tree was tried in about 25 variations one after another, and nothing limited anyone's card time.

The same work as a batch: write every change you plan; make them all in one sweep; then, for the tree, write about 10 variations whose
settings are far apart (branch count, lean, leaf amount), check them for free on this computer (the scout), send them in ONE batch
(3 cards at once, 600 x 400 pictures), look at ONE sheet, pick the best one or combine two, and draw at most ONE more batch around the
pick. That is 2 looks instead of 25. The person's own words for it: "Do one full sweep of changes, then look. Instead of one small change,
then check. Maybe even batch according to variations. So maybe 10 variations that are measurably different for each asset change."

## 2. The rule (every helper, every place, every set, every prop)

1. **Plan every change first, make them all in one sweep, then look once.** Not: change one thing, look, change the next.
2. **Build the scene once and save it.** A batch starts from the saved, finished scene. Never rebuild the scene to try one setting.
3. **For each change to a thing, draw about 10 measurably different variations in ONE batch.** Spread over the cards (up to 3 jobs at
   the same time). Look at the one sheet. Pick one or combine two or three. At most ONE more batch for that change (the tool counts
   batches and refuses a third).
4. **Small quick pictures until the end:** 600 x 400, EEVEE or low-sample Cycles by the renderer rule (the tool does this for you).
5. **Full-size pictures are drawn ONCE, at the very end,** from the last audited file (`render --finals`, in views that say
   `"kinds": ["final"]`).
6. **Stay inside your card-time allowance and report the card seconds you used** (builder 10 minutes, fixer 5, integrator 10, renderer 10,
   checker 3, planner 0: judged). The tool refuses past it.

## 3. Doing it, step by step (example: cracks and chips on the canal lock's brick wall and timber gate)

1. Finish and save the scene (`finish --save-as lock-finished.blend`; the pass and the audit come first, see `the-required-steps.md`).
2. Make the file of variations. Let the tool spread the settings for you, so ten variations are far apart by construction:
   ```
   explainer-film-place variations make --keys dials.cracks_and_chips.crack_density dials.cracks_and_chips.crack_width_metres \
     dials.cracks_and_chips.chip_amount --range dials.cracks_and_chips.crack_density 0.5 1 \
     --count 10 --change "cracks on the lock walls and gate" --scene lock-finished.blend --settings place-settings.json \
     --cameras "Camera A" "Camera B" --out cracks-variations.json
   ```
   (`--range KEY LOW HIGH` spreads one setting only over the part of its range that shows. Measured on the lock's first card batch: the five
   variations with a crack density under 0.5 came out nearly the same as each other, because below about 0.5 the cracks are gone, so half of that
   batch told one thing five times.) Or write the file by hand (section 5). `explainer-film-place variations keys` lists every setting a variation
   may change, with its range. The file this made for the real lock (seed 12) is `${CLAUDE_PLUGIN_ROOT}/kit/place-kit/data/examples/canal-lock-cracks-variations.json`.
   The names it makes show each of the first two settings as a percent of its whole range: `crackwid25` is a crack width a quarter of the
   way from 0.002 to 0.05 m (0.014 m), not 25 mm; `cover5` is a cover of 0.05.
3. **The free scout:** `explainer-film-place variations scout cracks-variations.json`. It draws the very same variations HERE, on this
   computer, tiny (240 x 160) and with few samples, in one job: about 40 seconds for the small lock, and no card seconds. It is not a batch.
   Look at its sheet with the Read tool. It says which variations would come out nearly the same as the saved scene or as each other.
   If fewer than 10 would show, spread wider (another `--range`, another setting) and scout again: it is free. It also names the pairs
   that are measurably (not always visibly) different: "may not be visible" means only a faint, even shift, almost no pixel moved
   by much. Those are kept; if you cannot tell them apart on the sheet, take them out of the file before you send it.
4. Look at the plan; it draws nothing and costs nothing: `explainer-film-place variations plan cracks-variations.json --helper builder-walls --role builder`
   (`--helper` takes a short name for this helper, such as `builder-walls`; never a person's name).
   It uses the scout by itself: what the scout found nearly the same is dropped BEFORE drawing, with a sentence for each. It also drops
   variations whose settings are too close, says how the rest are split into jobs, and the card seconds it expects (an estimate, not a bill).
5. Draw the batch: `explainer-film-place variations run cracks-variations.json --where rented --helper builder-walls --role builder`.
   It waits for the cards (about 1 to 3 minutes for a small place), so give the command a long time limit (10 minutes). If it is cut off
   anyway, nothing is lost: the jobs were written into the ledger when they went out, and `explainer-film-place variations collect RUN-FOLDER`
   finishes the batch without sending anything again. (`--where local` draws here, one job after another: for tiny scenes and tests only;
   this computer is slow. A run with `--where local` still counts as one of your two batches for that change; the free scout does not. So
   do not try a batch here first and then send it to the cards: scout it, then send it.)
6. Look at the sheet with the Read tool (the path is printed; it is one JPG under 400 KB). Pick one variation, or combine two or three.
7. If you are not sure, ONE more batch around the pick(s): `explainer-film-place variations refine cracks-variations-run/variations-result.json --pick NAME NAME`,
   then `scout`, `plan` and `run` the new file. The rule allows no third batch.
8. Put the pick into the real stage file or settings (a number in `place-settings.json`, or the script hook's numbers in the stage file),
   run the pass once more, audit last. Full-size pictures only now, once.

When NOT to scout: when this computer needs more than a few minutes to open and draw the scene (a big place). Then send the batch without it;
the card's own check after drawing still says which variations came out nearly the same.

## 4. What the tools do for you (so you do not have to)

- **The scout checks the pictures BEFORE the card.** Measured on 23 October 2026: the two real card batches of 10 on the canal lock (moss, and
  cracks and chips; 600 x 400, 24 samples) were drawn again as scouts here (240 x 160, 8 samples, 37 to 39 seconds each). With the scout's own limits
  (`place_variations.scout_picture_mean_difference_min` 0.75 of 255 and `place_variations.scout_picture_changed_share_min` 0.3 percent: tiny
  low-sample pictures differ more than big ones) the scouts called exactly the same 22 pairs nearly the same as the cards did, and no other. In the
  moss batch, 5 of the 10 variations had shown nothing on the card (moss cover under about 0.5 does not show from those two cameras), and the scout
  named the same 5. Then the batch of section 3 was made with `--range`, scouted (two first files each had one pair too alike and never went
  to a card; the third scouted clean) and sent: on the cards all 10 came out measurably different, in 178 card seconds (about US$0.05, an
  estimate), wake-ups 0.8, 19.9 and 23.3 seconds. One scene only, and the margin was thin for cracks, so the card's own check after drawing still
  runs on every batch.
- **Checks the settings BEFORE drawing.** A variation is dropped when no setting of it is at least `place_variations.settings_difference_min_share`
  (8 percent: invented) of that setting's range away from the saved scene or from an earlier variation. The sentence says which one and why.
  Example: moss cover 0.50 and 0.55 are 5 percent apart, so the second is dropped; 0.50 and 0.90 are 40 percent apart. A scout also reads what the
  saved scene really has for every dial the batch varies (the sheet shows it under the baseline), and this check then compares with that instead of
  the dial's default.
- **amount and master scale the saved scene.** `amount.<layer>` 1 is the layer as saved, 0 is off, 2 is twice as strong (0 to 2,
  `place_variations.amount_scale_max`); `master` does the same for every layer at once. So a batch can try more wear as well as less.
- **Splits the variations** over up to `place_render.workers_max` (3) card jobs, at least `place_variations.min_variations_per_job` (3) in each, so one
  wake-up of a card (20 to 25 seconds: measured) is shared. The saved scene is drawn too, as the baseline, in the job that has the fewest.
- **Each job opens the scene once.** For each variation it applies the settings, draws the small pictures through every camera, then puts the
  values back and checks them with a fingerprint; a variation with a script hook, or one whose reset did not come back exact, makes the job reopen
  the scene instead, so one variation can never leak into the next. The scene is never saved. `--check-reset` draws the baseline again at the
  end of its job to prove it (one more small picture).
- **Checks AFTER drawing that the pictures differ.** Every pair of pictures is compared pixel by pixel; a pair that came out nearly the same through
  EVERY camera is flagged ("nearly the same as #3"), and a variation nearly the same as the baseline is flagged "does not show in these cameras"
  (its settings may be right, but the change cannot be seen from where the cameras are, or it changes nothing in this scene).
- **Measurably (not always visibly) different.** A pair counts as different when, in some camera, the mean difference OR the share of changed
  pixels reaches its limit. A faint, even tint passes on the mean alone. Example (a tiny wall, scout 240 x 160): one variation against the saved
  scene had a mean difference of 0.68 and 0.97 of 255 in the two cameras, but only 0.02 and 0.05 percent of its pixels changed by more than 8
  levels; by eye the two look the same. Such a pair is named "may not be visible" on the sheet and in the report: it is kept, and you judge it by
  looking. The rule itself was kept (measured): calling a pair different only by its changed pixels would have changed the verdict on 7 pairs
  of the real moss batch, and the scout would then have missed one of them.
- **Makes ONE contact sheet.** The baseline first, then every variation: its name, its settings in plain words and its measures, and at the bottom the
  card seconds and the wake-up times. The measures are made here from the small pictures after they come back (they cost no card seconds), against
  the baseline:
  - `range`: the 5th and 95th percentile of brightness and their gap (a flat picture has a small gap);
  - `detail`: fine contrast, and in brackets how far it moved from the baseline;
  - `colour shift`: how far the average colour moved from the baseline, in Lab units (0 = the same; about 2 is the least a person sees);
  - `sat`: the change in colourfulness;
  - `squint`: how well the big shapes and the light hold, 1.0 = the same as the baseline (the house target `place_measures.squint_target` is 0.92:
    a variation under it changed the big shapes or the light a lot).
  These are measured. Whether a variation looks right is judged: you decide, by looking.

## 5. A variations file by hand (settings, or a script hook for anything else)

```
{ "change": "moss and the lean of the lock gate",
  "scene": "lock-finished.blend", "settings": "place-settings.json", "cameras": ["Camera A"],
  "variations": [
    { "name": "moss-light", "set": { "amount.moss_and_algae": 0.4 } },
    { "name": "moss-thick-damp", "set": { "amount.moss_and_algae": 1.8, "dials.moss_and_algae.cover": 0.9, "state": "damp" } },
    { "name": "lean-8", "script": "hooks/lean.py", "args": { "lean_degrees": 8 }, "ranges": { "lean_degrees": [0, 20] } } ] }
```
- `set` takes the dials of the wear layers (`amount.<layer>`, `dials.<layer>.<dial>`), `master`, `state` and `look`.
- A shape (a tree's branches, the number of boards, a new prop) goes in a small script hook: a Python file with `apply(variation)` that runs inside
  Blender on the freshly opened scene; its numbers go in `args`, with their range in `ranges` so the tool can tell whether two are far enough apart
  (template: `kit/place-kit/data/templates/variation_hook.py`).
- One batch may try several kinds of change at once, as above (the person: "they can test multiple different types of changes at once"); the
  sheet shows which kind moved the picture.
- Names: 1 to 40 characters, lower-case letters, digits, `-` and `_`. `baseline` is reserved.
- About 10 variations (`place_variations.batch_size`; at least 3 and at most 16). Fewer than 3 is not a batch: draw one picture. More than 16 is
  wandering, and the tool refuses it unless you write a reason.

## 6. Card time: the ledger and the allowance

Every job sent to a rented card is written into one ledger file (one line for each job: who, what, work seconds, wake-up seconds, the idle tail of about
5 seconds). **Card seconds = work + wake-up + idle tail**, counted cautiously so a number is never too small. The price shown (about US$0.0003 a second on a
4090) is an estimate from the hourly price of the day, never a bill.

- A job is written twice: a "sent" line the moment it goes out (it counts at its estimate) and its billed seconds when it is finished (then only those
  count). So a command that is cut off still counts the card time it started.
- Say who you are on every command that can use a card: `--helper NAME --role builder|fixer|integrator|renderer|checker|planner`, where NAME is a
  short name for this helper, such as `builder-walls` (never a person's name)
  (or the environment `PLACE_HELPER`, `PLACE_HELPER_ROLE`, and `PLACE_CARD_LEDGER` for the file). Use the ledger file you were given: all helpers of one run use the same one.
- `explainer-film-place card-time show` prints the ledger and what each helper has left. `card-time check --estimate-seconds 200` says whether a step would fit.
- The tool WARNS at 80 percent of your allowance, REFUSES a step that would pass it (nothing is sent), and refuses a third batch for one change.
  A scout is free and is not counted as a batch. A run with `--where local` IS counted as one of the two batches (it uses no card seconds,
  but it is a look).
- Over the allowance only with `--over-allowance "a reason of at least 15 letters"`: the reason is written into the ledger and the person reads it, and even then
  nothing may pass the allowance by more than half again. Past that, stop and tell the person.
- The whole job has a total too (`place_card_time.team_total_minutes`, 60 minutes: judged); only the person raises it (`card-time start --team-minutes N`).
- A job that waits in line more than 5 minutes while workers show idle STOPS the batch with a plain sentence. Never purge the queue and never change the endpoint.
- Never put a key, an endpoint id or any personal detail into a file. The clients read the person's settings when they run.

## 7. When NOT to use a batch

- One setting, one number: draw one small picture (or none: read the audit).
- A FAIL line of the audit or the construction check: fix it; the checks are the look.
- A pure check of structure (is the plank carried?): no picture at all.
- The shot checker's order (the camera first, then the props, then the light; fix problem 1 and run it again): it is a measured check that runs
  here and costs no card time, so one change at a time is right there.

## 8. What to report

The number of batches, the variations asked, dropped before drawing (by their settings, and by the scout) and flagged after drawing, the card seconds used
(from the ledger), the wake-up times, which variation you picked and why (measured or judged), and what you did NOT test.
