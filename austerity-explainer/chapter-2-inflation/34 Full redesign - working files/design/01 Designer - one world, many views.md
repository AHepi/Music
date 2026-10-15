# Shot plan - chapter 2 for newcomers, the full redesign - one world, many views

Source: Clara E. Mattei, *The Capital Order* (2022).

**What this file is:** a complete plan for filming all 16 pages of "33 Script - chapter 2 - what really
causes inflation - for newcomers" in the look you kept in log 32 ("Wow that's incredible. Yes keep it."):
places built in 3D in Blender by script, drawn once from their main view (the plate), repainted by Flux 3
in the series' painted style, and the painting shone back onto the set so the camera can slide without
tearing; live flames, flicker and smoke on top; typed cards for words on screen. Nothing here has been
built, painted or filmed. It is a plan from one angle, **one world, many views**: as few places as
possible, each coming back from different spots, so the viewer learns the places and is never lost, and
each plate and painting is used many times.

**The short version.** Four places, ten views, 32 shots, 13 plates, 24 paintings (about US$2.40 at
10 US cents each, at most about US$5.30 if each costs what the notice corner's did), about 3.7 hours of
filming at a planned 1.2 seconds a frame (two at a time). The two factories live in one imagined valley and
come back on 12 of the 16 pages, always in the same places and colours. Workers waiting at the gate are
simple figure shapes seen from behind at dusk, which the painter turns into painted people. The cheapest
test that shows the plan works is the flat-out factory's gate, built free, then three paintings (30 to
66 US cents, with your yes).

**Words used here** (one name each):
- **place**: one 3D set (one Blender file). **view**: one camera spot in a place. **shot**: from one cut to the next.
- **plate**: the picture Blender draws of a view, for the painter. **painting**: Flux's repaint of a plate.
- **behind painting**: a copy of a painting with the near props painted out, for what they hid once the camera moves.
- **state**: one condition of a view (for example the quiet factory with its gates shut, then working). A
  **state painting** is a second painting of the same view in another state.
- **slide**: the camera moves in a straight line toward the subject, never turning. **lens push**: the lens
  narrows (a zoom); nothing new is uncovered. **hold**: the camera is still.
- **own surface**: a sign or label that keeps its own sharp 3D lettering instead of the painting (the painter
  garbles small print).
- **story props**, **where the lines meet**, **the brightest parts**: as in "07 Composing a shot".
- **figure shapes**: plain 3D stand-ins for people (caps, coats, no faces), seen from behind.

---

## 0. The world in one picture

Four places, chosen so that every page lands somewhere the viewer has already been or will come back to:

