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
  cut-outs are only drawn where at least half solid). Use `setFading` from
  `paper-film/scenes/house-sample/page-1.js` (log 27, lesson 87 of the project notes).

- Built places, painted over (`paper-film/scenes/projected-set.js`, the pit village test, log 29):
  - The plate's frame is only a little wider than the film's: turn the camera at most a degree or two
    and push in with the lens. Check the `weights` view at the end of every move (blue at an edge =
    no painting there).
  - Moving past near props uncovers what they hid, and the painter's outlines round them lie on the
    road: give the projection a `behind` painting (the same painting with the near props painted out
    by Flux) and soft contact shadows under those props.
  - Signs keep their own sharp surfaces (`ownSurface`); the painter garbles small print.
  - Leave flames out of the plate (painted, they read as paper cut-outs); draw them live.
  - A full-frame helper pass must not test depth (`runPass` turns it off): a working picture that held
    the set's depths silently hid most of a pass.

- Composing a shot (log 30; full rules in `07 Composing a shot.md`):
  - A shot looks arranged when its strong things agree: where the street's lines meet, the biggest
    bright shape, the biggest near props and the warm light all fall on the subject. Even weight left
    and right is not enough. Check with `paper-film/tools/measure_composition.py`.
  - Aim the street by turning the camera; move it only by sliding. A turn during a move slides the point
    where the lines meet across the frame.
  - Stand the camera where a person would stand to look at the subject, at eye height, level.
  - Story props touch and overlap as one group; work props stay small and far; nothing big and dark in
    the bottom left, where the eye enters.
  - Image models are good layout sketches when allowed to choose the camera, but never use their
    lettering: all of them garbled the notice.
