# Painted place

What this is: a small Claude plugin for building a place in Blender and bringing it into the series' painted blue-hour look, built so that what was learned once transfers to the next place and the next session. Version 0.4.1, 3 November 2026.

Why it is shaped this way: the record of the earlier plugin (`procedural-textures/Procedural textures - project story.md`, logs 32 to 38) shows that lessons stored as procedure and as the plugin's own building blocks made a model's places worse than its unaided ones (blind scores 2.7 against 6.3 and 6.4), while a visible target, a judge in plain words and one fix pass helped most (6.0 to 7.2). So this plugin carries five things and a loop, and no gate.

## The five things

| Thing | Where | What it is |
|---|---|---|
| The look | `look/The look.md`, `look/reference/` | The target: five reference pictures and one page with the measured bands |
| The judge | `look/measure.py`, `look/judge.py`, `agents/blind-judge.md` | Numbers against the bands, and a blind rubric a fresh model answers in plain words |
| The look stage | `stage/look_stage.py`, `stage/render_small.py` | One function: lights at every glowing window and lamp, the sky rig, the painted sky, haze, Cycles with AgX, the restrained paint filter |
| The dressing | `materials/apply_by_role.py` (with `lay_setts.py`, `lay_facade.py`, `lay_timber.py`, `lay_details.py`, `survey.py`, `lay_shore.py`, `lay_trees.py`, `scans.py`), `materials/Roles.md`, `materials/Materials.blend`, `materials/textures/` | One call: the street bundle's 45 proven materials by role words, with a real sandstone's grain laid over its stone, and weathered timber, deck planks, bark, damp sand and driftwood from free photographed scans (Poly Haven, CC0); laid setts and flags on flat roads and pavements; flat stone walls built up into ashlar with dressed windows, bands and quoins; plain timber walls laid as boards; the details from the place's own shape (puddles where lights will mirror, gutter water, damp feet, stains, rust, weeds, moss, rubbish, whitened steps); and, from a survey of what the camera sees, rot and mould up timber, weeds and leaves at the feet of anything standing, sand drifted against things, water's edges (wet ground, foam, a wrack line, driftwood, mossy banks, things wet to the tide line) and what trees drop |
| The loop | `skills/make-a-painted-place/SKILL.md` | Build, dress, light and draw small, measure, judge blind (the look and the request), one fix pass, full size once |

## Install

```
/plugin marketplace add AHepi/Music
/plugin install painted-place@ahepi-music
```

Needs Blender 5.1 or later (the look stage uses the 5.1 compositor), or the `bpy` Python module (`pip install bpy==5.1.2`), plus Python with Pillow for the measures. Every command answers `--help`. With only the `bpy` module, run each script as `python3 SCRIPT ARGS` instead of `blender -b --python SCRIPT -- ARGS`.

## Try it in five minutes

```
cd plugins/painted-place
sh tests/run_tests.sh                                                     # six tests, a few minutes
blender -b --python examples/lane-blockout/build_lane.py -- --out /tmp/lane/lane.blend
blender -b --python materials/apply_by_role.py -- --scene /tmp/lane/lane.blend --save-as /tmp/lane/dressed.blend
blender -b --python stage/render_small.py -- --scene /tmp/lane/dressed.blend --out /tmp/lane/round-1.png --rain
python3 look/measure.py /tmp/lane/round-1.png
python3 look/judge.py /tmp/lane/round-1.png --out /tmp/lane/judge-1 --request "a narrow old lane in the rain"   # then: "Judge the packet at /tmp/lane/judge-1."
```

## What it does not do

- It does not model the place. Shapes are the builder's (a model's or a person's); the plugin dresses them (stones, ashlar, dressings, details) and lights them.
- It does not paint over the render with an image model. For the flatter painted look, the explainer-film plugin's `paint-and-cut` skill does that from the full-size picture.
- It does not make daylight. The look stage is a blue hour; a daylight variant does not exist yet.
- It does not film. A moving camera through a place lit this way is untested (the paint filter and Cycles' noise clean-up could flicker between frames).

## Record

- `examples/coal-mine/`: the transfer test (a place built by others, with its own materials: as it was, the look's defaults, one fix pass).
- `examples/lane-blockout/`: a grey-box lane of 674 named boxes, dressed and lit by the plugin alone; `before and after the details.jpg` shows the same boxes before and after the facade and details step.
- `procedural-textures/40 Blind test - a bach on the beach in Samoa/`: the first blind test. A fresh Sonnet builder with the plugin and six words against the same model with Blender alone; six blind judges all chose the plugin's picture for the film (look lens 5.0 against 1.7), while it lost on photograph and request; level overall.
- `examples/bach-on-the-beach/`: the blind test's bach re-dressed by 0.3.0 (timber, the shore, what the palms drop), from the camera and from a view up the shore.
- `examples/scanned-surfaces/`: the lane and the bach dressed with and without the Poly Haven scans (0.4.0), from the camera and close up.
- Decisions 50 to 54 in `austerity-explainer/project-notes/Decisions.md`; story logs 38 to 43.

## Traps

- A place laid along X instead of Y gets the stone picture smeared on its long walls (`materials/Roles.md`).
- The look stage replaces the sky; a sunset painted on a dome is gone unless `--keep-world`.
- Measures inside every band do not make a picture right; judge every round.
- One fix pass. The third pass is where the last plugin's costs and procedure grew.