| Place | Era | Views | Pages it appears on | What it teaches |
|---|---|---|---|---|
| **The New Zealand street** (an invented Wellington street at winter dusk) | 2020 to 2026 | N1 the checkout (inside the foodmarket), N2 the street up to the Reserve Bank, N3 the building site, N4 the petrol forecourt | 1, 2, 10, 11, 12, 13, 15, 16 | "Here": the basket, the warning, the Reserve Bank, workers, materials and machines, homes and rents, petrol and diesel |
| **The valley** (imagined: two brick works side by side at dusk) | timeless, early twentieth-century look | V1 the valley wide, V2 the quiet factory's gate, V3 the flat-out factory's gate | 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16 | The picture: spare or nothing spare, and every real case placed on it |
| **The Glasgow street** (tenements with a munitions works at the end) | 1915 | G1 the street to the works, G2 the tenement row and the half-built tenement | 6, 7 | Britain at war; Glasgow's homes |
| **The Tokyo back office** (an ordinary bank's back room at night) | 2013 | T1 the back office and its strong room | 8, 9 | New money that sat in the banks |

How the world hangs together, so the viewer is never lost:
- **Places you can see from each other.** From the checkout (N1), the foodmarket's front window shows the
  street at dusk: the petrol canopy across the road and the Reserve Bank tower's lit top. From the street
  (N2) you see the foodmarket's verandah, the petrol canopy and the building site's crane, with the
  Reserve Bank at the end. The crane shows over the forecourt (N4); the tower shows over the site (N3).
- **Neighbours at the edge of the frame.** The two works stand side by side, quiet on the left, flat out
  on the right, always. From the quiet factory's gate (V2) a slice of the flat-out factory's buff wall shows
  at the right edge; from the flat-out factory's gate (V3) a slice of the quiet factory's red wall shows at
  the left edge.
- **Rhymes between eras.** Glasgow's half-built tenement (1915, few new homes) and New Zealand's
  building site (2022, the price of building new homes) are the same kind of picture in two places.
- **One time of day everywhere:** dusk (Tokyo: night), lamps lit, the series' teal and amber. The story
  changes the states, never the light, so a return looks like the same place.
- **Three of the four places come out of one script.** The pit village street builder
  (`build_street.py`: a street running up to a landmark, with kerbs, gutters, terraces, sash windows,
  doors, gutters and downpipes, gas lamps) is copied for the Glasgow street (tenements, a works at the end)
  and the New Zealand street (Edwardian shops with verandahs, the Reserve Bank at the end). The valley comes
  from chapter 2's own factory and town scripts.

Pages turn as in the cinema look (the page peels 0.3 seconds after the last word); within a page, shots
change by plain cuts.

---

## 1. THE PLACES

Every sign and label below carries real lettering, era-correct, as its own surface. In-world lettering
carries names, or a short form of what Malina says; it never carries a figure (no prices, years, door
numbers, sizes or rates) except figures Malina says. Every invented name is searched before building,
and changed if a real business of that name exists in that place. No logos, no flags, no party colours:
no prominent prop is mainly red, mainly blue, mainly green or yellow-and-black.

### 1.1 The New Zealand street (N)

- **What it is:** an invented side street in Wellington, present day, climbing gently toward a hillside
  of weatherboard houses. Left side: two-storey Edwardian shops with cast-iron verandahs over the
  footpath, the foodmarket nearest. Right side: the petrol station on the corner, then a gap site with the
  building site, then a villa with a "FOR RENT" board. At the top of the street: the Reserve Bank, an
  invented plain grey 1970s office tower (not a copy of the real building), with a stone forecourt wall.
  The foodmarket's inside is built too, because N1 stands in it.
- **Era and place:** New Zealand, 2020 to 2026, winter dusk (the basket's months are June). The year is
  told by the typed title, and by one own-surface sign on page 10 only.
- **Main view: N2, the street up to the Reserve Bank.** A person stands on the left footpath under the
  foodmarket's verandah, eye height (1.65 m), level. The kerbs, the verandah fronts and the power lines meet
  at the Reserve Bank's lit entrance at the top of the street (about 100 m). Two upright columns (rule 7):
  the tower (its top in the top third) above its lit entrance; the hillside houses with a few lit windows
  above the left-hand shops. The tower's upper floors are mostly dark after hours, so the lit entrance is
  the brightest thing; the foodmarket window at the left edge and the petrol canopy are kept dimmer.
  Near props stay small and quiet: a bench, a bin, the café's A-frame sign.
- **Other views:**
  - **N1, the checkout.** A person stands in the queue at the end of the checkout lane, eye height, level,
    looking along the belt toward the front window. The belt's edges, the counter edge, the ceiling light
    rows and the shelf edges meet at the basket at the lane's far end. Story props, one touching group: the
    basket of shopping on the belt; the newspaper rack at the counter's end, touching the basket, its top
    paper's headline facing us; a reusable shopping bag over the basket's rim; car keys beside the card
    terminal. A column: the lane's lamp, then the headline, then the basket. The rest of the shop is half
    lit (closing time), so the basket under the lane lamp is the brightest thing. Through the window, the
    street at dusk. The shelf-edge tags on the shelf behind the basket are own-surface and can flip.
  - **N3, the building site.** A person stands on the opposite footpath, eye height. The scaffold planks
    and the site fence lead to the timber frame's front corner. Story props, touching: the site hut with a
    lit window and hard hats and hi-vis vests on hooks (the workers' things: no workers), a stack of
    framing timber, a concrete mixer; the tower crane rising into the top third over them. The villa next
    door with its "FOR RENT" board at the frame's side. Warm light: the hut's window and a work lamp.
  - **N4, the forecourt.** A person stands by the kiosk wall, eye height. The canopy edge and the pump
    island's kerbs meet at the near pump. Story props, touching: the pump with its PETROL and DIESEL
    nozzles, the motor oil rack, a jerry can on the island. Warm light from the kiosk window; the crane on
    the skyline behind.
- **What can be reused** (files):
  - `film-kit/paper-film/blender/pit-village/build_street.py`: the street skeleton (sloping road, kerbs,
    gutters, footpaths, ground and sky), the mesh builder, `build_sash_window` and `build_front_door` (the
    shops' upper floors are Edwardian, with sash windows), gutters and downpipes, `place_cottage_row` for
    placing shop rows, the headframe's lattice code for the tower crane.
  - `set_dressing.py` (`place_prop`, `light_reaches`, `see_through`, `render`, `export_for_film`),
    `assemble_notice_corner.py` as the pattern for each view's assembly script, `shot_facts.py` and
    `check-shot.sh` for every view.
  - Props library: none of the 1926 props fits a 2026 street; only the library's building tools are reused.
  - Textures already here: `blue_painted_planks` (a villa's weatherboards), `grey_plaster_02`.
- **What must be built new by script** (with lettering):
  - The street: asphalt road with painted markings ("BUS STOP" on the road, a "KEEP CLEAR" box at the
    side road), concrete footpaths and kerbs, power poles with cables, two cabbage trees (tī kōuka:
    trunk and tufts of strap leaves) in planters.
  - The shop row: four Edwardian two-storey fronts with cast-iron verandah posts and corrugated roofs;
    fascia lettering "HILLSIDE FOODMARKET" (the foodmarket; name to be checked), "BAKERY", "PHARMACY",
    "FISH & CHIPS", "CAFÉ"; the café's A-frame sign "FLAT WHITE / OPEN"; the foodmarket door "OPEN" and
    "PUSH"; a street name blade with an invented street name (checked); a "BUS STOP" sign.
  - The Reserve Bank: a grey precast-panel tower about 18 floors high, a few lit floors, a lit glass
    entrance; a stone forecourt wall carrying "RESERVE BANK OF NEW ZEALAND" in plain carved capitals (no
    logo). The typed card names it on screen; the carving is too small to rely on.
  - Hillside villas: three weatherboard villa variants with corrugated roofs and lit sash windows, placed
    up the hill (they stand for "many people with loans" on page 13).
  - The foodmarket inside: vinyl floor, ceiling with fluorescent fittings, three gondola shelf runs with
    product boxes lettered RICE, FLOUR, SUGAR, TEA, CEREAL, OATS (no sizes, no prices, no brands); shelf-edge
    tag strips that show the product name on one face and an up-arrow (▲) on the other, so they can flip;
    the checkout counter with conveyor belt, scanner, a divider bar "NEXT CUSTOMER", a till screen
    "WELCOME", a lane lamp "CHECKOUT" (no number), a card terminal whose screen says "TAP CARD" (keypad
    turned away from the camera); a plastic shopping basket with "HILLSIDE FOODMARKET" moulded on the
    handle; groceries: a milk bottle "MILK", a bread bag "BREAD", "BUTTER", an egg carton "FREE RANGE
    EGGS", a tin "BAKED BEANS", a pasta packet "PASTA" (no sizes or weights printed); a reusable bag with
    the shop's name; car keys; the newspaper rack with folded papers, the top one with an invented
    masthead (proposed "THE HILLSIDE HERALD", checked against real New Zealand papers) and the headline
    **NEW MONEY 'WILL PUSH PRICES UP'** (a short form of "If new money is created... prices will go up").
  - The petrol station: canopy with lit underside and a fascia lettered "PETROL · DIESEL" (no brand; never
    "FUEL"), two pump islands, pumps lettered "PETROL", "PREMIUM PETROL", "DIESEL", "PAY INSIDE" (grade
    numbers left off); the price sign stands edge-on to every camera, so no prices show; a motor oil rack
    with bottles lettered "MOTOR OIL"; an air pump "AIR"; the kiosk with a lit window.
  - The building site: a two-storey townhouse block in pine framing (studs, plates, nogs), modern tube
    scaffolding with planks and toe boards, a tower crane (lattice mast and jib, faded white, a red warning
    light on top), a concrete mixer, a framing-timber stack with steel strapping and a tag "FRAMING TIMBER",
    a pallet of concrete blocks, a skip, the site hut with hooks of hard hats and hi-vis vests, site boards
    "TŌTARA BUILDERS" (invented, checked), "HARD HATS MUST BE WORN", "NO UNAUTHORISED ENTRY", "SITE OFFICE"
    on the hut door; the villa's board "FOR RENT" (own surface, appears on "rents", page 11).
  - Page 10's own-surface sign on the foodmarket door: "PLEASE SANITISE YOUR HANDS" (2020; shown on page 10 only).
- **Poly Haven to fetch** (CC0; names checked in Poly Haven's list on 15 October 2026):
  - Surfaces: `clean_asphalt` (road), `concrete_pavement` (footpaths), `painted_plaster_wall` and
    `plastered_wall` (shop fronts), `worn_corrugated_iron` and `corrugated_iron` (verandahs, villa roofs),
    `weathered_plank_siding` (villas), `concrete_tile_facade` and `rectangular_facade_tiles` (the tower),
    `granite_tile` (the forecourt), `floor_tiles_06` (the shop floor), `ceiling_interior`,
    `box_profile_metal_sheet` (canopy fascia, site hut), `coated_pine` (framing timber), `plywood`,
    `oriented_strand_board`, `raked_dirt` and `excavated_soil_wall` (the site), `gravel`.
  - Models: `mounted_fluorescent_lights`, `food_kiwi_01`, `food_apple_01`, `bananas`, `food_avocado_01`,
    `lemon`, `plastic_crate_01`, `plastic_crate_02`, `hand_truck`, `WetFloorSign_01` (check its printed
    words), `metal_trash_can`, `modular_street_seating`, `street_lamp_01`, `modular_electricity_poles`,
    `modular_electric_cables`, `utility_box_01`, `shrub_01` to `shrub_04`, `potted_plant_01`,
    `tree_small_02`, `modular_chainlink_fence`, `cement_bag` (check its printed label; replace any brand
    with "CEMENT"), `ladder_sectioned_01`, `portable_generator`, `security_light`, `sledgehammer_01`,
    `trashbag`, `metal_jerrycan`, `exterior_aircon_unit`.
- **Light:** winter dusk, the sky kept dim (rule 5). The people's own lights: the
  checkout lane lamp (warm) on the basket; the shop windows; the hut window and work lamp at the site; the
  kiosk window at the forecourt; the Reserve Bank's lit entrance (warm) at the top of the street. Cool
  light: the petrol canopy and the shop's fluorescent tubes, kept dimmer than each view's subject.
- **Plates and paintings:** 4 plates (N1 and N2 from the start of their slides, N3 and N4 from their
  held spots), **7 paintings**: N1 main and behind; N2 main and behind, plus N2 with the bakery's lights out
  (a state painting made from N2's painting, page 12 "less to spend"); N3; N4.

### 1.2 The valley (V)

- **What it is:** the "two factories" picture made into one place: a valley floor with a cobbled factory
  road; two brick works standing side by side behind it, their fronts facing us, their gates near the
  middle where a lane from the camera meets the factory road. **The quiet factory always on the left, the
  flat-out factory always on the right.** Behind them, the valley's terraced houses climbing the sides, a
  gasholder, a church spire and an arched railway viaduct across the back (chapter 2's town, made to real
  size).
- **Era and place:** imagined. Brick works and gas lamps of the early twentieth century, as a storybook
  picture with no date and no country on any sign. The script calls it "our picture".
- **Each factory's fixed identity** (never changes, in any view):
  - **The quiet factory:** red-brown brick, one tall round chimney, a four-bay sawtooth roof, green-painted
    iron gates, its name board **THE QUIET FACTORY** on the gate pier.
  - **The flat-out factory:** buff (yellow-grey) brick, two square chimneys, a water tank on a steel
    trestle, red-brown painted gates, its name board **THE FLAT-OUT FACTORY** on the gate pier.
  - The two gate areas are built the same way (pier, name board, gas lamp on a bracket, a bench against the
    pier, a wages hatch in the pier wall), so the two gate views are a matched pair: a cut from one to the
    other reads as "same kind of place, different state".
- **Main view: V1, the valley wide.** A person stands on the footpath of the lane, about 55 m from the
  factory road, eye height, level. The lane's kerbs and setts meet at the seam between the two gates. Two
  upright columns (rule 7, like the notice corner's pit column and notice column): the quiet factory on the
  left (cold chimney in the top third, dark sawtooth roofs, the shut gate with workers waiting), the
  flat-out factory on the right (two chimneys smoking, lit windows, the open gate's warm glow). The
  brightest parts are the flat-out factory's open gate and the quiet factory's gate lamp, both beside the
  seam. The far town fills the quiet sides.
- **Other views (matched):**
  - **V2, the quiet factory's gate.** A person stands across the factory road on the far footpath, about
    13 m from the gate, eye height, level. The kerb, the factory's wall base and the fence meet at the gate
    pier, beside the name board. Story props, one touching group: the pier with its name board and gas lamp;
    the bench against the pier with lunch tins and a lit hurricane lantern (the workers' own light, rule 6);
    seven figure shapes waiting in a loose queue in front of the shut, chained gates, the nearest one
    overlapping the pier's base. Column: chimney top, name board and lamp, bench and queue. A slice of the
    flat-out factory's buff wall at the right edge.
  - **V3, the flat-out factory's gate**, framed the same way from the same distance. Story props: the pier
    with its name board, gas lamp and lit wages hatch ("WAGES"); stacked crates of goods by the pier; the
    open gate showing the lit yard and a workshop door with sparks. A slice of the quiet factory's red
    wall at the left edge.
- **States** (each a separate plate from the same set; state changes happen only while the camera holds):
  - Quiet factory: **QUIET** (gates shut and chained, windows dark, chimney cold, seven figures waiting,
    lantern on the bench) and **WORKING** (gates open, chain hanging, no figures, windows lit, crates of goods
    at the loading door, chimney smoking: page 3 only).
  - Flat-out factory: **FLAT OUT** (gates open, every window lit, two chimneys smoking, no one at the gate)
    and **SLOWED** (half the windows dark, gates shut, thin smoke, workers waiting) in two counts: five
    figures (pages 12 to 14) and ten (page 14, "more workers waiting").
  - V1 always shows the quiet factory QUIET and the flat-out factory FLAT OUT: the two halves of the rule.
- **What can be reused** (files):
  - `film-kit/paper-film/blender/build_factory.py` (both works: brick, sawtooth roofs with north lights,
    chimney, office, water tank, machines in silhouette inside the door; options `--brick` and
    `--office`), `build_town.py` (terraces, other works, gasholder, spire, viaduct with a goods train),
    `build_props.py` (barrels, crates, lamp post, cart), `model_kit.py`. These were built at about a tenth of
    real size (a works 3.2 units wide); they get a size setting that scales positions and re-tiles every
    texture at real size (scaling the old .glb files would give giant bricks). The old files in
    `assets/models/inflation-chapter-2/` stay as they are.
  - Props library (`assets/models/pit-village/props/`): `iron-gates-pair.glb` (both gates),
    `gas-lamp-wall-bracket.glb`, `gas-lamp-post.glb`, `settle-bench.glb`, `hurricane-lantern.glb`,
    `wooden-barrel.glb`, `handcart.glb`, `dustbins.glb`, `wooden-pail.glb`.
  - Pit village surfaces: `red_brick`, `castle_brick_02_red`, `square_cobblestone`, `large_grey_tiles`,
    `roof_slates_03`, `rusty_metal_02`, `dusk_sky`, the lit and dark window pictures.
- **What must be built new by script** (with lettering):
  - The gate areas: brick piers with stone caps; name boards in sign-writer lettering (the library's OFL
    fonts Ultra and Alfa Slab One): **THE QUIET FACTORY**, **THE FLAT-OUT FACTORY**; a wages hatch with a
    small board **WAGES** in each pier; a gate chain with padlock (quiet factory).
  - Workers' things: lunch tins, a tea can, caps on the bench (no lettering).
  - Goods crates stencilled **THIS WAY UP** (era-plausible, no figures).
  - **Figure shapes**, about 14 in five poses: standing with hands in pockets, arms folded, leaning on the
    fence, sitting on the kerb, one hand on the gate. Caps, long coats or jackets and trousers, boots; slight
    differences of height and build; no faces modelled (they face the gates).
  - Optional: a cast-iron fingerpost at the lane's mouth, arms lettered **THE QUIET FACTORY** and
    **THE FLAT-OUT FACTORY**, if V1 needs a near story prop.
- **Poly Haven to fetch:** models `wooden_crate_01`, `wooden_crate_02` (goods crates, our stencils added),
  `wooden_bucket_01`; surfaces `white_sandstone_bricks` (tinted buff, the flat-out factory's brick),
  `large_red_bricks` (the quiet factory's piers).
- **Light:** dusk, sky dim. The people's own lights: the gas lamps on the piers, the lantern on the quiet
  factory's bench (warm on the waiting figures' backs), the flat-out factory's lit windows and yard (warm,
  through the open gate). The quiet factory's windows dark.
- **Plates and paintings:** 5 plates (V1 from its slide start; V2 QUIET from its slide start, V2 WORKING
  from its held spot; V3 FLAT OUT from its slide start, V3 SLOWED with ten figures from its held spot, where its page 14 slide starts),
  **10 paintings**: V1 main and behind; V2 QUIET main and behind, V2 WORKING; V3 FLAT OUT main and behind;
  V3 SLOWED (ten) main and behind; V3 SLOWED (five), made from the ten-figure painting with five figures
  painted out.

### 1.3 The Glasgow street (G)

- **What it is:** a level street of four-storey red sandstone tenements in Glasgow, with shops on the
  ground floor and close entrances (the arched passages into each tenement), granite setts with tram rails
  and tram poles with overhead wire, gas lamps; at the end of the street, about 120 m away, the high wall and
  arched gate of a munitions works, lit and smoking. At the end of the right-hand row, a half-built tenement
  standing abandoned in its timber-pole scaffolding.
- **Era and place:** Glasgow, 1915, November dusk.
- **Main view: G1, the street to the works.** Built like the notice corner. A person stands on the
  right-hand pavement, eye height, level, about an arm's length in from the kerb. The setts, the tram rails,
  the kerbs and the tenement cornices meet at the works' arched gate. Right beside that spot, near the
  camera: a recruiting poster pasted on the end wall of a close (the near subject, its left edge at the
  spot where the lines meet, like the notice board's), a gas lamp above it, the bill-poster's paste pail
  and brush on the pavement below (the empty prop for the person who pasted it). Up the street, a crowd of
  about 18 figure shapes walk toward the works, seen from behind: men in caps and jackets, women in long
  skirts and shawls, some carrying bundles (war workers arriving). Column: the works' chimney and smoke,
  the lamp, the poster, the pail. The left-hand row is the quiet side: dim sandstone, lit windows, a shop.
- **Other view: G2, the tenement row.** A person stands on the opposite pavement, eye height, looking up
  the street along the right-hand row at an angle. The cornices, the rows of windows and the kerb meet at
  the half-built tenement at the row's end. Story props, touching: a close entrance with tiled walls inside;
  the landlord's notice pasted at the close mouth; a gas lamp; a kitchen chair at the close mouth with
  knitting on it (someone sat here watching the street). Every window lit and crowded with curtains. The
  rent strike placards are own-surface signs, added in the windows on the word "refusing".
- **What can be reused** (files): `build_street.py` again (street, setts, kerbs, flagstones, gutters,
  `build_sash_window`, `build_front_door`, chimney stacks, slate roofs, cast-iron gutters and downpipes,
  `place_gas_lamps`); the cottage shell code, raised to four storeys with ashlar fronts; `build_factory.py`
  for the works' sheds behind its wall (sooty red brick, one round chimney, big shed roofs: kept unlike the
  flat-out factory); the notice paper builder in `props/build_scripted_props.py` (the landlord's notice and
  the recruiting poster are paper on a wall, like the lock-out notice); props `gas-lamp-post.glb`,
  `wooden-pail.glb`, `kitchen-chair.glb`, `dustbins.glb`, `milk-can.glb`, `handcart.glb`; surfaces
  `square_cobblestone`, `large_grey_tiles`, `roof_slates_03`, `stone_brick_wall_001`, `red_brick`,
  `large_sandstone_blocks`, the window pictures.
- **What must be built new by script** (with lettering):
  - The tenement block (four storeys, ashlar, bay of sash windows, close entrances with glazed tile
    walls inside, chimney stacks along the ridge), in two variants.
  - Shopfronts with sign-written fascias: "J. M'LEAN · GROCER & PROVISION MERCHANT", "DAIRY",
    "PAWNBROKER" (with the three brass balls), "R. KERR · BOOTMAKER" (all invented, checked). A street
    name plate with an invented name (checked). No numbers over the closes.
  - Tram rails set in the setts; tram poles with overhead wire (no tram car).
  - The works: a high brick wall with an arched gate, lettered "STRATHVALE ENGINEERING COMPANY LIMITED"
    (invented, checked) and "WORKS ENTRANCE".
  - The recruiting poster, text only, no portrait, no flag: "YOUR KING AND COUNTRY NEED YOU / ENLIST TO-DAY /
    GOD SAVE THE KING" (the wording of 1914 text-only posters; the history helper confirms it from a
    source before it is built).
  - The landlord's notice, no figures: "NOTICE TO TENANTS / Your rent will be increased from the next term. /
    By order of the Landlord." (history helper checks the wording).
  - Twelve rent strike placards, hand-painted capitals (an OFL font with a scripted wobble): "RENT STRIKE"
    and "WE ARE NOT PAYING INCREASED RENT" if a 1915 photograph confirms that wording; otherwise "NOT
    PAYING THE INCREASE" (a short form of "refusing to pay the extra"). Never WON, never RENTS FROZEN.
  - The half-built tenement: walls to the second floor, timber scaffold poles lashed with putlogs, a few
    planks missing, weeds; a builder's board "D. ROSS & SON · BUILDERS" (invented, checked).
  - Crowd figure shapes: walking poses added to the valley's figure set (caps and jackets; long skirts and
    shawls; bundles and bags).
- **Poly Haven to fetch:** surfaces `red_sandstone_wall` (the tenement fronts), `long_white_tiles` or
  `square_tiles_02` (the close tiles). Nothing else; the 1926 kit covers the rest.
- **Light:** November dusk; gas lamps and lit windows (warm); the works' gate and furnace glow at the end
  (warm), its chimney smoking. The poster lit from below by the lamp's spill and the shop window beside
  it (rule 6).
- **Plates and paintings:** 2 plates (G1 and G2, each from the start of its slide), **4 paintings**:
  G1 main and behind; G2 main and behind.

### 1.4 The Tokyo back office (T)

- **What it is:** the back room of an ordinary Tokyo bank branch at night: steel shelving, the strong
  room door standing open, a cash trolley, a desk with a lamp, a window with blinds half open onto a
  Tokyo street at night. No bank is named. This is where the new money arrives and sits; the typed cards
  say who planned it, and nothing claims this room is Japan's central bank.
- **Era and place:** Tokyo, 2013, night.
- **Main view: T1.** A person stands just inside the room's door, eye height, level. The shelving rows,
  the ceiling tiles and the floor tiles meet at the open strong room door. Story props, touching: the cash
  trolley stacked with paper-wrapped bundles, against the shelving bay at the strong room door; the desk
  beside it with the lamp lighting both (the people's own light); a note-counting machine on the desk; the
  desk chair pushed back with a jacket over it (the clerk has just stepped away). The window on the left
  is the quiet side: lit shop signs of the street outside. The ceiling's fluorescent lights are half off.
- **States:** **HALF** (shelves half full; page 8) and **FULL** (shelves full, bundles stacked on the
  trolley and the floor; page 9).
- **What can be reused** (files): `set_dressing.py`, the assembly pattern, the checker; the scripted
  props kit for paper bands and lettering.
- **What must be built new by script** (with lettering; Japanese set in Noto Sans JP and Noto Serif JP,
  OFL, fetched from Google Fonts, and read by a helper who reads Japanese before anything is drawn):
  - Room shell with a window, venetian blinds, ceiling tiles, a wall notice "整理整頓" (keep things tidy).
  - The strong room door: round steel door with bolts, its plate lettered "金庫室" (strong room).
  - Cash bundles: paper-wrapped bricks of banknotes, the paper bands lettered "日本銀行券" (Bank of Japan
    notes); no note's face visible anywhere (a banknote carries a real person's portrait).
  - Cash cases lettered "現金" (cash); the cash trolley; the note-counting machine; a flat screen and
    keyboard (the screen showing a plain blue log-in panel lettered "ログイン", no figures).
  - The street outside, built simply (lit fronts and vertical signs): "ラーメン" (ramen), "居酒屋"
    (pub), "薬局" (pharmacy), "クリーニング" (dry cleaning); no brand names, no prices.
- **Poly Haven to fetch:** models `steel_frame_shelves_01`, `steel_frame_shelves_02`,
  `metal_office_desk`, `desk_lamp_arm_01`, `mounted_fluorescent_lights` (also used in N1),
  `cardboard_box_01`; surfaces `floor_tiles_02`, `ceiling_interior`, `metal_plate`, `painted_plaster_wall`.
- **Light:** night. The desk lamp (warm) on the trolley and shelves; half the fluorescent tubes on (cool,
  dim); the street's signs through the blinds (coloured, dim).
- **Plates and paintings:** 2 plates (HALF from the start of the slide, FULL from the held spot),
  **3 paintings**: HALF main and behind, FULL.

### 1.5 People: how "workers wait at the gate" and crowds are shown

**The choice: simple figure shapes that the painter turns into painted people, always seen from behind
at dusk, never closer than about 10 m, and only where counting people is the point.**

| Where | How | Why |
|---|---|---|
| V2 quiet factory's gate (pages 3, 9), V1 (small, at the quiet factory's gate) | 7 figure shapes queuing at the shut gates, backs to us | "Workers wait at the gate" is the picture's core: spare workers have to be seen and counted. An empty bench can't show waiting, and can't show "more" |
| V3 flat-out factory's gate, SLOWED (pages 12, 13, 14) | 5, then 10 figure shapes | "More workers wait at the gate": the count must grow |
| G1 Glasgow street (pages 6, 7) | about 18 walking figure shapes, backs to us, going toward the works | "Crowds of war workers had come to Glasgow" |
| G2 tenement row (page 7) | no people: the rent strike placards in the windows, one per family | The placards count the families; a chair with knitting at the close mouth shows someone lives here |
| N1, N2, N3, N4 (New Zealand) | no people: the basket, hard hats on hooks, lit windows on the hillside | Present-day painted people risk looking like real, recognisable people; the props carry them |
| T1 Tokyo | no people: the chair pushed back with a jacket over it | Night; the money sitting is the subject |

Seen from behind, the figures have no faces to garble and no likeness of anyone; facing the gate is
exactly what waiting looks like. At dusk they read as shapes first, so small differences between
paintings matter less. The empty prop made for a person (rule 9) still works beside them: the lit lantern
and lunch tins on the bench say they have been here a while.

**What could go wrong, and how it is caught:**
- The painter adds faces, turns figures round, adds or removes people, or changes the count between two
  paintings. Painter words: "keep every figure exactly where and as it is, seen from behind; add no people,
  no faces, no details". Caught by: a helper counts the figures in every painting against the plate; the
  shot checker lists each figure as a prop, so `align_painting.py` and the out-of-date test show a figure
  that moved.
- They look like shop dummies or ghosts. Caught in the first paid test (the flat-out factory's gate,
  SLOWED), on a phone, before any other place is painted.
- The Glasgow crowd reads as soldiers marching. No rifles, no step in time, mixed men and women with
  bundles; the history helper checks.
- A dissolve makes people fade in like ghosts (page 12). Kept to a 2-second dissolve while the lights go
  down, read as time passing; checked in motion. Fallback: a hard cut to SLOWED.
- **Fallbacks, in order:** ask again with stronger painter words (10 cents); keep the figures as their own
  surfaces (dark shapes with a rim of lamplight, not painted); last, no figures: a row of empty folding
  stools, caps on hooks and lunch tins at the gate, with "more workers" shown by more stools.

---

## 2. THE SHOTS, page by page

How to read each shot:
- **Camera**: the view's spot (a person's spot, eye height, level, never turning; section 1 gives each).
- **Move**: one slide, one lens push, or none. Slides last 3 to 6 seconds, start and stop gently, and stop
  on the view's composed frame. At most 3 moves a page; never a turn or a pan.
- **Events**: each starts on the quoted spoken word. A word spoken more than once on the page is asked for by
  its count ("spent", 2). Cards are typed in the kit's plain heavy type (`hook`, `placeTitle`, `credit`,
  `counter`, `bars`, `lineChart` in `graphics.js`), in the dim sky or upper part of the frame, left of 0.90 across.
- **Effects** and their added time a frame, from the research's measurements on this machine ("26 Research -
  fully 3D scenes and cheap effects"): chimney smoke about 0.1 s per chimney (12 puffs; 40 puffs measured
  0.41 s); lamp and lantern flicker, sparks, dust motes, a blinking light: about 0. The base frame (the
  projected set with its behind painting and sky card, the cards and grabbing the frame) is about 0.55 s
  with the stage's depth blur, glow pass and shadow maps all off (see section 3).
- Card words are short forms of what Malina says on that page; the only figures are ones she says; small
  credits (STATS NZ, US FEDERAL RESERVE, THE CAPITAL ORDER) carry no figures.

### Page 1 - The question (about 29 s)

**Shot 1.1 - N1, the checkout.** Subject: the basket of shopping. Story props: basket, newspaper rack,
reusable bag, keys, card terminal.
- Move 1, slide 1.0 m toward the basket: from "felt" to about "ago".
- Move 2, lens push 1.25 times, centred on the basket and headline (both in the middle band): from
  "warning" over 2 s.
- Events:
  - "inflation": INFLATION; "general": = PRICES IN GENERAL, GOING UP.
  - "whole": every shelf-edge tag flips to an up-arrow, one after another over 1 s (own surfaces); THE WHOLE BASKET.
  - "warning": the push brings the in-world headline NEW MONEY 'WILL PUSH PRICES UP' up big (no card needed).
  - "always": IS THAT ALWAYS TRUE?
  - "cure": THE USUAL CURE →; "loans": MANY LOANS COST MORE →; "work": OUT OF WORK.
- Effects: one far fluorescent tube flickers (about 0); soft contact shadows under the basket and rack
  fade in as the slide starts. About 0.55 s a frame.

### Page 2 - Who can create new money (about 21 s)

**Shot 2.1 - N2, the street up to the Reserve Bank.** Subject: the Reserve Bank's lit entrance.
- Move 1, slide 1.2 m up the footpath: from "Who" to "can" (2).
- Events: "Zealand": title NEW ZEALAND; "Bank": THE RESERVE BANK (a callout to the forecourt wall);
  "can" (2): CAN CREATE NEW MONEY; "stop": TRIES TO STOP PRICES GOING UP TOO FAST.
- Effects: the tower's warning light blinks (about 0). About 0.55 s.

**Shot 2.2 - N3, the building site** (cut on "There"). Subject: the site's workers' things, materials and
machines in one group. Hold.
- Events: "economists": ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS; "argue": ARGUE:; "money" (3):
  OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY; "But": BUT IT CAN RUN OUT OF...; "workers": WORKERS (callout
  to the hard hats on their hooks); "materials": MATERIALS (to the timber stack); "machines": MACHINES (to
  the mixer and the crane).
- Effects: the crane's red light blinks (about 0). About 0.55 s.

### Page 3 - The quiet factory (about 27 s)

**Shot 3.1 - V1, the valley wide.** Subject: the two gates, side by side.
- Move 1, slide 2 m along the lane toward the gates: from "Picture" to "machines" (1).
- Events: "Picture": PICTURE TWO FACTORIES; "country": EACH ONE = A WHOLE COUNTRY; "machines" (1):
  WORKERS, MATERIALS, MACHINES; small name tags appear over each column as the factories are named later
  (from page 5 on they come with every return to V1).
- Effects: the flat-out factory's two chimneys smoke (0.2); its windows' glow flickers faintly (about 0).
  About 0.75 s.

**Shot 3.2 - V2, the quiet factory's gate** (cut on "In" (1)). QUIET, then WORKING.
- Move 2, slide 1.0 m toward the gate: from "still" to "job".
- Events:
  - "Workers" (2): WORKERS WAIT AT THE GATE; "quiet": THE QUIET FACTORY (big).
  - "spends": THE GOVERNMENT SPENDS NEW MONEY; "makes": ON WHAT IT MAKES.
  - "go" ("The workers go in"): dissolve from QUIET to WORKING over 1.2 s (the camera has stopped).
  - "start": the chimney's smoke begins, the windows' glow flickers.
  - "buy": MORE MONEY / MORE THINGS TO BUY (the same layout page 5 uses for SAME and page 6 for FEWER).
  - "barely": PRICES BARELY MOVE, with a level arrow over the works.
- Effects: the lantern on the bench flickers (QUIET); one chimney's smoke after "start" (0.1).
  About 0.65 s.

### Page 4 - The flat-out factory, the first guess (about 18 s, then a 4 s hold)

**Shot 4.1 - V3, the flat-out factory's gate.** FLAT OUT.
- Move 1, slide 1.0 m toward the gate, matching V2's slide: from "second" to "can".
- Events: "busy": EVERY WORKER, EVERY MACHINE BUSY; "can": WORKING AS HARD AS THEY CAN; "No": NO ONE WAITS AT
  THE GATE; "flat-out": THE FLAT-OUT FACTORY (big), with FLAT OUT = WORKING AS HARD AS THEY CAN small under it;
  "same": THE SAME NEW MONEY IS SPENT; "prices": WHAT HAPPENS TO PRICES?; "guess": HAVE A GUESS with a small
  ring that fills over 4 s.
- **The 4-second guess hold** goes here, on the composed frame, smoke still rising.
- Effects: two chimneys' smoke (0.2), sparks at the workshop door and window glow flicker (about 0).
  About 0.75 s.

### Page 5 - The rule (about 25 s, then a 2 s hold)

**Shot 5.1 - V3, FLAT OUT** (held on the composed frame).
- Events: "spare" (1): NO SPARE WORKERS, MATERIALS OR MACHINES; "extra": NO EXTRA THINGS MADE; "same":
  MORE MONEY / SAME THINGS TO BUY; "ask": BUSINESSES CAN ASK MORE; "up" (1): a price arrow over the works
  climbs; "agree": MOST ECONOMISTS AGREE (small).
- Effects as 4.1. About 0.75 s.

**Shot 5.2 - V1, the valley wide** (cut on "When" (1); held). The two small name tags QUIET and FLAT OUT
over their columns.
- Events, the two rule cards built word by word: "spent" (1): NEW MONEY SPENT; "spare" (2): + SPARE;
  "made" (2): → MOSTLY MORE THINGS MADE (over the quiet factory's column); "nothing": NOTHING SPARE; "up" (2):
  → MOSTLY PRICES UP (over the flat-out factory's column).
- **The 2-second rule hold** goes here, after "up", music up, before the page turn.
- Effects: the flat-out factory's smoke (0.2). About 0.75 s.

### Page 6 - Britain at war (about 27 s)

**Shot 6.1 - G1, the Glasgow street to the works.** Subject: the recruiting poster beside the spot where
the lines meet, with the works' gate glowing just past it.
- Move 1, slide 1.5 m up the pavement toward the poster: from "real" to "fight".
- Events: "real": A REAL CASE; "War" (1): title BRITAIN, FIRST WORLD WAR; "fight": MILLIONS WENT TO FIGHT;
  "hundred": the 100-dot panel, the last dot nearly empty: FEWER THAN 1 IN 100 OUT OF WORK; "submarines":
  SHIPS SUNK; "materials": FOOD, MATERIALS; "partly": PARTLY NEW MONEY; "fewer" (2): MORE MONEY / FEWER
  THINGS TO BUY; "doubled": two bars, BEFORE THE WAR and END OF THE WAR: ROUGHLY ×2.
- Effects: the works' chimney smoke (0.1), gas lamp flicker (about 0). About 0.65 s.

**Shot 6.2 - V3, FLAT OUT** (cut on "Britain" (2); held; the page 4 painting reused).
- Events: "flat-out": CLOSE TO THE FLAT-OUT FACTORY.
- Effects as 4.1. About 0.75 s.

### Page 7 - Glasgow's homes (about 34 s)

**Shot 7.1 - G1** (held on the composed frame; the walking crowd is in the painting).
- Events: "Glasgow" (1): title GLASGOW 1915; "crowds": CROWDS OF WAR WORKERS.
- Effects as 6.1. About 0.65 s.

**Shot 7.2 - G2, the tenement row** (cut on "There"). Subject: the close mouth with the landlord's notice.
- Move 1, slide 1.2 m toward the close: from "Landlords" to "quarter".
- Events: "few" (1): TOO FEW HOMES ALREADY; "builders": BUILDERS AND MATERIALS GONE TO THE WAR (callout to the
  half-built tenement); "built": FEW NEW HOMES; "thing": ONE KIND OF THING (small); "flat-out": FOR HOMES:
  LIKE THE FLAT-OUT FACTORY; "rent" (1): RENT RAISED; "quarter": UP TO A QUARTER MORE, IN PLACES;
  "refusing": the placards appear in the windows one by one over 3 s (own surfaces), with the counter
  ABOUT 20,000 FAMILIES REFUSING THE EXTRA landing on "extra"; "Parliament": the stamp RENTS ON SMALL HOMES
  BACK TO BEFORE THE WAR, landing on "war" (3).
- Never WON, RENTS FROZEN or NOT ENOUGH HOMES; no Mary Barbour card.
- Effects: gas lamp flicker, a lit window's flicker (about 0). About 0.55 s.

### Page 8 - Japan, the second guess (about 14 s, then a 4 s hold)

**Shot 8.1 - T1, the Tokyo back office.** HALF. Subject: the cash trolley at the strong room door.
- Move 1, slide 0.8 m toward the trolley: from "Japan" (1) to "thirteen".
- Events: "thirteen": title JAPAN 2013; "version": JAPAN'S VERSION OF OUR RESERVE BANK (small); "double":
  PLANNED: ×2 MONEY; "years": IN TWO YEARS; "warning": a dashed line IF THE WARNING IS RIGHT climbs (upper
  part of the frame); "happened": WHAT HAPPENED?; "guess": HAVE A GUESS with the 4-second ring.
- **The 4-second guess hold** goes here.
- Effects: dust motes in the desk lamp's beam, a faint beam (0.02), a street sign blinking through the
  blinds (about 0). About 0.6 s.

### Page 9 - Japan, the answer (about 27 s, then a 2 s hold)

**Shot 9.1 - T1** (held on the composed frame). HALF, then FULL.
- Events: "barely": the real line draws almost level beside the dashed one: PRICES BARELY MOVED; "eight":
  FOR ABOUT 8 YEARS; "half": ABOUT ½% A YEAR, ON AVERAGE; "reason": ONE REASON ECONOMISTS GIVE (small);
  "sat": dissolve from HALF to FULL over 1.5 s (shelves fill, bundles pile on the trolley and floor), with
  MOST SAT IN THE BANKS.
- Effects as 8.1. About 0.6 s.

**Shot 9.2 - V2, QUIET** (cut on "In" (2), "In our picture"; held; the page 3 painting reused).
- Events: "factory": IN OUR PICTURE: MOST OF IT NEVER REACHED THE FACTORY.
- Effects: the lantern's flicker (about 0). About 0.55 s.

**Shot 9.3 - V1** (cut on "So"; held; name tags on).
- Events: "much": NOT JUST HOW MUCH; "what" (1): WHETHER IT'S SPENT, AND ON WHAT; "buys": SPARE WORKERS,
  MATERIALS, MACHINES TO MAKE WHAT IT BUYS?
- **The 2-second hold** on that card goes here, before the page turn.
- Effects: the flat-out factory's smoke (0.2). About 0.75 s.

### Page 10 - New Zealand, the third guess (about 21 s, then a 4 s hold)

**Shot 10.1 - N2** (held on the composed frame). The door sign PLEASE SANITISE YOUR HANDS is on the
foodmarket door for this page only.
- Events: "twenty" (1): title NEW ZEALAND 2020; "Covid": WHEN COVID HIT; "money": THE RESERVE BANK CREATED
  NEW MONEY; "spent": THE GOVERNMENT SPENT MORE; "wages": INCLUDING HELP PAYING WAGES; "twenty-one": END OF
  2021; "found": ALMOST EVERYONE LOOKING FOR WORK FOUND IT; "hundred": the 100-dot panel with 3 empty: ABOUT 3
  IN 100 OUT OF WORK, credit STATS NZ.
- Effects: the tower's light blinks (about 0). About 0.55 s.

**Shot 10.2 - V1** (cut on "Which"; held).
- Events: "closer": WHICH ONE?; "guess": HAVE A GUESS with the ring.
- **The 4-second guess hold** goes here.
- Effects: the flat-out factory's smoke (0.2). About 0.75 s.

### Page 11 - New Zealand, the answer (about 20 s)

**Shot 11.1 - V3, FLAT OUT** (held; page 4's painting).
- Events: "flat-out": CLOSE TO THE FLAT-OUT FACTORY; "gate": ALMOST NO ONE WAITING.
- Effects as 4.1. About 0.75 s.

**Shot 11.2 - N4, the forecourt** (cut on "And" (1); held). Subject: the pump.
- Events: "fast": PRICES WENT UP FAST; "spent": PARTLY: MORE SPENT; "oil": PARTLY: PRICES OVERSEAS, LIKE OIL.
- Effects: a canopy tube flickers (about 0). About 0.55 s.

**Shot 11.3 - N3, the building site** (cut on "At" (2), "At the peak"). Subject: the timber frame.
- Move 1, lens push 1.2 times, centred on the frame: from "peak" over 3 s.
- Events: "peak": AT THE PEAK:; "homes": THE PRICE OF BUILDING NEW HOMES; "rents": , AND RENTS, and the
  villa's FOR RENT board appears (own surface). Never BUILDING NEW HOMES on its own; no house prices.
- Effects: the crane's light (about 0). About 0.55 s.

### Page 12 - The usual cure (about 27 s)

**Shot 12.1 - N2** (held).
- Events: "cure": THE USUAL CURE?; "raises": the dial INTEREST RATE, its needle rising (no figures); "Interest"
  (2): INTEREST = THE EXTRA YOU PAY BACK; "loans": MANY LOANS COST MORE; "spend": dissolve to N2 with the
  bakery's lights out over 1 s, with LESS TO SPEND; "things": BUSINESSES SELL FEWER THINGS; "people": AND HIRE
  FEWER PEOPLE; "slowly" (1): PRICES GO UP MORE SLOWLY; "down": USUALLY NOT DOWN.
- Effects: none. About 0.55 s.

**Shot 12.2 - V3** (cut on "In" ("In our picture"); held). FLAT OUT, then SLOWED (five figures).
- Events: "slows": dissolve from FLAT OUT to SLOWED over 2 s (half the windows go dark, the gates are shut,
  the queue is there); the smoke thins as it plays; "gate": MORE WORKERS WAIT AT THE GATE.
- Effects: smoke thinning to one chimney (0.2 falling to 0.05). About 0.7 s.

### Page 13 - Who pays, here (about 30 s)

**Shot 13.1 - N2** (held; the bakery dark).
- Events: "pays" (1): WHO PAYS FOR THE CURE? (small); "again": the dial climbs in steps, LATE 2021 TO 2023:
  AGAIN AND AGAIN; "loans" (1): MANY LOANS COST MORE; "find": JOBS HARDER TO FIND; "twenty-six": MIDDLE OF 2026;
  "hundred": the 100-dot panel with nearly 6 empty: NEARLY 6 IN 100 OUT OF WORK, credit STATS NZ; "three":
  UP FROM ABOUT 3 (faint); "reason": NOT THE ONLY REASON (small); "pays" (2): WHO PAYS? (big); "loans" (2):
  MANY PEOPLE WITH LOANS (a callout to the lit windows of the hillside houses).
- Effects: none. About 0.55 s.

**Shot 13.2 - V3, SLOWED (five)** (cut on "put"; held).
- Events: "work" (2): PEOPLE PUT OUT OF WORK.
- Effects: thin smoke from one chimney (0.05); the lantern flickers. About 0.6 s.

### Page 14 - Two views (about 26 s)

**Shot 14.1 - V3** (held, then one slide). SLOWED (five), then SLOWED (ten).
- Events: "America's": AMERICA'S VERSION OF OUR RESERVE BANK:, with the small credit US FEDERAL RESERVE;
  "jobs" (1): FEWER JOBS; "unfortunate": UNFORTUNATE,; "goal" (1): NOT THE GOAL (no quotation marks); "Clara":
  the name card CLARA E. MATTEI (no portrait); "follows": the small source credit THE CAPITAL ORDER (no
  year); "argues": MATTEI ARGUES:; "goal" (2): FEWER JOBS ARE THE MAIN GOAL; "more": dissolve from five
  waiting to ten over 1.5 s; "wages": LESS POWER TO ASK FOR HIGHER WAGES.
- Move 1, slide 0.8 m toward the queue: from "says" to "wages" (after the dissolve has finished).
- Effects: thin smoke (0.05), the lantern and the wages hatch's lamp flicker (about 0); soft contact
  shadows under the nearest figures fade in as the slide starts. About 0.6 s.

### Page 15 - Back at the checkout (about 29 s)

**Shot 15.1 - N1** (held on the composed frame).
- Events: "twenty-five": a tag card beside the basket, $100, JUNE 2025; "four": it flips to ABOUT $104, A
  YEAR LATER; "three": a ghost tag beside it, ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED, credit
  STATS NZ. No 4.1%, 2.9% or 2026 on screen.
- About 0.55 s.

**Shot 15.2 - N4** (cut on "When"; held; page 11's painting).
- Events: "up" (1): PETROL AND DIESEL GO UP; "moved": ALMOST EVERYTHING MADE OR MOVED GOES UP TOO. About 0.55 s.

**Shot 15.3 - V1** (cut on "both"; held; name tags on).
- Events: "both": a price arrow climbs over each factory's column: BOTH FACTORIES. About 0.75 s.

**Shot 15.4 - N1** (cut on "So"; held).
- Events: "diesel" (3): PART OF IT: PETROL AND DIESEL. Never "mostly". About 0.55 s.

### Page 16 - Spent on what? (about 25 s, then the 4 s fade)

**Shot 16.1 - V1** (held; name tags on).
- Events: "always": DOES NEW MONEY ALWAYS PUSH PRICES UP?; "No": NO.; the two rule cards exactly as page 5,
  in the same places: "spent" (1), "spare" (1), "made", "nothing", "up" (2).
- Effects: smoke (0.2). About 0.75 s.

**Shot 16.2 - N1** (cut on "So"). Subject: the headline beside the basket, the warning again.
- Move 1, lens push 1.25 times centred on the headline: from "warning" over 3 s.
- Events: "Spent" (2): SPENT ON WHAT?; "anything": ANYTHING SPARE TO MAKE WHAT IT BUYS? (small, under it);
  "pays": WHO PAYS FOR THE CURE?; both hold.
- **The 4-second fade** goes here, on the held headline and cards.
- About 0.55 s.

### Moves, holds and reuse at a glance

| Page | Shots (views) | Moves | Holds |
|---|---|---|---|
| 1 | N1 | slide, lens push | |
| 2 | N2, N3 | slide | |
| 3 | V1, V2 | slide, slide | |
| 4 | V3 | slide | 4 s guess (V3) |
| 5 | V3, V1 | none | 2 s rule (V1) |
| 6 | G1, V3 | slide | |
| 7 | G1, G2 | slide | |
| 8 | T1 | slide | 4 s guess (T1) |
| 9 | T1, V2, V1 | none | 2 s (V1) |
| 10 | N2, V1 | none | 4 s guess (V1) |
| 11 | V3, N4, N3 | lens push | |
| 12 | N2, V3 | none | |
| 13 | N2, V3 | none | |
| 14 | V3 | slide | |
| 15 | N1, N4, V1, N1 | none | |
| 16 | V1, N1 | lens push | 4 s fade (N1) |

32 shots, 12 moves (9 slides, 3 lens pushes), never more than 2 on a page. **Rule for slides: a view slides
the first time we meet it (it shows the place is real 3D), then holds on every return** (cheap, and a
return looks exactly the same). The exceptions: N3 and N4 only ever hold (one painting each); lens pushes on
returns (pages 11 and 16) uncover nothing; and page 14's slide toward the queue carries "with more workers
waiting at the gate".

How often each painting is used: V1 main on 6 pages (3, 5, 9, 10, 15, 16); V3 FLAT OUT on 5 (4, 5, 6, 11, 12);
N2 main on 4 (2, 10, 12, 13); N1 main on 3 (1, 15, 16); N4 and N3 on 2 each; V2 QUIET on 2 (3, 9).

### How the two factories stay consistent wherever they come back

1. **One set, one script, fixed places.** Both works are in one valley set built by one script. In V1 the
   quiet factory is always on the left and the flat-out factory on the right; never mirrored, never swapped.
   In each gate view, the other factory's wall shows at the side where it really stands.
2. **Fixed identities**, chosen to differ at a glance even at phone size: red-brown brick, one round
   chimney, green gates (quiet) against buff brick, two square chimneys, a water tank, red-brown gates
   (flat out). Each wears its name on its gate pier, and V1 carries two small typed name tags on every
   return from page 5 on.
3. **Matched gate views.** V2 and V3 are framed the same way from the same distance with the same lens and
   the same gate furniture, so a cut between them compares like with like.
4. **Canonical states.** V1 always shows QUIET and FLAT OUT, the two halves of the rule. The states change
   only in the gate views, only while the camera holds, and only on the spoken word that names the change
   ("go", "slows", "more").
5. **One painting chain.** The first valley view painted becomes the valley's master (in the test, V3 FLAT
   OUT; its style picture is the chapter 2 painting the notice corner used). Every other valley view and state
   is painted with image 1 its own plate and image 2 the master painting. Then:
   - each painting is lined up with its plate (`align_painting.py`);
   - its colours are compared with the master shone onto the set from its own camera (the brick of each
     works, the gates, the sky), with `match_model_colours.py`; a clear mismatch means a repaint;
   - a state painting is patched, not used whole: only the parts where its plate differs from the main
     state's plate (gates, windows, figures, smoke-free chimney tops) are taken from it, feathered, and laid
     into the main painting (`composite_fill.py`), so everything else is the same picture to the pixel and a
     dissolve changes only what the story changes.
6. **Returns reuse paintings.** The quick cuts back (pages 6, 9, 11, 13, 15) use paintings already made, so
   they match by construction.
7. **Same live effects every time.** The flat-out factory's two smokes, sparks and window flicker, and the
   quiet factory's lantern, are the same code with the same seeds on every page.

---

## 3. THE NUMBERS

### Plates, paintings and cost

| Place | Plates | Paintings | Which |
|---|---|---|---|
| New Zealand street | 4 | 7 | N1 main, N1 behind; N2 main, N2 behind, N2 bakery dark (state); N3; N4 |
| Valley | 5 | 10 | V1 main, behind; V2 QUIET main, behind; V2 WORKING; V3 FLAT OUT main, behind; V3 SLOWED (ten) main, behind; V3 SLOWED (five) |
| Glasgow street | 2 | 4 | G1 main, behind; G2 main, behind |
| Tokyo back office | 2 | 3 | T1 HALF main, behind; T1 FULL |
| **Total** | **13** | **24** | |

| Spending (all on hold until you say yes) | US$ |
|---|---|
| Narration (about 6,300 ElevenLabs credits) | about 1.10 |
| 24 paintings at about 10 US cents (Flux 3 edit on fal) | about 2.40 |
| The same if each costs what the notice corner's did (up to about 22 cents) | up to about 5.30 |
| Nano Banana Pro composition sketches, only if the shot checker can't find a passing frame for a main view (0 to 4) | 0 to 0.60 |
| **Planned total** | **about 3.50 to 7.00** |
| Repaint reserve (12 paintings, half the plan once more) | about 1.20 to 2.65 |
| **Planned total with every repaint used** | **at most about 9.65**, under the US$12 line; at least about US$10 of the US$20 left over |

Every request goes in the folder's `00-requests.json`. No step of the plan needs more than this.

### New props and models

- **Built by script, about 58 pieces:** New Zealand 30 (the shop row with verandahs, the Reserve Bank tower
  and wall, three villa variants, the foodmarket's inside, gondola shelves and lettered products, flipping
  shelf tags, the checkout counter, basket, seven grocery packs, reusable bag, keys, newspaper rack and
  papers, petrol canopy, pumps, oil rack, air pump, kiosk, timber frame, scaffolding, tower crane, concrete
  mixer, timber stack, block pallet, skip, site hut with hard hats and vests, site boards, the FOR RENT
  board, cabbage trees, the café A-frame, street blade, page 10's door sign); valley 9 (both works rebuilt
  at real size, gate piers and name boards, wages hatches, chain and padlock, lunch tins and tea can, goods
  crate stencils, figure shapes in five poses, the optional fingerpost, the town at real size); Glasgow 10
  (tenement blocks, close entrances, shopfronts, tram rails and poles, the works wall and gate, the
  recruiting poster, the landlord's notice, placards, the half-built tenement, walking figures); Tokyo 9
  (room shell and window, blinds, strong room door, cash bundles, cash cases, trolley, note counter, screen
  and keyboard, the street outside).
- **Fetched from Poly Haven:** 39 models and 26 surfaces (named in section 1; every name checked in Poly Haven's list); converted with the
  library's `convert_poly_haven.py` and listed in a new `index.json` beside the pit village one.
- **Reused:** the pit village street builder, set dressing and checker; 11 library props; chapter 2's
  factory, town and props scripts; the projection, effects and graphics code; the pit village's surfaces
  (setts, flagstones, brick, sandstone, slates, rust, the dusk sky, the window pictures).

### Blender time (machine time, two at a time)

| Step | Each | Count | Time |
|---|---|---|---|
| Plates (EEVEE, 1536 x 2730) | about 10 min | 13, each drawn about twice after checks | about 4.3 h |
| Preview stills (540 x 960) | about 1 min | about 15 per view, 10 views | about 2.5 h |
| Shot checker runs | about 1 min | about 10 per view | about 1.7 h |
| Exports (.glb and camera.json) | about 5 min | 13 | about 1.1 h |
| Poly Haven conversions | about 1 min | about 33 | about 0.5 h |
| **Total** | | | **about 10 h of machine time, about 5 to 6 h of waiting with two at a time** |

### Filming

- **Frames:** about 12,900 (about 7 minutes 10 seconds at Malina's measured 164 words a minute, with the
  planned page gaps, guess holds, rule holds and the fade).
- **Seconds a frame, expected:** about 0.55 s for plain shots and about 0.75 s for shots with chimney
  smoke, with three settings changed from the notice corner page: the stage's depth blur off (measured
  +1.07 s a frame), its glow pass off (+0.33 s; flames, lamps and windows glow with sprites instead), and no
  shadow-casting lamps (+0.37 s; soft contact shadows under near props instead). The painting already
  carries its own soft focus and light. Shine-back alone measured 0.29 to 0.32 s. Grain and darkened
  corners are added after filming (about 2 minutes for the chapter).
- About 5,300 frames carry smoke (the valley, the Glasgow works), about 7,600 don't: about 2.3 hours filmed
  one at a time, about **2.0 hours** two at a time.
- **Planned, with room for being wrong: 1.2 s a frame**, about 4.3 hours one at a time, **about 3.7 hours**
  two at a time (measured 17% faster on this machine). **The ceiling: 2 s a frame**, about 6.1 hours two at
  a time. Filmed in stretches of under 2 hours (`FILM_FROM` / `FILM_TO`), because a cloud session stops
  background jobs at 2 hours.
- The first free test (section 4) measures this before anything is built.

### Disk (about 8 GB free)

| What | About |
|---|---|
| Poly Haven downloads and conversions | 450 MB |
| Four .blend files | 400 MB |
| Set exports for the film (one set and one signs file per place, culled to what the cameras see) | 350 MB |
| Plates (PNG, with re-draws) and paintings (raw and lined up) | 300 MB |
| Checker reports, stills and contact sheets | 400 MB |
| Narration, word times, mix | 50 MB |
| Film pieces and chunks (kept as video, never as single pictures) and the finished film | 900 MB |
| **Peak** | **about 2.9 GB**, leaving about 5 GB |

Props are loaded from the library, never copied per set. Old stills are cleared after each place passes its checks.

---

## 4. THE ORDER OF WORK

### The cheapest test that would show the plan works

The plan rests on three things never tried: **painted figure shapes**, **state paintings that dissolve
cleanly**, and **a second view of a place painted to match the first**. One shot the film needs anyway
tests all three: page 12's "the flat-out factory slows... and more workers wait at the gate".

1. **Free, about 30 minutes: measure filming speed.** Film 90 frames of the notice corner as it is, then
   with depth blur, the glow pass and shadow maps off. Passes at about 1 s a frame or less without smoke.
   If not, the budget in section 3 is redone before building.
2. **Free, about a day: build the valley** (both works at real size, the gates, the town, figure shapes),
   compose V1 and V3 with the shot checker, draw the V3 FLAT OUT plate, the V3 SLOWED plate and the V1 plate.
   Film a 10-second test with the **unpainted plates** shone back: V3's slide, the hold, the dissolve to
   SLOWED. Shows the slide stays inside the plate (the weights view), the dissolve mechanics work, and the
   figure shapes read as people waiting at phone size.
3. **Paid, 3 paintings, about 30 to 66 US cents, with your yes:** V3 FLAT OUT (style: the chapter 2
   painting), V3 SLOWED (ten figures; image 2 the first painting), and V1 (image 2 the first painting). Then
   patch, line up, film the same 10 seconds painted, plus 3 seconds of V1.
   - **It passes if:** the figures read as workers waiting, from behind, with no faces, and the same count as
     the plate; the dissolve changes only the gates, windows, figures and smoke (a difference picture shows
     nothing else above a small threshold); V1's two works have the same colours as in V3 (the comparison
     tool, then a helper's eye); the slide doesn't tear; it looks like the notice corner on your phone.
   - Three fresh helpers check it (looks; painter faults; figures), then you look. The paintings are kept:
     they are pages 4, 5, 6, 11, 12, 13 and 14's.

### After the test

4. **Record the narration** (about US$1.10, with your yes; it can be asked for with the test). Word
   times, timeline and mix as in "Workflows". Until then, pages are built on estimated word times (164
   words a minute) and switched over when the real times arrive.
5. **Finish the valley** (V2 and both its states, V3's other count); then **build the New Zealand street**
   (the largest build: shops, the foodmarket's inside, the tower, the site, the forecourt), then **Glasgow**
   (from the same street script), then **Tokyo** (smallest). For each view: compose with the shot checker
   until it passes; the history helper checks a preview with the lettering list; then draw the plates
   (checking the render log for shadow memory faults).
6. **Paint, a place at a time, with your yes for each batch**, master view first; line up, patch state
   paintings, make behind paintings, keep painted shadows (`keep_painted_shadows.py`), check the colours
   against the master.
7. **Page files**: one per page, timed to words with `kit.at`; the camera checked with `camera_audit.py`;
   for every slide the four stills (the projector's view, the end, the middle, the weights view); every
   card checked against the narration by a words-on-screen helper.
8. **Film** in stretches of under 2 hours, two at a time; a frame-to-frame jump scan; two helpers and a
   skeptic check it in motion; fix and re-film only the changed chunks.
9. **Finish**: mix, captions, loudness and timing checks; then the real test: show it to the people who
   got lost, with the listener questions in the script file.

### Risks, and how each is caught

| Risk | How it is caught | What then |
|---|---|---|
| The figure shapes paint badly (faces, extra people, dummies, ghostly dissolves) | The paid test, a figure count per painting, the checker's out-of-date test per figure, your eye on a phone | Stronger painter words; own-surface silhouettes; empty props (section 1.5) |
| A state painting changes more than the story (a wobble or colour jump in the dissolve) | A difference picture between the two paintings outside the changed parts | Patch only the changed parts into the main painting (`composite_fill.py`) |
| The same factory looks different in two views | The colour comparison against the master shone from the other camera; a helper compares stills side by side | Repaint with the master as image 2 (10 cents) |
| Filming is slower than planned | The speed test first; each page's first chunk timed | Fewer smoke puffs; smoke only where it carries the story (the flat-out factory); held frames already dominate |
| The painter garbles lettering, or adds its own | Every sign is an own surface; a helper reads every sign in the film's stills | Nothing painted is ever used for lettering |
| Wrong Japanese, or wrong 1915 Glasgow wording | A helper who reads Japanese checks every Japanese sign before it is built; the history helper checks the poster, the notice and the placards against sources | Change the wording before drawing the plate |
| A figure on screen that Malina doesn't say (a price board, door number, keypad, calendar, receipt, pack size) | The lettering lists in section 1 are checked against the narration before building; a helper scans every still for digits | Turn it away, leave it off, or letter it with words |
| A real business or organisation imitated | Every invented name is searched first; the Reserve Bank carries its name only, in plain capitals, no logo, and the tower is not a copy of the real building | Rename; drop the carving and keep only the typed card |
| Party colours (the election is on 7 November 2026) | A helper checks every New Zealand still for a prominent red, blue, green or yellow-and-black prop or sign | Recolour |
| Era mistakes (2020s New Zealand, 1915 Glasgow, 2013 Tokyo) | The history helper is given the pictures, not only the words (lesson 83) | Fix in 3D before the plate |
| A slide leaves the painted area (a strip of plain surfaces at an edge) | The weights view at the end of every slide (blue at an edge) | A shorter slide, or a lens push instead |
| The painter adds flames, glows or shadows round near props | The painter words from log 32; a comparison of plate and painting | Ask again |
| The Glasgow works or the town is taken for the flat-out factory, or the valley for a real place | Distinct works (sooty red, one round chimney, a wall and arch) against the valley's; the cards PICTURE TWO FACTORIES, A REAL CASE, IN OUR PICTURE; the newcomer test | Stronger difference in the Glasgow works' shape |
| Returning to the same paintings feels repetitive | The newcomer test; a helper watching the whole film | It is on purpose (the viewer learns the places); a second lens framing of a return is free |
| Building the New Zealand street runs long (the biggest piece) | It comes after the valley test, so the method is proven first; build progress against a list | Simplify the far parts (hillside, tower) to blocks: they are painted over and small |
| Building Glasgow runs long | As above | Fallback for page 6 only: the pit village street (already built), dressed for 1915; page 7 still needs the tenements |
| The real narration moves the words | All events are tied to words, not seconds; holds absorb timing changes | Re-check stills at each page's word times |
| Money | Each batch is costed before you are asked; `00-requests.json` totals | Nothing in the plan needs more than about US$9.65 |
| Disk fills | `df` before each export and filming stretch | Clear old stills and plates already painted |

---

## Traps

- Never turn the camera during a move, and never pan: slides, rises, sideways steps and lens pushes only,
  at most 3 a page. A lens push stays centred: the subject must already be in the middle band.
- A state changes only while the camera holds. A view slides in one state only (the one with a behind painting).
- Draw a state's plate from where that state is shown: from the start of its slide if it slides, from the
  held spot if it only holds. A held view's painting is then its frame exactly.
- Paint a place's master view first, and give it as image 2 to every other painting of that place.
- Never put a program's lettering on screen; every sign keeps its own surface.
- Words on screen are short forms of what Malina says on that page; no figure she doesn't say, on cards or
  on signs; credits carry no figures.
- Never "MMT"; never the school's name; Mattei's view always under MATTEI ARGUES.
- The quiet factory is always left of the flat-out factory in V1. Never swap them, never mirror a picture.
- No faces anywhere. Figure shapes face away; real people appear only as typed name cards.
- No depth blur, glow pass or shadow maps in the film's settings without timing them first.
- The paid steps wait for your yes, batch by batch.
