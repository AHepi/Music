# Shot check: facts

19 problems found in 39 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 3: story props in the frame). Move man 4 about 1.22 m to the right (bring it just inside the frame).

## Problems

1. **rule 3: story props in the frame.** man 4 is outside the frame, past the left edge: it would sit -0.25 to -0.01 across, 0.48 to 0.73 down.
   - Fix: Move man 4 about 1.22 m to the right (bring it just inside the frame).
2. **rule 3: story props in the frame.** man 8 is outside the frame, past the left edge: it would sit -0.25 to -0.03 across, 0.48 to 0.71 down.
   - Fix: Move man 8 about 1.33 m to the right (bring it just inside the frame).
3. **rule 3: story props close together.** The story props fill a box 0.88 of the frame wide and 0.58 tall (limit 0.40 x 0.50). Its edges: man 3's left side (0.00 across), crate table's right side (0.88), no-2 gate's top (0.27 down) and upturned crate's bottom (0.85).
   - Fix: Move crate table about 1.47 m to the left; move no-2 gate about 0.46 m lower.
4. **rule 5: nothing in the story group as bright as no-2 gate.** the brightest parts of jacket reach 0.20, as bright as no-2 gate (0.03); the brightest parts of crate table reach 0.39, as bright as no-2 gate (0.03); the brightest parts of cap reach 0.39, as bright as no-2 gate (0.03); the brightest parts of mug reach 0.23, as bright as no-2 gate (0.03); the brightest parts of wages reach 0.73, as bright as no-2 gate (0.03); the brightest parts of upturned crate reach 0.31, as bright as no-2 gate (0.03); the brightest parts of man 1 reach 0.14, as bright as no-2 gate (0.03); the brightest parts of man 2 reach 0.14, as bright as no-2 gate (0.03); the brightest parts of man 3 reach 0.15, as bright as no-2 gate (0.03); the brightest parts of man 5 reach 0.13, as bright as no-2 gate (0.03); the brightest parts of man 6 reach 0.11, as bright as no-2 gate (0.03); the brightest parts of man 7 reach 0.16, as bright as no-2 gate (0.03).
   - Fix: Make jacket darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make crate table darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make cap darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make mug darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make wages darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make upturned crate darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make man 1 darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make man 2 darker (its own colour) or move it further from the light on it (no-2-men-rim-yard). Make man 3 darker (its own colour) or move it further from the light on it (no-2-men-rim-yard). Make man 5 darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make man 6 darker (its own colour) or move it further from the light on it (w4-corner-lamp). Make man 7 darker (its own colour) or move it further from the light on it (no-2-men-rim-yard).
5. **rule 5: no-2 gate is bright.** no-2 gate is 0.33 times as bright as the frame's average (need 1.8).
   - Fix: Light no-2 gate more, or darken what is around it.
6. **rule 5: no-2 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on no-2 gate (need 40%) and 83% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-2 gate more.
7. **rule 12: nothing important cut by the frame edge.** man 3 is cut by the frame's left edge: about 84% of it is inside. (it would sit -0.04 to 0.18 across, 0.48 to 0.73 down)
   - Fix: Move man 3 about 0.27 m to the right to bring it all in.
8. **rule 4: overlap clearly or leave a clear gap.** man 2's edge runs right along no-2 gate's edge for 106 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.52 to 0.56 down, around 0.21 across; no-2 gate is nearer the camera)
   - Fix: Move man 2 about 0.07 m to the right so man 2 clearly passes behind no-2 gate, or move man 2 about 0.08 m to the left to leave a clear gap.
