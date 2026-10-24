32. **Fixing what three rounds of critics found in the notice corner, sharpening the shot checker, and
    painting it** (continues log 31; decision 37). No new words from you; this follows log 31's next step.
    - **The second critics' fixes, and one that went wrong.** The skeptic of the second round asked for a sooty
      lining inside the drum 0.365 m across its radius. The drum is only 0.296 m, so the lining stuck out as a
      flat orange band and brought the drum's edge to 9 pixels from the notice. The shot checker caught the
      near-touch; a measurement of the drum model found why. The lining now fits inside the wall (lesson 116).
    - **Light linking.** Blender can choose which objects a light reaches. The warm light aimed at the notice's
      bottom edge now reaches only the notice and its board (it had lit the chair's top rail as bright as the
      notice); the lantern's light skips the lantern itself (it lit the brass frame and made the glass look
      milky); the fire's light skips the drum and the chair (from 0.4 m over the rim it turned the rim and the
      chair's back as bright as the notice). The film's live flames light the drum instead.
    - **The third critics** (composition and light; what the painter will garble; 1926 and the story) **and a
      skeptic** found, and these were fixed:
      - the drum's mouth an even orange disc that would be painted as orange soup or a lid: its glow now fades
        up from the coals, dark under the rim;
      - the shut colliery gates lost in a pure-black doorway, so the gate read as open: dim shut doors behind
        them;
      - the gas lamps and the lantern flat amber cards: the "see-through" setting had been ignored, because the
        imported glass takes that value from its picture; unhooked, the mantles and the flame show;
      - the extra lit window landed off the frame: moving the camera never refreshed the scene, so the window
        picker used the old camera; two windows now light on the left side of the frame;
      - the whole frame a third darker than the picture you liked: a brighter dusk sky (1.4 to 1.96);
      - the chair so dark its legs were darker than the pavement: lighter paint (0.25), still darker than the
        notice;
      - the gutter still like steps: a plain stone colour (the first try was a pale stripe, the second joined
        the drum's shadow into one dark pool where the eye enters; the third sits just under the road);
      - the drum's side running 2 pixels in front of the board's left post for 113 pixels: the post moved 4.5 cm.
      - Left as they are: the oil-drum brazier (more 1984 than 1926, but the composition depends on it), the
        board across the pavement, the pail in the band where apps put captions.
    - **What the shot checker learnt** (each tested; the 11 faults planted on purpose still come first):
      - edges by colour as well as brightness: a rusty drum against a blue-grey road is about as bright as the
        road, so it took a correct picture for an out-of-date one;
      - a picture is out of date only when a prop lines up clearly better once slid a little (a moved prop
        does; one with faint edges doesn't). It caught all four old pictures, passed every new one, and later
        found the painter's 3-pixel shift;
      - the longest stretch where two edges touch, so a deep overlap higher up no longer excuses a post running
        along the drum's side lower down;
      - background props in the check (the far lamp, handcart, sacks, dustbins): it found the handcart only
        just overlapping the dustbins and the new lamp's post meeting their edge;
      - which lights reach which props (light linking), and that a lit lantern's small flame may outshine the
        notice while its glass may not (a flame lights about 6% of the lantern that bright; a glowing glass 18
        to 22%).
    - **Where the frame stands** ("32 Notice corner - relit and checked"): the checker passes 32 of 38 checks.
      Open: the quiet left half holds 38% of the weight (aim 40; the picture you liked 42%); the notice's
      bottom is 0.08 warmer than its top (needs 0.10), but in the film the notice is its own surface, lit by
      the film page, which now has a copy of the warm light under it; and four places that differ from the
      picture you liked on purpose.
    - **The paint-over** ("32 Notice corner - plate and painting"): Flux 3 repainted the plate (the bigger
      picture drawn from where the slide starts) in the series' style, with the critics' instructions: keep
      every shape and the light and dark; a dull rust drum with a dark sooty mouth; shut gates against grey
      doors; and never add flames, smoke, glows or new shadows round the near props, because those would
      slide or blink out once the camera moves. It did all of that, and added nothing. The notice and the
      colliery sign went to blurred marks, as expected: the film keeps its own sharp copies of both.
    - **Lining the painting up.** The shot checker's new test showed every prop in the painting lining up
      better once slid about 4 pixels: the painter had stretched the picture by 0.65% and shifted it 3
      pixels. A new tool (`align_painting.py`) finds that stretch and shift from the props' outlines and undoes
      it: 96% of the outlines then sit on the painting's edges, against 70% before. A second painting with the
      near props painted out (what the film shows behind them as the camera moves) was lined up against the
      first ("32 Notice corner - painting with and without the near props").
    - **The film page's own end frame**, checked by the shot checker: the notice is 0.23 warmer at its bottom
      than its top (needs 0.10; the picture you liked measures 0.17), now that the page has a copy of the warm
      light under it; and the quiet left half holds 46% of the weight (aim 40 to 48). New there, from the
      painting: a dark painted gutter leading in from the bottom (2.1% of the frame, limit 1%), the lamps and lit
      windows spreading the warm light (43% of it round the story props), and pale painted dustbins. Kept as
      they are: the gutter is a narrow lead-in line, not a dark mass.
    - **The film** ("32 Test - notice corner slide", 13 seconds, music only): BRITAIN 1926 over the dim sky,
      one slow slide of 1.5 m toward the notice without turning, the drum's live fire and smoke, the lantern's
      flicker, then LOCKED OUT / FROM 1 MAY 1926 over the held frame, and a fade. The music is a quiet stretch
      of your soundtrack (from 3 minutes 36 seconds), faded in and out.
    - **Checked in motion by two helpers and a skeptic.** Clean: the camera never turns (everything spreads
      out from one fixed spot), the move is smooth and stops by 8.4 seconds, no blinks, no painted outlines left
      on the road, no smearing at the frame's edges, the notice's print steady and its dates right. One fault a
      viewer would see: 2 seconds in, the long shadows the fire throws from the pail and the chair faded off
      the pavement. The painting with the near props painted out had lost them, and the film switches to it
      round the props as soon as the camera moves. Fixed by keeping the main painting everywhere except inside
      the props' own outlines (`keep_painted_shadows.py`), then filmed again. Also changed: the fire glow's
      size pulse calmed (its rim slid on the road), a soft dark band behind the first title (the amber 1926 was
      faint against the sky), the two chimney smokes dropped (both chimneys are out of the frame), and the
      music raised from -17.7 to -14 LUFS (a helper found it faint on a phone speaker).
    - **Filmed again** (about 41 minutes, two halves at once): the patch of pavement right of the pail now stayed at
      70 to 71 (on a 0 to 255 scale) through the switch, where the first filming rose to 89 as the shadow faded.
      A fresh helper checked the changes and found one new fault the fix had made: a pale outline 10 to 15
      pixels wide round the pail from 1.8 seconds to the end. The narrow gap kept round each prop (so the
      painter's ink lines don't stay on the road) still had no shadow. Fixed by carrying the shadows' darkening
      into the gap and under the props (measured outside them and spread inward), checked on single frames,
      and filmed a third time. The helper found the title band smooth, the fire glow steady (1.2% swing against
      2.8%), nothing else changed, and the music at -13.7 LUFS with clean starts and ends.
    - **The third filming** has no pale outline round the pail (checked side by side at 10 seconds), no jumps, and
      the same clean shadows, title band and glow. It is the one sent ("32 Test - notice corner slide", 8.5 MB).
    - **Left for later** (minor, or a bigger change): the notice's key lines are only just readable on a phone
      (PITS WILL BE CLOSED 11 pixels tall; about 18 would read easily); the flames look like flat cut-outs and
      the sparks rise in tidy strings; the notice paper's edges show a faint 1-pixel saw-tooth zoomed in; the
      end titles arrive at 8.9 seconds with a small pop; and nothing personal is left on the chair to say
      someone kept watch there (a cap or jacket would).
    - **Not checked, or unsure:** I haven't seen it on a phone; the helpers judged from frames and measurements
      and could not listen. The music's stretch was chosen by its loudness, not by ear. The checker measures only
      what shows on screen, so props poking into each other in 3D are not caught. The paintings' price is a
      range because fal didn't show the exact charge.
    - **Computer time:** about 3 hours of drawing and filming in all (each filming about 41 minutes).
    - **Cost:** about 20 to 45 US cents on fal for the two paintings; everything else ran here. About US$5.00 of the
      picture allowance is left (between US$4.95 and US$5.20).
