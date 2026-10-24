# Shot plan - chapter 2 for newcomers, the full redesign (one plan made from two)

Source for the story: Clara E. Mattei, *The Capital Order* (2022).

**What this is:** the plan for filming all 16 pages of "33 Script - chapter 2 - what really causes
inflation - for newcomers" (about 7 minutes) in the look you kept in log 32 ("Wow that's incredible. Yes
keep it."). Each place is a real 3D set built in Blender by script. It is drawn once from its main view
(the plate), repainted by Flux 3 in the series' painted style, and the painting is shone back onto the set
so the camera can slide without the picture tearing. Flames, flicker and smoke are drawn live on top, and
words on screen are typed cards.

Two designers wrote plans independently. **"Strongest picture"** looked for the one picture that teaches
each page. **"One world"** used as few places as possible and kept coming back to them. I judged both on
teaching first, then on how the shots will look, then on cost and computer time. **"Strongest picture" is
the spine of this plan**, and the best parts of "One world" are added page by page. Every choice is
labelled with where it came from: **[Strongest picture]**, **[One world]**, or **[new]** when it is mine.

Nothing here is built, painted or filmed, and no money has been spent. The paid steps wait for your yes.

## In short

- **6 places, 11 views, 31 shots.**
  - **The Works:** the script's "our picture", two factories side by side at the head of a lane. It has 4
    views and appears on 11 of the 16 pages.
  - **Five real places:** a New Zealand supermarket checkout, a New Zealand building site (busy, then
    stopped), a New Zealand kitchen table, a Glasgow street in 1915 (2 views), and a Japanese corner shop's
    counter in 2013.
- **The two factories look different at a glance** [One world]. The quiet factory has dark red-brown brick
  and one tall round chimney. The flat-out factory has pale buff-grey brick, two square chimneys and a water
  tank. Their gate boards say "No. 1" and "No. 2", short for Malina's "the first" and "the second"
  [Strongest picture]. So on page 12, when the flat-out factory slows and a queue forms at its gate, a
  newcomer still knows which factory it is.
- **11 plates and 19 paintings:** about US$1.90 at 10 cents a painting, up to about US$4.30 if each costs
  what log 32's did.
  - With the narration (about US$1.10) and up to four optional sketches (60 cents), the plan spends **about
    US$3.60, at most about US$6.00**.
  - With a reserve of ten repaints, it spends at most about **US$8.25**. That is under the US$12 line and
    leaves at least US$11.75 of the US$20.
- **About 1 second a frame on average, about 3 hours of filming** with two helpers at once.
  - When the camera holds still, the stage draws the set once and redraws only what moves. It already does
    this ("held shots" in `cinema-stage.js`).
  - Only about 1,200 of about 12,200 frames redraw everything.
- **9 slides in all, at most one on any page, never a turn.** Each slide lands one point.
- **People:**
  - The waiting workers are simple figure shapes that the painter turns into painted people. They are always
    seen from behind or against the light, never nearer than about 6 m, and only at the Works, where their
    number is the point.
  - Everywhere else, a person is shown by something made for a person: a hi-vis vest, a pulled-out chair
    with a cardigan, a suitcase on a step.
  - The one crowd (war workers walking to the Glasgow works) is small, far away, and can be dropped.
- **The first tests:**
  - Two are free: time the stage on the notice corner, then build the Works and film page 3 with the plates
    standing in for paintings.
  - The first paid step needs your yes. It records the narration and paints three pictures (30 to 70 cents).
    Together they test the three things nobody has tried yet: painted people, people leaving a painted
    picture, and a second view of a place painted to match the first.

## Words used here

- **Plate:** the picture Blender draws of a set from a view, a little wider than the film's frame.
- **Painting:** Flux's repaint of a plate. It is shone back onto the set.
- **Behind painting:** a second painting of the same view with the near things painted out. It is shown
  where they stood once the camera slides, or once they leave (the waiting men going in).
- **Helper plate:** a free extra plate drawn without some things (the figures, the gates). Comparing it with
  the plate shows where their painted shadows fall. It is never painted.
- **Own surface:** a thing that keeps its own sharp 3D surface instead of the painting: every sign and every
  letter (the painter garbles small print), and things that must change on a word (a gate swinging, a
  window lighting up).
- **Held shot:** the camera stays still. The set is drawn once, and only moving things (smoke, flames, cards,
  a fading figure) are drawn each frame.
- **Slide:** the camera moves in a straight line toward its subject (or back from it) at the same height. It
  starts and stops gently and never turns.
- **Story group:** the few things that tell a shot's story, placed so they touch or overlap ("07 Composing a
  shot", rule 3).
- **The main rule:** where the lines meet, the brightest parts, the warm light and the story group all fall
  in one part of the frame, the part that holds the subject ("07 Composing a shot").
- **Master painting:** the first painting of a place. Every later painting of that place is given it as its
  style picture, so they all match.

---

## How the two plans were judged, and what came from where

### Teaching: will a newcomer understand and remember each idea?

| Where "Strongest picture" teaches better | Where "One world" teaches better |
|---|---|
| One unforgettable picture per idea: the line of men's backs leading to a shut gate (spare workers), the same gate seen with nobody ahead (flat out), a nearly bare grocer's window (fewer things to buy), a suitcase under a rent notice (too few homes), a letter about the home loan on a kitchen table (loans cost more), the same building site busy and then stopped (put out of work), the queue seen from inside the gate by someone with a job (Mattei's argument) | The two factories look different at a glance, so every return is recognised at once. With identical twins (Strongest picture), page 12's slowed flat-out factory with a queue at its gate would look exactly like the quiet factory |
| Page 9 shows the money sitting in a bank and both gates untouched. It doesn't suggest which factory Japan was like. One world's cut to the quiet factory's queue at "never reached the factory" would quietly suggest Japan had spare workers, which the research ledger doesn't say | The cards PICTURE TWO FACTORIES, A REAL CASE and IN OUR PICTURE mark what is imagined and what is real. That is the script's own teaching device ("Now a real case" is the one line it says must never be cut) |
| The busy site on page 2 and the stopped site on page 13 make a before and after that the viewer remembers | The warning is a thing in the world: a newspaper headline at the checkout, which comes back at the end with "next time you hear the warning" |
| Few people drawn, so less goes wrong | Rent strike placards appearing in Glasgow's windows count the refusing families. War workers walking up the street to a smoking munitions works show "crowds of war workers" and a flat-out factory in one picture |

What "One world" does less well for teaching:
- **The New Zealand street up to an invented Reserve Bank tower.** It teaches little that a typed card
  doesn't, puts a real institution's name on an invented building, and is the biggest build in either plan.
- **The Tokyo bank's back office stacked with paper cash.** It is literal, but paper cash misleads about
  what "new money sitting in the banks" was, and it costs a new room and three paintings.
- **Painted figures fading from 5 to 10.** This adds risk for little gain.

### How the shots will look ("07 Composing a shot")

- **Strongest picture's camera spots are a person's spots, and people make the lines.**
  - The quiet gate is seen from the end of the queue: the backs lead the eye to the gate (rules 1 and 2).
  - The flat-out gate is seen from exactly the same spot with nobody ahead.
  - The view from inside the yard puts the cause (the queue) and the person it affects (a jacket on a nail)
    in one column.
- **One world's main views put the subject a long way off.** The two gates are 55 m away, and the Reserve
  Bank's entrance about 100 m. Both are small on a phone, so this plan keeps Strongest picture's 30 m.
- **Strongest picture breaks the main rule once, on purpose:** the lit bank and the untouched gates on
  page 9. The labels tie the two together. It is kept, and recorded in the check file.
- **One world's rule "a state changes only while the camera holds"** is adopted everywhere.

### Cost and computer time

| | Strongest picture | One world | This plan |
|---|---|---|---|
| Places / views / shots | 6 / 11 / 29 | 4 / 10 / 32 | 6 / 11 / 31 |
| Plates / paintings | 11 / 19 | 13 / 24 | 11 / 19 |
| Paintings at 10 cents | US$1.90 | US$2.40 | US$1.90 |
| Filming (two at once) | about 3 h | about 3.7 h | about 3 h |
| What the filming time rests on | held shots, which the stage already has | turning off depth blur, the glow pass and shadow maps, which were never timed on a painted set | held shots; the settings are timed in the free test and kept only if they help |

**Verdict:** Strongest picture is the spine. It teaches better, uses fewer paintings and rests on something
the stage already does. These parts of One world are grafted on:
1. distinct factory shapes and typed name tags on every return;
2. the cards PICTURE TWO FACTORIES, A REAL CASE and IN OUR PICTURE;
3. the warning as a newspaper headline at the checkout;
4. places seen from each other: a dim petrol canopy through the checkout window, and a closed bank across
   the street from the Japanese shop;
5. the munitions works and walkers in Glasgow;
6. the rent strike placards;
7. the FOR RENT board on page 11;
8. the painting chain: a master painting as image 2, a colour check, and second paintings used only where
   they differ;
9. the free timing test of the stage settings;
10. "a state changes only while the camera holds";
11. the Glasgow fallback (the pit village street, dressed for 1915).

---

## People: how "workers wait at the gate" and crowds are shown

"Workers wait at the gate" is the chapter's central picture:
- its presence defines the quiet factory (page 3);
- its absence defines the flat-out factory (pages 4 and 11);
- its return is the cure (page 12);
- it is Mattei's argument (page 14).

A newcomer has to see people waiting, and see their number change. So:

| Where | How | Why |
|---|---|---|
| The Works: the quiet factory's gate (page 3); the small queue at No. 1 in the both-gates view (every time); the flat-out factory's gate once it slows (page 12); outside its gate seen from the yard (page 14) | **Simple figure shapes that the painter turns into painted people** [both plans]. Eight standing figures built by script, in five poses (hands in pockets, arms folded, leaning on the wall, one hand on a gate bar, one stooped to the brazier) [poses from One world]. Long work coats, caps, dull browns and greys. Always backs to the camera, or against the lamp-lit lane with their faces in shadow. **The nearest is never closer than about 6 m** [new: Strongest picture said 4 m, One world 10 m]. At 6 m a figure is about a quarter of the frame's height | Waiting has to be seen and counted. An empty bench can't show waiting and can't show "more" |
| Glasgow, the street to the works (pages 6 and 7) | **About eight small walking figure shapes far up the street** (at least 25 m away), backs to us, men and women with bundles, walking toward the munitions works [One world, made smaller: 8, not 18] | "Crowds of war workers had come to Glasgow", and a works where everyone has a job. The first to go if painted people fail; the shot still works with the works' glow, smoke and poster |
| Glasgow, the close mouth (page 7) | No people. A suitcase with a blanket bundle tied on top on the step under the rent notice [Strongest picture]; rent strike placards appearing in the windows [One world] | The suitcase is a newcomer with nowhere to go; the placards count the families |
| New Zealand and Japan | No people [both plans]. The hi-vis vest on the digger's door and the hard hat on the timber; the vest hung on the locked fence and gumboots by the post; the chair pushed back with a cardigan and glasses on the letter; the basket on the counter | Present-day painted people risk looking like real, recognisable people, and close painted faces edge toward portraits |
| The Works after the men go in | The brazier still burning by the empty wall, a lunch tin on the coping [Strongest picture] | "They've just gone in" (the notice corner's empty-chair device, rule 9) |
| Inside the flat-out factory's yard | A worker's jacket and cap on a nail by the gate, his mug on an upturned crate [Strongest picture] | Someone with a job |

**How the figures come and go.**
- The figures are near things in the projection. The behind painting has them painted out.
- A helper plate drawn without the figures and gate leaves shows where their painted shadows fall. That area
  takes the behind painting too, so the shadows leave with the men [Strongest picture's point, made with a
  free helper plate: new].
- The figures are built see-through from the start and fade over 1.2 seconds, so they don't snap off
  halfway (lesson 87).
- They are drawn as moving things over the held set, so a fade doesn't redraw the whole set.

**Painter words for figures** [both plans]: "Keep every figure exactly where and as it is: a dark painted
worker seen from behind. No faces, no new people, no details added."

**What could go wrong, and how it is caught:**
- The painter adds faces, turns figures round, adds or loses people, or makes them look photographic or like
  shop dummies. Caught by:
  - counting the figures in each painting against the plate's figure outlines (the shot checker lists each
    figure as a prop);
  - a helper looking at every painting at full size.
- The fade reads as ghosts. Caught by a fresh helper who watches it in motion without being told what it
  shows.
- The Glasgow walkers read as soldiers marching. Prevented by no rifles, no step in time, mixed men and women
  with bundles. The history helper checks.

**Fallbacks, in order:**
1. Repaint with plainer words and darker backlight (10 cents).
2. Keep the figures as their own surfaces: dark shapes with a rim of lamplight, not painted [One world].
3. No figures at all: caps and lunch tins along the wall's coping and empty stools by the gate, with "more
   workers" shown by more stools [Strongest picture and One world]. The fade becomes the caps
   disappearing.

The Glasgow walkers go first, at step 1.

---

## 1. The places

Every view keeps a dim, quiet band across the top of the frame (sky, a dark wall or a ceiling) for the typed
words, with anything that must be read left of 0.90 across (rule 12).

The lettering rules apply to every set:
- Every sign carries real lettering, era-correct, as its own surface.
- In-world lettering carries names, or a short form of what Malina says. It never carries a figure she
  doesn't say: no prices, door numbers, lane numbers, dates, sizes or phone numbers.
- Every invented name is searched before it is built, and changed if a real business of that name exists in
  that place.
- No logos, no flags, no shop chain's or bank's colours, and no large flat areas of a party's colour.

| Place | What and when | Views (plates) | Paintings | Pages |
|---|---|---|---|---|
| A. The Works | imagined, undated: two factories at the head of a short lane, dusk | W3 both gates, W1 No. 1's gate, W2 No. 2's gate, W4 No. 2's gate from inside the yard | 1 + 2 + 2 + 2 = 7 | 3, 4, 5, 6, 9, 10, 11, 12, 14, 15, 16 |
| B. The checkout | New Zealand, 2025-26, a small suburban supermarket, evening | C1 | 2 | 1, 11, 15, 16 |
| C. The corner shop | Japan, 2013, a family-run corner shop's counter at night (built from B's script) | J1 | 1 | 8, 9 |
| D. The building site | New Zealand, a house going up: busy (2020-22), stopped (2026), dusk | S1a, S1b | 2 + 1 = 3 | 2, 10, 11, 13 |
| E. The kitchen | New Zealand, 2022-23, a kitchen table at night | K1 | 2 | 12, 13 |
| F. The Glasgow street | Glasgow, 1915, a tenement street at dusk | G1 street to the works, G2 close mouth | 2 + 2 = 4 | 6, 7 |
| | | **11 plates** (plus 2 free helper plates) | **19** | |

