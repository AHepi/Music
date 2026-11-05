# 55 Store helper for the shop and windows - report

What this file is: the report, word for word, of the helper that made seven new parts for the store from what the three street builders made by hand (5 November 2026). Saved by the session.

---

I've added all seven parts to the store, and the full parts test passes: 48 parts, including the other helpers' new ones. Each of my parts has its four cards, which I looked at myself, and a saved part file. I did not touch Store.md, the tests, the tools or other helpers' files, and I did not run catalogue.py.

**The parts** (sizes at the default options; I tried every option at least once):

1. **shop_front**, 4.94 x 2.08 x 3.53 m. Options: `width` (4.8), `lit` (True), `door` ('right' or 'left').
   - The builders' version was flat boxes with the goods stuck on a glowing plane.
   - Now it has pilasters, scroll consoles, a blank fascia, a stepped cornice with lead on top, a panelled stall riser, mullions and a transom with small top panes, and a half-glazed door set back in a tiled lobby with a fanlight and a stone step.
   - Behind real glass there is a real shop: tins stacked in the window, a counter with brass scales, a gas globe, and shelves of jars and tins against a glowing back wall. A hidden 45 W light inside spills out onto the pavement.
   - The inside goes 1.6 m back into the building. The part brings a hidden box, 'shop_front opening', that a builder can use to cut the wall away behind it. That is its trap.
2. **dormer**, 1.44 x 2.63 x 2.06 m. Options: `lit` (True), `pitch` of the main roof (36).
   - The builders' version was a stone box with a glass plane.
   - Now the cheeks and front are hung with slates, there is a two-over-two sash window, its own gabled slate roof with barge boards and a finial, and lead where it meets the roof: an apron, stepped flashings, valleys and a ridge roll.
   - Its origin is on the roof surface under the middle of its front. The apron reaches 0.15 m lower down the slope, so the card gives `foot_z` -0.15.
3. **window_dressing**, 0.92 x 0.06 x 1.61 m. Options: `kind` ('blind', 'nets', 'curtains', 'blind and nets'), `width` (0.96), `height` (1.62), `drawn` (0.5), `side` ('right', 'left', 'both'), `lit` (False).
   - Hanging cloth in real folds. The blind has a roller, a lath in the hem, and a cord down to a brass pulley at the sill. The nets are see-through lace on a wire. The curtains hang from a pole with rings. When lit, the cloth glows warm.
   - Trap: the store's window glass is opaque, so this part goes 2 mm in front of it, as the builders did.
4. **boarded_window**, 1.27 x 0.23 x 1.63 m. Options: `width`, `height`, `boards` (4), `corner` (True).
   - A full sash window set 6 cm back in its opening, the lower panes broken with shards left in the corners and the dark stair behind.
   - Each board is its own sawn timber with its own shade, with rusty nail heads and rust run under them, plus one board across the cracked pane above.
5. **window_box**, 1.10 x 0.31 x 0.53 m. Options: `length` (1.06), `pots` (4), `flowers` (1.0).
   - A box of grey boards on wedges, clay pots with earth, and geraniums with round scalloped leaves showing the dark ring, under heads of small red flowers (a few gone brown).
6. **sign_board**, 0.12 x 1.14 x 1.28 m. Options: `width` (0.9), `paint` ('cream', 'green', 'red', 'black').
   - A blank framed board in two faded, peeling paints, on S-hooks from a forged bracket with a curl and a scroll, and rust run down the wall under it.
   - Its origin is the foot of the wall under the sign, as with teapot_sign; `foot_z` is 1.80.
7. **stair_door**, 1.35 x 0.55 x 2.97 m. Options: `width` (1.0), `lit` (True).
   - A panelled door with two glazed upper panels lit from the stair, brass knob and plates, a door case with a lit fanlight, and a hollow-worn step whitened at its edge.
   - It has its own 25 W light 0.3 m outside the glass, which lights the step. The trap says to turn it up or down, never take it away.

**What does not read well yet**
- Drawn alone, the dormer has no roof under it, so its cards show its open underside and back.
- The window_dressing cards show only the default blind. I checked the nets and the lit curtains in small test pictures, not on the store's cards.
- On the boarded window, the broken panes are mostly hidden behind the boards, and the crack in the upper pane is not drawn.
- The shop's lit back wall goes pale cream at the top.
- The store's dark paint looks olive under the card lights. That is the store's own material, which I left unchanged.
- Red geraniums will go near-black at dusk unless a light reaches them; that is in their trap.

**Mistakes I made and fixed**
- **Black squares wherever timbers crossed**, in the shop front, dormer, boarded window and stair door. Two members had faces in exactly the same plane, which the renderer draws as black. I made the crossing members a few millimetres shallower and redrew the cards. This could go in the Lessons file, and perhaps in the plugin's traps.
- **The shop's glowing back wall showed through its back.** I closed the shell behind it.
- **My first dormer would have failed the test's centring check**, which my own checker did not have at first; I added it. I moved the dormer's origin onto the roof under its front and lowered the eaves 14 cm to keep its proportions.
- **The dormer's light was too strong.** I cut it from 12 W to 4 W. One of my edit scripts also stopped before writing, so the first redraw used the old file; I caught it and redid it.
- **The geranium leaves first read as pale paper discs on spindly stalks.** I made them darker, without the sheen, more of them, bigger and lower.
- **The sign's `paint` option text could not be read by the test.** I reworded it, and removed a stray apostrophe from the shop's `door` text that the test would have taken as a quote mark.
- **The sign's peeling showed only as flecks.** I made the patches bigger.
- I also caught and fixed some small slips before the first builds: a zero-thickness panel, floating display stands, and a tapering block used as a door panel.

**Files I created** (in /home/claude/music/plugins/painted-place/brief/store/):
- `parts/src/_shapes_street_shop.py` (my shared helper module)
- `parts/src/shop_front.py`, `dormer.py`, `window_dressing.py`, `boarded_window.py`, `window_box.py`, `sign_board.py`, `stair_door.py`
- `parts/<each name>.blend` (7 part files)
- `cards/parts/<each name> - three.png`, `- close.png`, `- side.png`, `- back.png` (28 cards)

Outside the plugin, in /home/claude/store-work/street55/: my checker script (`scripts/check_part.py`), the pictures I looked at (`look/`), and the test logs (`test_parts.log`, `test_parts2.log`).

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 55: the store's tests, and the cards it looked at.
