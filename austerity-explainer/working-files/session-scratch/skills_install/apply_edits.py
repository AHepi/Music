#!/usr/bin/env python3
"""Apply reviewed text edits to the STAGED copies only. Each old text must occur exactly once.
Usage: apply_edits.py <staging_dir> [--dry]
Prints one line per edit; writes a JSON log to <skills_install>/edit_log.json
"""
import json
import os
import sys

STAGING = sys.argv[1]
DRY = "--dry" in sys.argv
EXP = "scenario-blender-expert"
TEX = "scenario-blender-texturing-shading"
UVB = "scenario-blender-uv-baking"
GNO = "scenario-blender-geometry-nodes"
LIT = "scenario-blender-lighting-rendering"
EXPT = "scenario-blender-export"
PRV = "scenario-blender-previs-storyboard"

EDITS = []


def E(skill, rel, old, new, why):
    EDITS.append((skill, rel, old, new, why))


XV = "xvfb-run -a /home/user/work/blender-app/blender-5.2.2-linux-x64/blender"

# ============================================================ scenario-blender-expert
E(EXP, "SKILL.md",
  r'''If a sibling skill named here is missing from
your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.''',
  r'''If a sibling skill named here is missing from
your available skills, do not install anything: tell the person which skill is missing and carry on
without it (proceed from tool schemas and flag the gap).''',
  "remove npx self-install instruction (must-change)")

E(EXP, "SKILL.md",
  r'''## 1. Execution channel
''',
  r'''## 1. Execution channel

**Local rules for this project (they override everything below):** run Blender only as `''' + XV + r''' -b --disable-autoexec --factory-startup --python-exit-code 1 -P script.py -- args` (plain `blender` is not on the search path; `xvfb-run -a` gives Blender a virtual screen, not a window, and without it Blender stops with "Couldn't open libEGL.so.1" as soon as a script renders or uses the graphics side, which includes the Workbench review sheets). Headless only: never open a Blender window and never use a live GUI session, an MCP bridge or the Scenario Blender Plugin. Never install anything (no `npx`, `pip`, add-ons or extensions), never sign in to or call an outside service, and do not load add-ons. Do not render the film's plates or run EEVEE or Cycles animation or bake jobs on this shared computer (they are slow): those go to the rented machine with the project's render guide; only the quick Workbench review sheets and the audits of this skill run here. Write output only to a scratch folder, keep it small (disk is tight) and delete it when done.
''',
  "local rules paragraph (second reader); wording adjusted: tested here, Blender starts without xvfb-run for plain scripts but fails with libEGL once anything renders")

E(EXP, "SKILL.md",
  r'''**Live GUI Blender** (user's session over the MCP bridge)''',
  r'''**Live GUI Blender** (not used here: no Blender window is ever opened, so never use a live session or an MCP bridge) (user's session over the MCP bridge)''',
  "second reader's better wording")

E(EXP, "SKILL.md",
  r'''`blender -b [file] --factory-startup --python-exit-code 1 -P x.py -- args`''',
  r'''`''' + XV + r''' -b --disable-autoexec [file] --factory-startup --python-exit-code 1 -P x.py -- args`''',
  "full path, xvfb-run, --disable-autoexec (second reader's better edit)")

E(EXP, "SKILL.md",
  r'''`blender --background scene.blend --command scenario_blender`, is the exception because it needs''',
  r'''`blender --background scene.blend --command scenario_blender` (NEVER run this here: the Scenario add-on is not installed, no add-on or extension is ever loaded, and `--factory-startup` has no exception), would be the exception because it needs''',
  "stop the Scenario add-on headless-server exception (must-change, second reader)")

E(EXP, "SKILL.md",
  r'''**Live channel: the Scenario Blender Plugin.**''',
  r'''**Live channel: the Scenario Blender Plugin (not used here: the Scenario add-on is not installed and no Blender window is ever opened, so skip this whole section).**''',
  "second reader's better wording")

E(EXP, "SKILL.md",
  r'''results are the `scenario-blender` skill's work;''',
  r'''results are the `scenario-blender` (not installed here) skill's work;''',
  "not-installed note")