### A. The Works (the model: "our picture")

**What it is:**
- A short cobbled lane of terraced cottages and gas lamps, ending at one long factory wall.
- The wall has two iron gates in brick arches, about 7 m apart either side of a shared brick pier. That keeps
  both gates inside the middle 0.40 of the frame from 30 m.
- Behind the wall stand two works side by side, each with its chimney rising above its own gate, so each
  factory makes an upright column (rule 7).
- Halfway up the lane on the left (the quiet side) stands a small stone-fronted bank with a barred window
  [Strongest picture].
- Beyond the roofs is the far town: chimneys, a gasholder, a spire.

**Era and place:** none on purpose. It is "our picture", not a real case: sign-writer's lettering, gas lamps
and brick that could be any industrial town of the early twentieth century [both plans].

**Fixed looks, the same in every view** [One world's identities; colours changed here: new]:

| | The quiet factory (No. 1, always on the left) | The flat-out factory (No. 2, always on the right) |
|---|---|---|
| Brick | dark red-brown | pale buff-grey (`white_sandstone_bricks`, toned) |
| Chimneys | one tall round chimney | two square chimneys and a water tank on a steel trestle |
| Roof | four-bay sawtooth | long pitched shed roofs with a roof lantern |
| Gate | dark iron, chained and padlocked when quiet | dark iron |
| Gate board | "No. 1", cream sign-writer's lettering on near-black | "No. 2", the same |

The two factories differ by shape first (round against square chimneys, a water tank), because shapes
survive the painter and a phone screen better than colours. Both gates are dark iron and the boards
near-black: no large red, blue, green or yellow-and-black areas (the election is on 7 November).

**States** (the same settings in every view, kept in one shared page module, `works-effects.js`)
[Strongest picture]:

| | windows | chimney | gate | at the gate |
|---|---|---|---|---|
| No. 1 quiet | dark | cold | shut, chained | 7 men waiting, a brazier, a lit lantern |
| No. 1 working (page 3, after "go in") | lit | smoking | open | nobody; the brazier still burning, a lunch tin on the coping |
| No. 2 flat out | blazing, flickering | heavy smoke from both | wide open, crates stacked against the leaf, a handcart half out | nobody; the gateway's warm light on the empty pavement |
| No. 2 slowed (page 12 on) | a third lit | thin smoke from one | half shut | 8 men waiting |

The both-gates view (W3) always shows the two as first described: No. 1 quiet, No. 2 flat out. The changes
on pages 3 and 12 happen in the gate views and don't carry over into it.

**The views:**
- **W3, both gates (the main view, painted first).**
  - Camera: on the right-hand pavement at the lane's mouth, about 30 m from the wall, standing eye height
    (about 1.7 m), level. Turned so the kerbs, gutters and rooflines meet on the shared pier between the
    gates.
  - Two columns: on the left, No. 1's cold round chimney, its shut gate, the brazier and a small queue of 7;
    on the right, No. 2's two smoking chimneys and tank, the open lit gateway, crates and the fuel drums.
  - The bank is on the left, dim, its window dark until page 9.
  - Brightest part: No. 2's gateway, beside the meeting point. The brazier is second.
- **W1, the quiet factory's gate.**
  - Camera: on the pavement at the wall's foot, left of No. 1's gate, about 1 m out from the wall, eye height,
    level. This is where the next man looking for work would stand: 13 m from the gate at the slide's start,
    11.8 m at its end [Strongest picture; distances lengthened so the nearest man is about 6 m away: new].
  - The queue's line of backs runs along the wall and leads the eye to the shut gate (rule 1, made by
    people).
  - Story group: the shut gates with chain and padlock; the brazier against the gate's left pier, its rim
    clearly overlapping the pier's base; the first man beside it with one hand on a gate bar; six more back
    along the wall, each overlapping the one in front; a lit lantern and a lunch tin on the coping above the
    third man.
  - Beyond the gate, far along the wall: the flat-out factory's two square chimneys smoking small and dim
    above the wall. They are the same column as the gate, like the pithead behind the notice. They tell the
    viewer which side they're on [new, after One world's "neighbours at the edge of the frame"]. No. 2's lit
    gateway itself stays hidden behind No. 1's pier, or it would be a second bright place [Strongest
    picture].
- **W2, the flat-out factory's gate.**
  - The mirror of W1: right of No. 2's gate, the same distances, the same lens and the same gate furniture,
    so a cut between the two compares like with like [both plans].
  - From exactly where a waiting man would stand, but nobody is ahead of us.
  - Beyond, small: the quiet factory's single round chimney, cold.
- **W4, No. 2's gate from inside the yard.**
  - Camera: where a worker on his break would stand, 7.2 m from the half-shut gate at the slide's start and
    6.0 m at its end, level.
  - Story group: the half-shut gate leaf; the jacket and cap on a nail on the inside post; an upturned crate
    with a tin mug and lunch tin against the post's foot.
  - Through the bars: the lamp-lit lane and the queue of 8 outside, faces in shadow, the nearest just
    outside the bars at about 6.5 m [Strongest picture].

**Reused (files):**
- `paper-film/blender/pit-village/build_street.py`: the cobbled lane, kerbs, pavements, cottages and gas
  lamps, run without the colliery, with a gentle slope and a 7 m lane.
- `paper-film/blender/build_factory.py`, run twice:
  - `--brick red --office left` for No. 1, and `--brick yellow` (toned to buff-grey) `--office right` for
    No. 2;
  - it gets a size setting that scales positions and re-tiles every texture at true scale, because scaling
    the old model would give giant bricks [One world];
  - it gets two new options: no water tank for No. 1, and two square chimneys for No. 2;
  - its blank sign board is lettered or removed (decision 34);
  - it already joins parts that share a material (about 19 pieces instead of 232), which keeps drawing
    cheap.
- `paper-film/blender/build_town.py`: the far town, at the same scale. The old models in
  `assets/models/inflation-chapter-2/` stay as they are.
- From `assets/models/pit-village/props/`:
  - `iron-gates-pair.glb` (both gates), `brazier-drum.glb`, `hurricane-lantern.glb`;
  - `gas-lamp-post.glb`, `gas-lamp-wall-bracket.glb`;
  - `handcart.glb`, `wooden-chest.glb` and `wooden-chest-lettered.glb` (the crates), `wooden-barrel.glb`,
    `dustbins.glb`.
- In `paper-film/blender/pit-village/props/build_scripted_props.py`: the coal-sack builder (re-stencilled)
  and the colliery name board's builder (re-lettered).
- `set_dressing.py` (placing props, light linking, export) and `assemble_notice_corner.py` as the pattern for
  each view's assembly script.
- Surfaces in `assets/models/pit-village/textures/`: `red_brick`, `castle_brick_02_red`,
  `large_sandstone_blocks`, `square_cobblestone`, `roof_slates_03`, `rusty_metal_02`, `dusk_sky`, and the lit
  and dark window pictures.

**Built new by script, with the lettering each carries:**
- the factory wall, with two brick gate arches, stone copings and piers;
- two gate boards, **"No. 1"** and **"No. 2"** [Strongest picture];
- the bank front: stone, a barred window with a shallow lit room behind it (own surface, dark until page 9),
  and a brass plate **"BANK"** [Strongest picture];