9. **rule 6: warm light from the people's own lights.** Warm light covers only 0.7% of the frame (aim for 1.5 to 3%). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Let the fire and the lantern light more.
10. **rule 8: nothing big where the eye enters.** no-2 gate fills 2.6% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move no-2 gate out of the bottom-left quarter.
11. **rule 8: nothing big where the eye enters.** man 3 fills 2.4% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 3 out of the bottom-left quarter.
12. **rule 4: overlap clearly or leave a clear gap.** man 2 only just overlaps handcart: it reaches 5 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.54 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.02 m to the right and about 1.16 m further from the camera (but man 6 stands there) so it clearly overlaps handcart, or move man 2 about 0.04 m to the left and about 1.49 m nearer to the camera to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** man 7's edge runs right along no-2 gate's edge for 61 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.65 to 0.68 down, around 0.19 across; no-2 gate is nearer the camera)
   - Fix: Move man 7 about 0.08 m to the right so man 7 clearly passes behind no-2 gate, or move man 7 about 0.09 m to the left to leave a clear gap.
14. **rule 10: nothing on the quiet side outshines the subject.** A light in the right half (at 0.76 across, 0.63 down) is 0.64 bright, as bright as no-2 gate (0.05).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
15. **rule 8: nothing big where the eye enters.** man 2 fills 1.5% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 2 out of the bottom-left quarter.
16. **rule 4: overlap clearly or leave a clear gap.** mug and wages almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.80 across, 0.64 down; mug is nearer the camera)
   - Fix: Move crate table (with mug on it) about 0.10 m to the left so it clearly overlaps wages, or move mug on crate table's seat or top about 0.01 m to the right to leave a clear gap.
17. **rule 8: nothing big where the eye enters.** man 1 fills 1.2% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 1 out of the bottom-left quarter.
18. **rule 4: overlap clearly or leave a clear gap.** man 1's edge runs right along no-2 gate's edge for 29 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.54 to 0.54 down, around 0.53 across; no-2 gate is nearer the camera)
   - Fix: Move man 1 about 0.07 m to the left so man 1 clearly passes behind no-2 gate, or move man 1 about 0.08 m to the right to leave a clear gap.
19. **rule 12: titles in dim sky.** Only 30% of the title area is sky (need 85%). (30% of the title area is sky; its brightness 0.16)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: crate table, upturned crate, handcart, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- props rest where they should: cap rests on crate table.
- props rest where they should: mug rests on crate table.
- props rest where they should: wages rests on crate table.
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gate is 0.000 of the frame width away (limit 0.03).
- rule 3: story props together in the street: crate table, upturned crate, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand in front of None and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another. Not showing at all: man 4 (problem 1), man 8 (problem 2).
- rule 7: the story reaches the frame's lower part: The lowest story thing that shows is upturned crate, reaching 0.85 down the frame (the check file asks for at least 0.80).
- rule 3: nothing hides the words: 1% of wages's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of no-2 board back's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (jacket 0.84, crate table 0.88, cap 0.77, mug 0.85, wages 0.80, upturned crate 0.65, man 1 0.54, man 2 0.33, man 3 0.15, man 5 0.58, man 6 0.44, man 7 0.27, no-2 board back 0.35).
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.3% of the frame (limit 1%): brightness 0.05 against 0.11 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.13, 0.21, 0.13 (limit 0.36).
- rule 6: lit from below: The bottom of no-2 gate is 0.52 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: the quiet side keeps the frame from tipping: The right half (away from no-2 gate) holds 48% of the weight (aim for 40 to 48%).
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.69 across, 0.61 down; centre of the warm light 0.62 across, 0.61 down; centre of the story props 0.45 across, 0.64 down; centre of no-2 gate 0.34 across, 0.57 down. Together they span 0.35 of the frame wide and 0.14 tall (limit 0.40 x 0.50, holding no-2 gate).

## Notes

- rule 4: overlap clearly or leave a clear gap: mug overlaps jacket by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: crate table and upturned crate are 21 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: cap overlaps wages by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: upturned crate overlaps man 5 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 1 overlaps handcart by 19 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 3 overlaps man 7 by 15 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.60 across, 0.62 down (1.1% of the frame; lit most by brazier_light); at 0.76 across, 0.84 down (0.7% of the frame; lit most by w4-corner-lamp); at 0.90 across, 0.70 down (0.3% of the frame; lit most by brazier_light). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
