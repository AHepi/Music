# Surface recipes (surface by surface)

What this is: for each kind of surface, how its relief is made, how strong the normal map is, whether it is
displaced, how big one tile is, how it is mapped, how shiny it is and what colours it has. The numbers the kit really
uses are in `place-kit/data/surfaces.json` (each with its kind and source); this text explains them, so read both.
Every number below says what kind it is: **measured** (taken from a picture, a render or a test),
**judged** (chosen by people or checkers from evidence) or **invented** (a starting guess nobody has tested).

**Example first: the dirt road.** One tile covers 2 m. Its height picture is soft clods, blurred 1 to 2 pixels at
2048 pixels, with nothing smaller than about 5 mm (no pores). The normal map is made from it so that the steepest
one percent of the slopes tilts the surface 26 to 34 degrees (judged, garden), and its strength in the material is
0.8 to 1.0 (judged). Where the mesh is graded (squares of 0.12 m near the camera, each step 1.09 times bigger, out
to 5 m: judged, from the coal-mine yard) the surface is also displaced 6 cm (judged, the same yard used 5 to 6 cm).
Roughness is 0.85 to 0.95 when dry (measured on the wet street: dry about 0.9) and about 0.3 in the wet ruts
(measured: the wet recipe gave 0.28). The colour is a dull brown with a few big darker patches, never an even brown.

## Two words people mix up

- **map steepness**: how steep the slopes in the height picture are when it is turned into a normal map. Set it so the
  steepest one percent of slopes tilts the normal 26 to 34 degrees (judged, from the garden). Too low and the map does
  nothing; too high and it looks like plastic.
- **node strength**: the Strength of the Normal Map node in the material: 0.6 to 1.0 (judged). Where displacement is on
  as well, multiply it by 0.6 (judged, coal-mine yard).

## The rules that go with every surface

1. Colour pictures are sRGB. Data pictures (normal, roughness, height) are Non-Color.
2. Normal maps are OpenGL: green is up the picture. Set a generated image's colour space right after `images.new` and
   before writing any pixels. Blender 5.2.2 wipes a generated image to black if you change it afterwards.
   A normal map you did NOT make may use the other (DirectX) convention, and a name such as `nor_gl` is only a label
   (for such maps `normals-test` reads the convention from the file name, it does not measure it). Measure it: draw three
   small panels under a low raking light, one with the map as it is, one with its green channel flipped, and one with
   real displacement from the same height picture; the right map agrees with the displaced panel (the coal mine did this
   for every uploaded map). Flip green in a copy, never in the person's file.
3. The Bump node's Distance default (0.001) is nearly flat. Never turn Strength up where the real fix is Distance
   (0.02 to 0.1 for a visible bump; judged from the cookbook).
4. Fine grain is carried by the normal map on every surface. Displacement is added only for the roles whose `displace` flag is true in `place-kit/data/roles.json` (nine: dirt road, mud, forest floor, stone paving, gravel,
   rock ground, plain earth ground, stone wall and thatch), on a dense or adaptive mesh, never on a flat plane (`finish` makes the mesh fine: a grid for a plain rectangle, a split in place for any other shape).
5. UV first. A tangent-space normal map needs a UV layer on every object that uses it (box UV per face in metres for
   walls, stones and timber; planar from above for ground and water; planks: u along the length, v across, plus a
   random offset for each plank, and mirror or turn some planks and switch the knot off on about half; roof tiles: put
   the UV on the one prototype tile and every instance inherits it). Never mirrored islands (judged: at most 2 percent).
6. Hide repeats: look the picture up twice, the second at 0.79 scale and offset 0.37 and 0.58, and blend the two by a
   slow noise (judged); give every object its own small tint and offset.
7. At most 4 image maps in one material (judged: render time and file size).
8. Marks and relief are soft and large: nothing finer than the style allows (`style-rule-and-measures.md`).
9. Where two ground surfaces meet (road, verge, forest floor), blend them with a mask instead of a hard line, and keep to
   one ground mesh with a material driven by attributes where you can: two overlapping meshes with two materials show a hard
   seam or fight each other (z-fighting). The coal-mine yard did it with one graded ground mesh.
10. Real displacement is heavy on memory: 1.8 GB at 540 x 960 and 4.7 GB at 1080 x 1920 with a dicing rate of 2 pixels
   (measured, coal mine). If memory is short, raise the dicing number to 3 or 4. Adaptive subdivision with simple (not
   smooth) subdivision keeps flat faces flat.
