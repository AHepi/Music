# Shot check: box world

9 problems found in 26 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (rule 3: story props in the frame). Move notice out from behind board, or in front of it.

## Problems

1. **rule 3: story props in the frame.** notice is in the frame but hidden behind board.
   - Fix: Move notice out from behind board, or in front of it.
2. **rule 8: nothing big where the eye enters.** handcart fills 2.2% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move handcart about 3.25 m nearer to the camera (its middle then about 0.60 down, out of the corner and just inside the middle band, rule 8).
3. **rule 8: nothing big where the eye enters.** drum fills 1.5% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move drum out of the bottom-left quarter.
4. **rule 12: room for phone buttons.** board reaches 0.96 across (limit 0.95); (the reference has the same fault: notice 0.91, chair 0.97, pail 0.96). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: For board: move the camera about 0.05 m to the right without turning it. Near props slide left on screen more than far ones, and where the lines meet stays where it is. Then check again: the props slide by different amounts, so their overlaps change (rule 4). Don't turn the camera instead: that would move where the lines meet away from the reference's.
5. **rule 8: work props small, far and dim.** handcart covers 2.2% of the frame, its middle 0.55 down. It covers 2.2% of the frame (limit 2%).
   - Fix: Keep handcart where it is but in shadow.
6. **reference: where each prop stands.** lamp post: ours at 0.87 across, 0.08 down; the reference's at 0.79, 0.10.
   - Fix: Move lamp post about 0.28 m to the left.
7. **reference: where each prop stands.** lantern: ours at 0.76 across, 0.70 down; the reference's at 0.81, 0.69; ours is 1.14 times as wide and 1.13 times as tall as the reference's.
   - Fix: Move chair (with lantern on it) about 0.12 m to the right.
8. **reference: where each prop stands.** pail: ours at 0.77 across, 0.88 down; the reference's at 0.89, 0.83; ours is 1.40 times as wide and 0.94 times as tall as the reference's.
   - Fix: Move pail about 0.40 m further from the camera (but chair stands there).
9. **reference: where each prop stands.** drum: ours at 0.57 across, 0.74 down; the reference's at 0.59, 0.74; ours is 1.57 times as wide and 1.27 times as tall as the reference's.
   - Fix: Make it 0.79 times smaller, or move it about 1.10 m further from the camera (which also moves it on screen).

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.80 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.02 m in height, 0.13 m sideways, 0.1 degrees of turn and 0.7 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 62 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.684 across, 0.439 down; the reference's at 0.706, 0.424: 0.022 of the frame width and 0.015 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- reference: how far the camera stands: The props are about the reference's size (middle of 6: 1.10 times).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.003 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels, handcart, sacks, dustbins just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 3: story props together in the street: drum, chair, pail stand in front of board and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.46 of the frame wide and 0.33 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.43 across), chair's right side (0.89), chair's top (0.61 down) and pail's bottom (0.94). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.29, so up to 0.48 by 0.50 is allowed.)
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: sacks covers 0.2% of the frame, its middle 0.52 down.
- rule 8: work props small, far and dim: dustbins covers 0.2% of the frame, its middle 0.49 down.
- reference: where each prop stands: chair: ours at 0.75 across, 0.74 down; the reference's at 0.84, 0.72; ours is 1.07 times as wide and 1.13 times as tall as the reference's.
- reference: where each prop stands: handcart: ours at 0.21 across, 0.55 down; the reference's at 0.23, 0.53; ours is 1.07 times as wide and 1.07 times as tall as the reference's.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- reference: where each prop stands: notice: compare with the reference again after problem 1.
- reference: where each prop stands: chair: the reference has it 0.09 of the frame width further right (ours at 0.75 across, the reference's at 0.84), but matching that would push its right edge to 0.98, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: where each prop stands: pail: the reference has it 0.12 of the frame width further right (ours at 0.77 across, the reference's at 0.89), but matching that would push its right edge to 0.99, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: landmarks: These are buildings, not props: they are never moved; they only show whether the camera matches. winding wheels ours at 0.61 across, 0.23 down; the reference's at 0.62, 0.22; chimney ours at 0.47 across, 0.07 down; the reference's at 0.45, 0.12.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
