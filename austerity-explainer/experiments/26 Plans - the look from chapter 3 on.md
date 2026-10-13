# Chapter 3 onward: four plans for the look, and the one to try first

This document puts the two reports together: the design review of chapter 2, and the research on 3D tools and cheap effects. I checked their main claims against the finished film, the project files and the tools' own web pages. From them I built four different plans for the series from chapter 3 on (Britain and Italy in the 1920s).

- Times are minutes:seconds into "20 Chapter 2 - what really causes inflation.mp4".
- Positions in the frame are shares of its height, measured from the top (0% is the top edge).
- Money is in US dollars.
- Nothing was spent, no account was made and nothing was uploaded.

## In short

### What I found

- **Both reports hold up when checked.** Three examples:
  - **The review says the bottom of the frame is dark and empty.**
    - I measured one frame a second across the whole film. The bottom tenth of the frame averages 38 (out of 255), against 74 to 81 in the middle.
    - In 70% of frames the bottom fifth is more than 30% darker than the middle. The review found 72%.
    - The frames I looked at match its descriptions: the empty checkout belt at 0:18, the empty factory floor at 0:21, the empty cobbles at 1:16.
  - **The research says Blender's fast drawing mode (EEVEE) crashes on this machine unless it is given a virtual screen**, which is a pretend display. With one, it draws a tall frame in about 20 seconds. I ran it myself:
    - without the virtual screen it stopped at once ("Couldn't open libEGL.so.1");
    - with it, the brick works and the town took 28.7 seconds for the first frame and 18.7 for the second.
  - **The prices and licences I rechecked on the tools' own pages match the research.** SAM 3D and TRELLIS cost 2 US cents a model through fal. Tripo through fal costs 20 to 40 cents. A World Labs world costs about US$1.26, with a US$5 minimum purchase.
- **One thing neither report says, which I found in the film's code.**
  - The tearing at the petrol station (2:39.5 to 2:40.9) happens during a move the page calls "pan down". The code also raises the camera about 0.85 units at the same time.
  - Any change in where the camera stands tears a painted room. A pure turn, or a pure lens zoom, does not tear it, because the camera stays where it is (as long as the view stays inside the painting).
  - In chapter 2, most "pans" and "zooms" also move the camera.

### What it means

- **Real 3D matters only in a few moments.** Your camera rule keeps the camera still most of the time, so a fully 3D scene pays off in three places:
  - the few camera moves;
  - light that changes on a word, such as windows going dark;
  - things that land on, or move among, real surfaces. An example is the coins that sank into the pavement in round 20.

  The rest of the time the viewer is looking at a still picture. So how full and how good that still picture is matters most.
- **The two reports answer the two halves of your question.**
  - The review says what to show. Give every strip of the tall frame a job, put people in front, use one kind of material, and let light carry facts.
  - The research says how to get real depth without tearing. Put true 3D shapes under the paint, and draw what doesn't change only once per shot.
  - The four plans combine those halves in different ways.

### The four plans

1. **Painted places, refilled.** Today's method, with paintings made for the tall frame, people in front, and no plain code-built props. It is the cheapest plan, but it is not fully 3D.
2. **The house.** Each chapter is staged in one cut-away building of society:
   - decisions at the top;
   - public services in the middle;
   - work and homes at the bottom;
   - the street in front.

   It is built as real 3D rooms with flat paintings on their walls.
3. **Built places, painted over.** Realistic period places are built in Blender and painted over by Flux in the series style. The painting is then shone back onto the 3D shapes, so the camera can move freely.
4. **Generated worlds.** A paid service, World Labs, turns each painting into a whole 3D place.

### What I recommend

**Plan 2, the house.**
- It fills the tall frame by its shape, and every strip of the frame carries Mattei's argument.
- It ends the tearing by its construction, because flat paintings on flat walls can't tear.
- It costs about as much to film as today.
- It doesn't depend on any untested step.

**The first test costs nothing.** I would build Britain's house as plain coloured boxes with chapter 1's existing cut-outs, lit at night, with one pan down from the vault to the mine. If it reads well on your phone, the next step is about ten wall paintings and a front wall, for about 35 US cents. That step happens only with your yes.

### Money

Plans 1 to 3 each fit inside the roughly US$3 left for paintings: chapter 3 would need between US$1.10 and US$2.65. Plan 4 needs at least US$5 at a new service, a new account, and your paintings uploaded there.

## Words used here

| Word | What it means here |
|---|---|
| painting | a picture painted by Flux on fal for the film |
| painted room | the project's word: a painting pushed back into 3D using its distance picture, so the camera can move a little inside it |
| cut-out | a painted figure or object cut out with a narrow paper edge |
| card model | a plain 3D object built in code: the banknote bundles, coins, oil barrel, house frame |
| Blender model | a detailed 3D model built in Blender by script: the brick works, the town, the desk |
| set | a real 3D place built from shapes and models, which the camera can move through without tearing |
| projection | the project's word: shining a painting onto 3D shapes from where it was painted, like a slide projector |
| paint-over | Flux repainting a plain picture of a set in the series style, guided by its distance picture so the shapes stay where they are |
| background still | the unchanging part of a still shot, drawn once and reused behind everything that moves. The research calls it a "plate"; I use another word because the project's "clean plate" means something else. |
| object maker | a service that turns one picture of an object into a 3D model: SAM 3D, TRELLIS, Tripo |
| splat world | a 3D place made of millions of soft coloured dots, made by a world-making service from one picture |
| virtual screen | a pretend display that lets Blender's fast drawing mode (EEVEE) run on this machine, which has no graphics card |
| baked light | light worked out once in Blender and painted onto a model, so the film engine doesn't work it out every frame |
| the stage | the project's film engine, which draws each frame in a hidden browser using a 3D library called three.js |
| band | a horizontal strip of the frame, given as a share of the height from the top |
| shot | the stretch from one cut to the next |
| move | one of your named camera moves |

