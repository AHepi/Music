# 53 Plan for Opus: ground tools

What this file is: the plan a worker session (Opus) follows, written on 4 November 2026 after the research in `53 Research - ground, wet and dry, pebbles and tracks.md`. The owner's words that set it (decision 69): "Can we work on ground tools now. Maybe start with dry dirt ground, wet dirt ground, then adding making separate rocks/pebbles layers. Then add a tracks layer that automatically changes according to conditions of wet or dry. So human tracks, car tyre tracks, cart when tracks. The last two will need to add things like sink holes and depressions according to age and so on."

Read this whole file, then the research file, then `plugins/painted-place/brief/store/Store.md`, `store/tools/store.py`, `store/tools/lay_walkway.py` and `store/tools/puddle.py` (the two tools whose shape these follow), `austerity-explainer/project-notes/Decisions.md` items 62 to 69, and the story's logs 51 and 52. Everything below assumes you have.

## The idea in three sentences

Ground is built in layers that each read the height of the one below: the shape, the soil, the stones, the thin stuff, then the wear. Wet and dry are one soil whose wetness varies over the ground by height and by a dial, not two materials. Tracks are real depth carved into the ground along a line the builder gives, and their look (lip, water, crumbs, dust) follows the wetness and an age dial; nothing places itself.

## Standing rules (unchanged)

The repository's rules file; decisions 45 (no technique in a builder's request), 49 (no keys or names in requests), 57 (the owner judges), 62 and 65 (the kit carries the look; the store places nothing), 68 (two passes; feed the store). Plain words to the owner, one word per thing: **ground** (the object), **soil** (its material), **wetness** (0 dry to 1 flooded), **stones** (the separate rocks and pebbles), **track** (any mark of passing: ruts, a path, footprints), **age** (0 fresh to 1 old). Every tool answers `--help`, has a `TOOL` dict, works only on what it is given, is tested, catalogued and read by a fresh checker before it is called finished. Lessons for every failure; a story log entry (the next is 53); commit and push with the session's attribution lines.

## Step 1: the ground and its soil (about three hours)

`store/tools/ground.py`:

- `make(size=(x, y), location, cell=0.1, relief=0.08, camber=None, seed=0, soil='dry dirt')` makes a subdivided ground plane with soft hollows and humps (two scales of noise: metre-wide swells of about `relief`, and hand-sized roughness), optionally cambered along a line the builder gives (`camber=(points, width, drop)`: the middle of the way higher than its edges by `drop`, which is what sheds water in the research). Returns the object; records its own hollows (a float point attribute `hollow`, 0 on crowns to 1 in the deepest dips) for the layers above to read.
- `wet(ground, wetness=0.5, pattern='hollows')` sets the ground's wetness: a float point attribute `wetness` from the `hollow` attribute and the dial, so the four states lie on one surface (crowns dry, slopes damp, dips wet, the deepest dips flooded above a threshold); `pattern='even'` for ground wet all over (after rain), `'hollows'` after rain has drained. Returns the list of flooded dips (centre, size) so the builder may put the puddle tool's water there with `puddle.make(..., level=...)`; the tool does not make puddles itself.
- Two soil materials in `made.py`, one dial between them: `MADE • dirt` (built from the shelf's `brown_mud` and `gravel_road` photographs, or `mud_forest` for dark soil, chosen by option) reads the `wetness` attribute and does the research's curve: dry is pale with a dust crust and a little bleaching; damp darker; wet dark and glossy with the bumps still in the reflection; flooded handled by the puddle water. The darkening follows the curve (strongest for mid tones), the gloss comes in after the darkening and goes first on drying. A `crust` dial adds dried-mud cracks (a Voronoi edge pattern, plates 5 to 30 cm, curled edges in the bump) where wetness is low on ground that was once wet. Make `MADE • dirt, dark` the same with the forest mud.
- Test: a 12 x 12 m ground at wetness 0, 0.3, 0.6, 0.9 drawn under one low amber lamp and a blue world from the builders' eye height; the four states visible on one ground at 0.6; the crust at 0; the measure tool's bands on each. Count: the `hollow` and `wetness` attributes run 0 to 1; flooded dips returned only above the threshold; same seed same ground.

## Step 2: stones in layers (about two hours)

`store/tools/stones.py`: `scatter(ground, area=None, layers=('rocks', 'pebbles', 'grit'), amount=1.0, where='hollows'|'even'|'crowns', buried=0.35, seed=0)` lays separate stone objects on the ground within the area the builder gives (a rectangle, a polygon, or the whole ground): three size layers (rocks 8 to 20 cm, pebbles 2 to 6 cm, grit under 2 cm as one merged mesh for speed), each stone sunk into the soil by `buried` of its height so the soil covers its foot, more small stones at the feet of big ones and in the hollows (reading `hollow`), fewer in wet mud (reading `wetness`: wet ground swallows stones, dry worn ground shows them). Stone shapes: a dozen seeded prototypes with the store's `STONE • unique sandstone / damp soot` or a dark river-pebble material you make (`MADE • pebbles, wet` reading `wetness` too, so stones in a wet dip are dark and glossy). Returns the objects by layer. Test: counts per layer scale with `amount`; no stone floats (lowest point below the ground's surface there); more stones per square metre in the hollows than on the crowns when `where='hollows'`.

