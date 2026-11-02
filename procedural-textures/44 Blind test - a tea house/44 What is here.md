# 44 Blind test: a tea house

What this folder is: the record of the second blind test of the `painted-place` plugin (log 44 in the project story; decisions 55, 57 and 58).

## The test

- The request, to both builders, word for word: "A tea house."
- Both builders were fresh Sonnet models on the same 80-minute clock (00:30 to 01:50, 3 November 2026).
- The plugin builder had `painted-place` 0.4.1 and the request (`plugin builder brief.md`).
- The control builder had Blender alone, the plugin's one-page look description and its five reference pictures (`control builder brief.md`).
- At 00:58 the owner said: "No blind judges. I'll judge". The plugin builder's own blind judge was stopped before it answered, and no final judges were started.

## What is here

| File | What it is |
|---|---|
| `44 Tea house - picture A - hand-in size.png`, `... B ...` | The two hand-in pictures (540 x 960) under the letters the owner judged them by |
| `44 Tea house - key, which picture is which.json` | The key, made at random before judging and opened after: A was the control build, B the plugin build |
| `44 Tea house - picture A - full size.jpg`, `... B ...` | Both redrawn the same way at 1080 x 1920, 64 samples, each with its own builder's script and dials (A took 1415 s, B 1765 s, one after the other) |
| `44 Plugin builder's report.md`, `44 Control builder's report.md` | Each builder's own report (returned as text and saved by the coordinating session) |
| `44 plugin builder - build_tea_house.py` | The plugin builder's script for the place's shapes (the plugin dressed and lit them) |
| `44 control builder - render_final.py` | The control builder's whole scene, light and finish in one script |

## The verdict

The owner, at 02:25: "Absolutely incredible. The plugin works. Now only minor adjustments are needed." The key then showed that B, the street with the teapot lantern, was the plugin's picture.

## What it taught the plugin (now 0.5.0)

Brass, copper and china roles; casings, sills and sashes for windows in plaster walls (and sashes for windows in timber walls); a warning when glowing glass takes more than 2 percent of the frame; traps for smoke against a dark sky, light shafts and importing bpy before bmesh.

## Traps

- The two builders read different documents; the control builder never saw the plugin and the plugin builder never saw the reference pictures. Do not compare their reports as if they had the same brief.
- The plugin builder drew its second round at 32 samples, the control builder at 64; the full-size redraws use 64 for both.
- A long background drawing is lost if the machine restarts (the first full-size redraw was); check it is still running before promising it.
