# How a page file works

**What this is:** the reference for writing page files: where things go on screen, how big they
are, how they move, how they are timed to the narration, and recipes from the example chapter.
The template is `paper-film/scenes/new-chapter-template/page-1.js`; the ten example pages are in
`paper-film/scenes/austerity-chapter-1/`.

## A concrete example first

Page 3 of the example, the tank (from `austerity-chapter-1/page-3.js`, shortened):

```js
const tank = await kit.piece('tank', { sheet: glasgow, width: 7.2, x: 0.7, y: 3.5, z: 1.95 });
const T = { tankLands: at('tanks') + 0.02 };          // 0.02 s after the narrator starts "tanks"
kit.shake(T.tankLands, 0.13, 0.17);                   // the camera shakes as it lands
// in pose(t):
kit.place(tank, dropIn(t, T.tankLands, { fall: 0.36, height: 14, roll: 7, bounce: 0.32 }));
```

`kit.piece` stands the painted tank 1.95 units in front of the Glasgow sheet, 7.2 units wide, its
bottom edge centred at x 0.7, y 3.5. `dropIn` returns where the tank is at any moment: hidden until
0.36 s before landing, then falling from 14 units above, landing on the word, bouncing. `kit.place`
puts it there, and also folds it away before the page turns.

## The shape of a page file

```js
export const SHEETS = ['glasgow-square', 'pithead'];   // painted sheets, top first (names from the cut list)
export async function build(kit) {
  // 1. make the pieces      2. work out the times from words      3. return pose(t)
  return { pose, turns: [/* only for a page with more than one sheet, or a special last turn */] };
}
```
`pose(t)` is called for every frame while the page is showing; it calls `kit.place(piece, pose)` for
every piece. It must depend only on `t` (no memory of earlier frames), so any frame can be drawn on
its own and pages can be filmed separately.

## Where things go

- The frame shows about **9 units wide and 16 tall** of the sheet: x from -4.5 (left) to 4.5 (right),
  y from 0 (bottom) to 16 (top). The camera looks at y 8.
- `x, y` place the **middle of a piece's bottom edge** (its hinge). `y` can be below 0 to let a crowd
  run off the bottom of the frame.
- `z` is how far a piece stands **in front of its sheet**. Words: 0.55. Pieces: about 0.6 to 3.
  Further forward looks bigger (by 26 / (26 - z)), casts a longer shadow, and covers what is behind.
- **Keep edges inside the frame**: a piece's edge should stay within about 4.1 units of the middle,
  less for pieces further forward (roughly 4.3 - 0.17 x z). Chapter 1 had to pull several pieces in.
- `yaw` (radians, use `degrees(6)`) turns a piece slightly, like a card set at an angle.
- Sizes used in chapter 1: crowds 9.4 to 11.2 wide; a speaker at a lectern 7.6; a row of six seated
  delegates 9.2; objects 1.5 to 3.6; words `size: 1` (letters about a unit tall; a one-line word is
  about 1.35 tall, a two-line word about 2.5).

## Making pieces

| Call | Makes |
|---|---|
| `kit.piece(name, { sheet, width, x, y, z, yaw })` | a painted cut-out from the chapter's `pieces.json` |
| `kit.word(lines, { sheet, size, x, y, z })` | plain words cut from off-white card (`['WHY NOT', 'FOR PEOPLE?']` for two lines) |
| `kit.card(lines, { sheet, look, width, x, y, z })` | a printed card, sign or poster in dark ink; `look` sets `cardColour`, `inkColour`, `borderColour`, `minWidth` and `aspect` (same `minWidth` and `aspect` give same-size cards); no lines gives a plain board |
| `kit.speaker(name, { sheet, width, x, y, z, jawDropShare })` | a speaking figure from the cut list's `jaw` setting: returns `{ piece, setOpen(0 to 1) }` |
| `kit.effect(new DustBurst({ count, seed }))` | dust that bursts where something lands; `.set({ origin, width, age })` |
| `kit.effect(new Smoke({ count, life, seed }))` | smoke from a chimney; `.set({ t, origin, from, until, scale })` |
| `loadMouthTrack(url)` | a function of time giving how open a jaw is (from `make_mouth_track.py`) |

`sheet` defaults to the page's first sheet. The same painting can be used by several pieces (two
pay packets of different sizes); each picture file is loaded once.

## Timing from the narration

- `kit.at('word')`: when the narrator starts the word (seconds in the chapter); `kit.at('word', 2)`:
  its second time on this page. `kit.end('word')`: when it finishes. Words are matched without
  capitals or punctuation; keep apostrophes (`at("owners'")`).
- Pop-ups start about 0.1 s **before** their word; things that land, land about 0.03 s **after** their
  word starts; a word hook pops about 0.05 s before its word.
- Collect the times in one `T` object at the top of `build`, then use them in `pose(t)`.
- `kit.firstWordAt` and `kit.lastWordEnd` give the page's first and last spoken moments.

## Motions (all in `paper-kit.js`)

A pose is `{ visible, fold, dx, dy, roll, lift }`: `fold` 0 is standing, `Math.PI / 2` lies flat
toward the camera (seen edge-on, it disappears); negative leans back. `dx`, `dy` move it on the sheet;
`roll` turns it in the sheet's plane (radians); `lift` moves it toward the camera.

