# Shot check: m3-c-chair-pushed-back

5 problems found in 24 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 2408e9f8; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move chair about 0.05 m to the left (across the street) and about 0.52 m down the street, toward the camera so it is back under lantern; or move lantern about 0.05 m to the right (across the street) and about 0.52 m up the street, away from the camera so it is over the middle of chair.

## Problems

1. **props rest where they should.** lantern should rest on chair, but there is 0.47 m of air under it. chair stands 0.52 m from lantern (chair's middle at Blender x 3.27, y 22.20; lantern's at x 3.22, y 21.68), so one of them has moved.
   - Fix: Move chair about 0.05 m to the left (across the street) and about 0.52 m down the street, toward the camera so it is back under lantern; or move lantern about 0.05 m to the right (across the street) and about 0.52 m up the street, away from the camera so it is over the middle of chair.
2. **rule 12: room for phone buttons.** board reaches 0.99 across (limit 0.95); notice reaches 0.93 across (limit 0.90); (the reference has the same fault: notice 0.91, chair 0.97, pail 0.96). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: For board and notice: move the camera about 0.14 m to the right without turning it. Near props slide left on screen more than far ones, and where the lines meet stays where it is. Then check again: the props slide by different amounts, so their overlaps change (rule 4). Don't turn the camera instead: that would move where the lines meet away from the reference's.
3. **rule 3: nothing hides the words.** 9% of notice's words are hidden behind chair (only its bottom fifth, the signature, may be covered). (the hidden part is around 0.85 across, 0.61 down)
   - Fix: Move chair about 0.51 m to the right so it no longer hides notice's words. Or move chair about 0.82 m further from the camera, behind board.
4. **reference: where each prop stands.** notice: ours at 0.84 across, 0.58 down; the reference's at 0.83, 0.55; ours is 1.05 times as wide and 0.72 times as tall as the reference's.
   - Fix: It is as wide as the reference's (0.18 against 0.17 of the frame) but 0.72 times as tall: make it about 1.39 times taller without making it wider.
5. **reference: where each prop stands.** lamp post: ours at 0.84 across, 0.10 down; the reference's at 0.79, 0.10.
   - Fix: Move lamp post about 0.19 m to the left.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.81 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.02 m in height, 0.01 m sideways, 0.1 degrees of turn and 0.7 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 62 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.684 across, 0.439 down; the reference's at 0.706, 0.424: 0.022 of the frame width and 0.015 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- reference: how far the camera stands: The props are about the reference's size (middle of 6: 1.00 times).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.009 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 3: story props together in the street: drum, chair, pail stand in front of board and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.43 of the frame wide and 0.42 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.50 across), notice's right side (0.93), notice's top (0.51 down) and pail's bottom (0.93). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.44, so up to 0.48 by 0.50 is allowed.)
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.52 down.
- rule 8: work props small, far and dim: sacks hardly shows (under 0.1% of the frame), its middle 0.50 down.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- reference: where each prop stands: drum: ours at 0.61 across, 0.73 down; the reference's at 0.59, 0.74; ours is 1.22 times as wide and 1.21 times as tall as the reference's.
- reference: where each prop stands: chair: ours at 0.79 across, 0.71 down; the reference's at 0.84, 0.72; ours is 0.90 times as wide and 0.97 times as tall as the reference's.
- reference: where each prop stands: pail: ours at 0.84 across, 0.86 down; the reference's at 0.89, 0.83; ours is 1.02 times as wide and 1.08 times as tall as the reference's.
- reference: where each prop stands: handcart: ours at 0.19 across, 0.53 down; the reference's at 0.23, 0.53; ours is 0.82 times as wide and 0.83 times as tall as the reference's.

## Notes

- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 8: work props small, far and dim: dustbins does not show in this frame.
- reference: where each prop stands: chair: the reference has it 0.05 of the frame width further right (ours at 0.79 across, the reference's at 0.84), but matching that would push its right edge to 0.96, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: where each prop stands: lantern: not compared until it rests where it should (problem 1).
- reference: where each prop stands: pail: the reference has it 0.06 of the frame width further right (ours at 0.84 across, the reference's at 0.89), but matching that would push its right edge to 0.96, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: landmarks: These are buildings, not props: they are never moved; they only show whether the camera matches. winding wheels ours at 0.62 across, 0.23 down; the reference's at 0.62, 0.22; chimney ours at 0.47 across, 0.08 down; the reference's at 0.45, 0.12.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
