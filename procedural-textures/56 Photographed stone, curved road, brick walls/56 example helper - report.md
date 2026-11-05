# 56 The worked example's helper - report

What this file is: the report, word for word, of the helper that built the worked example "a curved corner after rain" with the new road, wall and stone tools (5 November 2026, 18:17 to 19:08). Saved by the session.

---

**The street corner is built and the final picture was finished at 19:08, before your 19:20 limit.** It is 540 x 960 and inside all four measure bands. It is the third final I drew; I kept the first two.

- Final picture: `/home/claude/store-work/pbr56/example/final.png` (earlier finals: `final_v1.png`, `final_v2.png`)
- Example script (the only plugin file I added or changed): `/home/claude/music/plugins/painted-place/brief/store/examples/street - a curved corner after rain.py`. Its top note says what it builds and how to run it: `python3 "<script>" WIDTH HEIGHT SAMPLES OUT.png`.
- Notes, written as I went: `/home/claude/store-work/pbr56/example/notes.md`

## What the picture shows
- **Road:** a sett road (rows of stone blocks) bends right through a quarter circle 9 m across, climbing gently. It is wet and glossy, with each sett its own shade, stones from two quarries, a few setts sunk and tipped, and grit and moss in the joints.
- **Kerbs and pavements:** both edges have kerbs and flagged pavements (stone slabs). All were laid from the same road line, so they follow the bend exactly.
- **Wall on the outside of the bend:** eight flat panels, one per straight stretch, each filled by the new wall tool:
  - old red brick in the common bond;
  - one stretch of the dark sooty brick in Flemish bond;
  - two stretches of stone blocks;
  - a stone cap along the top of each panel.
- **House:** the photographed stone blocks from the house-front tool, with a door, windows, corner stones, a slate roof with gutters and a chimney. One window glows warm and one dim amber, each with a small light outside it.
- **Gas lamp:** about 15 m from the eye, lit, standing in front of the dark brick so its light falls on both kinds of brick and on the wet setts. A second store lamp stands just out of frame, so only its light shows on the near setts.
- **Puddles:** each one's water level comes from the road tool's height call (`top_at`), as its tool text says. The long puddle holds the lamp's reflection. A puddle on the far pavement catches the lit window.
- **Small things:** an ash bin under the lit window, an opened sodden newspaper in the gutter, and weeds in the joints by the kerbs, kept out of the wheel lines.
- **Camera:** at eye height in the road, looking along the bend. The sky, haze, lights and finishing are copied from the cart-track example.

## Every picture
The four measures are brightness, warm share, cool share and warm light. "Small" is 270 x 480, quick; "full quick" is 540 x 960 at low quality; "final" is 540 x 960 at finished quality.

| Picture | Time | Size | Measures | Result |
|---|---|---|---|---|
| t1 | 18:25 | small | 0.15, 4%, 68%, 0.1% | warm too low, too blue, lamps light nothing |
| t2 | 18:27 | small | 0.18, 23%, 39%, 0.7% | inside |
| t3 | 18:29 | small | 0.17, 18%, 47%, 0.3% | warm light too low: the lit window was out of frame |
| t4 | 18:31 | full quick | 0.18, 26%, 43%, 0.7% | inside |
| t5 | 18:34 | full quick | 0.18, 26%, 43%, 0.6% | inside |
| t6 | 18:36 | full quick | 0.18, 26%, 42%, 0.9% | inside |
| where | 18:37 | tiny 54 x 96 | not measured | only to print where things fall in the frame |
| t7 | 18:40 | full quick | 0.18, 26%, 42%, 0.9% | inside |
| t8 | 18:43 | full quick | 0.18, 26%, 42%, 0.9% | inside |
| t9 | 18:45 | full quick | 0.18, 25%, 41%, 0.8% | inside |
| final 1 | 18:50 | final, 5 min | 0.18, 26%, 40%, 0.8% | inside |
| t10 | 18:53 | full quick | 0.18, 25%, 41%, 0.8% | inside |
| final 2 | 18:59 | final, 6 min | 0.18, 26%, 40%, 0.8% | inside |
| t11 | 19:01 | full quick | 0.18, 25%, 41%, 0.8% | inside |
| **final 3** | **19:08** | **final, 6 min** | **0.18, 26%, 40%, 0.8%** | **inside: this is final.png** |

## What I checked at full size and fixed
- **Too dark and blue (t1):** I made the lamp stronger, added the hidden second lamp and lit two windows.
- **Puddle reading as a black hole (t4, t5):** water nearer the eye than the lamp's reflection mirrors the dark sky above the lamp. I moved the long puddle so the reflection sits at its near end, and set the water 1 mm below the setts' tops so the highest setts poke through. Then I narrowed the clear rim, which was drawing a pale outline round the water under the lamp.
- **Bricks:** examined close up, they look like real separate bricks, not stretched. The dark Flemish stretch and the red stretch look different from each other.
- **Kerbs and flags:** they stay on the road's edge all round the bend.
- **Newspaper:** on the wet buff flags it disappeared, so I moved it into the dark gutter and opened it out.
- **Flags:** I gave each slab more shade and a little relief. They still look fairly smooth.
- **Near setts:** I tipped and sank more of them near the eye so they catch the light separately and stop looking like one flat picture.

## The new tools in use
**Did well:**
- The curved road, the edge lines, the kerbs and the curved pavements all lined up exactly from one line.
- The height call (`top_at`) gave correct puddle levels on the climbing road.
- The wall tool filled every panel with whole photographed bricks or blocks, including panels with a sloping bottom edge. It handled three bonds, both brick sets and stone blocks, and nothing failed.
- The house-front tool's stone blocks show well on the house.
- The whole place builds in about 30 seconds.

**Problems, with the exact calls:**
- **First road lines refused:** `lay_cobbles.road_edges(LINE, 5.0, beyond=1.35, rise=0.13)` stopped with "the line bends too tightly for edges 3.85 m from it: 29.8 m along it its radius is 3.54 m … give the bend a radius of at least 4.5 m". The second try stopped the same way at "4.18 m". My points sat on a 9 m circle, but were unevenly spaced, and the smooth curve through them bends tighter than the circle. Points evenly about 2.4 m apart fixed it. The refusal itself was clear and helpful.
- **Wrong height on pavements, with no warning:** `lay_cobbles.top_at(flags, 0.0, 14.0)`, on flags laid along `[(0,0,0),(0,5,0.25),(0,10,0.5),(0,15,0.75)]`, returned 0.0 where the slabs' top is about 0.70. It only works for the road. For the pavement puddle I read the height from the pavement's own middle line instead.
- **No way to light a window:** the house-front tool has no option for it. I changed one window's glass myself by finding it by position.
- **Pale puddle rim:** at its default size, the puddle tool's clear rim draws a pale outline under a lamp. `shallow_band=0.04` fixed it.

## What I did not do
- I added no picture next to the script and no line in `examples/README.md`, because the rules allowed only the script.
- The project's standing rule says each new set's lessons go into the plugin. None of the problems above are written into the plugin yet; that still needs doing.
- A low dark-brick wall round the inside of the bend is built, but the tall frame never shows it.
- The newspaper and ash bin can be made out, but only just. The far-left brick sits in shadow. There is no falling rain.
- I did not run the plugin's tests, since I changed no tool.
- A syntax check left a cache folder in the examples folder; I deleted it.

---

## Traps

- This is the helper's own account. What the session did with its findings is in the project story, log 56.
