# Shot check: check-final-plate

3 problems found in 29 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 8: nothing big and dark where the eye enters). First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.

## Problems

1. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 2.0% of the frame (limit 1%): brightness 0.15 against 0.44 for the lit ground around it. It is not a prop: probably a shadow cast across the ground. (from 0.14 to 0.38 across, 0.85 to 1.00 down)
   - Fix: First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.
2. **rule 6: warm light from the people's own lights.** Warm light covers only 1.2% of the frame (aim for 1.5 to 3%); only 49% of it lies round the story props (need most of it). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Let the fire and the lantern light more. 51% of the warm light is away from the story props; the largest patch is on the road or pavement at 0.85 across, 0.67 down (marked). The warm lights lighting it most: warm-lamp (6.8 m from it, out of the frame; about 37% of the warm light reaching it if nothing shades it); street-light-1--4.5 (11.8 m from it, in the frame; about 36% of the warm light reaching it if nothing shades it). Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
3. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from bill) holds 51% of the weight (aim for 40 to 48%).
   - Fix: The left half is too busy: dim or remove some of its detail.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.60 m above the pavement under it (a standing person: 1.50 to 1.70 m).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of bill stand is 0.004 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of bill, basket, divider, card terminal, checkout sign, till just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props fill a box 0.29 of the frame wide and 0.27 tall (limit 0.40 x 0.50). Its edges: basket's left side (0.48 across), basket's right side (0.76), bill's top (0.44 down) and divider's bottom (0.71).
- rule 7: the story reaches the frame's lower part: The lowest story thing that shows is divider, reaching 0.71 down the frame (the check file asks for at least 0.70).
- rule 3: nothing hides the words: 0% of bill's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of bread label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of milk label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 2% of butter label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of cheese label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of checkout sign's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of petrol fascia's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (basket 0.76, divider 0.72, butter label 0.58, bill 0.76, checkout sign 0.77, petrol fascia 0.42, bread label 0.56, cheese label 0.65, milk label 0.64).
- rule 12: titles in dim sky: The title area (0.06 to 0.90 across, 0.05 to 0.22 down) is dim, empty sky.
- rule 8: work props small, far and dim: till covers 0.3% of the frame, its middle 0.59 down, its brightness 0.11 (it must stay under the frame's average, 0.20).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 5: bill is the biggest bright thing: Of the brightest parts (the brightest 3% of the frame), 75% lie on bill (need 40%) and 81% in the story props' box (need 75%). The largest bright patch belongs to bill.
- rule 5: bill is bright: bill is 3.17 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.08, 0.04, 0.01 (limit 0.36).
- rule 6: lit from below: The bottom of bill is 0.11 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- rule 5: nothing in the story group as bright as bill: Every story prop stays darker than bill (0.78).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as bill, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.65 across, 0.58 down; centre of the warm light 0.77 across, 0.68 down; centre of the story props 0.62 across, 0.57 down; centre of bill 0.63 across, 0.52 down. Together they span 0.27 of the frame wide and 0.18 tall (limit 0.40 x 0.50, holding bill).

## Notes

- rule 4: overlap clearly or leave a clear gap: divider overlaps basket by 15 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 8: work props small, far and dim: bag rack does not show in this frame.
- rule 8: work props small, far and dim: crates does not show in this frame.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.87 across, 0.76 down (1.4% of the frame; lit most by warm-lamp); at 0.04 across, 0.74 down (0.7% of the frame; lit most by warm-lamp); at 0.79 across, 0.81 down (0.5% of the frame; lit most by warm-lamp). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