## Where the two reports agree and disagree

**Where they agree:**
- Painted rooms tear when the camera changes position.
- Plain card models break the painted world.
- The camera should stay still, and an unchanging background only needs drawing once.
- A still camera needs a living world: smoke, rain, dust.
- Most of those effects are almost free on this machine.

**Where they, or the older project notes, disagree, and how I settled it:**

| Question | What one side says | What the other side says | What I found, and how I settled it |
|---|---|---|---|
| Can Blender draw the film? | Older notes (lesson 60, decision 25): far too slow, 35 to 90 seconds a frame, 80 to 200 hours a chapter. | Research: Blender's fast mode works with a virtual screen, about 20 seconds a frame. | My run: 28.7 seconds for the first frame, then 18.7. The old note is out of date for single pictures. Blender is still too slow to draw every frame (about 35 to 60 hours a chapter), so use it for one background still per shot. |
| What do detailed models cost to film? | Review: Blender props push a page toward 12 to 16 seconds a frame, so keep them for a few rooms. | Research: with baked light, the brick works drew in 0.31 seconds instead of 0.85. | Lesson 70 says the cost on page 3 was mostly the realistic surfaces, not the detail. With baked light, detailed models are affordable. Keep the review's caution until the first test measures it. |
| Is glass slow to draw? | Review: its money-machine idea would film slowly, because see-through glass is slow to draw (5 to 9 hours a chapter). | Research: five full-frame see-through layers added only 0.32 seconds a frame. | Glass is not the cost. Realistic metal surfaces are (lesson 70). |
| How do you make 3D look painted? | Review: paint each wall once and hang it on a flat wall. | Research: paint over a whole picture of each shot, then use projection. | Both work. Painting each wall is consistent from every angle and cheap. A paint-over gives richer painted light, but each paint-over is a new painting, so the same street can change between shots. My rule: paint over once per place, and start any later paint-over from the first one. |
| What caused the petrol station tear? | Review: "the sideways move". | (not covered) | It is an upward move: the camera rises 0.85 units during a "pan down". The fix for painted rooms is pure turns and pure lens zooms. |
| How much of the film is frozen? | Review: nothing moves in 60% of frames. | (not covered) | My count is between a third and three-fifths of frames, depending on how small a change counts. Pages 4 and 6 never freeze, because rain and snow keep falling. The review's point stands. |
| How much money is left? | Both reports: about US$3. | The notes count about US$1.28 of fal spending since your "up to $10" note (US$1.16 for chapter 2, 12 cents for log 22). | I planned every option to fit inside US$3 and flag the difference below for you to settle. |
| Is the Phillips machine on show in Wellington? | Review: unsure. | (not covered) | The Reserve Bank's own factsheet says one has been on display at its museum since 2007. I did not confirm that it is still there. |

