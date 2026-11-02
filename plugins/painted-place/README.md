# Painted place

What this is: a small Claude plugin for building a place in Blender and bringing it into the series' painted blue-hour look, built so that what was learned once transfers to the next place and the next session. Version 0.2.0, 2 November 2026.

Why it is shaped this way: the record of the earlier plugin (`procedural-textures/Procedural textures - project story.md`, logs 32 to 38) shows that lessons stored as procedure and as the plugin's own building blocks made a model's places worse than its unaided ones (blind scores 2.7 against 6.3 and 6.4), while a visible target, a judge in plain words and one fix pass helped most (6.0 to 7.2). So this plugin carries five things and a loop, and no gate.

## The five things

| Thing | Where | What it is |
|---|---|---|
| The look | `look/The look.md`, `look/reference/` | The target: five reference pictures and one page with the measured bands |
| The judge | `look/measure.py`, `look/judge.py`, `agents/blind-judge.md` | Numbers against the bands, and a blind rubric a fresh model answers in plain words |
| The look stage | `stage/look_stage.py`, `stage/render_small.py` | One function: lights at every glowing window and lamp, the sky rig, the painted sky, haze, Cycles with AgX, the restrained paint filter |
| The dressing | `materials/apply_by_role.py` (with `lay_setts.py`, `lay_facade.py`, `lay_details.py`), `materials/Roles.md`, `materials/Materials.blend` | One call: the street bundle's 45 proven materials by role words; laid setts and flags on flat roads and pavements; flat stone walls built up into ashlar with dressed windows, bands and quoins; and the details from the place's own shape: puddles where lights will mirror, gutter water, damp feet, stains, rust, weeds, moss, rubbish, whitened steps |
| The loop | `skills/make-a-painted-place/SKILL.md` | Build, dress, light and draw small, measure, judge blind, one fix pass, full size once |

## Install

```
/plugin marketplace add AHepi/Music
/plugin install painted-place@ahepi-music
```

Needs Blender 5.1 or later (the look stage uses the 5.1 compositor), or the `bpy` Python module (`pip install bpy==5.1.2`), plus Python with Pillow for the measures. Every command answers `--help`.

## Try it in five minutes

```
cd plugins/painted-place
sh tests/run_tests.sh                                                     # three tests, about a minute
blender -b --python examples/lane-blockout/build_lane.py -- --out /tmp/lane/lane.blend
blender -b --python materials/apply_by_role.py -- --scene /tmp/lane/lane.blend --save-as /tmp/lane/dressed.blend
blender -b --python stage/render_small.py -- --scene /tmp/lane/dressed.blend --out /tmp/lane/round-1.png --rain
python3 look/measure.py /tmp/lane/round-1.png
python3 look/judge.py /tmp/lane/round-1.png --out /tmp/lane/judge-1       # then: "Judge the packet at /tmp/lane/judge-1."
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
- Decisions 50 and 51 in `austerity-explainer/project-notes/Decisions.md`; story logs 38 to 40.

## Traps

- A place laid along X instead of Y gets the stone picture smeared on its long walls (`materials/Roles.md`).
- The look stage replaces the sky; a sunset painted on a dome is gone unless `--keep-world`.
- Measures inside every band do not make a picture right; judge every round.
- One fix pass. The third pass is where the last plugin's costs and procedure grew.