- sacks in the bank's room stencilled **"NEW MONEY"**: re-stencilled coal sacks [Strongest picture];
- two steel drums by each gate stencilled **"PETROL"** and **"DIESEL"**, dull grey-black, never red or green
  (page 15) [Strongest picture's fuel cans, as drums: a jerrycan is a later design];
- goods crates stencilled **"THIS WAY UP"** [One world];
- a chain and padlock;
- 8 figure shapes in 5 poses;
- a lunch tin, a jacket and cap on a nail, a tin mug.

**Fetch from Poly Haven (free for any use; names checked in Poly Haven's list):**
- model `hand_truck` (No. 2's yard);
- surfaces `white_sandstone_bricks` (No. 2, toned buff-grey) and `large_red_bricks` (No. 1's piers).

**Light:** the notice corner's dusk (sky brightness about 1.4 to 1.96). The people's own lights:
- a gas lamp on each gate pier;
- the brazier and the lantern at No. 1;
- No. 2's windows and lit gateway;
- the bank's window on page 9.

**Plates and paintings:** 4 plates, plus 2 free helper plates (W1 and W2 drawn without the figures and gate
leaves, to find their shadows). 7 paintings:
- W3: 1 (always held);
- W1: main (quiet, with the queue) and behind (figures, gate leaves and near props painted out, the yard
  painted in);
- W2: main (with the queue, used for the slowed state) and behind. The flat-out state is the main painting
  with the figures' and gates' area taken from the behind painting. That is a free image step
  (`composite_fill.py` with the helper plate's mask), not another painting;
- W4: main and behind.

### B. The checkout (New Zealand, 2025-26)

**What it is:** one checkout lane of a small suburban supermarket in the evening: the belt, the till, the card
terminal on its stand, the bag rack. Behind them are the ends of two aisles and the window to the car park
at dusk. Across the road, small and dim through the window, is a petrol station's canopy [One world's "places
you can see from each other"; kept dimmer than the basket].

**Main view (C1)** [Strongest picture]:
- Camera: where the shopper stands at the end of the belt, about 1.6 m, level, looking along the belt to the
  till. The plate is drawn from 1.3 m further back, where page 1's slide starts.
- Lines meet: the belt's edges, the counter edge and the rows of ceiling lights meet at the basket's far
  corner, beside the newspaper.
- Columns: the lane lamp and the CHECKOUT sign at the top; the headline and the till in the middle; the
  basket at the bottom.

**Story group:**
- a grey wire basket on the belt holding bread in a paper bag, a bottle of milk, kiwifruit, apples and a
  block of butter, bananas hanging over its rim;
- the divider bar against the basket's front;
- the newspaper rack at the counter's end, its corner overlapping the basket's far side, the top paper's
  headline facing us [One world];
- the card terminal beyond, its keypad turned away from the camera (no digits) [One world].

A warm light over the belt makes the basket the brightest thing. The newspaper is slightly greyed, so it
comes second (rule 5).

**Built new by script, with lettering:**
- the counter, belt, divider bar, card terminal (screen dark), till, bag rack and wire basket;
- groceries labelled **"BREAD"**, **"MILK"**, **"BUTTER"**, with no sizes or prices;
- a hanging **"CHECKOUT"** sign with no lane number;
- the shop's invented name on the window, searched first;
- the newspaper rack. The top paper has an invented masthead (One world proposes "THE HILLSIDE HERALD", to be
  checked against real New Zealand papers). Its headline is **"NEW MONEY: PRICES WILL GO UP"**, a short form
  of Malina's "If new money is created... prices will go up" [new wording; One world's headline put words in
  quotation marks];
- the petrol canopy's fascia **"PETROL · DIESEL"**, with no brand and its price board edge-on.

There are no price tags on the shelves. Everything is in neutral greys and wood: no supermarket chain's green,
red or yellow.

**Fetch from Poly Haven:**
- models `food_kiwi_01`, `food_apple_01`, `bananas`, `lemon`, `food_avocado_01`, `steel_frame_shelves_01`,
  `mounted_fluorescent_lights`, `cardboard_box_01`, `plastic_crate_01`;
- surfaces `large_floor_tiles_02`, `painted_plaster_wall`, `ceiling_interior`.

**Light:** evening. Cool shop lights, half of them off for closing time; a warm lamp over the belt (the
people's own light, rule 6); dusk blue in the window.

**Plates and paintings:** 1 plate; 2 paintings (main and behind: page 1 slides in, page 16 slides back out).

### C. The corner shop (Japan, 2013)

**What it is:** the counter of a small family-run corner shop at night, not a chain store, so no chain's
coloured stripes [new]. It has the till, a glowing hot-food cabinet and shelves behind. Through the window,
across the night street, is a bank branch with its shutter down and its small cash-machine corner lit
[new, after One world's bank: the real case's banks are seen in Japan, the model's bank in the Works].

**Main view (J1):** where the customer stands at the counter, about 1.6 m, level. It is built from B's script,
so it rhymes with page 1: another country's basket at another checkout [Strongest picture].

**Story group:** a basket on the counter with rice balls, a bottle of tea and a carton of milk, touching the
till's edge; a change tray in front of it; the hot-food cabinet against the till's other side.

**Built new by script (a second dressing of B's script), with lettering in correct Japanese, read by a helper
who reads Japanese:**
- labels **おにぎり** (rice ball), **お茶** (tea), **牛乳** (milk);
- a small **レジ** (checkout) sign over the counter, the same object as page 1's "CHECKOUT" in another
  country;
- across the street: **銀行** (bank) on the shutter's fascia and **ATM** at the lit corner. No bank's name.

There is no drinks machine (its buttons would show prices), no prices and no shop chain's name.

**Fetch from Poly Haven:**
- models `plastic_crate_02`, `steel_frame_shelves_02`, `modular_electricity_poles`, `modular_electric_cables`
  (outside), and `mounted_fluorescent_lights` (shared with B);
- surface `interior_tiles`.

**Light:** night. White shop light, and the hot-food cabinet's orange glow on the basket. The bank across the
street is dim, but brighter than the street around it.

**Plates and paintings:** 1 plate; 1 painting (held only).

### D. The building site (New Zealand, 2020-26)

**What it is:** a suburban section where a timber-framed house is going up (pine frame, building wrap,
scaffolding), behind temporary mesh fence panels, between finished weatherboard houses with corrugated iron
roofs. It is the one place where "workers, materials and machines" are New Zealand things [Strongest
picture].

**Main view (S1):** on the footpath outside the fence, at the fence gate, about 1.7 m, level. Turned so the
fence line, the kerb and the frame's top plate meet at the gate's far post.

**State a, busy (pages 2, 10, 11):**
- The gate is open. Just inside it is the story group, all touching: a mini digger parked with its bucket on
  the ground; a strapped packet of fresh timber against its track; the hi-vis vest hanging on the digger's
  door; a hard hat on the timber.
- The site's work light is on.
- The neighbour's fence carries a **"FOR RENT"** board (own surface, hidden until "rents" on page 11) [One
  world].
- On page 10 only, a small **"PLEASE SANITISE YOUR HANDS"** sign is on the gate (own surface, the 2020 marker)
  [One world, moved here].

**State b, stopped (2026, page 13)** [Strongest picture]:
- The gate is shut with a chain and padlock.
- The hi-vis vest hangs over the fence rail on our side, with gumboots by the post.
- The digger is gone, leaving a flattened patch. The timber is grey under a torn cover.
- The frame is no further on, the work light is off, and grass grows along the fence.

**Built new by script, with lettering:**
- the mini digger, faded orange, with no maker's name;
- the timber packet and the house frame with wrap (an invented wrap maker's name, searched first);
- scaffolding, mesh fence panels with feet, the fence gate, chain and padlock;
- the hi-vis vest (orange, never yellow-and-black) and the hard hat (white);
- the builder's banner on the fence, an invented builder's name only (searched first);
- two weatherboard neighbours, the FOR RENT board (plain, no phone number), the sanitise sign, and the torn
  cover.

**Fetch from Poly Haven:**
- models `rubber_boots` (gumboots), `cement_bag` (replace any printed brand with "CEMENT"), `security_light`
  (the work light), `ladder_sectioned_01`, `sledgehammer_01`, `portable_generator`;
- surfaces `weathered_plank_siding`, `corrugated_iron`, `worn_corrugated_iron`, `plywood`, `coated_pine`,
  `oriented_strand_board`, `raked_dirt`, `concrete_pavement`, `clean_asphalt`, `gravel`.

**Light:** dusk. In state a, the work light (warm white) is on the group and a neighbour's porch light is on.
In state b there is only the street lamp and the porch light, so it is colder.

**Plates and paintings:** 2 plates; 3 paintings:
- S1a main and behind (page 11 slides);
- S1b, painted with S1a's painting as its style picture. Then only the parts where its plate differs from
  S1a's are taken from it, so everything else is the same picture to the pixel [the patching idea from One
  world].

### E. The kitchen (New Zealand, 2022-23)

**What it is:** a small kitchen at night. A table stands by a window (a dark garden, a neighbour's lit
window), with a pendant lamp over the table and the bench with a kettle on the camera's side [Strongest
picture].

**Main view (K1):** standing at the kitchen bench, about 1.6 m, level, 2.6 m from the table at the slide's
start and 1.4 m at its end.

**Story group:** the opened letter from the bank, its torn envelope under it, reading glasses on its corner, a
mug against the glasses, a phone face down; the chair pushed back at an angle with a cardigan over it.

**Built new by script, with lettering:**
- the room, the window and the bench;
- the letter (own surface): **an invented bank's name** (searched against every New Zealand bank, and never a
  bank's colours), **"Your home loan"** and **"Your new interest rate"**, with no figures and no date;
- the envelope, mug, phone and cardigan.

**Fetch from Poly Haven:**
- models `dining_table`, `dining_chair_02`, `round_spectacles`, `vintage_electric_kettle`,
  `modern_ceiling_lamp_01`, `potted_plant_01`;
- surfaces `laminate_floor`, `painted_plaster_wall`.

**Light:** night. The pendant lamp is warm on the letter, the brightest thing; the window is blue-black.

**Plates and paintings:** 1 plate; 2 paintings (main and behind: page 12 slides).

### F. The Glasgow street (1915)

**What it is:**
- A level street of four-storey red and blond sandstone tenements, with shops at street level, arched close
  entrances, granite setts and gas lamps.
- At the far end, about 120 m away, stands the high wall and arched gate of a munitions works, lit and
  smoking [One world]. Its shape is unlike both model factories: a blank wall, tall shed roofs with a
  furnace glow, and several thin iron stacks (not a sawtooth roof or one round chimney, so it isn't taken for
  the quiet factory).
- Further along the right-hand row stands a tenement started and left: scaffold poles, a brick stack under a
  tarpaulin, and a builder's handcart [both plans].

**The views:**
- **G1, the street to the works (page 6, and the start of page 7)** [One world's view, with Strongest
  picture's grocer as its near subject: new combination].
  - Camera: on the right-hand pavement, about an arm's length in from the kerb, eye height, level.
  - The setts, kerbs and cornices meet at the works' arched gate, just left of the near story group, the
    notice corner's own composition.
  - Near right is a corner grocer's shop whose angled corner window faces the camera.
  - Story group: the tiered display almost bare (three labelled tins on a lot of empty shelf); an empty
    wicker basket against the stand's foot; a slumped flour sack against the door frame; through the glass,
    the brass till in the shop's gas light; and, pasted on the pilaster beside the window and overlapping
    its frame, a text-only recruiting poster, with a gas lamp above it.
  - Up the street: about eight small walking figures heading for the works.
  - Two halves of the page in one picture: no spare workers (the poster, the works flat out, people going to
    work) and fewer things to buy (the bare window, the till still there).
- **G2, the close mouth (page 7)** [Strongest picture].
  - Camera: on the pavement where a neighbour would stand, about 7 m down the street from the close, near the
    kerb, level. Turned so the kerb, string courses and gutters of both sides meet at the close's arch edge.
  - Story group: the factor's notice on the pilaster at the close's edge; directly below it on the step, a
    suitcase with a blanket bundle tied on top; the close's gas bracket just inside the arch, lighting the
    notice from the side and below.
  - On the quiet side: the abandoned half-built tenement.
  - The tenement windows on both sides keep their own glass (own surfaces), so they can light in a ripple
    and show placards.

**Reused:**
- `build_street.py`: setts, kerbs, flagstones, gutters, `build_sash_window`, `build_front_door`, chimney
  stacks, slate roofs, downpipes, gas lamps; the cottage shell code, raised to four storeys with ashlar
  fronts [One world].
- `build_factory.py`'s parts for the works' sheds behind its wall.
- The notice-paper builder in `props/build_scripted_props.py`, for the factor's notice and the poster.
- Props: `gas-lamp-post.glb`, `gas-lamp-wall-bracket.glb`, `handcart.glb` (re-lettered), `wicker-basket-tray.glb`,
  `wooden-chest.glb`, `dustbins.glb`, `milk-can.glb`.
- Surfaces: `square_cobblestone`, `large_grey_tiles`, `roof_slates_03`, `stone_brick_wall_001`,
  `red_brick`, `large_sandstone_blocks`.

**Built new by script, with lettering (every line checked by the history helper before building):**
- a tenement block builder: four storeys, sash windows with own-surface glass, close arches with glazed tile
  walls inside, shopfronts;
- the corner grocer's fascia **"W. ANDERSON · FAMILY GROCER"** (invented, searched); tins **"TEA"**,
  **"COCOA"**, **"SYRUP"**;
- the recruiting poster, text only, no portrait, no flag, in the wording of a real 1914-15 text-only poster.
  The history helper confirms it from a source first. One world proposes "YOUR KING AND COUNTRY NEED YOU /
  ENLIST TO-DAY / GOD SAVE THE KING";
- the munitions works' wall and arched gate, lettered with an invented engineering company's name (searched)
  and **"WORKS ENTRANCE"**;
- the factor's notice: **"NOTICE TO TENANTS. Take notice that the Rents of these Houses will be Increased. By
  Order, THE FACTOR."** No figures, no date, no names [Strongest picture];
- the half-built tenement: walls to the second floor, timber scaffold poles lashed with putlogs, a few planks
  missing, weeds; a builder's board **"J. LAIRD · BUILDER"** (invented, searched);
- the brick stack and tarpaulin; the suitcase bundle;
- twelve rent strike placards in hand-painted capitals [One world]. The wording comes only from a 1915
  photograph the history helper confirms (for example "RENT STRIKE" and "WE ARE NOT PAYING INCREASED RENT");
  otherwise **"RENT STRIKE"** alone. Never WON, never RENTS FROZEN;
- about eight walking figure shapes (optional);
- no close numbers, house numbers or street names.

**Fetch from Poly Haven:**
- models `CashRegister_01` (the till: check its look and build one by script if it looks modern),
  `vintage_suitcase`;
- surfaces `red_sandstone_wall`, `sandstone_blocks_05`, `long_white_tiles` (the close's tiles).

**Light:** November dusk. Street gas lamps, the close's gas bracket, the grocer's gas mantle inside, the
works' gate and furnace glow at the end, and the tenement windows (lit live on page 7).

**Plates and paintings:** 2 plates; 4 paintings (G1 main and behind, G2 main and behind).

**If Glasgow runs long:** page 6 can use the pit village street, already built, dressed for 1915 with the
poster and a bare shop window [One world]. Page 7 still needs the tenements.

---

## 2. The shots, page by page

**How to read each shot:**
- **Camera:** each view's spot is in section 1: a person's spot, eye height, level, never turning.
- **Move:** none, or one slide. A slide lasts about 3 to 4 seconds, starts and stops gently, and stops on the
  view's composed frame. Each slide says why it is essential (your rule: "still unless it's essential to land
  an important point").
- **Events:** each starts on the quoted spoken word. A word spoken more than once on the page is asked for by
  its count, for example "spent" (2). Times in brackets are from the estimated timeline
  (`film-kit/examples/inflation-chapter-2-newcomers/timeline-estimated.json`); the events follow the real
  recording, because they are tied to words.
- **Words on screen:** short forms of what Malina says on that page, typed in the kit's plain heavy type
  (`graphics.js`: `hook`, `placeTitle`, `credit`, `counter`, `bars`, `lineChart`) in the dim top band, left
  of 0.90 across. The only figures are ones she says. Small source credits (STATS NZ, US FEDERAL RESERVE, THE
  CAPITAL ORDER) carry no figures.
- **A state changes only while the camera holds** [One world].
- **Cost of a frame on this computer** [Strongest picture's figures, from the stage's own measurement on the
  notice corner: 3.6 seconds a frame drawn whole, of which 3.1 is the painted set]:
  - **held, nothing live:** about 0.5 s;
  - **held, with smoke, flames or flicker drawn on top:** about 1.0 s;
  - **moving or changing:** about 3.5 s, while the camera slides or the set changes.
  - Gates swinging, windows lighting and figures fading can be drawn as moving things over the held set,
    which is cheaper, but they are budgeted here as full redraws to be safe.
- **Between pages:** the series' page peel, 0.3 s after the last word, except where the next page continues
  the same frame (4 into 5, 8 into 9), which runs on with no join. **Inside a page:** plain cuts.

### Page 1 - The question (1.1 to 26.9 s)

**Must teach:** inflation is prices in general going up, the whole basket; the warning; why it matters (the
cure makes many loans cost more and can put people out of work).

**Shot 1a - C1, the checkout (the whole page)** [Strongest picture, with One world's headline].
- Subject: the basket. Story group as in place B, with the newspaper's headline touching the basket.
- Move: one slide of 1.3 m toward the basket, from "same" (3.4 s) to "inflation" (7.3 s). Why: we step up to
  our own basket.
- Events and words on screen:
  - "felt" (1.4 s): the picture fades up from dark.
  - "inflation" (7.3 s): **INFLATION**. "general" (8.9 s): **PRICES IN GENERAL, GOING UP**.
  - "whole" (10.8 s): an up-arrow tag springs up beside every item at once (arrows, no prices), with **THE
    WHOLE BASKET** [Strongest picture].
  - "warning" (12.8 s): the tags fold away; a small label with a thin line to the headline, **THE WARNING**
    [new]. The in-world headline NEW MONEY: PRICES WILL GO UP carries the warning itself [One world]. It must
    measure at least about 40 pixels a letter on the composed still. If it doesn't, the typed card **NEW MONEY
    → PRICES UP?** goes up on "prices" (2) (15.8 s) instead [Strongest picture].
  - "always" (17.7 s): **IS THAT ALWAYS TRUE?**
  - "cure" (22.4 s): **THE USUAL CURE →**. "loans" (23.3 s): **MANY LOANS COST MORE →**. "out" (25.9 s):
    **OUT OF WORK**.
- Light effects: one far fluorescent tube flickers (about 0 s). About 0.5 s a frame held, 3.5 s during the
  slide.

### Page 2 - Who can create new money (28.4 to 46.6 s)

**Must teach:** here, the Reserve Bank can create new money and tries to stop prices going up too fast.
Economists who study how modern money works argue our government can't run out of its own money, but it can
run out of workers, materials and machines.

**Shot 2a - S1a, the building site (busy), held** [Strongest picture].
- Subject: the three things touching just inside the open gate: the digger, the timber against its track,
  the vest on its door and the hard hat on the timber.
- Move: none.
- Events and words on screen:
  - "Zealand" (30.7 s): **NEW ZEALAND**. "Reserve" (31.6 s): **THE RESERVE BANK** (typed, no logo); "can" (2)
    (32.3 s): **CAN CREATE NEW MONEY**.
  - "tries" (33.4 s): **TRIES TO STOP PRICES GOING UP TOO FAST**.
  - "economists" (36.5 s): **ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS**. "argue" (39.6 s): **THEY
    ARGUE:**; "money" (3) (42.2 s): **OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY**.
  - "But" (43.0 s): **BUT IT CAN RUN OUT OF...**, then a label with a thin line to each thing: "workers"
    (44.2 s) **WORKERS** → the vest and hat; "materials" (45.0 s) **MATERIALS** → the timber; "machines"
    (45.7 s) **MACHINES** → the digger.
- Light effects: none live. About 0.5 s a frame.
- Not used: One world's street up to an invented Reserve Bank tower (see the judging section). The Reserve
  Bank is a typed card, as the script's own picture notes had it.

### Page 3 - The quiet factory (48.1 to 74.0 s)

**Must teach:** the two-factories picture, each standing for a whole country. The quiet factory has spare
workers. New money spent there gets more things made, so prices barely move.

**Shot 3a - W3, both gates, held (48.1 to 55.1 s)** [Strongest picture; cards from One world].
- Subject: the two gates side by side.
- Events and words on screen:
  - "Picture" (48.1 s): **PICTURE TWO FACTORIES** (it marks the picture as imagined) [One world].
  - "country" (51.3 s): **EACH ONE = A WHOLE COUNTRY:**, then word by word "workers" (1) (52.7 s),
    "materials" (53.4 s), "machines" (1) (54.1 s): **WORKERS, MATERIALS, MACHINES**.
- No name tags yet: Malina hasn't named the factories.
- Light effects: No. 2's chimney smoke, No. 2's window flicker, No. 1's brazier flames and the lantern's
  flicker. About 1.0 s a frame.

**Shot 3b - W1, the quiet factory's gate (cut on "In", 55.1 s, to the page turn)** [Strongest
picture].
- Subject: the shut No. 1 gate at the head of the queue.
- Move: one slide of 1.2 m along the queue toward the gate, from "Workers" (2) (57.9 s) to "Call" (61.0 s).
  Why: we join the line.
- Events and words on screen:
  - Cut in on "In": windows dark, chimney cold ("the machines stand still").
  - "Workers" (2) (57.9 s): small **WORKERS WAIT AT THE GATE** (the phrase comes back on pages 4, 11, 12 and
    14) [One world].
  - "quiet" (61.6 s): **THE QUIET FACTORY**.
  - "government" (63.3 s): **THE GOVERNMENT SPENDS NEW MONEY**.
  - "go" (67.2 s): the gate leaves swing open (1.2 s) and the queue fades away (1.2 s, from "in", 67.4 s).
    They have gone in. The brazier keeps burning by the empty wall, and the lunch tin stays.
  - "start" (68.7 s): No. 1's windows light (0.8 s) and its chimney begins to smoke.
  - "More" (1) (69.5 s): **MORE MONEY**; "things" (71.2 s): **MORE THINGS TO BUY**. This is the same
    layout as page 5's MORE MONEY / SAME THINGS TO BUY and page 6's FEWER.
  - "barely" (72.9 s): a price arrow over No. 1 that stays level, **PRICES BARELY MOVE**.
- Light effects: the brazier's flames, glow and a little smoke; the lantern's flicker; after "start", chimney
  smoke and a faint flicker in the windows. About 1.0 s a frame held, 3.5 s during the slide and the
  changes (about 5 s of film).

### Page 4 - The flat-out factory, the first guess (75.5 to 91.8 s, then the 4-second hold)

**Must teach:** in the flat-out factory every worker and machine is busy and no one waits at the gate. The
same new money is spent there. What happens to prices?

**Shot 4a - W2, the flat-out factory's gate (cut on "In", 75.5 s, to the end of the hold)** [Strongest
picture].
- Subject: the open gate.
- Story group: the gate leaf pinned back against the wall, crates stacked against its inside, the handcart's
  shafts over the crates, the gate lamp on the pier above, and the warm patch of light on the empty pavement
  where a queue would be.
- Move: one slide of 1.2 m toward the gate, from "No" (82.0 s) to "factory" (84.9 s). Why: we walk up to the
  gate with nobody in the way. The camera stands where W1's did, mirrored.
- Events and words on screen:
  - "busy" (79.2 s): the windows flicker brighter.
  - "No" (82.0 s): small **NO ONE WAITS AT THE GATE** [One world].
  - "flat-out" (84.5 s): **THE FLAT-OUT FACTORY**, with a small line under it, **FLAT OUT = WORKING AS HARD
    AS THEY CAN**.
  - "same" (86.0 s): **THE SAME NEW MONEY IS SPENT**.
  - "prices" (90.0 s): **WHAT HAPPENS TO PRICES?**; "guess" (91.0 s): small **HAVE A GUESS** with a ring that
    fills over 4 seconds.
- **The 4-second guess hold:** from Malina's last word (91.8 s) to page 5 (95.7 s), on the still composed
  frame, with the question and the ring held and the music up. No join: page 5 continues this frame.
- Light effects: heavy smoke from both chimneys, window flicker. About 1.0 s a frame held, 3.5 s during the
  slide.

### Page 5 - The rule (95.8 to 120.6 s, then the 2-second hold)

**Must teach:** why prices go up when nothing is spare (more money, the same things, so businesses can ask
more); the rule, which most economists agree on.

**Shot 5a - W2, the composed frame, held (95.8 to 107.1 s)** [both plans].
- Events and words on screen: "spare" (1) (95.9 s): **NO SPARE:**, then **WORKERS / MATERIALS / MACHINES**
  word by word. "same" (102.2 s): **MORE MONEY / SAME THINGS TO BUY**. "businesses" (103.9 s): **BUSINESSES
  CAN ASK MORE**. "up" (1) (106.5 s): a price arrow over No. 2 climbs.
- Light effects: as page 4. About 1.0 s a frame.

**Shot 5b - W3, held (cut on "Most", 107.1 s, to the page turn)** [both plans].
- Events and words on screen:
  - Cut on "Most": the small name tags **QUIET** and **FLAT OUT** appear over the two columns. They come back
    on every return to W3 from here on [One world].
  - "agree" (108.0 s): small **MOST ECONOMISTS AGREE**.
  - The rule cards build word by word [One world's timing]. Over No. 1: "spent" (110.4 s) **NEW MONEY
    SPENT**, "spare" (2) (112.1 s) **+ SPARE**, "made" (2) (116.3 s) **→ MOSTLY MORE THINGS MADE**. Over
    No. 2: "nothing" (117.3 s) **NOTHING SPARE**, "up" (2) (120.0 s) **→ MOSTLY PRICES UP**.
- **The 2-second rule hold:** both cards held from Malina's last word (120.6 s) for 2 seconds, music up, then
  the page turn.
- Light effects: as 3a. About 1.0 s a frame.

### Page 6 - Britain at war (124.1 to 149.3 s)

**Must teach:** a real case close to the flat-out factory. Millions went to fight; soon fewer than one worker
in a hundred was out of work; ships were sunk; the war was paid for partly with new money. More money and
fewer things, so prices roughly doubled.

**Shot 6a - G1, the street to the works (124.1 to 146.4 s)** [One world's street, Strongest picture's
window, combined: new].
- Subject: the grocer's nearly bare corner window and the recruiting poster beside it, with the works'
  glowing gate just past them where the lines meet.
- Move: one slide of 1.2 m toward the window, from "fewer" (2) (141.4 s) to "doubled" (145.5 s). Why: we
  step up to the bare shelves on "fewer things to buy" [Strongest picture].
- Events and words on screen:
  - "real" (124.4 s): **A REAL CASE** [One world].
  - "Britain" (1) (125.5 s): **BRITAIN, FIRST WORLD WAR**.
  - "Millions" (128.1 s): **MILLIONS WENT TO FIGHT**, with a thin line to the poster.
  - "fewer" (1) (130.4 s): the 100-dot panel, every dot lit but the last, which is nearly empty: **FEWER THAN
    1 IN 100 OUT OF WORK**.
  - "submarines" (134.0 s): **SHIPS SUNK: FOOD, MATERIALS**.
  - "partly" (138.4 s): **PARTLY NEW MONEY**.
  - "More" (140.1 s): **MORE MONEY**; "fewer" (2) (141.4 s): **FEWER THINGS TO BUY**.
  - "doubled" (145.5 s): two bars, **BEFORE THE WAR** and **END OF THE WAR: ROUGHLY ×2**.
- Light effects: the works' smoke (about 0.1 to 0.2 s), gas lamp flicker (about 0). About 1.0 s a frame
  held, 3.5 s during the slide.

**Shot 6b - W2, the composed frame (cut on "Britain" (2), 146.4 s, to the page turn)** [both plans].
- "close" (147.4 s): **CLOSE TO THE FLAT-OUT FACTORY**; the tag FLAT OUT. About 1.0 s a frame.

### Page 7 - Glasgow's homes (150.8 to 182.3 s)

**Must teach:**
- the picture works for one kind of thing, homes;
- war workers came to Glasgow, where there were already too few homes;
- builders and materials went to the war;
- landlords raised rents, up to a quarter in places;
- about twenty thousand families refused the extra;
- Parliament brought rents on small homes back.

**Shot 7a - G1, held from the slide's starting spot (150.8 to 154.9 s)** [One world].
- "fifteen" (151.5 s): **GLASGOW 1915**. "crowds" (152.2 s): **CROWDS OF WAR WORKERS**, with a thin line to
  the walkers (or to the works' gate, if the walkers were dropped).
- Light effects: as 6a. About 1.0 s a frame.

**Shot 7b - G2, the close mouth (cut on "There", 154.9 s, to the page turn)** [Strongest picture, with
One world's placards].
- Subject: the factor's notice, with the suitcase on the step below it.
- Move: one slide of 1.2 m toward the notice, from "Landlords" (167.7 s) to "quarter" (170.8 s). Why: we step
  up to the notice that turns too few homes into higher rent.
- Events and words on screen:
  - "homes" (1) (156.4 s): the tenement windows light in a quick ripple from the close outward until every one
    is lit (1.5 s): every home full. **TOO FEW HOMES ALREADY** [Strongest picture].
  - "builders" (157.4 s): a label with a thin line to the half-built tenement, **BUILDERS AND MATERIALS GONE
    TO THE WAR**; "built" (160.8 s): **FEW NEW HOMES**.
  - "thing" (163.4 s): small **ONE KIND OF THING**. "factory" (166.8 s): **FOR HOMES: LIKE THE FLAT-OUT
    FACTORY**. The lit windows rhyme with No. 2's, so there is no cut away.
  - "rent" (168.8 s): **RENT RAISED**; "quarter" (170.8 s): **UP TO A QUARTER MORE, IN PLACES**.
  - "twenty" (172.9 s): a counter rolls up to **ABOUT 20,000 FAMILIES REFUSING THE EXTRA**, finished by
    "extra" (175.5 s). From "refusing" (174.5 s), placards appear in the lit windows one by one over 3 seconds
    (own surfaces) [One world].
  - "back" (179.9 s): a typed stamp, **RENTS ON SMALL HOMES BACK TO BEFORE THE WAR**, landing on "war" (3)
    (181.7 s) [One world's wording, closer to Malina's].
  - Never WON, FROZEN or NOT ENOUGH, and no Mary Barbour card (the script's rules).
- Light effects: gas lamp flicker (about 0). About 0.5 s a frame held, 3.5 s during the ripple, the slide and
  the placards (about 8 s of film).

### Page 8 - Japan, the second guess (183.8 to 197.9 s, then the 4-second hold)

**Must teach:** Japan in 2013. Japan's version of our Reserve Bank planned to double the money it had created
in two years. If the warning is right, prices should go up fast. Guess.

**Shot 8a - J1, the corner shop's counter, held (183.8 s to the end of the hold)** [Strongest picture].
- Subject: the basket against the till. Another country's basket at another checkout.
- Events and words on screen:
  - "thirteen" (184.8 s): **JAPAN 2013**.
  - "version" (186.2 s): small **JAPAN'S VERSION OF OUR RESERVE BANK**.
  - "double" (188.2 s): **×2 MONEY**; "years" (190.8 s): **IN TWO YEARS**.
  - "warning" (192.0 s): a dashed line climbing steeply, **IF THE WARNING IS RIGHT**.
  - "happened" (196.0 s): **WHAT HAPPENED?**; "guess" (197.1 s): **HAVE A GUESS** and its ring.
- **The 4-second guess hold:** 197.9 to 201.8 s. No join: page 9 continues this frame.
- Light effects: none live. About 0.5 s a frame.

### Page 9 - Japan, the answer (201.9 to 227.4 s, then the 2-second hold)

**Must teach:**
- prices barely moved for about eight years, about half a percent a year on average;
- one reason: most of the new money sat in the banks, and in our picture never reached the factory;
- so what matters is whether it is spent, and on what.

**Shot 9a - J1, the same frame (201.9 to 214.0 s)** [Strongest picture; the bank across the street is new].
- "barely" (202.2 s): a real line runs almost level beside the dashed one, **PRICES BARELY MOVED**.
- "eight" (204.0 s): **FOR ABOUT 8 YEARS**.
- "half" (207.1 s): **ABOUT ½% A YEAR, ON AVERAGE**.
- "reason" (209.4 s): small **ONE REASON ECONOMISTS GIVE** [One world].
- "banks" (213.2 s): a label with a thin line to the bank across the street, **MOST SAT IN THE BANKS**.
- About 0.5 s a frame.
- Fallback: if the bank across the street doesn't read on a phone, cut to 9b on "most" (1) (211.2 s), as
  Strongest picture planned.

**Shot 9b - W3, held (cut on "In", 214.0 s, to the page turn)** [Strongest picture; first card from One
world].
- This view breaks the main rule on purpose: the cause (the lit bank) and the effect (the untouched gates)
  are apart, and the empty lane between them is the story. The labels' lines tie them together. It is
  written into the check file.
- Events and words on screen:
  - "picture" (214.4 s): small **IN OUR PICTURE** [One world].
  - "most" (2) (215.1 s): the bank's window lights from inside (1 s), showing the NEW MONEY sacks.
  - "never" (215.7 s): a label to the gates, **NEVER REACHED THE FACTORY**. Both gates are unchanged, so the
    picture doesn't say which factory Japan was like.
  - "much" (218.7 s): **NOT JUST HOW MUCH**. "whether" (220.7 s): **WHETHER IT'S SPENT, AND ON WHAT**.
  - "spare" (223.8 s): **SPARE WORKERS, MATERIALS, MACHINES TO MAKE WHAT IT BUYS?**
- **The 2-second hold:** that card is held from 227.4 s for 2 seconds, then the page turn.
- Light effects: as 3a, plus the bank window's own light. About 1.0 s a frame.

### Page 10 - New Zealand, the third guess (230.9 to 252.0 s, then the 4-second hold)

**Must teach:** here, from 2020, the Reserve Bank created new money and the government spent more, including
help paying wages. By the end of 2021 about three in a hundred were out of work. Which factory was New Zealand
closer to?

**Shot 10a - S1a, held (230.9 to 248.5 s)** [Strongest picture; the sanitise sign from One world].
- The PLEASE SANITISE YOUR HANDS sign is on the site gate for this page only.
- Events and words on screen:
  - "here" (231.4 s): **NEW ZEALAND 2020**.
  - "money" (235.7 s): **NEW MONEY**.
  - "government" (237.0 s): **GOVERNMENT SPENT MORE**; "wages" (239.8 s): **INCLUDING HELP PAYING WAGES**.
  - "twenty-one" (241.8 s): **END OF 2021**.
  - "three" (246.1 s): the 100-dot panel with three dots empty, **ABOUT 3 IN 100 OUT OF WORK**, with the small
    credit **STATS NZ**.
- About 0.5 s a frame.

**Shot 10b - W3, held (cut on "Which", 248.5 s, to the end of the hold)** [both plans].
- "Which" (248.5 s): **WHICH ONE?** with a small arrow to each gate; the tags QUIET and FLAT OUT.
- "guess" (251.2 s): **HAVE A GUESS** and its ring.
- **The 4-second guess hold:** 252.0 to 255.9 s.
- About 1.0 s a frame.

### Page 11 - New Zealand, the answer (256.0 to 273.8 s)

**Must teach:**
- close to the flat-out factory;
- prices went up fast, partly because more was being spent and partly because of prices overseas, like oil;
- at the peak, the biggest push came from the price of building new homes, and rents.

**Shot 11a - W2, the composed frame (256.0 to 260.5 s)** [both plans].
- "Close" (256.0 s): **CLOSE TO THE FLAT-OUT FACTORY**. "waiting" (258.9 s): small **ALMOST NO ONE
  WAITING**.
- About 1.0 s a frame.

**Shot 11b - C1, the composed frame, held (cut on "And", 260.5 s, to 268.3 s)** [new: prices are shown
where they are felt, the viewer's own checkout].
- "prices" (1) (260.7 s): **PRICES WENT UP FAST**.
- "Partly" (262.5 s): **PARTLY: MORE SPENT**; "partly" (2) (265.2 s): **PARTLY: PRICES OVERSEAS, LIKE OIL**.
  The petrol canopy is through the window, unlabelled.
- About 0.5 s a frame.

**Shot 11c - S1a (cut on "At", 268.3 s, to the page turn)** [Strongest picture; the FOR RENT board from One
world].
- Move: one slide of 1.2 m toward the house frame, from "peak" (268.6 s) to "homes" (272.0 s). Why: it lands
  on "the price of building new homes", the homes the viewer saw going up on page 2.
- Events and words on screen:
  - "peak" (268.6 s): **AT THE PEAK:**.
  - "building" (271.4 s): **THE PRICE OF BUILDING NEW HOMES**.
  - "rents" (273.1 s): **AND RENTS**, while the FOR RENT board appears on the neighbour's fence (the camera
    has stopped).
  - Never BUILDING NEW HOMES on its own, and no house prices.
- About 0.5 s a frame held, 3.5 s during the slide.

### Page 12 - The usual cure (275.3 to 300.1 s)

**Must teach:**
- the Reserve Bank raises its interest rate; interest is the extra you pay back when you borrow;
- many loans cost more, so people have less to spend; businesses sell fewer things and hire fewer people;
- prices go up more slowly, usually not down;
- in the picture, the flat-out factory slows and more workers wait at the gate.

**Shot 12a - K1, the kitchen (275.3 to 294.8 s)** [Strongest picture].
- Subject: the letter about the home loan.
- Move: one slide of 1.2 m toward the table, from "Many" (282.8 s) to "spend" (285.7 s). Why: we step up to
  the letter on "Many loans cost more".
- Events and words on screen:
  - "cure" (276.4 s): **THE USUAL CURE**.
  - "raises" (277.8 s): a dial in the dark window, **INTEREST RATE**, its needle rising, with no figures.
  - "Interest" (2) (279.6 s): **INTEREST = THE EXTRA YOU PAY BACK WHEN YOU BORROW**.
  - "loans" (283.0 s): **MANY LOANS COST MORE**; "spend" (285.7 s): **→ LESS TO SPEND**; "sell" (287.0 s):
    **→ SELL FEWER THINGS**; "hire" (288.5 s): **→ HIRE FEWER PEOPLE**.
  - "slowly" (1) (291.1 s): **PRICES GO UP MORE SLOWLY**; "down" (292.6 s): **USUALLY NOT DOWN**.
- Light effects: none live. About 0.5 s a frame held, 3.5 s during the slide.

**Shot 12b - W2, the composed frame (cut on "In", 294.8 s, to the page turn)** [Strongest picture; the
card from One world].
- Events and words on screen:
  - "picture" (295.2 s): small **IN OUR PICTURE**. The tag FLAT OUT stays on through the change, so the
    viewer knows this is still the flat-out factory [new].
  - "slows" (297.0 s): No. 2's windows dim to a third, its smoke thins to one chimney, and the gate swings
    half shut (1.5 s).
  - "workers" (298.4 s): the queue fades in along the wall (1.2 s). "gate" (299.4 s): **MORE WORKERS AT THE
    GATE**.
- Light effects: smoke and flicker. About 1.0 s a frame held, 3.5 s during the change (about 2.7 s).

### Page 13 - Who pays, here (301.6 to 327.8 s)

**Must teach:**
- the Reserve Bank raised its interest rate again and again from late 2021 into 2023;
- many loans cost more and jobs got harder to find;
- nearly six in a hundred were out of work by the middle of 2026, up from about three, and the interest rate
  isn't the only reason;
- who pays: many people with loans, and people put out of work.

All four shots are held and joined by cuts [Strongest picture].

**Shot 13a - K1, the composed frame (301.6 to 311.2 s).**
- "pays" (1) (301.8 s): **WHO PAYS FOR THE CURE?**
- "From" (303.0 s): the dial's needle steps up again and again; by "again" (2) (308.7 s): **LATE 2021 TO
  2023: AGAIN AND AGAIN**.
- "loans" (1) (309.8 s): **MANY LOANS COST MORE**.

**Shot 13b - S1b, the stopped site (cut on "jobs", 311.2 s, to 324.2 s).**
- "jobs" (311.2 s): **JOBS HARDER TO FIND**.
- "middle" (313.4 s): **MIDDLE OF 2026**.
- "six" (315.7 s): the 100-dot panel with nearly six empty, **NEARLY 6 IN 100 OUT OF WORK**, with the credit
  **STATS NZ**.
- "three" (318.7 s): faint **UP FROM ABOUT 3**.
- "only" (321.0 s): small **NOT THE ONLY REASON**.
- "pays" (2) (323.0 s): **WHO PAYS?**

**Shot 13c - K1 (cut on "Many" (2), 324.2 s, to 325.9 s).**
- "loans" (2) (325.1 s): **MANY PEOPLE WITH LOANS**.

**Shot 13d - S1b (cut on "and" (3), 325.9 s, to the page turn).**
- "put" (326.5 s): **PEOPLE PUT OUT OF WORK**.

Moves: none. Light effects: none live. About 0.5 s a frame.

### Page 14 - Two views (329.3 to 351.8 s)

**Must teach:**
- America's version of our Reserve Bank says the cure would probably mean fewer jobs, unfortunate but not the
  goal;
- Mattei argues fewer jobs are the cure's main goal: with more workers waiting at the gate, people with jobs
  have less power to ask for higher wages.

**Shot 14a - W4, from inside the yard (the whole page)** [Strongest picture].
- Subject: the gate opening, with the queue beyond. Story group as in place A's W4: the jacket and cap of
  someone with a job, and the queue of people without one.
- Move: one slide of 1.2 m toward the gate, from "With" (345.2 s) to "says" (347.8 s). Why: we move closer to
  the queue on "with more workers waiting at the gate".
- Events and words on screen:
  - "America's" (329.3 s): **AMERICA'S VERSION OF OUR RESERVE BANK**, with the small credit **US FEDERAL
    RESERVE**.
  - "jobs" (1) (333.5 s): **FEWER JOBS**. "unfortunate" (335.2 s): **UNFORTUNATE,**; "goal" (1)
    (337.0 s): **NOT THE GOAL** (no quotation marks).
  - "Clara" (337.7 s): a typed name card, **CLARA E. MATTEI**, with the small source credit **THE CAPITAL
    ORDER** (no portrait, no book cover, no year).
  - "argues" (342.2 s): **MATTEI ARGUES:**, and on "goal" (2) (344.5 s): **FEWER JOBS ARE THE MAIN GOAL**.
  - "power" (349.8 s): **LESS POWER TO ASK FOR HIGHER WAGES**. MATTEI ARGUES stays on screen above it to the
    page's end, so her view stays marked as hers [new].
- Light effects: thin smoke beyond the wall and the lane's gas lamps flickering faintly. About 1.0 s a frame
  held, 3.5 s during the slide.

### Page 15 - Back at the checkout (353.3 to 378.3 s)

**Must teach:**
- a hundred-dollar basket in June 2025 cost about a hundred and four a year later, and would have cost about a
  hundred and three if petrol and diesel prices hadn't changed;
- petrol and diesel push up almost everything made or moved, in both factories;
- so part of what you felt came from petrol and diesel.

**Shot 15a - C1, the composed frame (353.3 to 367.4 s)** [Strongest picture].
- "dollars" (356.2 s): a tag beside the basket, **$100, JUNE 2025**.
- "later" (358.9 s): it flips to **ABOUT $104, A YEAR LATER**.
- "three" (366.6 s): a ghost tag beside it, **ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED**, with
  the credit **STATS NZ**. No 4.1%, 2.9% or 2026 on screen.
- About 0.5 s a frame.

**Shot 15b - W3, held (cut on "When", 367.4 s, to 374.3 s)** [Strongest picture].
- "petrol" (2) (367.7 s): labels with thin lines to the drums at both gates, **PETROL AND DIESEL**.
- "both" (373.0 s): a price arrow climbs over each factory, **BOTH FACTORIES**.
- About 1.0 s a frame.

**Shot 15c - C1 (cut on "So", 374.3 s, to the page turn).**
- "part" (374.4 s): **PART OF IT: PETROL AND DIESEL**. Never "mostly".
- About 0.5 s a frame.

### Page 16 - Spent on what? (379.8 to 402.9 s, then the 4-second fade)

**Must teach:** the rule again, in the same words; the two questions to ask next time.

**Shot 16a - W3, held (379.8 to 393.9 s)** [both plans].
- "always" (380.6 s): **DOES NEW MONEY ALWAYS PUSH PRICES UP?**; "No" (382.1 s): **NO.**
- Then page 5's cards, with the same words, in the same places and the same order: "spent" (1) (383.7 s),
  "spare" (1) (385.3 s), "made" (389.5 s) over No. 1; "nothing" (390.6 s), "up" (2) (393.3 s) over No. 2.
- About 1.0 s a frame.

**Shot 16b - C1 (cut on "So", 393.9 s, to the end)** [Strongest picture's move, One world's headline].
- Move: one slide of 1.3 m back from the basket to the plate's spot, from "next" (394.1 s) to about 397.3 s,
  the reverse of page 1. Why: stepping back as the questions land. The headline stays in frame.
- Events and words on screen:
  - "warning" (395.3 s): the small label **THE WARNING** to the headline again, as on page 1 [new].
  - "Spent" (2) (397.7 s): **SPENT ON WHAT?**, with a small line under it on "anything" (399.2 s): **ANYTHING
    SPARE TO MAKE WHAT IT BUYS?**
  - "pays" (401.8 s): **WHO PAYS FOR THE CURE?**
  - Both are held. **The 4-second fade** to dark follows Malina's last word (402.9 s).
- About 3.5 s a frame during the slide, 0.5 s held.

### The moves and holds at a glance

| Page | Shots (views) | Moves (one slide each, never a turn) | Holds |
|---|---|---|---|
| 1 | C1 | toward the basket | |
| 2 | S1a | none | |
| 3 | W3, W1 | along the queue to No. 1's gate | |
| 4 | W2 | toward No. 2's gate | 4-second guess hold (W2) |
| 5 | W2, W3 | none | 2-second rule hold (W3) |
| 6 | G1, W2 | toward the grocer's window | |
| 7 | G1, G2 | toward the rent notice | |
| 8 | J1 | none | 4-second guess hold (J1) |
| 9 | J1, W3 | none | 2-second hold on the "spare ... to make what it buys?" card (W3) |
| 10 | S1a, W3 | none | 4-second guess hold (W3) |
| 11 | W2, C1, S1a | toward the house frame | |
| 12 | K1, W2 | toward the letter | |
| 13 | K1, S1b, K1, S1b | none | |
| 14 | W4 | toward the gate and the queue | |
| 15 | C1, W3, C1 | none | |
| 16 | W3, C1 | back from the basket | 4-second fade at the end (C1) |

**31 shots, 9 slides.** Pages 2, 5, 8, 9, 10, 13 and 15 hold still throughout. No page has more than one
move, against your limit of three.

How often the busiest paintings are used:
- W3: on 6 pages (3, 5, 9, 10, 15, 16), and it is the master for every Works painting;
- W2: on 5 pages (4, 5, 6, 11, 12), in both its states;
- C1: on 4 (1, 11, 15, 16);
- S1a: on 3 (2, 10, 11).

### How the two factories stay the same wherever they come back

1. **One set, one script, fixed places.** Both factories are in one set file (`works.blend`) with four named
   cameras. It is never rebuilt between views. The quiet factory is always on the left and the flat-out
   factory on the right, never mirrored or swapped [both plans].
2. **Different at a glance:** round against square chimneys, a water tank, dark red-brown against pale
   buff-grey brick, and the "No. 1" and "No. 2" boards [One world's identities, Strongest picture's boards].
3. **Each gate view shows the other factory where it really stands:** in W1, No. 2's two square chimneys
   beyond the gate; in W2, No. 1's single round chimney [new].
4. **Typed name tags** QUIET and FLAT OUT on every return to W3 from page 5, and on the flat-out factory
   through its change on page 12 [One world].
5. **Matched gate views:** W1 and W2 are framed the same way, from the same distance, with the same lens and
   gate furniture [both plans].
6. **One painting chain** [both plans; checks from One world]:
   - W3 is painted first and becomes the master. Every other Works painting gets it as image 2.
   - Each painting is lined up with its plate (`align_painting.py`).
   - Then a colour check: the average colour of each factory's brick and roofs, the gates and the sky,
     measured inside their outlines (the shot checker's prop masks) in the new painting and in the master.
     A clear mismatch means a 10-cent repaint. `match_model_colours.py` is only a rough check (its own note
     says so).
7. **Second states come from the same painting:** the flat-out state from W2's main and behind paintings,
   and S1b patched into S1a's painting, so only what the story changes changes.
8. **One shared settings module** (`works-effects.js`) for the four states: window brightness, smoke amount,
   gate angle, how many men. The same smoke and flicker with the same seeds on every page [both plans].
9. **A continuity sheet** before filming: one still from each Works view side by side (chimneys, boards, gate
   states, how many men, sky), checked by a helper [Strongest picture].

---

## 3. The numbers

### Plates, paintings and money

| View | Plates | Paintings | Why |
|---|---|---|---|
| W3 both gates | 1 | 1 | always held; its changes are own surfaces (the bank's window) or live (smoke) |
| W1 No. 1's gate | 1 (+1 free helper plate) | 2 | slides; the queue leaves |
| W2 No. 2's gate | 1 (+1 free helper plate) | 2 | slides; the queue comes and goes (the flat-out state is made from these two for free) |
| W4 inside the yard | 1 | 2 | slides |
| C1 the checkout | 1 | 2 | slides in (page 1) and out (page 16) |
| J1 the corner shop | 1 | 1 | held |
| S1a the busy site | 1 | 2 | slides (page 11) |
| S1b the stopped site | 1 | 1 | held, patched into S1a's painting |
| K1 the kitchen | 1 | 2 | slides |
| G1 street to the works | 1 | 2 | slides |
| G2 the close mouth | 1 | 2 | slides; windows and placards are own surfaces |
| **Total** | **11** (+2) | **19** | |

| Spending (all on hold until you say yes) | Low (10 cents a painting) | High (log 32's 20 to 45 cents for two) |
|---|---|---|
| 19 paintings (Flux 3 edit on fal) | US$1.90 | US$4.28 |
| Up to 4 composition sketches by Nano Banana Pro, only where the shot checker can't settle a view | US$0.60 | US$0.60 |
| Narration (about 6,300 characters) | US$1.10 | US$1.10 |
| **Planned** | **US$3.60** | **US$5.98** |
| Repaint reserve: 10 repaints (about one in two; lesson 97: Flux's strength varies) | US$1.00 | US$2.25 |
| **Planned with every repaint used** | **US$4.60** | **US$8.23** |

Every case is under the US$12 line, and at least US$11.77 of the US$20 is never touched. Every request is
listed in the folder's `00-requests.json`, and no step of the plan needs more than this.

### New props to build by script (about 60 pieces, most of them small)

- **The Works (about 14):** the wall with two gate arches and piers; the No. 1 and No. 2 boards; the bank
  front with its lit room and brass plate; the NEW MONEY sacks; the PETROL and DIESEL drums; the THIS WAY UP
  crate stencils; a chain and padlock; figure shapes in five poses; a lunch tin; a jacket and cap on a nail;
  a tin mug; the two factory options (no tank on No. 1, two square chimneys on No. 2); both works and the
  town at real size (adapted, not new).
- **The checkout and corner shop (about 17):** counter, belt, divider bar, card terminal, till, bag rack, wire
  basket, bread bag, milk bottle, butter, CHECKOUT sign, newspaper rack and papers with the masthead and
  headline, the petrol canopy seen through the window; the corner shop's counter, hot-food cabinet, rice
  balls, tea bottle, milk carton, レジ sign, and the bank across the street.
- **The building site (about 14):** mini digger, timber packet, house frame with wrap, scaffolding, mesh fence
  panels and gate, chain and padlock, hi-vis vest, hard hat, builder's banner, two weatherboard houses, the
  torn cover, the FOR RENT board, the sanitise sign.
- **The kitchen (about 5):** room and window, letter and envelope, mug, phone, cardigan.
- **Glasgow (about 11):** the tenement block builder, the corner grocer's shopfront and bare display with
  tins, the recruiting poster, the factor's notice, the munitions works' wall and gate, the half-built
  tenement with scaffold poles, the brick stack and tarpaulin, the re-lettered builder's cart, the suitcase
  bundle, twelve placards, the walking figure shapes.

**Fetched from Poly Haven:** 28 models and 20 surfaces, every name checked against Poly Haven's list
(saved in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/polyhaven/`). They are converted with the library's `paper-film/blender/pit-village/props/convert_poly_haven.py` and listed
in a new `index.json` beside the pit village one. The wooden crates, ladder and wicker basket are already in
the prop library.

### Computer time

**Blender:** about 12 hours of machine time. Plates are drawn one at a time, because each uses all 4
processors.

| Step | Each | Count | Time |
|---|---|---|---|
| Plates (EEVEE, 1536 x 2730) | about 10 min | 11, each drawn about twice after checks | about 3.7 h |
| Helper plates (W1 and W2 without the figures and gates) | about 10 min | 2 | about 0.3 h |
| Small preview stills (540 x 960) | about 1 min | about 15 a view | about 2.8 h |
| Shot checker runs | about 1 min | about 8 a view | about 1.5 h |
| Finished stills for the light rules | about 10 min | 11 | about 1.8 h |
| Exports (sets as .glb, cameras as camera.json) and Poly Haven conversions | | | about 1.5 h |

**Filming:** about 12,200 frames on the estimated timeline, planned as 13,000 in case Malina reads more
slowly.

| Kind of frame | Frames (of 12,208) | Seconds a frame | Hours on one helper |
|---|---|---|---|
| held, nothing live | about 5,900 | about 0.5 | 0.8 |
| held, with smoke, flames or flicker drawn on top (the Works, Glasgow's works) | about 5,100 | about 1.0 | 1.4 |
| camera sliding or the set changing (about 40 s of film in all) | about 1,200 | about 3.5 | 1.2 |
| **All** | **12,208** | **about 1.0 on average** | **about 3.4** |

- With two helpers at once (about 17% faster on 4 processors): **about 2.8 hours, about 3 hours at 13,000
  frames.** That is about half the planned ceiling of 2 seconds a frame. Allow one more hour for re-filming
  pages after the critics.
- If moving frames are as slow as 6 s, add about 0.7 hours.
- If held shots didn't work at all, every frame would cost about 3.6 s, about 11 hours with two at once.
  That is why the free test measures them first.
- Turning off the stage's depth blur, glow pass and shadow maps may save more [One world]. It is timed in
  the free test and kept only where the picture doesn't suffer.
- Filming runs in stretches under 2 hours (`FILM_FROM` / `FILM_TO`), because a cloud session stops background
  jobs at 2 hours.

**Disk (about 8 GB free):** peak about 2.5 to 3 GB.

| What | About |
|---|---|
| Poly Haven downloads and conversions | 0.3 GB |
| Six .blend files | 0.5 GB |
| Exported sets (one per place, cut to what the cameras see) | 0.4 GB |
| Plates and paintings, raw and lined up | 0.3 GB |
| Checker reports, stills and contact sheets | 0.4 GB |
| Narration, word times and the mix | 0.05 GB |
| Film pieces (kept as video, never as single pictures) and the finished film | 1 GB |

Props are loaded from the library and never copied per set. Old stills are cleared once a place passes its
checks, and film pieces once they are joined.

---

## 4. The order of work

### The cheapest tests that would show the plan works

1. **Free, about 45 minutes: time the stage** [One world's test, widened].
   - Use the notice corner as it is. Film 60 frames of each kind: held, held with fire and smoke, and
     sliding. Then film the same frames with the depth blur, glow pass and shadow maps off.
   - Use `profile_frame.mjs` to see which part is slow.
   - It passes at about 1 s a frame held with effects and about 4 s or less sliding. If it doesn't, the
     budget in section 3 is redone before anything is built.
   - It also checks whether a set's number of materials drives the cost. The notice corner's set has 840
     materials and takes 3.1 s to draw; the old factory model joins its parts to about 19. If it does, every
     set is exported with its pieces joined by material [new].
2. **Free, about a day: build the Works and film page 3 with stand-ins** [Strongest picture's test, with One
   world's second view].
   - Build both factories at real size with their own shapes, the wall, gates, boards, 7 figure shapes, the
     brazier and lantern, and the bank front (dark).
   - Compose W3 and W1 with the shot checker. Draw both plates and W1's helper plate.
   - Film all of page 3 (about 27 seconds) on the estimated timeline, with the plates standing in for the
     paintings and the helper plate for the behind painting.
   - Before any money is spent, it shows:
     - the speed of each kind of frame on a real chapter set;
     - whether "the workers go in" reads as people going in, not ghosts (a fresh helper watches it in motion
       without being told what it shows);
     - whether the swinging gate and the boards sit well, and whether the two factories are told apart at
       phone size (a helper names them from a still);
     - that nothing tears on the slide (the weights view).
3. **The first paid step, with your yes (one approval for both parts).**
   - **Record the narration** (about US$1.10). First, open a source for page 7's "builders and materials gone
     to the war" (the script's "Sources still to open"), because re-recording one page moves every time after
     it.
   - **Paint three pictures** (about 30 to 68 cents):
     - W3, the master, with a chapter 2 painting as its style, as for the notice corner;
     - W1's main painting, with W3's as its style;
     - W1's behind painting.
   - These three test the three things nobody has tried yet [One world's idea, aimed at Strongest picture's
     biggest risk]:
     - painted people;
     - people leaving a painted picture, shadows and all;
     - a second view that matches the master.
   - Then line them up, run the colour check, re-film page 3 painted, and look at it in motion. Three fresh
     helpers check it (looks; the painter's faults; the figures), then you look on your phone.
   - The paintings are kept for pages 3, 5, 9, 10, 15 and 16.
   - If the painted figures fail twice, switch to the fallbacks (section "People") before painting anything
     else, and tell you.

### After the tests

4. **The rest of the Works:** W2 (with its helper plate) and W4, painted with W3 as their style; then the
   continuity sheet.
5. **New Zealand:** the building site (S1a, then S1b painted with S1a's painting as its style and patched in),
   the checkout (C1), the kitchen (K1).
6. **Glasgow (G1, G2) and the corner shop (J1).**
7. **For every view, before its plate:**
   - compose it with the shot checker until it passes;
   - the history helper checks a preview still with the lettering list. A reader of Japanese checks J1, and
     a colour helper checks every New Zealand view for party and chain colours;
   - every invented name is searched;
   - read the plate's render log for shadow-memory faults.
8. **Paint a place at a time, each batch with your yes.** For each painting:
   - line it up (`align_painting.py`);
   - make the behind painting and keep its painted shadows (`keep_painted_shadows.py`);
   - make the free state pictures (`composite_fill.py`);
   - check the colours against the master.
9. **Pages:**
   - the real word times from the recording;
   - one page file per page, timed to words with `kit.at`;
   - the camera checked with `camera_audit.py`;
   - for every slide, four stills: the projector's view, the end, the middle, and the weights view;
   - every card checked against the narration by a words-on-screen helper;
   - independent critics (looks; history; rules: figures on screen, party colours, Mattei marked as hers);
   - fixes.
10. **Film** in stretches under 2 hours, two at a time.
    - Look for jumps between frames (`find_jumps.py`), with the planned cuts listed.
    - Two helpers and a skeptic check the film in motion.
    - Fix, and re-film only the changed stretches.
11. **Finish:** the mix, captions, loudness and timing checks. Then the real test: show it to the people who
    got lost, with the listener questions in the script file.

**If time runs short, the first to go** [Strongest picture]:
- the kitchen. Pages 12 and 13 use the checkout instead, with the interest rate dial in its window;
- then the Glasgow walkers;
- then the bank across the street from the Japanese shop. Page 9 then cuts to W3 on "most" (1).

### Risks, and how each will be caught

| Risk | How it will be caught | What then |
|---|---|---|
| The painter gives the waiting men faces, changes how many there are, adds people, or makes them look photographic | a figure count against the plate's outlines; a helper looking at every painting at full size; the first paid test | repaint with plainer words and darker backlight; then own-surface silhouettes; then caps, lunch tins and stools |
| The fade of the men going in, or coming back, reads as ghosts | a fresh helper watching the free test and the painted test in motion | a quicker fade hidden in the gate's swing |
| The men's or the gates' painted shadows stay after they leave | stills before and after; the helper plate's difference marks where the shadows fall | widen the area taken from the behind painting |
| Filming is slower than planned | the free timing test, then each page's first stretch timed | join set pieces by material; fewer live effects on held frames; lighter far parts (fewer cottages, a simpler town) |
| Own surfaces (gates, windows, letters, placards) look like 3D renders next to the paint | a looks helper on stills; colour-matching them to the painting, as on the notice corner | darken and match; keep them small or dim; or replace the change with a patched second painting (10 cents) |
| The two factories don't match between views, or can't be told apart on a phone | the colour check against the master; the continuity sheet; a helper naming the factories from stills | repaint the odd one out; strengthen the chimney shapes |
| The painter garbles or invents lettering | every legible sign keeps its own surface; a helper reads every sign at full size | add the sign to the own-surface list |
| The painter stretches or shifts its picture | `align_painting.py` on every painting (log 32 found 0.65% and 3 pixels) | line it up before use |
| A figure on screen that Malina doesn't say (a price tag, keypad, lane or close number, phone number, pack size, a vending machine's buttons) | the lettering lists checked against the narration before building; a helper scanning every still for digits | turn it away, leave it off, or letter it with words |
| A picture says a fact the ledger doesn't (Japan shown as a quiet factory; a stopped site in 2026 read as "building stopped because of the cure"; Glasgow walkers read as a count) | a fact helper asks of each picture "what does this claim?" against the ledger | change the picture. Page 9 keeps both gates untouched; page 13 keeps NOT THE ONLY REASON |
| Wrong era or place details (1915 shopfronts, the poster's, notice's and placards' wording, New Zealand building materials, Japanese labels) | the history helper is given the pictures, not only the words (lesson 83), before painting; a reader of Japanese | fix in 3D before the plate |
| An invented name matches a real business (the grocer, the builders, the bank on the letter, the newspaper, the supermarket, the engineering company) | a search of each name before it is built | pick another |
| Party, supermarket-chain or bank colours (the election is on 7 November) | a colour helper on every New Zealand and Japanese view | recolour; no large flat areas of one colour |
| The Glasgow works is taken for the flat-out factory, or the model for a real place | distinct shapes; the cards PICTURE TWO FACTORIES, A REAL CASE and IN OUR PICTURE; the newcomer test | change the works' shape further |
| W3 on page 9 breaks the main rule | the shot checker reports it | accepted on purpose, written in the check file, tied together by the labels |
| A slide leaves the painted area | the weights view at the end of every slide (blue at an edge) | a shorter slide |
| The plate runs out of shadow memory (lesson 110) | reading each plate's render log | lower the shadows' resolution |
| A guess or rule hold is cut short when the real recording lands | the page-turn check on the real timeline | the holds are written as pauses in the timeline, not as seconds in the page |
| Fading things snap off halfway (lesson 87) | stills every 0.1 s through each fade | build them see-through from the start |
| Page 7's "builders and materials gone to the war" rests on a source seen second-hand | opening a source before recording | if the line changes, the half-built tenement loses its label and stays as background |
| Facts that change soon: new price figures on 22 October, out-of-work figures on 4 November | the script's own re-check list, before filming the cards | the cards follow the script's change (for example MORE THAN 5 IN 100) |
| A cloud session stops background jobs after 2 hours | filming in stretches, kept in 60-frame pieces | carry on from the last piece |
| Money | each batch costed before you are asked; `00-requests.json` totals | nothing in the plan needs more than about US$8.25 |
| The disk fills | checking free space before each export and filming stretch | clear old stills and plates already painted |

---

## Traps

- Never put a program's lettering on screen: every sign that can be read keeps its own surface.
- Never a figure on screen that Malina doesn't say. The only numerals in the sets are "No. 1" and "No. 2"
  (her "the first" and "the second"). No price tags, keypads, lane, close or door numbers, dates or phone
  numbers on set dressing.
- Never name the school of economists, by name or by its letters: the card says ECONOMISTS WHO STUDY HOW MODERN
  MONEY WORKS.
- Mattei appears only as a typed name card, and her view only under MATTEI ARGUES, which stays on screen
  through "less power to ask for higher wages".
- Never WON, RENTS FROZEN or NOT ENOUGH; never "building new homes" on its own; never "mostly" on page 15.
- The quiet factory is always left of the flat-out factory in W3. Never swap them and never mirror a picture.
  W3 always shows the two as first described.
- Paint W3 before the other Works views: it is their style picture.
- A state changes only while the camera holds. Story changes happen on the spoken word that names them.
- The waiting men always face away from the camera or stand against the light, never nearer than about 6 m.
- No New Zealand or Japanese banknotes or coins anywhere: they carry real people's portraits.
- No supermarket chain's, bank's or party's colours; hi-vis orange, never yellow-and-black.
- The paid steps wait for your yes, batch by batch.
