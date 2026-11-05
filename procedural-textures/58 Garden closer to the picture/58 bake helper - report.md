# 58 Bake helper - report

What this file is: the report, word for word, of the helper who baked the azalea onto a simple shape as PBR pictures at the owner's word (decision 87), and made the store's `bake_to_pbr` tool (log 58; 6 November 2026, 06:59, stopped by the server under a minute in, resumed 07:01, finished 07:43). Saved by the session. Its words are in `58 bake helper - text.md`.

---

## Bake test of the azalea, and the new bake_to_pbr tool

**In short:** the baked azalea looks like the built one from about 3 m away and further. At garden distance (8 m, dusk) the two can hardly be told apart. Closer than that, at 1.8 m, the flowers look flat and soft. It draws faster. It only makes the file smaller when its pictures are small, because the built azalea is already stored very compactly. Cycles was faster than Eevee on this machine, so I drew everything with Cycles.

All paths below are in `/home/claude/store-work/closer58/bake/`. Built bush is on the left, baked bush on the right. Each bush was drawn alone under the same light, Cycles with 32 samples. The built bush draws 265,367 faces; the baked bush is 320 faces, 20,480 once its height is turned into real bumps.

**The dark swirl the session saw was a fault in the bake, and it is fixed.**
- **Cause:** most of the bush's leaves and petals are single faces, and 173,274 of the 265,367 faced inwards. The bake took those as dents, which drew dark, worst in a swirl near the top.
- **Fix:** the tool now turns every inward-facing face outwards before it bakes.
- **What this means for the owner:** the three pairs already sent were made before the fix. They show the swirl and leaves that are too dark. Please send the "v2" pictures below to replace them.

### What the test showed

| Picture | Built | Baked |
|---|---|---|
| `pics/close_built_vs_baked_v2.png`: card view, 3 m, 420 x 420 | 13.2 s, memory 20 MB | 8.2 s, 34 MB |
| `pics/close_built_vs_baked_8bit.png`: same view, final 8-bit pictures | 13.2 s, 20 MB | 8.3 s, 30 MB |
| `pics/near_built_vs_baked.png`: 1.8 m | 20.9 s, 20 MB | 10.3 s, 30 MB |
| `pics/garden_built_vs_baked_full_v2.png` and `pics/garden_built_vs_baked_middle_v2.png`: 540 x 960 from 8.2 m, dim blue sky, lit stone lantern 1.2 m from the bush | 21.4 s, 86 MB | 19.0 s, 100 MB |
| `pics/garden_built_vs_baked_middle_8bit.png`: same garden view, final 8-bit pictures | 21.4 s, 86 MB | 20.2 s, 96 MB |
| `pics/mounds3_built_vs_baked.png`: a run of three mounds | 11.6 s | 7.7 s |

At 3 m the two read as the same bush. At 1.8 m the difference shows. In the garden they are the same bush, and the average brightness of the bush matches within a few points.

Other pictures:
- **Smooth shape vs bumpy shape:** `pics/close_flat_vs_relief_v2.png`. The smooth shape (7.5 s, 320 faces) reads as a shiny painted dome. Turning the height picture into real bumps is clearly better: the outline becomes lumpy like the real bush.
- **Picture sizes at 8 m:** `pics/garden_zoom_sizes.png`, enlarged, shows built and baked with 1024, 512 and 256 pictures. All three baked versions read the same.
- **Sharper close up:** `pics/near_built_vs_baked_2048.png`, with 2048 pictures and finer bumps. Sharper, but it takes 59 s to bake, the pictures are 9.4 MB, and it uses 76 MB of memory.

**Eevee against Cycles** (3 m view): Eevee took 27.0 s for the built bush and 11.1 s for the baked one; Cycles took 13.2 s and 7.6 s. Cycles is faster.

**Faces:** built 265,367; baked 320 (20,480 with bumps). The run of three mounds is 422,510 built against the same 320 baked.

**File sizes**, with the 0.48 MB of an empty file taken off:
- **Built azalea:** 0.92 MB. It is stored as points that the leaves and flowers are copied onto, so it is already small.
- **Baked azalea:** 0.10 MB plus its pictures: 3.0 MB at 1024, 0.92 MB at 512, 0.26 MB at 256. With 16-bit pictures, 1024 comes to 6.7 MB.
- **So:** it only saves space at 256 pictures. At 512 it is about even, and at 1024 it is about three times bigger.

