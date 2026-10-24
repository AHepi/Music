# Handoff: WRITER 2, "text and routing" (lessons round, plugin 1.4.0)

Plain summary: the 40 lessons the audit ranked (A1 to A40) and the partly carried lessons named in the plan (R) are now
written into the skills, agents, workflows, hook, docs and README that I own, as a check wherever one could hold them
(the hook, the workflow, a new test) and as short text elsewhere. Nothing was committed or pushed. No card time was used
(0 seconds). Nothing was written outside the plugin and this folder. No Blender run was needed for my part.

## Files I changed (all inside /home/user/Music/plugins/explainer-film)

- hooks/place-reminder.py (still three lines; no new place words)
- skills: surfaces-wear-and-construction/SKILL.md and its reference files (construction-and-scale.md, the-required-steps.md,
  blender-5-traps.md, wear-recipes.md, surface-recipes.md, style-rule-and-measures.md, rendering-on-rented-cards.md,
  fresh-checkers.md, batched-rounds-and-card-time.md); make-3d-models/SKILL.md; build-and-paint-a-place/SKILL.md;
  make-explainer-film/house-rules.md and SKILL.md; paint-and-cut/SKILL.md; check-and-critique/SKILL.md; check-facts/SKILL.md;
  film-and-finish/SKILL.md; build-cinema-page/SKILL.md and guide.md
- agents: place-planner, place-builder, place-integrator, place-renderer, place-checker, film-critic, fact-checker
  (page-builder unchanged: no lesson was routed to it)
- workflows: build-a-place.js, critique-film.js, verify-facts.js
- kit/docs: LLM tips and tricks.md (sections 0, 7, 10, 16, 19; no section renumbered), paper-look 00, 01, 02, 04, 05, 06, 07
- README.md (version stays 1.4.0; plugin.json untouched)
- new: kit/examples/house-sample/00 About this example.md
- tests: test_place_hook.py, test_build_a_place_workflow.py, new fixture fixtures/place-workflow/render-first-view.json,
  new test_lessons_text.py

## What was done, lesson by lesson

- A1 (dark/wet look): build-and-paint-a-place section 7 (toe 1, vignette 0.25, `after_painting.py check --toe 1` "arrives at",
  under about 0.9 invented, tell the person when two shots differ); doc 05 block copied from the film kit and reworded.
- A2 (wet and dry as a pair): build-and-paint-a-place 5b and traps ("pale patch" from `--behind`); tips 10.2; doc 05.
- A3 (several draws, control): tips 0.13; fresh-checkers.md; check-and-critique section 4; doc 05 trap; cites
  `calculators/regression_compare.py --old --new`.
- A4 (routing to the film frame): hook line 2; REQUIRED block line 5 in the three skills (identical); pointers at the top of
  make-3d-models and the surfaces skill; build-a-place.js `film: true` (views 1080 x 1920, tall previews 540 x 960, planner
  runs plan_shot.py and writes "for_film": true); place-planner item 10.
- A5 (history critic, pictures to the fact checker): critique-film.js new critic keyed `history` (output keeps {critics, verdict};
  every picture critic and the history critic told to read section 19); phone-button numbers now 0.90 across / 0.80 down;
  verify-facts.js takes `pictures` and `propLettering` (dates with weekdays); check-and-critique, check-facts, film-critic,
  fact-checker, place-checker (period check in Mode look), tips section 19.
- A6 (the world round the place): construction-and-scale.md new section (role `backdrop`, "place: world", no haze); build-a-place
  planner prompt and ground block ("every named view must see a finished horizon"); place-planner, place-integrator.
- A7 (low sun): the-required-steps Step 7 ("place: sun"); tips 7.12.
- A8 (lettering): paint-and-cut explains blank placards; make-3d-models and build-and-paint-a-place carry the rule and
  "place: lettering".
- A9 (privacy): house rules (new Privacy section); surface-recipes (every site); place-builder; place-checker process mode
  (web-request scripts); build-a-place RULES; doc 06.
