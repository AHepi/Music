# 43 Blind test: a tea house (stopped, ready to restart)

What this folder is: everything needed to run the second blind test of `painted-place` again. It was started twice on 2 November 2026 and stopped both times before anything was drawn.

## How it is set up

- The request, the owner's own first example ("ask for a different scene, like a tea house or modern street"): "A tea house."
- Two Sonnet builders start at the same minute and stop at the same minute (80 minutes), both on this 2-processor computer, both isolated (no internet, no image generation, no rented machines, no other folders).
- `plugin builder brief.md`: the builder gets a copy of the plugin folder and the request, nothing else; it stops for the blind judge after its first small picture and is resumed with the verdict.
- `control builder brief.md`: the builder gets Blender alone, the request, the five reference pictures and the look page (as the owner described giving an LLM reference images). The first blind test's control had the words only.
- Both final scenes are redrawn the same way for the judges: 1080 x 1920, 64 samples.
- `make_judging_folders.py`: one folder per judge (four), the two pictures under letters swapped for half the judges, the reference pictures and the look page beside them; four lenses scored 0 to 10: could it be a photograph, does it deliver the request, could it be a backdrop in the look, how old and used are its surfaces; then a choice and one fix each.
- The clock in the briefs (`23:50`) is from the second start: set a new end time before starting again.

## What happened

- 22:11: started. 22:18: stopped, because the fresh checker's report (log 42) listed faults that could have sunk the plugin's builder (names like "tea house floor" becoming a stone wall, weeds indoors, a second dressing stretching the stone picture).
- 22:30: restarted on the fixed plugin with a new clock. 22:38: the owner's interruption ("Just a hint. See if you can improve the look using PBR textures from poly haven.") stopped both builders and a second checker. Nothing had been drawn.

## Traps

- Restart it only when the owner says so (decision 54).
- Wait for any checker before starting: a test that runs on a plugin about to change measures the wrong plugin (lesson 157).
- Give both builders the same end time, written as a clock time they can check with `date`.
