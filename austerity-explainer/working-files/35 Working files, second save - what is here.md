# Working files, second save: what is here (log 35)

What this file is: a map of the second full save of working files (24 October 2026), what went in, what stayed out and why, and how to use the
big scene files that had to be split.

You asked: "Push everything to repo. Including all the images", then "And sets already constructed", and later "There's nothing I want to keep
secret" and "Push them all" (decision 49 in `../project-notes/Decisions.md`).

## What is here

About 17,400 files, roughly 8.7 GB, added in 33 commits named "Working files (log 35) ..." (plus one that took 15 files back out).

| Folder | What it holds |
|---|---|
| `session-scratch/` | Everything from the sessions' own working folder, in its original layout: every picture, check sheet, test render, mask, map, scene file, script, note, log and result. The biggest parts: `proc-work/` (the texture and place work, about 2 GB), `redesign/` (chapter 2's redesign rounds), `plan3/` (the pit village street test), `plugin-work/` (building the film plugin), `village-test/`, `village-control/` and `village-without-plugin` material, `mine-work/`, `house/`, `review-26/`, `sam3d/`, `astra-upload/`, `astra-upload-021/` and `astra-work/` (your Astra add-on and the work done with it). |
| `session-scratch/proc-work/reference/` | Your six uploaded texture sets (mud, slate, gravel, brick, metal, wood) as the texture work used them. |
| `chapter-2-work-folder/`, `film-kit-live-leftovers/`, `plugin-install-tests/` | New files in those places since the first save (log 25). |
| `runpod-store/place-jobs/` | Scenes that existed only on the rented machines' store (the plugin's place jobs). |
| `session-workflow-scripts/` | The instructions given to every team of helpers in this session. |

**The constructed sets (scene files):** 200 scene files, among them the plugin village at every stage (`session-scratch/village-test/`: each
part, rounds 2 to 4, the final scene with your mud inside and a copy without it), the village built without the plugin by Sonnet
(`session-scratch/village-control/village.blend`), the Japanese garden in both looks and every character fix (`session-scratch/proc-work/garden/`),
the street and door tests (`session-scratch/proc-work/skills_test/`, `street_wet/`), the plugin's test huts, yards and canal lock
(`session-scratch/plugin-work/`), the coal mine scene (`session-scratch/mine-work/out/`), chapter 2's factory and checkout trials
(`session-scratch/redesign/`) and the Astra courtyard tests (`session-scratch/astra-work/out/`). The scenes that were only on the rented machines'
store were downloaded and checked against the store's own checksums first.

## Scene files split into parts

GitHub refuses single files over 100 MB, so four scenes are saved in numbered parts (`NAME.blend.part-1-of-2`, `NAME.blend.part-2-of-2`):
the plugin village's round 2, round 3 and round 4 scenes, and the round 4 copy without your textures. To join them back into one file that Blender opens:

- Mac or Linux, in a terminal in that folder: `cat "NAME.blend.part-1-of-2" "NAME.blend.part-2-of-2" > "NAME.blend"`
- Windows, in a command window in that folder: `copy /b "NAME.blend.part-1-of-2" + "NAME.blend.part-2-of-2" "NAME.blend"`

## What stayed out, and why

| Left out | Files | Why |
|---|---|---|
| Videos and audio | 192 | Your rule (decision 30). |
| Other people's work | about 6,500 | Downloaded models and Poly Haven scans, fetched web pages and papers, copied software, skills and the animation engine of another plugin (decision 30's call). Free Poly Haven scans packed inside our own scenes did go in: their licence allows sharing. |
| Login keys and rented machine ids | 27 | Text files that hold, or look like they hold, a key, token or address. They stay on this computer only. |
| Installed software, fonts and caches | 38 | Not made here, and reinstalled on demand. |
| Zips | 2 | Packed copies of files saved unpacked. |
| Opus's village, second pass | about 70 | Still being made; saved when it is finished, with its first-pass scene. |

## Good to know

- **15 files went up early by mistake** (your mine pictures, crops of the mine reference screenshot, four maps made from your textures, your
  texture pack's read-me) and were taken back out of the current version. You chose to leave them in the history. With "Push them all" they are
  back in the current version anyway.
- **This computer's copy of the repository leaves these folders out of its checkout** to save disk space; they are on GitHub. To bring one back
  here: `git sparse-checkout add /austerity-explainer/working-files/<folder>/`. Commands that read every file (for example a diff with file
  sizes) start downloading all of it; avoid them on this computer.