| Motion | What it does |
|---|---|
| `popUp(t, start, piece, { stiffness, damping })` | folds up from flat at `start` with a small settle (stiffer = faster, a door slam used 26 and 0.5) |
| `foldDown(t, start, duration)` | folds down to flat, speeding up, then hides |
| `popUpUntil(t, start, stop, piece)` | pops up at `start`, folds away at `stop` |
| `dropIn(t, landAt, { fall, height, roll, bounce })` | falls from above and lands at `landAt` with a bounce |
| `slideIn(t, start, { from, stiffness, damping, tilt })` | slides in from the side (`from` -12 = from the left) |
| `hop(t, at, height)` | a small jump (add to `dy`) |
| `walkBob(t, from, to, height, steps)` | a paper figure's walking bob while it slides (add to `dy`) |
| `rock(t, from, to, amount, rate)` | rocks side to side (use as `roll`) |
| `knock(age, amount, rate, decay)` | a fading jolt after an impact (add to `fold` or `roll`) |
| `slapFlat(t, start)` | slapped down and left lying flat; only high in the frame (low down its paper back shows as pale blobs) |
| `addFold(pose, extra)` | adds a tilt (a jolt or lean) to a pose that is showing |
| `spring`, `easeIn`, `easeOut`, `easeInOut`, `clamp01`, `degrees` | building blocks for your own motions |

## Page turns and putting pieces away

- The page's last sheet turns by itself 0.3 s after the page's last word (0.8 s long). Every piece on a
  sheet folds down flat just before its sheet turns, front pieces first, so nothing stands on a
  turning page. You don't need to code this; `kit.place` does it.
- A page with two sheets turns its first sheet part-way through. Return
  `turns: [{ sheet: kit.sheets[0], from: kit.end('money', 3) + 0.14, length: 0.75 }]` (example page 8).
- A special last turn (example page 10): a `curve(t)` function giving the turn from 0 to 1, with `from`
  set to when the full turn begins; the corner lift on "That's next." is a turn of 0.34 held still.
  A final plain dark sheet is `'blank'` in `SHEETS`, with `{ sheet: kit.sheets[1], from: Infinity, length: 1 }`.
- Dust and smoke are not folded away; stop them yourself when the page starts to turn:
  `age: t >= kit.foldAwayAt.get(kit.sheets[0]) ? 9 : t - T.landed`.
- `kit.shake(time, amount, decay)` adds a camera shake: 0.13 for a tank, 0.06 to 0.1 for a big crash,
  0.03 for a card slapped down.

## Recipes from the example chapter

| Effect | Page | How |
|---|---|---|
| A crowd doubles | 3 | a second, bigger crowd pops up in front of the first |
| Cheering | 3, 4 | a bob (`dy`) and a small `roll` that rise and fall over the cheering words |
| A tank crashes into a crowd | 3 | `dropIn`, shake, dust, the crowd jolts (`knock`), a word knocked flat |
| A figure speaks the quote | 1, 3 | `kit.speaker` + `loadMouthTrack`; jaw drop 0.018 to 0.022 of the piece's height |
| A silent mechanical mouth flap | 10 | `setOpen(0.85 * max(0, sin(...)))` for three quick opens |
| A weight squashes a pay packet | 1 | the weight lands on the packet's top; the packet slaps flat; the weight sinks to the floor |
| An official stamp hits each thing as it is named | 2 | one stamp, falling and lifting between positions (`stampPose`) |
| Shells made, then running out | 2 | a row pops up one by one, then folds away one by one faster |
| Workers march off into a factory | 4 | slide right and up while folding down |
| A red flag rises behind a roof | 4 | the flag stands behind the factory (smaller `z`) and springs up from below |
| Words wobble and topple | 5 | growing `roll`, then fold flat speeding up |
| A door slams in someone's face | 6 | a taller door pops up (stiff spring) in front of the walking worker; shake |
| Cards slapped down, each replacing the last | 6 | `dropIn` for each card; the one before folds down at the same moment |
| Three parts on three boards | 7 | dark plain cards as boards, a word on each, objects standing on them |
| A factory stops smoking | 7 | `Smoke` with `until` set to the word "down" |
| A shrinking pay packet / a growing price tag | 7, 10 | swap for a smaller or bigger copy of the same painting |
| A SOLD sign / a TAX tag dropped on | 7 | small `dropIn` onto the object, a little in front of it |
| Gold slams down on wages and prices | 8 | lift (`dy`, `lift`), then fall onto them; they fold away under it |
| Posters slapped onto a wall | 9 | start close to the camera (`lift` 6) and fly back onto the wall |
| A teasing corner lift, then the end | 10 | the special last turn and a `'blank'` sheet |

## Checking and speed

- `node paper-film/tools/render-paper-film.mjs <chapter> folder --stills t1 t2 ...` draws single
  moments (about a second each). Look at full size; small sheets hide faults.
- If the scene fails to load, the tool prints the reason (a missing piece name, a word not on the page).
- Filming runs about 0.6 to 0.9 seconds a frame. Large textures slow loading: big pieces up to 2048
  pixels, small objects about 1024.

## Traps

- A word spoken twice on a page must be asked for by its number (`at('get', 2)`), or the picture lands
  on the first one. Chapter 1 caught three of these before filming.
- `pose(t)` must not remember earlier frames; pages are filmed separately and stills are drawn out of order.
- Dust and smoke made without `kit.effect` stay on screen after their page has gone.
- A piece left lying flat low in the frame shows its paper back as pale shapes; fold it away instead.
- A piece that should hide another must be bigger on screen (taller and nearer); check the edges.
- A spring with `damping` of exactly 1 has its own formula; keep custom motions free of divisions by zero.
