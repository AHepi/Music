# Shot plan - chapter 2 for newcomers, the full redesign (built places, painted over)

Source for the story: Clara E. Mattei, *The Capital Order* (2022).

**What this is:** a plan for filming the whole of chapter 2 for newcomers ("33 Script - chapter 2 - what
really causes inflation - for newcomers", 16 pages, about 7 minutes) in the look you kept in log 32: each
place is a real 3D set built in Blender by script, drawn once from its main view (the plate), repainted in
the series' painted style by Flux, and the painting shone back onto the set so the camera can slide without
the picture tearing. Live light effects go on top; words on screen are typed cards.

**The angle of this plan:** start from what each page must teach and what a newcomer must *see* to get it
(the toolkit's "a concrete case before the general idea"), find the one picture that says it, the way the
notice corner's empty chair said "someone sat here", then cut back to what fits the money and this computer.
Nothing here is built, painted or filmed yet. Times in brackets are from the estimated timeline
(`film-kit/examples/inflation-chapter-2-newcomers/timeline-estimated.json`); every event is tied to its
spoken word, not to the second, so it follows the real recording.

## In short

- **6 places, 11 views, 29 shots.** One imagined place, **the Works** (two twin factories side by side, the
  picture the whole chapter keeps coming back to: 4 views), and five real places: a **New Zealand
  supermarket checkout**, a **New Zealand building site** (seen in two years: busy, then stopped), a **New
  Zealand kitchen table**, a **Glasgow tenement street in the First World War** (2 views), and a **Japanese
  corner shop's counter** (built from the checkout's script).
- **19 paintings**, about **US$1.90** at 10 cents each (up to about US$4.30 if each costs what log 32's two
  did). With the narration (about US$1.10) and up to four optional composition sketches (60 cents), the plan
  spends **about US$3.60, at most about US$6.00**, inside the US$12 ceiling, with room for repaints. Nothing
  paid happens without your yes.
- **About 1 second a frame on average, about 3 hours of filming** with two helpers at once, because a still
  shot's set is drawn once and only what moves is drawn each frame (the stage already does this,
  `cinema-stage.js`, "held shots"). Only about 1,200 of about 13,000 frames redraw the whole set.
- **One slide at most on any page**, never a turn. Nine pages have one slide; seven hold still.
- **People:** the waiting workers are simple figure shapes the painter turns into painted people, always seen
  from behind or against the light, never closer than about 4 metres. Everywhere else a person is shown by
  something made for a person (a hi-vis vest, a pulled-out chair, a suitcase). Crowds are never drawn: lit
  windows, typed counters and the 100-dot panel count them.
- **The first test is free:** build one view of the Works (the quiet factory's gate with its queue), film its
  19 seconds of page 3 with the plate itself standing in for the painting, and measure the speed and whether
  "the workers go in" reads. The first paid test (about 20 to 45 cents, with your yes) paints that same view,
  because painted people are this plan's biggest risk.

## Words used here

- **Plate:** the picture Blender draws of a set from its main view, a little wider than the film's frame.
- **Painting:** Flux's repaint of the plate in the series' style. It is shone back onto the set.
- **Behind painting:** a second painting of the same view with the near things painted out. It covers what
  they hid once the camera slides, or once they leave (the waiting men going in).
- **Own surface:** a thing that keeps its own sharp 3D surface instead of the painting: every sign and
  letter (the painter garbles small print), and anything that must change on a word (a gate swinging, a
  window lighting up).
- **Held shot:** the camera stays still; the set is drawn once and only moving things (smoke, flames, cards)
  are drawn on top each frame.
- **Slide:** the camera moves in a straight line toward (or back from) its subject at the same height,
  starting and stopping gently, never turning.
- **Story group:** the few things that tell a shot's story, placed so they touch or overlap ("07 Composing a
  shot", rule 3).
- **The model:** the script's two factories ("our picture"): the quiet factory (No. 1) and the flat-out
  factory (No. 2).

## How each picture was chosen, and what was cut back

For every page I asked: what must a newcomer understand, what would they need to see, and what single
composed picture makes that unforgettable? Then I cut back:

| Strongest picture first considered | Kept, changed or cut | Why |
|---|---|---|
| A 1915 labour exchange with empty benches (page 6: "fewer than one in a hundred out of work") | Cut | A whole new interior for 6 seconds; the 100-dot panel and the cut to the empty No. 2 gate carry it |
| A Japanese bank street at night (page 9: "sat in the banks") | Replaced | The model's own bank, lit up with the money sitting in it, shows "never reached the factory" in the same picture; Japan's real place becomes a corner-shop counter built from the checkout's script, which also rhymes with page 1 |
| Inside the flat-out factory, machines running (page 4) | Cut | A big interior; blazing windows, smoke, an open gate and stacked goods say "working as hard as they can" |
| A rise from the lane to a high view of both factories ("move up to see the bigger picture") | Cut | Needs its own plate and shows roofs the plate never saw; a view up the lane shows both gates side by side |
| Fire wherever people gather | Kept once | Only the brazier at the quiet factory's gate: they have waited long enough to light a fire, and it is still burning after they go in |
| The politician saying the warning (old plan) | Cut | No near people in this look; the warning is a typed card in Malina's words |
| A cut to the stopped building site at the end of page 1 ("put people out of work") | Cut | Page 2 shows the same site busy; seeing it stopped first would confuse a newcomer |
| Coins raining, banknotes landing | Cut | 3D money dropped into a painted set looked wrong before (decision 25), and New Zealand and Japanese notes and coins carry real people's portraits |
| A kitchen for "people with loans" (pages 12 and 13) | Kept | The opened letter from the bank and the chair pushed back make "loans cost more" a thing in someone's home; first to go if time runs short (fallback: the checkout with a lighter basket) |

## People: how the waiting workers and crowds are shown

"Workers wait at the gate" is the chapter's central picture: it defines the quiet factory (page 3), its
absence defines the flat-out factory (pages 4 and 11), its return is the cure (page 12), and it is Mattei's
argument (page 14). A newcomer has to see people waiting, and see their number change. So:

1. **Simple figure shapes, painted into people, only at the Works.** Eight standing figures built by
   script: long work coats, caps, hands in pockets or arms folded, one leaning on the wall, in dull browns
   and greys. They stand in a line along the factory wall, facing the gate, so the camera sees their backs
   (views W1, W3) or sees them against the lamp-lit lane, faces in shadow (view W4). The nearest is never
   closer than about 4 metres. The painter is told: keep each figure where it is, as a dark painted worker
   seen from behind, no faces, no new people.
   - **Where:** W1 (7 figures, page 3), W3 (7 small figures at No. 1's gate, every time), W2 (8 figures,
     only when the flat-out factory slows, page 12), W4 (8 figures outside the gate, page 14).
   - **How they come and go:** the figures are "near things" in the projection. The behind painting has
     them (and their shadows) painted out. "The workers go in" fades the figures away over 1.2 seconds as
     the gate swings open, showing the behind painting where they stood; "more workers wait at the gate"
     fades them back. Their painted shadows go with them (their swap area covers the figure and its
     shadow), unlike the notice corner's props, whose shadows were kept (lesson 122).
   - **Why not silhouettes alone, or none:** a row of black cut-outs would read as paper, and "none" makes
     "workers wait at the gate" a typed claim instead of a picture.
2. **An empty thing made for a person, everywhere else** (the notice corner's device, and your reading of
   it: "Seat next to fire makes sense ..."):
   - the building site: a hi-vis vest on the digger's door and a hard hat on the timber (workers, page 2);
     later the vest hung over the locked fence and gumboots by the post (put out of work, page 13);
   - the kitchen: the chair pushed back with a cardigan on it, glasses left on the letter (a borrower who
     has just got up);
   - Glasgow: a suitcase with a blanket bundle on the close step under the rent notice (one of the war
     workers who came, with nowhere to go);
   - the grocer's window: an empty basket;
   - the quiet factory after the men go in: the brazier still burning by the empty wall, a lunch tin left on
     the coping ("they've just gone in");
   - the inside of the flat-out factory's yard: a worker's jacket and cap on a nail by the gate (someone
     with a job).
   Why: real places in real years would need painted people in correct clothes of 1915, 2013 or 2021, which
   the painter can get wrong, and close painted faces edge toward portraits.
3. **Crowds are never drawn.** "Crowds of war workers", "twenty thousand families" and "millions went to
   fight" are shown by the Glasgow windows lighting until every home is lit, the suitcase, typed counters,
   and the 100-dot panel (people as dots). Painted crowds would be a jumble at phone size and cost
   paintings.

**What could go wrong with the painted figures, and the fallback:** the painter adds faces, changes how many
there are, adds people elsewhere, makes them look modern or photographic, or the fade reads as ghosts.
Caught by counting figures against the plate's figure outlines (the shot checker's outline test), a helper
looking at each painting at full size, and a fresh helper watching the fade in motion. Fixed by repainting
with stronger words and darker backlight; if two tries fail, the queue becomes things made for people: a row
of caps and lunch tins on the wall's coping by the brazier, and the fade becomes the caps disappearing.

