# Shot check: base-w4

24 problems found in 36 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 3: story props in the frame). Move man 4 about 1.24 m to the right (bring it just inside the frame).

## Problems

1. **rule 3: story props in the frame.** man 4 is outside the frame, past the left edge: it would sit -0.23 to -0.01 across, 0.48 to 0.71 down.
   - Fix: Move man 4 about 1.24 m to the right (bring it just inside the frame).
2. **rule 3: story props in the frame.** man 8 is outside the frame, past the left edge: it would sit -0.23 to -0.03 across, 0.48 to 0.69 down.
   - Fix: Move man 8 about 1.35 m to the right (bring it just inside the frame).
3. **rule 6: warm light from the people's own lights.** Warm light covers 23.9% of the frame, 8.0 times the most allowed (3%); only 42% of it lies round the story props (need most of it). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: 58% of the warm light is away from the story props; the largest patch is on the house walls at 0.79 across, 0.34 down (marked). The warm lights lighting it most: none found. Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
4. **rule 5: nothing in the story group as bright as no-2 gate.** the brightest parts of jacket and cap reach 0.44, as bright as no-2 gate (0.29); the brightest parts of upturned crate reach 0.55, as bright as no-2 gate (0.29); the brightest parts of mug and wages reach 0.83, as bright as no-2 gate (0.29); the brightest parts of man 1 reach 0.33, as bright as no-2 gate (0.29); the brightest parts of man 2 reach 0.41, as bright as no-2 gate (0.29); the brightest parts of man 3 reach 0.37, as bright as no-2 gate (0.29); the brightest parts of man 5 reach 0.30, as bright as no-2 gate (0.29); the brightest parts of man 6 reach 0.32, as bright as no-2 gate (0.29); the brightest parts of man 7 reach 0.42, as bright as no-2 gate (0.29).
   - Fix: Make jacket and cap darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make upturned crate darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make mug and wages darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 1 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 2 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 3 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 5 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 6 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 7 darker (its own colour) or move it further from the light on it (no-2-gateway-beam).
5. **rule 3: story props close together.** The story props fill a box 0.75 of the frame wide and 0.52 tall (limit 0.40 x 0.50). Its edges: man 3's left side (0.00 across), jacket and cap's right side (0.75), no-2 gate's top (0.29 down) and upturned crate's bottom (0.81).
   - Fix: Move jacket and cap about 1.26 m to the left; move upturned crate about 0.34 m further from the camera.
6. **rule 8: nothing big where the eye enters.** crates fills 6.0% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move crates out of the bottom-left quarter.
7. **rule 5: no-2 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on no-2 gate (need 40%) and 73% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-2 gate more.
8. **rule 5: no-2 gate is bright.** no-2 gate is 0.75 times as bright as the frame's average (need 1.8).
   - Fix: Light no-2 gate more, or darken what is around it.
9. **rule 12: nothing important cut by the frame edge.** man 3 is cut by the frame's left edge: about 83% of it is inside. (it would sit -0.03 to 0.17 across, 0.48 to 0.71 down)
   - Fix: Move man 3 about 0.29 m to the right to bring it all in.
10. **rule 5: keep the sky dim.** The top third's brightness, left to right: 0.26, 0.47, 0.51 (limit 0.36).
   - Fix: Darken the sky (or ask the painter for a darker sky).
11. **rule 8: nothing big where the eye enters.** no-2 gate fills 2.3% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move no-2 gate out of the bottom-left quarter.
12. **rule 4: overlap clearly or leave a clear gap.** man 1's edge runs right along no-2 gate's edge for 64 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.62 to 0.64 down, around 0.48 across; no-2 gate is nearer the camera)
   - Fix: Move man 1 about 0.07 m to the left so man 1 clearly passes behind no-2 gate, or move man 1 about 0.09 m to the right to leave a clear gap.
13. **rule 10: nothing on the quiet side outshines the subject.** A light in the right half (at 0.55 across, 0.39 down) is 0.81 bright, as bright as no-2 gate (0.31).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
14. **rule 4: overlap clearly or leave a clear gap.** man 7's edge runs right along crates's edge for 53 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.64 to 0.66 down, around 0.16 across; crates is nearer the camera)
   - Fix: Move man 7 about 0.08 m to the left so man 7 clearly passes behind crates, or move man 7 about 0.09 m to the right to leave a clear gap.
15. **rule 10: the quiet side keeps the frame from tipping.** The right half (away from no-2 gate) holds 51% of the weight (aim for 40 to 48%).
   - Fix: The right half is too busy: dim or remove some of its detail.
16. **rule 8: nothing big where the eye enters.** man 3 fills 1.4% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 3 out of the bottom-left quarter.
17. **rule 8: nothing big where the eye enters.** man 2 fills 1.3% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 2 out of the bottom-left quarter.
18. **rule 4: overlap clearly or leave a clear gap.** man 2 and handcart almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.31 across, 0.53 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.13 m to the right so it clearly overlaps handcart, or move man 2 about 0.02 m to the left to leave a clear gap.
19. **rule 8: nothing big where the eye enters.** man 1 fills 1.2% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 1 out of the bottom-left quarter.
20. **rule 8: nothing big where the eye enters.** upturned crate fills 1.1% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move upturned crate out of the bottom-left quarter.
21. **rule 4: overlap clearly or leave a clear gap.** man 3 only just overlaps man 7: it reaches 14 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.14 across, 0.56 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.01 m to the right and about 0.17 m further from the camera so it clearly overlaps man 7, or move man 3 about 0.10 m to the left and about 1.26 m nearer to the camera to leave a clear gap.
22. **rule 6: lit from below.** The bottom of no-2 gate is 0.09 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give no-2 gate's bottom more warm light than its top: dim or whiten the light from above (dusk_skylight, no-2-gateway-spill); or add a warm light below it, aimed at its bottom edge. Then check again.
23. **rule 4: overlap clearly or leave a clear gap.** man 7's edge runs right along no-2 gate's edge for 31 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.50 to 0.52 down, around 0.18 across; no-2 gate is nearer the camera)
   - Fix: Move man 7 about 0.08 m to the right so man 7 clearly passes behind no-2 gate, or move man 7 about 0.09 m to the left to leave a clear gap.
24. **rule 12: titles in dim sky.** Only 28% of the title area is sky (need 85%); it is too bright for titles (0.44, limit 0.36). (28% of the title area is sky; its brightness 0.44)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: upturned crate, crates, handcart, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- props rest where they should: mug and wages rests on upturned crate.
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gate is 0.006 of the frame width away (limit 0.03).
- rule 3: story props together in the street: upturned crate, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand in front of None and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another. Not showing at all: man 4 (problem 1), man 8 (problem 2).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (jacket and cap 0.75, upturned crate 0.58, mug and wages 0.58, man 1 0.50, man 2 0.30, man 3 0.14, man 5 0.54, man 6 0.41, man 7 0.25).
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.4% of the frame (limit 1%): brightness 0.12 against 0.45 for the lit ground around it. Most of it is crates.
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.59 across, 0.34 down; centre of the warm light 0.65 across, 0.43 down; centre of the story props 0.36 across, 0.60 down; centre of no-2 gate 0.32 across, 0.55 down. Together they span 0.34 of the frame wide and 0.25 tall (limit 0.40 x 0.50, holding no-2 gate).

## Notes

- rule 4: overlap clearly or leave a clear gap: no-2 gate and man 3 are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.62 across, 0.84 down (22.3% of the frame; lit most by no-2-gateway-beam); at 0.89 across, 0.17 down (6.2% of the frame); at 0.14 across, 0.13 down (0.6% of the frame). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