E(EXP, "SKILL.md",
  r'''spelling (quit, factory reset, file deletion) changed nothing: rewrite the call.''',
  r'''spelling (quit, factory reset, file deletion) changed nothing: do not try another spelling of the same action; stop and tell the person.''',
  "do not work around a refused call (must-change, second reader)")

E(EXP, "SKILL.md",
  r'''`scenario-blender-sculpting/scripts/bx_sculpt.py`''',
  r'''`scenario-blender-sculpting/scripts/bx_sculpt.py` (not installed here)''',
  "not-installed note")

E(EXP, "SKILL.md",
  r'''## 3. Persona pipelines
''',
  r'''## 3. Persona pipelines

Only scenario-blender-expert, scenario-blender-texturing-shading, scenario-blender-uv-baking, scenario-blender-geometry-nodes, scenario-blender-lighting-rendering, scenario-blender-export and scenario-blender-previs-storyboard are installed here. Every other skill named in this table (sculpting, retopology, hair, hard-surface, rigging, animation, grease-pencil, scenario-3d, scenario-textures) is NOT installed: skip that step, do not install it and do not use any outside service for it.
''',
  "installed-skills sentence (second reader)")

E(EXP, "SKILL.md",
  r'''scenario-blender-sculpting, scenario-blender-retopology, scenario-blender-uv-baking, scenario-blender-texturing-shading, scenario-blender-hair''',
  r'''scenario-blender-sculpting (not installed here), scenario-blender-retopology (not installed here), scenario-blender-uv-baking, scenario-blender-texturing-shading, scenario-blender-hair (not installed here)''',
  "not-installed notes (character artist row)")

E(EXP, "SKILL.md",
  r'''scenario-blender-retopology (or cleanup + remesh)''',
  r'''scenario-blender-retopology (not installed here) (or cleanup + remesh)''',
  "not-installed note")

E(EXP, "SKILL.md",
  r'''generation itself: scenario-3d''',
  r'''generation itself: scenario-3d (not installed here)''',
  "not-installed note (Scenario AI generation service)")

E(EXP, "SKILL.md",
  r'''scenario-blender-hard-surface or scenario-blender-sculpting, scenario-blender-retopology (game budget)''',
  r'''scenario-blender-hard-surface (not installed here) or scenario-blender-sculpting (not installed here), scenario-blender-retopology (not installed here) (game budget)''',
  "not-installed notes (game asset row)")

E(EXP, "SKILL.md",
  r'''scenario-blender-rigging''',
  r'''scenario-blender-rigging (not installed here)''',
  "not-installed note (rigger row)")

E(EXP, "SKILL.md",
  r'''scenario-blender-animation''',
  r'''scenario-blender-animation (not installed here)''',
  "not-installed note (animator row)")

E(EXP, "SKILL.md",
  r'''scenario-blender-previs-storyboard, scenario-blender-grease-pencil''',
  r'''scenario-blender-previs-storyboard, scenario-blender-grease-pencil (not installed here)''',
  "not-installed note (story/previs row)")

E(EXP, "SKILL.md",
  r'''| scenario-blender-grease-pencil''',
  r'''| scenario-blender-grease-pencil (not installed here)''',
  "not-installed note (2D animator row)")

E(EXP, "SKILL.md",
  r'''scenario-3d (generate meshes to finish here), scenario-textures (AI''',
  r'''scenario-3d (not installed here) (generate meshes to finish here), scenario-textures (not installed here) (AI''',
  "not-installed notes (Scenario AI generation skills)")

E(EXP, "SKILL.md",
  r'''`blender -b f.blend --python bx_audit.py -- --object Name [--high Sculpt] [--json out.json]`''',
  r'''`''' + XV + r''' -b --disable-autoexec f.blend --factory-startup --python-exit-code 1 -P bx_audit.py -- --object Name [--high Sculpt] [--json out.json]`''',
  "full path, xvfb-run, --disable-autoexec (second reader)")

E(EXP, "SKILL.md",
  r'''CLI, exit code 2 on failure:''',
  r'''CLI, exit code 2 on failure (`--import` first empties that Blender process, so use it only in a throwaway headless run with nothing unsaved):''',
  "warn that --import wipes the process (first reader)")