---

## 1. The places

| Place | What, when | Views (plates) | Paintings | Pages |
|---|---|---|---|---|
| A. The Works | imagined, undated: two twin brick factories at the head of a short lane, dusk | W1 No. 1 gate, W2 No. 2 gate, W3 both gates, W4 No. 2's gate from inside | 2 + 2 + 1 + 2 = 7 | 3, 4, 5, 6, 9, 10, 11, 12, 14, 15, 16 |
| B. The checkout | New Zealand, 2025-26, a small suburban supermarket, evening | C1 | 2 | 1, 15, 16 |
| C. The corner shop | Japan, 2013, a corner shop's counter at night (built from B's script) | J1 | 1 | 8, 9 |
| D. The building site | New Zealand, a house going up; busy (2020-22), stopped (2026), dusk | S1a, S1b | 2 + 1 = 3 | 2, 10, 11, 13 |
| E. The kitchen | New Zealand, 2022-23, a kitchen table at night | K1 | 2 | 12, 13 |
| F. The Glasgow street | Glasgow, 1915-18, a tenement street at dusk | G1 grocer's window, G2 close mouth | 2 + 2 = 4 | 6, 7 |
| | | **11 plates** | **19** | |

Every view keeps a dim, quiet band across the top of the frame (sky, a dark wall or ceiling) for the typed
words, left of 0.90 across (rule 12).

### A. The Works (the model: "our picture")

- **What it is:** a short cobbled lane in an old brick industrial town, ending at one long factory wall with
  two iron gates about 9 metres apart. Behind the wall stand two twin brick works with sawtooth roofs and a
  tall chimney each, mirror images of each other. A pavement runs along the wall's foot. Halfway up the
  lane on the left stands a stone-fronted bank with a barred ground-floor window. The rest of the lane is
  terraced cottages and gas lamps; beyond the roofs, the far town (chimneys, a gasholder, a spire).
- **Era and place:** none on purpose. It is "our picture", not a real case: sign-writer's lettering, gas
  lamps and brick that could be any industrial town of the last century. The twins differ only in their
  state, so the lesson is plain: the only difference is whether anything is spare.
- **States** (the same in every view):

  | | windows | chimney | gate | at the gate |
  |---|---|---|---|---|
  | No. 1 quiet | dark | cold | shut, chained | 7 men waiting, a brazier, a lantern |
  | No. 1 working (page 3, after "go in") | lit | smoking | open | nobody; the brazier still burning, a lunch tin |
  | No. 2 flat-out | blazing, flickering | heavy smoke | open, crates stacked, a cart half out | nobody; the gateway's light on the empty pavement |
  | No. 2 slowed (page 12 on) | a third lit | thin smoke | half shut | 8 men waiting |

- **Main views:**
  - **W3, both gates** (the main view, painted first): on the right-hand pavement at the lane's mouth, about
    30 metres from the wall, at standing eye height (1.7 m), level, turned so the lane's kerbs, gutters and
    rooflines meet on the brick pier between the two gates. Two upright columns, as in the notice corner:
    No. 1's cold chimney, shut gate and queue on the left; No. 2's smoking chimney, open lit gate and
    stacked crates on the right. The bank is on the quiet left side, dim, its window dark until page 9.
  - **W1, the quiet factory's gate:** on the pavement at the wall's foot to the left of No. 1, about 1 metre
    out from the wall, standing at the end of the queue, where the next man looking for work would stand:
    9.7 metres from the gate at the slide's start, 8.5 at its end. The queue's line of backs leads the eye
    to the gate (rule 1 made by people). No. 2's lit gate further along the wall is kept hidden behind No. 1's
    pier, or it becomes a second bright place.
  - **W2, the flat-out factory's gate:** the mirror of W1 on the right of No. 2, from exactly where a waiting
    man would stand, but nobody is ahead of us.
  - **W4, No. 2's gate from inside the yard:** where a worker on his break would stand, 7.2 metres from the
    half-shut gate at the start, 6.0 at the end, level; through the bars, the lamp-lit lane and the queue.
- **Reused (files):** `paper-film/blender/pit-village/build_street.py` (cobbled lane, kerbs, pavements,
  cottages, gas lamps; run without the colliery, a 2-degree slope, a 7-metre lane);
  `paper-film/blender/build_factory.py` (the 1915 works, run twice with `--office left` and `--office
  right`, scaled from model size to real size, about 25 m wide, with its brick texture re-mapped at true
  scale); `assets/models/inflation-chapter-2/town.glb` (the far town, scaled the same); from
  `assets/models/pit-village/props/`: `iron-gates-pair.glb` (both gates), `brazier-drum.glb`,
  `hurricane-lantern.glb`, `gas-lamp-post.glb`, `gas-lamp-wall-bracket.glb`, `handcart.glb`,
  `wooden-chest.glb`, `wooden-barrel.glb`, `dustbins.glb`; the coal-sack builder in
  `paper-film/blender/pit-village/props/build_scripted_props.py` (re-stencilled); the colliery name board's
  builder (re-lettered); `set_dressing.py` (placing props, light linking, export); textures
  `red_brick`, `castle_brick_02_red`, `large_sandstone_blocks`, `grey_plaster_02` already in
  `assets/models/pit-village/textures/`.
- **Built new by script, with the lettering each carries:**
  - the factory wall with two brick gate arches, stone copings and piers;
  - two gate boards, sign-writer gold shaded red on dark green: **"No. 1"** and **"No. 2"** (Malina says
    "the first" and "the second", so these are short forms of her words, not new figures);
  - the bank front: stone, a barred window with a shallow lit room behind it (own surface, dark until page
    9), a brass plate **"BANK"**;
  - sacks in the bank's window stencilled **"NEW MONEY"** (re-stencilled coal sacks);
  - fuel cans by each gate stencilled **"PETROL"** and **"DIESEL"** (small; page 15);
  - eight waiting figures; a lunch tin; a worker's jacket and cap on a nail; a tin mug (W4).
