# Plugin builder's reports (tea house)

What this file is: the plugin builder's two reports, returned as text because the harness refused its file writes; saved here unchanged in substance by the coordinating session. The full text of each is in the session record; the key facts:

- Started 00:30, round 1 drawn 00:48 (291 s), packet for the blind judge made; the owner then decided "No blind judges. I'll judge", so the judge was stopped before answering and the builder fixed from its own measures and eyes.
- Round 2 finished 01:25 (369 s). Dials: rain, exposure -0.35, window light 0.2, lamp light 0.5, sky light 6.0, amber reflection 0, haze 1.6, painterly 0.28; dressing with --grime 1.6 --growth 1.2 (DRESSED-4.blend).
- Measures of round 2: brightness 0.22 (in band), warm 39 percent (band 15-35), cool 41 percent (in band), warm light 3.9 percent (band 0.4-3.0).
- Shape changes for round 2: a bigger teapot lantern with lid, knob, foot, spout and handle; three smoke volumes; smaller lamp heads; fewer lit panes; tea sets 1.5 times life size; sash bars on the plaster wall's windows.
- Six extra small test pictures (270 x 480) were drawn to set the dials, more than the skill's one fix pass asks for.
- Plugin gaps it found: no brass or copper role; windows in plaster walls get no jambs, sill or sash; smoke faint against the dark sky; a first picture with big lit panes far too bright (sky light had to reach about 6); scripts must import bpy before bmesh.
- Redraw at full size: python3 /home/claude/blind-test-2/painted-place/stage/render_small.py --scene /home/claude/blind-test-2/plugin-build/DRESSED-4.blend --out /home/claude/blind-test-2/plugin-build/round-2-1080x1920.png --rain --exposure -0.35 --window-light 0.2 --lamp-light 0.5 --sky-light 6.0 --haze 1.6 --amber-reflection 0 --width 1080 --height 1920 --samples 64
