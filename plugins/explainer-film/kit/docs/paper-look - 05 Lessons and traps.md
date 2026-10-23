# Lessons and traps

**What this is:** what went wrong while building and testing chapter 1 of the austerity explainer
in this look, and how each was fixed. The fixes are already in the kit; the lessons are here so a
new series doesn't walk into the same holes.

## The voice and the sound

1. **The accent switched and the voice shouted.** Mixed mood cues ([urgent], [serious]) moved the
   voice up and down between pages, and words in capitals made it push. Fix: one accent instruction
   opens every page, no other cues, no capitals. The voice still sounded "a bit Australian" to the
   user, who accepted it ("It'll do for now").
2. **The instruction was timed as spoken words.** A bracketed instruction several words long came back
   from the transcript as words. Fix: everything from "[" to "]" is kept apart as the instruction.
3. **The first word was placed late.** After the instruction, ElevenLabs put each page's first word up
   to 0.32 s after the voice really starts. Fix: the word-times tool finds where the voice begins in
   the recording and moves the first word back.
4. **Levelling pushed peaks past full scale.** Fix: the narration track is kept in floating-point
   samples; the mix's limiter holds the final peaks at about -1.6 dB.
5. **The sound came out 5 ms late.** The limiter looks ahead 5 ms. Fix: its delay compensation is on
   (`latency=1`). Measure alignment after every change (`check_sound_alignment.py`).
6. **The music vanished under the voice** at the first ducking setting (31 dB under). Fix: settings
   measured and chosen so the music sits about 18 dB under the voice.
7. **A sample-rate change made the mix 3 seconds short.** ffmpeg's loudness filter switches to
   192,000 samples a second; convert back to 48,000 straight after it.

## The paintings and cut-outs

8. **Video and image models invented things.** Second World War tanks in a 1919 scene, a tank facing
   the crowd (the research said otherwise), a symbol like a hooked cross on a placard, a real
   movement's red-and-black flag, shells that looked like rifle cartridges, a tank with an odd shape.
   Fix: describe historical shapes exactly, say what must not be there, check every picture on a
   contact sheet, re-paint failures.
9. **The background remover dropped parts of pictures**: a wooden lectern, half of Sardinia, part of a
   coal heap. Found by laying every cut-out over magenta (`contact_sheet_masks.py`). Fix in the cut list:
   `add_polygons` puts back an outline, `map_card` prints a map on a card, `mask_threshold` keeps faint parts.
10. **A pale fin on a tank's roof could read as a flag.** Fix: `leave_out_boxes` cuts it away.

## The paper stage

11. **No shadows at all.** Flat sheets lit from the front cast nothing: the 3D library draws shadows
    from a sheet's back face only. Found by lighting with the lamp alone. Fix: every sheet casts from
    both faces. Check with `check-shadows.mjs`.
12. **The smoothest soft shadows failed silently** in the hidden browser (no half-precision filtering
    in software graphics). Fix: plain shadows with widened, softened edges.
13. **Shadows too small, then words with ghost shadows.** Pieces stood too close to their sheet, so
    their shadows hid behind their own paper margins; standing words further out made their shadow read
    as a second word. Fix: pieces at 0.6 to 3, words at 0.55.
14. **The first page turn swung like a door and left white strips.** Fix: the corner peel, with pieces
    folding down and being put away before the turn.
