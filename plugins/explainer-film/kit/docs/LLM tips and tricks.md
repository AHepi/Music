# LLM tips and tricks: making the next explainer film

What this is: the short rules a model should follow when it makes the next film with this kit. They were
learned the hard way over 35 logs of the austerity explainer (chapter 1, chapter 2, the pit village tests,
the Works and the checkout). Each tip names the tool that checks it, so you run the tool instead of
searching by hand. Where no tool can check it, the tip says **judgement: ask a critic**.

How to read it:
- **Preflight stages.** `explainer-film-preflight STAGE` runs the checks for one stage of the work and
  writes one report. The nine stages are in the table below. Its `--help` says exactly what each stage
  runs and which files it needs; if it skips a tool because a file is missing, run that tool yourself.
- **Commands** such as `calculators/plan_shot.py` run from the kit folder (the folder `explainer-film-setup`
  made). Every tool answers `--help`, prints a plain report, takes `--json`, `--out` and `--report`, and ends
  by listing the house numbers it used. The calculators' own guide is `calculators/README.md`.
- **House numbers** live in one table, `film-settings.json`, and nowhere else. Each one says what kind it is:
  **measured** (taken from a recording, a render or a bill), **judged** (chosen by people or critics from
  evidence), **invented** (a starting guess nobody has tested) or **worked out** (follows from other numbers
  by a sum). `python3 calculators/settings.py show SECTION` prints them.
- Numbers in brackets such as (lesson 137) or (log 34) point to the austerity explainer's project notes,
  where the full story is. You don't need them to follow the tip.

## The preflight stages

| Stage | When | What it runs | What it guards |
|---|---|---|---|
| `script` | before recording | `lint_script.py before`, the estimated timeline, the voice's credits and dollars, the spend ledger | recording the narration |
| `record` | after recording | `lint_script.py after`, `sound_gates.py voice` | using the recordings |
| `shots` | before building or drawing a place's views | `place_facts.py check`, `plan_shot.py`, `view_audit.py`, `plan_effects.py wind`, `plan_lights.py plan`, `plan_states.py plan`, each view's check file | building and drawing the views and plates |
| `place` | after a place is built, before its views are drawn (order: `shots`, build, `place`, `plates`) | `place_audit_check.py check` (roles, treatments, layer amounts, normal maps, UVs, displacement, construction, scale, keep-out, renderer; film frame, world, sun, lettering and the object count), a stale-audit check against the scene file, and when given `picture_measures.py check` and `place_audit_check.py fresh` | drawing the place's views and plates (a flat, clean or floating place is drawn again) |
| `plates` | before paying for paintings | `plan_lights.py render-log`, the shot checker's report (new problems only), `paint_request.py preflight` and `price`, `model_lint.py`, the spend ledger, the place audit again when a scene is named (a LOOK says so when none is), and LOOKs for a Cycles plate (the painting checks were tuned on EEVEE plates) and for one place drawn with two engines | asking the painter |
| `paint` | after each painting arrives | `after_painting.py check` (with its LOOKs: bottom fifth, clouds, how much of the ground's brightness arrives with `--toe`; a behind painting's "pale patch" FAILs) | using the painting |
| `pages` | while building pages | `plan_page_timing.py check`, `check_page_layout.mjs`, `camera_audit.py`, `plan_effects.py lint`, all from `page_events.mjs`'s events | filming the pages |
| `film` | before filming | a critique newer than every page file, each finding fixed or accepted, with a history critic among its critics (a FAIL without one, unless accepted); a passed `pages` report newer than every page file; `plan_budget.py filming` | filming the chapter |
| `finish` | after finishing | `sound_gates.py` loudness, length and alignment; `find_jumps.py` with the planned cuts; `plan_budget.py push`; a fresh helper's critique of the filmed clip in motion (`--clip-critique`, required: newer than the film, no must-fix finding left open) | sending or publishing |

How to run it:
- `explainer-film-preflight STAGE --project FILM_FOLDER [inputs]`. Name a film's files once in a preflight
  plan (`FILM_FOLDER/preflight-plan.json`; `explainer-film-preflight --example-plan` prints one) instead of
  typing them every time. `explainer-film-preflight --list` lists every stage's inputs and the tool that makes
  each.
- Reports go to `FILM_FOLDER/preflight-reports/`, in plain words and as JSON, with every tool's own output
  beside them. Exit 0 is a pass (perhaps with things to look at), 1 a failure, 2 a missing input: the report
  names the file to make and the tool that makes it.
