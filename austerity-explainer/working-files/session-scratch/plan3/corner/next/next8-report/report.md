# Shot check: next scene, test 8

7 problems found in 33 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). Boxes on marked.jpg carry the problem's number (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Yellow arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; orange, the warm light; blue, the story props; green, the subject.

## Fix first

Problem 1 (rule 10: the quiet side keeps the frame from tipping). Add a few small dim lights or details in the left half (a lit window, a distant lamp) until it holds about 42%.

## Problems

1. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from notice) holds 33% of the weight (aim for 40 to 48%).
   - Fix: Add a few small dim lights or details in the left half (a lit window, a distant lamp) until it holds about 42%.
2. **rule 6: lit from below.** The bottom of notice is 0.09 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the picture the user liked measures about 0.17).
   - Fix: Bring the lantern or the fire's light closer below notice, or turn down the cool light from above.
3. **reference: where each prop stands.** pail: ours at 0.77 across, 0.88 down; the reference's at 0.89, 0.83; ours is 0.79 times as tall as the reference's.
   - Fix: Move pail about 0.41 m further from the camera (but chair stands there); it is 0.79 times as tall as the reference's: make it 1.26 times bigger, or move it about 0.67 m nearer to the camera (which also moves it on screen).
4. **reference: where each prop stands.** notice: ours at 0.80 across, 0.58 down; the reference's at 0.83, 0.55; ours is 0.72 times as tall as the reference's.
   - Fix: It is 0.72 times as tall as the reference's: make it 1.39 times bigger, or move board (with notice on it) about 1.38 m nearer to the camera (which also moves it on screen).
5. **reference: where each prop stands.** lamp post: ours at 0.86 across, 0.10 down; the reference's at 0.79, 0.10.
   - Fix: Move lamp post about 0.27 m to the left.
6. **reference: where each prop stands.** lantern: ours at 0.75 across, 0.70 down; the reference's at 0.81, 0.69; ours is 1.05 times as tall as the reference's.
   - Fix: Move chair (with lantern on it) about 0.14 m to the right.
7. **reference: where each prop stands.** handcart: ours at 0.18 across, 0.53 down; the reference's at 0.23, 0.53; ours is 0.83 times as tall as the reference's.
   - Fix: Move handcart about 0.41 m to the right.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.80 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.02 m in height, 0.13 m sideways, 0.1 degrees of turn and 0.7 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 62 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.684 across, 0.439 down; the reference's at 0.706, 0.424 (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the ground (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.004 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels just touch (overlaps at least 14 pixels deep, gaps at least 18).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.43 of the frame wide and 0.42 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.46 across), notice's right side (0.88), notice's top (0.51 down) and pail's bottom (0.93). The rule's limit is 0.40 x 0.50, but the reference measures 0.46 x 0.44 by the same count, so its size plus 0.02 is allowed.
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (board 0.94, drum 0.67, chair 0.88, lantern 0.78, pail 0.84, notice 0.89).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.52 down, its brightness 0.12 (it must stay under the frame's average, 0.27).
- rule 8: work props small, far and dim: sacks covers 0.2% of the frame, its middle 0.52 down, its brightness 0.11 (it must stay under the frame's average, 0.27).
- rule 8: work props small, far and dim: dustbins covers 0.1% of the frame, its middle 0.49 down, its brightness 0.19 (it must stay under the frame's average, 0.27).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 1.0% of the frame (limit 1%): brightness 0.16 against 0.33 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: notice is the biggest bright thing: Of the brightest parts (the brightest 3% of the frame), 60% lie on notice (need 40%) and 89% in the story props' box (need 75%). The largest bright patch belongs to notice.
- rule 5: notice is bright: notice is 3.12 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.24, 0.25, 0.21 (limit 0.36).
- rule 6: warm light from the people's own lights: Warm light covers 2.8% of the frame, 96% of it round the story props.
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as notice, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.68 across, 0.44 down; centre of the brightest parts 0.79 across, 0.55 down; centre of the warm light 0.70 across, 0.61 down; centre of the story props 0.72 across, 0.67 down; centre of notice 0.79 across, 0.57 down. Together they span 0.11 of the frame wide and 0.23 tall (limit 0.40 x 0.50, holding notice).
- reference: where each prop stands: drum: ours at 0.57 across, 0.73 down; the reference's at 0.59, 0.74; ours is 1.21 times as tall as the reference's.
- reference: where each prop stands: chair: ours at 0.75 across, 0.74 down; the reference's at 0.84, 0.72; ours is 1.10 times as tall as the reference's.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- reference: where each prop stands: chair: the reference has it 0.09 of the frame width further right (ours at 0.75 across, the reference's at 0.84), but matching that would push its right edge to 0.97, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: where each prop stands: pail: the reference has it 0.12 of the frame width further right (ours at 0.77 across, the reference's at 0.89), but matching that would push its right edge to 0.96, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: landmarks: These are buildings, not props: they are never moved; they only show whether the camera matches. winding wheels ours at 0.61 across, 0.23 down; the reference's at 0.62, 0.22; chimney ours at 0.47 across, 0.08 down; the reference's at 0.45, 0.12.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
