# 50 Military base from the kit with a board, a shelf and a material list, in two passes

What this folder is: the military base built a fourth and fifth time (log 50; decision 64), to test the three changes the research (file 49) asked for: a reference board of real photographs, a material list written before building, and a shelf of photographed surfaces; and a second, set-dressing pass by a fresh builder.

| File | What it is |
|---|---|
| `50 Military base - pictures only, kit, kit with board and shelf.jpg` | The pictures-only base (log 46), the first kit try (log 48) and this first pass side by side |
| `50 Military base - first pass - final.png` | The first pass: built from the material list, 20:12 to 21:25 (clock 21:55) |
| `50 Military base - second pass, dressed - final.png` | The second pass: the same scene dressed by a second builder, 21:31 to 22:16 (clock 22:55) |
| `50 Military base - first pass beside second pass.jpg`, `... close-up ...` | Before and after the dressing, whole and the left foreground |
| `50 first pass - materials.md`, `50 second pass - materials.md` | The material lists: who is here, what they left, every surface and its wear |
| `50 first pass - render_final.py`, `50 second pass - ...` | The scripts (the second is the first with the dressing added) |
| `50 ... brief.txt`, `50 ... builder's report.md` | Each builder's brief and report |

## What happened

- The first builder read the board and wrote the material list before building (a gun battery's men and the camp guard; a lantern on a crate, a bucket, shells by the gun, a spade in a sandbag wall), then built those things. It laid seven photographed surfaces from the shelf: mud with wheel tracks, old planks, painted planks, rusted corrugated iron, rusted iron, sacking, canvas. It measured every picture with the real tool and finished inside every band. It stopped 30 minutes early.
- The second builder kept the layout, camera and lights and added wear by rule (edges bright, mud climbing by height, wet films, nail rust) and the things people left, each with an owner. It stopped 39 minutes early.

## What it shows

- The board and the material list gave the placement a reason: the things in the picture belong to someone. That was the research's point about set dressing, and it held.
- The shelf gave the ground and the boards real surfaces; the tents and the tower stayed clean simple shapes, because photographed surfaces do not give a shape its seams, sag and patches.
- The second pass added small, sensible things, but the gain at 540 x 960 is modest: most of what it added is a few pixels wide.
- Builders keep stopping early, now three in a row, each saying the remaining changes were not worth the risk of breaking a picture that measured well. The measure tool has become a reason to stop.

## Traps

- The two scripts read the shelf from `place-brief/surfaces/` by a path; move the kit and they stop drawing.
- The measure tool checks colour and light only. A builder that treats "inside every band" as finished will stop early; the brief now needs to say that the bands are a floor, not the goal.
