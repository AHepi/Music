You are building one place for a narrated explainer film, alone, as a test.

The owner's request, in their own words: "A tea house."

The film has a look. Five pictures in /home/claude/blind-test-2/control-build/target/reference/ show it, and /home/claude/blind-test-2/control-build/target/The look.md describes it. Your picture should belong with them.

What you have:
- A work folder: /home/claude/blind-test-2/control-build. Write everything there.
- Blender 5.1.2 as the Python module `bpy`: run scripts with `python3`. The computer has 2 processors and another builder is drawing on it at the same time, so pictures take a while.

Rules:
- Read nothing outside your work folder. No internet, no image generation, no rented machines, no other folders on this computer.
- Your clock: your last picture must be finished by 23:50 by this computer's clock (check with `date`). Plan for it.
- Your final picture is a tall frame for a vertical film. Draw it at 540 x 960 within your time. It will be redrawn at 1080 x 1920 with 64 samples for the judges, so also leave a script, render_final.py, that draws your final scene with all its finishing, run as: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
- When you finish (or at 23:50), end with a report in plain words: what you built, how you lit and framed it, every picture you drew with how long it took, what you checked and fixed, and what you did not do. Also save the report as REPORT.md in your work folder if you can.
