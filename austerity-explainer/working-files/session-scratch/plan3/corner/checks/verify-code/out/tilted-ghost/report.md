# Shot check: f-tilted-ghost

4 problems found in 16 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). Boxes on marked.jpg carry the problem's number (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Yellow arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; orange, the warm light; blue, the story props; green, the subject.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (set-up). Check its name patterns in the check file against the objects' names in Blender.
Fix the camera before anything else, then check again: the places of the props on screen will all change.

## Problems

1. **set-up.** No object in the scene matches the group "ghost", so it was not measured.
   - Fix: Check its name patterns in the check file against the objects' names in Blender.
2. **rule 2: keep the camera level.** The camera is not level: tilted 3.0 degrees up and leaning 0.0 degrees to one side.
   - Fix: Tilt it 3.0 degrees down, so posts, drainpipes and chimneys stay upright.
3. **reference: where the lines meet.** Ours meet at 0.684 across, 0.485 down; the reference's at 0.706, 0.424 (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
   - Fix: Ours meet 0.06 of the frame height lower than the reference's because our camera is not level (problem 2): level it and check again.
4. **rule 12: room for phone buttons.** board reaches 1.00 across (limit 0.95); notice reaches 0.94 across (limit 0.90). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: Fix the camera first (problem 2) and check again: this may change. If it stays: Move the camera about 0.16 m to the right without turning it: near props slide left on screen more than far ones, and where the lines meet stays where it is (check rule 1 again afterwards). Or turn the camera about 1.7 degrees right: everything slides left together, but where the lines meet moves too. (The reference has the same fault: notice 0.91, chair 0.97, pail 0.96.)

## Passed

- rule 2: stand at eye height: The camera's eye is 1.81 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the ground (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.485 down; the nearest edge of board is 0.009 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels just touch (overlaps at least 14 pixels deep, gaps at least 18).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.44 of the frame wide and 0.44 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.50 across), chair's right side (0.94), notice's top (0.55 down) and pail's bottom (0.99). The rule's limit is 0.40 x 0.50, but the reference measures 0.46 x 0.44 by the same count, so its size plus 0.02 is allowed.
- rule 3: nothing hides the words: 3% of notice's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.57 down.
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.55 down.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- reference: the camera: Not compared: our camera is not level (tilt 3.0, lean 0.0 degrees; problem 2). Level it, then check again.
- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 8: work props small, far and dim: dustbins does not show in this frame.
- reference: where each prop stands: Not judged: the camera is wrong (problem 2), and the camera moves everything on screen. Fix the camera, then check again; don't move any prop yet.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