E(EXP, "SKILL.md",
  r'''`blender -b --factory-startup --python-exit-code 1 -P bx_audit.py -- --deliverable [--import model.glb | --objects A B] --profile game [--json out.json]`''',
  r'''`''' + XV + r''' -b --disable-autoexec --factory-startup --python-exit-code 1 -P bx_audit.py -- --deliverable [--import model.glb | --objects A B] --profile game [--json out.json]`''',
  "full path, xvfb-run, --disable-autoexec (second reader)")

E(EXP, "SKILL.md",
  r'''user settings untouched; `playblast(out_path, res_pct=50)`;''',
  r'''user preferences untouched, but the default `wire` mode overwrites the Object Color of the objects you pass in (leave `wire` out of `modes` to avoid it) and `playblast` resets the scene's still-image format to 8-bit PNG and its video container and codec, and renders the whole frame range, so run `playblast` only on a throwaway copy of the .blend, with the frame range set first, and never save that copy afterwards; `playblast(out_path, res_pct=50)`;''',
  "measured side effects of bx_review (second reader)")

E(EXP, "SKILL.md",
  r'''`bx_gui.py`: real brushes in a live session:''',
  r'''`bx_gui.py` (not usable here, it needs a window): real brushes in a live session:''',
  "bx_gui needs a window (first reader)")

E(EXP, "SKILL.md",
  r'''`import sys; sys.path.append("<this skill>/scripts"); import bx_audit, bx_review`''',
  r'''`import sys; sys.dont_write_bytecode = True; sys.path.append("<this skill>/scripts"); import bx_audit, bx_review` (the second statement stops Python writing a `__pycache__` folder into the installed skill folder)''',
  "no __pycache__ in the installed folder (second reader)")

E(EXP, "references/bpy-reliability.md",
  r'''`blender -b [file.blend] --factory-startup --python-exit-code 1 -P script.py -- <args>`''',
  r'''`''' + XV + r''' -b --disable-autoexec [file.blend] --factory-startup --python-exit-code 1 -P script.py -- <args>`''',
  "full path, xvfb-run, --disable-autoexec (second reader)")

E(EXP, "references/bpy-reliability.md",
  r'''After a rerun: `bpy.data.orphans_purge(do_recursive=True)` removes nothing new''',
  r'''After a rerun (only in a throwaway copy: it really deletes every unused data-block in the open session): `bpy.data.orphans_purge(do_recursive=True)` removes nothing new''',
  "orphans_purge is a real purge (second reader)")

E(EXP, "references/bpy-reliability.md",
  r'''`bpy.ops.wm.save_as_mainfile(filepath=abs_path)`.''',
  r'''`bpy.ops.wm.save_as_mainfile(filepath=abs_path)` (abs_path is a new file in a folder the person named, never the file the job opened).''',
  "do not overwrite the opened file (first reader)")

E(EXP, "references/bpy-reliability.md",
  r'''`blender -b scene.blend --factory-startup --python-exit-code 1 -P setup.py -E CYCLES -o /abs/out/frame_#### -F PNG -f 10`''',
  r'''`''' + XV + r''' -b --disable-autoexec scene.blend --factory-startup --python-exit-code 1 -P setup.py -E CYCLES -o /abs/out/frame_#### -F PNG -f 10` (an example of the flag ORDER only: on this shared computer never run a Cycles or EEVEE render like this; use `-E BLENDER_WORKBENCH` for quick looks and send real renders to the rented machine)''',
  "P8 is an example only (second reader)")

E(EXP, "references/bpy-reliability.md",
  r'''/Applications/Blender.app/Contents/Resources/5.2/scripts/startup/bl_ui/*.py''',
  r'''/home/user/work/blender-app/blender-5.2.2-linux-x64/5.2/scripts/startup/bl_ui/*.py''',
  "Mac path replaced by this computer's path (first reader)")

E(EXP, "references/blender-5.2-deltas.md",
  r'''/Applications/Blender.app/Contents/Resources/5.2/datafiles/assets/brushes/''',
  r'''/home/user/work/blender-app/blender-5.2.2-linux-x64/5.2/datafiles/assets/brushes/''',
  "Mac path replaced by this computer's path (first reader)")

