# Shot check: k-lamp-post-touches-board

3 problems found in 14 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 2caf1916; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (rule 3: story props close together). Move drum about 0.11 m to the right.

## Problems

1. **rule 3: story props close together.** The story props (leaving out board) fill a box 0.44 of the frame wide and 0.42 tall (limit 0.40 x 0.50). Its edges: drum's left side (0.50 across), chair's right side (0.94), notice's top (0.51 down) and pail's bottom (0.93).
   - Fix: Move drum about 0.11 m to the right.
2. **rule 12: room for phone buttons.** board reaches 0.99 across (limit 0.95); notice reaches 0.93 across (limit 0.90). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: Move the camera about 0.14 m to the right without turning it: near props slide left on screen more than far ones, and where the lines meet stays where it is. Then check again: the props slide by different amounts, so their overlaps change (rule 4). Or turn the camera about 1.5 degrees right: everything slides left together, where the lines meet too.
3. **rule 4: overlap clearly or leave a clear gap.** lamp post's edge runs right along board's edge for 375 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.44 to 0.63 down, around 0.70 across; board is nearer the camera)
   - Fix: Move lamp post about 0.06 m to the right so lamp post clearly passes behind board, or move lamp post about 0.07 m to the left to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.81 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.009 of the frame width away (limit 0.03).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: nothing hides the words: 2% of notice's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.52 down.
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.50 down.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 8: work props small, far and dim: dustbins does not show in this frame.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