### Baked pictures kept
- `baked/size1024_8bit/` (the default): colour 0.81 MB, normal 1.51 MB, height 0.60 MB, shine 0.08 MB, 3.0 MB in all.
- `baked/size512_8bit/`: 0.92 MB in all.
- `baked/size256_8bit/`: 0.26 MB in all.
- `baked/size1024/`: 16-bit, 6.7 MB.

Each folder's `both.blend` holds the part and its baked shape.

### What I made
- **The tool** `brief/store/tools/bake_to_pbr.py`. The call:
  `baked = bake_to_pbr.bake(store.add_part('azalea'), size=512, lit_through=0.3, folder='/my/work/baked')`
  - It returns a 320-face dome that hugs the bush, with the four baked pictures as its material and its height as real bumps.
  - The builder's own objects are left exactly as they were; the builder hides them.
  - The options are listed in the tool's help: the shape it bakes onto (dome, ball, or one you give), the picture size, how far in and out it looks, the bumps on or off and how fine, how much light comes through the leaves, and 8 or 16-bit pictures.
- **Its card** `brief/store/cards/tools/bake_to_pbr.png`. I looked at it at full size: built bush on the left, the tool's baked bush on the right, both whole.
- **Its test** `tests/test_store_bake.py`. It passes.

Test runs:
- `test_store_tools.py` passes.
- `test_store_rules.py` passes its rule checks (109 files). Its catalogue check fails, as expected, until you run `catalogue.py`.
- I ran `catalogue.py --check` once to see the tool's row. That mode writes nothing, and `Store.md` is untouched.

### What does not read well
- At 1.8 m the flowers look flat, soft and a little bluer on the side the blue light comes from. The outline is smoother than the built bush's.
- From a slant, the flowers seem smaller and leafy gaps look bigger. On the built bush the flowers stand out over the leaves; baked, they lie on the surface.
- With 2048 pictures, the bumps smear flowers into short spikes along the outline.
- In the three-mound run, the dips between mounds come out a little filled in.

### Mistakes and fixes
1. The usual Blender way of laying the pictures out failed inside the tool's own working scene. I gave the dome its own layout instead: one piece seen from the top, with no seams.
2. The first bake had no leaves. I had removed each temporary copy too early. Fixed by making every copy first.
3. The pictures had black holes at the foot. They are now filled from the pixels around them.
4. The dark swirl, described above.
5. The dome stood 4.6 cm below the ground, following leaves that hang below it. It now stands on the part's own foot.
6. A shape the builder gives was added to their collection twice, which caused an error. Fixed.
7. My first garden picture was too dark, with the lantern facing away from the bush. I turned the lantern to face the bush.

### Files
Created in the plugin: the three files above. Nothing else in the plugin was changed by me. Everything else is in the scratch folder: notes in `notes.md`, scripts in `scripts/`. The session's two Eevee check scripts are left as they were.

### Lines for Store.md
- **A baked stand-in** (decision 87): `bake_to_pbr.bake(part_root, size=512, lit_through=0.3)` bakes a part onto a 320-face dome with four PBR pictures and its height as real bumps; hide the part yourself. Tested on the azalea: from about 3 m on it reads as the built bush; at 8 m at dusk it is the same bush, and 256 or 512 pictures do. At 1.8 m its flowers look flat and soft; without bumps it reads as a shiny painted dome.
- What it saves: drawing time (8 against 13 s at 3 m, 10 against 21 s at 1.8 m, little in a whole garden: 20 against 21 s). File space only with small pictures: the azalea itself is 0.92 MB because it is stored as points; baked it is 0.36 MB with 256 pictures, about 1 MB with 512, 3.1 MB with 1024.
- Trap: leaves and petals made of one face that faces into a bush bake as dark dents in a normal picture. The tool turns them outwards; a bake of your own must do the same.
- Trap: the stand-in's leaves cast no shadows of their own, so bake again after changing the bush. Like the built azalea, it needs a lantern within a metre or two at dusk.
- On this machine (no graphics card) Eevee was slower than Cycles for both the built and the baked bush.

---

## Traps

- This is the helper's own account; what the session checked afterwards is in the project story, log 58.
- Its first three pairs, sent to the owner before the swirl was fixed, are not kept here; the pictures here are the fixed ones.
