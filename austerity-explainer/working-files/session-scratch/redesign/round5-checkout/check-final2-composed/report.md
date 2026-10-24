# Shot check: check-final2-composed

0 problems found in 29 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.60 m above the pavement under it (a standing person: 1.50 to 1.70 m).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of bill stand is 0.005 of the frame width away (limit 0.03).
- rule 4: overlap clearly or leave a clear gap: No two of bill, basket, divider, card terminal, checkout sign, till just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: story props close together: The story props fill a box 0.37 of the frame wide and 0.35 tall (limit 0.40 x 0.50). Its edges: basket's left side (0.47 across), basket's right side (0.84), bill's top (0.43 down) and divider's bottom (0.78).
- rule 7: the story reaches the frame's lower part: The lowest story thing that shows is divider, reaching 0.78 down the frame (the check file asks for at least 0.70).
- rule 3: nothing hides the words: 0% of bill's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of bread label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of milk label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 1% of butter label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of cheese label's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of checkout sign's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of petrol fascia's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (basket 0.83, divider 0.79, checkout sign 0.81, milk label 0.68, butter label 0.60, petrol fascia 0.42, cheese label 0.70, bill 0.82, bread label 0.57).
- rule 12: titles in dim sky: The title area (0.06 to 0.90 across, 0.05 to 0.22 down) is dim, empty sky.
- rule 8: work props small, far and dim: till covers 0.4% of the frame, its middle 0.61 down, its brightness 0.12 (it must stay under the frame's average, 0.23).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.4% of the frame (limit 1%): brightness 0.09 against 0.49 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: bill is the biggest bright thing: Of the brightest parts (the brightest 3% of the frame), 95% lie on bill (need 40%) and 99% in the story props' box (need 75%). The largest bright patch belongs to bill.
- rule 5: bill is bright: bill is 2.71 times as bright as the frame's average (need 1.8).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.10, 0.05, 0.02 (limit 0.36).
- rule 6: warm light from the people's own lights: Warm light covers 1.7% of the frame, 59% of it round the story props.
- rule 6: lit from below: The bottom of bill is 0.12 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- rule 5: nothing in the story group as bright as bill: Every story prop stays darker than bill (0.79).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: the quiet side keeps the frame from tipping: The left half (away from bill) holds 46% of the weight (aim for 40 to 48%).
- rule 10: nothing on the quiet side outshines the subject: Nothing in the left half is as bright as bill, and no prop there covers more than 2%.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.67 across, 0.57 down; centre of the warm light 0.80 across, 0.69 down; centre of the story props 0.65 across, 0.60 down; centre of bill 0.66 across, 0.52 down. Together they span 0.30 of the frame wide and 0.19 tall (limit 0.40 x 0.50, holding bill).

## Notes

- rule 8: work props small, far and dim: bag rack does not show in this frame.
- rule 8: work props small, far and dim: crates does not show in this frame.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.87 across, 0.94 down (2.3% of the frame; lit most by warm-lamp); at 0.94 across, 0.79 down (1.6% of the frame; lit most by warm-lamp); at 0.33 across, 0.95 down (1.0% of the frame; lit most by warm-lamp). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