- Only new failures block. A problem accepted on purpose (in a check file's or the place facts' `accepted`
  list, or the plan's, each with who and the date) is reported as known, and fails again only if it has grown
  worse than when it was accepted.
- `explainer-film-preflight STAGE --gate` answers, without running anything, whether the newest report of
  that stage passed and its inputs are unchanged since. Use it right before a paid or long step.

## 0. How to work

1. Run the stage's preflight first and read its whole report before you do anything by hand.
   *Check:* `explainer-film-preflight STAGE`.
2. Compute before you render. Where a thing lands, how big it comes out, how far back the camera may stand
   and how long a slide may be are sums that answer in a second, before any picture is drawn.
   *Check:* `calculators/frame_geometry.py project | boxes | reach | slide`, `calculators/plan_shot.py`.
3. Make one change, then measure again. A camera change moves everything, so fix in this order: the camera,
   then the props, then the light. *Check:* the shot checker lists problems in that order
   (`paper-film/tools/check-shot.sh`); fix problem 1 only and run it again. (This is for measured checks that run here and cost no card time; a look at a picture follows the batch rule: one sweep, then one look.)
4. Quote measured numbers in every report ("reaches 0.71 down", "-15.0 LUFS"), never "looks fine". Say what
   you did not measure (nobody watched it at full speed; nobody listened).
5. Never trust a single still. Page turns, one-frame pops, snapping fades and smoke only show between
   frames. *Check:* `paper-film/tools/check_page_layout.mjs` (stage `pages`), `paper-film/tools/find_jumps.py`
   (stage `finish`).
6. Test a tool's advice by following it once, then measure again: reading advice is not testing it. Once,
   following the checker's prop advice dropped the lantern to the pavement (lesson 108).
7. Read the render log before judging any light. "Shadow buffer full" or "Could not allocate shadow atlas"
   means the picture cannot be judged. *Check:* `calculators/plan_lights.py render-log LOG`.
8. For your own 3D shots, trust the 3D facts (the place facts and `paper-film/blender/shot_facts.py`) over a
   line finder run on a picture. `paper-film/tools/measure_composition.py` is only for pictures you did not
   build.
9. Before calling a problem a failure, read the view's kinds of shot and its accepted list. A crowd, an
   overview, an interior and a dark subject relax some still-life rules on purpose.
   *Check:* `calculators/settings.py profile crowd dark_subject`; the check file's `kind_of_shot` and
   `accepted`.
10. Treat an invented number as a guess, and say so whenever a result rests on one.
    *Check:* `calculators/settings.py show SECTION` prints each number's kind.
11. Don't edit a file while helpers are checking it. Every report names its tool version and settings, so
    two helpers can tell whether they checked the same thing.
12. Ask the person only about what they want, risk or money. Make routine technical choices yourself.
13. Prove "unchanged" with several draws, and run the control before you blame a change. Some pictures come out two
    slightly different ways from one run to the next: the house sample at 20 s differed in 7.7 percent of its dots, by
    at most 7 of 255, with nothing changed, and the unchanged old stage alone gave both versions (lesson 141). Draw each
    comparison picture at least three times with the old and the new version, say how many pictures and draws you
    compared, and call a difference real only when it shows in every draw and is bigger than the old-against-old
    difference. Before you blame a change for a faint speckle, redraw the unchanged old version several times first.
    Write what was measured, never "dot for dot". *Check:* `calculators/regression_compare.py --old OLD_FOLDER --new NEW_FOLDER`.
14. When a planning or filming check fails, look at the free disk before you blame your change: the filming plan keeps
    a 4 GB reserve, and a machine with 1.3 GB free failed the check for that reason alone (lesson 140). *Check:* `df -h`.

## 1. Numbers to know

| What | Number | Kind | Key in `film-settings.json` |
|---|---|---|---|
| Frame | 1080 x 1920 pixels, 30 frames a second | judged | `frame.*` |
| Film lens | 60.4 degrees top to bottom; focal length 1649 px | measured; the focal length worked out | `frame.film_vertical_fov_degrees` |
| Size on screen | pixels = metres x 1649 / distance in metres | worked out | (`frame_geometry.py size`) |
| One degree of turn | moves everything 0.027 of the frame's width | worked out | (`frame_geometry.py turn`) |
| Plate | 64.4 degrees (film lens + 4), 1536 x 2730 pixels | judged | `frame.plate_*` |
| What the painter returns | 1504 x 2672 pixels | measured | `frame.painting_returned_size_pixels` |
| Longest slide | about 1.29 times nearer, at the nearest painted thing | worked out | (`frame_geometry.py slide`) |
| Eye height | 1.5 to 1.9 m above the surface under the camera (1.7 to start) | judged | `camera.eye_height_*` |
| Where the lines meet | within 0.03 of the width of the subject; drifts at most 0.02 during a slide | judged | `camera.meeting_point_*` |
| Subject size | 2.9 to 3.3% of the frame | measured | `composing.subject_frame_share` |
| Subject brightness | at least 1.8 times the frame's mean (still life) | measured | `shot_kind_profiles.still_life.rules.rule5_*` |
| Warm light | 1.5 to 3% of the frame (still life) | measured | `shot_kind_profiles.still_life.rules.rule6_warm_share` |
| Story reach | the nearest story thing reaches 0.70 down (the planner aims at 0.72) | judged | `...rule7_story_reaches_down`, `shot_planner.reach_aim_margin_down` |
| Phone buttons (rule 12) | words end left of 0.90 across; story props left of 0.95 between 0.45 and 0.95 down; typed words 0.05 to 0.22 down with letter tops at least 0.06 down; nothing to read below 0.80 down | judged | `safe_area.*` |
| Landmark tops | below 0.24 down, or the typed words collide with them | judged | `safe_area.landmark_top_min_down` |
| Letters to be read | fail under 20 px tall, warn under 25 px (11 px read "only just", 14 "tiny", 22 fine, 29 easy) | judged from measured cases | `lettering.*` |
| A sign nobody names | dimmed to 0.15 until it is said (0.3 was still read) | judged by eye | `lettering.unnamed_sign_dim` |
| People from behind | at least 6 m from every camera spot along the slide; a head is 63 px tall at 6 m | judged; head size worked out | `people.backs_to_camera_min_distance_metres` |
| A face that shows | head over about 24 px turned toward the camera | invented | `people.facing_head_max_pixels` |
| A crowd | long axis at least 60 degrees to every view; heads a head width apart; each figure at least half seen | 60 degrees invented; the rest judged | `people.crowd_*` |
| Dark subject | silhouette contrast at least 2.2 | measured on painted figures, never on a gate | `people.painted_figure_contrast` |
| Painted figures | no brighter than 0.35 of their surroundings (plate 0.15; the faulty painting 0.50) | invented | `painting_tools.after_painting.figure_surround_ratio_max` |
| Exposure | 1.0 to 1.8 per view (the darkest Works view 1.6) | judged | `light_planner.exposure_range` |
| EEVEE shadow pool | 1024, scaled to the plate's width | measured | `light.shadow_pool_size` |
| State change | a time cut up to 0.12 of the frame changed; more is a blend of 0.8 s in 3 steps | judged | `painting_tools.plan_states.*`, `state_pictures.stepped_blend` |
| State picture thresholds | 6 and 3 levels | measured | `state_pictures.threshold_levels`, `faint_levels` |
| Smoke | each plume travels at least 0.15 of the width while seen | judged | `effects_planner.travel_min_share_of_width` |
| A teaching change | at least 15 levels where the eye is | judged | `effects.busy_window_change_min_levels` |
| Narrator's speed | about 160 words a minute (she read 164); a page over 170 is flagged | measured; flag judged | `timing.words_per_minute`, `script_gate.*` |
| Sentences | about 9 words; none over 20; mean at most 12 | judged | `script.*`, `script_gate.*` |
| Spoken figures | at most 6 a minute of speech | judged | `script_gate.figures_per_minute_max` |
| Timeline | first word at 1.08 s; 4.0 s after the last word | judged | `timing.first_word_at_seconds`, `tail_after_last_word_seconds` |
| Pause between pages | the join's wait + its length + 0.15 s; 1.1 to 1.7 s only for a plain peel (1.4 to start) | judged | `page_timing.settle_after_join_seconds`, `timing.*` |
| Holds | a guess 4.0 s; a key number 1.0 s; a conclusion 1.2 s; any label at least 1.0 s readable | judged | `timing.*` |
| Words on screen | about one word group every 6 s | judged | `timing.word_group_every_seconds` |
| Loudness | the mix -15 LUFS; music-only clips -14; true peak at most -1 dBTP | measured; -14 and -1 judged | `sound.*` |
| Music under the voice | 18 dB while she speaks, 12 in pauses | measured | `sound.music_under_voice_db` |
| Sound checks | every file as long as asked within 0.05 s; sound within 2 ms of the pictures; 48,000 samples a second | judged | `sound.*`, `sound_gates.*` |
| Filming (one worker) | about 0.9 s a frame held, 4.3 s sliding, 34 s loading a piece | measured (round 4); profile your own film first | `filming.*` |
| Filming stretches | under 2 hours; pieces of 240 frames for lazy chapters; about 2.6 to 2.8 GB a piece | measured; piece size judged | `filming.*` |
| Paintings | 4.8 US cents a megapixel, returned + every picture sent (read 16 October 2026; 2.4 when the plan was written a day earlier) | the rate on one day, not a bill | `money.fal_flux_3_edit_cents_per_megapixel` |
| Voice | about 1 ElevenLabs credit a letter (about US$0.75 for 4,300) | credits measured; dollars judged | `money.elevenlabs_*` |
| Sendable copy | under 28 MB | judged | `delivery.sendable_megabytes` |
| Normal map size | at least 1024 pixels for a final (256 with `--quick`) | judged | `place_surfaces.normal_map_size_min_pixels` |
| Normal map direction | correlation at least +0.25 under a low light | judged | `place_surfaces.normal_direction_correlation_min` |
| Normal strength where displaced | times 0.6 | judged | `place_surfaces.normal_strength_with_displacement_factor` |
| Required treatments missing | none allowed | judged | `place_audit.required_treatments_missing_allowed` |
| Share of treatments switched off | at most a quarter, each with a reason | invented | `place_audit.off_share_max` |
| Touching, carried | within 5 mm; rest patch 16 square centimetres | judged | `place_construction.touch_metres`, `place_construction.rest_patch_square_centimetres_min` |
| Longest free stretch between supports | by role: planks and floor boards 1.38 m, beams and fences 2.5 m; longer only with a sourced `free_span` fact in the place's facts file | judged | `max_span_metres` in `place-kit/data/roles.json` (`place_construction.support_span_metres_max` keeps the garden's 1.38 m) |
| Floating | a gap over 5 mm fails | judged | `place_construction.float_gap_millimetres_fail` |
| Doorway floor | within 0.30 m below the sill | invented | `place_construction.doorway_floor_gap_metres_max` |
| Size out of range | fails beyond 1.5 times the range | invented | `place_scale.fail_factor` |
| Grime | at most a quarter of an area, a third darker | measured on the street | `place_wear.grime_area_share`, `place_wear.grime_darkening_share` |
| No plants where | footfall 0.6, crown 0.7, keep-clear 0.5 | measured on the street | `place_wear.exact_zero_gate_footfall`, `place_wear.exact_zero_gate_crown`, `place_wear.exact_zero_gate_keepclear` |
| Smallest mark that survives the painter | a patch 15 dots, a line 3 dots, a fleck 5 dots | measured on painted plates | `place_wear.mark_dots_patches_size`, `place_wear.mark_dots_lines_size`, `place_wear.mark_dots_marks_size` |
| Picture value range | each percentile within 0.03 of the guard | judged | `place_measures.percentile_tolerance` |
| Detail energy | 0.9 to 1.4 times the guard, never above 10 | judged | `place_measures.detail_energy_ratio_low`, `place_measures.detail_energy_ratio_high`, `place_measures.detail_energy_cap` |
| Squint test | 0.92 (a look, not a fail) | judged | `place_measures.squint_target` |
| Rented card | about US$1.10 an hour on an RTX 4090 (read 22 October 2026) | measured on one day, not a bill | `place_render.card_dollars_per_hour` |
| Stop waiting | jobs wait over 5 minutes while workers show idle | judged | `place_render.jobs_waiting_stop_minutes` |
| Fix rounds | one, then stop | judged | `place_checks.fix_rounds` |

