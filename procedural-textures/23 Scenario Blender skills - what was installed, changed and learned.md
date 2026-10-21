# Scenario Blender skills: what was installed, changed and learned (21 October 2026)

What this file is: the record of installing seven of Scenario's Blender skills into the project, what was changed in them before installing, and what four
try-outs on our wet street showed. A "skill" is a folder of written instructions (and sometimes helper scripts) that Claude loads for one kind of task.

## What was installed
In `/home/user/Music/.claude/skills/` (46 files, about 1.4 MB), from Scenario's public repository (MIT licence, version 0.59.0, commit 6e7b8c3 of 20 Oct 2026):
scenario-blender-expert (the main one), -texturing-shading, -uv-baking, -geometry-nodes, -lighting-rendering, -export, -previs-storyboard.
Each folder carries the MIT licence file, as the licence requires. Never copied: Scenario's add-on skill, the blockout skill (it sends work to outside video
services) and the other eight Blender skills.

## How it was checked before installing
* Two helpers per skill read every file in full, the second one looking for what the first missed. All seven were judged safe once edited.
* 83 edits were made to the text, each checked to apply exactly once. A final helper compared the installed files with the download: only those edits and the
  licence files differ. Six of the nine helper scripts are byte for byte as downloaded.

## What was changed, and why
* Every skill told Claude to install missing sibling skills with "npx skills add". Now: "do not install anything, tell the person which skill is missing and
  carry on".
* Scenario's add-on and its live-window bridge are marked "not used here, skip". One line said to start Scenario's add-on server in headless Blender, and one
  said to try a different spelling if a safety filter blocked a quit, reset or delete: both reversed.
* Pointers to skills not installed say "(not installed here)".
* Blender commands in the notes use our Blender's full path, `--disable-autoexec` and a pretend screen (`xvfb-run -a`): tested, Blender stops with a graphics
  error as soon as anything is drawn without it.
* Warnings where a tool changes or wipes an open scene (the review sheet recolours objects; a storyboard template wiped the whole session and now stops with
  an error instead); example paths that wrote into made-up folders now say "use a scratch copy".
* Slow drawing is steered to small sizes or the rented machine; the texturing skill's finished pictures default to EEVEE, our plate renderer.
* Three scripts got tiny changes: two warning comments (bx_gn.py), `--disable-autoexec` on a second Blender launch (bx_export.py), and a guard so the animatic
  step cannot wipe the shot scene (bx_previs.py).
* The main skill's one-line description now says "headless only, no window and no bridge" (a checker pointed out the old wording could nudge Claude towards the
  Blender bridge, which is configured here but not used).

## What the four try-outs on the street showed (pictures: `23 Scenario Blender skills test - pictures/`; picture titles still say 22, their old number)
| Try-out | Worth keeping | Not useful or misleading |
|---|---|---|
| 23a main skill: delivery check and review sheet | Found a real fault nobody had noticed: 73 closed parts are inside-out (69 headframe bars, both winding wheels, 2 engine-house trims). They look fine now, but go see-through if back faces are ever hidden (a game-style viewer). Confirmed nothing floats, no stray scale, no missing UVs; road, kerbs, flags and ground are clean. | On the whole street file it reports 908 "errors": its distances scale with the 3.5 km sky dome. Leave out the sky and far hills and set 1 mm by hand (a wrapper does this). Its review sheet uses fixed views that suit one object, not a street (a main-camera wrapper was written). Its topology warnings are how our kit-built props are made and do not show in a plate. |
| 23b texturing and baking | Edge chips and cavity dirt that follow a prop's real mouldings, which our tile recipes cannot do. Works in EEVEE only after baking it to pictures (tested). | It shows only in Cycles, not in EEVEE, the film's renderer, unless baked. It writes colour and roughness, not height. Its node groups have no seed, so every door would wear the same way (read from the code, not drawn). Its automatic UV seams failed on our finely modelled door; the baked relief failed its own check. Keep our own layers for walls, ground and tiles. |
| 23c lighting and shot planning | Light-and-dark study with the subject outlined; blown and crushed shares; a colour-setting audit (it found data pictures set to colour inside our wetness layer); a lens comparison; a "is the view blocked" test. | Its one-lamp-at-a-time shares mislead on a street full of glowing windows; its subject verdicts are built for faces. Neither adds composition checks like our own shot checker. |
| 23d scatter and export | The scatter builder made a correct litter scatter first time and its counting checks prove it. The export check found three real faults the exporter hides (litter missing unless "realised", cameras dropped, a crash in the comparison). | Scattered litter is too small to read in the film's main camera. The "web" export squeezes shapes lossily (up to 52 mm off on our street) and our stage cannot read squeezed files without one added line. Use it with squeezing off and cameras on (10.2 MB instead of 16.9 MB, lossless). |

## Not tested
* That a fresh Claude session started in `/home/user/Music` lists and loads these skills (this session began before they were installed).
* Many tools: the window-only ones, most light-rig tools, most export presets, moving mannequins and the animatic.
* The "local rules" written into the skills are instructions, not locks.

## Files
* The installer's clean copy, full edit list (every old and new text) and test script: scratch folder `skills_install/` (not in the repository).
* The try-outs' scripts and numbers: `skills_test/` (23a to 23d; large reports left out).
