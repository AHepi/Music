# 60 Moss helper - report

What this file is: the report, word for word, of the helper who gave the store real moss at the owner's word (decision 90; 6 November 2026, about 11:43 to 12:52). Saved by the session. Its words are in `60 moss helper - text.md`.

---

## Moss helper report (moss60)

The store now has real moss, and the rocks tool uses it by default. The final pictures are below. Tests pass. Everything I did is logged with times in `/home/claude/store-work/moss60/notes.md`.

### What I made

**1. Real moss in the moss tool** (`brief/store/tools/moss.py`).
- **Cushions:** soft, rounded mounds of moss with real thickness, up to about 3 cm deep.
  - They are thick on tops and in hollows. Each cushion rises from nothing at its edge over about 14 cm, and its edges fray into the stone.
  - Cushions creep over a rock's rim and hang a little down the sides. Moss keeps off sharp ridges, as real moss does.
- **Fine pile:** small star-shaped tufts about 1.5 cm high, laid by Blender's particle system as copies (about 16,000 per square metre). One tuft shape in six carries seed capsules on thin red-brown stalks. The tufts are dark down low and bright at the tips, with a soft sheen.
- **Several greens:** bright young moss, darker old moss, and brownish dry tips.
- **Photographed moss under it:** a new photo set from Poly Haven (free to use), `forest_leaves_02`. I added it to the shelf and to the store as `SURFACE • forest_leaves_02`. Poly Haven has no close photo of moss on its own; this set has moss cushions among fallen leaves.
- **Lichen:** pale crusts on the bare stone.
- **Plants at the rocks' feet:** moss tufts on the soil, grass from the grass tool, and ferns from the fern part.