## 2. The script (stage `script`, before recording)

1. Plan the length at the narrator's measured speed (about 160 words a minute), never a generic 140.
   Better still, make the estimated timeline from her measured word times and build the pages on it.
   *Check:* `narration-tools/lint_script.py before SCRIPT.json --word-times EARLIER.json --timeline-out timeline-estimated.json`.
2. One identical accent cue at the start of every page and no other cue; no capitals for emphasis (the voice
   shouts them); names the voice gets wrong in sound spelling, mapped back in `phonetic_names`.
   *Check:* `lint_script.py before`.
3. Sentences of about 9 words, none over 20; at most 6 spoken figures a minute (the recorded chapter 2 had
   8 to 9 a minute, too many for newcomers; the newcomer script has about 4). *Check:* `lint_script.py before`.
4. Say the main rule twice, word for word, and only as broadly as its evidence ("When new money is
   spent...", lesson 127). *Check:* `lint_script.py before` checks the repeat; the breadth is a
   **judgement: ask a fact checker** (skill `check-facts`).
5. Mark the page that carries the main idea `"key": true` and give it a slower page with fewer words: the
   fastest pages carried the main idea (lesson 126). *Check:* `lint_script.py before`.
6. A guess needs about 4 s of calm picture after the page; a written "..." gives under a second (lesson 129).
   End the page on the guess and let the timeline tool hold it. *Check:* `lint_script.py before` finds the
   guess phrases and fills the holds.
7. One word for one thing, both ways: "banks" meant two things, "price" meant six (lesson 128).
   **Judgement: ask a critic**; the lint lists repeated words with every sentence they are in.
8. Check whose words stand behind every "they say" (lesson 131). **Judgement: ask a fact checker.**
9. Write the next release date beside every "latest" figure, so it gets flagged once it passes.
   *Check:* `lint_script.py before --ledger LEDGER.json --today DATE`.
10. Pages ask for words, not seconds, so they retime themselves when the real recording arrives: build and
    check them on the estimated timeline before paying for the voice.
11. Quote the recording's credits and dollars and get a clear yes. *Check:* `lint_script.py before` prints
    them; `calculators/plan_budget.py ledger LEDGER.json --next-cost DOLLARS` says whether they fit.
12. Test the script on newcomers who get only what a viewer hears and sees, never the notes (lesson 130).
    **Judgement:** workflow `test-script-with-newcomers`.

## 3. The recording (stage `record`, after recording)

1. Download each recording at once: the links expire after 2 hours. *Check:* `lint_script.py after` lists
   missing downloads.
2. Take word times only from `narration-tools/extract_word_times.py`; ElevenLabs places the first word late.
3. Check from the free transcript that the cue was not read aloud and that names were said right.
   *Check:* `narration-tools/lint_script.py after SCRIPT.json --transcripts DIR --recordings DIR`.
4. Judge the voice by numbers, not by ear, and re-record only the pages it names. *Check:*
   `narration-tools/sound_gates.py voice word-times.json --recordings-from DIR`.
5. Record every page before filming: a late retake moves every page after it. *Check:*
   `calculators/plan_page_timing.py refilm OLD_TIMELINE NEW_TIMELINE --chunks FOLDER` lists the filmed pieces
   to redo.
6. Find a new soundtrack's level by measurement: the music sits 18 dB under her voice while she speaks.
   "Slightly louder" was 3 dB. *Check:* `sound_gates.py duck MUSIC NARRATION TIMELINE`; the mix script stops
   on a FAIL line.
7. Never trust an audio filter's output length. Resample to 48 kHz straight after any loudness step (one
   switched quietly to 192 kHz and the padding miscounted), then measure. *Check:*
   `sound_gates.py length FILE --expected SECONDS`; the mix and finish scripts call it.

## 4. Places, cameras and composing (stage `shots`, before building or drawing a view)

For places built in 3D and painted over:

1. Write the place's facts first: views, signs, chimneys and fires, figures, lights, the surfaces things
   stand on and the accepted list. Every later tool reads them. *Check:* `calculators/place_facts.py check FILE`.
2. Stand the camera where a person could stand, the eye 1.5 to 1.9 m above the surface under it, level, in
   line with the subject's near edge. Never in the middle of an empty road; about 1.5 m out from the house
   fronts. *Check:* `calculators/plan_shot.py --place-facts F --view V --plan`.
3. Turn once, to put where the street's lines meet beside the subject; after that, only slide. Never close a
   gap by turning: a turn moves the subject and the meeting point together (lessons 105 to 107).
   *Check:* `plan_shot.py`; on the page, `paper-film/tools/camera_audit.py CAMERA.json --built-set`.
4. Work the camera's distance out from the reach: the nearest story thing must reach 0.70 down. Bare floor
   in the bottom third means the camera is too far back. *Check:* `plan_shot.py`,
   `calculators/frame_geometry.py reach`, the shot checker's rule 7.
5. For a "bigger picture" view, raise the eye until the story reaches the bottom third; never tilt.
   *Check:* `calculators/frame_geometry.py eye`, `plan_shot.py` (overview).
6. Draw the plate 4 degrees wider than the film lens, from the slide's start. *Check:* `plan_shot.py` gives
   the plate's lens and rows.
7. Slide at most about 1.29 times nearer, judged at the nearest painted thing, not at the subject: the
   notice corner's pail came 1.45 times nearer while the notice came only 1.30. Sideways moves are a few
   centimetres. *Check:* `calculators/frame_geometry.py slide --place-facts F --view V`; on the page,
   `camera_audit.py --built-set`.
8. Clear the phone buttons with a small sideways slide, never a turn. *Check:* `plan_shot.py`,
   `frame_geometry.py boxes`.