15. **The first paper mouth looked like a black bar.** Fix: a narrower jaw with rounded top corners, a
    small drop (about 2% of the figure's height), no tipping, and loudness thresholds that open it only
    on louder syllables.
16. **Dust was hidden behind the crowd**, and later **washed out a falling word** standing in front of
    it. Fix: dust bursts above or behind what it belongs to.
17. **Dust lingered after its page had gone** when frames were drawn out of order. Fix: dust and smoke
    belong to their page (`kit.effect`) and are hidden with it.
18. **Knocked-down pieces showed as pale blobs** low in the frame (a flat piece lies toward the camera
    like a shelf and shows its paper back). Fix: fold such pieces away instead of leaving them flat.
19. **Pieces near the sides were cut off by the frame.** A piece in front of its sheet looks bigger than
    its size on the sheet. Fix: keep edges within about 4.1 units of the middle (less further forward).
20. **A worker's cap peeked over a door meant to hide him.** The door was the same height on the sheet
    but further forward, so it looked shorter than expected. Fix: the door made taller and wider. Found
    only after filming, on a close look at one frame.
21. **The motion maths divided by zero** for a spring with no overshoot (damping 1). Fix: a separate
    formula for that case.

## Timing and filming

22. **Pictures tied to the wrong word.** Words spoken twice on a page ("war", "get", "prices",
    "shells") were looked up by their first time. Fix: ask by number (`at('war', 2)`); check every lookup.
23. **Two films at once were no faster.** One hidden browser already uses both processors. Fix: film
    one page-sized chunk after another; this also lets one page be filmed again alone.
24. **A 37 MB film was over the 30 MB sending limit.** Fix: a second copy squeezed in two passes
    (`finish_film.sh`), checked against the master on busy frames.

## Traps

- Check for shadows with the lamp alone: a scene can look fine while casting no shadows at all.
- Lay every cut-out over a loud colour before using it: missing and faint parts show at once.
- Check every painting for wrong-era details, symbols, flags and writing.
- Look at single frames at full size; contact sheets of small frames hide edge and overlap faults.
- Anything a page shows (pieces, dust, smoke) must be put away with that page.
- Measure, don't assume, that sound and picture line up; filters can add delay.
- A word spoken twice on a page must be asked for by which time it is spoken.

- Fading a cut-out with `.set({ opacity })` snaps instead of fading: the piece stays solid, then
  vanishes at half opacity (a piece first drawn solid keeps a recipe that ignores see-through, and
  cut-outs are only drawn where at least half solid). Use `setFading(piece, pose)` from
  `paper-film/scenes/cinema-kit.js` (in this plugin kit; the same function as in
  `paper-film/scenes/house-sample/page-1.js`, log 27, lesson 87 of the austerity project's notes) on every
  frame the piece shows.

- Built places, painted over (`paper-film/scenes/projected-set.js`, the pit village test, log 29):
  - The plate's frame is only a little wider than the film's. Never turn the camera during a move:
    slide it in a straight line toward the subject, from one spoken word to another, starting and stopping
    gently (chapter 2's newcomer pages plan 0.4 to 1.5 m in 2.6 to 4.1 s; the notice corner's test clip slid
    1.5 m over 8.5 s), and stop on the composed frame (rule 11 of `07 Composing a shot`, logs 31 to 34; this replaces log
    29's "turn a degree or two and push in with the lens"). Check the `weights` view at the end of every
    move (blue at an edge = no painting there).
  - Moving past near props uncovers what they hid, and the painter's outlines round them lie on the
    road: give the projection a `behind` painting (the same painting with the near props painted out
    by Flux) and soft contact shadows under those props.
  - Signs keep their own sharp surfaces (`ownSurface`); the painter garbles small print.
  - Leave flames out of the plate (painted, they read as paper cut-outs); draw them live.
  - Put the painted sky on a far card with `skyCard(kit, projection, painting, projector)` from
    `projected-set.js` (this plugin kit; the film kit's scenes write it out by hand).
  - A full-frame helper pass must not test depth (`runPass` turns it off): a working picture that held
    the set's depths silently hid most of a pass.

- Composing a shot (log 30; full rules in `07 Composing a shot.md`):
  - A shot looks arranged when its strong things agree: where the street's lines meet, the
    brightest parts, the biggest near props and the warm light all fall on the subject. Even weight left
    and right is not enough. Check with `paper-film/tools/measure_composition.py`.
  - Aim the street by turning the camera; move it only by sliding. A turn during a move slides where the
    lines meet across the frame.
  - Stand the camera where a person would stand to look at the subject, at eye height, level.
  - Story props touch and overlap as one group; work props stay small and far; nothing big and dark in
    the bottom left, where the eye enters.
  - In one run, Nano Banana Pro made a good sketch of the composition when free to choose the camera;
    never use a program's lettering: the notices came back garbled.

- A dark painted street (the wet lockout, log 37; `paper-film/scenes/lockout-test.js`):
  - The stage's filmic curve darkens dark values, so a dark wet road arrived at 0.75 to 0.86 of its painted
    brightness and some of it crushed to black. Give that scene `toe: 1` in its look (the curve may brighten
    but never darkens a value) and ease the dark frame edge (`vignette: 0.25`). `toe` is 0 for every scene
    that does not ask, so no other scene's look should change. What was measured: eight stills drawn once with
    the old and once with the new stage showed no difference; a ninth, the house sample at 20 s, differed in a
    checker's redraw by a faint speckle (7.7 percent of dots, by at most 7 of 255, with no lighter or darker lean),
    and drawn ten times that picture came out two ways even with the unchanged old stage alone (lesson 141 of the
    austerity project's notes). After a new painting, measure how bright the road arrives in the plate view against
    the painting (the wet lockout: 0.935, the dry one with the same look: 0.96;
    `calculators/after_painting.py check --toe 1` prints it).
  - A wet front painting needs its own wet behind painting: with the old dry behind painting the road
    the near props hid came back pale and dry when the camera moved (59 percent of the road dots lighter).
    Swap the two paintings as a pair, with the look line, and keep the dry pair beside them with a short note
    saying how to go back.
  - Painted dry and wet streets differ in feel: the wet painting reads as a detailed picture with a paint
    finish (no thick ink outlines, a plain dark sky); the dry one has flat colour and thick outlines.

- A proof that a change left other scenes unchanged needs several draws of each picture with each version
  (at least three) and a count of the pictures and draws compared: some scenes (the house sample at 20 s) come
  out two slightly different ways from run to run with nothing changed (lesson 141). Before you blame a change
  for a speckle, redraw the unchanged old version several times. Compare with `calculators/regression_compare.py`,
  and write what was measured, never "dot for dot".
- Text with prices written through the shell loses its dollar signs: US$0.048 became US/bin/bash.048 (the
  shell read `$0` as its own name; lesson 142). Write such text with the file-writing tool or a quoted
  here-document (`<<'EOF'`), then search the file for `bin/bash`.