How to use it:
- On any stone object you give (a basin, a lantern's foot, a wall top): `moss.grow(my_basin, amount=0.9)`. This makes a new object, 'moss on …', attached to yours. Your object is not changed.
- At the rocks' feet: `moss.feet(yard, laid_rocks, turf=0.5, ferns=1)`
- Lichen on any stone material: `moss.add(material, lichen=0.6)`. Old `moss.add` calls work exactly as before.

**2. The rocks tool uses it by default.** Any rocks given `moss=` now get the real moss.
- New options: `moss_style`, `moss_thickness`, `moss_pile`, `lichen`. `moss_style='paint'` gives back the old colour-only moss.
- Example: `rocks.scatter(yard, moss=0.9)`.
- **Why default:** the old moss was flat green paint, and the new one looked clearly better in every picture I drew.
- **Cost:** a picture with mossy rocks takes about a fifth longer to draw.
- The garden script's calls to `material`, `_shapes` and `_sheet` still work; the test checks this.

### The pictures

All are Cycles, 540 x 960, the same place and light, and the same light as the pair already sent.
- Measures are: brightness / warm share / cool share / warm light.
- The bands are 0.14–0.35 / 15–36% / 30–60% / 0.4–4.5%.

| Picture | File in `/home/claude/store-work/moss60/` | Time | Measures |
|---|---|---|---|
| Close (2.2 m), moss as the garden has it now | `close_paint.png` | 109 s | 0.18 / 33% / 32% / 0.1% |
| Close, new moss (final) | `close_cushions_4.png` | 129 s | 0.16 / 28% / 36% / 0.1% |
| 6 m at eye height, garden moss now | `far_paint.png` | 56 s | 0.28 / 34% / 38% / 0.0% |
| 6 m at eye height, new moss | `far_cushions_4_eye.png` | 60 s | 0.28 / 34% / 38% / 0.0% |
| 5.8 m from a veranda's height, garden moss now | `far_paint_2.png` | 89 s | 0.18 / 61% / 13% / 0.0% |
| 5.8 m from a veranda's height, new moss | `far_cushions_4_veranda.png` | 100 s | 0.18 / 58% / 14% / 0.0% |

**Pictures not inside every band:**
- Warm light is under its floor in all six, old and new alike. The lantern's windows draw white rather than warm, and I kept the light the same as the pair already sent, as you asked.
- The veranda pair is also too warm and not blue enough, because no sky is in the frame.

Side-by-side pairs, 1080 x 960, all ending "… garden moss now (left) and new moss, final (right).png":
- `close - …`
- `far 6 m at eye height - …`
- `far 5.8 m from a veranda - …`

Earlier versions are there too:
- `close_cushions.png`: the slab version you saw.
- `close_cushions_2.png`: after your note.
- `close_cushions_3.png`: before the plants at the feet were added.

### What it costs

| What | Before | With real moss |
|---|---|---|
| A 1.05 m boulder | 10,436 faces | 12,891 faces, about 6,800 tufts |
| A 0.8 m flat stone | 5,314 faces | 6,568 faces, about 4,000 tufts |
| A garden-sized bank of 120 mossy boulders | 632,068 faces, built in 3.7 s | 779,710 faces (+23%), 142,986 tufts, built in 7.4 s |
| Drawing the close picture | 109 s | 129 s (+18%) |
| Drawing the far pictures | 56 s / 89 s | 60 s / 100 s |
| Most memory used | 1.50 GB | 1.92 GB |
| Saved file | 5.3 MB | 7.8 MB |

The store's `Materials.blend` went from 14.82 to 14.83 MB; I saved it compressed.

### What does not read well yet
- At 2 m the pile reads as a soft velvety fuzz. Single tufts only show from closer than about 1 m.
- The moss tufts on the soil are faint in shade. The ferns and grass carry the "plants round the rocks".
- A flat-topped stone gets one big blanket-like cushion rather than patches.
- The lichen hardly shows at dusk in these pictures.
- I have not redrawn the garden itself. Its next build gets the new moss on every mossy rock and will draw slower. Its stone basin gets lichen but no cushions unless the builder calls `moss.grow` on it.
- Moss inside a basin's bowl also grows under the water, hidden by it.

### Mistakes I made and fixed
1. **Too much moss.** The first cushions covered whole rocks. Now `amount` sets what share of the stone gets moss.
2. **Slab-like cushions.** The first cushions read as blocky slabs, as you saw. They are now rounded mounds with frayed edges, a darker pile with bright tips, and a sheen.
3. **Moss at the feet.** It read first as a green rug, then as cut-out squares. It is now tufts placed straight on the soil.
4. **Round holes.** The moss had round holes like Swiss cheese. Bare patches now follow the rock's ridges.
5. **Wrinkles.** Twigs in the photo drew wrinkles on the moss. I turned the photo's relief down.
6. **Light tries.** My attempts at a warm sky turned the whole scene orange. I went back to your light.
7. **First far view.** It showed the edge of the ground and a lot of empty sky. I added the veranda view and kept both.
8. **Bugs found by the tests:**
   - Moss on a mesh with no material at all got painted the moss material all over.
   - Putting "cushions" in the middle of rock material names broke a check in the rocks test.
   - The rocks test measured rock sizes with the moss included.
   - My own test was too strict about tuft sizes, and read the moss's position too early.

### Tests
- `test_store_moss`: passes, 8 checks.
- `test_store_rocks`, `test_store_tools`, `test_store_materials`, `test_store_photographed`: pass.
- `test_store_rules`: its rule checks pass. Only the catalogue check fails, which you said to expect until you run `catalogue.py`.

### Files
Changed (in `/home/claude/music/plugins/painted-place/`):
- `brief/store/tools/moss.py`, `brief/store/tools/rocks.py`
- `tests/test_store_rocks.py`: only two small changes. It now measures rock sizes without the moss, and it no longer mistakes a moss tuft for a rock.
- `brief/surfaces/manifest.json`, `brief/surfaces/Surfaces.md`
- `brief/store/materials/Materials.blend`. Blender's backup copy, `Materials.blend1`, now holds the version from before my change.
- `brief/store/cards/tools/moss.png`, `brief/store/cards/tools/rocks.png`

Created:
- `tests/test_store_moss.py`
- `brief/surfaces/forest_leaves_02/` (four pictures)
- `brief/store/cards/materials/SURFACE - forest_leaves_02.png`

In my scratch folder: the scene, cost, card and material scripts are in `scripts/`, plus copies of the original files (`*.orig`, `card_*.before.png`).

### Lines to add to Store.md
- **Real moss** (the owner's word of 6 November 2026, "Ok. I meant the rocks with moss. Not the pavement lol. Those are still lacking a lot of detail"):
  - The rocks tool's moss is now real by default (`moss_style='cushions'`): soft rounded cushions up to `moss_thickness=0.03` m, thick on tops and in hollows, thinning to nothing at frayed edges and creeping over rims.
  - On them is a pile of tufts about 1.5 cm high, laid by the particle system (`moss_pile=1.0`, about 16,000 per square metre), in greens from young to old with dry tips, over `SURFACE • forest_leaves_02`. The bare stone gets pale lichen (`lichen=0.6`).
  - `moss_style='paint'` gives the old colour-only moss.
  - `moss.grow(my_basin, amount=0.9)` grows the same moss on your own stone object as a new object, 'moss on …', attached to it.
  - `moss.feet(yard, laid, turf=0.5, ferns=1)` adds moss tufts, grass and ferns where rocks meet the soil.
  - `moss.add(material, lichen=0.6)` adds lichen crusts to any stone material.
- **Trap:** a mossy rock is taller by its moss. The `top` that `at_spots` gives back is the top of the moss, so a lantern set on a mossy seat stands on the moss.
- **Trap:** moss with thickness that stops at full depth reads as foam slabs, and moss as a separate sheet on the ground reads as cut-out squares. The tool's cushions rise from nothing and fray at the edge; the moss at the feet is tufts on the soil.
- **Trap:** a 1 m mossy boulder carries about 7,000 tufts and a quarter more faces. A bank of 120 mossy boulders carries about 143,000 tufts. Pictures with mossy rocks draw about 18% slower. For moss that is far off, use `moss_pile=0.5` or `moss_style='paint'`.
- **Trap:** `moss.grow` follows your object as it is drawn now; grow again after changing the object. Inside a basin's bowl the moss also grows under the water.

---

## Traps

- This is the helper's own account; what the session checked afterwards is in the project story, log 60.
- Its test pictures' light leaves the warm-light share under the look's floor (white lantern windows), and the veranda pair has no sky: they compare the moss, not the look.