9. Every strong thing points at the subject: where the lines meet, the brightest parts, the warm light and
   the story props. Fix the one strong thing pointing elsewhere first. *Check:* the shot checker (rules 1, 5, 6).
10. Props either clearly touch or clearly stand apart (overlap at least about 15 px or a gap of at least
    about 18 px at 1080 wide). Posts and pipes beside a nearer prop's edge are the usual offenders; list
    background props too. *Check:* `paper-film/blender/make_check_file.py` writes `pairs_also`; the shot
    checker's rule 4.
11. Work props small, far (10 to 35 m) and dim; nothing dark or big in the bottom-left quarter; fill the
    bottom third with the story itself, not filler. *Check:* the shot checker; `plan_shot.py`.
12. Project every tall landmark's top: above about 0.24 down it collides with the typed words.
    *Check:* `calculators/view_audit.py audit --place-facts F`.
13. For every word that changes the picture, check the thing that changes is inside that view's frame.
    *Check:* `calculators/plan_states.py plan` (a cue outside the frame or in the words band).
14. Write the check file from the scene, not by hand: only the story roles (subject, support, story, work)
    are yours. Hand-made files got `must_read`, `pairs_also` and `on_ground` wrong. *Check:*
    `paper-film/blender/make_check_file.py` (inside Blender, after the assemble script).
15. Put the view's kinds of shot and its accepted problems in its check file (`kind_of_shot`, `figures`,
    `accepted` with rule, reason, who and date), so a kept problem shows as known instead of failing every
    run. *Check:* `paper-film/tools/check_shot.py` reads them.
16. When the person likes a picture, match its camera by landmarks before moving any prop. **Judgement:** read
    the landmarks by hand; the line finder only helps.