# ============================================================ scenario-blender-texturing-shading
E(TEX, "SKILL.md",
  r'''If a sibling skill named here is missing from your available skills, ask the user
to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool
schemas and flag the gap.''',
  r'''If a sibling skill is missing, do not install anything: tell the person which skill is missing and carry
on without it.''',
  "remove npx self-install instruction (must-change)")

E(TEX, "SKILL.md",
  r'''(execution channel, review loop, 5.2 API changes)''',
  r'''(execution channel, review loop, 5.2 API changes; here use only its headless channel, never an MCP bridge, add-on or live window)''',
  "headless channel only (first reader)")

E(TEX, "SKILL.md",
  r'''import bx_materials as M`.''',
  r'''import bx_materials as M`.

On this shared computer: call `M.preview` only with `engines=("BLENDER_EEVEE",)`, `res=256`, `samples=8` and an `out_dir` inside the scratch folder (its default also renders Cycles at 64 samples on the CPU, which is slow here). `M.value_report` is cheap (six small renders) but also needs a scratch `out_dir`. The Cycles half of every check runs on the rented machine. Never pass the film project's folder as `out_dir` or as a `save_image` path.''',
  "slow-render guard at the top of the toolkit section (second reader)")

E(TEX, "SKILL.md",
  r'''Cycles finals, EEVEE side by side''',
  r'''EEVEE finals (our plate renderer), Cycles as a check''',
  "default to EEVEE finals (first reader)")

E(TEX, "SKILL.md",
  r'''GUI: brushes are assets''',
  r'''GUI (needs a live window: not available here, use the Headless route below): brushes are assets''',
  "live-window route not usable (first reader)")

E(TEX, "SKILL.md",
  r'''`M.preview` (EEVEE and Cycles, studio, backlit, roughness),''',
  r'''`M.preview` (EEVEE and Cycles, studio, backlit, roughness; on the shared computer pass `engines=("BLENDER_EEVEE",)`, `res=256`, `samples=8` and leave the Cycles half to the rented machine),''',
  "slow-render guard (first reader)")

E(TEX, "references/critique.md",
  r'''EEVEE and Cycles), open the sheet,''',
  r'''EEVEE only here via `engines=("BLENDER_EEVEE",), res=256, samples=8`; the Cycles half runs on the rented machine), open the sheet,''',
  "slow-render guard in the rubric (second reader)")

E(TEX, "references/expert-notes.md",
  r'''Load Factory Settings when lost''',
  r'''Load Factory Settings when lost (a GUI habit from the video; never do it here, it wipes the open session)''',
  "never reset the session (first reader)")

E(TEX, "references/procedures.md",
  r'''## P9. Anisotropic hair or brushed metal (Cycles only)''',
  r'''## P9. Anisotropic hair or brushed metal (Cycles only; not for our EEVEE plates: it aims the Material Output at CYCLES, so EEVEE ignores that output)''',
  "EEVEE trap (second reader)")

# ============================================================ scenario-blender-uv-baking
E(UVB, "SKILL.md",
  r'''sibling skill named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.''',
  r'''sibling skill is missing, do not install anything: tell the person which skill is missing and carry on without it.''',
  "remove npx self-install instruction (must-change)")

E(UVB, "SKILL.md",
  r'''Metal GPU, headless''',
  r'''Metal GPU on a Mac, headless (CPU-only: far slower)''',
  "timing caveat (second reader)")

