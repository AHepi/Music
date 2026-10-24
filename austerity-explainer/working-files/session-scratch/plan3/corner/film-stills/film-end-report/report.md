# Shot check: the film's end frame (9.5 s)

8 problems found in 37 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 8: nothing big and dark where the eye enters). First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.

## Problems

1. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 2.1% of the frame (limit 1%): brightness 0.14 against 0.33 for the lit ground around it. It is not a prop: probably a shadow cast across the ground. (from 0.26 to 0.50 across, 0.80 to 0.97 down)
   - Fix: First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.
2. **rule 5: notice is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 57% lie on notice (need 40%) and 67% in the story props' box (need 75%). The largest bright patch belongs to notice.
   - Fix: Light notice more, or dim what is around it.
3. **rule 6: warm light from the people's own lights.** Only 43% of it lies round the story props (need most of it). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: 57% of the warm light is away from the story props; the largest patch is on the road or pavement at 0.36 across, 0.71 down (marked). The warm lights lighting it most: fire_glow_on_road (2.1 m from it, in the frame; about 75% of the warm light reaching it if nothing shades it); brazier_light (2.1 m from it, in the frame; about 12% of the warm light reaching it if nothing shades it). Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
4. **rule 8: work props small, far and dim.** dustbins covers 0.2% of the frame, its middle 0.50 down, its brightness 0.30 (it must stay under the frame's average, 0.27). It is brighter than the frame's average.
   - Fix: Keep dustbins where it is but in shadow.
5. **reference: where each prop stands.** lamp post: ours at 0.81 across, 0.20 down; the reference's at 0.79, 0.10.
   - Fix: Move lamp post about 2.17 m nearer to the camera.
6. **reference: where each prop stands.** pail: ours at 0.77 across, 0.88 down; the reference's at 0.89, 0.83; ours is 1.00 times as wide and 0.79 times as tall as the reference's.
   - Fix: Move pail about 0.41 m further from the camera (but chair stands there); it is as wide as the reference's (0.14 against 0.14 of the frame) but 0.79 times as tall: make it about 1.26 times taller without making it wider.
7. **reference: where each prop stands.** notice: ours at 0.80 across, 0.58 down; the reference's at 0.83, 0.55; ours is 1.03 times as wide and 0.72 times as tall as the reference's.
   - Fix: It is as wide as the reference's (0.18 against 0.17 of the frame) but 0.72 times as tall: make it about 1.39 times taller without making it wider.
8. **reference: where each prop stands.** lantern: ours at 0.76 across, 0.71 down; the reference's at 0.81, 0.69; ours is 0.87 times as wide and 1.08 times as tall as the reference's.
   - Fix: Move chair (with lantern on it) about 0.12 m to the right.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.80 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- reference: the camera: Our camera is within 0.02 m in height, 0.13 m sideways, 0.1 degrees of turn and 0.7 degrees of view of the camera that best matches the reference. Even that best camera misses the reference's landmarks by up to 62 pixels (the reference is a painting, not an exact photo), so differences this small mean nothing.
- reference: where the lines meet: Ours meet at 0.684 across, 0.439 down; the reference's at 0.706, 0.424: 0.022 of the frame width and 0.015 of its height apart (a drawn picture's lines rarely meet at one exact point, so 0.03 either way is allowed).
- reference: how far the camera stands: The props are about the reference's size (middle of 6: 1.05 times).
- props rest where they should: board, drum, chair, pail, lamp post, handcart, barrel, dustbins, left lamp stand on the pavement or road (within 3 cm).
- props rest where they should: lantern rests on chair.
- rule 1: aim the street at the story: The street's lines meet at 0.684 across, 0.439 down; the nearest edge of board is 0.005 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of notice, board, drum, chair, lantern, pail, lamp post, winding wheels, left lamp, handcart, sacks, dustbins just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 3: story props together in the street: drum, chair, pail stand in front of board and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props (leaving out board) fill a box 0.43 of the frame wide and 0.42 tall (limit 0.48 x 0.50). Its edges: drum's left side (0.46 across), notice's right side (0.88), notice's top (0.51 down) and pail's bottom (0.93). (The rule says 0.40 wide and 0.50 tall, but the reference fills 0.46 by 0.44, so up to 0.48 by 0.50 is allowed.)
- rule 3: nothing hides the words: 3% of notice's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (board 0.94, drum 0.67, chair 0.88, lantern 0.79, pail 0.84, notice 0.89).
- rule 12: titles in dim sky: The title area (0.05 to 0.62 across, 0.02 to 0.12 down) is dim, empty sky.
- rule 8: work props small, far and dim: handcart covers 0.9% of the frame, its middle 0.54 down, its brightness 0.16 (it must stay under the frame's average, 0.27).
- rule 8: work props small, far and dim: sacks covers 0.2% of the frame, its middle 0.52 down, its brightness 0.15 (it must stay under the frame's average, 0.27).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 5: notice is bright: notice is 2.39 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.26, 0.32, 0.22 (limit 0.36).
- rule 6: lit from below: The bottom of notice is 0.23 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- rule 5: nothing in the story group as bright as notice: Every story prop stays darker than notice (0.73), apart from the small flame of lantern.
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: the quiet side keeps the frame from tipping: The left half (away from notice) holds 46% of the weight (aim for 40 to 48%).
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as notice, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.68 across, 0.44 down; centre of the brightest parts 0.66 across, 0.52 down; centre of the warm light 0.49 across, 0.52 down; centre of the story props 0.72 across, 0.67 down; centre of notice 0.79 across, 0.57 down. Together they span 0.31 of the frame wide and 0.23 tall (limit 0.40 x 0.50, holding notice).
- reference: where each prop stands: drum: ours at 0.57 across, 0.73 down; the reference's at 0.59, 0.74; ours is 1.22 times as wide and 1.21 times as tall as the reference's.
- reference: where each prop stands: chair: ours at 0.75 across, 0.74 down; the reference's at 0.84, 0.72; ours is 1.01 times as wide and 1.10 times as tall as the reference's.
- reference: where each prop stands: handcart: ours at 0.22 across, 0.55 down; the reference's at 0.23, 0.53; ours is 0.99 times as wide and 1.03 times as tall as the reference's.

## Notes

- rule 4: overlap clearly or leave a clear gap: board and lantern are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 8: work props small, far and dim: barrel does not show in this frame.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.37 across, 0.70 down (1.2% of the frame; lit most by fire_glow_on_road); at 0.55 across, 0.61 down (0.4% of the frame; lit most by gas_lamp_1_light). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.
- reference: where each prop stands: chair: the reference has it 0.09 of the frame width further right (ours at 0.75 across, the reference's at 0.84), but matching that would push its right edge to 0.97, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: where each prop stands: pail: the reference has it 0.12 of the frame width further right (ours at 0.77 across, the reference's at 0.89), but matching that would push its right edge to 0.96, past rule 12's limit of 0.95: leave it (the reference breaks rule 12 there).
- reference: landmarks: These are buildings, not props: they are never moved; they only show whether the camera matches. winding wheels ours at 0.61 across, 0.23 down; the reference's at 0.62, 0.22; chimney ours at 0.47 across, 0.08 down; the reference's at 0.45, 0.12.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