17. A rule-of-thirds reason was tested and dropped (log 30). Don't use it.
18. Indoors, props rest on declared surfaces (the checkout's counter at 0.885 m) and the reach is measured
    above the counter. *Check:* place facts `support_surfaces`; the `interior` kind of shot (provisional).

For painted relief rooms and paper pages:

19. In a painted room, push with the lens; travel 1 to 2 units; never rise during a pan. *Check:*
    `camera_audit.py`.
20. Check each paper piece at its own distance from the camera, and stack things in depth, not side by side:
    a tall frame is narrow. *Check:* `frame_geometry.py boxes`.
21. At most 3 named moves a shot; cut instead of adding a fourth. *Check:* `kit.stillShot` refuses a fourth;
    `camera_audit.py`.

## 5. People

1. Backs to the camera at 6 m or more, measured from every camera spot along the slide. *Check:*
   `plan_shot.py`.
2. Never answer a face that shows with a dark silhouette: flat black figures laid over a painting read as
   shadow puppets (lesson 137). Turn the figure away or move it back; if a face must show, the painter is
   told "face lost in deep shadow under the cap, no lit cheek". *Check:* `plan_shot.py` (it never offers a
   silhouette), `paint_request.py prompt`, the skin check in `after_painting.py`.
3. A waiting crowd stands across the view, two deep, with gaps between heads. A file of people seen end-on is
   one dark column (lesson 132). *Check:* `plan_shot.py` (heads a head width apart, each figure half seen, the
   crowd's long axis at least 60 degrees to every view). The 60 degrees is invented: five men in a ring round a
   fire lay at 48 degrees and read fine.
4. Turn heads away from the fire, not only from the camera: a fire-lit cheek in profile becomes a painted
   face. **Judgement: ask a critic** on the plate at full size.
5. Dark matt hair, collars up: the back of a head paler than its coat comes back as a face or a bald dummy.
   *Check:* `paint_request.py preflight` (heads paler than coats).
6. Judge coat colours after the film's colour finish: it turns dark browns red. *Check:*
   `paint_request.py preflight` (cloth the finish turns red).
7. A thin rim light from behind separates dark figures from a dark street, linked so it lights only them.
   *Check:* `plan_lights.py plan`.
8. No long shadows from people, only a soft patch under the feet (lesson 135). *Check:*
   `paint_request.py preflight --helper-plate PLATE_WITHOUT_PEOPLE`.
9. When the words say people are working, show a figure at work; an empty lit room reads as deserted.
   *Check:* `plan_states.py plan` warns on busy states.
10. Keep figures out of live smoke: a man inside the smoke reads as a ghost. *Check:*
    `plan_effects.py wind` (thick smoke over a figure).
11. Nothing round above a hung coat's collar: the painter turns it into a person. **Judgement: ask a critic.**
12. Never paint a real person; type their name. *Check:* `paint_request.py preflight --real-names FILE`.

## 6. Lettering

1. All lettering is ours, on its own surface (`ownSurface` in the page). Ask the painter for plain marks,
   never words: it garbles them. *Check:* `paint_request.py prompt`.
2. Size letters from the distance: a word the page needs fails under 20 px and warns under 25 px.
   *Check:* `calculators/view_audit.py audit --place-facts F --timeline T --page N`.
3. Words to be read face the camera; turn each drum toward the cameras that read it. *Check:* `view_audit.py`
   (drum turns).
4. Every lettered prop goes in `must_read`, so no fragment such as "DIESE" shows. *Check:*
   `make_check_file.py`; the shot checker (words hidden).
5. A readable sign the narration does not name is read first. Dim it until it is named, or take it out of
   frame. *Check:* `view_audit.py` (loud signs; its limit was set on one sign). How much to dim is a
   **judgement**: 0.15 was chosen by eye after 0.3 still read.
6. Keep joints and tacks clear of letters, and letter the back of a board that shows from behind.
   *Check:* `view_audit.py` (backs of signs); joints are a **judgement: ask a critic**.
7. No year or number on screen that the narrator does not say. *Check:* `plan_page_timing.py check`
   (typed words and numbers against the narration and the research ledger).

## 7. Light

1. Give the subject its own narrow key light, from below, linked to it alone; keep the fire's own light low.
   Measure warmth as red against blue, not brightness. *Check:* `calculators/plan_lights.py plan`; the shot
   checker's rules 5 and 6.
2. Work out practical lights' watts from distances: a lamp 15 cm from a seat needs a few watts.
   *Check:* `plan_lights.py plan` (starting watts by the inverse square from the subject's own light).
3. Cut a light's reach before its strength: give every spot a reach just past its target, or it paints the
   wall behind. *Check:* `plan_lights.py plan` (reach from Blender's ray hits,
   `paper-film/blender/set_measurements.py beam`).
4. Only a few lights cast shadows (the key, a fire, a doorway, the sky); people get soft foot patches.
   Plates draw faster and state pictures stay small. *Check:* `plan_lights.py plan`.
5. Glowing things get a black base colour; a lamp's glass may not outshine its flame. Lamps go on inner faces
   or above the subject: a lamp on the face of a wall lights the wall. *Check:* `model_lint.py` (glows),
   `plan_lights.py plan` (a lamp lighting the face it hangs on).
6. Show a dark subject (an iron gate, a doorway) against a lit background and judge it by silhouette
   contrast. Whether a view counts as a "dark subject" is a **judgement**: round 5 tried to make the gate the
   brightest thing and failed. *Check:* `plan_lights.py contrast`; the `dark_subject` kind of shot.
7. Warm light covers 1.5 to 3% of the frame, and the subject is at least 1.8 times the frame's mean (still-life and
   lamp-lit views; in daylight the subject stands out by its own narrow key light, never by putting the place in shade:
   rule 12). *Check:* the shot checker on a finished still.
8. Tune by the checker's numbers on small renders, one named light per round. The notice corner took 26
   lighting rounds by eye; most changed position, linking or colour, not watts. *Check:* the shot checker;
   `plan_lights.py plan` for the starting point. (The automatic tuner is not built.)
9. Check the painting's own warm spots too: painted lamps and windows spread light. *Check:* the shot checker
   with the painting as the finished picture.
10. Set each view's exposure from its measured brightness on the painting, not the plate. The target is a
    **judgement** (the darkest Works view was accepted at 1.6). *Check:* `plan_lights.py exposure`.
11. Never add a lamp to projected surfaces; signs on their own surfaces need copies of the plate's lights in
    the page, or they look flat.
12. The sun can do nothing: check that it reaches the ground you show before you judge the materials. Shadow
    length = height / tan(elevation): a 4 m hall with the sun 9 degrees up throws a shadow about 25 m long, and in
    the Japanese garden that, with hazy backdrop hills, put most of the view in shadow while the materials were
    blamed. Raise the sun or move what is in its way; far shapes get the role `backdrop` (they cast no shadow).
    *Check:* the place audit's line "place: sun" (the share of the seen ground in shadow, and the object that shadows most).
13. A mark nobody can explain (a white shape, a streak): hide one group of objects at a time and draw a small
    picture each time until the mark goes. Glowing things reflected in water are a common cause (the garden's pond
    mirrored its glowing paper screens): roughen the water slightly, dim the glow, or hide the lamps from
    reflections. **Judgement** (no tool hunts it yet).
14. Lit rooms at night: make back walls solid (light leaked out of a cottage's back windows); rooms lit by their own
    glow are cheap and can change on a word; in a dark room the cut-outs go dark too; a street needs its own light (a
    lit pavement, a lamp's pool of light), or the people look as if they stand inside the lit rooms. **Judgement**;
    the house sample's code shows each (its look was rejected; its code is kept).

## 8. Models and Blender

1. Measure a model before fitting anything to it; never use a size worked out from a helper's picture
   (lesson 116). *Check:* `paper-film/blender/model_lint.py FILES.glb --index index.json` (sizes).
2. Cast placement rays from below, after `view_layer.update()`, and judge "stands on" from the feet.
3. Rename second copies: Blender names them ".001" and a copy gets taken for the original. Record each
   model's front direction once. *Check:* `model_lint.py` (names, fronts; `--write-index` records them).
4. Never put two surfaces on one plane (leave about 1 cm), and never lay a floor 2 cm over another ground.
   *Check:* `model_lint.py` (same-plane faces, floors).
5. Run the stripe check: a squashed texture shows as streaks, and the painter copies them.
   *Check:* `model_lint.py` (stripes).
6. Unhook the see-through value on glass, or a lamp reads as a flat amber card. *Check:* `model_lint.py` (glass).
7. Run EEVEE under a virtual screen (Xvfb) with the shadow pool at 1024, scaled to the picture's width. A
   plate takes about 6 to 11 minutes.
8. One heavy job at a time; turn `.blend1` backups off. Filming while Blender draws is about 1.8 times slower.
9. Budget a set by filming time, not triangles: profile one frame. *Check:*
   `node paper-film/tools/profile_frame.mjs PAGE TIME`.
10. Open every downloaded texture at full size and look for stickers, brands and digits. **Judgement.** For the surfaces,
    wear and construction of a place, see section 8a.

## 8a. Surfaces, wear and construction (stage `place`, before drawing a place's views)

The full treatment is the skill `surfaces-wear-and-construction` (start with its first screen). Every place, set or prop
built in Blender goes through it, whatever the request says. In short:

1. Build with supports: every plank on a support, every support on the ground, nothing floating, at real size.
   *Check:* `explainer-film-place construction` (stage `place`: "place: construction", "place: scale").
2. Give every object a role and an owner as you make it. *Check:* `explainer-film-place roles`; the audit fails an
   object with no role ("place: roles").
3. Run the whole pass in one call, not piece by piece, and repeat it freely (it gives the same counts twice).
   *Check:* `explainer-film-place finish`, then `audit`.
4. Real normal maps that point the right way: OpenGL, Non-Color, through a Normal Map node with a UV layer, at least
   1024 pixels for a final. *Check:* `explainer-film-place normals-test`; the audit's "place: normal maps".
5. UVs first: a normal map needs a UV layer on every object that uses it. *Check:* "place: uv".
6. Displacement only where the role says (dirt road, mud, thatch, rock ground), on a dense mesh, with the normal
   strength x 0.6. *Check:* "place: displacement".
7. Layers in their fixed order: dirt and grime, then wetness, then cracks and edge wear, then moss, then rubbish.
   Every object needs its `pk_<layer>_amount` property. *Check:* `explainer-film-place age`; "place: layer amounts".
8. Marks few and big, sized in picture dots, in the place's own style (a designed mark, not photographic noise).
   *Check:* `explainer-film-place measure` (detail energy, flat windows). Whether it reads as designed is a
   **judgement: ask a critic**.
9. Plants and rubbish stay off wheel tracks, crowns, doorsteps and puddles; the counts there are exactly 0.
   *Check:* "place: keep-out".
10. A layer set to 0 needs an `off` entry with a reason (or a signed accepted entry). *Check:* "place: off reasons".
11. Draw with the renderer rule: Cycles where lamps, windows, lanterns or fires are lit, EEVEE when they are off.
    *Check:* `explainer-film-place renderer-for`; "place: renderer".
12. Make the style guard from the first honest picture and call it provisional until a reference or a critic agrees.
    *Check:* `explainer-film-place measure PICTURE --make-guard`.
13. Audit last, on the exact file you will draw. A scene saved after the audit makes it stale and the preflight says so.
    *Check:* `explainer-film-preflight place --place-audit FILE --blend SCENE.blend` ("place: stale audit").
14. Output made with `--quick` is for trials, not for a final. *Check:* the audit records it.
15. Have the place checked by helpers who did not build it, who recompute the builders' claims. *Check:* the workflow
    `build-a-place`; the preflight's `--fresh-check`.
16. Make every change in ONE sweep, then look once. Build the scene once and save it; every test starts from the saved file. A change tried one small step at a time, with a look after each,
    cost US$10.89 of card time in the Japanese garden (the finished pictures cost about 5 cents). *Check:* `explainer-film-place variations plan` (free) and the card-time ledger.
17. For each change to a thing, draw about 10 variations that are measurably different, in ONE batch on up to 3 rented cards at once, and look at ONE labelled sheet. Pick or combine, then at most ONE
    more batch around the pick. Variations closer than 8 percent of a setting's range are dropped before drawing; pictures that came out nearly the same are flagged after drawing.
    Before the card, scout for free: `variations scout FILE.json` draws the same batch here, tiny (about 40 s for a small place), and `plan` and `run` then drop what would not show
    (on the canal lock half of a first moss batch showed nothing on the card, and the scout named exactly those). A dial that shows only above some value: spread it over that part
    (`variations make --range KEY LOW HIGH`). `amount` and `master` scale the saved scene (1 = as saved, up to 2).
    *Check:* `explainer-film-place variations make | scout | plan | run | refine`; the batch rule is counted by `card-time` (a third batch for one change is refused; a scout is not a batch).
18. Small quick pictures (600 x 400 for trying variations, or 360 x 640 for a place marked for the film, EEVEE or low-sample Cycles; 1200 x 800 for the checkers' previews, 540 x 960 for a film place) until the end; full-size pictures drawn ONCE, at the very end. *Check:* `variations` draws small by itself; `render --finals` only on the last audited file.
19. Every card job goes in the card-time ledger and each helper has an allowance (builder 10 minutes, fixer 5, integrator 10, renderer 10, checker 3, planner 0: judged); the tool warns at 80 percent and refuses
    past it; going over needs a written reason and never more than half again. Report the card seconds you used. *Check:* `explainer-film-place card-time show | check`.
    A batch waits for the cards (1 to 3 minutes for a small place): give the command a long time limit. If it is cut off, its jobs still count (each was written as "sent"), and
    `explainer-film-place variations collect RUN-FOLDER` finishes it without sending anything again.
    Seconds are work + wake-up + idle tail; the price is an estimate, never a bill. The skill is `surfaces-wear-and-construction`, file `batched-rounds-and-card-time.md`.

## 9. Before painting (stage `plates`)

1. Fix the light in 3D first; the painter copies the plate's light and dark. Pass the preflight before
   paying. *Check:* `calculators/paint_request.py request ...` (it refuses without a render log and a shot
   report, and never sends anything).
2. Darken a faint glow inside a hollow (a drum, a brazier) before painting: the painter lifts it into a
   bright band (lesson 138). *Check:* `paint_request.py preflight --hollow GROUP`.
3. No pure-black openings: the painter reads them as open (a shut gate came back open). *Check:*
   `paint_request.py preflight` (black holes).
4. Find every wire, rung and bar under 6 px wide: remove it, thicken it, or name it so the painter keeps it.
   *Check:* `paint_request.py preflight` (thin parts).
5. Build the prompt from the template. Write only each story prop's `paint_as` words in the check file (what
   it is, its colour, its state, what it must not become) and a short brief. *Check:* `paint_request.py prompt`.
6. Count and describe every person: how many, near or far, which way they face. Far walkers are "flat dark
   shapes with no pale spots"; "keep the figures as dark as in image 1". Forbid flames, smoke, glows and new
   shadows: the film draws them live, and they would show twice. *Check:* `paint_request.py prompt`.
7. Paint the place's master view first and send it as the style picture for every other view, at about
   1 megapixel. *Check:* `paint_request.py price` counts every picture sent.
8. Plan the behind painting and the state plates together with the plate: the behind painting is half the
   repaint cost. *Check:* `calculators/plan_states.py plan --plan PLAN.json`.

## 10. When a painting arrives (stage `paint`)

1. Line every painting up with its plate before anything else: the painter shifted one 3 px and stretched it
   0.65%. *Check:* `calculators/after_painting.py check --painting P --plate PLATE --check C --facts F --out-folder D`.
2. Make the behind painting from the same state, line it up against the main painting, then keep the main
   painting's shadows round the near props: the painter took them away (lesson 122). The same state means wet with
   wet and dry with dry: a wet front painting over a dry behind painting shows a pale dry patch where the camera
   uncovers what a near prop hid (59 percent of the road dots came out lighter). Wet and dry paintings go in and out
   as a pair, with the page's look line; keep the other pair beside them with a note on how to go back. *Check:*
   `after_painting.py check --behind B` (it fails with a "pale patch" line).
3. Count the figures and check their outlines and darkness: painted men lifted from 15% to 50% of their
   surroundings' brightness turned mid-grey on a phone. Darken them back. *Check:* `after_painting.py`
   (figures).
4. Skin added on a head means a face appeared. *Check:* `after_painting.py` (skin pixels; its limit is
   invented, so look at the head).
5. Save PNG only. A JPEG moves every pixel, and a state picture made from it changes everywhere. *Check:*
   `after_painting.py` writes PNG.
6. If a result looks like a photograph, re-ask once, and ask the person before paying again. Whether it looks
   painted enough is a **judgement**.

## 11. State changes on a held shot

1. Swap only what changes, inside a mask made from the two plates' difference plus the changing things'
   outlines; look at the mask picture before trusting it. *Check:* `paper-film/tools/make_state_picture.py`;
   `plan_states.py plan --measure`.
2. One plate per change, each on its own word. Two changes on different words in one plate is an error: the
   earlier one ghosts in. *Check:* `plan_states.py plan`.
3. Cut when up to about 12% of the frame changes; blend (0.8 s in 3 steps) when more does. *Check:*
   `plan_states.py plan --measure`. (The shared table's older `state_pictures.cut_when_mask_share_max` says
   0.10; `plan_states.py` uses 0.12. A person should settle it.)
4. Never change state during a slide. *Check:* `plan_states.py plan`; `check_page_layout.mjs`.
5. When only people change at a cut, change something else with them (lesson 136). *Check:*
   `plan_states.py plan` warns.

## 12. Smoke, fire and other live effects

1. Blow smoke across every view and trace it on every view before filming. Blown away from the camera, the
   puffs pile up into rings (lesson 134). *Check:* `calculators/plan_effects.py wind --place-facts F` (each
   plume travels at least 0.15 of the width; puff tops stay under the word cards).
2. Only smoke sources that are in frame and make sense in the story: a closed pit has no smoke. *Check:*
   `plan_effects.py wind` drops plumes that never enter; the story sense is a **judgement**.
3. Vary flames in size and lean; even, regular flames look like a cartoon. *Check:* `plan_effects.py fire`.
4. Give every prop the behind painting removes its own soft contact shadow, faded in as the camera starts
   to move. *Check:* `plan_effects.py contact-shadows --place-facts F`.
5. A change that teaches a word must change the picture by at least 15 levels where the eye is.
   *Check:* `plan_effects.py window-change --box l,t,r,b STILL_AT_WORD STILL_LATER`.
6. On paper pages, make every effect through `kit.effect`. *Check:* `plan_effects.py lint PAGE.js`.

## 13. Pages: timing and words on screen (stage `pages`)

1. Run the page events, then the two checks on them, before drawing any stills. *Check:*
   `node paper-film/tools/page_events.mjs CHAPTER EVENTS.json`, then
   `python3 calculators/plan_page_timing.py check EVENTS.json` and
   `node paper-film/tools/check_page_layout.mjs EVENTS.json`.
2. On-screen words are short forms of what she says within a few seconds; never show a year or price she
   doesn't say. *Check:* `plan_page_timing.py check --ledger NUMBERS.json`.
3. Give the occurrence for any word said twice on a page, `kit.at('war', 2)`, even when you mean the first:
   a later script edit can move "the first". *Check:* `plan_page_timing.py check`, or with no browser
   `plan_page_timing.py lookups TIMELINE PAGE.js:N`.
4. Every word group stays readable at least 1 s; a conclusion 1.2 s, starting on the first word of its
   phrase. Under a second before a cut, bring the label's words in with its line or start it a word earlier.
   *Check:* `plan_page_timing.py check`.
5. `fadeOut: 0` for anything that ends on a cut; one line per box at a time. *Check:* `plan_page_timing.py check`.
6. Counts finish on the spoken number and hold at least 1 s. *Check:* `plan_page_timing.py check`.
7. A label's line leaves its target sideways, never through what it names, and its words sit on empty ground.
   *Check:* `check_page_layout.mjs` (overlaps); the rest is a **judgement: ask a critic**.
8. A soft dark band goes behind words over busy or bright backgrounds (`topShade`). *Check:*
   `calculators/view_audit.py title-contrast --still P --box l,t,r,b`.
9. About one word group every 6 s; let the pictures carry the rest. *Check:* `plan_page_timing.py check`.
10. Write a page's holds into its join and the timeline's pause, never as seconds inside the page, and use
    the pause the tool prints. *Check:* `plan_page_timing.py check` (pauses).
11. Check page turns in one run of the whole chapter, with still times separated by spaces; use the still
    list the tool prints rather than picking times by eye. *Check:* `plan_page_timing.py check` (the stills
    command).
12. Set every effect from the moment alone; never leave state on from an earlier frame. *Check:*
    `page_events.mjs` draws moments out of order; `check_page_layout.mjs`.
13. Mark smoke, flames and flicker with `kit.moving` and return still keys while the camera holds, or a held
    set films about 5 times slower. *Check:* `check_page_layout.mjs`.
14. A cut-out that fades uses `setFading(piece, pose)`; `.set({ opacity })` snaps off half way.
15. Measure the camera. Built sets:
    `paper-film/tools/camera_audit.py CAMERA.json --built-set --place-facts F --view V`. Other pages:
    `camera_audit.py CAMERA.json --timeline timeline.json --page N --page-files DIR`. Any PROBLEM line is a
    must-fix.

## 14. Filming (stage `film`)

1. Work out the time and tell the person before starting. Profile first: the old cost table missed round 5's
   filming by half, while a short profile got three rounds within about 5%. *Check:*
   `calculators/plan_budget.py profile-commands EVENTS.json --scene CHAPTER`, film those pieces, then
   `plan_budget.py measure LOGS... --events EVENTS.json --out rates.json` and
   `plan_budget.py filming EVENTS.json --scene CHAPTER --rates rates.json`.
2. Lazy chapters with pieces of 240 frames or more; stretches under 2 hours (background jobs are stopped
   after 2). *Check:* `plan_budget.py filming` prints every stretch's FILM_FROM/FILM_TO command.
3. Workers by processor count: 1 on 2 processors, 2 on 4. *Check:* `plan_budget.py filming`.
4. Stop a job by the process number you saved, never with `pkill -f`: it stopped the session's own shell.
5. Watch for a job stopping, not only for it finishing; check the first finished stretch at once.
   *Check:* `plan_budget.py status CHUNKS_FOLDER`.
6. Get an independent critique before filming, and save it as JSON with each finding marked `"status":
   "fixed"` or `"accepted"` (with who and the date) once dealt with. **Judgement: ask a critic** (skill
   `check-and-critique`). *Check:* the `film` stage refuses a critique, or a `pages` report, older than any
   page file.

## 15. Sound and finishing (stage `finish`)

1. Level pages by gain only, and let only the final limiter (with `latency=1`) touch the peaks; without it
   the sound came 5 ms late.
2. Measure loudness and true peak on the encoded copy, not the WAV: encoding raises peaks. *Check:*
   `narration-tools/sound_gates.py loudness FILE`; `narration-tools/finish_film.sh` runs it.
3. Measure the sound's alignment in milliseconds at every page's first word. *Check:* `finish_film.sh` with
   the timeline as its 6th argument (without it, it ends with exit 3).
4. Deliver captions as separate files; the sendable copy stays under 28 MB. *Check:* `finish_film.sh`.
5. Music-only clips go at -14 LUFS. Choose the music stretch by measurement, since nobody can listen here,
   and say so. *Check:* `sound_gates.py music-start MUSIC --seconds N`; `paper-film/tools/add_music_bed.sh`.
6. Run the jump finder with the planned cuts; any jump that is not a planned cut is a must-fix. *Check:*
   `paper-film/tools/find_jumps.py` with the cut list `plan_page_timing.py check` prints.
7. Check files before pushing: GitHub refuses anything over 100 MB. *Check:* `calculators/plan_budget.py push`.
8. Have a fresh helper judge the filmed clip in motion (the film-critic agent's clip mode: jumps, flicker, seams, pale
   patches, words on screen at the wrong time), then fix its must-fix findings. Stills miss what moves. *Check:* the
   `finish` stage refuses to run without `--clip-critique CRITIQUE.json` (exit 2), and fails one older than the film or
   with a must-fix finding neither fixed nor accepted.

## 16. Money and approval

1. Prices change between plan and purchase: Flux 3 edit cost 2.4 US cents a megapixel when the plan was
   written and 4.8 a day later (lesson 139). Read fal's live price before every paid batch and give it to the
   planner. *Check:* `calculators/plan_budget.py cost PLAN.json --rate CENTS --rate-date DATE`.
2. Count the pictures you send, not only the one you get back: a 2k repaint with a style picture came to
   about 44 cents at 4.8. *Check:* `paint_request.py price`; `plan_budget.py cost`.
3. Every painting price so far was worked out from the rate on the day, not read from a bill. Read the real
   charges once from fal's request history (free) and fit the rate. *Check:*
   `paint_request.py fit-price --charges FILE`.
4. Keep a running total counted from the allowance's start date, never from memory. *Check:*
   `plan_budget.py ledger LEDGER.json --allowance DOLLARS --next-cost DOLLARS` refuses a step bigger than
   what is left.
5. Budget one repaint for every two paintings and one page of re-recording.
6. Do every free step first, then ask once, with the exact cost. A vague reply is not a yes, and a refusal
   is never worked around. **Judgement:** only the person's own clear yes counts.
7. Rented-card time is limited the same way as painting money: each helper has an allowance in card minutes, written in a ledger, and the tools refuse past it. Try variations in batches (one sweep, about 10
   far-apart variations, one sheet, at most one more batch); full-size pictures once at the end (section 8a, tips 16 to 19). *Check:* `explainer-film-place card-time show`.
8. Write any file that holds prices with the file-writing tool or a quoted here-document (`<<'EOF'`): written
   through the shell, US$0.048 became US/bin/bash.048 (lesson 142). Then search the file for `bin/bash`.
   *Check:* `plan_budget.py ledger` and `plan_budget.py push` fail on it.
9. An allowance covers the kind of spending it was given for (pictures and props from the painting service; voice
   only from the voice service). Spending inside it is still reported each time, a different kind of spending needs
   a fresh, clear yes, and a helper's brief gets the true remaining figure (one brief said US$3 when US$8.70 was
   left). *Check:* `plan_budget.py ledger` prints a line that starts "For helper briefs:".
10. Never send a message to a helper that is spending money while it runs: it woke a second copy, which made 8 extra
    paid calls (about US$0.70). *Check:* `explainer-film-place card-time check` refuses a second card job in flight.

## 17. The people test's lessons (lessons 135 to 139)

The people test (log 34) painted five waiting men round a brazier and some far walkers in the pit village,
then made them leave on a time cut. It cost one paid round and gave five lessons; each is now checked.

- **135. Asked to remove the people, the painter left their long shadows.** Dark streaks stayed on the road
  after the cut, and the area to swap grew to 46% of the frame for people covering 6%. Draw plates in which
  figures cast no long shadows, only a soft patch under their feet. *Check:*
  `paint_request.py preflight --helper-plate`; `after_painting.py` (shadows left behind); `plan_states.py`
  (swap area against the people's outlines).
- **136. When only the people change at a cut, they seem to blink out.** A first-time viewer read it as a
  glitch. Change something else with them: the fire lower, the light later. *Check:* `plan_states.py` warns;
  whether it reads as time passing is a **judgement: ask a critic**.
- **137. Painted figures belong to the painting; dark figures laid over it don't.** The silhouettes came out
  flat black and read as shadow puppets or holes; the painted men matched the street's brushwork. Never use a
  silhouette as the answer to a face. *Check:* `plan_shot.py`; `after_painting.py` (figure darkness and skin).
- **138. The painter lifts a glowing hollow into a band.** A drum's faint inner glow came back as a bright
  orange band above the rim. Darken it in the plate first. *Check:* `paint_request.py preflight --hollow`.
- **139. Prices change between plan and purchase.** The rate doubled in a day. *Check:*
  `plan_budget.py cost --rate` with today's price.

Also from the people test: the men went from about 15% to about 50% of their surroundings' brightness when
painted (a must-fix: on a phone they turned mid-grey), far walkers got pale face and hand dots, and the facing
man got a lit cheek. The prompt clauses in section 9 and the figure checks in section 10 answer these.

## 18. The traps that cost the most rounds

1. **A single file of people seen end-on** (rounds 3 and 4). Seven men lined up the lane; both cameras look
   up the lane, so they stacked into one dark column nobody could count. Stand a crowd across the view, two
   deep. *Check:* `plan_shot.py` fails the single file before anything is built.
2. **The story high over a bare floor** (rounds 4 and 5). Every Works view passed the shot checker's main
   rule, yet the story sat 0.53 to 0.65 down over bare paving. The nearest story thing must reach 0.70 down.
   *Check:* `plan_shot.py` (round 4's camera spot comes out 0.653 and it asks for 2.2 m nearer),
   `frame_geometry.py reach`, the shot checker's rule 7.
3. **Smoke blown away from the camera** (round 4). With the wind straight up the lane, a plume moved 0.044
   of the width while seen and piled into rings; blown across the view it moved 0.188. *Check:*
   `plan_effects.py wind`.
4. **The painter leaving shadows** (logs 32 and 34). Painting the near props out took their shadows away,
   and painting the people out kept theirs. Keep the main painting's shadows round the props; draw people
   without long shadows. *Check:* `after_painting.py check --behind`; `paint_request.py preflight --helper-plate`.
5. **A cut where only people change** (log 34). It read as a glitch. *Check:* `plan_states.py`.
6. **Lighting by eye** (logs 31 and 32). The notice corner took 26 rounds. Start from the planned watts and reach,
   then change one named light per round by the checker's numbers. *Check:* `plan_lights.py plan`; the shot
   checker.
7. **Turning to close a gap** (logs 30 and 31). A turn moves the subject and where the lines meet together;
   slide instead. *Check:* `plan_shot.py`; `camera_audit.py --built-set`.

Other traps, one line each:
- The 192 kHz loudness trap: resample to 48 kHz after any loudnorm (`sound_gates.py length`).
- A word said twice on a page: give the occurrence (`plan_page_timing.py lookups`).
- One-frame pops and a fade that snaps off half way (`check_page_layout.mjs`; `setFading`).
- Bald-looking heads and coats the grade turns red (`paint_request.py preflight`).
- Shadow-memory wedges in a plate (`plan_lights.py render-log`).
- The painter's 3 px shift (`after_painting.py check`).
- A JPEG state picture (PNG only).
- `pkill -f`, and the 2-hour limit on background jobs (`plan_budget.py filming`, `status`).
- A ".001" copy taken for the original, and a size taken from a helper's picture (`model_lint.py`).
- Prices that change from one day to the next (`plan_budget.py cost --rate`).

## 19. What the calculators can't judge

The tools measure; people still judge these. **Judgement: ask a critic** for each.

- Whether a detail reads as something else on a phone (little cameras, sunglasses, wood like a contour map,
  doorways like a bar chart, a gasholder as a tank). The tools only supply phone-size sheets and a stripe test.
- Period and story accuracy of every painted object, built prop, person's clothes and word written on a prop:
  "was this in that place and that year?" The project's faults: wrong-era tanks, too much coal in a lockout,
  snow-like blotches on a May road, sacks shaped like clay jars, an oil-drum brazier more 1984 than 1926, a symbol
  like a hooked cross. A history critic checks every one, not only the words (workflow `critique-film`, the critic
  whose area is history), and the fact checker gets the pictures and the words on props (workflow `verify-facts`,
  `pictures` and `propLettering`). A date on a prop and its weekday must agree (30 April 1926 was a Friday).
- Whether motion matches the meaning of the words (a needle falling on "raising").
- Whether machines read as machines and props as what they are (looms that read as church benches).
- Whether a hero prop has enough detail.
- Research honesty: a rule said exactly as broadly as its evidence, one word for one meaning, whose words
  stand behind "they say".
- Whether a newcomer understands, and the 3 or 4 things a newcomer must see in each shot (workflow
  `test-script-with-newcomers`; testers get only the spoken and on-screen words).
- Whether a time cut where people vanish reads as time passing or as a glitch.
- Whether a picture contradicts a card, beyond the small table the tools know, or contradicts its own rule (a
  closing picture said "more things made" while pointing at a cold chimney with men still waiting); and whether a
  label's arrow runs through a number board (it must not).
- Whether a colour or symbol carries political or commercial meaning in context.
- Whether to keep an on-screen short form that the words check could not match to the narration.
- The story choices: place, era, mood, which thing is the subject, which props tell the story, and what
  each prop must not turn into in the painting (the `paint_as` words).
- Whether a returned painting looks painted enough, and how strict colour continuity should be.
- The mood of a soundtrack stretch: picked by measurement because nobody can listen here, and said so.
- Which rule wins when rules conflict (a dark iron gate can't be the brightest thing; chimney tops in the
  words band against words placed beside them).
- Whether a view is a "dark subject"; each view's exposure target; how much to dim a sign nobody names.
- Whether the painted ground at the frame's bottom edge counts as the nearest painted thing during a slide
  (`frame_geometry.py slide --count-ground` shows it; counting it would fail every slide made so far).
- The overall feel of the light (cool against warm, dusk mood), beyond the rule numbers.
- Whether a flagged near-touch, thin part or small sign is worth fixing or fine for the story; if fine, put
  it in the `accepted` list with the reason, who and the date.
- Whether a worn road reads as worn by use and not as noise.
- Whether wear reads as designed (the style rule) and not photographic, and whether a mark that passes the dot-size rule
  still reads at phone size.
- Whether a squint-test miss is acceptable (the garden missed at 0.883 and 0.873 against 0.92 and the person decided).
- Paid steps: the person's own clear yes.

How to get those judgements:
- A fresh critic, who has not seen the work, compares it with the best frame made so far; then a skeptic
  checks the findings. After fixing, a fresh checker looks again: fixes make new faults.
- Look at stills at phone size (about 300 px wide) and ask "what else could this read as?".
- Pass this list to the critics with their brief, so they spend their effort where the tools can't.

## 20. Keeping the kit honest

1. Change house numbers only in `film-settings.json`, and mark each one measured, judged or invented with
   its source. *Check:* `python3 calculators/settings.py check`.
2. After changing a tool, run every test: `python3 calculators/tests/run_all.py`. Tests that need the
   austerity project's big pictures skip with a plain message when they are not on the machine.
3. `explainer-film-setup` checks that every kit file a skill names exists. Before trusting an instruction,
   check its file is there.
4. For built-and-painted sets, the rules of logs 30 to 34 (the kit's `docs/paper-look - 07 Composing a shot.md`)
   beat the older rules of log 20 for painted rooms.
5. The place kit's data files (looks, surfaces, roles, facts) are checked by `explainer-film-place check-presets`: every
   number there carries its kind and its source.
6. Known disagreements a person should settle: the default pause after a plain page turn (1.4 s in the
   table, 1.5 s in `estimate_timeline.py`, about 1.3 s from the timing formula); `frame_check.py` still
   warns at 0.87 across, where the rule is 0.90 (`frame_geometry.py boxes` uses 0.90); a state cut at 0.10 or
   0.12 of the frame.
