# 57 The Japanese garden, second builder - report

What this file is: the second builder's report, word for word (5 November 2026, 21:32 to 22:40). Saved by the session.

---

## Build 57, second pass (dressing the Japanese garden): report

Everything is in /home/claude/build-57-garden/dress:
- **final.png**: 540 x 960, 40 samples
- **closeup.png**: 540 x 960, 40 samples, drawn with `--closeup`
- **render_final.py**: `python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png`, plus `--closeup`. It draws both pictures with all the finishing. Each change is marked "second pass" in the code.
- **materials.md**: the first deliverable, kept true during the build
- **notes.md**: every picture with its time and measures, every change, the checks

The layout, camera and lights are as the first builder left them. I added no lights and moved none.

**Both delivered pictures are inside every band:**

| picture | brightness | warm | cool | warm light |
|---|---|---|---|---|
| final.png | 0.175 | 35.7% | 40.4% | 2.2% |
| closeup.png | 0.216 | 34.0% | 37.0% | 0.47% |

### What I changed (bottom third first)

**Things people left.** Each one sits beside the path, never on it.
- **The maid's bamboo broom**, leant on the garden fence's top rail.
- **The heap of leaves she swept** to the path's edge, beside the broom.
- **Her wooden bucket**, with copper hoops, water and a bamboo dipper. It stands beside the path, 3 cm clear of its edge.
- **The guests' clogs**, rebuilt as a neat pair on the step stone. In the first pass they read as two white boxes; now they read as sandals with red thongs.

**Surfaces and wear:**
- **Path slabs:** corners knocked off and edges wandering, like the split stone in the owner's second picture. Their photographed surface shows more relief, worn edges are slightly lighter, and each slab has its own shade.
- **Puddles:** smaller, with ragged edges and a faint ripple. The stone shows through where the water mirrors the dark eave. The one that mirrors the hanging lantern stays long.
- **The first builder's small puddle** lost the pale ring round its water.
- **Joints:** darker photographed gravel with less moss.
- **Leaves:** recoloured from salmon-pink to deep red, orange and brown. Their shine was mirroring the blue sky and turning them pink, so I turned it down.
- **The jar's glaze:** greyed, with rain streaks from the rim.
- **On the soil only:** damp and mud stains by the bucket and the basin. Leaves, twigs and pebbles in the bed between the path and the fence.
- **Bamboo fence and spout post:** dark and green at the foot. This hardly shows in the dusk.
- **Close view finishing:** a little brighter (exposure 4.2 to 4.5) with more glow round the lantern's reflection. Its warm light had been just under the band.

**The owner's PBR note:** the bucket, slabs and joints use the photographed surface sets. I added no pebble shapes to the joints, because the first builder had already taken them out for that reason.

### Pictures (time, size and samples, brightness / warm / cool / warm light)

- 21:32 t00, first pass unchanged (timing only): 270x480, 16 samples, 26 s to draw
- First pass final: 0.18 / 35 / 41 / 2.2. First pass close view: 0.21 / 26 / 43 / 0.5
- 21:42 t01: 270x480, 16 — 0.18 / 34 / 42 / 2.2. Broom and bucket too dark to name.
- 21:43 c01: 270x480, 16 — 0.20 / 25 / 41 / 0.3 (low). Puddles mostly black.
- 21:45 t02: 540x960, 12 — 0.18 / 34 / 42 / 2.1. The broom stood in front of the bucket.
- 21:46 c02: 270x480, 16 — 0.20 / 26 / 38 / 0.1 (low).
- 21:49 t03: 540x960, 12 — 0.18 / 35 / 41 / 2.1. Bucket reads; broom too dark; puddles were smooth ovals.
- 21:50 c03: 540x960, 12 — 0.20 / 28 / 39 / 0.3 (low).
- 21:53 t04: 540x960, 12 — 0.18 / 35 / 41 / 2.1. Broom reads; clogs still boxes.
- 21:55 c04: 540x960, 12 — 0.21 / 29 / 38 / 0.3 (low).
- 21:56 t05: 540x960, 12 — 0.18 / 35 / 41 / 2.1. Clogs and heap read.
- 21:59 c06: 540x960, 12 — 0.20 / 32 / 38 / 0.3 (low). Leaves still pink in this view.
- 22:01 t06: 540x960, 12 — 0.17 / 35 / 41 / 2.1.
- 22:05 final_v07: 540x960, 40 — warm 36.2%, just over the 36% top. Traced to warm-brown jar streaks and the new props; fixed in v08.
- 22:10 final_v08: 540x960, 40 — 0.175 / 35.7 / 40.5 / 2.2.
- 22:15 closeup_v08: 540x960, 40 — 0.204 / 33.4 / 37.6 / 0.35 (low). Re-finished it at exposure 4.6, 5.0, and 4.5 with more glow; the last gave 0.45 and was chosen.
- 22:20 final_v09: 540x960, 40 — 0.175 / 35.7 / 40.5 / 2.2.
- 22:24 closeup_v09: 540x960, 40 — 0.215 / 34.0 / 36.5 / 0.44.
- 22:28 final_v10, two mended fence canes: in band, but the canes can't be seen even at 3x, so I took them out.
- 22:32 final_v11, stronger ripple: 0.175 / 35.7 / 40.4 / 2.2. Delivered as final.png.
- 22:36 closeup_v11: 0.216 / 34.0 / 37.0 / 0.47. Delivered as closeup.png.
- c05 was drawn but replaced before I looked at it.

### What I checked and fixed

- **Every picture was measured.** I looked at the bottom third at 2x or 3x after each one.
- **Nothing is on the path or the walk to the bridge.**
- **No stain on the glossy path or a puddle.**
- **The broom was moved twice:** it first hid the bucket, then crossed the basin's edge.
- **The bucket was in the basin's shadow**, so I made its wood paler and gave it copper hoops.
- **Three of my own mistakes, each fixed:**
  - A stop command I ran also stopped its own shell, so that step's edits didn't happen. I redid them.
  - Changing the slab outlines first would have left sharp corners, so the worn edges are worked out from the original slab shape.
  - Rectangular water stuck out past the knocked-off corners, so each puddle is now an oval inside its stone.

### What I did not do, and why

I stopped changing the scene at 22:37, with 15 minutes left. Another round of both pictures takes about 8 minutes plus checking. These were the next candidates:
- **Moss on the slabs:** would dull the wet shine the puddles need.
- **A cracked or relaid slab:** would change the path pattern the first builder laid.
- **Pebble shapes in the joints:** go against the owner's PBR note.
- **Stronger soil stains:** the stains are faint, and I left them that way rather than smear the path.

### For you to decide

- **The plugin was not updated.** The house rule says each new set updates `painted-place`, but I could only write in the dress folder. Things that could go into the plugin:
  - **Traps:**
    - Glossy leaves under a blue dusk sky turn pink.
    - Clogs built from boxes read as boxes.
    - A dark prop in a big object's shadow can be made readable with pale materials or metal hoops, without adding a light.
    - A broom in front of a bucket cancels both.
    - The puddle tool's wet film drew a pale ring round the water.
    - Things under about 3 cm can't be seen at this size.
  - **Parts:** the broom, the wooden bucket, the swept heap, and the knocked-off slab corners with oval water.
- **Folder rule slip:** my first folder listing accidentally printed the file names in /home/claude/build-57-garden/work. I read none of those files.
- **Memory:** the only thing I used from memory was the user's preference for plain words.
