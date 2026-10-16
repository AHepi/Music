# Guide, round 20: the camera rule, filling the frame, and nothing passing through anything

This adds to `guide.md` (in this skill) (read that
first; everything in it still holds). It was written for chapter 2's painted rooms and card models (log 20);
section 1a and the margins in section 2 add the newer rules for places built in 3D and painted over (logs 29
to 34, the kit's `docs/paper-look - 07 Composing a shot.md`). Where the two disagree on a built-and-painted
set, follow the newer rules. The film is finished and the viewer has watched it on a phone.
These are the viewer's words:

> "The camera also sometimes moves around too much. It needs to stay still unless it's essential to
> land an important point. Then movement makes sense. Zoom out to make room, zoom in to narrow
> perspective or transition to the next frame when a particular object become the main focus, pan
> left or right to shift perspective, pan up to signal ideals, pan down to signal pressure. Move up
> to see the bigger picture, move down expose the minor details. 3 movements per frame, max. If you
> need more, make more frames."

> "The price tags clip other objects and the bread basket clips the conveyor belt."
> "The envelope clips the workers and the ground."
> "The coins disappear through the ground."

## 1. The camera rule (strict)

- The camera holds still. It moves only when a move lands an important point, and each move must
  mean what the viewer's grammar says:
  - **zoom in**: narrow the view onto what matters now (an object becomes the main focus)
  - **zoom out**: make room for what comes next
  - **pan left / pan right**: shift perspective (to another thing in the same place)
  - **pan up**: toward ideals (hopes, promises, "what we're told")
  - **pan down**: pressure (weight, cost, people squeezed)
  - **move up**: see the bigger picture
  - **move down**: show the small details
- **At most 3 moves per shot.** A shot runs from one cut to the next. If a page needs more, cut to a
  new shot (a hard cut on a word, or a quick dip: `look.fade` up to 1 and back over about 0.2 s each
  way), and start that shot still.
- No drifting, no handheld wobble, no slow creep through a whole page. A move should be short and
  clear (usually 0.6 to 1.5 seconds on painted-room and card-model pages; slides in built-and-painted
  sets are longer, section 1a), eased in and out, and then the camera holds.
- Sideways pans read stronger on a tall phone frame than on a wide one: keep them small.
- Changing only the focus is not a move (it is free).
- The small shakes when something heavy lands (`kit.shake`) are allowed but keep them small.

### How to write it: `kit.stillShot`

Replace every `kit.shot([...])` on your page with `kit.stillShot(start, moves, { name })`:

```js
const shot = kit.stillShot(
  { position: [0, 0.1, 0.2], target: [0, -0.5, -30], fov: 40, focus: 12 },        // where it holds
  [
    { from: T.unemployment + 0.2, to: T.unemployment + 0.8, kind: 'focus', focus: 9.0 },  // focus only: free
    { from: T.newMoney - 0.9, to: T.newMoney + 0.3, kind: 'move down', position: [0.05, -0.35, -1.2], target: [0, -1.8, -30], focus: stackPoint },
    { from: T.factories - 0.1, to: T.warWork + 0.5, kind: 'pan right', target: [0.9, -1.6, -26] },
  ],
  { name: 'the munitions hall' });
// in pose(t): return { camera: shot(t), look: {...} }
```

- Each move eases from the pose before it to the pose it names; anything it leaves out stays.
- `kind` must be one of: 'zoom in', 'zoom out', 'pan left', 'pan right', 'pan up', 'pan down',
  'move up', 'move down', 'focus'. More than 3 counted moves, moves out of order or overlapping, or an
  unknown kind stop the page from loading with a clear message. That is on purpose.
- A page with cuts has one `stillShot` per shot (give each its own `name`) and picks one by time in
  `pose(t)`, as page 8 does with its three places.
- Worked example: `paper-film/scenes/inflation-chapter-2/page-2.js` (done this round).

### 1a. In a set built in 3D and painted over: one slide, never a turn

A built-and-painted set (`projected-set.js`: the plate drawn in Blender, painted over, and the painting shone
back onto the set) allows one kind of move: a **slide**. The camera's position changes and the way it faces
never does (rule 11 of `07 Composing a shot`, logs 31 to 34):
- Where the street's lines meet depends only on which way the camera faces, so a slide keeps them on the
  subject in every frame; a turn slides them across the frame and makes the move feel wrong (clip 29).
- The plate's frame is only a little wider than the film's (the notice corner: 64.4 degrees against the
  film's 60.4), so a turn or a pan soon shows the edge of the painting.
- At most one slide per shot, from one spoken word to another, starting and stopping gently; then the
  camera holds (and the page returns `still: true`, so the stage draws the painted set once). Chapter 2's
  newcomer pages plan 0.4 to 1.5 m in 2.6 to 4.1 s; the notice corner's test clip slid 1.5 m in 8.5 s.
- Write it as one `stillShot` move whose end pose moves the position and the target together, so the
  heading stays the same: `kit.stillShot(works.cameraAt('w1', 'plate'), [{ kind: 'zoom in', from, to,
  ...works.cameraAt('w1', 'composed') }])` (`paper-film/scenes/inflation-chapter-2-newcomers/page-3.js`).
- Check: where the lines meet moves no more than 0.02 of the frame's width between the first, middle and
  last frames of the slide; look at the `weights` view at the end of the slide (blue at an edge = no
  painting there).
- Lens blur in these sets: `aperture: 4.0, maxBlur: 2` (the notice corner, the people test, the Works).

### Check it by measurement (do this before you finish)

```
cd <kit>
PAPER_FILM_PAGES=N timeout 300 node paper-film/tools/render-paper-film.mjs cinema-test-pages --camera <stills>/r20-pN-camera.json 3
python3 -I paper-film/tools/camera_audit.py <stills>/r20-pN-camera.json --timeline examples/<chapter>/timeline.json --page N --page-files paper-film/scenes/<chapter>
```

(`--timeline ... --page N` works the page's window out from the timeline and the page files, the same edges
the stage uses; `--window FROM TO` with the window from your brief still works.) It lists each shot, each
move it measured and how long the camera is still. It must end with `0 problem(s)`. It takes about 10
seconds. On a place built in 3D and painted over, add `--built-set --place-facts place-facts.json --view VIEW`:
it also checks that the camera never turns during a slide, that where the lines meet holds still, the
magnification at the nearest painted thing (about 1.29 times at most) and that the frame stays inside the
painted plate.

## 2. Fill the frame (tall 9:16 phone frame)

From research on miniature and vertical filming (No Film School on shooting miniatures; Adam Sebire's
9:16 tips; vertical-video composition guides):

- The thing she is talking about fills most of the frame's width (60 to 80%), not a small object in a
  big empty space. (On painted-room and card-model pages. In a built-and-painted set, compose by `07
  Composing a shot` instead: the story props in one touching group inside a box at most 0.40 of the
  frame wide and 0.50 tall, reaching at least 0.70 down, with where the lines meet, the brightest parts
  and the warm light on the subject; the shot checker measures it.)
- Fill the top third and the bottom third too: something in the near foreground at the bottom (soft
  with focus), the subject in the middle, a lit background (painted room, skyline, smoke, light) at
  the top. Never a big empty dark floor, table or sky.
- Keep a low, close camera rather than a high, distant one. Wider lens close in, not a long lens far away.
- Light for depth: a warm pool of light on the subject, darker edges.
- Leave room for phone buttons and titles (rule 12 of `07 Composing a shot`; logs 30 to 34). Video apps
  put their buttons down the right edge, from a little above the middle to near the bottom, and a bar
  across the top:
  - anything that must be read ends left of 0.90 across (972 px of 1080; `TEXT_RIGHT` in `graphics.js`)
    and starts right of 0.06 (65 px; `TEXT_LEFT`);
  - story props and other important things end left of 0.95 across where the buttons are, from 0.45 to
    0.95 down; only unimportant edges reach further;
  - typed words go in the top band, 0.05 to 0.22 down, with the top of every letter at least 0.06 down
    (115 px; a heading at 0.047 was flagged in round 3), over dim sky or a soft dark band (`topShade`);
  - nothing to read below 0.80 down (the bottom 380 px).
  These replace the older "140 px from the sides and top": 140 px from the right is 0.87, stricter than
  needed. `paper-film/tools/frame_check.py` still warns at 140 px; for words between 0.87 and 0.90 across
  the warning can be ignored. The shot checker (`check-shot.sh`), `calculators/frame_geometry.py boxes` and
  `calculators/plan_page_timing.py check` (for typed words, from the page events) use the 0.90 and 0.95 limits.

## 3. Nothing passes through anything (strict)

No 3D thing (cut-out, card, price tag, coin, note, model) may pass into the painted room, the floor,
or another 3D thing, at any moment, including while it moves, lands, swings or pops up.

- **Into the painting:** each painted room now has `room.clearance(object)`: how far the object stands
  in front of the painted surface behind it (world units; negative = it pokes through). While testing,
  pose the page at the moment you want to check and print it, for example inside `pose(t)`:
  `if (Math.abs(t - 15.0) < 0.02) console.warn('tag 3 clearance', room.clearance(tags[3].group).toFixed(3));`
  (warnings print in the terminal when you make stills). Aim for at least 0.05 for things standing
  on the floor and 0.15 for things in the air. Remove the test lines before you finish.
- **Standing on the floor:** the bottom of a standing thing sits ON the floor surface: use
  `room.pointAt(u, v)` for the floor point and put the bottom edge there (not below it).
- **Into each other:** `import { boxesOverlap } from '../cinema-kit.js'` gives
  `boxesOverlap(a, b)` → `{ overlap, by }` (boxes, so slightly pessimistic for slanted cards).
  Separate things in depth (z) or across, or make one smaller.
- **Falling things** (coins, notes, a dropped envelope) stop exactly on the surface they land on (the
  floor point's height, or the top of the pile) and stay above it.
- Then look at stills of the landing moments, close up (crop with Python if needed).

## 4. Testing on a shared machine

Several helpers work at the same time on 4 processors: keep still rounds to 4 to 8 stills and don't
run more than one render at a time yourself. Use new folders under `<stills>/`
named `r20-pN-a`, `r20-pN-b`, ... The contact sheet:
`python3 -I paper-film/tools/contact_sheet.py SHEET.jpg 4 FOLDER`.

## 5. What you may edit

Only your own `paper-film/scenes/<chapter>/page-N.js` (and page-N-something.js helpers).
Never edit shared files (cinema-kit.js, models.js, effects.js, graphics.js, cinema-chapter.js, the
stage, two-factories-set.js, tools), other pages, paintings or pieces. Spend no money. Do not commit.
If a shared piece is missing or broken, work around it in your page and say so in your report.
