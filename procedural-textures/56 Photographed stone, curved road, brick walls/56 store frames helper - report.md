# 56 Store helper for the timber door and window frames - report

What this file is: the report, word for word, of the helper that gave the house-front tool timber frames round its doors and windows, at the owner's word (decision 81), and lit windows (5 November 2026, 18:44 to 19:17). Saved by the session.

---

**The window and door framing on lay_stone is now painted wood. It is in the plugin and all its tests pass (19:17).**

**What I made**
- There is a new option, `frames`. It is set to 'wood' unless you say otherwise, so every house front the tool builds now gets timber frames. Each window and door gets:
  - a moulded casing up both sides: about 8 cm wide on windows and 11 cm on doors. The stone jambs were 10.5 to 14.5 cm on windows and 22 cm on doors, so these are much slimmer.
  - a head butted across the top, with a small drip cap along it.
  - under each window, a timber sill with a sloped top, a nose and a small drip groove. The dark drip line is gone.
  - for a door, the same casing and head, standing on plinth blocks at the foot.
- The frames stand 1 to 2 cm in front of the stones. The stones stop against them with a tight 4 mm joint: no gap, and no stone behind or through them.
- Each piece leans a little out of true and is worn at its edges, more in some places than others.
- If a strip of stone above a head or below a sill would be too thin to look right, the head gets deeper, or the sill gets a board under it, instead.
- The sashes and panelled doors are unchanged.
- To use it: `lay_stone.lay(wall, openings=[...], seed=2)` gives the wood frames.
- `frames='stone'` gives the old stone surrounds. I checked these are exactly the same as before: identical points in six different walls, and the new test file checks it again every time.
- The frames' material is a new option, `frame_material`. I chose `SURFACE • distressed_painted_planks`: blue-grey paint worn to the wood.
  - I tested it on the frames against the dark door paint and the grey old planks. Seen from about 9 m away, the dark door paint melted into the dark sashes, while the blue-grey reads clearly as painted frames and suits the dark doors.
  - Each piece shows its own part of the photograph.
  - The heads and sills use turned copies of the material, so the grain runs along every piece, never across it.
- I updated the tool's notes at the top, its TOOL text, its `--help` (new `--frames`, `--frame-material` and `--lit`) and its trap. The trap now warns that the frames take about 8 to 11 cm beside each opening and stand up to 31 cm out from the wall.
- **Lit windows (the session asked for this partway through):** a new option, `lit`.
  - `lit=[1, 3]` lights the openings at those places in your list (0 is the first). `lit=0.3` lights that share of the windows, picked by the seed.
  - The lit glass is `GLASS • warm occupied interiors` or `GLASS • dim amber rooms`, picked by the seed.
  - A door, or a number that isn't a window, is refused with an explanation.
  - The glow lights nothing around it, so you still need a small warm light just outside the glass; the tool's text says so.

**Tests:** the four test files pass when run on the plugin's copy: `test_store_tools`, `test_store_street_fronts`, `test_store_wall` and my new `test_store_frames`. The new file checks:
- casings on both sides and a head on every opening, a sill under every window, plinth blocks under door casings
- no overlap with any stone or the sash, everything in front of the stones
- the stones stopping at the frames in every row
- the grain running along each piece
- wrong `frames` values refused, the same seed giving the same frames, and lit windows

**What does not read well yet**
- Close up, the paint photograph shows patches of bare orange wood on some faces. It reads as worn paint; from a distance the frames read blue-grey.
- On a wall turned about 45 degrees to the scene, the grain on heads and sills may run at a slant on some faces.
- The door's edges and the window glass tuck 1 cm into the frame, as they did into the stone. It can't be seen, but it is there.
- Where a head or sill grows to avoid a thin strip of stone, it can be up to 7 cm deeper than on other floors.
- Store.md still describes stone surrounds: **the session needs to run `catalogue.py`**. Until then, the catalogue check in `test_store_rules` will fail. Its code check found nothing wrong.
- The worked example script calls lay_stone without naming `frames`, so it will now get wood frames. It lights its window by hand, which I did not re-check; it could use `lit=` instead.

**Mistakes I made and fixed**
- Stones next to a frame were dropped when shorter than 12 cm, leaving gaps. Now a stone either runs on to the frame or stops at it.
- Random wear set separately at each point along a piece made it look striped. I made the wear change smoothly along each piece.
- My first turned copy fixed the grain on a sill's front but put it across the sill's top. I replaced it with two copies that turn only the faces that need it.
- A stray apostrophe broke my scratch copy for a few seconds. I fixed it.
- One line would have broken `frames='stone'`; my before-and-after comparison caught it.
- A tiny 1.5 mm sag in the head touched the sash in the overlap check, so I removed it.
- My test first counted stones from the next side round the corner. It now counts only that side's own stones.

**Files**
- Changed: `/home/claude/music/plugins/painted-place/brief/store/tools/lay_stone.py` (replaced in one move at 19:15, after the session gave the go-ahead)
- New: `/home/claude/music/plugins/painted-place/tests/test_store_frames.py`
- Redrawn: `/home/claude/music/plugins/painted-place/brief/store/cards/tools/lay_stone.png` (with `cards.py` after the swap; I looked at it full size and close on the window and door)
- Scratch folder `/home/claude/store-work/pbr56/frames/`: `notes.md`, `lay_stone_original.py` (the old tool), `card_old.png` (the old card), `compare_stone.py` (the before-and-after proof) and the look pictures t1 to t9.

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 56.
