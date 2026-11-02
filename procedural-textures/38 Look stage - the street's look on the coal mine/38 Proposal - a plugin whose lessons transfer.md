# 38 Proposal: a plugin whose lessons transfer

What this file is: what the record says about why the lessons have not transferred, and the shape of a plugin built so that they do. One page. The decision at the end is yours.

## What the record says (your own logs)

- The plugin carried its lessons as **procedure**: 400 lines of required steps, gates, audits and card ledgers in one skill alone, 622 files in all. A model following them spends its attention on the process. Its own building blocks (trees, hill band, coarse ground, flat light) pulled the picture below what the same model did unaided. Blind judges: plugin village 2.7 out of 10; Sonnet alone 6.3; Opus alone 6.4 (logs 32 to 34).
- The plugin taught **surfaces**; what held the villages back was shapes, light and cameras (log 33's lesson).
- The step that helped most was not a rule: **blind judges' plain words, then one fix pass** took Opus from 6.0 to 7.2, more than the switch from Sonnet to Opus did (log 36).
- The street bundle got close in one session because one model held the whole picture and iterated against the reference; its scripts then welded the look to that one street. Today's test (38) shows the look's scene-independent half transfers as one function: the mine landed with the street on every measure after one fix pass.

So: lessons transfer when they are (a) a target the next session can see (reference pictures and a written look), (b) a judge that measures and speaks in plain words, and (c) code that does the part a model will not do from a guide. They do not transfer as instructions, however many.

## The shape

Small. Five things, nothing mandatory but the loop.

1. **The look.** Six to ten reference pictures (the three paintings, the street render, the wet lockout painting, the mine C picture once you accept it) and one page in words with the measured bands (brightness 0.16 to 0.30, warm light 0.5 to 1.5 percent of the frame, teal-blue shadows, one dominant light with a consequence in the air, everything old, single-point perspective, hero centred, foreground along the bottom).
2. **The judge.** One tool: the three measures against the bands, plus a blind judging prompt with a fixed rubric drawn from the look page, run by a fresh model that does not know who built the picture. It returns plain-word fixes ordered by what a viewer notices first, and where a fix is a dial (exposure, window light, haze, sky strength, finish mix, camera height and lens) it names the dial. This is the lesson carrier: every lesson so far that was about *what looks wrong* lives here as a rubric line, not as a build rule.
3. **The look stage.** `look_stage.py` as tested today, grown only where the judge keeps asking for the same thing (a low-sun variant, a daylight variant, rain, snow). The only "how-to" in code.
4. **Proven materials by role.** The street bundle's 45 materials (stone, cobble, pavement, wet film, slate, wood, iron, rust, warm and dark glass) applied by a role word (wall, ground, roof, window, iron), because they are good. The plugin's own trees, hill band and ground do not come along; the model builds shapes its own way, where it is already strong.
5. **The loop.** Build the shapes → look stage → small render → judge → one fix pass → (second judge only if the first said "nearly") → plate → painter if the flatter painted look is wanted → stage. The picture is the test; no gate stops a picture.

Rules kept from your decisions: Cycles when lights are on (44); batches of far-apart variations when trying a change (46); Opus writes and checks the plugin, Sonnet is the blind builder (47); every new set updates the plugin (48); the plugin carries the techniques itself and a test build gets only the plugin and your plain words (45, CLAUDE.md).

## What to do with the old plugin

Two honest options:

- **A. A new small plugin beside it** (`painted-place`, say), built from the five things above, tested blind on a place that is not a village (the courtyard, a tea house, a harbour). The old plugin stays for the paper-film chapters it already makes (pages, narration timing, fact checks), which it does well. Clean test, nothing lost.
- **B. Rebuild the old plugin around the five things**, keeping its film-making skills and dropping the place-building procedure. Fewer plugins; a bigger, slower change, and the blind test is muddied by what remains.

I would take A: it lets the blind test say whether the new shape works before anything is removed.

## Costs

The look stage and the judge's measures run free here. A blind test of the new plugin needs one Sonnet build and one judging pass (model time only). Renders: free at small size here (two minutes a picture on this machine), seconds on the rented cards.

## Traps

- If the judge's rubric is written from the plugin's old lessons instead of from the reference pictures, it will teach the old mistakes. Write it from the pictures.
- A judge that sees who built the picture, or the builder's own report, is not blind. Hand it the picture and the references only.
- "One fix pass" means one. A third pass is where the card bills and the procedure grew last time.
- The look stage is a blue hour. A request for noon needs a daylight variant first, or the judge will fail every picture for the wrong reason.