## Step 3: tracks (about five hours; the owner's main ask)

`store/tools/tracks.py`, one tool with three kinds, all carving the ground's own height along a line the builder gives (points, a curve or a line mesh, as lay_walkway reads lines) and all reading the ground's `wetness` at each point:

- `ruts(ground, line, vehicle='cart'|'car'|'lorry'|custom (gauge, tyre width), passes=1, age=0.3, seed=0)`: two grooves at the vehicle's wheel spacing (cart 1.45 m, car 1.4 m, lorry 1.7 m) and tyre width (cart 0.06 m, car 0.11 m, lorry 0.18 m), carved into the ground by moving its points down: depth from the wetness (dry firm 1 to 2 cm, damp 3 to 5, wet 6 to 12 cm, deeper with `passes`), a raised lip on both sides where wet (soft ground pushed aside), none where dry, the floor flat for a tyre and narrow-rounded for a cart's iron tyre, deeper by half again in the first and last 2 m of the line and at turns (the research: slowing, starting, turning). The tyre's tread or the iron band's plain floor as a small bump pattern along the groove. The groove's floor gets `wetness` raised (water gathers there) so the soil darkens in it; where the floor's wetness passes the flooded threshold the tool returns puddle spots (centre, length, width, turn along the groove) for the builder to give the puddle tool; it does not make the water itself.
- `path(ground, line, width=0.5, age=0.5, seed=0)`: one trodden strip, lower by 2 to 6 cm, polished in the middle (writes a `wear` attribute the dirt material reads to pale and smooth the middle), wetter in its hollows, its edges soft.
- `footprints(ground, line, stride=0.75, boot=(0.30, 0.11), age=0.2, seed=0)`: single prints stamped along the line left and right of it with a stride, each a boot shape pressed into the height: in wet mud deep (2 to 4 cm), heel deepest, the mud slumped out to a soft lip; in firm damp mud shallow and sharp; in dry dust only a `wear` mark (brushed-clean oval) with almost no depth. Hobnail pattern as a small bump where sharp.
- **Age** (0 fresh to 1 old) moves four things together, for every kind: edge sharpness (a smoothing of the carved points' profile that grows with age), the floor's darkness and sheen (fresh wet floor dark and glossy; old floor matte but still darker; written into `wetness`/`wear`), debris (old grooves get grit from the stones tool's smallest layer, and fallen leaves if the builder passes a material), and water (fresh: the whole groove damp; half-aged: water only in the deepest third; old: a dry ring and a cracked floor where the puddle was, which is the `crust` dial applied along the groove).
- **Sink-holes:** `potholes(ground, line, at=(distances along the line) or 'ends and turns', size=0.5, age=0.6)`: round hollows with a steep front edge and a splashed-out back edge, 5 to 15 cm deep, in the wheel lines at the points given, flooded by wetness and age as above. Placed only at the distances the builder gives, or at the line's ends and turns when the builder says so.
- The carving is done once on the ground's mesh points (the ground from step 1 is fine enough at `cell=0.1`; the tool refines the mesh under the line to 2.5 cm cells first, with a bmesh subdivision of the faces the line crosses, so a 6 cm cart tyre has points to carve). Normals are recalculated; the ground's `hollow` attribute is updated so the stones and wet read the new shape.
- Tests: a straight cart track on wet ground has two grooves 1.45 m apart with lips; the same on dry ground has no lips and a quarter the depth; `age=1` floors are smoother than `age=0` (measure the profile's second difference); footprints alternate sides with the stride; potholes only at the distances given; nothing is carved outside the line's width plus the lip; same seed same marks.

## Step 4: the dirt material reads it all, and a worked ground (about two hours)

- `MADE • dirt` reads `wetness` (dark, gloss), `wear` (pale polished middle of a path, brushed-clean footprints in dust) and `crust` (dried cracks); the wet puddle water from the puddle tool sits in the flooded dips and groove floors.
- A worked example script `store/examples/ground - a cart track after rain.py` (the store's first example): a ground with a cambered lane, wet after rain, stones in the verges, cart ruts with potholes at the gate, a footpath crossing, footprints to a door, the puddle tool's water in the returned spots, drawn from the builders' eye height at 540 x 960 and finished with `finish.py`. Its picture goes to the owner beside the second-pass military base (log 50) and the chapel lane (log 52), as the test the owner judges.
- Cards: each tool's card from the example; the dirt materials' cards.
- `Store.md`: the catalogue rows by `catalogue.py`; one new paragraph in the conventions, "Ground", saying the layers and that the tools carve the ground the builder gives along the lines the builder gives.

## Step 5: checks and records (about two hours)

- Tests in `tests/test_store_tools_more.py` for every claim above; the parts test is untouched; `run_tests.sh` passes.
- A fresh checker reads the three tools, the two materials and the example against this plan and the research, draws the example, and reports; fix its findings before calling the step done.
- A trap for `brief/Traps.md`: decal tracks look painted under a low lamp; tracks are carved depth.
- Records: story log 53, lessons, status, decision entries if the owner decides anything, this plan's "what happened" as a short section at its end, commit and push, the project story sent.

## What not to do

- No simulation of vehicles or water; the tools carve once along given lines.
- No placement by the tool: no "find the road", no "put ruts where the ground is flat"; the builder names the line, the vehicle, the wetness and the age. The ground's own hollows decide only where wet and small stones gather within what the builder gave.
- Do not change the old ground surfaces on the shelf; the dirt material is new beside them.
- Do not touch `The look.md` or `reference/`.

## Time budget

About fourteen hours. If it does not all fit: steps 1, 2 and the ruts and path of step 3 first, the example and the checks, then footprints, potholes and age's debris can follow.


## What happened (4 November, 17:16 to 21:30)

- **Steps 1 to 3 done as planned:** `ground.py` (relief, camber, wetness by height and dial, four states on one ground, water,
  cracked beds), `stones.py` (by a helper: rocks, pebbles and grit, `settle`), `tracks.py` (ruts, path, footprints, potholes, one age
  dial, the mesh divided under each mark, every random choice seeded); soil materials `MADE • dirt` and `MADE • dirt, dark`.
- **The owner changed the plan twice** (decisions 71 and 72): the tools must also make deep motor ruts in a wet field like the
  owner's picture, and carts must stay. Added: heavy ruts (a tractor's tread ridges holding water; lumpy, torn, smeared walls),
  hoof prints for a cart's horse, a grass tool, a litter tool (leaves, twigs), rain rings on the water, and a second worked example.
- **The water changed:** one flat sheet per pool, cut from the ground's own faces (no boxes past the ground's edge or into another
  dip); water stands only in a groove's lower part; ground long dry holds none.
- **Photographs used whole** (the owner's question about PBR): `ground.detail` really moves the near ground by the soil's own
  height photographs; churned mud is Poly Haven's `brown_mud_03` where tracks left bare earth; the soils use Poly Haven's normal
  pictures; scanned grass, nettles, dandelions and branches and two photographed skies came from Poly Haven into the store.
- **Step 4:** the worked examples are in `store/examples/`, with their pictures; cards for the ground, tracks, grass, litter and
  stones tools and for the new materials; the "Ground" paragraph in `Store.md`; the catalogue rebuilt.
- **Step 5:** tests in `tests/test_store_ground.py` (not in `test_store_tools_more.py`, which the stones helper was editing at the
  time); `run_tests.sh` passes (64 lines). The trap about painted tracks and one about water past the ground's edge are in
  `brief/Traps.md`. The fresh checker was stopped before it reported: **no independent check yet.**
- **Not done:** leaves from photographs (the owner offered a generated sheet); Poly Haven's scanned rocks for the stones tool; a
  fresh builder using the ground tools.

## Traps

- A ground carved after the stones were laid leaves stones floating over the groove: lay tracks before stones, or re-drop the stones (the stones tool should offer `settle(ground)`).
- The `wetness` attribute is per point; a coarse mesh makes blotchy wet edges. Keep `cell` at 0.1 m or finer, and refine under tracks.
- Displacement in the material cannot stand in for carving: the puddle tool and the stones read the real mesh.
- Builders' eye height and the tall frame show the near ground at 2 m wide: a cart's two ruts 1.45 m apart fill the frame's bottom. Test at that framing, not from above.
- The same seed must give the same ground, stones and tracks: every random choice through the seeded generator, as in the store's other tools.