E(UVB, "SKILL.md",
  r'''- `scripts/bx_uvbake.py`: the module (docstrings list every function).''',
  r'''- `scripts/bx_uvbake.py`: the module (docstrings list every function).

## Local setup notes (this project, added after reading)

- Blender 5.2.2, headless only (`-b --disable-autoexec`); nothing here needs a window. The module was
  tested on 5.2.1, so check the first run on 5.2.2.
- The four picture-review functions (`checker_review`, `distortion_review`, `map_problem_review`,
  `bake_review`) import `bx_review` from the `scenario-blender-expert` folder next to this one. Keep
  the folders side by side, also when copying them to the rented machine, and install nothing.
- Baking needs Cycles (EEVEE cannot bake). `bake_high_to_low` switches the scene to Cycles and puts
  the engine back afterwards; the film's plate renderer stays EEVEE. In a background run it also
  switches Blender's Cycles graphics-card setting in memory (nothing here saves preferences).
- This computer is shared and slow. Test bakes at `res=512` with `adaptive=False` (the adaptive bake
  repeats every map five times). `bake_review` makes 12 EEVEE pictures: pass `views=("threequarter",)`
  and a small `res`, or ask the person whether to run it on the rented machine.
- Work on a duplicate object or a new UV map (`uv_map=`), never on the film's own objects.
  `unwrap`, `pack`, `prepare_low` and `hookup_maps` change the object, or its materials (which other
  objects may share), in place. `unwrap` overwrites the UV map with a placeholder first and restores
  it only when it succeeds, so an error halfway leaves the UVs ruined. Call `explode` once and
  `unexplode` after the bake.
- Every bake leaves its image in the open Blender session (about 64 MB each at 2048) and may add a
  material or a World if the scene had none. Use a throwaway scene or a fresh Blender process per
  bake, and do not save the film's .blend afterwards.
- `bake_id` picks colours with Python's `hash()`, which changes from run to run: read the colours back
  from the map each time.
- Run the raw snippets in `references/procedures.md` only in a scratch session, never in the film
  project: they add demo objects, some switch the engine to Cycles or hide other objects from render
  without restoring, and `s2a_bake` writes a small PNG into Blender's temp folder.''',
  "local setup notes (second reader's merged version)")

# ============================================================ scenario-blender-geometry-nodes
E(GNO, "SKILL.md",
  r'''If a sibling skill named here is missing from your
available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`);
unattended, proceed from tool schemas and flag the gap.''',
  r'''If a sibling skill named here is not installed, do not install, download or ask for anything: carry on without it.''',
  "remove npx self-install instruction (must-change, second reader's wording)")

E(GNO, "SKILL.md",
  r'''Curl, Hair Dynamics grooms): scenario-blender-hair.''',
  r'''Curl, Hair Dynamics grooms): scenario-blender-hair (not installed here; ignore this pointer and do not try to fetch it).''',
  "not-installed note (second reader's wording)")

E(GNO, "SKILL.md",
  r'''(headless or live, idempotent:''',
  r'''(headless only here, with no Blender window; idempotent:''',
  "no live window (second reader)")

E(GNO, "references/procedures.md",
  r'''for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
''',
  r'''# TEST HARNESS ONLY: the next two lines delete EVERY object in the open file. Never run them in a session that holds the person's scene; use a fresh headless run.
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
''',
  "warn before the delete-all-objects test harness (first reader)")

E(GNO, "references/procedures.md",
  r'''obj.rotation_euler = (math.pi, 0, 0); bpy.context.view_layer.update(); obj.update_tag()''',
  r'''# NOTE: this changes the object's rotation. Run the probe on a scratch copy of the object, or save tuple(obj.rotation_euler) first and put it back afterwards.
obj.rotation_euler = (math.pi, 0, 0); bpy.context.view_layer.update(); obj.update_tag()''',
  "comment: probe changes rotation (second reader)")

E(GNO, "scripts/bx_gn.py",
  r'''    Returns the sheet path; a <path>_legend.txt lists the tiles."""''',
  r'''    Returns the sheet path; a <path>_legend.txt lists the tiles.

    CAUTION: it renders the OPEN scene itself, so that scene's compositor, sequencer and output
    settings apply, and it overwrites files named like <path> and <path>_f0001_<view>.png. Use it on a
    scratch copy of the scene, point path at a scratch folder, and delete the tile PNGs afterwards."""''',
  "docstring caution (second reader)")

E(GNO, "scripts/bx_gn.py",
  r'''def free_bake(obj):
    with _Selected(obj):
        return bpy.ops.object.simulation_nodes_cache_delete(selected=True)''',
  r'''def free_bake(obj):
    """Delete the simulation caches and bakes of obj. If a modifier bakes to DISK this can also remove
    that bake folder (its path comes from the modifier). Use only on a scratch object baked with bake()."""
    with _Selected(obj):
        return bpy.ops.object.simulation_nodes_cache_delete(selected=True)''',
  "docstring caution (second reader)")