11. Never a normal map and a bump on one surface (judged, garden): one of them is doubled relief.

## The surfaces

Each line: tile size (metres); height; node strength and displacement; UV; roughness; colour. Kinds in brackets.

**dirt_road** is above. UV planar from above. Colour value about 0.20 to 0.40 (invented).
**packed_earth** (yard, doorstep, an earth floor, a bank, a seabed; the role `ground.earth`): tile 2 m, node strength 0.8 and displacement 3 cm in the data; flatter clods, half the size of the road's; UV planar; roughness 0.8 to
0.95, lower (about 0.7) where feet polish it (judged).
**mud**: tile 5 m, displacement 6 cm, strength 0.8, roughness 0.9 (judged, coal-mine yard); dark brown, wetter than the
road; puddle hollows 4 cm deep (judged, same yard); shine in the hollows (roughness 0.3, measured).
**forest_floor** (leaf litter, needles, bare soil): tile 2 m (invented); height from a few big leaf shapes over soft earth;
normal strength 1.0 and displacement 4 cm in the data (the role displaces); roughness 0.85 to 0.95; dull olive-brown with a few red-brown leaves; moss and plants
come from the growth step, not from the picture.
**grass**: tile 3 m (invented); very soft height; strength 0.6; roughness 0.85; olive and dusk green (never fresh spring
green: judged, garden style note); chunky 3D tufts (5 to 9 simple blades) do the real work.
**timber_weathered** (house walls, posts, beams, fences, gate boards): tile 1 m by 0.25 m for a plank (judged); grooves along the
grain, 2 to 4 soft knots, 1 or 2 thin checks, a calibrated steepness; node strength 0.8 to 1.5 (judged: the garden's
planks used up to 1.5, stone 0.8); no displacement; UV plank method; roughness 0.65 to 0.9 (judged: no gloss); warm
grey-brown #987a6a and #8e6958, silvered grey-brown #9b8476 on sun-bleached boards (judged, garden); darker, greener
near the ground.
**timber_planks** (floors, doors, decks): as timber_weathered; widths 9 to 17 cm, gaps 5 to 14 mm (judged, garden
bridge), worn pale along the walking line (0.02 to 0.06 lighter: judged).
**log_wall**: tile 1.2 m (invented); round logs as real geometry (a bevelled cylinder with a crack), bark-like normal
map; roughness 0.8; corner notches as shape, not texture.
**plaster_lime** (plastered and whitewashed walls, and the plaster between the timbers of a timber frame): tile 1.5 m;
soft blotches 20 to 60 cm across, a few clean cracks, plaster loss patches that show the brick, stone or timber
underneath; node strength 1.0 (garden plaster); roughness 0.75 to 0.95; cream to grey-cream, darker and greener at
the foot.
**stone_rubble** (footings, walls, field stone): tile 2 m, strength 0.8 (garden stone); stones are geometry (blocky,
4 to 6 readable planes, rounded corners, half-buried); roughness 0.75 to 0.9; warm grey-beige with olive moss.
**thatch**: tile 1.5 m (invented); bunch ridges running down the slope, a ragged eave edge; displacement 4 to 6 cm
near the camera (invented, from the mud's 6 cm); node strength about 0.5 (0.8 times 0.6, because displacement is on); UV along the slope; roughness 0.9; straw
gold at the top fading to grey-brown and green at the lower, damper part; sag and thin patches as geometry.
**shingle_wood**: tile 1 m (invented); rows of overlapping boards, each its own tone; no displacement; roughness 0.8.
**roof_tile_clay**: one prototype tile with its own UV, instanced; node strength 0.8 to 0.9 (garden roof); tile tones
differ by at least 0.02 in brightness, a few chipped, slipped or missing (garden check); roughness 0.55 to 0.7.
**slate**: tile 2 m, depth 4 cm, roughness 0.55 (judged, coal-mine scene); cool blue-grey, pale marks only on dark tones.
**iron_forged** (bands, hinges, nails, cramps): tile 2 m, depth 1.6 cm (judged, coal-mine scene: metal); a few pits, not
a texture; roughness 0.6 clean to 0.85 rusty; rust brown #5a3a2a with a lighter edge (garden); metallic 1 on clean
metal, 0 on rust (judged).
**straw**: loose strands as 3D litter pieces (thin, curved, short: the street's first straws looked like
matchsticks); the surface under it is packed_earth.
**wicker**: tile 0.5 m (invented); woven height picture, strength 0.8; roughness 0.8; warm tan.
**cloth_sack / rope**: cloth: tile 0.3 m, strength 0.5, roughness 0.9; rope as a twisted bevelled cylinder with a tiling
twist normal map (all invented).
**ceramic**: roughness 0.3 glazed, 0.8 unglazed; one clean chip is better than texture (judged).
**bark**: strength 0.9 (garden); deep soft ridges along the trunk, moss on the damp, shaded side (judged).
**foliage cards**: leaves and needles on cards or clumps; colour variation only, no normal map (judged); designed as
chunky clumps (the garden's pine needles read as hair until made as brush-stroke clumps).
**trees** (the Japanese garden's maples, judged): leaves made as chunky balls looked like popcorn. Use flat pointed leaves
over a dark core, at real size (5 to 12 cm, not 20 to 34 cm; about seven lobes for a maple), a crown in separate layers
with gaps so the trunk and a low sun show through, translucent leaves, and colours from deep red to a few yellow-green
and brown.
**water_still**: planar UV, a gentle swell normal map, roughness 0.05 to 0.15, clear with a visible bed near the bank
(judged); the garden's swell map read +0.39 in the direction test, lower than its other maps but above the +0.25 line.
**glass_old**: roughness 0.05 to 0.2, a little dirt (a thin grime layer); glass needs its see-through unhooked from any
picture (model lint checks it).

### The other surfaces in the data (read the numbers from `place-kit/data/surfaces.json`; this table is the short form)

The recipes above are the ones this text explains. `surfaces.json` holds 45 ids; these are the ones not named above. All their numbers are first tries (invented) unless the file says otherwise.

| Surface id | Used for | Tile | Normal strength, displacement | Roughness | Bevel and UV |
|---|---|---|---|---|---|
| `gravel_path` | a gravel path, towpath or drive (role `ground.gravel`) | 1.5 m | 1.0, 4 cm | 0.7 to 0.95 | planar |
| `cobble_paving` | cobbles, setts, a paved quay (role `ground.stone_paving`) | 1.5 m | 0.9, 3 cm | 0.6 to 0.9 | planar; joints darker and duller |
| `flagstone` | a flagstone floor (`floor.stone`) | 2 m | 0.9, none | 0.6 to 0.9 | planar |
| `timber_beam` | posts and beams (`timber.post`, `timber.beam`) | 1 m | 1.2, none | 0.6 to 0.85 | 6 to 12 mm, plank UV |
| `plaster_lime` | plastered and whitewashed walls (`wall.plaster`, `wall.timber_frame`) | 1.5 m | 1.0, none | 0.75 to 0.95 | 8 to 15 mm, box UV |
| `cob_wall` | a cob or clay wall (`wall.cob`) | 1.5 m | 1.0, none | 0.8 to 0.95 | 8 to 15 mm, box UV |
| `stone_dressed` | cut stone: coping, steps, quoins (`stone.step`) | 1.5 m | 0.8, none | 0.55 to 0.85 | 8 to 15 mm, box UV |
| `ceramic_glazed` | pots, jugs, bowls (`prop.ceramic`) | 0.5 m | 0.4, none | 0.25 to 0.6 | box UV |
| `water_sea` | sea and harbour water (`water.sea`) | 8 m | 0.4, none | 0.05 to 0.3 | planar |
| `rock_ore` | bare rock ground, a quarry (`ground.rock`) | 2 m | 1.0, 4 cm | 0.6 to 0.9 | box UV |
| `tile_floor` | a tiled floor (`floor.tile`) | 1 m | 0.7, none | 0.4 to 0.8 | planar |
| `carpet_fabric` | a carpet or rug (`floor.carpet`) | 0.5 m | 0.6, none | 0.9 to 0.98 | planar |
| `generic_wood`, `generic_stone`, `generic_metal`, `generic_cloth` | the fallback for an unnamed prop of that stuff (`prop.wood`, `prop.generic`, `prop.imported`) | 1.0, 1.5, 0.5, 0.5 m | 1.2, 0.9, 0.8, 0.7; none | 0.65 to 0.9, 0.6 to 0.9, 0.4 to 0.8, 0.85 to 0.95 | 6 to 12 mm, 8 to 15 mm, 4 to 8 mm, none; box UV |

### First guesses for other kinds of place (invented unless marked; confirm with a small test plate)

| Surface | Tile | Normal and displacement | Roughness | Note |
|---|---|---|---|---|
| brick | 1.5 m | strength 1.0, depth 3 cm (judged, coal mine) | 0.85 | mortar lines slightly darker and rougher; soot above sills |
| concrete | 2 m | strength 0.6, no displacement | 0.8 to 0.95 | big soft stains, hairline cracks, rain streaks |
| tarmac | 2 m | strength 0.8, no displacement | 0.9, wet 0.3 | patched cracks, painted lines worn pale |
| sand | 3 m | strength 0.5, no displacement | 0.9 | wind ripples as soft height; footprints as shape |
| snow | 3 m | strength 0.4, no displacement | 0.6 | blue shade; dirty at the edges of paths |
| rock or ore | 2 m | strength 0.9, displacement 3 to 5 cm | 0.7 | big blocky planes, mineral veins as a few big marks |
| steel plate, painted metal | 2 m | strength 0.6, depth 1.6 cm (judged) | 0.4 to 0.6 | paint chips at edges and bolts, rust below them |
| tile or stone floor | 1 m | strength 0.8, no displacement | 0.4 clean, 0.8 dull | joints darker and duller (the street needed this), worn paths |
| cloth, carpet | 0.5 m | strength 0.5 | 0.9 | worn pale along the walking line |
| sea or river water | 5 m | swell normal map, no displacement | 0.05 to 0.15 | foam as a few big shapes at edges and posts |

## Photo surfaces from Poly Haven (CC0, fetched at run time, never shipped)

Poly Haven pictures are free to use without credit. The kit's `place-kit/data/polyhaven_choices.json` is a SMALL
SAMPLE read once from the public Poly Haven list on 23 October 2026: one or two pictures for each kind of surface the kit
knows, and a few everyday props, each with its real size read from the list and a caution. It is not a shopping list for
any place. **Search the site for the surfaces and props your own place needs** (https://polyhaven.com/textures and
https://polyhaven.com/models, or the full list `https://api.polyhaven.com/assets?t=textures`, whose `dimensions` give
the real size in millimetres). The picture URL pattern is
`https://dl.polyhaven.org/file/ph-assets/Textures/jpg/<1k|2k>/<id>/<id>_<map>_<1k|2k>.jpg`. Send a generic client name
with the request, never a person's name or address. That holds for EVERY outside website or service, not only Poly
Haven (Wikipedia, Wikimedia, any download script): no name, email or address in the identity line (User-Agent), in a
header or in a file name. One helper wrote the person's email into the identity line of its picture downloads;
`plan_budget.py push` fails on an email-like string in a script that makes web requests.

- Example: for a wet stone quay you would search "cobblestone", "paving" and "stone wall", draw a small test plate of two
  or three, and keep the one that reads right at film size. The sample's `cobblestone_05` (2.4 m a copy) and
  `stone_wall` (2 m) are only a starting point.
- Sample textures (one or two per kind): ground: asphalt_02, concrete_floor_worn_001, cobblestone_05,
  rectangular_paving, gravel_road, dry_ground_01, brown_mud_02, leafy_grass, forest_leaves_02, coast_sand_01, snow_02;
  floors: wood_floor_worn, floor_tiles_06; walls: brick_wall_001, plastered_wall_02, concrete_wall_001, stone_wall,
  corrugated_iron; metal: rusty_metal_02, metal_plate; roofs: clay_roof_tiles, roof_slates_02, thatch_roof_angled;
  wood: weathered_planks, rough_wood, bark_brown_02.
- Sample models: wooden_crate_01, plastic_crate_01, cardboard_box_01, wine_barrel_01, Barrel_01, propane_tank,
  metal_trash_can, old_tyre, ladder_sectioned_01, street_lamp_01, fire_hydrant, concrete_road_barrier, utility_box_01,
  painted_wooden_bench, wooden_picnic_table, planter_box_01, lifebuoy.
- If Poly Haven has no model of a prop you need, build it in a script.

How to use them: draw a small test plate of the surface first; open every downloaded picture at full size and look for
stickers, brands and digits (judgement); remember that scans alone read bland. In the street, scanned bricks looked
good in a plate, but wear showed little at film size. Designed marks, real shape and 3D plants go on top. An imported
prop counts its own maps as the normal map and roughness variation (role `prop.imported`), but still gets dirt, grime,
weathering and wetness from the pass. A scan that already carries moss gets no moss layer on top (doubled moss, judged).

A painterly material library (one the person uploaded) was tried on the street and rejected: drawing was about 7 times
slower (223 s against 33 s, measured), nothing looked painted, the brick was richer but the wet stone road came out icy
(judged). Do not offer it again unless the person asks.