- A10 (never message a paying helper): house rules; batched-rounds file ("already has a job in flight"); place-builder,
  place-renderer; build-a-place RULES (every prompt but the blind reader's); tips 16.10; doc 06.
- A11 (start small): house rules; build-and-paint-a-place top; place-planner; build-a-place.js `firstViewOnly` default TRUE (the run
  draws only the first view's small picture and stops "for the person's reaction"; `allViews: true` or `firstViewOnly: false` goes on);
  README; doc 06. The harness carried it: the existing cases now pass `allViews: true`.
- A12 (dollar signs): house rules; tips 16.8; film-and-finish; place-renderer; place-checker; doc 05 trap; doc 06.
- A13 (lower quarter): paint-and-cut, docs 01, 02, 04 say "paper route only" and 0.70 down; doc 04's prompt rows left as they were.
- A14 (the person's "no plugin" wins): hook prints nothing for plain Blender / without the plugin / do not (don't) use the plugin /
  do not use the skill; REQUIRED block line; house rules; README exception; doc 06.
- A15 (never overwrite; keep the old beside the new): house rules; build-and-paint-a-place 5b; place-builder; doc 06.
- A16 (wrapping up): house rules (new section); doc 06.
- A17 (one renderer per place): build-and-paint-a-place section 6; rendering-on-rented-cards section 1; place-renderer.
- A18 (what the method cannot do): build-and-paint-a-place top; README.
- A19 (wear reads the scene's sun): the-required-steps Step 7; wear-recipes.
- A20 (DirectX normal maps): surface-recipes rule 2 (raking-light panels, flip green in a copy).
- A21 (Blender 5.2 traps 17, 18; setup probe): blender-5-traps.md.
- A22 (bulk building, objects_total_max): blender-5-traps trap 19; place-builder.
- A23 (thread limit): blender-5-traps trap 20; build-a-place.js (`blenderThreads`, default 2; EXPLAINER_FILM_BLENDER_THREADS and
  blender -t in every prompt's Blender text); place-builder, place-integrator.
- A24 (hide one group at a time): build-and-paint-a-place traps; tips 7.13.
- A25 (names and dates on props): build-and-paint-a-place step 2; check-facts; verify-facts.js; fact-checker; place-checker.
- A26 (two buildings tellable apart): build-and-paint-a-place step 2 (judged, no tool); place-planner item 11; place-checker
  (blind reader says what looks alike; the same neutral sentence is in the workflow's blind prompt).
- A27 (house look rejected): new kit/examples/house-sample/00 About this example.md; doc 00; guide.md; README.
- A28 (the person's words for the look): style-rule-and-measures; place-planner item 6.
- A29 (plain sky): build-and-paint-a-place 4b ("clouds" LOOK).
- A30 (concept pictures): style-rule-and-measures; place-planner item 6.
- A31 (versions of the same scene): house rules; build-and-paint-a-place top; doc 06.
- A32 (what an allowance covers): house rules; make-explainer-film SKILL.md money lines; tips 16.9.
- A33 (re-read notes against data): house rules; fresh-checkers; place-checker process mode; doc 06.
- A34 (controls, several seeds): fresh-checkers.
- A35 (clip judged in motion): check-and-critique new section 5; film-and-finish; film-critic clip mode (writes the clip critique
  JSON in the contract's shape; `explainer-film-preflight finish --clip-critique FILE`).
- A36: not mine (code writer: kit-sync-notes and the setup command).
- A37 (read Decisions.md first): house rules; doc 06.
- A38 (free disk first): blender-5-traps trap 16; tips 0.14 (uses `df -h`; I did not claim the preflight prints the free disk).
- A39 (banding): film-and-finish.
- A40 (aesthetic handover; effort per job): house rules; doc 06.
- R lessons named in the plan, all done: public repository and blocked saves, uploaded add-on (house rules, place-builder);
  reports with the original beside the new, checklist not proof, worse keeps the old (house rules, fresh-checkers, place-checker);
  painting gives way to the behind painting at once, twin plate and brightness match, slide checklist, define a place's look once
  (build-and-paint-a-place); sky dome out of the inside-out count (construction-and-scale); warm fill at dusk (Step 7); try unused
  tools on tiny meshes (trap 21); distant ground quiet, .glb maps never reach the film (wear-recipes); displacement memory, trees,
  no doubled moss and no normal map plus bump, the rejected painterly library (surface-recipes); rank fixes (style rule); EEVEE
  against Cycles findings, light groups (rendering-on-rented-cards); drawing time from surfaces (make-3d-models); one way of
  making pictures (build-cinema-page); lit rooms (tips 7.14); a picture must not contradict its own rule, arrows and number
  boards (tips 19); authority object big and further back, composition by a picture program (doc 07).

## Names from the contract that my text cites (the code writer makes them)

regression_compare.py; after_painting.py `--behind` "pale patch", `--toe` "arrives at", LOOK "bottom fifth", LOOK "clouds";
"for_film" and "place: film frame"; role `backdrop` and "place: world"; "place: sun"; "place: lettering";
place_audit.objects_total_max; EXPLAINER_FILM_BLENDER_THREADS; `card-time check` "already has a job in flight";
list_prop_lettering.py --out; plan_budget.py push (email, dollar sign) and "For helper briefs:"; the film stage's history area;
`--clip-critique`; the plates stage's engine LOOKs; the "Blender 5.2 probe"; the wear masks reading the scene's sun.
Two behaviours I describe that are in the code writer's task list but not in the names contract, for the verify step to check:
"the audit prints which sun direction it used" (the-required-steps Step 7) and "the setup probe also reads one pairing"
(blender-5-traps trap 18).

## Tests run and results

While working, by name: test_place_hook (57 of 57), test_place_batching_rule (27 of 27), test_place_skills (70 of 70 once the
code writer's names existed), test_place_generic (18 of 18), test_build_a_place_workflow (142 of 142, up from the earlier count:
new cases for start small, film, threads, the world, the no-message rule and one more mutation), test_lessons_text (22 of 22),
test_house_rules (5 of 5). Each new check in test_lessons_text is also tried on a wrong text and fails there.
The critique-film and verify-facts workflows were also run with stand-in helpers (node): the critics' areas include "history",
and the pictures and prop lettering reach the claim splitter and the checkers.

Whole suite (python3 kit/calculators/tests/run_all.py):
- Baseline before my edits, without Blender: 43 files, 39 passed, 0 failed, 4 skipped.
- Final, without Blender (after both writers finished): 51 files, 46 passed, 0 failed, 5 skipped; 1,763 checks passed. 4 min 10 s.
- Final, with BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender: 51 files, 48 passed, 1 FAILED, 2 skipped;
  2,020 checks passed, 1 failed. 13 min.
  The failure is NOT in my files: test_place_blender.py, "the yard finishes and passes the audit": the code writer's new check
  "place: world" now FAILs the old test yard ("Camera A: 138 of its 512 rays below the horizon hit nothing (27%): the view sees past
  the edge of the ground into empty sky"). The yard was built before the world rule; either the test yard needs a backdrop and
  more ground, or the test should accept that FAIL as the new rule working. It is the code writer's file and check, so I did not
  touch it.
- Earlier runs during the round showed failures that the code writer has since fixed (check_presets finding the word "mine" in
  place_kit/cli.py's note, the hut audit warning, the roles test, the invented-number share in test_settings) and my own
  citations of contract names before they existed (`--clip-critique`, `place_audit.objects_total_max`, `list_prop_lettering.py`):
  all gone in the final runs.

## Not done, and why

- page-builder.md: no lesson was routed to it.
- The hook's format was still not run inside Claude Code itself (only through its tests), as before.
- Nobody has tested that a smaller model, given only the plugin and a plain request, uses these lessons unprompted.
- The build-a-place workflow's new behaviour (start small, film, threads) was run only with canned helpers, not under the real
  Workflow tool.
- I wrote no requests for the other writer: none of my lessons needed a change in their files.

## Card time

None used (0 seconds). No paid step of any kind.