# ============================================================ scenario-blender-lighting-rendering
E(LIT, "SKILL.md",
  r'''ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`);''',
  r'''do not install anything: tell the person which skill is missing and carry on without it;''',
  "remove npx self-install instruction (must-change)")

E(LIT, "SKILL.md",
  r'''scenario-blender-previs-storyboard (shot planning, cameras).''',
  r'''scenario-blender-previs-storyboard (shot planning, cameras).

**Local rules for this install (added by the person who installed it):** run Blender only headless (`-b --disable-autoexec`); never open a window and never use a live or bridge session. The `BL.*` helpers that set things (`aim_camera_at_frame_point`, `preset_eevee`, `preset_cycles`, `color_setup`, `working_space`, `outdoor_sun_sky`, `split_world`, `world_gradient`, `haze`, `comp_tree`, `comp_finish`, `light_groups`, `lightgroup_mix`, `register_aovs`, `freestyle`, `outline_hull`) change the open scene in memory: use them on a scratch copy, never on the film project's own files, and do not save over a scene that must stay as it was. Write every picture, EXR and sheet into the scratchpad folder (never into the film project, and never a made-up path such as `/abs/out`), keep them small (`pct=25`, `exr=False`) and delete the big ones afterwards. Cycles renders, `bake_probes` and `light_contributions` are slow on the shared computer: do them on the rented machine or skip them. Never run npx, npm or pip, and never open or download the video links in `references/sources.md`.''',
  "local rules paragraph (second reader)")

E(LIT, "SKILL.md",
  r'''Import: `sys.path.append("<this skill>/scripts"); import bx_light as BL`.''',
  r'''Import: `import sys; sys.dont_write_bytecode = True; sys.path.append("<this skill>/scripts"); import bx_light as BL` (the first statement stops Python writing a `__pycache__` folder into the skill).''',
  "no __pycache__ in the installed folder (second reader)")

E(LIT, "SKILL.md",
  r'''`BL.aim_camera_at_frame_point(head, 1/3 or 2/3, 0.62)` for look room, and 80 mm for boxy''',
  r'''`BL.aim_camera_at_frame_point(head, 1/3 or 2/3, 0.62)` for look room (it ROTATES the scene camera: use it only on a scratch copy, and skip it when the camera is already fixed), and 80 mm for boxy''',
  "camera-rotation caution (second reader)")

E(LIT, "references/procedures.md",
  r'''BL.file_output(tree, "//exr/", {"rebuilt": rebuilt, "image": rl.outputs["Image"]}, depth="32")''',
  r'''BL.file_output(tree, OUT_DIR + "/exr/", {"rebuilt": rebuilt, "image": rl.outputs["Image"]}, depth="32")  # set OUT_DIR first, to a folder in the scratchpad''',
  "no relative output path (second reader's better edit)")

E(LIT, "references/procedures.md",
  r'''L = BL.new_light("Key", "AREA")''',
  r'''L = BL.new_light("BX_TestKey", "AREA")''',
  "do not take over a real light named Key (second reader)")

E(LIT, "references/procedures.md",
  r'''It works in a live GUI session too (object mode).''',
  r'''Here it is always run headless (never open a Blender window). Paths such as `/abs/out/...` in the examples are placeholders: replace them with a folder in the scratchpad.''',
  "no live GUI, placeholder paths (second reader)")

E(LIT, "references/sources.md",
  r'''Fifteen videos, distilled into `notes/lighting/` (one note each) and two digests''',
  r'''Reference list only: do not open, fetch or download any link or video named here. Fifteen videos, distilled into `notes/lighting/` (one note each) and two digests''',
  "do not fetch links (second reader)")

# ============================================================ scenario-blender-export
E(EXPT, "SKILL.md",
  r'''If a sibling skill named here is missing from your available skills,
ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended,
proceed from tool schemas and flag the gap.''',
  r'''If a sibling skill is missing, do not install anything: tell the person which skill is missing and carry on without it.''',
  "remove npx self-install instruction (must-change)")

