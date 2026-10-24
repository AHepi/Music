# Shot check: notice corner plate, from the slide's start

13 problems found in 35 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version ab62f926; a report made by another version may give other numbers.

## Fix first

Problem 1 (reference: the camera). Lower the camera about 0.10 m; narrow its view by about 4.1 degrees (top to bottom).
Fix the camera before anything else, then check again: the places of the props on screen will all change.

## Problems

1. **reference: the camera.** The camera that best matches the reference (at our distance up the street) is 1.81 m above the pavement, 2.96 m right of the street's middle line, turned 6.9 degrees left of straight up the street, seeing 60.3 degrees top to bottom; ours is 1.91 m above the pavement, 2.99 m right of the street's middle line, turned 6.9 degrees left of straight up the street, seeing 64.4 degrees top to bottom. Ours misses the reference's landmarks by up to 83 pixels (right wheel hub); the best camera by up to 63. (landmarks missed by ours, in pixels: left wheel hub 81, right wheel hub 83, chimney top 28, gate bottom left 10, gate top left 14, left roofline 61, left kerb 30, right kerb 12)
   - Fix: Lower the camera about 0.10 m; narrow its view by about 4.1 degrees (top to bottom).
2. **rule 2: stand at eye height.** The camera's eye is 1.91 m above the pavement under it (a standing person: 1.50 to 1.90 m).
   - Fix: The camera fix in problem 1 covers this: it puts the camera's eye 1.81 m above the pavement. Check again after it.
3. **rule 5: notice is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 36% lie on notice (need 40%) and 58% in the story props' box (need 75%). The largest bright patch belongs to notice.
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Light notice more, or dim what is around it.
4. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps board: it reaches 4 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.75 across, 0.62 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.22 m further from the camera so it clearly overlaps board, or move chair (with lantern on it) about 0.35 m nearer to the camera (but pail stands there) to leave a clear gap.
5. **rule 4: overlap clearly or leave a clear gap.** notice and lantern almost touch: 7 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.75 across, 0.61 down; lantern is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair (with lantern on it) about 0.45 m further from the camera so it clearly overlaps notice, or move chair (with lantern on it) about 0.22 m nearer to the camera (but pail stands there) to leave a clear gap.
6. **rule 6: warm light from the people's own lights.** Warm light covers only 1.2% of the frame (aim for 1.5 to 3%). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Let the fire and the lantern light more.
7. **rule 6: lit from below.** The bottom of notice is 0.08 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Give notice's bottom more warm light than its top: bring the warm light below it closer under its bottom edge, or aim it there (fire_glow_on_notice, lantern_light); or dim or whiten the light from above (brazier_light, fire_glow_on_road, right_row_a_cottage_05_window_light_upper_1, dusk_skylight). Then check again.
8. **rule 3: nothing hides the words.** 5% of notice's words are hidden behind chair (only its bottom fifth, the signature, may be covered). (the hidden part is around 0.78 across, 0.58 down)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair about 0.10 m nearer to the camera, so it no longer hides notice's words.
9. **rule 4: overlap clearly or leave a clear gap.** chair's edge runs right along pail's edge for 30 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.71 to 0.73 down, around 0.80 across; pail is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move chair about 0.06 m to the left so chair clearly passes behind pail, or move chair about 0.07 m to the right to leave a clear gap.
10. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from notice) holds 40% of the weight (aim for 40 to 48%).
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Add a few small dim lights or details in the left half (a lit window, a distant lamp) until it holds about 42%.
11. **rule 4: overlap clearly or leave a clear gap.** sacks only just overlaps dustbins: it reaches 3 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.20 across, 0.52 down; sacks is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move sacks about 0.15 m to the left so it clearly overlaps dustbins, or move sacks about 0.24 m to the right to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** left lamp and handcart almost touch: 14 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.37 across, 0.50 down; handcart is nearer the camera)
   - Fix: Fix the camera first (problem 1) and check again: this may change. If it stays: Move handcart about 0.20 m to the right and about 2.75 m further from the camera so it clearly overlaps left lamp, or move handcart about 0.04 m to the left and about 0.45 m nearer to the camera to leave a clear gap.
13. **reference: where the lines meet.** Ours meet at 0.670 across, 0.444 down; the reference's at 0.706, 0.424: 0.036 of the frame width and 0.020 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
   - Fix: This follows from the camera: the fix in problem 1 moves where the lines meet too. Check again after it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- reference: how far the camera stands: The props are about the reference's size (middle of 6: 0.70 times).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins, left lamp stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.670 across, 0.444 down; the nearest edge of board is 0.029 of the frame width away (limit 0.03).
- rule 3: story props together in the street: drum, chair, pail stand in front of board and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.29 of the frame wide and 0.26 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.54 across), notice's right side (0.84), notice's top (0.51 down) and pail's bottom (0.77). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.44, so up to 0.48 by 0.50 is allowed.)
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (board 0.88, drum 0.69, chair 0.83, lantern 0.77, pail 0.80, notice 0.84).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.6% of the frame, its middle 0.53 down, its brightness 0.10 (it must stay under the frame's average, 0.21).
- rule 8: work props small, far and dim: sacks covers 0.2% of the frame, its middle 0.52 down, its brightness 0.11 (it must stay under the frame's average, 0.21).
- rule 8: work props small, far and dim: dustbins covers 0.2% of the frame, its middle 0.50 down, its brightness 0.18 (it must stay under the frame's average, 0.21).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.4% of the frame (limit 1%): brightness 0.09 against 0.21 for the lit ground around it. Most of it is handcart.
- rule 5: notice is bright: notice is 3.35 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.24, 0.26, 0.18 (limit 0.36).
- rule 5: nothing in the story group as bright as notice: Every story prop stays darker than notice (0.74).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as notice, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.67 across, 0.44 down; centre of the brightest parts 0.64 across, 0.49 down; centre of the warm light 0.75 across, 0.52 down; centre of the story props 0.73 across, 0.61 down; centre of notice 0.77 across, 0.55 down. Together they span 0.13 of the frame wide and 0.16 tall (limit 0.40 x 0.50, holding notice).

## Notes

- rule 4: overlap clearly or leave a clear gap: notice and drum are 23 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: drum overlaps board by 19 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.87 across, 0.70 down (0.4% of the frame; lit most by brazier_light); at 0.67 across, 0.79 down (0.3% of the frame; lit most by brazier_light); at 0.46 across, 0.65 down (0.2% of the frame; lit most by fire_glow_on_road). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.
- reference: where each prop stands: Not judged: the camera is wrong (problem 1), and the camera moves everything on screen. Fix the camera, then check again; don't move any prop yet.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
