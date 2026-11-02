# Coal mine: the look stage on a place built by someone else

What this file is: the record of the transfer test (2 November 2026, procedural textures log 38). The coal-mine scene (`mine-scene/`, built by other sessions from the owner's own textures, with its own lights and a painted sky picture) was drawn as it was, then with the look stage and nothing else, then after one fix pass. Same camera every time, 540 x 960, 32 samples, on a 2-processor machine.

| Picture | What | Brightness | Warm : cool | Warm light covers | Time |
|---|---|---|---|---|---|
| `mine-A-as-is.jpg` | The mine's own lights, sky and settings | 0.27 | 19 : 54 | 0.1 % | 59 s |
| `mine-B-look.jpg` | `apply_look` with its defaults (exposure 0.5, window light 1.0) | 0.12 | 31 : 53 | 0.2 % | 135 s |
| `mine-C-look-fixed.jpg` | One fix pass: exposure 1.0, window light 2.0, cap 48 | 0.18 | 32 : 49 | 1.1 % | 139 s |
| `mine-A-B-C.jpg` | The three side by side | | | | |

The look stage found 133 warm glowing patches (village windows, engine-house windows and door, lamps) and put a real light at 50 of them (71 after the cap was raised); it muted the mine's seven lights and replaced its sky picture with the painted blue-hour sky. Nothing in it was written for the mine. The dials of picture C were set from the measures of picture B. The balloon-shaped smoke and the flat hills remain: shapes are not the look stage's business, and a judge would list them first.

The scene is rebuilt in 18 s with `MINE_TEXTURES=.../austerity-explainer/working-files/session-scratch/mine-work/textures_ready python3 mine-scene/assemble_mine.py -- OUT --quick --no-render --save-blend`, then `stage/render_small.py --scene OUT.blend --out C.png --exposure 1.0 --window-light 2.0`.

## Traps

- Picture C's window light 2.0 was set when every glowing window had a 40 W floor; the floor is now 8 W, so a repeat of C needs a touch more (untested).
- The mine's sunset lived in its sky picture; the look stage's blue hour has none. `--keep-world` keeps the picture but loses the sky light's colour.