E(EXPT, "SKILL.md",
  r'''**Engine check:** import into the engine and look, with `scenario-unity-pipeline-automation`,
   `scenario-unreal-pipeline-automation` or `scenario-godot-pipeline-automation`.''',
  r'''**Engine check:** skip it here. No game engine is installed and the Unity, Unreal and Godot
   pipeline skills it names are not installed; do not install them. Say in your report that the
   engine check was not done.''',
  "skip the engine check (second reader's better edit)")

E(EXPT, "SKILL.md",
  r'''Building ARKit or viseme sets is `scenario-blender-rigging`'s work.''',
  r'''Building ARKit or viseme sets is the work of `scenario-blender-rigging` (not installed here).''',
  "not-installed note (first reader)")

E(EXPT, "SKILL.md",
  r'''bpy.ops.wm.read_factory_settings(use_empty=True)''',
  r'''bpy.ops.wm.read_factory_settings(use_empty=True)   # wipes the open scene: only in a throwaway run, never on a scene you still need''',
  "warning comment (first reader)")

E(EXPT, "SKILL.md",
  r'''Open the report before calling the batch done.''',
  r'''Open the report before calling the batch done. Use an output folder that is not the input folder (same-named files in it are overwritten), and run it only in its own headless Blender, since every file is loaded into a wiped, empty scene.''',
  "batch warning (first reader)")

E(EXPT, "SKILL.md",
  '''blender -b --factory-startup --python-exit-code 1 -P bx_export.py -- ''' + chr(92),
  XV + ''' -b --disable-autoexec --factory-startup --python-exit-code 1 -P bx_export.py -- ''' + chr(92),
  "full path, xvfb-run, --disable-autoexec (second reader)")

E(EXPT, "SKILL.md",
  r'''Join them (`bpy.ops.object.join` with
the parts selected) for a single static prop, then gate again.''',
  r'''Join them (`bpy.ops.object.join` with
the parts selected; it merges the objects and removes the originals, so do it only in a throwaway run, never on a scene you still need) for a single static prop, then gate again.''',
  "join warning (second reader)")

E(EXPT, "references/engines.md",
  r'''Vendor pages were read on 2026-10-18: check them again
before relying on a number in a new engine version.''',
  r'''Vendor pages were read on 2026-10-18. Do not open them from here (no outside services are used);
if a number matters for a newer engine version, tell the person it needs checking.''',
  "no outside web pages (second reader)")

E(EXPT, "scripts/bx_export.py",
  r'''[bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1",''',
  r'''[bpy.app.binary_path, "-b", "--disable-autoexec", "--factory-startup", "--python-exit-code", "1",''',
  "child Blender also gets --disable-autoexec (second reader)")

# ============================================================ scenario-blender-previs-storyboard
E(PRV, "SKILL.md",
  r'''If a sibling skill named here is missing from
your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.''',
  r'''If a sibling skill is missing, do not install anything: tell the person which skill is missing and carry on without it.''',
  "remove npx self-install instruction (must-change)")

E(PRV, "SKILL.md",
  r'''rebuild it with scenario-blender-blockout,''',
  r'''rebuild it with scenario-blender-blockout (deliberately not installed here, since it uses outside video services: do not install or use it),''',
  "blockout stays uninstalled (second reader's wording)")

E(PRV, "SKILL.md",
  r'''Strokes: scenario-blender-grease-pencil.''',
  r'''Strokes: scenario-blender-grease-pencil (not installed here).''',
  "not-installed note")

E(PRV, "SKILL.md",
  r'''layout: scenario-blender-animation. Real rigs: scenario-blender-rigging.''',
  r'''layout: scenario-blender-animation (not installed here). Real rigs: scenario-blender-rigging (not installed here).''',
  "not-installed notes")

E(PRV, "SKILL.md",
  r'''**REQUIRED BACKGROUND:** scenario-blender-expert (execution channel, review loop, 5.2 API changes).''',
  r'''**REQUIRED BACKGROUND:** scenario-blender-expert (execution channel, review loop, 5.2 API changes).

**Local rules (this machine):** run only in a fresh `-b --factory-startup --disable-autoexec` session, never inside the film's own .blend. Give every scene, object, collection, camera, marker and shot id a new previs-only name: the helpers reuse and overwrite same-named ones. Always pass a new `edit_name` to `P.animatic` (it deletes the strips of the scene it finds). Write only into a new folder under the scratch area, and delete scratch outputs when done.''',
  "local rules paragraph (second reader)")