- **Fetch from Poly Haven (CC0):** models `wooden_crate_01`, `wooden_crate_02` (finished goods at No. 2),
  `metal_jerrycan`, `metal_jerrycan_green` (the fuel cans), `hand_truck` (No. 2's yard); textures
  `brick_wall_02` (the factory wall), `cobblestone_floor_05` or the street's own setts.
- **Light:** the notice corner's dusk (sky about 1.4 to 1.96). The people's own lights: a gas lamp on each
  gate pier, the brazier and the lantern at No. 1, No. 2's blazing windows and lit gateway, and (page 9) the
  bank's window.
- **Plates and paintings:** 4 plates; 7 paintings: W1 main and behind, W2 main and behind, W3 main, W4 main
  and behind. W2's main painting is made **with** its queue (the slowed state); its flat-out state hides
  them and shows the behind painting in their place.
- **How the two factories stay the same wherever they come back:**
  1. One set file (`works.blend`) with four named cameras; it is never rebuilt between views.
  2. The twins come from one script, so brick, roofs, boards and gates match exactly.
  3. W3 is painted first; every later Works painting is given W3's painting as Flux's style picture (its
     second picture), not an older chapter 2 painting, so colour and brushwork match.
  4. Everything lettered or changing keeps its own surface (boards, gates, window glass, the bank's lit
     room, sack and can stencils), so it is identical in every view.
  5. One shared page module (a `works-effects.js` beside `pit-village-effects.js`) holds the four states'
     settings (window brightness, smoke amount, gate angle, how many men), so a state looks the same
     in every view.
  6. W3 always shows the two factories as first described (No. 1 quiet, No. 2 flat-out); the changes on
     pages 3 and 12 are "what happens next" on that page and don't carry over.
  7. Before filming, a continuity sheet (one still from each Works view side by side) is checked by a
     helper: chimneys, boards, gate states, how many men, sky.

### B. The checkout (New Zealand, 2025-26)

- **What it is:** one checkout lane of a small suburban supermarket in the evening: the belt, the till, the
  card terminal on its stand, the bag rack; behind, the ends of two aisles and the window to the car park
  at dusk.
- **Main view (C1):** where the shopper stands at the end of the belt, 1.6 m eye height, level, looking
  along the belt to the till; the plate is drawn from 1.3 m further back (the start of page 1's slide).
- **Story group:** a wire basket on the belt holding bread in a paper bag, a bottle of milk, kiwifruit,
  apples and a block of butter, bananas hanging over its rim; the divider bar against the basket's front;
  the card terminal just beyond, overlapping the basket's far corner. A warm light over the belt makes the
  basket the brightest thing.
- **Reused:** the checkout's script is written so that place C (Japan) is a second dressing of it.
- **Built new by script, with lettering:** the counter, belt, divider bar, card terminal (screen dark: no
  program text), till, bag rack, wire basket, bread bag, milk bottle and butter with invented brand labels
  (**"BREAD"**, **"MILK"**, **"BUTTER"**), a hanging **"CHECKOUT"** sign (no lane number), the shop's
  invented name on the window. No price tags on the shelves (no figures Malina doesn't say).
- **Fetch from Poly Haven:** `food_kiwi_01`, `food_apple_01`, `bananas`, `lemon`, `steel_frame_shelves_01`,
  `mounted_fluorescent_lights`, `cardboard_box_01`; textures `large_floor_tiles_02`, `painted_plaster_wall`.
- **Light:** evening; cool shop lights, a warm light over the belt (the people's own light, rule 6), dusk blue
  in the window.
- **Plates and paintings:** 1 plate; 2 paintings (main and behind: page 1 slides in, page 16 slides out).

### C. The corner shop (Japan, 2013)

- **What it is:** the counter of a small Japanese corner shop at night: the till, a glowing hot-food cabinet,
  shelves behind, the window to a night street with a drinks machine glowing across the road.
- **Main view (J1):** where the customer stands at the counter, 1.6 m, level.
- **Story group:** a basket on the counter with rice balls, a bottle of tea and a carton of milk, touching the
  till's edge; a change tray in front of it; the hot-food cabinet against the till's other side.
- **Built new by script (a second dressing of B's script), with lettering in correct Japanese:** labels
  **おにぎり** (rice ball), **お茶** (tea), **牛乳** (milk); a small **レジ** (checkout) sign over the counter,
  the same object as page 1's **"CHECKOUT"** in another country. No shop chain's name, no prices.
- **Fetch from Poly Haven:** `plastic_crate_01`, `mounted_fluorescent_lights`, `modular_electricity_poles`
  (seen through the window); texture `interior_tiles`.
- **Light:** night; white shop light, the hot-food cabinet's orange glow on the basket.
- **Plates and paintings:** 1 plate; 1 painting (held only).

### D. The building site (New Zealand, 2020-26)

- **What it is:** a suburban section where a timber-framed house is going up (pine frame, building wrap,
  scaffolding), behind temporary mesh fence panels, between finished weatherboard houses with corrugated
  iron roofs. The one place where "workers, materials and machines" are New Zealand things.
- **Main view (S1):** on the footpath outside the fence, at the fence gate, 1.7 m, level, turned so the
  fence line, the kerb and the frame's top plate meet at the gate's far post.
- **State a, busy (pages 2, 10, 11):** the gate open; just inside it the story group: a mini digger parked with
  its bucket resting on the ground, a strapped packet of fresh timber against its track, the hi-vis vest
  hanging on the digger's door, a hard hat on the timber; the site's work light on.
- **State b, stopped, 2026 (page 13):** the gate shut with a chain and padlock; the hi-vis vest hung over the
  fence rail on our side; gumboots by the post; the digger gone (a flattened patch where it stood); the
  timber grey under a torn cover; the frame no further on; the work light off; grass along the fence.
- **Built new by script, with lettering:** the mini digger (in faded orange, with no maker's name), the
  timber packet, the house frame with wrap (an invented maker's name repeated on the wrap), scaffolding,
  mesh fence panels with feet, the fence gate, chain and padlock, the hi-vis vest, the hard hat, the
  builder's banner on the fence (**an invented builder's name only**), two weatherboard neighbours.
- **Fetch from Poly Haven:** `rubber_boots` (gumboots), `cement_bag`, `security_light` (the work light),
  `wooden_ladder`; textures `weathered_plank_siding`, `corrugated_iron`, `plywood`, `concrete_floor`,
  `asphalt_02`, `concrete_pavement`.
- **Light:** dusk. State a: the work light (warm white) on the group, a neighbour's porch light. State b:
  only the street lamp and the porch light; colder.
- **Plates and paintings:** 2 plates (the states have different props in different places); 3 paintings:
  S1a main and behind (page 11 slides), S1b main (given S1a's painting as its style picture, so it is the
  same place).

### E. The kitchen (New Zealand, 2022-23)

- **What it is:** a small kitchen at night: a table by a window (a dark garden, a neighbour's lit window),
  a pendant lamp over the table, the bench with a kettle behind the camera's side.
- **Main view (K1):** standing at the kitchen bench, 1.6 m, level, 2.6 m from the table at the start, 1.4 m
  at the end of the slide.
- **Story group:** the opened letter from the bank, its torn envelope under it, reading glasses on its corner,
  a mug against the glasses, a phone face down; the chair pushed back at an angle with a cardigan over it.
- **Built new by script, with lettering:** the room, the window, the bench; the letter (own surface):
  **an invented bank's name**, **"Your home loan"** and **"Your new interest rate"**, no figures and no
  date; the envelope; the mug; the phone; the cardigan.
- **Fetch from Poly Haven:** `dining_table`, `dining_chair_02`, `round_spectacles`,
  `vintage_electric_kettle`, `modern_ceiling_lamp_01`, `potted_plant_01`; textures `laminate_floor`,
  `painted_plaster_wall`.
- **Light:** night; the pendant lamp warm on the letter (the brightest thing), the window blue-black.
- **Plates and paintings:** 1 plate; 2 paintings (main and behind: page 12 slides).

### F. The Glasgow street (1915-18)

- **What it is:** a Govan tenement street at dusk: four-storey blond and red sandstone tenements, shops at
  street level, arched close entrances, granite setts, gas lamps, and a gap where a new tenement was started
  and left: scaffold poles, a brick stack under a tarpaulin, a builder's handcart.
- **Main views:**
  - **G1, the grocer's window (page 6):** on the pavement where a passer-by stops at the window, about 3.5 m
    from the glass, 1.7 m, level. Story group: a tiered display almost bare (three labelled tins on a lot of
    empty shelf), an empty wicker basket against the stand's foot, a slumped flour sack against the door
    frame, and through the glass, lined up just above the basket, the brass till on the counter in the
    shop's gas light.
  - **G2, the close mouth (page 7):** on the pavement where a neighbour would stand, about 7 m down the street
    from the close, near the kerb, level, turned so the kerb, string courses and gutters of both sides meet at
    the close's arch edge: the notice corner's own composition, moved to Glasgow, with dozens of tenement
    windows receding on both sides. Story group: the factor's notice on the pilaster at the close's edge;
    directly below it on the step, a suitcase with a blanket bundle tied on top; the close's gas bracket just
    inside the arch lighting the notice from the side and below. On the quiet side: the stopped building
    site.
- **Reused:** `notice-paper.glb`'s builder (re-lettered), `handcart.glb` (re-lettered), `gas-lamp-post.glb`,
  `gas-lamp-wall-bracket.glb`, `wicker-basket-tray.glb`, `wooden-chest.glb`; the street builder's kerbs and
  setts; textures `large_sandstone_blocks`.
- **Built new by script, with lettering (each line checked by the history helper):** a tenement block
  builder (four storeys, sash windows whose glass keeps its own surface so it can light up, close arches,
  shopfronts); the grocer's fascia **"W. ANDERSON · FAMILY GROCER"** (invented); tins **"TEA"**,
  **"COCOA"**, **"SYRUP"**; the factor's notice: **"NOTICE TO TENANTS. Take notice that the Rents of these
  Houses will be Increased. By Order, THE FACTOR."** (no figures, no date, no names); the builder's cart
  **"J. LAIRD · BUILDER"** (invented); scaffold poles and boards, the brick stack and tarpaulin; the blanket
  bundle. No close numbers or street names (figures and real addresses).
- **Fetch from Poly Haven:** `CashRegister_01` (the till), `vintage_suitcase`, `wicker_basket_01`,
  `wooden_ladder`; textures `red_sandstone_wall`, `sandstone_blocks_05`, `square_cobblestone`.
- **Light:** dusk; street gas lamps, the close's gas bracket, the grocer's gas mantle inside, the tenement
  windows (live, page 7).
- **Plates and paintings:** 2 plates; 4 paintings (G1 main and behind, G2 main and behind).

---

## 2. The shots, page by page

Each page lists: what it must teach, what a newcomer must see, the strongest picture, then its shots.
Costs are the drawing time per frame on this computer, from the stage's own measurement (the notice
corner: 3.6 seconds a frame drawn whole, of which 3.1 is the painted set) and plan 26's effect costs:
**about 0.5 s** a held frame with nothing live, **about 1.0 s** with smoke, flames or flicker drawn on top,
**about 3.5 s** while the camera slides or the set changes.

**Between pages:** the series' page peel, except where the next page continues the same frame (4 into 5,
8 into 9), which runs on with no join. **Inside a page:** straight cuts.

### Page 1 - The question (about 28 s)

- **Must teach:** inflation is prices in general going up, the whole basket; the warning; why it matters
  (the cure makes loans cost more and can put people out of work).
- **Must see:** their own basket at a checkout, every item going up together.
- **Strongest picture:** one full basket on the belt at an empty checkout; on "The whole basket" an up-arrow
  tag springs up beside every item at once.

**Shot 1a - C1, the checkout (whole page).**
- Camera: the shopper's spot at the end of the belt, 1.6 m, level. Subject: the basket. Story group as in
  place B.
- Move: one slide toward the basket, 1.3 m, from "The same" (3.2 s) to about 7 s, stopping on the composed
  frame.
- Events and words on screen:
  - "felt" (1.4 s): the picture fades up from dark.
  - "inflation" (7.3 s): **INFLATION**; "general" (8.9 s): **PRICES IN GENERAL, GOING UP**.
  - "whole" (10.8 s): an up-arrow tag beside every item at once, **THE WHOLE BASKET** (arrows, no prices).
  - "warning" (12.8 s): the tags fold away; "prices" (15.8 s): **NEW MONEY → PRICES UP?**
  - "always" (17.7 s): **IS THAT ALWAYS TRUE?**
  - "cure" (22.4 s): **THE USUAL CURE**; "loans" (23.3 s): **→ MANY LOANS COST MORE**; "out" (25.9 s):
    **→ OUT OF WORK**.
- Light effects: none live. About 0.5 s a frame held, 3.5 s during the slide.

### Page 2 - Who can create new money (about 20 s)

- **Must teach:** here, the Reserve Bank can create new money and tries to stop prices going up too fast;
  economists who study how modern money works argue our government can't run out of its own money, but it can
  run out of workers, materials and machines.
- **Must see:** what "workers, materials and machines" are, as real New Zealand things.
- **Strongest picture:** a New Zealand house going up at dusk; just inside the site gate, the three things
  touching: the parked digger, the packet of fresh timber against its track, the hi-vis vest on its door and
  the hard hat on the timber.

**Shot 2a - S1a, the building site (busy), held.**
- Camera: on the footpath at the open fence gate, 1.7 m, level. Subject and story group as in place D.
- Move: none.
- Events and words on screen:
  - "New Zealand" (30.4 s): **NEW ZEALAND**; "Reserve" (31.6 s): **THE RESERVE BANK** / "can" (32.3 s)
    **CAN CREATE NEW MONEY** (typed, no logo).
  - "tries" (33.4 s): **TRIES TO STOP PRICES GOING UP TOO FAST**.
  - "economists" (36.5 s): **ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS**; "argue" (39.6 s): **THEY ARGUE:
    OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY**.
  - "But" (43.0 s): **BUT IT CAN RUN OUT OF...**; then a label with a thin line to each thing: "workers"
    (44.2 s) **WORKERS** → the vest and hat; "materials" (45.0 s) **MATERIALS** → the timber; "machines"
    (45.7 s) **MACHINES** → the digger.
- Light effects: none live. About 0.5 s a frame.

### Page 3 - The quiet factory (about 27 s)

- **Must teach:** the two-factories picture, each standing for a whole country; the quiet factory has spare
  workers; new money spent there gets more things made, so prices barely move.
- **Must see:** two factories that differ only in whether people wait at the gate; then the quiet one: a
  queue at a shut gate, and what happens when the money is spent: the gate opens, the people go in, the
  lights and the chimney come on.
- **Strongest picture:** W1: the line of waiting men's backs along the wall, leading the eye to the shut
  No. 1 gate with a small fire at the front of the queue; then the same view with the gate open, the men
  gone in, and the fire still burning by the empty wall.

**Shot 3a - W3, both gates, held (48.1 to 55.1 s).**
- Subject: the two gates side by side. Story group: No. 1's shut gate, brazier and queue; No. 2's open gate
  with its crates and cart.
- Move: none.
- Events and words: "two factories" (48.5 s): **TWO FACTORIES**; "country" (51.3 s): **A WHOLE COUNTRY:**
  then word by word **WORKERS, MATERIALS, MACHINES** (52.7 to 54.1 s).
- Light effects: No. 2's chimney smoke, No. 2's window flicker, No. 1's brazier flames, the lantern's
  flicker. About 1.0 s a frame.

**Shot 3b - W1, the quiet factory's gate (55.1 s to the page turn).**
- Camera: the end of the queue, 1 m out from the wall, 1.7 m, level. Subject: the shut No. 1 gate.
- Story group: the shut gates with chain and padlock; the brazier against the gate's left pier (its rim
  clearly over the pier's base); the first man beside it with one hand on a gate bar; six more back along the
  wall, each overlapping the one in front; a lit lantern and a lunch tin on the coping above the third man.
- Move: one slide along the queue toward the gate, 1.2 m, from "Workers" (57.9 s) to "job" (60.3 s), as if
  joining the line.
- Events and words:
  - "first" (55.5 s): cut in; the windows dark, the chimney cold ("the machines stand still").
  - "quiet" (61.6 s): **THE QUIET FACTORY**.
  - "government" (63.3 s): **THE GOVERNMENT SPENDS NEW MONEY**.
  - "go" (67.2 s): the gate swings open (1.2 s) and the queue fades away (1.2 s, from "in", 67.4 s): they
    have gone in. The brazier keeps burning by the empty wall; the lunch tin stays.
  - "start" (68.7 s): No. 1's windows light up (0.8 s) and its chimney begins to smoke.
  - "More money" (69.5 s): **MORE MONEY** / "things" (71.2 s): **MORE THINGS TO BUY** (the same layout as
    page 5's MORE MONEY / SAME THINGS TO BUY and page 6's FEWER).
  - "barely" (72.9 s): a price arrow over No. 1 that stays level: **PRICES BARELY MOVE**.
- Light effects: brazier flames, glow and a little smoke; lantern flicker; after "start", chimney smoke and a
  faint flicker in the windows. About 1.0 s a frame held, 3.5 s during the slide and the changes (about 5 s
  of film).

### Page 4 - The flat-out factory, the first guess (about 20 s, with the 4-second hold)

- **Must teach:** in the flat-out factory every worker and machine is busy and no one waits at the gate; the
  same new money is spent there; what happens to prices?
- **Must see:** the same wall and gate as No. 1, with nobody there and every sign of full work.
- **Strongest picture:** W2 from where a waiting man would stand, but nobody is ahead of us: the gate wide
  open, crates of finished goods stacked against its leaf, a loaded cart halfway out, the yard and every
  window blazing, the chimney pouring smoke, and the gateway's warm light falling on the empty pavement where
  a queue would be.

**Shot 4a - W2, the flat-out factory's gate (75.5 s to the end of the hold).**
- Camera: the mirror of W1, at the wall's foot to the right of No. 2, 9.7 m from the gate at the start.
  Subject: the open gate.
- Story group: the gate leaf pinned back against the wall, crates stacked against its inside, the loaded
  handcart's shafts over the crates, the gate lamp on the pier above, the warm patch of light on the empty
  pavement.
- Move: one slide toward the gate, 1.2 m, from "No one" (82.0 s) to "factory" (84.9 s): walking up to the
  gate with no one in the way.
- Events and words:
  - "busy" (79.2 s): the windows flicker brighter.
  - "flat-out" (84.5 s): **THE FLAT-OUT FACTORY**, with a small line under it **FLAT OUT = WORKING AS HARD
    AS THEY CAN**.
  - "same" (86.0 s): **THE SAME NEW MONEY IS SPENT**.
  - "prices" (90.0 s): **WHAT HAPPENS TO PRICES?**; "guess" (91.0 s): a small **HAVE A GUESS** with a ring
    that fills over 4 seconds.
- **The 4-second guess hold:** from Malina's last word (91.8 s) to page 5 (95.7 s), on the still composed
  frame, the question and ring held, the music up. No join: page 5 continues this frame.
- Light effects: heavy chimney smoke, window flicker. About 1.0 s a frame held, 3.5 s during the slide.

### Page 5 - The rule (about 28 s, with the 2-second hold)

- **Must teach:** why prices go up when nothing is spare (more money, the same things, so businesses can ask
  more); the rule, which most economists agree on.
- **Must see:** the flat-out factory while the reason is given; then both factories side by side with the rule
  written over each one.
- **Strongest picture:** W3, the two gates side by side, a rule card over each factory: over No. 1 and its
  queue, "spare: mostly more things made"; over No. 2 and its empty pavement, "nothing spare: mostly prices
  up".

**Shot 5a - W2, the composed frame, held (95.8 to 107.1 s).**
- Events and words: "spare" (95.9 s): **NO SPARE:** then **WORKERS / MATERIALS / MACHINES** word by word;
  "same" (102.2 s): **MORE MONEY / SAME THINGS TO BUY**; "businesses" (103.9 s): **BUSINESSES CAN ASK
  MORE**; "up" (106.5 s): a price arrow over No. 2 climbs.
- Light effects: as page 4. About 1.0 s a frame.

**Shot 5b - W3, held (107.1 s to the page turn).**
- Events and words: "Most" (107.1 s): cut; "agree" (108.0 s): small **MOST ECONOMISTS AGREE**; "spent"
  (110.4 s): the card over No. 1 begins **NEW MONEY SPENT + SPARE**, and on "made" (116.3 s) ends
  **→ MOSTLY MORE THINGS MADE**; "nothing" (117.3 s): the card over No. 2 **NOTHING SPARE**, and on "up"
  (120.0 s) **→ MOSTLY PRICES UP**.
- **The 2-second rule hold:** both cards held from Malina's last word (120.6 s) to the page turn (about
  124 s), the music up.
- Light effects: as 3a. About 1.0 s a frame.

### Page 6 - Britain at war (about 27 s)

- **Must teach:** a real case close to the flat-out factory: millions went to fight, fewer than one worker in
  a hundred out of work, ships sunk, the war paid for partly with new money; more money, fewer things; prices
  roughly doubled.
- **Must see:** "fewer things to buy" as an everyday thing, the money still there in the till.
- **Strongest picture:** G1, a grocer's window in the war: a tiered display almost bare, an empty basket, a
  slumped flour sack by the door; through the glass, the brass till in the shop's gas light. Money in, few
  things out.

**Shot 6a - G1, the grocer's window (124.1 to 146.4 s).**
- Camera: the passer-by's spot, 3.5 m from the glass, 1.7 m, level. Subject: the display. Story group as in
  place F.
- Move: one slide toward the window, 1.2 m, from "fewer things" (141.4 s) to "doubled" (145.5 s).
- Events and words:
  - "Britain" (125.5 s): **BRITAIN, FIRST WORLD WAR**.
  - "Millions" (128.1 s): **MILLIONS WENT TO FIGHT**.
  - "fewer" (130.4 s): the 100-dot panel, every dot lit but the last, nearly empty: **FEWER THAN 1 IN 100 OUT
    OF WORK**.
  - "submarines" (134.0 s): **SHIPS SUNK: FOOD, MATERIALS**.
  - "partly" (138.4 s): **PARTLY NEW MONEY**.
  - "More" (140.1 s): **MORE MONEY** / "fewer" (141.4 s): **FEWER THINGS TO BUY**.
  - "doubled" (145.5 s): two bars, **BEFORE** and **END OF THE WAR: ROUGHLY ×2**.
- Light effects: none live (the gas light is painted). About 0.5 s a frame held, 3.5 s during the slide.

**Shot 6b - W2, the composed frame (146.4 s to the page turn).** "close" (147.4 s): **CLOSE TO THE
FLAT-OUT FACTORY**. About 1.0 s a frame.

### Page 7 - Glasgow's homes (about 33 s)

- **Must teach:** the picture works for one kind of thing, homes: war workers came to Glasgow; there were
  already too few homes; builders and materials went to the war; landlords raised rents up to a quarter in
  places; about twenty thousand families refused the extra; Parliament brought rents on small homes back.
- **Must see:** homes that are all full, newcomers with nowhere to go, building that stopped, and the
  landlord's notice that turned it into higher rent.
- **Strongest picture:** G2, a Glasgow close mouth at dusk: the factor's rent notice pasted beside it, a newly
  arrived worker's suitcase and bundle on the step below it, the tenement windows on both sides lighting up
  until every home is lit, and to one side, a building site where the work stopped.

**Shot 7a - G2, the close mouth (whole page).**
- Camera: the neighbour's spot, 7 m down the street from the close, near the kerb, 1.7 m, level. Subject: the
  notice. Story group as in place F.
- Move: one slide toward the notice, 1.2 m, from "Landlords" (167.7 s) to "quarter" (170.8 s).
- Events and words:
  - "fifteen" (151.5 s): **GLASGOW 1915**; "crowds" (152.2 s): **CROWDS OF WAR WORKERS**.
  - "homes" (156.4 s): the tenement windows light in a quick ripple from the close outward until every one is
    lit (1.5 s): **TOO FEW HOMES ALREADY**.
  - "builders" (157.4 s): a label with a thin line to the stopped site: **BUILDERS AND MATERIALS GONE TO
    WAR**; "built" (160.8 s): **FEW NEW HOMES**.
  - "thing" (163.4 s): small **ONE KIND OF THING**; "factory" (166.8 s): **FOR HOMES: LIKE THE FLAT-OUT
    FACTORY** (the blazing windows rhyme with No. 2's; no cut away).
  - "rent" (168.8 s): **RENT RAISED**; "quarter" (170.8 s): **UP TO A QUARTER MORE, IN PLACES**.
  - "twenty thousand" (172.9 s): a counter rolls up to **ABOUT 20,000 FAMILIES REFUSING THE EXTRA** (done by
    "extra", 175.5 s).
  - "back" (179.9 s): a typed stamp **RENTS BACK TO BEFORE THE WAR**.
  - Never WON, FROZEN, NOT ENOUGH or a Mary Barbour card (the script's rules).
- Light effects: none live; the window ripple is a set change (1.5 s of full drawing). About 0.5 s a frame
  held, 3.5 s during the ripple and the slide.

### Page 8 - Japan, the second guess (about 18 s, with the 4-second hold)

- **Must teach:** Japan, 2013: Japan's version of our Reserve Bank planned to double the money it had created in
  two years; if the warning is right, prices should go up fast; guess.
- **Must see:** a real everyday place in Japan where prices are felt, the same kind of place as page 1.
- **Strongest picture:** J1, a Japanese corner shop's counter at night with a basket on it against the till,
  the hot-food cabinet glowing beside it: another country's basket at another checkout.

**Shot 8a - J1, the corner shop counter, held (183.8 s to the end of the hold).**
- Camera: the customer's spot, 1.6 m, level. Subject: the basket. Story group as in place C.
- Move: none.
- Events and words: "Japan" (183.8 s): **JAPAN 2013**; "version" (186.2 s): small **JAPAN'S VERSION OF OUR
  RESERVE BANK**; "double" (188.2 s): **×2 MONEY**; "years" (190.8 s): **IN TWO YEARS**; "warning" (192.0
  s): a dashed line climbing steeply, **IF THE WARNING IS RIGHT**; "happened" (196.0 s): **WHAT
  HAPPENED?**; "guess" (197.1 s): **HAVE A GUESS** and its ring.
- **The 4-second guess hold:** 197.9 to 201.8 s, held. No join: page 9 continues this frame.
- Light effects: none live. About 0.5 s a frame.

### Page 9 - Japan, the answer (about 29 s, with the 2-second hold)

- **Must teach:** prices barely moved for about eight years, about half a percent a year on average; one reason:
  most of the new money sat in the banks and never reached the factory; so what matters is whether it is
  spent, and on what.
- **Must see:** money that was made, but stopped short of the factory.
- **Strongest picture:** W3 at dusk, the bank halfway up the lane lit from inside, sacks stencilled NEW MONEY
  piled behind its barred window, and the lane beyond it to both gates empty: the money is in the bank, not
  at the gates.

**Shot 9a - J1, the same frame (201.9 to 211.2 s).** "barely" (202.2 s): a real line runs almost level beside
the dashed one, **PRICES BARELY MOVED**; "eight" (204.0 s): **ABOUT 8 YEARS**; "half" (207.1 s): **ABOUT
½% A YEAR, ON AVERAGE**. About 0.5 s a frame.

**Shot 9b - W3, held (211.2 s to the page turn).**
- This view breaks the main rule on purpose: the cause (the lit bank) and the effect (the untouched gates)
  are apart, and the empty lane between them is the story. The labels' lines tie them together.
- Events and words: "most" (211.2 s): cut; "banks" (213.2 s): the bank's window lights from inside, showing
  the sacks (1 s): a label to it, **MOST SAT IN THE BANKS**; "never" (215.7 s): a label to the gates,
  **NEVER REACHED THE FACTORY**; "not just" (218.0 s): **NOT JUST HOW MUCH**; "whether" (220.7 s):
  **WHETHER IT'S SPENT, AND ON WHAT**; "spare" (223.8 s): **SPARE WORKERS, MATERIALS, MACHINES TO MAKE
  WHAT IT BUYS?**
- **The 2-second hold:** that card held from 227.4 s to the page turn (about 230.8 s).
- Light effects: as 3a, plus the bank window's own light. About 1.0 s a frame.

### Page 10 - New Zealand, the third guess (about 25 s, with the 4-second hold)

- **Must teach:** here, from 2020: the Reserve Bank created new money, the government spent more including help
  paying wages; by the end of 2021 about three in a hundred were out of work; which factory was New Zealand
  closer to?
- **Must see:** New Zealand's own workers, materials and machines (page 2's site), busy, and the clue counted
  as people.
- **Strongest picture:** the page 2 site again, now dated, with the 100-dot panel; then both factories with
  the question.

**Shot 10a - S1a, held (230.9 to 248.5 s).** "here" (231.4 s): **NEW ZEALAND 2020**; "money" (235.7 s):
**NEW MONEY**; "government" (237.0 s): **GOVERNMENT SPENT MORE**; "wages" (239.8 s): **INCLUDING HELP
PAYING WAGES**; "twenty-one" (241.8 s): **END OF 2021**; "three" (246.1 s): the 100-dot panel, three dots
empty, **ABOUT 3 IN 100 OUT OF WORK**, small credit **STATS NZ**. About 0.5 s a frame.

**Shot 10b - W3, held (248.5 s to the end of the hold).** "Which" (248.5 s): cut, **WHICH ONE?** with a
small arrow to each gate; "guess" (251.2 s): **HAVE A GUESS**. **The 4-second guess hold:** 252.0 to
255.9 s. About 1.0 s a frame.

### Page 11 - New Zealand, the answer (about 19 s)

- **Must teach:** close to the flat-out factory; prices went up fast, partly because more was being spent and
  partly because of prices overseas, like oil; at the peak the biggest push came from the price of building
  new homes, and rents.
- **Must see:** the answer on the picture (the empty No. 2 gate), then where the push came from: the cost of
  building the very homes they have watched go up.
- **Strongest picture:** the site, the camera sliding toward the half-built house on "the price of building
  new homes".

**Shot 11a - W2, the composed frame (256.0 to 260.5 s).** "Close" (256.0 s): **CLOSE TO THE FLAT-OUT
FACTORY**; "waiting" (258.9 s): small **ALMOST NO ONE WAITING**. About 1.0 s a frame.

**Shot 11b - S1a (260.5 s to the page turn).**
- Move: one slide toward the house frame, 1.2 m, from "push" (269.9 s) to "homes" (272.0 s).
- Events and words: "prices" (260.7 s): **PRICES WENT UP FAST**; "Partly" (262.5 s): **PARTLY: MORE SPENT**;
  "partly" (265.2 s): **PARTLY: PRICES OVERSEAS, LIKE OIL**; "peak" (268.6 s): **AT THE PEAK:**; "building"
  (271.4 s): **THE PRICE OF BUILDING NEW HOMES**; "rents" (273.1 s): **AND RENTS**. Never "building new
  homes" on its own.
- Light effects: none live. About 0.5 s a frame held, 3.5 s during the slide.

### Page 12 - The usual cure (about 26 s)

- **Must teach:** the Reserve Bank raises its interest rate; interest is the extra you pay back when you
  borrow; many loans cost more, so people have less to spend; businesses sell fewer things and hire fewer
  people; prices go up more slowly, usually not down; on the picture, the flat-out factory slows and more
  workers wait at the gate.
- **Must see:** the cure arriving in a home as a letter; the chain from the letter to fewer jobs; then the
  factory slowing and the queue coming back.
- **Strongest picture:** K1, a kitchen table at night with the opened letter about the home loan's interest
  rate, glasses on it, a cold mug, and the chair pushed back with a cardigan on it; then W2 dimming as the
  queue returns.

**Shot 12a - K1, the kitchen (275.3 to 294.8 s).**
- Camera: standing at the bench, 1.6 m, level. Subject: the letter. Story group as in place E.
- Move: one slide toward the table, 1.2 m, from "Many loans" (282.8 s) to "spend" (285.7 s).
- Events and words: "cure" (276.4 s): **THE USUAL CURE**; "raises" (277.8 s): a dial in the dark window,
  **INTEREST RATE**, its needle rising (no figures); "Interest" (279.6 s): **INTEREST = THE EXTRA YOU PAY
  BACK WHEN YOU BORROW**; "loans" (283.0 s): **MANY LOANS COST MORE**; "spend" (285.7 s): **→ LESS TO
  SPEND**; "sell" (287.0 s): **→ SELL FEWER THINGS**; "hire" (288.5 s): **→ HIRE FEWER PEOPLE**; "slowly"
  (291.1 s): **PRICES GO UP MORE SLOWLY**; "down" (292.6 s): **USUALLY NOT DOWN**.
- Light effects: none live. About 0.5 s a frame held, 3.5 s during the slide.

**Shot 12b - W2, the composed frame (294.8 s to the page turn).**
- Events and words: "picture" (295.2 s): cut; "slows" (297.0 s): No. 2's windows dim to a third, its smoke
  thins, the gate swings half shut (1.5 s); "workers" (298.4 s): the queue fades in along the wall (1.2 s):
  **MORE WORKERS AT THE GATE** (299.4 s).
- Light effects: smoke, flicker. About 1.0 s a frame held, 3.5 s during the change.

### Page 13 - Who pays, here (about 28 s)

- **Must teach:** the Reserve Bank raised its interest rate again and again from late 2021 into 2023; many
  loans cost more and jobs got harder to find; by the middle of 2026 nearly six in a hundred were out of work,
  up from about three; the interest rate isn't the only reason; who pays: many people with loans, and people
  put out of work.
- **Must see:** the two kinds of people who pay, as two places they already know.
- **Strongest picture:** S1b, the same site as pages 2, 10 and 11, stopped: the fence gate chained, the hi-vis
  vest hung over the fence on the footpath side, gumboots by the post, the timber grey under a torn cover,
  the frame no further on.

**Shot 13a - K1, the composed frame (301.6 to 311.0 s).** "Who pays" (301.8 s): **WHO PAYS FOR THE CURE?**;
"From late" (303.3 s): the dial's needle steps up again and again: **LATE 2021 TO 2023: AGAIN AND AGAIN**
(by "again", 308.7 s); "loans" (309.8 s): **MANY LOANS COST MORE**.

**Shot 13b - S1b, the stopped site, held (311.0 to 324.2 s).** "jobs" (311.2 s): cut, **JOBS HARDER TO
FIND**; "middle" (313.4 s): **MIDDLE OF 2026**; "six" (315.7 s): the 100-dot panel with nearly six empty:
**NEARLY 6 IN 100 OUT OF WORK**, credit **STATS NZ**; "three" (318.7 s): faint **UP FROM ABOUT 3**; "only"
(321.0 s): small **NOT THE ONLY REASON**; "who pays" (322.7 s): **WHO PAYS?**

**Shot 13c - K1 (324.2 to 325.9 s).** **MANY PEOPLE WITH LOANS**.

**Shot 13d - S1b (325.9 s to the page turn).** **PEOPLE PUT OUT OF WORK**.

- Moves: none (cuts only). Light effects: none live. About 0.5 s a frame.

### Page 14 - Two views (about 24 s)

- **Must teach:** America's version of our Reserve Bank says the cure would probably mean fewer jobs,
  unfortunate but not the goal; Mattei argues fewer jobs are the cure's main goal: with more workers waiting
  at the gate, people with jobs have less power to ask for higher wages.
- **Must see:** Mattei's argument from the side of someone who has a job: the queue outside, seen from inside.
- **Strongest picture:** W4, from inside No. 2's yard by the half-shut gate: a worker's jacket and cap on a
  nail on the gatepost, his mug on an upturned crate, and through the bars, the lamp-lit queue waiting
  outside.

**Shot 14a - W4 (whole page).**
- Camera: where a worker on his break would stand, 7.2 m from the gate at the start, 1.7 m, level. Subject:
  the gate opening with the queue beyond.
- Story group: the half-shut gate leaf; the jacket and cap on the inside post; the crate with the mug and
  lunch tin against the post's foot; the nearest waiting man just outside the bars, about 6.5 m from the
  camera, lit from behind.
- Move: one slide toward the gate, 1.2 m, from "With more workers" (345.2 s) to "gate" (346.9 s).
- Events and words: "America's" (329.3 s): **AMERICA'S VERSION OF OUR RESERVE BANK**, small credit **US
  FEDERAL RESERVE**; "fewer jobs" (333.2 s): **FEWER JOBS**; "unfortunate" (335.2 s): **UNFORTUNATE,**;
  "not the goal" (336.5 s): **NOT THE GOAL** (no quotation marks); "Clara" (337.7 s): a typed name card
  **CLARA E. MATTEI**, with a small source credit **THE CAPITAL ORDER** (no portrait, no book cover);
  "argues" (342.2 s): **MATTEI ARGUES:** and on "goal" (344.5 s) **FEWER JOBS ARE THE MAIN GOAL**; "power"
  (349.8 s): **LESS POWER TO ASK FOR HIGHER WAGES**.
- Light effects: thin smoke beyond the wall, the lane's gas lamps' faint flicker. About 1.0 s a frame held,
  3.5 s during the slide.

### Page 15 - Back at the checkout (about 27 s)

- **Must teach:** a hundred-dollar basket in June 2025 cost about a hundred and four a year later, and would
  have cost about a hundred and three if petrol and diesel prices hadn't changed; petrol and diesel push up
  almost everything made or moved, in both factories; so part of what you felt came from petrol and diesel.
- **Must see:** their own basket again with the prices side by side, then petrol and diesel at both factories.
- **Strongest picture:** C1's composed frame with a tag on the basket flipping from $100 to about $104, and a
  ghost tag beside it at about $103.

**Shot 15a - C1, the composed frame (353.3 to 367.4 s).** "dollars" (356.2 s): a tag **$100, JUNE 2025**;
"later" (358.9 s): it flips to **ABOUT $104, A YEAR LATER**; "three" (366.6 s): a ghost tag **ABOUT $103 IF
PETROL AND DIESEL PRICES HADN'T CHANGED**, credit **STATS NZ** (no 4.1% or 2.9% on screen). About 0.5 s.

**Shot 15b - W3, held (367.4 to 374.3 s).** "petrol" (367.7 s): labels with thin lines to the fuel cans at
both gates, **PETROL AND DIESEL**; "both" (373.0 s): a price arrow climbs over each factory, **BOTH
FACTORIES**. About 1.0 s.

**Shot 15c - C1 (374.3 s to the page turn).** "part" (374.4 s): **PART OF IT: PETROL AND DIESEL**. About
0.5 s.

### Page 16 - Spent on what? (about 27 s, with the 4-second fade)

- **Must teach:** the rule again in the same words; the two questions to ask next time.
- **Must see:** the same picture as the first time the rule was said (so it feels like recognition), then
  their own checkout with the questions.
- **Strongest picture:** W3 with page 5's two rule cards in the same places, then the checkout, the camera
  slowly stepping back from the basket as the questions land.

**Shot 16a - W3, held (379.8 to 393.9 s).** "always" (380.6 s): **DOES NEW MONEY ALWAYS PUSH PRICES UP?**;
"No" (382.1 s): **NO.**; then page 5's cards, same words, same places, same order: "spent" (383.7 s) to
"made" (389.5 s) over No. 1, "nothing" (390.6 s) to "up" (393.3 s) over No. 2. About 1.0 s.

**Shot 16b - C1 (393.9 s to the end).**
- Move: one slide back from the basket to the plate's spot, 1.3 m, from "next time" (394.1 s) to "warning"
  (395.3 s) plus about 2 s, the reverse of page 1.
- Events and words: "Spent" (397.7 s): **SPENT ON WHAT?**, with a small line under it on "anything"
  (399.2 s): **ANYTHING SPARE TO MAKE WHAT IT BUYS?**; "who pays" (401.6 s): **WHO PAYS FOR THE CURE?**;
  held; **the 4-second fade** to dark after the last word (402.9 s).
- About 3.5 s a frame during the slide, 0.5 s held.

### The holds and the moves at a glance

| Page | Holds | Moves (one slide each, never a turn) |
|---|---|---|
| 1 | | toward the basket |
| 3 | | along the queue to No. 1's gate |
| 4 | 4-second guess hold on W2 | toward No. 2's gate |
| 5 | 2-second hold on the rule cards (W3) | |
| 6 | | toward the grocer's window |
| 7 | | toward the rent notice |
| 8 | 4-second guess hold on J1 | |
| 9 | 2-second hold on the "spare ... to make what it buys?" card (W3) | |
| 10 | 4-second guess hold on W3 | |
| 11 | | toward the half-built house |
| 12 | | toward the letter |
| 14 | | toward the gate and the queue |
| 16 | 4-second fade at the end (C1) | back from the basket |

Pages 2, 5, 8, 9, 10, 13 and 15 hold still throughout.

---

## 3. The numbers

### Plates, paintings and money

| View | Plate | Paintings | Why |
|---|---|---|---|
| W1 | 1 | 2 | slides; the queue leaves |
| W2 | 1 | 2 | slides; the queue comes and goes |
| W3 | 1 | 1 | always held; changes are own surfaces (bank window) or live (smoke) |
| W4 | 1 | 2 | slides |
| C1 | 1 | 2 | slides in (page 1) and out (page 16) |
| J1 | 1 | 1 | held |
| S1a | 1 | 2 | slides (page 11) |
| S1b | 1 | 1 | held |
| K1 | 1 | 2 | slides |
| G1 | 1 | 2 | slides |
| G2 | 1 | 2 | slides; windows light (own surfaces) |
| **Total** | **11** | **19** | |

| Spending (all on hold until you say yes) | Low (10 c a painting) | High (log 32's measured 20 to 45 c for two) |
|---|---|---|
| 19 paintings | US$1.90 | US$4.28 |
| Up to 4 composition sketches by Nano Banana Pro (only where the checker can't settle a view) | US$0.60 | US$0.60 |
| Narration (about 6,300 characters) | US$1.10 | US$1.10 |
| **Planned** | **US$3.60** | **US$5.98** |
| Repaint reserve, about 1 in 3 (lesson 97: Flux's strength varies) | US$0.60 | US$1.35 |
| **Planned with reserve** | **US$4.20** | **US$7.33** |

Under the US$12 ceiling in every case, with at least US$4.67 more for repaints before reaching it, and at
least US$12.67 of the US$20 untouched.

### New props to build by script (about 35)

- The Works: 8 waiting figures; the factory wall with two gate arches and piers; the No. 1 and No. 2 boards;
  the bank front with its lit room; NEW MONEY sacks; PETROL and DIESEL stencils; a lunch tin; a jacket and cap
  on a nail; a tin mug; the twin works at real size (adapted, not new).
- The checkout and corner shop: counter, belt, divider bar, card terminal, till, bag rack, wire basket, bread
  bag, milk bottle, butter, CHECKOUT sign; the corner shop's counter, hot-food cabinet, rice balls, tea bottle,
  milk carton, レジ sign, the drinks machine seen through the window.
- The building site: mini digger, timber packet, house frame with wrap, scaffolding, mesh fence panels and
  gate, chain and padlock, hi-vis vest, hard hat, builder's banner, two weatherboard houses.
- The kitchen: room and window, the letter and envelope, mug, phone, cardigan.
- Glasgow: the tenement block builder, the grocer's shopfront and display with tins, the factor's notice (re-
  lettered), scaffold and brick stack with tarpaulin, the blanket bundle, the re-lettered builder's cart.

### Computer time

- **Blender:** 11 plates at about 10 minutes each (about 1.8 hours); composing each view (small previews,
  three to five shot-checker runs, one finished still for the light rules) about 35 minutes a view (about 6.5
  hours); building and exporting the sets and props about 3.5 hours. **About 12 hours of Blender time**, one
  render at a time (each uses all 4 processors); builds can run beside other work.
- **Filming:** about 12,200 frames on the estimated timeline; planned for about 13,000 in case Malina reads
  slower.

  | Kind of frame | Frames (of 12,208) | Seconds a frame | Hours |
  |---|---|---|---|
  | held, nothing live | about 6,600 | about 0.5 | 0.9 |
  | held, with smoke, flames or flicker on top | about 4,400 | about 1.0 | 1.2 |
  | camera sliding or the set changing (about 40 s of film in all) | about 1,200 | about 3.5 | 1.2 |
  | **All** | **12,208** | **about 1.0 on average** | **about 3.3 on one helper** |

  With two helpers at once (about 17% faster on 4 processors), **about 2.8 hours; about 3 hours at 13,000
  frames.** Allow about one more hour for re-filming pages after the critics. If sliding frames are as slow as
  the old notice corner's (about 6 s), add about 0.8 hour. If held pictures did not work at all, every frame
  would cost about 3.6 s, about 13 hours: that is why the first test measures them.
- **Disk:** Poly Haven downloads about 0.1 GB; six .blend files about 0.5 GB; exported sets about 0.4 GB;
  plates about 0.1 GB; paintings about 0.05 GB; filming pieces and the master about 1 to 1.5 GB. **Peak about
  2.5 to 3 GB of the 8 GB free**; old filming pieces are deleted once joined.

---

## 4. The order of work, and the risks

### The order of work

1. **The cheapest test that shows the plan works (free, about half a day).** Build only what W1 needs: the
   lane and the twin works at real size, the wall and gates, the No. 1 board, 7 waiting figures, the brazier
   and lantern. Compose W1 with the shot checker; draw its plate, and a second plate without the figures,
   gates and near props. Film page 3's W1 shot (about 19 seconds) on the estimated timeline, with the plate
   itself standing in for the painting and the second plate for the behind painting. It shows, before any
   money is spent:
   - the speed: seconds a frame for held frames, held frames with fire and smoke, the slide, and the moments
     the gate swings and the men leave (pass: about 1 s held, about 4 s or less moving);
   - whether "the workers go in" reads as people going in, not ghosts (a fresh helper watches it in motion
     without being told what it shows);
   - whether the own-surface gate and board sit well in the picture, and nothing tears on the slide.
2. **The first paid step (with your yes, one approval for both):** record the narration (about US$1.10), and
   paint W1 (two paintings, about 20 to 45 cents). Check the painted men (how many, no faces, no extra people,
   painted rather than photographic), line both paintings up (`align_painting.py`), re-film the W1 shot and
   look at it in motion. This tests the plan's biggest risk first. If two tries fail, switch the queue to the
   fallback (caps and lunch tins on the coping) before painting anything else, and tell you.
3. **The rest of the Works:** W3 first (its painting becomes the style picture for all Works paintings), then
   W2 and W4; the continuity sheet.
4. **New Zealand:** the building site (S1a, then S1b with S1a's painting as its style), the checkout (C1), the
   kitchen (K1).
5. **Glasgow (G1, G2) and the corner shop (J1).**
6. **Pages:** the real word times from the recording; one page file per page; stills of every event; the camera
   check, the page-turn check; independent critics (looks, history, rules: words on screen, figures, party
   colours, Mattei marked as hers); fixes; filming in stretches under 2 hours each (`FILM_FROM`/`FILM_TO`);
   a motion check of the whole film; finishing, captions, loudness.

### Risks, and how each will be caught

| Risk | How it will be caught | What then |
|---|---|---|
| The painter gives the waiting men faces, changes how many there are, or adds people | counting figures against the plate's outlines; a helper at full size on every painting | repaint with darker backlight and plainer words; after two failures, the empty-props fallback |
| The fade of the men going in, or coming back, reads as ghosts | a fresh helper watching the free test and the painted test in motion | a quicker fade hidden in the gate's swing, or a cut to the same frame later |
| The men's painted shadows stay after they leave | stills before and after the fade; the swap area includes each man's shadow | widen the swap area to the shadows |
| Filming is slower than planned | the free test measures held, effect and sliding frames | fewer live effects on held frames, lighter sets (fewer cottages, simpler far town), fewer redraw moments |
| Own-surface gates, windows and letters look like 3D renders next to the paint | a looks helper on stills; the colour match on own surfaces (as in the notice corner) | darken and colour-match; keep them small or dim |
| The two factories don't match between views | the continuity sheet; W3's painting as every Works painting's style picture | repaint the odd one out |
| The painter garbles or invents lettering | every legible sign keeps its own surface; a helper reads every sign at full size | add the sign to the own-surface list |
| The painter stretches or shifts its picture | `align_painting.py` on every painting (log 32 found 0.65% and 3 pixels) | line up before use |
| Wrong era or place details (1915 shopfronts and notice wording, New Zealand building materials, Japanese labels) | a history helper checks every set and every line of lettering before painting (the painter copies the plate) | change the set before the paid step |
| An invented name matches a real business (the bank on the kitchen letter, the builder, the grocer, the supermarket) | a search of each name before it is used | pick another |
| Party colours during the 7 November election (the digger, vest, basket) | a helper checks the colours of every New Zealand view | change the colour; avoid large flat areas of any one party's colour |
| The quiet factory's view shows No. 2's lit gate as a second bright place | the shot checker's main rule on W1 | hide it behind No. 1's pier or slide the camera |
| W3 on page 9 breaks the main rule (the bank and the gates are apart on purpose) | the shot checker reports it | accepted on purpose and written in the check file, with the labels tying the two |
| Page 7's "builders and materials gone to the war" still rests on a source seen second-hand (the script's "Sources still to open") | the script's own check before recording | if the line changes, the stopped building site in G2 loses its label and stays as background |
| The shadow memory fault in plates (lesson 110) | reading each plate's render log, as the checker does | lower the shadows' resolution |
| A guess hold or rule hold gets cut short when the real recording lands | the page-turn check on the real timeline | the holds are written as pauses in the timeline, not as seconds in the page |
| Figures fading out snap off half way (lesson 87) | stills every 0.1 s through each fade | build them see-through from the start |
| A cloud session stops background jobs after 2 hours | filming in stretches, kept in 60-frame pieces | carry on from the last piece |

## Traps

- Never put a program's lettering on screen: every sign that can be read keeps its own surface.
- Never a figure on screen Malina doesn't say; the only numbers in the sets are "No. 1" and "No. 2" (her "the
  first" and "the second"). No price tags, lane numbers, close numbers or dates on set dressing.
- W3 always shows the two factories as first described; don't carry page 3's or page 12's changes into it.
- Paint W3 before the other Works views; it is their style picture.
- The waiting men always face away from the camera or stand against the light; never nearer than about 4 m.
- No New Zealand or Japanese banknotes or coins anywhere (they carry real people's portraits).
- Mattei appears only as a typed name card, and her view only inside MATTEI ARGUES.
