# Shot plan - chapter 2 for newcomers, the full redesign (production plan)

Source for the story: Clara E. Mattei, *The Capital Order* (2022).

**What this is:** the plan for filming all 16 pages of "33 Script - chapter 2 - what really causes
inflation - for newcomers" (about 7 minutes) in the look you kept in log 32 ("Wow that's incredible. Yes
keep it."). Each place is a real 3D set built in Blender by script. It is drawn once from its main view
(the plate), repainted by Flux 3 in the series' painted style, and the painting is shone back onto the set
so the camera can slide without the picture tearing. Flames, flicker and smoke are drawn live on top, and
words on screen are typed cards.

This is the plan after two critics checked the earlier version. Every point they raised was checked
against the files on this machine; part 5 says what was fixed, what was fixed only in part, and why.
The shot list that goes with it, one entry per shot, is `shots.json` in the same folder.

Nothing here is built, painted or filmed, and no money has been spent. The paid steps wait for your yes.

## In short

- **6 places, 11 views, 30 shots, 9 slides** (never more than one on a page, never a turn).
  - **The Works**, the script's "our picture": two factories at the head of one lane, seen from 4 views,
    on 11 of the 16 pages.
  - **Five real places:** a New Zealand supermarket checkout, a New Zealand building site (busy, then
    stopped), a New Zealand kitchen table, a Glasgow street in 1915 (2 views), and a Japanese corner shop's
    counter in 2013.
- **The two factories look different at a glance.** The quiet factory has dark red-brown brick and one tall
  round chimney. The flat-out factory has pale buff-grey brick, two square chimneys and a water tank. Their
  gate boards say "No. 1" and "No. 2", short for Malina's "the first" and "the second".
