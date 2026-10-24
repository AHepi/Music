# Shot check: a-camera-too-high

9 problems found in 21 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version d911c430; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (reference: the camera). Lower the camera about 0.42 m; move it about 0.29 m to the left (across the street); turn it about 1.0 degrees left.
Fix the camera before anything else, then check again: the places of the props on screen will all change.

## Problems

1. **reference: the camera.** The camera that best matches the reference (at our distance up the street) is 1.80 m above the pavement, 2.96 m right of the street's middle line, turned 6.9 degrees left of straight up the street, seeing 60.4 degrees top to bottom; ours is 2.22 m above the pavement, 3.25 m right of the street's middle line, turned 5.9 degrees left of straight up the street, seeing 60.0 degrees top to bottom. Ours misses the reference's landmarks by up to 85 pixels (left roofline); the best camera by up to 63. (landmarks missed by ours, in pixels: left wheel hub 59, right wheel hub 61, chimney top 57, gate bottom left 39, gate top left 37, left roofline 85, left kerb 20, right kerb 29)
   - Fix: Lower the camera about 0.42 m; move it about 0.29 m to the left (across the street); turn it about 1.0 degrees left.
2. **rule 2: stand at eye height.** The camera's eye is 2.22 m above the pavement under it (a standing person: 1.50 to 1.90 m).
   - Fix: The camera fix in problem 1 covers this: it puts the camera's eye 1.80 m above the pavement. Check again after it.
3. **props rest where they should.** dustbins is sunk 0.03 m into the pavement or road (at Blender x -3.60, y 27.20).
   - Fix: Raise dustbins by 0.03 m so it stands on top.
4. **rule 4: overlap clearly or leave a clear gap.** board's edge runs right along drum's edge for 147 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.66 to 0.73 down, around 0.60 across; drum is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move drum about 0.06 m to the right so board clearly passes behind drum, or move drum about 0.07 m to the left to leave a clear gap.
5. **rule 1: aim the street at the story.** The street's lines meet at 0.659 across, 0.439 down; the nearest edge of board is 0.090 of the frame width away (limit 0.03): 40 pixels to the left and 89 pixels below. (board spans 0.58 to 0.84 across, 0.48 to 0.75 down)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Turning the camera won't help: it moves where the lines meet and the props together. Lower the camera about 0.33 m (board then rises on screen while where the lines meet stays put); and move the camera about 0.15 m to the left, or move board about 0.15 m to the right.
6. **rule 4: overlap clearly or leave a clear gap.** board and lantern almost touch: 9 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.63 across, 0.71 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.08 m to the left so it clearly overlaps board, or move chair (with lantern on it) about 0.04 m to the right to leave a clear gap.
7. **rule 4: overlap clearly or leave a clear gap.** lamp post and winding wheels almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.67 across, 0.26 down; lamp post is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move lamp post about 0.07 m to the left so it clearly overlaps winding wheels, or move lamp post about 0.08 m to the right to leave a clear gap.
8. **rule 4: overlap clearly or leave a clear gap.** lantern and lamp post almost touch: 13 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.68 across, 0.72 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.09 m to the right so it clearly overlaps lamp post, or move chair (with lantern on it) about 0.02 m to the left to leave a clear gap.
9. **reference: where the lines meet.** Ours meet at 0.659 across, 0.439 down; the reference's at 0.706, 0.424: 0.047 of the frame width and 0.015 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
   - Fix: This follows from the camera: the fix in problem 1 moves where the lines meet too. Check again after it.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- reference: how far the camera stands: The props are about the reference's size (middle of 6: 0.77 times).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.35 of the frame wide and 0.32 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.44 across), notice's right side (0.78), notice's top (0.55 down) and pail's bottom (0.87). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.44, so up to 0.48 by 0.50 is allowed.)
- rule 3: nothing hides the words: 1% of notice's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (board 0.82, drum 0.60, chair 0.76, lantern 0.67, pail 0.72, notice 0.78).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.5% of the frame, its middle 0.54 down.
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.52 down.
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