E(PRV, "references/procedures.md",
  r'''## P21. Storyboarding app template (replaces the open file, run last)''',
  r'''## P21. Storyboarding app template (replaces the open file, run last). DO NOT RUN unless the person asks for this template: it wipes the open Blender session''',
  "stop sign on the session-wiping block (must-change)")

E(PRV, "references/procedures.md",
  r'''bpy.ops.wm.read_homefile(app_template="Storyboarding")''',
  r'''raise RuntimeError("P21 is disabled on this machine: read_homefile would replace the open Blender session")''',
  "make the session-wiping call stop (second reader)")

E(PRV, "references/procedures.md",
  r'''line: `blender --app-template Storyboarding`.''',
  r'''line: `blender --app-template Storyboarding` (this opens a Blender window: never run it here).''',
  "no window (second reader)")

E(PRV, "references/procedures.md",
  r'''blender --background --factory-startup --python-exit-code 1 --python tests/code/blender-previs-storyboard/<test>.py''',
  r'''<full path to blender> -b --factory-startup --disable-autoexec --python-exit-code 1 --python <your script>.py''',
  "run-command template follows our rules (second reader)")

E(PRV, "references/procedures.md",
  r'''# any writable folder''',
  r'''# a NEW empty folder under the scratch area; REPLACE this placeholder first (makedirs would otherwise create /abs/path/to/output on the disk)''',
  "placeholder path warning (second reader)")

E(PRV, "references/procedures.md",
  r'''Strokes: scenario-blender-grease-pencil;''',
  r'''Strokes: scenario-blender-grease-pencil (not installed here);''',
  "not-installed note")

E(PRV, "references/procedures.md",
  r'''Full rigging: scenario-blender-rigging.''',
  r'''Full rigging: scenario-blender-rigging (not installed here).''',
  "not-installed note")

E(PRV, "references/sources.md",
  r'''Seven videos, distilled in''',
  r'''Citations only: never fetch or open these links. Seven videos, distilled in''',
  "do not fetch links (second reader)")

E(PRV, "scripts/bx_previs.py",
  r'''    ed = bpy.data.scenes.get(edit_name or sc.name.replace("_blend", "_edit")) or \
        bpy.data.scenes.new(edit_name or sc.name.replace("_blend", "_edit"))''',
  r'''    ed = bpy.data.scenes.get(edit_name or sc.name.replace("_blend", "_edit")) or \
        bpy.data.scenes.new(edit_name or sc.name.replace("_blend", "_edit"))
    if ed == sc:
        raise ValueError("animatic: the edit scene would be the previs scene itself (no '_blend' in its name); pass edit_name")''',
  "guard: edit scene must not be the previs scene (second reader, optional but listed)")


def main():
    log = []
    bad = 0
    # group by file, apply in order
    contents = {}
    for skill, rel, old, new, why in EDITS:
        path = os.path.join(STAGING, skill, rel)
        if path not in contents:
            with open(path, encoding="utf-8", newline="") as f:
                contents[path] = f.read()
        txt = contents[path]
        n = txt.count(old)
        entry = {"file": f"{skill}/{rel}", "old": old, "new": new, "why": why, "count_before": n}
        if n != 1:
            bad += 1
            entry["status"] = "SKIPPED (count != 1)"
            print(f"FAIL count={n}: {skill}/{rel}: {old[:70]!r}")
        else:
            contents[path] = txt.replace(old, new)
            entry["status"] = "applied"
            print(f"ok   {skill}/{rel}: {old[:60]!r}")
        log.append(entry)
    if not DRY and bad == 0:
        for path, txt in contents.items():
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(txt)
        print("WROTE", len(contents), "files")
    elif not DRY:
        print("NOT WRITTEN because of failures:", bad)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edit_log.json"), "w") as f:
        json.dump(log, f, indent=1)
    print("edits:", len(EDITS), "failures:", bad)


main()
