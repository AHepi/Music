# Wear recipes (where each kind of wear goes, how much, how big, in what order)

What this is: the rules for dirt, grime, weathering, wetness, damage, moss, rust, weeds and rubbish. The kit's numbers
are in `place-kit/data/dial_table.json` and `place-kit/data/looks/`; this text says why. Each number says what kind it
is: **measured** (taken from a picture, render or test), **judged** (chosen from evidence) or **invented** (a guess).

**Example first: a road cut by heavy carts (the coal-mine yard built earlier in this project).** The yard has five cart
roads, each with two wheel ruts. Across a road, from one side to the other: the rough ground beside it; a raised bank
of thrown-up earth; the left rut (a trench, with water lying in its low places); the strip between the ruts; the right
rut; the bank; the rough ground again. The numbers (measured in the yard's build code unless marked):
- the two ruts of a road are 1.24 m apart (a cart's gauge; the generic range is 1.0 to 1.8 m: judged);
- each rut is about 0.15 m deep (0.13 to 0.21 m along the road, because the depth wanders) and about 0.4 m across at
  half depth;
- a bank beside each rut stands about 0.30 of the rut's depth;
- the yard has eight puddles, some of them lying in the ruts;
- a lighter road, the way the plugin drafts one, has ruts 5 to 15 cm deep (invented, 8 cm by default);
- on a lightly used road a low crown of grass may grow between the ruts (the setting `centre_grass`); on a busy road the
  whole width is bare;
- where animals walk (a farm track, a towpath) hoof prints can be added with `"hoof": true`: round dimples 12 to 14 cm
  across, one every 0.8 to 1.0 m, left and right in turn (invented; the canal lock's towpath used them);
- nothing grows in the wheel tracks: the count of roots there is exactly 0 (measured gate).
These are real shape: the `roads` verb cuts them into the ground mesh, and the dirt-road surface and the wetness layer
go on top. A texture alone makes a flat road with brown stripes.

## The layers, in their fixed order

The order was measured on the street and never changes: dirt and grime go on first (water then sits on top of them);
then wetness; then cracks_and_chips and edge_wear (they stay dull when wet); then moss_and_algae; then rubbish last.
Rust is part of the first group, for iron. 3D plants and litter are separate pieces placed after the layers.
Each object needs its own `pk_<layer>_amount` property; `age` writes it. Without it the layer is silently off there.

| Layer | What it is (and the words people use) | Where it goes |
|---|---|---|
| dirt | soil film, mud splash, dust, polish on worn roads, dried puddle rings | low places; a band up the wall foot measured from each wall's own bottom edge (the street's splash band was 15 to 35 cm; stone plinths 15 to 46 cm high once hid it when measured from the world floor); footfall |
| grime | soot, run-off streaks under eaves and sills, damp bands, stains | sheltered places and under projections; soot above hearths and chimneys. A real TIDE LINE (a band at the water's own height) is not made by a layer: build it as shape (a band of darker, slimier stone, a row of barnacle shapes) in the part that owns the quay or the wheel pit. The layers darken an object's own foot and the wall under a sill. They do NOT darken the ground where a thing stands (under a crate, a stall or a wagon, round a post), stone under iron (a rust run below a ring), or where water runs on the ground (the drip line under the eaves, a spout's spill, down a slipway): build those as a few big, soft, darker designed shapes in the part that owns the thing |
| weathering | silvering of timber, sun fade, bleaching, patina | sun-facing, rain-facing, upper surfaces; the grey-silver of old unpainted timber |
| wetness | darker, smoother, a film coat, puddles | low places and rut bottoms; ground within 1.5 m of any water (the plan masks wet it: full at the waterline, fading to nothing 1.5 m away; measured on a quay: 0.59 at 10 cm, 0.16 at 1 m, 0 from 3 m); by state (dry, damp, wet) |
| cracks_and_chips | split planks, plaster loss, chipped stone corners, a sagging roof | corners and ends; one clean line, not a net |
| edge_wear | worn bevels, pale rubbed edges | edges and corners a hand or a cart touches |
| moss_and_algae | flat moss, algae, lichen | damp and shaded; never on a trodden or keep-clear dot |
| rust | iron: height bands, collars at joins, runs below | iron roles only |
| rubbish | leaf litter, straw, wet straw, mud | wall feet, gutters, road edges, the corners; never on the wheel tracks |
| plants, litter_pieces | nettle, fern, bramble, tufts, leaves, sticks, pine needles, clods, straw | by habitat gates; chunky designed shapes |

## Joints (between stones, bricks and planks)

A joint is a narrow gap, and it is easy to lose. On the street, sett joints showed only while the photo made them dark: in
test lightings that were flat, wet or from the side they vanished (6 of 22 lightings passed, only the dry ones; measured).
The fix was a joints step after the wetness layer: the joint is darker, stays dull when wet (rougher, less shine and water
film), and the stone's edge gets a rounded slope; puddles still cover joints. Then 21 of 22 lightings passed (18 of 22
counting every dot; measured). Real 8 mm grooves cut into the road looked worse in the middle distance and were switched
off. So: give every joint a darker, duller, sloped look, check the first preview under flat, wet and side light, and do not
rely on the colour alone.

## How much, how big (the numbers)

- **Grime budget** (measured, street): at most about a quarter of a surface darkened by about a third. More turns the
  street to one dark mush (the check failed when more than 25 percent of a class was darkened by a third).
- **Pale first on dark surfaces** (measured): on a surface where most dots are under 0.10 brightness, a dark mark is
  lost; make the mark by lifting patches paler than the film round them.
- **The darkest part of a mark** stays at 0.10 or above (measured: the film's finishing curve crushes values under about
  0.12); keep a surround of about 0.18 or more (judged).
- **Marks are sized in picture dots**, not metres, so they survive the painter and a phone screen (measured on the street
  plates after painting): a patch about 15 dots wide at contrast 0.04, a crack 3 dots wide at contrast 0.11, a fleck
  5 dots at 0.08. `set_picture_size` tells the layers how big a dot is for the camera. A mark that looks right at full
  size can vanish at phone size.
- **Exact-zero gates for plants** (measured): none where footfall is 0.6 or more, where the crown is 0.7 or more
  (on a paved street, the highest middle of the road), where keep-clear is 0.5 or more; none in a puddle; litter keeps
  5 cm clear of other litter; no rubbish on the crown. The audit counts these and each count must be 0.
- **Moss is never brighter than the stone it grows on** (a courtyard fix), and it reads by contrast, not by size.
- **Cover**: the street's weed dial settled at 0.01 to 0.02, about 1 to 2 percent of the ground (judged); a `neglected`
  place can take about twice that (invented).
- **Wetness colours** were measured only for stone and brick: wet walls came out 0.84 of dry and the wet foot 0.66, and
  the first try made walls lighter when wet (wrong). For timber, thatch and plaster the ratios are UNMEASURED: judge
  by eye and say so. The roughness map does the work (dry about 0.9, wet about 0.3: measured); the specular map changed
  the road by only 0.006 (measured). No shine on walls.
- **Dirt darkens by multiplying** the colour under it, so the surface's own variation shows through (judged). A layer
  that paints a flat colour over the top hides everything below it.

## The four looks, and the three states

The looks are presets of dial values and nothing else (`place-kit/data/looks/`):
- `kept`: light dirt, no moss on walls, little rubbish. A tidy farmyard or a museum.
- `lived_in` (default): normal use: some dirt and grime, edge wear on what is touched, a little moss in the damp,
  a few weeds at the edges, some rubbish at the wall feet.
- `neglected`: stronger dirt, grime, weeds, moss, rubbish and wetness. A road nobody maintains.
- `derelict`: adds cracks, sag and heavy moss. A ruin. (The pass bends, chips and leans parts but never removes one: missing,
  slipped or replaced pieces are built by the builder as shape, for example a missing slate, a gap in the planking, one new board.)
Different roles can have different looks (`look_by_role`). State: `dry`, `damp`, `wet`; switch it with
`age --state wet` or `finish --state damp`. Only the wetness layer changes, and puddles appear by depth (judged: about
40, 40 and 20 percent of the puddle area in three depths).

**The dials and the state are the same for every role.** There is no setting that turns the wetness or the moss up for the waterside roles only. To treat one role differently, give it its own look with `look_by_role` (the four
looks differ in how much wetness and moss they hold), or switch a layer off for it with an `off` entry and a true reason; for a wet quay, put the whole place in state `wet` and rely on the water-edge dampness above. What the
kit does NOT make: seaweed, barnacles, shells, foam and reeds as plants (the plants it scatters are tuft, clover, nettle, fern, bramble and moss cushion, `place-kit/data/species.json`), nor the rubbish of the place's own
work (its litter is only leaves, pine needles, sticks, straw and clods): fish scraps, crushed ice and broken fish boxes at a market; coal, cinders and ash at a station or a mine; sawdust at a mill. Build those as a
few big designed shapes in the part that owns them, where the work happens.

## Honest note: what shows at film size

On the street, after calming the layers, a viewer could see little at film size except rust and a few weeds: the walls
were nearly black and seen edge-on, so soot, run-off streaks and damp bands vanished (measured). In the garden, what
read was the designed geometry plus real normal maps: bridge posts and beams, planks that were all different, tiles
that were chipped and slipped, tufts with seed heads, moss cushions. So lean on shape, normal maps and 3D plants, and
keep the shader marks few, big and pale-first on walls. Where a mark is too small to see at the picture's size, the
audit does not know it: look at a 100 percent crop and at a phone-sized one.

## Things that already went wrong

- Weeds stood in puddles and mid-slab on a pavement; moss looked like cut-outs; doorsteps went cold blue; cracks were
  over-even. All were fixed by gates, by calming the colours and by varying the shapes.
- A moss patch looked like a "sticker" on a lantern and the weathering splash gave stripes on rocks: tone the layers
  down on stone, and keep marks few and soft.
- Moss cushions heaped up like rows of bean bags: vary their size and keep them off the ridges.
- A builder claimed 9.8 percent moss and mould on planks; a fresh checker counted 0.6 percent olive pixels on one run
  of planks and 3.8 percent on the other. Count by the picture.
