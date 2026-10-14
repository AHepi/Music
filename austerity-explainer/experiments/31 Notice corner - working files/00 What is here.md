# 31 Notice corner - working files

What this folder is: the working files from rebuilding the picture you liked in our 3D street and from building
the shot checker (log 31 in the project story).

- `test pictures/`: every test picture in order. "round 1" to "round 9" are the camera and placing rounds (round 9
  is after the camera was matched to the picture you liked); "first rebuild" is the frame the four critics
  judged (one copy shows the render fault, the hard black wedge); "lighting round 1" to "26" are the small
  test pictures made while relighting the frame, each checked by the shot checker; the pictures named after a
  round with a description show what that round found (the drum's lining sticking out, the chair's and the
  lantern's brightest parts, the drum outline the checker could not see, the left lamp just meeting the dustbins).
- `checker tests/`: the shot checker's report and marked picture for the good frame and for each of the eleven
  scenes broken on purpose (the names say what was broken), and `measure-all.sh`, which made them. The same
  tests can be run again with `film-kit/paper-film/blender/tests/run-checker-tests.sh`.
- `final frame measurements/`: what Blender measured for the finished frame (`facts.json`, the flat-colour
  pictures).
- `reviews/`: what the helpers and skeptics found: the verifier on the first checker; the five helpers and the
  skeptic on the second; the four critics and the skeptic on the first rebuild.
- `tools/`: the scripts used to match the camera to the picture you liked (`match_camera.py`, landmarks in
  `landmarks.py`), to draw its street lines onto our pictures (`target_lines.py`), and to look inside the prop
  models (`inspect_*.py`).
- `tools/` also holds the small scripts from the last relighting rounds: `measure_drum.py` (the drum's size, to fit
  its sooty lining inside it), `brightest_parts.py` (marks a prop's brightest parts), `light_link_trial.py` and
  `inspect_link.py` (trying Blender's light linking, which chooses what a light reaches), `lamp_names.py` (why a
  second gas lamp would have been taken for the first), `quiet_weight.py` (the quiet half's weight, rule 10), and
  `measure_outline_shift.py`, `colour_edges_trial.py`, `shift_trial.py`, `row_probe.py` (the trials behind the
  checker's new test for a picture made before the scene changed). In them, KIT stands for the film kit's folder,
  BLENDER for Blender, and OUT_FOLDER and SCRATCH for a folder of your own.
