# Shot check: composed-end

6 problems found in 30 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). Boxes on marked.jpg carry the problem's number (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Yellow arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; orange, the warm light; blue, the story props; green, the subject.

## Fix first

Problem 1 (rule 6: lit from below). Bring the lantern or the fire's light closer below notice, or turn down the cool light from above.

## Problems

1. **rule 6: lit from below.** The bottom of notice is 0.02 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the picture the user liked measures about 0.17).
   - Fix: Bring the lantern or the fire's light closer below notice, or turn down the cool light from above.
2. **rule 6: warm light from the people's own lights.** Warm light covers 7.6% of the frame, 2.5 times the most allowed (3%). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: 27% of the warm light is away from the story props; the largest patch is on the ground and walls at 0.20 across, 0.76 down (marked). The warm lights lighting it most: brazier_light (1.8 m from it, in the frame; about 90% of the warm light reaching it if nothing shades it); lantern_light (2.1 m from it, in the frame; about 4% of the warm light reaching it if nothing shades it). Shorten their reach (lower their strength or the distance their light travels) first.
3. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from notice) holds 32% of the weight (aim for 40 to 48%).
   - Fix: Add a few small dim lights or details in the left half (a lit window, a distant lamp) until it holds about 42%.
4. **rule 12: room for phone buttons.** board reaches 0.99 across (limit 0.95); notice reaches 0.93 across (limit 0.90). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: Move the camera about 0.14 m to the right without turning it: near props slide left on screen more than far ones, and where the lines meet stays where it is (check rule 1 again afterwards). Or turn the camera about 1.5 degrees right: everything slides left together, but where the lines meet moves too. (The reference has the same fault: notice 0.91, chair 0.97, pail 0.96.)
5. **reference: where each prop stands.** notice: ours at 0.84 across, 0.58 down; the reference's at 0.83, 0.55; ours is 0.72 times as tall as the reference's.
   - Fix: It is 0.72 times as tall as the reference's: make it 1.39 times bigger, or move board (with notice on it) about 1.36 m nearer to the camera (which also moves it on screen).
6. **reference: where each prop stands.** lamp post: ours at 0.84 across, 0.10 down; the reference's at 0.79, 0.10.
   - Fix: Move lamp post about 0.19 m to the left.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.81 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.02 m in height, 0.01 m sideways, 0.1 degrees of turn and 0.7 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 62 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.684 across, 0.439 down; the reference's at 0.706, 0.424 (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the ground (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.009 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels just touch (overlaps at least 14 pixels deep, gaps at least 18).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.44 of the frame wide and 0.42 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.50 across), chair's right side (0.94), notice's top (0.51 down) and pail's bottom (0.93). The rule's limit is 0.40 x 0.50, but the reference measures 0.46 x 0.44 by the same count, so its size plus 0.02 is allowed.
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.52 down, its brightness 0.14 (it must stay under the frame's average, 0.31).
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.50 down, its brightness 0.10 (it must stay under the frame's average, 0.31).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.6% of the frame (limit 1%): brightness 0.15 against 0.36 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: notice is the biggest bright thing: Of the brightest parts (the brightest 3% of the frame), 60% lie on notice (need 40%) and 93% in the story props' box (need 75%). The largest bright patch belongs to notice.
- rule 5: notice is bright: notice is 3.06 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.22, 0.25, 0.24 (limit 0.36).
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as notice, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.68 across, 0.44 down; centre of the brightest parts 0.81 across, 0.57 down; centre of the warm light 0.71 across, 0.72 down; centre of the story props 0.77 across, 0.67 down; centre of notice 0.84 across, 0.57 down. Together they span 0.15 of the frame wide and 0.28 tall (limit 0.40 x 0.50, holding notice).
- reference: where each prop stands: drum: ours at 0.61 across, 0.73 down; the reference's at 0.59, 0.74; ours is 1.21 times as tall as the reference's.
- reference: where each prop stands: chair: ours at 0.80 across, 0.74 down; the reference's at 0.84, 0.72; ours is 1.11 times as tall as the reference's.
- reference: where each prop stands: lantern: ours at 0.79 across, 0.70 down; the reference's at 0.81, 0.69; ours is 1.03 times as tall as the reference's.
- reference: where each prop stands: pail: ours at 0.84 across, 0.86 down; the reference's at 0.89, 0.83; ours is 1.08 times as tall as the reference's.
- reference: where each prop stands: handcart: ours at 0.19 across, 0.53 down; the reference's at 0.23, 0.53; ours is 0.83 times as tall as the reference's.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 8: work props small, far and dim: dustbins does not show in this frame.
- reference: where each prop stands: pail: the reference has it 0.06 of the frame width further right (ours at 0.84 across, the reference's at 0.89), but matching that would push its right edge to 0.96, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: landmarks: These are buildings, not props: they are never moved; they only show whether the camera matches. winding wheels ours at 0.62 across, 0.23 down; the reference's at 0.62, 0.22; chimney ours at 0.47 across, 0.08 down; the reference's at 0.45, 0.12.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