**One rule for the frame, used by every plan below (the review's, checked against the film):**

| Band | Its job |
|---|---|
| 0 to 7% | calm: sky or ceiling, under the app's top bar |
| 7 to 33% | the world above: place title, the hook, and whatever holds power or promise |
| 33 to 70% | the subject, big: 50 to 80% of the width |
| 70 to 80% | the ground, where things land |
| 80 to 100% | the people nearest us, under the phone's captions: faces, never words |

**The painting prompts' rule that "the lower quarter of the picture is the empty floor/street" has to go in every plan that uses paintings.** That rule is where the empty bottom of chapter 2 comes from.

## The four plans

Chapter 3's history isn't researched yet. So every name, date, tax and piece of wording in the frames below is a placeholder until chapter 3's research is done.

To make the plans easy to compare, each one shows the same three moments:
- 1922: the cuts reach the council homes.
- 1925 and 1926: back to gold, then the strike.
- Italy: the same medicine, and the economists Mattei argues helped.

### Plan 1: painted places, refilled

**The idea.** Keep chapter 2's way of working: paintings as painted rooms, cut-outs, and documentary titles and figures on top. Paint every place for the tall frame, fill its bottom with the people the line is about, and replace every card model with a painted object. The camera keeps to pure turns and pure lens zooms, which never tear a painting, plus short pushes where nothing tall stands near the camera.

**Three frames of chapter 3**

*Frame 1. Britain, 1922: a council estate stopped half-built.* A new painting at dusk in light rain. It is seen from first-floor height, so the road climbs the frame on a diagonal instead of running straight down the middle.
- 7 to 33%: low sky, scaffolding poles and the town's chimneys, with the title "BRITAIN 1922" at about 9%.
- 33 to 70%: the row of houses: three finished ones with lit windows at the far end, and brick shells with bare roof timbers nearer.
- 70 to 100%: a family at the site fence (two adults, two children, a pram, bundles). They are cut-outs from a new crowd painting, with heads and shoulders large, under the captions.
- On "cut":
  - chapter 1's scissors crash in and cut the rope across the site gate;
  - the scaffold lanterns go out from the far end toward us (dark patches laid over the painting);
  - a typed notice slaps onto the site board;
  - the rain thickens;
  - the one hook is "CUT".
- Camera: one pan down from the scaffolding to the family, as a pure turn.

*Frame 2. 1926: the strike, then the lockout.* A new painting at dawn of a pit village, seen from a little above its street.
- 7 to 33%: the pithead tower and its wheels against a pale sky, with smoke from the engine house.
- 33 to 70%: terraced cottages stepping down the slope, some windows lit.
- 70 to 100%: miners walking to the pit, every face different, lamps glinting.
- On "strike":
  - the smoke thins and stops;
  - the windows go dark one by one;
  - the miners stop and turn to face us (one set of cut-outs swapped for another);
  - a typed notice lands on the pit gate;
  - a printed calendar on a cottage wall flips from May to November while snow begins.
- Camera: one zoom in onto the gate notice, as a pure lens zoom.

*Frame 3. Italy, 1922 to 1925: the finance ministry.* A new painting from low down, looking up at a tall window, which is how the film looks up at power.
- 7 to 33%: the window, Rome's roofs and, far off, a factory chimney, with the title "ITALY 1922–1925".
- 33 to 70%: the desk, with typed name cards:
  - "ALBERTO DE STEFANI · FINANCE MINISTER";
  - books carrying the typed names of the economists Mattei names;
  - all under "MATTEI:" with her book's credit, the pattern the review praised at 3:50.
- 70 to 100%: the open ledger at the desk's near edge, in type about 40 pixels tall so it can be read on a phone.
- On her words, the line for a tax on the rich is struck through in dark ink. A red stamp lands on a new line for a tax on wages or on what everyone buys.
- Camera: one pan down from the window to the ledger, as a pure turn.

**How it fills the frame and serves the story.**
- **The bands come from the painting prompt.**
  - The nearest band holds the people or things the line is about, painted as separate cut-out layers.
  - The camera height changes with the meaning: low for power, high for pressure.
- **"Who decides and who pays" is told by cutting between places**, as in chapter 2, not inside one frame.
- **One world.**
  - Every object is painted.
  - People come from crowd paintings in which every face is different.
  - The white paper edges are darkened so they stop glowing like stickers.

**Tools and effects.**
- Flux on fal, and the stage as it is.
- Light changes as dark patches over the painting.
- Rain, snow, smoke, dust in lamp beams and lamp flicker, with grain added after filming.
- Log 24's stand-ins for any move that must shift the camera.

**Money and computer time.**
- **About US$1.40 for chapter 3.**
  - about eight place paintings at 2k: 80 cents;
  - three crowd paintings: 30 cents;
  - about ten painted objects at 1k: 25 cents;
  - distance pictures and masks: a few cents.
- **About 3.5 hours of filming** for a 4.5-minute chapter. That is about 3 seconds a frame, like chapter 2's painted pages, filmed two stretches at a time.

**What it takes to build.** The least of the four: new prompt rules, crowd paintings and painted objects. Pages are built as now.

**Main risks.**
- It stays chapter 2's look, only fuller. It adds no real depth, and you asked for fully 3D scenes.
- Pure turns and lens zooms look flatter than pushes, because nothing near slides against anything far.
- The collage look comes back if card models creep in again.

**Smallest first test (free).**
- Redo two chapter 2 moments with pieces that already exist:
  - "workers wait at the gate" (0:46 to 0:51), with chapter 1's front crowd big in the bottom band;
  - page 7's move as a pure turn.
- It passes if the bottom band carries the line, nothing tears, and it reads on your phone.
- It fails if the paintings' empty floors can't be covered without crowding.
- After that, one new painting made for the tall frame would cost 10 US cents, with your yes.

### Plan 2: the house

**The idea.** Each chapter is staged in one tall building of society, cut open from roof to cellar like a doll's house:
- decisions on the top floor;
- what public money pays for in the middle;
- work and homes at the bottom;
- the street and its people in front.

The rooms are real 3D boxes with flat paintings on their walls. That means the camera can move freely through the house without tearing, and the light in each room can carry the facts. This is the review's chosen direction; the way of building it combines the review with the research.

**Three frames of chapter 3**

*Frame 1. Britain, 1922: the cuts.* The whole house in a still shot, at night.
- 0 to 10%: night sky and chimney smoke, with "BRITAIN 1922" at about 9%.
- 10 to 32%, the top floor:
  - a committee room with a long table, empty chairs and typed name cards. No drawn faces of real people.
  - the Bank's vault, dim.
- 32 to 66%, two middle storeys, all warm-lit: a classroom, a clinic, and a council-house building site with scaffolding and bricklayers.
- 66 to 84%, the ground floor: a factory floor with a lathe, and a kitchen with a family at the table and a pay packet.
- 84 to 100%, the cellar: the coal seam, with miners' lamps glinting under the captions.
- On "cuts":
  - an axe drops through the roof into the middle storeys, with a short shake. (The 1922 cuts were nicknamed "the Geddes Axe"; to be confirmed.)
  - the building site goes dark and its scaffolding folds flat;
  - the classroom dims to half;
  - a typed card slides onto the site's door;
  - "CUT" appears in the sky.

*Frame 2. 1925 to 1926: back to gold, then the strike.* The same house, with one pan down.
- **On "back to gold":**
  - gold bars land in the vault, glinting, with a small shake;
  - the iron column down the middle takes the weight, and dust falls in every room below;
  - the cellar's ceiling lowers, so the mine shrinks from about 16% to 12% of the height;
  - the miners' pay packets are swapped for smaller ones;
  - the hook is "BACK ON GOLD, 1925".
- **Camera:** pan down from the vault to the mine. This is your "pan down to signal pressure".
- **In 1926:**
  - the lower rooms empty as their people walk out into the street in front of the house, filling the bottom fifth with caps, faces and blank placards;
  - the lower windows go dark;
  - after nine days the crowd folds away, except the miners;
  - the miners stay outside the dark mine while a calendar on its wall flips through the months, and snow falls.

*Frame 3. Italy: the same medicine.* Two half-buildings, one above the other.
- 0 to 47%: Britain's house, smaller.
- 53 to 100%: an Italian building cut open, with arcades at street level, a ministry upstairs, a telephone exchange and a factory.
- About 50%, between them: "SAME ADVICE".
- On her words, the same three things happen in both buildings:
  - pay packets are swapped for smaller ones on both ground floors;
  - in the Italian building, a public company's sign changes to "SOLD", and its room slides up a floor into the owners' rooms;
  - on the Italian top floor, a typed ledger line for a tax on the rich is struck through, while a stamp lands on the ground floor for a tax on what everyone buys.
- Camera: move down into the Italian top floor, onto the typed name cards: "ALBERTO DE STEFANI · FINANCE MINISTER" and the economists Mattei names, under "MATTEI:".

**How it fills the frame and serves the story.**
- **The building's shape is the band rule.** Each band is a level of society, so no band is ever "just floor". The cellar and the street sit under the captions, where faces can go and words can't.
- **Cause and cost share one frame.** The weight lands at the top, and the ceiling lowers at the bottom.
- **Your camera grammar becomes literal.** Pan up to the experts' promises, pan down to the pressure, move up to see the whole building, move down into one room.
- **A rule I would add: in whole-house shots, light only the one to three rooms the line is about, and keep the rest dim.**
  - A phone shows the 1,080 pixels across about 65 to 71 mm. So a storey is about 2 cm tall, and a person in it about 1.2 cm, with a face about 1.5 mm across (my arithmetic).
  - Whole-house shots therefore work through light, posture and movement. Faces and name cards need the camera to move into a room.

**Tools and effects.**
- **The house itself:**
  - room boxes with flat wall paintings, painted straight-on with little painted depth;
  - a front wall built in Blender by script, with baked light;
  - each room lit by baked or painted light, not by a dozen live lamps (every live lamp adds drawing time to everything it lights).
- **People and objects:**
  - chapter 1's cut-outs: crowds, the dole queue, the pithead, council houses, pay packet, iron weight, gold bars, scissors, school, lathe, kitchen table and the map of Italy;
  - new crowd paintings;
  - cut-out edges darkened so they read as figures in a model;
  - objects turned into 3D by SAM 3D or TRELLIS (2 US cents each), wearing their paintings;
  - free furniture from Poly Haven (free for any use, no credit needed).
- **Effects:** rooms switching on and off, dust falling under the gold, a glow on the gold, haze and chimney smoke, snow and lamp flicker.
- **Later, if flat walls look too plain:** Plan 3's paint-over for the whole-house views, one painting per view, shone back onto the boxes.

**Money and computer time.**
- **About US$1.65 for chapter 3.**
  - Each building needs about ten wall paintings at 1k (25 cents), a front wall and sky at 2k (10 cents), and about fifteen new people and objects at 1k (38 cents).
  - The chapter has two buildings, plus two crowd paintings (20 cents).
  - The optional painted-over finish adds about 15 cents per whole-house view.
- **Filming: about 2.5 to 4.5 hours a chapter.** My estimate is 2 to 4 seconds a frame. In the research's test, a painting, a 34,000-triangle model, a lamp and shadows drew in 0.86 seconds. Background blur adds about 1 second, and glow 0.3.
- **Drawing each still shot's unchanging background once would cut that further.**

**What it takes to build.** A medium amount of work:
- design two buildings: the rooms, their scale and one light plan;
- write a house piece for the stage: rooms, lights on and off, rooms that slide, the column;
- build the front-wall model and make the wall paintings;
- draw up a map of which room changes on which word.

One building serves most of a chapter's shots.

**Main risks.**
- **It could read as a diagram**, especially if the rooms are sparse. That is the same problem as your round-19 note that the card house was "sparse in detail". Rooms need painted walls, period furniture, people and light.
- **Whole-house shots can't show faces.** The camera has to move in for the human moments.
- **One building for a whole chapter could tire the eye.** As the review suggests, use the whole house for openings, turning points and endings (about a third of the shots) and single rooms for the rest.
- **It is a symbol, not a real place.** The documentary place-and-year feel has to come from the titles, the period rooms and the street.
- **Italy needs care.** The Italian building must carry no regime symbols, and black must not become a colour code.

**Smallest first test (free, about half a day to a day of building).** This is the review's test, with pass marks added.
- **Build:** Britain's house as plain coloured boxes with chapter 1's cut-outs, lit at night.
- **Draw:**
  - three test pictures: the whole house; the middle floors dimmed after "cuts"; the street full of strikers;
  - two short moves: a pan down from the vault to the mine, and a 1-unit sideways step.
- **It passes if:**
  - you can tell which room is which on your phone;
  - the frame feels full and the pan down reads as pressure;
  - nothing tears;
  - it draws in under about 5 seconds a frame.
- **It fails if** it reads as a diagram, or the rooms blur together.

### Plan 3: built places, painted over

**The idea.**
- Each place in the chapter is built as a real 3D set in Blender, from script and free models.
- Each set is drawn once from its main view, and Flux paints over that picture in the series style.
- The stage then shines the painting back onto the set's shapes (projection), so the camera can push, rise and step sideways without tearing.

This is the research's leading route, and the natural next step after logs 22 to 24. There, shapes were fitted to a painting; here, the painting is made to fit the shapes.

**Three frames of chapter 3**

*Frame 1. Britain, 1922: a council estate stopped half-built.* A built set at dusk in rain. It has rows of brick council houses, a few finished and most at shell or foundation stage, scaffolding, a muddy road curving away, and the town's chimneys behind.
- 7 to 33%: sky, scaffolding and chimneys, with "BRITAIN 1922".
- 33 to 70%: the curving road between finished houses (lit windows) and shells.
- 70 to 100%: the family at the fence (cut-outs).
- On "cut":
  - the lanterns go out house by house (two background stills, one lit and one dark, blended house by house);
  - the bricklayers fold away;
  - a typed notice slaps onto the site board;
  - the rain thickens.
- Camera: one move up, to see the bigger picture.
  - The camera rises about 3 units over the family and shows the whole estate: a few finished houses, then rows of bare foundations running to the edge of the frame.
  - A painted room can't do this; a set can. "CUT" appears in the sky.
  - The high view needs a second paint-over, started from the first one, so the estate doesn't change.

*Frame 2. 1925 to 1926: gold, then the pit.*
- **A short shot in a small vault set.** Gold bars slide onto the shelves, glinting, with "BACK ON GOLD, 1925". Hard cut on "wages".
- **The pit village set.** The pithead tower with turning wheels is built by script (the research found no free model of one), with the engine house and terraced cottages on a slope.
  - 7 to 33%: the tower, the wheels and smoke.
  - 33 to 70%: the cottages, with lit windows.
  - 70 to 100%: miners walking to the pit.
  - On "strike", the wheels slow and stop (a real moving part), the smoke stops, and the miners stop and turn.
  - Camera: one pan right with a real sideways step of about 1.5 units along the street. The tower slides behind the cottages, and the shot ends on doorways where families stand. A calendar in a window flips the months, and snow falls.

*Frame 3. Italy: the ministry.* A built office with a tall window, a coffered ceiling, a long desk and free furniture, painted over.
- The bands are the same as Plan 1's frame 3: window and title at the top; desk, name cards and the "MATTEI:" credit in the middle; the ledger at the bottom.
- Camera: one move down from window height to the ledger. This is a real change of position, so the desk's edge slides past in the foreground.

**How it fills the frame and serves the story.**
- The same band rules and people in front as Plan 1.
- Moves that show scale and consequence, like the estate's empty foundations.
- Real contact between things and surfaces.
- "Who decides and who pays" is still told by cutting between places.

**Tools and effects.**
- **Building the sets:**
  - Blender by script, with free models and textures from Poly Haven (the research counted 521 models and 868 textures);
  - Blender's fast drawing mode with a virtual screen, for the background stills.
- **Painting them:**
  - Flux paint-over, guided by the distance picture;
  - the projection code from log 24;
  - baked textures for surfaces the main view never saw.
- **People and effects:**
  - people stay painted cut-outs;
  - effects as in Plan 2, plus lamplit wet streets with real reflections (+0.38 seconds a frame), which become possible once the ground is real.
- **A rule I would add:** paint each place over once, from a view drawn wider than the frame. When a shot needs a new view, start its paint-over from the first painting shone onto the set.

**Money and computer time.**
- **About US$1.10 to 2.65 for chapter 3.**
  - About seven places, each with one or two paint-overs at about 8 to 15 US cents: US$0.55 to 2.10.
  - Crowd paintings: 30 cents.
  - Painted objects: 25 cents.
- **Background stills take about 15 to 25 minutes a chapter.** Each one takes 20 to 30 seconds, and about 25 shots need a lit and a dark version.
- **Filming takes about 2 to 3.5 hours a chapter**, at 1.5 to 2.5 seconds a frame. The projection itself drew in 0.3 seconds in the research.

**What it takes to build.** The most work of the four:
- six to eight sets per chapter, each with its main view, background stills, paint-over and projection set-up;
- a stage that can load each set together with its painting.

**Main risks.**
- **The paint-over may shift edges by a few pixels** (lesson 80), which would show as fringes when the camera moves. This is untested, because testing it costs money.
- **Each paint-over is a new painting.** Unless "paint once per place" holds, a street can change between shots.
- **Unseen surfaces need matching light.** In the research's test, surfaces the main view never saw came out too dark: a dark wedge appeared in the corner after a 1.5-unit step.
- **Modelling period places by script is slow**, for example a pithead tower or a Roman ministry. Plain models look like a model railway until they are painted over.
- **Every paint-over needs the usual check** for wrong-era details and symbols.

**Smallest first test (about 10 to 15 US cents, with your yes, about a day).**
- Block out one place: the pit village street, partly from the existing town model.
- Draw one background still, run one Flux paint-over, shine it back, and film a 2-second move with a 1-unit sideways step and a push.
- It passes if the painted edges stay on their shapes within about 3 pixels, and it looks like chapter 2's paintings on your phone.
- The free half (shining a filtered Blender picture back onto its set) already passed in the research.

### Plan 4: generated worlds

**The idea.** Paint one picture per place with Flux, as now. World Labs' Marble service then turns each painting into a splat world: a whole 3D place the camera can move through. Moving parts come from object makers and wear their paintings. The stage shows the worlds with World Labs' free Spark viewer.

**Three frames of chapter 3.** The same three moments as Plan 1, but each painting becomes a world.
- **Frame 1, the council estate.**
  - One move down, from scaffolding height to the family's eye level.
  - The service invents the ground and fence the painting didn't show, so every invented part needs the period check.
  - The lanterns can't be switched off inside the world, because its light is fixed. The dimming has to be a dark patch laid over the frame, which only holds while the camera is still.
- **Frame 2, the pit village.**
  - One pan right with a sideways step along the street.
  - The wheels are frozen into the world, so a separate wheel model from SAM 3D (2 US cents) has to be laid over them to turn.
  - The miners are cut-outs, because the research found these services handle people poorly.
- **Frame 3, the ministry.**
  - One move down from the window to the desk.
  - The name cards and the ledger are the stage's own typed objects, because generated worlds blur writing.

**How it fills the frame and serves the story.** The same as Plan 1, but with real depth when the camera moves. Light can't carry facts the way it can in Plans 2 and 3.

**Tools and effects.**
- World Labs' service: its app, or its pay-as-you-go access for scripts (an API).
- Spark 2.3.1, a free viewer under a licence that allows any use. The stage's three.js would have to be upgraded from version 0.169 to 0.180 or newer.
- SAM 3D, TRELLIS or Tripo through fal for moving parts.
- Cut-outs for people, and the same effects as Plan 1.

**Money and computer time.**
- **About US$10 for chapter 3, or US$35 a month.** That is well over the US$3 left.
  - A world costs about US$1.26 through pay-as-you-go (1,580 credits, at US$1 per 1,250), and credits are bought in lots of at least US$5.
  - About seven worlds is about US$9, plus about US$1.10 of paintings.
  - In the app, commercial rights start at the Pro plan, which is US$35 a month.
  - Rough drafts cost about 18 US cents a world.
- **Computer time depends on drawing still backgrounds once.**
  - Drawing takes 7 to 25 seconds a frame (500,000 to 2 million dots), or about 9 with 2 million capped to 600,000.
  - Drawing each still shot's background once is essential: then filming is about 3 to 5 hours a chapter.
  - Drawing every frame would take about 16 to 56 hours.

**What it takes to build.**
- A three.js upgrade, and a re-check of every existing page.
- Spark added to the stage.
- An account, a purchase, and uploads of your paintings.

**Main risks.**
- **Your paintings would be uploaded to a new service.** Its terms say your inputs "may be visible to others", and they licence your inputs to World Labs, including for training. Paid users can opt out from then on.
- **It invents what the painting didn't show**, which is risky for period detail.
- **The picture has limits.** Its light can't change, and the dots look soft or needle-like up close.
- **It is over budget**, and needs a new account.
- **Don't use the cheaper alternative.** The Hunyuan world maker on fal costs 30 US cents, but it comes from an open model whose licence forbids using or displaying its output in the UK, the EU and South Korea. It is unclear whether that follows the hosted version, so I would not use it for a film about Britain.

**Smallest first test (at least US$5, plus your yes to an account and an upload).**
- Make one world from an existing painting (the Glasgow tenements), then film a 1-unit sideways step and a push.
- It passes if it holds up at phone size with period details intact, in under about 10 seconds a frame.
- The research's free run on World Labs' public sample street proves only that the technique works here. It doesn't prove the series' painted style.

### Where the other ideas fit

- **The review's money machine.** Use one gauge or pipe inside the house for moments about how money moves, rather than making it the series' look. The Phillips machine it is modelled on has a New Zealand link, noted above.
- **The review's pop-up book.** Borrow its paper actions (cut, fold flat, pop up) for the big moments. Keep the page turns as the thread back to chapter 1.
- **Tripo and the other object makers** make single objects, not scenes, so they are tools for props in Plans 2 to 4. In order of preference:
  1. SAM 3D (2 US cents), already proven on the petrol station in log 22.
  2. TRELLIS (2 cents).
  3. Tripo through fal (20 to 40 cents), for a prop that must hold up from every side.

  Never use Tripo's free plan. Its terms give Tripo all rights to what free users upload and make, and its free models are public and non-commercial. Tripo's own Pro plan (US$20 a month, billed yearly) only makes sense for many props. A three-way prop comparison on one painted cut-out (SAM 3D, TRELLIS and Tripo) would cost about 34 US cents.
- **Drawing each still shot's unchanging background once**, and redrawing only what moves, would cut filming time in every plan. It is a change to the engine. Watch for the layering fault in lesson 51.

### Cheap effects that carry chapter 3's story

The added drawing times are the research's measurements on this machine.

| Effect | What it carries in chapter 3 | Added drawing time here |
|---|---|---|
| Smoke that stops | chimneys and the pit going cold in the strike and lockout | about 0.4 seconds a frame for 40 big puffs |
| Snow | the lockout running on into winter | about 0 |
| Rain | council homes left half-built | about 0.03 seconds |
| Dust in lamp beams, or falling | still offices; the gold's weight shaking the rooms below | about 0 to 0.06 seconds |
| Glow | the gold bars of 1925, furnace mouths, lamps | about 0.33 seconds |
| Lamp flicker | miners' lamps, gas lamps | about 0 (not measured) |
| Haze | coal smoke; separating near from far | about 0 |
| Wet-ground reflections | lamplit streets (needs real 3D ground: Plans 2 and 3) | about 0.38 seconds |
| Grain, dark corners, colour finish | an archive feel; one finish over every material | about 2 minutes a chapter, after filming |
| Painterly filter | turns a Blender picture into brushwork | about 1.6 seconds per background still in Blender. Avoid it in the stage: 2.5 to 4.7 seconds a frame, and it shimmers on moves. |

## The plans side by side

| | 1. Painted places, refilled | 2. The house | 3. Built places, painted over | 4. Generated worlds |
|---|---|---|---|---|
| Look | chapter 2's paintings, fuller | a lit, cut-away model building with painted walls | chapter 2's painted look on real 3D places | the paintings as 3D places; soft dots up close |
| Story fit | good place by place; who decides and who pays is told by cutting | strongest: every wide shot shows who decides and who pays | as Plan 1, plus moves that show scale | as Plan 1; light can't change on a word |
| Fully 3D | no | yes | yes | yes |
| Money, chapter 3 | about US$1.40 | about US$1.65 (+ about 15 cents per painted-over view) | about US$1.10 to 2.65 | about US$10, or US$35 a month |
| Filming time, 4.5-minute chapter | about 3.5 hours | about 2.5 to 4.5 hours (my estimate) | about 2 to 3.5 hours, + 15 to 25 minutes of background stills | about 3 to 5 hours with still backgrounds drawn once; 16 to 56 without |
| Building effort | low | medium | high | medium, plus a three.js upgrade |
| Biggest risk | no new depth; tears on any change of camera position | reads as a diagram; small rooms on a phone | paint-over edges drift; places change between shots | uploads and money; invented details; light can't change |
| What carries over | nearly everything | the stage, cut-outs, effects, titles and figures, Blender skills | the stage, log 24's projection code, Blender skills | paintings, cut-outs, titles and figures; the stage needs upgrading |
| First test | free | free | 10 to 15 US cents | at least US$5, an account and an upload |

## What I recommend, and why

**Plan 2, the house, with three things borrowed from the others:**
- From Plan 1: the new painting rules (no empty lower quarter; the camera height chosen for power or pressure), crowd paintings in which every face is different, and fewer, bigger words.
- From Plan 3: Blender for the front wall and props, baked light, background stills, and the paint-over as a later upgrade if flat walls look plain.
- From the research: props from SAM 3D or TRELLIS (2 US cents), and the cheap effects above.

**Why:**
1. **It fills the tall frame by its shape.** The bottom band, dark and empty in 70% of chapter 2's frames, becomes the cellar and the street, where the people are.
2. **It carries Mattei's argument in every wide shot.** Who decides sits at the top and who pays at the bottom. Cause and cost are joined by something you can see: the weight, the column, the lowering ceiling.
3. **It ends the tearing by its construction**, with flat paintings on flat walls inside real rooms. Nothing in it depends on an untested step; the paint-over is an upgrade, not the foundation.
4. **It is cheap.** Chapter 3 needs about US$1.65 of paintings, and filming takes about as long as today.
5. **It reuses the kit**: the stage, chapter 1's cut-outs, the effects, the titles and figures, and the Blender skills from round 20.
6. **It grows through the series.** Thatcher's chapter can return to the same British house sixty years on, with the same mine in the cellar. New Zealand and Australia get houses of their own.

**The first test.** Free, about half a day to a day of building, as described under Plan 2:
- Britain's house as plain coloured boxes with chapter 1's cut-outs, lit at night;
- three test pictures;
- a pan down from the vault to the mine, and a 1-unit sideways step;
- drawing time measured.

**The free test answers whether the house reads and fills the frame. It doesn't answer whether it looks rich enough.** That comes next, with your yes: about ten wall paintings and a front wall, about 35 US cents. Then a one-page trial on Malina's chapter 3 words, once the chapter 3 script exists, with the independent critique before filming (lesson 53).

**What would change my mind.** If the free test reads as a diagram, or the rooms blur together on your phone, I would switch:
- to Plan 3, if you want realistic places and full camera freedom (first test 10 to 15 US cents);
- to Plan 1, if time and money matter most.

**How sure I am.**
- The house is the review's idea, and nobody has built or seen it yet.
- I checked the review's claims about chapter 2 against the film, and they hold. But whether the house looks striking rather than like a diagram is a judgement the free test exists to settle.
- The filming times for Plans 2 to 4 are my estimates from the research's measurements, not tests of those scenes.

## What I checked, what I didn't, and what I'm unsure of

**Checked.**
- **Read:**
  - both reports in full;
  - the project story, all of it, including logs 19 to 25;
  - all 30 items in Decisions and all 80 lessons;
  - the style rules, the kit's lessons and traps, and the painting prompts' rules;
  - the round-20 camera guide and chapter 2's script;
  - the stage's still-shot code, page 7's camera moves, and every zoom move in chapter 2's pages.
- **Looked at 40 frames of the film:**
  - 0:02, 0:12, 0:18, 0:21, 0:25, 0:32, 0:37, 0:47, 0:50, 0:53, 1:05, 1:10, 1:16, 1:20, 1:28, 1:33, 1:44, 2:00, 2:06, 2:12, 2:23, 2:38, 2:40.4, 2:41, 2:45, 2:55, 3:13, 3:16, 3:22, 3:43, 3:50, 4:12, 4:16 and 4:22;
  - close frames at 2:23.2, 2:23.4, 2:39.5, 2:40.9, 4:15.4 and 4:16.0.

  They match the review's descriptions: the cut-off heads at 0:25, the boats on a floor pool at 0:32, the copied strips at 1:20 and 3:43 to 3:50, the soap-like bundles at 2:00, the black slab at 2:23, the smear at 2:40.9, and the needle falling while Malina says "raising" at 4:16.
- **Measured:**
  - brightness by tenth of the height, on one frame a second (270 frames);
  - the change from frame to frame, across all 8,110 frames.
- **Pictures:**
  - chapter 2's background contact sheet, test 24 (the 3D petrol station), and chapter 1's 45 cut-outs;
  - the research's evidence pictures: render comparison, painterly crops, projection test, splat comparison, effects sheet, baked-light comparison;
  - its raw timing logs, which match its tables.
- **Ran:** Blender's fast drawing mode with and without a virtual screen.
- **On the tools' own pages** (13 October 2026):
  - Tripo: pricing page, and terms sections 5.2.1 and 5.2.2 (read in a hidden browser, because the site blocks plain downloads);
  - fal prices through the account's price lookup, and fal's Tripo page;
  - World Labs: pay-as-you-go pricing, the app's pricing, its FAQ and its terms;
  - the Hunyuan3D 2.1 and HunyuanWorld 1.0 licences;
  - Spark 2.3.1's package details, and the stage's three.js version;
  - Blender 5.3 release notes;
  - Stable Fast 3D's instructions (it can run without a graphics card, but needs a sign-up to download);
  - the SAM 3D, Apple SHARP, Depth Anything 3 and Poly Haven licences;
  - a search result citing the Reserve Bank of New Zealand's factsheet on the Phillips machine.

**Not checked.**
- Any paid step: a Flux paint-over, any object maker or world maker on your paintings.
- The house in 3D: I didn't build it. Nor the filming times of Plans 2 to 4, which are estimates.
- Tripo's month-to-month price (its page showed the yearly price), Blendkit and Sketchfab terms, and Blender 5.3 itself.
- Chapter 3's history: every name, date, tax and piece of wording in the frames is a placeholder.
- The sound, playback at full speed, and a real phone screen.

**Unsure.**
- **How much money is left.** The brief says about US$3. Your "up to $10 in Fal" was said for chapter 2, and the notes count about US$1.28 of fal spending since then. On that reading, more is left. I planned everything to fit US$3; which count is right is your call.
- **Whether the house looks striking or reads as a diagram.**
- **Whether Flux's paint-over keeps edges within 3 pixels.**
- **Whether Tencent's licence restrictions follow its models hosted on fal.**
- **Whether the Phillips machine is still on display.**

My working files (frames, contact sheets, measurements, the Blender check) are in this session's working folder, which is cleared when the session ends. No project file was changed.

## Sources (read 13 October 2026)

**Tripo**
- https://www.tripo3d.ai/pricing
- https://www.tripo3d.ai/terms (last updated 11 July 2025)

**fal**
- https://fal.ai/models/tripo3d/h3.1/image-to-3d
- fal's price lookup for: fal-ai/sam-3/3d-objects, fal-ai/trellis, tripo3d/h3.1/image-to-3d, fal-ai/hunyuan_world/image-to-world, fal-ai/flux-control-lora-depth, fal-ai/imageutils/marigold-depth

**World Labs**
- https://docs.worldlabs.ai/api/pricing.md
- https://marble.worldlabs.ai/pricing
- https://docs.worldlabs.ai/api/faq.md
- https://www.worldlabs.ai/terms-of-service (in effect from 21 January 2026)

**Licences, tools and assets**
- https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE
- https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanWorld-1.0/main/LICENSE
- https://sparkjs.dev/ and the npm package @sparkjsdev/spark 2.3.1 (needs three.js 0.180 or newer)
- https://developer.blender.org/docs/release_notes/5.3/
- https://developer.blender.org/docs/release_notes/5.3/rendering/
- https://developer.blender.org/docs/release_notes/5.3/eevee/
- https://raw.githubusercontent.com/Stability-AI/stable-fast-3d/main/README.md
- https://raw.githubusercontent.com/facebookresearch/sam-3d-objects/main/LICENSE
- https://raw.githubusercontent.com/apple/ml-sharp/main/LICENSE_MODEL
- https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/main/README.md
- https://polyhaven.com/license

**The Phillips machine**
- https://www.rbnz.govt.nz/-/media/project/sites/rbnz/files/publications/factsheets-and-guides/factsheet-bill-phillips-and-the-moniac.pdf (seen as a search result)
- https://en.wikipedia.org/wiki/Phillips_Machine

**Project files**
- the two reports
- `project-notes/` (project story, Decisions, Lessons)
- `film-kit/` (style rules, lessons and traps, painting prompts, `paper-film/scenes/cinema-kit.js` and chapter 2's page files)
- `chapter-2-inflation/` (script, round-20 camera guide, paintings, the finished film)
- `experiments/24 Test - 3D petrol station.jpg`