- **Every camera stands where a person would stand, in line with the edge of its subject**, so the
  street's lines meet right beside it. The earlier plan had four views where they couldn't (the gates seen
  edge-on, the rent notice squashed at the frame's edge); those are rebuilt (part 5, T1 to T4).
- **People:** painted figures seen from behind at the Works' gates; dark silhouettes kept as their own
  surfaces where men face the camera (page 14); small far-off walkers in Glasgow; everywhere else an empty
  thing made for a person (a vest on a fence, a pushed-back chair). Tested first, for about 50 cents, in
  the pit village street that already exists.
- **Light tells imagined from real:** only the Works is in a blue dusk. Glasgow is a grey November late
  afternoon, the busy site has low warm sun, the stopped site is grey, the checkout is lit inside in the
  evening, and the kitchen and the corner shop are at night.
- **Words on screen: about 65 groups of words, about one every 6 seconds** (the earlier plan had about 130
  cards): names, every figure Malina says, the questions and guesses, the rule cards, the markers (A REAL
  CASE, IN OUR PICTURE, MATTEI ARGUES and the like) and labels that point at things.
- **13 plates and 20 paintings** for the film, plus 2 for the people test.
- **Money:** fal charges about 25 cents a painting (its price list: 2.4 cents a megapixel, counting the
  pictures sent as well as the one made).
  - Planned: **about US$7.20** (paintings US$5.50 with the test, narration US$1.10, up to four sketches
    US$0.60).
  - With ten repaints and a reserve for re-recording one page: **at most about US$10.00**, under the US$12
    line, leaving US$10 of the US$20 untouched.
- **Filming: about 5 to 6.5 hours for the whole chapter, plus 2 to 3 hours of re-filming** after the
  critics. That is about 1.5 to 1.8 seconds a frame, under the 2-second ceiling.
  - It holds only if the chapter loads just the pages each piece of film needs. Today it loads all 16
    pages for every 2-second piece. Changing that is free and comes first.
- **Work time: about 110 to 170 hours, so about 5 to 7 days of steady work.** The first thing you can watch,
  pages 3 to 5 at the Works, painted, comes after about 2 to 3 days.
- **The narration is recorded after 22 October**, when new price figures come out, and page 13 is checked
  again after 4 November's out-of-work figures.
- **Disk is the tightest limit:** about 6.5 to 7.5 GB at the peak against 8.5 GB free. I'll ask you before
  deleting any old files.

## Words used here

- **Plate:** the picture Blender draws of a set from a view, a little wider than the film's frame.
- **Painting:** Flux's repaint of a plate. It is shone back onto the set.
- **Behind painting:** a second painting of the same view with the near things painted out. The film shows
  it where they stood once the camera slides.
- **Helper plate:** an extra plate drawn with some things left out or changed (the men gone, the windows
  lit). Some are painted (part 3 lists which); comparing any of them with the plate shows where the
  painted shadows of what changed fall.
- **State picture:** a copy of a view's painting with one area taken from another painting of the same
  view (for example the men gone). It is made by a free image step (`composite_fill.py`), and the film
  swaps it in on a spoken word.
- **Time cut:** a cut within a held shot to the same view a moment later (the men already gone). It reads
  as time passing.
- **Own surface:** a thing that keeps its own sharp 3D surface instead of wearing the painting: every sign
  and every letter (the painter garbles small print), the Works' iron gates, and things that change on a
  word (a window lighting, a placard appearing, crates popping up).
- **Held shot:** the camera stays still. The set is drawn once, and only moving things (smoke, flames,
  cards, a swinging gate) are drawn each frame. A state change draws the set once more.
- **Slide:** the camera moves in a straight line toward its subject (or back), at the same height, starting
  and stopping gently, never turning. It ends on the **composed frame**.
- **Story group:** the few things that tell a shot's story, placed so they touch or overlap ("07 Composing a
  shot", rule 3).
- **The main rule:** where the lines meet, the brightest parts, the warm light and the story group all fall
  in one part of the frame, the part that holds the subject.
- **"In line with":** the camera stands so that, looking straight ahead, it faces the subject's edge. Where
  the lines meet depends only on which way the camera faces, so this is what puts the meeting point right
  beside the subject (rule 1; log 31: turning the camera can't close that gap).
- **Master painting:** the first painting of a place. Every later painting of that place gets it as its
  style picture, so they all match.
- **Positions in the frame** are fractions: 0 is the left or top edge, 1 the right or bottom edge. The
  **top band** (about 0.05 to 0.22 down) is kept dim for typed words; anything to be read stays left of
  0.90 across, clear of the phone's buttons.

---

## Where this plan came from

Two designers wrote plans independently. **"Strongest picture"** looked for the one picture that teaches
each page; **"One world"** used as few places as possible and kept coming back to them. A first synthesis
took Strongest picture as the spine (one memorable picture per idea, fewer paintings, held shots) and added
from One world: factories that differ by shape, the cards PICTURE TWO FACTORIES, A REAL CASE and IN OUR
PICTURE, the warning as a newspaper's words at the checkout, the munitions works and walkers in Glasgow,
the rent strike placards, the FOR RENT board, the painting chain (a master painting as everyone's style,
a colour check), and "a state changes only while the camera holds". It left out One world's invented
Reserve Bank tower and Tokyo cash room.

Then two critics went over it: one on whether the computer, the money and the schedule hold up, one on
teaching, pictures and accuracy. Their 37 findings were each checked against the files, the research
ledger, the lens and fal's price list. All the must-fix findings were real. Part 5 lists every finding
and what became of it; they are referred to here as F1 to F15 (computer, money and schedule) and T1 to
T22 (teaching, pictures and accuracy).

---

## People: how "workers wait at the gate" and crowds are shown

"Workers wait at the gate" is the chapter's central picture. It defines the quiet factory (page 3); its
absence defines the flat-out factory (pages 4 and 11); its return is the cure (page 12); and it is Mattei's
argument (page 14). A newcomer has to see people waiting, and see their number change, so an empty prop
alone won't do at the Works.

| Where | How | Why |
|---|---|---|
| The Works, seen from behind the queue: No. 1's gate (page 3), the small queue at No. 1 in the both-gates view (every time), No. 2's gate once it slows (page 12) | **Simple figure shapes that the painter turns into painted people.** Built by script in five poses (hands in pockets, arms folded, one hand on a gate bar, one stooped to the brazier, one leaning), long work coats and caps, dull browns and greys. Always backs to the camera, their faces turned to the gate and its light, so even a turned head is in shadow. **Never nearer than about 6 m** (about a quarter of the frame's height) | Waiting has to be seen and counted. An empty bench can't show waiting, or "more" |
| The Works, seen from inside No. 2's yard (page 14) | **Dark silhouettes kept as their own surfaces**, never painted: the same figure shapes in near-black wool, rimmed by the lamp-lit lane behind them, seen through the gate's bars, the nearest at about 6.5 m [T8] | These men face the camera (they face the gate). At 6.5 m a painted head would be about 58 pixels and the painter would paint faces |
| Glasgow, the street to the works (pages 6 and 7) | **About 14 small walking figures 40 to 80 m up the street**, backs to us, men and women with bundles, heading for the munitions works' gate [T20] | "Crowds of war workers had come to Glasgow". At 50 m a figure is about 56 pixels tall, too small for a face. The first thing to go if painted people fail; the label then points at the works' gate |
| Glasgow, the close mouth (page 7) | No people. A suitcase with a blanket bundle on the step under the rent notice; placards appearing in the lit windows | A newcomer with nowhere to go; the placards count the families |
| New Zealand and Japan | No people. The hi-vis vest on the digger's door and the hard hat on the timber; the vest hung on the shut fence and gumboots by the post; the chair pushed back with a cardigan; the basket at the counter | Present-day painted people risk looking like real, recognisable people |
| The Works after the men go in | The brazier still burning by the empty pier, a lunch tin on the coping | "They've just gone in" (the notice corner's empty-chair idea, rule 9) |
| Inside the flat-out factory's yard | A jacket and cap on a nail, his mug and a pay envelope lettered WAGES on an upturned crate [T8] | Someone with a job, and the wages the queue outside puts pressure on |

**How the men come and go.**
- The men are in the main painting. The other painting of the same view has them left out (W1's
  "working" painting, drawn from a helper plate with the men gone and the windows lit; W2's flat-out
  painting). Swapping between the two, only inside the men's outlines and the area where their painted
  shadows fell (found by comparing the two plates), gives a **state picture** with the men gone or come.
- On the spoken word, the film makes a **time cut** to the state picture: the men are simply gone (page 3)
  or there (page 12). It reads as time passing, costs one redraw of the set, and can't look like ghosts.
  [T9]
- If a fresh helper finds the cut reads as a glitch, the fallback is a 1.2-second blend between the two
  held frames, hidden inside the gate's swing. Both frames are drawn once, so a blend costs two set draws,
  not one per frame. Things that fade are built see-through from the start, so they don't snap off halfway
  (lesson 87).

**Painter words for figures:** "Keep every figure exactly where and as it is: a dark painted worker seen
from behind. No faces, no new people, no details added."

**What could go wrong, and how it is caught:**
- The painter adds faces, turns figures round, adds or loses people, or makes them look like photographs
  or shop dummies. Caught by counting the figures in each painting against the plate's outlines (the shot
  checker lists each figure as a prop) and by a helper looking at every painting at full size.
- The men's painted shadows stay after they leave: the area taken from the other painting includes where
  the shadows fell, measured from the two plates.
- The silhouettes on page 14 look like 3D mannequins next to the paint: they are near-black against a lit
  lane, with only a rim of light; the people test films one beside painted figures first.
- The Glasgow walkers read as soldiers marching: no rifles, no step in time, mixed men and women with
  bundles. The history helper checks.

**The people test comes first** [F6], before anything is built for the chapter: five figure poses stood
in a copy of the pit village street near the notice corner (the kept shot itself is not touched): four from
behind at 6 to 9 m by the brazier, one facing the camera against the lit street at 7 m, and six small
walkers 40 to 60 m up the street. One plate, one helper plate without them, and two paintings (about 50
cents, with your yes). It is filmed both ways: painted figures leaving by a time cut, and the dark
own-surface silhouettes over the painting without them.

**Fallbacks, in order:**
1. Repaint with plainer words and darker backlight (about 25 cents).
2. Silhouettes kept as their own surfaces everywhere (as on page 14).
3. No figures at all: caps and lunch tins along the wall's coping and empty stools by the gate, with
   "more workers" shown by more stools. The time cut then removes the caps.

The Glasgow walkers go first, at step 1.

---

## 1. The places

**Every view keeps the top band dim and quiet** (sky, a dark wall or a dark ceiling) for the typed words,
away from the brightest lamp; a soft dark band sits behind any words that cross smoke or a chimney [T13].

**The lettering rules apply to every set:**
- Every sign carries real lettering, era-correct, and keeps its own surface in every view, near or far.
- In-world lettering carries names, or a short form of what Malina says. It never carries a figure she
  doesn't say: no prices, door numbers, lane or close numbers, dates, sizes or phone numbers.
- **Two stated exceptions**, each marking an era and each checked by the history helper: the recruiting
  poster in Glasgow (page 6) and the PLEASE SANITISE YOUR HANDS sign on the site's gate (page 10). Neither
  carries a figure [T17].
- Every invented name is searched before it is built, and changed if a real business of that name exists
  in that place.
- No logos, no flags, no shop chain's or bank's colours, and no large flat areas of a party's colour (the
  election is on 7 November). Hi-vis is orange, never yellow-and-black.

| Place | What and when | Views | Plates | Paintings | Pages |
|---|---|---|---|---|---|
| A. The Works | imagined, undated: two factories at the head of a short lane, blue dusk | W3 both gates, W1 No. 1's gate, W2 No. 2's gate, W4 No. 2's gate from inside the yard | 6 | 8 | 3, 4, 5, 6, 9, 10, 11, 12, 14, 15, 16 |
| B. The checkout | New Zealand, 2025-26, a small suburban supermarket, evening, inside | C1 | 1 | 2 | 1, 15, 16 |
| C. The corner shop | Japan, 2013, a family-run corner shop's counter at night | J1 | 1 | 1 | 8, 9 |
| D. The building site | New Zealand: busy (2020-22) in low late-afternoon sun; stopped (2026) under a grey sky | S1a, S1b | 2 | 3 | 2, 10, 11, 13 |
| E. The kitchen | New Zealand, 2022-23, a kitchen table at night | K1 | 1 | 2 | 12, 13 |
| F. Glasgow | 1915, a tenement street on a grey November late afternoon, the gas lamps just lit | G1 street to the works, G2 close mouth | 2 | 4 | 6, 7 |
| | | **11 views** | **13** | **20** | |

### A. The Works (the model: "our picture")

**Layout (all sizes about; the shot checker settles them):**
- A short cobbled lane, about 22 m long, with a carriageway of about 6 m and pavements of about 2.2 m,
  between terraces of cottages with gas lamps. At its mouth it meets a cross street; across that stands
  an end house whose upstairs window looks straight up the lane (W3's camera).
- The lane ends at one long works wall, about 4 m high with a stone coping. In it are two iron gates,
  each about 3 m wide, each at the head of its own pavement: No. 1's on the left, No. 2's on the right,
  about 7 m apart centre to centre.
- Between the gates, behind the wall, a high dividing wall splits the two yards, so the two works read as
  two places, not one [T15].
- Behind the wall, each works' mill front stands about 8 m back, its upper windows showing over the wall.
  Each works' chimney stands at the back of its yard, about 35 m behind the wall and about 25 m tall, in
  line with its gate's outer pier. Set that far back, it shows in every view from the lane: above its own
  gate in W1 and W2, and small above the other gate's side, so each gate view also shows the other
  factory's chimney.
- In the lane's last third on the left, about 20 to 24 m from W3's camera, stands a small stone-fronted
  bank: a barred window (its own glass, dark until page 9) and a hanging sign **"BANK"** on a bracket,
  square to the lane, so W3 sees it face-on [T2, T10].
- Beyond the works, the far town: chimneys, a gasholder, a spire.

**Era and place:** none on purpose. It is "our picture", not a real case: sign-writer's lettering, gas
lamps and brick that could be any industrial town of the early twentieth century. **Its light is its own:**
one blue dusk (sky brightness about 1.4 to 1.96, as at the notice corner), which no real place uses, so
the cut from a real place to the Works is seen, not only read [T14].

**Fixed looks, the same in every view:**

| | The quiet factory (No. 1, always on the left) | The flat-out factory (No. 2, always on the right) |
|---|---|---|
| Brick | dark red-brown | pale buff-grey (`white_sandstone_bricks`, toned) |
| Chimneys | one tall round chimney | two square chimneys, and a water tank on a steel trestle |
| Roof | four-bay sawtooth | long pitched shed roofs with a roof lantern |
| Gate | dark iron, chained and padlocked when quiet | dark iron |
| Gate board | "No. 1", cream sign-writer's lettering on near-black | "No. 2", the same |

The factories differ by shape first (round against square chimneys, the tank), because shapes survive the
painter and a phone screen better than colours. No large red, blue, green or yellow-and-black areas.

**States, and how each change is made without another painting:**

| | windows | chimney | gate (own surface) | at the gate | made from |
|---|---|---|---|---|---|
| No. 1 quiet | dark | cold | shut, chained | 7 men waiting (about 6 m of queue), a brazier, a lit lantern | W1's main painting |
| No. 1 working (page 3, from "go") | lit (a blend on "start") | smoking (live) | open | nobody; the brazier still burning, a lunch tin on the coping; crates pop up on "things" (own surfaces) | W1's working painting, as state pictures |
| No. 2 flat out | blazing, flickering | heavy smoke from both (live) | wide open, crates inside the gateway, a handcart's shafts over them | nobody; the gateway's warm light on the empty pavement | W2's main painting |
| No. 2 slowed (page 12) | a third lit (a blend on "slows") | thin smoke from one (live) | half shut | 8 men waiting | W2's slowed painting, as state pictures |

- **The gates are never in a plate.** Their leaves are own surfaces in every Works view, so one painting
  serves a gate shut, open or half shut, and the bars stay sharp (the painter would garble them) [new].
- The both-gates view (W3) always shows the two as first described: No. 1 quiet, No. 2 flat out.
- All four states' settings (window brightness, smoke amount, gate angle, how many men) live in one shared
  page module, `works-effects.js`, with the same smoke and flicker seeds on every page.

**The views** (each camera is level, at a person's spot, and never turns; numbers are what the lens
works out to and the shot checker confirms):

- **W3, both gates (the main view, painted first).**
  - Camera: the upstairs window of the end house across the cross street, on the lane's centre line, about
    30 m from the works wall, eye about 4.6 m up, facing straight up the lane. The shot checker compares
    heights from 4.5 to 7 m, and the far pavement of the cross street at standing height as a fallback
    [T2]. This is your own rule from decision 25: "Move up to see the bigger picture".
  - The lane's lines meet on the wall between the two gates, at the pier's head (about halfway down the
    frame).
  - Two columns: on the left, No. 1's round chimney (its top about a quarter of the way down), its mill,
    its shut gate (about 0.33 across), the brazier and the queue; on the right, No. 2's two smoking square
    chimneys and tank, the open lit gateway (about 0.67 across), crates, and a handcart of crates coming
    up the right pavement into the bottom third. The queue's tail reaches toward the bottom third on the
    left, so both columns run from top to bottom (rule 7).
  - The bank on the left (about 0.1 to 0.2 across, its sign about 22 pixels a letter), dim until page 9.
  - Brightest part: No. 2's gateway, beside the meeting point. The brazier is second.
  - No in-world lettering here is needed to be read: the boards are about 16 to 27 pixels a letter, and
    typed tags carry the names.
- **W1, the quiet factory's gate** [T1].
  - Camera: on the lane's left pavement, standing in line with the left pier of No. 1's gate (where the
    brazier is), 13 m from the gate at the plate's spot and 11.8 m at the composed frame, eye height about
    1.7 m, facing straight up the lane.
  - The lines meet at the pier's edge, at the middle of the frame. The gate is face-on just right of it
    (about 0.5 to 0.88 across), its "No. 1" board about 41 pixels a letter.
  - The queue stands in single file along the pavement just right of the camera's line, backs to us, each
    man overlapping the one in front, leading the eye to the gate. The nearest is about 6 m away.
  - Story group: the shut gates with chain and padlock; the brazier against the left pier, its rim clearly
    overlapping the pier's base; the front man beside it, one hand on a gate bar; a lit lantern and a lunch
    tin on the coping above the third man; two drums stencilled PETROL and DIESEL against the pier.
  - Column: No. 1's chimney rises straight above the meeting point; its mill's upper windows show over the
    wall (about 0.14 to 0.33 down); the board, the gate, the brazier below. Small at the upper right (about
    0.75 across), No. 2's two square chimneys say which side we're on. No. 2's gate is out of frame to the
    right.
  - If the gate's right edge crowds 0.90, the camera slides sideways toward the gate's centre, so the lines
    meet on the chain; the shot checker compares the two spots.
- **W2, the flat-out factory's gate.**
  - The mirror of W1 on the right pavement, in line with the right pier of No. 2's gate, the same distances
    and lens, so a cut between the two compares like with like. The gate is face-on just left of the
    meeting point (about 0.12 to 0.5 across).
  - From exactly where a waiting man would stand, but nobody is ahead of us: the gateway's warm light lies
    on the empty pavement. The same PETROL and DIESEL drums stand against No. 2's pier (page 11 points at
    them, and page 15 comes back to them).
  - Small at the upper left, No. 1's single round chimney, cold.
  - On page 12 the 8 men stand in single file along the pavement just left of the camera's line.
- **W4, No. 2's gate from inside the yard.**
  - Camera: where a worker on his break would stand, in line with the gate's hinge post, 7.2 m from the
    gate at the plate's spot and 6.0 m at the composed frame, facing straight out through the gate and down
    the lane.
  - Story group: the half-shut gate leaf; the jacket and cap on a nail on the inside post; an upturned
    crate against the post's foot with a tin mug and a pay envelope lettered **"WAGES"** (a short form of
    Malina's "higher wages") [T8].
  - Through the bars: the lamp-lit lane and the queue of 8, standing on the pavement in line with the gate
    (so the wall doesn't hide them), as dark own-surface silhouettes, the nearest just outside at about
    6.5 m.

**Reused files, and the changes they need** [F4, F5]:
- `paper-film/blender/build_factory.py`, run twice (about 4 to 6 hours of changes). Today it builds a small
  model (the shed is 3.2 x 2.0 x 1.3) with a tapering square chimney, a sawtooth roof, a water tank on every
  factory, every window in one merged glowing piece, and a shading bake. It needs:
  - a round chimney for No. 1, and two square stacks for No. 2, placed at the back of each yard;
  - a pitched roof with a roof lantern for No. 2;
  - the water tank switched off for No. 1;
  - windows kept as separate pieces in groups, so the plates can be drawn with some lit and some dark;
  - a scale-up done after building, then every surface re-mapped at true scale (rather than a scale
    threaded through hundreds of fixed sizes, which would also give giant bricks);
  - no shading bake (Blender draws the plate itself; the option `--no-bake` exists);
  - its blank sign board lettered or removed (decision 34).
- `paper-film/blender/build_town.py`: the far town, scaled up the same way (about 1 hour). The old models in
  `assets/models/inflation-chapter-2/` stay as they are.
- `paper-film/blender/pit-village/build_street.py`: today it takes no settings and always writes
  `assets/models/pit-village/street.blend`, `street.glb` and `camera.json`, which the notice corner (the shot
  you kept) is built on. It gets an output folder and settings for the colliery (off), the lane's width and
  the slope (level). `set_dressing.py`'s `export_for_film` gets an output folder, and its ground fallback
  (the pit street's 4-degree slope) a setting. About 1 to 2 hours; then the notice corner is rebuilt once
  to show it is unchanged.
- From `assets/models/pit-village/props/` (46 props): `iron-gates-pair.glb` (separate left and right leaves,
  so they can swing), `brazier-drum.glb`, `hurricane-lantern.glb`, `gas-lamp-post.glb`,
  `gas-lamp-wall-bracket.glb`, `handcart.glb`, `wooden-chest.glb` (the crates), `wooden-barrel.glb`,
  `dustbins.glb`.
- In `props/build_scripted_props.py`: the colliery name board's builder, re-lettered for the gate boards
  and the bank's sign.
- `assemble_notice_corner.py` as the pattern for each view's assembly script.
- Surfaces in `assets/models/pit-village/textures/`: `red_brick`, `castle_brick_02_red`,
  `large_sandstone_blocks`, `square_cobblestone`, `roof_slates_03`, `rusty_metal_02`, `dusk_sky`, and the lit
  and dark window pictures.

**Built new by script, with the lettering each carries:**
- the works wall with its two gate arches, copings and piers, and the dividing wall behind;
- two gate boards, **"No. 1"** and **"No. 2"**;
- the bank front: stone, a barred window with its own glass and a shallow lit room, a brass plate and a
  hanging sign, both **"BANK"**;
- two steel drums by each gate stencilled **"PETROL"** and **"DIESEL"**, dull grey-black (the stencils are
  own surfaces);
- crates stencilled **"THIS WAY UP"** (the stencils are own surfaces);
- a chain and padlock; a lunch tin; a jacket and cap on a nail; a tin mug; a pay envelope **"WAGES"**;
- figure shapes in five poses (the same shapes serve as the silhouettes on page 14).

**Fetch from Poly Haven** (free for any use; names checked in its list): model `hand_truck` (No. 2's yard);
surfaces `white_sandstone_bricks` (No. 2, toned buff-grey) and `large_red_bricks` (No. 1's piers).

**Light:** the blue dusk. The people's own lights: a gas lamp on each gate pier; the brazier and the
lantern at No. 1; No. 2's windows and lit gateway; the bank's window on page 9.

**Plates and paintings:** 6 plates, 8 paintings.
- W3: 1 painting (always held). It is the master for every other Works painting.
- W1: the main painting (quiet: the men, the windows dark) and the **working painting**, painted from a
  helper plate with the men gone and the factory windows lit, with W1's main painting as its style. It
  serves as the behind painting for the slide and as the source of every page 3 state picture [new: the
  painter paints the real lit windows and pavement, rather than guessing what the men hid].
- W2: the main painting flat out (seen on pages 4, 5, 6, 11 and 12, about 50 seconds), its behind
  painting, and a **slowed painting** from a plate with the men and two thirds of the windows dark, with
  the flat-out painting as its style, used only where it differs (page 12, about 5 seconds) [F9].
- W4: the main painting (no men, no gate leaves: both are own surfaces) and its behind painting.

### B. The checkout (New Zealand, 2025-26)

**What it is:** one checkout lane of a small suburban supermarket in the evening: the belt, the till, the
card terminal on its stand, the bag rack with reusable bags (single-use plastic bags were banned in 2019)
[T18]. Behind them, the ends of two aisles and the window to the car park; across the road, small and dim,
a petrol station's canopy.

**View C1:**
- Camera: where the next shopper in the line stands, in line with the edge of the newspaper bill, 3.1 m
  from the basket at the plate's spot and 2.4 m at the composed frame; eye height 1.6 m, level, looking
  along the belt [T4]. The basket then sits about 0.75 down the frame, above the strip where phone apps
  show captions. The slide is 1.3 times at most, which the painting can stand [F13].
- The belt's lines meet at the bill's edge, just above the basket.
- Column: the dark ceiling (the top band), the bill with its big words, the basket.

**Story group:**
- a full grey wire basket on the belt: bread in a paper bag, milk in a plastic bottle, butter, cheese,
  kiwifruit, apples, bananas hanging over the rim, so a hundred dollars is believable on page 15 [T18];
- the divider bar against the basket's front;
- a **newspaper bill** in a wire stand at the counter's end, its edge overlapping the basket's far side: an
  invented masthead and four or five big words, **"NEW MONEY: PRICES WILL GO UP"**, about 0.1 m tall, so
  about 60 pixels a letter, readable on a phone [T12]. The typed label THE WARNING points at it;
- the card terminal beyond, its keypad turned away (no digits).

A warm lamp over the belt makes the basket and the bill the brightest things.

**Built new by script, with lettering:** the counter, belt, divider bar, card terminal (screen dark), till,
bag rack and bags, wire basket; groceries labelled **"BREAD"**, **"MILK"**, **"BUTTER"**, **"CHEESE"**, with no
sizes or prices; a hanging **"CHECKOUT"** sign with no lane number; the bill stand and bill (the masthead
must not use "Herald", "Times", "Post", "Press", "Star" or any real paper's word, and is searched first);
the petrol canopy's fascia **"PETROL · DIESEL"**, no brand, its price board edge-on. No shop name on the
window (from inside it would read backwards) [new]. No price tags. Neutral greys and wood: no chain's green,
red or yellow.

**Fetch from Poly Haven:** models `food_kiwi_01`, `food_apple_01`, `bananas`, `lemon`, `food_avocado_01`,
`steel_frame_shelves_01`, `mounted_fluorescent_lights`, `cardboard_box_01`, `plastic_crate_02` (not `_01`,
which carries a brand print) [F11]; surfaces `large_floor_tiles_02`, `painted_plaster_wall`,
`ceiling_interior`.

**Light:** evening. The ceiling rows near the camera switched off for closing time, which leaves a dark
patch of ceiling for the typed words [T21]; a warm lamp over the belt; the window blue-black.

**Plates and paintings:** 1 plate; 2 paintings (main and behind: page 1 slides in, page 16 slides out).

### C. The corner shop (Japan, 2013)

**What it is:** the counter of a small family-run corner shop at night, not a chain store. It has the till,
a glowing hot-food cabinet and shelves behind. Through the window, across the night street, is a bank
branch with its shutter down and its small cash-machine corner lit. It is built from B's script, so it
rhymes with page 1: another country's basket at another checkout.

**View J1:** where the next customer stands, about 2.4 m from the basket on the counter, eye height 1.6 m,
level, in line with the edge of the till [T4].

**Story group:** a basket on the counter with rice balls, a bottle of tea and a carton of milk, touching the
till's edge; a change tray in front; the hot-food cabinet against the till's other side.

**Built new by script (a second dressing of B's script), with lettering in correct Japanese, read by a
helper who reads Japanese:** labels **おにぎり** (rice ball), **お茶** (tea), **牛乳** (milk); a small **レジ**
(checkout) sign over the counter; across the street **銀行** (bank) on the shutter's fascia and **ATM** at the lit
corner, with no bank's name. No drinks machine (its buttons would show prices), no prices, no chain's name.
(A Japanese font, IPAGothic, is installed.)

**Fetch from Poly Haven:** models `plastic_crate_02`, `steel_frame_shelves_02`, `modular_electricity_poles`
(it is a 131 m kit of about 200,000 polygons: one pole is cut out before converting, or the converter's
thinning would wreck it) [F11], `modular_electric_cables`, and `mounted_fluorescent_lights` (shared with B);
surface `interior_tiles`.

**Light:** night. One row of shop lights over the counter; the ceiling above the camera dark for the words
[T21]; the hot-food cabinet's orange glow on the basket. The bank across the street is dim, but brighter
than the street around it.

**Plates and paintings:** 1 plate; 1 painting (held only).

### D. The building site (New Zealand, 2020-26)

**What it is:** a suburban section where a timber-framed house is going up (pine frame, building wrap,
scaffolding), behind temporary mesh fence panels, between finished weatherboard houses with corrugated iron
roofs. A driveway runs from the fence gate into the section.

**Views S1a (busy) and S1b (stopped), the same camera:** on the footpath at the site's gate, in line with
the edge of the digger's cab, about 6 m from the digger, eye height, level, looking straight up the driveway
[T22]. The driveway's edges, the neighbours' side walls and the scaffold planks meet at the cab's edge. (Seen
along the fence, the gate would be edge-on, the trap the critics found at the Works.) In S1b, where the
digger stood, the shot checker confirms the meeting point falls on the timber stack's edge.

**S1a, busy (pages 2, 10, 11), in low late-afternoon sun:**
- The gate is open. Just inside it, all touching: a faded-orange mini digger with its bucket on the ground,
  a strapped packet of fresh timber against its track, the orange hi-vis vest hanging on the digger's door,
  a white hard hat on the timber.
- The neighbour's fence carries a **"FOR RENT"** board (own surface, hidden until "rents" on page 11).
- On page 10 only, a plain **"PLEASE SANITISE YOUR HANDS"** sign on the gate (own surface, words only: none of
  the government's yellow-and-white stripes, no QR code poster) [T18].

**S1b, stopped (2026, page 13), under a grey sky:**
- The gate shut with a chain and padlock, close in front of us.
- The hi-vis vest hung over the fence rail on our side, gumboots by the post.
- The digger gone, a flattened patch where it stood; the timber grey under a torn cover; the frame no
  further on; grass along the fence.
- Because its light differs (grey, no sun), S1b is a whole painting from its own plate, with S1a's painting
  as its style, not a patch of S1a [new, after T14]. Same cost.

**Built new by script, with lettering:** the mini digger (no maker's name); the timber packet; the house
frame with wrap (an invented wrap maker's name, searched); scaffolding; mesh fence panels with feet; the
gate, chain and padlock; the hi-vis vest (orange) and hard hat (white); the builder's banner on the fence
(an invented builder's name only, searched); two weatherboard neighbours; the FOR RENT board (no phone
number); the sanitise sign; the torn cover.

**Fetch from Poly Haven:** models `rubber_boots` (gumboots), `cement_bag` (its printed brand and icons
replaced by the word **"CEMENT"**), `security_light`, `ladder_sectioned_01`, `sledgehammer_01`. The portable
generator is dropped (yellow, with branding) [F11]. Surfaces `weathered_plank_siding`, `corrugated_iron`,
`worn_corrugated_iron`, `plywood`, `coated_pine`, `oriented_strand_board`, `raked_dirt`,
`concrete_pavement`, `clean_asphalt`, `gravel`.

**Light:** S1a low warm sun from the side, the story group lit, the background houses in their own shade;
S1b flat grey, no work light, colder.

**Plates and paintings:** 2 plates; 3 paintings (S1a main and behind, for page 11's slide; S1b).

**The fact this picture could claim:** the ledger has no line on New Zealand building slowing in 2023-26.
NOT THE ONLY REASON stays on screen from the word "only" through every later shot of S1b, and the fact
helper is given the picture itself (lesson 83) [T19].

### E. The kitchen (New Zealand, 2022-23)

**What it is:** a small kitchen at night. A table stands by a window (a dark garden, a neighbour's lit
window). The pendant lamp hangs above the frame, its light pooled on the table.

**View K1:** seated in the chair across the table from the pushed-back one (eye about 1.2 m), in line with
the letter's edge, 1.85 m from the letter at the plate's spot and 1.42 m at the composed frame, level [T4].
The slide is 1.3 times at most [F13]. The letter then sits about 0.7 to 0.78 down the frame.

**Story group:** the opened letter from the bank **propped against a mug, facing us**, as if slid across the
table to show someone (lying flat it would be squashed to a third of its height and unreadable) [new]; its
torn envelope under it; reading glasses folded on it; a phone face down; across the table, the chair pushed
back at an angle with a cardigan over it.

**Built new by script, with lettering:** the room, window and bench; the letter (own surface): **an invented
bank's name** (searched against every New Zealand bank; never a bank's colours), **"Your home loan"** and
**"Your new interest rate"**, with no figures and no date; the envelope, mug, phone, cardigan, and a plain
modern kettle on the bench.

**Fetch from Poly Haven:** models `dining_table`, `dining_chair_02`, `round_spectacles`,
`modern_ceiling_lamp_01`, `potted_plant_01`; surfaces `laminate_floor`, `painted_plaster_wall`. (The
`vintage_electric_kettle` is dropped: it is a rusted antique, wrong for a 2022 kitchen.)

**Light:** night. The lamp's warm pool on the letter, the brightest thing; the window blue-black, where the
interest rate dial is drawn on pages 12 and 13.

**Plates and paintings:** 1 plate; 2 paintings (main and behind: page 12 slides).

### F. Glasgow (1915)

**What it is:** a level street of four-storey red and blond sandstone tenements, with shops at street level,
arched close entrances, granite setts and gas lamps. At the far end, about 120 m away, the high wall and
arched gate of a munitions works, lit and smoking: a blank wall, tall shed roofs with a furnace glow and
several thin iron stacks, unlike both model factories. **Its light is a grey November late afternoon, the
gas lamps just lit**, so it never looks like the Works' blue dusk [T14].

**G1, the street to the works (page 6, and the start of page 7):**
- Camera: on the right-hand pavement, an arm's length in from the kerb, in line with the munitions works'
  gate, eye height, level, facing straight down the street. The street's lines meet at the works' gate.
- Just right of the meeting point (about 0.6 to 0.8 across, 8 m away at the plate's spot), across the next
  side street, a corner grocer's splayed corner window faces us. The story group: its tiered display
  **thinning out**, with gaps between stocked stands and a half-empty tier, not bare (the ledger puts the
  worst shortages in 1917, C2-XA02) [T5]; an empty wicker basket at the stand's foot; a slumped flour sack
  by the door frame; the brass till in the gas light; and on the pilaster beside the window, overlapping its
  frame, a text-only recruiting poster, with a gas lamp above it.
- Up the street, about 14 small walkers, 40 to 80 m away, heading for the works' gate [T20].
- One picture holds both halves of page 6: no spare workers (the poster, the works flat out, people going
  to work) and fewer things to buy (the thinning window).

**G2, the close mouth (page 7)** [T3]:
- The close faces the camera: it is in the tenement at the head of a short side street (a T-junction).
- Camera: on that street's left pavement, in line with the close arch's right edge, 8.0 m from the close at
  the plate's spot and 6.5 m at the composed frame, eye height, level, facing straight up the street. The
  lines meet at the arch's edge.
- Story group: the factor's notice on the pilaster beside the arch, face-on (its heading about 23 pixels a
  letter); directly below it on the step, a suitcase with a blanket bundle tied on top; the close's gas
  bracket just inside the arch, lighting the notice from the side and below.
- The facing tenement's windows are face-on, with their own glass, so they light in a ripple and take
  placards. The nearest ground-floor window beside the close, about 7 m away, holds a placard with letters
  about 0.12 m tall, about 28 pixels.
- On the quiet side of the frame: the half-built tenement, scaffold poles and a wall stopped at the second
  floor.
- The close is painted plain, with a two-tone painted band (the rent-strike districts, such as Govan and
  Partick, mostly had plain painted closes; glazed tiles mark better-off tenements) [T17].

**Reused:** `build_street.py` (after its settings change): setts, kerbs, flagstones, gutters,
`build_sash_window`, `build_front_door`, chimney stacks, slate roofs, downpipes, gas lamps; the cottage shell
raised to four storeys with ashlar fronts. `build_factory.py`'s parts for the munitions works' sheds. The
notice-paper builder in `props/build_scripted_props.py`, for the factor's notice and the poster. Props
`gas-lamp-post.glb`, `gas-lamp-wall-bracket.glb`, `handcart.glb` (re-lettered), `wicker-basket-tray.glb`,
`wooden-chest.glb`, `dustbins.glb`, `milk-can.glb`. Surfaces `square_cobblestone`, `large_grey_tiles`,
`roof_slates_03`, `stone_brick_wall_001`, `red_brick`, `large_sandstone_blocks`.

**Built new by script, with lettering (every line checked by the history helper before building):**
- a tenement block builder: four storeys, sash windows with own-surface glass, close arches, shopfronts;
- the corner grocer's fascia **"W. ANDERSON · FAMILY GROCER"** (invented, searched); tins **"TEA"**, **"COCOA"**,
  **"SYRUP"**; a brass till (built by script: Poly Haven's cash register carries decals) [F11];
- the recruiting poster, text only, no portrait, no flag, in the wording of a real 1914-15 text-only poster
  the history helper confirms from a source, **with no figures** (no ages, heights, numbers of men, poster
  number or printer's line) [T17];
- the munitions works' wall and gate, with an invented engineering company's name (searched) and
  **"WORKS ENTRANCE"**;
- the factor's notice: **"NOTICE TO TENANTS. Take notice that the Rents of these Houses will be Increased. By
  Order, THE FACTOR."** No figures, no date, no names;
- the half-built tenement with timber scaffold poles and putlogs, a few planks missing, weeds; a builder's
  board **"J. LAIRD · BUILDER"** (invented, searched); a brick stack under a tarpaulin;
- the suitcase with its blanket bundle, built by script (Poly Haven's carries travel stickers) [F11];
- twelve rent strike placards in hand-painted capitals, worded only from a 1915 photograph the history
  helper confirms; otherwise **"RENT STRIKE"** alone. Never WON, never RENTS FROZEN;
- about 14 small walking figure shapes;
- no close numbers, house numbers or street names.

**Fetch from Poly Haven:** surfaces `red_sandstone_wall`, `sandstone_blocks_05`.

**Light:** grey late afternoon; street gas lamps just lit; the close's gas bracket; the grocer's gas mantle
inside; the works' gate and furnace glow at the end; tenement windows lit live on page 7.

**Plates and paintings:** 2 plates; 4 paintings (G1 main and behind, G2 main and behind).

**If Glasgow runs long:** page 6 can use the pit village street, already built, dressed for 1915 with the
poster and a thinning shop window. Page 7 still needs the tenements.

---

## 2. The shots, page by page

**How to read each shot** (the same shots, with the same words, are in `shots.json`):
- **Camera:** each view's spot is in part 1: a person's spot, level, in line with the subject's edge, never
  turning.
- **Move:** none, or one slide of about 3 to 4 seconds that starts and stops gently and stops on the view's
  composed frame. Each slide says why it is essential (your rule: "still unless it's essential to land an
  important point"). No slide brings its subject more than 1.3 times nearer, so the painting stays sharp
  [F13].
- **Events** start on the quoted spoken word. A word spoken more than once on the page is asked for by its
  count, for example "spent" (2). Times are from the estimated timeline
  (`film-kit/examples/inflation-chapter-2-newcomers/timeline-estimated.json`); the events follow the real
  recording, because they are tied to words.
- **A state changes only while the camera holds.** Cards may change during a slide.
- **Words on screen** are typed in the kit's plain heavy type (`graphics.js`) in the top band, left of 0.90
  across. Only figures Malina says. Small source credits (STATS NZ, US FEDERAL RESERVE, THE CAPITAL ORDER)
  carry no figures. A card stays until the next one replaces it or the page turns [T6].
- **Cost of a frame on this computer** (measured on the notice corner [F3]): held with nothing live about
  0.8 s; held with smoke, flames or flicker about 1.05 s (two helpers at once) to 1.5 s (one); moving about
  5.6 to 7 s, with no gain from two helpers at once.
- **Between pages:** the series' page peel, 0.3 s after the last word. Pages 4 into 5 and 8 into 9 run on
  in the same frame with no join; page 10 into 11 is a plain cut on "Close", because the guess hold fills
  the pause [new]. Inside a page: plain cuts.

### Page 1 - The question (0.0 to 28.1 s)

**Must teach:** inflation is prices in general going up, the whole basket; the warning; why it matters (the usual cure makes many loans cost more and can put people out of work).

**Shot 1a - C1, the basket at the checkout, with the newspaper bill's warning beside it (0.0 to 28.1 s, about 28 s).**
- Move: one slide of 0.7 m toward the basket (3.1 m to 2.4 m), from 'same' to 'inflation'. Why: we step up to our own basket.
- Events, each on its spoken word:
  - "felt", 1.4 s: the picture fades up from dark.
  - "same", 3.4 s: the slide starts: 0.7 m toward the basket.
  - "inflation", 7.3 s: the slide stops on the composed frame; INFLATION.
  - "general", 8.9 s: PRICES IN GENERAL, GOING UP under it.
  - "whole", 10.8 s: small up-arrow tags spring up beside every item at once (arrows only, no prices).
  - "warning", 12.8 s: the tags fold away; the label THE WARNING with a thin line to the newspaper bill, whose own lettering reads NEW MONEY: PRICES WILL GO UP.
  - "always", 17.7 s: IS THAT ALWAYS TRUE?
  - "cure", 22.4 s: THE USUAL CURE.
  - "loans", 23.3 s: → MANY LOANS COST MORE.
  - "out", 25.9 s: → OUT OF WORK.
  - 27.2 s: page peel.
- Words on screen: **INFLATION** (top band); **PRICES IN GENERAL, GOING UP** (small, under it); **THE WARNING** (label with a thin line to the newspaper bill); **IS THAT ALWAYS TRUE?** (top band); **THE USUAL CURE → MANY LOANS COST MORE → OUT OF WORK** (top band; builds word by word).
- Light effects: none live. Cost: about 0.8 s a frame held; about 5.6 to 7 s a frame during the slide.

### Page 2 - Who can create new money (28.1 to 47.7 s)

**Must teach:** here, the Reserve Bank can create new money (and tries to stop prices going up too fast); economists who study how modern money works argue that our government can't run out of its own money, but it can run out of workers, materials and machines.

**Shot 2a - S1a, workers, materials and machines: the three things touching just inside the open gate (28.1 to 47.7 s, about 20 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Reserve", 31.6 s: THE RESERVE BANK (typed, no logo).
  - "can" (2), 32.3 s: CAN CREATE NEW MONEY under it.
  - "economists", 36.5 s: the Reserve Bank card clears; ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS.
  - "argue", 39.6 s: ARGUE: is added.
  - "money" (3), 42.2 s: OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY.
  - "But", 43.0 s: BUT IT CAN RUN OUT OF...
  - "workers", 44.2 s: label WORKERS with a thin line to the vest and hard hat.
  - "materials", 45.0 s: label MATERIALS to the timber.
  - "machines", 45.7 s: label MACHINES to the digger.
- Words on screen: **THE RESERVE BANK** (top band); **CAN CREATE NEW MONEY** (small, under it); **ECONOMISTS WHO STUDY HOW MODERN MONEY WORKS ARGUE:** (top band (smaller heading)); **OUR GOVERNMENT CAN'T RUN OUT OF ITS OWN MONEY** (under it); **BUT IT CAN RUN OUT OF...** (under it, replacing the line above); **WORKERS** (label → the vest and hard hat); **MATERIALS** (label → the timber); **MACHINES** (label → the digger).
- Light effects: none live. Cost: about 0.8 s a frame held.

### Page 3 - The quiet factory (47.7 to 75.1 s)

**Must teach:** the two-factories picture, each one standing for a whole country; the quiet factory has spare workers; new money spent there gets more things made, so prices barely move.

**Shot 3a - W3, the two factories side by side, each its own column (47.7 to 55.1 s, about 7 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Picture", 48.1 s: PICTURE TWO FACTORIES.
  - "country", 51.3 s: EACH ONE = A WHOLE COUNTRY (held to the cut).
  - "workers" (1), 52.7 s: label WORKERS → No. 1's queue.
  - "materials", 53.4 s: label MATERIALS → the crates at No. 2's gate.
  - "machines" (1), 54.1 s: label MACHINES → No. 2's lit sheds.
- Words on screen: **PICTURE TWO FACTORIES** (top band); **EACH ONE = A WHOLE COUNTRY** (under it); **WORKERS** (label → No. 1's queue); **MATERIALS** (label → the crates at No. 2's gate); **MACHINES** (label → No. 2's lit sheds).
- Light effects: No. 2's smoke from both chimneys, No. 2's window flicker, No. 1's brazier flames and glow, the lantern's flicker. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 3b - W1, the shut No. 1 gate at the head of the queue (55.1 to 75.1 s, about 20 s).**
- Move: one slide of 1.2 m along the queue toward the gate, from 'Workers' (2) to 'Call'. Why: we join the line.
- Events, each on its spoken word:
  - "In", 55.1 s: cut in: windows dark, chimney cold, gate shut and chained, 7 men waiting, the brazier burning.
  - "Workers" (2), 57.9 s: the slide starts: 1.2 m along the queue toward the gate.
  - "Call", 61.0 s: the slide stops on the composed frame.
  - "quiet", 61.6 s: THE QUIET FACTORY.
  - "spends", 63.9 s: NEW MONEY SPENT, with a small arrow into the gate.
  - "go", 67.2 s: a cut within the held shot: the gate stands open, the men are gone, the brazier still burns by the empty pier, the lunch tin stays on the coping (fallback: the gate swings open in 0.8 s and the men fade in 1.2 s inside the swing).
  - "start", 68.7 s: No. 1's windows light (a 0.8 s blend to the lit picture) and its chimney starts to smoke.
  - "More" (1), 69.5 s: MORE MONEY.
  - "things", 71.2 s: + MORE THINGS TO BUY, as crates stencilled THIS WAY UP pop up stacked inside the open gateway.
  - "barely", 72.9 s: a price arrow over No. 1 that stays level: → PRICES BARELY MOVE.
  - 74.3 s: page peel.
- Words on screen: **THE QUIET FACTORY** (top band; stays as the page's tag); **NEW MONEY SPENT** (under it, with a small arrow into the gate); **MORE MONEY + MORE THINGS TO BUY → PRICES BARELY MOVE** (under it; builds in three steps, the arrow level over No. 1's column).
- Light effects: the brazier's flames, glow and a little smoke, the lantern's flicker, after 'start': chimney smoke at the top of the frame and a faint window flicker. Cost: about 1.05 to 1.5 s a frame held (live effects); about 5.6 to 7 s a frame during the slide.

### Page 4 - The flat-out factory, the first guess (75.1 to 95.7 s)

**Must teach:** in the flat-out factory every worker and machine is busy and no one waits at the gate; the same new money is spent there; what happens to prices?

**Shot 4a - W2, the open No. 2 gate with nobody waiting (75.1 to 95.7 s, about 21 s).**
- Move: one slide of 1.2 m toward the gate, from 'No' to 'factory' (2). Why: we walk up to the gate with nobody in the way, from where W1's camera stood, mirrored.
- Events, each on its spoken word:
  - "In", 75.5 s: flat out: the gate wide open, windows blazing, both chimneys smoking hard, the empty pavement lit by the gateway.
  - "busy", 79.2 s: the windows flicker brighter.
  - "No", 82.0 s: the slide starts: 1.2 m toward the gate, with nobody in the way.
  - "flat-out", 84.5 s: THE FLAT-OUT FACTORY, with a small line under it: FLAT OUT = WORKING AS HARD AS THEY CAN.
  - "factory" (2), 84.9 s: the slide stops on the composed frame.
  - "spent", 87.0 s: NEW MONEY SPENT (the same words as page 3).
  - "prices", 90.0 s: WHAT HAPPENS TO PRICES?
  - "guess", 91.0 s: HAVE A GUESS, with a ring that fills over 4 seconds.
  - 91.8 to 95.7 s: the 4-second guess hold on the still frame, music up; page 5 runs on with no join.
- Words on screen: **THE FLAT-OUT FACTORY** (top band); **FLAT OUT = WORKING AS HARD AS THEY CAN** (small, under it); **NEW MONEY SPENT** (under it); **WHAT HAPPENS TO PRICES?** (top band); **HAVE A GUESS** (small, under it, with the ring).
- Light effects: heavy smoke from both chimneys, window flicker, the gate lamp's glow. Cost: about 1.05 to 1.5 s a frame held (live effects); about 5.6 to 7 s a frame during the slide.

### Page 5 - The rule (95.7 to 123.5 s)

**Must teach:** why prices go up when nothing is spare (more money, the same things to buy, so businesses can ask more); the rule, which most economists agree on.

**Shot 5a - W2, the flat-out gate, the composed frame (95.7 to 107.1 s, about 11 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "spare" (1), 95.9 s: the question and ring clear; NO SPARE.
  - "More", 100.7 s: MORE MONEY.
  - "same", 102.2 s: + SAME THINGS TO BUY (the crates in the gateway stay as they are).
  - "up" (1), 106.5 s: a price arrow over No. 2 climbs: → PRICES UP.
- Words on screen: **NO SPARE** (top band); **MORE MONEY + SAME THINGS TO BUY → PRICES UP** (under it; same layout as page 3's line).
- Light effects: as page 4. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 5b - W3, both factories, with the rule over them (107.1 to 123.5 s, about 16 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Most", 107.1 s: cut; the small name tags QUIET and FLAT OUT appear over the two columns (they come back on every return to W3).
  - "agree", 108.0 s: MOST ECONOMISTS AGREE.
  - "spent", 110.4 s: upper rule card: NEW MONEY SPENT.
  - "spare" (2), 112.1 s: + SPARE.
  - "made" (2), 116.3 s: → MOSTLY MORE THINGS MADE, with a thin line down to No. 1's chimney.
  - "nothing", 117.3 s: lower rule card: NOTHING SPARE.
  - "up" (2), 120.0 s: → MOSTLY PRICES UP, with a thin line down to No. 2's chimneys.
  - 120.6 to 122.6 s: the 2-second rule hold, music up; then the page peel.
- Words on screen: **QUIET** (small tag over No. 1's column); **FLAT OUT** (small tag over No. 2's column); **MOST ECONOMISTS AGREE** (small, top band, above the rule cards); **NEW MONEY SPENT + SPARE → MOSTLY MORE THINGS MADE** (upper rule card, 0.06 to 0.90 across, about 0.07 to 0.15 down, over a soft dark band; thin line to No. 1's chimney); **NOTHING SPARE → MOSTLY PRICES UP** (lower rule card, 0.06 to 0.90 across, about 0.16 to 0.24 down; thin line to No. 2's chimneys).
- Light effects: No. 2's smoke, No. 2's window flicker, No. 1's brazier and lantern. Cost: about 1.05 to 1.5 s a frame held (live effects).

### Page 6 - Britain at war (123.5 to 150.5 s)

**Must teach:** a real case close to the flat-out factory: millions went to fight; soon fewer than one worker in a hundred was out of work; ships were sunk; the war was paid for partly with new money. More money and fewer things to buy, so prices roughly doubled.

**Shot 6a - G1, the grocer's thinning window and the recruiting poster, with the munitions works' gate where the lines meet (123.5 to 146.4 s, about 23 s).**
- Move: one slide of 1.2 m toward the grocer's window, from 'fewer' (2) to 'doubled'. Why: we step up to the thinning shelves on 'fewer things to buy'.
- Events, each on its spoken word:
  - "real", 124.4 s: A REAL CASE.
  - "Britain" (1), 125.5 s: BRITAIN, FIRST WORLD WAR.
  - "fewer" (1), 130.4 s: the 100-dot panel, every dot lit but the last, which is nearly empty: FEWER THAN 1 IN 100 OUT OF WORK.
  - "More", 140.1 s: MORE MONEY.
  - "fewer" (2), 141.4 s: + FEWER THINGS TO BUY; the slide starts: 1.2 m toward the grocer's window.
  - "doubled", 145.5 s: the slide stops; two bars, BEFORE THE WAR and END OF THE WAR: ROUGHLY ×2.
- Words on screen: **A REAL CASE** (top band); **BRITAIN, FIRST WORLD WAR** (under it (place title)); **FEWER THAN 1 IN 100 OUT OF WORK** (100-dot panel, top band); **MORE MONEY + FEWER THINGS TO BUY** (under it; same layout as pages 3 and 5); **PRICES: BEFORE THE WAR / END OF THE WAR: ROUGHLY ×2** (two bars in the top band, left).
- Light effects: the works' smoke far off, the gas lamps' faint flicker. Cost: about 1.05 to 1.5 s a frame held (live effects); about 5.6 to 7 s a frame during the slide.

**Shot 6b - W2, the flat-out gate, the composed frame (146.4 to 150.5 s, about 4 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Britain" (2), 146.4 s: cut to W2, flat out; the tag FLAT OUT.
  - "close", 147.4 s: CLOSE TO THE FLAT-OUT FACTORY.
- Words on screen: **FLAT OUT** (small tag over the gate's column); **CLOSE TO THE FLAT-OUT FACTORY** (top band).
- Light effects: as page 4. Cost: about 1.05 to 1.5 s a frame held (live effects).

### Page 7 - Glasgow's homes (150.5 to 183.5 s)

**Must teach:** the picture works for one kind of thing, homes; war workers came to Glasgow, where there were already too few homes; builders and materials went to the war; landlords raised rents, up to a quarter in places; about twenty thousand families refused the extra; Parliament brought rents on small homes back.

**Shot 7a - G1, the street to the works, from the plate's spot (150.5 to 154.9 s, about 4 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "fifteen", 151.5 s: GLASGOW 1915.
  - "crowds", 152.2 s: label CROWDS OF WAR WORKERS with a thin line to the walkers (or to the works' gate, if the walkers are dropped).
- Words on screen: **GLASGOW 1915** (top band (place title)); **CROWDS OF WAR WORKERS** (label → the walkers).
- Light effects: the works' smoke, the gas lamps' faint flicker. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 7b - G2, the factor's notice at the close mouth, the suitcase on the step below it (154.9 to 183.5 s, about 29 s).**
- Move: one slide of 1.5 m toward the notice, from 'Landlords' to 'quarter'. Why: we step up to the notice that turns too few homes into higher rent.
- Events, each on its spoken word:
  - "There", 154.9 s: cut to the close mouth; the tenement windows dark.
  - "homes" (1), 156.4 s: the windows light in a quick ripple from the close outward, in 12 steps over 1.5 s: every home full; TOO FEW HOMES ALREADY.
  - "built", 160.8 s: label FEW NEW HOMES BUILT → the half-built tenement.
  - "factory", 166.8 s: FOR HOMES: LIKE THE FLAT-OUT FACTORY (the lit windows rhyme with No. 2's).
  - "Landlords", 167.7 s: the slide starts: 1.5 m toward the notice.
  - "rent", 168.8 s: RENT RAISED.
  - "quarter", 170.8 s: the slide stops; UP TO A QUARTER MORE, IN PLACES.
  - "twenty", 172.9 s: ABOUT 20,000 FAMILIES REFUSING THE EXTRA lands whole.
  - "refusing", 174.5 s: placards appear in the lit windows one by one over 3 s (own surfaces, in steps).
  - "back", 179.9 s: a typed stamp RENTS ON SMALL HOMES BACK TO BEFORE THE WAR, landing on 'war' (3) (181.7 s).
  - 182.6 s: page peel.
- Words on screen: **TOO FEW HOMES ALREADY** (top band); **FEW NEW HOMES BUILT** (label → the half-built tenement); **FOR HOMES: LIKE THE FLAT-OUT FACTORY** (top band); **RENT RAISED: UP TO A QUARTER MORE, IN PLACES** (under it); **ABOUT 20,000 FAMILIES REFUSING THE EXTRA** (top band, replacing the cards above); **RENTS ON SMALL HOMES BACK TO BEFORE THE WAR** (a typed stamp across the middle of the top band).
- Light effects: the gas lamps' and the close bracket's faint flicker. Cost: about 1.05 to 1.5 s a frame held (live effects); about 5.6 to 7 s a frame during the slide.

### Page 8 - Japan, the second guess (183.5 to 201.8 s)

**Must teach:** Japan in 2013; Japan's version of our Reserve Bank planned to double the money it had created, in two years; if the warning is right, prices should go up fast. Guess.

**Shot 8a - J1, another country's basket at another checkout (183.5 to 201.8 s, about 18 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "thirteen", 184.8 s: JAPAN 2013.
  - "version", 186.2 s: a small heading, JAPAN'S VERSION OF OUR RESERVE BANK, ends in a colon.
  - "double", 188.2 s: ×2 MONEY.
  - "years", 190.8 s: IN TWO YEARS.
  - "warning", 192.0 s: a small chart: a dashed line climbs steeply, IF THE WARNING IS RIGHT.
  - "happened", 196.0 s: WHAT HAPPENED?
  - "guess", 197.1 s: HAVE A GUESS and its ring.
  - 197.9 to 201.8 s: the 4-second guess hold; page 9 runs on with no join.
- Words on screen: **JAPAN 2013** (top band (place title)); **JAPAN'S VERSION OF OUR RESERVE BANK: ×2 MONEY IN TWO YEARS** (under it); **IF THE WARNING IS RIGHT** (on the dashed line of a small chart in the top band); **WHAT HAPPENED?** (top band); **HAVE A GUESS** (small, under it, with the ring).
- Light effects: none live. Cost: about 0.8 s a frame held.

### Page 9 - Japan, the answer (201.8 to 230.2 s)

**Must teach:** prices barely moved for about eight years, about half a percent a year on average; one reason: most of the new money sat in the banks, and in our picture never reached the factory; so what matters is whether it is spent, and on what.

**Shot 9a - J1, the same frame; the answer lands on the chart (201.8 to 214.0 s, about 12 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "barely", 202.2 s: a real line runs almost level beside the dashed one: PRICES BARELY MOVED.
  - "eight", 204.0 s: FOR ABOUT 8 YEARS, along the chart's span.
  - "half", 207.1 s: ABOUT ½% A YEAR, ON AVERAGE, on the line.
  - "banks", 213.2 s: label ONE REASON: MOST SAT IN THE BANKS, with a thin line to the bank across the street (fallback: cut to 9b on 'most' (1), 211.2 s).
- Words on screen: **PRICES BARELY MOVED** (chart title in the top band); **FOR ABOUT 8 YEARS** (along the chart's span); **ABOUT ½% A YEAR, ON AVERAGE** (on the chart's line); **ONE REASON: MOST SAT IN THE BANKS** (label → the bank across the street).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 9b - W3, both factories, untouched; the lit bank in the lane (214.0 to 230.2 s, about 16 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "In", 214.0 s: cut to W3; tags QUIET and FLAT OUT.
  - "picture", 214.4 s: IN OUR PICTURE.
  - "most" (2), 215.1 s: the bank's window lights from inside (1 s, its own glass) with a soft pool of light on the pavement; a tag NEW MONEY lands on the window.
  - "never", 215.7 s: a dotted line runs from the bank up the lane toward the gates and stops halfway: NEVER REACHED THE FACTORY. Both gates stay as they are, so the picture doesn't say which factory Japan was like.
  - "much", 218.7 s: NOT JUST HOW MUCH.
  - "whether", 220.7 s: → WHETHER IT'S SPENT, AND ON WHAT.
  - "spare", 223.8 s: SPARE WORKERS, MATERIALS, MACHINES TO MAKE WHAT IT BUYS? replaces the cards.
  - 227.4 to 229.4 s: that card held 2 seconds, then the page peel.
- Words on screen: **IN OUR PICTURE** (top band (small)); **NEW MONEY** (tag on the bank's lit window); **NEVER REACHED THE FACTORY** (at the dotted line's end, halfway up the lane); **NOT JUST HOW MUCH → WHETHER IT'S SPENT, AND ON WHAT** (under it); **SPARE WORKERS, MATERIALS, MACHINES TO MAKE WHAT IT BUYS?** (top band, replacing the cards above).
- Light effects: No. 2's smoke and window flicker, No. 1's brazier and lantern, the bank window's own light. Cost: about 1.05 to 1.5 s a frame held (live effects).

### Page 10 - New Zealand, the third guess (230.2 to 256.0 s)

**Must teach:** here, from 2020, the Reserve Bank created new money and the government spent more, including help paying wages; by the end of 2021 about three in a hundred were out of work. Which factory was New Zealand closer to?

**Shot 10a - S1a, the busy site in 2020, the sanitise sign on the gate (230.2 to 248.5 s, about 18 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "here", 231.4 s: NEW ZEALAND.
  - "twenty" (2), 233.5 s: 2020 joins it.
  - "money", 235.7 s: NEW MONEY.
  - "government", 237.0 s: + GOVERNMENT SPENT MORE.
  - "twenty-one", 241.8 s: the 100-dot panel appears, headed END OF 2021.
  - "three", 246.1 s: three dots empty: ABOUT 3 IN 100 OUT OF WORK, with the small credit STATS NZ.
- Words on screen: **NEW ZEALAND 2020** (top band (place title)); **NEW MONEY + GOVERNMENT SPENT MORE** (under it); **END OF 2021: ABOUT 3 IN 100 OUT OF WORK** (100-dot panel, top band); **STATS NZ** (small credit).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 10b - W3, both factories: which one? (248.5 to 256.0 s, about 8 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Which", 248.5 s: cut to W3: WHICH ONE? with a small arrow to each gate; tags QUIET and FLAT OUT; the dot panel carried over, small, beside the question.
  - "guess", 251.2 s: HAVE A GUESS and its ring.
  - 252.0 to 255.9 s: the 4-second guess hold; a plain cut to page 11 on 'Close'.
- Words on screen: **WHICH ONE?** (top band, with a small arrow to each gate); **ABOUT 3 IN 100 OUT OF WORK** (the dot panel, small, top band right of the question, left of 0.90); **HAVE A GUESS** (small, under it, with the ring).
- Light effects: as 3a. Cost: about 1.05 to 1.5 s a frame held (live effects).

### Page 11 - New Zealand, the answer (256.0 to 275.0 s)

**Must teach:** close to the flat-out factory; prices went up fast, partly because more was being spent and partly because of prices overseas, like oil; at the peak the biggest push came from the price of building new homes, and rents.

**Shot 11a - W2, the flat-out gate: the answer (256.0 to 268.3 s, about 12 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Close", 256.0 s: plain cut from the guess; CLOSE TO THE FLAT-OUT FACTORY; tag FLAT OUT.
  - "prices" (1), 260.7 s: PRICES WENT UP FAST, a price arrow climbing over No. 2.
  - "Partly", 262.5 s: PARTLY: MORE SPENT.
  - "partly" (2), 265.2 s: PARTLY: PRICES OVERSEAS, LIKE OIL, with a thin line to the PETROL and DIESEL drums by the gate.
- Words on screen: **CLOSE TO THE FLAT-OUT FACTORY** (top band); **PRICES WENT UP FAST:** (top band, replacing it); **PARTLY: MORE SPENT** (under it); **PARTLY: PRICES OVERSEAS, LIKE OIL** (under it; thin line to the drums).
- Light effects: as page 4. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 11b - S1a, the house frame going up (268.3 to 275.0 s, about 7 s).**
- Move: one slide of 1.2 m through the gate toward the house frame, from 'peak' to 'homes'. Why: it lands on the price of building new homes, the homes the viewer saw going up on page 2.
- Events, each on its spoken word:
  - "At", 268.3 s: cut to the busy site.
  - "peak", 268.6 s: the slide starts: 1.2 m through the gate toward the house frame; AT THE PEAK, ending in a colon.
  - "building", 271.4 s: THE PRICE OF BUILDING NEW HOMES.
  - "homes", 272.0 s: the slide stops.
  - "rents", 273.1 s: AND RENTS, as the FOR RENT board appears on the neighbour's fence (the camera has stopped).
  - 274.2 s: page peel.
- Words on screen: **AT THE PEAK: THE PRICE OF BUILDING NEW HOMES... AND RENTS** (top band; builds in three steps, never BUILDING NEW HOMES on its own).
- Light effects: none live. Cost: about 0.8 s a frame held; about 5.6 to 7 s a frame during the slide.

### Page 12 - The usual cure (275.0 to 301.2 s)

**Must teach:** the Reserve Bank raises its interest rate; interest is the extra you pay back when you borrow; many loans cost more, so people have less to spend; businesses sell fewer things and hire fewer people; prices go up more slowly, usually not down; in the picture, the flat-out factory slows and more workers wait at the gate.

**Shot 12a - K1, the letter about the home loan (275.0 to 294.8 s, about 20 s).**
- Move: one slide of 0.43 m toward the letter (1.85 m to 1.42 m), from 'Many' to 'spend'. Why: we lean in to the letter on 'Many loans cost more'.
- Events, each on its spoken word:
  - "cure", 276.4 s: THE USUAL CURE.
  - "raises", 277.8 s: a dial in the dark window under it, INTEREST RATE, its needle rising (no figures).
  - "Interest" (2), 279.6 s: INTEREST = THE EXTRA YOU PAY BACK WHEN YOU BORROW.
  - "Many", 282.8 s: the slide starts: 0.43 m toward the letter.
  - "loans", 283.0 s: MANY LOANS COST MORE.
  - "spend", 285.7 s: the slide stops; → LESS TO SPEND.
  - "sell", 287.0 s: → SELL FEWER THINGS.
  - "hire", 288.5 s: → HIRE FEWER PEOPLE.
  - "slowly" (1), 291.1 s: the chain clears: PRICES GO UP MORE SLOWLY.
  - "down", 292.6 s: USUALLY NOT DOWN.
- Words on screen: **THE USUAL CURE** (top band); **INTEREST RATE** (label on the dial drawn in the dark window); **INTEREST = THE EXTRA YOU PAY BACK WHEN YOU BORROW** (under it); **MANY LOANS COST MORE → LESS TO SPEND → SELL FEWER THINGS → HIRE FEWER PEOPLE** (top band; builds as a chain); **PRICES GO UP MORE SLOWLY. USUALLY NOT DOWN** (top band, replacing the chain).
- Light effects: none live. Cost: about 0.8 s a frame held; about 5.6 to 7 s a frame during the slide.

**Shot 12b - W2, the flat-out factory slows and the queue returns (294.8 to 301.2 s, about 6 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "In", 294.8 s: cut to W2, flat out; tag FLAT OUT.
  - "picture", 295.2 s: IN OUR PICTURE.
  - "slows", 297.0 s: the tag becomes THE FLAT-OUT FACTORY SLOWS; two thirds of the windows dim (a 1.5 s blend to the slowed picture), the smoke thins to one chimney, the gate leaf swings half shut (own surface).
  - "workers", 298.4 s: a cut within the held shot: 8 men wait along the pavement (fallback: a 1.2 s fade).
  - "gate", 299.4 s: MORE WORKERS AT THE GATE.
  - 300.4 s: page peel.
- Words on screen: **IN OUR PICTURE** (top band (small)); **THE FLAT-OUT FACTORY SLOWS** (the tag over the gate's column, replacing FLAT OUT); **MORE WORKERS AT THE GATE** (under it).
- Light effects: smoke (thinning on 'slows'), window flicker (dimming). Cost: about 1.05 to 1.5 s a frame held (live effects).

### Page 13 - Who pays, here (301.2 to 328.9 s)

**Must teach:** the Reserve Bank raised its interest rate again and again from late 2021 into 2023; many loans cost more and jobs got harder to find; nearly six in a hundred were out of work by the middle of 2026, up from about three, and the interest rate isn't the only reason; who pays: many people with loans, and people put out of work.

**Shot 13a - K1, the letter, the composed frame (301.2 to 311.2 s, about 10 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "pays" (1), 301.8 s: WHO PAYS FOR THE CURE?
  - "From", 303.0 s: the dial returns in the window, its needle stepping up again and again.
  - "twenty-one", 303.9 s: LATE 2021 under the dial.
  - "twenty-three", 305.1 s: → 2023.
- Words on screen: **WHO PAYS FOR THE CURE?** (top band); **LATE 2021 → 2023** (caption under the dial in the window).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 13b - S1b, the same site, stopped (311.2 to 324.2 s, about 13 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "jobs", 311.2 s: cut to the stopped site.
  - "middle", 313.4 s: the dot panel returns, headed MIDDLE OF 2026.
  - "six", 315.7 s: nearly six dots empty: NEARLY 6 IN 100 OUT OF WORK, with the credit STATS NZ.
  - "three", 318.7 s: three dots outlined faintly: UP FROM ABOUT 3.
  - "only", 321.0 s: small NOT THE ONLY REASON (it stays on through 13d).
  - "pays" (2), 323.0 s: WHO PAYS?
- Words on screen: **MIDDLE OF 2026: NEARLY 6 IN 100 OUT OF WORK** (100-dot panel, top band); **UP FROM ABOUT 3** (faint, on the panel); **STATS NZ** (small credit); **NOT THE ONLY REASON** (small, under the panel); **WHO PAYS?** (top band).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 13c - K1, the letter (324.2 to 325.9 s, about 2 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "Many" (2), 324.2 s: cut to the letter.
  - "loans" (2), 325.1 s: MANY PEOPLE WITH LOANS under WHO PAYS?
- Words on screen: **MANY PEOPLE WITH LOANS** (under it).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 13d - S1b, the stopped site (325.9 to 328.9 s, about 3 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "and" (3), 325.9 s: cut to the stopped site; NOT THE ONLY REASON stays.
  - "put", 326.5 s: ...AND PEOPLE PUT OUT OF WORK.
  - 328.1 s: page peel.
- Words on screen: **AND PEOPLE PUT OUT OF WORK** (under MANY PEOPLE WITH LOANS); **NOT THE ONLY REASON** (small, stays).
- Light effects: none live. Cost: about 0.8 s a frame held.

### Page 14 - Two views (328.9 to 352.9 s)

**Must teach:** America's version of our Reserve Bank says the cure would probably mean fewer jobs, unfortunate but not the goal; Mattei argues that fewer jobs are the cure's main goal: with more workers waiting at the gate, people with jobs have less power to ask for higher wages.

**Shot 14a - W4, someone with a job, and the men waiting outside the gate (328.9 to 352.9 s, about 24 s).**
- Move: one slide of 1.2 m toward the gate, from 'With' to 'says'. Why: we move closer to the queue on 'with more workers waiting at the gate'.
- Events, each on its spoken word:
  - "America's", 329.3 s: heading AMERICA'S VERSION OF OUR RESERVE BANK:, with the small credit US FEDERAL RESERVE.
  - "jobs" (1), 333.5 s: PROBABLY FEWER JOBS.
  - "unfortunate", 335.2 s: UNFORTUNATE, appears under it.
  - "goal" (1), 337.0 s: BUT NOT THE GOAL (no quotation marks).
  - "Clara", 337.7 s: the typed name card CLARA E. MATTEI comes in below the American block, with the small credit THE CAPITAL ORDER (no portrait, no book cover, no year).
  - "Mattei", 338.7 s: the American block (heading and its two cards) clears at about 339.5 s; the name card stays.
  - "argues", 342.2 s: MATTEI ARGUES: heads her block.
  - "goal" (2), 344.5 s: FEWER JOBS ARE THE MAIN GOAL.
  - "With", 345.2 s: the slide starts: 1.2 m toward the gate and the queue.
  - "says", 347.8 s: the slide stops.
  - "power", 349.8 s: LESS POWER TO ASK FOR HIGHER WAGES, under MATTEI ARGUES, which stays to the page's end.
  - 352.1 s: page peel.
- Words on screen: **AMERICA'S VERSION OF OUR RESERVE BANK:** (top band (heading)); **US FEDERAL RESERVE** (small credit); **PROBABLY FEWER JOBS** (under it); **UNFORTUNATE, BUT NOT THE GOAL** (under PROBABLY FEWER JOBS); **CLARA E. MATTEI** (typed name card below the American block, about 0.25 down); **THE CAPITAL ORDER** (small credit); **MATTEI ARGUES:** (top band (heading, replacing the American one)); **FEWER JOBS ARE THE MAIN GOAL** (under it); **LESS POWER TO ASK FOR HIGHER WAGES** (under FEWER JOBS ARE THE MAIN GOAL).
- Light effects: the lane's gas lamps glowing, a faint flicker. Cost: about 1.05 to 1.5 s a frame held (live effects); about 5.6 to 7 s a frame during the slide.

### Page 15 - Back at the checkout (352.9 to 379.5 s)

**Must teach:** a hundred-dollar basket in June 2025 cost about a hundred and four a year later, and would have cost about a hundred and three if petrol and diesel prices hadn't changed; petrol and diesel push up almost everything made or moved, in both factories; so part of what you felt came from petrol and diesel.

**Shot 15a - C1, the basket again: a hundred dollars (352.9 to 367.4 s, about 14 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "dollars", 356.2 s: a tag beside the basket: $100.
  - "twenty-five", 357.4 s: , JUNE 2025 joins it.
  - "later", 358.9 s: it flips to ABOUT $104, A YEAR LATER.
  - "three", 366.6 s: a ghost tag beside it: ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED, with the credit STATS NZ.
- Words on screen: **$100, JUNE 2025 → ABOUT $104, A YEAR LATER** (price tag beside the basket); **ABOUT $103 IF PETROL AND DIESEL PRICES HADN'T CHANGED** (ghost tag beside the first); **STATS NZ** (small credit).
- Light effects: none live. Cost: about 0.8 s a frame held.

**Shot 15b - W3, both factories, petrol and diesel at both gates (367.4 to 374.3 s, about 7 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "When", 367.4 s: cut to W3; tags QUIET and FLAT OUT.
  - "petrol" (2), 367.7 s: labels with thin lines to the drums at both gates: PETROL AND DIESEL.
  - "both", 373.0 s: a price arrow climbs over each factory: IN BOTH FACTORIES.
- Words on screen: **PETROL AND DIESEL** (labels → the drums at both gates); **IN BOTH FACTORIES** (top band, with an arrow climbing over each column).
- Light effects: as 3a. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 15c - C1, the basket (374.3 to 379.5 s, about 5 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "So", 374.3 s: cut back to the basket.
  - "part", 374.4 s: PART OF IT: PETROL AND DIESEL (never 'mostly').
  - 378.6 s: page peel.
- Words on screen: **PART OF IT: PETROL AND DIESEL** (top band).
- Light effects: none live. Cost: about 0.8 s a frame held.

### Page 16 - Spent on what? (379.5 to 406.9 s)

**Must teach:** the rule again, in the same words; the two questions to ask next time.

**Shot 16a - W3, both factories, the rule again (379.5 to 393.9 s, about 14 s).**
- Move: none (held).
- Events, each on its spoken word:
  - "always", 380.6 s: DOES NEW MONEY ALWAYS PUSH PRICES UP?
  - "No", 382.1 s: NO.
  - "spent" (1), 383.7 s: page 5's upper rule card, the same words in the same place: NEW MONEY SPENT.
  - "spare" (1), 385.3 s: + SPARE.
  - "made", 389.5 s: → MOSTLY MORE THINGS MADE.
  - "nothing", 390.6 s: lower card: NOTHING SPARE.
  - "up" (2), 393.3 s: → MOSTLY PRICES UP.
- Words on screen: **DOES NEW MONEY ALWAYS PUSH PRICES UP? NO.** (top band, cleared at 'spent' for the rule cards); **NEW MONEY SPENT + SPARE → MOSTLY MORE THINGS MADE** (upper rule card, exactly as page 5); **NOTHING SPARE → MOSTLY PRICES UP** (lower rule card, exactly as page 5).
- Light effects: as 3a. Cost: about 1.05 to 1.5 s a frame held (live effects).

**Shot 16b - C1, the basket and the warning, stepping back (393.9 to 406.9 s, about 13 s).**
- Move: one slide of 0.7 m back from the basket to the plate's spot, from 'next' to about 397.3 s. Why: stepping back as the two questions land; the bill stays in frame.
- Events, each on its spoken word:
  - "So", 393.9 s: cut to the basket at the composed frame.
  - "next", 394.1 s: the slide starts: 0.7 m back from the basket to the plate's spot, the reverse of page 1 (stops about 397.3 s).
  - "warning", 395.3 s: the label THE WARNING to the newspaper bill again, as on page 1.
  - "Spent" (2), 397.7 s: SPENT ON WHAT?
  - "anything", 399.2 s: ANYTHING SPARE TO MAKE WHAT IT BUYS? in a small line under it.
  - "pays", 401.8 s: WHO PAYS FOR THE CURE?
  - 402.9 to 406.9 s: both held; the 4-second fade to dark.
- Words on screen: **THE WARNING** (label → the newspaper bill); **SPENT ON WHAT?** (top band); **ANYTHING SPARE TO MAKE WHAT IT BUYS?** (small, under it); **WHO PAYS FOR THE CURE?** (under it).
- Light effects: none live. Cost: about 0.8 s a frame held; about 5.6 to 7 s a frame during the slide.

### The moves and holds at a glance

| Page | Shots (views) | Moves (one slide each, never a turn) | Holds |
|---|---|---|---|
| 1 | C1 | toward the basket (0.7 m) | |
| 2 | S1a | none | |
| 3 | W3, W1 | along the queue to No. 1's gate (1.2 m) | |
| 4 | W2 | toward No. 2's gate (1.2 m) | 4-second guess hold |
| 5 | W2, W3 | none | 2-second rule hold |
| 6 | G1, W2 | toward the grocer's window (1.2 m) | |
| 7 | G1, G2 | toward the rent notice (1.5 m) | |
| 8 | J1 | none | 4-second guess hold |
| 9 | J1, W3 | none | 2-second hold on the question |
| 10 | S1a, W3 | none | 4-second guess hold, then a plain cut |
| 11 | W2, S1a | toward the house frame (1.2 m) | |
| 12 | K1, W2 | toward the letter (0.43 m) | |
| 13 | K1, S1b, K1, S1b | none | |
| 14 | W4 | toward the gate and the queue (1.2 m) | |
| 15 | C1, W3, C1 | none | |
| 16 | W3, C1 | back from the basket (0.7 m) | 4-second fade at the end |

**30 shots, 9 slides.** Pages 2, 5, 8, 9, 10, 13 and 15 hold still throughout. No page has more than one
move, against your limit of three. No page shows more than two views, which keeps the film's memory use
down [new, after F1]: page 11 no longer cuts to the checkout; its "prices overseas, like oil" points at the
PETROL and DIESEL drums at No. 2's gate, the drums page 15 comes back to.

How long each view is on screen: W3 about 69 s (pages 3, 5, 9, 10, 15, 16; the master for every Works
painting); C1 about 61 s (pages 1, 15, 16); W2 about 55 s (pages 4, 5, 6, 11, 12); S1a about 45 s; K1
about 31 s; J1 about 31 s; G2 about 29 s; G1 about 27 s; W4 about 24 s; W1 about 20 s; S1b about 16 s.

### How the two factories stay the same wherever they come back

1. **One set, one script, fixed places.** Both factories are in one set file with four named cameras,
   never rebuilt between views. No. 1 is always on the left and No. 2 on the right, never mirrored or
   swapped.
2. **Different at a glance:** round against square chimneys, a water tank, dark red-brown against pale
   buff-grey brick, and the "No. 1" and "No. 2" boards.
3. **Each gate view shows the other factory where it really stands:** in W1, No. 2's two square chimneys
   at the upper right; in W2, No. 1's single round chimney at the upper left. This works because the
   chimneys stand at the back of their yards [T1].
4. **Typed name tags** QUIET and FLAT OUT on every return to W3 from page 5, and FLAT OUT (then THE
   FLAT-OUT FACTORY SLOWS) on W2 from page 6.
5. **Matched gate views:** W1 and W2 are mirror spots, at the same distances, with the same lens and gate
   furniture.
6. **One painting chain:**
   - W3 is painted first and becomes the master. Every other Works painting gets it as its style picture
     (sent at about 1 megapixel, which saves about 7 cents a painting) [F10].
   - Each painting is lined up with its plate (`align_painting.py`).
   - Then a colour check: the average colour of each factory's brick and roofs, the gates and the sky,
     measured inside their outlines in the new painting and in the master. A clear mismatch means a
     repaint. (`match_model_colours.py` is only a rough check, as its own note says.)
7. **Second states come from the same view's own paintings** (state pictures), so only what the story
   changes changes.
8. **One shared settings module** (`works-effects.js`) for the four states, with the same smoke and flicker
   seeds on every page.
9. **A continuity sheet** before filming: one still from each Works view side by side (chimneys, boards,
   gate states, how many men, sky), checked by a helper.

---

## 3. The numbers

### Plates, paintings and money

| View | Plates | Paintings | Why |
|---|---|---|---|
| W3 both gates | 1 | 1 | always held; its changes are own surfaces (the bank's window, the gates) or live (smoke) |
| W1 No. 1's gate | 2 (the quiet plate, and the working helper plate) | 2 | slides; the men go; the windows light |
| W2 No. 2's gate | 2 (flat out, and slowed) | 3 | slides (page 4); the slowed state with the men (page 12) |
| W4 inside the yard | 1 | 2 | slides; the men and gates are own surfaces |
| C1 the checkout | 1 | 2 | slides in (page 1) and out (page 16) |
| J1 the corner shop | 1 | 1 | held |
| S1a the busy site | 1 | 2 | slides (page 11) |
| S1b the stopped site | 1 | 1 | held; its own light |
| K1 the kitchen | 1 | 2 | slides |
| G1 street to the works | 1 | 2 | slides |
| G2 the close mouth | 1 | 2 | slides; windows and placards are own surfaces |
| **The film** | **13** | **20** | |
| The people test (pit village street) | 2 (with and without figures) | 2 | painted people, and people leaving |

fal's price list gives Flux 3 edit at 2.4 US cents a megapixel. A painting is about 4 megapixels, and log
32's 20 to 45 cents for two shows that the pictures sent are charged as well. So this plan counts **about
25 cents a painting**, with the style picture sent at about 1 megapixel [F10].

| Spending (all on hold until you say yes) | US$ |
|---|---|
| The people test: 2 paintings | 0.50 |
| 20 paintings for the film | 5.00 |
| Up to 4 composition sketches by Nano Banana Pro (15 cents each), only where the shot checker can't settle a view | 0.60 |
| Narration (about 6,300 characters), after 22 October | 1.10 |
| **Planned** | **7.20** |
| Repaint reserve: 10 repaints (about one in two; lesson 97: Flux's strength varies) | 2.50 |
| Re-recording reserve: one page after 22 October or 4 November | 0.30 |
| **The most it can come to** | **10.00** |

That is under the US$12 line, and US$10 of the US$20 is never touched. Every request is listed in the
folder's `00-requests.json`, and no step of the plan needs more.

**The paid requests, each asked for separately:**
1. the people test (about US$0.50);
2. W3, W1 main and W1 working (about US$0.75);
3. W2's three and W4's two (about US$1.25);
4. New Zealand: S1a's two, S1b, C1's two, K1's two (about US$1.75);
5. Glasgow's four and J1 (about US$1.25);
6. the narration, after 22 October (about US$1.10) [F7].

### New things to build by script (about 60, most of them small)

- **The Works (about 16):** the wall with two gate arches, piers and the dividing wall; the No. 1 and No. 2
  boards; the bank front with its lit room, brass plate and hanging sign; the PETROL and DIESEL drums; the
  THIS WAY UP crates; a chain and padlock; figure shapes in five poses; a lunch tin; a jacket and cap on a
  nail; a tin mug; the WAGES envelope; the factory changes (round chimney, two square stacks, pitched roof
  with a lantern, tank off, grouped windows, true scale) and the town at true scale.
- **The checkout and corner shop (about 18):** counter, belt, divider bar, card terminal, till, bag rack and
  reusable bags, wire basket, bread bag, milk bottle, butter, cheese, CHECKOUT sign, the newspaper bill and
  its wire stand, the petrol canopy seen through the window; the corner shop's counter, hot-food cabinet,
  rice balls, tea bottle, milk carton, レジ sign, and the bank across the street.
- **The building site (about 14):** mini digger, timber packet, house frame with wrap, scaffolding, mesh
  fence panels and gate, chain and padlock, hi-vis vest, hard hat, builder's banner, two weatherboard
  houses, the torn cover, the FOR RENT board, the sanitise sign.
- **The kitchen (about 6):** room and window, letter and envelope, mug, phone, cardigan, a plain kettle.
- **Glasgow (about 13):** the tenement block builder, the corner grocer's shopfront and thinning display with
  tins, a brass till, the recruiting poster, the factor's notice, the munitions works' wall and gate, the
  half-built tenement with scaffold poles, the brick stack and tarpaulin, the re-lettered builder's cart,
  the suitcase and bundle, twelve placards, the walking figure shapes.

**Fetched from Poly Haven: 23 models and 19 surfaces**, every name checked against Poly Haven's list (saved
in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/polyhaven/`).
Five of the earlier list are dropped for their lettering or era: `plastic_crate_01`, `portable_generator`,
`CashRegister_01`, `vintage_suitcase`, `vintage_electric_kettle`; and the close's glazed tiles are no longer
needed. Today `convert_poly_haven.py` and `prop_library.py` write into the pit village's props folder and its
`index.json`, from a fixed list; they get a new choices list and an output folder, so chapter 2's props go
into their own `index.json` (about 2 to 3 hours, with cutting out the pole) [F11].

### Computer time

**Blender: about 12 to 13 hours of machine time.** Plates are drawn one at a time, because each uses all 4
processors.

| Step | Each | Count | Time |
|---|---|---|---|
| Plates (EEVEE, 1536 x 2730) | about 10 min | 15 (13 for the film, 2 for the people test), each drawn about twice after checks | about 5 h |
| Small preview stills (540 x 960) | about 1 min | about 15 a view | about 2.8 h |
| Shot checker runs | about 1 min | about 8 a view | about 1.5 h |
| Finished stills for the light rules | about 10 min | 11 | about 1.8 h |
| Exports (sets and cameras) and Poly Haven conversions | | | about 1.5 h |

**Filming: about 12,200 frames on the estimated timeline** (planned as 13,000 in case Malina reads more
slowly), counted from the shot list:

| Kind of frame | Frames | Seconds a frame (measured on the notice corner) | Hours |
|---|---|---|---|
| held, nothing live (C1, J1, S1a, S1b, K1) | about 5,100 | about 0.57 with two helpers at once, 0.8 with one | 0.8 to 1.1 |
| held, with smoke, flames or flicker (the Works and Glasgow) | about 6,230 | about 1.05 with two at once, 1.5 with one | 1.8 to 2.6 |
| sliding (9 slides, about 29 s of film) | about 880 | about 5.6 to 7, one helper at a time | 1.4 to 1.7 |
| page peels (both pages drawn; counted inside the rows above) | about 310 | about double | 0.1 |
| loading the sets (about 50 pieces, each loading only its own pages) | | about 30 to 90 s a piece | about 0.5 |
| **All** | **12,208** | **about 1.5 to 1.8 on average** | **about 5 to 6** (5 to 6.5 at 13,000 frames) |

- Then **2 to 3 hours of re-filming** after the critics (the notice corner was filmed three times).
- Moving stretches are filmed one at a time and held stretches two at a time [F3].
- **All of this rests on one change** [F1]: today `cinema-chapter.js` builds every page before drawing
  anything, and `film-chapter-parallel.sh` starts a fresh browser for every 60-frame piece. Opening one
  painted set was measured at 20 to 31 seconds and about 2.6 GB of browser memory, so loading all six places
  for every piece would likely run out of memory on two helpers at once (16 GB, no swap), and if it didn't,
  it would add 4 to 7 hours. So the chapter is changed to build only the pages each piece covers (plus the
  next during a page peel), and pieces become about 240 to 300 frames. It is tested first, for free.
- Filming runs in stretches under 2 hours (`FILM_FROM` and `FILM_TO`), because a cloud session stops
  background jobs at 2 hours.
- The jump finder (`find_jumps.py`) holds every frame of a film in memory: on the whole chapter it would need
  about 19 GB, so it is run one piece or one page at a time [F12].

### Disk (about 8.5 GB free)

Measured: the kit's film settings with film grain make about 3.5 MB a second, even on held frames, so one
full-quality copy of the chapter is about 1.4 to 1.6 GB [F2].

| What | About |
|---|---|
| Poly Haven downloads and conversions | 0.5 GB |
| Blender set files (pictures kept outside them) | 0.5 to 0.8 GB |
| Sets exported for the film | 0.6 to 0.9 GB |
| Plates, paintings, state pictures and distance pictures | 0.4 GB |
| Check stills and reports, cleared as each view passes (the notice corner's checks alone left 1.4 GB) | up to 1.5 GB at a time |
| Narration and mix | 0.1 GB |
| Film: the pieces (about 1.5 GB), then the joined silent film, then the master. The pieces are deleted once the silent film is checked, and the silent film once the master is checked, so at most two full copies exist at once | up to 3.2 GB |
| **Peak** | **about 6.5 to 7.5 GB** |

That leaves about 1 to 2 GB spare, too little for a second filming beside the first. So, early on, **I'll ask
you whether these old files can go** (about 9 GB): `/home/user/work/chapter-2` (3.6 GB: old masters,
pieces and stills of the recorded chapter 2), the old chapter 2 pieces and silent film in
`/home/user/work/paper-pop-up-film-kit/paper-film/out` (about 1.5 GB), and three scratch folders from earlier
tests (`plan3` 2.0 GB, `house` 1.1 GB, `rebuild-check` 0.9 GB). Free space is checked before every export
and every filming stretch.

**The repository** [F15]: placing a prop copies it, with its pictures, into the Blender file and into the
exported set (the notice corner's are 83 MB and 62 MB for one view). A set with two factories, the lane, the
town and four cameras would pass GitHub's 100 MB limit. So the pictures stay outside the Blender files, the
Works' export is split (the factories, the lane, the town), every file's size is checked before saving to
the repository, and Blender's `.blend1` backups are turned off in every new script (as `build_street.py`
already does) and added to the ignore list.

### Work time

The schedule depends on hours of work, not machine time [F14]. The notice corner took about 9 hours for one
view (composing, three critic rounds, painting, three filmings).

| Work | Hours |
|---|---|
| The free tests (loading, timing) and the change to load one page at a time | 3 to 5 |
| The people test (figures, plate, painting, two filmings, helpers) | 3 to 5 |
| `build_street.py` and `set_dressing.py` settings, and the notice corner rebuilt to check | 1 to 2 |
| The Works: factories 4 to 6, wall, gates, bank and small props 3 to 5, figures 2 to 4, lane and town 2 to 3 | 11 to 18 |
| The checkout and the corner shop | 6 to 10 |
| The building site (the mini digger alone 3 to 5) | 6 to 9 |
| The kitchen | 3 to 5 |
| Glasgow: tenements, the munitions works, shop, notices and placards | 8 to 14 |
| Poly Haven: the converter's settings, downloads, the pole cut out | 2 to 3 |
| Stage code (below) | 8 to 12 |
| Composing, checking and critics, 11 views at 3 to 5 hours each | 33 to 55 |
| 16 page files | about 16 |
| Critique of the film and fixes | 10 to 15 |
| **All** | **about 110 to 170, so about 5 to 7 days** |

**Stage code to write** (none of it exists yet) [F8]:
- build only the pages a piece covers (above) [F1];
- swap a state picture onto a held set on a word (a time cut), and blend between two held frames (two set
  draws, not one per frame);
- one set that switches its painting and projector at a cut, so two views of one place on a page (W3 then
  W1 on page 3) need one copy of the set, not two (each copy also carries two distance pictures of about
  38 MB);
- window glass and placards that change in steps (the held set is redrawn about 30 times on page 7, not on
  every frame);
- gate leaves that swing as moving things over the held set;
- the 100-dot panel (`graphics.js` has titles, labels, counters, bars and line charts, but no dot panel).

The first milestone you can watch: **pages 3 to 5 at the Works, painted, after about 2 to 3 days** (the free
tests, the Works and its stage code, then the first two paid batches).

---

## 4. The order of work

### First: the cheapest tests that would show the plan works

1. **Free, about 1 hour: can the computer hold the chapter?** [F1, F6]
   - Make a stand-in chapter of 16 pages, each loading a copy of the notice corner's set and painting (the
     heaviest place known), and film two pieces at once. Measure memory and loading time.
   - Then change the chapter to build only the pages each piece covers, and pieces to about 270 frames, and
     measure again. If two helpers at once still risk running out of memory on pages with two views, those
     stretches are filmed one at a time.
   - At the same time, ask you about clearing the old files (part 3, disk).
2. **Free, about 1 to 2 hours: what's still unknown about speed** [F3], on the notice corner as it is: held
   frames with nothing live; whether turning off the depth blur, the glow pass or the shadow maps helps
   without hurting the picture; and whether joining the set's pieces by material speeds up moving frames
   (the notice corner's set has 840 materials; the old factory model joins its parts to about 19).
3. **The people test, about 3 to 5 hours, then about 50 cents with your yes** (part "People") [F6]. If the
   painted figures fail twice, the fallbacks are chosen here, before the Works is built around them.
4. **Settings for the reused street scripts** (about 1 to 2 hours), and the notice corner rebuilt once to
   show it is unchanged [F5].
5. **Free, about 1.5 days: build the Works and film pages 3 to 5 with stand-ins.**
   - Build both factories at true scale with their own shapes, the wall, gates, boards, bank, lane, town,
     the figures (as step 3 decided) and the props.
   - Compose W3, W1 and W2 with the shot checker until they pass, and draw their plates, W1's working
     helper plate and W2's slowed plate. Check the end frame of the slide and the "weights" view with the plate standing in for
     the painting (blue at an edge means the camera left the painted area) [F13].
   - Write the stage code and film pages 3 to 5 on the estimated timeline, with the plates standing in for
     the paintings.
   - Before any more money is spent, it shows: the speed of each kind of frame on a real chapter set;
     whether the time cut reads as "they've gone in" (a fresh helper watches it in motion without being told
     what it shows); whether the gates and boards sit well; whether the two factories are told apart at
     phone size (a helper names them from a still); that nothing tears on the slide.
6. **With your yes: paint W3, W1 main and W1 working (about 75 cents)**, then line them up, colour-check,
   film page 3 painted, and have three fresh helpers check it (looks; the painter's faults; the figures).
   **Then W4 is composed and drawn, and, with your yes, W2's and W4's paintings (about US$1.25)**, the
   continuity sheet, and pages 3 to 5 painted, sent to you to watch on your phone: the first milestone.

### Then

7. **New Zealand:** the building site (S1a, then S1b painted with S1a's painting as its style), the checkout
   (C1), the kitchen (K1). One paid batch.
8. **Glasgow (G1, G2) and the corner shop (J1).** One paid batch.
9. **For every view, before its plate:**
   - compose it with the shot checker until it passes (each view gets its own check file; the checker's
     notice-specific rules are adjusted per view);
   - the history helper checks a preview still with the lettering list, a reader of Japanese checks J1, and
     a colour helper checks every New Zealand view for party and chain colours;
   - every invented name is searched;
   - read the plate's render log for shadow-memory faults (lesson 110).
10. **For every painting:** line it up (`align_painting.py`); make the behind painting and keep its painted
    shadows (`keep_painted_shadows.py`); make the state pictures (`composite_fill.py`); check the colours
    against the master.
11. **Record the narration after 22 October** [F7], when the new price figures come out: first check that
    page 1's "costs more than it did a year ago" still holds and decide whether page 15's basket switches,
    and open a source for page 7's "builders and materials gone to the war" (the script's "Sources still to
    open"). This is its own request (about US$1.10).
12. **Pages:** the real word times from the recording; one page file per page, timed to words with
    `kit.at`; the camera checked with `camera_audit.py`; for every slide four stills (the projector's view,
    the end, the middle, the weights view); every card checked against the narration by a words-on-screen
    helper; independent critics (looks; history; rules: figures on screen, party colours, Mattei marked as
    hers); fixes.
13. **Film pages 1 to 12 first and pages 13 to 16 last**, in stretches under 2 hours: moving stretches one at
    a time, held stretches two at a time. Look for jumps one piece at a time (`find_jumps.py`), with the
    planned cuts listed. Two helpers and a skeptic check the film in motion. Fix, and re-film only the
    changed stretches.
14. **Finish:** the mix, captions, loudness and timing checks. Then the real test: show it to the people who
    got lost, with the listener questions in the script file.
15. **After 4 November:** check page 13's "nearly six in a hundred" against the revised figure. If the June
    quarter is revised to 5.4% or lower, re-record page 13 as "more than five in a hundred" (from the
    reserve) and re-film pages 13 to 16 (about 3,200 frames, 1.5 to 2 hours).

**If time runs short, the first to go:**
- the kitchen: pages 12 and 13 use the checkout instead, with the interest rate dial drawn in its window;
- then the Glasgow walkers (the label points at the works' gate);
- then the bank across the street from the Japanese shop: page 9 then cuts to W3 on "most" (1).

### Risks, and how each will be caught

| Risk | How it will be caught | What then |
|---|---|---|
| The chapter runs out of memory or loads too slowly | the free stand-in test (step 1) before anything is built | load one page at a time; film heavy stretches one at a time |
| The disk fills near the end | free space checked before every export and filming stretch | delete pieces once the silent film is checked; old files cleared with your yes |
| The painter gives the waiting men faces, changes how many there are, or makes them look photographic | the people test; a figure count against the plate's outlines; a helper at full size | plainer words and darker backlight; then own-surface silhouettes; then caps, lunch tins and stools |
| The time cut reads as a glitch, or a fade as ghosts | a fresh helper watching in motion, not told what it shows | a 1.2 s blend hidden in the gate's swing |
| Painted shadows stay after the men leave | stills before and after; the two plates show where the shadows fall | widen the area taken from the other painting |
| Filming is slower than planned | the free timing test, then each page's first stretch timed | join set pieces by material; fewer live effects on held frames; a simpler far town |
| Own surfaces (gates, crates, windows, letters, placards, silhouettes) look like 3D renders next to the paint | a looks helper on stills; colour-matching them to the painting, as on the notice corner | darken and match; keep them small or dim; or paint the change into a state picture |
| The two factories don't match between views, or can't be told apart on a phone | the colour check against the master; the continuity sheet; a helper naming them from stills | repaint the odd one; strengthen the chimney shapes |
| A view can't meet its composition (W3's height, G1's grocer, G2's notice) | the shot checker on each view before its plate | slide the camera or move the subject, as the checker says; a sketch only if it can't settle it |
| The painter garbles or invents lettering | every lettered surface is its own surface; a helper reads every sign at full size | add it to the own-surface list |
| The painter stretches or shifts its picture | `align_painting.py` on every painting (log 32 found 0.65% and 3 pixels) | line it up before use |
| A slide goes soft or leaves the painted area | the end frame and weights view with the plate as stand-in, before paying | a shorter slide, or the plate drawn from the slide's middle |
| A figure on screen that Malina doesn't say (a price tag, keypad, lane or close number, phone number, pack size, a poster's numbers) | lettering lists checked against the narration before building; a helper scanning every still for digits | turn it away, leave it off, or letter it with words |
| A picture says a fact the ledger doesn't (Japan shown as a quiet factory; a stopped site read as "stopped because of the cure"; a bare window in 1915) | a fact helper asks of each picture "what does this claim?", with the picture in hand (lesson 83) | change the picture: page 9 leaves both gates untouched; NOT THE ONLY REASON stays; the window thins, not empties |
| Wrong era or place details | the history helper is given the pictures, not only the words, before painting; a reader of Japanese | fix in 3D before the plate |
| An invented name matches a real business or paper | a search of each name before it is built | pick another |
| Party, supermarket chain or bank colours | a colour helper on every New Zealand and Japanese view | recolour; no large flat areas of one colour |
| The Glasgow works is taken for a model factory, or the model for a real place | distinct shapes; the Works' own blue dusk; the cards A REAL CASE and IN OUR PICTURE; the newcomer test | change the works' shape further |
| The plate runs out of shadow memory (lesson 110) | reading each plate's render log | lower the shadows' resolution |
| A guess or rule hold is cut short when the real recording lands | the page-turn check on the real timeline | the holds are written as pauses in the timeline, not as seconds in the page |
| New figures on 22 October or 4 November change a spoken line | recording after 22 October; page 13 checked after 4 November | re-record one page from the reserve; re-film from that page on |
| A cloud session stops background jobs after 2 hours | filming in stretches, kept in pieces | carry on from the last piece |
| A file passes GitHub's 100 MB limit | sizes checked before saving to the repository | split the set; keep pictures outside the Blender files |
| Money | each batch costed before you are asked; `00-requests.json` totals | nothing in the plan needs more than about US$10 |

---

## 5. Findings: fixed or rejected, and why

Every finding was checked against the files before it was acted on. None was rejected outright; four were
fixed only in part, for the reasons given.

### From the feasibility critic (computer, money, schedule)

| | Finding | Checked | What was done |
|---|---|---|---|
| F1 | Every 60-frame piece loads all 16 pages: likely out of memory, or hours of loading (must-fix) | **Confirmed.** `cinema-chapter.js` builds every page before drawing (its line 25); `film-chapter-parallel.sh` starts a fresh browser for each piece. The memory and loading figures are the critic's measurements on the notice corner; the "over 10 GB" for a whole chapter is an estimate | **Fixed.** Build only the pages a piece covers; pieces of about 270 frames; a free stand-in test first (step 1). Also no page shows more than two views, and two views of one place share one set |
| F2 | Disk: 1 GB for film is about 4 times too low (must-fix) | **Confirmed.** The notice corner's film is 45 MB for 13 s (3.5 MB a second); the old chapter 2 folders and scratch folders are the sizes stated | **Fixed.** New disk table (peak about 6.5 to 7.5 GB); pieces deleted after the silent film is checked; at most two full copies; check stills cleared per view; you're asked early about clearing about 9 GB of old files |
| F3 | The filming figures came from the profiler, not real filming | **Confirmed** from the critic's logs (2.1 s a frame on each of two helpers on held frames with fire and smoke) and the notice corner's filming log (about 12 s a frame on each of two helpers, before held shots) | **Fixed.** Measured figures used; about 5 to 6 hours plus 2 to 3 of re-filming; moving stretches one at a time; free test 2 shrunk to what's still unknown |
| F4 | `build_factory.py` does much less than assumed | **Confirmed**: tapering square chimney, sawtooth roof only, a tank on every factory, a 3.2 m shed, one merged window material, a bake by default (it has a `--no-bake` option) | **Fixed.** The real changes listed and budgeted (4 to 6 hours, town 1 hour) |
| F5 | `build_street.py` and `set_dressing.py` write into the pit village folder; running them would overwrite the base of the kept shot | **Confirmed**: fixed output paths, the 4-degree slope in the ground fallback | **Fixed.** Output folder and settings first; the notice corner rebuilt once to show it's unchanged |
| F6 | Painted people and whole-chapter loading are tested too late | Agreed | **Fixed.** New order: the loading test, the timing test, then the people test in the existing street, then the Works |
| F7 | Recording before 22 October risks re-recording and re-filming | **Confirmed** against the script's "Facts that change soon" | **Fixed.** Record after 22 October as its own request; film pages 13 to 16 last; re-record reserve US$0.30; page 13 checked after 4 November |
| F8 | Stage code for states, two views, windows, placards and the dot panel isn't listed | **Confirmed**: `projected-set.js` shows the behind painting only once the camera moves; `graphics.js` has no dot panel | **Fixed.** Listed and budgeted (8 to 12 hours); made simpler: state changes are whole pictures swapped or blended between two held frames; windows and placards change in steps |
| F9 | W2's plate was drawn slowed, though it's seen flat out for about 36 to 50 seconds | Agreed | **Fixed.** W2's main plate is flat out; the slowed state is a third painting used only where it differs (+25 cents; 20 paintings) |
| F10 | About 25 cents a painting, not 10 | **Confirmed** on fal's price list (2.4 cents a megapixel) | **Fixed.** One cost column at 25 cents; style picture at about 1 megapixel |
| F11 | Some Poly Haven models carry lettering or are unusable as they are | **Confirmed** where the saved list shows it (the suitcase is tagged "stickers"; crate 01 is a drinks crate; the generator; the poles kit) | **Fixed.** Crate 02; generator dropped; suitcase and till built by script; one pole cut out; converter gets its own choices list and folder. Also dropped: the rusted antique kettle (wrong for 2022) and the glazed close tiles (T17) |
| F12 | `find_jumps.py` on the whole chapter would need about 19 GB | **Confirmed**: it holds every frame as 32-bit numbers and makes two more copies | **Fixed.** Run per piece or page |
| F13 | K1's and C1's slides magnify too much | **Confirmed**: the painting has about 1.3 plate pixels per film pixel at the plate's spot | **Fixed.** Every slide 1.3 times or less (K1 1.85 to 1.42 m; C1 3.1 to 2.4 m); end frames checked with the plate before paying |
| F14 | No work-time estimate | Agreed | **Fixed.** Work-time table (about 110 to 170 hours, 5 to 7 days) and a first milestone (pages 3 to 5 painted, after about 2 to 3 days) |
| F15 | Props are copied into each Blender file and export; files may pass GitHub's 100 MB limit | **Confirmed** (83 MB and 62 MB for the notice corner). The `.blend1` point is partly wrong: `build_street.py` already turns those backups off | **Fixed in part.** Pictures kept outside the Blender files, the Works' export split, sizes checked before saving; backups off in each new script |

### From the teaching and pictures critic

| | Finding | Checked | What was done |
|---|---|---|---|
| T1 | W1 and W2 see the gate edge-on, with the windows and chimneys out of frame (must-fix) | **Confirmed** with the film's lens (60.4 degrees top to bottom, 18.1 degrees either side): from 1 m out the gate is seen at about 4.5 degrees | **Fixed.** Both cameras stand on the pavement in line with the gate's outer pier, facing up the lane; the queue stands in line on the pavement; the chimneys stand at the back of the yards so each view shows its own above the gate and the other's small |
| T2 | W3's lines meet on No. 2's gate, the bank is out of frame, the bottom 45% is empty (must-fix) | **Confirmed**: a camera 3 to 3.6 m right of the lane's middle puts the meeting point 0.15 to 0.18 of the frame's width right of the pier, and turning can't close it | **Fixed.** Camera on the lane's centre line, in an upstairs window across the cross street (your "move up to see the bigger picture"), the ground-level spot as a fallback; the bank moved to the lane's last third with a hanging sign face-on; the queue's tail and a handcart reach the bottom third; no in-world lettering relied on |
| T3 | G2's notice squashed at the frame's edge (must-fix) | **Confirmed**: 0.89 to 1.05 across, squashed to a quarter or a third of its width | **Fixed.** The close faces the camera at the head of a short street; the notice face-on; a placard within about 7 m |
| T4 | Level cameras at standing height drop the letter and the baskets off the bottom (must-fix) | **Confirmed**: the letter at 1.4 m falls below the frame | **Fixed.** K1 seated across the table (and the letter propped up, facing us); C1 and J1 at the next shopper's spot, about 2.4 m away |
| T5 | A nearly bare window under GLASGOW 1915 claims scarcity two years early (must-fix) | **Confirmed**: ledger C2-XA02 says the worst losses came in 1917 | **Fixed.** The display thins out (gaps, a half-empty tier); the history helper checks it with the picture in hand |
| T6 | About 130 cards, one every 3 seconds, against your "minimal" (should-fix) | **Confirmed** against decision 13 | **Fixed in part.** About 65 groups of words, about one every 6 seconds; most pages carry 3 to 5. Page 7, which holds three figures and the rent strike's outcome, carries 7, because each one is a figure or a placement Malina says |
| T7 | Page 14 drops "probably", and the American view loses its owner | **Confirmed** | **Fixed.** PROBABLY FEWER JOBS; the heading AMERICA'S VERSION OF OUR RESERVE BANK stays over its two cards until about 339.5 s with CLARA E. MATTEI coming in below; then MATTEI ARGUES heads her block |
| T8 | W4's men face the camera; the wall hides a queue along it; nothing shows wages | **Confirmed** (a head about 58 pixels at 6.5 m) | **Fixed.** The queue stands in line with the gate; the men are dark own-surface silhouettes, never painted; a WAGES pay envelope on the crate |
| T9 | Page 3 has no picture for "more things to buy"; a fade risks ghosts | Agreed | **Fixed.** Crates pop up in the open gateway on "things"; a time cut on "go" first, the fade as fallback; page 5's crates stay the same while the arrow climbs |
| T10 | Page 9's bank is a sliver and its sacks unreadable; sacks of money mislead | **Confirmed** by the lens | **Fixed.** The bank is placed where W3 sees it; the sacks are dropped; a NEW MONEY tag lands on the lit window and a dotted line stops halfway to the gates |
| T11 | Page 10's clue vanishes during the guess | Agreed | **Fixed.** The dot panel stays, small, beside WHICH ONE? |
| T12 | The checkout headline can't be read; the masthead echoes the New Zealand Herald | **Confirmed**: 4 cm letters at 2.5 m are about 26 pixels | **Fixed.** A newspaper bill in a wire stand with 4 or 5 big words (about 60 pixels a letter); THE WARNING label points at it; the masthead avoids every real paper's word |
| T13 | The rule cards don't fit; smoke crosses the words | Agreed | **Fixed.** The two rules stacked, each across 0.06 to 0.90, with a thin line to its chimney and a soft dark band behind the type; identical on pages 5 and 16 |
| T14 | The Works and Glasgow look like one world; every place is at dusk or night | Agreed | **Fixed.** Only the Works has the blue dusk; Glasgow grey late afternoon; the busy site low sun, the stopped site grey (so S1b is its own painting, not a patch: the same cost) |
| T15 | Two factories on one lane: why don't the men walk next door? | Agreed in part | **Fixed in part.** EACH ONE = A WHOLE COUNTRY stays to the end of shot 3a, and a high dividing wall splits the yards. A railway between them was not added: a bigger build for a small gain |
| T16 | FLAT OUT stays on a factory that is slowing | Agreed | **Fixed.** The tag becomes THE FLAT-OUT FACTORY SLOWS on "slows" |
| T17 | 1915 details: posters carry figures; two era signs break the lettering rule; glazed closes; a rolling counter shows figures she doesn't say | Agreed | **Fixed.** Poster wording with no figures; the poster and the sanitise sign written in as stated exceptions; the close plain with a two-tone band; ABOUT 20,000 FAMILIES lands whole on "twenty" |
| T18 | New Zealand details: plastic bags, milk, the Covid stripes, a thin $100 basket | Agreed | **Fixed.** Reusable bags, a plastic milk bottle, a plain sanitise sign, a full basket |
| T19 | NOT THE ONLY REASON should show whenever S1b does | Agreed in part | **Fixed in part.** It comes on with Malina's "only" and stays through every later shot of S1b. It doesn't go up before she says it (13b's first 10 seconds), because words on screen follow her voice; those seconds carry the dated figure and its STATS NZ credit |
| T20 | Eight walkers read as a few people, not crowds | Agreed | **Fixed.** About 14, further off (40 to 80 m), where faces can't show; the label points at the works' gate if they're dropped |
| T21 | Bright ceiling lights in the top band of C1 and J1 | Agreed | **Fixed.** The near ceiling rows off; a dark ceiling patch for the words, checked with the shot checker's brightest-parts measure |
| T22 | "Turned so the lines meet" can't work unless the camera stands in line | **Confirmed** (rule 1; log 31) | **Fixed.** Every view's camera is written as "in line with" its subject's edge, and the site's camera now looks up the driveway, not along the fence |

---

## Traps

- Never put a program's lettering on screen: every lettered surface keeps its own surface, near or far.
- Never a figure on screen that Malina doesn't say. The only numerals in the sets are "No. 1" and "No. 2"
  (her "the first" and "the second"). No price tags, keypads, lane, close or door numbers, dates, poster
  numbers or phone numbers on set dressing.
- Never name the school of economists, by name or by its letters: the card says ECONOMISTS WHO STUDY HOW
  MODERN MONEY WORKS.
- Mattei appears only as a typed name card, and her view only under MATTEI ARGUES, which stays on screen
  through "less power to ask for higher wages". The American view stays under its own heading.
- Never WON, RENTS FROZEN or NOT ENOUGH; never BUILDING NEW HOMES on its own; never "mostly" on page 15.
- No. 1 is always left of No. 2 in W3. Never swap them and never mirror a picture. W3 always shows the two
  as first described.
- Paint W3 before the other Works views: it is their style picture.
- The Works' gates are never in a plate: their leaves are own surfaces.
- A state changes only while the camera holds. Story changes happen on the spoken word that names them.
- The waiting men face away from the camera, never nearer than about 6 m. Where they face it (page 14) they
  are dark own-surface silhouettes, never painted.
- Every camera stands in line with its subject's edge. Turning it moves where the lines meet and every prop
  together; it can't close the gap.
- No slide brings its subject more than 1.3 times nearer.
- No New Zealand or Japanese banknotes or coins anywhere: they carry real people's portraits.
- No supermarket chain's, bank's or party's colours; hi-vis orange, never yellow-and-black.
- Don't run `build_street.py` or `set_dressing.py`'s export before they get an output folder: they would
  overwrite the base of the notice corner.
- Don't film before the chapter loads one page at a time, and don't run the jump finder on the whole film.
- Record the narration after 22 October; check page 13 after 4 November.
- The paid steps wait for your yes, batch by batch.
