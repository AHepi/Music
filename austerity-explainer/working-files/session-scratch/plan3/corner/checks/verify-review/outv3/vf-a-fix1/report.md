# Shot check: a-fix1

6 problems found in 20 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version d911c430; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (reference: how far the camera stands). Move the camera about 1.11 m toward the props (up the street), without turning it, then check again.
Fix the camera before anything else, then check again: the places of the props on screen will all change.

## Problems

1. **reference: how far the camera stands.** Most props look 0.76 times as tall as in the reference (notice 0.58, drum 0.90, chair 0.80, lantern 0.77, pail 0.75, handcart 0.75): the camera stands too far from them, not the props in the wrong places.
   - Fix: Move the camera about 1.11 m toward the props (up the street), without turning it, then check again.
2. **rule 4: overlap clearly or leave a clear gap.** notice and lantern almost touch: 2 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.76 across, 0.60 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.33 m further from the camera so it clearly overlaps notice, or move chair (with lantern on it) about 0.28 m nearer to the camera (but pail stands there) to leave a clear gap.
3. **rule 4: overlap clearly or leave a clear gap.** chair's edge runs right along pail's edge for 40 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.73 to 0.74 down, around 0.85 across; pail is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair about 0.05 m to the left so chair clearly passes behind pail, or move chair about 0.06 m to the right to leave a clear gap.
4. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps board: it reaches 12 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.77 across, 0.63 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.08 m further from the camera so it clearly overlaps board, or move chair (with lantern on it) about 0.42 m nearer to the camera (but pail stands there) to leave a clear gap.
5. **rule 3: nothing hides the words.** 7% of notice's words are hidden behind chair (only its bottom fifth, the signature, may be covered). (the hidden part is around 0.82 across, 0.58 down)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair about 0.49 m to the right so it no longer hides notice's words. Or move chair about 1.27 m further from the camera, behind board.
6. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps lamp post: it reaches 7 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.78 across, 0.66 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.02 m to the right and about 0.11 m nearer to the camera (but pail stands there) so it clearly overlaps lamp post, or move chair (with lantern on it) about 0.04 m to the left and about 0.30 m further from the camera to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.81 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.00 m in height, 0.00 m sideways, 0.0 degrees of turn and 0.4 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 63 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.686 across, 0.439 down; the reference's at 0.706, 0.424: 0.020 of the frame width and 0.015 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.686 across, 0.439 down; the nearest edge of board is 0.008 of the frame width away (limit 0.03).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.34 of the frame wide and 0.30 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.54 across), notice's right side (0.88), notice's top (0.49 down) and pail's bottom (0.79). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.44, so up to 0.48 by 0.50 is allowed.)
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (board 0.93, drum 0.71, chair 0.88, lantern 0.79, pail 0.85, notice 0.88).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.5% of the frame, its middle 0.52 down.
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.50 down.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 8: work props small, far and dim: dustbins does not show in this frame.
- reference: where each prop stands: Not judged: the camera is wrong (problem 1), and the camera moves everything on screen. Fix the camera, then check again; don't move any prop yet.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
